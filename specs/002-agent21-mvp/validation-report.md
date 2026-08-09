# Validation Report: Agent21 MVP

**Date**: 2026-08-09  
**Version**: 0.1.0  
**Result**: PASS（本地实现与发布候选门禁）

## Implemented Surface

- `agent21 init --agents --mode --yes`
- `agent21 sync [--dry-run]`
- `agent21 doctor`
- `agent21 skill install/list/remove`
- Claude Code、Codex、Cursor、OpenCode、Pi MVP adapter
- 确定性 YAML manifest/config、MCP 转换、copy/symlink/auto、锁与回滚

## Verification

| Check | Result |
| --- | --- |
| Ruff format + lint | PASS |
| Strict mypy over `src` and `tests` | PASS（85 files） |
| Full test suite | PASS（152 tests） |
| Overall branch coverage | PASS（89.61% ≥ 80%） |
| Core aggregate coverage | PASS（93% ≥ 90%） |
| 20-run sync idempotency | PASS |
| Project escape / unmanaged conflict / rollback / redaction | PASS |
| macOS compatibility and installed CLI E2E | PASS |
| sdist + wheel metadata | PASS |
| Clean wheel install and all-command smoke | PASS |
| GitHub workflow YAML and gate contracts | PASS |

## Remote Follow-up

推送后由 GitHub Actions 执行 Linux、macOS、Windows 以及 Python 3.11–3.14 的声明矩阵。
PyPI 发布使用受保护的 `pypi` environment 与 OIDC Trusted Publishing，不在仓库存放 token。
