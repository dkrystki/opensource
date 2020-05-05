import os
from dataclasses import dataclass
from pathlib import Path

from envo import Env, VenvEnv, BaseEnv


@dataclass
class OpensourceEnvComm(Env):
    venv: VenvEnv

    @dataclass
    class Package(BaseEnv):
        root: Path

    comm: Package
    pangea: Package
    rhei: Package
    stickybeak: Package

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
        self._name = "os"
        self.venv = VenvEnv(owner=self)

        self.comm = self.Package(root=self.root / "comm")
        self.envo = self.Package(root=self.root / "envo")
        self.pangea = self.Package(root=self.root / "pangea")
        self.rhei = self.Package(root=self.root / "rhei")
        self.stickybeak = self.Package(root=self.root / "stickybeak")
