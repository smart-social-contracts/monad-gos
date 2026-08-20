"""Poll citizen threads and post Monad replies."""

from __future__ import annotations

import atexit
import logging
import time
from typing import Any

from backend.client import ChoraBackendClient
from engine.base import LLMEngine
from pipeline.converse import generate_reply_bundle

logger = logging.getLogger(__name__)


def _last_message(thread: dict[str, Any]) -> dict[str, Any] | None:
    messages = thread.get("messages") or []
    return messages[-1] if messages else None


def reply_if_needed(
    backend: ChoraBackendClient,
    engine: LLMEngine,
    thread_id: str,
    *,
    in_flight: set[str],
) -> str | None:
    if thread_id in in_flight:
        return None
    thread = backend.read_thread(thread_id)
    if not thread:
        return None
    last = _last_message(thread)
    if last is None:
        return None
    if last.get("author") == backend.principal:
        return None

    in_flight.add(thread_id)
    try:
        bundle = generate_reply_bundle(engine, thread.get("messages") or [], backend.principal)
        message_id = backend.reply_to_thread(thread_id, bundle["body"])
        backend.record_reply_inputs(
            {
                **bundle,
                "message_id": message_id,
                "thread_id": thread_id,
                "kind": "thread",
            }
        )
        logger.info("Replied to %s as %s", thread_id, message_id)
        return message_id
    finally:
        in_flight.discard(thread_id)


def tick(backend: ChoraBackendClient, engine: LLMEngine, in_flight: set[str]) -> int:
    replied = 0
    try:
        summaries = backend.list_threads()
    except Exception:
        logger.exception("Failed to list threads")
        return 0
    for summary in summaries:
        thread_id = summary.get("id")
        if not thread_id:
            continue
        try:
            if reply_if_needed(backend, engine, thread_id, in_flight=in_flight):
                replied += 1
        except Exception:
            logger.exception("Failed to reply to %s", thread_id)
    return replied


def run_loop(*, interval_s: float = 3.0) -> None:
    from backend import load_client
    from engine import get_engine
    from engine.ollama import OllamaEngine

    backend = load_client()
    engine = get_engine()
    in_flight: set[str] = set()
    logger.info("Monad reply loop starting as %s", backend.principal)

    if isinstance(engine, OllamaEngine):
        from inactivity import (
            clear_reply_loop_running,
            mark_reply_loop_running,
            start_inactivity_monitor,
        )

        mark_reply_loop_running()
        atexit.register(clear_reply_loop_running)
        start_inactivity_monitor()

    try:
        while True:
            try:
                tick(backend, engine, in_flight)
            except Exception:
                logger.exception("Reply loop tick failed")
            time.sleep(interval_s)
    finally:
        if isinstance(engine, OllamaEngine):
            from inactivity import clear_reply_loop_running

            clear_reply_loop_running()
