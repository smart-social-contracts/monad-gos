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

To flip `chora-gos` to available, the release repo
(`smart-social-contracts/chora`) must ship:

| Field | Value |
|---|---|
| `id` | `chora-gos` |
| `label` | `Chora GOS` |
| `default_version` | `v0.1.0` |
| `release_repo` | `smart-social-contracts/chora` |
| `artifacts.backend_wasm_key` | `chora-backend` |
| `artifacts.frontend_wasm_key` | `chora-assets` |
| `artifacts.backend_asset` | `chora_backend.wasm.gz` |
| `artifacts.frontend_asset` | `chora_frontend.tar.gz` |
| `loader_profile` | `chora-iframe-v1` |
| `available` | `false` → `true` when shipped |

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

## 5. The citizen's assistant (reuse the Geister MCP server)

Chora does **not** ship a local LLM, and it does **not** operate its own MCP
server. gos-as-a-service already runs a production MCP server — **Geister**
(`geister-mcp.realmsgos.dev/mcp`) — that lets any MCP-compatible assistant
(Claude, ChatGPT, …) drive a realm on the citizen's behalf. Chora **reuses
Geister** and adds its own domain tools to it.

This is a deliberate inversion of the "local LLM" idea:

- **No pinned model, no constitutional amendment to change assistants.** The
  front-door model is the citizen's *choice*, not a component Chora imposes —
  so the "your model shaped my wish" risk becomes the citizen's liability, not
  Chora's.
- **Adoption friction collapses.** Citizens use an assistant they already trust;
  no on-device model to install, pin, or exclude weak hardware over.
- **The auth/capability problem is already solved.** Geister provides OAuth 2.1
  + Internet Identity, scoped tokens (`read` / `full`), consent, and revocation.
  Chora inherits this rather than rebuilding it.

**What Chora adds:** its own tools on the existing Geister surface —
`submit_wish`, `read_broadcast`, the alignment-coefficient read, and the thread
interface — alongside the generic realm tools Geister already exposes
(`cast_vote`, `submit_proposal`, …).

**The one real gap: delegated signing.** Geister's own docs note that on-chain
*writes* that must be signed as the user (e.g. casting a vote) are constrained
by Geister's calling identity — full delegated signing from an MCP client is
"future work" (it needs an II session delegation, not just an OAuth identity
binding). For Chora this is the **core** citizen act — submitting a wish and
voting — so closing the delegated-signing gap is Chora's main MCP work, not
standing up a server.

## Interface trust summary

| Interface | Trust posture | Grammar reaches? | Mitigation |
|---|---|---|---|
| GaaS platform | implement GGG spec (Motoko) | yes (by spec) | shared Candid schema from `ggg` repo |
| Monad key | central operator | **no** | HSM/KMS attestation + kill switch |
| Federation | public record | partial | on-record traffic |
| Oracles | open | **no** | falsifiable claims + critic fact-check |
| Citizen assistant (Geister MCP) | citizen-chosen assistant; reuse Geister server | **no** | inherited OAuth+II scopes; delegated-signing gap to close |
