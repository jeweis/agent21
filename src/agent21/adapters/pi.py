"""Pi adapter planning."""

from __future__ import annotations

from agent21.adapters.protocol import (
    AdapterContext,
    AgentCapability,
    PlannedArtifact,
)
from agent21.models import CapabilityStatus

AGENT = "pi"
DISPLAY_NAME = "Pi"

capability = AgentCapability(
    agent=AGENT,
    instructions=CapabilityStatus.NATIVE,
    skills=CapabilityStatus.NATIVE,
    mcp=CapabilityStatus.UNSUPPORTED,
    implemented=True,
    executable="pi",
)


def plan(context: AdapterContext) -> tuple[PlannedArtifact, ...]:
    """Pi 在 MVP 中没有托管输出，MCP 明确 unsupported。"""
    del context
    return ()
