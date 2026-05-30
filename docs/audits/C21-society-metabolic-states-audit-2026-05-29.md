# C21 — SOCIETY_METABOLIC_STATES.md Internal Consistency Audit

**Audit ID**: C21
**Date**: 2026-05-29
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (419 lines, v1.0.0, "Proposed Standard")
**Cadence**: Informal C-series spec audit cycle (C12–C20 fully merged; this is the next read-only audit pass)
**Auditor session**: legion-web4-20260529-180057 (LEAD)
**Out of scope**: spec source edits, SDK edits, sister-doc finding-generation (cross-reference reads only)

---

## 1. Methodology

Single-file internal-consistency audit with cross-anchor verification. Severity tags: HIGH (correctness / multi-anchor canonical drift / implementation-blocking ambiguity), MEDIUM (substantive cross-doc gap or design defect), LOW (cosmetic correctness, single-site inconsistency), INFO (advisory, no remediation required), DEMOTED (considered, judged not a defect).

Each finding cites line numbers in the target spec (`L<n>`) and lists the authoritative artifact(s) used to verify. Each is tagged **AUTONOMOUS-ACTIONABLE** (wire-level remediation can be applied without operator design input) or **DESIGN-Q** (resolution requires operator/architect decision).

### Anchor authorities consulted

| Anchor | Path | Role in this audit |
|---|---|---|
| **Spec target** | `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` | The document under audit |
| **SDK canonical** | `web4-standard/implementation/sdk/web4/metabolic.py` | 8-state enum, energy multipliers, trust effects, transitions, wake penalty (header L4: "Canonical implementation per …") |
| **Sister SDK** | `web4-standard/implementation/sdk/web4/society.py` | `metabolic_state` field on `SocietyState`, `transition_metabolic_state()` (L256, L576) |
| **Test vector** | `web4-standard/test-vectors/metabolic/society-metabolic-states.json` (132L, 11 vectors) | Canonical conformance suite; named in SDK `metabolic.py:21` |
| **Ontology** | `web4-standard/ontology/web4-core-ontology.ttl` | Searched for `web4:MetabolicState` and related predicates |
| **ATP/ADP spec** | `web4-standard/core-spec/atp-adp-cycle.md` | Energy-cost framing for cross-check |
| **Sister doc 1** | `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` | Parent society spec, cross-reference search |
| **Sister doc 2** | `web4-standard/core-spec/web4-society-authority-law.md` | SAL governance spec, cross-reference search |
| **README index** | `web4-standard/README.md` | Spec listing (`L60` cites this doc as "NEW") |

---

## 2. Findings

### HIGH

#### H1 — §2.3 Sleep "trust tensor updates" semantics disagree across spec body, §5.1 table, and SDK
**Citation**: `L54` "Trust tensor updates batch hourly" (§2.2 Rest — same wording reused implicitly for Sleep behaviour discussion); `L70` "Trust tensors decay at 10% normal rate" (§2.3 Sleep); `L291` table row "Sleep | 10% decay rate" (§5.1); SDK `metabolic.py:108` `TrustEffect(update_rate=0.0, decay_rate=0.1, description="Minimal activity")`.

**Defect**: Sleep state has three different stories about its trust-update behaviour:
- **Spec body §2.3 `L70`**: only mentions *decay* ("Trust tensors decay at 10% normal rate") — silent on whether new updates apply.
- **Spec §5.1 table `L291`**: column "Trust Tensor Effect" = "10% decay rate" — again only decay.
- **SDK `metabolic.py:108`**: chose `update_rate=0.0` (frozen updates, no new T3/V3 changes accepted) and `decay_rate=0.1` (10% of normal decay) — a normative two-axis decision the spec never makes.

The spec's silence on update_rate forced the SDK to make a load-bearing canonical decision. If `update_rate=0` is correct, the spec needs to say so. If updates *should* happen during Sleep (e.g., batched), the SDK is wrong. Per BC#5 corpus sweep below, this same field-presence asymmetry recurs in 3 of 8 states.

**Class**: `spec-prose-vs-canon-table-vs-sdk-three-way-drift` (recurring C-series flagship; closely related to C17/C19 flagship pattern).

**Tag**: DESIGN-Q (operator/architect must decide whether Sleep accepts updates; mechanical fix not safe).

**Recommendation**: §5.1 column should be split into "Update rate" and "Decay rate" (separate semantic axes). §2.3 should explicitly state both — likely `update_rate = 0` if "ATP allocations frozen" (L69) is the design intent.

---

