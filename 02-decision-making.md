# 02 — The Monad's decision-making

The Monad's inner loop is **adversarial deliberation inside a grammar, learning
through voted doctrine.** Five stages per epoch, plus a cross-epoch learning
loop.

## Per-epoch pipeline

### 1. Ingest → aggregate

The Monad decrypts the sealed epoch and aggregates wishes into *concerns*, with
counts, so that minorities are not flattened into the median.

The compression is itself a political act: deciding which wishes count as "the
same concern" shapes the outcome. Monad GOS mitigates this upstream — the public
discussion layer lets citizens converge on shared framings *before* the seal —
but the Monad's aggregation step is still a place bias can enter, and it is
part of the public record so it can be audited.

### 2. Deliberate (adversarial)

Three roles, not one voice:

- **Proposer** drafts a candidate policy addressing the aggregated concerns.
- **Critic** attacks it: what does it cost, whom does it harm, what does it
  contradict (existing doctrine, prior promises, the codex envelope)?
- **Judge** reconciles: advance, send back for revision, or kill.

The critic's dissent is **preserved, not discarded** — it ships with the
proposal so ratifiers see the strongest case against.

> Open fork: whether the critic is a *different model* (different weights,
> possibly a different vendor) so it is a genuine adversary rather than the
> Monad arguing with itself. See 05.

### 3. Constrain (grammar, not filter)

The surviving candidate is only expressible if it fits the codex **grammar**:

- valid GGG entity types only,
- within codex-set spend caps,
- no forbidden operations.

Invalid proposals **cannot be constructed**, so there is nothing to reject
after the fact. This is stronger than a filter (propose freely, reject
violations): the space of emittable proposals excludes the invalid ones by
construction.

### 4. Emit with justification

Every proposal carries:

- the **wish-hashes** that motivated it (hashes, not plaintext — wishes stay
  encrypted),
- the **expected effect** and **cost**,
- **who loses**,
- the **critic's dissent**,
- for any external fact, a **falsifiable oracle claim** (see 04).

This is what makes ratification meaningful instead of theater.

### 5. Execute

Ratified proposals become GGG calls. The Monad never writes GGG state directly.

## Cross-epoch: the learning loop

After execution, the Monad compares **outcome to promise** and writes a
plain-English **doctrine amendment** — e.g. "wishes framed as X tend to fail
when Y; prefer Z."

The amendment is itself an ordinary GGG `Proposal` and goes through the *same*
adversarial + ratify pipeline as any policy. Adopted doctrine is injected into
the proposer / critic / judge context for the next epoch.

**The Monad's self-improvement is not a special privileged channel.** "How the
Monad thinks" is under the same democratic control as "what the Monad does."

### Doctrine conflicts

When a new amendment contradicts existing doctrine, the amendment must
**explicitly repeal** the old clause. Silent override is rejected — implicit
precedence is how drift hides.

## Why this configuration

- **Adversarial** over single-pass: you get a written dissent for free, which is
  exactly what ratification needs.
- **Grammar** over filter: safety is structural, not dependent on a reviewer
  catching a violation.
- **Doctrine** over self-modification: the Monad's judgment evolves only through
  artifacts humans can read and vote on. It cannot drift its own weights or
  prompt invisibly.
