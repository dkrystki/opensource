from dataclasses import dataclass

from ..env_test import ParentEnv
from .env_comm import ChildEnvComm


@dataclass
class ChildEnv(ChildEnvComm):
    class Meta(ChildEnvComm.Meta):
        stage = "test"
        parent = ParentEnv()
        emoji = "🛠"

    def __init__(self) -> None:
        super().__init__()
        self.test_var = "test_var_value"


Env = ChildEnv
