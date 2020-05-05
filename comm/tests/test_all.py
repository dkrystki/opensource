from pathlib import Path

from plasma_comm import comm


class TestUnit:
    def test_dir_name_to_class_name(self):
        assert comm.dir_name_to_class_name("sample_dir") == "SampleDir"
        assert comm.dir_name_to_class_name(".sample_dir") == "SampleDir"
        assert comm.dir_name_to_class_name("sample dir") == "SampleDir"


class TestSandbox:
    @classmethod
    def teardown_class(cls):
        assert not Path("sandbox").exists()

    def test_in_sandbox(self, in_sandbox):
        assert Path(".").absolute().name == "sandbox"
        assert list(Path(".").glob("*")) == []
        Path("test.txt").touch()
        assert list(Path(".").glob("*")) != []
