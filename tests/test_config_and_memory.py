from assistant.config.config_loader import ConfigLoader
from assistant.memory.sqlite_memory import SQLiteMemory


def test_config_loader_reads_yaml() -> None:
    loader = ConfigLoader()
    assert loader.get("assistant.name") == "Linux AI Assistant"


def test_sqlite_memory_round_trip(tmp_path) -> None:
    memory = SQLiteMemory(db_path=tmp_path / "memory.sqlite")
    memory.set("name", "value")

    assert memory.get("name") == "value"
