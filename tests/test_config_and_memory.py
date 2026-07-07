from assistant.config.config_loader import ConfigLoader
from assistant.memory.sqlite_memory import MemoryManager, SQLiteMemory


def test_config_loader_reads_yaml() -> None:
    """Verify that the default YAML configuration can be loaded."""
    loader = ConfigLoader()
    assert loader.get("assistant.name") == "Linux AI Assistant"


def test_sqlite_memory_round_trip(tmp_path) -> None:
    """Verify that SQLite memory can store and retrieve a value."""
    memory = SQLiteMemory(db_path=tmp_path / "memory.sqlite")
    memory.set("name", "value")

    assert memory.get("name") == "value"


def test_memory_manager_filters_sensitive_keys(tmp_path) -> None:
    """Verify persistent memory avoids sensitive keys by default."""
    manager = MemoryManager(db_path=tmp_path / "memory.sqlite")

    assert manager.remember("preferred_model", "qwen3")
    assert not manager.remember("api_token", "secret")

    rows = manager.list_memory()["persistent"]
    assert any(row["key"] == "preferred_model" for row in rows)
    assert all(row["key"] != "api_token" for row in rows)


def test_preference_manager_round_trip(tmp_path) -> None:
    """Verify preferences are stored in their own namespace."""
    manager = MemoryManager(db_path=tmp_path / "memory.sqlite")
    manager.preferences.set("editor", "vim")

    assert manager.preferences.get("editor") == "vim"
    assert manager.preferences.list()["editor"] == "vim"
