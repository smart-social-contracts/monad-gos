# Monad GOS

<p align="center">
  <img src="brand/monad-gos-lockup.png" alt="Monad" width="420" />
</p>

**Monad GOS** is a Governance Operating System (GOS), GGG-compliant, in which an AI
executive — the **Monad** — drafts legislation from the stated wishes and
concerns of citizens, and citizens ratify it by vote.

Where Realms encodes law as Python written by humans (a *codex*), Monad GOS has the
Monad draft it each epoch from what citizens actually asked for. Same GGG
entities, same voting, different origin of legislation: **law-as-inference**
instead of law-as-code.

> Status: **live on IC mainnet**. Backend `sea3h-pyaaa-aaaab-qhewq-cai`,
> frontend `sndq3-zqaaa-aaaab-qhexa-cai`. GaaS registers this GOS as `monad-gos`.

## Releases

`gaas` downloads Monad GOS the same way it downloads any other GOS: public GitHub
release assets from this repo.

Tag a version to cut a release. CI builds the Motoko backend WASM and the
Svelte frontend bundle, then uploads them:

```bash
git tag v0.1.0
git push origin v0.1.0
```

| Asset | Used by `gaas` as |
|---|---|
| `monad_backend.wasm.gz` | backend WASM |
| `monad_frontend.tar.gz` | frontend asset bundle |
| `monad_backend.did` | Candid interface |
| `checksums.txt` | SHA-256 verification |

## Design documents

| Doc | Contents |
|---|---|
| [00-overview.md](00-overview.md) | Thesis, design principles, GGG conformance posture |
| [01-architecture.md](01-architecture.md) | Components, the epoch loop, trust topology |
| [02-decision-making.md](02-decision-making.md) | The Monad's inner loop: adversarial deliberation, grammar constraint, doctrine learning |
| [03-communication.md](03-communication.md) | Channels, the Wish entity, the per-epoch rhythm |
| [04-interfaces.md](04-interfaces.md) | GaaS platform, the Monad key, federation, oracles, Oikos |
| [05-open-questions.md](05-open-questions.md) | Unresolved forks and known risks |
| [06-ui.md](06-ui.md) | Conversational UI: Monad broadcast, threads, separate voting, alignment coefficient |
| [07-succession.md](07-succession.md) | Replacing & upgrading the Monad: seat vs. officer, rekey, self-nomination |
| [08-implementation.md](08-implementation.md) | Stack & architecture: Motoko GGG backend, Svelte 5 frontend, off-chain Monad |

## One-paragraph summary

Citizens plug their **own AI assistant** (ChatGPT, Claude, …) into **Monad GOS
MCP** (`monad-mcp`), which exposes tools like `submit_wish`. The assistant
helps the citizen articulate a `Wish`; the wish is encrypted to the Monad's
vetKey and posted to a canister (the **Agora**). Wishes stream in continuously
and citizens deliberate publicly while the epoch is open; at the deadline the
input seals. The Monad — an off-chain model holding a realm `Position` under a
revocable `Mandate` — reads the sealed record, deliberates **adversarially**
(proposer / critic / judge), and emits GGG `Proposal` objects that are **valid
by construction** under a codex grammar.
Citizens ratify; approved proposals execute as GGG calls. After execution the
Monad compares outcome to promise and proposes a plain-English **doctrine
amendment** — itself an ordinary `Proposal` that citizens vote on. The Monad
optimizes the **stated satisfaction of existing users**, with user growth
reported as a metric, never the objective.
