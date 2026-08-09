"""Unit tests for deterministic and redacted file tree snapshots."""

from pathlib import Path

from tests.support.tree_snapshot import (
    redact_absolute_path,
    redact_credentials,
    snapshot_tree,
)


def test_snapshot_tree_sorts_paths_and_normalizes_separators(tmp_path: Path) -> None:
    """Snapshot entries use deterministic POSIX-style relative paths."""

    root = tmp_path / "project"
    (root / "b").mkdir(parents=True)
    (root / "b" / "two.txt").write_text("two\n", encoding="utf-8")
    (root / "a.txt").write_text("one\n", encoding="utf-8")

    snapshot = snapshot_tree(root)

    assert [entry.path for entry in snapshot.entries] == ["a.txt", "b", "b/two.txt"]


def test_snapshot_tree_redacts_text_content(tmp_path: Path) -> None:
    """Caller redactors remove environment-specific and secret output."""

    root = tmp_path / "project"
    root.mkdir()
    (root / "config.txt").write_text(
        f"path={root.as_posix()}\napi_key=fixture-secret-value\n",
        encoding="utf-8",
    )

    snapshot = snapshot_tree(root, redactors=(redact_absolute_path(root), redact_credentials))

    entry = snapshot.by_path()["config.txt"]
    assert "<PROJECT>" in (entry.content or "")
    assert "fixture-secret-value" not in (entry.content or "")


def test_snapshot_tree_records_binary_digest_without_content(tmp_path: Path) -> None:
    """Binary files are compared by digest and not embedded in review output."""

    root = tmp_path / "project"
    root.mkdir()
    (root / "asset.bin").write_bytes(b"\x00\x01\x02")

    entry = snapshot_tree(root).by_path()["asset.bin"]

    assert entry.digest
    assert entry.content is None


def test_snapshot_tree_ignores_cache_directories(tmp_path: Path) -> None:
    """Volatile pytest and bytecode cache directories stay out of baselines."""

    root = tmp_path / "project"
    (root / ".pytest_cache").mkdir(parents=True)
    (root / ".pytest_cache" / "data").write_text("volatile\n", encoding="utf-8")
    (root / "stable.txt").write_text("stable\n", encoding="utf-8")

    snapshot = snapshot_tree(root)

    assert list(snapshot.by_path()) == ["stable.txt"]
