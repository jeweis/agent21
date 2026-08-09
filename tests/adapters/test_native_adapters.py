"""OpenCode 和 Pi 原生 adapter 行为测试。"""

from __future__ import annotations

from types import ModuleType

import pytest

from agent21.adapters import opencode, pi
from agent21.adapters.protocol import AdapterContext
from agent21.models import CapabilityStatus

pytestmark = pytest.mark.adapter


@pytest.mark.parametrize("adapter", [opencode, pi])
def test_native_adapters_have_no_managed_outputs(adapter: ModuleType) -> None:
    """OpenCode/Pi 在 MVP 中不生成任何托管产物。"""
    assert adapter.plan(AdapterContext(mcp_servers={"tool": {"command": "tool"}})) == ()


@pytest.mark.parametrize("adapter", [opencode, pi])
def test_native_adapters_mark_mcp_unsupported(adapter: ModuleType) -> None:
    """OpenCode/Pi MCP 明确 unsupported，不能伪装成兼容或 transform。"""
    assert adapter.capability.instructions is CapabilityStatus.NATIVE
    assert adapter.capability.skills is CapabilityStatus.NATIVE
    assert adapter.capability.mcp is CapabilityStatus.UNSUPPORTED
