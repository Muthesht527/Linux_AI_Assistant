from assistant.core.tool_engine import ToolEngine
from assistant.tools.filesystem_tool import FilesystemTool


def test_tool_engine_executes_registered_tool(tmp_path) -> None:
    """Verify that the tool engine executes a registered filesystem tool."""
    engine = ToolEngine([FilesystemTool()])
    result = engine.execute("filesystem", path=str(tmp_path))

    assert result["path"] == str(tmp_path)
    assert isinstance(result["entries"], list)


def test_filesystem_tool_returns_error_for_missing_path(tmp_path) -> None:
    """Verify filesystem inspection returns errors instead of raising."""
    tool = FilesystemTool()

    result = tool.execute(path=str(tmp_path / "missing"))

    assert result["path"] == str(tmp_path / "missing")
    assert "error" in result
