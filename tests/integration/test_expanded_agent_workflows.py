"""Independent integration workflows for newly supported agents."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent21.init import initialize_project
from agent21.sync import sync_project

pytestmark = pytest.mark.integration


def test_opencode_mcp_sync_is_idempotent(tmp_path: Path) -> None:
    """OpenCode gets one deterministic config and preserves root authority."""

    initialize_project(tmp_path, agents=("opencode",), mode="copy", assume_yes=True)
    source = {"mcpServers": {"demo": {"command": "npx", "args": ["-y", "demo"]}}}
    (tmp_path / ".mcp.json").write_text(json.dumps(source), encoding="utf-8")

    first = sync_project(tmp_path, available_agents={"opencode": True})
    second = sync_project(tmp_path, available_agents={"opencode": True})

    assert first.created == ["opencode.json"]
    assert second.unchanged == ["opencode.json"]
    assert json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8")) == source


def test_qoder_sync_maps_only_skills(tmp_path: Path) -> None:
    """Qoder keeps root instructions and MCP native while mapping Skills."""

    initialize_project(tmp_path, agents=("qoder",), mode="copy", assume_yes=True)

    result = sync_project(tmp_path, available_agents={"qoder": True})

    assert result.created == [".qoder/skills"]
    assert not (tmp_path / ".qoder/AGENTS.md").exists()
    assert not (tmp_path / ".qoder/mcp.json").exists()


def test_pi_sync_reports_missing_adapter_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing Pi MCP support is visible without installing or running code."""

    initialize_project(tmp_path, agents=("pi",), mode="copy", assume_yes=True)
    (tmp_path / ".mcp.json").write_text(
        '{"mcpServers":{"demo":{"command":"demo"}}}\n', encoding="utf-8"
    )
    monkeypatch.setattr("agent21.sync.executable_available", lambda command: False)

    result = sync_project(tmp_path, available_agents={"pi": True})

    assert result.created == []
    assert result.skipped == [
        "pi: MCP dependency unavailable (pi-mcp-adapter); action: pi install npm:pi-mcp-adapter"
    ]
    assert not (tmp_path / ".pi").exists()
