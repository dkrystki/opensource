from dataclasses import dataclass

from .env_comm import ChildEnvComm


@dataclass
class ChildEnv(ChildEnvComm):
    def __init__(self) -> None:
        self.stage = "test"
        self.emoji = "🛠️"

        super().__init__()

        self.child_env = "test_child_value"


Env = ChildEnv
