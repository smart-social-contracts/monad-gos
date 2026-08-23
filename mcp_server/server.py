#!/usr/bin/env python3
"""
Monad MCP server (Streamable HTTP).

Exposes Monad GOS citizen tools to MCP clients such as Claude. Every tool call is
scoped to the IC principal the bearer pairing token authenticates as.

Run:
    MONAD_MCP_PORT=5002 python3 -m mcp_server.server

Transport: Streamable HTTP at /mcp (stateless). Health at /healthz.
Public URL (documentation only): https://monad-mcp.realmsgos.dev
"""
from __future__ import annotations

import contextlib
import json
import logging
import os
import sys
from contextvars import ContextVar
from typing import Optional

_MONAD_GOS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_MCP_TOOLS = os.path.join(_MONAD_GOS_ROOT, "mcp_tools")
for _path in (_MONAD_GOS_ROOT, _MCP_TOOLS):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import anyio
import uvicorn
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route

from monad_gos_client import get_client

import mcp.types as types
from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend, RequireAuthMiddleware
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from monad_gos_tools import (
    MONAD_GOS_TOOLS,
    MONAD_GOS_TOOL_NAMES,
    MONAD_GOS_WRITE_TOOLS,
    execute_monad_gos_tool,
)
from mcp_server import tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("monad-mcp")

MCP_PORT = int(os.getenv("MONAD_MCP_PORT", "5002"))
MCP_HOST = os.getenv("MONAD_MCP_HOST", "127.0.0.1")
DEFAULT_NETWORK = os.getenv("MONAD_MCP_NETWORK", "ic")
DEFAULT_MONAD_GOS_CANISTER = os.getenv(
    "MONAD_GOS_CANISTER_ID", "sea3h-pyaaa-aaaab-qhewq-cai"
).strip()
MAX_RESULT_CHARS = int(os.getenv("MONAD_MCP_MAX_RESULT_CHARS", "24000"))
PUBLIC_URL = os.getenv(
    "MONAD_MCP_PUBLIC_URL", "https://monad-mcp.realmsgos.dev"
).rstrip("/")

WRITE_TOOLS = set(MONAD_GOS_WRITE_TOOLS)
ALL_TOOLS = MONAD_GOS_TOOLS

_CURRENT: ContextVar[Optional[dict]] = ContextVar("mcp_principal", default=None)
IDENTITY_INJECTED = {"author_principal"}

_SCHEMA_BY_NAME = {
    t["function"]["name"]: t["function"].get(
        "parameters", {"type": "object", "properties": {}}
    )
    for t in ALL_TOOLS
}


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _effective_scopes(scope: str) -> list[str]:
    return ["read", "full"] if scope == "full" else ["read"]


def _public_schema(schema: dict) -> dict:
    props = {
        k: v
        for k, v in schema.get("properties", {}).items()
        if k not in IDENTITY_INJECTED
    }
    required = [r for r in schema.get("required", []) if r not in IDENTITY_INJECTED]
    out = {"type": schema.get("type", "object"), "properties": props}
    if required:
        out["required"] = required
    return out


def _tools_for_scope(scope: str) -> list[types.Tool]:
    tools = []
    for entry in ALL_TOOLS:
        fn = entry["function"]
        name = fn["name"]
        if scope == "read" and name in WRITE_TOOLS:
            continue
        description = fn.get("description", "")
        if name in WRITE_TOOLS:
            description += " [Mutating action; runs on behalf of your principal.]"
        tools.append(
            types.Tool(
                name=name,
                description=description,
                inputSchema=_public_schema(
                    _SCHEMA_BY_NAME.get(name, {"type": "object", "properties": {}})
                ),
            )
        )
    return tools


class MonadGosAccessToken(AccessToken):
    user_principal: str = ""


class PairingTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> Optional[MonadGosAccessToken]:
        info = await anyio.to_thread.run_sync(tokens.validate_token, token)
        if info is None:
            return None
        return MonadGosAccessToken(
            token=token,
            client_id="pairing-token",
            scopes=_effective_scopes(info["scope"]),
            expires_at=None,
            user_principal=info["principal"],
        )


token_verifier = PairingTokenVerifier()
server: Server = Server("monad-mcp")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    ctx = _CURRENT.get()
    scope = ctx["scope"] if ctx else "read"
    return _tools_for_scope(scope)


def _cap_result(name: str, result: str) -> str:
    if not isinstance(result, str) or len(result) <= MAX_RESULT_CHARS:
        return result
    logger.warning(
        "tool %s result truncated: %d > %d chars", name, len(result), MAX_RESULT_CHARS
    )
    return json.dumps({
        "truncated": True,
        "tool": name,
        "original_length": len(result),
        "returned_length": MAX_RESULT_CHARS,
        "note": "Result was too large to return in full and has been truncated.",
        "preview": result[:MAX_RESULT_CHARS],
    })


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
    ctx = _CURRENT.get()
    if ctx is None:
        return [types.TextContent(type="text", text=json.dumps({"error": "unauthenticated"}))]

    principal = ctx["principal"]
    scope = ctx["scope"]

    if name not in _SCHEMA_BY_NAME:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": f"unknown tool '{name}'"}),
            )
        ]
    if scope == "read" and name in WRITE_TOOLS:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "error": (
                        f"tool '{name}' requires a full-access token; "
                        "this token is read-only"
                    ),
                }),
            )
        ]

    args = dict(arguments or {})
    props = _SCHEMA_BY_NAME[name].get("properties", {})
    if "author_principal" in props and not args.get("author_principal"):
        args["author_principal"] = principal

    monad_gos_id = (
        args.pop("monad_gos_canister_id", "")
        or args.pop("realm_id", "")
        or DEFAULT_MONAD_GOS_CANISTER
    )

    def _run() -> str:
        return execute_monad_gos_tool(
            name,
            args,
            network=DEFAULT_NETWORK,
            monad_gos_canister_id=monad_gos_id,
            user_principal=principal,
            user_identity="",
        )

    try:
        if name in MONAD_GOS_TOOL_NAMES:
            result = await anyio.to_thread.run_sync(_run)
        else:
            result = json.dumps({"error": f"unknown tool '{name}'"})
    except Exception as e:
        logger.exception("tool %s failed", name)
        result = json.dumps({"error": str(e)})

    result = _cap_result(name, result)
    return [types.TextContent(type="text", text=result)]


