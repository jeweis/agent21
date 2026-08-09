"""CLI contract tests for project Skill management."""

from __future__ import annotations

from typer.testing import CliRunner

from agent21.cli import app


def test_skill_help_exposes_lifecycle_commands() -> None:
    """Skill command group publishes install, list, and remove operations."""

    result = CliRunner().invoke(app, ["skill", "--help"])

    assert result.exit_code == 0
    for command in ("install", "list", "remove"):
        assert command in result.stdout


def test_skill_install_requires_source() -> None:
    """Missing positional syntax is a stable usage error."""

    result = CliRunner().invoke(app, ["skill", "install"])

    assert result.exit_code == 2
