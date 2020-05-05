from dataclasses import dataclass

from envo import Path
from pangea.env import ClusterEnv

import os


@dataclass
class {{ class_name }}EnvComm(ClusterEnv):
    def __init__(self) -> None:
        self._name = "{{ cluster_name }}"
        super().__init__(root=Path(os.path.realpath(__file__)).parent)

        self.skaffold_ver = "1.6.0"
        self.kubectl_ver = "1.17.0"
        self.helm_ver = "2.15.2"
        self.kind_ver = "0.7.0"
        self.debian_ver = "buster"
        self.docker_ver = "18.09.9"


Env = {{ class_name }}EnvComm

