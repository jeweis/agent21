"""Safe initialization of project-local Agent21 authoritative sources."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path

from agent21 import __version__
from agent21.config import default_config, save_config
from agent21.errors import ConfigError
from agent21.manifest import save_manifest
from agent21.models import AgentSelection, Manifest, SyncMode
from agent21.scanner import EXECUTABLES, detect_agents

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
    unknown = sorted(set(selected).difference(EXECUTABLES))
    if unknown:
        raise ConfigError(f"unknown agent: {', '.join(unknown)}")
    return selected


def initialize_project(
    root: Path,
    *,
    agents: Iterable[str] | None = None,
    mode: str = "auto",
    assume_yes: bool = False,
) -> InitResult:
    """Create deterministic project truth sources without replacing existing content."""

    del assume_yes
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    try:
        sync_mode = SyncMode(mode)
    except ValueError as exc:
        raise ConfigError(f"unsupported sync mode: {mode}") from exc
    selected = _selected_agents(agents)
    defaults = default_config()
    config = replace(
        defaults,
        sync_mode=sync_mode,
        agents={name: AgentSelection(enabled=name in selected) for name in sorted(defaults.agents)},
    )

    created: list[str] = []
    reused: list[str] = []
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

    config_path = root / ".agents/config.yaml"
    if config_path.exists():
        reused.append(".agents/config.yaml")
    else:
        save_config(root, config)
        created.append(".agents/config.yaml")

    manifest_path = root / ".agents/manifest.yaml"
    if manifest_path.exists():
        reused.append(".agents/manifest.yaml")
    else:
        save_manifest(root, Manifest(agent21_version=__version__))
        created.append(".agents/manifest.yaml")

    return InitResult(selected, tuple(sorted(created)), tuple(sorted(reused)))
