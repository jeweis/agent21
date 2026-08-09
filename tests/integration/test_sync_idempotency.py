"""Repeated synchronization idempotency tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.init import initialize_project
from agent21.manifest import MANIFEST_PATH
from agent21.sync import sync_project


@pytest.mark.integration
def test_twenty_sync_runs_keep_tree_and_manifest_equivalent(tmp_path: Path) -> None:
    """Identical authoritative inputs never accumulate output or manifest drift."""

    initialize_project(tmp_path, agents=("claude",), mode="copy", assume_yes=True)
    first = sync_project(tmp_path, available_agents={"claude": True})
    assert first.created
    baseline_manifest = (tmp_path / MANIFEST_PATH).read_bytes()
    baseline_target = (tmp_path / "CLAUDE.md").read_bytes()

    for _ in range(19):
        result = sync_project(tmp_path, available_agents={"claude": True})
        assert not result.created
        assert not result.updated
        assert result.unchanged

    assert (tmp_path / MANIFEST_PATH).read_bytes() == baseline_manifest
    assert (tmp_path / "CLAUDE.md").read_bytes() == baseline_target
