"""Contract tests for coverage policy stored in project metadata."""

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.contract


def _project_config() -> dict[str, object]:
    """Load the committed project configuration using the standard parser."""
    return tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))


def test_global_branch_coverage_threshold() -> None:
    """The project must enforce branch coverage with an 80 percent global floor."""
    config = _project_config()
    coverage = config["tool"]["coverage"]  # type: ignore[index]

    assert coverage["run"]["branch"] is True
    assert coverage["report"]["fail_under"] == 80


def test_core_coverage_threshold_is_encoded_in_nox() -> None:
    """Critical modules must receive the stricter 90 percent report."""
    nox_source = Path("noxfile.py").read_text(encoding="utf-8")

    assert '"--fail-under=90"' in nox_source
    assert "CORE_PATHS" in nox_source
