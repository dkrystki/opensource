from dataclasses import dataclass
from typing import Any
from pathlib import Path

from envo.comm import import_module_from_file
OpensourceEnvComm: Any = import_module_from_file(Path("env_comm.py")).OpensourceEnvComm


@dataclass
class OpensourceEnv(OpensourceEnvComm):
    class Meta(OpensourceEnvComm.Meta):
        stage = "local"
        emoji = "🐣"

    def __init__(self) -> None:
        super().__init__()


Env = OpensourceEnv
