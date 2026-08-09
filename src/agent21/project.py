"""Project root and boundary-safe path helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePath

from agent21.errors import BoundaryError
from agent21.models import validate_project_path

PROJECT_MARKERS = (".git", ".agents", "AGENTS.md", ".mcp.json")


@dataclass(frozen=True)
class Project:
    """Resolved project root wrapper used by foundational services."""

    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.resolve())

    def join(self, relative_path: str | PurePath) -> Path:
        """Resolve a project-relative path and enforce containment."""

        return safe_join(self.root, relative_path)

    def display(self, path: str | PurePath) -> str:
        """Format a path relative to this project root."""

        return display_path(self.root, path)


def find_project_root(start: str | PurePath = ".") -> Path:
    """Find the nearest parent with project markers, or return the start directory."""

    current = Path(start).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in PROJECT_MARKERS):
            return candidate
    return current


def safe_join(project_root: str | PurePath, relative_path: str | PurePath) -> Path:
    """Join a project-relative value to the root after lexical validation."""

    value = validate_project_path(relative_path)
    candidate = Path(project_root) / value
    safe_relative_path(project_root, candidate)
    return candidate.resolve(strict=False)


def safe_relative_path(project_root: str | PurePath, candidate: str | PurePath) -> Path:
    """Resolve symlinks and reject candidates outside the project root."""

    root = Path(project_root).resolve()
    path = Path(candidate)
    unresolved = path if path.is_absolute() else root / path
    resolved = _resolve_existing_parent(unresolved)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise BoundaryError(f"path is outside project: {display_path(root, unresolved)}") from exc
    return unresolved


def display_path(project_root: str | PurePath, path: str | PurePath) -> str:
    """Return a stable POSIX display path relative to the project when possible."""

    root = Path(project_root).resolve()
    candidate = Path(path)
    absolute = candidate if candidate.is_absolute() else root / candidate
    try:
        relative = absolute.resolve(strict=False).relative_to(root)
    except ValueError:
        return absolute.resolve(strict=False).as_posix()
    value = relative.as_posix()
    return value if value else "."


def _resolve_existing_parent(path: Path) -> Path:
    """Resolve symlinked parents even when the final path does not exist yet."""

    if path.exists() or path.is_symlink():
        return path.resolve()
    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    resolved_parent = parent.resolve()
    return resolved_parent / path.relative_to(parent)
