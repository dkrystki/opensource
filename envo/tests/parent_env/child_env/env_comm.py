import os
from dataclasses import dataclass
from pathlib import Path

from envo import Env, Raw


@dataclass
class ChildEnvComm(Env):
    class Meta(Env.Meta):
        root = Path(os.path.realpath(__file__)).parent
        name = "ch"

    test_var: str
    path: Raw[str]

    def __init__(self) -> None:
        super().__init__()

        self.path = os.environ["PATH"]
        self.path = "/child_bin_dir:" + self.path
