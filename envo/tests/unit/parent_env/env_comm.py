import os
from dataclasses import dataclass
from pathlib import Path

from envo import Env, Raw


@dataclass
class ParentEnvComm(Env):
    class Meta(Env.Meta):
        root = Path(os.path.realpath(__file__)).parent
        name = "pa"

    test_parent_var: str
    path: Raw[str]

    def __init__(self) -> None:
        super().__init__()

        self.path = os.environ["PATH"]
        self.path = "/parent_bin_dir:" + self.path
