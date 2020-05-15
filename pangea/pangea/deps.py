import collections
import os
import re
import shutil
import time
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import List, OrderedDict

from jinja2 import Template
from loguru import logger

import environ
import fire
from pangea import apps, pkg_vars
from pangea.devops import run
from pangea.env import ClusterEnv
from pangea.kube import Namespace

environ = environ.Env()


__all__ = ["Cluster", "ClusterDevice", "Kind", "Microk8s"]


class ClusterDevice:
    env: ClusterEnv

    def __init__(self, env: ClusterEnv):
        self.env = env

    def bootstrap(self) -> None:
        pass

    def _post_bootstrap(self) -> None:
        logger.info("Initializing helm ⏳")
        run(
            f"""
        helm init --wait --tiller-connection-timeout 600
        kubectl apply -f {str(pkg_vars.package_root / "k8s/ingress-rbac.yaml")}
        kubectl apply -f {str(pkg_vars.package_root / "k8s/rbac-storage-provisioner.yaml")}
        kubectl create serviceaccount -n kube-system tiller
        kubectl create clusterrolebinding tiller-cluster-admin \\
            --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
        kubectl --namespace kube-system patch deploy tiller-deploy -p \\
            '{{"spec":{{"template":{{"spec":{{"serviceAccount":"tiller"}} }} }} }}'
        """,
            progress_bar=True,
        )

    def get_ip(self) -> str:
        raise NotImplementedError()


class Kind(ClusterDevice):
    def __init__(self, env: ClusterEnv):
        super().__init__(env)

    def bootstrap(self) -> None:
        super().bootstrap()

        logger.info("Creating kind cluster ⏳")

        template = Template((pkg_vars.templates_dir / "kind.yaml.templ").read_text())
        kind_file = Path(f"kind.{self.env.stage}.yaml")
        context = {"env": self.env}
        kind_file.write_text(template.render(**context))

        Path(environ.str("KUBECONFIG")).unlink(missing_ok=True)
        run(
            f"""
            kind delete cluster --name={self.env.device.name}
            kind create cluster --config={str(kind_file)} --name={self.env.device.name}
            """,
            progress_bar=True,
        )

        ip = self.get_ip()

        run(
            f"""
            docker exec {self.env.device.name}-control-plane bash -c "echo \\"{ip} \\
            {self.env.registry.address}\\" >> /etc/hosts"
            # For some reason dns resolution doesn't work on CI. This line fixes it
            docker exec {self.env.device.name}-control-plane \\
            bash -c "echo \\"nameserver 8.8.8.8\\" >> /etc/resolv.conf"
            """
        )

        self._post_bootstrap()

    def get_ip(self) -> str:
        result = run(f"""kubectl describe nodes {self.env.device.name}""")
        ip_phrase = re.search(r"InternalIP: .*", "\n".join(result)).group(0)
        ip = ip_phrase.split(":")[1].strip()
        return ip.strip()


class Microk8s(ClusterDevice):
    def __init__(self, env: ClusterEnv):
        super().__init__(env)

    def bootstrap(self) -> None:
        super().bootstrap()

        logger.info("Creating microk8s cluster")

        self.env.kubeconfig.unlink(missing_ok=True)
        run(
            f"""
        sudo snap remove microk8s
        sudo snap install microk8s --classic --channel="{self.env.device.k8s_ver}"/stable
        sudo sed -i "s/local.insecure-registry.io/{self.env.registry.address}/g" \\
            /var/snap/microk8s/current/args/containerd-template.toml
        sudo sed -i "s/http:\/\/localhost:32000/http:\/\/{self.env.registry.address}/g" \\
            /var/snap/microk8s/current/args/containerd-template.toml
        sudo microk8s.start

        mkdir -p "$(dirname "$KUBECONFIG")"
        sudo microk8s.config > "$KUBECONFIG"

        sudo microk8s.enable dns
        sudo microk8s.enable rbac
        sudo microk8s.enable storage
        sudo microk8s.enable ingress

        sudo sh -c 'echo "--allow-privileged=true" >> /var/snap/microk8s/current/args/kube-apiserver'
        sudo systemctl restart snap.microk8s.daemon-apiserver.service
        """,
            progress_bar=True,
        )

        time.sleep(30)

        self._post_bootstrap()

    def get_ip(self) -> str:
        return "127.0.0.1"


