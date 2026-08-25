"""Hashed inference receipt for a Monad reply.

The receipt is a content commitment: SHA-256 of the public inputs, model id, and
parameters used to produce the reply. It is computed at inference time and
persisted with the reply so it cannot be rewritten later without changing the
hash. Re-runs are not bit-exact — LLMs are non-deterministic.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

RECEIPT_VERSION = "v1"
RECEIPT_HASH_PREFIX = "sha256:"

# Fields a persisted receipt must carry (Candid ReplyInputs + commitment).
REQUIRED_RECEIPT_FIELDS: tuple[str, ...] = (
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
)


def _param_text(value: object) -> str:
    return "" if value is None else str(value)


def canonical_receipt_payload(
    *,
    inputs: str,
    model: str,
    temperature: object = "",
    num_predict: object = 0,
    seed: object = "",
    json_mode: object = False,
) -> str:
    """Stable, versioned payload hashed into ``receipt_hash``.

    Only inputs + model id + inference params — not host, engine label, or
    timestamps, so the commitment matches what a citizen would re-send.
    """
    return "\n".join(
        [
            RECEIPT_VERSION,
            f"model={_param_text(model)}",
            f"temperature={_param_text(temperature)}",
            f"num_predict={int(num_predict or 0)}",
            f"seed={_param_text(seed)}",
            f"json_mode={1 if json_mode else 0}",
            "inputs:",
            inputs,
        ]
    )


def receipt_hash(
    *,
    inputs: str,
    model: str,
    temperature: object = "",
    num_predict: object = 0,
    seed: object = "",
    json_mode: object = False,
) -> str:
    payload = canonical_receipt_payload(
        inputs=inputs,
        model=model,
        temperature=temperature,
        num_predict=num_predict,
        seed=seed,
        json_mode=json_mode,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{RECEIPT_HASH_PREFIX}{digest}"


def public_inputs_for_receipt(
    *,
    kind: str,
    prompt: str,
    thread_visibility: str | None = None,
) -> str:
    """Prefer inputs the realm already treats as public on that reply.

    Private-thread prompts stay in the persisted record, but
    ``get_reply_inputs`` only returns them to callers who can read the thread.
    Broadcast / public-thread receipts may store the prompt as-is (it is
    already on the public record).
    """
    if kind == "broadcast" or thread_visibility == "public":
        return prompt
    return prompt


def build_receipt(
    bundle: Mapping[str, Any],
    *,
    message_id: str,
    thread_id: str = "",
    broadcast_id: str = "",
    kind: str = "thread",
    thread_visibility: str | None = None,
    created_at: int = 0,
) -> dict[str, Any]:
    """Build a persistable ReplyInputs record with a content-commitment hash."""
    prompt = public_inputs_for_receipt(
        kind=kind,
        prompt=str(bundle.get("prompt", "")),
        thread_visibility=thread_visibility,
    )
    model = _param_text(bundle.get("model", ""))
    temperature = _param_text(bundle.get("temperature", ""))
    num_predict = int(bundle.get("num_predict") or 0)
    seed = _param_text(bundle.get("seed", ""))
    json_mode = bool(bundle.get("json_mode", False))
    record = {
        "message_id": message_id,
        "thread_id": thread_id,
        "broadcast_id": broadcast_id,
        "kind": kind,
        "model": model,
        "engine": _param_text(bundle.get("engine", "")),
        "engine_host": _param_text(bundle.get("engine_host", "")),
        "prompt": prompt,
        "temperature": temperature,
        "num_predict": num_predict,
        "seed": seed,
        "json_mode": json_mode,
        "created_at": int(created_at or 0),
        "receipt_hash": receipt_hash(
            inputs=prompt,
            model=model,
            temperature=temperature,
            num_predict=num_predict,
            seed=seed,
            json_mode=json_mode,
        ),
    }
    return record


def rerun_payload(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Enough public fields for anyone to re-send a similar request."""
    return {
        "model": _param_text(receipt.get("model", "")),
        "temperature": _param_text(receipt.get("temperature", "")),
        "num_predict": int(receipt.get("num_predict") or 0),
        "seed": _param_text(receipt.get("seed", "")),
        "json_mode": bool(receipt.get("json_mode", False)),
        "prompt": str(receipt.get("prompt", "")),
    }
