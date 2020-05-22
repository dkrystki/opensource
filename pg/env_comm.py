import os
from dataclasses import dataclass
from pathlib import Path

from envo import Env, Raw, VenvEnv
from opensource.env_local import OpensourceEnv


@dataclass
class PangeaEnvComm(Env):
    class Meta(Env.Meta):
        root = Path(os.path.realpath(__file__)).parent
        name = "pg"
        parent_env_comm = OpensourceEnv

    venv: VenvEnv

    skaffold_ver: str
    kubectl_ver: str
    hostess_ver: str
    helm_ver: str
    kind_ver: str

    deps_dir: Path
    bin_dir: Path
    path: Raw[str]
    # pythonpath: Raw[str]

    def __init__(self) -> None:
        super().__init__()
        self.venv = VenvEnv(owner=self)

        self.skaffold_ver = "1.6.0"
        self.kubectl_ver = "1.17.0"
        self.hostess_ver = "0.3.0"
        self.helm_ver = "3.2.1"
        self.kind_ver = "0.8.1"

        self.deps_dir = self.meta.root / ".deps"
        self.bin_dir = self.meta.root / ".bin"

        self.path = self.venv.path
        self.path = str(self.bin_dir) + ":" + self.path

        if "PYTHONPATH" not in os.environ:
            os.environ["PYTHONPATH"] = ""

        # self.pythonpath = os.environ["PYTHONPATH"]
        # self.pythonpath = str(self.meta.root) + ":" + self.pythonpath
