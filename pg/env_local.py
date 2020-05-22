from dataclasses import dataclass

from opensource.pg.env_comm import PangeaEnvComm


@dataclass
class PangeaEnv(PangeaEnvComm):
    class Meta(PangeaEnvComm.Meta):
        stage = "local"
        emoji = "🐣"

    def __init__(self) -> None:
        super().__init__()


Env = PangeaEnv
