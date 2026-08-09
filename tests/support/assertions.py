"""Reusable assertions for diagnostics, idempotency, and file safety."""

from __future__ import annotations

import re
from pathlib import Path

from tests.support.cli_runner import CliResult
from tests.support.project_factory import ProtectedFileState
from tests.support.tree_snapshot import TreeSnapshot

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret)\s*[=:]\s*[A-Za-z0-9_./+-]{8,}"),
    re.compile(r"sk-[A-Za-z0-9]{12,}"),
    re.compile(r"fixture-secret-[A-Za-z0-9_-]+"),
)


def redact_diagnostics(text: str) -> str:
    """Redact common secret-looking values from command diagnostics."""

    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: _redact_match(match.group(0)), redacted)
    return redacted


def assert_no_credentials(output: str) -> None:
    """Fail when diagnostics expose token-like fixture secrets."""

    for pattern in SECRET_PATTERNS:
        if pattern.search(output):
            raise AssertionError("diagnostic output contains an unredacted credential")


def assert_diagnostic_contains(
    result: CliResult,
    *,
    subject: str,
    action: str,
    next_step: str,
) -> None:
    """Require failures to name the object, failed action, and next step."""

    output = result.combined_output
    missing = [item for item in (subject, action, next_step) if item not in output]
    if missing:
        raise AssertionError(f"diagnostic output missing: {', '.join(missing)}")
    assert_no_credentials(output)


def assert_snapshots_equal(before: TreeSnapshot, after: TreeSnapshot) -> None:
    """Assert two normalized tree snapshots are identical."""

    if before.entries != after.entries:
        raise AssertionError(_format_snapshot_diff(before, after))


def assert_idempotent(first: TreeSnapshot, second: TreeSnapshot) -> None:
    """Assert repeated workflow execution produced no new tree differences."""

    assert_snapshots_equal(first, second)


def assert_protected_files_unchanged(
    project_root: Path,
    before: dict[Path, ProtectedFileState],
) -> None:
    """Compare captured protected files against current filesystem bytes."""

    for relative_path, state in before.items():
        target = project_root / relative_path
        if state.file_type == "symlink":
            current_type = "symlink"
            payload = target.readlink().as_posix().encode("utf-8")
        elif target.is_file():
            current_type = "file"
            payload = target.read_bytes()
        elif target.is_dir():
            current_type = "directory"
            payload = b""
        else:
            raise AssertionError(f"protected path disappeared: {relative_path}")
        if current_type != state.file_type or payload != state.payload:
            raise AssertionError(f"protected path changed: {relative_path}")


def _redact_match(value: str) -> str:
    """Preserve key names in redacted key-value diagnostics."""

    if "=" in value:
        return f"{value.split('=', 1)[0]}=<REDACTED>"
    if ":" in value:
        return f"{value.split(':', 1)[0]}:<REDACTED>"
    return "<REDACTED>"


def _format_snapshot_diff(before: TreeSnapshot, after: TreeSnapshot) -> str:
    """Return a concise path-level diff for failed idempotency assertions."""

    before_paths = before.by_path()
    after_paths = after.by_path()
    added = sorted(set(after_paths) - set(before_paths))
    removed = sorted(set(before_paths) - set(after_paths))
    changed = sorted(
        path
        for path in set(before_paths) & set(after_paths)
        if before_paths[path] != after_paths[path]
    )
    return f"tree snapshots differ; added={added}, removed={removed}, changed={changed}"
