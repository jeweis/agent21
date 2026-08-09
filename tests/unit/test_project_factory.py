"""Unit tests for isolated project fixture copying and boundary checks."""

from pathlib import Path

import pytest

from tests.support.project_factory import (
    ProjectBoundaryError,
    assert_inside_project,
    available_project_fixtures,
    capture_protected_files,
    copy_project_fixture,
    create_external_sentinel,
)


def test_available_fixtures_include_required_project_shapes() -> None:
    """The foundational fixture catalog exposes all planned project shapes."""

    assert set(available_project_fixtures()) >= {
        "empty_project",
        "agents_project",
        "claude_project",
        "cursor_project",
        "mixed_project",
        "broken_project",
    }


def test_copy_project_fixture_uses_writable_tmp_copy(tmp_path: Path) -> None:
    """Mutating a copied fixture must not mutate the repository fixture source."""

    fixture = copy_project_fixture("empty_project", tmp_path)
    copied_readme = fixture.root / "README.md"
    source_readme = fixture.source_path / "README.md"

    copied_readme.write_text("changed in isolated copy\n", encoding="utf-8")

    assert fixture.root.is_dir()
    assert copied_readme.read_text(encoding="utf-8") != source_readme.read_text(encoding="utf-8")


def test_copy_project_fixture_rejects_traversal_fixture_id(tmp_path: Path) -> None:
    """Fixture ids are names, not paths supplied by the test caller."""

    with pytest.raises(ValueError):
        copy_project_fixture("../mixed_project", tmp_path)


def test_assert_inside_project_rejects_external_paths(tmp_path: Path) -> None:
    """Boundary validation resolves candidate paths before accepting them."""

    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("sentinel\n", encoding="utf-8")

    nested_file = project / "nested" / "file.txt"

    assert assert_inside_project(project, nested_file) == nested_file
    with pytest.raises(ProjectBoundaryError):
        assert_inside_project(project, project / ".." / "outside.txt")


def test_capture_protected_files_detects_unmanaged_mutation(tmp_path: Path) -> None:
    """Protected file baselines preserve bytes for later safety assertions."""

    fixture = copy_project_fixture("mixed_project", tmp_path)
    protected = capture_protected_files(fixture.root, (Path("notes/unmanaged.txt"),))

    (fixture.root / "notes/unmanaged.txt").write_text("mutated\n", encoding="utf-8")

    assert protected[Path("notes/unmanaged.txt")].payload != b"mutated\n"


def test_external_sentinel_is_created_outside_project(tmp_path: Path) -> None:
    """Path-escape tests need an explicit project-outside sentinel file."""

    fixture = copy_project_fixture("empty_project", tmp_path)
    sentinel = create_external_sentinel(tmp_path)

    assert sentinel.exists()
    assert not str(sentinel).startswith(str(fixture.root))
