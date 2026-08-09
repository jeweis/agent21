"""Filesystem capability and fallback compatibility tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent21.fs import supports_symlink


@pytest.mark.compatibility
def test_symlink_probe_cleans_all_probe_state(tmp_path: Path) -> None:
    """Capability detection is safe regardless of the platform result."""

    result = supports_symlink(tmp_path)

    assert isinstance(result, bool)
    assert not (tmp_path / ".agents/.symlink-probe").exists()
