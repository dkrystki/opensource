from dataclasses import dataclass

from .env_comm import SandboxEnvComm


@dataclass
class SandboxEnv(SandboxEnvComm):
    def __init__(self) -> None:
        self.stage = "local"
        self.emoji = "🐣"

        super().__init__()

        self.registry = self.Registry(
            address="sandbox.registry.local", username="user", password="password"
        )

        self.device = self.Device(
            k8s_ver="1.15.7", name=f"{self._name}-{self.stage}", type="kind"
        )


Env = SandboxEnv
