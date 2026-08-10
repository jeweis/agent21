"""Unit tests for safe filesystem transactions."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.fs import (
    ArtifactConflictError,
    PlannedArtifact,
    TransactionError,
    apply_transaction,
    directory_digest,
    file_digest,
    prevalidate_artifacts,
)
from agent21.models import ArtifactKind as ModelArtifactKind
from agent21.models import ArtifactMode as ModelArtifactMode


def test_transaction_creates_file_and_cleans_temporary_state(tmp_path: Path) -> None:
    """A successful transaction writes atomically and leaves no journal behind."""

    artifact = PlannedArtifact(
        agent="claude",
        target=Path("CLAUDE.md"),
        kind="file",
        mode="transform",
        content=b"# Claude\n",
    )

    result = apply_transaction(tmp_path, [artifact], managed_paths={Path("CLAUDE.md")})

    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "# Claude\n"
    assert result.created == (Path("CLAUDE.md"),)
    assert result.updated == ()
    assert not (tmp_path / ".agents" / ".tmp").exists()


def test_prevalidation_rejects_project_escape(tmp_path: Path) -> None:
    """Targets are resolved before writes so relative traversal cannot escape."""

    artifact = PlannedArtifact(
        agent="codex",
        target=Path("../outside.md"),
        kind="file",
        mode="transform",
        content=b"bad\n",
    )

    with pytest.raises(ArtifactConflictError, match="outside project"):
        prevalidate_artifacts(tmp_path, [artifact])


def test_prevalidation_adopts_existing_unmanaged_target(tmp_path: Path) -> None:
    """Existing targets are adopted and replaced by the authoritative content."""

    (tmp_path / "CLAUDE.md").write_text("user content\n", encoding="utf-8")
    artifact = PlannedArtifact(
        agent="claude",
        target=Path("CLAUDE.md"),
        kind="file",
        mode="transform",
        content=b"generated\n",
    )

    validated = prevalidate_artifacts(tmp_path, [artifact])

    assert len(validated) == 1
    assert validated[0].exists
    assert not validated[0].unchanged


def test_transaction_marks_matching_managed_file_unchanged(tmp_path: Path) -> None:
    """Managed outputs with matching digest are reported unchanged and not rewritten."""

    target = tmp_path / "CLAUDE.md"
    target.write_bytes(b"# Claude\n")
    before_mtime = target.stat().st_mtime_ns
    artifact = PlannedArtifact(
        agent="claude",
        target=Path("CLAUDE.md"),
        kind="file",
        mode="transform",
        content=b"# Claude\n",
    )

    result = apply_transaction(tmp_path, [artifact], managed_paths={Path("CLAUDE.md")})

    assert result.unchanged == (Path("CLAUDE.md"),)
    assert target.stat().st_mtime_ns == before_mtime


def test_transaction_normalizes_enum_artifact_kind_for_unchanged(
    tmp_path: Path,
) -> None:
    """String-like model enums follow the same unchanged path as literals."""

    target = tmp_path / "CLAUDE.md"
    target.write_bytes(b"# Claude\n")
    artifact = PlannedArtifact(
        agent="claude",
        target=Path("CLAUDE.md"),
        kind=ModelArtifactKind.FILE,
        mode=ModelArtifactMode.TRANSFORM,
        content=b"# Claude\n",
    )

    result = apply_transaction(tmp_path, [artifact], managed_paths={Path("CLAUDE.md")})

    assert result.unchanged == (Path("CLAUDE.md"),)


def test_transaction_rolls_back_applied_file_when_later_replace_fails(tmp_path: Path) -> None:
    """If apply fails mid-flight, earlier managed targets are restored."""

    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("old first\n", encoding="utf-8")
    second.write_text("old second\n", encoding="utf-8")
    artifacts = [
        PlannedArtifact(
            agent="claude",
            target=Path("first.md"),
            kind="file",
            mode="transform",
            content=b"new first\n",
        ),
        PlannedArtifact(
            agent="codex",
            target=Path("second.md"),
            kind="file",
            mode="transform",
            content=b"new second\n",
        ),
    ]

    def fail_on_second(path: Path) -> None:
        if path.name == "second.md":
            raise OSError("simulated replace failure")

    with pytest.raises(TransactionError, match="simulated replace failure"):
        apply_transaction(
            tmp_path,
            artifacts,
            managed_paths={Path("first.md"), Path("second.md")},
            before_replace=fail_on_second,
        )

    assert first.read_text(encoding="utf-8") == "old first\n"
    assert second.read_text(encoding="utf-8") == "old second\n"


def test_transaction_creates_project_relative_symlink(tmp_path: Path) -> None:
    """Symlink plans use relative links and keep the resolved source in-project."""

    source = tmp_path / ".agents" / "skills"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    artifact = PlannedArtifact(
        agent="claude",
        target=Path(".claude/skills"),
        kind="symlink",
        mode="symlink",
        source=Path(".agents/skills"),
    )

    apply_transaction(tmp_path, [artifact], managed_paths={Path(".claude/skills")})

    target = tmp_path / ".claude" / "skills"
    assert target.is_symlink()
    assert target.readlink() == Path("../.agents/skills")


def test_directory_digest_is_stable_for_file_order(tmp_path: Path) -> None:
    """Directory digests sort paths before hashing content."""

    directory = tmp_path / "skills"
    directory.mkdir()
    (directory / "b.txt").write_text("b\n", encoding="utf-8")
    (directory / "a.txt").write_text("a\n", encoding="utf-8")

    first = directory_digest(directory)
    (directory / "a.txt").write_text("a\n", encoding="utf-8")

    assert first == directory_digest(directory)
    assert file_digest(directory / "a.txt").startswith("sha256:")


def test_transaction_retires_managed_file(tmp_path: Path) -> None:
    """A retired managed target is removed inside the transaction, leaving no state."""

    target = tmp_path / "CLAUDE.md"
    target.write_text("# Claude\n", encoding="utf-8")

    result = apply_transaction(
        tmp_path,
        [],
        managed_paths={Path("CLAUDE.md")},
        retire=[Path("CLAUDE.md")],
    )

    assert not target.exists()
    assert result.retired == (Path("CLAUDE.md"),)
    assert not (tmp_path / ".agents" / ".tmp").exists()


def test_transaction_retire_rolls_back_when_later_apply_fails(tmp_path: Path) -> None:
    """A failed transaction restores both written and retired targets."""

    target = tmp_path / "CLAUDE.md"
    target.write_text("# Claude\n", encoding="utf-8")
    artifact = PlannedArtifact(
        agent="claude",
        target=Path("AGENTS.md"),
        kind="file",
        mode="transform",
        content=b"# AGENTS\n",
    )

    def interrupt(path: Path) -> None:
        if path == target:
            raise OSError("simulated retire interruption")

    with pytest.raises(TransactionError, match="simulated retire interruption"):
        apply_transaction(
            tmp_path,
            [artifact],
            managed_paths={Path("CLAUDE.md"), Path("AGENTS.md")},
            retire=[Path("CLAUDE.md")],
            before_replace=interrupt,
        )

    assert target.read_text(encoding="utf-8") == "# Claude\n"
    assert not (tmp_path / "AGENTS.md").exists()
