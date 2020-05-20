import os
from pathlib import Path

import pexpect
import pytest
from pangea.comm.test_utils import spawn, strs_in_regex
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
        shell.expect(pexpect.EOF)

    def test_cluster_commands(self, shell):
        shell.sendline("./cluster.py -h")
        shell.expect(".*help.*")

    def test_cluster_short(self, shell):
        shell.sendline("cl -h")
        shell.expect(".*help.*")

    def test_install_deps(self, shell):
        shell.sendline("cl install_deps")
        shell.expect(r"Installing dependencies")
        shell.expect(r"Installing kubectl", timeout=60)
        shell.expect(r"Installing kind", timeout=60)
        shell.expect(r"Installing skaffold", timeout=60)
        shell.expect(r"Installing hostess", timeout=60)
        shell.expect(r"Installing helm", timeout=60)

        shell.sendline("kubectl version")
        shell.expect(
            r'.*Client Version: version\.Info\{Major:"1", Minor:"17", GitVersion:"v1\.17\.0".*',
            timeout=60,
        )

        shell.sendline("kind version")
        shell.expect(r"kind v0\.7\.0 go1\.13\.6 linux/amd64")

        shell.sendline("skaffold version")
        shell.expect(r"v1\.6\.0")

        shell.sendline("hostess --version")
        shell.expect(r"hostess version 0\.3\.0", timeout=2)

        shell.sendline("helm version")
        shell.expect(r'Client: &version\.Version\{SemVer:"v2\.15\.2", .*')

    def test_bootstrap(self, deps, shell):
        shell.sendline("cl bootstrap")
        shell.expect(r"Installing dependencies")
        shell.expect(r"kubectl already exists")
        shell.expect(r"kind already exists")
        shell.expect(r"skaffold already exists")
        shell.expect(r"hostess already exists")
        shell.expect(r"helm already exists")

        shell.expect(r"Creating kind cluster")
        shell.expect(r"Initializing helm", timeout=300)
        shell.expect(r"Adding hosts to /etc/hosts file", timeout=300)
        shell.expect(r"Cluster is ready", timeout=10)

        shell.sendline("kubectl get nodes")
        shell.expect(
            r".*sandbox\-test\-control\-plane   Ready    master   .*   v1\.15\.7.*",
            timeout=3,
        )

    def test_deploy(self, deps, bootstrap, shell):
        shell.sendline("cl deploy")
        shell.expect(r'Deploying to "test"')
        shell.expect(
            strs_in_regex(["Deploy", "ingress", "namespace", "system"]), timeout=10
        )
        shell.expect(r"All done", timeout=300)


class TestApps:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init):
        pass

    def test_create_app_already_exists(self, shell):
        shell.sendline("cl createapp ingress flesh my_ingress")
        shell.expect(strs_in_regex(['"my_ingress"', '"flesh"', '"ingress"', "created"]))

        shell.sendline("cl createapp ingress flesh my_ingress")
        shell.expect(
            strs_in_regex(['"my_ingress"', '"flesh"', '"ingress"', "already exists"])
        )

    def test_create_app_unknown_app(self, shell):
        shell.sendline("cl createapp ingresst flesh my_ingress")
        shell.expect(strs_in_regex(['"ingresst"', "not exist"]))

    def test_create_app(self, shell):
        shell.sendline("cl createapp registry system registry")
        shell.expect(strs_in_regex(['"registry"', '"registry"', '"system"', "created"]))

        app_dir = Path("system/registry")

        assert app_dir.exists()
        assert (app_dir / "values.yaml").exists()
        assert (app_dir / "__init__.py").exists()
        assert (app_dir / "env_local.py").exists()
        assert (app_dir / "env_test.py").exists()
        assert (app_dir / "env_stage.py").exists()
        assert (app_dir / "env_prod.py").exists()

        os.chdir(str(app_dir))

        e = spawn("envo")
        e.expect()
