import os
from dataclasses import dataclass
from pathlib import Path

from envo import BaseEnv, Env


@dataclass
class RawEnvComm(Env):
    @dataclass
    class SomeEnvGroup(BaseEnv):
        class Meta:
            raw = ["nested"]

        nested: str

    class Meta:
        raw = ["not_nested"]

    not_nested: str
    group: SomeEnvGroup

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
