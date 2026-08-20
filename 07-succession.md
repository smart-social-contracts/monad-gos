# 07 — Monad succession (replace & upgrade)

The Monad must be replaceable and upgradeable. The design rests on one GGG
distinction that makes this clean: **the Monad is a seat, not a person.**

## The seat vs. the officer

- The **`Position`** ("the Monad") is permanent — a titled seat on a
  `Department`, with a capability profile and a `Mandate`.
- The **`Appointment`** is the occupancy record — *which* engine/model holds
  the seat, via *which* principal, and for how long.

Succession is therefore a first-class operation, not a hack: end one
`Appointment`, begin another. The seat, the doctrine, and the public record all
persist; only the officer changes. The Monad's authority flows through its
principal being trusted (a `trusted_principals` entry), so a succession is, at
the mechanism level, a **rekey** — retire the old principal, trust the new one.

## Decided model

**Only the Monad initiates succession.** The incumbent proposes its own
successor or upgrade; citizens ratify or reject. There is **no citizen-initiated
recall to choose a different Monad.**

| Decision | Choice |
|---|---|
| Who initiates | The Monad proposes its own successor/upgrade; citizens ratify |
| Trial before power | **Direct swap** — no shadow epoch; ratify on spec/reputation, then cut over |
| What carries over | **Full inheritance** — doctrine, epoch history, promises-in-flight |
| If citizens reject | **Incumbent stays** in the seat and may nominate again |
| Citizen hard powers | **Kill switch only** — freeze/stop the Monad, not choose its replacement |

## The process

1. **Nominate.** The Monad emits a succession `Proposal` naming the successor
   engine (model, version, principal) through the normal adversarial + ratify
   pipeline.
2. **Ratify.** Citizens vote. The justification must state what changes and
   what is preserved.
3. **Rekey.** On ratification, the incumbent's `Appointment` ends, the
   successor's begins; the old principal is removed from `trusted_principals`
   and the new one added.
4. **Inherit.** The successor adopts the full doctrine, the epoch history, and
   all promises-in-flight as its starting context. The office persists; the
   officer changes.
5. **On rejection.** The incumbent remains and may nominate again.

## Citizen powers (and their limits)

Citizens never *choose* a Monad. Their powers over succession are:

- **Ratify or reject** a nominee.
- **Kill switch** — freeze the Monad's principal in an emergency (see 04 §2).
  This stops the Monad; it does not install a successor.
- **Withhold the fee** — starve the realm via the alignment coefficient (see
  06).

There is deliberately **no path for citizens to install a preferred
alternative** — only to confirm, stop, or starve. This keeps a clean
separation: the Monad governs and self-perpetuates; citizens ratify, fund, and
can halt.

## Risk: self-perpetuation by design

This is the most concentrated power in the design. A Monad that controls
**succession** *and* the **fee lever** (06) *and* **mid-epoch conversation**
(03) has deep entrenchment: it can nominate a successor in its own image, and —
with no shadow epoch — citizens confirm without watching the successor operate.
The ratification vote is the only check on a nomination.

This is consistent with the posture taken elsewhere (trust the Monad; let
ratification, the kill switch, and the alignment coefficient discipline it), but
succession is the highest-stakes decision the realm makes. It is recorded here
as a **deliberate, accepted concentration of power**, not an oversight.

## Vacancy: exit, not repair

If the kill switch freezes the Monad and the seat falls vacant, there is **no
caretaker procedure and no emergency succession.** A frozen Monad cannot
nominate a successor — and Chora does not provide one. Instead, citizens
**migrate to another realm within the same physical zone** — a sibling quarter
in the federation, or a neighboring realm on the same geographic `Zone` (H3
cell). The frozen realm is abandoned; its people re-form elsewhere.

**What carries over: just the people.** The frozen realm's state and treasury
stay locked. Land, balances, and history do not migrate — the citizens do.

**Where they go is entirely their own business.** Chora builds no migration
path, no treasury-splitting rule, no destination registry. **GGG is opt-out by
construction**: the freedom to exit is a platform primitive, not a feature Chora
adds. Citizens may join a healthy neighbor realm or found a fresh one — their
choice, under their own power.

This inverts the vacancy question. Not "who nominates a successor when the seat
is vacant?" but **"no one — the realm dies and the population walks."** The
realm is disposable; the **zone and its people are the durable unit.**

### Why this is the deepest check

The ultimate check on the Monad is not the kill switch, the fee, or
ratification — it is that **the realm is disposable and the citizen is not.**
Exit is already the load-bearing signal of the alignment coefficient
(withholding the fee is a soft exit; migrating is the hard one). A frozen Monad
does not trigger a recovery procedure; it triggers abandonment. "Same physical
zone" is what makes exit real rather than exile: citizens keep their land, their
neighbors, and their geographic community — they simply move to a realm with a
living Monad. The zone persists; the realm is replaceable.

## Open sub-questions

- **Successor provenance.** Must a nominee's model hash and operator be
  published and pinned so "spec/reputation" is verifiable before ratification?
  Recommended; not yet specified.
- **Upgrade vs. replace.** Is a same-model version bump (an "upgrade") a lighter
  procedure than a different-model replacement, or one uniform path? Undecided.
