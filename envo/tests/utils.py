import asyncio
import os
import sys
import time
from pathlib import Path
from threading import Thread

import pexpect

test_root = Path(os.path.realpath(__file__)).parent
envo_root = test_root.parent


def command(*args):
    sys.argv = ("envo",) + args
    from envo import scripts

    scripts._main()
    sys.argv = []


def flake8() -> None:
    p = pexpect.run("flake8", echo=False)
    assert p == b""


def mypy() -> None:
    from pexpect import run

    original_dir = Path(".").absolute()
    package_name = original_dir.name
    Path("__init__.py").touch()
    os.chdir("..")
    environ = {"MYPYPATH": str(envo_root)}
    environ.update(os.environ)
    p = run(f"mypy {package_name}", env=environ, echo=False)
    assert b"Success: no issues found" in p
    os.chdir(str(original_dir))
    Path("__init__.py").unlink()


def spawn(command: str) -> pexpect.spawn:
    p = pexpect.spawn(command, echo=False)
    return p


def change_file(file: Path, delay_s: float, line_n: int, line: str) -> None:
    def fun(file: Path, delay_s: float, line_n: int, line: str) -> None:
        time.sleep(delay_s)
        content = file.read_text().splitlines(keepends=True)
        content.insert(line_n, line)
        content = "".join(content)
        file.write_text(content)

    thread = Thread(target=fun, args=(file, delay_s, line_n, line))
    thread.start()
