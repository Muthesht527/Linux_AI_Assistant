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


def test_plugin_manager_persists_disabled_state(tmp_path) -> None:
    """Verify plugin enable and disable state is persisted."""
    state_path = tmp_path / "plugin_state.json"
    manager = PluginManager(state_path=state_path)
    manager.discover()
    manager.disable("example")

    restored = PluginManager(state_path=state_path)
    metadata = restored.list_metadata()

    assert any(plugin.name == "example" and not plugin.enabled for plugin in metadata)

    restored.enable("example")
    enabled = PluginManager(state_path=state_path).list_metadata()
    assert any(plugin.name == "example" and plugin.enabled for plugin in enabled)


def test_plugin_manager_dependency_validation() -> None:
    """Verify missing plugin dependencies are reported."""
    manager = PluginManager()

    class MissingDependencyTool:
        name = "missing_dependency"
        description = "Missing dependency test"
        version = "1.0.0"
        author = "Tests"
        permission_level = "SAFE"
        dependencies = ["definitely_missing_package_for_linux_ai_assistant"]

    error = manager.validate(MissingDependencyTool())  # type: ignore[arg-type]

    assert error is not None
    assert "Missing dependencies" in error
