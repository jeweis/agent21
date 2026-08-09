"""Contracts for the pull-request workflow path classifier."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.contract
WORKFLOW = Path(".github/workflows/pr.yml")


def test_pr_workflow_has_documentation_only_lane_and_code_gate() -> None:
    """Documentation-only changes retain config checks without launching Python matrices."""

    content = WORKFLOW.read_text(encoding="utf-8")

    assert "code_changed" in content
    assert "docs-only" in content
    assert "needs.changes.outputs.code_changed == 'true'" in content
    assert "needs.changes.outputs.code_changed == 'false'" in content
