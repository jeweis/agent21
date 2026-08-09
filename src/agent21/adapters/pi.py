"""Pi adapter planning."""

from __future__ import annotations

from agent21.adapters.protocol import (
    AdapterContext,
    AgentCapability,
    PlannedArtifact,
)
from agent21.models import CapabilityStatus, DependencyRequirement

AGENT = "pi"
DISPLAY_NAME = "Pi"

capability = AgentCapability(
    agent=AGENT,
    instructions=CapabilityStatus.NATIVE,
    skills=CapabilityStatus.NATIVE,
    mcp=CapabilityStatus.COMPATIBLE,
    implemented=True,
    executable="pi",
    mcp_dependency=DependencyRequirement(
        executable="pi-mcp-adapter",
        install_hint="pi install npm:pi-mcp-adapter",
        required_for=CapabilityStatus.COMPATIBLE,
    ),
)


def plan(context: AdapterContext) -> tuple[PlannedArtifact, ...]:
    """Pi adapter 直接消费根 MCP 权威源，不需要托管输出。"""
    del context
    return ()
