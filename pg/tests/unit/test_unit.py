import os
from pathlib import Path

import pytest
from pangea.cluster import Cluster
from pangea.comm.test_utils import flake8
from pangea.kube import Kube

from . import utils
from .utils import command


class TestKube:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init, mock_run, env, assert_no_stderr):
        env.activate()
        yield
        assert_no_stderr()

    def test_get_namespaces(self, cluster):
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

    def test_nodes_ready(self, cluster, mocker):
        assert Kube.Node.is_all_ready()

        magic_mock2 = mocker.patch("pangea.kube.run")
        magic_mock2.return_value = [
            """NAME                         STATUS     ROLES    AGE   VERSION
               sandbox-test-control-plane   NotReady   master   12s   v1.15.7"""
        ]

        assert not Kube.Node.is_all_ready()


class TestPangea:
    @pytest.fixture(autouse=True)
    def setup(self, sandbox, version, init, mock_run, assert_no_stderr):
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
    def setup(self, sandbox, version, init, mock_run, env, assert_no_stderr):
        env.activate()
        yield
        assert_no_stderr()

    def test_get_ip(self, cluster, bootstrap):
        assert cluster.device.get_ip() == "172.18.0.2"

    def test_namespaces(self, cluster):
        assert "system" in cluster.namespaces
        assert len(cluster.namespaces) == 1

    def test_bootstrap(self, cluster, bootstrap):
        assert Path("kind.test.yaml").exists()

    def test_create_app_not_exists(self, cluster, bootstrap):
        with pytest.raises(Cluster.ClusterException) as exc:
            cluster.createapp("non_existent_app", "flesh", "my_app")

        assert str(exc.value) == 'App "non_existent_app" does not exist 😓'

    def test_create_app(self, cluster, bootstrap, add_registry_app):
        cluster.createapp("registry", "system", "registry")

        app_dir = Path("system/registry")

        assert app_dir.exists()
        assert (app_dir / "values.yaml").exists()
        assert (app_dir / "__init__.py").exists()
        assert (app_dir / "env_local.py").exists()
        assert (app_dir / "env_test.py").exists()
        assert (app_dir / "env_stage.py").exists()
        assert (app_dir / "env_prod.py").exists()

    def test_deploy(self, cluster, add_registry_app, bootstrap, cluster_ip):
        cluster.createapp("registry", "system", "registry")
        # we have to recreate cluster object due changing env_comm.py in registry_app fixture
        cluster = utils.cluster()
        cluster.deploy()

        assert Path("kind.test.yaml").exists()
        assert Path(".hosts").exists()
        assert (
            Path(os.environ["HOSTALIASES"]).read_text()
            == f"{cluster_ip} sandbox.registry.test"
        )

        ingress_dir = Path("system/ingress")
        assert ingress_dir.exists()
        assert (ingress_dir / "values.yaml").exists()
        assert (ingress_dir / "values.test.yaml").exists()
        assert (ingress_dir / "__init__.py").exists()
        assert (ingress_dir / "env_local.py").exists()
        assert (ingress_dir / "env_test.py").exists()
        assert (ingress_dir / "env_stage.py").exists()
        assert (ingress_dir / "env_prod.py").exists()

        registry_dir = Path("system/registry")
        assert registry_dir.exists()
        assert (registry_dir / "values.yaml").exists()
        assert (registry_dir / "values.test.yaml").exists()
        assert (registry_dir / "__init__.py").exists()
        assert (registry_dir / "env_local.py").exists()
        assert (registry_dir / "env_test.py").exists()
        assert (registry_dir / "env_stage.py").exists()
        assert (registry_dir / "env_prod.py").exists()
