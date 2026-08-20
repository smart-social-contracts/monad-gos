"""Monad off-chain service entrypoint."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from backend import load_client
from engine import MockEngine, get_engine
from keys import load_keys
from pipeline import run_deliberation


def stub_wishes() -> list[dict[str, str]]:
    """Placeholder aggregated wishes for dry-run mode."""
    return [
        {
            "hash": "sha256:wish-garden-001",
            "summary": "More community garden space near the riverfront.",
        },
        {
            "hash": "sha256:wish-green-002",
            "summary": "Turn vacant lots into green commons instead of parking.",
        },
    ]


def run(*, dry_run: bool = False) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if dry_run:
        engine = MockEngine()
        wishes = stub_wishes()
        backend = None
    else:
        engine = get_engine()
        backend = load_client()
        epoch = backend.get_epoch_status()
        logging.info(
            "Epoch %s phase=%s seal_in=%ss",
            epoch["epoch_id"],
            next(iter(epoch["phase"])),
            epoch["seconds_until_seal"],
        )
        alignment = backend.alignment_coefficient()
        logging.info(
            "Alignment coefficient=%.3f citizens=%s/%s",
            alignment["coefficient"],
            alignment["citizens_current"],
            alignment["citizens_total"],
        )
        wishes = backend.wishes_for_deliberation(epoch["epoch_id"])
        logging.info("Loaded %d wishes for deliberation", len(wishes))

    keys = load_keys()
    proposal = run_deliberation(engine, wishes)
    signed = keys.sign_proposal(dict(proposal))

    if backend is not None:
        proposal_input = {
            "title": proposal["title"],
            "description": proposal["description"],
            "code_url": "",
            "code_checksum": "",
            "voting_deadline": None,
            "required_threshold": None,
            "org_scope": "chora",
            "metadata": json.dumps(
                {
                    "motivating_wish_hashes": proposal["motivating_wish_hashes"],
                    "expected_effect": proposal["expected_effect"],
                    "cost": proposal["cost"],
                    "losers": proposal["losers"],
                    "dissent": proposal["dissent"],
                }
            ),
        }
        backend.validate_proposal(proposal_input)
        logging.info("Proposal validated on-chain (not submitted)")

    print(json.dumps(signed, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chora Monad off-chain service")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the MockEngine pipeline end-to-end and print the signed proposal",
    )
    parser.add_argument(
        "--reply-loop",
        action="store_true",
        help="Watch citizen threads and auto-reply as the Monad",
    )
    args = parser.parse_args(argv)
    try:
        if args.reply_loop:
            from reply_loop import run_loop

            logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
            run_loop()
            return 0
        exit_code = run(dry_run=args.dry_run)
        return exit_code
    except Exception as exc:
        logging.error("%s", exc)
        return 1
    finally:
        if (
            not args.reply_loop
            and not args.dry_run
            and os.environ.get("MONAD_ENGINE", "mock").strip().lower() == "ollama"
        ):
            from inactivity import stop_pod_after_oneshot

            stop_pod_after_oneshot()


if __name__ == "__main__":
    sys.exit(main())
