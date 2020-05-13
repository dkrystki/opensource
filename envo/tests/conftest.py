import os
from importlib import import_module, reload
from pathlib import Path

from envo import Env
from pexpect import run
from pytest import fixture
from tests.nested_env.env_test import NestedEnv
from tests.parent_env.child_env.env_test import ChildEnv
from tests.property_env.env_test import PropertyEnv
from tests.raw_env.env_test import RawEnv
from tests.undecl_env.env_test import UndeclEnv
from tests.unset_env.env_test import UnsetEnv
from tests.utils import command

test_root = Path(os.path.realpath(__file__)).parent
envo_root = test_root.parent

pytest_plugins = [
    "envo.comm.fixtures",
]


@fixture
def nested_env() -> NestedEnv:
    env = NestedEnv()
    return env


@fixture
def unset_env() -> UnsetEnv:
    env = UnsetEnv()
    return env


@fixture
def undecl_env() -> UndeclEnv:
    env = UndeclEnv()
    return env


@fixture
def raw_env() -> RawEnv:
    env = RawEnv()
    return env


@fixture
def property_env() -> PropertyEnv:
    env = PropertyEnv()
    return env


@fixture
def child_env() -> ChildEnv:
    env = ChildEnv()
    return env


@fixture
def mock_exit(mocker) -> None:
    mocker.patch("os._exit")


@fixture
def version() -> None:
    file = envo_root / "envo/__version__.py"
    file.touch()
    file.write_text('__version__ = "1.2.3"')

    yield

    file.unlink()


@fixture
def init() -> None:
    command("test", "--init")


@fixture
def e2e_init() -> None:
    run("envo test --init")


@fixture
def env() -> Env:
    reload(import_module("sandbox.env_comm"))
    env = reload(import_module("sandbox.env_test")).Env()
    return env
