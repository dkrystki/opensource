import os
from dataclasses import dataclass

from envo import Env, Path, VenvEnv


@dataclass
class CommEnvComm(Env):
    class Meta:
        raw = ["pythonpath", "path"]

    venv: VenvEnv
    pythonpath: str
    bin_dir: Path
    path: str

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
        self._name = "comm"
        self.venv = VenvEnv(owner=self)

        self.bin_dir = self.root / ".bin"

        self.path = self.venv.path
        self.path = str(self.bin_dir) + ":" + self.path

        self.pythonpath = str(self.root)
