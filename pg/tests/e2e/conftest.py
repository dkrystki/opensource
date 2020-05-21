import os
import shutil
from pathlib import Path

from pexpect import run
from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent
root = test_root.parent


@fixture
def init() -> str:
    return run("pangea --init").decode("utf-8")


@fixture
def bootstrap(shell) -> None:
    shell.sendline("cl bootstrap")
    shell.expect(r"Cluster is ready", timeout=600)


@fixture
def deps() -> None:
    shutil.rmtree(".deps")
    shutil.copytree(root.parent / ".deps", ".deps")


@fixture
def docker_images() -> None:
    docker_images = [
        "quay.io/kubernetes-ingress-controller/nginx-ingress-controller:0.30.0",
        "k8s.gcr.io/defaultbackend-amd64:1.5",
    ]

    for i in docker_images:
        run(f"docker pull {i}")
        run(f"kind load docker-image {i} --name sandbox-test")
