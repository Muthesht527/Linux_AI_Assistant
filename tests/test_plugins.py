from assistant.plugins.plugin_manager import PluginManager


def test_plugin_manager_discovers_example_tool() -> None:
    """Verify that plugin discovery finds the example tool."""
    manager = PluginManager()
    plugins = manager.discover()

    assert any(plugin.name == "example" for plugin in plugins)


def test_plugin_manager_exposes_metadata() -> None:
    """Verify plugin discovery exposes production metadata."""
    manager = PluginManager()
    metadata = manager.list_metadata()

    assert any(plugin.name == "example" and plugin.valid for plugin in metadata)
