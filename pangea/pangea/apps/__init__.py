import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jinja2 import Template
from loguru import logger

from typing import TYPE_CHECKING, Dict, Any

from pangea.cluster import ClusterEnv
from pangea.kube import Namespace

from pangea.devops import run
from envo import Env

import environ

environ = environ.Env()


@dataclass
class AppEnv(Env):
    app_name: str = None

    def __init__(self, root: Path):
        super().__init__(root)


class App:
    @dataclass
    class Sets:
        name: str
        root: Path

    @dataclass
    class Links:
        namespace: "Namespace"

    def __init__(self, se: Sets, li: Links) -> None:
        self.se = se
        self.li = li

    def chdir_to_root(self):
        os.chdir(str(self.se.root))

    def deploy(self) -> None:
        # TODO: only create when needed
        self.li.namespace.create()
        logger.info(f"🚀Deploying {self.se.name}.")
        self.chdir_to_root()

    def terminal(self) -> None:
        pass

    def delete(self) -> None:
        logger.info(f"Delete {self.se.name}.")
        self.chdir_to_root()

    def prepare(self) -> None:
        """
        Prepare app. Prebuild images etc.
        :return:
        """
        logger.info(f'Preparing app "{self.se.name}"')


class Image:
    @dataclass
    class Sets:
        tag: str

    @dataclass
    class Links:
        registry_env: ClusterEnv.Registry

    def __init__(self, li: Links, se: Sets):
        self.li = li
        self.se = se

    def push(self) -> None:
        env = self.li.registry_env
        run(f"""
            docker login {env.address} \\
            --username {env.username} -p{env.password}
            docker push {self.se.tag}
            """, print_output=False)


class Dockerfile:
    @dataclass
    class Sets:
        template: Path
        out_path: Path
        base_image: str

    @dataclass
    class Links:
        app_env: AppEnv
        cluster_env: ClusterEnv

    def __init__(self, li: Links, se: Sets):
        self.li = li
        self.se = se

    def render(self):
        template = Template(self.se.template.read_text())
        context = {
            "env": self.li.app_env,
            "base_image": f"{self.se.base_image}"
        }
        self.se.out_path.write_text(template.render(**context))

    def build(self, tag: str):
        run(f"""
            docker build -f {str(self.se.out_path)} -t {tag} {str(self.li.cluster_env.root)}
            """, print_output=False)

        return Image(se=Image.Sets(tag=tag),
                     li=Image.Links(registry_env=self.li.cluster_env.registry))


class DockerUtils:
    @dataclass
    class Sets:
        pass

    @dataclass
    class Links:
        env: AppEnv
        dockerfile: Dockerfile

    def __init__(self, se: Sets, li: Links) -> None:
        self.se = se
        self.li = li


class PythonUtils:
    @dataclass
    class Sets:
        root: Path

    @dataclass
    class Links:
        pass

    def __init__(self, se: Sets, li: Links) -> None:
        self.se = se
        self.li = li

    def flake8(self) -> None:
        os.chdir(str(self.se.root))
        run("flake8", print_output=True)
        logger.info(f"Flaky!")

    def isort(self) -> None:
        os.chdir(str(self.se.root))
        run("isort -rc .", print_output=True)

    def black(self) -> None:
        os.chdir(str(self.se.root))
        run("black .", print_output=True)

    def mypy(self) -> None:
        os.chdir(str(self.se.root))
        logger.info(f"Not implemented!")

    def format(self) -> None:
        self.isort()
        self.black()


class AppPythonUtils(PythonUtils):
    @dataclass
    class Sets(PythonUtils.Sets):
        src: Path

    @dataclass
    class Links(PythonUtils.Links):
        pass

    def __init__(self, se: Sets, li: Links) -> None:
        super().__init__(se, li)
        self.se = se
        self.li = li

    def test(self) -> None:
        os.chdir(str(self.se.src))
        run("poetry run pytest", print_output=True)

    def bootstrap_local_dev(self) -> None:
        os.chdir(str(self.se.src))
        logger.info(f"Bootstrapping local python development.")
        run(f"""
            poetry config virtualenvs.in-project true
            poetry config virtualenvs.create true
            poetry install
            """, print_output=True)


