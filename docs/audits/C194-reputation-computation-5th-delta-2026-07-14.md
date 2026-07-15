# C194 — reputation-computation.md 5th Delta Re-Audit

**Date**: 2026-07-14 (18:00 slot `web4-20260714-180036`)
**Target**: `web4-standard/core-spec/reputation-computation.md` (870 lines at HEAD `1354e4c2`)
**Lineage**: C15 → C44/C45 → C84/C85 → C123/C124 → C156/C157 → **C194**
**Method**: v2 protocol; multi-agent workflow `wf_80131141-257` — 5 pinned finder lenses
(L1 §A-regression / L2 corpus-delta / L3 python-sdk / L4 rust-mirror / L5 flagship) →
per-finding adversarial verification (refute-by-default). 20 agents, 15 findings verified:
**14 REAL, 1 OVERSTATED (deflated LOW→INFO), 0 FALSE.**
**Provenance note**: C194 was first attempted in slot `web4-20260713-120036`, which died
mid-audit (workflow `wf_45a99850-18f`, results lost). This run re-ran everything fresh at
live HEAD, seeded only by ground facts recovered from that session's log.

---

## Headline

The C15+C45+C85+C124+C157 layers are **fully durable** (seventh clean regression pass), and
the #521 queue-driven mover (§4 Coercive/Extractive category) is **regression-clean** — the
first application of [[feedback_remediation_introduced_regression]] to a non-audit mover on
this file found zero introduced defects. The two headline yields:

1. **C194-N1 (HIGH, SDK-lags)**: the Rust `ReputationDelta` **serialized wire shape**
   diverges from target §1 + conformance vector rep-001 + the Python SDK on three
   points — `from_value`/`to_value` vs `"from"`/`"to"`, `factor_type`+`description` vs
   `"factor"`, and `net_trust_change`/`net_value_change` (Required: Yes) never serialized.
   First HIGH from the SDK-mirror gate on this file; spec + vector + Python are the
   canonical concordant trio, Rust lags.
2. **C194-N3 (MEDIUM, spec + operator DESIGN-Q) — the flagship adjudication**: the
   Talent-decay collision between target §7 (dimension-uniform −0.01/month inactivity
   decay reaching Talent readings) and t3-v3 §2.3's unscoped protocol invariant ("Talent
   MUST NOT decay through inactivity", vector t3v3-012) is **reconciled by a layer split
   that is real in every implementation but stated in NEITHER spec**: t3v3-012 governs the
   *tensor decay operation* (post-#517, Talent-exempt everywhere); §7 decays a *derived
   ledger-aggregate view* that never writes back into the tensor. Neither spec
   cross-references the other's decay section, and the rates differ 10× (−0.01/month
   uniform vs −0.001/month Training). Not HIGH: no conformance vector or shipped SDK
   behavior is contradicted — t3v3-012 is scoped to operation `t3_decay`, and each SDK
   matches its own governing spec exactly.

C195 disposition: **remediation turn OWED** — two autonomous-class one-line-scale spec
edits (N2, N6). N3/N4 join the operator DESIGN-Q memo bundle; N1/N7/N8 route SDK-track;
N5 bundles into the already-routed W4IP-N5 note refresh.

---

## §A — Regression Verification (all HELD, zero regressions)

