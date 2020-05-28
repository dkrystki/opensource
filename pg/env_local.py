from dataclasses import dataclass
from pathlib import Path
from typing import Any

from envo.comm import import_module_from_file

PangeaEnvComm: Any = import_module_from_file(Path("env_comm.py")).PangeaEnvComm


@dataclass
class PangeaEnv(PangeaEnvComm):
    class Meta(PangeaEnvComm.Meta):
        stage = "local"
        emoji = "🐣"

    def __init__(self) -> None:
        super().__init__()


Env = PangeaEnv
