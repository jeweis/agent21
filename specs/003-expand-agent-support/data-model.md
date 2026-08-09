# Data Model: 扩展 Agent 支持

本功能沿用现有 dataclass 与稳定 YAML/JSON/TOML/Markdown 输出。所有托管路径仍为项目相对 POSIX 字符串。

## ProjectConfig

| Field | Type | Rules |
| --- | --- | --- |
| `schema_version` | integer | 保持 `1` |
| `agents` | map<string, AgentSelection> | 只允许七个登记 slug；稳定排序 |
| `sync_mode` | enum | `auto`、`copy`、`symlink` |
| `instructions_source` | path | 默认 `AGENTS.md` |
| `skills_source` | path | 默认 `.agents/skills` |
| `mcp_source` | path | 默认 `.mcp.json` |

### Agent 集合与迁移

```text
legacy required: claude, codex, cursor, opencode, pi
additive optional: workbuddy, qoder
normalized runtime: all seven keys; missing additive keys => enabled=false
serialized new config: all seven keys in stable order
unknown key: rejected
```

## AgentCapability

| Field | Type | Rules |
| --- | --- | --- |
| `agent` | slug | 七个登记 Agent 之一 |
| `instructions` | capability enum | native/compatible/transform/unsupported |
| `skills` | capability enum | 同上 |
| `mcp` | capability enum | 同上 |
| `implemented` | boolean | 契约和测试均存在时为 true |
| `executable` | string/null | `null` 表示 configuration-only，不以 CLI availability 阻止同步 |
| `mcp_dependency` | DependencyRequirement/null | Pi 使用，其他 Agent 为空 |

## DependencyRequirement

非持久化 adapter 元数据，不进入 manifest。

| Field | Type | Rules |
| --- | --- | --- |
| `executable` | string | 稳定、无 shell 的命令名，例如 `pi-mcp-adapter` |
| `install_hint` | string | 静态修复命令，不含凭证 |
| `required_for` | capability | 当前仅 MCP |

### Dependency states

```text
not-applicable -> no diagnostic
detectable     -> info; adapter is discoverable but runtime compatibility is not asserted
missing        -> unsupported/skipped with install hint
```

依赖检测只检查命令是否存在，不运行命令、不读取版本输出、不安装包。

## McpConfig / McpServer

`McpConfig` 保持权威 `mcpServers` 映射。OpenCode 转换为每服务器验证，Pi/WorkBuddy/Qoder 直接复用权威文件。

| Source shape | Validation | OpenCode target |
| --- | --- | --- |
| `command: string` + optional `args: string[]` | command 非空、args 仅字符串 | `type: local`, `command: [command, ...args]` |
| optional `env: object<string,string>` | key/value 均为字符串 | `environment` |
| optional `cwd: string` | 非空项目/命令工作目录文本 | `cwd` |
| `url: string` + optional `headers` | url 非空、headers 为字符串映射 | `type: remote`, `url`, `headers` |
| optional `disabled: boolean` | 必须为 boolean | `enabled: !disabled` |
| optional `timeout: number` | 正数 | `timeout` |

`command` 与 `url` 互斥且必须有一个。未知或目标不支持字段在 OpenCode 转换时产生错误，错误仅包含服务器名和字段名。

## PlannedArtifact additions

| Agent | Target | Kind | Mode | Source |
| --- | --- | --- | --- | --- |
| OpenCode | `opencode.json` | file | transform | `.mcp.json` |
| WorkBuddy | `.codebuddy/rules/agent21.md` | file | copy | `AGENTS.md` |
| WorkBuddy | `.codebuddy/skills` | directory/symlink | copy/symlink | `.agents/skills` |
| Qoder | `.qoder/skills` | directory/symlink | copy/symlink | `.agents/skills` |

Pi、WorkBuddy MCP、Qoder instructions/MCP 和 OpenCode instructions/Skills 为 native/compatible-without-output，不创建 artifact。

## HealthCheckResult additions

| Check ID | Subject | Status |
| --- | --- | --- |
| `agent.executable` | qoder 等 CLI Agent | info/unsupported |
| `agent.configuration` | workbuddy | info，说明 installation 不可由 CLI 确认 |
| `agent.dependency` | `pi:pi-mcp-adapter` | pass/unsupported |
| `artifact.drift` | 新增托管目标 | pass/blocked |

## Relationships

```text
ProjectConfig 1 --- 7 AgentSelection
AgentCapability 0..1 --- 1 DependencyRequirement
AgentAdapter 1 --- * PlannedArtifact
McpConfig 1 --- * McpServer
McpServer 1 --- 0..1 OpenCodeMcpEntry
Manifest 1 --- * ManagedArtifact
Doctor 1 --- * HealthCheckResult
```
