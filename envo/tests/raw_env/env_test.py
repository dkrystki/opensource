from dataclasses import dataclass

from .env_comm import RawEnvComm


@dataclass
class RawEnv(RawEnvComm):
    def __init__(self) -> None:
        self.stage = "test"
        super().__init__()
        self.emoji = "🛠️"

        self.not_nested = "NOT_NESTED_TEST"
        self.group = self.SomeEnvGroup(nested="NESTED_TEST")


Env = RawEnv
