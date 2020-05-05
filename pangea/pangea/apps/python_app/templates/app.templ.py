import pathlib

from pangea.apps.python_app import PythonApp


class {{  }}(PythonApp):
    @dataclass
    class Sets(PythonApp.Sets):
        pass

    @dataclass
    class Links(PythonApp.Links):
        env = {{ env_name }}Env

    def __init__(self, se: Sets, li: Links):
        super().__init__(se, li)
