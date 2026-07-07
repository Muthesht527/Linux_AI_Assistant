from assistant.core.tool_engine import ToolEngine
from assistant.tools.filesystem_tool import FilesystemTool


def test_tool_engine_executes_registered_tool(tmp_path) -> None:
    engine = ToolEngine([FilesystemTool()])
    result = engine.execute("filesystem", path=str(tmp_path))

    assert result["path"] == str(tmp_path)
    assert isinstance(result["entries"], list)
