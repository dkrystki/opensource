from pangea.apps import App, AppEnv
from pangea.cluster import Cluster
from pangea.kube import Namespace

__all__ = ["Ingress"]


class Ingress(App):
    def __init__(self, cluster: Cluster, namespace: Namespace, env: AppEnv):
        super().__init__(cluster, namespace, env=env)

    def deploy(self) -> None:
        super().deploy()

        self.namespace.helm(self.env.get_name()).install(
            "stable/nginx-ingress",
            values=self.env.root / f"values.{self.env.stage}.yaml",
            version=self.env.meta.version,
        )

        # Kind needs it
        self.namespace.kubectl(
            """patch deployments ingress-controller -p '{"spec":{"template":{"spec":{"containers":["""
            """{"name":"nginx-ingress-controller","ports":[{"containerPort":80,"hostPort":80},"""
            """{"containerPort":443,"hostPort":443}]}]}}}}'"""
        )

    def delete(self) -> None:
        super().delete()

        self.namespace.helm(self.env.get_name()).delete()
