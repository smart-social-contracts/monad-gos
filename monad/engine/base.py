"""Abstract LLM engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMEngine(ABC):
    """Swappable backend for proposer / critic / judge LLM calls."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Return the model's completion for *prompt*."""

    def complete_text(self, prompt: str) -> str:
        """Plain-text completion (no JSON constraint). Defaults to ``complete``."""
        return self.complete(prompt)

    def describe(self) -> dict[str, object]:
        """Public engine metadata for a reproducibility record."""
        return {
            "engine": "unknown",
            "model": "",
            "engine_host": "",
            "temperature": "",
            "num_predict": 0,
            "seed": "",
            "json_mode": False,
        }
