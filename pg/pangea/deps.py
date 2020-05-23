import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from loguru import logger

import docker
import docker.types
from pangea import pkg_vars
from pangea.devops import run

__all__ = ["Dependency", "Kubectl", "Hostess", "Skaffold", "Helm", "Kind"]


class Dependency:
    @dataclass
    class Sets:
        version: str
        deps_dir: Path

    name: str

    def __init__(self, se: Sets) -> None:
        self.se = se

    def install(self) -> None:
        if self.exists():
            logger.opt(colors=True).info(f"<green>{self.name} already exists 👌</green>")
        else:
            logger.info(f"Installing {self.name} ⏳")

    def exists(self) -> bool:
        raise NotImplementedError

    def uninstall(self) -> None:
        raise NotImplementedError


class BinaryDep(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se
        self.bin_file = self.se.deps_dir / self.name

    def exists(self) -> bool:
        return self.bin_file.exists()

    def uninstall(self) -> None:
        self.bin_file.unlink()


class DockerDep(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    image_name: str

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se
        self.docker = docker.from_env()

        self.image_full_name = f"{self.image_name}:{self.se.version}"

        # tarball for caching
        self.tar_file = Path(self.se.deps_dir) / "dns_server.tar"

    def image_exists(self) -> bool:
        return self.docker.images.list(name=self.image_full_name) != []

    def exists(self) -> bool:
        return self.tar_file.exists()

    def install(self) -> None:
        super().install()

        if self.exists():
            if not self.image_exists():
                self.docker.images.load(self.tar_file.read_bytes())
            return
        else:
            if not self.image_exists():
                image = self.docker.images.pull(
                    repository=self.image_name, tag=self.se.version
                )
            else:
                image = self.docker.images.list(name=self.image_full_name)[0]

            self.tar_file.touch(exist_ok=True)

            tar_chunks = []
            for c in image.save():
                tar_chunks.append(c)

            self.tar_file.write_bytes(b"".join(tar_chunks))

    def uninstall(self) -> None:
        if not self.exists():
            raise RuntimeError(f"{self.name} already uninstalled")

        self.docker.images.remove(image=self.image_full_name)
        self.tar_file.unlink(missing_ok=True)


class Kubectl(BinaryDep):
    @dataclass
    class Sets(BinaryDep.Sets):
        deps_dir: Path

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
            mv kubectl {str(self.bin_file)}
            """
        )


class Hostess(BinaryDep):
    @dataclass
    class Sets(BinaryDep.Sets):
        deps_dir: Path

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
            mv hostess {self.se.deps_dir}/{self.name}
            """
        )


class Helm(BinaryDep):
    @dataclass
    class Sets(BinaryDep.Sets):
        deps_dir: Path

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
            mv linux-386/helm {str(self.bin_file)}
            """
        )


class Skaffold(BinaryDep):
    @dataclass
    class Sets(BinaryDep.Sets):
        deps_dir: Path

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
            mv skaffold {str(self.bin_file)}
            """
        )


class Kind(BinaryDep):
    @dataclass
    class Sets(BinaryDep.Sets):
        deps_dir: Path

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
            mv kind {str(self.bin_file)}
            """
        )


class DnsServer(DockerDep):
    @dataclass
    class Sets(DockerDep.Sets):
        pass

    name = "dns_server"
    container_name = "pangea_dns_server"
    image_name = "defreitas/dns-proxy-server"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

        self.dot_dir = Path.home() / ".pangea"
        self.dot_dir.mkdir(exist_ok=True)

        self.conf_dir = self.dot_dir / "conf"
        self.conf_dir.mkdir(exist_ok=True)

        self.conf_file = self.conf_dir / "config.json"

        if not self.conf_file.exists():
            shutil.copy(
                str(pkg_vars.templates_dir / "dns_server_config.json"),
                str(self.conf_file),
            )

    def is_running(self) -> bool:
        return (
            self.docker.containers.list(filters={"name": self.container_name}, all=True)
            != []
        )

    def start(self) -> None:
        self._wait_until_not_running()

        self.docker.containers.run(
            image=self.image_full_name,
            hostname="dns.pangea",
            detach=True,
            volumes={
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"},
                "/etc/resolv.conf": {"bind": "/etc/resolv.conf", "mode": "rw"},
                str(self.conf_dir): {"bind": "/app/conf", "mode": "rw"},
            },
            name=self.container_name,
            auto_remove=True,
        )

        time.sleep(2)
        if not self.is_running():
            raise RuntimeError("Dns server has crashed.!")

    def stop(self) -> None:
        self.docker.containers.get(self.container_name).stop()
        self._wait_until_not_running()

    def restart(self) -> None:
        if self.is_running():
            self.stop()

        self.start()

    def get_hosts(self) -> Dict[str, str]:
        """
        :return: Dict[hostname, ip]
        """
        content = json.loads(self.conf_file.read_text())

        hosts_raw = content["envs"][0]["hostnames"]

        hosts = {}
        for h in hosts_raw:
            hosts[h["hostname"]] = h["ip"]

        return hosts

    def update_hosts(self, hosts: Dict[str, str]) -> None:
        """
        :param hosts:
        """
        content = json.loads(self.conf_file.read_text())

        payload = []
        for i, (k, v) in enumerate(hosts.items()):
            payload.append(
                {"id": i + 1, "ttl": 100000000, "hostname": k, "ip": v,}
            )

        content["envs"][0]["hostnames"] = payload

        self.conf_file.write_text(json.dumps(content, indent=4, sort_keys=True))

        if self.is_running():
            self.restart()

    def _wait_until_not_running(self):
        for i in range(5):
            time.sleep(0.5)
            if not self.is_running():
                return
        else:
            raise RuntimeError("Timeout waiting for dns_server to stop!")
