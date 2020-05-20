import shutil
import typing
from collections import OrderedDict
from importlib import import_module
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger

import environ
import fire
from envo import stage_emoji_mapping
from pangea import apps, comm, deps, devices, pkg_vars
from pangea.apps import App
from pangea.devops import run
from pangea.env import ClusterEnv
from pangea.kube import Namespace

environ = environ.Env()


__all__ = ["Cluster"]


class Cluster:
    class ClusterException(Exception):
        pass

    class Meta:
        name: str

    device: devices.ClusterDevice
    senv: ClusterEnv
    namespaces: typing.OrderedDict[str, Namespace]
    deps: List[deps.Dependency]
    python: apps.PythonUtils
    system: Namespace

    def __init__(self, env: ClusterEnv) -> None:
        self.env = env

        self.device = devices.all[self.env.device.type](self.env)

        self.deps = [
            deps.Kubectl(
                deps.Kubectl.Sets(
                    deps_dir=self.env.deps_dir, version=self.env.kubectl_ver
                )
            ),
            deps.Kind(
                deps.Kind.Sets(deps_dir=self.env.deps_dir, version=self.env.kind_ver)
            ),
            deps.Skaffold(
                deps.Skaffold.Sets(
                    deps_dir=self.env.deps_dir, version=self.env.skaffold_ver
                )
            ),
            deps.Hostess(
                deps.Hostess.Sets(
                    deps_dir=self.env.deps_dir, version=self.env.hostess_ver
                )
            ),
            deps.Helm(
                deps.Helm.Sets(deps_dir=self.env.deps_dir, version=self.env.helm_ver)
            ),
        ]

        self.namespaces = OrderedDict()

        self.python = apps.PythonUtils(
            se=apps.PythonUtils.Sets(root=self.env.root), li=apps.PythonUtils.Links()
        )

        self._create_apps()

    @classmethod
    def get_current_cluster(cls) -> "Cluster":
        env_comm = import_module(f"{cls.Meta.name}.env_comm").Env()
        env = env_comm.get_current_stage()

        current_cluster = cls(env=env)
        return current_cluster

    @classmethod
    def handle_command(cls) -> None:
        current_cluster = cls.get_current_cluster()
        try:
            fire.Fire(current_cluster)
        except Cluster.ClusterException as exc:
            logger.error(exc)

    @classmethod
    def createapp(cls, app_name: str, namespace: str, app_instance_name: str) -> None:
        app_dir = pkg_vars.apps_dir / app_name
        if not app_dir.exists():
            raise cls.ClusterException(f'App "{app_name}" does not exist 😓')

        app_instance_dir = Path(namespace) / Path(app_instance_name)

        if (app_instance_dir).exists():
            raise cls.ClusterException(
                f'App instance "{app_instance_name}" already exists in namespace "{namespace}" 😓'
            )

        app_instance_dir.mkdir(parents=True)

        context_base = {
            "instance_class_name": comm.dir_name_to_class_name(app_instance_name),
            "instance_name": app_instance_name,
        }

        comm.render_py_file(
            app_dir / "templates/env_comm.py.templ",
            app_instance_dir / "env_comm.py",
            context=context_base,
        )

        for s in ["local", "test", "stage", "prod"]:
            comm.render_py_file(
                app_dir / f"templates/env.py.templ",
                app_instance_dir / f"env_{s}.py",
                context={"stage": s, "emoji": stage_emoji_mapping[s], **context_base},
            )

        comm.render_py_file(
            app_dir / "templates/app.py.templ",
            app_instance_dir / "app.py",
            context={**context_base},
        )

        shutil.copy(app_dir / "values.yaml", app_instance_dir / "values.yaml")

        Path(app_instance_dir / "__init__.py").touch()

        logger.info(
            f'Instance "{app_instance_name}" of app "{app_name}" has been created in namespace "{namespace}" 🍰'
        )

    def is_ci_job(self) -> bool:
        return "CI_JOB_ID" in environ

    def sudo(self) -> str:
        if self.is_ci_job():
            return ""
        else:
            return "sudo"

    def _create_apps(self) -> None:
        for a in self.env.apps:
            namespace_name: str
            app_name: str
            namespace_name, app_name = a.split(".")
            if namespace_name not in self.namespaces:
                self.namespaces[namespace_name] = Namespace(name=namespace_name)

            namespace = self.namespaces[namespace_name]
            app = import_module(f"{self.env.get_name()}.{a}.app").App(
                cluster=self, namespace=namespace
            )
            namespace.add_app(app)

    def prepare_all(self) -> None:
        for n in self.namespaces.values():
            for a in n.apps.values():
                a.prepare()

    def deploy(self) -> None:
        logger.info(f'Deploying to "{self.env.stage}" 🚀')
        run("helm repo update")

        a: App
        for a in self.get_apps().values():
            a.deploy()

        logger.info(f"All done 👌")

    def add_hosts(self) -> None:
        logger.info("Adding hosts to /etc/hosts file")

    def reset(self) -> None:
        n: Namespace
        for n in reversed(self.namespaces.values()):
            if n.exists():
                n.delete()

    def install_deps(self) -> None:
        logger.opt(colors=True).info("<blue>Installing dependencies </blue>⏳")

        for d in self.deps:
            d.install()

    def bootstrap(self) -> None:
        # TODO: Disable this on prod
        self.install_deps()
        self.device.bootstrap()
        self.add_hosts()
        self.prepare_all()

        logger.info("Cluster is ready 🍰")

    def get_apps(self) -> Dict[str, App]:
        ret = {}

        n: Namespace
        for n in self.namespaces.values():
            ret.update(n.apps)

        i: Tuple[str, App]
        ret = OrderedDict(sorted(ret.items(), key=lambda i: i[1].env.deploy_priority))

        return ret
