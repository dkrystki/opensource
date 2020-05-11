import collections
import os
import re
import time
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import OrderedDict

from jinja2 import Template

import environ
import fire
from loguru import logger
from pangea import apps
from pangea.devops import run
from pangea.env import ClusterEnv
from pangea.kube import Namespace
from pangea.pkg_vars import package_root, templates_dir

environ = environ.Env()


__all__ = ["Cluster", "ClusterDevice", "Kind", "Microk8s"]


class ClusterDevice:
    env: ClusterEnv

    def __init__(self, env: ClusterEnv):
        self.env = env

    def bootstrap(self) -> None:
        pass

    def _post_bootstrap(self) -> None:
        logger.info("Initializing helm")
        run(
            f"""
        helm init --wait --tiller-connection-timeout 600
        kubectl apply -f {str(package_root / "k8s/ingress-rbac.yaml")}
        kubectl apply -f {str(package_root / "k8s/rbac-storage-provisioner.yaml")}
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

        logger.info("Creating kind cluster")

        template = Template((templates_dir / "kind.yaml.templ").read_text())
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
            """,
            progress_bar=True,
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


class Cluster:
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
    python: apps.PythonUtils
    system: Namespace

    def __init__(self, li: Links, se: Sets, env: ClusterEnv) -> None:
        from pangea.apps.ingress import Ingress
        from pangea.apps.registry import Registry

        self.li = li
        self.se = se
        self.env = env

        self.device = devices[self.env.device.type](self.env)

        self.namespaces = collections.OrderedDict()

        self.python = apps.PythonUtils(
            se=apps.PythonUtils.Sets(root=self.env.root), li=apps.PythonUtils.Links()
        )

        self.system = self.create_namespace("system")
        if self.se.deploy_ingress:
            self.system.create_app("ingress", Ingress)

        self.system.create_app("registry", Registry)

    @classmethod
    def handle_command(cls) -> None:
        stage = os.environ[f"ENVO_STAGE"]
        env = import_module(f"{cls.Meta.name}.env_{stage}").Env()

        current_cluster = cls(li=cls.Links(), se=cls.Sets(deploy_ingress=True), env=env)
        fire.Fire(current_cluster)

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
        logger.info("Preparing apps.")

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

        self.install_hostess()
        self.install_kubectl()
        self.install_helm()
        self.install_skaffold()
        self.install_kind()

    def install_helm(self) -> None:
        self.chdir_to_project_root()
        logger.info("Installing helm")

        if (Path(self.env.deps_dir) / "helm").exists():
            logger.info("Already exists, passing.")
            return

        release_name = f"helm-v{self.env.helm_ver}-linux-386"
        run(
            f"""
            cd /tmp
            curl -Lso helm.tar.gz https://get.helm.sh/{release_name}.tar.gz
            tar -zxf helm.tar.gz
            mv linux-386/helm {self.env.deps_dir}/helm
            """,
            progress_bar=True,
        )
        logger.info("Done")

    def install_kind(self) -> None:
        self.chdir_to_project_root()
        logger.info("Installing kind")

        if (Path(self.env.deps_dir) / "kind").exists():
            logger.info("Already exists, passing.")
            return

        run(
            f"""
            cd /tmp
            curl -Lso kind \\
                "https://github.com/kubernetes-sigs/kind/releases/download/v{self.env.kind_ver}/kind-$(uname)-amd64"
            chmod +x kind
            mv kind {self.env.deps_dir}/kind
            """,
            progress_bar=True,
        )

    def install_kubectl(self) -> None:
        self.chdir_to_project_root()
        logger.info("Installing kubectl")

        if (Path(self.env.deps_dir) / "kubectl").exists():
            logger.info("Already exists, passing.")
            return

        run(
            f"""
            cd /tmp
            curl -Lso kubectl \\
            "https://storage.googleapis.com/kubernetes-release/release/v{self.env.kubectl_ver}/bin/linux/amd64/kubectl"
            chmod +x kubectl
            mv kubectl {self.env.deps_dir}/kubectl
            """,
            progress_bar=True,
        )
        logger.info("Done")

    def install_skaffold(self) -> None:
        self.chdir_to_project_root()
        logger.info("Installing skaffold")

        if (Path(self.env.deps_dir) / "skaffold").exists():
            logger.info("Already exists, passing.")
            return

        run(
            f"""
            cd /tmp
            curl -Lso skaffold \\
                "https://storage.googleapis.com/skaffold/releases/v{self.env.skaffold_ver}/skaffold-linux-amd64"
            chmod +x skaffold
            mv skaffold {self.env.deps_dir}/skaffold
            """,
            progress_bar=True,
        )
        logger.info("Done")

    def install_hostess(self) -> None:
        self.chdir_to_project_root()
        logger.info("Installing hostess")

        if (Path(self.env.deps_dir) / "hostess").exists():
            logger.info("Already exists, passing.")
            return

        run(
            f"""
            cd /tmp
            curl -Lso hostess https://github.com/cbednarski/hostess/releases/download/v0.3.0/hostess_linux_386
            chmod u+x hostess
            mv hostess {self.env.deps_dir}/hostess
            """,
            progress_bar=True,
        )
        logger.info("Done")

    def bootstrap(self) -> None:
        # TODO: Disable this on prod
        self.chdir_to_project_root()
        logger.info(f"Bootstraping {self.env.stage} cluster")

        self.device.bootstrap()
        self.add_hosts()
        self.prepare_all()

        logger.info("Cluster is ready")
