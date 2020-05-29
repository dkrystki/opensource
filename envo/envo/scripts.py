#!/usr/bin/env python3
import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from subprocess import Popen
from threading import Lock, Thread
from traceback import print_exc
from typing import Any, Dict, List, Optional

from ilock import ILock
from inotify.adapters import Inotify  # type: ignore
from jinja2 import Environment, Template
from loguru import logger

from envo import Env, comm
from envo.comm import import_module_from_file

__all__ = ["stage_emoji_mapping"]


package_root = Path(os.path.realpath(__file__)).parent
templates_dir = package_root / "templates"

stage_emoji_mapping: Dict[str, str] = {
    "comm": "",
    "test": "🛠",
    "local": "🐣",
    "stage": "🤖",
    "prod": "🔥",
}


class Envo:
    @dataclass
    class Sets:
        stage: str
        addons: List[str]
        init: bool

    root: Path
    stage: str
    env_dirs: List[Path]
    selected_addons: List[str]
    addons: List[str]

    def __init__(self, sets: Sets) -> None:
        self.se = sets

        self.addons = ["venv"]
        self.env_dirs = []

        unknown_addons = [a for a in self.se.addons if a not in self.addons]
        if unknown_addons:
            raise RuntimeError(f"Unknown addons {unknown_addons}")

        self.inotify = Inotify()

        self.shell_proc: Optional[Popen] = None
        self.shell_thread = Thread(target=self._shell_thread)

        self.source_changed = False

        self._envs_before: Dict[str, Any] = os.environ.copy()

        self.shell_lock = Lock()

    def spawn_shell(self) -> None:
        if self.shell_proc:
            self.shell_proc.terminate()
            self.shell_proc.wait()
            self.shell_proc = None
        try:
            env = self.get_env()
            os.environ = self._envs_before.copy()  # type: ignore
            self.shell_proc = env.shell()
        except Env.EnvException as exc:
            logger.error(exc)
        except Exception:
            print_exc()

    def _shell_thread(self) -> None:
        while True:
            with self.shell_lock:
                pass

            if self.shell_proc:
                self.source_changed = False
                self.shell_proc.wait()

            # it means that user pressed ctr-d and wants to exit
            if not self.source_changed:
                os._exit(0)

    def _files_watchdog(self) -> None:
        for event in self.inotify.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            if "IN_CLOSE_WRITE" in type_names:
                with self.shell_lock:
                    logger.info(f'\nDetected changes in "{str(path)}".')
                    logger.info("Reloading...")

                    self.source_changed = True
                    self.spawn_shell()

                    # without this delay envo creates nested popen shells after modifying envs files too quickly
                    time.sleep(1.0)

    def _start_files_watchdog(self) -> None:
        for d in self.env_dirs:
            comm_env_file = d / "env_comm.py"
            env_file = d / f"env_{self.se.stage}.py"
            self.inotify.add_watch(str(comm_env_file))
            self.inotify.add_watch(str(env_file))

        self.files_watchdog_thread = Thread(target=self._files_watchdog)
        self.files_watchdog_thread.start()

    def _discover_envs(self) -> None:
        path = Path(".").absolute()
        while True:
            env_file = path / f"env_{self.se.stage}.py"
            if env_file.exists():
                self.env_dirs.append(path)
            else:
                if path == Path("/"):
                    break
            path = path.parent

        sys.path.insert(0, str(self.env_dirs[0].parent))

        if not self.env_dirs:
            raise RuntimeError("""Can't find "env_comm.py" """)

    def _create_init_files(self) -> None:
        for d in self.env_dirs:
            init_file = d / "__init__.py"

            if init_file.exists():
                init_file_tmp = d / Path("__init__.py.tmp")
                init_file_tmp.touch()
                init_file_tmp.write_text(init_file.read_text())

            if not init_file.exists():
                init_file.touch()

            init_file.write_text("# __envo_delete__")

    def _delete_init_files(self) -> None:
        for d in self.env_dirs:
            init_file = d / Path("__init__.py")
            init_file_tmp = d / Path("__init__.py.tmp")

            if init_file.read_text() == "# __envo_delete__":
                init_file.unlink()

            if init_file_tmp.exists():
                init_file.touch()
                init_file.write_text(init_file_tmp.read_text())
                init_file_tmp.unlink()

    def _unload_modules(self) -> None:
        modules = list(sys.modules.keys())[:]
        for m in modules:
            for d in self.env_dirs:
                package = d.name
                if m.startswith(package):
                    sys.modules.pop(m)

    def get_env(self) -> Env:
        env_dir = self.env_dirs[0]
        package = env_dir.name
        env_name = f"env_{self.se.stage}"
        env_file = env_dir / f"{env_name}.py"

        module_name = f"{package}.{env_name}"

        with ILock("envo_lock"):
            # time.sleep(random.uniform(0.0, 1.5))
            self._create_init_files()

            self._unload_modules()

            try:
                module = import_module_from_file(env_file)
                env: Env
                env = module.Env()
                return env
            except ImportError as exc:
                logger.error(f"""Couldn't import "{module_name}" ({exc}).""")
                raise
            finally:
                self._delete_init_files()

    def _create_from_templ(
        self, templ_file: Path, output_file: Path, is_comm: bool = False
    ) -> None:
        Environment(keep_trailing_newline=True)
        template = Template((templates_dir / templ_file).read_text())
        if output_file.exists():
            logger.error(f"{str(output_file)} file already exists.")
            exit(1)

        output_file.touch()
        env_dir = Path(".").absolute()
        package_name = comm.dir_name_to_pkg_name(env_dir.name)
        class_name = comm.dir_name_to_class_name(package_name) + "Env"

        context = {
            "class_name": class_name,
            "name": env_dir.name,
            "package_name": package_name,
            "stage": self.se.stage,
            "emoji": stage_emoji_mapping[self.se.stage],
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
        logger.info(f"Created {self.se.stage} environment 🍰!")

    def handle_command(self, args: argparse.Namespace) -> None:
        if args.version:
            from envo.__version__ import __version__

            logger.info(__version__)
            return

        if args.init:
            self.init_files()
            return

        self._discover_envs()

        if args.save:
            self.get_env().dump_dot_env()
            return

        if args.dry_run:
            self.get_env().print_envs()
        else:
            self.spawn_shell()
            self._start_files_watchdog()
            self.shell_thread.start()


def _main() -> None:
    # os.environ["PYTHONPATH"] = ":".join(os.environ["PYTHONPATH"].split(":")[:-1])

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


if __name__ == "__main__":
    _main()
