from dataclasses import dataclass

from opensource.env_local import OpensourceEnv
from opensource.pangea.env_comm import PangeaEnvComm


@dataclass
class PangeaEnv(PangeaEnvComm):
    class Meta(PangeaEnvComm.Meta):
        stage = "local"
        emoji = "🐣"
        parent = OpensourceEnv()

    def __init__(self) -> None:
        super().__init__()


Env = PangeaEnv
