import os
from dataclasses import dataclass
from pathlib import Path

from envo import Env, Parent

from ..env_comm import ParentEnvComm


@dataclass
class ChildEnvComm(Env):
    child_env: Parent[ParentEnvComm]

    parent: ParentEnvComm

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent, name="ch")