class AwsCluster(ClusterDevice):
    def bootstrap(self) -> None:
        logger.info("Creating aws cluster")

        self.env.kubeconfig.unlink(missing_ok=True)

        run(f"eksctl delete cluster=--name {self.env.device.name}", ignore_errors=True)
        run(
            f"""
        eksctl create cluster --name={self.env.device.name} --region=ap-southeast-1 --nodegroup-name=standard-workers \\
        --node-type=t3.medium --nodes=1 --nodes-min=1 --nodes-max=1 --ssh-access \\
        --version={self.env.device.k8s_ver[:-2]} \\
         --ssh-public-key=~/.ssh/id_rsa.pub --managed
        eksctl utils write-kubeconfig --cluster={self.env.device.name} --kubeconfig={str(self.env.kubeconfig)}
        """,
            print_output=True,
        )

        self._post_bootstrap()

    def get_ip(self) -> str:
        result = run(f"""kubectl describe nodes""")
        ip_phrase = re.search(r"ExternalIP: .*", "\n".join(result)).group(0)
        ip = ip_phrase.split(":")[1].strip()
        return ip.strip()


devices = {"kind": Kind, "aws": AwsCluster, "microk8s": Microk8s}


class Dependency:
    @dataclass
    class Sets:
        deps_dir: Path
        version: str

    name: str

    def __init__(self, se: Sets) -> None:
        self.se = se

    def install(self) -> None:
        if self.exists():
            logger.opt(colors=True).info(f"<green>{self.name} already exists 👌</green>")
        else:
            logger.info(f"Installing {self.name} ⏳")

    def exists(self) -> bool:
        if (Path(self.se.deps_dir) / self.name).exists():
            return True
        else:
            return False


