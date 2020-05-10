import os
from dataclasses import dataclass

from envo import Env, Path, Raw, VenvEnv


@dataclass
class CommEnvComm(Env):
    class Meta(Env.Meta):
        root = Path(os.path.realpath(__file__)).parent
        name = "comm"
        parent = None

    venv: VenvEnv
    pythonpath: Raw[str]
    bin_dir: Path
    path: Raw[str]

    def __init__(self) -> None:
        super().__init__()
        self.venv = VenvEnv(owner=self)

        self.bin_dir = self.root / ".bin"

        self.path = self.venv.path
        self.path = str(self.bin_dir) + ":" + self.path

        self.pythonpath = str(self.root)
