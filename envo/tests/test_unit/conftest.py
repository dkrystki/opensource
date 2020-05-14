import os
from importlib import import_module, reload
from pathlib import Path

from envo import Env
from pytest import fixture
from tests.test_unit.nested_env.env_test import NestedEnv
from tests.test_unit.parent_env.child_env.env_test import ChildEnv
from tests.test_unit.property_env.env_test import PropertyEnv
from tests.test_unit.raw_env.env_test import RawEnv
from tests.test_unit.undecl_env.env_test import UndeclEnv
from tests.test_unit.unset_env.env_test import UnsetEnv
from tests.test_unit.utils import command

test_root = Path(os.path.realpath(__file__)).parent


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
def init() -> None:
    command("test", "--init")


@fixture
def env() -> Env:
    reload(import_module("sandbox.env_comm"))
    env = reload(import_module("sandbox.env_test")).Env()
    return env
