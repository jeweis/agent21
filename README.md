# Agent21

Agent21 是面向开发团队的本地 CLI：团队只维护 `AGENTS.md`、`.agents/skills/`
和可选 `.mcp.json`，Agent21 将它们安全同步到 Claude Code、Codex、Cursor、OpenCode 和 Pi。

## Install and First Use

```bash
python -m pip install agent21
cd /path/to/your/project
agent21 init --agents claude,codex,cursor,opencode,pi --mode auto --yes
agent21 sync
agent21 doctor
```

`init` 只在当前项目创建权威配置，遇到未托管冲突会停止；`sync --dry-run` 可在写入前查看计划。
`doctor` 检查配置、manifest、生成物漂移、Skills、MCP、锁和中断事务。

管理项目级 Skill：

```bash
agent21 skill install path/to/my-skill
agent21 skill list
agent21 skill remove my-skill
```

本地 Skill 必须包含根 `SKILL.md`。Git 来源也支持显式 URL；Agent21 只复制内容，
不执行 Skill 代码、不保存 Git 凭证，也不修改用户全局 Agent 配置。

## First Contributor Validation

首次贡献者可以在 15 分钟内完成标准验证准备：

1. 安装 Git、uv 和 Python 3.11 或更高版本。
2. 克隆仓库并进入项目根目录。
3. 同步锁定依赖：

   ```bash
   uv sync --locked --group dev
   ```

4. 运行贡献者门禁：

   ```bash
   uv run nox -s pr
   ```

5. 只排查当前失败项；不要自动更新快照，也不要使用真实凭证。

`pr` 会话覆盖格式、lint、类型、单元、适配器、契约、集成、安全快速子集和覆盖率门槛。
文档专用变更在 CI 中会走轻量路径，但本地仍建议运行 `uv run nox -s pr`。

## Targeted Checks

```bash
uv run pytest -m unit
uv run pytest -m "adapter or contract"
uv run pytest -m integration
uv run pytest -m safety
uv run pytest -m snapshot
uv run nox -s package
```

快照只在产品契约有意变化时本地更新：

```bash
uv run pytest -m snapshot --snapshot-update
git diff -- tests
uv run pytest -m snapshot
```

CI 中不得运行 `--snapshot-update`。

## Release Validation

发布候选版本必须通过主分支门禁、三平台 release session、包构建、干净安装和公开 CLI 冒烟检查。
详细流程见 [docs/release-validation.md](docs/release-validation.md)。

## Contributing and Security

- 贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。
- 安全报告流程见 [SECURITY.md](SECURITY.md)。
- 项目许可证见 [LICENSE](LICENSE)。
