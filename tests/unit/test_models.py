"""Unit tests for Agent21 foundational domain models."""

from __future__ import annotations

from pathlib import PureWindowsPath

import pytest

from agent21.errors import Agent21Error, BoundaryError, classify_exit
from agent21.models import (
    AgentSelection,
    ArtifactKind,
    ArtifactMode,
    ManagedArtifact,
    PlannedArtifact,
    SourceType,
    digest_bytes,
    validate_agent_slug,
    validate_project_path,
)


def test_agent_selection_rejects_string_booleans() -> None:
    """Agent enablement is a real boolean, never a YAML truthy string."""

    with pytest.raises(TypeError, match="enabled"):
        AgentSelection(enabled="true")  # type: ignore[arg-type]


def test_project_path_validation_rejects_escape_and_absolute_paths() -> None:
    """Project-relative paths must not escape the repository boundary."""

    assert validate_project_path(".agents/skills/demo") == ".agents/skills/demo"

    for value in ("/tmp/outside", "../outside", "nested/../../outside", "C:/outside"):
        with pytest.raises(BoundaryError):
            validate_project_path(value)


def test_project_path_validation_normalizes_windows_path_objects() -> None:
    """Internal Windows Path-like values are normalized before validation."""

    path = PureWindowsPath(".agents/config.yaml")

    assert validate_project_path(path) == ".agents/config.yaml"


def test_project_path_validation_rejects_backslash_strings() -> None:
    """User-provided strings must use explicit POSIX separators."""

    with pytest.raises(BoundaryError, match="POSIX separators"):
        validate_project_path(r".agents\config.yaml")


def test_agent_slug_validation_allows_only_registered_agents() -> None:
    """Stored artifact ownership is limited to the MVP agent registry."""

    assert validate_agent_slug("codex") == "codex"

    with pytest.raises(ValueError, match="unknown agent"):
        validate_agent_slug("unknown")


def test_digest_bytes_uses_sha256_prefix() -> None:
    """All model digests share the manifest-compatible sha256 prefix."""

    digest = digest_bytes(b"agent21\n")

    assert digest.startswith("sha256:")
    assert len(digest) == len("sha256:") + 64


def test_planned_artifact_requires_exactly_one_payload_source() -> None:
    """Adapter write plans use either source or content, not both or neither."""

    PlannedArtifact(
        agent="claude",
        target=".claude/CLAUDE.md",
        kind=ArtifactKind.FILE,
        mode=ArtifactMode.COPY,
        source="AGENTS.md",
        content=None,
        digest=digest_bytes(b"agent21\n"),
    )

    with pytest.raises(ValueError, match="exactly one"):
        PlannedArtifact(
            agent="claude",
            target=".claude/CLAUDE.md",
            kind=ArtifactKind.FILE,
            mode=ArtifactMode.COPY,
            source="AGENTS.md",
            content=b"agent21\n",
            digest=digest_bytes(b"agent21\n"),
        )


def test_managed_artifact_validates_kind_mode_and_source() -> None:
    """Manifest artifacts keep path, agent, kind, mode, source, and digest valid."""

    artifact = ManagedArtifact(
        agent="cursor",
        path=".cursor/mcp.json",
        kind=ArtifactKind.FILE,
        mode=ArtifactMode.TRANSFORM,
        source=".mcp.json",
        digest=digest_bytes(b"{}"),
    )

    assert artifact.source == ".mcp.json"


def test_skill_source_type_accepts_declared_values() -> None:
    """Skill source type is constrained to local and git records."""

    assert SourceType.LOCAL.value == "local"
    assert SourceType.GIT.value == "git"


def test_errors_have_stable_exit_classification() -> None:
    """Domain errors expose stable CLI exit classes for later wiring."""

    assert classify_exit(Agent21Error("bad input", exit_code=2)) == 2
    assert classify_exit(RuntimeError("boom")) == 1
