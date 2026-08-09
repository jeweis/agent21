"""Qoder project configuration adapter."""

from __future__ import annotations

from agent21.adapters.protocol import (
    AdapterContext,
    AgentCapability,
    PlannedArtifact,
    directory_artifact,
    sorted_artifacts,
)
from agent21.models import CapabilityStatus

AGENT = "qoder"
DISPLAY_NAME = "Qoder"

capability = AgentCapability(
    agent=AGENT,
    instructions=CapabilityStatus.NATIVE,
    skills=CapabilityStatus.COMPATIBLE,
    mcp=CapabilityStatus.NATIVE,
    implemented=True,
    executable="qodercli",
)


def plan(context: AdapterContext) -> tuple[PlannedArtifact, ...]:
    """Map only Skills because Qoder reads root instructions and MCP natively."""

    return sorted_artifacts(
        [directory_artifact(AGENT, context.skills_source, ".qoder/skills", context.sync_mode)]
    )
