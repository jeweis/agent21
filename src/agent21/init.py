"""Safe initialization of project-local Agent21 authoritative sources."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path

from agent21 import __version__
from agent21.config import default_config, load_config, save_config
from agent21.errors import ConfigError
from agent21.manifest import save_manifest
from agent21.models import (
    REGISTERED_AGENTS,
    AgentSelection,
    Manifest,
    ProjectConfig,
    SyncMode,
)
from agent21.scanner import detect_agents

DEFAULT_INSTRUCTIONS = """# Project Agent Instructions

This file is the authoritative project-level instruction source managed by the team.
"""


@dataclass(frozen=True)
class InitResult:
    """Stable summary returned after project initialization."""

    enabled_agents: tuple[str, ...]
    created: tuple[str, ...]
    reused: tuple[str, ...]


def _selected_agents(agents: Iterable[str] | None) -> tuple[str, ...]:
    """Validate an explicit selection or derive it from executable discovery."""

    if agents is None:
        return tuple(name for name, available in detect_agents().items() if available)
    selected = tuple(sorted(set(agents)))
    unknown = sorted(set(selected).difference(REGISTERED_AGENTS))
    if unknown:
        raise ConfigError(f"unknown agent: {', '.join(unknown)}")
    return selected


def initialize_project(
    root: Path,
    *,
    agents: Iterable[str] | None = None,
    mode: str = "auto",
) -> InitResult:
    """Create or extend deterministic project truth sources without replacing content."""

    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    try:
        sync_mode = SyncMode(mode)
    except ValueError as exc:
        raise ConfigError(f"unsupported sync mode: {mode}") from exc
    selected = _selected_agents(agents)
    config, config_created = _resolve_config(root, selected, sync_mode, agents)

    created: list[str] = []
    reused: list[str] = []
    if config_created:
        created.append(".agents/config.yaml")
    else:
        reused.append(".agents/config.yaml")

    instructions_path = root / config.instructions_source
    if instructions_path.exists():
        reused.append(config.instructions_source)
    else:
        instructions_path.write_text(DEFAULT_INSTRUCTIONS, encoding="utf-8")
        created.append(config.instructions_source)

    skills_path = root / config.skills_source
    if skills_path.exists():
        reused.append(config.skills_source)
    else:
        skills_path.mkdir(parents=True)
        created.append(config.skills_source)

    mcp_path = root / config.mcp_source
    if mcp_path.exists():
        reused.append(config.mcp_source)

    manifest_path = root / ".agents/manifest.yaml"
    if manifest_path.exists():
        reused.append(".agents/manifest.yaml")
    else:
        save_manifest(root, Manifest(agent21_version=__version__))
        created.append(".agents/manifest.yaml")

    enabled = tuple(name for name, selection in config.agents.items() if selection.enabled)
    return InitResult(enabled, tuple(sorted(created)), tuple(sorted(reused)))


def _resolve_config(
    root: Path,
    selected: tuple[str, ...],
    sync_mode: SyncMode,
    agents: Iterable[str] | None,
) -> tuple[ProjectConfig, bool]:
    """加载已有配置并合并启用项，或为全新项目建立确定性配置。

    返回 (最终配置, 是否新建了配置文件)。已有配置且显式指定 agents 时，
    本次选择的 agent 被合并启用，其余保持原状，不关闭任何已启用项。
    """

    config_path = root / ".agents/config.yaml"
    if not config_path.exists():
        defaults = default_config()
        config = replace(
            defaults,
            sync_mode=sync_mode,
            agents={
                name: AgentSelection(enabled=name in selected) for name in sorted(defaults.agents)
            },
        )
        save_config(root, config)
        return config, True
    existing = load_config(root)
    if agents is None:
        return existing, False
    merged = {
        name: AgentSelection(enabled=existing.agents[name].enabled or name in selected)
        for name in REGISTERED_AGENTS
    }
    config = replace(existing, agents=merged)
    if config != existing:
        save_config(root, config)
    return config, False


def disable_agents(root: Path, agents: Iterable[str]) -> None:
    """将指定 Agent 置为禁用并写回 config；未启用的目标报错。"""

    config = load_config(root)
    for agent in agents:
        if not config.agents[agent].enabled:
            raise ConfigError(f"agent is not enabled: {agent}")
    merged = {
        name: AgentSelection(enabled=config.agents[name].enabled and name not in set(agents))
        for name in REGISTERED_AGENTS
    }
    updated = replace(config, agents=merged)
    if updated != config:
        save_config(root, updated)
