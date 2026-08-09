# CLI Contract: 扩展 Agent 支持

## Agent selection

`agent21 init --agents` 接受稳定 slug：

```text
claude,codex,cursor,opencode,pi,workbuddy,qoder
```

- 未知 slug 仍以用法有效但配置无效的错误退出。
- `workbuddy` 仅显式选择，不依赖假定 CLI 命令。
- 默认检测可启用 `qoder` 当 `qodercli` 可用。
- 旧 `.agents/config.yaml` 缺少 `workbuddy`/`qoder` 时读取成功，两者规范化为 disabled。

## Sync output

- `--dry-run` 对新目标使用既有 `created/updated/unchanged/skipped/blocked` 行格式，不写文件。
- Pi 已启用、MCP 非空且 `pi-mcp-adapter` 缺失时，输出稳定 skipped 诊断和安装动作；其他 Pi 能力保持可用。
- OpenCode 字段错误或未托管目标冲突写 stderr、退出 1，且所有相关目标在 apply 前保持不变。
- WorkBuddy configuration-only 不因缺少 CLI 被跳过。
- 输出不得包含 MCP 值、headers、env、token 或扩展凭证。

## Doctor output

- `agent.executable`: 可检测 CLI Agent 的 availability。
- `agent.configuration`: WorkBuddy 被启用时说明项目配置可同步但安装状态不可由 CLI 确认。
- `agent.dependency`: Pi MCP adapter detectable/missing；detectable 仅为 info，不声称运行成功；missing 使用
  unsupported，动作固定为 `pi install npm:pi-mcp-adapter`。
- 任何新托管输出继续使用 `artifact.drift` 检查摘要。

doctor 只有 blocked 状态时退出 1；configuration info 和 optional dependency unsupported 退出 0。
