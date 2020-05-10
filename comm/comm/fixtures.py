import os
import shutil
from pathlib import Path
from typing import Callable, Generator

from pytest import fixture

root = Path(".").absolute()


@fixture
def sandbox() -> Generator:
    sandbox_dir = root / "sandbox"
    if sandbox_dir.exists():
        shutil.rmtree(str(sandbox_dir))

    sandbox_dir.mkdir()
    os.chdir(str(sandbox_dir))

    yield
    if sandbox_dir.exists():
        shutil.rmtree(str(sandbox_dir))


@fixture
def prompt() -> bytes:
    return r".*@.*$".encode("utf-8")


@fixture
def assert_no_stderr(capsys) -> Callable[[], None]:
    def fun() -> None:
        captured = capsys.readouterr()
        assert captured.err == ""

    return fun


@fixture(name="shell")
def shell_fixture():
    from .utils import shell

    return shell()


@fixture
def envo_prompt():
    from .utils import envo_prompt

    return envo_prompt


@fixture
def prompt():
    from .utils import prompt

    return prompt
