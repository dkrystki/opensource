import os
import shutil
from pathlib import Path

from pexpect import run
from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent
root = test_root.parent


@fixture
def init() -> str:
    return run("pangea --init").decode("utf-8")


@fixture
def deps() -> None:
    shutil.rmtree(".deps")
    shutil.copytree("../../../.deps", ".deps")