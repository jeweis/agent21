"""Agent adapter protocol and side-effect-free planning primitives."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from agent21.models import (
    AgentCapability,
    ArtifactKind,
    ArtifactMode,
    PlannedArtifact,
    digest_bytes,
)

__all__ = [
    "AdapterContext",
    "AgentAdapter",
    "AgentCapability",
    "ArtifactKind",
    "ArtifactMode",
    "PlannedArtifact",
    "content_digest",
    "copy_artifact",
    "directory_artifact",
    "sorted_artifacts",
    "stable_json_bytes",
    "transform_artifact",
]


@dataclass(frozen=True)
class AdapterContext:
    """adapter 生成计划所需的权威输入引用。

    adapter 只消费这里传入的路径和 MCP 数据，不读取或写入项目文件。
    后续 sync 层负责将这些计划交给统一事务执行。
    """

    instructions_source: str = "AGENTS.md"
    skills_source: str = ".agents/skills"
    mcp_source: str = ".mcp.json"
    mcp_servers: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    sync_mode: ArtifactMode = ArtifactMode.COPY


class AgentAdapter(Protocol):
    """所有 Agent adapter 必须实现的最小协议。"""

    capability: AgentCapability

    def plan(self, context: AdapterContext) -> tuple[PlannedArtifact, ...]:
        """根据权威输入生成确定性计划，不产生文件系统副作用。"""


def content_digest(content: bytes) -> str:
    """计算文件内容的规范摘要。"""
    return digest_bytes(content)


def source_digest(source: str, *, mode: ArtifactMode) -> str:
    """计算 copy/symlink 计划的稳定摘要占位。

    sync 层真正应用时会读取源内容或链接目标再校验；adapter 只需要提供
    可重复的计划摘要，避免在规划阶段触碰文件系统。
    """
    payload = f"{mode.value}:{source}".encode()
    return content_digest(payload)


def stable_json_bytes(data: Mapping[str, object]) -> bytes:
    """将映射编码为稳定 JSON bytes，供 Cursor MCP 转换使用。"""
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def copy_artifact(agent: str, source: str, target: str) -> PlannedArtifact:
    """创建稳定 copy 计划。"""
    return PlannedArtifact(
        agent=agent,
        target=target,
        kind=ArtifactKind.FILE,
        mode=ArtifactMode.COPY,
        source=source,
        content=None,
        digest=source_digest(source, mode=ArtifactMode.COPY),
    )


def directory_artifact(agent: str, source: str, target: str, mode: ArtifactMode) -> PlannedArtifact:
    """创建目录 copy/symlink 计划。"""
    if mode not in {ArtifactMode.COPY, ArtifactMode.SYMLINK}:
        raise ValueError("directory artifacts only support copy or symlink mode")
    return PlannedArtifact(
        agent=agent,
        target=target,
        kind=ArtifactKind.DIRECTORY if mode == ArtifactMode.COPY else ArtifactKind.SYMLINK,
        mode=mode,
        source=source,
        content=None,
        digest=source_digest(source, mode=mode),
    )


def transform_artifact(agent: str, target: str, content: bytes) -> PlannedArtifact:
    """创建稳定 transform 文件计划。"""
    return PlannedArtifact(
        agent=agent,
        target=target,
        kind=ArtifactKind.FILE,
        mode=ArtifactMode.TRANSFORM,
        source=None,
        content=content,
        digest=content_digest(content),
    )


def sorted_artifacts(artifacts: Sequence[PlannedArtifact]) -> tuple[PlannedArtifact, ...]:
    """按目标路径稳定排序计划，便于后续事务和快照比较。"""
    return tuple(sorted(artifacts, key=lambda artifact: (artifact.target, artifact.agent)))
