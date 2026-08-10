"""Interactive Agent selection helpers for the default enable command."""

from __future__ import annotations

import sys

from agent21.adapters import REGISTRY
from agent21.models import REGISTERED_AGENTS
from agent21.scanner import detect_agents


def installed_names() -> tuple[str, ...]:
    """Return Agent names whose CLI executable is available on PATH."""

    detected = detect_agents()
    return tuple(
        agent
        for agent in REGISTERED_AGENTS
        if detected.get(agent, False)
        and REGISTRY.get(agent) is not None
        and REGISTRY[agent].capability.executable is not None
    )


def parse_selection(text: str, names: tuple[str, ...]) -> tuple[str, ...]:
    """Parse comma-separated 1-based indices into a unique selected-name tuple.

    空白输入返回空元组（由调用方解释为"全部"或"保持现状"）；非法编号抛
    ValueError 提示重新输入；重复编号去重。
    """

    stripped = text.strip()
    if not stripped:
        return ()
    selected: list[str] = []
    for token in stripped.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            index = int(token)
        except ValueError as exc:
            raise ValueError(f"invalid selection: {token}") from exc
        if index < 1 or index > len(names):
            raise ValueError(f"invalid selection: {token}")
        name = names[index - 1]
        if name not in selected:
            selected.append(name)
    return tuple(selected)


def render_selection_list(enabled: set[str]) -> tuple[str, tuple[str, ...]]:
    """渲染交互选择列表，返回 (列表文本, 全部候选名)。"""

    installed = set(installed_names())
    lines = ["可用 Agent："]
    names: list[str] = []
    for index, agent in enumerate(REGISTERED_AGENTS, start=1):
        marks: list[str] = []
        if agent in enabled:
            marks.append("[已启用]")
        if agent in installed:
            marks.append("[已安装]")
        suffix = f" {' '.join(marks)}" if marks else ""
        lines.append(f"  {index}. {agent}{suffix}")
        names.append(agent)
    lines.append("选择要启用的 Agent（编号逗号分隔，留空=全部）：")
    return "\n".join(lines), tuple(names)


def select_agents_interactive(enabled: set[str]) -> tuple[str, ...]:
    """在 TTY 交互选择要启用的 Agent，返回所选名称；Ctrl+C 抛 KeyboardInterrupt。"""

    prompt, names = render_selection_list(enabled)
    print(prompt)
    while True:
        try:
            raw = input()
        except EOFError as exc:
            raise KeyboardInterrupt from exc
        try:
            return parse_selection(raw, names)
        except ValueError as exc:
            print(f"error: {exc}; please retry")
            continue


def is_tty() -> bool:
    """Whether stdin is an interactive terminal."""

    return sys.stdin.isatty()
