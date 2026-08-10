"""Integration tests for the disable command and retired-output cleanup."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent21.cli import app
from agent21.config import load_config
from agent21.models import REGISTERED_AGENTS

runner = CliRunner()


@pytest.mark.integration
def test_disable_dry_run_previews_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """disable --dry-run lists managed outputs to retire without touching config/files."""

    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["--agents", "workbuddy", "--mode", "copy"]).exit_code == 0
    before_config = (tmp_path / ".agents/config.yaml").read_bytes()

    result = runner.invoke(app, ["disable", "--agents", "workbuddy", "--dry-run"])

    assert result.exit_code == 0, result.output
    assert "would retire: .codebuddy/skills" in result.output
    assert (tmp_path / ".codebuddy/skills").is_dir()
    assert (tmp_path / ".agents/config.yaml").read_bytes() == before_config


@pytest.mark.integration
def test_disable_retires_only_target_agent_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """disable removes the target Agent's managed outputs and keeps others and user files."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "agent21.sync.detect_agents",
        lambda: {agent: agent == "claude" for agent in REGISTERED_AGENTS},
    )
    assert runner.invoke(app, ["--agents", "workbuddy,claude", "--mode", "copy"]).exit_code == 0
    custom = tmp_path / "custom.md"
    custom.write_text("manual\n", encoding="utf-8")

    result = runner.invoke(app, ["disable", "--agents", "workbuddy"])

    assert result.exit_code == 0, result.output
    assert "disabled: workbuddy" in result.output
    assert "retired: .codebuddy/skills" in result.output
    assert not (tmp_path / ".codebuddy/skills").exists()
    assert (tmp_path / "CLAUDE.md").is_file()
    assert custom.read_text(encoding="utf-8") == "manual\n"
    assert not load_config(tmp_path).agents["workbuddy"].enabled
    assert load_config(tmp_path).agents["claude"].enabled


@pytest.mark.integration
def test_disable_not_enabled_agent_reports_clearly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """disabling an Agent that is not enabled is a clear error, not a no-op."""

    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["--agents", "workbuddy", "--mode", "copy"]).exit_code == 0

    result = runner.invoke(app, ["disable", "--agents", "claude"])

    assert result.exit_code == 1
    assert "not enabled" in result.output
    assert load_config(tmp_path).agents["workbuddy"].enabled
