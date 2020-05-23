import inspect
import os
from pathlib import Path
from typing import List

from tests.unit import utils

import pytest_socket
from envo import Env
from pangea.cluster import Cluster
from pytest import fixture
from unit import utils

test_root = Path(os.path.realpath(__file__)).parent
root = test_root.parent


def pytest_runtest_setup():
    pytest_socket.disable_socket()


@fixture
def init() -> None:
    utils.command("--init")


@fixture
def bootstrap() -> None:
    cluster = utils.cluster()
    cluster.bootstrap()


@fixture
def cluster_ip() -> str:
    return "172.18.0.2"


@fixture
def mock_run(mocker, cluster_ip) -> None:
    def ret(string: str) -> List[str]:
        string = inspect.cleandoc(string)
        return [string]

    def run(
        command: str,
        ignore_errors: bool = False,
        print_output: bool = False,
        progress_bar: bool = False,
    ) -> List[str]:
        if command == "kubectl describe nodes sandbox-test":
            return ret(
                f"""
            Addresses:
              InternalIP:  {cluster_ip}
              Hostname:    sandbox-test-control-plane
            Capacity:"""
            )
        if command == "kubectl get nodes":
            return ret(
                """
                NAME                         STATUS     ROLES    AGE   VERSION
                sandbox-test-control-plane   Ready      master   12s   v1.15.7
                """
            )

        if command == "kubectl get namespaces":
            return ret(
                """
            NAME                 STATUS   AGE
            aux                  Active   9h
            default              Active   10h
            flesh                Active   9h
            kube-node-lease      Active   10h
            kube-public          Active   10h
            kube-system          Active   10h
            local-path-storage   Active   10h
            system               Active   10h
            """
            )
        return []

    magic_mock1 = mocker.patch("sandbox.cluster.cluster.run")
    magic_mock1.side_effect = run
    magic_mock2 = mocker.patch("pangea.kube.run")
    magic_mock2.side_effect = run
    magic_mock3 = mocker.patch("pangea.deps.run")
    magic_mock3.side_effect = run
    magic_mock4 = mocker.patch("pangea.devices.run")
    magic_mock4.side_effect = run


@fixture
def env() -> Env:
    return utils.env()


@fixture
def cluster() -> Cluster:
    return utils.cluster()
