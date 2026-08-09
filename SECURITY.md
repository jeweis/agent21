# Security Policy

Agent21 会读取和写入本地项目配置，因此安全问题包括路径逃逸、未托管文件覆盖、
凭证泄露、权限处理错误和不可信输入导致的意外执行。

## Supported Versions

当前项目处于初始开发阶段。维护者只为默认分支和最新发布候选提供安全修复。

## Reporting a Vulnerability

请通过 GitHub Security Advisories 私下报告漏洞。不要在公开 issue、PR、测试快照或日志中发布：

- 真实访问令牌、API key、SSH key 或 cookie。
- 可直接攻击第三方服务的复现数据。
- 包含个人项目路径或私有仓库内容的完整归档。

报告中请包含：

- 受影响版本或提交。
- 复现步骤和期望行为。
- 实际影响范围，包括是否可能写出项目边界、覆盖未托管文件或泄露敏感信息。
- 已知缓解方式。

## Handling Expectations

维护者确认报告后会先复现问题，再评估影响、修复范围和发布时间。
安全修复必须包含回归测试，并通过 PR、main 和适用的 release validation。

## CI and Secrets

CI 不需要真实第三方 Agent、MCP 服务或远程 Skill 仓库凭证。
PyPI 上传使用 Trusted Publishing 和 OIDC，不在仓库或 Actions secrets 中保存发布 token。
