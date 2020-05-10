from dataclasses import dataclass

from opensource.comm.env_comm import CommEnvComm
from opensource.env_local import OpensourceEnv


@dataclass
class CommEnv(CommEnvComm):
    class Meta(CommEnvComm.Meta):
        stage = "local"
        emoji = "🐣"
        parent = OpensourceEnv()

    def __init__(self) -> None:
        super().__init__()


Env = CommEnv
