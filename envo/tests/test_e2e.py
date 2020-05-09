import os
from pathlib import Path

import pytest
from pexpect import run

from envo.comm.utils import spawn
from tests.utils import change_file, prompt, shell, test_root


class TestE2e:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, prompt, e2e_init):
        self.shell = shell()

    def test_shell(self):
        self.shell.sendline("echo test")
        self.shell.expect(b"test.*" + prompt, timeout=1)

        self.shell.sendcontrol("d")

        assert Path("env_comm.py").exists()
        assert Path("env_test.py").exists()

    def test_dry_run(self):
        ret = run("envo test --dry-run", timeout=2)
        assert ret != b""

    def test_save(self):
        run("envo test --save")

        assert Path("env_comm.py").exists()
        assert Path("env_test.py").exists()
        assert Path(".env_test").exists()

    def test_hot_reload(self):
        change_file(Path("env_comm.py"), 0.5, 6, "\n")
        self.shell.expect(prompt, timeout=5)
        self.shell.sendcontrol("d")

    def test_hot_reload_old_envs_gone(self):
        self.shell.sendline("echo $SANDBOX_STAGE")
        self.shell.expect("test", timeout=1)

        change_file(Path("env_comm.py"), 0.5, 14, '        self._name = "new"\n')
        new_prompt = prompt.replace(b"sandbox", b"new")
        self.shell.expect(new_prompt, timeout=2)

        self.shell.sendline("echo $NEW_STAGE")
        self.shell.expect("test", timeout=1)

        self.shell.sendline("echo $SANDBOX_STAGE")
        self.shell.expect(new_prompt, timeout=1)
        self.shell.sendcontrol("d")

    def test_hot_reload_child_dir(self):
        Path("./test_dir").mkdir()
        os.chdir("./test_dir")

        change_file(Path("../env_comm.py"), 0.5, 6, "\n")
        self.shell.expect(prompt, timeout=5)
        self.shell.sendcontrol("d")

    def test_hot_reload_error(self):
        file_before = Path("env_comm.py").read_text()

        change_file(Path("env_comm.py"), 0.5, 9, "    test_var: int\n")
        self.shell.expect(r'.*Env variable "sandbox.test_var" is not set!.*', timeout=5)

        Path("env_comm.py").write_text(file_before)
        self.shell.expect(prompt)

        self.shell.sendcontrol("d")

        assert Path("env_comm.py").exists()
        assert Path("env_test.py").exists()

    def test_autodiscovery(self):
        Path("./test_dir").mkdir()
        os.chdir("./test_dir")

        s = shell()
        s.sendline("echo test")
        s.expect(prompt, timeout=1)
        s.sendcontrol("d")

        assert list(Path(".").glob(".*")) == []

    def test_init_nested(self):
        expected_files = ["env_comm.py", "env_local.py"]

        Path("./test_dir").mkdir()
        os.chdir("./test_dir")
        for f in expected_files:
            if Path(f).exists():
                Path(f).unlink()

        nested_prompt = r"🐣\(test_dir\).*".encode("utf-8")
        run("envo --init")
        s = spawn("envo")
        s.sendline("echo test")
        s.expect(nested_prompt, timeout=1)
        s.sendcontrol("d")

        for f in expected_files:
            assert Path(f).exists()
            Path(f).unlink()

    def test_env_persists_in_bash_scripts(self):
        file = Path("script.sh")
        file.touch()
        file.write_text("echo $SANDBOX_ROOT\n")

        self.shell.sendline("bash script.sh")
        self.shell.expect(str(Path(".").absolute()), timeout=1)

    def test_child_parent_prompt(self):
        os.chdir(test_root / "parent_env/child_env")

        s = spawn("envo test")
        s.expect(r"🛠\(pa.ch\).*".encode("utf-8"), timeout=2)
