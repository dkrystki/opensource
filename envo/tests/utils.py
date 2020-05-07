import os
import sys
import time
from pathlib import Path
from threading import Thread

test_root = Path(os.path.realpath(__file__)).parent
envo_root = test_root.parent


def command(*args):
    sys.argv = ("envo",) + args
    from envo import scripts

    scripts._main()
    sys.argv = []


def change_file(file: Path, delay_s: float, line_n: int, line: str) -> None:
    def fun(file: Path, delay_s: float, line_n: int, line: str) -> None:
        time.sleep(delay_s)
        content = file.read_text().splitlines(keepends=True)
        content.insert(line_n, line)
        content = "".join(content)
        file.write_text(content)

    thread = Thread(target=fun, args=(file, delay_s, line_n, line))
    thread.start()
