"""已实现适配器的语义覆盖测试。"""

from __future__ import annotations

import pytest

from tests.support.adapter_contracts import (
    load_adapter_contracts,
    validate_implemented_semantics,
)

pytestmark = pytest.mark.adapter


def test_planned_contracts_are_exempt_from_semantic_coverage() -> None:
    """planned 只登记目标，不要求能力用例覆盖。"""
    for contract in load_adapter_contracts():
        validate_implemented_semantics(contract)


def test_implemented_supported_capabilities_need_cases() -> None:
    """implemented 的每个非 unsupported 能力必须至少有一个用例。"""
    contract = {
        "schema_version": "1.0",
        "agent": "codex-cli",
        "status": "implemented",
        "capabilities": {
            "instructions": {"mode": "native"},
            "skills": {"mode": "native"},
            "mcp": {"mode": "transform"},
        },
        "source_inputs": ["AGENTS.md", ".agents/skills/example/SKILL.md"],
        "managed_outputs": [
            {
                "path": ".codex/mcp.json",
                "kind": "file",
                "managed": True,
                "snapshot": True,
            }
        ],
        "platform_modes": {
            "linux": ["auto"],
            "macos": ["auto"],
            "windows": ["copy"],
        },
        "contract_cases": ["codex-cli-instructions", "codex-cli-skills"],
    }

    with pytest.raises(AssertionError, match="mcp"):
        validate_implemented_semantics(contract)
