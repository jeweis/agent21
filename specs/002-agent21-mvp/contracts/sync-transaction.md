# Sync Transaction Contract

## Phases

1. **Plan**: 读取 config、manifest 和权威源；收集并排序 PlannedArtifact。
2. **Validate**: 校验所有路径、来源、目标、未托管冲突、漂移和权限；任何错误阻止写入。
3. **Lock**: 原子创建 `.agents/.lock`；存在锁则退出 1。
4. **Stage**: 在 `.agents/.tmp/<id>/` 创建完整目标和前态 journal。
5. **Apply**: 按目标路径排序，以 replace/rename 应用；每步记录状态。
6. **Commit**: 最后原子写 manifest，标记 journal committed。
7. **Cleanup**: 删除 journal/temp 并释放 lock。

## Rollback

- apply 后任一步失败，按 journal 逆序恢复原文件、目录或 symlink。
- 原本不存在的目标在回滚时删除。
- 未托管文件不会进入 journal，因为 validate 阶段已阻止冲突。
- 回滚本身失败时保留 journal，doctor 报 `transaction.dangling` blocked。
- 无论成功或异常，能安全清理的临时文件和 lock 必须清理。

## Idempotency

- digest 相同的托管目标记为 unchanged，不重写。
- manifest 不含时间戳，列表稳定排序。
- 第二次相同同步结果只包含 unchanged/skipped，文件树摘要与第一次一致。

## Copy and Symlink

- `copy`: 内容由权威源复制，目标记录 digest。
- `symlink`: 只创建项目内相对链接；链接解析后仍必须位于项目根。
- `auto`: 先能力探测 symlink；失败时改为 copy 并在结果中报告实际模式。
