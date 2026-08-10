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


def opencode_json(servers: Mapping[str, Mapping[str, Any]]) -> str:
    """Render the supported MCP subset as deterministic OpenCode JSON."""

    mapped = {name: _opencode_server(name, server) for name, server in sorted(servers.items())}
    payload = {"$schema": "https://opencode.ai/config.json", "mcp": mapped}
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _opencode_server(name: str, server: Mapping[str, Any]) -> JsonObject:
    """将通用 MCP server 映射为 OpenCode 视图；其他工具的私有扩展字段被过滤。

    `.mcp.json` 是跨工具共享真源，可能包含特定工具（如 pi-mcp-adapter 的
    `directTools`）的扩展字段。这些字段不属于 OpenCode 视图，转换时忽略，
    但仍保留结构契约校验（command/url 恰一、类型与矛盾字段检查）。
    """

    has_command = "command" in server
    has_url = "url" in server
    if has_command == has_url:
        raise McpConfigError(f"MCP server {name} must define exactly one of command or url")
    _validate_transport_type(name, server)
    result = _opencode_local(name, server) if has_command else _opencode_remote(name, server)
    _copy_opencode_options(name, server, result)
    return result


def _validate_transport_type(name: str, server: Mapping[str, Any]) -> None:
    """接受可选 MCP 传输类型元数据；OpenCode 输出类型仍由 command/url 决定。"""

    value = server.get("type")
    if value is None:
        return
    if not isinstance(value, str) or not value:
        raise McpConfigError(f"MCP server {name} field type must be a non-empty string")


def _opencode_local(name: str, server: Mapping[str, Any]) -> JsonObject:
    """Map one local stdio server to OpenCode's command-array shape."""

    command = server["command"]
    args = server.get("args", [])
    if not isinstance(command, str) or not command:
        raise McpConfigError(f"MCP server {name} field command must be a non-empty string")
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise McpConfigError(f"MCP server {name} field args must be a string array")
    result: JsonObject = {"type": "local", "command": [command, *args]}
    env = server.get("env")
    if env is not None:
        result["environment"] = _string_mapping(name, "env", env)
    cwd = server.get("cwd")
    if cwd is not None:
        if not isinstance(cwd, str) or not cwd:
            raise McpConfigError(f"MCP server {name} field cwd must be a non-empty string")
        result["cwd"] = cwd
    if "headers" in server:
        raise McpConfigError(f"MCP server {name} has unsupported field: headers")
    return result


def _opencode_remote(name: str, server: Mapping[str, Any]) -> JsonObject:
    """Map one remote HTTP server to OpenCode's remote shape."""

    url = server["url"]
    if not isinstance(url, str) or not url:
        raise McpConfigError(f"MCP server {name} field url must be a non-empty string")
    result: JsonObject = {"type": "remote", "url": url}
    headers = server.get("headers")
    if headers is not None:
        result["headers"] = _string_mapping(name, "headers", headers)
    for field in ("args", "env", "cwd"):
        if field in server:
            raise McpConfigError(f"MCP server {name} has unsupported field: {field}")
    return result


def _copy_opencode_options(name: str, server: Mapping[str, Any], result: JsonObject) -> None:
    """Validate and copy options shared by local and remote OpenCode servers."""

    if "disabled" in server:
        disabled = server["disabled"]
        if type(disabled) is not bool:
            raise McpConfigError(f"MCP server {name} field disabled must be a boolean")
        result["enabled"] = not disabled
    if "timeout" in server:
        timeout = server["timeout"]
        if isinstance(timeout, bool) or not isinstance(timeout, int | float) or timeout <= 0:
            raise McpConfigError(f"MCP server {name} field timeout must be positive")
        result["timeout"] = timeout


def _string_mapping(name: str, field: str, value: Any) -> dict[str, str]:
    """Validate an MCP string-to-string mapping."""

    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise McpConfigError(f"MCP server {name} field {field} must be a string mapping")
    return {key: value[key] for key in sorted(value)}


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
