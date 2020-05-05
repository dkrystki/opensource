import os
from dataclasses import dataclass

from envo import Env, Path, VenvEnv


@dataclass
class CommEnvComm(Env):
    class Meta:
        raw = ["pythonpath"]

    venv: VenvEnv
    pythonpath: str

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
        self.name = "comm"
        self.venv = VenvEnv(owner=self)

        self.pythonpath = str(self.root)
