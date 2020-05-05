from dataclasses import dataclass

from .env_comm import PangeaEnvComm


@dataclass
class PangeaEnv(PangeaEnvComm):
    class Meta:
        raw = ["pythonpath"]

    def __init__(self) -> None:
        self.emoji = "🐣"
        self.stage = "local"
        super().__init__()

        self.pythonpath = str(self.root)


Env = PangeaEnv