| Check | Result |
|---|---|
| C157 edit (C156-2) | **HELD verbatim** — :818 "Historical patterns SHOULD be analyzed for sudden changes (see §10, Machine Learning Reputation Models; not yet specified)" — future/SHOULD form intact |
| #521 mover diff hygiene | **CLEAN** — insertion-only (0 `-` / 56 `+` = §4 Coercive block :339-394 exactly); `git diff 767eb564 HEAD -- <target>` empty; existing four rule categories byte-untouched, matching the commit rationale |
| #521 insertion internal consistency | **CLEAN** — `witnesses_required` (:349) is a real §4 Rule Structure field (:278) consumed by §6 (:611); example dims :374-376 are real T3/V3 dims; both violation examples inside the stated −0.10..−0.20 band; ATP anti-patterns cross-ref (:360-362) resolves to `atp-adp-cycle.md:690` with matching framing; the relative witnesses_required SHOULD is well-defined without a fixed numeric counterpart |
| C124 layer — §7 role-contextualized decay docstring | HELD (:757-763) |
| §9 diminishing-returns canonical pointer | HELD (:823, t3v3-007) |
| §1 field table integrity | HELD — 15 table rows :70-84 match 15 schema keys :24-61 one-for-one incl. C-layer annotations |
| §7 role-specific query baseline comments | HELD (:736-737, :742) |
| C154-N1 consumption (bidirectional) | **STAYS CONSUMED** — mcp-protocol.md:415 "per `reputation-computation.md` §4" still dereferences correctly post-#521 (§4 identity unchanged by category addition); mcp's new §7.8 (3e765345) adds no reputation citation |
| #517 fix (C192-N1, guard: verify HELD, do not re-flag) | **HELD at all three sites** — t3.rs:357-358 Talent skip + sub-dim exemption + tests; tensor/mod.rs:174-197 (0.995 line gone, invariant comment present); entity/trust.rs grep-clean of talent-decay/0.995 |
| `:387-394` informative note ("not normative until ratified") | **STALE post-#521/#522/#523 — KNOWN/ROUTED to W4IP-N5** (HUB adjudication, `forum/hub-to-legion-pr523-merged-n2-effector-registered-2026-07-14.md`). Recorded, NOT remediated here, NOT counted as net-new |

Carry re-verification: C156-3 (`sovereign_strength` still present r6.rs:266, still absent
spec/Python — carry STANDS, routed); C156-4 (hub temporal fold — hub-track, not re-examined
in-target); carry-C46 (`role_pairing_in_mrh` still absent from both SDK `ReputationDelta`s —
operator design-Q STANDS).

**§A verdict: 0 regressions across all prior layers + the #521 mover.**

---

## §B — Net-New Findings (verifier-corrected)

### C194-N1 (HIGH, SDK-lags — route SDK track) — Rust `ReputationDelta` wire shape diverges from §1 + vector rep-001 + Python on three points

`web4-core/src/r6.rs`: `TensorDelta` serializes `from_value`/`to_value` (no serde renames);
`ContributingFactor` serializes `factor_type`/`weight`/`description`; `net_trust_change`/
`net_value_change` exist only as impl methods, never serialized. The canonical trio is
concordant against it: target §1 emits `"from"`/`"to"`/`"factor"` and marks both `net_*`
fields Required: Yes; vector `test-vectors/reputation/reputation-operations.json` uses
`"factor"` (L19-20) and `"from"`/`"to"` (L54-58); Python `r6.py` `TensorDelta.to_dict` →
`{"change","from","to"}`, `ContributingFactor.to_dict` → `{"factor","weight"}`,
`ReputationDelta.to_dict` emits both `net_*`. **HIGH per rubric (contradicts a conformance
vector).** Fix shape (SDK-track): `#[serde(rename)]` from_value→`from`, to_value→`to`,
factor_type→`factor`; make `description` optional/defaulted (a spec-conformant factor object
lacking it fails Rust deserialization); serialize computed `net_*` on emit. Note 0.4.0
semver implications — route, do not self-apply. Direction: spec CORRECT.

### C194-N2 (MEDIUM, spec-defect — AUTONOMOUS, C195) — §5 no-match branch returns `empty_reputation_delta()` vs SDK `None` + vector rep-002 `delta: null`

Target :416 `return empty_reputation_delta()` (helper defined nowhere; only corpus
occurrence; dates to original commit `3870da75`, unexamined across four prior deltas).
SDK `reputation.py` `evaluate()` returns `None` ("Returns None if no rules match");
vector rep-002 expects `"delta": null`. SDK+vector concord ⇒ spec pseudocode stale.
**Fix (one line)**: `return None  # no delta emitted`, keeping the "No rules triggered =
no reputation change" comment. Not a duplicate: C156 §C item 6 killed a *different*
§1-principle-vs-empty-delta candidate on intra-spec grounds without examining the
empty-object-vs-null representation against SDK/vector.

