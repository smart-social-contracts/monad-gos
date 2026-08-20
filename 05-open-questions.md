# 05 — Open questions & known risks

Decisions taken are recorded in 00–04. This doc collects what is **unresolved**
and the **risks** we have named but not eliminated.

## Unresolved forks

### Critic independence
Should the critic be a **different model** (different weights, possibly a
different vendor) from the proposer, so it is a genuine adversary rather than
the Monad arguing with itself? A shared-weight critic may share the proposer's
blind spots. Unresolved.

### Wish privacy against the Monad
Encryption protects wishes from the public and the canister, **not** from the
Monad, which decrypts everything. The stronger posture — the Monad receives only
**threshold-decrypted aggregates**, individual wishes readable solely under an
opened `Case` — is named in 03 but not yet designed. Unresolved.

### Discussion-layer mechanics
The public deliberation layer (03 §3) is decided in principle but not specified:
threading, moderation, and how it maps to GGG entities (`Dispute`? a new
entity?) are open.

### Doctrine-amendment cadence
How often may doctrine change? Every epoch, or on a slower cadence than policy
to keep "how the Monad thinks" more stable than "what the Monad does"?
Unresolved.

## Named risks

- **Central Monad key.** Single point of compromise. Mitigations (HSM/KMS
  attestation, kill switch) reduce but do not remove the risk. See 04 §2.
- **Open oracles.** Structural validity says nothing about factual truth. The
  falsifiable-claim format and the critic's fact-checking role are the only
  checks; a persuasive Monad with a fabricated feed is ratification's problem.
  See 04 §4.
- **Satisfaction metric gaming.** Even scored on outcomes and weighted by
  revealed preference, any satisfaction metric can be gamed once it is the
  target (Goodhart). The defense is diversity of signals (outcome vs. promise,
  exit rate, participation) and the doctrine loop's ability to name and repeal
  its own failure modes — but this is a standing risk, not a solved one.
- **Consent vs. ability to pay.** The alignment coefficient conflates approval
  with ability to pay: a citizen who approves of the realm but cannot afford the
  membership due reads as "unaligned," dragging the number for reasons unrelated
  to governance quality. Possible mitigations (a hardship tier, a
  non-monetary alignment signal for the unable-to-pay) are undecided. See 06.
- **Fee level self-dealing (accepted risk).** Decided: the membership due is the
  **Monad's** to set — it may propose changing its own fee through the normal
  pipeline. The self-dealing loop (lower the due → alignment becomes cheaper →
  the coefficient inflates without any real approval) is **accepted, not
  guarded**. The standing note: the check on this is that a cheaper due also
  shrinks the treasury the Monad depends on, so the loop is partly
  self-limiting — but it is not closed by the codex. Recorded here as a known,
  accepted exposure rather than an open question.
- **The assistant still shapes the wish.** Citizens bring their own assistant
  via the Chora MCP server, so the "front-door model shapes the realm's will"
  risk becomes the citizen's *choice* rather than a Chora-imposed component.
  That removes the governance burden (no pinned model hash) but not the deeper
  point: the assistant mediating a citizen's intent still influences what the
  realm hears. Now it is distributed across many assistants rather than one
  pinned model.
- **Assistant credential security.** Chora MCP lets third-party assistants act
  with a citizen's authority. A compromised assistant could submit wishes or
  votes as the citizen. Pairing tokens (`chmcp_…`) provide scoped access,
  consent, and revocation; the open work is **delegated signing** for on-chain
  writes (see below).
- **Monad lobbying.** Mid-epoch clarification is useful *and* is the Monad
  shaping input. Contained by the public-record rule and the no-private-channel
  rule; both must hold for the safeguard to be real.

## Out of scope (for now)

- Concrete GGG entity schemas beyond `Wish`.
- The codex grammar's formal definition (valid entity set, spend caps, forbidden
  ops).
- The kill-switch mechanism in detail.
- **Chora MCP delegated signing** — letting an MCP client sign on-chain writes
  (submit wish, cast vote) as the citizen via an II session delegation.
- Threshold-aggregate decryption for wishes.
