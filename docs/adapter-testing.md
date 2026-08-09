# Adapter Testing

Agent21 的适配器测试以 `specs/001-test-infrastructure/contracts/adapter-matrix.md`
为权威矩阵，以 `tests/fixtures/adapter_contracts/*.json` 为可执行契约资产。
Claude Code、Codex CLI、Cursor、OpenCode 和 Pi 已提升为 `implemented`；
WorkBuddy 和 Qoder 仍为后续路线图，不计入 MVP 支持率。

## MVP Capability Mapping

- Claude Code：`CLAUDE.md` 与 `.claude/skills` 为受管兼容输出，根 `.mcp.json` 原生复用。
- Codex CLI：原生读取 `AGENTS.md`/`.agents/skills`，MCP 转换为 `.codex/config.toml`。
- Cursor：原生读取指令/Skills，MCP 转换为 `.cursor/mcp.json`。
- OpenCode、Pi：原生复用指令/Skills，MVP 对 MCP 明确报告 `unsupported`。

运行时 registry 使用 `claude`、`codex`、`cursor`、`opencode`、`pi` 稳定 slug；
测试 fixture 可保留面向用户的产品展示名。

## Promotion Flow

将适配器从 `planned` 提升为 `implemented` 时，需要同一变更完成：

1. 更新矩阵状态和能力分类。
2. 更新对应 JSON 契约，并保持 schema 校验通过。
3. 为每个非 `unsupported` 能力添加 `<agent>-<capability>` 用例。
4. 原生能力证明复用权威输入，不生成同名冗余托管副本。
5. `compatible` 或 `transform` 输出必须声明纳入快照的托管产物。

## Baseline Review

稳定输出基线只覆盖用户可见且确定性的内容。路径、换行和临时根必须在比较前规范化；
未批准漂移应让测试失败并展示差异。CI 不允许自动更新快照。

目标验证命令：

```bash
uv run pytest -m "adapter or contract or snapshot"
```
