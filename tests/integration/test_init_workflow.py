"""Integration tests for initializing an empty Agent21 project."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent21.cli import app
from agent21.config import load_config
from agent21.manifest import load_manifest


@pytest.mark.integration
def test_init_creates_authoritative_project_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-interactive initialization creates the version-controlled truth sources."""

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["init", "--agents", "codex,cursor", "--mode", "copy", "--yes"]
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / ".agents/skills").is_dir()
    assert (tmp_path / ".agents/config.yaml").is_file()
    assert (tmp_path / ".agents/manifest.yaml").is_file()
    config = load_config(tmp_path)
    assert config.agents["codex"].enabled
    assert config.agents["cursor"].enabled
    assert not config.agents["claude"].enabled
    assert load_manifest(tmp_path).managed_artifacts == []


@pytest.mark.integration
def test_init_default_selection_uses_detected_agents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no explicit list is supplied, scanner results determine enablement."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("agent21.init.detect_agents", lambda: {"pi": True, "codex": False})

    result = CliRunner().invoke(app, ["init", "--yes"])

    assert result.exit_code == 0, result.output
    assert load_config(tmp_path).agents["pi"].enabled
