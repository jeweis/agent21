"""pytest 级测试配置、marker 注册和快照安全策略。"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

MARKERS = {
    "unit": "无文件工作流的最小逻辑。",
    "adapter": "单一 Agent 适配器输入输出契约。",
    "contract": "公共 CLI、配置 schema 或版本化格式契约。",
    "integration": "在隔离项目中组合多个组件。",
    "e2e": "安装后通过 subprocess 调用真实 CLI。",
    "compatibility": "平台、Python 版本或同步模式差异。",
    "snapshot": "需要稳定输出基线。",
    "safety": "未托管文件、路径边界、权限或敏感信息验证。",
    "slow": "不进入默认快速子集的高成本验证。",
}


def pytest_configure(config: pytest.Config) -> None:
    """注册严格 marker 所需的描述，并阻断 CI 自动更新快照。"""
    for name, description in MARKERS.items():
        config.addinivalue_line("markers", f"{name}: {description}")

    reason = snapshot_update_block_reason(
        is_ci=_env_flag("CI"),
        update_requested=bool(config.getoption("--snapshot-update", default=False)),
    )
    if reason:
        raise pytest.UsageError(reason)


def snapshot_update_block_reason(
    *,
    is_ci: bool,
    update_requested: bool,
) -> str | None:
    """返回快照更新被阻断的原因；允许时返回 None。"""
    if is_ci and update_requested:
        return "CI must not run with --snapshot-update; review snapshots locally."
    return None


def normalize_snapshot_value(value: Any, *, temp_root: Path | None = None) -> Any:
    """规范化快照值中的换行、路径分隔符和临时根。"""
    if isinstance(value, str):
        normalized = value.replace("\r\n", "\n").replace("\\", "/")
        if temp_root is not None:
            normalized = normalized.replace(str(temp_root).replace("\\", "/"), "<TMP>")
        return normalized
    if isinstance(value, list):
        return [normalize_snapshot_value(item, temp_root=temp_root) for item in value]
    if isinstance(value, dict):
        return {
            key: normalize_snapshot_value(item, temp_root=temp_root)
            for key, item in sorted(value.items())
        }
    return value


@pytest.fixture
def normalized_snapshot() -> Callable[..., Any]:
    """提供测试内可复用的快照规范化函数。"""
    return normalize_snapshot_value


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}
