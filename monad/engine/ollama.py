"""Ollama HTTP API engine."""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from .base import LLMEngine

DEFAULT_OLLAMA_URL = "https://geister-ollama.realmsgos.dev"
DEFAULT_MODEL = "llama3.2"


class OllamaEngine(LLMEngine):
    """Call a remote or local Ollama ``/api/generate`` endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("MONAD_OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
        self.model = model or os.environ.get("MONAD_OLLAMA_MODEL", DEFAULT_MODEL)
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        return self._generate(prompt, json_mode=True, num_predict=2048)

    def complete_text(self, prompt: str) -> str:
        return self._generate(prompt, json_mode=False, num_predict=512)

    def _generate(self, prompt: str, *, json_mode: bool, num_predict: int) -> str:
        from inactivity import ollama_session

        url = f"{self.base_url}/api/generate"
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": num_predict},
        }
        if json_mode:
            payload["format"] = "json"
        with ollama_session(self.base_url):
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", "")).strip()
