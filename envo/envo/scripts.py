#!/usr/bin/env python3
import argparse
import os
import sys
import time
from dataclasses import dataclass
from importlib import import_module, reload
from pathlib import Path
from subprocess import Popen
from threading import Thread
from traceback import print_exc
from typing import Any, Dict, List, Optional

from inotify.adapters import Inotify  # type: ignore
from jinja2 import Environment, Template

from envo import Env, comm


class Envo:
    @dataclass
    class Sets:
        stage: str
        addons: List[str]
        init: bool

    stage_emoji_mapping: Dict[str, str] = {
        "comm": "",
        "test": "🛠️",
        "local": "🐣",
        "stage": "🤖",
        "prod": "🔥",
    }
    root: Path
    stage: str
    templates_dir: Path
    env_dir: Path
    package_name: str
    selected_addons: List[str]
    addons: List[str]

    def __init__(self, sets: Sets) -> None:
        self.se = sets

        self.root = Path(os.path.realpath(__file__)).parent
        self.addons = ["venv"]
        self.templates_dir = self.root / "templates"

        self.env_dir = Path(".").absolute()
        self.package_name = self.env_dir.name

        unknown_addons = [a for a in self.se.addons if a not in self.addons]
        if unknown_addons:
            raise RuntimeError(f"Unknown addons {unknown_addons}")

        self.inotify = Inotify()

        self.shell_proc: Optional[Popen] = None
        self.shell_thread = Thread(target=self._shell_thread)

        self.source_changed = False

        self._envs_before: Dict[str, Any] = os.environ.copy()
        self.env_root = Path(".").absolute()

    def spawn_shell(self) -> None:
        if self.shell_proc:
            self.shell_proc.terminate()
            self.shell_proc.wait()
            self.shell_proc = None
        try:
            env = self.get_env()
            os.environ = self._envs_before.copy()  # type: ignore
            self.shell_proc = env.shell()
        except Exception:
            print_exc()

    def _shell_thread(self) -> None:
        while True:
            if self.shell_proc:
                self.source_changed = False
                self.shell_proc.wait()

            # it means that user pressed ctr-d and wants to exit
            if not self.source_changed:
                os._exit(0)

            time.sleep(1)

    def _files_watchdog(self) -> None:
        for event in self.inotify.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            if "IN_CLOSE_WRITE" in type_names:
                print(f'\nDetected changes in "{str(path)}".')
                print("Reloading...")

                self.source_changed = True
                self.spawn_shell()
                print("Reloaded")

    def _start_files_watchdog(self) -> None:
        self.inotify.add_watch(str(self.env_dir / "env_comm.py"))
        self.inotify.add_watch(str(self.env_dir / f"env_{self.se.stage}.py"))
        self.files_watchdog_thread = Thread(target=self._files_watchdog)
        self.files_watchdog_thread.start()

    def _discover_envs(self) -> None:
        path = Path(".").absolute()
        while True:
            if (path / "env_comm.py").exists():
                self.env_root = path
                sys.path.append(str(path.parent))
                break
            else:
                if path == Path("/"):
                    raise RuntimeError("""Can't find "env_comm.py" """)
                path = path.parent

        self.env_dir = path
        self.package_name = self.env_dir.name

    def get_env(self) -> Env:
        package = self.env_dir.name
        env_name = f"env_{self.se.stage}"
        module_name = f"{package}.{env_name}"
        comm_module_name = f"{package}.env_comm"

        init_file = self.env_root / "__init__.py"

        if init_file.exists():
            init_exists = True
        else:
            init_exists = False
            init_file.touch()

        try:
            reload(import_module(comm_module_name, package=package))
            env: Env
            env = reload(import_module(module_name, package=package)).Env()  # type: ignore
            return env
        except ImportError as exc:
            print(f"""Couldn't import "{module_name}" ({exc}).""")
            raise
        finally:
            if not init_exists and init_file.exists():
                init_file.unlink()

    def _create_from_templ(
        self, templ_file: Path, output_file: Path, is_comm: bool = False
    ) -> None:
        Environment(keep_trailing_newline=True)
        template = Template((self.templates_dir / templ_file).read_text())
        if output_file.exists():
            print(f"{str(output_file)} file already exists.")
            exit(1)

        output_file.touch()

        class_name = comm.dir_name_to_class_name(self.package_name) + "Env"
        context = {
            "class_name": class_name,
            "name": self.package_name,
            "stage": self.se.stage,
            "emoji": self.stage_emoji_mapping[self.se.stage],
            "selected_addons": self.se.addons,
        }

        if not is_comm:
            context["stage"] = self.se.stage

        output_file.write_text(template.render(**context))

    def init_files(self) -> None:
        env_comm_file = Path("env_comm.py")

        if not env_comm_file.exists():
            self._create_from_templ(
                Path("env_comm.py.templ"), env_comm_file, is_comm=True
            )

        env_file = Path(f"env_{self.se.stage}.py")
        self._create_from_templ(Path("env.py.templ"), env_file)

    def handle_command(self, args: argparse.Namespace) -> None:
        if args.version:
            from envo.__version__ import __version__

            print(__version__)
            return

        if args.init:
            self.init_files()

        self._discover_envs()

        if args.save:
            self.get_env().dump_dot_env()

        if args.dry_run:
            self.get_env().print_envs()
        else:
            self.spawn_shell()
            self._start_files_watchdog()
            self.shell_thread.start()


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage", type=str, default="local", help="Stage to activate.", nargs="?"
    )
    parser.add_argument("--dry-run", default=False, action="store_true")
    parser.add_argument("--version", default=False, action="store_true")
    parser.add_argument("--save", default=False, action="store_true")
    parser.add_argument("-i", "--init", nargs="?", const=True, action="store")

    args = parser.parse_args(sys.argv[1:])

    if isinstance(args.init, str):
        selected_addons = args.init.split()
    else:
        selected_addons = []

    envo = Envo(
        Envo.Sets(stage=args.stage, addons=selected_addons, init=bool(args.init))
    )
    envo.handle_command(args)

    sys.argv = []
