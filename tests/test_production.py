"""Production readiness tests for cache, stats, and release helpers."""

from assistant.core.production import ApplicationStatistics, CacheManager, ReleaseManager


def test_cache_manager_tracks_hits_and_misses() -> None:
    """Verify cache values expire through normal lookup semantics."""
    cache = CacheManager(max_entries=2, ttl_seconds=60)
    cache.set("models", ["qwen3"])

    assert cache.get("models") == ["qwen3"]
    assert cache.get("missing") is None
    assert cache.stats()["hits"] == 1
    assert cache.stats()["misses"] == 1


def test_application_statistics_snapshot() -> None:
    """Verify statistics expose command, tool, and timing totals."""
    stats = ApplicationStatistics()
    stats.record_command("info")
    stats.record_tool("diagnostics")
    stats.performance.record(0.5)

    snapshot = stats.snapshot()

    assert snapshot["commands_executed"] == 1
    assert snapshot["tools_executed"] == 1
    assert snapshot["average_response_time"] == 0.5


def test_release_manager_detects_required_files(tmp_path) -> None:
    """Verify release readiness checks required packaging files."""
    for name in ReleaseManager.REQUIRED_FILES:
        (tmp_path / name).write_text("ok", encoding="utf-8")

    report = ReleaseManager(tmp_path).check()

    assert report["ready"]
    assert report["missing_files"] == []
