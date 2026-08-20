# 08 — Implementation: stack & architecture

Chora is a **slim Motoko backend** implementing the GGG spec, a Svelte 5
frontend, and an off-chain Monad service. The platform (gos-as-a-service)
dictates the packaging; the language choices are deliberate.

## The GGG standard repo

GGG is a **language-neutral standard** in its own repository:
`smart-social-contracts/ggg` — **spec-only**, no implementation code. It holds:

- the **versioned Candid interface** (the interop surface),
- the **data schema** (entity fields, wire format),
- the **entity semantics** (what each GGG entity means and how it behaves).

Two independent implementations honor that spec and interoperate over the wire:

| Implementation | Language | Repo |
|---|---|---|
| Realms GOS | Python (Kybra/Basilisk) | `smart-social-contracts/realms` |
| Chora GOS | **Motoko** | `smart-social-contracts/chora-gos` |

**Why Motoko, and why slim.** Two reasons, both strategic:

1. **A working Motoko GGG is an ecosystem contribution.** Today GGG exists only
   as Python. A clean Motoko implementation makes GGG a language-neutral
   *standard* rather than a Python library — usable by others in the ecosystem.
2. **It proves gos-as-a-service is language-agnostic.** The platform's pitch is
   implementation-agnosticism, but every GOS so far is Python. A Motoko
   `chora-gos` interoperating with Python `realms-gos` over Candid makes that
   claim concrete.

This **supersedes** the earlier "reuse Realms GGG as a Python library" decision
(see 00, 04). Conformance is no longer free (structural via shared code); it is
a **testable claim against the spec**. The interop surface is the **Candid
schema**, not shared entity classes — get the wire format right and the two
implementations interoperate; get it wrong and there are two incompatible
"GGG"s.

## Backend: Motoko, as slim as possible

The Agora + GGG core is a **Motoko canister** implementing the GGG spec. Slim is
a goal, not an afterthought — Chora carries only what the design needs:

- **GGG entities** — the Motoko implementation of the spec's entity set.
- **The `Wish` entity + Agora write path** — append vetKey-encrypted wishes,
  seal at the epoch boundary.
- **The grammar** — the validation layer constraining what a Monad-signed
  proposal may contain (valid entity types, spend caps, forbidden ops). The one
  genuinely novel backend piece.
- **The Monad's principal** as a trusted principal, plus the **kill switch** (a
  revoke that freezes it).
- **The alignment coefficient** — membership-due accounting, read continuously.

> Open decision: whether the **grammar lives in the canister** (enforced at
> validation, so it holds even against a compromised Monad) **or in the Monad's
> emit path** (enforced at construction). Recommendation: **in the canister.**

## Frontend: Svelte 5, lib-mode bundle

A **Svelte 5** frontend built as a lib-mode ESM bundle, packaged as
`chora_frontend.tar.gz`, embedded via the `chora-iframe-v1` loader profile in
the gos.earth portal. One Internet Identity principal across realms; the portal
is the only login origin.

The UI is the conversational model from 06: Monad broadcast on top, threads
branching off, a separate minimal voting area, the single alignment-coefficient
number, a thin epoch status line.

## The citizen edge: Chora MCP server (no local LLM)

Chora does **not** ship a local LLM. Citizens plug their own assistant (Claude,
ChatGPT, …) into **`chora-mcp`** — Chora's Streamable-HTTP MCP server (default
local `:5002`; public URL planned `https://chora-mcp.realmsgos.dev/mcp`). Auth
uses Chora pairing tokens (`chmcp_…`) with scopes `read` / `full`.

The **open work** on Chora MCP is **delegated signing**: on-chain writes
(submit wish, cast vote) need an II session delegation, not just a pairing
token.

## The Monad: off-chain service

The Monad is the only component with no platform precedent. An **off-chain
service** that:

- holds the vetKey decryption key (HSM/KMS, per 04),
- reads the sealed epoch from the Agora canister,
- runs the adversarial loop (proposer / critic / judge) against an LLM,
- emits signed GGG proposals — conforming to the shared Candid schema — back to
  the canister.

