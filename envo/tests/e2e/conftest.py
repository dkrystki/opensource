import os
from pathlib import Path

from tests.e2e import utils

from pexpect import run
from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent


@fixture
def init() -> None:
    run("envo test --init")


@fixture
def init_child_env() -> None:
    child_dir = Path("child")
    utils.init_child_env(child_dir)


@fixture
def init_2_same_childs() -> None:
    sandbox1 = Path("sandbox")
    utils.init_child_env(sandbox1)

    sandbox2 = Path("sandbox/sandbox")
    utils.init_child_env(sandbox2)
