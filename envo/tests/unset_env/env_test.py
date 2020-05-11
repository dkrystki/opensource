from dataclasses import dataclass

from .env_comm import ChildEnv, UndefEnvComm


@dataclass
class ChildEnv(ChildEnv):
    class Meta(ChildEnv.Meta):
        stage = "test"
        emoji = "🛠"

    def __init__(self) -> None:
        super().__init__()


@dataclass
class UndefEnv(UndefEnvComm):
    class Meta(UndefEnvComm.Meta):
        stage = "test"
        emoji = "🛠"

    def __init__(self) -> None:
        super().__init__()

        self.child_env = ChildEnv()


Env = UndefEnv
