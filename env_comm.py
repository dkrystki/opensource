import os
from dataclasses import dataclass
from pathlib import Path

from envo import Env, VenvEnv, BaseEnv


@dataclass
class OpensourceEnvComm(Env):
    class Meta:
        raw = ["path"]

    @dataclass
    class Package(BaseEnv):
        root: Path

    venv: VenvEnv
    comm: Package
    pangea: Package
    rhei: Package
    stickybeak: Package
    path: str
    bin_dir: Path

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
        self._name = "os"
        self.venv = VenvEnv(owner=self)

        self.path = self.venv.path
        self.bin_dir = self.root / ".bin"
        self.path = str(self.bin_dir) + ":" + self.path
        self.comm = self.Package(root=self.root / "comm")
        self.envo = self.Package(root=self.root / "envo")
        self.pangea = self.Package(root=self.root / "pangea")
        self.rhei = self.Package(root=self.root / "rhei")
        self.stickybeak = self.Package(root=self.root / "stickybeak")
