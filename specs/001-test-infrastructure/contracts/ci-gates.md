# CI Gate Contract

## Pull Request Gate

**Goal**: 在 10 分钟目标内阻止常见逻辑、契约和安全回归。

Required:

1. `uv.lock` 与 `pyproject.toml` 一致。
2. Ruff 格式检查与 lint。
3. mypy 类型检查。
4. unit、adapter、contract、integration 和 safety 快速子集。
5. 分支覆盖率整体不低于 80%，核心区域不低于 90%。
6. 依赖变更审查；发现不允许等级的漏洞时失败。

默认在 Linux 上覆盖最低和最高支持 Python 版本。纯文档变更可以通过路径过滤跳过
高成本测试，但仍必须执行文档和配置一致性检查。

## Main Gate

**Goal**: 验证合并后的完整行为、稳定输出和兼容范围。

除 PR Gate 外，Required:

1. 完整 E2E、snapshot、safety 和 compatibility 测试。
2. 精简矩阵：Linux 运行 Python 3.11、3.12、3.13、3.14；Windows 和 macOS
   至少运行最低与最高支持版本，共八个显式组合。
3. `python -m build`、`twine check --strict` 和 package session。
4. pip-audit 或等价的锁文件依赖漏洞审计。
5. 上传失败差异、测试报告和构建产物；产物不得包含凭证。

## Release Gate

**Goal**: 只允许可安装、可诊断、三平台可信的候选版本进入发布环境。

Required:

1. 对候选 tag 对应的精确提交重新执行 release session。
2. 在 Linux、Windows、macOS 的干净环境分别安装 wheel 并运行 import、
   `agent21 --help`、`agent21 --version`、`agent21 doctor` 冒烟检查。
3. 从 sdist 构建 wheel并至少完成一次干净安装，防止源分发缺文件。
4. 所有 Main Gate 结果已通过且仍在有效期内。
5. 受保护发布环境完成维护者审批后才能进入上传步骤。

任一强制检查失败、错误、取消或缺失时，Release Gate 状态必须为 `blocked`；
人工审批不能覆盖技术门禁失败。

## Matrix and Capability Rules

- runner 的 `-latest` 标签必须视为可漂移环境，失败报告需记录实际 OS 镜像版本。
- 符号链接和权限行为先探测能力；探测失败时验证产品声明的 copy 回退或可诊断失败。
- `skip` 必须包含可审查理由；安全、CLI 契约和发布安装测试不得宽泛 `xfail`。
- 不运行完整 3×4 笛卡尔积；新增平台或 Python 版本时更新显式组合并说明风险覆盖。
