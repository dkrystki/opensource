from pathlib import Path

import comm
from comm import test_utils


class TestUnit:
    def test_dir_name_to_class_name(self):
        assert comm.dir_name_to_class_name("sample_dir") == "SampleDir"
        assert comm.dir_name_to_class_name(".sample_dir") == "SampleDir"
        assert comm.dir_name_to_class_name("sample dir") == "SampleDir"


class TestSandbox:
    @classmethod
    def teardown_class(cls):
        assert not Path("sandbox").exists()

    def test_in_sandbox(self, sandbox):
        assert Path(".").absolute().name == "sandbox"
        assert list(Path(".").glob("*")) == []
        Path("test.txt").touch()
        assert list(Path(".").glob("*")) != []


class TestUtils:
    def test_spawn(self):
        s = test_utils.spawn("/bin/bash")
        s.expect(".*$.*")
