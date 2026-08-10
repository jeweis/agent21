"""Integration tests for initializing an empty Agent21 project."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent21.cli import app
from agent21.config import load_config
from agent21.init import initialize_project
from agent21.manifest import load_manifest


@pytest.mark.integration
def test_init_creates_authoritative_project_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The default command non-interactively initializes truth sources for --agents."""

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["--agents", "codex,cursor", "--mode", "copy"])

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

    monkeypatch.setattr("agent21.init.detect_agents", lambda: {"pi": True, "codex": False})

    initialize_project(tmp_path, agents=None)

    assert load_config(tmp_path).agents["pi"].enabled
    assert not load_config(tmp_path).agents["codex"].enabled


@pytest.mark.integration
def test_init_appends_agents_to_existing_config(tmp_path: Path) -> None:
    """Re-running init with more agents enables them without disabling existing ones."""

    initialize_project(tmp_path, agents=("opencode",), mode="auto")

    result = initialize_project(tmp_path, agents=("opencode", "codex"))

    config = load_config(tmp_path)
    assert config.agents["opencode"].enabled
    assert config.agents["codex"].enabled
    assert not config.agents["claude"].enabled
    assert set(result.enabled_agents) == {"codex", "opencode"}


@pytest.mark.integration
def test_init_without_agents_keeps_existing_selection(tmp_path: Path) -> None:
    """Omitting --agents must not silently change an existing selection."""

    initialize_project(tmp_path, agents=("opencode",), mode="auto")
    config_before = (tmp_path / ".agents/config.yaml").read_bytes()

    result = initialize_project(tmp_path)

    assert (tmp_path / ".agents/config.yaml").read_bytes() == config_before
    assert set(result.enabled_agents) == {"opencode"}


@pytest.mark.integration
def test_init_creates_agents_readme_guide(tmp_path: Path) -> None:
    """.agents/README.md is created with the managed guidance block."""

    initialize_project(tmp_path, agents=("opencode",), mode="auto")

    readme = tmp_path / ".agents/README.md"
    assert readme.is_file()
    content = readme.read_text(encoding="utf-8")
    assert "<!-- AGENT21 START -->" in content
    assert "agent21 sync" in content
    assert "agent21 status" in content


@pytest.mark.integration
def test_init_readme_is_idempotent(tmp_path: Path) -> None:
    """Repeated init does not duplicate the managed README block."""

    initialize_project(tmp_path, agents=("opencode",), mode="auto")
    first = (tmp_path / ".agents/README.md").read_bytes()

    initialize_project(tmp_path, agents=("opencode",), mode="auto")

    assert (tmp_path / ".agents/README.md").read_bytes() == first


@pytest.mark.integration
def test_init_readme_appends_to_existing_user_content(tmp_path: Path) -> None:
    """Existing README without the marker gets the block appended, never replaced."""

    initialize_project(tmp_path, agents=("opencode",), mode="auto")
    readme = tmp_path / ".agents/README.md"
    readme.write_text("# My custom notes\n", encoding="utf-8")

    initialize_project(tmp_path, agents=("opencode",), mode="auto")

    content = readme.read_text(encoding="utf-8")
    assert content.startswith("# My custom notes")
    assert content.count("<!-- AGENT21 START -->") == 1
    assert "agent21 sync" in content
