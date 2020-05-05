import fire

from dataclasses import dataclass
from importlib import import_module

from pangea import cluster
import env_comm


class Sandbox(cluster.Cluster):
    @dataclass
    class Links(cluster.Cluster.Links):
        pass

    @dataclass
    class Sets(cluster.Cluster.Sets):
        pass

    def __init__(self, li: Links, se: Sets, env: env_comm.Env):
        super().__init__(li, se, env)

        self.env = env

        self.aux = self.create_namespace("aux")
        self.flesh = self.create_namespace("flesh")


def get_current_cluster() -> Sandbox:
    import os

    env = import_module(f"env_{os.environ['CG_STAGE']}").Env()

    current_cluster = Sandbox(
        li=Sandbox.Links(), se=Sandbox.Sets(deploy_ingress=True), env=env
    )
    return current_cluster


if __name__ == "__main__":
    fire.Fire(get_current_cluster())
