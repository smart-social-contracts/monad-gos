# Monad MCP server

Monad GOS runs its own **Streamable HTTP MCP server** for citizen tools. Connect
Claude, ChatGPT, or any MCP client to Monad GOS directly — not via Geister.

## Layout

| Path | Purpose |
|------|---------|
| `mcp_server/server.py` | Streamable HTTP MCP at `/mcp`, health at `/healthz` |
| `mcp_server/tokens.py` | SQLite pairing tokens (`mgosmcp_...`) |
| `mcp_server/run.sh` | start / stop / status / logs / fg |
| `mcp_tools/monad_gos_tools.py` | Tool definitions + `execute_monad_gos_tool()` |
| `mcp_tools/monad_gos_client.py` | Live IC client (`icp canister call` + `monad_backend.did`) |
| `mcp_tools/icp_candid.py` | Candid response parser |

## Run locally

```bash
cd /srv/dev/monad-gos
chmod +x mcp_server/run.sh
MONAD_MCP_PUBLIC_URL=http://localhost:5002 \
MONAD_MCP_NETWORK=ic \
MONAD_GOS_CANISTER_ID=sea3h-pyaaa-aaaab-qhewq-cai \
./mcp_server/run.sh fg
```

Or in the background:

```bash
./mcp_server/run.sh start
curl -s http://127.0.0.1:5002/healthz
```

Default bind: `127.0.0.1:5002`. Public URL (docs only):
`https://monad-mcp.realmsgos.dev`.

## Mint a pairing token

```bash
cd /srv/dev/monad-gos
PYTHONPATH=. python3 -m mcp_server.tokens mint \
  --principal YOUR_IC_PRINCIPAL \
  --scope full \
  --label "claude"
```

Copy the `mgosmcp_...` token once. List or revoke:

```bash
python3 -m mcp_server.tokens list
python3 -m mcp_server.tokens revoke mgosmcp_...   # or a token_hash prefix
```

Token DB default: `~/.monad-gos/mcp-tokens.sqlite` (`MONAD_MCP_TOKEN_DB`).

## Connect Claude (local)

Point your MCP client at:

```
http://localhost:5002/mcp
```

Header:

```
Authorization: Bearer mgosmcp_...
```

Read-scoped tokens hide write tools. Full-scoped tokens can call mutating tools;
writes still return `delegation_unavailable` until II session keys are wired.

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `MONAD_MCP_PORT` | `5002` | Listen port |
| `MONAD_MCP_HOST` | `127.0.0.1` | Bind address |
| `MONAD_MCP_PUBLIC_URL` | `https://monad-mcp.realmsgos.dev` | Documented public base URL |
| `MONAD_MCP_NETWORK` | `ic` | IC network passed to tools (`ic` or `local`) |
| `MONAD_GOS_CANISTER_ID` | `sea3h-pyaaa-aaaab-qhewq-cai` | Monad GOS backend canister |
| `MONAD_MCP_TOKEN_DB` | `~/.monad-gos/mcp-tokens.sqlite` | Pairing token database |

## Tools

| Tool | Scope | Mutates? |
|------|-------|----------|
| `submit_wish` | full | yes (delegation required) |
| `reply_to_broadcast` | full | yes |
| `reply_to_thread` | full | yes |
| `cast_vote` | full | yes |
| `read_broadcast` | read | no |
| `alignment_coefficient` | read | no |
| `alignment_trend` | read | no |
| `get_epoch_status` | read | no |
| `list_proposals` | read | no |
| `get_proposal` | read | no |
| `list_wishes_by_epoch` | read | no |
| `list_threads` | read | no |
| `read_thread` | read | no |
