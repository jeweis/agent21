"""Exclusive project lock helpers for Agent21 write operations."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass(frozen=True)
class LockDiagnostic:
    """Doctor-friendly lock status without exposing host-specific secrets."""

    check_id: str
    status: str
    subject: str
    message: str
    action: str | None
    stale: bool


class LockAlreadyHeld(RuntimeError):
    """Raised when another Agent21 write command owns the project lock."""

    def __init__(self, diagnostic: LockDiagnostic) -> None:
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


class ProjectLock:
    """Atomically create and release `.agents/.lock` for one project."""

    def __init__(
        self,
        project_root: Path,
        *,
        command: str,
        stale_after_seconds: int = 3600,
    ) -> None:
        self.project_root = project_root.resolve()
        self.command = command
        self.stale_after_seconds = stale_after_seconds
        self.path = self.project_root / ".agents" / ".lock"
        self._held = False

    def acquire(self) -> Self:
        """Acquire the lock or raise a diagnostic error for the existing owner."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pid": os.getpid(),
            "command": self.command,
            "created_at": time.time(),
            "project_root": self.project_root.as_posix(),
        }
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(self.path, flags, 0o600)
        except FileExistsError as exc:
            diagnostic = inspect_lock(self.project_root, self.stale_after_seconds)
            raise LockAlreadyHeld(diagnostic) from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.write("\n")
        self._held = True
        return self

    def release(self) -> None:
        """Release only the lock acquired by this instance."""

        if not self._held:
            return
        self.path.unlink(missing_ok=True)
        self._held = False

    def __enter__(self) -> Self:
        """Acquire the lock for context-manager use."""

        return self.acquire()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Always release a held lock when leaving the context."""

        self.release()


def inspect_lock(project_root: Path, stale_after_seconds: int = 3600) -> LockDiagnostic:
    """Inspect `.agents/.lock` and classify stale or active ownership."""

    lock_path = project_root.resolve() / ".agents" / ".lock"
    subject = ".agents/.lock"
    if not lock_path.exists():
        return LockDiagnostic(
            "transaction.lock",
            "pass",
            subject,
            "no active Agent21 lock",
            None,
            False,
        )
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _blocked(subject, "lock file is unreadable", True)

    pid = payload.get("pid")
    created_at = payload.get("created_at")
    command = str(payload.get("command", "unknown"))
    stale = _is_stale_pid(pid) or _is_stale_age(created_at, stale_after_seconds)
    if stale:
        return _blocked(subject, f"stale Agent21 lock from {command}", True)
    return _blocked(subject, f"Agent21 lock is held by {command}", False)


def _blocked(subject: str, message: str, stale: bool) -> LockDiagnostic:
    """Build the stable blocked diagnostic shape used by doctor."""

    action = (
        "remove the stale lock after confirming no Agent21 command is running" if stale else None
    )
    return LockDiagnostic("transaction.lock", "blocked", subject, message, action, stale)


def _is_stale_pid(pid: object) -> bool:
    """Return true when the recorded process is clearly not alive."""

    if not isinstance(pid, int) or pid <= 0:
        return True
    if pid == os.getpid():
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    except OSError:
        return False
    return False


def _is_stale_age(created_at: object, stale_after_seconds: int) -> bool:
    """Treat malformed or expired lock timestamps as stale."""

    if not isinstance(created_at, int | float):
        return True
    return time.time() - float(created_at) > stale_after_seconds
