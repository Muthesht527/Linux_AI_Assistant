from assistant.core.assistant_controller import AssistantController
from assistant.tools.echo_tool import EchoTool


def test_controller_uses_echo_tool() -> None:
    controller = AssistantController([EchoTool()])

    result = controller.handle("hello")

    assert result["tool_used"] == "echo"
    assert result["response"] == "Echo: hello"
