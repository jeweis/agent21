# MCP Mapping Contract

## Authority

`.mcp.json` 的 `mcpServers` 是唯一项目级服务器清单。WorkBuddy、Qoder 和安装 adapter 后的 Pi 直接消费它；
OpenCode 生成工具专用视图。

## OpenCode local server

Source:

```json
{
  "command": "npx",
  "args": ["-y", "server"],
  "env": {"TOKEN": "${TOKEN}"},
  "cwd": ".",
  "disabled": false,
  "timeout": 5000
}
```

Target entry under `opencode.json:mcp.<name>`:

```json
{
  "type": "local",
  "command": ["npx", "-y", "server"],
  "environment": {"TOKEN": "${TOKEN}"},
  "cwd": ".",
  "enabled": true,
  "timeout": 5000
}
```

## OpenCode remote server

Source:

```json
{
  "url": "https://example.test/mcp",
  "headers": {"Authorization": "Bearer ${TOKEN}"},
  "disabled": false,
  "timeout": 5000
}
```

Target:

```json
{
  "type": "remote",
  "url": "https://example.test/mcp",
  "headers": {"Authorization": "Bearer ${TOKEN}"},
  "enabled": true,
  "timeout": 5000
}
```

## Validation and errors

- 一个服务器必须恰有 `command` 或 `url`。
- `args` 只能是字符串数组；`env`/`headers` 只能是字符串映射。
- local 接受 `command,args,env,cwd,disabled,timeout`；remote 接受 `url,headers,disabled,timeout`。
- 其他字段不得静默丢弃，错误格式为 `MCP server <name> field <field> is unsupported for OpenCode`。
- 类型错误只报告服务器名、字段名和预期类型，不报告实际敏感值。
- 服务器和字段按名称排序；输出 UTF-8、两个空格缩进、单个末尾换行。
- 空 `mcpServers` 不创建 `opencode.json`。

## Pi compatibility dependency

- Package: `pi-mcp-adapter`
- User-authorized install command: `pi install npm:pi-mcp-adapter`
- Detection command name: `pi-mcp-adapter`
- Preferred project config: `.mcp.json`
- Agent21 不调用 adapter、不连接服务器、不写 `.pi/mcp.json`。
