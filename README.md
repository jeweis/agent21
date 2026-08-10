# Agent21

Agent21 是一个项目级 AI 编程代理配置同步 CLI。团队只维护一套工程配置，
即可在 Claude Code、Codex CLI、Cursor、OpenCode、Pi、WorkBuddy 和 Qoder 之间同步使用：

- `AGENTS.md`：项目指令
- `.agents/skills/`：项目 Skills
- `.mcp.json`：MCP 服务配置（可选）

Agent21 只管理当前项目，不修改用户的全局 Agent 配置。

> 当前版本：`0.1.5`（Alpha）。建议先提交现有项目文件，再执行首次同步。

## 快速开始

进入需要统一配置的项目，首次运行 `agent21` 完成初始化与同步，之后每次修改配置
只需 `agent21 sync`：

```bash
uv tool install agent21
cd /path/to/your/project
agent21        # 首次：初始化权威源并同步到已启用的 Agent（交互选择，或用 --agents 指定）
agent21 sync   # 之后：修改 AGENTS.md / .agents/skills / .mcp.json 后重新同步
```

`agent21 sync` 依赖项目已初始化（存在 `.agents/config.yaml`），因此首次先运行 `agent21`
建立权威源并同步；`agent21` 与 `agent21 sync` 构成「安装 → 用起来 → 保持同步」的最小闭环。

## 安装

需要 Python 3.11 或更高版本。

使用 uv（推荐）：

```bash
uv tool install agent21
```

使用 uv 安装后，更新到最新版本：

```bash
uv tool upgrade agent21
```

或使用 pip：

```bash
python -m pip install agent21
```

确认安装成功：

```bash
agent21 --version
```

## 常用命令

| 命令 | 用途 |
| --- | --- |
| `agent21 [--agents A,B]` | 默认命令：启用指定 Agent 并同步（省略时交互选择） |
| `agent21 enable --agents A,B` | 显式启用并同步（与默认命令等价） |
| `agent21 disable --agents A,B [--dry-run]` | 禁用 Agent 并回收其托管产物 |
| `agent21 status` | 查看每个 Agent 的启用状态、可用性与托管产物 |
| `agent21 sync --dry-run` | 校验并预览同步计划，不写入文件 |
| `agent21 sync` | 将权威配置同步到所有已启用的 Agent |
| `agent21 doctor` | 只读检查配置、漂移、Skills、MCP、锁和中断事务 |
| `agent21 skill install <source>` | 从本地目录或显式 Git URL 安装项目 Skill |
| `agent21 skill list` | 列出 Agent21 管理的项目 Skills |
| `agent21 skill remove <name>` | 删除未被修改的托管 Skill |
| `agent21 --help` | 查看完整命令帮助 |

只启用团队实际使用的 Agent，以及移除不再使用的 Agent：

```bash
agent21 --agents codex,cursor
agent21 disable --agents cursor --dry-run   # 先预览将删除的托管产物
agent21 disable --agents cursor
```

同步模式支持：

- `auto`：平台支持时使用符号链接，否则复制（推荐）
- `copy`：始终复制
- `symlink`：始终使用符号链接

启用状态与同步模式也可以在 `.agents/config.yaml` 中查看和调整。

**两点说明**：

- **启用即生成**：只要 Agent 在 config 中启用，`sync` 就会生成它的配置产物，
  与本机是否安装对应 CLI 无关（未安装也可先同步，装好即可用）。
- **接管替换**：目标路径（如 `.claude/skills`）若已存在但未被 agent21 托管，
  `sync` 会用权威源内容接管替换它（事务内备份旧内容后写入），并记入托管清单。

## 管理项目 Skills

本地 Skill 目录必须包含根文件 `SKILL.md`：

```bash
agent21 skill install path/to/my-skill
agent21 skill list
agent21 skill remove my-skill
```

也可以安装显式 Git URL，并按需指定名称：

```bash
agent21 skill install https://github.com/example/my-skill.git --name my-skill
```

Agent21 只复制并记录 Skill 内容，不执行 Skill 代码，也不保存 Git 凭证。

## Agent 支持范围

| Agent | 项目指令 | Skills | MCP |
| --- | --- | --- | --- |
| Claude Code | 兼容同步 | 兼容同步 | 原生读取 `.mcp.json` |
| Codex CLI | 原生读取 | 原生读取 | 转换为 `.codex/config.toml` |
| Cursor | 原生读取 | 原生读取 | 转换为 `.cursor/mcp.json` |
| OpenCode | 原生读取 | 原生读取 | 转换为 `opencode.json` |
| Pi | 原生读取 | 原生读取 | 通过 `pi-mcp-adapter` 兼容读取 |
| WorkBuddy | 原生读取根 `AGENTS.md` | 映射到 `.codebuddy/skills/` | 原生读取根 `.mcp.json` |
| Qoder | 原生读取 | 映射到 `.qoder/skills/` | 原生读取根 `.mcp.json` |

Agent21 不会安装这些 Agent 或第三方扩展。Pi MCP 需由用户显式安装：

```bash
pi install npm:pi-mcp-adapter
```

Agent21 只检测 `pi-mcp-adapter` 是否可用，不执行它，也不会把“可检测”误报为已加载。
WorkBuddy 沿用腾讯 CodeBuddy 的项目配置目录，因此不依赖推测的 CLI 名称；显式启用后即可同步
`.codebuddy/skills/`。当根目录没有 `CODEBUDDY.md` 时，WorkBuddy 原生读取 `AGENTS.md`；若两者同时存在，
`agent21 doctor` 会报告 `CODEBUDDY.md` 遮蔽统一指令。其他已启用但本机找不到可执行文件的 Agent 会被标记为
`skipped`。

## 安全与冲突处理

- 不覆盖未由 Agent21 管理的冲突文件。
- `sync --dry-run` 在写入前展示已校验的计划。
- 同步通过事务写入；失败时避免留下部分更新。
- manifest 记录托管产物及摘要，`doctor` 可发现手工修改造成的漂移。
- 诊断输出不会回显 MCP 密钥值，但 `.mcp.json` 仍应按项目的凭证策略妥善管理。

遇到问题时，先运行：

```bash
agent21 doctor
agent21 --help
```

如果问题仍然存在，请在 [GitHub Issues](https://github.com/jeweis/agent21/issues) 提交可复现步骤；
安全问题请遵循 [SECURITY.md](SECURITY.md)，不要公开提交凭证或漏洞细节。

## 开发与贡献

README 面向 CLI 使用者。开发环境、测试设计、适配器验证和发布流程分别维护在：

- [贡献指南](CONTRIBUTING.md)
- [测试指南](docs/testing.md)
- [适配器测试](docs/adapter-testing.md)
- [发布验证](docs/release-validation.md)
- [测试追踪关系](docs/testing-traceability.md)

项目采用 [MIT License](LICENSE)。
