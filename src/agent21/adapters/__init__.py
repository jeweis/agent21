"""Agent21 MVP adapter registry."""

from __future__ import annotations

from types import ModuleType

from agent21.adapters import claude, codex, cursor, opencode, pi, qoder, workbuddy
from agent21.adapters.protocol import (
    AdapterContext,
    AgentAdapter,
    AgentCapability,
    ArtifactKind,
    ArtifactMode,
    PlannedArtifact,
)
from agent21.models import CapabilityStatus

REGISTRY: dict[str, ModuleType] = {
    claude.capability.agent: claude,
    codex.capability.agent: codex,
    cursor.capability.agent: cursor,
    opencode.capability.agent: opencode,
    pi.capability.agent: pi,
    qoder.capability.agent: qoder,
    workbuddy.capability.agent: workbuddy,
}

__all__ = [
    "REGISTRY",
    "AdapterContext",
    "AgentAdapter",
    "AgentCapability",
    "ArtifactKind",
    "ArtifactMode",
    "CapabilityStatus",
    "PlannedArtifact",
]
