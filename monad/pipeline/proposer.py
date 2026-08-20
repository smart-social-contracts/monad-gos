"""Proposer step: draft a candidate policy from aggregated wishes."""

from __future__ import annotations

import json
from typing import Any

from engine.base import LLMEngine

from ._json import extract_json


def _format_wishes(wishes: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for wish in wishes:
        lines.append(
            f"- hash={wish.get('hash', 'unknown')}: "
            f"{wish.get('summary', wish.get('text', ''))}"
        )
    return "\n".join(lines) if lines else "(no wishes)"


def run_proposer(engine: LLMEngine, wishes: list[dict[str, Any]]) -> dict[str, Any]:
    """Draft a candidate policy addressing aggregated concerns."""
    prompt = f"""[ROLE: proposer]
You are the Monad proposer. Draft a candidate policy addressing these aggregated wishes.
Respond with a single JSON object only (no markdown) containing:
title, description, motivating_wish_hashes (list of wish hash strings),
expected_effect, cost, losers.

Wishes:
{_format_wishes(wishes)}
"""
    raw = engine.complete(prompt)
    return extract_json(raw)
