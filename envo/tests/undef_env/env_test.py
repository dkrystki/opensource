from dataclasses import dataclass

from .env_comm import UndefEnvComm


@dataclass
class UndefEnv(UndefEnvComm):
    class Meta(UndefEnvComm.Meta):
        stage = "test"
        emoji = "🛠"

    def __init__(self) -> None:
        super().__init__()


Env = UndefEnv
