# Retirement Contract: 托管产物回收

> 定义 sync 回收托管产物的安全规则，供 disable 与手动禁用场景共用。

## 触发

每次 sync（含 dry-run）计算 `retired`：旧 `manifest.managed_artifacts` 中满足
**全部**条件的目标：

1. 其 `path` 不在本次 validated targets（本次不再计划该产物）
2. 其 `agent` **不属于** `unavailable_agents`（enabled 但 executable 缺失的 Agent 保留）

## 规则

- **只删托管**：仅处理 manifest 明确标记为托管的路径；用户自建/未托管文件不在
  `managed_artifacts`，永不进入 retired。
- **dry-run 一致性**：`sync --dry-run` 与 `disable --dry-run` 输出的 retired 清单，
  与真实执行的删除集合逐项一致（SC-002）。
- **漂移保护**：retired 目标若已被手工改动（digest 不匹配），不得静默删除；
  由 `doctor` 报告 drift 并给出 `run agent21 sync` 修复路径。
- **事务化**：删除走 `apply_transaction` 的 retire 流程——备份到
  `.agents/.tmp/<txn>/backup`、journal 记录、失败回滚恢复，不留半删状态。
- **platform 降级**：Windows 等平台删除受限时按既有错误处理回滚并报告。

## 输出契约

| 场景 | 输出 |
|---|---|
| `disable <name> --dry-run` | `would retire: <path>`（不写盘、不改 config） |
| `disable <name>` | `disabled: <name>` + `retired: <path>` |
| `sync --dry-run` | `retired: <path>`（将回收清单） |
| `sync` | `retired: <path>`（本次已回收） |
