import os
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Callable

import pexpect
from pytest import fixture

from envo import Env

test_root = Path(os.path.realpath(__file__)).parent
envo_root = test_root.parent

pytest_plugins = [
    "plasma_comm.tests",
]


@fixture
def nested_env() -> Env:
    from nested_env.env_test import Env

    env = Env()

    return env


@fixture
def undef_env() -> Env:
    from undef_env.env_test import Env

    env = Env()

    return env


@fixture
def raw_env() -> Env:
    from raw_env.env_test import Env

    env = Env()

    return env


@fixture
def mock_exit(mocker) -> None:
    mocker.patch("os._exit")


@fixture
def flake8() -> Callable[[], None]:
    def fun() -> None:
        p = pexpect.run("flake8", echo=False)
        assert p == b""

    return fun


@fixture
def mypy() -> Callable[[], None]:
    def fun() -> None:
        original_dir = Path(".").absolute()
        package_name = original_dir.name
        Path("__init__.py").touch()
        os.chdir("..")
        environ = {"MYPYPATH": str(envo_root)}
        environ.update(os.environ)
        p = pexpect.run(f"mypy {package_name}", env=environ, echo=False)
        assert b"Success: no issues found" in p
        os.chdir(str(original_dir))
        Path("__init__.py").unlink()

    return fun


@fixture
def prompt() -> bytes:
    return r"🐣\(sandbox\).*@.*$".encode("utf-8")


@fixture
def pexpect_factory() -> Callable[[str], pexpect.spawn]:
    def factory(command: str) -> pexpect.spawn:
        p = pexpect.spawn(command, echo=False)
        return p

    return factory


@fixture
def change_file() -> Callable[[Path, float, int, str], None]:
    def fun(file: Path, delay_s: float, line_n: int, line: str) -> None:
        sleep(delay_s)
        content = file.read_text().splitlines(keepends=True)
        content.insert(line_n, line)
        content = "".join(content)
        file.write_text(content)

    def factory(file: Path, delay_s: float, line_n: int, line: str) -> None:
        thread = Thread(target=fun, args=(file, delay_s, line_n, line))
        thread.start()

    return factory
