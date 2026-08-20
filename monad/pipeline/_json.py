"""Tolerant JSON extraction from LLM completions.

Small models rarely return clean JSON — they wrap it in prose or markdown
fences. These helpers extract the first JSON object from a completion and parse
it, raising a clear error when none is present.
"""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_json(raw: str) -> dict[str, Any]:
    """Parse the first JSON object found in *raw*.

    Tries, in order: the whole string, a ```json fenced block, then the first
    balanced {...} span. Raises ValueError if no parseable object is found.
    """
    text = raw.strip()

    for candidate in _candidates(text):
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(parsed, dict):
            return parsed

    raise ValueError(f"No parseable JSON object in completion: {raw[:200]!r}")


def _candidates(text: str) -> list[str]:
    out = [text]
    fence = _FENCE_RE.search(text)
    if fence:
        out.append(fence.group(1))
    start = text.find("{")
    if start != -1:
        end = text.rfind("}")
        if end > start:
            out.append(text[start : end + 1])
    return out
