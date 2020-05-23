import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from envo import BaseEnv, Env, Raw


@dataclass
class ClusterEnv(Env):
    @dataclass
    class Device(BaseEnv):
        type: str
        k8s_ver: str
        name: str

    @dataclass
    class Registry(BaseEnv):
        address: str
        username: str
        password: str

    @dataclass
    class Deps(BaseEnv):
        skaffold_ver: str
        kubectl_ver: str
        helm_ver: str
        kind_ver: str
        hostess_ver: str
        debian_ver: str
        docker_ver: str
        dns_server_ver: str

    class Meta(Env.Meta):
        pass

    device: Device
    registry: Registry
    deps_dir: Path
    bin_dir: Path

    comm: Path
    path: Raw[str]
    kubeconfig: Raw[Path]
    pythonpath: Raw[str]
    apps: List[str]

    deps: Deps

    def __init__(self):
        super().__init__()

        self.deps_dir = self.root / Path(".deps")
        self.bin_dir = self.root / Path(".bin")
        self.kubeconfig = self.root / f"envs/{self.stage}/kubeconfig.yaml"
        self.comm = self.root / "comm"

        self.path = os.environ["PATH"]
        self.path = f"{str(self.deps_dir)}:{self.path}"
        self.path = f"{str(self.bin_dir)}:{self.path}"

        self.pythonpath = str(self.meta.root.parent.absolute())

        self.apps = ["system.ingress"]
