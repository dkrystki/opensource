import sys

from loguru import logger


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
