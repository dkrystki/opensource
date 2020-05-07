import os
import shutil
from pathlib import Path
from typing import Generator

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
