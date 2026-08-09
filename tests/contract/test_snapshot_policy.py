"""快照更新策略契约测试。"""

from __future__ import annotations

import pytest

from tests.conftest import snapshot_update_block_reason

pytestmark = pytest.mark.contract


def test_ci_forbids_snapshot_update_flag() -> None:
    """CI 环境中出现快照更新参数必须被阻断。"""
    reason = snapshot_update_block_reason(is_ci=True, update_requested=True)

    assert reason is not None
    assert "--snapshot-update" in reason
    assert "CI" in reason


def test_local_explicit_snapshot_update_is_allowed() -> None:
    """本地只有显式传参时才允许更新快照。"""
    assert snapshot_update_block_reason(is_ci=False, update_requested=True) is None
    assert snapshot_update_block_reason(is_ci=False, update_requested=False) is None
