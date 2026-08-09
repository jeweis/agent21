"""适配器矩阵状态规则测试。"""

from __future__ import annotations

import pytest

from tests.support.adapter_contracts import (
    implemented_contracts,
    load_adapter_contracts,
    load_adapter_matrix,
    validate_contract_against_matrix,
)

pytestmark = pytest.mark.adapter


def test_all_seven_adapters_count_as_implemented() -> None:
    """七个已验证 adapter 全部进入契约通过率。"""
    contracts = load_adapter_contracts()

    assert {contract["agent"] for contract in implemented_contracts(contracts)} == {
        "claude-code",
        "codex-cli",
        "cursor",
        "opencode",
        "pi",
        "qoder",
        "workbuddy",
    }
    assert not {contract["agent"] for contract in contracts if contract["status"] == "planned"}


def test_contract_status_and_capabilities_match_matrix() -> None:
    """契约 fixture 的状态与能力分类必须逐项匹配矩阵。"""
    matrix = load_adapter_matrix()

    for contract in load_adapter_contracts():
        validate_contract_against_matrix(contract, matrix[contract["agent"]])
