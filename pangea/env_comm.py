import os
from dataclasses import dataclass
from pathlib import Path

from envo import Env, VenvEnv


@dataclass
class PangeaEnvComm(Env):
    class Meta(Env.Meta):
        root = Path(os.path.realpath(__file__)).parent
        name = "pangea"

    venv: VenvEnv

    def __init__(self) -> None:
        super().__init__()
        self.venv = VenvEnv(owner=self)
