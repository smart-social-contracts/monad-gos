"""Publish Codex changes to GitHub, then deploy the backend."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_PATH = "src/monad_backend/codex/codex.mo"


def _run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def current_commit() -> str:
    return _run(["git", "rev-parse", "HEAD"]).stdout.strip()


def publish(message: str, *, deploy: bool = True) -> str:
    """Commit tracked Codex changes, push to origin, optionally deploy."""
    _run(["git", "add", CODEX_PATH])
    status = _run(["git", "status", "--porcelain", CODEX_PATH], check=False)
    if not status.stdout.strip():
        logger.info("No Codex changes to publish")
        return current_commit()

    _run(["git", "commit", "-m", message])
    sha = current_commit()
    _run(["git", "push", "origin", "HEAD"])
    logger.info("Published Codex %s", sha)
    if deploy:
        deploy_backend()
    return sha


def deploy_backend() -> None:
    _run(["icp", "deploy", "monad_backend", "--environment", "ic", "--mode", "upgrade"])
    logger.info("Deployed monad_backend")
