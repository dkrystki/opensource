import os
from pathlib import Path

package_root: Path = Path(os.path.realpath(__file__)).parent
templates_dir = package_root / "templates"
