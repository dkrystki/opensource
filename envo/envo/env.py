import inspect
import os
from dataclasses import dataclass, field, fields
from importlib import import_module, reload
from pathlib import Path
from subprocess import Popen
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, Generic, List, Optional, Type, TypeVar, Union

from loguru import logger

__all__ = ["BaseEnv", "Env", "Raw", "VenvEnv"]


T = TypeVar("T")

if TYPE_CHECKING:
    Raw = Union[T]
else:

    class Raw(Generic[T]):
        pass


@dataclass
class BaseEnv:
    class EnvException(Exception):
        pass

    def __init__(self, name: Optional[str] = None) -> None:
        if name:
            self._name = name
        else:
            self._name = str(self.__class__.__name__)

    # Repeating this code to populate _name without calling super().__init__() in subclasses
    def __post_init__(self) -> None:
        if not hasattr(self, "_name"):
            self._name = str(self.__class__.__name__)

    def validate(self) -> None:
        errors = self.get_errors(self.get_name())
        if errors:
            raise self.EnvException("Detected errors!\n" + "\n".join(errors))

    def get_errors(self, parent_name: str = "") -> List[str]:
        """
        :param parent_name:
        :return: error messages
        """
        # look for undeclared variables
        field_names = set([fie.name for fie in fields(self)])

        var_names = set()
        f: str
        for f in dir(self):
            attr: Any = getattr(self, f)

            if hasattr(self.__class__, f):
                class_attr: Any = getattr(self.__class__, f)
            else:
                class_attr = None

            if (
                inspect.ismethod(attr)
                or (class_attr is not None and inspect.isdatadescriptor(class_attr))
                or f.startswith("_")
                # parent_env_comm is a special case here, we have to exclude it
                or (f != "parent_env_comm" and inspect.isclass(attr))
                or f == "meta"
                or f == "parent"
            ):
                continue

            var_names.add(f)

        unset = field_names - var_names
        undeclr = var_names - field_names

        error_msgs: List[str] = []

        if unset:
            error_msgs += [f'Variable "{parent_name}.{v}" is unset!' for v in unset]

        if undeclr:
            error_msgs += [
                f'Variable "{parent_name}.{v}" is undeclared!' for v in undeclr
            ]

        fields_to_check = field_names - unset - undeclr

        for f in fields_to_check:
            attr2check: Any = getattr(self, f)
            if issubclass(type(attr2check), BaseEnv):
                error_msgs += attr2check.get_errors(parent_name=f"{parent_name}.{f}")

        return error_msgs

    def get_namespace(self) -> str:
        return self._name.replace("_", "").upper()

    def activate(self, owner_namespace: str = "") -> None:
        self.validate()

        for f in fields(self):
            var = getattr(self, f.name)

            namespace = ""
            var_name = ""
            var_type: Any = None
            if hasattr(f.type, "__origin__"):
                var_type = f.type.__origin__

            if var_type == Raw:
                var_name = f.name.upper()
            else:
                namespace = f"{owner_namespace}{self.get_namespace()}_"
                var_name = namespace + f.name.replace("_", "").upper()

            if isinstance(var, BaseEnv):
                var.activate(owner_namespace=namespace)
            else:
                os.environ[var_name] = str(var)

    def get_name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name


@dataclass
class Env(BaseEnv):
    @dataclass
    class Meta(BaseEnv):
        stage: str = field(default="comm", init=False)
        emoji: str = field(default="", init=False)
        name: str = field(init=False)
        root: Path = field(init=False)
        parent_env_comm: Optional[Type["Env"]] = field(default=None, init=False)
        version: str = field(default="0.1.0", init=False)

    root: Path
    stage: str
    envo_stage: Raw[str]

    def __init__(self) -> None:
        self.meta = self.Meta()
        self.meta.validate()

        self.root = self.meta.root
        self.stage = self.meta.stage
        self.envo_stage = self.stage

        self.parent = None

        if self.meta.parent_env_comm:
            self.parent = self.meta.parent_env_comm.get_stage(self.stage)
            self.parent.activate()

        super().__init__(self.meta.name)

    def as_string(self, add_export: bool = False) -> List[str]:
        lines: List[str] = []

        for key, value in os.environ.items():
            if "BASH_FUNC_" not in key:
                line = "export " if add_export else ""
                line += f'{key}="{value}"'
                lines.append(line)

        return lines

    def activate(self, owner_namespace: str = "") -> None:
        if self.meta.stage == "comm":
            raise RuntimeError('Cannot activate env with "comm" stage!')

        super().activate(owner_namespace)

        self._set_pythonpath()

    def print_envs(self) -> None:
        self.activate()
        content = "".join([f"export {line}\n" for line in self.as_string()])
        print(content)

    def dump_dot_env(self) -> None:
        self.activate()
        path = Path(f".env{'_' if self.meta.stage else ''}{self.meta.stage}")
        content = "\n".join(self.as_string())
        path.write_text(content)
        logger.info(f"Saved envs to {str(path)} 💾")

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

        bash_rc.write(f"PS1={self.meta.emoji}\\({self.get_full_name()}\\)$PS1\n")

        return Popen(["bash", "--rcfile", f"{bash_rc.name}"])

    def get_full_name(self) -> str:
        if self.parent:
            return self.parent.get_full_name() + "." + self.get_name()
        else:
            return self.get_name()

    @classmethod
    def get_current_stage(cls) -> "Env":
        parent_module = ".".join(cls.__module__.split(".")[0:-1])
        stage = os.environ["ENVO_STAGE"]
        env: "Env" = reload(import_module(f"{parent_module}.env_{stage}")).Env()  # type: ignore
        return env

    @classmethod
    def get_stage(cls, stage: str) -> "Env":
        parent_module = ".".join(cls.__module__.split(".")[0:-1])
        env: "Env" = reload(import_module(f"{parent_module}.env_{stage}")).Env()  # type: ignore
        return env

    def _set_pythonpath(self) -> None:
        if "PYTHONPATH" not in os.environ:
            os.environ["PYTHONPATH"] = ""

        os.environ["PYTHONPATH"] = (
            str(self.meta.root.parent) + ":" + os.environ["PYTHONPATH"]
        )

        if self.parent:
            self.parent._set_pythonpath()


@dataclass
class VenvEnv(BaseEnv):
    path: Raw[str]
    bin: Path

    def __init__(self, owner: Env) -> None:
        self._owner = owner
        super().__init__(name="venv")

        self.bin = self._owner.root / ".venv/bin"
        self.path = f"""{str(self.bin)}:{os.environ['PATH']}"""
