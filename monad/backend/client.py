"""IC mainnet client for the Chora backend canister."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import cbor2
import httpx
from ic.agent import sign_request
from ic.candid import Types, decode, encode
from ic.client import Client
from ic.identity import Identity
from ic.certificate import lookup
from ic.principal import Principal

logger = logging.getLogger(__name__)

DEFAULT_HOST = "https://icp0.io"
DEFAULT_CANISTER_ID = "sea3h-pyaaa-aaaab-qhewq-cai"
DEFAULT_CANDID_PATH = Path(__file__).resolve().parents[2] / "chora_backend.did"
DEFAULT_PEM_PATH = Path(__file__).resolve().parents[1] / "keys" / "chora-monad.pem"

EPOCH_PHASE = Types.Variant(
    {
        "converse": Types.Null,
        "sealed": Types.Null,
        "deliberate": Types.Null,
        "ratify": Types.Null,
        "execute": Types.Null,
    }
)

EPOCH_STATUS = Types.Record(
    {
        "epoch_id": Types.Text,
        "phase": EPOCH_PHASE,
        "seal_at": Types.Nat64,
        "seconds_until_seal": Types.Nat,
    }
)

ALIGNMENT_COEFFICIENT = Types.Record(
    {
        "coefficient": Types.Float64,
        "citizens_total": Types.Nat,
        "citizens_current": Types.Nat,
        "membership_due": Types.Nat,
        "as_of": Types.Nat64,
    }
)

WISH = Types.Record(
    {
        "id": Types.Text,
        "author": Types.Text,
        "domain": Types.Text,
        "ciphertext": Types.Text,
        "epoch": Types.Text,
        "assistant_id": Types.Text,
        "created_at": Types.Nat64,
    }
)

BROADCAST_MESSAGE = Types.Record(
    {
        "id": Types.Text,
        "author": Types.Text,
        "body": Types.Text,
        "epoch": Types.Text,
        "created_at": Types.Nat64,
    }
)

THREAD_SUMMARY = Types.Record(
    {
        "id": Types.Text,
        "title": Types.Text,
        "participant_count": Types.Nat,
        "visibility": Types.Text,
        "last_activity_at": Types.Nat64,
        "epoch": Types.Text,
    }
)

BROADCAST_FEED = Types.Record(
    {
        "broadcasts": Types.Vec(BROADCAST_MESSAGE),
        "public_threads": Types.Vec(THREAD_SUMMARY),
    }
)

SUBMIT_PROPOSAL_INPUT = Types.Record(
    {
        "title": Types.Text,
        "description": Types.Text,
        "code_url": Types.Text,
        "code_checksum": Types.Text,
        "voting_deadline": Types.Opt(Types.Text),
        "required_threshold": Types.Opt(Types.Float64),
        "org_scope": Types.Text,
        "metadata": Types.Text,
    }
)

GGG_ERROR = Types.Variant(
    {
        "not_found": Types.Null,
        "unauthorized": Types.Null,
        "invalid_input": Types.Text,
        "conflict": Types.Text,
        "forbidden": Types.Text,
    }
)

RESULT = Types.Variant({"ok": Types.Null, "err": GGG_ERROR})
RESULT_BROADCAST_ID = Types.Variant({"ok": Types.Text, "err": GGG_ERROR})
RESULT_PROPOSAL_ID = Types.Variant({"ok": Types.Text, "err": GGG_ERROR})
RESULT_THREAD_MESSAGE_ID = Types.Variant({"ok": Types.Text, "err": GGG_ERROR})

THREAD_MESSAGE = Types.Record(
    {
        "id": Types.Text,
        "thread_id": Types.Text,
        "author": Types.Text,
        "body": Types.Text,
        "created_at": Types.Nat64,
    }
)

THREAD = Types.Record(
    {
        "id": Types.Text,
        "title": Types.Text,
        "visibility": Types.Text,
        "participant_count": Types.Nat,
        "epoch": Types.Text,
        "broadcast_id": Types.Opt(Types.Text),
        "messages": Types.Vec(THREAD_MESSAGE),
        "created_at": Types.Nat64,
        "updated_at": Types.Nat64,
    }
)


def _unwrap(value: Any) -> Any:
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict) and "value" in value[0]:
        return value[0]["value"]
    return value


def _unwrap_variant(value: dict[str, Any]) -> tuple[str, Any]:
    if len(value) != 1:
        raise ValueError(f"Expected variant with one branch, got {value!r}")
    name, payload = next(iter(value.items()))
    return name, payload


def _unwrap_ok(value: Any, *, operation: str) -> Any:
    name, payload = _unwrap_variant(_unwrap(value))
    if name == "ok":
        return payload
    if name == "err":
        raise RuntimeError(f"{operation} failed: {_format_ggg_error(payload)}")
    raise RuntimeError(f"{operation} returned unexpected variant {name!r}")


def _format_ggg_error(err: dict[str, Any]) -> str:
    name, payload = _unwrap_variant(err)
    if payload is None:
        return name
    return f"{name}: {payload}"


class ChoraBackendClient:
    """Authenticated client for Monad-gated Chora backend methods."""

    def __init__(
        self,
        *,
        pem_path: str | Path,
        host: str = DEFAULT_HOST,
        canister_id: str = DEFAULT_CANISTER_ID,
        candid_path: str | Path | None = DEFAULT_CANDID_PATH,
        max_retries: int = 5,
        retry_delay_s: float = 0.25,
    ) -> None:
        pem_text = Path(pem_path).read_text(encoding="utf-8")
        self.identity = Identity.from_pem(pem_text)
        self.host = host.rstrip("/")
        self.canister_id = canister_id
        self.candid_path = Path(candid_path) if candid_path else None
        self.max_retries = max_retries
        self.retry_delay_s = retry_delay_s
        self._client = Client(self.host)
        self._principal = self.identity.sender().to_str()

    @property
    def principal(self) -> str:
        return self._principal

    def _signed_envelope(self, request_type: str, method_name: str, arg: bytes) -> bytes:
        req = {
            "request_type": request_type,
            "sender": self.identity.sender().bytes,
            "canister_id": Principal.from_str(self.canister_id).bytes,
            "method_name": method_name,
            "arg": arg,
            "ingress_expiry": int(time.time() + 300) * 10**9,
        }
        _, data = sign_request(req, self.identity)
        return data

    def _post(self, endpoint_suffix: str, envelope: bytes) -> httpx.Response:
        url = f"{self.host}/api/v2/canister/{self.canister_id}/{endpoint_suffix}"
        return httpx.post(
            url,
            content=envelope,
            headers={"Content-Type": "application/cbor"},
            timeout=60.0,
        )

    def _query(self, method_name: str, args: list[dict[str, Any]] | None, ret_types: list[Any]) -> Any:
        arg = encode(args or [])
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            response = self._post("query", self._signed_envelope("query", method_name, arg))
            if response.status_code == 400 and "Invalid signature" in response.text:
                last_error = RuntimeError(response.text)
                logger.warning(
                    "Query %s signature rejected (attempt %d/%d)",
                    method_name,
                    attempt,
                    self.max_retries,
                )
                time.sleep(self.retry_delay_s * attempt)
                continue
            if response.status_code != 200:
                raise RuntimeError(
                    f"Query {method_name} failed with HTTP {response.status_code}: {response.text}"
                )
            payload = cbor2.loads(response.content)
            if payload.get("status") == "replied":
                return _unwrap(decode(payload["reply"]["arg"], ret_types))
            if payload.get("status") == "rejected":
                raise RuntimeError(f"Query {method_name} rejected: {payload.get('reject_message')}")
            raise RuntimeError(f"Query {method_name} returned unexpected payload: {payload!r}")
        raise RuntimeError(f"Query {method_name} failed after retries") from last_error

    def _update(self, method_name: str, args: list[dict[str, Any]], ret_types: list[Any]) -> Any:
        arg = encode(args)
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            req = {
                "request_type": "call",
                "sender": self.identity.sender().bytes,
                "canister_id": Principal.from_str(self.canister_id).bytes,
                "method_name": method_name,
                "arg": arg,
                "ingress_expiry": int(time.time() + 300) * 10**9,
            }
            req_id, envelope = sign_request(req, self.identity)
            response = self._post("call", envelope)
            if response.status_code == 400 and "Invalid signature" in response.text:
                last_error = RuntimeError(response.text)
                logger.warning(
                    "Update %s signature rejected (attempt %d/%d)",
                    method_name,
                    attempt,
                    self.max_retries,
                )
                time.sleep(self.retry_delay_s * attempt)
                continue
            if response.status_code not in (200, 202):
                raise RuntimeError(
                    f"Update {method_name} failed with HTTP {response.status_code}: {response.text}"
                )

            for _ in range(60):
                time.sleep(1)
                status_response = self._read_request_status(req_id)
                if status_response is None:
                    continue
                status, cert = status_response
                if status == "replied":
                    reply = lookup(["request_status".encode(), req_id, "reply".encode()], cert)
                    return decode(reply, ret_types)
                if status == "rejected":
                    message = lookup(
                        ["request_status".encode(), req_id, "reject_message".encode()],
                        cert,
                    )
                    raise RuntimeError(
                        f"Update {method_name} rejected: {message.decode() if message else 'unknown'}"
                    )
            raise RuntimeError(f"Update {method_name} timed out waiting for reply")
        raise RuntimeError(f"Update {method_name} failed after retries") from last_error

    def _read_request_status(self, req_id: bytes) -> tuple[str, Any] | None:
        for attempt in range(1, self.max_retries + 1):
            req = {
                "request_type": "read_state",
                "sender": self.identity.sender().bytes,
                "paths": [["request_status".encode(), req_id]],
                "ingress_expiry": int(time.time() + 300) * 10**9,
            }
            _, envelope = sign_request(req, self.identity)
            response = self._post("read_state", envelope)
            if response.status_code == 400 and "Invalid signature" in response.text:
                time.sleep(self.retry_delay_s * attempt)
                continue
            if response.status_code != 200:
                raise RuntimeError(
                    f"read_state failed with HTTP {response.status_code}: {response.text}"
                )
            payload = cbor2.loads(response.content)
            cert = cbor2.loads(payload["certificate"])
            status = lookup(["request_status".encode(), req_id, "status".encode()], cert)
            if status is None:
                return None
            return status.decode(), cert
        return None

    def get_epoch_status(self) -> dict[str, Any]:
        return self._query("get_epoch_status", None, [EPOCH_STATUS])

    def alignment_coefficient(self) -> dict[str, Any]:
        return self._query("alignment_coefficient", None, [ALIGNMENT_COEFFICIENT])

    def list_wishes_by_epoch(self, epoch_id: str) -> list[dict[str, Any]]:
        args = [{"type": Types.Text, "value": epoch_id}]
        return self._query("list_wishes_by_epoch", args, [Types.Vec(WISH)])

    def read_broadcast(self) -> dict[str, Any]:
        return self._query("read_broadcast", None, [BROADCAST_FEED])

    def list_threads(self) -> list[dict[str, Any]]:
        return self._query("list_threads", None, [Types.Vec(THREAD_SUMMARY)])

    def read_thread(self, thread_id: str) -> dict[str, Any] | None:
        args = [{"type": Types.Text, "value": thread_id}]
        result = self._query("read_thread", args, [Types.Opt(THREAD)])
        if result in (None, [], [None]):
            return None
        if isinstance(result, list):
            return result[0] if result else None
        return result

    def reply_to_thread(self, thread_id: str, body: str) -> str:
        args = [
            {"type": Types.Text, "value": thread_id},
            {"type": Types.Text, "value": body},
        ]
        return str(
            _unwrap_ok(
                self._update("reply_to_thread", args, [RESULT_THREAD_MESSAGE_ID]),
                operation="reply_to_thread",
            )
        )

    def post_broadcast(self, text: str) -> str:
        args = [{"type": Types.Text, "value": text}]
        return str(_unwrap_ok(self._update("post_broadcast", args, [RESULT_BROADCAST_ID]), operation="post_broadcast"))

    def validate_proposal(self, proposal_input: dict[str, Any]) -> None:
        args = [{"type": SUBMIT_PROPOSAL_INPUT, "value": proposal_input}]
        _unwrap_ok(self._query("validate_proposal", args, [RESULT]), operation="validate_proposal")

    def submit_proposal(self, proposal_input: dict[str, Any]) -> str:
        args = [{"type": SUBMIT_PROPOSAL_INPUT, "value": proposal_input}]
        return str(
            _unwrap_ok(self._update("submit_proposal", args, [RESULT_PROPOSAL_ID]), operation="submit_proposal")
        )

    def wishes_for_deliberation(self, epoch_id: str) -> list[dict[str, str]]:
        """Map on-chain wishes to the pipeline's lightweight wish summaries."""
        wishes: list[dict[str, str]] = []
        for wish in self.list_wishes_by_epoch(epoch_id):
            wishes.append(
                {
                    "hash": f"sha256:{wish['id']}",
                    "summary": wish.get("ciphertext", "")[:200] or f"wish {wish['id']}",
                    "id": wish["id"],
                    "domain": wish.get("domain", ""),
                    "assistant_id": wish.get("assistant_id", ""),
                }
            )
        return wishes


def load_client() -> ChoraBackendClient:
    """Construct a client from environment variables."""
    pem_path = os.environ.get("MONAD_KEY_PATH", str(DEFAULT_PEM_PATH))
    host = os.environ.get("MONAD_IC_HOST", DEFAULT_HOST)
    canister_id = os.environ.get("MONAD_CANISTER_ID", DEFAULT_CANISTER_ID)
    candid_path = os.environ.get("MONAD_CANDID_PATH", str(DEFAULT_CANDID_PATH))
    return ChoraBackendClient(
        pem_path=pem_path,
        host=host,
        canister_id=canister_id,
        candid_path=candid_path,
    )
