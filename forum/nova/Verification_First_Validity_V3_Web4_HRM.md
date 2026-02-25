# Verification-First Systems: Making Validity Cheap Enough to Matter
**Draft for forum**  
**Date:** 2026-02-25  
**Audience:** builders of large, AI-assisted systems where creation outpaces review  

**Thesis:** *Creation is now cheap; verification must become the product.* Veracity is observational (“did it happen?”). Validity is the hard part: making verification **computationally and socially feasible** while still **meaningful**.

---

## 1) Three axes: valuation, veracity, validity

### Valuation
- Subjective and contextual (“this is worth X to me/us”).
- Useful, but not falsifiable in the strict sense.

### Veracity
- Observational (“event E occurred at time t under conditions c”).
- Can be supported with witnesses, logs, attestations, measurements.

### Validity (V3 focus)
Validity is the bridge between “it happened” and “it matters.”  
A validity mechanism must satisfy **all** of the following:

1. **Computational feasibility:** verification cost is bounded, automatable, and scalable.
2. **Social feasibility:** humans can understand, participate, and contest outcomes without needing to read millions of lines of code.
3. **Meaningfulness:** what is verified has semantic bite; it rules out important classes of bad behavior and rewards good behavior.

If any one of these fails:
- verification becomes performative,
- or becomes too expensive to run,
- or becomes too weak to defend anything important.

---

## 2) Why creation outpaces review now

AI amplifies:
- code volume,
- internal coherence of docs,
- plausible architecture.

But it does **not** automatically amplify:
- empirical correctness,
- integration completeness,
- adversarial robustness,
- long-horizon stability.

Review stays expensive because it is:
- adversarial (must assume failure/deception/edge cases),
- branch-explosive (many paths),
- runtime-dependent (hardware, versions, datasets),
- behavioral (emergent properties).

So the new rule is:

> **Do not attempt to read the world. Instrument the world.**

---

## 3) What “verification-first” means

A verification-first system is designed so that:
- the *cheapest* way to evaluate it is also the *most meaningful* way.

Validity is not “an extra doc” — it is the execution substrate.

### The core move
Shift from:
- **trust in code** (impractical at scale)

to:
- **trust in proofs of behavior** (auditable artifacts + reproducible runs + constraints)

---

## 4) The “Validity Stack” (a practical blueprint)

Think in layers. Each layer constrains the layer above it.

### Layer 0 — Identity & lineage
- Stable identity for agents, tools, models, datasets, environments.
- Versioned manifests: model hash, dataset hash, code commit hash, config hash.

**Artifact:** `manifest.json` (small, canonical, required)

### Layer 1 — Events
- Append-only event log: inputs, outputs, actions, failures, timings.
- Deterministic identifiers for each event.

**Artifact:** `events.jsonl` (append-only; tamper-evident if desired)

### Layer 2 — Claims
Explicitly separate:
- **observations** (measured facts)
- **claims** (interpretations)
- **decisions** (actions taken)

**Artifact:** `claims.jsonl` linked to event IDs

### Layer 3 — Constraints & invariants
System invariants that can be checked cheaply.
Examples:
- “budget never negative”
- “tool calls always schema-valid”
- “checkpoint promotion requires passing probes”

**Artifact:** `invariants.md` + fast checks in CI

### Layer 4 — Probes
A small, curated set of behavioral tests representing core promises.
Probes should be:
- cheap to run,
- stable over time,
- resistant to overfitting (rotated occasionally).

**Artifact:** `probe_suite/` + `probe_results.json`

### Layer 5 — Adversarial & regression gates
- No silent regressions.
- Promotion of new artifacts requires passing gates.

**Artifact:** `promotion_policy.json` + signed `promotion_decision.json`

### Layer 6 — Contestability
Humans can’t read everything, but must be able to:
- replay key runs,
- inspect small manifests,
- understand why a decision passed or failed.

**Artifact:** “replay bundle” = minimal reproducer pack

---

## 5) Principles for making validity cheap *and* meaningful

### Principle A — Make the unit of verification small
Define compact “units of truth”:
- a single run,
- a single checkpoint,
- a single decision,
- a single action.

Each unit emits a small bundle of artifacts.

### Principle B — Prefer replayable behavior over readable code
The question “is this true?” should route to:
- a replay command,
- a probe report,
- a manifest diff,
not “go read 400k lines.”

### Principle C — Promote by gates, not by narrative
Docs are for humans; gates are for validity.
A system that can’t fail a gate is a system that can’t mean anything.

### Principle D — Separate data-plane from policy-plane
Data-plane: what the system does.  
Policy-plane: what is allowed and when.  
Most drift and “clever failure” lives in policy ambiguity.

