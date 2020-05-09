import os
from dataclasses import dataclass, fields
from pathlib import Path
from subprocess import Popen
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, Generic, List, Optional, TypeVar, Union

T = TypeVar("T")

if TYPE_CHECKING:
    Raw = Union[T]
    Parent = Union[T]
else:

    class Raw(Generic[T]):
        pass

    class Parent(Generic[T]):
        pass


@dataclass
class BaseEnv:
    class UnsetVariable(Exception):
        pass

    class Meta:
        raw: List[str] = []
        parent: Optional[str] = None

    def __init__(self, name: Optional[str] = None) -> None:
        if name:
            self._name = name
        else:
            self._name = str(self.__class__.__name__)

    # Repeating this code to populate _name without calling super().__init__() in subclasses
    def __post_init__(self) -> None:
        if not hasattr(self, "_name"):
            self._name = str(self.__class__.__name__)

    def _validate(self, parent_name: str) -> None:
        for f in fields(self):
            if not hasattr(self, f.name):
                # TODO: sometimes prints double dots
                raise self.UnsetVariable(
                    f'Env variable "{parent_name}.{f.name}" is not set!'
                )

            attr: Any = getattr(self, f.name)

            if issubclass(type(attr), BaseEnv):
                attr._validate(parent_name=f"{parent_name}.{f.name}.")

    def get_namespace(self) -> str:
        return self._name.replace("_", "").upper()

    def activate(self, namespace: str = "") -> None:
        self._validate(self._name)

        namespace = f"{namespace}{self.get_namespace()}_"
        for f in fields(self):
            var_name: str = f.name
            var = getattr(self, var_name)
            if isinstance(var, BaseEnv):
                var.activate(namespace=namespace)
            else:
                if hasattr(f.type, "__origin__"):
                    is_raw = f.type.__origin__ == Raw
                else:
                    is_raw = False
                os.environ[f"{namespace if not is_raw else''}{var_name.upper()}"] = str(
                    var
                )

    def __str__(self) -> str:
        return self._name


@dataclass
class Env(BaseEnv):
    root: Path
    emoji: str
    stage: str

    def __init__(self, root: Path, name: Optional[str] = None) -> None:
        super().__init__(name)
        self.root = root

    def activate(self, *args: Any, **kwargs: Any) -> None:
        super().activate(*args, **kwargs)

    def as_string(self, add_export: bool = False) -> List[str]:
        lines: List[str] = []

        for key, value in os.environ.items():
            if "BASH_FUNC_" not in key:
                line = "export " if add_export else ""
                line += f'{key}="{value}"'
                lines.append(line)

        return lines

    def print_envs(self) -> None:
        self.activate()
        content = "".join([f"export {line}\n" for line in self.as_string()])
        print(content)

    def dump_dot_env(self) -> None:
        self.activate()
        path = Path(f".env{'_' if self.stage else ''}{self.stage}")
        content = "\n".join(self.as_string())
        path.write_text(content)

    def shell(self) -> Popen:
        self.activate()

        bash_rc = NamedTemporaryFile(
            mode="w", buffering=True, delete=False, encoding="utf-8"
        )
        bash_rc.write("source ~/.bashrc\n")
        bash_rc.write("")
        content = ";\n".join(self.as_string(add_export=True))
        bash_rc.write(content)
        bash_rc.write("\n")
        bash_rc.write(f"PS1={self.emoji}\\({self._name}\\)$PS1\n")

        return Popen(["bash", "--rcfile", f"{bash_rc.name}"])

    def get_name(self) -> str:
        return self._name


@dataclass
class VenvEnv(BaseEnv):
    path: Raw[str]
    bin: Path

    def __init__(self, owner: Env) -> None:
        self.owner = owner
        super().__init__(name="venv")

        self.bin = self.owner.root / ".venv/bin"
        self.path = f"""{str(self.bin)}:{os.environ['PATH']}"""
