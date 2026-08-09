"""原生能力不得生成冗余第二真源的契约测试。"""

from __future__ import annotations

import pytest

from tests.support.adapter_contracts import (
    load_adapter_contracts,
    validate_native_output_policy,
)

pytestmark = pytest.mark.adapter


def test_planned_native_capabilities_have_no_redundant_outputs() -> None:
    """planned fixture 当前不声明托管输出，因此不会伪造原生产物。"""
    for contract in load_adapter_contracts():
        validate_native_output_policy(contract)


def test_native_capability_rejects_duplicate_authoritative_file() -> None:
    """原生能力不能把权威输入再复制成另一个托管输出。"""
    contract = {
        "schema_version": "1.0",
        "agent": "codex-cli",
        "status": "implemented",
        "capabilities": {
            "instructions": {"mode": "native"},
            "skills": {"mode": "unsupported"},
            "mcp": {"mode": "unsupported"},
        },
        "source_inputs": ["AGENTS.md"],
        "managed_outputs": [
            {
                "path": ".codex/AGENTS.md",
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
        "contract_cases": ["codex-cli-instructions"],
    }

    with pytest.raises(AssertionError, match="native"):
        validate_native_output_policy(contract)
