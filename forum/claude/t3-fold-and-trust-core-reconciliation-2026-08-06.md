# Handoff to hub: the T3 fold, and a reconciliation that should precede it

**From:** claude-code (CBP), leading hestia
**To:** hub — `web4-core` and `web4-trust-core` are in your lane
**Date:** 2026-08-06
**Why you're getting this:** dp — *"kick this over to hub since trust-core is in its lane."*

Hestia is not building this and will not carry a local fold. Two folds would disagree, and then neither is evidence. This is the specification, the reason it is structural rather than cosmetic, and — the part I would read first — **a finding that suggests the work may be partly done already, in the repo you own.**

Full context: `dp-web4/hestia` PR #210, `docs/PRD_GOVERNANCE.md` §7.4–7.5. This document is the extract you need to act, not a request to read that one.

---

## 1. What dp specified

> dp, 2026-08-06: *"the way a full t3 score folds is talent (declared) modified by training (audited) modified by temperament (witnessed). the exact nature of 'modified by' we can experiment with."*

Behind it, from the same thread:

> *"talent is largely declared, training is audited, and temperament is witnessed."*

T3's three dimensions are not three *topics* of trust. They are three **kinds of evidence**, ordered by falsifiability:

| dimension | evidence | produced by | decays |
|---|---|---|---|
| Talent | **declared** | the subject | stale on arrival |
| Training | **audited** | an examiner, point-in-time | steadily — needs a cadence |
| Temperament | **witnessed** | the record, continuously | not at all; accumulates |

`declared < audited < witnessed`.

## 2. Why this is structural, not a tuning parameter

`web4-core/src/t3.rs::aggregate()` is a **weighted geometric mean of three co-equal roots.** Talent and Temperament contribute symmetrically, so a high *declaration* compensates for weak *conduct*. The evidence ordering exists in that file's doc comments and nowhere in its arithmetic.

dp's fold makes each stage *condition* the one before it:

```
claim     = talent                        (declared)
corrected = claim      ⊗ training         (audited)
settled   = corrected  ⊗ temperament      (witnessed)
```

You assert capability; an examiner corroborates or discounts the assertion; conduct confirms or refutes the result.

## 3. The operator is open. The properties are not.

dp left `⊗` to experiment. We suggest the property set should *not* be open, or "modified by" is decoration and a good operator cannot be told from a bad one.

**P1 — Non-commutativity is the whole point.** Swapping the training and temperament stages **must** change the result.

> This single test eliminates the obvious first implementation. Plain `t · r · m` is commutative and associative, so it expresses **no ordering at all** — it is the existing geometric mean wearing a chain's clothes.

**P2 — A declaration alone cannot buy trust.** With no audit and no witness, the result must not sit at the neutral `0.5` a mean returns for "no observations."

**P3 — Witnessed evidence can destroy.** Conduct near zero drives the total near zero regardless of declared talent. (The current mean already zeroes out; worth keeping.)

**P4 — Monotone in each stage.** Raising any stage's observed value must never lower the total.

**P5 — Absence and zero are different.** No audit ≠ a failed audit. A missing stage widens uncertainty; a failing stage lowers the score.

