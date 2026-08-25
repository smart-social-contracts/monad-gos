"""Tests for the persisted Monad inference receipt shape and hash."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MONAD_ROOT = Path(__file__).resolve().parents[1]
if str(MONAD_ROOT) not in sys.path:
    sys.path.insert(0, str(MONAD_ROOT))

from engine.mock import MockEngine
from pipeline.converse import generate_reply_bundle
from pipeline.receipt import (
    REQUIRED_RECEIPT_FIELDS,
    RECEIPT_HASH_PREFIX,
    RECEIPT_VERSION,
    build_receipt,
    canonical_receipt_payload,
    receipt_hash,
    rerun_payload,
)


SAMPLE_INPUTS = (
    "You are the Monad of this Monad GOS realm.\n\n"
    "Conversation so far:\nCitizen: Why 12 credits?\n\nMonad:"
)


class TestReceiptShape(unittest.TestCase):
    def test_required_fields_are_stable(self) -> None:
        self.assertEqual(
            REQUIRED_RECEIPT_FIELDS,
            (
                "message_id",
                "thread_id",
                "broadcast_id",
                "kind",
                "model",
                "engine",
                "engine_host",
                "prompt",
                "temperature",
                "num_predict",
                "seed",
                "json_mode",
                "created_at",
                "receipt_hash",
            ),
        )

    def test_build_receipt_includes_every_required_field(self) -> None:
        receipt = build_receipt(
            {
                "prompt": SAMPLE_INPUTS,
                "model": "mock",
                "engine": "mock",
                "engine_host": "local",
                "temperature": "0",
                "num_predict": 0,
                "seed": "0",
                "json_mode": False,
            },
            message_id="msg-2",
            thread_id="thread-1",
            broadcast_id="broadcast-2",
            kind="thread",
        )
        for field in REQUIRED_RECEIPT_FIELDS:
            self.assertIn(field, receipt)
        self.assertTrue(receipt["receipt_hash"].startswith(RECEIPT_HASH_PREFIX))
        self.assertEqual(len(receipt["receipt_hash"]), len(RECEIPT_HASH_PREFIX) + 64)
        self.assertEqual(receipt["model"], "mock")
        self.assertEqual(receipt["prompt"], SAMPLE_INPUTS)

    def test_hash_is_deterministic(self) -> None:
        kwargs = dict(
            inputs=SAMPLE_INPUTS,
            model="mock",
            temperature="0",
            num_predict=0,
            seed="0",
            json_mode=False,
        )
        self.assertEqual(receipt_hash(**kwargs), receipt_hash(**kwargs))

    def test_known_thread_receipt_vector(self) -> None:
        digest = receipt_hash(
            inputs=(
                "You are the Monad of this Monad GOS realm.\n\n"
                "Conversation so far:\nCitizen: Why 12 credits? Last epoch it was 10.\n\nMonad:"
            ),
            model="mock",
            temperature="0",
            num_predict=0,
            seed="0",
            json_mode=False,
        )
        self.assertEqual(
            digest,
            "sha256:af8ab9797d029abe886c0da047c150b84910e98b92bf9f1555081a6d5461a771",
        )

    def test_hash_covers_inputs_model_and_params(self) -> None:
        base = dict(
            inputs=SAMPLE_INPUTS,
            model="mock",
            temperature="0",
            num_predict=0,
            seed="0",
            json_mode=False,
        )
        original = receipt_hash(**base)
        self.assertNotEqual(original, receipt_hash(**{**base, "model": "llama3.2"}))
        self.assertNotEqual(original, receipt_hash(**{**base, "temperature": "0.8"}))
        self.assertNotEqual(original, receipt_hash(**{**base, "inputs": SAMPLE_INPUTS + " extra"}))
        self.assertNotEqual(original, receipt_hash(**{**base, "seed": "99"}))

    def test_canonical_payload_is_versioned(self) -> None:
        payload = canonical_receipt_payload(
            inputs=SAMPLE_INPUTS,
            model="mock",
            temperature="0",
            num_predict=0,
            seed="0",
            json_mode=False,
        )
        self.assertTrue(payload.startswith(RECEIPT_VERSION + "\n"))
        self.assertIn("model=mock", payload)
        self.assertIn("inputs:", payload)
        self.assertIn(SAMPLE_INPUTS, payload)

    def test_rerun_payload_is_enough_to_resend(self) -> None:
        receipt = build_receipt(
            {
                "prompt": SAMPLE_INPUTS,
                "model": "llama3.2",
                "temperature": "0.8",
                "num_predict": 512,
                "seed": "",
                "json_mode": False,
            },
            message_id="msg-9",
            kind="thread",
        )
        payload = rerun_payload(receipt)
        self.assertEqual(
            set(payload),
            {"model", "temperature", "num_predict", "seed", "json_mode", "prompt"},
        )
        self.assertEqual(payload["model"], "llama3.2")
        self.assertEqual(payload["prompt"], SAMPLE_INPUTS)
        self.assertNotIn("engine_host", payload)

    def test_generate_reply_bundle_attaches_receipt_hash(self) -> None:
        bundle = generate_reply_bundle(
            MockEngine(),
            [{"author": "citizen-1", "body": "Why 12 credits?"}],
            "aaaaa-aa",
        )
        self.assertIn("receipt_hash", bundle)
        self.assertTrue(bundle["receipt_hash"].startswith(RECEIPT_HASH_PREFIX))
        recomputed = receipt_hash(
            inputs=bundle["prompt"],
            model=bundle["model"],
            temperature=bundle["temperature"],
            num_predict=bundle["num_predict"],
            seed=bundle["seed"],
            json_mode=bundle["json_mode"],
        )
        self.assertEqual(bundle["receipt_hash"], recomputed)

    def test_broadcast_receipt_uses_public_inputs_only(self) -> None:
        public_prompt = (
            "Public legislative input. Membership due is 12 credits per month. "
            "Paying keeps you current; withholding is a legitimate signal."
        )
        receipt = build_receipt(
            {
                "prompt": public_prompt,
                "model": "mock",
                "temperature": "0",
                "num_predict": 0,
                "seed": "0",
                "json_mode": False,
            },
            message_id="broadcast-2",
            broadcast_id="broadcast-2",
            kind="broadcast",
        )
        self.assertEqual(receipt["kind"], "broadcast")
        self.assertEqual(receipt["prompt"], public_prompt)
        self.assertNotIn("private thread", receipt["prompt"].lower())
        self.assertEqual(
            receipt["receipt_hash"],
            "sha256:52cd0ea65006be445e82e99e2fae162d047229e417125e6de82f800e0d14c9ec",
        )


if __name__ == "__main__":
    unittest.main()
