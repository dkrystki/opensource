import os
from pathlib import Path

import pexpect
import pytest
from pangea.comm.test_utils import spawn, strs_in_regex
from pexpect import run


class TestDnsServer:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, docker, dns_server):
        self.image = f"{dns_server.image_name}:{dns_server.se.version}"

        hosts_before = dns_server.get_hosts()

        if dns_server.is_running():
            dns_server.stop()

        yield
        dns_server.update_hosts(hosts_before)
        if dns_server.is_running():
            dns_server.stop()

    def test_install(self, docker, dns_server):
        if dns_server.exists():
            dns_server.uninstall()

        dns_server.install()
        assert dns_server.exists()
        assert dns_server.image_exists()
        assert docker.images.list(name=self.image) is not None

    def test_start(self, docker, dns_server):
        dns_server.install()
        dns_server.start()

        assert (
            docker.containers.list(filters={"name": dns_server.container_name})
            is not None
        )
        assert dns_server.is_running()

    def test_stop(self, docker, dns_server):
        dns_server.install()
        dns_server.start()
        dns_server.stop()

        assert (
            docker.containers.list(filters={"name": dns_server.container_name})
            is not None
        )
        assert not dns_server.is_running()

    def test_adding_hosts(self, dns_server):
        dns_server.install()
        dns_server.start()

        hosts = {}
        hosts["server1.test"] = "127.0.0.1"
        hosts["server2.test"] = "192.232.88.2"

        dns_server.update_hosts(hosts)

        ping1 = run("ping server1.test -c 1 -W 1")
        assert b"0% packet loss" in ping1
        assert b"127.0.0.1" in ping1

        ping2 = run("ping server2.test -c 1 -W 1")
        assert b"100% packet loss" in ping2
        assert b"192.232.88.2" in ping2

    def test_remove_host(self, dns_server, dns_test_host):
        dns_server.install()
        dns_server.start()

        ping_before = run("ping server.test -c 1 -W 1")
        assert b"0% packet loss" in ping_before
        assert b"127.0.0.1" in ping_before

        hosts = dns_server.get_hosts()

        del hosts["server.test"]

        dns_server.update_hosts(hosts)
        ping_after = run("ping server.test -c 1 -W 1")
        assert b"Name or service not known" in ping_after


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

    def test_install_deps(self, uninstall_dns_server, shell, docker):
        shell.sendline("cl install_deps")
        shell.expect(r"Installing dependencies")
        shell.expect(r"Installing kubectl", timeout=60)
        shell.expect(r"Installing kind", timeout=60)
        shell.expect(r"Installing skaffold", timeout=60)
        shell.expect(r"Installing helm", timeout=60)
        shell.expect(r"Installing dns_server", timeout=60)

        shell.sendline("kubectl version")
        shell.expect(
            r'Client Version: version\.Info\{Major:"1", Minor:"17", GitVersion:"v1\.17\.0".*',
            timeout=60,
        )

        shell.sendline("kind version")
        shell.expect(r"kind v0\.8\.1 go1\.14\.2 linux/amd64")

        shell.sendline("skaffold version")
        shell.expect(r"v1\.6\.0")

        shell.sendline("hostess --version")
        shell.expect(r"hostess version 0\.3\.0", timeout=2)

        shell.sendline("helm version")
        shell.expect(r'version.BuildInfo{Version:"v3\.2\.1"')

        assert docker.images.list(name="defreitas/dns-proxy-server:2.19.0")

    def test_bootstrap(self, deps, shell):
        shell.sendline("cl bootstrap")
        shell.expect(r"Installing dependencies")
        shell.expect(r"kubectl already exists")
        shell.expect(r"kind already exists")
        shell.expect(r"skaffold already exists")
        shell.expect(r"helm already exists")
        shell.expect(r"dns_server already exists")

        shell.expect(r"Creating kind cluster")
        shell.expect(r"Waiting for nodes", timeout=120)
        shell.expect(r"Cluster is ready", timeout=60)

        shell.sendline("kubectl get nodes")
        shell.expect(
            r".*sandbox\-test\-control\-plane   Ready    master   .*   v1\.15\.7.*",
            timeout=1,
        )

    def test_deploy(self, deps, bootstrap, docker_images, shell):
        shell.sendline("cl deploy")
        shell.expect(r'Deploying to "test"')
        shell.expect(
            strs_in_regex(["Deploy", "ingress", "namespace", "system"]), timeout=60
        )
        shell.expect(strs_in_regex(["Adding", "hosts"]), timeout=60)
        shell.expect(r"All done", timeout=300)


class TestApps:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init):
        pass

    def test_create_already_exists(self, shell):
        shell.sendline("cl createapp ingress flesh my_ingress")
        shell.expect(strs_in_regex(['"my_ingress"', '"flesh"', '"ingress"', "created"]))

        shell.sendline("cl createapp ingress flesh my_ingress")
        shell.expect(
            strs_in_regex(['"my_ingress"', '"flesh"', '"ingress"', "already exists"])
        )

    def test_create_unknown(self, shell):
        shell.sendline("cl createapp ingresst flesh my_ingress")
        shell.expect(strs_in_regex(['"ingresst"', "not exist"]))

    def test_create(self, shell, envo_prompt):
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

        e = spawn("envo test")
        new_propmp = envo_prompt.replace(b"sandbox", b"sandbox.registry")
        e.expect(new_propmp)

    def test_deploy(self, deps, bootstrap, docker_images, shell, create_registry_app):
        shell.sendline("cl deploy")

        shell.expect(
            strs_in_regex(["Deploy", "registry", "namespace", "system"]), timeout=60
        )

        shell.expect(r"All done", timeout=300)

        shell.sendline("curl sandbox.registry.test/v2/")
        shell.expect(
            r'{"errors":\[{"code":"UNAUTHORIZED","message":"authentication required","detail":null}\]}'
        )
