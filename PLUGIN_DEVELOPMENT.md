# Plugin Development

Plugins live in `assistant/plugins` and expose tools by defining subclasses of
`assistant.core.base_tool.BaseTool`.

Each plugin tool should define:

- `name`
- `description`
- `category`
- `version`
- `author`
- `permission_level`
- `parameter_schema`
- `execute`

Example:

```python
from assistant.core.base_tool import BaseTool, ToolResult


class MyTool(BaseTool):
    name = "my_tool"
    description = "Example local plugin"
    category = "plugin"
    version = "1.0.0"
    author = "Local User"
    permission_level = "SAFE"

    def execute(self, **kwargs) -> ToolResult:
        return self.result(success=True, message="done", data={"ok": True})
```

Inspect plugins with:

```bash
python3 main.py plugins list
python3 main.py plugins reload
```
