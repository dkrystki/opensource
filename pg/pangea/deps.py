from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from pangea.devops import run

__all__ = ["Dependency", "Kubectl", "Hostess", "Skaffold", "Helm", "Kind"]


class Dependency:
    @dataclass
    class Sets:
        deps_dir: Path
        version: str

    name: str

    def __init__(self, se: Sets) -> None:
        self.se = se

    def install(self) -> None:
        if self.exists():
            logger.opt(colors=True).info(f"<green>{self.name} already exists 👌</green>")
        else:
            logger.info(f"Installing {self.name} ⏳")

    def exists(self) -> bool:
        if (Path(self.se.deps_dir) / self.name).exists():
            return True
        else:
            return False


class Kubectl(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "kubectl"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        run(
            f"""
            cd /tmp
            curl -Lso kubectl \\
            "https://storage.googleapis.com/kubernetes-release/release/v{self.se.version}/bin/linux/amd64/kubectl"
            chmod +x kubectl
            mv kubectl {self.se.deps_dir}/kubectl
            """
        )


class Hostess(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "hostess"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        run(
            f"""
            cd /tmp
            curl -Lso hostess https://github.com/cbednarski/hostess/releases/download/v{self.se.version}/hostess_linux_386
            chmod u+x hostess
            mv hostess {self.se.deps_dir}/hostess
            """
        )


class Helm(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "helm"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        release_name = f"helm-v{self.se.version}-linux-386"
        run(
            f"""
            cd /tmp
            curl -Lso helm.tar.gz https://get.helm.sh/{release_name}.tar.gz
            tar -zxf helm.tar.gz
            mv linux-386/helm {self.se.deps_dir}/helm
            """
        )


class Skaffold(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "skaffold"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        run(
            f"""
            cd /tmp
            curl -Lso skaffold \\
                "https://storage.googleapis.com/skaffold/releases/v{self.se.version}/skaffold-linux-amd64"
            chmod +x skaffold
            mv skaffold {self.se.deps_dir}/skaffold
            """
        )


class Kind(Dependency):
    @dataclass
    class Sets(Dependency.Sets):
        pass

    name = "kind"

    def __init__(self, se: Sets) -> None:
        super().__init__(se)
        self.se = se

    def install(self) -> None:
        super().install()

        if self.exists():
            return

        run(
            f"""
            cd /tmp
            curl -Lso kind \\
                "https://github.com/kubernetes-sigs/kind/releases/download/v{self.se.version}/kind-$(uname)-amd64"
            chmod +x kind
            mv kind {self.se.deps_dir}/kind
            """
        )
