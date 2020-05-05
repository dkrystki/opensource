from dataclasses import dataclass

from .env_comm import UndefEnvComm


@dataclass
class UndefEnv(UndefEnvComm):
    def __init__(self) -> None:
        self.stage = "test"
        super().__init__()
        self.emoji = "🛠️"


Env = UndefEnv
