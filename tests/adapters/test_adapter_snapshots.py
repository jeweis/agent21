"""兼容映射与转换输出的稳定基线策略测试。"""

from __future__ import annotations

import pytest

from tests.support.adapter_contracts import (
    load_adapter_contracts,
    validate_mapped_outputs_have_snapshots,
)

pytestmark = [pytest.mark.adapter, pytest.mark.snapshot]


def test_planned_mapped_outputs_do_not_require_baselines() -> None:
    """planned 适配器未实现输出时，不要求稳定基线。"""
    for contract in load_adapter_contracts():
        validate_mapped_outputs_have_snapshots(contract)


def test_transform_capability_requires_snapshot_output() -> None:
    """转换能力一旦实现，必须至少有一个纳入快照的托管输出。"""
    contract = {
        "schema_version": "1.0",
        "agent": "cursor",
        "status": "implemented",
        "capabilities": {
            "instructions": {"mode": "native"},
            "skills": {"mode": "native"},
            "mcp": {"mode": "transform"},
        },
        "source_inputs": ["AGENTS.md"],
        "managed_outputs": [
            {
                "path": ".cursor/mcp.json",
                "kind": "file",
                "managed": True,
                "snapshot": False,
            }
        ],
        "platform_modes": {
            "linux": ["auto"],
            "macos": ["auto"],
            "windows": ["copy"],
        },
        "contract_cases": [
            "cursor-instructions",
            "cursor-skills",
            "cursor-mcp",
        ],
    }

    with pytest.raises(AssertionError, match="snapshot"):
        validate_mapped_outputs_have_snapshots(contract)
