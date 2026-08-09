"""Shared Agent21 domain errors and CLI exit classification."""

from __future__ import annotations


class Agent21Error(Exception):
    """Base class for expected Agent21 failures with stable exit behavior."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class ConfigError(Agent21Error):
    """Raised when `.agents/config.yaml` is missing, malformed, or unsafe."""


class ManifestError(Agent21Error):
    """Raised when `.agents/manifest.yaml` is malformed or inconsistent."""


class BoundaryError(Agent21Error):
    """Raised when a project path would escape the repository boundary."""

    def __init__(self, message: str) -> None:
        super().__init__(message, exit_code=2)


class ConflictError(Agent21Error):
    """Raised when an unmanaged or drifted path blocks a write operation."""


class ValidationError(Agent21Error):
    """Raised when in-memory model data violates the Agent21 contract."""


def classify_exit(error: BaseException) -> int:
    """Return the stable process exit code for an exception."""

    if isinstance(error, Agent21Error):
        return error.exit_code
    return 1
