import sys
from pathlib import Path

import pexpect
import pytest
from pangea.comm.utils import flake8, mypy, spawn


class TestPangea:
    @pytest.fixture(autouse=True)
    def setup(self, prompt, envo_prompt, sandbox, version):
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

    def test_cluster_commands(self):
        self.envo.sendline("./cluster.py -h")
        self.envo.expect("help", timeout=1)

    def test_version(self):
        self.envo.sendline("pangea --version")
        self.envo.expect("")
