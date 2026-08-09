# Implementation Plan: Agent21 测试基础设施

**Branch**: `未创建` | **Date**: 2026-08-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-test-infrastructure/spec.md`

**Note**: 本计划只建设测试、验证和发布门禁，不实现 Agent21 业务命令或未交付适配器。

## Summary

为 Agent21 建立一套跨平台、测试优先且可长期维护的验证体系。方案使用标准 Python
项目元数据，以分层测试覆盖核心逻辑、适配器契约、真实文件工作流、安装后 CLI 和平台差异；
用隔离 fixture、稳定输出快照、文件树状态比较和失败注入证明幂等、未托管文件保护与可恢复性；
通过 PR、主分支和发布三层门禁平衡反馈速度与发布可信度。

## Technical Context

**Language/Version**: Python 3.11+；兼容矩阵覆盖 3.11、3.12、3.13、3.14

**Primary Dependencies**: 标准 `pyproject.toml`、`uv`、`hatchling`；测试依赖为
pytest、pytest-cov、syrupy、Nox；质量与发布验证使用 Ruff、mypy、pip-audit、build、Twine。
仅当产品 CLI 使用 Typer 时复用其 CliRunner，不把 Typer 作为测试基础设施新增的运行时依赖。

**Storage**: 无数据库；版本化存储 fixture、适配器契约和稳定输出快照，临时项目与测试报告可重建

**Testing**: pytest 分层与严格 marker；内置 `tmp_path`、`monkeypatch`、`capsys/capfd`；
安装后 console script 的 subprocess E2E；分支覆盖率整体不低于 80%，核心区域不低于 90%

**Target Platform**: Linux、macOS、Windows；支持产品声明的 `auto`、`copy`、`symlink` 模式；发布到 PyPI

**Project Type**: 单包 Python CLI，采用 `src/` 布局

**Performance Goals**: 至少 90% 的常规贡献变更在 PR 门禁中 10 分钟内得到确定结果；
单元测试保持秒级，较慢的三平台、安装和完整 E2E 留在主分支或发布门禁

**Constraints**: 默认离线；测试写入仅限隔离临时根；不得使用真实凭证或执行 Skill 内容；
稳定输出更新必须显式评审；测试不得依赖执行顺序；单文件不超过 1000 行、单函数不超过 80 行

**Scale/Scope**: 4 个验证层级、3 个 CI 门禁、3 个操作系统、4 个 Python 版本、
6 类 fixture、7 个可登记 Agent、5 个 MVP CLI 命令组

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate: PASS

- **Single source**: 产品规格、宪章、公开 CLI/配置契约和 Agent 支持矩阵是判定依据。
  fixture 与快照是经评审的测试资产；报告、临时项目和覆盖率结果均为可重建产物，不成为产品配置真源。
- **Adapter boundary**: 本功能不新增产品适配器。测试契约按原生、兼容映射、转换、不支持分类，
  只强制验证已实现适配器；计划中登记但未实现的 Agent 不会伪装通过。
- **Safe synchronization**: 每个写入型命令通过执行前后规范化文件树、重复执行、失败注入、
  项目外哨兵和未托管文件字节比较验证确定性、幂等、边界与恢复。
- **Compatibility contract**: 三平台与 Python 3.11–3.14 使用显式矩阵；链接能力通过运行时探测，
  不仅按操作系统名称推断；公共 CLI、适配器和 CI 门禁均有版本化契约。
- **Verification**: 行为变更先写失败测试；单元、适配器、集成、E2E、快照、安全和兼容测试
  分层运行；最终门禁包含干净安装、公开命令冒烟和 `agent21 doctor`。
- **Security boundary**: fixture 复制到 `tmp_path` 后才可写；测试禁用未声明网络访问，使用假凭证；
  路径安全检查解析符号链接后验证项目边界，日志与快照执行脱敏。
- **Simplicity**: 优先使用 pytest 内置 fixture，只为覆盖率、稳定快照和跨阶段编排保留必要依赖。
  不引入数据库、服务容器、真实 Agent 控制或并行插件；文件和函数规模约束适用于测试代码。

### Post-Design Re-check: PASS

Phase 1 产物没有引入新的真源或产品适配器。数据模型只描述测试资产；契约明确了
公开命令、适配器和门禁边界；quickstart 中的所有写入均限定在测试环境或构建目录。
不存在需要豁免的宪章冲突。

## Project Structure

### Documentation (this feature)

```text
specs/001-test-infrastructure/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── adapter-contract.schema.json
│   ├── adapter-matrix.md
│   ├── agent21-cli-contract.md
│   ├── ci-gates.md
│   └── validation-sessions.md
└── tasks.md                         # 由 /speckit-tasks 生成
```

### Source Code (repository root)

```text
pyproject.toml
uv.lock
noxfile.py
src/
└── agent21/                         # 产品代码；本功能不实现业务能力
tests/
├── conftest.py
├── unit/
├── adapters/
├── contract/
├── integration/
├── e2e/
├── compatibility/
├── fixtures/
│   └── projects/
│       ├── empty_project/
│       ├── agents_project/
│       ├── claude_project/
│       ├── cursor_project/
│       ├── mixed_project/
│       └── broken_project/
├── snapshots/
└── support/
    ├── project_factory.py
    ├── tree_snapshot.py
    ├── cli_runner.py
    └── assertions.py
.github/
├── dependabot.yml
└── workflows/
    ├── pr.yml
    ├── main.yml
    └── release.yml
```

**Structure Decision**: 采用单包 `src/` 布局并按验证责任拆分测试目录。
fixture 源只读，测试运行时复制到临时根；共享帮助代码集中在 `tests/support/`，
但每个帮助模块保持单一职责。CI 分为三个工作流，避免在 PR 上运行完整发布成本。

## Complexity Tracking

无宪章例外或需要保留的复杂度豁免。
