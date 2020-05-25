import os
from dataclasses import dataclass
from pathlib import Path

import envo
from envo import VenvEnv, BaseEnv, Raw


@dataclass
class OpensourceEnvComm(envo.Env):
    class Meta(envo.Env.Meta):
        root = Path(os.path.realpath(__file__)).parent
        name = "os"
        parent = None

    venv: VenvEnv
    path: Raw[str]
    bin_dir: Path

    def __init__(self) -> None:
        super().__init__()
        self.venv = VenvEnv(owner=self)

        self.path = self.venv.path
        self.bin_dir = self.root / ".bin"
        self.path = str(self.bin_dir) + ":" + self.path


Env = OpensourceEnvComm
