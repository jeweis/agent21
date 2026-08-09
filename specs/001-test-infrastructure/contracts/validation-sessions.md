# Validation Session Contract

本契约定义贡献者和 CI 共用的验证入口。具体工具版本由 `uv.lock` 固定，
会话行为变化视为测试基础设施契约变更。

## Public Sessions

| Session | Command | Required checks | Intended trigger |
| --- | --- | --- | --- |
| `pr` | `uv run nox -s pr` | 格式、lint、类型、unit、adapter、contract、integration、safety 快速子集、整体与核心覆盖率 | 本地提交前、Pull Request |
| `main` | `uv run nox -s main` | `pr` 全部内容，加 E2E、snapshot、safety、当前平台 compatibility | 主分支、发布前本地复现 |
| `package` | `uv run nox -s package` | sdist/wheel、元数据检查、干净安装、import、`--help`、`--version`、`doctor` | 主分支、发布 |
| `release` | `uv run nox -s release` | `main` + `package`；CI 另外聚合三平台结果 | 候选发布 |

任一子检查失败时，会话必须返回非零状态，不得用自动重试掩盖失败。

## Targeted Sessions

| Purpose | Command |
| --- | --- |
| 单元测试 | `uv run pytest -m unit` |
| 适配器契约 | `uv run pytest -m "adapter or contract"` |
| 集成流程 | `uv run pytest -m integration` |
| 文件安全 | `uv run pytest -m safety` |
| 稳定输出 | `uv run pytest -m snapshot` |
| 当前平台完整验证 | `uv run pytest -m "e2e or compatibility"` |

## Marker Registry

必须注册并启用 `--strict-markers`：

- `unit`: 无文件工作流的最小逻辑。
- `adapter`: 单一 Agent 适配器输入输出契约。
- `contract`: 公共 CLI、配置 schema 或版本化格式契约。
- `integration`: 在隔离项目中组合多个组件。
- `e2e`: 安装后通过 subprocess 调用真实 CLI。
- `compatibility`: 平台、Python 版本或同步模式差异。
- `snapshot`: 需要稳定输出基线。
- `safety`: 未托管文件、路径边界、权限或敏感信息验证。
- `slow`: 不进入默认快速子集的高成本验证。

## Snapshot Update

只有开发者可在本地显式运行：

```bash
uv run pytest -m snapshot --snapshot-update
```

更新后必须审查版本库 diff，再不带更新参数重新运行。CI 中出现 `--snapshot-update`
或未审查的新基线都属于配置错误。
