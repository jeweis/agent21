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


def test_only_promoted_mvp_adapters_count_as_implemented() -> None:
    """五个已验证 MVP adapter 进入通过率，路线图 adapter 仍被排除。"""
    contracts = load_adapter_contracts()

    assert {contract["agent"] for contract in implemented_contracts(contracts)} == {
        "claude-code",
        "codex-cli",
        "cursor",
        "opencode",
        "pi",
    }
    assert {contract["agent"] for contract in contracts if contract["status"] == "planned"} == {
        "qoder",
        "workbuddy",
    }


def test_contract_status_and_capabilities_match_matrix() -> None:
    """契约 fixture 的状态与能力分类必须逐项匹配矩阵。"""
    matrix = load_adapter_matrix()

    for contract in load_adapter_contracts():
        validate_contract_against_matrix(contract, matrix[contract["agent"]])
