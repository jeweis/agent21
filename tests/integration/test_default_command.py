"""Integration tests for the default enable command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent21.cli import app
from agent21.config import load_config

runner = CliRunner()


@pytest.mark.integration
def test_default_command_initializes_and_syncs_workbuddy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--agents establishes truth sources and syncs a CLI-free Agent end to end."""

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--agents", "workbuddy", "--mode", "copy"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / ".agents/config.yaml").is_file()
    assert (tmp_path / ".agents/manifest.yaml").is_file()
    assert (tmp_path / ".codebuddy/skills").is_dir()
    assert load_config(tmp_path).agents["workbuddy"].enabled


@pytest.mark.integration
def test_default_command_is_idempotent_and_appendable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Re-running the default command is idempotent and appends without disabling."""

    monkeypatch.chdir(tmp_path)
    first = runner.invoke(app, ["--agents", "workbuddy", "--mode", "copy"])
    second = runner.invoke(app, ["--agents", "workbuddy", "--mode", "copy"])
    appended = runner.invoke(app, ["--agents", "workbuddy,claude", "--mode", "copy"])

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert "created: .codebuddy/skills" in first.output
    assert appended.exit_code == 0, appended.output
    config = load_config(tmp_path)
    assert config.agents["workbuddy"].enabled
    assert config.agents["claude"].enabled


@pytest.mark.integration
def test_default_command_without_agents_in_non_tty_guides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-TTY bare `agent21` fails fast and guides toward --agents."""

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, [])

    assert result.exit_code == 1
    assert "--agents" in result.output


@pytest.mark.integration
def test_default_command_interactive_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bare `agent21` in a TTY enables exactly the Agents chosen interactively."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("agent21.cli.is_tty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *args: "3")

    result = runner.invoke(app, [])

    assert result.exit_code == 0, result.output
    config = load_config(tmp_path)
    assert config.agents["cursor"].enabled
    assert not config.agents["claude"].enabled
