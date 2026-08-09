"""WorkBuddy project configuration adapter."""

from __future__ import annotations

from agent21.adapters.protocol import (
    AdapterContext,
    AgentCapability,
    PlannedArtifact,
    copy_artifact,
    directory_artifact,
    sorted_artifacts,
)
from agent21.models import CapabilityStatus

AGENT = "workbuddy"
DISPLAY_NAME = "WorkBuddy"

capability = AgentCapability(
    agent=AGENT,
    instructions=CapabilityStatus.COMPATIBLE,
    skills=CapabilityStatus.COMPATIBLE,
    mcp=CapabilityStatus.NATIVE,
    implemented=True,
    executable=None,
)


def plan(context: AdapterContext) -> tuple[PlannedArtifact, ...]:
    """Map project instructions and Skills into WorkBuddy's `.codebuddy` paths."""

    artifacts = [
        copy_artifact(AGENT, context.instructions_source, ".codebuddy/rules/agent21.md"),
        directory_artifact(AGENT, context.skills_source, ".codebuddy/skills", context.sync_mode),
    ]
    return sorted_artifacts(artifacts)
