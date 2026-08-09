"""Project-boundary integration tests with external sentinels."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.errors import BoundaryError
from agent21.init import initialize_project
from agent21.sync import sync_project


@pytest.mark.integration
@pytest.mark.safety
def test_symlinked_mcp_source_cannot_escape_project(tmp_path: Path) -> None:
    """A project path resolving to an external file is rejected before it is read."""

    root = tmp_path / "project"
    initialize_project(root, agents=("cursor",), assume_yes=True)
    sentinel = tmp_path / "outside.json"
    payload = b'{"mcpServers":{}}\n'
    sentinel.write_bytes(payload)
    (root / ".mcp.json").symlink_to(sentinel)

    with pytest.raises(BoundaryError):
        sync_project(root, available_agents={"cursor": True})

    assert sentinel.read_bytes() == payload
    assert not (root / ".cursor/mcp.json").exists()
