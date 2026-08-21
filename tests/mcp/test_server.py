import importlib
import importlib.util
import sys


def test_healthz_service():
    import mcp_server.server as server

    import asyncio

    response = asyncio.run(server.healthz(None))
    body = response.body.decode()
    import json

    data = json.loads(body)
    assert data["service"] == "chora-mcp"
    assert data["auth"] == "pairing-token"
    assert "chora_tool_count" not in data
    assert "geister" not in body.lower()


def test_tool_names_include_cast_vote():
    from chora_tools import CHORA_TOOLS, CHORA_WRITE_TOOLS

    names = {t["function"]["name"] for t in CHORA_TOOLS}
    assert "cast_vote" in names
    assert "chora_cast_vote" not in names
    assert "cast_vote" in CHORA_WRITE_TOOLS


def test_geister_not_imported():
    for mod in list(sys.modules):
        if mod.startswith("geister"):
            del sys.modules[mod]

    if "mcp_server.server" in sys.modules:
        del sys.modules["mcp_server.server"]

    import mcp_server.server  # noqa: F401

    assert "geister" not in sys.modules

    source = importlib.util.find_spec("mcp_server.server").origin
    with open(source, encoding="utf-8") as f:
        text = f.read()
    assert "geister" not in text.lower()
