import pexpect
import pytest


class TestPangea:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init):
        pass

    def test_envs(self, shell):
        shell.sendcontrol("d")
        shell.expect(pexpect.EOF, timeout=1)

    def test_cluster_commands(self, shell):
        shell.sendline("./cluster.py -h")
        shell.expect("help", timeout=1)

    def test_version(self, shell):
        shell.sendline("pangea --version")
        shell.expect("")
