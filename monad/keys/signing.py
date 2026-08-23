"""Stub key management for Monad signing and vetKey decryption."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MonadKeys:
    """Placeholder for Monad signing + vetKey material."""

    key_path: str | None

    def decrypt_epoch(self, sealed_epoch: bytes) -> list[dict[str, Any]]:
        """Stub: log and return an empty wish list."""
        logger.info(
            "vetKey decrypt stub: key_path=%s sealed_bytes=%d",
            self.key_path,
            len(sealed_epoch),
        )
        return []

    def sign_proposal(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """Stub: log and attach a placeholder signature envelope."""
        logger.info(
            "sign_proposal stub: key_path=%s title=%r",
            self.key_path,
            proposal.get("title"),
        )
        return {
            "proposal": proposal,
            "signature": "stub:unsigned",
            "signer": "monad-stub",
        }


def load_keys() -> MonadKeys:
    """Load key configuration from ``MONAD_KEY_PATH``."""
    key_path = os.environ.get("MONAD_KEY_PATH")
    if not key_path:
        default_pem = Path(__file__).resolve().parent / "monad-executive.pem"
        if default_pem.is_file():
            key_path = str(default_pem)
    if key_path:
        logger.info("Monad key path configured: %s", key_path)
    else:
        logger.warning("MONAD_KEY_PATH not set; signing and vetKey ops are stubbed")
    return MonadKeys(key_path=key_path)
