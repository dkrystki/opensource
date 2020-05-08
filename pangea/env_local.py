from dataclasses import dataclass

from .env_comm import PangeaEnvComm


@dataclass
class PangeaEnv(PangeaEnvComm):
    def __init__(self) -> None:
        self.emoji = "🐣"
        self.stage = "local"
        super().__init__()


Env = PangeaEnv
