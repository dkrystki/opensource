import os
from importlib import import_module, reload
from pathlib import Path

from pexpect import run
from pytest import fixture

from envo import Env
from tests.utils import command

test_root = Path(os.path.realpath(__file__)).parent
envo_root = test_root.parent

pytest_plugins = [
    "envo.comm.fixtures",
]


@fixture
def nested_env() -> Env:
    from tests.nested_env.env_test import Env

    env = Env()
    return env


@fixture
def undef_env() -> Env:
    from tests.undef_env.env_test import Env

    env = Env()
    return env


@fixture
def raw_env() -> Env:
    from tests.raw_env.env_test import Env

    env = Env()
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
