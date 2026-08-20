# 01 — Architecture

## Components

Agora, GGG core, and Ratification are **modules in a single slim Motoko
canister**, not separate canisters. The Monad and the citizen's assistant are
off-chain.

| Component | Where it runs | Role |
|---|---|---|
| **Personal assistant** | Citizen's choice (ChatGPT, Claude, …) | The citizen's own AI assistant, plugged into the realm via the existing **Geister MCP server**. Helps the citizen articulate a wish and submits it. Chosen and trusted by the citizen, not shipped by Chora. |
| **Geister MCP server** | gos-as-a-service (existing) | The production MCP server the platform already runs. Chora reuses it and adds Chora-specific tools (`submit_wish`, `read_broadcast`, …). The controlled entry point between a citizen's assistant and the realm. |
| **Agora** | Module in the Chora canister | The message repository. The *only* citizen write path. Stores encrypted wishes and the public discussion record. |
| **Monad** | Off-chain (single operator) | The AI executive. Reads the sealed epoch, deliberates adversarially, emits signed GGG `Proposal`s. Holds a realm `Position` under a revocable `Mandate`. |
| **GGG core** | Module in the Chora canister | Chora's **Motoko implementation of the `ggg` spec** (see 08). Defines the entities the Monad reasons over and the grammar its output must satisfy. |
| **Ratification** | Module in the Chora canister | Citizen voting on proposals (and on doctrine amendments). |

## The epoch loop

Chora runs in discrete **epochs**. One epoch:

```
        ┌─────────────────────────────────────────────────┐
        │                   EPOCH                         │
        │                                                 │
  OPEN  │  CONVERSE          SEAL    DELIBERATE  EMIT     │  RATIFY   EXECUTE+LEARN
        │                                                 │
  wish  │  wishes stream in; input  Monad reads proposals  citizens  approved
  chann │  Monad clarifies;  freezes the sealed adversarially; with     vote     proposals
  el +  │  citizens discuss  (no    record;     grammar-   justifica-  │        execute;
  discus│  publicly; framings lobby  aggregate  checked    tion +      │        outcomes
  sion  │  converge          ing)   & draft     output     dissent     │        feed doctrine
  live  │                                                 │           │        amendment
        └─────────────────────────────────────────────────┘
```

1. **Open** — epoch begins; wish channel and discussion layer both live.
2. **Converse** — wishes stream in continuously; the Monad asks clarifying
   questions; citizens deliberate publicly; framings converge. The Monad does
   **not act** during this phase.
3. **Seal** — deadline hits; input freezes. No more lobbying.
4. **Deliberate** — the Monad runs its adversarial loop over the sealed,
   enriched record (see 02).
5. **Emit** — proposals with justifications and the critic's dissent.
6. **Ratify** — citizens vote.
7. **Execute + learn** — approved proposals execute as GGG calls; outcomes feed
   a doctrine amendment, which re-enters at step 4.

## Trust topology

The grammar keeps the *inside* clean. Trust leaks in at exactly the boundaries
the grammar cannot reach:

```
 citizen ──(trusts)──> own assistant ──(MCP)──> Agora ──(sealed)──> Monad
                                                              │ off-chain key
                                                              ▼
 citizen <──(ratifies)── GGG core <──(signed Proposal)── Monad output
                                                              │
                                                    oracle feeds (external facts)
```

- **The citizen's own assistant** shapes every wish. Because the citizen chooses
  it (ChatGPT, Claude, …), the shaping is done by a tool they trust — not one
  Chora imposes. There is no pinned model hash and no constitutional amendment
  to change assistants; the choice is the citizen's, and may differ per citizen.
- **The Geister MCP server** is the controlled entry point: it authenticates the
  citizen (OAuth 2.1 + Internet Identity) and holds their authority to submit
  wishes and vote. See 04 §5.
- **The Monad's signing key** is held off-chain. See 04 for the central-operator
  posture and its required mitigations (HSM/KMS attestation + codex kill
  switch).
- **Oracle feeds** supply external facts. See 04 for the falsifiability
  requirement.

## What the canister guarantees vs. what it cannot

The canister can guarantee: ordering, sealing, signatures, the public record,
the grammar check, the vote tally, and execution of ratified proposals.

The canister **cannot** guarantee: that the Monad reasoned honestly, that an
oracle told the truth, or that a citizen's assistant represented them
faithfully. Those are handled by transparency (everything is on the record),
falsifiability (claims name checkable sources), and revocability (the Monad can
be frozen and unseated) — not by the grammar.
