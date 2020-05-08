import os
from pathlib import Path

root: Path = Path(os.path.realpath(__file__)).parent
templates_dir = root / "templates"
