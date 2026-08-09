"""OpenCode adapter MCP transform tests."""

from __future__ import annotations

import json

import pytest

from agent21.adapters.opencode import capability, plan
from agent21.adapters.protocol import AdapterContext
from agent21.models import ArtifactMode, CapabilityStatus

pytestmark = pytest.mark.adapter


def test_opencode_plans_stable_mcp_transform() -> None:
    """OpenCode receives one deterministic project configuration file."""

    artifacts = plan(
        AdapterContext(
            mcp_servers={
                "remote": {"url": "https://example.test/mcp", "headers": {"X-Key": "v"}},
                "local": {"command": "npx", "args": ["-y", "server"], "env": {"A": "b"}},
            }
        )
    )

    assert capability.mcp is CapabilityStatus.TRANSFORM
    assert len(artifacts) == 1
    assert artifacts[0].target == "opencode.json"
    assert artifacts[0].mode is ArtifactMode.TRANSFORM
    payload = json.loads(artifacts[0].content or b"")
    assert payload["mcp"]["local"]["command"] == ["npx", "-y", "server"]
    assert payload["mcp"]["remote"]["type"] == "remote"
    assert artifacts[0].content == (
        b'{\n  "$schema": "https://opencode.ai/config.json",\n  "mcp": {\n'
        b'    "local": {\n      "command": [\n        "npx",\n        "-y",\n'
        b'        "server"\n      ],\n      "environment": {\n        "A": "b"\n'
        b'      },\n      "type": "local"\n    },\n    "remote": {\n'
        b'      "headers": {\n        "X-Key": "v"\n      },\n'
        b'      "type": "remote",\n      "url": "https://example.test/mcp"\n'
        b"    }\n  }\n}\n"
    )


def test_opencode_empty_mcp_has_no_output() -> None:
    """An absent optional MCP source must not create redundant config."""

    assert plan(AdapterContext()) == ()
