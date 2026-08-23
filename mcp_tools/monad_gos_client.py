#!/usr/bin/env python3
"""
Thin client for the Monad GOS backend canister.

Uses ``icp canister call`` against the live Candid interface in monad_backend.did.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional, TypedDict

MonadGosDomain = Literal[
    "finance", "justice", "land", "system", "governance", "identity"
]
ThreadVisibility = Literal["private", "public"]

MAINNET_CANISTER_ID = "sea3h-pyaaa-aaaab-qhewq-cai"
DEFAULT_IC_HOST = "https://icp0.io"

_ICP_NETWORK = {
    "staging": "ic",
    "ic": "ic",
    "mainnet": "ic",
    "demo": "ic",
    "test": "ic",
    "local": "local",
}

_MONAD_GOS_DID = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "monad_backend.did")
)


import icp_candid as _ct


class SubmitWishRequest(TypedDict):
    text: str
    domain: MonadGosDomain
    author_principal: str
    assistant_id: str


class SubmitWishResponse(TypedDict):
    wish_id: str
    epoch: str
    domain: MonadGosDomain
    author_pseudonym: str
    sealed: bool


class BroadcastMessage(TypedDict):
    id: str
    kind: Literal["broadcast", "epoch_status", "proposal_announcement"]
    body: str
    posted_at: str
    epoch: str


class ThreadSummary(TypedDict):
    id: str
    title: str
    visibility: ThreadVisibility
    epoch: str
    last_message_at: str
    message_count: int


class ThreadMessage(TypedDict):
    id: str
    author: str
    role: Literal["citizen", "monad", "system"]
    body: str
    posted_at: str


class ReadBroadcastResponse(TypedDict):
    epoch: str
    epoch_phase: str
    broadcasts: list[BroadcastMessage]
    public_thread_summaries: list[ThreadSummary]


class AlignmentCoefficientResponse(TypedDict):
    coefficient: float
    citizens_current: int
    citizens_total: int
    trend: list[dict[str, Any]]
    as_of: str


class ListThreadsResponse(TypedDict):
    threads: list[ThreadSummary]


class ReadThreadResponse(TypedDict):
    thread: ThreadSummary
    messages: list[ThreadMessage]


def _ts_to_iso(ts: Any) -> str:
    if ts is None:
        return ""
    if isinstance(ts, str):
        return ts
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return str(ts)


def _candid_text(value: str) -> str:
    return json.dumps(value)


def _candid_opt_text(value: Optional[str]) -> str:
    if value is None:
        return "null"
    return f"opt {_candid_text(value)}"


def _candid_opt_variant(status: Optional[str]) -> str:
    if not status:
        return "null"
    key = status.strip().lower()
    mapping = {
        "pending_vote": "pending_vote",
        "voting": "voting",
        "approved": "approved",
        "rejected": "rejected",
        "no_quorum": "no_quorum",
        "expired": "expired",
    }
    variant = mapping.get(key)
    if variant is None:
        raise ValueError(f"unknown proposal status {status!r}")
    return f"opt (variant {{ {variant} }})"


def _candid_vote_choice(choice: str) -> str:
    key = choice.strip().lower()
    if key not in {"yes", "no", "abstain"}:
        raise ValueError(f"vote choice must be yes/no/abstain, got {choice!r}")
    return f"(variant {{ {key} }})"


def _unwrap_result(value: Any, ok_key: str = "ok") -> Any:
    if isinstance(value, dict):
        if ok_key in value:
            return value[ok_key]
        if "err" in value:
            err = value["err"]
            if isinstance(err, dict):
                for k, v in err.items():
                    if k == "invalid_input" and isinstance(v, str):
                        raise RuntimeError(f"invalid_input: {v}")
                    if k == "conflict" and isinstance(v, str):
                        raise RuntimeError(f"conflict: {v}")
                    if k == "forbidden" and isinstance(v, str):
                        raise RuntimeError(f"forbidden: {v}")
                    if k in {"not_found", "unauthorized"}:
                        raise RuntimeError(k)
            raise RuntimeError(str(err))
    return value


def _thread_summary(raw: dict[str, Any]) -> ThreadSummary:
    return {
        "id": str(raw.get("id", "")),
        "title": str(raw.get("title", "")),
        "visibility": str(raw.get("visibility", "private")),  # type: ignore[typeddict-item]
        "epoch": str(raw.get("epoch", "")),
        "last_message_at": _ts_to_iso(raw.get("last_activity_at")),
        "message_count": int(raw.get("participant_count", 0) or 0),
    }


def _broadcast_message(raw: dict[str, Any]) -> BroadcastMessage:
    return {
        "id": str(raw.get("id", "")),
        "kind": "broadcast",
        "body": str(raw.get("body", "")),
        "posted_at": _ts_to_iso(raw.get("created_at")),
        "epoch": str(raw.get("epoch", "")),
    }


def _thread_message(raw: dict[str, Any]) -> ThreadMessage:
    author = str(raw.get("author", ""))
    return {
        "id": str(raw.get("id", "")),
        "author": author,
        "role": "citizen",
        "body": str(raw.get("body", "")),
        "posted_at": _ts_to_iso(raw.get("created_at")),
    }


@dataclass
class MonadGosClient:
    """HTTP/Candid agent for the Monad GOS backend canister."""

    canister_id: str = field(
        default_factory=lambda: os.getenv("MONAD_GOS_CANISTER_ID", MAINNET_CANISTER_ID).strip()
        or MAINNET_CANISTER_ID
    )
    network: str = field(
        default_factory=lambda: os.getenv("MONAD_GOS_NETWORK", "staging").strip() or "staging"
    )
    base_url: str = field(
        default_factory=lambda: os.getenv("MONAD_GOS_BASE_URL", DEFAULT_IC_HOST).strip()
        or DEFAULT_IC_HOST
    )
    candid_path: str = field(
        default_factory=lambda: os.getenv("MONAD_GOS_CANDID_PATH", _MONAD_GOS_DID).strip() or _MONAD_GOS_DID
    )

    def _require_canister(self) -> str:
        if not self.canister_id:
            raise ValueError(
                "MONAD_GOS_CANISTER_ID is not set; cannot reach the Monad GOS backend"
            )
        return self.canister_id

    def _icp_net(self) -> str:
        return _ICP_NETWORK.get(self.network, "ic")

    def _call(
        self,
        method: str,
        args: str = "()",
        *,
        identity: str = "",
        query: bool = False,
        timeout: int = 60,
    ) -> Any:
        target = self._require_canister()
        icp_net = self._icp_net()
        cmd = [
            "icp", "canister", "call", target, method, args,
            "-n", icp_net, "--json",
        ]
        if query:
            cmd.append("--query")
        if os.path.isfile(self.candid_path):
            cmd.extend(["--candid", self.candid_path])
        if identity:
            try:
                from icp_identity import icp_import_from_dfx

                icp_import_from_dfx(identity)
            except Exception:
                pass
            cmd.extend(["--identity", identity])

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "icp call failed").strip()
            raise RuntimeError(err)
        raw = result.stdout.strip()
        if not raw:
            return None
        envelope = json.loads(raw)
        candid_str = envelope.get("response_candid") or ""
        if not candid_str:
            return envelope
        parsed = _ct.parse(candid_str)
        if parsed is None:
            raise RuntimeError(f"failed to parse candid response for {method}")
        return parsed

    def _current_epoch(self) -> str:
        epoch = self._call("current_epoch", "()", query=True)
        return str(epoch or "")

    def submit_wish(
        self,
        request: SubmitWishRequest,
        *,
        identity: str = "",
        ciphertext: str = "",
        epoch: str = "",
    ) -> SubmitWishResponse:
        self._require_canister()
        wish_epoch = epoch or self._current_epoch()
        cipher = ciphertext or request["text"]
        args = (
            "(record { "
            f"domain = {_candid_text(request['domain'])}; "
            f"ciphertext = {_candid_text(cipher)}; "
            f"epoch = {_candid_text(wish_epoch)}; "
            f"assistant_id = {_candid_text(request.get('assistant_id') or 'monad-mcp')}; "
            "})"
        )
        raw = self._call("submit_wish", args, identity=identity, query=False)
        wish_id = str(_unwrap_result(raw))
        return {
            "wish_id": wish_id,
            "epoch": wish_epoch,
            "domain": request["domain"],
            "author_pseudonym": request["author_principal"][:8],
            "sealed": False,
        }

    def read_broadcast(self) -> ReadBroadcastResponse:
        feed = self._call("read_broadcast", "()", query=True)
        if not isinstance(feed, dict):
            feed = {}
        broadcasts = [
            _broadcast_message(item)
            for item in feed.get("broadcasts", []) or []
            if isinstance(item, dict)
        ]
        threads = [
            _thread_summary(item)
            for item in feed.get("public_threads", []) or []
            if isinstance(item, dict)
        ]
        epoch = self._current_epoch()
        status = self.get_epoch_status()
        return {
            "epoch": epoch,
            "epoch_phase": str(status.get("phase", "")),
            "broadcasts": broadcasts,
            "public_thread_summaries": threads,
        }

    def alignment_coefficient(self) -> AlignmentCoefficientResponse:
        raw = self._call("alignment_coefficient", "()", query=True)
        if not isinstance(raw, dict):
            raw = {}
        trend_raw = self._call("alignment_trend", "()", query=True)
        trend: list[dict[str, Any]] = []
        if isinstance(trend_raw, list):
            for point in trend_raw:
                if not isinstance(point, dict):
                    continue
                trend.append({
                    "epoch": str(point.get("epoch", "")),
                    "coefficient": float(point.get("coefficient", 0.0) or 0.0),
                    "as_of": _ts_to_iso(point.get("as_of")),
                })
        return {
            "coefficient": float(raw.get("coefficient", 0.0) or 0.0),
            "citizens_current": int(raw.get("citizens_current", 0) or 0),
            "citizens_total": int(raw.get("citizens_total", 0) or 0),
            "trend": trend,
            "as_of": _ts_to_iso(raw.get("as_of")),
        }

    def alignment_trend(self) -> list[dict[str, Any]]:
        raw = self._call("alignment_trend", "()", query=True)
        if not isinstance(raw, list):
            return []
        out: list[dict[str, Any]] = []
        for point in raw:
            if not isinstance(point, dict):
                continue
            out.append({
                "epoch": str(point.get("epoch", "")),
                "coefficient": float(point.get("coefficient", 0.0) or 0.0),
                "as_of": _ts_to_iso(point.get("as_of")),
            })
        return out

    def get_epoch_status(self) -> dict[str, Any]:
        raw = self._call("get_epoch_status", "()", query=True)
        if not isinstance(raw, dict):
            return {}
        phase = raw.get("phase", "")
        if isinstance(phase, dict) and len(phase) == 1:
            phase = next(iter(phase))
        return {
            "epoch_id": str(raw.get("epoch_id", "")),
            "phase": str(phase),
            "seal_at": _ts_to_iso(raw.get("seal_at")),
            "seconds_until_seal": int(raw.get("seconds_until_seal", 0) or 0),
        }

    def list_proposals(
        self,
        *,
        status: Optional[str] = None,
        org_scope: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        args = (
            "(record { "
            f"status = {_candid_opt_variant(status)}; "
            f"org_scope = {_candid_opt_text(org_scope)}; "
            f"limit = {int(limit)} : nat; "
            f"offset = {int(offset)} : nat; "
            "})"
        )
        raw = self._call("list_proposals", args, query=True)
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    def get_proposal(self, proposal_id: str) -> Optional[dict[str, Any]]:
        args = f"({_candid_text(proposal_id)})"
        raw = self._call("get_proposal", args, query=True)
        return raw if isinstance(raw, dict) else None

    def list_wishes_by_epoch(self, epoch: str = "") -> list[dict[str, Any]]:
        epoch_id = epoch or self._current_epoch()
        args = f"({_candid_text(epoch_id)})"
        raw = self._call("list_wishes_by_epoch", args, query=True)
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    def list_threads(self) -> ListThreadsResponse:
        raw = self._call("list_threads", "()", query=True)
        if not isinstance(raw, list):
            return {"threads": []}
        return {
            "threads": [
                _thread_summary(item) for item in raw if isinstance(item, dict)
            ],
        }

    def read_thread(self, thread_id: str) -> ReadThreadResponse:
        args = f"({_candid_text(thread_id)})"
        raw = self._call("read_thread", args, query=True)
        if not isinstance(raw, dict):
            raise RuntimeError("thread not found")
        messages = [
            _thread_message(item)
            for item in raw.get("messages", []) or []
            if isinstance(item, dict)
        ]
        return {
            "thread": _thread_summary(raw),
            "messages": messages,
        }

    def reply_to_broadcast(
        self, broadcast_id: str, body: str, *, identity: str = ""
    ) -> dict[str, Any]:
        args = f"({_candid_text(broadcast_id)}, {_candid_text(body)})"
        raw = self._call("reply_to_broadcast", args, identity=identity, query=False)
        thread_id = str(_unwrap_result(raw))
        return {"thread_id": thread_id}

    def reply_to_thread(
        self, thread_id: str, body: str, *, identity: str = ""
    ) -> dict[str, Any]:
        args = f"({_candid_text(thread_id)}, {_candid_text(body)})"
        raw = self._call("reply_to_thread", args, identity=identity, query=False)
        message_id = str(_unwrap_result(raw))
        return {"message_id": message_id}

    def verify_mcp_pairing(self, code: str) -> str | None:
        args = f"({_candid_text(code)})"
        raw = self._call("verify_mcp_pairing", args, query=True)
        if raw is None:
            return None
        if isinstance(raw, str):
            return raw
        return None

    def cast_vote(
        self,
        proposal_id: str,
        choice: str,
        *,
        metadata: str = "",
        identity: str = "",
    ) -> dict[str, Any]:
        args = (
            "(record { "
            f"proposal_id = {_candid_text(proposal_id)}; "
            f"choice = {_candid_vote_choice(choice)}; "
            f"metadata = {_candid_text(metadata)}; "
            "})"
        )
        raw = self._call("cast_vote", args, identity=identity, query=False)
        vote_id = str(_unwrap_result(raw))
        return {"vote_id": vote_id}


_default_client: Optional[MonadGosClient] = None


def get_client(
    *,
    canister_id: str = "",
    network: str = "",
    base_url: str = "",
) -> MonadGosClient:
    """Return a process-wide MonadGosClient, optionally overriding env defaults."""
    global _default_client
    if canister_id or network or base_url:
        return MonadGosClient(
            canister_id=canister_id or os.getenv("MONAD_GOS_CANISTER_ID", MAINNET_CANISTER_ID).strip() or MAINNET_CANISTER_ID,
            network=network or os.getenv("MONAD_GOS_NETWORK", "staging").strip() or "staging",
            base_url=base_url or os.getenv("MONAD_GOS_BASE_URL", DEFAULT_IC_HOST).strip() or DEFAULT_IC_HOST,
        )
    if _default_client is None:
        _default_client = MonadGosClient()
    return _default_client
