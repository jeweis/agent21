# Validation Report: Agent21 测试基础设施

**Date**: 2026-08-09  
**Platform**: macOS / Python 3.14.3  
**Result**: PASS（本地门禁）；远程三平台结果由推送后的 GitHub Actions 生成。

## Evidence

| Gate | Result | Evidence |
| --- | --- | --- |
| Format | PASS | `ruff format --check .`，146 files already formatted |
| Lint | PASS | `ruff check .` |
| Types | PASS | `mypy src tests`，85 source files |
| PR session | PASS | 142 tests；整体覆盖率 88.52%；核心聚合覆盖率 93% |
| Main session | PASS | 151 tests；整体覆盖率 89.58%；核心聚合覆盖率 93% |
| Release session | PASS | 152 tests；整体覆盖率 89.61%；核心聚合覆盖率 93% |
| Package | PASS | sdist/wheel 构建、`twine check --strict`、干净安装、help/version/init/sync/doctor/Skill 生命周期 |
| Adapter contracts | PASS | 5 implemented、2 planned；schema、语义、原生无冗余、转换快照契约通过 |
| PyPI name probe | PASS | PyPI 官方 JSON 接口对 `agent21` 返回 HTTP 404，当前未发现已注册项目 |

## Safety Review

- 所有写入路径先进行项目边界与 symlink-aware 校验。
- 未托管目标、漂移产物、嵌套 Skill symlink 和并发锁均安全拒绝。
- 事务失败回滚并清理临时目录；doctor 可识别残留 journal 和 stale lock。
- CI 禁止自动更新快照；仓库扫描未发现真实凭证。
- 源码最大文件 393 行，未发现超过 80 行的函数。
