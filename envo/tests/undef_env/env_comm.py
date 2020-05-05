import os
from dataclasses import dataclass
from pathlib import Path

from envo import BaseEnv, Env


@dataclass
class UndefEnvComm(Env):
    @dataclass
    class Python(BaseEnv):
        version: str

    python: Python

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
