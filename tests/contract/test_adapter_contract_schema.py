"""适配器契约 JSON Schema 与 planned fixture 的契约测试。"""

from __future__ import annotations

import pytest

from tests.support.adapter_contracts import (
    load_adapter_contracts,
    load_adapter_matrix,
    validate_contract_against_matrix,
    validate_contract_schema,
)

pytestmark = pytest.mark.contract


def test_planned_adapter_contracts_match_schema_and_matrix() -> None:
    """所有 planned fixture 必须结构合法，并且与权威矩阵一致。"""
    matrix = load_adapter_matrix()
    contracts = load_adapter_contracts()

    assert {contract["agent"] for contract in contracts} == set(matrix)

    for contract in contracts:
        validate_contract_schema(contract)
        validate_contract_against_matrix(contract, matrix[contract["agent"]])
        if contract["status"] == "planned":
            assert contract["contract_cases"] == []


def test_implemented_contract_requires_at_least_one_case() -> None:
    """implemented 状态不能没有总体契约用例。"""
    contract = {
        "schema_version": "1.0",
        "agent": "codex-cli",
        "status": "implemented",
        "capabilities": {
            "instructions": {"mode": "native"},
            "skills": {"mode": "native"},
            "mcp": {"mode": "transform"},
        },
        "source_inputs": ["AGENTS.md"],
        "managed_outputs": [],
        "platform_modes": {
            "linux": ["auto"],
            "macos": ["auto"],
            "windows": ["copy"],
        },
        "contract_cases": [],
    }

    with pytest.raises(AssertionError, match="contract_cases"):
        validate_contract_schema(contract)


def test_repository_paths_reject_boundary_escape() -> None:
    """契约路径只允许仓库相对路径，避免 fixture 描述越界输出。"""
    contract = {
        "schema_version": "1.0",
        "agent": "bad-agent",
        "status": "planned",
        "capabilities": {
            "instructions": {"mode": "native"},
            "skills": {"mode": "unsupported"},
            "mcp": {"mode": "unsupported"},
        },
        "source_inputs": ["../AGENTS.md"],
        "managed_outputs": [],
        "platform_modes": {
            "linux": ["auto"],
            "macos": ["auto"],
            "windows": ["copy"],
        },
        "contract_cases": [],
    }

    with pytest.raises(AssertionError, match="repository-relative"):
        validate_contract_schema(contract)
