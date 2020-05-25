import os
from importlib import import_module, reload
from pathlib import Path
from typing import Type

from tests.unit.nested_env.env_test import NestedEnv
from tests.unit.parent_env.child_env.env_test import ChildEnv
from tests.unit.property_env.env_test import PropertyEnv
from tests.unit.raw_env.env_test import RawEnv
from tests.unit.undecl_env.env_test import UndeclEnv
from tests.unit.unset_env.env_test import UnsetEnv
from tests.unit.utils import command

from envo import Env
from pytest import fixture

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
def init() -> None:
    command("test", "--init")


@fixture
def env() -> Env:
    reload(import_module("sandbox.env_comm"))
    env = reload(import_module("sandbox.env_test")).Env()
    return env


@fixture
def env_comm() -> Type[Env]:
    env = reload(import_module("sandbox.env_comm")).Env
    return env
