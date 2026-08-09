"""Cursor adapter 行为测试。"""

from __future__ import annotations

import json

import pytest

from agent21.adapters.cursor import capability, plan
from agent21.adapters.protocol import AdapterContext
from agent21.models import ArtifactKind, ArtifactMode, CapabilityStatus

pytestmark = pytest.mark.adapter


def test_cursor_capability_matches_project_mcp_target() -> None:
    """Cursor 原生读取指令和 Skills，MCP 转换为项目 JSON。"""
    assert capability.agent == "cursor"
    assert capability.instructions is CapabilityStatus.NATIVE
    assert capability.skills is CapabilityStatus.NATIVE
    assert capability.mcp is CapabilityStatus.TRANSFORM


def test_cursor_plans_mcp_json() -> None:
    """Cursor MCP 输出到 `.cursor/mcp.json` 的 `mcpServers`。"""
    artifacts = plan(
        AdapterContext(
            mcp_servers={
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                }
            }
        )
    )

    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.target == ".cursor/mcp.json"
    assert artifact.kind is ArtifactKind.FILE
    assert artifact.mode is ArtifactMode.TRANSFORM
    assert artifact.content is not None
    assert json.loads(artifact.content) == {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
            }
        }
    }


def test_cursor_skips_mcp_artifact_when_source_has_no_servers() -> None:
    """没有 MCP server 时不创建空 Cursor 配置。"""
    assert plan(AdapterContext(mcp_servers={})) == ()
