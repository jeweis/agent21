"""兼容映射与转换输出的稳定基线策略测试。"""

from __future__ import annotations

import pytest

from tests.support.adapter_contracts import (
    load_adapter_contracts,
    validate_mapped_outputs_have_snapshots,
)

pytestmark = [pytest.mark.adapter, pytest.mark.snapshot]


def test_mapped_outputs_require_baselines_when_outputs_exist() -> None:
    """外部直接消费无需快照，实际映射或转换输出必须有稳定基线。"""
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
