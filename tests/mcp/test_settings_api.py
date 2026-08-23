import json
import os
import tempfile

import pytest
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette.applications import Starlette

import mcp_server.server as server
from mcp_server import tokens


@pytest.fixture
def token_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "tokens.sqlite")
        tokens.ensure_schema(path)
        monkeypatch.setenv("MONAD_MCP_TOKEN_DB", path)
        yield path


@pytest.fixture
def mock_principal(monkeypatch):
    principal = "aaaaa-aa"

    class FakeClient:
        def verify_mcp_pairing(self, code: str):
            if code == "valid-code":
                return principal
            return None

    monkeypatch.setattr(server, "get_client", lambda: FakeClient())
    return principal


@pytest.fixture
def client(token_db):
    routes = [
        Route("/api/settings", server.api_settings, methods=["GET"]),
        Route("/api/tokens", server.api_mint_token, methods=["POST"]),
        Route("/api/tokens", server.api_list_tokens, methods=["GET"]),
        Route("/api/tokens/{id}", server.api_revoke_token, methods=["DELETE"]),
    ]
    app = CORSMiddleware(
        Starlette(routes=routes),
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    with TestClient(app) as test_client:
        yield test_client


def test_settings_payload(client):
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "monad-mcp"
    assert data["mcp_url"].endswith("/mcp")
    assert data["public_url"] == server.PUBLIC_URL


def test_mint_rejected_without_pairing(client):
    response = client.post("/api/tokens", json={})
    assert response.status_code == 400


def test_mint_rejected_invalid_pairing(client, mock_principal):
    response = client.post("/api/tokens", json={"pairing_code": "bad-code"})
    assert response.status_code == 401


def test_mint_list_revoke(client, mock_principal):
    mint = client.post(
        "/api/tokens",
        json={
            "pairing_code": "valid-code",
            "label": "claude",
            "scope": "read",
            "ttl_days": 30,
        },
    )
    assert mint.status_code == 201
    mint_data = mint.json()
    assert mint_data["token"].startswith("mgosmcp_")
    metadata = mint_data["metadata"]
    assert metadata["label"] == "claude"
    assert metadata["scope"] == "read"
    assert "token" not in metadata
    token_id = metadata["id"]

    listed = client.get("/api/tokens", params={"pairing_code": "valid-code"})
    assert listed.status_code == 200
    rows = listed.json()["tokens"]
    assert len(rows) == 1
    assert rows[0]["id"] == token_id
    assert rows[0]["label"] == "claude"

    revoked = client.request(
        "DELETE",
        f"/api/tokens/{token_id}",
        content=json.dumps({"pairing_code": "valid-code"}),
        headers={"Content-Type": "application/json"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["revoked"] is True

    info = tokens.validate_token(mint_data["token"])
    assert info is None
