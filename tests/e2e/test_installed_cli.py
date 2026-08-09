"""Subprocess smoke tests for the packaged Agent21 command surface."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the package module with the current isolated interpreter."""

    environment = os.environ.copy()
    source_root = Path(__file__).resolve().parents[2] / "src"
    environment["PYTHONPATH"] = str(source_root)
    return subprocess.run(
        [sys.executable, "-m", "agent21", *args],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.e2e
def test_cli_help_version_and_local_project_lifecycle(tmp_path: Path) -> None:
    """A clean process can initialize, diagnose, and manage a local Skill."""

    assert _run(tmp_path, "--help").returncode == 0
    assert _run(tmp_path, "--version").returncode == 0
    initialized = _run(tmp_path, "init", "--agents", "", "--yes")
    assert initialized.returncode == 0, initialized.stderr
    source = tmp_path / "source/demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
    assert _run(tmp_path, "skill", "install", "source/demo").returncode == 0
    assert "demo" in _run(tmp_path, "skill", "list").stdout
    assert _run(tmp_path, "doctor").returncode == 0
    assert _run(tmp_path, "skill", "remove", "demo").returncode == 0
