"""Critic step: attack the draft policy."""

from __future__ import annotations

import json
from typing import Any

from engine.base import LLMEngine

from ._json import extract_json


def run_critic(
    engine: LLMEngine,
    draft: dict[str, Any],
    wishes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Attack the draft on cost, harm, and contradictions."""
    prompt = f"""[ROLE: critic]
You are the Monad critic. Attack this draft policy on cost, who it harms, and contradictions.
Respond with a single JSON object only (no markdown) containing:
attacks (list of strings), dissent (string — the strongest case against, preserved for ratifiers).

Draft policy:
{json.dumps(draft, indent=2)}

Original wishes:
{json.dumps(wishes, indent=2)}
"""
    raw = engine.complete(prompt)
    return extract_json(raw)
