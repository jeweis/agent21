"""Safe project-scoped filesystem transaction helpers for Agent21.

The sync layer owns planning and manifest semantics; this module owns the
low-level guarantee that project writes are prevalidated, staged, applied
atomically where the platform allows, and rolled back on failure.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Literal
from uuid import uuid4

ArtifactKind = Literal["file", "directory", "symlink"]
ArtifactMode = Literal["copy", "symlink", "transform"]


class TransactionError(RuntimeError):
    """Raised when a staged filesystem transaction cannot complete safely."""


class ArtifactConflictError(TransactionError):
    """Raised when prevalidation finds a blocking artifact conflict."""


@dataclass(frozen=True)
class PlannedArtifact:
    """Side-effect-free artifact plan produced by an adapter or sync planner."""

    agent: str
    target: Path
    kind: ArtifactKind
    mode: ArtifactMode
    source: Path | None = None
    content: bytes | None = None
    digest: str | None = None


@dataclass(frozen=True)
class TransactionResult:
    """Deterministic summary of transaction effects."""

    created: tuple[Path, ...] = ()
    updated: tuple[Path, ...] = ()
    unchanged: tuple[Path, ...] = ()


@dataclass(frozen=True)
class ValidatedArtifact:
    """Project-resolved artifact with computed digest and target status."""

    plan: PlannedArtifact
    relative_target: Path
    absolute_target: Path
    absolute_source: Path | None
    digest: str
    unchanged: bool
    exists: bool


@dataclass
class JournalEntry:
    """Backup information needed to undo one applied target."""

    target: Path
    backup: Path | None
    existed: bool


@dataclass
class TransactionJournal:
    """Small JSON-serializable journal kept while a transaction is active."""

    transaction_id: str
    command: str
    entries: list[JournalEntry] = field(default_factory=list)
    state: str = "staging"


def project_relative(path: Path | str) -> Path:
    """Normalize a project-relative path to a POSIX-like `Path`."""

    raw = PurePosixPath(str(path).replace("\\", "/"))
    if raw.is_absolute() or any(part in {"", ".", ".."} for part in raw.parts):
        raise ArtifactConflictError(f"path is outside project: {path}")
    return Path(*raw.parts)


def resolve_inside_project(project_root: Path, relative_path: Path | str) -> Path:
    """Resolve a path and require it to stay under the project root."""

    root = project_root.resolve()
    candidate = (root / project_relative(relative_path)).resolve(strict=False)
    if candidate != root and root not in candidate.parents:
        raise ArtifactConflictError(f"path is outside project: {relative_path}")
    return candidate


def bytes_digest(payload: bytes) -> str:
    """Return the Agent21 `sha256:<hex>` digest for bytes."""

    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def file_digest(path: Path) -> str:
    """Hash a file's raw bytes."""

    return bytes_digest(path.read_bytes())


def symlink_digest(link_text: str | Path) -> str:
    """Hash the target string used for a symlink."""

    return bytes_digest(str(link_text).encode("utf-8"))


def directory_digest(path: Path) -> str:
    """Hash a directory by sorted relative paths, object types, and content."""

    hasher = hashlib.sha256()
    children = sorted(item for item in path.rglob("*") if item.is_file() or item.is_symlink())
    for child in children:
        rel = child.relative_to(path).as_posix().encode("utf-8")
        hasher.update(rel)
        hasher.update(b"\0")
        if child.is_symlink():
            hasher.update(b"L")
            hasher.update(os.readlink(child).encode("utf-8"))
        else:
            hasher.update(b"F")
            hasher.update(child.read_bytes())
        hasher.update(b"\0")
    return f"sha256:{hasher.hexdigest()}"


def supports_symlink(project_root: Path) -> bool:
    """Probe project-filesystem symlink support and remove all probe artifacts."""

    probe_root = project_root.resolve() / ".agents" / ".symlink-probe"
    source = probe_root / "source"
    link = probe_root / "link"
    try:
        source.mkdir(parents=True)
        link.symlink_to("source", target_is_directory=True)
        return link.is_symlink() and link.resolve() == source.resolve()
    except OSError:
        return False
    finally:
        if link.is_symlink() or link.exists():
            link.unlink(missing_ok=True)
        shutil.rmtree(probe_root, ignore_errors=True)


