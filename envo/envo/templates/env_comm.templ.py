import os
from dataclasses import dataclass
from pathlib import Path

from envo import Env

{%- if "venv" in selected_addons-%}
, VenvEnv
{%- endif %}


@dataclass
class {{ class_name }}Comm(Env):
    {%- if "venv" in selected_addons%}
    venv: VenvEnv
    {%- endif %}

    def __init__(self) -> None:
        super().__init__(root=Path(os.path.realpath(__file__)).parent)
        self._name = "{{ name }}"

        {%- if "venv" in selected_addons %}
        self.venv = VenvEnv(owner=self)
        {%- endif %}


Env = {{ class_name }}Comm

