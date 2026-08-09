"""Contracts for release blocking and trusted publishing."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.contract


def test_release_aggregates_validation_and_build_before_publish() -> None:
    """Publishing cannot run unless matrix validation and package build both succeed."""

    content = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "needs.release-validation.result" in content
    assert "needs.build-distribution.result" in content
    assert "needs: release-gate" in content
    assert "id-token: write" in content
    assert "pypa/gh-action-pypi-publish@release/v1" in content
