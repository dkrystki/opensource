import os
from dataclasses import dataclass

from envo import Env, Path, VenvEnv


@dataclass
class PangeaEnvComm(Env):
    class Meta:
        raw = ["pythonpath"]

    venv: VenvEnv
    pythonpath: str

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
        self._name = "pangea"
        self.venv = VenvEnv(owner=self)

        self.pythonpath = str(self.root.parent)