session_manager = StreamableHTTPSessionManager(
    app=server,
    json_response=True,
    stateless=True,
)


async def _handle_mcp(scope, receive, send):
    await session_manager.handle_request(scope, receive, send)


class PrincipalContextMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        user = scope.get("user")
        tok = getattr(user, "access_token", None) if user else None
        if tok is None:
            await self.app(scope, receive, send)
            return
        effective = "full" if "full" in (tok.scopes or []) else "read"
        reset = _CURRENT.set(
            {"principal": getattr(tok, "user_principal", ""), "scope": effective}
        )
        try:
            await self.app(scope, receive, send)
        finally:
            _CURRENT.reset(reset)


async def healthz(_request: Request):
    return JSONResponse({
        "status": "ok",
        "service": "monad-mcp",
        "network": DEFAULT_NETWORK,
        "tool_count": len(ALL_TOOLS),
        "canister": DEFAULT_MONAD_GOS_CANISTER or None,
        "auth": "pairing-token",
    })


async def root(_request: Request):
    return PlainTextResponse(
        "Monad MCP server. Connect an MCP client to /mcp with "
        "Authorization: Bearer <mgosmcp_... pairing token>."
    )


async def _principal_from_pairing_code(code: str | None) -> str:
    if not code:
        raise HTTPException(status_code=400, detail="pairing_code is required")
    principal = await anyio.to_thread.run_sync(
        lambda: get_client().verify_mcp_pairing(code)
    )
    if not principal:
        raise HTTPException(status_code=401, detail="invalid pairing code")
    return principal


async def api_settings(_request: Request):
    return JSONResponse({
        "service": "monad-mcp",
        "mcp_url": f"{PUBLIC_URL}/mcp",
        "public_url": PUBLIC_URL,
    })


async def api_mint_token(request: Request):
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid JSON body") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON object required")

    principal = await _principal_from_pairing_code(body.get("pairing_code"))
    label = body.get("label") or ""
    scope = body.get("scope") or "read"
    ttl_days = body.get("ttl_days")

    try:
        row = await anyio.to_thread.run_sync(
            lambda: tokens.mint_token(
                principal,
                label=label,
                scope=scope,
                ttl_days=ttl_days,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    token = row.pop("token")
    return JSONResponse({"token": token, "metadata": row}, status_code=201)


async def api_list_tokens(request: Request):
    principal = await _principal_from_pairing_code(
        request.query_params.get("pairing_code")
    )
    rows = await anyio.to_thread.run_sync(tokens.list_tokens_for_principal, principal)
    return JSONResponse({"tokens": rows})


async def api_revoke_token(request: Request):
    token_id = request.path_params.get("id")
    try:
        token_id_int = int(token_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="invalid token id") from None

    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid JSON body") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON object required")

    principal = await _principal_from_pairing_code(body.get("pairing_code"))
    revoked = await anyio.to_thread.run_sync(
        tokens.revoke_token_id, principal, token_id_int
    )
    if not revoked:
        raise HTTPException(status_code=404, detail="token not found")
    return JSONResponse({"revoked": True})


@contextlib.asynccontextmanager
async def lifespan(_app):
    try:
        tokens.ensure_schema()
    except Exception as e:
        logger.warning("could not ensure token schema at startup: %s", e)
    async with session_manager.run():
        _log(
            f"[monad-mcp] listening on {MCP_HOST}:{MCP_PORT} "
            f"(network={DEFAULT_NETWORK}, public_url={PUBLIC_URL})"
        )
        yield


_mcp_app = AuthenticationMiddleware(
    AuthContextMiddleware(
        RequireAuthMiddleware(
            PrincipalContextMiddleware(_handle_mcp),
            required_scopes=["read"],
            resource_metadata_url=None,
        )
    ),
    backend=BearerAuthBackend(token_verifier),
)
_mcp_app = CORSMiddleware(
    _mcp_app,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id", "WWW-Authenticate"],
)

_routes = [
    Route("/", root, methods=["GET"]),
    Route("/healthz", healthz, methods=["GET"]),
    Route("/api/settings", api_settings, methods=["GET"]),
    Route("/api/tokens", api_mint_token, methods=["POST"]),
    Route("/api/tokens", api_list_tokens, methods=["GET"]),
    Route("/api/tokens/{id}", api_revoke_token, methods=["DELETE"]),
    Mount("/mcp", app=_mcp_app),
]

_starlette_app = Starlette(debug=False, routes=_routes, lifespan=lifespan)
_starlette_app = CORSMiddleware(
    _starlette_app,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


class _McpSlashAdapter:
    """Let /mcp and /mcp/ both reach the Streamable HTTP transport."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("path") == "/mcp":
            scope = dict(scope)
            scope["path"] = "/mcp/"
            if scope.get("raw_path") in (b"/mcp", None):
                scope["raw_path"] = b"/mcp/"
        await self.app(scope, receive, send)


app = _McpSlashAdapter(_starlette_app)


if __name__ == "__main__":
    uvicorn.run(app, host=MCP_HOST, port=MCP_PORT, log_level="info")
