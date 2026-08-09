"""Contract tests for the minimum public CLI surface."""

import pytest
from typer.testing import CliRunner

from agent21 import __version__
from agent21.cli import app

pytestmark = pytest.mark.contract
runner = CliRunner()


def test_help_lists_product_description() -> None:
    """The installed entry point must provide useful help without project state."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Synchronize project-level configuration" in result.stdout


def test_version_is_machine_parseable() -> None:
    """The version flag must return only the installed semantic version."""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__
