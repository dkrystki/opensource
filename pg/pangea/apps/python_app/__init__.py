import pathlib
from dataclasses import dataclass

import envo
from pangea.apps import AppPythonUtils, DockerUtils, SkaffoldApp
from pangea.env import AppEnv


@dataclass
class PythonAppEnv(AppEnv):
    class Python(envo.BaseEnv):
        ver_major: int
        ver_minor: int
        ver_patch: int
        poetry_ver: str
        pyenv_root: envo.Path

        @property
        def version(self) -> str:
            return f"{self.ver_major}.{self.ver_minor}.{self.ver_patch}"

    python: Python

    def __init__(self, root: pathlib.Path) -> None:
        super().__init__(root)


class PythonApp(SkaffoldApp):
    @dataclass
    class Sets(SkaffoldApp.Sets):
        pass

    @dataclass
    class Links(SkaffoldApp.Links):
        env = PythonAppEnv

    def __init__(self, se: Sets, li: Links):
        super().__init__(se, li)

        self.python = AppPythonUtils(
            se=AppPythonUtils.Sets(), li=AppPythonUtils.Links(env=self.env)
        )

        self.docker = DockerUtils(
            se=DockerUtils.Sets(),
            li=DockerUtils.Links(env=self.env, dockerfile=self.dockerfile),
        )
