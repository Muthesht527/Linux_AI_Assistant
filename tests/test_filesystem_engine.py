"""Filesystem subsystem tests."""

from __future__ import annotations

from assistant.filesystem import FilesystemConfiguration, FilesystemManager


def _manager(tmp_path) -> FilesystemManager:
    root = tmp_path / "root"
    root.mkdir()
    configuration = FilesystemConfiguration(
        indexed_paths=[root],
        index_location=tmp_path / "index.sqlite3",
        ignored_folders=[".git", "__pycache__"],
        maximum_file_size=1024 * 1024,
        cache_size=2,
    )
    return FilesystemManager(configuration, project_root=tmp_path)


def test_index_and_search_by_partial_name(tmp_path) -> None:
    """Verify incremental indexing and filename search."""
    manager = _manager(tmp_path)
    (tmp_path / "root" / "notes.md").write_text("hello filesystem", encoding="utf-8")

    result = manager.index()
    search = manager.search(partial="note")

    assert result["indexed"] == 1
    assert search["total"] == 1
    assert search["results"][0]["filename"] == "notes.md"


def test_search_inside_files(tmp_path) -> None:
    """Verify content search over indexed text files."""
    manager = _manager(tmp_path)
    (tmp_path / "root" / "app.py").write_text("def useful_function(): pass", encoding="utf-8")
    manager.index()

    result = manager.search_content("useful_function")

    assert result["total"] == 1
    assert result["results"][0]["filename"] == "app.py"


def test_reader_metadata_and_cache(tmp_path) -> None:
    """Verify readers, metadata, and metadata cache behavior."""
    manager = _manager(tmp_path)
    path = tmp_path / "root" / "data.json"
    path.write_text('{"ok": true}', encoding="utf-8")

    read = manager.read(path)
    first = manager.metadata(path)
    second = manager.metadata(path)

    assert read["content"] == {"ok": True}
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["extension"] == ".json"


def test_directory_listing_and_missing_file_errors(tmp_path) -> None:
    """Verify directory listing and friendly missing file errors."""
    manager = _manager(tmp_path)
    (tmp_path / "root" / "sample.txt").write_text("sample", encoding="utf-8")

    listing = manager.list_directory(tmp_path / "root")

    assert listing["entries"][0]["name"] == "sample.txt"
    try:
        manager.read(tmp_path / "root" / "missing.txt")
    except FileNotFoundError as exc:
        assert "Path does not exist" in str(exc)
    else:
        raise AssertionError("Expected missing file to raise FileNotFoundError")


def test_partition_detection_uses_configured_roots(tmp_path) -> None:
    """Verify configured roots are detected without hardcoded paths."""
    manager = _manager(tmp_path)

    roots = manager.roots()

    assert roots == [(tmp_path / "root").resolve()]
