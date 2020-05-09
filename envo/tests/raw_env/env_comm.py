import os
from dataclasses import dataclass
from pathlib import Path

from envo import BaseEnv, Env, Raw


@dataclass
class RawEnvComm(Env):
    @dataclass
    class SomeEnvGroup(BaseEnv):
        nested: Raw[str]

    not_nested: Raw[str]
    group: SomeEnvGroup

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
