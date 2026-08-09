"""Deterministic file-tree snapshots for Agent21 test fixtures."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

Redactor = Callable[[str], str]


@dataclass(frozen=True, order=True)
class TreeEntry:
    """A normalized representation of one filesystem object."""

    path: str
    kind: str
    digest: str | None = None
    content: str | None = None
    target: str | None = None


@dataclass(frozen=True)
class TreeSnapshot:
    """A stable, comparable snapshot of a project tree."""

    root: Path
    entries: tuple[TreeEntry, ...]

    def by_path(self) -> dict[str, TreeEntry]:
        """Index snapshot entries by normalized relative path."""

        return {entry.path: entry for entry in self.entries}


def snapshot_tree(
    root: Path,
    *,
    redactors: Iterable[Redactor] = (),
    ignore_names: Iterable[str] = (".git", "__pycache__", ".pytest_cache"),
) -> TreeSnapshot:
    """Capture a deterministic snapshot with normalized text content."""

    resolved_root = root.resolve()
    ignored = set(ignore_names)
    entries: list[TreeEntry] = []

    for path in sorted(resolved_root.rglob("*"), key=lambda item: _relative(item, resolved_root)):
        if any(part in ignored for part in path.relative_to(resolved_root).parts):
            continue
        entries.append(_snapshot_entry(path, resolved_root, tuple(redactors)))

    return TreeSnapshot(resolved_root, tuple(sorted(entries)))


def redact_text(text: str, *redactors: Redactor) -> str:
    """Normalize line endings and apply caller-provided redaction hooks."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    for redactor in redactors:
        normalized = redactor(normalized)
    return normalized


def redact_absolute_path(root: Path, replacement: str = "<PROJECT>") -> Redactor:
    """Build a redactor that hides platform-specific absolute project paths."""

    root_text = root.resolve().as_posix()

    def _redact(value: str) -> str:
        return value.replace(root_text, replacement)

    return _redact


def redact_credentials(text: str) -> str:
    """Hide common key, token, and secret assignments in stable snapshots."""

    patterns = (
        r"(?i)(api[_-]?key\s*[=:]\s*)[^\s]+",
        r"(?i)(token\s*[=:]\s*)[^\s]+",
        r"(?i)(secret\s*[=:]\s*)[^\s]+",
    )
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, r"\1<REDACTED>", redacted)
    return redacted


def _snapshot_entry(path: Path, root: Path, redactors: tuple[Redactor, ...]) -> TreeEntry:
    """Convert one path into a normalized snapshot entry."""

    relative_path = _relative(path, root)
    if path.is_symlink():
        return TreeEntry(relative_path, "symlink", target=path.readlink().as_posix())
    if path.is_dir():
        return TreeEntry(relative_path, "directory")
    payload = path.read_bytes()
    if _is_probably_text(payload):
        content = redact_text(payload.decode("utf-8"), *redactors)
        digest = sha256(content.encode("utf-8")).hexdigest()
        return TreeEntry(relative_path, "file", digest=digest, content=content)
    return TreeEntry(relative_path, "file", digest=sha256(payload).hexdigest())


def _relative(path: Path, root: Path) -> str:
    """Return a POSIX relative path for platform-stable ordering."""

    return path.relative_to(root).as_posix()


def _is_probably_text(payload: bytes) -> bool:
    """Classify bytes as UTF-8 text when snapshot content can be reviewed."""

    try:
        payload.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return b"\0" not in payload
