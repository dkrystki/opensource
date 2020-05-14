import os
import shutil
from pathlib import Path

from pexpect import run
from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent


@fixture
def init() -> None:
    run("envo test --init")


@fixture
def child_env() -> None:
    cwd = Path(".").absolute()
    child_dir = Path("child")
    if child_dir.exists():
        shutil.rmtree(child_dir)

    child_dir.mkdir()
    os.chdir(str(child_dir))
    run("envo test --init")

    comm_file = Path("env_comm.py")
    content = comm_file.read_text()
    content = content.splitlines(keepends=True)
    content.insert(0, "from sandbox.env_test import SandboxEnv\n")
    content.pop(13)
    content.insert(13, "        parent = SandboxEnv()\n")
    content = "".join(content)
    comm_file.write_text(content)

    os.chdir(str(cwd))

    yield
    if child_dir.exists():
        shutil.rmtree(child_dir)
