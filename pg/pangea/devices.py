import re
import time
from pathlib import Path

from jinja2 import Template
from loguru import logger

import environ
from pangea import pkg_vars
from pangea.devops import run
from pangea.env import ClusterEnv

environ = environ.Env()


__all__ = ["ClusterDevice", "Kind", "Microk8s", "Aws", "all"]


class ClusterDevice:
    env: ClusterEnv

    def __init__(self, env: ClusterEnv):
        self.env = env

    def bootstrap(self) -> None:
        pass

    def _post_bootstrap(self) -> None:
        pass

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


class Aws(ClusterDevice):
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


all = {"kind": Kind, "aws": Aws, "microk8s": Microk8s}