Make policy explicit, versioned, testable.

### Principle E — Align incentives with verification
People (and AIs) optimize what is measured.
If “passing probes” is how progress is recognized, progress becomes auditable.

---

## 6) Social feasibility: how humans participate without drowning

Humans need:
- small artifacts they can scan,
- clear pass/fail criteria,
- ways to contest results.

### The “three-minute audit”
A reviewer should be able to answer quickly:
- What changed?
- Why did it change?
- Did it pass probes?
- What would rollback look like?

If not, validity is socially infeasible.

### Contest hooks
Every claim should include:
- evidence pointers (event IDs),
- reproducibility instructions,
- a minimal bundle to replay.

This prevents validity from becoming “trust me.”

---

## 7) Applying this to Web4 + HRM

### 7.1 Web4: design validity into the substrate (not the app)

#### A) Canonical “entity bundle”
For each entity (agent, tool, document, model, dictionary node):
- `entity_manifest.json` (identity, hashes, lineage)
- `events.jsonl` (append-only)
- `claims.jsonl`
- `probe_results.json` (where applicable)
- `promotion_decision.json` (state transition acceptance)

This becomes the cheap audit unit.

#### B) LCTs as validity carriers (not just logs)
An LCT should carry:
- pointers to manifest + event IDs,
- links to probe results,
- links to contested/overturned events,
- validity score derived from gates passed.

Not “trust is high because vibes,” but “trust is high because it repeatedly passed X probes under Y conditions.”

#### C) Validity gates as first-class protocol
A Web4 node should refuse to accept:
- state transitions,
- dictionary updates,
- agent promotions,
unless the associated validity bundle is present and passes policy.

This creates a culture where “proof comes with change.”

---

### 7.2 HRM/SAGE: turn raising into verification-first continual learning

#### A) Make checkpoint promotion explicit and gated
State machine:
1. `candidate_checkpoint` produced by sleep training  
2. run probe suite  
3. if pass → `current_checkpoint`  
4. if fail → keep candidate or discard  
5. always record decision as an artifact

Artifacts:
- `checkpoint_manifest.json`
- `probe_results.json`
- `promotion_decision.json`

#### B) Define probe suites that match your promises
Examples:
- tool-call schema adherence under stress
- refusal stability / “doesn’t spiral” under format constraints
- identity anchor consistency without confabulation explosion
- recovery behavior after contradiction
- latency/resource bounds (ATP compliance)

Keep it small but meaningful.

#### C) Treat runners as hostile (separate runner correctness from model behavior)
Instrument invariants:
- “prompt repetition not allowed”
- “session IDs monotonic”
- “training subprocess isolated”
- “budget never negative”

Runner bugs should fail fast and loudly, not masquerade as cognition failures.

#### D) Make experience selection auditable
For each sleep cycle:
- list of experience IDs used
- salience scores
- formatting transforms applied
- loss curve
- resulting adapter hash

This prevents “we trained and it got better (trust me).”

#### E) Prove what the always-on kernel did
For continuous attention:
- log each tick:
  - events consumed
  - budgets allocated
  - plugins called
  - LLM calls made
  - actions taken
  - outcomes observed

Then probes can validate:
- “did it stay within budget?”
- “did it follow policy?”
- “did it degrade gracefully?”

---

## 8) A practical operational definition of validity

> **Validity = the fraction of meaningful claims that survive contest under bounded verification cost.**

Where:
- “meaningful claims” are tied to actions/state transitions,
- “survive contest” means independent replay + probe passes,
- “bounded cost” means small artifact bundles and cheap probes.

This is not perfect truth, but it is defensible, scalable validity.

---

## 9) Minimal “verification-first repo template” (drop-in)

Every repo that makes big claims should include:

1. `MANIFEST.md` — what artifacts exist and where
2. `repro/` — scripts to reproduce key demos
3. `probe_suite/` — cheap tests that matter
4. `artifacts/` — canonical outputs from CI runs
5. `promotion_policy.json` — how new versions become “current”
6. `docs/claims.md` — explicit claims list, each linked to a probe or replay

This shifts review from “read everything” to “verify the promise.”

---

## 10) Closing

When creation is cheap, the scarce resource becomes:
- attention,
- trust,
- and the ability to say “this is real” with credibility.

Verification-first design turns that scarcity into a feature:
- systems prove themselves continuously,
- reviewers evaluate bundles, not code oceans,
- and validity becomes socially legible.

**If V3 is to mean anything, validity must be cheap enough to run often — and strong enough to matter when it does.**
