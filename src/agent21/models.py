"""Dataclass domain models and validation helpers for Agent21."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePath, PurePosixPath

from agent21.errors import BoundaryError

SCHEMA_VERSION = 1
LEGACY_AGENTS = ("claude", "codex", "cursor", "opencode", "pi")
REGISTERED_AGENTS = (*LEGACY_AGENTS, "qoder", "workbuddy")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


class SyncMode(StrEnum):
    """Supported synchronization strategies."""

    AUTO = "auto"
    COPY = "copy"
    SYMLINK = "symlink"


class ArtifactKind(StrEnum):
    """Filesystem object kinds managed by Agent21."""

    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"


class ArtifactMode(StrEnum):
    """How a managed artifact is derived from an authority source."""

    NATIVE = "native"
    COPY = "copy"
    SYMLINK = "symlink"
    TRANSFORM = "transform"


class CapabilityStatus(StrEnum):
    """Adapter support level for each capability class."""

    NATIVE = "native"
    COMPATIBLE = "compatible"
    TRANSFORM = "transform"
    UNSUPPORTED = "unsupported"


class ArtifactState(StrEnum):
    """Lifecycle state for planned and manifest-backed artifacts."""

    PLANNED = "planned"
    STAGED = "staged"
    APPLIED = "applied"
    UNCHANGED = "unchanged"
    DRIFTED = "drifted"
    REMOVED = "removed"


class SourceType(StrEnum):
    """Skill source classes recorded in the manifest."""

    LOCAL = "local"
    GIT = "git"


class HealthStatus(StrEnum):
    """Doctor status levels with stable sort-friendly values."""

    PASS = "pass"
    INFO = "info"
    UNSUPPORTED = "unsupported"
    BLOCKED = "blocked"


class JournalState(StrEnum):
    """Transaction journal states used by later filesystem orchestration."""

    STAGING = "staging"
    APPLYING = "applying"
    COMMITTED = "committed"
    ROLLING_BACK = "rolling_back"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentSelection:
    """Project-level enablement for one registered agent."""

    enabled: bool

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise TypeError("agent selection enabled must be a boolean")


@dataclass(frozen=True)
class ProjectConfig:
    """Validated contents of `.agents/config.yaml`."""

    agents: dict[str, AgentSelection]
    sync_mode: SyncMode = SyncMode.AUTO
    instructions_source: str = "AGENTS.md"
    skills_source: str = ".agents/skills"
    mcp_source: str = ".mcp.json"
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("schema_version must be 1")
        for agent in self.agents:
            validate_agent_slug(agent)
        for source in (self.instructions_source, self.skills_source, self.mcp_source):
            validate_project_path(source)


@dataclass(frozen=True)
class ManagedArtifact:
    """A manifest record for one path owned by Agent21."""

    agent: str
    path: str
    kind: ArtifactKind
    mode: ArtifactMode
    source: str
    digest: str

    def __post_init__(self) -> None:
        validate_agent_slug(self.agent)
        validate_project_path(self.path)
        validate_project_path(self.source)
        validate_digest(self.digest)


@dataclass(frozen=True)
class SkillRecord:
    """A manifest record for one installed project skill."""

    name: str
    path: str
    source_type: SourceType
    source: str
    version: str | None
    digest: str

    def __post_init__(self) -> None:
        if not _SKILL_NAME_RE.fullmatch(self.name):
            raise ValueError(f"invalid skill name: {self.name}")
        validate_project_path(self.path)
        if not self.path.startswith(".agents/skills/"):
            raise ValueError("skill path must be under .agents/skills")
        if self.source_type is SourceType.LOCAL:
            validate_project_path(self.source)
        validate_digest(self.digest)


@dataclass(frozen=True)
class Manifest:
    """Validated contents of `.agents/manifest.yaml`."""

    version: str
    managed_artifacts: list[ManagedArtifact] = field(default_factory=list)
    skills: list[SkillRecord] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("schema_version must be 1")
        if not self.version:
            raise ValueError("version is required")
        artifact_paths = [artifact.path for artifact in self.managed_artifacts]
        skill_names = [skill.name for skill in self.skills]
        if len(set(artifact_paths)) != len(artifact_paths):
            raise ValueError("duplicate managed artifact path")
        if len(set(skill_names)) != len(skill_names):
            raise ValueError("duplicate skill name")

    def sorted(self) -> Manifest:
        """Return a copy sorted for deterministic serialization and lookup."""

        return Manifest(
            schema_version=self.schema_version,
            version=self.version,
            managed_artifacts=sorted(
                self.managed_artifacts,
                key=lambda artifact: (artifact.path, artifact.agent),
            ),
            skills=sorted(self.skills, key=lambda skill: skill.name),
        )

    def owner_of(self, path: ProjectPathValue) -> ManagedArtifact | None:
        """Return the managed artifact owning a normalized project path."""

        normalized = normalize_project_path(path)
        return next(
            (artifact for artifact in self.managed_artifacts if artifact.path == normalized),
            None,
        )


@dataclass(frozen=True)
class DependencyRequirement:
    """Optional executable required for one adapter capability."""

    executable: str
    install_hint: str
    required_for: CapabilityStatus

    def __post_init__(self) -> None:
        if not self.executable or not self.install_hint:
            raise ValueError("dependency executable and install hint are required")


@dataclass(frozen=True)
class AgentCapability:
    """Declared adapter support for one registered agent."""

    agent: str
    instructions: CapabilityStatus
    skills: CapabilityStatus
    mcp: CapabilityStatus
    implemented: bool
    executable: str | None = None
    mcp_dependency: DependencyRequirement | None = None
    instructions_blocker: str | None = None

    def __post_init__(self) -> None:
        validate_agent_slug(self.agent)
        if self.instructions_blocker is not None:
            validate_project_path(self.instructions_blocker)


@dataclass(frozen=True)
class PlannedArtifact:
    """Side-effect-free write plan emitted by adapters."""

    agent: str
    target: str
    kind: ArtifactKind
    mode: ArtifactMode
    source: str | None
    content: bytes | None
    digest: str

    def __post_init__(self) -> None:
        validate_agent_slug(self.agent)
        validate_project_path(self.target)
        if self.source is not None:
            validate_project_path(self.source)
        if (self.source is None) == (self.content is None):
            raise ValueError("planned artifact requires exactly one source or content")
        validate_digest(self.digest)


@dataclass(frozen=True)
class SyncPlan:
    """Sorted planned artifacts with pre-apply validation messages."""

    artifacts: list[PlannedArtifact]
    conflicts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.artifacts.sort(key=lambda artifact: (artifact.target, artifact.agent))
        self.conflicts.sort()
        self.errors.sort()


@dataclass(frozen=True)
class SyncResult:
    """User-visible synchronization summary buckets."""

    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    retired: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for values in (
            self.created,
            self.updated,
            self.unchanged,
            self.retired,
            self.skipped,
            self.conflicts,
            self.errors,
        ):
            values.sort()


@dataclass(frozen=True)
class HealthCheckResult:
    """One doctor result row."""

    check_id: str
    status: HealthStatus
    subject: str
    message: str
    action: str | None = None


def validate_agent_slug(agent: str) -> str:
    """Validate and return a registered MVP agent slug."""

    if agent not in REGISTERED_AGENTS:
        raise ValueError(f"unknown agent: {agent}")
    return agent


ProjectPathValue = str | PurePath


def normalize_project_path(path: ProjectPathValue) -> str:
    """Convert a relative path value to the manifest's POSIX representation."""

    if isinstance(path, str):
        return path
    return path.as_posix()