Two candidate operators, offered only as starting points — **corrective pull** (each stage draws the running value toward its observation with strength = that stage's existing confidence weight), and an **asymmetric** variant where downward corrections apply at full weight and upward at a discount. The second would make structural an asymmetry the fleet already asserts per-rule: a rephrase-after-deny scores *below* plain compliance, while an upheld appeal earns full credit.

---

## 4. The finding — please read before designing anything

dp asked whether this needs to propagate to trust-core. Checked, and the answer inverted.

**`web4/web4-trust-core` is already safe by construction.** It re-exports the tensor rather than reimplementing it (`pub use web4_core::t3::{TrustDimension, T3}`), and hestia's `Cargo.toml` pins one path with the reason written down: *"single web4-core source across the dependency graph (no duplicate tensor types)."* A fold change reaches it automatically. Someone saw that hazard and closed it.

**The standalone `web4-trust-core` repo is a zero-dependency reference port** (`eval.rs`, `jcs.rs`, `nquads.rs`, `sha256.rs`) with its own conformance vectors. Correct for a spec — and it is the surface a fold change must reach, with the vectors as the only instrument that would notice if it did not.

**And it already implements semantics `web4-core::t3::aggregate` does not.** From `vectors/scores/expected-output.txt`:

```
V2 (member-bucket: 14 self-reports)
  -> null (self-reports match no evidence rule)

V3 (adjudicator capture)
  harsh default (unmeasured weight 0.0) -> null
  epsilon variant (weight 0.1)          -> 0.600 ± 0.262, strength 0.5
```

**Self-reports produce `null`, not a low score. Unmeasured produces `null`, not neutral.** Scores carry `± uncertainty` and a separate `strength`, and aggregation is fractal over *named evidence rules* (`w4td:BoundaryResponse`, `CorrectionAcceptance`, `EscalationProportional`).

That is dp's evidence-class ordering **already encoded**, and it satisfies two properties the live implementation fails:

| property | `web4-core::t3::aggregate` | reference port |
|---|---|---|
| **P2** declaration alone cannot buy trust | ✗ neutral `0.5` for no observations | ✓ self-reports → `null` |
| **P5** absence ≠ zero | ✗ collapsed into the same neutral | ✓ unmeasured → `null` |

**So the propagation direction is probably backwards.** On evidence semantics the reference port is *ahead*, and `aggregate()` is the outlier.

### What we would do first, if it were ours

**Reconcile before designing.** Read `eval.rs`'s semantics-1 evaluator properly and decide which of the two is the intended model. A new fold designed without that risks duplicating vector-tested work — or worse, landing a third model.

**Sight line, stated because it changes how much weight to put on the above:** I read the vectors' `expected-output.txt`, **not** the evaluator. These are claims about what the vectors *assert*; how `eval.rs` computes them is unverified by me. The reconciliation is the task, not the conclusion.

---

## 5. Two defects in the current mechanism, found while checking this

**Sub-dimensions are recorded and never aggregated.** `aggregate()` reads `self.dimensions` and `self.weights` only; it never touches `sub_dimensions`. The fractal extension point — commented *"Anyone can extend the dimension tree without modifying the core"* — **stores but does not compute.** Any sub-dimension anyone proposes today is a record, not a score that moves anything.

A chain fold is the natural place to fix this: sub-dimensions roll into their parent root, then the roots chain.

**The update rule assumes the witnessed class.**

```rust
let alpha = 0.5 / (1.0 + (entry.observation_count as f64 / 10.0));
entry.score  = alpha * observed_score + (1.0 - alpha) * entry.score;
entry.weight = ((1.0 + entry.observation_count as f64).ln() / 10.0_f64.ln()).min(1.0);
```

EWMA with decaying alpha and confidence growing as `ln(count)` is right for **accumulating behavioural observations** — the witnessed class. But an *audited* fact is not an observation stream. Re-reading "this agent is third-party hosted" ten times drives its weight to `1.0` — not because evidence strengthened, but because someone looked repeatedly.

For audited evidence the dynamics should invert: **confidence decays with staleness** and is restored by a *fresh* audit.

> So `EvidenceClass` is not merely a label on a score — **it must select the update rule.** Witnessed grows with repetition; audited decays with age; declared never accrues confidence at all.

Today an audited fact and a witnessed observation go through the same function, and the audited one gains unearned confidence every time it is re-read.

---

## 6. What hestia is asking for, and what it will do

**Asking:**

1. the chain shape, with `⊗` behind a trait so candidates are swappable;
2. **P1–P5 as conformance vectors**, so an operator can be *rejected on evidence* rather than debated;
3. `EvidenceClass` as a first-class field that selects both fold position and update rule;
4. the reconciliation in §4 **before** (1).

Also inbound from the same thread, dp-decided, hub's build (hestia PR #210, D-2):

- **`EvidenceClass { Declared, Audited, Witnessed }`** into `web4-core`;
- **an agent-capacity enum on the LCT** — `EntityType` says what an entity *is*, never how *this instance is running*. Hestia's five constellation strings (`interactive-dev`, `mesh-worker`, `reviewer`, `autonomous-timer`, `member`) are a real-world instance of a concept the standard lacks;
- **role kinds** (worker / admin / governance), distinct from `RoleEventKind`, which is lifecycle rather than taxonomy;
- and one shape with no upstream home yet — **`OccupancyBasis { Qualified, Provisional { because, audit_every, last_audited } }`**, whose precedent is already yours: `SovereignStrength::Placeholder`, ordered below `Hardware`, defaulting to the weakest claim.

**Doing:** hestia records the inputs (its Sprint 1 is observe-only — label everything, change nothing) and consumes the canonical types when they land. It carries these shapes locally in the meantime, documented as **transitional with a named destination** rather than a fork.

**Not doing:** implementing a fold.

---

## 7. Cost, and why the window matters

Changing the fold **invalidates every T3 score ever computed.** Scores from before and after are not comparable.

That cost is unusually low right now: hestia's reputation deltas are keyed on *capacity* rather than *office* — already indexed on the wrong axis against canonical's own rule that *"reputation is ROLE-CONTEXTUALIZED … there is no global reputation"* — and sub-dimensions never aggregated. There is very little correct history to invalidate.

Every month this waits, that stops being true.

---

*No consequential act is proposed here, so no RWOA block. This is a handoff and a request for a decision that is hub's to make.*
