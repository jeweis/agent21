# Agent Adapter Matrix: 扩展 Agent 支持

| Agent | Detect | Instructions | Skills | MCP | Managed outputs |
| --- | --- | --- | --- | --- | --- |
| Claude Code | `claude` | compatible | compatible | native | `CLAUDE.md`, `.claude/skills` |
| Codex CLI | `codex` | native | native | transform | `.codex/config.toml` |
| Cursor | `cursor` | native | native | transform | `.cursor/mcp.json` |
| OpenCode | `opencode` | native | native | transform | `opencode.json` |
| Pi | `pi` + `pi-mcp-adapter` for MCP | native | native | compatible | none |
| WorkBuddy | configuration-only | compatible | compatible | native | `.codebuddy/rules/agent21.md`, `.codebuddy/skills` |
| Qoder | `qodercli` | native | compatible | native | `.qoder/skills` |

## Rules

- native 能力直接复用权威源，不生成冗余输出。
- compatible 映射只生成目标工具必需的最小文件或目录；Pi MCP compatible 由显式第三方依赖消费根配置。
- transform 必须逐字段验证并具有稳定快照；不能表达的字段必须阻止该转换。
- configuration-only Agent 不参与默认自动检测，但被用户显式启用后必须生成项目配置。
- 缺失可选依赖只影响对应能力，不得伪装成功或阻断同一 Agent 的其他原生能力。
