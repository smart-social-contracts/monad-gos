"""Conversational replies from the Monad to a citizen thread."""

from __future__ import annotations

from typing import Any

from engine.base import LLMEngine

SYSTEM_PROMPT = """You are the Monad of Chora — the realm's executive voice.
A citizen is speaking to you in a private thread.

Reply in the first person as the Monad.
Be brief: 2 to 6 sentences.
Be present and concrete. Do not be bureaucratic.
Do not claim you have already executed policy. You propose; citizens ratify.
Do not output JSON, markdown fences, or a title. Just the reply."""


def format_history(messages: list[dict[str, Any]], monad_principal: str) -> str:
    lines: list[str] = []
    for message in messages:
        author = message.get("author", "")
        speaker = "Monad" if author == monad_principal else "Citizen"
        body = str(message.get("body", "")).strip()
        if body:
            lines.append(f"{speaker}: {body}")
    return "\n".join(lines)


def build_prompt(messages: list[dict[str, Any]], monad_principal: str) -> str:
    history = format_history(messages, monad_principal)
    return f"{SYSTEM_PROMPT}\n\nConversation so far:\n{history}\n\nMonad:"


def generate_reply(
    engine: LLMEngine,
    messages: list[dict[str, Any]],
    monad_principal: str,
) -> str:
    text = engine.complete_text(build_prompt(messages, monad_principal)).strip()
    if text.startswith("Monad:"):
        text = text[len("Monad:") :].strip()
    if len(text) > 800:
        text = text[:797].rstrip() + "…"
    if not text:
        raise ValueError("empty Monad reply")
    return text
