"""Unit tests for manifest serialization, ownership, and drift helpers."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath

import pytest

from agent21.errors import ManifestError
from agent21.manifest import MANIFEST_PATH, artifact_is_drifted, load_manifest, save_manifest
from agent21.models import (
    ArtifactKind,
    ArtifactMode,
    ManagedArtifact,
    Manifest,
    SkillRecord,
    SourceType,
    digest_bytes,
    digest_path,
)


def test_save_manifest_sorts_artifacts_and_skills(tmp_path: Path) -> None:
    """Manifest output is deterministic for stable reviews and idempotency."""

    manifest = Manifest(
        version="0.1.0",
        managed_artifacts=[
            ManagedArtifact(
                "pi",
                "PI.md",
                ArtifactKind.FILE,
                ArtifactMode.NATIVE,
                "AGENTS.md",
                digest_bytes(b"b"),
            ),
            ManagedArtifact(
                "codex",
                ".codex/config.toml",
                ArtifactKind.FILE,
                ArtifactMode.TRANSFORM,
                ".mcp.json",
                digest_bytes(b"a"),
            ),
        ],
        skills=[
            SkillRecord(
                "zeta",
                ".agents/skills/zeta",
                SourceType.LOCAL,
                ".agents/skills/zeta",
                None,
                digest_bytes(b"z"),
            ),
            SkillRecord(
                "alpha",
                ".agents/skills/alpha",
                SourceType.LOCAL,
                ".agents/skills/alpha",
                None,
                digest_bytes(b"a"),
            ),
        ],
    )

    save_manifest(tmp_path, manifest)
    loaded = load_manifest(tmp_path)

    assert [artifact.path for artifact in loaded.managed_artifacts] == [
        ".codex/config.toml",
        "PI.md",
    ]
    assert [skill.name for skill in loaded.skills] == ["alpha", "zeta"]


def test_load_manifest_rejects_duplicate_artifact_paths(tmp_path: Path) -> None:
    """Only one owner record can manage a project path."""

    path = tmp_path / MANIFEST_PATH
    path.parent.mkdir(parents=True)
    digest = digest_bytes(b"x")
    path.write_text(
        "\n".join(
            [
                "agent21:",
                "  schema_version: 1",
                "  version: 0.1.0",
                "  managed_artifacts:",
                "    - {agent: codex, path: target.txt, kind: file, "
                f"mode: copy, source: AGENTS.md, digest: {digest}}}",
                "    - {agent: claude, path: target.txt, kind: file, "
                f"mode: copy, source: AGENTS.md, digest: {digest}}}",
                "  skills: []",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ManifestError, match="duplicate"):
        load_manifest(tmp_path)


def test_manifest_ownership_lookup_uses_normalized_paths() -> None:
    """Ownership checks use the same POSIX path normalization as saved records."""

    artifact = ManagedArtifact(
        "codex",
        ".codex/config.toml",
        ArtifactKind.FILE,
        ArtifactMode.TRANSFORM,
        ".mcp.json",
        digest_bytes(b"{}"),
    )
    manifest = Manifest(version="0.1.0", managed_artifacts=[artifact], skills=[])

    assert manifest.owner_of(Path(".codex") / "config.toml") == artifact
    assert manifest.owner_of(PureWindowsPath(".codex/config.toml")) == artifact
    assert manifest.owner_of("missing.txt") is None


def test_save_manifest_writes_wrapped_agent21_format(tmp_path: Path) -> None:
    """Manifest wraps all fields under the agent21 root key."""

    save_manifest(tmp_path, Manifest(version="0.1.5", managed_artifacts=[], skills=[]))

    text = (tmp_path / MANIFEST_PATH).read_text(encoding="utf-8")
    assert text.startswith("agent21:")
    assert "  schema_version: 1" in text
    assert "  version: 0.1.5" in text
    assert "managed_artifacts: []" in text


def test_digest_path_detects_file_drift(tmp_path: Path) -> None:
    """Artifact drift compares the current target bytes with stored digest."""

    target = tmp_path / "target.txt"
    target.write_text("before\n", encoding="utf-8")
    artifact = ManagedArtifact(
        "claude",
        "target.txt",
        ArtifactKind.FILE,
        ArtifactMode.COPY,
        "AGENTS.md",
        digest_path(target),
    )

    assert not artifact_is_drifted(tmp_path, artifact)
    target.write_text("after\n", encoding="utf-8")
    assert artifact_is_drifted(tmp_path, artifact)
