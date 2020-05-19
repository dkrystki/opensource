import os
from pathlib import Path
from typing import List

import pexpect as pexpect

__all__ = [
    "prompt",
    "envo_prompt",
    "spawn",
    "shell",
    "flake8",
    "mypy",
    "render_py_file",
]

prompt = r".*@.*$".encode("utf-8")
envo_prompt = r"🛠\(sandbox\).*".encode("utf-8")


def spawn(command: str) -> pexpect.spawn:
    s = pexpect.spawn(command, echo=False)
    return s


def shell() -> pexpect.spawn:
    p = pexpect.spawn("envo test")
    p.expect(envo_prompt, timeout=2)
    return p


def flake8() -> None:
    p = pexpect.run("flake8", echo=False)
    assert p == b""


def mypy() -> None:
    from pexpect import run

    original_dir = Path(".").absolute()
    package_name = original_dir.name
    Path("__init__.py").touch()
    os.chdir("..")
    environ = {"MYPYPATH": str(original_dir)}
    environ.update(os.environ)
    p = run(f"mypy {package_name}", env=environ, echo=False)
    assert b"Success: no issues found" in p
    os.chdir(str(original_dir))
    Path("__init__.py").unlink()


def strs_in_regex(strings: List[str]) -> str:
    """
    Return regex that matches strings in any order.
    """
    ret = "".join([rf"(?=.*{s})" for s in strings])
    return ret