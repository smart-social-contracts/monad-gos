"""Conversational replies from the Monad to a citizen thread."""

from __future__ import annotations

from typing import Any

from engine.base import LLMEngine

SYSTEM_PROMPT = """You are the Monad of this Monad GOS realm — the realm's executive voice.
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


def build_prompt(
    messages: list[dict[str, Any]],
    monad_principal: str,
    personality: dict | None = None,
) -> str:
    history = format_history(messages, monad_principal)
    prompt = SYSTEM_PROMPT
    if personality:
        voice = str(personality.get("voice", "")).strip()
        stance = str(personality.get("stance", "")).strip()
        description = str(personality.get("description", "")).strip()
        principles = personality.get("principles") or []
        if isinstance(principles, list):
            principle_text = ", ".join(str(p).strip() for p in principles if str(p).strip())
        else:
            principle_text = ""
        lines = ["Founding personality:"]
        if voice:
            lines.append(f"Voice: {voice}")
        if stance:
            lines.append(f"Stance: {stance}")
        if principle_text:
            lines.append(f"Principles: {principle_text}")
        if description:
            lines.append(f"Description: {description}")
        if len(lines) > 1:
            prompt = f"{SYSTEM_PROMPT}\n\n" + "\n".join(lines)
    return f"{prompt}\n\nConversation so far:\n{history}\n\nMonad:"


def generate_reply(
    engine: LLMEngine,
    messages: list[dict[str, Any]],
    monad_principal: str,
    personality: dict | None = None,
) -> str:
    return generate_reply_bundle(engine, messages, monad_principal, personality)["body"]


def generate_reply_bundle(
    engine: LLMEngine,
    messages: list[dict[str, Any]],
    monad_principal: str,
    personality: dict | None = None,
) -> dict[str, Any]:
    prompt = build_prompt(messages, monad_principal, personality)
    text = engine.complete_text(prompt).strip()
    if text.startswith("Monad:"):
        text = text[len("Monad:") :].strip()
    if len(text) > 800:
        text = text[:797].rstrip() + "…"
    if not text:
        raise ValueError("empty Monad reply")
    return {
        "body": text,
        "prompt": prompt,
        **engine.describe(),
    }
