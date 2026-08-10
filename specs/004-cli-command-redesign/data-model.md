# Data Model: CLI 命令重构与 Agent 管理

> 描述本 feature 涉及的数据实体、字段与状态迁移。命令面不新增持久化 schema；
> `AgentSelection` 与 `ManagedArtifact` 保持既有契约，`SyncResult` 新增 `retired` 字段。

## 1. AgentSelection（`.agents/config.yaml`，既有不变）

每个已注册 Agent 一个启用开关，是默认命令 / enable / disable / status 的判断依据。

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 已注册 Agent 名（REGISTERED_AGENTS 子集） |
| `enabled` | bool | 是否启用；enable→true，disable→false |

**状态迁移**：默认命令/enable：`false → true`（或保持 true）；disable：`true → false`。
迁移遵循合并语义——enable 只增不减，不关闭其他 Agent。

## 2. ManagedArtifact（`.agents/manifest.yaml`，既有不变）

记录每个托管产物路径及其归属 Agent，是「只删托管产物」的安全边界。

| 字段 | 类型 | 说明 |
|---|---|---|
| `agent` | str | 产出该产物的 Agent |
| `path` | str | 项目相对路径（POSIX） |
| `kind` | str | file / directory / symlink |
| `mode` | str | copy / symlink / transform |
| `source` | str | 权威源路径或 mcp_source |
| `digest` | str | 内容摘要 |

**状态迁移**（本 feature 新增回收）：当某 Agent 被禁用后，其 `ManagedArtifact` 记录
在下次 sync 中被移除，且对应文件被事务删除；`unavailable_agents`（enabled 但 executable
缺失）的产物**保留**记录与文件。

## 3. SyncResult（`models.py`，新增 `retired`）

sync 的结果模型，dry-run 与执行共用，保证预览/执行一致。

| 字段 | 既有/新增 | 说明 |
|---|---|---|
| `created` | 既有 | 本次新建的托管产物 |
| `updated` | 既有 | 本次更新的托管产物 |
| `unchanged` | 既有 | 无变化的托管产物 |
| `skipped` | 既有 | 因 executable/dependency 不可用而跳过的 Agent 提示 |
| `conflicts` | 既有 | 冲突（未托管文件、锁、事务中断） |
| `errors` | 既有 | 错误清单 |
| `retired` | **新增** | 本次事务化删除的托管产物路径（dry-run 时为将删除清单） |

## 4. 命令面模型（`cli.py` 新增）

| 概念 | 类型 | 说明 |
|---|---|---|
| `--agents` 参数 | str \| None | 逗号分隔的 Agent 名（`codex,cursor`）；非交互确定性启用的权威路径 |
| `ctx.invoked_subcommand` | str \| None | Typer 原生：无子命令时为 None（走默认 enable），否则为子命令名 |
| `parse_selection(text, names)` | tuple[str, ...] | 纯函数：交互编号输入 → 选定 Agent 名；处理空/非法/重复输入 |
| `select_agents_interactive()` | tuple[str, ...] | 薄 I/O 封装：打印编号列表（含 `[已安装]` 标记）→ input() → parse_selection |
| `is_tty()` | bool | `sys.stdin.isatty()`，决定交互 vs 非 TTY 引导 `--agents` |

**交互选择模型**：
- 候选集合 = 全部 `REGISTERED_AGENTS`（7 个，不因检测结果遗漏）。
- 标记：`capability.executable` 存在且 `shutil.which` 命中 → `[已安装]`；`None` → 无标记。
- 留空语义：全新项目 = 全部启用；已初始化 = 保持现状（只增不减）。

## 5. HealthCheckResult（`doctor.py`，既有复用）

status 复用的诊断模型：`check_id`、`subject`、`status`（pass/info/blocked/unsupported）、
`message`、`action`。status 只展示 `blocked` 项及其 `action`。

## 6. 事务状态（`.agents/.tmp/<txn>/`，fs 既有 + 扩展 retire）

| 文件 | 说明 |
|---|---|
| `stage/` | 本次写入内容的暂存区 |
| `backup/` | 被替换或被删除（retire）目标的备份区 |
| `journal.json` | 记录每个目标的备份路径与存在状态，供失败回滚与 doctor 诊断 |

**新增**：retire 删除同样记录到 journal（target + backup + existed），失败时从 backup
恢复，不留半删状态。
