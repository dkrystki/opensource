from dataclasses import dataclass

from .env_comm import {{ class_name }}Comm


@dataclass
class {{ class_name }}({{ class_name }}Comm):
    def __init__(self) -> None:
        self.emoji = "{{ emoji }}"
        self.stage = "{{ stage }}"
        super().__init__()


Env = {{ class_name }}

