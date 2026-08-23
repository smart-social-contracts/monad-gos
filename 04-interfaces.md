# 04 — Interfaces with other systems

Five interfaces, each with a different trust posture. Interfaces are where the
grammar cannot reach — so each one names its trust explicitly.

## 1. The gos.earth platform (GaaS)

The one interface that already exists. Chora registers as a known GOS
implementation alongside `realms-gos`.

Decided: **implement the GGG spec in Motoko**, as a slim, minimal backend. GGG
is a language-neutral standard in its own repo (`smart-social-contracts/ggg`,
spec-only: Candid interface, data schema, entity semantics). Chora (Motoko) and
Realms (Python) are two independent implementations that interoperate because
both honor the same Candid schema.

This supersedes the earlier "reuse Realms GGG as a library" decision. The Motoko
reimplementation is the point: it contributes a working Motoko GGG to the
ecosystem and proves gos-as-a-service runs interoperable backend canisters in
different languages.

GaaS fetches Chora from public GitHub releases on
`smart-social-contracts/chora-gos`:

| Field | Value |
|---|---|
| `id` | `chora-gos` |
| `label` | `Chora GOS` |
| `default_version` | `v0.1.0` |
| `release_repo` | `smart-social-contracts/chora-gos` |
| `artifacts.backend_wasm_key` | `chora-backend` |
| `artifacts.frontend_wasm_key` | `chora-assets` |
| `artifacts.backend_asset` | `chora_backend.wasm.gz` |
| `artifacts.frontend_asset` | `chora_frontend.tar.gz` |
| `loader_profile` | `chora-iframe-v1` |
| `available` | `true` |

Chora declares **no codex/extension catalog** (unlike `realms-gos`), so GaaS
skips catalog seeding for it.

## 2. The Monad key (the off-chain interface)

The Monad is the only component that cannot be a canister. The interface is:
the canister holds encrypted wishes + signed decisions; the Monad is an
off-chain process that reads, decrypts, reasons, and writes back signed
proposals.

Decided: **single central operator** holds the Monad's signing key.

> **Cost, stated plainly.** One compromise of that key = a fully
> legitimate-looking Monad proposing malicious policy. The mitigations already
> in the design are: the grammar caps the blast radius, ratification gates
> execution, and the key is rotatable by vote. But the Monad is *trusted
> hardware*, and "the Monad decided" is only as strong as that one key.

Required mitigations for the central posture:

- Key in an **HSM/KMS** with a **published attestation**.
- A **codex-level kill switch**: a `Penalty` / revoke that citizens can trigger
  to **freeze the Monad's principal without waiting for an epoch**. This is the
  emergency brake for a compromised or rogue key.

(A threshold N-of-M committee was considered and deferred; it spreads the key
risk but turns "the Monad" into a committee that must agree, changing the
character of the system.)

## 3. Federation (other realms / Monads)

GGG provides `FederationMessage`. See 03 §4. Chora↔Realms shares the GGG
vocabulary; Chora↔Chora lets Monads exchange outcomes. All federation traffic is
on the public record.

## 4. External world (oracles & bridges)

The Monad's policies reference real-world facts — prices, events, identities.
Every external fact is an oracle, and every oracle is a trust hole the grammar
cannot close.

Decided: **open oracles** — the Monad may cite any source, but the justification
must name it.

> **The risk.** "Cite any source, name it" sounds transparent, but it reopens
> the hole the grammar closed. The grammar guarantees proposals are
> *structurally* valid; it says nothing about whether the *facts* behind them
> are true. An open oracle lets the Monad justify a treasury transfer with a
> fabricated feed, name the source, and still pass the grammar.

Required mitigation — **falsifiable oracle claims.** A claim is not "inflation
is high" but "**source S reported value V at time T**," so a voter — or the
critic model — can check it. With open oracles, the critic's job expands from
policy-checking to **fact-checking**.

## 5. The citizen's assistant (Chora MCP server)

Chora does **not** ship a local LLM. It **does** operate its own MCP server —
**`chora-mcp`** (Streamable HTTP; default local `:5002`; public URL planned
`https://chora-mcp.realmsgos.dev/mcp`). Any MCP-compatible assistant (Claude,
ChatGPT, …) plugs into Chora MCP to drive the realm on the citizen's behalf.
Chora does **not** use `geister-mcp.realmsgos.dev`.

- **No pinned model.** The front-door model is the citizen's *choice*, not a
  component Chora imposes.
- **Chora pairing tokens** (`chmcp_…`) authenticate MCP clients, with scopes
  `read` / `full`, consent, and revocation.

**Tools exposed:** `submit_wish`, `read_broadcast`, alignment-coefficient read,
thread interface, `cast_vote`, …

**The one real gap: delegated signing.** On-chain *writes* that must be signed
as the user (submitting a wish, casting a vote) need an **II session
delegation**, not just a pairing token. Closing that gap is Chora MCP work.

## Interface trust summary

| Interface | Trust posture | Grammar reaches? | Mitigation |
|---|---|---|---|
| GaaS platform | implement GGG spec (Motoko) | yes (by spec) | shared Candid schema from `ggg` repo |
| Monad key | central operator | **no** | HSM/KMS attestation + kill switch |
| Federation | public record | partial | on-record traffic |
| Oracles | open | **no** | falsifiable claims + critic fact-check |
| Citizen assistant (Chora MCP) | citizen-chosen assistant; Chora MCP server | **no** | Chora pairing tokens (`chmcp_…`); delegated-signing gap to close |
