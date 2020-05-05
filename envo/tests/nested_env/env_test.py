from dataclasses import dataclass

from .env_comm import NestedEnvComm


@dataclass
class NestedEnv(NestedEnvComm):
    def __init__(self) -> None:
        self.stage = "test"
        super().__init__()
        self.emoji = "🛠️"

        self.python = self.Python(version="3.8.2")


Env = NestedEnv
