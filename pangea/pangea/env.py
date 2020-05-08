import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import envo


@dataclass
class AppEnv(envo.Env):
    class Meta:
        raw: List[str] = ["path", "pythonpath"]

    venv: envo.VenvEnv
    app_name: str
    bin_path: Path
    comm: Path
    prebuild: bool
    path: str
    pythonpath: str

    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.comm = self.root / "comm"
        self.bin_path = self.root / Path(".bin")

        self.path = os.environ["PATH"]
        self.path = f"{str(self.bin_path)}:{self.path}"

        self.pythonpath = f"{str(self.root)}/comm/python"
        self.pythonpath = f"{str(self.root.parent)}:{self.pythonpath}"

        self.venv = envo.VenvEnv(owner=self)


@dataclass
class ClusterEnv(envo.Env):
    @dataclass
    class Device(envo.BaseEnv):
        type: str
        k8s_ver: str
        name: str

    @dataclass
    class Registry(envo.BaseEnv):
        address: str
        username: str
        password: str

    class Meta:
        raw: List[str] = ["path", "pythonpath", "kubeconfig"]

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

    def __init__(self, root: Path):
        super().__init__(root)

        self.deps_dir = self.root / Path(".deps")
        self.bin_dir = self.root / Path(".bin")
        self.kubeconfig = self.root / f"envs/{self.stage}/kubeconfig.yaml"
        self.comm = self.root / "comm"

        self.path = os.environ["PATH"]
        self.path = f"{str(self.deps_dir)}:{self.path}"
        self.path = f"{str(self.bin_dir)}:{self.path}"

        self.pythonpath = f"{str(self.comm)}/python"
