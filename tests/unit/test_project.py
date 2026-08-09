"""Unit tests for project-root and safe path helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.errors import BoundaryError
from agent21.project import Project, display_path, find_project_root, safe_join, safe_relative_path


def test_find_project_root_accepts_current_directory_with_git_or_agents(tmp_path: Path) -> None:
    """A project root is recognized by common repository or Agent21 markers."""

    root = tmp_path / "repo"
    nested = root / "src" / "pkg"
    nested.mkdir(parents=True)
    (root / ".git").mkdir()

    assert find_project_root(nested) == root.resolve()


def test_find_project_root_falls_back_to_start_directory(tmp_path: Path) -> None:
    """Empty projects can still be initialized from their current directory."""

    start = tmp_path / "empty"
    start.mkdir()

    assert find_project_root(start) == start.resolve()


def test_safe_join_rejects_parent_traversal(tmp_path: Path) -> None:
    """Relative paths are resolved and checked before use."""

    project = Project(tmp_path)

    assert safe_join(project.root, "nested/file.txt") == (tmp_path / "nested/file.txt").resolve()
    with pytest.raises(BoundaryError):
        safe_join(project.root, "../outside.txt")


def test_safe_relative_path_rejects_symlink_escape(tmp_path: Path) -> None:
    """Containment checks resolve symlinks before accepting a target."""

    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "link"
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(BoundaryError):
        safe_relative_path(root, link / "secret.txt")


def test_display_path_normalizes_separators_and_dot(tmp_path: Path) -> None:
    """User-facing project paths are stable POSIX strings."""

    root = tmp_path / "repo"
    nested = root / "nested" / "file.txt"
    root.mkdir()

    assert display_path(root, root) == "."
    assert display_path(root, nested) == "nested/file.txt"
