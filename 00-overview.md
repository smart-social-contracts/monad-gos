# 00 — Overview

## Thesis

Monad GOS is a Governance Operating System (GOS), compliant with the GGG standard
(Generalized Global Governance). Its distinguishing feature: the executive and
legislative drafting function is performed by an AI — the **Monad** — rather
than by a human-written codex.

Realms and Monad GOS are two answers to the same question ("how does a community
turn its will into executed policy?"):

| | Realms | Monad GOS |
|---|---|---|
| Origin of legislation | Human-written Python codex | Monad-drafted, per epoch |
| Source of rules | Law-as-code | Law-as-inference |
| GGG entities | shared | shared |
| Ratification | vote | vote |
| Executive | codex-defined offices | the Monad, holding a revocable office |

Both are GGG-conforming GOS implementations on the gos.earth platform, which is
deliberately implementation-agnostic.

## What the Monad is

- An **off-chain LLM**. No LLM runs inside a canister; the canister stores
  encrypted inputs and signed outputs only.
- An **officeholder, not an oracle**. The Monad holds a GGG `Position` inside a
  `Department`, under a `Mandate` with an expiry. It can be sued
  (`Dispute`/`Case`), fined (`Penalty`), and unrenewed by vote.
- The **sole drafter** of legislation. It proposes; it never executes directly.
  Humans ratify.

## What the Monad is for

**Objective: the stated satisfaction of existing users.** User growth is a
*reported metric*, never the optimization target.

> Why not growth? "Increase its number of users" is engagement maximization
> with policy power. It rewards telling people what they want to hear, buying
> loyalty from the treasury, and suppressing exit. Growth is an outcome of a
> well-run realm, not a goal.

Satisfaction is measured by **revealed preference**, not self-report: citizens
express alignment by paying — or withholding — a recurring membership due that
funds the treasury. The **alignment coefficient** (the % of citizens current on
their due, read continuously) is the realm's single public indicator and the
Monad's target (100%). Because the due funds the treasury, the Monad's goal, the
realm's budget, and the check on its power are the same number — sedating or
disappointing the population reads as a falling coefficient *and* a shrinking
treasury. See 06.

## Design principles

1. **GGG by spec.** GGG is a language-neutral standard living in its own repo
   (`smart-social-contracts/ggg`, spec-only: Candid interface, data schema,
   entity semantics). Monad GOS implements it in **Motoko**; Realms implements it in
   Python. Conformance means honoring the shared spec, not sharing code.
2. **The Monad proposes, humans dispose.** The Monad has no direct write path
   to GGG state. Every effect passes through a ratified `Proposal`.
3. **Valid by construction.** The Monad's output is constrained by a codex
   *grammar*: it can only emit proposals that are structurally valid, within
   spend caps, and free of forbidden operations. There is nothing to "slip
   through."
4. **Self-improvement is not privileged.** The Monad's own doctrine evolves
   through the exact same adversarial + ratify pipeline as any policy.
5. **No private channel.** The Monad has no off-channel line to any citizen.
   Every exchange is part of the public record.
6. **Trust is named, not hidden.** Every interface the grammar cannot reach —
   the Monad's signing key, every oracle feed — is explicit, falsifiable, and
   revocable.

## GGG conformance

Monad GOS targets `ggg_conformance: "1.0"`. GGG is a **language-neutral standard**
in `smart-social-contracts/ggg` (spec-only: the versioned Candid interface, the
data schema, and the entity semantics). Monad GOS is a **slim Motoko implementation**
of that spec; Realms is the Python implementation. The two interoperate over the
wire because both honor the same Candid schema — not because they share code.

This makes Monad GOS the **second, independent implementation** that proves GGG is a
protocol, not a Realms internal — and proves gos-as-a-service can run backend
canisters in different languages that interoperate.

The six GGG domains — Identity, Governance, Finance, Justice, Land, System —
are the vocabulary the Monad reasons in and the namespace its proposals occupy.
