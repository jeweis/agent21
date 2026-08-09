"""Repeated synchronization idempotency tests."""

from __future__ import annotations

import json
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


@pytest.mark.integration
@pytest.mark.parametrize(
    ("agent", "expected_targets"),
    [
        ("opencode", ("opencode.json",)),
        ("workbuddy", (".codebuddy/rules/agent21.md", ".codebuddy/skills")),
        ("qoder", (".qoder/skills",)),
    ],
)
def test_expanded_agents_remain_idempotent_for_twenty_syncs(
    tmp_path: Path, agent: str, expected_targets: tuple[str, ...]
) -> None:
    """Every new managed-output adapter stays stable across twenty runs."""

    initialize_project(tmp_path, agents=(agent,), mode="copy", assume_yes=True)
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"demo": {"command": "demo"}}}), encoding="utf-8"
    )
    availability = {agent: agent != "workbuddy"}
    first = sync_project(tmp_path, available_agents=availability)
    assert tuple(first.created) == expected_targets
    baseline_manifest = (tmp_path / MANIFEST_PATH).read_bytes()

    for _ in range(19):
        result = sync_project(tmp_path, available_agents=availability)
        assert not result.created
        assert not result.updated
        assert tuple(result.unchanged) == expected_targets

    assert (tmp_path / MANIFEST_PATH).read_bytes() == baseline_manifest
