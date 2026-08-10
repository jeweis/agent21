"""Unit tests for interactive Agent selection parsing."""

from __future__ import annotations

import pytest

from agent21.selection import parse_selection

NAMES = ("claude", "codex", "cursor", "opencode", "pi", "workbuddy", "qoder")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", ()),
        ("   ", ()),
        ("1", ("claude",)),
        ("2,3", ("codex", "cursor")),
        ("7", ("qoder",)),
        ("2,2,3", ("codex", "cursor")),
        ("1, 4", ("claude", "opencode")),
        ("7,1", ("qoder", "claude")),
    ],
)
def test_parse_selection_accepts_valid_indices(text: str, expected: tuple[str, ...]) -> None:
    """逗号分隔编号被解析为唯一、有序的 Agent 名。"""

    assert parse_selection(text, NAMES) == expected


@pytest.mark.parametrize("text", ["0", "8", "abc", "1,9", "1,x"])
def test_parse_selection_rejects_invalid_input(text: str) -> None:
    """越界、非数字输入被拒绝并给出重输提示。"""

    with pytest.raises(ValueError, match="invalid selection"):
        parse_selection(text, NAMES)
