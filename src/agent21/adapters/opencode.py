"""OpenCode adapter planning."""

from __future__ import annotations

from agent21.adapters.protocol import (
    AdapterContext,
    AgentCapability,
    PlannedArtifact,
)
from agent21.models import CapabilityStatus

AGENT = "opencode"
DISPLAY_NAME = "OpenCode"

capability = AgentCapability(
    agent=AGENT,
    instructions=CapabilityStatus.NATIVE,
    skills=CapabilityStatus.NATIVE,
    mcp=CapabilityStatus.UNSUPPORTED,
    implemented=True,
    executable="opencode",
)


def plan(context: AdapterContext) -> tuple[PlannedArtifact, ...]:
    """OpenCode 在 MVP 中不需要托管输出，MCP 明确 unsupported。"""
    del context
    return ()
