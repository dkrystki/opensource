#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Any, Dict

import black
from jinja2 import Template

from envo.scripts import Envo
from pangea import comm, pkg_vars

__all__ = []


class Pangea:
    def __init__(self) -> None:
        self.current_dir = Path(".").absolute()

        self.cluster_name = self.current_dir.name
        self.class_name = comm.dir_name_to_class_name(self.cluster_name)

        self.context = {
            "class_name": self.class_name,
            "cluster_name": self.cluster_name,
        }

    def _render_py_file(
        self, template_filename: str, output: Path, context: Dict[str, Any]
    ) -> None:
        template = Template((pkg_vars.templates_dir / template_filename).read_text())
        output.write_text(template.render(**context))
        try:
            black.main([str(output), "-q"])
        except SystemExit:
            pass

    def create_env(self, stage: str) -> None:
        # render env_local
        env_templ_context = self.context.copy()
        env_templ_context.update(
            {"stage": stage, "emoji": Envo.stage_emoji_mapping[stage]}
        )
        self._render_py_file("env.py.templ", Path(f"env_{stage}.py"), env_templ_context)

    def create_cluster(self) -> None:
        # render cluster.py
        cluster_file = Path("cluster.py")
        self._render_py_file("cluster.py.templ", cluster_file, self.context)
        self._render_py_file("env_comm.py.templ", Path("env_comm.py"), self.context)

        cluster_file.chmod(0o777)

        self.create_env("local")
        self.create_env("test")
        self.create_env("stage")

        Path(".deps").mkdir()
        Path(".bin").mkdir()

    def handle_command(self, args: argparse.Namespace) -> None:
        if args.version:
            from pangea.__version__ import __version__

            print(__version__)
            return

        if args.init:
            self.create_cluster()


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", default=False, action="store_true")
    parser.add_argument("--version", default=False, action="store_true")

    args = parser.parse_args(sys.argv[1:])

    pangea = Pangea()
    pangea.handle_command(args)
