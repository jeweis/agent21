"""Integration tests for MCP safety and diagnostic redaction."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.init import initialize_project
from agent21.mcp import McpConfigError
from agent21.sync import sync_project


@pytest.mark.integration
@pytest.mark.safety
def test_invalid_mcp_source_fails_before_adapter_outputs(tmp_path: Path) -> None:
    """Malformed MCP JSON cannot leave partially transformed tool configuration."""

    initialize_project(tmp_path, agents=("codex", "cursor"))
    (tmp_path / ".mcp.json").write_text('{"token":"fixture-secret-token"', encoding="utf-8")

    with pytest.raises(McpConfigError) as failure:
        sync_project(tmp_path, available_agents={"codex": True, "cursor": True})

    assert "fixture-secret-token" not in str(failure.value)
    assert not (tmp_path / ".codex/config.toml").exists()
    assert not (tmp_path / ".cursor/mcp.json").exists()
