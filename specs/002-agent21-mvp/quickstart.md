# Quickstart: Agent21 MVP Validation

## Prerequisites

- Python 3.11+
- uv
- Git（仅 Git Skill 场景需要）

## Install Development Environment

```bash
uv sync --locked --group dev
```

## Initialize an Isolated Project

```bash
project_dir="$(mktemp -d)"
cd "$project_dir"
printf '# Project instructions\n' > AGENTS.md
agent21 init --yes --agents claude,codex,cursor,opencode,pi --mode copy
```

Expected: `.agents/config.yaml`、`.agents/manifest.yaml` 和 `.agents/skills/` 存在；
既有 `AGENTS.md` 被复用且内容不变。

## Add MCP Configuration and Sync

```bash
printf '%s\n' '{"mcpServers":{"demo":{"command":"demo-mcp","args":["--stdio"]}}}' > .mcp.json
agent21 sync
agent21 sync
```

Expected: Claude 使用根 `.mcp.json`；Codex 生成 `.codex/config.toml`；Cursor 生成
`.cursor/mcp.json`；第二次同步只报告 unchanged/skipped。

## Diagnose

```bash
agent21 doctor
```

Expected: 所有检查按稳定顺序输出；没有 blocked 时退出 0。手工修改托管产物后再次运行应报告漂移并退出 1。

## Install and Remove a Local Skill

```bash
mkdir -p demo-skill
printf '%s\n' '# Demo Skill' > demo-skill/SKILL.md
agent21 skill install demo-skill
agent21 skill list
agent21 skill remove demo-skill
```

Expected: 安装记录来源与摘要，列表稳定排序，remove 只删除 manifest 管理目录。

## Safety and Full Validation

```bash
cd /path/to/agent21
uv run pytest -m safety
uv run nox -s pr
uv run nox -s main
uv run nox -s package
```

Expected: 安全、覆盖率、适配器、安装后 CLI 和 package 门禁全部通过。
