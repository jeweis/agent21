"""Unit tests for project-level exclusive locking."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from agent21.lock import LockAlreadyHeld, ProjectLock, inspect_lock


def test_project_lock_creates_and_releases_lock_file(tmp_path: Path) -> None:
    """The lock file exists only while the context manager is active."""

    with ProjectLock(tmp_path, command="sync") as lock:
        assert lock.path.exists()
        payload = json.loads(lock.path.read_text(encoding="utf-8"))
        assert payload["pid"] == os.getpid()
        assert payload["command"] == "sync"

    assert not (tmp_path / ".agents" / ".lock").exists()


def test_project_lock_rejects_second_holder(tmp_path: Path) -> None:
    """An existing live lock produces a deterministic diagnostic error."""

    with ProjectLock(tmp_path, command="sync"), pytest.raises(LockAlreadyHeld) as exc_info:
        ProjectLock(tmp_path, command="doctor").acquire()

    assert exc_info.value.diagnostic.status == "blocked"
    assert exc_info.value.diagnostic.stale is False


def test_inspect_lock_marks_dead_pid_stale(tmp_path: Path) -> None:
    """A lock owned by a non-existent process is stale and actionable."""

    lock_path = tmp_path / ".agents" / ".lock"
    lock_path.parent.mkdir()
    lock_path.write_text(
        json.dumps({"pid": 999999999, "command": "sync", "created_at": time.time()}),
        encoding="utf-8",
    )

    diagnostic = inspect_lock(tmp_path)

    assert diagnostic.status == "blocked"
    assert diagnostic.stale is True
    assert diagnostic.subject == ".agents/.lock"


def test_inspect_lock_reports_missing_lock_as_pass(tmp_path: Path) -> None:
    """No lock means doctor can continue other checks."""

    diagnostic = inspect_lock(tmp_path)

    assert diagnostic.status == "pass"
    assert diagnostic.stale is False
