# Agent21 测试指南

Agent21 会修改开发者项目，因此测试首先证明用户资产安全，其次才是代码覆盖率。
本地与 CI 使用相同的 Nox 会话，避免维护两套验证逻辑。

## 首次准备

```bash
uv sync --locked --group dev
```

依赖必须来自已提交的 `uv.lock`。若 `pyproject.toml` 发生变化，先运行 `uv lock`，
审查 lockfile diff，再同步环境。

## 日常验证

提交前运行：

```bash
uv run nox -s pr
```

该会话执行格式、lint、类型检查、快速测试、安全子集和覆盖率门禁。
失败会返回非零状态；先用输出中的测试路径和用例名在本地定向复现。

常用定向命令：

```bash
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m safety
uv run pytest -m "adapter or contract"
uv run pytest -m snapshot
```

核心产品工作流可在临时目录执行：

```bash
agent21 --agents claude,codex,cursor --mode copy
agent21 sync --dry-run
agent21 sync
agent21 doctor
```

写入型测试同时验证全量预校验、未托管冲突、项目边界、事务回滚、锁清理和重复同步幂等。

纯文档变更可由 PR 工作流跳过高成本矩阵，但仍必须检查文档、配置和链接一致性。

## Fixture 规则

- `tests/fixtures/` 下的源 fixture 只读，不得作为命令工作目录。
- 每个测试必须复制 fixture 到独立 `tmp_path` 后再写入。
- 并发测试不得共享可写目录、manifest 或环境变量。
- 越界安全测试必须在项目外创建哨兵，并在执行后按字节验证哨兵未改变。
- 真实凭证不得进入 fixture；假凭证也必须在日志与快照中脱敏。

## 安全失败排查

安全用例失败时按以下顺序检查：

1. 确认命令实际工作目录位于本测试的临时根。
2. 比较执行前后规范化文件树，区分托管产物、未托管文件和项目外哨兵。
3. 解析符号链接后的目标，再判断是否位于项目边界；不能只比较字符串路径。
4. 确认失败没有留下临时文件、半写 manifest 或无法识别的托管状态。
5. 检查 stdout、stderr、报告和快照是否包含令牌、密钥或绝对临时路径。

权限和符号链接行为依赖平台能力。测试必须先探测能力，再验证产品声明的回退或失败；
不得用整个平台宽泛 `xfail` 隐藏安全缺口。

## 快照更新

CI 永远不得自动更新快照。只有公开契约有意变化时，才可在本地运行：

```bash
uv run pytest -m snapshot --snapshot-update
git diff -- tests
uv run pytest -m snapshot
```

评审必须确认：

- 变化对应已批准的规格或契约；
- 临时根、时间戳、路径分隔符和随机值已规范化；
- 快照没有凭证或机器相关信息；
- planned 适配器没有被误报为 implemented；
- 更新后不带 `--snapshot-update` 的测试可通过。

## 覆盖率政策

- Agent21 整体分支覆盖率不得低于 80%。
- 配置、适配器、Skill 和 MCP 核心区域不得低于 90%。
- 覆盖率排除必须有可审查理由，不能通过排除难测生产代码绕过门禁。
- 行为变更与缺陷修复先添加失败测试，再实现修改并保留回归用例。

## 维护性检查

自动检查之外，评审还必须确认：

- 单文件不超过 1000 行，单函数不超过 80 行；超限按职责拆分。
- 新建或实质变更的文件、方法和关键逻辑具有有意义的注释。
- 共享 helper 只承担一种测试责任，避免形成通用杂物模块。
- 测试不依赖执行顺序，且失败信息包含场景、预期、实际结果和复现线索。

## 发布验证

当前平台可运行：

```bash
uv run nox -s main
uv run nox -s package
uv run nox -s release
```

三平台聚合与 PyPI 发布规则见 [release-validation.md](release-validation.md)。
