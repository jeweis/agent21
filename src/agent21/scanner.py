"""Executable discovery for supported AI coding agents."""

from __future__ import annotations

import shutil

from agent21.models import REGISTERED_AGENTS

EXECUTABLES: dict[str, str] = {
    "claude": "claude",
    "codex": "codex",
    "cursor": "cursor",
    "opencode": "opencode",
    "pi": "pi",
    "qoder": "qodercli",
}


def detect_agents() -> dict[str, bool]:
    """Return supported Agent executable availability in stable name order."""

    detected = {
        agent: shutil.which(command) is not None for agent, command in sorted(EXECUTABLES.items())
    }
    return {agent: detected.get(agent, False) for agent in REGISTERED_AGENTS}


def executable_available(command: str) -> bool:
    """Check an executable without invoking third-party code."""

    return shutil.which(command) is not None
