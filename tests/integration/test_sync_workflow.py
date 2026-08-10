"""Integration tests for Agent21 synchronization planning and application."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.errors import ConfigError
from agent21.init import initialize_project
from agent21.manifest import load_manifest
from agent21.sync import sync_project


@pytest.mark.integration
def test_sync_dry_run_has_no_filesystem_side_effects(tmp_path: Path) -> None:
    """Dry-run reports planned targets without writing outputs or lock state."""

    initialize_project(tmp_path, agents=("claude",), mode="copy")
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    result = sync_project(tmp_path, dry_run=True)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert "CLAUDE.md" in result.created
    assert before == after
    assert not (tmp_path / ".agents/.lock").exists()


@pytest.mark.integration
@pytest.mark.safety
def test_sync_adopts_existing_unmanaged_target(tmp_path: Path) -> None:
    """An existing target is adopted and replaced by the authoritative content."""

    initialize_project(tmp_path, agents=("claude",), mode="copy")
    (tmp_path / "CLAUDE.md").write_text("user owned\n", encoding="utf-8")

    result = sync_project(tmp_path)

    assert result.updated == ["CLAUDE.md"]
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == (
        tmp_path / "AGENTS.md"
    ).read_text(encoding="utf-8")


@pytest.mark.integration
def test_sync_adopts_existing_skill_directory(tmp_path: Path) -> None:
    """An existing unmanaged skill directory is adopted and synced from truth."""

    initialize_project(tmp_path, agents=("claude",), mode="copy")
    (tmp_path / ".claude/skills").mkdir(parents=True)
    (tmp_path / ".claude/skills/legacy").mkdir()
    (tmp_path / ".claude/skills/legacy/SKILL.md").write_text("# old\n", encoding="utf-8")
    source = tmp_path / ".agents/skills/demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("---\nname: demo\n---\n# demo\n", encoding="utf-8")

    result = sync_project(tmp_path)

    assert (tmp_path / ".claude/skills/demo/SKILL.md").is_file()
    assert not (tmp_path / ".claude/skills/legacy").exists()
    assert ".claude/skills" in result.updated or ".claude/skills" in result.created


@pytest.mark.integration
def test_sync_generates_for_all_enabled_agents(tmp_path: Path) -> None:
    """Enabled Agents generate outputs regardless of local CLI availability."""

    initialize_project(tmp_path, agents=("claude", "cursor"), mode="copy")

    result = sync_project(tmp_path)

    assert result.skipped == []
    assert "CLAUDE.md" in result.created


@pytest.mark.integration
def test_configuration_only_workbuddy_syncs_without_executable(tmp_path: Path) -> None:
    """Explicit WorkBuddy selection writes only project `.codebuddy` outputs."""

    initialize_project(tmp_path, agents=("workbuddy",), mode="copy")

    first = sync_project(tmp_path)
    second = sync_project(tmp_path)

    assert first.created == [".codebuddy/skills"]
    assert second.unchanged == [".codebuddy/skills"]
    assert not (tmp_path / ".codebuddy/rules/agent21.md").exists()
    assert not (tmp_path / ".codebuddy/.mcp.json").exists()


@pytest.mark.integration
def test_enabled_agent_outputs_persist_regardless_of_executable(tmp_path: Path) -> None:
    """Enabled Agent outputs are generated and kept even without a local CLI."""

    initialize_project(tmp_path, agents=("qoder",), mode="copy")
    sync_project(tmp_path)

    result = sync_project(tmp_path)

    assert result.skipped == []
    assert [artifact.path for artifact in load_manifest(tmp_path).managed_artifacts] == [
        ".qoder/skills"
    ]


@pytest.mark.integration
def test_instruction_edit_propagates_to_claude_md(tmp_path: Path) -> None:
    """权威 AGENTS.md 的修改会在下一次 sync 更新生成的 CLAUDE.md。"""

    initialize_project(tmp_path, agents=("claude",), mode="copy")
    sync_project(tmp_path)
    (tmp_path / "AGENTS.md").write_text("# New rules\n", encoding="utf-8")

    result = sync_project(tmp_path)

    assert result.updated == ["CLAUDE.md"]
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "# New rules\n"


@pytest.mark.integration
def test_sync_without_init_guides_user_to_initialize(tmp_path: Path) -> None:
    """Sync on an uninitialized project fails fast with an actionable message."""

    with pytest.raises(ConfigError, match="run 'agent21' first"):
        sync_project(tmp_path)
