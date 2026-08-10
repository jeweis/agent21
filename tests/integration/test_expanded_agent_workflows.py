"""Independent integration workflows for newly supported agents."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent21.init import initialize_project
from agent21.sync import sync_project

pytestmark = pytest.mark.integration

ALL_AGENTS = ("claude", "codex", "cursor", "opencode", "pi", "workbuddy", "qoder")


def test_all_seven_agents_sync_in_one_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """启用全部七个 Agent 时，一次 sync 产出各自权威目标且无冲突、无跳过。"""

    initialize_project(tmp_path, agents=ALL_AGENTS, mode="copy")
    (tmp_path / ".mcp.json").write_text(
        '{"mcpServers":{"demo":{"command":"npx","args":["-y","demo"]}}}\n', encoding="utf-8"
    )
    monkeypatch.setattr("agent21.sync.executable_available", lambda command: True)

    result = sync_project(tmp_path)

    assert result.conflicts == []
    assert result.skipped == []
    for target in ("CLAUDE.md", ".codex/config.toml", ".cursor/mcp.json", "opencode.json"):
        assert (tmp_path / target).is_file()
    for target in (".claude/skills", ".codebuddy/skills", ".qoder/skills"):
        assert (tmp_path / target).is_dir()
    assert not (tmp_path / ".pi").exists()


@pytest.mark.parametrize(
    ("agent", "target_dir"),
    [
        ("claude", ".claude/skills"),
        ("workbuddy", ".codebuddy/skills"),
        ("qoder", ".qoder/skills"),
    ],
)
def test_skill_content_propagates_to_mapped_directories(
    tmp_path: Path, agent: str, target_dir: str
) -> None:
    """.agents/skills/<name>/SKILL.md 内容被完整映射到各 Agent 的 Skills 目录。"""

    initialize_project(tmp_path, agents=(agent,), mode="copy")
    source = tmp_path / ".agents/skills/demo"
    source.mkdir(parents=True)
    content = "---\nname: demo\n---\n# Demo\n"
    (source / "SKILL.md").write_text(content, encoding="utf-8")

    sync_project(tmp_path)

    mapped = tmp_path / target_dir / "demo" / "SKILL.md"
    assert mapped.read_text(encoding="utf-8") == content


def test_opencode_mcp_sync_is_idempotent(tmp_path: Path) -> None:
    """OpenCode gets one deterministic config and preserves root authority."""

    initialize_project(tmp_path, agents=("opencode",), mode="copy")
    source = {"mcpServers": {"demo": {"command": "npx", "args": ["-y", "demo"]}}}
    (tmp_path / ".mcp.json").write_text(json.dumps(source), encoding="utf-8")

    first = sync_project(tmp_path)
    second = sync_project(tmp_path)

    assert first.created == ["opencode.json"]
    assert second.unchanged == ["opencode.json"]
    assert json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8")) == source


def test_qoder_sync_maps_only_skills(tmp_path: Path) -> None:
    """Qoder keeps root instructions and MCP native while mapping Skills."""

    initialize_project(tmp_path, agents=("qoder",), mode="copy")

    result = sync_project(tmp_path)

    assert result.created == [".qoder/skills"]
    assert not (tmp_path / ".qoder/AGENTS.md").exists()
    assert not (tmp_path / ".qoder/mcp.json").exists()


def test_pi_sync_reports_missing_adapter_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing Pi MCP support is visible without installing or running code."""

    initialize_project(tmp_path, agents=("pi",), mode="copy")
    (tmp_path / ".mcp.json").write_text(
        '{"mcpServers":{"demo":{"command":"demo"}}}\n', encoding="utf-8"
    )
    monkeypatch.setattr("agent21.sync.executable_available", lambda command: False)

    result = sync_project(tmp_path)

    assert result.created == []
    assert result.skipped == [
        "pi: MCP dependency unavailable (pi-mcp-adapter); action: pi install npm:pi-mcp-adapter"
    ]
    assert not (tmp_path / ".pi").exists()
