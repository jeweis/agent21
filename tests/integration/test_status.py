"""Integration tests for the read-only status command."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent21.cli import app

runner = CliRunner()


@pytest.mark.integration
def test_status_shows_enablement_availability_and_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """status lists every Agent with enabled/availability/managed outputs."""

    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["--agents", "workbuddy", "--mode", "copy"]).exit_code == 0

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0, result.output
    assert "workbuddy\tenabled\tnone-required\t.codebuddy/skills" in result.output
    assert "claude\tdisabled" in result.output


@pytest.mark.integration
def test_status_appends_doctor_blocked_with_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """status surfaces doctor blocked items and their repair action."""

    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["--agents", "workbuddy", "--mode", "copy"]).exit_code == 0
    (tmp_path / "CODEBUDDY.md").write_text("# user-owned\n", encoding="utf-8")

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0, result.output
    assert "blocked: agent.instructions" in result.output
    assert "shadows AGENTS.md" in result.output


@pytest.mark.integration
def test_status_is_read_only_and_works_uninitialized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """status on an uninitialized project reports guidance without writing files."""

    monkeypatch.chdir(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "project not initialized" in result.output
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert before == after
