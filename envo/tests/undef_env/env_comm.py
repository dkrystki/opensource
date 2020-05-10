import os
from dataclasses import dataclass
from pathlib import Path

from envo import BaseEnv, Env


@dataclass
class UndefEnvComm(Env):
    class Meta(Env.Meta):
        root = Path(os.path.realpath(__file__)).parent
        name = "undef_env"

    @dataclass
    class Python(BaseEnv):
        version: str

    python: Python

    def __init__(self) -> None:
        super().__init__()
