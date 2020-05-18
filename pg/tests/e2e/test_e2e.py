from pathlib import Path

import pexpect
import pytest
from pangea.comm.test_utils import strs_in_regex
from pexpect import run


class TestPangea:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version):
        pass

    def test_init(self, init):
        assert init == (
            "\x1b[1mCreated cluster 🍰!\x1b[0m\r\n"
            '\x1b[1mInstance "ingress" of app "ingress" has been created in namespace "system" 🍰\x1b[0m\r\n'
            '\x1b[1mActivate 🐣 local environment with "envo"\x1b[0m\r\n'
        )

    def test_version(self):
        ver = run("pangea --version").decode("utf-8")
        assert ver == "1.2.3\r\n"


class TestCluster:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init):
        pass

    def test_envs(self, shell):
        shell.sendcontrol("d")
        shell.expect(pexpect.EOF, timeout=1)

    def test_cluster_commands(self, shell):
        shell.sendline("./cluster.py -h")
        shell.expect(".*help.*", timeout=1)

    def test_cluster_short(self, shell):
        shell.sendline("cl -h")
        shell.expect(".*help.*", timeout=1)

    def test_create_app_already_exists(self, shell):
        shell.sendline("cl createapp ingress flesh my_ingress")
        shell.expect(
            strs_in_regex(['"my_ingress"', '"flesh"', '"ingress"', "created"]),
            timeout=1,
        )

        shell.sendline("cl createapp ingress flesh my_ingress")
        shell.expect(
            strs_in_regex(['"my_ingress"', '"flesh"', '"ingress"', "already exists"]),
            timeout=1,
        )

    def test_create_app_unknown_app(self, shell):
        shell.sendline("cl createapp ingresst flesh my_ingress")
        shell.expect(strs_in_regex(['"ingresst"', "not exist"]), timeout=1)

    def test_create_app(self, shell):
        shell.sendline("cl createapp ingress flesh my_ingress")
        shell.expect(
            strs_in_regex(['"my_ingress"', '"ingress"', '"flesh"', "created"]),
            timeout=1,
        )

        assert Path("my_ingress").exists()
        assert Path("my_ingress/values.yaml").exists()
        assert Path("my_ingress/__init__.py").exists()
        assert Path("my_ingress/env_local.py").exists()
        assert Path("my_ingress/env_test.py").exists()
        assert Path("my_ingress/env_stage.py").exists()
        assert Path("my_ingress/env_prod.py").exists()

    def test_install_deps(self, shell):
        shell.sendline("cl bootstrap")
        shell.expect(r"Installing dependencies", timeout=1)
        shell.expect(r"Installing kubectl", timeout=1)
        shell.expect(r"Installing skaffold", timeout=60)
        shell.expect(r"Installing hostess", timeout=60)
        shell.expect(r"Installing helm", timeout=60)

    def test_bootstrap(self, deps, shell):
        shell.sendline("cl bootstrap")
        shell.expect(r"Installing dependencies", timeout=1)
        shell.expect(r"kubectl already exists", timeout=1)
        shell.expect(r"skaffold already exists", timeout=1)
        shell.expect(r"hostess already exists", timeout=1)
        shell.expect(r"helm already exists", timeout=1)

        shell.expect(r"Creating kind cluster", timeout=1)
        shell.expect(r"Initializing helm", timeout=300)
        shell.expect(r"Adding hosts to /etc/hosts file", timeout=300)
        shell.expect(r"Cluster is ready", timeout=10)

        shell.sendline("kubectl get nodes")
        shell.expect(
            r".*sandbox-test-control-plane   Ready    master   .*   v1.15.7.*",
            timeout=3,
        )
