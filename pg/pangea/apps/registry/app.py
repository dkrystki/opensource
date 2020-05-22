from pangea.apps import App, AppEnv
from pangea.cluster import Cluster
from pangea.kube import Namespace

__all__ = ["Registry"]


class Registry(App):
    def __init__(self, cluster: Cluster, namespace: Namespace, env: AppEnv):
        super().__init__(cluster, namespace, env=env)

    def deploy(self) -> None:
        super().deploy()

        self.namespace.helm(self.env.get_name()).install(
            "stable/docker-registry",
            values=self.env.root / f"values.{self.env.stage}.yaml",
            version=self.env.meta.version,
        )

    def delete(self) -> None:
        super().delete()

        self.namespace.helm(self.env.get_name()).delete()
