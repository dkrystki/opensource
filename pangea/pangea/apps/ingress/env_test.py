from dataclasses import dataclass

from ingress.env_comm import IngressEnvComm


@dataclass
class IngressEnv(IngressEnvComm):
    class Meta(IngressEnvComm.Meta):
        stage = "test"
        emoji = "🛠"

    def __init__(self) -> None:
        super().__init__()


Env = IngressEnv
