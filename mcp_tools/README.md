# Chora tool pack for Geister MCP

Chora does **not** run its own MCP server. This directory is a tool pack that
registers into the existing **Geister** MCP server (`geister-mcp.realmsgos.dev`)
alongside `REALM_TOOLS` from `geister/realm_tools.py`.

See `chora/04-interfaces.md` §5 and `chora/08-implementation.md` (citizen edge).

## Files

| File | Purpose |
|------|---------|
| `chora_tools.py` | `CHORA_TOOLS` definitions + `execute_chora_tool()` (mirrors `REALM_TOOLS` / `execute_tool`) |
| `chora_client.py` | Live IC client for the Chora backend canister (`icp canister call` + `chora_backend.did`) |

## Registration (wired in `geister/mcp_server.py`)

Geister imports this pack at startup:

1. Adds `/srv/dev/chora/mcp_tools` to `sys.path`.
2. Merges `CHORA_TOOLS` into the MCP tool list (`ALL_TOOLS = REALM_TOOLS + CHORA_TOOLS`).
3. Unions `CHORA_WRITE_TOOLS` into `WRITE_TOOLS` for scope gating.
4. Dispatches `CHORA_TOOL_NAMES` through `execute_chora_tool()`; realm tools still use `execute_tool()`.

`chora_canister_id` is injected into every Chora tool schema (like `realm_id` on
realm tools). The MCP handler resolves it from the call arguments, `realm_id`, or
`CHORA_CANISTER_ID` (default: mainnet `sea3h-pyaaa-aaaab-qhewq-cai`).

### Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `CHORA_CANISTER_ID` | `sea3h-pyaaa-aaaab-qhewq-cai` | Chora backend canister principal |
| `CHORA_NETWORK` | `staging` | IC network label (maps to `ic` / mainnet, same as `GEISTER_MCP_NETWORK`) |
| `CHORA_CANDID_PATH` | `../chora_backend.did` | Candid interface for `icp --candid` |
| `GEISTER_MCP_NETWORK` | `staging` | Network passed to Chora tools from the MCP server |

### Run locally

```bash
cd /srv/dev/geister
CHORA_CANISTER_ID=sea3h-pyaaa-aaaab-qhewq-cai \
GEISTER_MCP_NETWORK=staging \
GEISTER_MCP_PUBLIC_URL=http://localhost:5001 \
GEISTER_MCP_PORT=5001 \
vm/venv/bin/python3 mcp_server.py
```

Health check: `curl -s http://127.0.0.1:5001/healthz` (reports `chora_tool_count`).

## Tools and OAuth scopes

Geister tokens carry scope `read` or `full` (see `geister/docs/MCP_SERVER.md`).
Mutating tools are listed in `CHORA_WRITE_TOOLS` and require `full`.

| Tool | Scope | Mutates? | Live? |
|------|-------|----------|-------|
| `submit_wish` | **full** | yes | registered; returns `delegation_unavailable` |
| `reply_to_broadcast` | **full** | yes | registered; returns `delegation_unavailable` |
| `reply_to_thread` | **full** | yes | registered; returns `delegation_unavailable` |
| `chora_cast_vote` | **full** | yes | registered; returns `delegation_unavailable` |
| `read_broadcast` | read | no | **live** (mainnet query) |
| `alignment_coefficient` | read | no | **live** (includes trend) |
| `alignment_trend` | read | no | **live** |
| `get_epoch_status` | read | no | **live** |
| `list_proposals` | read | no | **live** |
| `get_proposal` | read | no | **live** |
| `list_wishes_by_epoch` | read | no | **live** |
| `list_threads` | read | no | **live** |
| `read_thread` | read | no | **live** |

`chora_cast_vote` is named distinctly from Geister's realm `cast_vote` to avoid
an MCP name collision.

`read`-scoped tokens never see write tools in `tools/list` and get a scope error
if they call one directly (same as `cast_vote`, `submit_proposal`, …).

## Delegated signing gap (current state)

On-chain **writes** (`submit_wish`, `reply_to_broadcast`, `reply_to_thread`,
`chora_cast_vote`) must be signed as the citizen's Internet Identity principal.

Geister MCP auth (OAuth 2.1 + II, or pairing tokens) binds requests to a stable
IC **principal** but does **not** pass an `icp`/`dfx` **identity** (session key)
into tool handlers. `mcp_server.py` calls `execute_chora_tool(..., user_identity="")`.

Until II session delegation is wired through Geister:

- Write tools stay registered and `full`-scoped.
- Calls return a structured error:

  ```json
  {
    "error": "On-chain writes must be signed as your Internet Identity principal. …",
    "error_code": "delegation_unavailable",
    "required": "II session delegation (not just OAuth identity binding)"
  }
  ```

- Geister does **not** fake writes or sign with a server identity.

The same gap affects generic realm writes (`cast_vote`, `submit_proposal`) and is
documented in `geister/docs/MCP_SERVER.md` under "Identity note".

Closing delegated signing is the **priority MCP work** for Chora citizen actions.
