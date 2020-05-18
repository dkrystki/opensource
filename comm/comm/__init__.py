import sys
from pathlib import Path
from typing import Any, Dict

import black
from jinja2 import Template
from loguru import logger

__all__ = ["dir_name_to_class_name", "setup_logger", "render_py_file"]


def dir_name_to_class_name(dir_name: str) -> str:
    class_name = dir_name.replace("_", " ")
    class_name = class_name.replace(".", " ")
    s: str
    class_name = "".join([s.strip().capitalize() for s in class_name.split()])

    return class_name


def setup_logger() -> None:
    logger.remove()

    logger.add(
        sys.stdout,
        format="<bold>{message}</bold>",
        level="INFO",
        filter=lambda x: x["level"].name == "INFO",
    )
    logger.add(
        sys.stderr,
        format="<bold><yellow>{message}</yellow></bold>",
        level="WARNING",
        filter=lambda x: x["level"].name == "WARNING",
    )
    logger.add(
        sys.stderr,
        format="<bold><red>{message}</red></bold>",
        level="ERROR",
        filter=lambda x: x["level"].name == "ERROR",
    )


def render_file(template_path: Path, output: Path, context: Dict[str, Any]) -> None:
    template = Template(template_path.read_text())
    output.write_text(template.render(**context))


def render_py_file(template_path: Path, output: Path, context: Dict[str, Any]) -> None:
    render_file(template_path, output, context)
    try:
        black.main([str(output), "-q"])
    except SystemExit:
        pass
