"""Claude Code adapter planning."""

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

AGENT = "claude"
DISPLAY_NAME = "Claude Code"

capability = AgentCapability(
    agent=AGENT,
    instructions=CapabilityStatus.COMPATIBLE,
    skills=CapabilityStatus.COMPATIBLE,
    mcp=CapabilityStatus.NATIVE,
    implemented=True,
    executable="claude",
)


def plan(context: AdapterContext) -> tuple[PlannedArtifact, ...]:
    """规划 Claude 兼容指令和 Skills 输出，根 `.mcp.json` 保持 native。"""
    artifacts = [
        copy_artifact(AGENT, context.instructions_source, "CLAUDE.md"),
        directory_artifact(AGENT, context.skills_source, ".claude/skills", context.sync_mode),
    ]
    return sorted_artifacts(artifacts)
