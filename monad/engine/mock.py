"""Deterministic mock engine for local testing."""

from __future__ import annotations

import json

from .base import LLMEngine


class MockEngine(LLMEngine):
    """Return canned JSON completions keyed off prompt role markers."""

    def complete(self, prompt: str) -> str:
        if "[ROLE: proposer]" in prompt:
            return json.dumps(
                {
                    "title": "Expand community garden plots",
                    "description": (
                        "Allocate unused municipal land for shared garden plots "
                        "with water access and a modest annual maintenance fund."
                    ),
                    "motivating_wish_hashes": [
                        "sha256:wish-garden-001",
                        "sha256:wish-green-002",
                    ],
                    "expected_effect": (
                        "Increase local food production and neighborhood cohesion."
                    ),
                    "cost": "EUR 12,000 annual maintenance; 2 FTE seasonal staff.",
                    "losers": "Developers holding options on the parcels.",
                }
            )
        if "[ROLE: critic]" in prompt:
            return json.dumps(
                {
                    "attacks": [
                        "Maintenance cost may exceed the stated EUR 12,000 if water infrastructure is degraded.",
                        "Parcel options may trigger legal challenges delaying implementation.",
                    ],
                    "dissent": (
                        "Without a binding maintenance covenant and a clear title review, "
                        "this proposal risks becoming an unfunded mandate that displaces "
                        "affordable housing pressure onto adjacent lots."
                    ),
                }
            )
        if "[ROLE: judge]" in prompt:
            return json.dumps(
                {
                    "verdict": "advance",
                    "title": "Expand community garden plots",
                    "description": (
                        "Allocate unused municipal land for shared garden plots "
                        "with water access and a modest annual maintenance fund, "
                        "contingent on a title review and a 5-year maintenance covenant."
                    ),
                    "motivating_wish_hashes": [
                        "sha256:wish-garden-001",
                        "sha256:wish-green-002",
                    ],
                    "expected_effect": (
                        "Increase local food production and neighborhood cohesion "
                        "once infrastructure and title risks are cleared."
                    ),
                    "cost": "EUR 12,000 annual maintenance; 2 FTE seasonal staff; one-time title review.",
                    "losers": "Developers holding options on the parcels.",
                    "dissent": (
                        "Without a binding maintenance covenant and a clear title review, "
                        "this proposal risks becoming an unfunded mandate that displaces "
                        "affordable housing pressure onto adjacent lots."
                    ),
                }
            )
        return json.dumps({"error": "unknown role", "prompt_head": prompt[:80]})

    def complete_text(self, prompt: str) -> str:
        return (
            "I hear you. I will weigh this with the other wishes of the epoch "
            "and speak again in the broadcast when I have something to propose."
        )
