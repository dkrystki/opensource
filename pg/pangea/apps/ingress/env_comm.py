import os
from dataclasses import dataclass
from pathlib import Path

import envo


@dataclass
class IngressEnvComm(envo.Env):
    class Meta(envo.Env.Meta):
        root = Path(os.path.realpath(__file__)).parent
        name = "ingress"
        parent = None

    def __init__(self) -> None:
        super().__init__()


Env = IngressEnvComm
