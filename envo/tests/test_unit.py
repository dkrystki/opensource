import os
import sys
from importlib import import_module, reload
from pathlib import Path

import pytest

import envo.scripts


@pytest.mark.usefixtures("mock_exit")
class TestUnit:
    def test_creating(self, in_sandbox, flake8, mypy):
        sys.argv = ["envo", "test", "--init"]
        envo.scripts._main()

        assert Path("env_comm.py").exists()
        assert Path("env_test.py").exists()

        flake8()
        mypy()

    def test_importing(self, in_sandbox):
        sys.argv = ["envo", "test", "--init"]
        envo.scripts._main()

        reload(import_module("sandbox.env_comm"))
        env = reload(import_module("sandbox.env_test")).Env()

        assert str(env) == "sandbox"
        assert env.stage == "test"
        assert env.emoji == envo.scripts.Envo.stage_emoji_mapping[env.stage]

    def test_shell(self, in_sandbox):
        sys.argv = ["envo", "test", "--init"]
        envo.scripts._main()

        sys.argv = ["envo", "test"]
        envo.scripts._main()

    def test_dry_run(self, in_sandbox, capsys):
        sys.argv = ["envo", "test", "--init"]
        envo.scripts._main()

        sys.argv = ["envo", "test", "--dry-run"]
        envo.scripts._main()

        captured = capsys.readouterr()
        assert captured.out != ""

    def test_save(self, in_sandbox, capsys):
        sys.argv = ["envo", "test", "--init"]
        envo.scripts._main()

        sys.argv = ["envo", "test", "--dry-run", "--save"]
        envo.scripts._main()

        assert Path(".env_test").exists()
        Path(".env_test").unlink()

        captured = capsys.readouterr()
        assert captured.out != ""

    def test_activating(self, in_sandbox):
        sys.argv = ["envo", "test", "--init"]
        envo.scripts._main()

        assert os.environ["SANDBOX_STAGE"] == "test"

    def test_nested(self, nested_env):
        nested_env.activate()
        assert os.environ["TE_STAGE"] == "test"
        assert os.environ["TE_PYTHON_VERSION"] == "3.8.2"

    def test_verify(self, undef_env):
        with pytest.raises(envo.BaseEnv.UnsetVariable):
            undef_env.activate()

    def test_raw(self, raw_env):
        raw_env.activate()
        assert os.environ["NOT_NESTED"] == "NOT_NESTED_TEST"
        assert os.environ["NESTED"] == "NESTED_TEST"

    def test_venv_addon(self, in_sandbox, flake8, mypy):
        sys.argv = ["envo", "test", "--init=venv"]
        envo.scripts._main()

        reload(import_module("sandbox.env_comm"))
        env = reload(import_module("sandbox.env_test")).Env()

        assert hasattr(env, "venv")
        env.activate()
        assert "SANDBOX_VENV_BIN" in os.environ
        assert f"{Path('.').absolute()}/.venv/bin" in os.environ["PATH"]

        flake8()
        mypy()
