"""Tests for managed-only, drift-safe Skill removal."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.init import initialize_project
from agent21.skills import SkillConflictError, install_skill, remove_skill


@pytest.mark.integration
def test_remove_deletes_only_unchanged_managed_skill(tmp_path: Path) -> None:
    """Removal updates both the managed directory and manifest record."""

    initialize_project(tmp_path, agents=())
    source = tmp_path / "source/demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
    install_skill(tmp_path, "source/demo")

    remove_skill(tmp_path, "demo")

    assert not (tmp_path / ".agents/skills/demo").exists()


@pytest.mark.integration
@pytest.mark.safety
def test_remove_refuses_drifted_skill(tmp_path: Path) -> None:
    """Hand-edited managed Skill content is never deleted silently."""

    initialize_project(tmp_path, agents=())
    source = tmp_path / "source/demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
    install_skill(tmp_path, "source/demo")
    target = tmp_path / ".agents/skills/demo/SKILL.md"
    target.write_text("# User change\n", encoding="utf-8")

    with pytest.raises(SkillConflictError, match="drift"):
        remove_skill(tmp_path, "demo")

    assert target.is_file()
