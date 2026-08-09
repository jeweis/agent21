"""确定性文件树基线测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.adapter_contracts import approved_baseline_name, stable_file_tree

pytestmark = pytest.mark.snapshot


def test_file_tree_baseline_is_sorted_and_path_normalized(tmp_path: Path) -> None:
    """文件树基线必须消除创建顺序和平台分隔符差异。"""
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "two.txt").write_text("two\n", encoding="utf-8")
    (tmp_path / "a.txt").write_text("one\n", encoding="utf-8")

    assert stable_file_tree(tmp_path) == "file:a.txt\nfile:b/two.txt"


def test_approved_baseline_name_uses_stable_contract_parts() -> None:
    """基线文件名由用例、格式和契约版本组成，便于评审追踪。"""
    assert approved_baseline_name("cursor-mcp", "json", "1.0") == "cursor-mcp__json__v1_0.snap"
