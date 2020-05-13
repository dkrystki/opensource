import os
from pathlib import Path

import pexpect
import pytest
from envo.comm.utils import spawn
from pexpect import run
from tests.utils import change_file, test_root


class TestE2e:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, prompt, e2e_init):
        pass

    def test_shell(self, shell, envo_prompt):
        shell.sendline("echo test")
        shell.expect(b"test.*" + envo_prompt, timeout=1)

        assert Path("env_comm.py").exists()
        assert Path("env_test.py").exists()

    def test_shell_exit(self, shell):
        shell.sendcontrol("d")
        shell.expect(pexpect.EOF, timeout=1)

    def test_dry_run(self):
        ret = run("envo test --dry-run", timeout=2)
        assert ret != b""

    def test_save(self):
        ret = run("envo test --save")
        assert b"Saved envs to .env_test" in ret
        assert Path(".env_test").exists()

    def test_hot_reload(self, shell, envo_prompt):
        new_content = Path("env_comm.py").read_text() + "\n"
        change_file(Path("env_comm.py"), 0.5, new_content)

        shell.expect(envo_prompt, timeout=5)

    def test_hot_reload_old_envs_gone(self, shell, envo_prompt):
        shell.sendline("echo $SANDBOX_STAGE")
        shell.expect("test", timeout=1)

        new_content = Path("env_comm.py").read_text().replace("sandbox", "new")
        change_file(Path("env_comm.py"), 0.5, new_content)
        new_prompt = envo_prompt.replace(b"sandbox", b"new")
        shell.expect(new_prompt, timeout=2)

        shell.sendline("echo $NEW_STAGE")
        shell.expect("test", timeout=1)

        shell.sendline("echo $SANDBOX_STAGE")
        shell.expect(new_prompt, timeout=1)

    def test_hot_reload_child_dir(self, shell, envo_prompt):
        Path("./test_dir").mkdir()
        os.chdir("./test_dir")

        new_content = Path("../env_comm.py").read_text() + "\n"
        change_file(Path("../env_comm.py"), 0.5, new_content)

        shell.expect(envo_prompt, timeout=5)

    def test_hot_reload_error(self, shell, envo_prompt):
        file_before = Path("env_comm.py").read_text()

        new_content = Path("env_comm.py").read_text()
        new_content = new_content.splitlines(keepends=True)
        new_content.insert(14, "    test_var: int\n\n")
        new_content = "".join(new_content)
        change_file(Path("env_comm.py"), 0.5, new_content)

        shell.expect(
            r'.*Reloading.*exit.*Detected errors!.*Variable "sandbox.test_var" is unset!.*',
            timeout=5,
        )

        Path("env_comm.py").write_text(file_before)
        shell.expect(envo_prompt)

    def test_autodiscovery(self, envo_prompt):
        from envo.comm.utils import shell

        Path("./test_dir").mkdir()
        os.chdir("./test_dir")

        s = shell()
        s.sendline("echo test")
        s.expect(envo_prompt, timeout=1)
        s.sendcontrol("d")

        assert list(Path(".").glob(".*")) == []

    def test_init_nested(self):
        from envo.comm.utils import spawn

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

    def test_env_persists_in_bash_scripts(self, shell):
        file = Path("script.sh")
        file.touch()
        file.write_text("echo $SANDBOX_ROOT\n")

        shell.sendline("bash script.sh")
        shell.expect(str(Path(".").absolute()), timeout=1)

    def test_child_parent_prompt(self):
        os.chdir(test_root / "parent_env/child_env")

        s = spawn("envo test")
        s.expect(r"🛠\(pa.ch\).*".encode("utf-8"), timeout=2)
