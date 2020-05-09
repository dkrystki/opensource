from dataclasses import dataclass

from parent_env.child_env.env_comm import ChildEnvComm
from parent_env.env_test import ParentEnv


@dataclass
class ChildEnv(ChildEnvComm):
    def __init__(self) -> None:
        self.stage = "test"
        self.emoji = "🛠"

        super().__init__()

        self.test_var = "test_var_value"
        self.parent = ParentEnv()


Env = ChildEnv
