"""Static contracts for reproducible local and CI validation sessions."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.contract


def test_required_public_sessions_exist() -> None:
    """Nox must expose the four documented public validation sessions."""
    source = Path("noxfile.py").read_text(encoding="utf-8")

    for name in ("pr", "main", "package", "release"):
        assert f"def {name}(" in source


def test_pr_session_propagates_quality_and_test_failures() -> None:
    """The PR gate must invoke both shared quality and fast test helpers."""
    source = Path("noxfile.py").read_text(encoding="utf-8")
    pr_body = source.split("def pr(", maxsplit=1)[1].split("@nox.session", maxsplit=1)[0]

    assert "_run_quality(session)" in pr_body
    assert "_run_pytest(session, FAST_MARKERS)" in pr_body
    assert "not e2e" in source
    assert "not slow" in source
