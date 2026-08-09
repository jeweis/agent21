"""Claude Code adapter 行为测试。"""

from __future__ import annotations

import pytest

from agent21.adapters import ArtifactKind, ArtifactMode
from agent21.adapters.claude import capability, plan
from agent21.adapters.protocol import AdapterContext
from agent21.models import CapabilityStatus

pytestmark = pytest.mark.adapter


def test_claude_capability_matches_mvp_matrix() -> None:
    """Claude 使用兼容映射输出，MCP 复用根 `.mcp.json`。"""
    assert capability.agent == "claude"
    assert capability.instructions is CapabilityStatus.COMPATIBLE
    assert capability.skills is CapabilityStatus.COMPATIBLE
    assert capability.mcp is CapabilityStatus.NATIVE
    assert capability.executable == "claude"


def test_claude_plans_instruction_and_skills_outputs() -> None:
    """Claude 只规划 CLAUDE.md 和 `.claude/skills`。"""
    artifacts = plan(AdapterContext(sync_mode=ArtifactMode.SYMLINK))

    assert [artifact.target for artifact in artifacts] == [".claude/skills", "CLAUDE.md"]
    assert artifacts[0].source == ".agents/skills"
    assert artifacts[0].kind is ArtifactKind.SYMLINK
    assert artifacts[0].mode is ArtifactMode.SYMLINK
    assert artifacts[1].source == "AGENTS.md"
    assert artifacts[1].kind is ArtifactKind.FILE
    assert artifacts[1].mode is ArtifactMode.COPY


def test_claude_does_not_duplicate_native_mcp() -> None:
    """根 `.mcp.json` 是 Claude 原生目标，不生成托管副本。"""
    artifacts = plan(AdapterContext(mcp_servers={"tool": {"command": "tool"}}))

    assert ".mcp.json" not in {artifact.target for artifact in artifacts}
