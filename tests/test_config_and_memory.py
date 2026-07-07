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


def test_memory_manager_learns_usage(tmp_path) -> None:
    """Verify persistent memory learns non-sensitive usage signals."""
    manager = MemoryManager(db_path=tmp_path / "memory.sqlite")

    manager.record_command("project")
    manager.record_folder(str(tmp_path))
    manager.record_repository(str(tmp_path))
    manager.record_language("Python")
    manager.record_model("qwen3:latest")

    rows = manager.list_memory()["persistent"]
    keys = {row["key"] for row in rows}

    assert "frequently_used_commands" in keys
    assert "frequently_accessed_folders" in keys
    assert "frequently_opened_repositories" in keys
    assert "preferred_programming_languages" in keys
    assert manager.preferences.get("preferred_model") == "qwen3:latest"


def test_session_memory_tracks_recent_activity(tmp_path) -> None:
    """Verify session memory stores current process context."""
    manager = MemoryManager(db_path=tmp_path / "memory.sqlite")
    manager.session.current_working_directory = str(tmp_path)
    manager.session.remember_file(str(tmp_path / "README.md"))
    manager.session.remember_tool("read_file")
    manager.session.remember_conversation("user", "hello")

    snapshot = manager.session.snapshot()

    assert snapshot["current_working_directory"] == str(tmp_path)
    assert snapshot["recently_opened_files"] == [str(tmp_path / "README.md")]
    assert snapshot["recently_executed_tools"] == ["read_file"]
    assert snapshot["recent_conversations"][0]["content"] == "hello"
