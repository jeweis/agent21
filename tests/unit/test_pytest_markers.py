"""Contract tests for pytest strict marker registration."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any, TypedDict, cast

import pytest

tomllib: ModuleType | None
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - only used by local Python 3.10- checks.
    tomllib = None


class PytestConfig(TypedDict):
    """Typed subset of pytest configuration used by marker contract tests."""

    addopts: str
    markers: list[str]


REQUIRED_MARKERS = {
    "unit",
    "adapter",
    "contract",
    "integration",
    "e2e",
    "compatibility",
    "safety",
    "snapshot",
    "slow",
}


def test_pytest_uses_strict_marker_validation() -> None:
    """Project pytest config must reject misspelled marker names."""

    config = _load_pytest_config()

    assert "--strict-markers" in config["addopts"]


def test_required_pytest_markers_are_registered() -> None:
    """All validation-layer markers are declared in project config."""

    config = _load_pytest_config()
    configured = {item.split(":", 1)[0].strip() for item in config["markers"]}

    assert configured >= REQUIRED_MARKERS


def _load_pytest_config() -> PytestConfig:
    """Load pytest config once project metadata exists."""

    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject.exists():
        pytest.skip("pyproject.toml is created by a separate setup task")

    if tomllib is None:
        return _load_pytest_config_without_tomllib(pyproject)

    data = cast(dict[str, Any], tomllib.loads(pyproject.read_text(encoding="utf-8")))
    tool = cast(dict[str, Any], data.get("tool", {}))
    pytest_config = cast(dict[str, Any], tool.get("pytest", {}))
    ini_options = cast(dict[str, Any], pytest_config.get("ini_options", {}))
    return {
        "addopts": str(ini_options.get("addopts", "")),
        "markers": list(cast(list[str], ini_options.get("markers", []))),
    }


def _load_pytest_config_without_tomllib(pyproject: Path) -> PytestConfig:
    """Read the small pytest config subset needed on Python versions below 3.11."""

    addopts = ""
    markers: list[str] = []
    in_pytest = False
    in_markers = False

    for raw_line in pyproject.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "[tool.pytest.ini_options]":
            in_pytest = True
            continue
        if in_pytest and line.startswith("[") and line != "[tool.pytest.ini_options]":
            break
        if not in_pytest:
            continue
        if line.startswith("addopts"):
            addopts = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("markers"):
            in_markers = True
        elif in_markers and line.startswith("]"):
            in_markers = False
        elif in_markers and line.startswith('"'):
            markers.append(line.rstrip(",").strip('"'))

    return {"addopts": addopts, "markers": markers}
