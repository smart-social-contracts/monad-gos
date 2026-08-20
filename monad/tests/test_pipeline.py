"""Tests for the Monad deliberation pipeline."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MONAD_ROOT = Path(__file__).resolve().parents[1]
if str(MONAD_ROOT) not in sys.path:
    sys.path.insert(0, str(MONAD_ROOT))

from engine.mock import MockEngine
from pipeline.deliberation import run_deliberation
from pipeline.types import REQUIRED_FIELDS


class TestMockPipeline(unittest.TestCase):
    def test_mock_pipeline_emits_full_proposal(self) -> None:
        wishes = [
            {"hash": "sha256:wish-garden-001", "summary": "gardens"},
            {"hash": "sha256:wish-green-002", "summary": "green commons"},
        ]
        proposal = run_deliberation(MockEngine(), wishes)
        for field in REQUIRED_FIELDS:
            self.assertIn(field, proposal)
            self.assertTrue(proposal[field])


if __name__ == "__main__":
    unittest.main()
