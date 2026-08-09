# Agent21 Test Traceability

本表把 MVP 规格与可执行验证入口关联；同一测试可覆盖多个安全或质量结果。

| Requirement / Outcome | Primary evidence |
| --- | --- |
| FR-001, FR-012, FR-013, SC-003 project boundary and safe writes | `tests/unit/test_project.py`, `tests/unit/test_fs.py`, `tests/integration/test_project_boundary.py`, `tests/integration/test_failure_recovery.py` |
| FR-002–FR-006 initialization, config, manifest | `tests/contract/test_init_cli_contract.py`, `tests/integration/test_init_*.py`, `tests/unit/test_config.py`, `tests/unit/test_manifest.py` |
| FR-007–FR-011, SC-002 synchronization and idempotency | `tests/adapters/test_*_adapter.py`, `tests/integration/test_sync_workflow.py`, `tests/integration/test_sync_idempotency.py` |
| FR-014–FR-015, SC-004 diagnostics and drift | `tests/contract/test_doctor_cli_contract.py`, `tests/integration/test_doctor_*.py` |
| FR-016–FR-017 Skill lifecycle | `tests/contract/test_skill_cli_contract.py`, `tests/integration/test_skill_*.py` |
| FR-018–FR-019 secret safety and local-only boundary | `tests/unit/test_mcp.py`, `tests/integration/test_mcp_config.py`, `tests/integration/test_project_boundary.py` |
| FR-020, SC-007 public CLI semantics | `tests/contract/test_cli_*.py`, `tests/e2e/test_installed_cli.py` |
| FR-021–FR-022, SC-006 cross-platform determinism | `tests/compatibility/`, `.github/workflows/main.yml`, `.github/workflows/release.yml` |
| SC-005 adapter capability truth | `tests/fixtures/adapter_contracts/`, `tests/adapters/`, `specs/001-test-infrastructure/contracts/adapter-matrix.md` |
| 003 FR-001–FR-018 expanded Agent support | `tests/adapters/test_opencode_adapter.py`, `tests/adapters/test_pi_adapter.py`, `tests/adapters/test_workbuddy_adapter.py`, `tests/adapters/test_qoder_adapter.py`, `tests/integration/test_expanded_agent_workflows.py` |
| SC-008 first-use documentation | `README.md`, `specs/002-agent21-mvp/quickstart.md` |
| SC-009 installable release artifact | `tests/e2e/test_installed_cli.py`, `noxfile.py::package`, `.github/workflows/release.yml` |

## Validation Gates

- Pull requests: `uv run nox -s pr`.
- Main branch: `uv run nox -s main`, package build, and dependency audit.
- Release: three operating systems on Python 3.11/3.14, clean package smoke, then protected PyPI OIDC publishing.
