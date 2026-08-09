# MVP Agent Adapter Matrix

| Agent | Detect | Instructions | Skills | MCP | Managed outputs |
| --- | --- | --- | --- | --- | --- |
| Claude Code | `claude` | compatible | compatible | native | `CLAUDE.md`；可选 `.claude/skills` link/copy |
| Codex CLI | `codex` | native | native | transform | `.codex/config.toml` |
| Cursor | `cursor` | native | native | transform | `.cursor/mcp.json` |
| OpenCode | `opencode` | native | native | unsupported | none |
| Pi | `pi` | native | native | unsupported | none |

Rules:

- native 不生成冗余产物，只由 doctor 验证权威源存在。
- compatible 只生成客户端确认需要的最小路径。
- transform 必须由稳定契约测试覆盖完整目标内容。
- unsupported 作为明确状态输出，不得伪装通过或自动安装第三方扩展。
- 未安装 executable 只影响环境提示，不改变用户显式启用状态。
