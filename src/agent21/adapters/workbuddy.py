"""WorkBuddy project configuration adapter."""

from __future__ import annotations

from agent21.adapters.protocol import (
    AdapterContext,
    AgentCapability,
    PlannedArtifact,
    directory_artifact,
    sorted_artifacts,
)
from agent21.models import CapabilityStatus

AGENT = "workbuddy"
DISPLAY_NAME = "WorkBuddy"

capability = AgentCapability(
    agent=AGENT,
    instructions=CapabilityStatus.NATIVE,
    skills=CapabilityStatus.COMPATIBLE,
    mcp=CapabilityStatus.NATIVE,
    implemented=True,
    executable=None,
    instructions_blocker="CODEBUDDY.md",
)


def plan(context: AdapterContext) -> tuple[PlannedArtifact, ...]:
    """Map only Skills because WorkBuddy reads root instructions and MCP natively."""

    artifacts = [
        directory_artifact(AGENT, context.skills_source, ".codebuddy/skills", context.sync_mode),
    ]
    return sorted_artifacts(artifacts)
