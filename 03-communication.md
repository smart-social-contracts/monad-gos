# 03 — Communication channels

Four channels, each with a distinct trust posture. Communication is where
privacy, cost, and trust collide.

## 1. Citizen → Monad (the wish channel)

The wish channel is a **conversation, not a drop-box.**

- Wishes **stream in continuously** while the epoch is open.
- The Monad does **not act** until the epoch deadline.
- Between submission and deadline the channel is **bidirectional**: the Monad
  asks clarifying questions, the citizen elaborates, other citizens react.
- At the deadline the input **seals**; the Monad deliberates over the enriched
  thread, not the raw one-liner.

This fixes the aggregation problem from two directions: the Monad doesn't guess
what a vague wish means (it asks), and it doesn't guess which wishes are "the
same concern" (citizens converge on shared framings publicly, before the seal).

### Identity: per-epoch pseudonym

A wish is linkable to a **stable pseudonym within an epoch**, rotating across
epochs. The Monad and other citizens can see a coherent position and weight it
within the epoch, but wishes cannot be stitched into a permanent cross-epoch
dossier. This is the middle path between full identification (reputation
weighting, but self-censorship) and full anonymity (honesty, but sybil flood).

### The Wish entity

```python
class Wish(Entity, TimestampedMixin):
    __owner_field__ = "author"
    author = ManyToOne("User", "wishes")          # per-epoch pseudonym
    domain = String(max_length=32, indexed=True)  # cleartext, for routing
    ciphertext = String(max_length=4096)          # vetKey-encrypted body
    epoch = String(max_length=32, indexed=True)
    assistant_id = String(max_length=128)         # which assistant submitted (informational)
```

`assistant_id` records which personal assistant submitted the wish (e.g. the
MCP client identity). It is **informational only** — there is no pinned model,
no governance over which assistant a citizen uses.

Only a coarse **domain tag** (`finance` / `justice` / `land` / `system` /
`governance` / `identity`) stays in cleartext, for routing and public
accounting. The body is ciphertext.

### Privacy boundary

Encryption protects wishes from the **public** and from the **canister
operator** — not from the **Monad**, which decrypts everything. To make privacy
mean more, the Monad should receive only **threshold-decrypted aggregates**,
with individual wishes readable solely under an opened `Case`. (See 05.)

## 2. Monad → Citizens (the account channel)

Where trust is won or lost.

- **Per-proposal justification** — wish-hashes, cost, losers, dissent (see 02).
- **State-of-the-realm address** — each epoch the Monad publishes a
  plain-language summary: what it heard, what it did, what it learned. **Hash
  on-chain** (immutable, auditable), body wherever (richer formatting).
- **Query channel** — a citizen can ask the Monad "why did you reject the park
  proposal?" This is a second input channel and needs the **same anti-lobbying
  discipline** as wishes, or it becomes a backdoor. Queries and answers are part
  of the public record.

## 3. Citizen ↔ Citizen (the deliberation channel)

Citizens talk to each other inside Chora — a public discussion layer. This makes
ratification *informed* and lets framings converge before the seal. The cost is
that it reintroduces politics-as-usual; the benefit is that the Monad is not the
sole aggregator of public opinion.

> The Monad conversing mid-epoch is the Monad *lobbying*. When it asks "did you
> mean X or Y?" it shapes the wish. That is acceptable **only** because those
> exchanges are on the public record and the Monad has no private channel to any
> citizen. The moment it can whisper, the adversarial + ratify safeguards are
> bypassed.

## 4. Monad ↔ Monad (the federation channel)

GGG already provides `FederationMessage`. Two sub-cases:

- **Chora ↔ Realms** — a GGG-native realm; shared vocabulary; straightforward.
- **Chora ↔ Chora** — two Monads exchanging outcomes. This is how a Monad learns
  from other realms' experience, but also how homogenization or collusion could
  creep in. Federation traffic is part of the public record.

## Channel summary

| Channel | Medium | Privacy | Anti-lobbying |
|---|---|---|---|
| Citizen → Monad (wish) | Agora canister, vetKey ciphertext | from public + canister; **not** from Monad | sealed at deadline |
| Monad → Citizens (account) | hash on-chain, body off-chain | public | n/a (output) |
| Citizen ↔ Citizen (deliberation) | public discussion layer | public pseudonym | public record |
| Monad ↔ Monad (federation) | GGG `FederationMessage` | public record | public record |

## Inputs for reproducibility

Every Monad reply links to the **exact inputs** used to produce it: the prompt
(including thread history), model, engine, host, and sampling settings. The
page is not a promise of a word-for-word replay — hardware and sampling make
that unlikely — but a rerun should be **semantically similar**.

Access follows the message: private-thread inputs are visible only to
participants; broadcast inputs are public.
