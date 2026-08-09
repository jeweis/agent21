"""Qoder project capability tests."""

from __future__ import annotations

import pytest

from agent21.adapters.protocol import AdapterContext
from agent21.adapters.qoder import capability, plan
from agent21.models import ArtifactMode, CapabilityStatus

pytestmark = pytest.mark.adapter


def test_qoder_only_maps_project_skills() -> None:
    """Qoder reads root instructions/MCP and only needs a Skills mapping."""

    artifacts = plan(AdapterContext(sync_mode=ArtifactMode.COPY))

    assert capability.executable == "qodercli"
    assert capability.instructions is CapabilityStatus.NATIVE
    assert capability.mcp is CapabilityStatus.NATIVE
    assert [artifact.target for artifact in artifacts] == [".qoder/skills"]
