import os
from dataclasses import dataclass
from pathlib import Path

from envo import Env


@dataclass
class ParentEnvComm(Env):
    test_parent_var: str

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent, name="pa")
