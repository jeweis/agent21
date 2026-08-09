# Research: Agent21 测试基础设施

## 1. Python 支持范围

**Decision**: 最低版本设为 Python 3.11，兼容矩阵覆盖 3.11–3.14。

**Rationale**: Python 3.10 将于 2026-10 结束支持，新项目以 3.11 为下限可避免很快承担
已停止安全维护的版本，同时仍覆盖四个活跃版本。参见 [Python versions](https://devguide.python.org/versions/)。

**Alternatives considered**: 3.10 覆盖更广但维护窗口过短；3.12 下限更现代但会过早排除企业环境。

## 2. 项目与依赖管理

**Decision**: 使用标准 `pyproject.toml` 的 PEP 621 元数据和 dependency groups，
`uv` 负责 lock/sync/run，`hatchling` 作为构建后端；CI 固定 uv 版本。

**Rationale**: 标准元数据和独立构建后端避免把发布格式绑定到单一工具，uv 提供快速、
跨平台且可复现的开发环境。参见 [PyPA pyproject guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
和 [uv project sync](https://docs.astral.sh/uv/concepts/projects/sync/)。

**Alternatives considered**: setuptools 配置面更大；Poetry/PDM 引入另一套项目模型；
uv_build 更轻但会把构建后端也绑定到较新的 uv 生态。

## 3. 测试框架与最小插件集

**Decision**: 使用 pytest、pytest-cov 和 syrupy。优先使用 pytest 内置的 `tmp_path`、
`monkeypatch`、`capsys/capfd`，不默认引入 pytest-mock、pytest-asyncio、xdist 或重试插件。

**Rationale**: 三个依赖分别解决测试运行、覆盖率门禁和稳定输出快照；其余能力在当前范围内
可由内置 fixture 满足，异步、并行和自动重试都没有已证实需求。参见
[pytest fixtures](https://docs.pytest.org/en/stable/reference/fixtures.html)、
[pytest-cov configuration](https://pytest-cov.readthedocs.io/en/stable/config.html) 和
[syrupy usage](https://syrupy-project.github.io/syrupy/)。

**Alternatives considered**: 手写 golden file 可零依赖，但差异和更新流程需要自行维护；
pytest-regressions 更适合数值、表格或图片，本项目主要是文本和结构化 CLI 输出。

## 4. 验证会话编排

**Decision**: 使用 Nox 定义 `pr`、`main`、`package`、`release` 和定向会话，
并以 uv 作为环境后端或命令执行器。CI 与本地调用同一会话，不复制检查逻辑。

**Rationale**: Nox 配置是跨平台 Python 文件，能提供规格要求的单一入口和分层会话，
同时保持每个命令可独立调试。参见 [Nox usage](https://nox.thea.codes/en/stable/usage.html)。

**Alternatives considered**: Makefile 在 Windows 上不统一；自写验证脚本需要自行维护会话、
退出码和环境隔离；只在 CI YAML 中串联会造成无法本地复现。

## 5. CLI 测试分层

**Decision**: 单元测试直接验证领域函数；集成测试使用产品 CLI 框架提供的进程内 runner；
E2E 在干净环境安装构建产物后，通过 subprocess 调用真实 console script。

**Rationale**: 进程内调用反馈快且易定位，subprocess E2E 能验证入口点、PATH、退出码和
stdout/stderr，二者职责互补。参见 [pytest usage](https://docs.pytest.org/en/stable/how-to/usage.html)。

**Alternatives considered**: 所有测试都用 subprocess 太慢且难定位；只用进程内 runner
无法发现打包和安装入口问题。

## 6. 稳定输出和文件树快照

**Decision**: syrupy 快照小型、确定性的文本与结构化输出；另提供一个小型文件树规范化器，
记录相对路径、对象类型、相对链接目标和规范化内容摘要。时间戳、临时根、路径分隔符和随机值必须脱敏。

**Rationale**: 用户可见生成文件是 Agent21 的核心契约，但原始平台元数据会制造误报。
CI 禁止自动更新快照，本地更新后必须审查 diff。路径解析遵循
[pathlib](https://docs.python.org/3/library/pathlib.html) 和
[os.path](https://docs.python.org/3/library/os.path.html) 的符号链接语义。

**Alternatives considered**: 快照整个目录最直接但噪声大；只断言文件存在无法发现内容漂移。

## 7. 隔离与文件系统安全

**Decision**: 每个测试从版本化 fixture 复制到唯一 `tmp_path`；任何越界场景都在临时根外
放置哨兵并验证其字节不变。安全判断必须解析现有父路径和符号链接后检查包含关系，
不得把字符串 `normpath` 当作边界校验。权限和链接测试先探测能力，再验证声明的回退或失败契约。

**Rationale**: `tmp_path` 提供独立临时根，而符号链接和 Windows 权限不能只按 OS 名称推断。
参见 [pytest tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html) 和
[Windows symbolic link policy](https://learn.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/create-symbolic-links)。

**Alternatives considered**: 在仓库 fixture 上原地运行风险不可接受；按 OS 固定跳过会掩盖
开发者模式、权限策略和 runner 镜像差异。

## 8. 覆盖率和标记策略

**Decision**: 开启分支覆盖；整体门禁 80%，再对配置、适配器、Skill 和 MCP 路径执行
90% 的核心区域报告。注册 `unit`、`adapter`、`contract`、`integration`、`e2e`、
`compatibility`、`snapshot`、`safety`、`slow` markers，并启用 `--strict-markers`。

**Rationale**: 两层门槛直接实现规格要求；严格 marker 防止拼写错误造成静默漏测。
参见 [coverage configuration](https://coverage.readthedocs.io/en/latest/config.html) 和
[pytest markers](https://docs.pytest.org/en/stable/how-to/mark.html)。

**Alternatives considered**: 单一 90% 容易鼓励低价值测试；100% 门槛与 MVP 的最小实现原则冲突。

## 9. CI 门禁与兼容矩阵

**Decision**: PR 运行格式、静态分析、依赖变更审查、单元、适配器、集成和覆盖率；
主分支增加完整 E2E、快照、安全与八项精简兼容矩阵；发布增加构建、干净安装和三平台冒烟。

**Rationale**: 分层满足 10 分钟 PR 反馈目标，同时在主分支和发布阶段覆盖完整风险。
矩阵使用显式 `include`，避免 3 OS × 4 Python 的无差别笛卡尔积。参见
[GitHub Actions matrix](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations)
和 [workflow triggers](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)。

**Alternatives considered**: PR 全矩阵成本高且反馈慢；单平台无法证明跨平台产品契约。

## 10. 构建、安装和供应链验证

**Decision**: 发布门禁使用 `python -m build` 生成 sdist 与 wheel，`twine check --strict`
检查元数据，在干净 venv 中分别安装并验证 import、`--help`、`--version` 和 `doctor`。
PR 使用 dependency review，主分支/定时任务使用 pip-audit；发布需要受保护环境审批。

**Rationale**: 从 sdist 构建 wheel 并在新环境安装能暴露缺文件和隐式依赖；依赖变更审查与
已知漏洞扫描覆盖不同阶段。参见 [PyPA build](https://build.pypa.io/en/latest/how-to/basic-usage.html)、
[Twine](https://twine.readthedocs.io/en/stable/index.html)、
[pip-audit](https://github.com/pypa/pip-audit) 和
[GitHub environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)。

**Alternatives considered**: 只安装 wheel 无法证明 sdist 完整；每次 PR 上传 TestPyPI 没有必要且引入外部状态。

## 11. 已推迟能力

**Decision**: MVP 不加入测试并行、自动重试、真实第三方 Agent 控制、真实网络依赖、
性能压测或自动接受快照。

**Rationale**: 这些能力不是当前验收条件，且会降低确定性或扩大维护面；只有在测试时长、
真实兼容缺口或可靠性数据证明必要时再单独规划。

**Alternatives considered**: 一开始启用所有插件和真实互操作能增加覆盖面，但与 KISS/YAGNI 冲突。
