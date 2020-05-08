import os
from importlib import import_module, reload
from pathlib import Path

import pytest

import envo.scripts
from envo.comm.utils import flake8, mypy
from tests.utils import command


class TestUnit:
    @pytest.fixture(autouse=True)
    def setup(self, mock_exit, sandbox, version, mocker, capsys):
        mocker.patch("envo.scripts.Envo._start_files_watchdog")
        yield
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_creating(self, init):
        assert Path("env_comm.py").exists()
        assert Path("env_test.py").exists()

        flake8()
        mypy()

    def test_importing(self, init, env):
        assert str(env) == "sandbox"
        assert env.stage == "test"
        assert env.emoji == envo.scripts.Envo.stage_emoji_mapping[env.stage]

    def test_version(self, capsys):
        command("--version")
        captured = capsys.readouterr()
        assert captured.out == "1.2.3\n"

    def test_shell(self, init):
        command("test")

    def test_get_name(self, init, env):
        assert env.get_name() == "sandbox"

    def test_get_namespace(self, init, env):
        assert env.get_namespace() == "SANDBOX"

    def test_shell_module_with_the_same_name(self, init):
        Path("sandbox").mkdir()
        Path("sandbox/__init__.py").touch()
        command("test")

    def test_dry_run(self, init, capsys):
        command("test", "--dry-run")
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_save(self, init, capsys):
        command("test", "--dry-run", "--save")

        assert Path(".env_test").exists()
        Path(".env_test").unlink()

        captured = capsys.readouterr()
        assert captured.out != ""

    def test_activating(self, init):
        assert os.environ["SANDBOX_STAGE"] == "test"

    def test_init_py_created(self, init, mocker):
        mocker.patch("envo.scripts.Path.unlink")
        command("test")
        assert Path("__init__.py").exists()

    def test_init_py_delete_if_not_exists(self, init):
        assert not Path("__init__.py").exists()

    def test_init_untouched_if_exists(self):
        file = Path("__init__.py")
        file.touch()
        file.write_text("a = 1")
        command("test", "--init")

        assert file.read_text() == "a = 1"

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

    def test_venv_addon(self):
        command("test", "--init=venv")

        reload(import_module("sandbox.env_comm"))
        env = reload(import_module("sandbox.env_test")).Env()

        assert hasattr(env, "venv")
        env.activate()
        assert "SANDBOX_VENV_BIN" in os.environ
        assert f"{Path('.').absolute()}/.venv/bin" in os.environ["PATH"]

        flake8()
        mypy()