def prevalidate_artifacts(
    project_root: Path,
    artifacts: Iterable[PlannedArtifact],
    *,
    managed_paths: Iterable[Path | str],
) -> tuple[ValidatedArtifact, ...]:
    """Validate all planned targets before any write begins."""

    managed = {project_relative(path) for path in managed_paths}
    validated: list[ValidatedArtifact] = []
    seen: set[Path] = set()
    for plan in sorted(artifacts, key=lambda item: project_relative(item.target).as_posix()):
        relative_target = project_relative(plan.target)
        if relative_target in seen:
            raise ArtifactConflictError(f"duplicate planned target: {relative_target.as_posix()}")
        seen.add(relative_target)
        target = resolve_inside_project(project_root, relative_target)
        source = _validate_source(project_root, plan)
        digest = plan.digest or _planned_digest(project_root, plan, source)
        exists = target.exists() or target.is_symlink()
        if exists and relative_target not in managed:
            raise ArtifactConflictError(f"unmanaged target conflict: {relative_target.as_posix()}")
        unchanged = exists and _existing_digest(target, plan.kind) == digest
        validated.append(
            ValidatedArtifact(plan, relative_target, target, source, digest, unchanged, exists)
        )
    return tuple(validated)


def apply_transaction(
    project_root: Path,
    artifacts: Iterable[PlannedArtifact],
    *,
    managed_paths: Iterable[Path | str],
    command: str = "sync",
    manifest_writer: Callable[[], None] | None = None,
    before_replace: Callable[[Path], None] | None = None,
) -> TransactionResult:
    """Apply a set of artifacts with staging, rollback, and cleanup."""

    root = project_root.resolve()
    validated = prevalidate_artifacts(root, artifacts, managed_paths=managed_paths)
    changed = [item for item in validated if not item.unchanged]
    if not changed:
        return TransactionResult(unchanged=tuple(item.relative_target for item in validated))

    tmp_root = root / ".agents" / ".tmp"
    transaction_id = uuid4().hex
    transaction_root = tmp_root / transaction_id
    staging_root = transaction_root / "stage"
    backup_root = transaction_root / "backup"
    journal = TransactionJournal(transaction_id=transaction_id, command=command)
    try:
        staging_root.mkdir(parents=True)
        backup_root.mkdir()
        _write_journal(transaction_root, journal)
        staged = _stage_artifacts(staging_root, changed)
        journal.state = "applying"
        _write_journal(transaction_root, journal)
        _apply_staged(changed, staged, backup_root, journal, transaction_root, before_replace)
        if manifest_writer is not None:
            manifest_writer()
        journal.state = "committed"
        _write_journal(transaction_root, journal)
    except Exception as exc:
        _rollback(journal)
        raise TransactionError(str(exc)) from exc
    finally:
        shutil.rmtree(transaction_root, ignore_errors=True)
        _remove_empty_tmp(tmp_root)

    created = tuple(item.relative_target for item in changed if not item.exists)
    updated = tuple(item.relative_target for item in changed if item.exists)
    unchanged = tuple(item.relative_target for item in validated if item.unchanged)
    return TransactionResult(created=created, updated=updated, unchanged=unchanged)


def _validate_source(project_root: Path, plan: PlannedArtifact) -> Path | None:
    """Validate source presence and project boundary for copy/symlink plans."""

    if plan.kind in {"directory", "symlink"} or plan.mode in {"copy", "symlink"}:
        if plan.source is None:
            raise ArtifactConflictError(f"source is required for {plan.target}")
        source = resolve_inside_project(project_root, plan.source)
        if not source.exists():
            raise ArtifactConflictError(f"source does not exist: {plan.source}")
        return source
    if plan.content is None:
        raise ArtifactConflictError(f"content is required for {plan.target}")
    return None


def _planned_digest(project_root: Path, plan: PlannedArtifact, source: Path | None) -> str:
    """Compute the digest that will exist after applying a plan."""

    if plan.kind == "symlink":
        if source is None:
            raise ArtifactConflictError(f"source is required for {plan.target}")
        target_parent = resolve_inside_project(project_root, plan.target).parent
        return symlink_digest(os.path.relpath(source, target_parent))
    if plan.content is not None:
        return bytes_digest(plan.content)
    if source is None:
        raise ArtifactConflictError(f"source or content is required for {plan.target}")
    return directory_digest(source) if source.is_dir() else file_digest(source)


