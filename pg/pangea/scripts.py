#!/usr/bin/env python3
import argparse
import os
import sys
from importlib import import_module
from pathlib import Path

from loguru import logger

import envo
from pangea import comm, pkg_vars

__all__ = []


def impor_module():
    pass


class Pangea:
    def __init__(self) -> None:
        self.current_dir = Path(".").absolute()

        self.cluster_name = self.current_dir.name
        self.class_name = comm.dir_name_to_class_name(self.cluster_name)

        self.context = {
            "class_name": self.class_name,
            "cluster_name": self.cluster_name,
        }

    def create_env(self, stage: str) -> None:
        # render env_local
        env_templ_context = self.context.copy()
        env_templ_context.update(
            {"stage": stage, "emoji": envo.stage_emoji_mapping[stage]}
        )
        comm.render_py_file(
            pkg_vars.templates_dir / "env.py.templ",
            Path(f"env_{stage}.py"),
            env_templ_context,
        )

    def create_cluster(self) -> None:
        # render cluster.py
        current_dir = Path(".").absolute()

        cluster_file = Path("cluster.py")
        comm.render_py_file(
            pkg_vars.templates_dir / "cluster.py.templ", cluster_file, self.context
        )
        comm.render_py_file(
            pkg_vars.templates_dir / "env_comm.py.templ",
            Path("env_comm.py"),
            self.context,
        )

        cluster_file.chmod(0o777)

        self.create_env("local")
        self.create_env("test")
        self.create_env("stage")

        bin_dir = Path(".bin")
        Path(".deps").mkdir()
        bin_dir.mkdir()

        os.chdir(str(bin_dir))
        os.symlink("../cluster.py", "cl")

        os.chdir(str(current_dir))

        logger.info(f"Created cluster 🍰!")

        sys.path.insert(0, str(current_dir.parent))
        env = import_module(f"{current_dir.name}.env_local").Env()
        env.activate()
        Cluster = import_module(f"{current_dir.name}.cluster").Cluster
        Cluster.createapp("ingress", "system", "ingress")

        sys.path.pop()

        logger.info('Activate 🐣 local environment with "envo"')

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
