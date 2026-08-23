#!/usr/bin/env python3
"""
Monad MCP tool definitions for the Monad MCP server.
"""
from __future__ import annotations

import inspect
import json
import logging
from typing import Optional

from monad_gos_client import MonadGosDomain, get_client

log = logging.getLogger(__name__)

_MONAD_GOS_DOMAIN_ENUM: list[str] = [
    "finance",
    "justice",
    "land",
    "system",
    "governance",
    "identity",
]

_DELEGATION_ERROR = {
    "error": (
        "On-chain writes must be signed as your Internet Identity principal. "
        "Monad MCP binds your principal via a pairing token but does not hold "
        "an II session delegation key yet, so mutating Monad GOS canister calls "
        "cannot be signed on your behalf."
    ),
    "error_code": "delegation_unavailable",
    "required": "II session delegation (not just pairing-token identity binding)",
}


def _delegation_blocked(identity: str) -> Optional[str]:
    if identity and str(identity).strip():
        return None
    return json.dumps(_DELEGATION_ERROR)


# =============================================================================
# Tool implementations
# =============================================================================

def submit_wish(
    text: str,
    domain: str,
    author_principal: str = "",
    assistant_id: str = "monad-mcp",
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Submit a citizen wish to the Monad GOS Agora canister."""
    blocked = _delegation_blocked(identity)
    if blocked:
        return blocked

    if domain not in _MONAD_GOS_DOMAIN_ENUM:
        return json.dumps({
            "error": (
                f"domain must be one of {_MONAD_GOS_DOMAIN_ENUM}, got {domain!r}"
            ),
        })

    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.submit_wish(
            {
                "text": text,
                "domain": domain,  # type: ignore[typeddict-item]
                "author_principal": author_principal,
                "assistant_id": assistant_id or "monad-mcp",
            },
            identity=identity,
        )
        return json.dumps(result)
    except Exception as e:
        log.exception("submit_wish failed")
        return json.dumps({"error": str(e)})


def read_broadcast(
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Read the Monad's broadcast feed and public thread summaries."""
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.read_broadcast()
        return json.dumps(result)
    except Exception as e:
        log.exception("read_broadcast failed")
        return json.dumps({"error": str(e)})


def alignment_coefficient(
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Read the current alignment coefficient (% citizens current on membership due)."""
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.alignment_coefficient()
        return json.dumps(result)
    except Exception as e:
        log.exception("alignment_coefficient failed")
        return json.dumps({"error": str(e)})


def alignment_trend(
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Read alignment coefficient history by epoch."""
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.alignment_trend()
        return json.dumps({"trend": result})
    except Exception as e:
        log.exception("alignment_trend failed")
        return json.dumps({"error": str(e)})


def get_epoch_status(
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Read the current epoch id, phase, and seal countdown."""
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.get_epoch_status()
        return json.dumps(result)
    except Exception as e:
        log.exception("get_epoch_status failed")
        return json.dumps({"error": str(e)})


def list_proposals(
    status: str = "",
    org_scope: str = "",
    limit: int = 50,
    offset: int = 0,
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """List governance proposals on the Monad GOS backend."""
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.list_proposals(
            status=status or None,
            org_scope=org_scope or None,
            limit=limit,
            offset=offset,
        )
        return json.dumps({"proposals": result})
    except Exception as e:
        log.exception("list_proposals failed")
        return json.dumps({"error": str(e)})


def get_proposal(
    proposal_id: str,
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Read one governance proposal by id."""
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.get_proposal(proposal_id)
        if result is None:
            return json.dumps({"error": "proposal not found", "error_code": "not_found"})
        return json.dumps({"proposal": result})
    except Exception as e:
        log.exception("get_proposal failed")
        return json.dumps({"error": str(e)})


def list_wishes_by_epoch(
    epoch: str = "",
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """List wishes submitted in an epoch (defaults to current)."""
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.list_wishes_by_epoch(epoch)
        return json.dumps({"wishes": result, "epoch": epoch or "current"})
    except Exception as e:
        log.exception("list_wishes_by_epoch failed")
        return json.dumps({"error": str(e)})


def list_threads(
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """List conversational threads (private and public) for the authenticated citizen."""
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.list_threads()
        return json.dumps(result)
    except Exception as e:
        log.exception("list_threads failed")
        return json.dumps({"error": str(e)})


def read_thread(
    thread_id: str,
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Read a single conversational thread by id."""
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.read_thread(thread_id)
        return json.dumps(result)
    except Exception as e:
        log.exception("read_thread failed")
        return json.dumps({"error": str(e)})


def reply_to_broadcast(
    broadcast_id: str,
    body: str,
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Reply to a Monad broadcast, opening or continuing a thread."""
    blocked = _delegation_blocked(identity)
    if blocked:
        return blocked
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.reply_to_broadcast(broadcast_id, body, identity=identity)
        return json.dumps(result)
    except Exception as e:
        log.exception("reply_to_broadcast failed")
        return json.dumps({"error": str(e)})


def reply_to_thread(
    thread_id: str,
    body: str,
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Post a message to an existing thread."""
    blocked = _delegation_blocked(identity)
    if blocked:
        return blocked
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.reply_to_thread(thread_id, body, identity=identity)
        return json.dumps(result)
    except Exception as e:
        log.exception("reply_to_thread failed")
        return json.dumps({"error": str(e)})


def cast_vote(
    proposal_id: str,
    choice: str,
    metadata: str = "",
    network: str = "staging",
    monad_gos_canister_id: str = "",
    identity: str = "",
) -> str:
    """Cast a vote on a Monad GOS governance proposal (yes/no/abstain)."""
    blocked = _delegation_blocked(identity)
    if blocked:
        return blocked
    client = get_client(canister_id=monad_gos_canister_id, network=network)
    try:
        result = client.cast_vote(
            proposal_id, choice, metadata=metadata, identity=identity,
        )
        return json.dumps(result)
    except Exception as e:
        log.exception("cast_vote failed")
        return json.dumps({"error": str(e)})


# =============================================================================
# Tool definitions (OpenAI-compatible format, same as REALM_TOOLS)
# =============================================================================

MONAD_GOS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "submit_wish",
            "description": (
                "Submit a citizen wish to the Monad GOS Agora. The wish body is "
                "encrypted to the Monad's vetKey; only a coarse domain tag stays "
                "cleartext for routing. Your author_principal is filled from "
                "your authenticated identity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The wish text (encrypted on chain)",
                    },
                    "domain": {
                        "type": "string",
                        "description": "Coarse routing domain (cleartext)",
                        "enum": _MONAD_GOS_DOMAIN_ENUM,
                    },
                    "author_principal": {
                        "type": "string",
                        "description": "Citizen principal submitting the wish",
                    },
                },
                "required": ["text", "domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_broadcast",
            "description": (
                "Read the Monad's broadcast feed (state-of-the-realm, epoch "
                "announcements, proposal links) plus summaries of public threads."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "alignment_coefficient",
            "description": (
                "Read the alignment coefficient: the percentage of citizens "
                "current on their membership due, with recent trend."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "alignment_trend",
            "description": "Read alignment coefficient history by epoch.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_epoch_status",
            "description": "Read the current Monad GOS epoch id, phase, and seal countdown.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_proposals",
            "description": "List governance proposals on the Monad GOS backend.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Optional filter: pending_vote, voting, approved, rejected, no_quorum, expired",
                    },
                    "org_scope": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_proposal",
            "description": "Read one Monad GOS governance proposal by id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proposal_id": {"type": "string"},
                },
                "required": ["proposal_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_wishes_by_epoch",
            "description": "List citizen wishes for an epoch (defaults to current).",
            "parameters": {
                "type": "object",
                "properties": {
                    "epoch": {"type": "string", "description": "Epoch id; omit for current"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_threads",
            "description": (
                "List conversational threads between citizens and the Monad "
                "(private citizen+Monad threads and public group threads)."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_thread",
            "description": "Read the full message history of a conversational thread.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "string",
                        "description": "Thread id from list_threads or read_broadcast",
                    },
                },
                "required": ["thread_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reply_to_broadcast",
            "description": "Reply to a Monad broadcast message, opening or continuing a thread.",
            "parameters": {
                "type": "object",
                "properties": {
                    "broadcast_id": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["broadcast_id", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reply_to_thread",
            "description": "Post a message to an existing Monad GOS thread.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["thread_id", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cast_vote",
            "description": (
                "Cast a vote on a Monad GOS governance proposal (yes, no, or abstain)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "proposal_id": {"type": "string"},
                    "choice": {
                        "type": "string",
                        "enum": ["yes", "no", "abstain"],
                    },
                    "metadata": {"type": "string", "default": ""},
                },
                "required": ["proposal_id", "choice"],
            },
        },
    },
]

MONAD_GOS_WRITE_TOOLS = frozenset({
    "submit_wish",
    "reply_to_broadcast",
    "reply_to_thread",
    "cast_vote",
})

MONAD_GOS_TOOL_NAMES = frozenset(t["function"]["name"] for t in MONAD_GOS_TOOLS)

_MONAD_GOS_CANISTER_PARAM = {
    "type": "string",
    "description": (
        "Canister ID of the Monad GOS backend to interact with. "
        "Falls back to MONAD_GOS_CANISTER_ID env."
    ),
}
for _tool in MONAD_GOS_TOOLS:
    _params = _tool["function"]["parameters"]
    _params.setdefault("properties", {})
    _params["properties"]["monad_gos_canister_id"] = _MONAD_GOS_CANISTER_PARAM

TOOL_FUNCTIONS = {
    "submit_wish": submit_wish,
    "read_broadcast": read_broadcast,
    "alignment_coefficient": alignment_coefficient,
    "alignment_trend": alignment_trend,
    "get_epoch_status": get_epoch_status,
    "list_proposals": list_proposals,
    "get_proposal": get_proposal,
    "list_wishes_by_epoch": list_wishes_by_epoch,
    "list_threads": list_threads,
    "read_thread": read_thread,
    "reply_to_broadcast": reply_to_broadcast,
    "reply_to_thread": reply_to_thread,
    "cast_vote": cast_vote,
}


def execute_monad_gos_tool(
    tool_name: str,
    arguments: dict,
    *,
    network: str = "staging",
    monad_gos_canister_id: str = "",
    user_principal: str = "",
    user_identity: str = "",
) -> str:
    """Execute a Monad GOS tool by name."""
    if tool_name not in TOOL_FUNCTIONS:
        return json.dumps({"error": f"Unknown Monad GOS tool '{tool_name}'"})

    if monad_gos_canister_id and "monad_gos_canister_id" not in (arguments or {}):
        arguments = dict(arguments or {})
        arguments["monad_gos_canister_id"] = monad_gos_canister_id

    func = TOOL_FUNCTIONS[tool_name]
    valid_params = set(inspect.signature(func).parameters.keys())

    filtered_args: dict = {
        "network": network,
        "monad_gos_canister_id": monad_gos_canister_id,
        "identity": user_identity,
    }

    if "author_principal" in valid_params and user_principal:
        filtered_args["author_principal"] = user_principal

    for key, value in (arguments or {}).items():
        if key in valid_params:
            filtered_args[key] = value

    if "monad_gos_canister_id" not in valid_params:
        filtered_args.pop("monad_gos_canister_id", None)
    if "identity" not in valid_params:
        filtered_args.pop("identity", None)

    try:
        return func(**filtered_args)
    except TypeError as e:
        return json.dumps({"error": str(e)})
