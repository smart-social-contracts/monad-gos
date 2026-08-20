"""Ollama HTTP API engine."""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from urllib.parse import urlparse

from .base import LLMEngine

DEFAULT_OLLAMA_URL = "https://geister-ollama.realmsgos.dev"
DEFAULT_MODEL = "llama3.2"
DEFAULT_TEMPERATURE = "0.8"
DEFAULT_NUM_PREDICT_TEXT = 512


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
        return self._generate(prompt, json_mode=False, num_predict=DEFAULT_NUM_PREDICT_TEXT)

    def describe(self) -> dict[str, object]:
        return {
            "engine": "ollama",
            "model": self.model,
            "engine_host": urlparse(self.base_url).netloc,
            "temperature": DEFAULT_TEMPERATURE,
            "num_predict": DEFAULT_NUM_PREDICT_TEXT,
            "seed": "",
            "json_mode": False,
        }

    def _generate(self, prompt: str, *, json_mode: bool, num_predict: int) -> str:
        from inactivity import ollama_session

        url = f"{self.base_url}/api/generate"
        options: dict[str, Any] = {
            "num_predict": num_predict,
            "temperature": float(DEFAULT_TEMPERATURE),
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if json_mode:
            payload["format"] = "json"
        with ollama_session(self.base_url):
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", "")).strip()