def validate_project_path(path: ProjectPathValue) -> str:
    """Validate a project-relative POSIX path string."""

    value = normalize_project_path(path)
    if not value or value == ".":
        raise BoundaryError("project path must not be empty")
    if value.startswith("/") or _WINDOWS_DRIVE_RE.match(value):
        raise BoundaryError(f"path is outside project: {value}")
    if isinstance(path, str) and "\\" in path:
        raise BoundaryError(f"path must use POSIX separators: {value}")
    parts = PurePosixPath(value).parts
    if any(part == ".." for part in parts):
        raise BoundaryError(f"path is outside project: {value}")
    return value


def validate_digest(digest: str) -> str:
    """Validate and return a sha256 manifest digest."""

    if not _DIGEST_RE.fullmatch(digest):
        raise ValueError("digest must match sha256:<64 lowercase hex>")
    return digest


def digest_bytes(payload: bytes) -> str:
    """Return the canonical sha256 digest for bytes."""

    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def digest_text(text: str) -> str:
    """Return the canonical sha256 digest for UTF-8 text."""

    return digest_bytes(text.encode("utf-8"))


def digest_symlink_target(target: str | Path) -> str:
    """Digest a symlink target string, not the target file content."""

    return digest_text(Path(target).as_posix())


def digest_path(path: Path) -> str:
    """Digest a filesystem path using Agent21 manifest semantics."""

    if path.is_symlink():
        return digest_symlink_target(path.readlink())
    if path.is_file():
        return digest_bytes(path.read_bytes())
    if path.is_dir():
        return digest_directory(path)
    raise FileNotFoundError(path)


def digest_directory(path: Path) -> str:
    """Digest directory entries by relative path and bytes in stable order."""

    hasher = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file() or item.is_symlink()):
        relative = child.relative_to(path).as_posix().encode("utf-8")
        hasher.update(relative)
        hasher.update(b"\0")
        if child.is_symlink():
            hasher.update(b"L")
            hasher.update(child.readlink().as_posix().encode("utf-8"))
        else:
            hasher.update(b"F")
            hasher.update(child.read_bytes())
        hasher.update(b"\0")
    return f"sha256:{hasher.hexdigest()}"
