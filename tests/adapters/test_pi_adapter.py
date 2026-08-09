"""Pi adapter dependency contract tests."""

from __future__ import annotations

import pytest

from agent21.adapters.pi import capability, plan
from agent21.adapters.protocol import AdapterContext
from agent21.models import CapabilityStatus

pytestmark = pytest.mark.adapter


def test_pi_declares_mcp_adapter_without_managed_output() -> None:
    """Pi uses the user-installed adapter against root `.mcp.json`."""

    assert capability.mcp is CapabilityStatus.COMPATIBLE
    assert capability.mcp_dependency is not None
    assert capability.mcp_dependency.executable == "pi-mcp-adapter"
    assert capability.mcp_dependency.install_hint == "pi install npm:pi-mcp-adapter"
    assert plan(AdapterContext(mcp_servers={"tool": {"command": "tool"}})) == ()
