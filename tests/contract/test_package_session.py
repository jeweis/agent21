"""Static contract for distribution build and clean-install smoke validation."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.contract


def test_package_session_contains_required_smoke_steps() -> None:
    """The package session must build, inspect, install, import, and invoke the CLI."""
    source = Path("noxfile.py").read_text(encoding="utf-8")

    for expected in (
        '"python", "-m", "build"',
        '"twine", "check", "--strict"',
        '"uv", "pip", "install"',
        '"-c", "import agent21"',
        'agent21, "--help"',
        'agent21, "--version"',
    ):
        assert expected in source
