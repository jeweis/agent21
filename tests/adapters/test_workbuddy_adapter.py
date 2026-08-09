"""WorkBuddy `.codebuddy` compatibility tests."""

from __future__ import annotations

import pytest

from agent21.adapters.protocol import AdapterContext
from agent21.adapters.workbuddy import capability, plan
from agent21.models import ArtifactMode, CapabilityStatus

pytestmark = pytest.mark.adapter


def test_workbuddy_uses_codebuddy_project_paths() -> None:
    """WorkBuddy maps rules and Skills while reusing root MCP natively."""

    artifacts = plan(AdapterContext(sync_mode=ArtifactMode.SYMLINK))

    assert capability.executable is None
    assert capability.mcp is CapabilityStatus.NATIVE
    assert [artifact.target for artifact in artifacts] == [
        ".codebuddy/rules/agent21.md",
        ".codebuddy/skills",
    ]
    assert artifacts[0].mode is ArtifactMode.COPY
    assert artifacts[1].mode is ArtifactMode.SYMLINK
