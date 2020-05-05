from dataclasses import dataclass

from .env_comm import CommEnvComm


@dataclass
class CommEnv(CommEnvComm):
    def __init__(self) -> None:
        self.emoji = "🐣"
        self.stage = "local"
        super().__init__()


Env = CommEnv
