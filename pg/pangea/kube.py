import typing
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING, Tuple

from loguru import logger

import environ
from pangea.devops import CommandError, run

if TYPE_CHECKING:
    from pangea.apps import App

environ = environ.Env()


class Kube:
    class Namespace:
        @classmethod
        def list(cls) -> List[str]:
            raw = run("kubectl get namespaces")[1:]
            # skip header
            ret = []
            for r in list(raw):
                ret.append(r.split()[0])
            return ret

        @classmethod
        def create(cls, name: str) -> None:
            run(f"kubectl create {name}")


class HelmRelease:
    """Representation of namespaced helm commands."""

    @dataclass
    class Links:
        namespace: "Namespace"

    def __init__(self, li: Links, release_name: str) -> None:
        self.li: HelmRelease.Links = li
        self.release_name = release_name
        self.namespaced_name = f"""{self.li.namespace.name + "-" if self.li.namespace.name else ""}{release_name}"""

    def install(
        self,
        chart: str,
        values: Path,
        version: Optional[str] = None,
        upgrade: bool = True,
        repo: str = "",
    ) -> None:
        """
        :param repo:
        :param stage:
        :param chart: chart repository name
        :param version: install default if None
        :param upgrade: Try to upgrade when True. Delete and install when False.
        """
        if not upgrade:
            try:
                run(f"""helm delete --purge {self.namespaced_name}""")
            except RuntimeError:
                pass

        if repo:
            run(f"helm repo add {repo}")

        run(
            f"""helm {"upgrade --install" if upgrade else "install"} \
                {"" if upgrade else "--name"} {self.namespaced_name} \
                --namespace={self.li.namespace.name} \
                --set fullnameOverride={self.release_name} \
                -f {str(values)} \
                {"--force" if upgrade else ""} --wait=true \
                --timeout=250000 \
                "{chart}" \
                {f"--version='{version}'"} \
            """
        )

    def delete(self) -> None:
        logger.info(f"Deleting {self.namespaced_name}")
        run(f"helm delete --purge {self.namespaced_name}")

    def exists(self) -> bool:
        try:
            run(f"helm ls | grep {self.namespaced_name}")
        except CommandError:
            return False
        else:
            return True


class Pod:
    @dataclass
    class Sets:
        name: str

    @dataclass
    class Links:
        app: "App"

    def __init__(self, se: Sets, li: Links):
        self.se = se
        self.li = li

    def exec(self, command: str, print_output: bool = False) -> List[str]:
        return self.li.app.li.namespace.exec(
            pod=self.se.name, command=command, print_output=print_output
        )

    def copy_from_pod(self, src_path: str, dst_path: str) -> None:
        return self.li.app.li.namespace.copy(
            src_path=f"{self.se.name}:{src_path}", dst_path=dst_path
        )

    def copy_to_pod(self, src_path: str, dst_path: str) -> None:
        return self.li.app.li.namespace.copy(
            src_path=src_path, dst_path=f"{self.se.name}:{dst_path}"
        )


class Namespace:
    apps: typing.OrderedDict[str, "App"]

    def __init__(self, name: str) -> None:
        self.name = name
        self.apps = OrderedDict()

    def add_app(self, app: "App") -> None:
        self.apps[app.env.get_name()] = app
        i: Tuple[str, App]
        self.apps = OrderedDict(
            sorted(self.apps.items(), key=lambda i: i[1].env.deploy_priority)
        )

    def exists(self) -> bool:
        return self.name in Kube.Namespace.list()

    def deploy_app(self, app_name: str) -> None:
        self.create()
        self.apps[app_name].deploy()

    def delete(self) -> None:
        logger.info(f"Deleting namespace {self.name}")
        run(f"kubectl delete namespace {self.name}")

    def kubectl(self, command: str, print_output: bool = False) -> List[str]:
        return run(f"kubectl -n {self.name} {command}", print_output=print_output)

    def exec(self, pod: str, command: str, print_output: bool = False) -> List[str]:
        return self.kubectl(
            f'exec {pod} -- bash -c "{command}"', print_output=print_output
        )

    def apply_yaml(self, filename: str) -> None:
        self.kubectl(f"apply -f {filename}")

    def delete_yaml(self, filename: str) -> None:
        """
        Delete object specified in a yaml file.

        :param filename: yaml file
        :return:
        """
        self.kubectl(f"delete -f k8s/{filename}")

    def copy(self, src_path: str, dst_path: str) -> None:
        self.kubectl(f"cp {src_path} {dst_path}")

    def get_pods(self) -> List[str]:
        return [
            p.metadata.name for p in self.li.kube.list_namespaced_pod(self.name).items
        ]

    def wait_for_pod(self, pod_name: str, timeout: int = 20) -> None:
        """
        :param pod_name:
        :param timeout: Timeout in seconds
        :return:
        """
        self.kubectl(f"wait --for=condition=ready pod {pod_name} --timeout={timeout}s")

    def _add_pullsecret(self) -> None:
        env = self.li.env
        logger.info(f"🚀Adding pull secret to {self.name}")
        self.kubectl(
            "create secret docker-registry pullsecret "
            f"--docker-server={env.registry.address} --docker-username={env.registry.username} "
            f"--docker-password={env.registry.password} --dry-run -o yaml | kubectl apply -f -"
        )

    def create(self, enable_istio: bool = True, add_pull_secret: bool = True) -> None:
        """
        Create namespace if doesn't exist.
        :param enable_istio:
        :param add_pull_secret:
        :return:
        """
        if self.name not in Kube.Namespace.list():
            Kube.Namespace.create(name=self.name)

        if enable_istio:
            run(
                f"kubectl label namespace {self.name} istio-injection=enabled --overwrite"
            )

        if add_pull_secret:
            self._add_pullsecret()

    def helm(self, release_name: str) -> HelmRelease:
        """
        Helm factory for a given release.

        :param release_name:
        :return:
        """
        return HelmRelease(
            li=HelmRelease.Links(namespace=self), release_name=release_name,
        )
