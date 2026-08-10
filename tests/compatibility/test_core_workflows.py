"""Platform-neutral core workflow smoke tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.doctor import diagnose_project, has_blocked
from agent21.init import initialize_project
from agent21.skills import install_skill, remove_skill
from agent21.sync import sync_project


@pytest.mark.compatibility
def test_core_workflow_handles_project_path_with_spaces(tmp_path: Path) -> None:
    """Init, sync, doctor, and Skill lifecycle remain inside a spaced root path."""

    root = tmp_path / "team project"
    initialize_project(root, agents=("claude",), mode="copy")
    source = root / "source/demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
    install_skill(root, "source/demo")
    sync_project(root)

    assert not has_blocked(diagnose_project(root))
    remove_skill(root, "demo")
    sync_project(root)
    assert not has_blocked(diagnose_project(root))
