"""Unit tests for project configuration loading and deterministic YAML."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.config import CONFIG_PATH, default_config, load_config, save_config
from agent21.errors import ConfigError
from agent21.models import SyncMode


def test_default_config_matches_mvp_sources_and_agents() -> None:
    """Defaults point at the three authority sources and registered agents."""

    config = default_config()

    assert config.schema_version == 1
    assert config.sync_mode is SyncMode.AUTO
    assert config.instructions_source == "AGENTS.md"
    assert config.skills_source == ".agents/skills"
    assert config.mcp_source == ".mcp.json"
    assert set(config.agents) == {
        "claude",
        "codex",
        "cursor",
        "opencode",
        "pi",
        "qoder",
        "workbuddy",
    }


def test_load_legacy_config_disables_additive_agents(tmp_path: Path) -> None:
    """Schema v1 projects gain new agents in a disabled state without migration."""

    config = default_config()
    save_config(tmp_path, config)
    path = tmp_path / CONFIG_PATH
    text = path.read_text(encoding="utf-8")
    text = text.replace("  qoder:\n    enabled: true\n", "")
    text = text.replace("  workbuddy:\n    enabled: true\n", "")
    path.write_text(text, encoding="utf-8")

    loaded = load_config(tmp_path)

    assert not loaded.agents["qoder"].enabled
    assert not loaded.agents["workbuddy"].enabled


def test_save_config_writes_deterministic_yaml(tmp_path: Path) -> None:
    """Saving the same config twice produces stable bytes."""

    config = default_config()

    save_config(tmp_path, config)
    first = (tmp_path / CONFIG_PATH).read_bytes()
    save_config(tmp_path, config)
    second = (tmp_path / CONFIG_PATH).read_bytes()

    assert first == second
    assert b"schema_version: 1\n" in first


def test_load_config_rejects_unknown_top_level_field(tmp_path: Path) -> None:
    """Config parsing is strict so typos cannot silently change behavior."""

    path = tmp_path / CONFIG_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        "schema_version: 1\nagents: {}\nsync: {mode: auto}\nsources: {}\nextra: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="unknown field"):
        load_config(tmp_path)


def test_load_config_rejects_string_enabled_values(tmp_path: Path) -> None:
    """YAML truthy strings are rejected for agent enablement."""

    path = tmp_path / CONFIG_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "agents:",
                "  claude: {enabled: 'true'}",
                "  codex: {enabled: true}",
                "  cursor: {enabled: true}",
                "  opencode: {enabled: true}",
                "  pi: {enabled: true}",
                "sync: {mode: auto}",
                "sources:",
                "  instructions: AGENTS.md",
                "  skills: .agents/skills",
                "  mcp: .mcp.json",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="enabled"):
        load_config(tmp_path)


def test_load_config_rejects_unsafe_source_path(tmp_path: Path) -> None:
    """Authority source paths must remain project-relative."""

    path = tmp_path / CONFIG_PATH
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "agents:",
                "  claude: {enabled: true}",
                "  codex: {enabled: true}",
                "  cursor: {enabled: true}",
                "  opencode: {enabled: true}",
                "  pi: {enabled: true}",
                "sync: {mode: auto}",
                "sources:",
                "  instructions: ../AGENTS.md",
                "  skills: .agents/skills",
                "  mcp: .mcp.json",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="outside project"):
        load_config(tmp_path)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("[]\n", "must be a mapping"),
        ("schema_version: 2\nagents: {}\nsync: {}\nsources: {}\n", "schema_version"),
        ("schema_version: 1\nagents: {}\nsync: {}\nsources: {}\n", "missing field"),
        ("schema_version: 1\nagents: []\nsync: {}\nsources: {}\n", "agents must be a mapping"),
    ],
)
def test_load_config_rejects_malformed_structures(
    tmp_path: Path, payload: str, message: str
) -> None:
    """Wrong schema versions, missing keys, and container types fail explicitly."""

    path = tmp_path / CONFIG_PATH
    path.parent.mkdir(parents=True)
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ConfigError, match=message):
        load_config(tmp_path)
