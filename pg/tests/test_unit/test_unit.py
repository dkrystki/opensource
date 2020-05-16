from pathlib import Path

import pytest
from pangea.cluster import Cluster
from pangea.comm.utils import flake8
from pangea.kube import Kube

from .utils import command


class TestKube:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init, env, assert_no_stderr):
        env.activate()
        yield
        assert_no_stderr()

    def test_get_namespaces(self, cluster):
        cluster.bootstrap()
        assert Kube.Namespace.list() == [
            "aux",
            "default",
            "flesh",
            "kube-node-lease",
            "kube-public",
            "kube-system",
            "local-path-storage",
            "system",
        ]


class TestPangea:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init, assert_no_stderr):
        yield
        assert_no_stderr()

    def test_creating(self):
        assert Path("cluster.py").exists()
        assert Path("env_comm.py").exists()
        assert Path("env_local.py").exists()
        assert Path(".deps").exists()
        assert Path(".bin").exists()

        flake8()
        # mypy()

    def test_version(self, capsys):
        command("--version")
        captured = capsys.readouterr()
        assert captured.out == "1.2.3\n"

    def test_init(self):
        assert Path("cluster.py").exists()
        assert Path("env_comm.py").exists()
        assert Path("env_local.py").exists()
        assert Path(".deps").exists()
        assert Path(".bin").exists()

        # mypy()


class TestCluster:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init, env, assert_no_stderr):
        env.activate()
        yield
        assert_no_stderr()

    def test_get_ip(self, cluster):
        cluster.bootstrap()
        assert cluster.device.get_ip() == "172.18.0.2"

    def test_bootstrap(self, cluster):
        cluster.bootstrap()

        assert Path("kind.test.yaml").exists()

    def test_create_app_not_exists(self, cluster):
        cluster.bootstrap()

        with pytest.raises(Cluster.ClusterException) as exc:
            cluster.createapp("non_existent_app", "my_app")

        assert str(exc.value) == 'App "non_existent_app" does not exist.'

    def test_create_app(self, cluster):
        cluster.bootstrap()
        cluster.createapp("ingress", "my_ingress")

        assert Path("ingress").exists()
        assert Path("ingress/values.yaml").exists()
        assert Path("ingress/__init__.py").exists()
        assert Path("ingress/env_local.py").exists()
        assert Path("ingress/env_test.py").exists()
        assert Path("ingress/env_stage.py").exists()
        assert Path("ingress/env_prod.py").exists()

    def test_deploy(self, cluster):
        cluster.bootstrap()
        cluster.deploy()

        assert Path("kind.test.yaml").exists()
