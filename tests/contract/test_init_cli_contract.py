"""Contract tests for the public ``agent21 init`` command."""

from __future__ import annotations

import re

from typer.testing import CliRunner

from agent21.cli import app


def test_init_help_exposes_non_interactive_options() -> None:
    """Initialization documents deterministic Agent and sync-mode selection."""

    result = CliRunner().invoke(app, ["init", "--help"])

    assert result.exit_code == 0
    output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    assert "--agents" in output
    assert "--mode" in output
    assert "--yes" in output


def test_init_rejects_unknown_agent_as_operational_failure(tmp_path: object) -> None:
    """A syntactically valid but unsupported Agent selection exits with status one."""

    result = CliRunner().invoke(app, ["init", "--agents", "unknown", "--yes"])

    assert result.exit_code == 1
    assert "unknown" in result.output.lower()
