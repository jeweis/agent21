"""Contract tests for the public ``agent21 init`` command."""

from __future__ import annotations

from typer.testing import CliRunner

from agent21.cli import app


def test_init_help_exposes_non_interactive_options() -> None:
    """Initialization documents deterministic Agent and sync-mode selection."""

    result = CliRunner().invoke(app, ["init", "--help"])

    assert result.exit_code == 0
    assert "--agents" in result.stdout
    assert "--mode" in result.stdout
    assert "--yes" in result.stdout


def test_init_rejects_unknown_agent_as_operational_failure(tmp_path: object) -> None:
    """A syntactically valid but unsupported Agent selection exits with status one."""

    result = CliRunner().invoke(app, ["init", "--agents", "unknown", "--yes"])

    assert result.exit_code == 1
    assert "unknown" in result.output.lower()
