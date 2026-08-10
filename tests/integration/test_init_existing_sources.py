"""Tests for reusing existing authoritative Agent21 sources."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.init import initialize_project


@pytest.mark.integration
def test_init_preserves_existing_authoritative_sources(tmp_path: Path) -> None:
    """Existing AGENTS and MCP files remain byte-for-byte authoritative."""

    instructions = b"# Existing team rules\n"
    mcp = b'{"mcpServers":{"local":{"command":"demo"}}}\n'
    (tmp_path / "AGENTS.md").write_bytes(instructions)
    (tmp_path / ".mcp.json").write_bytes(mcp)

    initialize_project(tmp_path, agents=("codex",), mode="auto")

    assert (tmp_path / "AGENTS.md").read_bytes() == instructions
    assert (tmp_path / ".mcp.json").read_bytes() == mcp
