import os
from dataclasses import dataclass
from pathlib import Path

from envo import BaseEnv, Env, Raw, VenvEnv


@dataclass
class AppEnv(Env):
    class Meta(Env.Meta):
        pass

    venv: VenvEnv
    app_name: str
    bin_path: Path
    comm: Path
    prebuild: bool
    path: str
    pythonpath: Raw[str]

    def __init__(self) -> None:
        super().__init__()
        self.comm = self.root / "comm"
        self.bin_path = self.root / Path(".bin")

        self.path = os.environ["PATH"]
        self.path = f"{str(self.bin_path)}:{self.path}"

        self.pythonpath = f"{str(self.root)}/comm/python"
        self.pythonpath = f"{str(self.root.parent)}:{self.pythonpath}"

        self.venv = VenvEnv(owner=self)


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

    class Meta(Env.Meta):
        pass

    skaffold_ver: str
    kubectl_ver: str
    helm_ver: str
    kind_ver: str
    debian_ver: str
    docker_ver: str
    device: Device
    registry: Registry
    deps_dir: Path
    bin_dir: Path

    comm: Path
    kubeconfig: Path

    def __init__(self):
        super().__init__()

        self.deps_dir = self.root / Path(".deps")
        self.bin_dir = self.root / Path(".bin")
        self.kubeconfig = self.root / f"envs/{self.stage}/kubeconfig.yaml"
        self.comm = self.root / "comm"

        self.path = os.environ["PATH"]
        self.path = f"{str(self.deps_dir)}:{self.path}"
        self.path = f"{str(self.bin_dir)}:{self.path}"

        self.pythonpath = f"{str(self.comm)}/python"
