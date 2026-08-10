"""Integration tests for Agent21 synchronization planning and application."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.config import ConfigError
from agent21.init import initialize_project
from agent21.manifest import load_manifest
from agent21.sync import sync_project


@pytest.mark.integration
def test_sync_dry_run_has_no_filesystem_side_effects(tmp_path: Path) -> None:
    """Dry-run reports planned targets without writing outputs or lock state."""

    initialize_project(tmp_path, agents=("claude",), mode="copy", assume_yes=True)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    result = sync_project(tmp_path, dry_run=True, available_agents={"claude": True})

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert "CLAUDE.md" in result.created
    assert before == after
    assert not (tmp_path / ".agents/.lock").exists()


@pytest.mark.integration
@pytest.mark.safety
def test_sync_refuses_unmanaged_target(tmp_path: Path) -> None:
    """An unmanaged target blocks the whole write transaction."""

    initialize_project(tmp_path, agents=("claude",), mode="copy", assume_yes=True)
    (tmp_path / "CLAUDE.md").write_text("user owned\n", encoding="utf-8")

    result = sync_project(tmp_path, available_agents={"claude": True})

    assert result.conflicts == ["CLAUDE.md"]
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "user owned\n"


@pytest.mark.integration
def test_sync_skips_disabled_and_missing_agents(tmp_path: Path) -> None:
    """Disabled or unavailable Agents do not cause redundant target creation."""

    initialize_project(tmp_path, agents=("claude", "cursor"), mode="copy", assume_yes=True)

    result = sync_project(tmp_path, available_agents={"claude": False, "cursor": False})

    assert result.created == []
    assert result.skipped == ["claude: executable unavailable", "cursor: executable unavailable"]


@pytest.mark.integration
def test_configuration_only_workbuddy_syncs_without_executable(tmp_path: Path) -> None:
    """Explicit WorkBuddy selection writes only project `.codebuddy` outputs."""

    initialize_project(tmp_path, agents=("workbuddy",), mode="copy", assume_yes=True)

    first = sync_project(tmp_path, available_agents={"workbuddy": False})
    second = sync_project(tmp_path, available_agents={"workbuddy": False})

    assert first.created == [".codebuddy/skills"]
    assert second.unchanged == [".codebuddy/skills"]
    assert not (tmp_path / ".codebuddy/rules/agent21.md").exists()
    assert not (tmp_path / ".codebuddy/.mcp.json").exists()


@pytest.mark.integration
def test_unavailable_agent_keeps_existing_manifest_ownership(tmp_path: Path) -> None:
    """A temporarily missing executable must not orphan managed outputs."""

    initialize_project(tmp_path, agents=("qoder",), mode="copy", assume_yes=True)
    sync_project(tmp_path, available_agents={"qoder": True})

    result = sync_project(tmp_path, available_agents={"qoder": False})

    assert result.skipped == ["qoder: executable unavailable"]
    assert [artifact.path for artifact in load_manifest(tmp_path).managed_artifacts] == [
        ".qoder/skills"
    ]


@pytest.mark.integration
def test_instruction_edit_propagates_to_claude_md(tmp_path: Path) -> None:
    """权威 AGENTS.md 的修改会在下一次 sync 更新生成的 CLAUDE.md。"""

    initialize_project(tmp_path, agents=("claude",), mode="copy", assume_yes=True)
    sync_project(tmp_path, available_agents={"claude": True})
    (tmp_path / "AGENTS.md").write_text("# New rules\n", encoding="utf-8")

    result = sync_project(tmp_path, available_agents={"claude": True})

    assert result.updated == ["CLAUDE.md"]
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "# New rules\n"


@pytest.mark.integration
def test_sync_without_init_guides_user_to_initialize(tmp_path: Path) -> None:
    """Sync on an uninitialized project fails fast with an actionable message."""

    with pytest.raises(ConfigError, match="run 'agent21 init --yes' first"):
        sync_project(tmp_path, available_agents={"claude": True})
