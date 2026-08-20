#!/usr/bin/env python3
"""
Pairing tokens for the Chora MCP server.

Stores only SHA-256 hashes in SQLite. Plaintext tokens use the ``chmcp_`` prefix
and are shown once at mint time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

TOKEN_PREFIX = "chmcp_"
VALID_SCOPES = ("read", "full")


def _default_db_path() -> str:
    return os.path.expanduser(
        os.getenv("CHORA_MCP_TOKEN_DB", "~/.chora/mcp-tokens.sqlite")
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or _default_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(db_path: Optional[str] = None) -> None:
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mcp_tokens (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash     TEXT NOT NULL UNIQUE,
                principal      TEXT NOT NULL,
                label          TEXT DEFAULT '',
                scope          TEXT NOT NULL DEFAULT 'read',
                created_at     TEXT NOT NULL,
                last_used_at   TEXT,
                expires_at     TEXT,
                revoked        INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mcp_tokens_principal ON mcp_tokens (principal)"
        )
        conn.commit()
    finally:
        conn.close()


def mint_token(
    principal: str,
    *,
    label: str = "",
    scope: str = "read",
    ttl_days: Optional[int] = None,
    db_path: Optional[str] = None,
) -> dict:
    if not principal:
        raise ValueError("principal is required")
    if scope not in VALID_SCOPES:
        raise ValueError(f"scope must be one of {VALID_SCOPES}")

    ensure_schema(db_path)
    raw = TOKEN_PREFIX + secrets.token_urlsafe(32)
    token_hash = _hash(raw)
    created_at = _now()
    expires_at = created_at + timedelta(days=ttl_days) if ttl_days else None

    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO mcp_tokens
                (token_hash, principal, label, scope, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                token_hash,
                principal,
                label,
                scope,
                _iso(created_at),
                _iso(expires_at),
            ),
        )
        conn.commit()
        row = {
            "id": cur.lastrowid,
            "principal": principal,
            "label": label,
            "scope": scope,
            "created_at": _iso(created_at),
            "expires_at": _iso(expires_at),
            "token": raw,
        }
    finally:
        conn.close()
    return row


def validate_token(token: str, db_path: Optional[str] = None) -> Optional[dict]:
    if not token or not token.startswith(TOKEN_PREFIX):
        return None

    ensure_schema(db_path)
    token_hash = _hash(token)
    conn = _connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT id, principal, scope, expires_at, revoked
            FROM mcp_tokens
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        if row is None or row["revoked"]:
            return None

        expires_at = _parse_iso(row["expires_at"])
        if expires_at is not None and expires_at < _now():
            return None

        conn.execute(
            "UPDATE mcp_tokens SET last_used_at = ? WHERE id = ?",
            (_iso(_now()), row["id"]),
        )
        conn.commit()
        return {
            "token_id": row["id"],
            "principal": row["principal"],
            "scope": row["scope"],
        }
    finally:
        conn.close()


def list_tokens(db_path: Optional[str] = None) -> list[dict]:
    ensure_schema(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, principal, label, scope, created_at, last_used_at, expires_at, revoked
            FROM mcp_tokens
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def list_tokens_for_principal(
    principal: str, db_path: Optional[str] = None
) -> list[dict]:
    if not principal:
        raise ValueError("principal is required")

    ensure_schema(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, principal, label, scope, created_at, last_used_at, expires_at, revoked
            FROM mcp_tokens
            WHERE principal = ?
            ORDER BY created_at DESC
            """,
            (principal,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def revoke_token_id(
    principal: str, token_id: int, db_path: Optional[str] = None
) -> bool:
    if not principal:
        raise ValueError("principal is required")

    ensure_schema(db_path)
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """
            UPDATE mcp_tokens SET revoked = 1
            WHERE id = ? AND principal = ? AND revoked = 0
            """,
            (token_id, principal),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def revoke_token(token_or_prefix: str, db_path: Optional[str] = None) -> bool:
    if not token_or_prefix:
        raise ValueError("token or hash prefix is required")

    ensure_schema(db_path)
    conn = _connect(db_path)
    try:
        if token_or_prefix.startswith(TOKEN_PREFIX):
            token_hash = _hash(token_or_prefix)
            cur = conn.execute(
                """
                UPDATE mcp_tokens SET revoked = 1
                WHERE token_hash = ? AND revoked = 0
                """,
                (token_hash,),
            )
        else:
            prefix = token_or_prefix.lower()
            cur = conn.execute(
                """
                UPDATE mcp_tokens SET revoked = 1
                WHERE revoked = 0 AND token_hash LIKE ?
                """,
                (prefix + "%",),
            )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def _cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Chora MCP pairing tokens")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_mint = sub.add_parser("mint", help="Mint a new pairing token")
    p_mint.add_argument("--principal", required=True, help="IC principal to bind")
    p_mint.add_argument("--label", default="", help="Human label (e.g. 'claude')")
    p_mint.add_argument("--scope", default="read", choices=VALID_SCOPES)
    p_mint.add_argument("--ttl-days", type=int, default=None, help="Optional expiry in days")

    sub.add_parser("list", help="List all tokens (metadata only)")

    p_revoke = sub.add_parser("revoke", help="Revoke by plaintext token or hash prefix")
    p_revoke.add_argument("token_or_prefix", help="Plaintext token or token_hash prefix")

    args = parser.parse_args(argv)

    if args.cmd == "mint":
        row = mint_token(
            args.principal,
            label=args.label,
            scope=args.scope,
            ttl_days=args.ttl_days,
        )
        print(json.dumps(row, indent=2))
        print("\n*** Copy the token now — it will not be shown again. ***", file=sys.stderr)
        return 0
    if args.cmd == "list":
        print(json.dumps(list_tokens(), indent=2))
        return 0
    if args.cmd == "revoke":
        ok = revoke_token(args.token_or_prefix)
        print(json.dumps({"revoked": ok}))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