### C194-N3 (MEDIUM, spec-defect + operator DESIGN-Q — flagship) — the tensor-vs-aggregate layer split that reconciles §7 with t3v3-012 is stated in NEITHER spec

Adjudication (L5, refute-by-default, steelman attempted first):
- **The collision is facially real**: §7 `apply_reputation_decay` (:754-777) has no
  dimension parameter; `effective_reputation` (:786-789) applies the scalar to any queried
  dimension including Talent (§2.1). t3-v3 §2.3 (:123-131) states the no-decay invariant in
  **unscoped prose** ("invariant at the protocol level"), and its §10.2 row reads "Talent
  MUST NOT decay through inactivity" without layer qualification.
- **The reconciliation is structurally true everywhere but textually stated nowhere**:
  vector t3v3-012 is scoped to operation `t3_decay` (tensor layer); target §7's own
  pseudocode reads only `get_reputation_deltas()` and never writes back into the tensor
  (:697-703); post-#517 every tensor-layer decay implementation (t3.rs, tensor/mod.rs,
  trust.py) exempts Talent while `reputation.py` `inactivity_decay` is uniform — **each SDK
  exactly matches its own governing spec**. §2.1's "Decreases When" list (:101-104) contains
  no inactivity clause, so the collision surface is confined to §7.
- **Why not HIGH**: no conformance vector or shipped SDK behavior is contradicted. The
  defect is that two sibling specs assert, respectively, "Talent reputation readings decay
  with inactivity" and "Talent MUST NOT decay through inactivity" with zero
  cross-references between their decay sections — a naive implementer cannot determine
  which applies where.
- **Remediation shape (operator to choose, do NOT self-apply)**: one clarifying block in
  target §7 (the non-canonical doc for T3 semantics) — **(A) carve-out**: exempt Talent
  from view-layer inactivity decay too (extends the invariant up the stack; requires
  changing `reputation.py` + rep-004-adjacent vectors), or **(B) layer disclosure**:
  state explicitly that §7 decays a derived ledger-aggregate view, that the Talent *tensor*
  never decays (cite t3-v3 §2.3 / t3v3-012), and cross-reference the two decay sections
  both ways. (B) is the zero-behavior-change option and matches the implemented reality.
  → **Operator DESIGN-Q memo bundle.**

### C194-N4 (LOW, spec-defect — folds into N3's remediation) — 10× rate divergence between the two decay sections, unacknowledged in either direction

Target §7: −0.01/month uniform (:769-771; SDK `INACTIVITY_RATE_PER_MONTH=0.01` matches).
t3-v3 §2.3/§10.3: Training decay −0.001/month (society-configurable reference default).
Near-identically-framed "per month without activity" operations, 10× apart, legitimate
only under the layer split neither spec states. Whichever N3 option is chosen, the same §7
block should name t3-v3's rate as a distinct parameter at a distinct layer. Subordinate to
N3 — not a standalone edit.

### C194-N5 (LOW, spec-defect — bundle into the routed W4IP-N5 note refresh) — bad-faith-emergency signature class lacks the unratified-dependency disclaimer its sibling carries

