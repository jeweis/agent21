"""Contracts for the explicit main and release platform matrices."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
import yaml

pytestmark = pytest.mark.contract


def _matrix(path: str, job: str) -> list[dict[str, str]]:
    """Load an explicit workflow matrix include list."""

    workflow = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return cast(list[dict[str, str]], workflow["jobs"][job]["strategy"]["matrix"]["include"])


def test_main_gate_declares_eight_platform_python_combinations() -> None:
    """Main validation covers four Linux and two Windows/macOS interpreter pairs."""

    matrix = _matrix(".github/workflows/main.yml", "full-validation")

    assert len(matrix) == 8
    assert {item["os"] for item in matrix} == {
        "ubuntu-latest",
        "windows-latest",
        "macos-latest",
    }


def test_release_gate_covers_minimum_and_maximum_python_on_three_platforms() -> None:
    """Release validation explicitly covers 3.11 and 3.14 on every target OS."""

    matrix = _matrix(".github/workflows/release.yml", "release-validation")

    assert len(matrix) == 6
    assert {item["python-version"] for item in matrix} == {"3.11", "3.14"}
