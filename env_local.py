from dataclasses import dataclass

from .env_comm import OpensourceEnvComm


@dataclass
class OpensourceEnv(OpensourceEnvComm):
    def __init__(self) -> None:
        self.emoji = "🐣"
        self.stage = "local"
        super().__init__()


Env = OpensourceEnv