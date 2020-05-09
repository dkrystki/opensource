from dataclasses import dataclass

from opensource.env_local import OpensourceEnv
from opensource.pangea.env_comm import PangeaEnvComm


@dataclass
class PangeaEnv(PangeaEnvComm):
    def __init__(self) -> None:
        self.emoji = "🐣"
        self.stage = "local"
        super().__init__()

        self.parent = OpensourceEnv()


Env = PangeaEnv
