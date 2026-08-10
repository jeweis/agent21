"""Contract tests for the default enable command surface."""

from __future__ import annotations

import re

from typer.testing import CliRunner

from agent21.cli import app

runner = CliRunner()


def test_help_exposes_enable_options_without_yes_and_init() -> None:
    """Help documents --agents/--mode but no --yes and no init command."""

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    assert "--agents" in output
    assert "--mode" in output
    assert "--yes" not in output
    assert "init" not in output


def test_unknown_agent_as_enable_selection_is_operational_failure() -> None:
    """A syntactically valid but unsupported Agent selection exits with status one."""

    result = runner.invoke(app, ["--agents", "unknown"])

    assert result.exit_code == 1
    assert "unknown" in result.output.lower()


def test_bare_agent_name_is_not_a_command() -> None:
    """An Agent name as a positional argument is rejected, guiding to --agents."""

    result = runner.invoke(app, ["codex"])

    assert result.exit_code == 2
    assert "No such command" in result.output
    assert "codex" in result.output


def test_enable_command_matches_default_surface() -> None:
    """`agent21 enable --help` exposes the same deterministic options."""

    result = runner.invoke(app, ["enable", "--help"])

    assert result.exit_code == 0
    output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    assert "--agents" in output
    assert "--mode" in output
    assert "--yes" not in output


def test_disable_and_status_commands_are_registered() -> None:
    """disable/status/sync/doctor are exposed in the help command list."""

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    for command in ("disable", "status", "sync", "doctor", "skill"):
        assert command in output
