"""Cross-platform synchronization mode and path behavior tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.init import initialize_project
from agent21.sync import sync_project


@pytest.mark.compatibility
def test_auto_mode_creates_project_relative_skill_link_when_supported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Auto mode prefers a relative project-local link on capable filesystems."""

    root = tmp_path / "project with spaces"
    initialize_project(root, agents=("claude",), mode="auto")
    monkeypatch.setattr("agent21.sync.supports_symlink", lambda _: True)

    sync_project(root, available_agents={"claude": True})

    link = root / ".claude/skills"
    assert link.is_symlink()
    assert not link.readlink().is_absolute()
    assert link.resolve() == (root / ".agents/skills").resolve()


@pytest.mark.compatibility
def test_auto_mode_falls_back_to_copy_when_links_are_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Auto mode produces an owned directory copy when link creation is unavailable."""

    initialize_project(tmp_path, agents=("claude",), mode="auto")
    (tmp_path / ".agents/skills/demo").mkdir()
    (tmp_path / ".agents/skills/demo/SKILL.md").write_text("# Demo\n", encoding="utf-8")
    monkeypatch.setattr("agent21.sync.supports_symlink", lambda _: False)

    sync_project(tmp_path, available_agents={"claude": True})

    target = tmp_path / ".claude/skills"
    assert target.is_dir()
    assert not target.is_symlink()
    assert (target / "demo/SKILL.md").is_file()
