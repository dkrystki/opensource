from dataclasses import dataclass

from opensource.env_comm import OpensourceEnvComm


@dataclass
class OpensourceEnv(OpensourceEnvComm):
    class Meta(OpensourceEnvComm.Meta):
        stage = "local"
        emoji = "🐣"

    def __init__(self) -> None:
        super().__init__()


Env = OpensourceEnv
