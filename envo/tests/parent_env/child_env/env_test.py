from dataclasses import dataclass

from parent_env.child_env.env_comm import ChildEnvComm
from parent_env.env_test import ParentEnv


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
