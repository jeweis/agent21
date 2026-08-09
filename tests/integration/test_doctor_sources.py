"""Tests for authoritative Skill and MCP source health."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.doctor import diagnose_project
from agent21.init import initialize_project


@pytest.mark.integration
def test_doctor_reports_invalid_skill_and_valid_empty_mcp(tmp_path: Path) -> None:
    """Skills need SKILL.md while an empty MCP server set remains valid."""

    initialize_project(tmp_path, agents=(), assume_yes=True)
    invalid_skill = tmp_path / ".agents/skills/demo"
    invalid_skill.mkdir()
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")

    results = diagnose_project(tmp_path)

    skill = next(item for item in results if item.check_id == "skill.invalid")
    mcp = next(item for item in results if item.check_id == "source.mcp")
    assert skill.status.value == "blocked"
    assert mcp.status.value == "pass"
