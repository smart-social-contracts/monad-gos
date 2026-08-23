import os
import tempfile

import pytest

from mcp_server import tokens


@pytest.fixture
def token_db():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "tokens.sqlite")
        tokens.ensure_schema(path)
        yield path


def test_mint_validate_revoke(token_db):
    row = tokens.mint_token(
        "aaaaa-aa",
        label="test",
        scope="full",
        db_path=token_db,
    )
    assert row["token"].startswith("mgosmcp_")
    assert row["principal"] == "aaaaa-aa"

    info = tokens.validate_token(row["token"], db_path=token_db)
    assert info is not None
    assert info["principal"] == "aaaaa-aa"
    assert info["scope"] == "full"

    assert tokens.revoke_token(row["token"], db_path=token_db) is True
    assert tokens.validate_token(row["token"], db_path=token_db) is None


def test_read_vs_full_scope(token_db):
    read_row = tokens.mint_token("read-principal", scope="read", db_path=token_db)
    full_row = tokens.mint_token("full-principal", scope="full", db_path=token_db)

    read_info = tokens.validate_token(read_row["token"], db_path=token_db)
    full_info = tokens.validate_token(full_row["token"], db_path=token_db)

    assert read_info["scope"] == "read"
    assert full_info["scope"] == "full"


def test_list_tokens(token_db):
    tokens.mint_token("p1", label="a", db_path=token_db)
    tokens.mint_token("p2", label="b", db_path=token_db)
    rows = tokens.list_tokens(db_path=token_db)
    assert len(rows) == 2
    assert "token" not in rows[0]
    assert "token_hash" not in rows[0]


def test_list_tokens_for_principal(token_db):
    row1 = tokens.mint_token("p1", label="a", db_path=token_db)
    tokens.mint_token("p2", label="b", db_path=token_db)
    rows = tokens.list_tokens_for_principal("p1", db_path=token_db)
    assert len(rows) == 1
    assert rows[0]["id"] == row1["id"]
    assert rows[0]["principal"] == "p1"
    assert "token" not in rows[0]
    assert "token_hash" not in rows[0]


def test_revoke_token_id_owner_only(token_db):
    row = tokens.mint_token("owner", db_path=token_db)
    assert tokens.revoke_token_id("owner", row["id"], db_path=token_db) is True
    assert tokens.validate_token(row["token"], db_path=token_db) is None
    row2 = tokens.mint_token("other", db_path=token_db)
    assert tokens.revoke_token_id("owner", row2["id"], db_path=token_db) is False
