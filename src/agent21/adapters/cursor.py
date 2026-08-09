"""Cursor adapter planning."""

from __future__ import annotations

from agent21.adapters.protocol import (
    AdapterContext,
    AgentCapability,
    PlannedArtifact,
    sorted_artifacts,
    stable_json_bytes,
    transform_artifact,
)
from agent21.models import CapabilityStatus

AGENT = "cursor"
DISPLAY_NAME = "Cursor"

capability = AgentCapability(
    agent=AGENT,
    instructions=CapabilityStatus.NATIVE,
    skills=CapabilityStatus.NATIVE,
    mcp=CapabilityStatus.TRANSFORM,
    implemented=True,
    executable="cursor",
)


def plan(context: AdapterContext) -> tuple[PlannedArtifact, ...]:
    """规划 Cursor 项目 MCP JSON；指令和 Skills 保持原生。"""
    if not context.mcp_servers:
        return ()
    content = stable_json_bytes({"mcpServers": dict(context.mcp_servers)})
    return sorted_artifacts([transform_artifact(AGENT, ".cursor/mcp.json", content)])
