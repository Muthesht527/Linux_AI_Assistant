from assistant.plugins.plugin_manager import PluginManager


def test_plugin_manager_discovers_example_tool() -> None:
    """Verify that plugin discovery finds the example tool."""
    manager = PluginManager()
    plugins = manager.discover()

    assert any(plugin.name == "example" for plugin in plugins)