#### H2 — §1.2 "Each state maps to biological precedents" but list contains only 5 of 8 states' analogs
**Citation**: `L17-L24`:
```
### 1.2 Biological Inspiration

Each state maps to biological precedents:
- Sleep cycles for daily rhythms
- Hibernation for seasonal resource scarcity
- Torpor for emergency conservation
- Molting for structural renewal
- REM/dreaming for memory consolidation
```
vs §2.x analogs (`L43, L59, L75, L91, L107, L123, L139, L155`):
| State | §2.x "Biological Analog" | Listed in §1.2? |
|---|---|---|
| Active | "Awake, alert organism" (L43) | NO |
| Rest | "Light sleep, easily awakened" (L59) | NO |
| Sleep | "Deep sleep with REM cycles" (L75) | YES (Sleep cycles) |
| Hibernation | "Bear hibernation" (L91) | YES |
| Torpor | "Hummingbird torpor" (L107) | YES |
| Estivation | "Snail estivation during drought" (L123) | NO |
| Dreaming | "REM sleep" (L139) | YES (REM/dreaming) |
| Molting | "Crab molting its shell" (L155) | YES |

**Defect**: §1.2 makes a universal claim ("Each state maps to") and lists only 5/8. Active/Rest/Estivation analogs are absent from the inspiration list despite being defined in §2.x.

