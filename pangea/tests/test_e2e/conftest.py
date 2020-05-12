import os
from pathlib import Path

from pexpect import run
from pytest import fixture


test_root = Path(os.path.realpath(__file__)).parent
root = test_root.parent

pytest_plugins = [
    "pangea.comm.fixtures",
]


@fixture
def init() -> str:
    return run("pangea --init").decode("utf-8")
