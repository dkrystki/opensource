import os
from pathlib import Path

import pytest
from envo.comm.utils import spawn
from pexpect import run
from tests.utils import change_file


@pytest.mark.usefixtures("sandbox")
class TestE2e:
    @pytest.fixture(autouse=True)
    def setup(self, prompt):
        self.prompt = prompt

    def test_shell(self):
        p = spawn("envo --init")
        p.expect(self.prompt, timeout=1)
        p.sendline("echo test")
        p.expect(self.prompt, timeout=1)

        p.sendcontrol("d")

        assert Path("env_comm.py").exists()
        assert Path("env_local.py").exists()

    def test_dry_run(self):
        p = spawn("envo --init")
        p.expect(self.prompt, timeout=1)
        p.sendcontrol("d")

        ret = run("envo --dry-run", timeout=2)
        assert ret != b""

    def test_save(self):
        p = spawn("envo --init --save")
        p.expect(self.prompt, timeout=1)
        p.sendcontrol("d")

        assert Path("env_comm.py").exists()
        assert Path("env_local.py").exists()
        assert Path(".env_local").exists()

    def test_hot_reload(self):
        p = spawn("envo --init")
        p.expect(self.prompt, timeout=1)

        change_file(Path("env_comm.py"), 0.5, 6, "\n")
        p.expect(self.prompt, timeout=5)
        p.sendcontrol("d")

    def test_hot_reload_old_envs_gone(self):
        p = spawn("envo --init")
        p.expect(self.prompt, timeout=1)

        p.sendline("echo $SANDBOX_STAGE")
        p.expect("local", timeout=1)

        change_file(Path("env_comm.py"), 0.5, 14, '        self._name = "new"\n')
        new_prompt = self.prompt.replace(b"sandbox", b"new")
        p.expect(new_prompt, timeout=1)

        p.sendline("echo $NEW_STAGE")
        p.expect("local", timeout=1)

        p.sendline("echo $SANDBOX_STAGE")
        p.expect(new_prompt, timeout=1)
        p.sendcontrol("d")

    def test_hot_reload_child_dir(self):
        p = spawn("envo --init")
        p.expect(self.prompt, timeout=1)
        p.sendcontrol("d")

        Path("./test_dir").mkdir()
        os.chdir("./test_dir")

        p = spawn("envo")
        p.expect(self.prompt, timeout=1)

        change_file(Path("../env_comm.py"), 0.5, 6, "\n")
        p.expect(self.prompt, timeout=5)
        p.sendcontrol("d")

    def test_hot_reload_error(self):
        p = spawn("envo --init")
        p.expect(self.prompt, timeout=1)

        file_before = Path("env_comm.py").read_text()

        change_file(Path("env_comm.py"), 0.5, 9, "    test_var: int\n")
        p.expect(r'.*Env variable "sandbox.test_var" is not set!.*', timeout=5)

        Path("env_comm.py").write_text(file_before)
        p.expect(self.prompt)

        p.sendcontrol("d")

        assert Path("env_comm.py").exists()
        assert Path("env_local.py").exists()

    def test_autodiscovery(self):
        p = spawn("envo --init")
        p.expect(self.prompt, timeout=1)
        p.sendcontrol("d")

        Path("./test_dir").mkdir()
        os.chdir("./test_dir")

        p = spawn("envo")
        p.sendline("echo test")
        p.expect(self.prompt, timeout=1)
        p.sendcontrol("d")

        assert list(Path(".").glob(".*")) == []

    def test_init_nested(self):
        expected_files = ["env_comm.py", "env_local.py"]

        p = spawn("envo --init")
        p.expect(self.prompt, timeout=1)
        p.sendcontrol("d")

        Path("./test_dir").mkdir()
        os.chdir("./test_dir")
        for f in expected_files:
            if Path(f).exists():
                Path(f).unlink()

        nested_prompt = r"🐣\(test_dir\).*".encode("utf-8")
        p = spawn("envo --init")
        p.sendline("echo test")
        p.expect(nested_prompt, timeout=1)
        p.sendcontrol("d")

        for f in expected_files:
            assert Path(f).exists()
            Path(f).unlink()

    def test_env_persists_in_bash_scripts(self):
        p = spawn("envo --init")
        p.expect(self.prompt, timeout=1)

        file = Path("script.sh")
        file.touch()
        file.write_text("echo $SANDBOX_ROOT\n")

        p.sendline("bash script.sh")
        p.expect(str(Path(".").absolute()), timeout=1)
