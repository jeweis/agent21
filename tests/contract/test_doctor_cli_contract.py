"""CLI contract tests for ``agent21 doctor``."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent21.cli import app
from agent21.init import initialize_project


def test_doctor_help_is_public() -> None:
    """The public command documents the health-check entry point."""

    result = CliRunner().invoke(app, ["doctor", "--help"])

    assert result.exit_code == 0
    assert "health" in result.stdout.lower()


def test_doctor_uses_blocked_exit_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing project configuration is an operational failure, not CLI misuse."""

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "blocked" in result.output


def test_doctor_healthy_project_exits_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A freshly initialized project has no blocking health finding."""

    initialize_project(tmp_path, agents=())
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0, result.output
