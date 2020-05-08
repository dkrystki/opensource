import sys
from pathlib import Path

import pexpect
import pytest
from pangea.comm.utils import flake8, mypy, spawn
from tests.utils import command


class TestUnit:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version):
        pass

    def test_creating(self):
        command("--init")

        assert Path("cluster.py").exists()
        assert Path("env_comm.py").exists()
        assert Path("env_local.py").exists()
        assert Path(".deps").exists()
        assert Path(".bin").exists()

        flake8()
        # mypy()

    def test_version(self, capsys):
        command("--version")
        captured = capsys.readouterr()
        assert captured.out == "1.2.3\n"

    def test_bootstrap(self):
        command("--init")

        assert Path("cluster.py").exists()
        assert Path("env_comm.py").exists()
        assert Path("env_local.py").exists()
        assert Path(".deps").exists()
        assert Path(".bin").exists()

        # mypy()
