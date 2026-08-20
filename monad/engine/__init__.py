"""Swappable LLM engine interface for the Monad deliberation pipeline."""

from .base import LLMEngine
from .mock import MockEngine
from .ollama import OllamaEngine

__all__ = ["LLMEngine", "MockEngine", "OllamaEngine"]


def get_engine() -> LLMEngine:
    """Instantiate the configured engine from ``MONAD_ENGINE``."""
    import os

    name = os.environ.get("MONAD_ENGINE", "mock").strip().lower()
    if name == "ollama":
        return OllamaEngine()
    if name == "mock":
        return MockEngine()
    raise ValueError(f"Unknown MONAD_ENGINE: {name!r} (expected 'ollama' or 'mock')")
