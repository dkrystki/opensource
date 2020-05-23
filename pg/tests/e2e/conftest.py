import os
import shutil
from pathlib import Path

import pytest_socket
from docker import DockerClient
from pangea.comm.test_utils import strs_in_regex
from pangea.deps import DnsServer
from pexpect import run
from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent
root = test_root.parent


def pytest_runtest_setup():
    pytest_socket.socket_allow_hosts(["127.0.0.1", None])


@fixture
def init() -> str:
    return run("pangea --init").decode("utf-8")


@fixture
def bootstrap(shell) -> None:
    shell.sendline("cl bootstrap")
    shell.expect(r"Cluster is ready", timeout=120)


@fixture
def deps() -> None:
    shutil.rmtree(".deps")
    shutil.copytree(root.parent / ".deps", ".deps")


@fixture
def create_registry_app(shell) -> None:
    from tests.utils import add_registry_app

    shell.sendline("cl createapp registry system registry")
    shell.expect(strs_in_regex(['"registry"', '"registry"', '"system"', "created"]))
    add_registry_app()


@fixture
def docker_images() -> None:
    docker_images = [
        "quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.30.0",
        "k8s.gcr.io/defaultbackend-amd64:1.5",
    ]

    for i in docker_images:
        run(f"docker pull {i}")
        run(f"kind load docker-image {i} --name sandbox-test")


@fixture
def docker() -> DockerClient:
    from docker import from_env

    return from_env()


@fixture
def uninstall_dns_server(dns_server) -> DockerClient:
    if dns_server.exists():

        if dns_server.is_running():
            dns_server.stop()

        dns_server.uninstall()

    yield

    if dns_server.is_running():
        dns_server.stop()

    dns_server.uninstall()


@fixture
def dns_server() -> DnsServer:
    deps_dir = Path(".deps").absolute()
    deps_dir.mkdir(exist_ok=True)
    dns = DnsServer(DnsServer.Sets(deps_dir=deps_dir, version="2.19.0"))
    return dns


@fixture
def dns_test_host(dns_server):
    hosts = {}
    hosts["server.test"] = "127.0.0.1"

    dns_server.update_hosts(hosts)
