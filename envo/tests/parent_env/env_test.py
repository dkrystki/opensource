from dataclasses import dataclass

from .env_comm import ParentEnvComm


@dataclass
class RawEnv(ParentEnvComm):
    def __init__(self) -> None:
        self.stage = "test"
        self.emoji = "🛠️"

        super().__init__()

        self.test_parent_var = "test_value"


Env = RawEnv