**Class**: `intro-claim-vs-body-count-mismatch` (analogous to C20 H1's "intro vs body count" pattern; C15 H1 reputation algorithm intro vs body).

**Tag**: AUTONOMOUS-ACTIONABLE.

**Recommendation**: Either (a) extend §1.2 list to all 8 analog categories, or (b) reframe as "Example precedents" / "Selected biological precedents include" so the universal claim is no longer made.

---

#### H3 — §5.1 Trust Tensor Effect column mixes incommensurable semantic categories
**Citation**: `L287-L296`:
```
| State | Trust Tensor Effect | Rationale |
|-------|-------------------|-----------|
| Active | Normal updates | Full operations |
| Rest | 90% update rate | Slightly delayed |
| Sleep | 10% decay rate | Minimal activity |
| Hibernation | Frozen | Preserved state |
| Torpor | Frozen + Alert bonus | Crisis response |
| Estivation | Internal only | Defensive mode |
| Dreaming | Recalibration | Pattern recognition |
| Molting | -20% temporary | Vulnerable period |
```
SDK had to fan one column into THREE fields (`metabolic.py:96-116`):
- `update_rate: float`
- `decay_rate: float`
- `temporary_penalty: float`
- (plus a `description: str` for the original prose)

**Defect**: Eight rows describe trust effects in eight different semantic registers:
- "Normal updates" / "Frozen" / "Recalibration" → *state of update process* (qualitative)
- "90% update rate" → *update rate* (rate)
- "10% decay rate" → *decay rate* (different rate)
- "Frozen + Alert bonus" → frozen plus undefined feature ("Alert bonus" — see M2)
- "Internal only" → *scope* (qualitative scope-restriction)
- "-20% temporary" → *temporary penalty delta* (different axis)

The single column conflates rate-of-update, rate-of-decay, scope-of-update, and temporary-T3-penalty. The SDK necessarily had to interpret each row separately and could not derive a uniform data model from the table. Any independent reimplementation will diverge.

**Class**: `table-design-defect-causes-implementation-divergence` (new class for C-series taxonomy).

**Tag**: DESIGN-Q (table redesign requires operator decision on what semantic axes are normative).

**Recommendation**: Redesign §5.1 as a multi-column table with explicit axes (e.g., `Update rate (0..1)`, `Decay rate (0..1)`, `Update scope`, `Temporary penalty`, `Notes`). The SDK already encodes the right shape — back-port that shape into the spec.

---

### MEDIUM

#### M1 — Parent doc orphaning: SOCIETY_SPECIFICATION.md and web4-society-authority-law.md contain ZERO references to metabolic states
**Citation**: `grep "metabolic\|Metabolic" web4-standard/core-spec/SOCIETY_SPECIFICATION.md` → no matches. Same for `web4-society-authority-law.md`.

**Defect**: The parent society spec defines society lifecycle (Genesis → Bootstrap → Operational, §1.3 of SOCIETY_SPECIFICATION.md L55-L70) without acknowledging metabolic states as part of that lifecycle. SAL (governance authority) defines society rules-of-law without referencing metabolic-state-bound permissions (e.g., whether laws may change during Molting). The metabolic states subsystem is informationally orphaned from the two specs that ought to compose with it.

**Class**: `parent-doc-cross-reference-orphan` (analogous to C18 M5 dictionary-entities orphan; C19 M2 multi-device parent-orphan).

**Tag**: AUTONOMOUS-ACTIONABLE (add a §X cross-reference paragraph in each parent spec — but BC#10 prevents this audit from doing so; remediation PR scope).

**Recommendation**: C21 remediation should add (1) a §1.4 paragraph in SOCIETY_SPECIFICATION.md describing operational-mode variability with link to SOCIETY_METABOLIC_STATES.md, and (2) a SAL paragraph noting that some governance actions (law amendments) require Molting state.

---

#### M2 — "Alert bonus" phantom feature in §5.1 Torpor row, undefined in §2.5 body or anywhere else
**Citation**: `L293` "Torpor | Frozen + Alert bonus | Crisis response"; §2.5 body `L102` only says "Trust tensors frozen at last values" — no mention of "Alert bonus"; §5.2 reliability score `L302-L323` does not reference "Alert bonus"; SDK `metabolic.py:110` faithfully replicates the phantom: `description="Frozen + alert bonus"`.

**Defect**: "Alert bonus" appears once in the table and is propagated to the SDK as a description string, but is nowhere defined. Implementers reading the table cannot determine whether "Alert bonus" is a numeric T3 bump, a witness-quorum exception, a wake-trigger sensitivity boost, or simply prose flavour.

**Class**: `phantom-feature-table-only` (single-anchor phantom — same family as C20 M4 birth-certificate circularity; C17 H1 placeholder semantics).

**Tag**: AUTONOMOUS-ACTIONABLE (two valid resolutions: define "Alert bonus" in §2.5 body with a numeric semantics, or remove it from §5.1 and SDK).

**Recommendation**: Decide whether Torpor has an alert-detection-sensitivity bonus that adds to T3/V3 on successful threat recognition. If yes, define it in §2.5 with a numeric delta and a triggering condition. If no, strip "+ Alert bonus" from the table.

---

#### M3 — Emergency states (Torpor, Estivation) reachable ONLY from Active per §3.1 — coverage gap for low-energy states
**Citation**: §3.1 transition matrix `L164-L191`:
- `L169`: "Active → Torpor: ATP reserves < 10%"
- `L172`: "Active → Estivation: Threat detected"
- All other "→ Torpor" and "→ Estivation" transitions: **absent**.

Verified against SDK `metabolic.py:132-158`: SDK transition list contains exactly the spec matrix; no Rest→Torpor, no Sleep→Torpor, no Estivation→Torpor, no Sleep→Estivation, etc.

**Defect**: If a society is already in Rest, Sleep, Hibernation, Dreaming, or Molting when ATP reserves drop below 10%, there is no defined transition into Torpor — the very state designed for that condition (§2.5 `L94-L108` "Crisis mode when resources critically low"). Same gap for threat-detected entry to Estivation from any non-Active state. This leaves the society stuck in an inapplicable state during a crisis. Mirrored gap: a society in Hibernation that encounters a threat has no Estivation path; it must wake to Active first (incurring 100x wake penalty per §6.2 `L347`) just to enter Estivation.

**Class**: `transition-graph-emergency-coverage-gap`.

**Tag**: DESIGN-Q (operator decision: should emergency states absorb from any state, or is current Active-only design intentional to avoid emergency-state oscillation? May be intentional if cost-of-transition is meant to be deliberate.)

**Recommendation**: Either document the design intent ("emergency states require deliberate Active-first transition") in §3.1 introduction, or add the missing transitions (e.g., `* → Torpor: ATP reserves < 10%` as a universal trigger).

---

#### M4 — §6.1 formula labelled "Daily ATP Cost" but baseline is hourly
**Citation**: `L334-L336`:
```
Daily ATP Cost = Baseline * State_Multiplier * Society_Size
```
vs §4.1 schema `L235`: `baseline_cost: "100 ATP/hour"`; SDK `metabolic.py:198-220` `energy_cost(state, baseline_cost_per_hour, society_size, hours)` — hourly baseline times hours.

**Defect**: Either the formula is wrong (missing `* 24` or `* hours`) or the label is wrong ("Daily" should be "Hourly"). SDK chose to interpret the formula as `Hourly * State_Multiplier * Society_Size * hours_elapsed`, which is the practical reading but doesn't match the literal §6.1 label.

**Class**: `unit-label-mismatch` (analogous to C15 §7 algorithm-spec-vs-SDK divergence — though this is a unit not algorithm defect).

**Tag**: AUTONOMOUS-ACTIONABLE.

**Recommendation**: Change "Daily ATP Cost" to "Hourly ATP Cost" and add a sentence: "For longer periods, multiply by the number of hours." OR change formula to `Baseline_Hourly * State_Multiplier * Society_Size * 24` and rename `baseline_cost` in §4.1 to make explicit it is hourly.

---

#### M5 — "Dormant states" used colloquially in §6.2 without definition; SDK partitions states differently
**Citation**: §6.2 `L340-L353`:
> "Premature wake from dormant states incurs cost:"
followed by a function that applies penalties to Sleep, Hibernation, Dreaming.

vs SDK `metabolic.py:374-382` `DORMANT_STATES = frozenset({REST, SLEEP, HIBERNATION, TORPOR, ESTIVATION})` (5 states) and `ACTIVE_STATES = frozenset({ACTIVE, DREAMING, MOLTING})` (3 states).

**Defect**: Spec §6.2 describes wake penalties as applying to "dormant states" and then includes Dreaming — but the SDK classifies Dreaming as an *active* state (in `ACTIVE_STATES`). The term "dormant" is loose in the spec and means "any state with reduced operations" colloquially, but the SDK partitions it precisely. Spec is the canonical authority but never defines "dormant" — the SDK had to choose.

**Class**: `loose-term-canonical-divergence`.

**Tag**: DESIGN-Q (which partition is normative? Is Dreaming dormant or active? Spec needs to state.)

**Recommendation**: Add a definition early in §2 distinguishing "dormant" (reduced operations + delayed transactions) from "active" (full operations) with explicit state-by-state classification. Reconcile §6.2's "dormant states" claim with the actual penalty-incurring states.

---

#### M6 — Test vector orphan: spec contains zero reference to `test-vectors/metabolic/society-metabolic-states.json`
**Citation**: `grep "test-vector\|test_vector\|society-metabolic-states\.json" core-spec/SOCIETY_METABOLIC_STATES.md` → no matches. Test vector exists at `web4-standard/test-vectors/metabolic/society-metabolic-states.json` (132L, 11 vectors covering energy cost, wake penalty, transition validity, reliability scoring); SDK `metabolic.py:21` references it as the canonical conformance suite.

**Defect**: The spec is unaware of its own conformance vectors. A reader of the spec cannot find the canonical test suite from the spec itself; only the SDK knows about it. Cross-language reimplementations have no spec-level pointer to "validate against this vector file."

**Class**: `spec-to-conformance-vector-orphan` (analogous to C18 H3 — spec's flagship example failed its own conformance vector; here weaker: spec doesn't even know its conformance vector exists).

**Tag**: AUTONOMOUS-ACTIONABLE.

**Recommendation**: C21 remediation should add a "Conformance" section (numbered §10 or as part of §9) citing the test-vector path with a one-line summary of what each vector class covers.

---

#### M7 — Ontology absence: `web4:MetabolicState` and metabolic-related predicates absent from `web4-core-ontology.ttl` (subordinate-ontology cluster — 6th audit)
**Citation**: `grep -i "metabolic\|MetabolicState" web4-standard/ontology/web4-core-ontology.ttl` returns only 2 lines (L85, L179) — both are inline `rdfs:comment` strings about ATP/ADP cycle, neither defines a `web4:MetabolicState` class. `t3v3-ontology.ttl` likewise contains no metabolic states.

vs SDK `metabolic.py:62-72` defines `MetabolicState` as a first-class enum with 8 named members; `society.py:256` makes `metabolic_state: MetabolicState` a required field on `SocietyState`; canonical test vectors enumerate all 8 named state strings; spec dedicates 419 lines to defining the subsystem.

**Defect**: Metabolic state is a first-class spec + SDK + test-vector concept with zero ontological representation. RDF reasoners querying a society LCT cannot extract "current metabolic state," reason about valid transitions, or filter by dormancy without out-of-band knowledge. The canonical equation (`Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP`) treats RDF as the ontological backbone, but the metabolic-states subsystem has no RDF presence.

**Cluster status**: This is the **6th C-series audit** to identify the subordinate-ontology gap as a finding (C16-M8 + C17-M1 + C18-M6 + C19-M5 + C20-M5 + C21-M7). Memory `MEMORY.md` notes the 5-audit operator-engagement threshold was reached at C20. This 6th hit further strengthens the case for a single bundled subordinate-ontology TTL extension PR (memory carry-NEW-A) — *not* drafted in this audit per BC#7.

**Class**: `subordinate-ontology-cluster` (6-audit operator-engagement-ready).

**Tag**: DESIGN-Q (introduces new ontology semantics — bundled TTL extension is "operator-engagement candidate, ready to draft" per memory exit #132).

**Recommendation**: Bundle with the C16/C17/C18/C19/C20 subordinate-ontology cluster as a single operator-engaged TTL extension PR. Predicates to draft (autonomous list, operator to ratify):
- `web4:MetabolicState` class (with 8 named instances)
- `web4:hasMetabolicState` predicate (Society → MetabolicState)
- `web4:isDormant`, `web4:isActive` boolean predicates
- `web4:validTransitionTo` predicate (MetabolicState → MetabolicState, with `web4:trigger` literal)
- `web4:energyMultiplier`, `web4:witnessFraction` data properties

---

#### M8 — §3.1 transition matrix and §4.1 config schema have reconciliation gaps (combined finding)
**Citation**:
- §3.1 `L172`: "Active → Estivation: Threat detected" (qualitative) vs §4.1 `L229-L231`: `estivation: condition: "threat_score > 80"` (quantitative threshold 80, with `clear: "threat_score < 20"` for the reverse).
- §3.1: hibernation-wake mechanism `L180` says "external witness or timeout" without a duration; §4.1 `L221-L223`: `wake_on: ["new_citizen", "external_witness", "timeout:90d"]` (90-day timeout, plus a "new_citizen" trigger absent from §3.1).
- §4.1 has trigger configs for only 3 of 8 states (hibernation, torpor, estivation); 5 states (rest, sleep, dreaming, molting, plus hibernation-exit) have no schema representation.

**Defect**: Three distinct reconciliation gaps between the matrix and the configuration schema, all compounding:
1. Same trigger expressed both qualitatively (§3.1) and quantitatively (§4.1) without cross-reference.
2. Hibernation timeout (90d) and wake-on-new-citizen are normative facts that appear only in the schema, not the matrix.
3. Schema is incomplete (3/8 state coverage).

**Class**: `matrix-vs-schema-reconciliation-gap`.

**Tag**: AUTONOMOUS-ACTIONABLE (mechanical: import schema thresholds into matrix or vice versa; expand schema coverage).

**Recommendation**: Update §3.1 to include the quantitative thresholds inline (e.g., "Active → Estivation: Threat detected (threat_score > 80, see §4.1)"). Add Hibernation timeout to the matrix ("Hibernation → Active: external witness, new_citizen trigger, or 90-day timeout"). Expand §4.1 schema to include triggers for all 8 states OR document that §4.1 is illustrative-not-normative.

---

### LOW

#### L1 — §2.3 Sleep biological analog "Deep sleep with REM cycles" overlaps with §2.7 Dreaming "REM sleep"
**Citation**: `L75` "Biological Analog: Deep sleep with REM cycles" (§2.3 Sleep) vs `L139` "Biological Analog: REM sleep" (§2.7 Dreaming).

**Defect**: Sleep is described as a separate state from Dreaming, but its analog folds REM into itself. REM (rapid eye movement) is biologically the dreaming phase of sleep; calling Sleep "Deep sleep with REM cycles" conflates the two states whose distinct purpose is exactly why the spec defines them separately.

**Tag**: AUTONOMOUS-ACTIONABLE.

**Recommendation**: Change §2.3 Sleep analog to "Deep non-REM sleep" or "Slow-wave sleep" to disambiguate from §2.7 Dreaming.

---

#### L4 — §2.6 Estivation energy cost (10%) lower than §2.3 Sleep (15%) despite "defensive posture maintained"
**Citation**: `L122` "Energy Cost: 10% of baseline" (§2.6 Estivation, characterised by "Defensive posture maintained", "Internal consolidation only" — implies vigilance) vs `L74` "Energy Cost: 15% of baseline" (§2.3 Sleep, "Deep rest with minimal maintenance operations").

**Defect**: A state with "defensive posture maintained" should plausibly cost *more* than one with "minimal maintenance operations." Energy ordering goes: Active 100 → Molting 60 → Rest 40 → Dreaming 20 → Sleep 15 → Estivation 10 → Hibernation 5 → Torpor 2. Estivation at 10% sitting below Sleep at 15% reads as an anomaly given the prose descriptions.

**Tag**: DESIGN-Q (could be intentional — defensive posture might mean *suspended* external ops + only *internal* low-cost consolidation; needs operator confirmation).

**Recommendation**: Either justify the 10% < 15% ordering in §2.6 prose (e.g., "Defensive posture is achieved through suspension of external interactions, allowing per-unit-cost lower than scheduled sleep maintenance") or transpose to align with prose intuition.

---

#### L5 — §2.2 Rest "New citizens queued for active period" vs SDK `accepts_new_citizens(REST)=False`
**Citation**: `L56` "New citizens queued for active period" (§2.2 Rest) vs SDK `metabolic.py:410-413` `accepts_new_citizens` returns `True` only for `MetabolicState.ACTIVE`.

**Defect**: Spec says Rest *queues* new citizens (accept-and-defer); SDK rejects outright (refuse + caller-retries-later). Different semantics for downstream caller error handling.

**Tag**: DESIGN-Q (which is correct: queued-acceptance or refusal? Affects API contract.)

**Recommendation**: If queueing is the design, SDK needs an `accepts_new_citizens_queued()` or similar; if refusal is the design, §2.2 should change "queued for active period" to "deferred until active state."

---

#### L6 — §5.1 Molting "-20% temporary" magic number absent from §2.8 body
**Citation**: `L296` "Molting | -20% temporary | Vulnerable period" (§5.1 table); §2.8 body `L142-L156` characterises Molting as "Vulnerable transition", "Witness rotation", "Treasury rebalancing", "Citizenship review", "Temporary performance degradation", "Heightened security" — none mention -20% or any numeric T3 penalty.

**Defect**: The -20% magic number appears only in the table; SDK `metabolic.py:113-115` faithfully replicates it as `temporary_penalty=-0.20`. The source of the -20% derivation is uncited (why -20% and not -10% or -30%?).

**Tag**: AUTONOMOUS-ACTIONABLE.

**Recommendation**: Either move the -20% definition into §2.8 with a brief derivation, or remove and replace with a non-magic-number framing (e.g., "T3 penalty parameterised by society's molt-risk configuration").

---

#### L7 — §6.2 wake penalty incomplete coverage (Sleep, Hibernation, Dreaming only)
**Citation**: `L342-L353`:
```python
penalties = {
    'sleep': 10 * incompleteness,
    'hibernation': 100 * incompleteness,
    'dreaming': 50 * incompleteness
}
```
SDK `metabolic.py:226-230` mirrors exactly.

**Defect**: Torpor, Estivation, and Molting are all states with characteristic durations (Torpor has "auto-recovery" §2.5 L104; Estivation has "Waiting for conditions to improve" §2.6 L119; Molting has "Renewal complete" exit §3.1 L190). Premature exits from any of these could plausibly incur cost — e.g., interrupted molt leaves the society partially restructured. Spec is silent.

**Tag**: DESIGN-Q (do these states have penalties? Or are they treated as best-effort durations? Operator decision.)

**Recommendation**: Either extend the penalty table to cover all 8 states (with explicit `0` for the no-penalty cases — Active, Rest, plus any others operator decides), or document the omission ("Only scheduled states incur penalty; emergency states are interruptible without cost").

---

### INFO (no remediation required; advisory)

#### INFO1 — Document is 16+ months old, still Status "Proposed Standard"
**Citation**: `L4` "Date: January 17, 2025"; `L5` "Status: Proposed Standard". Audit date: 2026-05-29.

Other C-series targets have evolved past "Proposed" (e.g., `presence-protocol.md` has CHANGELOG-tracked iteration). The author/operator may wish to update Status now that SDK + test vectors + multi-spec dependencies exist.

#### INFO2 — No CHANGELOG sibling file
**Citation**: `ls web4-standard/core-spec/*METABOLIC*CHANGELOG*` → no matches. Some sister specs maintain a CHANGELOG sibling file (e.g., `presence-protocol-CHANGELOG.md`).

This is informational; CHANGELOG-per-spec is not universal across the corpus.

#### INFO3 — §4.2 sketch code uses undefined identifiers `CYCLE_LENGTH` and `deterministic_shuffle`
**Citation**: `L251-L258`:
```python
def select_active_witnesses(witnesses, required_count, block_height):
    cycle = block_height // CYCLE_LENGTH
    seed = hash(f"{cycle}:{society_lct}")
    shuffled = deterministic_shuffle(witnesses, seed)
```
`CYCLE_LENGTH` and `deterministic_shuffle` are used without definition; `society_lct` is a free variable. Code is illustrative.

Sketch-code-not-runnable pattern is common in spec docs; not a defect, but reader-confusion risk.

#### INFO4 — §4.3 `SentinelWitness.monitor()` uses undefined global `society`
**Citation**: `L271-L278`:
```python
def monitor(self):
    while society.state in ['hibernation', 'torpor']:
        self.send_heartbeat()
        if self.check_wake_triggers():
            society.wake()
            break
        time.sleep(self.heartbeat_interval)
```
Class binds `self.society_lct` (L267) but the loop accesses `society` as a global without `self.` prefix. Inconsistent with the rest of the class.

Sketch-code defect; advisory.

#### INFO5 — §7.2 attack-prevention list omits Dreaming despite §7.1 listing Dreaming vulnerability
**Citation**: §7.1 table `L362-L368` includes "Dreaming | Data reorganization | Checkpointing". §7.2 attack-prevention list `L374-L377` covers Sleep, Hibernation, Torpor, Molting — Dreaming absent.

Advisory: minor §7.1 ↔ §7.2 misalignment.

#### INFO6 — §4.1 society_lct example uses value-only placeholder
**Citation**: `L210` `society_lct: "lct-society-example-001"`.

Same value-only-placeholder pattern flagged in C20 H2's recurring cluster (LCT id as bare string vs structured LCT envelope). Documented out-of-scope here because §4.1 is illustrative YAML, not normative wire format. Advisory cross-corpus tracker.

---

### DEMOTED (considered, not pursued as findings)

#### D1 — SDK `accepts_transactions(MOLTING) = True` (`metabolic.py:407`) where §2.8 doesn't say so explicitly
**Reason for demotion**: §2.8 mentions "Society laws under active revision" + "Temporary performance degradation" — neither confirms nor denies transaction acceptance. SDK chose "yes (degraded)" as a reasonable interpretation. Not a clear defect; ambiguity is in the spec but it's not contradicted, just unspecified. If the operator wants to disambiguate, that's a clarification request, not an audit finding.

#### D2 — SDK `DORMANT_STATES` ∪ `ACTIVE_STATES` partition has `accepts_transactions(DREAMING) = False` despite Dreaming ∈ ACTIVE_STATES
**Reason for demotion**: This is an SDK-internal categorisation inconsistency (the SDK's own `ACTIVE_STATES` membership predicate disagrees with its own `accepts_transactions` predicate for Dreaming). Out of scope for this spec audit per BC#10; should be filed against the SDK if pursued. Cross-referenced for the next SDK-side audit.

---

## 3. Findings Summary

| Severity | Count | IDs | Autonomous-actionable | Design-Q |
|---|---|---|---|---|
| **HIGH** | 3 | H1, H2, H3 | 1 (H2) | 2 (H1, H3) |
| **MEDIUM** | 8 | M1, M2, M3, M4, M5, M6, M7, M8 | 5 (M1, M2, M4, M6, M8) | 3 (M3, M5, M7) |
| **LOW** | 5 | L1, L4, L5, L6, L7 | 2 (L1, L6) | 3 (L4, L5, L7) |
| **INFO** | 6 | INFO1-INFO6 | (advisory) | (advisory) |
| **DEMOTED** | 2 | D1, D2 | (not pursued) | (not pursued) |

**Totals**: 16 actionable findings (3H + 8M + 5L) + 6 INFO + 2 DEMOTED. Of 16 actionable: 8 AUTONOMOUS-ACTIONABLE (H2 + M1, M2, M4, M6, M8 + L1, L6), 8 DESIGN-Q (H1, H3 + M3, M5, M7 + L4, L5, L7). The 50/50 autonomous/design-Q split echoes the graceful-partial-remediation pattern that has worked across C16–C20.

(Recount: AUTONOMOUS = H2, M1, M2, M4, M6, M8, L1, L6 = 8. DESIGN-Q = H1, H3, M3, M5, M7, L4, L5, L7 = 8. Equal split.)

---

## 4. P4 Reconciliation (BC#6)

Open operator-blocked item P4 in SESSION_FOCUS.md is recorded as:

> P4: MetabolicState reconciliation — 5-state (Rust/spec) vs 7-state (Python)

**Audit-verified counts**:

| Anchor | State count | Citation |
|---|---|---|
| Spec §1 intro claim | **8** | `L11` "defines eight metabolic states" |
| Spec §2 body enumeration | **8** | §2.1–§2.8 (`L30, L46, L62, L78, L94, L110, L126, L142`) |
| SDK `MetabolicState` enum | **8** | `metabolic.py:62-72` (ACTIVE, REST, SLEEP, HIBERNATION, TORPOR, ESTIVATION, DREAMING, MOLTING) |
| SDK `ENERGY_MULTIPLIERS` dict | **8** | `metabolic.py:77-86` |
| Test vector named states | **8** | `test-vectors/metabolic/society-metabolic-states.json` covers all 8 in transition + energy vectors |
| Ontology `web4:MetabolicState` | **0** (absent) | `grep -i metabolic web4-core-ontology.ttl` → no class |
| Rust toolchain (not in tree) | not verified in this audit | external `web4-trust-core` Rust repo not present in `web4-standard/`; cannot verify the Rust count |

**Conclusion**: **P4 IS RESOLVED-AS-STALE** with respect to spec ↔ Python SDK ↔ test vectors (all three at 8 states, fully aligned). The "5-state Rust" claim cannot be verified from this repo (Rust toolchain external); if the Rust side has only 5, it is the Rust side that is behind, not the spec or Python. The tracker entry referencing "5-state spec" is **factually incorrect at this date** — the spec defines 8 and has done since v1.0.0 (Jan 2025).

**Net-new drift**: Ontology absence (0 states defined in `web4-core-ontology.ttl`) is a *new* drift axis not captured in P4. Recommend P4 close-out and replace with a new operator item "Metabolic ontology gap" if the operator wants to track the M7 subordinate-ontology finding separately from the bundled cluster.

---

## 5. Subordinate-Ontology Cluster Tracker (BC#7)

Cluster history:
- C16-M8 — SAL subordinate predicates (federation, society membership)
- C17-M1 — Dictionary-entity subordinate predicates
- C18-M6 — ACP framework subordinate predicates
- C19-M5 — Multi-device LCT binding subordinate predicates
- C20-M5 — Capability level subordinate predicates
- **C21-M7 (this audit)** — MetabolicState subordinate predicates (class + 8 instances + 5+ data/object predicates)

**Cluster count**: **6 audits** identifying the same root gap (audit threshold met at C20=5; this is the 6th confirmation).

**Per BC#7, no autonomous TTL drafting in this audit.** The bundled TTL extension PR (memory carry-NEW-A) remains operator-engagement-flagged. M7 should be added to the cluster manifest for the operator-engaged session.

---

## 6. BC#5 Corpus Sweep — HIGH cluster (§5.1 table vs §2.x body trust-effect framing)

H1 and H3 both concern §5.1 column-semantic drift from §2.x body. Per BC#5, swept all 8 §2.x rows for body↔table consistency on trust-effect framing:

| State | §2.x body trust mention | §5.1 row | Aligned? |
|---|---|---|---|
| Active (§2.1) | "Immediate trust tensor updates" (L38) | "Normal updates" (L289) | ✓ aligned |
| Rest (§2.2) | "Trust tensor updates batch hourly" (L54) | "90% update rate" (L290) | ⚠ different framing (cadence vs rate) |
| Sleep (§2.3) | "Trust tensors decay at 10% normal rate" (L70) | "10% decay rate" (L291) | ⚠ body+table aligned on decay, both silent on updates (H1) |
| Hibernation (§2.4) | "Trust tensors frozen" (L87) | "Frozen" (L292) | ✓ aligned |
| Torpor (§2.5) | "Trust tensors frozen at last values" (L102) | "Frozen + Alert bonus" (L293) | ⚠ "Alert bonus" not in body (M2) |
| Estivation (§2.6) | "Trust preserved internally" (L120) | "Internal only" (L294) | ✓ aligned |
| Dreaming (§2.7) | "Trust tensor recalibration" (L134) | "Recalibration" (L295) | ✓ aligned in word but neither defines what "recalibration" *does* to T3/V3 values |
| Molting (§2.8) | "Heightened security during transition" (L152) | "-20% temporary" (L296) | ⚠ "-20%" not in body (L6) |

**Sweep outcome**: 4 of 8 rows (Rest, Sleep, Torpor, Molting) have body↔table inconsistencies, plus Dreaming has a poorly-defined cell. Confirms H1+H3 are systemic, not localised. No new HIGH-class findings missed by the audit; M2 (Alert bonus) and L6 (-20%) already capture the table-only inserts.

---

## 7. BC#3 Line-Citation Sweep

Re-verified every `L<n>` citation in this audit against the live file (`SOCIETY_METABOLIC_STATES.md` at audit time, `git rev-parse HEAD = b6383e71`). All citations confirmed accurate after **3 corrections** caught and applied during sweep:
- Initial draft of H1 cited `L70` as "decay at 15%"; corrected to "decay at 10% normal rate" (15% is the energy cost, not decay rate).
- Initial draft of M3 listed Sleep→Estivation as a missing transition twice (once explicitly, once by implication); de-duplicated.
- Initial draft of INFO5 cited `L373-L377` for the attack-prevention list; actual list is `L374-L377` (L373 is the blank line between section intro and the numbered list).

No remaining off-by-one errors detected after the sweep. BC#3 discipline catches this audit's third real-defect class — line-citation drift in advisory INFO findings is the same off-by-one family that BC#3 caught in C19 and C20 in higher-tier findings; advisory-tier discipline holds.

---

## 8. PR-Body Discipline Reference (BC#9)

The next-step C21 remediation PR (separate from this audit PR) should:
- Apply the 8 AUTONOMOUS-ACTIONABLE findings (H2, M1, M2, M4, M6, M8, L1, L6) in a single PR matching the C-series partial-remediation pattern.
- Defer the 8 DESIGN-Q findings (H1, H3, M3, M5, M7, L4, L5, L7) to operator-engagement (M7 is part of the subordinate-ontology cluster bundle).
- INFO items are advisory; no PR action required.
- DEMOTED items: D1 archived; D2 should be added to a future SDK-side audit (out of C-series scope).

Cross-track follow-up: the parent-orphan finding (M1) requires edits to TWO additional specs (SOCIETY_SPECIFICATION.md, web4-society-authority-law.md). The remediation PR should bundle all three edits — this is one finding with three file-level effects, not three findings.

---

## 9. Conclusion

C21 audit identified **16 actionable findings + 6 INFO + 2 DEMOTED** in `SOCIETY_METABOLIC_STATES.md`, with the recurring C-series flagship class (`spec-prose-vs-canon-table-vs-sdk-three-way-drift` — H1, H3) present and corpus-confirmed across half the §5.1 rows. The audit:

- Resolves open operator-blocked item **P4 as STALE** (verified spec/SDK/test-vectors at 8 states unanimously).
- Increments the **subordinate-ontology cluster** to **6 audits** (M7), further strengthening the operator-engagement case for the bundled TTL extension PR (memory carry-NEW-A).
- Surfaces the **test-vector-orphaning** pattern (M6) — spec doesn't know its own conformance vector exists — extending the C18 H3 family.
- Surfaces the **parent-doc orphaning** pattern (M1) — SOCIETY_SPECIFICATION.md and SAL have zero metabolic references — extending the C18 M5 / C19 M2 family.

8 findings are **autonomous-actionable** for a clean remediation PR (typical C-series shape); 8 are **design-Q** requiring operator engagement. The autonomous half follows the proven graceful-partial-remediation pattern established at C16 and reused through C20.

Next-step: **SEPARATE** C21-remediation PR. Do NOT bundle remediation into this audit PR.

---

*Audit produced under Autonomous Session Protocol v2 by legion-web4-20260529-180057 (LEAD voice, exit #133). Policy approval: APPROVED first-pass with 11 BCs; this document satisfies BC#1 (single new file in `docs/audits/`), BC#2 (severity-tagged with line citations and Findings Summary), BC#3 (line-citation sweep run + result reported), BC#4 (anchor authorities named explicitly with paths + lines), BC#5 (HIGH-cluster corpus sweep run + result reported), BC#6 (P4 reconciliation section), BC#7 (subordinate-ontology cluster tracker incremented without autonomous TTL drafting), BC#8 (16 actionable findings — within the >18 ceiling, no doc-split needed), BC#10 (no scope expansion to SOCIETY_SPECIFICATION.md — sister-doc cross-reads only, no findings generated against it).*
