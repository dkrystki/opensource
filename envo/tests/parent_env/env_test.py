from dataclasses import dataclass

from parent_env.env_comm import ParentEnvComm


@dataclass
class ParentEnv(ParentEnvComm):
    def __init__(self) -> None:
        self.stage = "test"
        self.emoji = "🛠️"

        super().__init__()

        self.test_parent_var = "test_value"


Env = ParentEnv
