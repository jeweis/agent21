"""Safety and idempotency tests for Agent21 initialization."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.init import initialize_project


@pytest.mark.integration
def test_repeat_init_is_byte_stable(tmp_path: Path) -> None:
    """Repeating initialization with the same inputs produces no content drift."""

    initialize_project(tmp_path, agents=("codex",), mode="copy")
    tracked = ("AGENTS.md", ".agents/config.yaml", ".agents/manifest.yaml")
    before = {path: (tmp_path / path).read_bytes() for path in tracked}

    initialize_project(tmp_path, agents=("codex",), mode="copy")

    assert {path: (tmp_path / path).read_bytes() for path in tracked} == before
