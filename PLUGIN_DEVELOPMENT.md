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

Plugins may also define `dependencies` as a list of import names. Missing
dependencies are reported by validation and prevent the plugin from being loaded
as a valid tool.

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
python3 main.py plugins validate
python3 main.py plugins info example
python3 main.py plugins disable example
python3 main.py plugins enable example
```

Disabled plugin state is persisted locally in `assistant/cache/plugin_state.json`.
