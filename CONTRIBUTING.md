# Contributing

感谢参与 Agent21。贡献应保持小而可验证，并遵循仓库中的规格、契约和测试门禁。

## Local Setup

```bash
uv sync --locked --group dev
uv run nox -s pr
```

`uv.lock` 是依赖真源。依赖变更必须同时更新锁文件，并通过依赖审查和安全审计。

## Development Rules

- 先为行为变化添加失败测试或可执行验收检查，再修改实现。
- 测试写入只能发生在隔离临时目录，不得读写贡献者真实项目资产。
- 不在 fixture、快照、日志或 CI 配置中提交真实凭证。
- 不自动接受快照漂移；基线更新必须审查 diff 后再提交。
- 单文件保持在 1000 行以内，单函数保持在 80 行以内；超出时按职责拆分。
- 代码和关键测试逻辑需要清晰注释，但不要添加与修改无关的格式化或重构。

## Validation Levels

- 日常贡献：`uv run nox -s pr`。
- 当前平台完整验证：`uv run nox -s main`。
- 包验证：`uv run nox -s package`。
- 发布候选：`uv run nox -s release`，再等待 CI 三平台 Release Gate。

## Pull Request Checklist

- 变更范围只覆盖当前需求。
- 新增或修改的行为有测试或明确验证证据。
- `uv run nox -s pr` 已在本地通过，或 PR 描述中说明无法运行的原因。
- 文档、CLI 契约、适配器矩阵和快照基线已随行为变化同步更新。
- 没有真实凭证、个人路径、临时报告或构建产物进入提交。

## Release Changes

发布相关变更还必须运行 `uv run nox -s package` 和 `uv run nox -s release`。
PyPI 发布只通过 Trusted Publishing 完成，不接受仓库密钥或手工 token。
