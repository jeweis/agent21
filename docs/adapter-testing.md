# Adapter Testing

Agent21 的适配器测试以 `specs/001-test-infrastructure/contracts/adapter-matrix.md`
为权威矩阵，以 `tests/fixtures/adapter_contracts/*.json` 为可执行契约资产。
Claude Code、Codex CLI、Cursor、OpenCode、Pi、WorkBuddy 和 Qoder 均为 `implemented`。

## MVP Capability Mapping

- Claude Code：`CLAUDE.md` 与 `.claude/skills` 为受管兼容输出，根 `.mcp.json` 原生复用。
- Codex CLI：原生读取 `AGENTS.md`/`.agents/skills`，MCP 转换为 `.codex/config.toml`。
- Cursor：原生读取指令/Skills，MCP 转换为 `.cursor/mcp.json`。
- OpenCode：原生复用指令/Skills，MCP 转换为项目 `opencode.json`。
- Pi：原生复用指令/Skills，`pi-mcp-adapter` 直接消费根 `.mcp.json`，Agent21 仅检测依赖。
- WorkBuddy：根目录无 `CODEBUDDY.md` 时原生读取 `AGENTS.md`，原生读取根 MCP，仅映射
  `.codebuddy/skills`；遮蔽文件由 doctor 阻断。
- Qoder：原生复用指令/MCP，仅映射 `.qoder/skills`。

运行时 registry 使用 `claude`、`codex`、`cursor`、`opencode`、`pi`、`workbuddy`、`qoder` 稳定 slug；
测试 fixture 可保留面向用户的产品展示名。

## Promotion Flow

将适配器从 `planned` 提升为 `implemented` 时，需要同一变更完成：

1. 更新矩阵状态和能力分类。
2. 更新对应 JSON 契约，并保持 schema 校验通过。
3. 为每个非 `unsupported` 能力添加 `<agent>-<capability>` 用例。
4. 原生能力证明复用权威输入，不生成同名冗余托管副本。
5. `compatible` 或 `transform` 若生成托管输出，必须声明纳入快照；直接消费权威源的外部兼容层无需伪造快照。

## Baseline Review

稳定输出基线只覆盖用户可见且确定性的内容。路径、换行和临时根必须在比较前规范化；
未批准漂移应让测试失败并展示差异。CI 不允许自动更新快照。

目标验证命令：

```bash
uv run pytest -m "adapter or contract or snapshot"
```
