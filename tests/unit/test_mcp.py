"""Unit tests for MCP parsing, transforms, and redaction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent21.mcp import (
    McpConfigError,
    codex_toml,
    cursor_json,
    load_mcp_config,
    opencode_json,
    redact_sensitive,
)


def test_load_mcp_config_accepts_mcp_servers_object(tmp_path: Path) -> None:
    """MCP source files use the common mcpServers object shape."""

    source = tmp_path / ".mcp.json"
    source.write_text(
        json.dumps({"mcpServers": {"filesystem": {"command": "npx", "args": ["-y"]}}}),
        encoding="utf-8",
    )

    config = load_mcp_config(source)

    assert list(config.servers) == ["filesystem"]
    assert config.servers["filesystem"]["command"] == "npx"


def test_load_mcp_config_rejects_non_object_servers(tmp_path: Path) -> None:
    """Invalid source shape fails before adapter transforms."""

    source = tmp_path / ".mcp.json"
    source.write_text(json.dumps({"mcpServers": []}), encoding="utf-8")

    with pytest.raises(McpConfigError, match="mcpServers"):
        load_mcp_config(source)


def test_codex_toml_transforms_servers_in_stable_order() -> None:
    """Codex receives project TOML with sorted mcp_servers tables."""

    content = codex_toml(
        {
            "zeta": {"command": "z", "args": ["--flag"]},
            "alpha": {"command": "a", "env": {"TOKEN": "fixture-secret-token"}},
        }
    )

    assert content.index('[mcp_servers."alpha"]') < content.index('[mcp_servers."zeta"]')
    assert 'command = "a"' in content
    assert 'args = ["--flag"]' in content
    assert 'env = { TOKEN = "fixture-secret-token" }' in content


def test_cursor_json_preserves_mcp_servers_shape_with_stable_sorting() -> None:
    """Cursor receives deterministic JSON using the common MCP key."""

    content = cursor_json(
        {
            "zeta": {"command": "z"},
            "alpha": {"command": "a"},
        }
    )

    assert content == (
        "{\n"
        '  "mcpServers": {\n'
        '    "alpha": {\n'
        '      "command": "a"\n'
        "    },\n"
        '    "zeta": {\n'
        '      "command": "z"\n'
        "    }\n"
        "  }\n"
        "}\n"
    )


def test_opencode_json_maps_local_and_remote_servers() -> None:
    """OpenCode mapping preserves every supported observable server field."""

    content = opencode_json(
        {
            "local": {
                "command": "npx",
                "args": ["-y", "tool"],
                "env": {"TOKEN": "value"},
                "cwd": "subdir",
                "disabled": True,
                "timeout": 10,
            },
            "remote": {
                "url": "https://example.test/mcp",
                "headers": {"Authorization": "Bearer value"},
            },
        }
    )
    payload = json.loads(content)

    assert payload["mcp"]["local"] == {
        "command": ["npx", "-y", "tool"],
        "cwd": "subdir",
        "enabled": False,
        "environment": {"TOKEN": "value"},
        "timeout": 10,
        "type": "local",
    }
    assert payload["mcp"]["remote"]["headers"]["Authorization"] == "Bearer value"


@pytest.mark.parametrize(
    "server",
    [
        {"command": "tool", "unknown": True},
        {"command": "tool", "url": "https://example.test"},
        {"command": "tool", "args": [1]},
        {"url": "https://example.test", "env": {"A": "b"}},
    ],
)
def test_opencode_json_rejects_unrepresentable_fields(server: dict[str, object]) -> None:
    """Target-incompatible values fail instead of being silently discarded."""

    with pytest.raises(McpConfigError, match="MCP server demo"):
        opencode_json({"demo": server})


def test_redact_sensitive_removes_secret_values_recursively() -> None:
    """Diagnostics keep keys visible while removing credential-looking values."""

    redacted = redact_sensitive(
        {
            "mcpServers": {
                "svc": {
                    "env": {
                        "API_KEY": "fixture-secret-token",
                        "PATH": "/usr/bin",
                    },
                    "headers": {"Authorization": "Bearer fixture-secret-token"},
                }
            }
        }
    )

    assert redacted["mcpServers"]["svc"]["env"]["API_KEY"] == "<REDACTED>"
    assert redacted["mcpServers"]["svc"]["env"]["PATH"] == "/usr/bin"
    assert redacted["mcpServers"]["svc"]["headers"]["Authorization"] == "<REDACTED>"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "JSON object"),
        ({"mcpServers": {"": {}}}, "names"),
        ({"mcpServers": {"demo": []}}, "must be an object"),
    ],
)
def test_load_mcp_config_rejects_invalid_root_and_server_shapes(
    tmp_path: Path, payload: object, message: str
) -> None:
    """Every MCP root, name, and server entry has an explicit structural contract."""

    source = tmp_path / ".mcp.json"
    source.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(McpConfigError, match=message):
        load_mcp_config(source)


def test_codex_toml_supports_scalar_inline_table_and_quoted_keys() -> None:
    """The supported MCP subset renders deterministic TOML value shapes."""

    content = codex_toml(
        {
            "demo": {
                "enabled": True,
                "timeout": 3,
                "ratio": 1.5,
                "odd key": "value",
                "env": {"A": "b"},
            }
        }
    )

    assert "enabled = true" in content
    assert "timeout = 3" in content
    assert "ratio = 1.5" in content
    assert '"odd key" = "value"' in content
    assert 'env = { A = "b" }' in content


@pytest.mark.parametrize("value", [None, {"bad": None}])
def test_codex_toml_rejects_null_values(value: object) -> None:
    """Null values are rejected instead of generating invalid TOML."""

    with pytest.raises(McpConfigError, match="null"):
        codex_toml({"demo": {"value": value}})


def test_redact_sensitive_handles_lists_and_secret_like_values() -> None:
    """Secret values nested in arrays are redacted while ordinary scalars remain intact."""

    assert redact_sensitive(["Bearer abc", 42, "safe"]) == ["<REDACTED>", 42, "safe"]