class NodeUtils:
    @dataclass
    class Sets:
        src: Path

    @dataclass
    class Links:
        pass

    def __init__(self, se: Sets, li: Links) -> None:
        self.se = se
        self.li = li

    def test(self) -> None:
        os.chdir(str(self.se.src))
        raise NotImplementedError()

    def test_devops(self) -> None:
        raise NotImplementedError()

    def test_bootstrap(self) -> None:
        raise NotImplementedError()

    def bootstrap_local_dev(self) -> None:
        raise NotImplementedError()


@dataclass
class SkaffoldAppEnv(AppEnv):
    app_name: str = None
    src: Path = None
    helm_release_name: str = None
    src_image: str = None
    dockerfile_templ: Path = None
    image_name: str = None

    def __init__(self):
        super().__init__()
        self.src = self.root / "flesh"

        # self.base_image = f"{self.cluster.registry.address}/{self.stage}/{self.app_name}-prebuild:latest"
        # self.image_name: str = f"{self.cluster.registry.address}/{self.stage}/{self.app_name}"


class SkaffoldApp(App):
    @dataclass
    class Sets(App.Sets):
        pass

    @dataclass
    class Links(App.Links):
        env: SkaffoldAppEnv
        cluster_env: ClusterEnv

    env: SkaffoldAppEnv
    dockerfile: Dockerfile
    skaffold_file: Path

    def __init__(self, se: Sets, li: Links) -> None:
        super().__init__(se, li)
        self.se = se
        self.li = li

        self.env = self.li.env

        self.dockerfile = Dockerfile(
            se=Dockerfile.Sets(template=self.env.dockerfile_templ,
                               out_path=Path(f"Dockerfile.{self.env.stage}"),
                               base_image=self.env.base_image),
            li=Dockerfile.Links(app_env=self.env, cluster_env=self.li.cluster_env)
        )

        self.skaffold_file = Path(f"skaffold.{self.env.stage}.yaml")

    def prepare(self) -> None:
        super().prepare()
        logger.info(f"Prebuilding {self.li.env.app_name}...")
        os.chdir(str(self.li.env.root))
        env = self.li.env
        dockerfile = Dockerfile(
            se=Dockerfile.Sets(template=self.dockerfile.se.template,
                               out_path=Path(f"{self.dockerfile.se.out_path}.prebuild"),
                               base_image=env.src_image),
            li=Dockerfile.Links(app_env=self.env, cluster_env=self.li.cluster_env)
        )
        dockerfile.render()
        image = dockerfile.build(tag=env.prebuild_image_name)
        image.push()

    def render(self, extra_context: Dict[str, Any] = None) -> None:
        self.chdir_to_root()

        self.dockerfile.render()

        template = Template((self.env.cluster.comm / "kubernetes/skaffold.yaml.templ").read_text())
        context = {
            "env": self.env,
            "image_name": self.env.image_name,
        }

        if extra_context:
            context.update(extra_context)

        self.skaffold_file.write_text(template.render(**context))

    def deploy(self) -> None:
        super().deploy()
        self.render()

        registry = self.env.cluster.registry
        logger.info("Building and deploying using skaffold.")

        os.environ["PL_IMAGE_NAME"] = self.env.image_name
        image_tag: str = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        os.environ["PL_IMAGE_TAG"] = image_tag

        image = f"{self.env.image_name}:{image_tag}"

        run(f"""
            docker login {registry.address} --username {registry.username} -p{registry.password}
            skaffold build -f {str(self.skaffold_file)} --insecure-registry {registry.address}
            docker push {image}
            skaffold deploy -f {str(self.skaffold_file)} --images {image}
            """, print_output=True)

    def dev(self) -> None:
        self.render(
            {
                "dev": True
            }
        )
        registry = self.env.cluster.registry

        run(f"""
            docker login {registry.address} --username {registry.username} -p{registry.password}
            skaffold dev -f {str(self.skaffold_file)} --verbosity debug
            """, print_output=True)
