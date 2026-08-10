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
        save_manifest(root, Manifest(agent21=__version__))
        created.append(".agents/manifest.yaml")

    _ensure_agents_readme(root, created, reused)

    enabled = tuple(name for name, selection in config.agents.items() if selection.enabled)
    return InitResult(enabled, tuple(sorted(created)), tuple(sorted(reused)))


AGENTS_README_START = "<!-- AGENT21 START -->"
AGENTS_README_END = "<!-- AGENT21 END -->"
AGENTS_README_BLOCK = f"""{AGENTS_README_START}
# Agent21 权威配置源

此目录（`.agents/`）与项目根目录的 `.mcp.json` 是 Agent21 的**权威配置源**。
你只需维护它们，然后运行同步命令，即可让所有已启用的 Agent 使用同一套配置。

- `AGENTS.md`：项目指令
- `.agents/skills/`：项目 Skills
- `.mcp.json`：MCP 服务配置（可选）
- `.agents/config.yaml`：启用的 Agent 与同步模式
- `.agents/manifest.yaml`：托管产物与 Skills 记录（由 Agent21 维护）

关键命令：

- `agent21`：启用 Agent 并同步
- `agent21 sync`：将权威配置同步到已启用的 Agent
- `agent21 status`：查看各 Agent 状态
- `agent21 doctor`：检查项目健康状态

修改权威源后，重新运行 `agent21 sync` 即可。除 `.agents/manifest.yaml`
由 Agent21 自动维护外，其他文件请交由团队审阅与版本控制。
{AGENTS_README_END}"""


def _ensure_agents_readme(root: Path, created: list[str], reused: list[str]) -> None:
    """创建或追加 `.agents/README.md` 的托管说明块（幂等，不覆盖用户内容）。"""

    readme_path = root / ".agents/README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        if AGENTS_README_START in content:
            reused.append(".agents/README.md")
            return
        with readme_path.open("a", encoding="utf-8") as handle:
            handle.write("\n" + AGENTS_README_BLOCK + "\n")
        reused.append(".agents/README.md")
        return
    readme_path.write_text(AGENTS_README_BLOCK + "\n", encoding="utf-8")
    created.append(".agents/README.md")


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
