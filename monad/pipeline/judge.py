"""Judge step: reconcile proposer and critic into a final proposal or kill."""

from __future__ import annotations

import json
from typing import Any

from engine.base import LLMEngine

from ._json import extract_json
from .types import Proposal, validate_proposal


class ProposalKilled(Exception):
    """Raised when the judge kills a candidate policy."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def run_judge(
    engine: LLMEngine,
    draft: dict[str, Any],
    critique: dict[str, Any],
) -> Proposal | None:
    """Reconcile draft and critique; return a proposal or None if killed."""
    prompt = f"""[ROLE: judge]
You are the Monad judge. Reconcile the draft and critic's dissent.
Respond with a single JSON object only (no markdown).
If advancing, set verdict to "advance" and include:
title, description, motivating_wish_hashes, expected_effect, cost, losers, dissent.
If killing, set verdict to "kill" and include reason (string).

Draft:
{json.dumps(draft, indent=2)}

Critique:
{json.dumps(critique, indent=2)}
"""
    raw = engine.complete(prompt)
    result: dict[str, Any] = extract_json(raw)
    verdict = str(result.get("verdict", "")).lower()
    if verdict == "kill":
        raise ProposalKilled(str(result.get("reason", "killed by judge")))
    if verdict != "advance":
        raise ValueError(f"Unexpected judge verdict: {verdict!r}")
    return validate_proposal(result)
