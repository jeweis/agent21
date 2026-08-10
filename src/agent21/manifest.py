"""Strict manifest load/save, ownership, and drift helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from agent21 import __version__
from agent21.errors import ManifestError
from agent21.models import (
    ArtifactKind,
    ArtifactMode,
    ManagedArtifact,
    Manifest,
    SkillRecord,
    SourceType,
    digest_path,
)
from agent21.project import safe_join

MANIFEST_PATH = Path(".agents/manifest.yaml")


def empty_manifest() -> Manifest:
    """Return an empty manifest for the current Agent21 package version."""

    return Manifest(agent21=__version__, managed_artifacts=[], skills=[])


def load_manifest(project_root: str | Path) -> Manifest:
    """Load and strictly validate `.agents/manifest.yaml`."""

    path = Path(project_root) / MANIFEST_PATH
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestError(f"could not read manifest: {MANIFEST_PATH.as_posix()}") from exc
    return _parse_manifest(raw).sorted()


def save_manifest(project_root: str | Path, manifest: Manifest) -> None:
    """Write deterministic manifest YAML after stable sorting."""

    root = Path(project_root)
    path = safe_join(root, MANIFEST_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_yaml(_manifest_to_data(manifest.sorted())), encoding="utf-8")


def artifact_is_drifted(project_root: str | Path, artifact: ManagedArtifact) -> bool:
    """Return True when a managed target's digest differs or it is missing."""

    target = Path(project_root) / artifact.path
    try:
        current_digest = digest_path(target)
    except FileNotFoundError:
        return True
    return current_digest != artifact.digest


def _parse_manifest(raw: Any) -> Manifest:
    if not isinstance(raw, dict):
        raise ManifestError("manifest must be a mapping")
    allowed = {"schema_version", "agent21", "agent21_version", "managed_artifacts", "skills"}
    _require_fields(raw, {"schema_version", "managed_artifacts", "skills"}, allowed=allowed)
    if raw["schema_version"] != 1:
        raise ManifestError("schema_version must be 1")
    try:
        manifest = Manifest(
            schema_version=1,
            agent21=_agent21_field(raw),
            managed_artifacts=[
                _parse_artifact(item)
                for item in _sequence(raw["managed_artifacts"], "managed_artifacts")
            ],
            skills=[_parse_skill(item) for item in _sequence(raw["skills"], "skills")],
        )
    except ValueError as exc:
        raise ManifestError(str(exc)) from exc
    return manifest


def _agent21_field(raw: dict[str, Any]) -> str:
    """返回 manifest 的 agent21 标识；兼容旧字段名 agent21_version。"""

    if "agent21" in raw:
        return _string(raw["agent21"], "agent21")
    if "agent21_version" in raw:
        return _string(raw["agent21_version"], "agent21_version")
    raise ManifestError("missing field in manifest: agent21")


def _parse_artifact(raw: Any) -> ManagedArtifact:
    item = _mapping(raw, "managed_artifacts[]")
    _require_fields(item, {"agent", "path", "kind", "mode", "source", "digest"})
    return ManagedArtifact(
        agent=_string(item["agent"], "artifact.agent"),
        path=_string(item["path"], "artifact.path"),
        kind=ArtifactKind(item["kind"]),
        mode=ArtifactMode(item["mode"]),
        source=_string(item["source"], "artifact.source"),
        digest=_string(item["digest"], "artifact.digest"),
    )


def _parse_skill(raw: Any) -> SkillRecord:
    item = _mapping(raw, "skills[]")
    required = {"name", "path", "source_type", "source", "digest"}
    allowed = required | {"version"}
    _require_fields(item, required, allowed=allowed)
    return SkillRecord(
        name=_string(item["name"], "skill.name"),
        path=_string(item["path"], "skill.path"),
        source_type=SourceType(item["source_type"]),
        source=_string(item["source"], "skill.source"),
        version=_optional_string(item.get("version"), "skill.version"),
        digest=_string(item["digest"], "skill.digest"),
    )


def _manifest_to_data(manifest: Manifest) -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version,
        "agent21": manifest.agent21,
        "managed_artifacts": [
            {
                "agent": artifact.agent,
                "path": artifact.path,
                "kind": artifact.kind.value,
                "mode": artifact.mode.value,
                "source": artifact.source,
                "digest": artifact.digest,
            }
            for artifact in manifest.managed_artifacts
        ],
        "skills": [
            {
                "name": skill.name,
                "path": skill.path,
                "source_type": skill.source_type.value,
                "source": skill.source,
                "version": skill.version,
                "digest": skill.digest,
            }
            for skill in manifest.skills
        ],
    }


def _dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def _require_fields(
    raw: dict[Any, Any],
    required: set[str],
    *,
    allowed: set[str] | None = None,
) -> None:
    allowed_fields = allowed or required
    keys = set(raw)
    unknown = sorted(keys - allowed_fields)
    missing = sorted(required - keys)
    if unknown:
        raise ManifestError(f"unknown field in manifest: {unknown[0]}")
    if missing:
        raise ManifestError(f"missing field in manifest: {missing[0]}")


def _mapping(raw: Any, subject: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ManifestError(f"{subject} must be a mapping")
    return cast(dict[str, Any], raw)


def _sequence(raw: Any, subject: str) -> list[Any]:
    if not isinstance(raw, list):
        raise ManifestError(f"{subject} must be a list")
    return raw


def _string(raw: Any, subject: str) -> str:
    if not isinstance(raw, str):
        raise ManifestError(f"{subject} must be a string")
    return raw


def _optional_string(raw: Any, subject: str) -> str | None:
    if raw is None:
        return None
    return _string(raw, subject)
