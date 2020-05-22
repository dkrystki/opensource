import os
from pathlib import Path

from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent
root = test_root.parent

pytest_plugins = [
    "pangea.comm.fixtures",
]


@fixture
def add_registry_app() -> None:
    from tests import utils

    utils.add_registry_app()


@fixture
def version() -> None:
    file = root / "pangea/__version__.py"
    file.touch()
    file.write_text('__version__ = "1.2.3"')

    yield

    file.unlink()
