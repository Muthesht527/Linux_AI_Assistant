import subprocess
from pathlib import Path

from assistant.core.tool_engine import ToolEngine
from assistant.project import (
    DependencyReader,
    DocumentationReader,
    GitRepositoryManager,
    LanguageDetector,
    ProjectConfiguration,
    RepositoryAnalyzer,
    StackTraceParser,
)
from assistant.tools.project_tool import ProjectSummaryTool, StackTraceTool


def test_repository_detection_and_summary(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("def run():\n    return True\n", encoding="utf-8")

    data = RepositoryAnalyzer(ProjectConfiguration()).analyze(tmp_path)

    assert "Git repository" in data["project_types"]
    assert "Python project" in data["project_types"]
    assert data["languages"]["Python"] == 1
    assert data["files_analyzed"] >= 1


def test_language_detection() -> None:
    detector = LanguageDetector()

    assert detector.detect_file(Path("example.py")) == "Python"
    assert detector.detect_file(Path("package.json")) == "JSON"


def test_dependency_reader_reads_manifests(tmp_path) -> None:
    (tmp_path / "requirements.txt").write_text("rich\n# comment\npydantic\n", encoding="utf-8")
    (tmp_path / "package.json").write_text('{"dependencies":{"vite":"latest"}}', encoding="utf-8")

    data = DependencyReader().read(tmp_path)

    assert data["requirements.txt"] == ["rich", "pydantic"]
    assert data["package.json"]["dependencies"]["vite"] == "latest"


def test_readme_reader_extracts_purpose_and_setup(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        "# Demo\n\nPurpose text.\n\n## Installation\n\npip install .\n",
        encoding="utf-8",
    )

    data = DocumentationReader().read(tmp_path)

    assert data["found"] is True
    assert "Demo" in data["purpose"]
    assert "pip install" in data["setup"]


def test_stack_trace_parser_extracts_python_frames() -> None:
    text = 'Traceback\n  File "app.py", line 4, in main\nValueError: bad value'

    data = StackTraceParser().parse(text)

    assert data["frames"][0]["file"] == "app.py"
    assert data["frames"][0]["line"] == 4
    assert data["root_cause"] == "ValueError: bad value"


def test_git_readers_are_read_only(tmp_path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    subprocess.run(["git", "add", "main.py"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / "main.py").write_text("print('changed')\n", encoding="utf-8")

    manager = GitRepositoryManager(ProjectConfiguration(git_history_depth=1))
    status = manager.status(tmp_path)
    history = manager.history(tmp_path)
    diff = manager.diff(tmp_path)

    assert status["current_branch"] in {"master", "main"}
    assert "main.py" in status["changed_files"]
    assert history["commits"][0]["subject"] == "initial"
    assert "main.py" in diff["changed_files"]


def test_project_tools_integrate_with_tool_engine(tmp_path) -> None:
    (tmp_path / "main.py").write_text("def run():\n    return True\n", encoding="utf-8")
    engine = ToolEngine([ProjectSummaryTool(), StackTraceTool()])

    summary = engine.execute("project_summary", {"path": str(tmp_path)})
    error = engine.execute("stack_trace", {"text": "ModuleNotFoundError: No module named 'x'"})

    assert summary.success is True
    assert summary.data["languages"]["Python"] == 1
    assert error.success is True
    assert "could not import" in error.data["explanation"]
