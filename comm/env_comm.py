import os
from dataclasses import dataclass

from envo import Env, Parent, Path, Raw, VenvEnv
from opensource.env_comm import OpensourceEnvComm


@dataclass
class CommEnvComm(Env):
    venv: VenvEnv
    pythonpath: Raw[str]
    bin_dir: Path
    path: Raw[str]
    parent: Parent[OpensourceEnvComm]

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
        self._name = "comm"
        self.venv = VenvEnv(owner=self)

        self.bin_dir = self.root / ".bin"

        self.path = self.venv.path
        self.path = str(self.bin_dir) + ":" + self.path

        self.pythonpath = str(self.root)
