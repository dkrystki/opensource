from envo.comm import import_module_from_file

OpensourceEnvCommCommEnvComm: Any = import_module_from_file(
    Path("env_comm.py")
).CommEnvComm


class CommEnv(CommEnvComm):
    class Meta(CommEnvComm.Meta):
        stage = "local"
        emoji = "🐣"

    def __init__(self) -> None:
        super().__init__()


Env = CommEnv
