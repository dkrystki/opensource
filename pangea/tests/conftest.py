import os
import sys
from pathlib import Path
from typing import Callable, List

import pexpect
from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent
root = test_root.parent

pytest_plugins = [
    "pangea.comm.fixtures",
]


@fixture
def envo_prompt() -> bytes:
    return r"🐣\(sandbox\).*".encode("utf-8")
