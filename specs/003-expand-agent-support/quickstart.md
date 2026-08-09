# Quickstart: 扩展 Agent 支持验证

## Prerequisites

- Python 3.11+
- uv
- Git
- 真实第三方 Agent 不是默认自动化验证的前置条件
- Pi 实机 MCP 冒烟需要用户显式执行 `pi install npm:pi-mcp-adapter`

## Install development environment

```bash
uv sync --locked --group dev
```

## Scenario 1: OpenCode MCP

在隔离项目初始化 OpenCode，创建同时包含 stdio 与 remote server 的根 `.mcp.json`，再执行：

```bash
agent21 init --yes --agents opencode --mode copy
agent21 sync --dry-run
agent21 sync
agent21 sync
agent21 doctor
```

Expected:

- `opencode.json` 只含 `$schema` 和确定性 `mcp` 视图。
- 第二次同步为 unchanged，无额外差异。
- 无效或未知字段在任何写入前失败。
- 既有未托管 `opencode.json` 不被覆盖。

## Scenario 2: Pi adapter

```bash
agent21 init --yes --agents pi --mode copy
agent21 sync
agent21 doctor
```

Expected when adapter is missing: 指令与 Skills 仍可用；MCP 依赖明确显示 unsupported/skipped，并给出
`pi install npm:pi-mcp-adapter`，不创建 `.pi/mcp.json`。

用户显式安装 adapter 后：

```bash
pi install npm:pi-mcp-adapter
agent21 doctor
```

Expected: dependency check 报告 adapter 可检测但不伪报运行状态；根 `.mcp.json` 保持唯一服务器来源。

## Scenario 3: WorkBuddy

```bash
agent21 init --yes --agents workbuddy --mode copy
agent21 sync --dry-run
agent21 sync
agent21 sync
agent21 doctor
```

Expected:

- 根 `AGENTS.md` 由 WorkBuddy 原生读取，不生成 `.codebuddy/rules/agent21.md`。
- `.codebuddy/skills` 来自 `.agents/skills`。
- 根 `.mcp.json` 原生复用，不生成 MCP 副本。
- WorkBuddy 不因缺少 CLI 可执行文件被跳过。
- 若存在 `CODEBUDDY.md`，doctor 报告其遮蔽 `AGENTS.md`，而不是伪报统一指令已生效。
- `~/.codebuddy` 未被读取或写入。

## Scenario 4: Qoder

```bash
agent21 init --yes --agents qoder --mode copy
agent21 sync --dry-run
agent21 sync
agent21 sync
agent21 doctor
```

Expected:

- 根 `AGENTS.md` 和 `.mcp.json` 原生复用。
- `.qoder/skills` 来自 `.agents/skills`。
- 第二次同步无额外差异。

## Automated gates

```bash
uv run pytest -m "adapter or contract"
uv run pytest -m "integration or safety"
uv run nox -s pr
uv run nox -s main
uv run nox -s package
```

所有失败测试必须在对应实现前建立；快照只在审查目标格式后更新。