def _existing_digest(target: Path, kind: ArtifactKind) -> str | None:
    """Compute the current target digest for idempotency checks."""

    if kind == "symlink" and target.is_symlink():
        return symlink_digest(os.readlink(target))
    if kind == "directory" and target.is_dir():
        return directory_digest(target)
    if kind == "file" and target.is_file():
        return file_digest(target)
    return None


def _stage_artifacts(
    staging_root: Path, artifacts: Iterable[ValidatedArtifact]
) -> Mapping[Path, Path]:
    """Materialize complete target payloads under the transaction directory."""

    staged: dict[Path, Path] = {}
    for item in artifacts:
        stage_path = staging_root / item.relative_target
        stage_path.parent.mkdir(parents=True, exist_ok=True)
        if item.plan.kind == "symlink":
            if item.absolute_source is None:
                raise ArtifactConflictError(f"source is required for {item.relative_target}")
            link_text = os.path.relpath(item.absolute_source, item.absolute_target.parent)
            stage_path.symlink_to(link_text, target_is_directory=item.absolute_source.is_dir())
        elif item.plan.content is not None:
            stage_path.write_bytes(item.plan.content)
        elif item.absolute_source is not None and item.absolute_source.is_dir():
            shutil.copytree(item.absolute_source, stage_path, symlinks=True)
        elif item.absolute_source is not None:
            shutil.copy2(item.absolute_source, stage_path)
        else:
            raise ArtifactConflictError(f"source or content is required for {item.relative_target}")
        staged[item.relative_target] = stage_path
    return staged


def _apply_staged(
    artifacts: Iterable[ValidatedArtifact],
    staged: Mapping[Path, Path],
    backup_root: Path,
    journal: TransactionJournal,
    transaction_root: Path,
    before_replace: Callable[[Path], None] | None,
) -> None:
    """Replace targets in sorted order and persist journal entries first."""

    for item in artifacts:
        if before_replace is not None:
            before_replace(item.absolute_target)
        backup = backup_root / item.relative_target
        backup.parent.mkdir(parents=True, exist_ok=True)
        existed = item.absolute_target.exists() or item.absolute_target.is_symlink()
        if existed:
            shutil.move(str(item.absolute_target), str(backup))
        item.absolute_target.parent.mkdir(parents=True, exist_ok=True)
        journal.entries.append(
            JournalEntry(item.absolute_target, backup if existed else None, existed)
        )
        _write_journal(transaction_root, journal)
        shutil.move(str(staged[item.relative_target]), str(item.absolute_target))


def _rollback(journal: TransactionJournal) -> None:
    """Restore applied targets in reverse order after a failure."""

    journal.state = "rolling_back"
    for entry in reversed(journal.entries):
        if entry.target.exists() or entry.target.is_symlink():
            if entry.target.is_dir() and not entry.target.is_symlink():
                shutil.rmtree(entry.target)
            else:
                entry.target.unlink()
        if entry.existed and entry.backup is not None:
            entry.target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(entry.backup), str(entry.target))


def _write_journal(transaction_root: Path, journal: TransactionJournal) -> None:
    """Persist a small journal for doctor to diagnose dangling transactions."""

    payload = {
        "transaction_id": journal.transaction_id,
        "command": journal.command,
        "state": journal.state,
        "entries": [
            {
                "target": entry.target.as_posix(),
                "backup": None if entry.backup is None else entry.backup.as_posix(),
                "existed": entry.existed,
            }
            for entry in journal.entries
        ],
    }
    transaction_root.mkdir(parents=True, exist_ok=True)
    _atomic_write_bytes(
        transaction_root / "journal.json",
        json.dumps(payload, sort_keys=True, indent=2).encode("utf-8") + b"\n",
    )


def _atomic_write_bytes(target: Path, payload: bytes) -> None:
    """Write bytes through a same-directory temporary file and replace."""

    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    finally:
        temp_path.unlink(missing_ok=True)


def _remove_empty_tmp(tmp_root: Path) -> None:
    """Remove empty transaction parents after cleanup."""

    try:
        tmp_root.rmdir()
        tmp_root.parent.rmdir()
    except OSError:
        pass
