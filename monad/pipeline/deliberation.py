"""Orchestrate proposer → critic → judge deliberation."""

from __future__ import annotations

from typing import Any

from engine.base import LLMEngine

from .critic import run_critic
from .judge import run_judge
from .proposer import run_proposer
from .types import Proposal


def run_deliberation(
    engine: LLMEngine,
    wishes: list[dict[str, Any]],
) -> Proposal:
    """Run the full adversarial loop and return a validated proposal."""
    draft = run_proposer(engine, wishes)
    critique = run_critic(engine, draft, wishes)
    proposal = run_judge(engine, draft, critique)
    if proposal is None:
        raise RuntimeError("Judge returned no proposal without raising ProposalKilled")
    return proposal
