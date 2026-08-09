"""Pi 无托管输出的兼容 adapter 行为测试。"""

from __future__ import annotations

from types import ModuleType

import pytest

from agent21.adapters import pi
from agent21.adapters.protocol import AdapterContext
from agent21.models import CapabilityStatus

pytestmark = pytest.mark.adapter


@pytest.mark.parametrize("adapter", [pi])
def test_native_adapters_have_no_managed_outputs(adapter: ModuleType) -> None:
    """Pi MCP adapter 直接消费根配置，不生成托管产物。"""
    assert adapter.plan(AdapterContext(mcp_servers={"tool": {"command": "tool"}})) == ()


@pytest.mark.parametrize("adapter", [pi])
def test_native_adapters_mark_mcp_compatible(adapter: ModuleType) -> None:
    """Pi MCP 通过显式第三方 adapter 兼容根配置。"""
    assert adapter.capability.instructions is CapabilityStatus.NATIVE
    assert adapter.capability.skills is CapabilityStatus.NATIVE
    assert adapter.capability.mcp is CapabilityStatus.COMPATIBLE
