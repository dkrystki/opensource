from pathlib import Path


def add_registry_app() -> None:
    env_file = Path("env_comm.py")
    env_content = env_file.read_text()
    env_content_lines = env_content.splitlines(keepends=True)
    index = [
        i for i, word in enumerate(env_content_lines) if "self.apps.extend" in word
    ][0]
    env_content_lines.insert(
        index + 1, '        self.apps.extend(["system.registry"])\n'
    )
    env_content = "".join(env_content_lines)
    env_file.write_text(env_content)
