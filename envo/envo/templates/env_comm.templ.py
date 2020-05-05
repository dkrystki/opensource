import os
from dataclasses import dataclass
from pathlib import Path

import envo


@dataclass
class {{ class_name }}Comm(envo.Env):
    {%- if "venv" in selected_addons%}
    venv: envo.VenvEnv
    {%- endif %}

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
        self._name = "{{ name }}"

        {%- if "venv" in selected_addons %}
        self.venv = envo.VenvEnv(owner=self)
        {%- endif %}


Env = {{ class_name }}Comm

