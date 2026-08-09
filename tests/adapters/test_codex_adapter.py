"""Codex CLI adapter 行为测试。"""

from __future__ import annotations

import tomllib

import pytest

from agent21.adapters.codex import capability, plan
from agent21.adapters.protocol import AdapterContext
from agent21.models import ArtifactKind, ArtifactMode, CapabilityStatus

pytestmark = pytest.mark.adapter


def test_codex_capability_matches_official_project_mcp_target() -> None:
    """Codex 原生读取指令和 Skills，仅 MCP 转换到 `.codex/config.toml`。"""
    assert capability.agent == "codex"
    assert capability.instructions is CapabilityStatus.NATIVE
    assert capability.skills is CapabilityStatus.NATIVE
    assert capability.mcp is CapabilityStatus.TRANSFORM


def test_codex_plans_config_toml_with_mcp_servers() -> None:
    """Codex MCP 使用官方 `mcp_servers.<name>` TOML 结构。"""
    artifacts = plan(
        AdapterContext(
            mcp_servers={
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                    "env": {"ROOT": "."},
                }
            }
        )
    )

    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.target == ".codex/config.toml"
    assert artifact.kind is ArtifactKind.FILE
    assert artifact.mode is ArtifactMode.TRANSFORM
    assert artifact.source is None
    assert artifact.content is not None

    parsed = tomllib.loads(artifact.content.decode("utf-8"))
    assert parsed["mcp_servers"]["filesystem"] == {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "env": {"ROOT": "."},
    }


def test_codex_skips_mcp_artifact_when_source_has_no_servers() -> None:
    """没有 MCP server 时不创建空配置文件。"""
    assert plan(AdapterContext(mcp_servers={})) == ()
