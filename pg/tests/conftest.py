import os
from importlib import import_module, reload
from pathlib import Path

from envo import Env
from pangea.cluster import Cluster
from pytest import fixture

test_root = Path(os.path.realpath(__file__)).parent
root = test_root.parent

pytest_plugins = [
    "pangea.comm.fixtures",
]


@fixture
def version() -> None:
    file = root / "pangea/__version__.py"
    file.touch()
    file.write_text('__version__ = "1.2.3"')

    yield

    file.unlink()


@fixture
def env() -> Env:
    reload(import_module("sandbox.env_comm"))
    env = reload(import_module("sandbox.env_test")).Env()
    return env


@fixture
def cluster(env, mock_run) -> Cluster:
    Sandbox = import_module(f"sandbox.cluster").Sandbox
    cluster = Sandbox(li=Sandbox.Links(), se=Sandbox.Sets(deploy_ingress=True), env=env)
    return cluster
