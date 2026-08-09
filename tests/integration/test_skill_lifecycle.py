"""Integration tests for local Skill installation and listing."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.init import initialize_project
from agent21.manifest import load_manifest
from agent21.skills import SkillConflictError, install_skill, list_skills, remove_skill


@pytest.mark.integration
def test_local_skill_install_records_digest_and_metadata(tmp_path: Path) -> None:
    """A valid project-local Skill is copied and recorded in the manifest."""

    initialize_project(tmp_path, agents=(), assume_yes=True)
    source = tmp_path / "skill-sources/demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text(
        "---\nname: demo\nversion: 1.2.3\n---\n# Demo\n", encoding="utf-8"
    )

    record = install_skill(tmp_path, str(source.relative_to(tmp_path)))

    assert record.name == "demo"
    assert record.version == "1.2.3"
    assert (tmp_path / record.path / "SKILL.md").is_file()
    assert list_skills(tmp_path) == (record,)
    assert load_manifest(tmp_path).skills == [record]


@pytest.mark.integration
@pytest.mark.safety
def test_local_skill_rejects_invalid_name_and_missing_skill_file(tmp_path: Path) -> None:
    """Invalid packages fail before the unified Skills directory changes."""

    initialize_project(tmp_path, agents=(), assume_yes=True)
    source = tmp_path / "Bad_Name"
    source.mkdir()

    with pytest.raises(ValueError):
        install_skill(tmp_path, "Bad_Name")

    assert not (tmp_path / ".agents/skills/Bad_Name").exists()


@pytest.mark.integration
def test_skill_lifecycle_rejects_duplicate_and_unmanaged_remove(tmp_path: Path) -> None:
    """Occupied installs and unknown removals never change manifest ownership."""

    initialize_project(tmp_path, agents=(), assume_yes=True)
    source = tmp_path / "source/demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
    install_skill(tmp_path, "source/demo")

    with pytest.raises(SkillConflictError, match="occupied"):
        install_skill(tmp_path, "source/demo")
    with pytest.raises(SkillConflictError, match="not managed"):
        remove_skill(tmp_path, "missing")


@pytest.mark.integration
@pytest.mark.safety
def test_skill_install_rejects_nested_symlink(tmp_path: Path) -> None:
    """Skill copies cannot dereference a nested link to project-external content."""

    initialize_project(tmp_path, agents=(), assume_yes=True)
    source = tmp_path / "source/demo"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
    outside = tmp_path.parent / "outside-skill-data"
    outside.write_text("private\n", encoding="utf-8")
    (source / "linked.txt").symlink_to(outside)

    with pytest.raises(ValueError, match="symbolic links"):
        install_skill(tmp_path, "source/demo")

    assert not (tmp_path / ".agents/skills/demo").exists()
