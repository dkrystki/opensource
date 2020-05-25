from dataclasses import dataclass

from opensource.comm.env_comm import CommEnvComm


@dataclass
class CommEnv(CommEnvComm):
    class Meta(CommEnvComm.Meta):
        stage = "local"
        emoji = "🐣"

    def __init__(self) -> None:
        super().__init__()


Env = CommEnv
