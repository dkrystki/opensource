import os
from pathlib import Path

import pexpect
import pytest
from envo.comm.utils import spawn
from pexpect import run
from tests.utils import change_file


class TestE2e:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, prompt, init):
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
        new_content = Path("env_comm.py").read_text().replace("sandbox", "new")
        change_file(Path("env_comm.py"), 0.5, new_content)
        new_prompt = envo_prompt.replace(b"sandbox", b"new")
        shell.expect(new_prompt, timeout=2)

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

    def test_multiple_instances(self, envo_prompt):
        from envo.comm.utils import shell

        shells = [shell() for i in range(6)]

        new_content = Path("env_comm.py").read_text() + "\n"
        change_file(Path("env_comm.py"), 0.5, new_content)

        [s.expect(envo_prompt, timeout=6) for s in shells]

    def test_env_persists_in_bash_scripts(self, shell):
        file = Path("script.sh")
        file.touch()
        file.write_text("echo $SANDBOX_ROOT\n")

        shell.sendline("bash script.sh")
        shell.expect(str(Path(".").absolute()), timeout=1)


class TestNested:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, prompt, init, child_env):
        pass

    def test_init(self, envo_prompt):
        from envo.comm.utils import spawn

        os.chdir("child")

        s = spawn("envo test")
        nested_prompt = envo_prompt.replace(b"sandbox", b"sandbox.child")

        s.expect(nested_prompt, timeout=1)

    def test_child_parent_prompt(self):
        os.chdir("child")

        s = spawn("envo test")
        s.expect(r"🛠\(sandbox.child\).*".encode("utf-8"), timeout=2)

    def test_hot_reload(self, envo_prompt):
        from envo.comm.utils import spawn

        os.chdir("child")

        s = spawn("envo test")
        nested_prompt = envo_prompt.replace(b"sandbox", b"sandbox.child")
        s.expect(nested_prompt, timeout=1)

        child_file = Path("env_comm.py")
        content = child_file.read_text()
        content = content.replace("child", "ch")
        child_file.write_text(content)

        new_prompt1 = nested_prompt.replace(b"child", b"ch")
        s.expect(new_prompt1, timeout=1)

        parent_file = Path("../env_comm.py")
        content = parent_file.read_text()
        content = content.replace("sandbox", "sb")
        parent_file.write_text(content)

        new_prompt2 = new_prompt1.replace(b"sandbox", b"sb")
        s.expect(new_prompt2, timeout=1)
