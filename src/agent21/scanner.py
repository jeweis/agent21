"""Executable discovery for supported AI coding agents."""

from __future__ import annotations

import shutil

EXECUTABLES: dict[str, str] = {
    "claude": "claude",
    "codex": "codex",
    "cursor": "cursor",
    "opencode": "opencode",
    "pi": "pi",
}


def detect_agents() -> dict[str, bool]:
    """Return supported Agent executable availability in stable name order."""

    return {
        agent: shutil.which(command) is not None for agent, command in sorted(EXECUTABLES.items())
    }
