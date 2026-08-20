"""Adversarial deliberation pipeline for the Monad."""

from .deliberation import run_deliberation
from .types import Proposal

__all__ = ["Proposal", "run_deliberation"]
