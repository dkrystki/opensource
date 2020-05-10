import pexpect
import pytest


class TestPangea:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init):
        pass

    def test_envs(self, shell):
        shell.sendcontrol("d")
        shell.expect(pexpect.EOF, timeout=1)

    def test_cluster_commands(self):
        self.envo.sendline("./cluster.py -h")
        self.envo.expect("help", timeout=1)

    def test_version(self):
        self.envo.sendline("pangea --version")
        self.envo.expect("")