The LLM sits behind an interface so the engine is **swappable** (succession, 07,
requires this). The Monad service's language is open, but not fully free: it
must **hold the vetKey**, **speak Candid** to the canister, and **emit proposals
conforming to the shared schema** — so any language with a Candid agent and an
HSM/KMS integration works.

> Open decisions: the Monad's **LLM provider/hosting** (affects succession
> provenance, 07), and the Monad **service's own language/stack**.

## Toolchain: `icp`, not `dfx`

Realms still has `dfx.json` and no `icp.yaml`. Chora is greenfield — **start on
`icp.yaml` directly** and do not inherit the deprecated toolchain. The one place
Chora can be cleaner than Realms from day one.

## Repository shape

```
chora/
├── icp.yaml                      # icp toolchain, not dfx
├── src/
│   ├── chora_backend/            # Motoko canister (slim)
│   │   ├── ggg/                  # Motoko impl of the GGG spec
│   │   ├── agora/                # Wish entity, epoch seal, write path
│   │   ├── grammar/              # proposal validation (the novel piece)
│   │   ├── alignment/            # membership-due / coefficient accounting
│   │   └── codex/codex.mo        # Monad-authored public law (treasury, budgets)
│   └── chora_frontend/           # Svelte 5 lib-mode bundle
│       └── src/                  # broadcast, threads, voting, coefficient
├── monad/                        # off-chain service
│   ├── engine/                   # swappable LLM interface (proposer/critic/judge)
│   ├── keys/                     # vetKey + signing (HSM/KMS)
│   └── pipeline/                 # read sealed epoch → deliberate → emit
├── mcp_server/                   # Chora MCP server (chora-mcp, Streamable HTTP)
├── mcp_tools/                    # tool pack for chora-mcp
│   ├── submit_wish.*             # citizen wish submission (needs delegated signing)
│   ├── read_broadcast.*          # Monad broadcast + threads
│   └── alignment.*               # alignment-coefficient read
└── docs/                         # the spec files (00–08)
```

Build artifacts for GaaS: `chora_backend.wasm.gz` + `chora_frontend.tar.gz`,
registered as `chora-gos` with loader profile `chora-iframe-v1` (see 04).

## Dependency on the `ggg` repo

Chora's backend is written **against the `ggg` spec repo**. That repo is the
single source of truth for the Candid interface and schema. Realms' Python GGG
stays in the Realms repo; Chora's Motoko GGG stays in the Chora repo; the spec
is what they share.

### v0.1 backend ↔ spec divergences (to reconcile)

The first Motoko backend pass diverged from `ggg.did` in these places. Each is
either a spec gap to adopt or a backend deviation to fix — decide per item:

1. **`Domain`** — spec uses a Candid variant incl. `system`; Motoko 1.9 rejects
   `#system` (keyword). Backend used `text` with validated tags. → Spec should
   use `text` (or rename the variant tag) for portability.
2. **`alignment_coefficient`** — spec returns `AlignmentCoefficient` (0.0–1.0 +
   `membership_due`); backend returns `AlignmentReport` (percent 0–100, `trend`,
   `previous_percent`). → Align on one shape; UI wants a trend.
3. **`list_wishes` vs `list_wishes_by_epoch`** — naming. → Pick one in spec.
4. **Grammar metadata** — backend parses line-oriented `spend:`/`op:` metadata,
   not JSON. → Spec should define the proposal-metadata wire format.
5. **Admin bootstrap** — `bootstrap_admin()` one-time admin set (Motoko 1.9
   disallows `shared persistent actor` initializer capture). → Document the
   admin/setup pattern in the spec semantics.
6. **Omitted from v0.1 (slim)** — `get_user`, `resolve_proposal`, mandates,
   finance, positions. → Confirm v0.1 scope in spec.
7. **Conversational surface** — `read_broadcast`, `list_threads`, `read_thread`,
   `reply_to_broadcast`, `reply_to_thread`, `get_epoch_status`, alignment trend
   were missing from the spec (flagged by the frontend) and are being added in
   spec v0.2.0. → Backend must implement them once the spec lands.
