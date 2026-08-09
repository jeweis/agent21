"""Project fixture helpers for isolated Agent21 workflow tests.

The source fixtures under ``tests/fixtures/projects`` are treated as immutable
test assets.  Tests must copy them into a temporary directory before running
code that may write files.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "projects"


class ProjectBoundaryError(ValueError):
    """Raised when a requested test path escapes the copied project root."""


@dataclass(frozen=True)
class ProjectFixture:
    """A copied project fixture and the immutable source it came from."""

    fixture_id: str
    source_path: Path
    root: Path
    protected_paths: tuple[Path, ...]

    def path(self, *parts: str) -> Path:
        """Return a path inside the copied fixture after boundary validation."""

        return assert_inside_project(self.root, self.root.joinpath(*parts))


@dataclass(frozen=True)
class ProtectedFileState:
    """Byte-for-byte baseline for a file that product code must not mutate."""

    relative_path: Path
    file_type: str
    payload: bytes


def available_project_fixtures() -> tuple[str, ...]:
    """Return fixture directory names in deterministic order."""

    if not FIXTURES_ROOT.exists():
        return ()
    return tuple(path.name for path in sorted(FIXTURES_ROOT.iterdir()) if path.is_dir())


def fixture_source_path(fixture_id: str) -> Path:
    """Resolve a fixture id to a source path without allowing traversal."""

    if not fixture_id or Path(fixture_id).name != fixture_id:
        raise ValueError(f"Invalid fixture id: {fixture_id!r}")

    source_path = (FIXTURES_ROOT / fixture_id).resolve()
    fixtures_root = FIXTURES_ROOT.resolve()
    if not source_path.is_dir() or not _is_relative_to(source_path, fixtures_root):
        raise FileNotFoundError(f"Unknown project fixture: {fixture_id}")
    return source_path


def copy_project_fixture(
    fixture_id: str,
    tmp_path: Path,
    *,
    protected_paths: tuple[str, ...] = (),
) -> ProjectFixture:
    """Copy a source fixture into ``tmp_path`` and return its writable root."""

    source_path = fixture_source_path(fixture_id)
    destination = tmp_path / fixture_id
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    shutil.copytree(source_path, destination, symlinks=True)
    protected = tuple(
        assert_inside_project(destination, destination / item) for item in protected_paths
    )
    return ProjectFixture(fixture_id, source_path, destination, protected)


def assert_inside_project(project_root: Path, candidate: Path) -> Path:
    """Resolve ``candidate`` and require it to stay within ``project_root``."""

    root = project_root.resolve()
    resolved = candidate.resolve(strict=False)
    if resolved == root or _is_relative_to(resolved, root):
        return resolved
    raise ProjectBoundaryError(f"Path escapes project boundary: {candidate}")


def capture_protected_files(
    project_root: Path,
    paths: tuple[str | Path, ...],
) -> dict[Path, ProtectedFileState]:
    """Capture bytes and object types for unmanaged files before a workflow runs."""

    captured: dict[Path, ProtectedFileState] = {}
    for raw_path in paths:
        relative_path = Path(raw_path)
        target = assert_inside_project(project_root, project_root / relative_path)
        if target.is_symlink():
            file_type = "symlink"
            payload = target.readlink().as_posix().encode("utf-8")
        elif target.is_file():
            file_type = "file"
            payload = target.read_bytes()
        elif target.is_dir():
            file_type = "directory"
            payload = b""
        else:
            raise FileNotFoundError(f"Protected path does not exist: {relative_path}")
        captured[relative_path] = ProtectedFileState(relative_path, file_type, payload)
    return captured


def create_external_sentinel(tmp_path: Path, name: str = "outside-sentinel.txt") -> Path:
    """Create a project-outside sentinel used by boundary safety tests."""

    sentinel = tmp_path / name
    sentinel.write_text("external sentinel must remain unchanged\n", encoding="utf-8")
    return sentinel


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Compatibility wrapper for Path.is_relative_to behavior."""

    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
