# Data Model: Agent21 MVP

模型通过 dataclass 表达，配置与 manifest 使用稳定 YAML 序列化。所有路径均为项目相对 POSIX 字符串。

## ProjectConfig

| Field | Type | Rules |
| --- | --- | --- |
| `schema_version` | integer | 必须为 `1` |
| `agents` | map<string, AgentSelection> | 只允许已登记 Agent；稳定排序 |
| `sync_mode` | enum | `auto`、`copy`、`symlink` |
| `instructions_source` | path | 默认 `AGENTS.md`，不得越界 |
| `skills_source` | path | 默认 `.agents/skills`，不得越界 |
| `mcp_source` | path | 默认 `.mcp.json`，不得越界 |

## AgentSelection

| Field | Type | Rules |
| --- | --- | --- |
| `enabled` | boolean | 必填，不接受真假字符串 |

## Manifest

| Field | Type | Rules |
| --- | --- | --- |
| `schema_version` | integer | 必须为 `1` |
| `agent21_version` | string | 生成 manifest 的版本 |
| `managed_artifacts` | list<ManagedArtifact> | 按 path、agent 排序且 path 唯一 |
| `skills` | list<SkillRecord> | 按 name 排序且 name 唯一 |

manifest 只描述托管状态，不覆盖 ProjectConfig 或权威源的语义。

## ManagedArtifact

| Field | Type | Rules |
| --- | --- | --- |
| `agent` | string | 已登记 Agent slug |
| `path` | path | 项目相对且唯一 |
| `kind` | enum | `file`、`directory`、`symlink` |
| `mode` | enum | `native`、`copy`、`symlink`、`transform` |
| `source` | path | 一个或多个权威源的主来源 |
| `digest` | string | `sha256:<hex>`；symlink 使用目标字符串摘要 |

**State**:

```text
planned -> staged -> applied -> unchanged
                    -> drifted
                    -> removed
```

## AgentCapability

| Field | Type | Rules |
| --- | --- | --- |
| `agent` | string | 稳定 slug |
| `instructions` | enum | `native`、`compatible`、`transform`、`unsupported` |
| `skills` | enum | 同上 |
| `mcp` | enum | 同上 |
| `implemented` | boolean | 只有契约和测试同时存在才为 true |
| `executable` | string/null | 可选环境检测命令名 |

## PlannedArtifact

adapter 产生的无副作用写入计划。

| Field | Type | Rules |
| --- | --- | --- |
| `agent` | string | 计划来源 adapter |
| `target` | path | 项目相对目标 |
| `kind` | enum | `file`、`directory`、`symlink` |
| `mode` | enum | `copy`、`symlink`、`transform` |
| `source` | path/null | copy/symlink 的来源 |
| `content` | bytes/null | transform/file 内容；与 source 二选一 |
| `digest` | string | 规范化目标摘要 |

## SyncPlan / SyncResult

`SyncPlan` 包含排序后的 PlannedArtifact 和预校验结果；`SyncResult` 聚合结果。

| Field | Type | Rules |
| --- | --- | --- |
| `created` | list<path> | 新托管产物 |
| `updated` | list<path> | 既有托管产物更新 |
| `unchanged` | list<path> | 摘要已一致 |
| `skipped` | list<string> | 未启用、未安装或不支持能力 |
| `conflicts` | list<path> | 同名未托管或漂移阻止写入 |
| `errors` | list<string> | 其他阻塞错误 |

所有集合输出前稳定排序。存在 conflicts/errors 时不得开始 apply。

## TransactionJournal

| Field | Type | Rules |
| --- | --- | --- |
| `transaction_id` | string | 进程内随机 ID，只用于临时路径 |
| `command` | string | 当前写入命令 |
| `entries` | list<JournalEntry> | 按 apply 顺序记录前态 |
| `state` | enum | `staging`、`applying`、`committed`、`rolling_back`、`failed` |

**State transitions**:

```text
staging -> applying -> committed
                 \-> rolling_back -> failed
```

journal 位于 `.agents/.tmp/<id>/`，成功或完整回滚后删除。残留 journal 由 doctor 报 blocked。

## SkillRecord

| Field | Type | Rules |
| --- | --- | --- |
| `name` | string | `^[a-z0-9][a-z0-9-]*$` |
| `path` | path | `.agents/skills/<name>` |
| `source_type` | enum | `local`、`git` |
| `source` | string | 本地使用项目相对路径；Git URL 不含凭证 |
| `version` | string/null | 来自可选元数据 |
| `digest` | string | 规范化目录摘要 |

## HealthCheckResult

| Field | Type | Rules |
| --- | --- | --- |
| `check_id` | string | 稳定且可排序 |
| `status` | enum | `pass`、`info`、`unsupported`、`blocked` |
| `subject` | string | 项目相对对象或 Agent 名称 |
| `message` | string | 不含敏感值 |
| `action` | string/null | 可执行的下一步 |

任何 `blocked` 结果使 doctor 退出 1；其余状态退出 0。

## Relationships

```text
ProjectConfig 1 --- * AgentSelection
ProjectConfig 1 --- * AgentAdapter
AgentAdapter 1 --- * PlannedArtifact
SyncPlan 1 --- * PlannedArtifact
Manifest 1 --- * ManagedArtifact
Manifest 1 --- * SkillRecord
TransactionJournal 1 --- * JournalEntry
Doctor 1 --- * HealthCheckResult
```
