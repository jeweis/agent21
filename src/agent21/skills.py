"""Project-local Skill installation, listing, and safe removal."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path, PurePath
from urllib.parse import urlsplit, urlunsplit

from agent21.lock import ProjectLock
from agent21.manifest import load_manifest, save_manifest
from agent21.models import SkillRecord, SourceType, digest_path
from agent21.project import safe_join

SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class SkillConflictError(ValueError):
    """Raised when Skill ownership or drift makes a write unsafe."""


def install_skill(root: Path, source: str, *, name: str | None = None) -> SkillRecord:
    """Validate and atomically install a local or explicit Git Skill source."""

    root = root.resolve()
    is_git = _is_git_source(source)
    # Normalize local relative paths so Windows backslashes never reach validators.
    local_source = source if is_git else PurePath(source).as_posix()
    with tempfile.TemporaryDirectory(prefix="agent21-skill-") as temp_dir:
        if is_git:
            staged_source = Path(temp_dir) / "repository"
            _clone(source, staged_source)
            source_type = SourceType.GIT
            recorded_source = _redact_url(source)
        else:
            staged_source = safe_join(root, local_source)
            source_type = SourceType.LOCAL
            recorded_source = local_source
        skill_name = name or staged_source.name.removesuffix(".git")
        _validate_package(staged_source, skill_name)
        target_relative = f".agents/skills/{skill_name}"
        target = safe_join(root, target_relative)
        manifest = load_manifest(root)
        if target.exists() or any(record.name == skill_name for record in manifest.skills):
            raise SkillConflictError(f"Skill target is already managed or occupied: {skill_name}")
        with ProjectLock(root, command="skill install"):
            _copy_without_git(staged_source, target)
            try:
                record = SkillRecord(
                    name=skill_name,
                    path=target_relative,
                    source_type=source_type,
                    source=recorded_source,
                    version=_read_version(target / "SKILL.md"),
                    digest=digest_path(target),
                )
                save_manifest(root, replace(manifest, skills=[*manifest.skills, record]))
            except Exception:
                shutil.rmtree(target, ignore_errors=True)
                raise
    return record


def list_skills(root: Path) -> tuple[SkillRecord, ...]:
    """Return manifest-owned Skills in deterministic name order."""

    return tuple(sorted(load_manifest(root).skills, key=lambda record: record.name))


def remove_skill(root: Path, name: str) -> SkillRecord:
    """Remove one unchanged manifest-owned Skill and its ownership record."""

    _validate_name(name)
    root = root.resolve()
    manifest = load_manifest(root)
    record = next((item for item in manifest.skills if item.name == name), None)
    if record is None:
        raise SkillConflictError(f"Skill is not managed: {name}")
    target = safe_join(root, record.path)
    if not target.is_dir() or digest_path(target) != record.digest:
        raise SkillConflictError(f"managed Skill has drifted: {name}")
    with ProjectLock(root, command="skill remove"):
        backup = target.with_name(f".{target.name}.removing")
        target.replace(backup)
        try:
            remaining = [item for item in manifest.skills if item.name != name]
            save_manifest(root, replace(manifest, skills=remaining))
        except Exception:
            backup.replace(target)
            raise
        shutil.rmtree(backup)
    return record


def _validate_package(source: Path, name: str) -> None:
    """Require a safe slug and root SKILL.md before any project write."""

    _validate_name(name)
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        raise ValueError("Skill source must be a directory containing SKILL.md")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("Skill source must not contain symbolic links")


def _validate_name(name: str) -> None:
    """Validate a Skill slug without accepting path separators or traversal."""

    if not SKILL_NAME.fullmatch(name):
        raise ValueError(f"invalid Skill name: {name}")


def _is_git_source(source: str) -> bool:
    """Recognize explicit Git transports without treating local paths as remote."""

    return source.startswith(
        ("git@", "ssh://", "https://", "http://", "file://")
    ) or source.endswith(".git")


def _clone(source: str, destination: Path) -> None:
    """Clone a Git Skill to temporary storage without executing repository code."""

    completed = subprocess.run(
        ["git", "clone", "--depth", "1", "--", source, str(destination)],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("unable to clone Git Skill source")


def _copy_without_git(source: Path, target: Path) -> None:
    """Copy a validated Skill while excluding nested Git metadata."""

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, symlinks=False, ignore=shutil.ignore_patterns(".git"))


def _read_version(skill_file: Path) -> str | None:
    """Read an optional simple YAML-frontmatter version without executing content."""

    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator and key.strip() == "version":
            return value.strip().strip("'\"") or None
    return None


def _redact_url(source: str) -> str:
    """Remove username/password fields before persisting a Git source URL."""

    parts = urlsplit(source)
    if not parts.netloc or "@" not in parts.netloc:
        return source
    hostname = parts.hostname or ""
    if parts.port:
        hostname = f"{hostname}:{parts.port}"
    return urlunsplit((parts.scheme, hostname, parts.path, parts.query, parts.fragment))
