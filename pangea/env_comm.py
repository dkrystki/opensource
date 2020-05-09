import os
from dataclasses import dataclass

from envo import Env, Parent, Path, VenvEnv
from opensource.env_comm import OpensourceEnvComm


@dataclass
class PangeaEnvComm(Env):
    venv: VenvEnv
    parent: Parent[OpensourceEnvComm]

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
        self._name = "pangea"
        self.venv = VenvEnv(owner=self)
