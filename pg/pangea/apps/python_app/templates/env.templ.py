import os
import pathlib

import envo
from pangea.apps.python_app import PythonAppEnv


@dataclass
class {{ env_name }}Env(PythonAppEnv):
    def __init__(self) -> None:
        self.app_name = "{{ app_name }}"
        super().__init__(path=pathlib.Path(os.path.realpath(__file__)).parent)
