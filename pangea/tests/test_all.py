import sys
from pathlib import Path

import pexpect
import pytest

import pangea.scripts


@pytest.mark.usefixtures("in_sandbox")
class TestUnit:
    def test_creating(self, pg, flake8, mypy):
        pg("--init")

        assert Path("cluster.py").exists()
        assert Path("env_comm.py").exists()
        assert Path("env_local.py").exists()
        assert Path(".deps").exists()
        assert Path(".bin").exists()

        flake8()
        # mypy()

    def test_bootstrap(self, pg):
        pg("--init")

        assert Path("cluster.py").exists()
        assert Path("env_comm.py").exists()
        assert Path("env_local.py").exists()
        assert Path(".deps").exists()
        assert Path(".bin").exists()

        # mypy()


@pytest.mark.usefixtures("in_sandbox")
class TestE2e:
    @pytest.fixture(autouse=True)
    def setup(self, prompt, envo_prompt, , spawn):
        self.prompt = prompt
        self.envo_prompt = envo_prompt

        self.bash = spawn("bash")
        self.bash.sendline("pangea --init")
        self.bash.expect(self.prompt, timeout=1)

        self.envo = spawn("envo")
        self.envo.expect(self.envo_prompt, timeout=1)

    def test_envs(self):
        self.envo.sendcontrol("d")
        self.envo.expect(pexpect.EOF, timeout=1)

    def test_cluster_util(self):
        self.envo.sendline("./cluster.py -h")
