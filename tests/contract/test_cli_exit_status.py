"""Contract tests for public CLI exit status categories."""

import pytest
from typer.testing import CliRunner

from agent21.cli import app

pytestmark = pytest.mark.contract
runner = CliRunner()


def test_unknown_command_returns_usage_error() -> None:
    """Unknown commands must use the documented usage-error status."""
    result = runner.invoke(app, ["unknown-command"])

    assert result.exit_code == 2
    assert "No such command" in result.output
