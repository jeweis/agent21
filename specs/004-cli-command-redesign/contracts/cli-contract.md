# CLI Command Contract: 004-cli-command-redesign

> 版本化公共契约。命令面变更影响用户脚本与文档，需随 README 迁移说明一起发布。

## 命令面总览

```
agent21 [--agents codex,cursor] [--mode auto]    # 默认动作 = enable（无子命令时）
agent21 enable --agents codex,cursor             # 显式等价形式
agent21 disable --agents codex,cursor [--dry-run]
agent21 status
agent21 sync [--dry-run]
agent21 doctor
agent21 skill install <source> [--name N]
agent21 skill list
agent21 skill remove <name>
agent21 --help / --version
```

## 参数解析（无歧义）

- 无子命令（`agent21` 或 `agent21 --agents ...`）：执行默认 enable。
- 有子命令：正常分发（Typer `invoke_without_command` + `ctx.invoked_subcommand`）。
- **Agent 名不作为位置参数**：`agent21 codex` 报 `No such command`（exit 2），
  引导使用 `--agents codex`。

## 命令规范

### 默认命令 / enable

- `agent21 [--agents codex,cursor] [--mode auto]`
- `--agents`：逗号分隔 Agent 名；指定则非交互启用这些 Agent。
- 省略 `--agents`：
  - TTY：交互选择（见下），选中后合并启用 + 同步。
  - 非 TTY：不执行任何启用/写操作，报错引导 `--agents codex,cursor`（退出码 1）。
- 未初始化：自动建立权威源（AGENTS.md、.agents/skills、.agents/config.yaml、
  .agents/manifest.yaml）后继续启用与同步。
- 已初始化：合并启用（只增不减），`--mode` 不覆盖已有同步模式。
- **生成规则**：只要 enabled 即生成配置产物，本机是否安装对应 CLI 不影响；
  目标路径已存在但未托管时接管替换（事务内备份旧内容）。
- 输出：`initialized Agent21 project` → `enabled: <names>` → 真源 `created/reused` →
  同步 `created/updated/unchanged/retired/skipped`；存在 `blocked` 时一并输出并退出码非 0。
- 退出码 0（成功）；未知 Agent 名或冲突退出码非 0。

### 交互选择（TTY、无 `--agents`）

```
可用 Agent：
  [已安装] 1. claude
  [已安装] 2. codex
           3. cursor
           4. opencode
  [已安装] 5. pi
           6. workbuddy
           7. qoder
选择要启用的 Agent（编号逗号分隔，留空=全部）：2,3
```

- 列表 = 全部已注册 Agent；`[已安装]` = 本机检测到对应 CLI（规则基于
  `capability.executable`，无 Agent 特判）。
- 留空：全新项目=全部启用；已初始化=保持现状。
- 非法编号提示重输；重复去重；Ctrl+C 取消且不写文件。
- 已初始化时列表标注当前 `[已启用]`，选择只增不减。

### disable

- `agent21 disable --agents codex,cursor [--dry-run]`
- 目标 Agent 未启用：明确提示（`not enabled: <name>`）退出码 1，不静默无操作。
- 目标 Agent 产物被手工改动（漂移）：报告漂移与修复路径，不静默删除。
- `--dry-run`：更新 config 与删除**均不执行**，仅输出 `would retire: <path>` 清单。
- 执行：config 置 `enabled=false`，事务化删除这些 Agent 全部托管产物，输出
  `disabled: <name>` 与 `retired: <path>`。
- 只删除 manifest 标记为托管且属于目标 Agent 的路径。

### status

- `agent21 status`，只读、无参数。
- 未初始化：输出未初始化提示与接入指引，退出码 0（非致命）。
- 输出：每行一个已注册 Agent：
  `<name>\t<enabled|disabled>\t<available|missing|none-required>\t<managed target list or ->`
  （`none-required` 表示无需 CLI 的配置型，如 workbuddy）
- 尾部追加 doctor 全部 `blocked` 项：
  `blocked: <check_id>: <subject>: <message>; action: <action>`

### sync / doctor / skill

- 沿用既有契约；未初始化时 `sync`/`skill` 报错退出码 1，引导统一为
  `run 'agent21' first`。
- `sync --dry-run` 额外输出 `retired: <path>`（将回收清单）。

## 移除项（迁移注意）

- `agent21 init` 命令**移除**，不保留别名；脚本请改用 `agent21` / `agent21 --agents ...`。
- `--yes`/`-y` **移除**；原 `init --yes` 调用改为 `agent21 [--agents ...]`。
- Agent 名位置参数语法（`agent21 codex`）**移除**，改用 `--agents codex`。
- 未初始化引导消息统一为 `run 'agent21' first`。

## 命名约束

- Agent 名不作为位置参数解析，因此命令名与 Agent 名不要求不相交；裸 Agent 名一律
  报 `No such command` 并引导使用 `--agents`。
