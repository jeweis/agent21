"""Integration tests for Git-backed Skill installation."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent21.init import initialize_project
from agent21.skills import install_skill


@pytest.mark.integration
def test_git_skill_install_excludes_repository_metadata(tmp_path: Path) -> None:
    """Git transport metadata never becomes part of the managed Skill asset."""

    initialize_project(tmp_path, agents=())
    repository = tmp_path / "repo/demo-git"
    repository.mkdir(parents=True)
    (repository / "SKILL.md").write_text("# Demo Git\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(["git", "-C", str(repository), "add", "SKILL.md"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )

    record = install_skill(tmp_path, repository.as_uri())

    assert record.source_type.value == "git"
    assert not (tmp_path / record.path / ".git").exists()


@pytest.mark.integration
def test_invalid_git_repository_leaves_no_target(tmp_path: Path) -> None:
    """Clone or validation failure cannot leave a partially installed Skill."""

    initialize_project(tmp_path, agents=())

    with pytest.raises(ValueError, match="unable to clone"):
        install_skill(tmp_path, (tmp_path / "missing.git").as_uri())

    assert list((tmp_path / ".agents/skills").iterdir()) == []
