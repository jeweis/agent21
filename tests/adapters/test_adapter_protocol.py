"""adapter 协议和注册表的无副作用契约测试。"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agent21.adapters import REGISTRY, AdapterContext, ArtifactKind, ArtifactMode, PlannedArtifact
from agent21.adapters.protocol import content_digest, transform_artifact
from agent21.errors import BoundaryError

pytestmark = pytest.mark.adapter


def test_registry_contains_mvp_adapters() -> None:
    """MVP 注册表只暴露五个已声明 Agent。"""
    assert set(REGISTRY) == {"claude", "codex", "cursor", "opencode", "pi"}
    assert [name for name in sorted(REGISTRY)] == sorted(REGISTRY)


def test_planned_artifact_rejects_unsafe_paths() -> None:
    """计划目标和来源必须是项目相对 POSIX 路径。"""
    digest = content_digest(b"content")

    with pytest.raises(BoundaryError, match="outside project"):
        PlannedArtifact(
            agent="codex",
            target="../escape",
            kind=ArtifactKind.FILE,
            mode=ArtifactMode.TRANSFORM,
            source=None,
            content=b"content",
            digest=digest,
        )

    with pytest.raises(BoundaryError, match="outside project"):
        PlannedArtifact(
            agent="claude",
            target="CLAUDE.md",
            kind=ArtifactKind.FILE,
            mode=ArtifactMode.COPY,
            source="/tmp/AGENTS.md",
            content=None,
            digest=digest,
        )


def test_planned_artifact_requires_source_or_content_exclusively() -> None:
    """copy/symlink 使用 source，transform 使用 content，二者不能同时出现。"""
    digest = content_digest(b"content")

    with pytest.raises(ValueError, match="exactly one"):
        PlannedArtifact(
            agent="cursor",
            target=".cursor/mcp.json",
            kind=ArtifactKind.FILE,
            mode=ArtifactMode.TRANSFORM,
            source=".mcp.json",
            content=b"{}",
            digest=digest,
        )


def test_transform_digest_matches_content() -> None:
    """transform 计划摘要由目标内容确定。"""
    artifact = transform_artifact("cursor", ".cursor/mcp.json", b"{}\n")

    assert artifact.digest == content_digest(b"{}\n")


def test_all_adapters_plan_without_touching_filesystem(tmp_path: Path) -> None:
    """adapter 规划不创建、修改或删除任何项目文件。"""
    context = AdapterContext(
        mcp_servers={
            "filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server"]}
        }
    )
    before = _tree(tmp_path)
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        plans = [artifact for adapter in REGISTRY.values() for artifact in adapter.plan(context)]
    finally:
        os.chdir(original_cwd)

    assert _tree(tmp_path) == before
    assert {artifact.agent for artifact in plans} == {"claude", "codex", "cursor"}


def _tree(root: Path) -> tuple[str, ...]:
    """返回临时项目的稳定文件树。"""
    return tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*")))
