"""Structured proposal schema emitted by the deliberation pipeline."""

from __future__ import annotations

from typing import TypedDict


class Proposal(TypedDict):
    """Final Monad proposal after judge reconciliation."""

    title: str
    description: str
    motivating_wish_hashes: list[str]
    expected_effect: str
    cost: str
    losers: str
    dissent: str


REQUIRED_FIELDS = (
    "title",
    "description",
    "motivating_wish_hashes",
    "expected_effect",
    "cost",
    "losers",
    "dissent",
)


def validate_proposal(data: dict) -> Proposal:
    """Ensure *data* contains every required proposal field."""
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"Proposal missing fields: {', '.join(missing)}")
    return Proposal(
        title=str(data["title"]),
        description=str(data["description"]),
        motivating_wish_hashes=list(data["motivating_wish_hashes"]),
        expected_effect=str(data["expected_effect"]),
        cost=str(data["cost"]),
        losers=str(data["losers"]),
        dissent=str(data["dissent"]),
    )