class Kubectl(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "kubectl"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        run(
            f"""
            cd /tmp
            curl -Lso kubectl \\
            "https://storage.googleapis.com/kubernetes-release/release/v{self.se.version}/bin/linux/amd64/kubectl"
            chmod +x kubectl
            mv kubectl {self.se.deps_dir}/kubectl
            """
        )


class Hostess(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "hostess"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        run(
            f"""
            cd /tmp
            curl -Lso hostess https://github.com/cbednarski/hostess/releases/download/v{self.se.version}/hostess_linux_386
            chmod u+x hostess
            mv hostess {self.se.deps_dir}/hostess
            """
        )


class Helm(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "helm"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        release_name = f"helm-v{self.se.version}-linux-386"
        run(
            f"""
            cd /tmp
            curl -Lso helm.tar.gz https://get.helm.sh/{release_name}.tar.gz
            tar -zxf helm.tar.gz
            mv linux-386/helm {self.se.deps_dir}/helm
            """
        )


class Skaffold(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "skaffold"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        run(
            f"""
            cd /tmp
            curl -Lso skaffold \\
                "https://storage.googleapis.com/skaffold/releases/v{self.se.version}/skaffold-linux-amd64"
            chmod +x skaffold
            mv skaffold {self.se.deps_dir}/skaffold
            """
        )


class Kind(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "kind"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        run(
            f"""
            cd /tmp
            curl -Lso kind \\
                "https://github.com/kubernetes-sigs/kind/releases/download/v{self.se.version}/kind-$(uname)-amd64"
            chmod +x kind
            mv kind {self.se.deps_dir}/kind
            """
        )


class Cluster:
    class ClusterException(Exception):
        pass

    class Meta:
        name: str

    @dataclass
    class Links:
        pass

    @dataclass
    class Sets:
        deploy_ingress: bool = True

    device: ClusterDevice
    li: Links
    se: Sets
    senv: ClusterEnv
    namespaces: OrderedDict[str, Namespace]
    deps: List[Dependency]
    python: apps.PythonUtils
    system: Namespace

    def __init__(self, li: Links, se: Sets, env: ClusterEnv) -> None:
        from pangea.apps.ingress import Ingress
        from pangea.apps.registry import Registry

        self.li = li
        self.se = se
        self.env = env

        self.device = devices[self.env.device.type](self.env)

        self.deps = [
            Kubectl(
                Kubectl.Sets(deps_dir=self.env.deps_dir, version=self.env.kubectl_ver)
            ),
            Kind(Kind.Sets(deps_dir=self.env.deps_dir, version=self.env.kind_ver)),
            Skaffold(
                Skaffold.Sets(deps_dir=self.env.deps_dir, version=self.env.skaffold_ver)
            ),
            Hostess(
                Hostess.Sets(deps_dir=self.env.deps_dir, version=self.env.hostess_ver)
            ),
            Helm(Helm.Sets(deps_dir=self.env.deps_dir, version=self.env.helm_ver)),
        ]

        self.namespaces = collections.OrderedDict()

        self.python = apps.PythonUtils(
            se=apps.PythonUtils.Sets(root=self.env.root), li=apps.PythonUtils.Links()
        )

        self.system = self.create_namespace("system")
        if self.se.deploy_ingress:
            self.system.add_app("ingress", Ingress)

        self.system.add_app("registry", Registry)

    @classmethod
    def handle_command(cls) -> None:
        stage = os.environ[f"ENVO_STAGE"]
        env = import_module(f"{cls.Meta.name}.env_{stage}").Env()

        current_cluster = cls(li=cls.Links(), se=cls.Sets(deploy_ingress=True), env=env)
        try:
            fire.Fire(current_cluster)
        except Cluster.ClusterException as exc:
            logger.error(exc)

    def createapp(self, app_name: str, app_instance_name: str) -> None:
        app_dir = pkg_vars.apps_dir / app_name
        if not app_dir.exists():
            raise self.ClusterException(f'App "{app_name}" does not exist 😓')

        app_instance_dir = Path(app_instance_name)

        if app_instance_dir.exists():
            raise self.ClusterException(
                f'App instance "{app_instance_dir}" already exists 😓'
            )

        shutil.copytree(str(app_dir), str(app_instance_dir))
        logger.info(
            f'App instance "{app_instance_name}" of app "{app_name}" has been created 🍰'
        )

    def is_ci_job(self) -> bool:
        return "CI_JOB_ID" in environ

    def sudo(self) -> str:
        if self.is_ci_job():
            return ""
        else:
            return "sudo"

    def chdir_to_project_root(self) -> None:
        os.chdir(str(self.env.root))

    def create_namespace(self, name) -> Namespace:
        namespace = Namespace(li=Namespace.Links(env=self.env,), name=name)
        self.namespaces[name] = namespace
        return namespace

    def prepare_all(self) -> None:
        for n in self.namespaces.values():
            for a in n.apps.values():
                a.prepare()

    def deploy(self) -> None:
        self.chdir_to_project_root()
        run("helm repo update")

        self.system.deploy()

        n: Namespace
        for n in self.namespaces.values():
            if n.name == "system":
                continue

            n.deploy()

    def add_hosts(self) -> None:
        logger.info("Adding hosts to /etc/hosts file")

    def reset(self) -> None:
        self.chdir_to_project_root()

        n: Namespace
        for n in reversed(self.namespaces.values()):
            if n.exists():
                n.delete()

    def install_deps(self) -> None:
        self.chdir_to_project_root()

        logger.opt(colors=True).info("<blue>Installing dependencies </blue>⏳")

        for d in self.deps:
            d.install()

    def bootstrap(self) -> None:
        # TODO: Disable this on prod
        self.chdir_to_project_root()
        self.install_deps()
        self.device.bootstrap()
        self.add_hosts()
        self.prepare_all()

        logger.info("Cluster is ready 🍰")
