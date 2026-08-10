"""Safety tests for legacy configuration coexistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.init import initialize_project


@pytest.mark.integration
@pytest.mark.safety
def test_init_preserves_unknown_legacy_configuration(tmp_path: Path) -> None:
    """MVP does not migrate, merge, or delete legacy configuration implicitly."""

    legacy = tmp_path / ".agent21/config.json"
    legacy.parent.mkdir()
    payload = b'{"legacy":true}\n'
    legacy.write_bytes(payload)

    initialize_project(tmp_path, agents=())

    assert legacy.read_bytes() == payload
    assert (tmp_path / ".agents/config.yaml").is_file()
