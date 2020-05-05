import os
import sys
from pathlib import Path
from typing import Callable, List

import pexpect
from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent
root = test_root.parent

pytest_plugins = [
    "plasma_comm.tests",
]


@fixture
def flake8() -> Callable[[], None]:
    def fun() -> None:
        Path(".flake8")
        p = pexpect.run(f"flake8 --config={str(root / '.flake8')}", echo=False)
        assert p == b""

    return fun


@fixture
def mypy() -> Callable[[], None]:
    def fun() -> None:
        original_dir = Path(".").absolute()
        package_name = original_dir.name
        Path("__init__.py").touch()
        os.chdir("..")
        environ = {"MYPYPATH": str(root)}
        environ.update(os.environ)
        p = pexpect.run(f"mypy {package_name}", env=environ, echo=False)
        assert b"Success: no issues found" in p
        os.chdir(str(original_dir))
        Path("__init__.py").unlink()

    return fun


@fixture
def envo_prompt() -> bytes:
    return r"🐣\(sandbox\).*@.*$".encode("utf-8")


@fixture
def pg():
    def fun(*args):
        sys.argv = ("pangea",) + args
        from pangea import scripts
        scripts._main()
        sys.argv = []

    return fun
