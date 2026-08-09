"""MCP source parsing, adapter transforms, and diagnostic redaction."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]
SECRET_KEY_PATTERN = re.compile(r"(token|secret|password|api[_-]?key|authorization)", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(r"(fixture-secret-token|bearer\s+\S+)", re.IGNORECASE)


class McpConfigError(ValueError):
    """Raised when `.mcp.json` cannot be parsed as a supported MCP source."""


@dataclass(frozen=True)
class McpConfig:
    """Parsed MCP configuration using the common `mcpServers` shape."""

    servers: Mapping[str, JsonObject]


def load_mcp_config(path: Path) -> McpConfig:
    """Load and validate a project MCP source file."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise McpConfigError(f"invalid MCP JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise McpConfigError("MCP config must be a JSON object")
    servers = payload.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise McpConfigError("MCP config field mcpServers must be an object")
    normalized: dict[str, JsonObject] = {}
    for name, server in sorted(servers.items()):
        if not isinstance(name, str) or not name:
            raise McpConfigError("MCP server names must be non-empty strings")
        if not isinstance(server, dict):
            raise McpConfigError(f"MCP server {name} must be an object")
        normalized[name] = dict(server)
    return McpConfig(servers=normalized)


def cursor_json(servers: Mapping[str, Mapping[str, Any]]) -> str:
    """Render Cursor MCP config as stable JSON."""

    payload = {"mcpServers": _sorted_json_object(servers)}
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def codex_toml(servers: Mapping[str, Mapping[str, Any]]) -> str:
    """Render Codex project MCP config as stable TOML text."""

    lines: list[str] = []
    for name in sorted(servers):
        if lines:
            lines.append("")
        lines.append(f"[mcp_servers.{json.dumps(name)}]")
        for key, value in sorted(servers[name].items()):
            lines.append(f"{_toml_key(key)} = {_toml_value(value)}")
    return "\n".join(lines) + ("\n" if lines else "")


def redact_sensitive(value: Any, *, parent_key: str = "") -> Any:
    """Recursively replace credential-looking values for logs and diagnostics."""

    if SECRET_KEY_PATTERN.search(parent_key):
        return "<REDACTED>"
    if isinstance(value, dict):
        return {
            str(key): redact_sensitive(item, parent_key=str(key)) for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(item, parent_key=parent_key) for item in value]
    if isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        return "<REDACTED>"
    return value


def _sorted_json_object(value: Mapping[str, Mapping[str, Any]]) -> dict[str, JsonObject]:
    """Copy nested mapping keys into deterministic insertion order."""

    result: dict[str, JsonObject] = {}
    for name in sorted(value):
        server = value[name]
        result[name] = {str(key): server[key] for key in sorted(server)}
    return result


def _toml_key(key: str) -> str:
    """Return a TOML bare key when safe, otherwise a quoted key."""

    if re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return key
    return json.dumps(key)


def _toml_value(value: Any) -> str:
    """Render the limited TOML value shapes needed for MCP server config."""

    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = [f"{_toml_key(str(key))} = {_toml_value(value[key])}" for key in sorted(value)]
        return "{ " + ", ".join(parts) + " }"
    if value is None:
        raise McpConfigError("TOML output does not support null values")
    raise McpConfigError(f"unsupported TOML value type: {type(value).__name__}")
