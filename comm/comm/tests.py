import os
import shutil
from pathlib import Path
from typing import Callable, Generator

import pexpect as pexpect
from pytest import fixture  # type: ignore

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
def spawn() -> Callable[[str], pexpect.spawn]:
    def factory(command: str) -> pexpect.spawn:
        p = pexpect.spawn(command, echo=False)
        return p

    return factory
