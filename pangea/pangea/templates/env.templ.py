from dataclasses import dataclass

from .env_comm import {{ class_name }}EnvComm


@dataclass
class {{ class_name }}Env({{ class_name }}EnvComm):
    def __init__(self) -> None:
        self.stage = "{{ stage }}"
        self.emoji = "{{ emoji }}"

        super().__init__()

        self.registry = self.Registry(address="{{ cluster_name }}.registry.{{ stage }}",
                                      username="user",
                                      password="password")

        self.device = self.Device(k8s_ver="1.15.7", name=f"{self._name}-{self.stage}",
                                  type="kind")


Env = {{ class_name }}Env

