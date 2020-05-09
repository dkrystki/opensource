from dataclasses import dataclass

from opensource.comm.env_comm import CommEnvComm
from opensource.env_local import OpensourceEnv


@dataclass
class CommEnv(CommEnvComm):
    def __init__(self) -> None:
        self.emoji = "🐣"
        self.stage = "local"
        super().__init__()

        self.parent = OpensourceEnv()


Env = CommEnv
