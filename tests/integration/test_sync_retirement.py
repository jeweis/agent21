"""Integration tests for retired managed-artifact cleanup during sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.init import initialize_project
from agent21.sync import sync_project


@pytest.mark.integration
def test_sync_retires_managed_artifact_of_disabled_agent(tmp_path: Path) -> None:
    """A disabled Agent's managed output is removed on the next sync."""

    initialize_project(tmp_path, agents=("claude",), mode="copy")
    sync_project(tmp_path)
    assert (tmp_path / "CLAUDE.md").is_file()

    _disable_agent(tmp_path, "claude")

    result = sync_project(tmp_path)

    assert not (tmp_path / "CLAUDE.md").exists()
    assert not (tmp_path / ".claude" / "skills").exists()
    assert result.retired == [".claude/skills", "CLAUDE.md"]


@pytest.mark.integration
def test_sync_dry_run_reports_retired_without_writing(tmp_path: Path) -> None:
    """Dry-run lists retired targets but leaves files and config untouched."""

    initialize_project(tmp_path, agents=("claude",), mode="copy")
    sync_project(tmp_path)
    _disable_agent(tmp_path, "claude")

    result = sync_project(tmp_path, dry_run=True)

    assert result.retired == [".claude/skills", "CLAUDE.md"]
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / ".claude" / "skills").is_dir()


@pytest.mark.integration
def test_sync_keeps_retired_artifacts_of_unavailable_agents(tmp_path: Path) -> None:
    """Executable-unavailable Agents keep their managed outputs (no orphan removal)."""

    initialize_project(tmp_path, agents=("qoder",), mode="copy")
    sync_project(tmp_path)

    result = sync_project(tmp_path)

    assert result.retired == []
    assert (tmp_path / ".qoder" / "skills").is_dir()


def _disable_agent(root: Path, agent: str) -> None:
    """Set an Agent disabled directly in the project config file."""

    config_path = root / ".agents" / "config.yaml"
    config = config_path.read_text(encoding="utf-8")
    config = config.replace(
        f"    {agent}:\n      enabled: true",
        f"    {agent}:\n      enabled: false",
    )
    config_path.write_text(config, encoding="utf-8")
