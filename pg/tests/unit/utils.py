import sys
from importlib import import_module, reload


from envo import Env
from pangea.cluster import Cluster


def command(*args):
    sys.argv = ("pangea",) + args
    from pangea import scripts

    scripts._main()
    sys.argv = []


def env() -> Env:
    reload(import_module("sandbox.env_comm"))
    env = reload(import_module("sandbox.env_test")).Env()
    return env


def cluster() -> Cluster:
    Sandbox = import_module(f"sandbox.cluster").Sandbox
    cluster = Sandbox(env=env())
    return cluster
