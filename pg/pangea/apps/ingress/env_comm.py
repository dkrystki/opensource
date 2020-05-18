from dataclasses import dataclass

from pangea.apps import AppEnv


@dataclass
class IngressEnvComm(AppEnv):
    class Meta(AppEnv.Meta):
        version = "0.1.0"

    def __init__(self) -> None:
        super().__init__()


Env = IngressEnvComm