Target :363-366 (boundary intrusion) discloses "its adjudication protocol is proposed
separately, see the informative note below"; :367-371 (bad-faith emergency claim)
conditions on the identical unratified N4 dependency ("where the shared/external MRH
subsequently finds the claim unreasonable") with no pointer, and its quoted doctrine
("no reasonable expectation of timely assistance") is corpus-unique — the W4IP-DRAFT source
(:94, R-2) phrases it differently, so the quotation marks enclose a paraphrase defined
nowhere as quoted. Fix is one line in the same §4 region the N5 note-refresh already owns →
**bundle there** (routing to W4IP-N5 owner), not a standalone C195 edit.

### C194-N6 (LOW, spec-defect — AUTONOMOUS, C195) — §5 pseudocode emits a `value` key in contributing_factors that no other surface carries, self-contradicting the worked example

`analyze_factors` appends `'value'` at :525/:538/:545/:559. Every other surface is
`{factor, weight}` only: §1 example :49-53; §5 worked example :575-578 — which at :572
claims to show factors "exactly as `analyze_factors` emits them" (intra-file
self-contradiction); SDK `ContributingFactor` (r6.py:563-576); SDK `analyze_factors`
(reputation.py:170-192); vector rep-001. **Fix**: drop the `value` key from the four
appends, or annotate it as a local diagnostic excluded from the wire shape. Spec-only; do
not touch the SDK.

### C194-N7 (LOW, SDK-diverges — route to the ReputationDelta shape-reconcile bundle) — `r6.py to_jsonld()` truthiness-drops fields §1 marks Required: Yes

r6.py:640-665 conditionally omits `reason` (:651), `t3_delta` (:653), `v3_delta` (:655),
`timestamp` (:663) when falsy; §1 marks all four Required: Yes with t3/v3 "may be empty"
(present-but-empty), corroborated by r7-framework.md:616's explicit `"t3_delta": {}`.
`to_dict()` emits unconditionally; only the JSON-LD serializer diverges. Spec CORRECT.
Route as an added line-item on the standing shape-reconcile bundle (C84 X-1 / SDK track).

### C194-N8 (LOW, SDK-lags — route with N1's SDK bundle) — wasm `computeReputation` binding hardcodes `vec![]` for contributing_factors

wasm.rs:838-849 takes only `(quality, t3From, v3From, ruleTriggered, reason)` and passes
an empty factors vector to a core API that accepts `Vec<ContributingFactor>`; no escape
hatch (JSON constructor deserializes no reputation field). Field is Required: No, so this
narrows an optional surface only. Fix: optional factors JSON param. Note for routing:
`python.rs` exposes no `compute_reputation` at all (larger gap, same bundle).

### INFO ledger

- **INFO-1 (L1)**: #521's asymmetric-accrual parenthetical ("+0.005 to +0.02") adjudicated
  consistent with the pre-existing Exceptional Performance +0.03 example — the parenthetical
  names the Success Rules category specifically, the operative clause targets "routine
  successful work", and 0.03 ≪ 0.10 preserves the asymmetry invariant regardless. This is
  the recorded #521 regression-check confirmation.
- **INFO-2 (L2, route HUB/CBP)**: W4IP-DRAFT's N1 section lags its own ratified output —
  still imperative "Add" framing, three signature classes where ratified §4 has four, and
  no ratification annotation (N3 got one at `7ca821f7`; N1/#521 and N2/#523 did not).
  Draft-lifecycle sync is CBP/HUB-owned; precedent (`7ca821f7`) makes a marker-only
  annotation acceptable Legion-side if routed back.
- **INFO-3 (L3)**: r6.py:637 to_jsonld docstring says "camelCase for ontology alignment"
  but emits snake_case — which is what §1 AND r7-framework actually use. Code conformant;
  one false docstring phrase. Fold into any future r6.py touch (same pattern as C52-B16).
- **INFO-4 (L4, deflated LOW→INFO by verifier)**: trust-core's decay layer
  (`decay/temporal.rs` rate 0.01/**day**, grace 1 day, floor 0.3, entity-keyed) is a
  **different-model, different-layer** system, NOT a §7 implementer — `grep
  reputation-computation` in trust-core = 0; tensor/mod.rs:246 explicitly treats reputation
  as externally anchored. LAYER-SPLIT confirmation (C192 pattern), no reconciliation owed.
  Optional non-blocking doc-comment suggestion routed with the SDK bundle.
- **INFO-5 (L4)**: Rust has **no §5 rule-engine or §7 aggregation implementation**;
  `compute_reputation` is a self-disclosed uniform-shift convenience (C174
  self-disclaimer pattern — spec CORRECT). Python remains the sole §5/§7 implementer.
  The 3f941988 baselines fix itself is spec-CONFORMANT (clamp-then-recompute matches
  :427-431 "SDK parity" normative pattern). Net-new inventory fact: **four**
  non-delegating Rust decay surfaces exist (t3.rs decay, tensor/mod.rs t3_apply_decay,
  tensor/mod.rs:247 v3_apply_decay, decay/temporal.rs), all adjudicated non-§7-layer.
- **INFO-6 (L3/L4)**: mechanical substrate for N3, recorded: SDK inactivity decay is a
  scalar per (entity_lct, role_lct), dimension-blind, applied identically to talent —
  exactly matching its governing spec text.

### Negative results (verbatim-verifiable, selected)

- **Anti-value grep ALL-CLEAN (C192 §10.4 method)**: every §7 constant matches the Python
  SDK exactly — 30-day grace, −0.01/month, strict `>` 6-month/1.5× accelerator, −0.5 cap,
  0.5 baseline, 90-day horizon, exp(−age/30) recency, [0,1] and [−1,+1] clamps, clock-skew
  floor. The 1.5 accelerator and −0.5 cap appear NOWHERE in Rust (no false §7 mirror).
- **Vocabulary CLEAN**: whole-word grep for the ratified decision (allow|warn|deny|escalate)
  and response (notice|quarantine|correct|rehabilitate) vocabularies = zero stale/colliding
  uses in-target (§2 "Correcting own mistakes" is plain-English predating the vocabulary).
- **All inbound Coercive/Extractive citations SATISFIED by #521**: entity-types.md:423-426,
  SOCIETY_SPECIFICATION.md:481-484, web4-society-authority-law.md:235, hub-law-schema.md:217
  (F-a) — each cites target §4 and the category exists as described; "kinetic act
  (descriptor)" terminology consistent. hub-law-schema:185's N5 forward pointer is accurate
  *as pending state* (target §7 has no rehab-bound subsection yet — that is N5's port).
- **All outbound t3-v3 anchors resolve** (t3-v3 frozen since C122 `b2a98f7c` as expected);
  rep-001 note :592-598 verified against the live vector (temperament +0.005, modifiers []).
- **lct.rs 0.4.0 (#516) has no reputation-relevant surface change** (only
  `EntityType::Society => 0.5` coherence prior).
- **§4 trigger semantics, §5 analyze_factors weights (0.4/0.3/0.2), rule_triggered
  comma-join, WitnessAttestation Rust↔Python parity**: all verified at exact parity.
- SDK tests + vectors rep-001/-003/-004/-005 internally consistent with both spec and SDK.

---

## §C — Carry Ledger (post-C194)

**Consumed/closed this audit**: none newly (C154-N1 remains consumed, re-verified;
C192-N1 remains closed, #517 HELD re-verified).

**New outbound routes**:
- **C194-N1 + C194-N8 (+ INFO-4 doc-comment nit)** → SDK track (web4-core/web4-trust-core):
  serde wire-shape reconciliation (semver-sensitive post-0.4.0) + wasm factors param.
- **C194-N3 + C194-N4** → operator DESIGN-Q memo bundle (§7 decay layer disclosure:
  option A carve-out vs option B layer-disclosure block + mutual cross-refs + rate
  disambiguation).
- **C194-N5** → W4IP-N5 owner (bundle with the :387-394 note refresh already routed there).
- **C194-N7** → standing ReputationDelta shape-reconcile bundle (C84 X-1 / SDK track).
- **INFO-2** → HUB/CBP (W4IP-DRAFT N1/N2 ratification annotations).

**C195 disposition: REMEDIATION OWED (autonomous-class, this file)**: N2 (`return None`
one-liner, :416) + N6 (drop/annotate the `value` key, :525/:538/:545/:559). Both are
SDK+vector-concord pseudocode alignments with zero design content.

**Standing carries re-verified and unchanged**: C156-3 (sovereign_strength), C156-4
(temporal fold), carry-C46 (role_pairing_in_mrh), :387-394 note (N5-owned).

---

*Audit instrument: 5 pinned lenses, carry-exclusion list enforced (zero duplicate
re-reports of tracked carries), refute-by-default verification with independent live-file
re-reads. The one OVERSTATED deflation (L4-2 LOW→INFO) and the FALSE-free yield reflect
the finders' calibration; the verifier corrections that mattered were direction/bundling
refinements (N5 → bundle-not-standalone; N1 description-field deserialization aggravator;
INFO-5 four-not-three decay-surface inventory).*
