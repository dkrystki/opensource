import os
from pathlib import Path

from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent
envo_root = test_root.parent

pytest_plugins = [
    "envo.comm.fixtures",
]


os_exit = os._exit


@fixture
def version() -> None:
    file = envo_root / "envo/__version__.py"
    file.touch()
    file.write_text('__version__ = "1.2.3"')

    yield

    file.unlink()


@fixture
def mock_exit() -> None:
    # Monkey patching because normal patch doesn't work reliably wit os.exit for some reason
    os._exit = lambda x: None
    yield
    os._exit = os_exit
