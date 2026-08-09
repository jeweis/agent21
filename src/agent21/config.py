"""Strict load/save helpers for `.agents/config.yaml`."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from agent21.errors import BoundaryError, ConfigError
from agent21.models import (
    REGISTERED_AGENTS,
    AgentSelection,
    ProjectConfig,
    SyncMode,
)
from agent21.project import safe_join

CONFIG_PATH = Path(".agents/config.yaml")


def default_config() -> ProjectConfig:
    """Return the MVP default project configuration."""

    return ProjectConfig(
        agents={agent: AgentSelection(enabled=True) for agent in REGISTERED_AGENTS},
        sync_mode=SyncMode.AUTO,
        instructions_source="AGENTS.md",
        skills_source=".agents/skills",
        mcp_source=".mcp.json",
    )


def load_config(project_root: str | Path) -> ProjectConfig:
    """Load and strictly validate project configuration from disk."""

    path = Path(project_root) / CONFIG_PATH
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"could not read config: {CONFIG_PATH.as_posix()}") from exc
    return _parse_config(raw)


def save_config(project_root: str | Path, config: ProjectConfig) -> None:
    """Write deterministic YAML for a validated project configuration."""

    root = Path(project_root)
    path = safe_join(root, CONFIG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_yaml(_config_to_data(config)), encoding="utf-8")


def _parse_config(raw: Any) -> ProjectConfig:
    if not isinstance(raw, dict):
        raise ConfigError("config must be a mapping")
    _require_fields(raw, {"schema_version", "agents", "sync", "sources"}, "config")
    if raw["schema_version"] != 1:
        raise ConfigError("schema_version must be 1")
    agents = _parse_agents(raw["agents"])
    sync = _mapping(raw["sync"], "sync")
    _require_fields(sync, {"mode"}, "sync")
    sources = _mapping(raw["sources"], "sources")
    _require_fields(sources, {"instructions", "skills", "mcp"}, "sources")
    try:
        return ProjectConfig(
            schema_version=1,
            agents=agents,
            sync_mode=SyncMode(sync["mode"]),
            instructions_source=_string(sources["instructions"], "sources.instructions"),
            skills_source=_string(sources["skills"], "sources.skills"),
            mcp_source=_string(sources["mcp"], "sources.mcp"),
        )
    except (BoundaryError, ValueError) as exc:
        raise ConfigError(str(exc)) from exc


def _parse_agents(raw: Any) -> dict[str, AgentSelection]:
    agents = _mapping(raw, "agents")
    _require_fields(agents, set(REGISTERED_AGENTS), "agents")
    parsed: dict[str, AgentSelection] = {}
    for agent in REGISTERED_AGENTS:
        selection = _mapping(agents[agent], f"agents.{agent}")
        _require_fields(selection, {"enabled"}, f"agents.{agent}")
        try:
            parsed[agent] = AgentSelection(enabled=selection["enabled"])
        except TypeError as exc:
            raise ConfigError(f"agents.{agent}.enabled must be a boolean") from exc
    return parsed


def _config_to_data(config: ProjectConfig) -> dict[str, Any]:
    return {
        "schema_version": config.schema_version,
        "agents": {
            agent: {"enabled": config.agents[agent].enabled} for agent in sorted(config.agents)
        },
        "sync": {"mode": config.sync_mode.value},
        "sources": {
            "instructions": config.instructions_source,
            "skills": config.skills_source,
            "mcp": config.mcp_source,
        },
    }


def _dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def _require_fields(raw: dict[Any, Any], expected: set[str], subject: str) -> None:
    keys = set(raw)
    unknown = sorted(keys - expected)
    missing = sorted(expected - keys)
    if unknown:
        raise ConfigError(f"unknown field in {subject}: {unknown[0]}")
    if missing:
        raise ConfigError(f"missing field in {subject}: {missing[0]}")


def _mapping(raw: Any, subject: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ConfigError(f"{subject} must be a mapping")
    return cast(dict[str, Any], raw)


def _string(raw: Any, subject: str) -> str:
    if not isinstance(raw, str):
        raise ConfigError(f"{subject} must be a string")
    return raw
