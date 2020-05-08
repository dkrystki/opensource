#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Any, Dict

import black
from jinja2 import Template

import pangea
from envo.scripts import Envo
from pangea import comm


class Pangea:
    def __init__(self) -> None:
        self.current_dir = Path(".").absolute()

    def _render_py_file(
        self, template_filename: str, output: Path, context: Dict[str, Any]
    ) -> None:
        template = Template((pangea.templates_dir / template_filename).read_text())
        output.write_text(template.render(**context))
        try:
            black.main([str(output), "-q"])
        except SystemExit:
            pass

    def create_cluster(self) -> None:
        cluster_name = self.current_dir.name
        class_name = comm.dir_name_to_class_name(cluster_name)

        # render cluster.py
        context = {"class_name": class_name, "cluster_name": cluster_name}
        self._render_py_file("cluster.templ.py", Path("cluster.py"), context)
        self._render_py_file("env_comm.templ.py", Path("env_comm.py"), context)

        # render env_local
        env_templ_context = context.copy()
        env_templ_context.update(
            {"stage": "local", "emoji": Envo.stage_emoji_mapping["local"]}
        )
        self._render_py_file("env.templ.py", Path("env_local.py"), env_templ_context)

        Path(".deps").mkdir()
        Path(".bin").mkdir()

    def handle_command(self, args: argparse.Namespace) -> None:
        if args.init:
            self.create_cluster()


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", default=False, action="store_true")

    args = parser.parse_args(sys.argv[1:])

    pangea = Pangea()
    pangea.handle_command(args)
