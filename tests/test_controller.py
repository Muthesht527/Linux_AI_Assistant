from assistant.core.assistant_controller import AssistantController
from assistant.models.ollama_model import OllamaModel
from assistant.tools.echo_tool import EchoTool


def test_controller_uses_echo_tool() -> None:
    """Verify that the controller routes input through the echo tool."""
    controller = AssistantController([EchoTool()])

    result = controller.handle("hello")

    assert result["tool_used"] == "echo"
    assert result["response"] == "Echo: hello"


def test_ollama_model_returns_structured_error_when_unavailable() -> None:
    """Verify that Ollama failures return structured errors."""
    model = OllamaModel(base_url="http://127.0.0.1:1", timeout=1)

    result = model.generate("hello")

    assert result["model"] == "qwen3"
    assert result["prompt"] == "hello"
    assert "error" in result
