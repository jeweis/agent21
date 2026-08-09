"""OpenCode adapter planning."""

from __future__ import annotations

from agent21.adapters.protocol import (
    AdapterContext,
    AgentCapability,
    PlannedArtifact,
    sorted_artifacts,
    transform_artifact,
)
from agent21.mcp import opencode_json
from agent21.models import CapabilityStatus

AGENT = "opencode"
DISPLAY_NAME = "OpenCode"

capability = AgentCapability(
    agent=AGENT,
    instructions=CapabilityStatus.NATIVE,
    skills=CapabilityStatus.NATIVE,
    mcp=CapabilityStatus.TRANSFORM,
    implemented=True,
    executable="opencode",
)


def plan(context: AdapterContext) -> tuple[PlannedArtifact, ...]:
    """规划 OpenCode MCP 转换；指令和 Skills 由工具原生读取。"""

    if not context.mcp_servers:
        return ()
    content = opencode_json(context.mcp_servers).encode("utf-8")
    return sorted_artifacts([transform_artifact(AGENT, "opencode.json", content)])
