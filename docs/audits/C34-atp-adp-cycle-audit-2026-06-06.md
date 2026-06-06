# C34 Audit: `atp-adp-cycle.md` Delta Re-Audit

**Date**: 2026-06-06
**Auditor**: Autonomous session (Legion, web4 track) — multi-agent workflow (5 finder dimensions × refute-by-default adversarial verification)
**Document**: `web4-standard/core-spec/atp-adp-cycle.md` (728 lines)
**Baseline**: C11 internal-consistency audit (`docs/audits/atp-adp-cycle-internal-consistency-2026-05-23.md`, 9 findings: 1H+6M+2L), remediated in PR #227
**Methodology**: C-series delta re-audit. §A re-verifies each C11 finding against the LIVE spec; the remaining sections surface NEW findings across internal-consistency, SDK alignment (`web4-standard/implementation/sdk/web4/atp.py`), cross-spec drift from the C24–C33 discovery wave (identifier schemes / errors / security / data-formats), and a primitive-clustered third pass (`auditor-blindspot-pattern`).
**SDK alignment**: Checked against `web4-standard/implementation/sdk/web4/atp.py` (393 lines).

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 1 | H1 |
| MEDIUM | 2 | M1, M2 |
| LOW | 6 | L1, L2, L3, L4, L5, L6 |
| INFO | 3 | I1, I2, I3 |
| CROSS-TRACK (to open C33 decision) | 1 | X1 |
| **Total actionable** | **12** | |

**Delta result (§A)**: All **9 C11 findings HELD** (remediated and not regressed). Two
C11 fixes left adjacent imperfections that surface here as NEW findings (the C11-H1
`caller` fix did not also define the sibling `witnesses` variable → **H1**; the C11-M6
two-state reconciliation landed in the spec but the SDK docstring wording lags → **I2**).
Two C11 LOW items (unnumbered Overview, JSON `type` vs `@type`) remain CARRIED — recorded
in §A and re-surfaced at their NEW IDs (I-carried / **L6**).

**Classification split**: 9 AUTONOMOUS · 1 DESIGN-Q (M2 — route to operator, do **not**
self-resolve) · 1 CROSS-TRACK (X1 — folds into the open C33 B-H1 identifier decision) ·
1 SDK-track (I2).

**Anti-padding statement**: 19 raw findings were generated; 2 were refuted outright and
6 were severity-downgraded under refute-by-default verification (see §F). This document
reports only what survived. The known C7/C9/C10/C11 *cross-doc overcall* streak was
actively deflated: the largest deflation was the "error-names-not-in-taxonomy" finding,
demoted HIGH→LOW (§E/L-note) because illustrative pseudocode exceptions are not wire
errors. Numbering is clean; no fabricated severities.

---

## §A — C11 Baseline Delta-Persistence

Each C11 finding re-verified against the live 728-line spec (the spec grew 689→728 lines
post-remediation; verified against live content, not C11's line refs).

| C11 ID | Title | Status | Evidence (live) |
|--------|-------|--------|-----------------|
| **H1** | §2.4 pseudocode undefined var `caller` | **HELD** | Line 168 now `def slash_atp(caller, violator, amount, evidence):` with docstring + comment (175–176). *But a sibling undefined-var `witnesses` remains at line 198 → see NEW **H1**.* |
| **M1** | §3.1 `charge_rate` doesn't match example data | **HELD** | Line 226 `charge_rate: 0.15` with comment "ATP/(ATP+ADP)"; ATP 15 000 000 / total 100 000 000 = 0.15 ✓. Allocations sum (90+5+3+2 M)=100 M ✓. |
| **M2** | R6 vs R7 terminology | **HELD** | §2.3 R6/R7 note (lines 154–161) explicitly scopes ATP→ADP as R6, with R7 reputation distinction. |
| **M3** | "MUST NOT hard-code fee rates" vs SDK default `0.05` | **HELD** | §6.3 added (533–551); SDK `transfer()` default now `fee_rate=0.0` (atp.py:237) with docstring citing §6.3; residual `sybil_cost` `0.05` documented as simulation parameter (atp.py:355–359). |
| **M4** | No cross-references to dependent specs | **HELD** | §References section added (713–727) + inline R6/R7/T3-V3/escrow notes. *One new cross-ref is imperfect → see NEW **L4**.* |
| **M5** | §4.3 attribution percentages hard-coded | **HELD** | §4.3 disclaimer (379–381): "illustrative defaults, not protocol constants … MUST NOT hard-code". |
| **M6** | SDK three-pool model not reflected in spec two-state | **HELD (spec side)** | §7.1 escrow note (564–570): "locked … remains ATP, not a third token state". Residual: SDK docstring still says "three sub-pools" → see NEW **I2**. |
| **L1** | Unnumbered "Overview" before §1 | **CARRIED** | Line 3 `## Overview` still unnumbered. House-style across the corpus; re-recorded as **I-carried** (INFO, no action recommended absent a corpus-wide convention). |
| **L2** | JSON examples use `"type"` not `"@type"` | **CARRIED** | 3× `"type":` (lines 43, 123, …), 0× `"@type":`. SDK `to_jsonld()` emits `"@type"`. Re-recorded as NEW **L6**. |

**Verdict**: zero regressions of the *substance* of any C11 finding. This is a
well-remediated spec. The NEW findings below are predominantly defects/inconsistencies
that the C11 single-doc pass did not cover (it focused on the 9 listed items) plus
cross-spec drift that only became visible after the C24–C33 wave established canonical
references (errors.md taxonomy, t3-v3 dimension names, C33 identifier decision).

---

## §B — NEW HIGH Findings

### H1: §2.4 `slash_atp` references undefined variable `witnesses`

**Line**: 198 (function defined at 168)
**Issue**: The same function the C11-H1 fix repaired still contains a second undefined
variable. Signature is `def slash_atp(caller, violator, amount, evidence):` — but step 5
calls:

```python
record_slashing_event(violator, slashed, evidence, witnesses)  # 'witnesses' undefined
```

`witnesses` is neither a parameter nor assigned anywhere in the body. (Contrast
`cross_society_transaction`, which explicitly constructs its witness list at lines
460–462.)

**Impact**: An implementer following this pseudocode hits a `NameError`. Same defect
class as the remediated C11-H1 `caller` bug, in the same function — the C11 fix added
`caller` to the signature but did not also resolve `witnesses`.
**Classification**: AUTONOMOUS.
**Remediation**: Add `witnesses` to the signature (e.g. `def slash_atp(caller, violator, amount, evidence, witnesses):`) or derive it from `evidence`/society context before the call.

---

## §C — NEW MEDIUM Findings

### M1: V3 tensor dimension named `value` instead of canonical `valuation`

**Lines**: 96 (`v3_delta={"value": +0.02}`), 147 (`"v3": {"value": +0.03}`), 338 (`{"v3.value": +0.05}`)
**Issue**: The canonical V3 dimensions are **Valuation / Veracity / Validity**
(`t3-v3-tensors.md`; `ontology/t3v3-ontology.ttl`; canonical equation). atp-adp uses the
correct `veracity` (line 194) and all three T3 dimension names correctly
(`training`/`talent`/`temperament` at 96, 194, 295, 339), but writes the first V3
dimension as `value` rather than `valuation` in all three tensor-delta examples.
**Impact**: Terminology drift from the canonical V3 root dimension; an implementer
copying these deltas would write to a non-existent `value` dimension. The internal
inconsistency (correct `veracity`, wrong `valuation`) makes this a clear drift rather
than an alternate vocabulary.
**Classification**: AUTONOMOUS (spec-text rename `value` → `valuation` in the three
examples). **Cross-check recommended**: scan the corpus for the same `v3.value`/`"value"`
drift before the remediation turn applies it (it may be a shared pattern).
**Remediation**: Replace `value` with `valuation` in the V3 deltas at lines 96, 147, 338.

### M2: Slashing authority is underspecified — generic predicate vs §6.1 monetary-authority power *(DESIGN-Q)*

**Lines**: 175–177 (`if not has_slashing_authority(caller): raise UnauthorizedSlashing()`) vs §6.1 (469–496, `monetary_authority.powers` includes `"slash_violations"`) and §6.1 constraint `max_slash_per_event: 10000` (487)
**Issue**: §2.4 gates slashing on a generic `has_slashing_authority(caller)` predicate,
while §6.1 enumerates `slash_violations` as a **monetary-authority** power with a
`max_slash_per_event` cap. The spec does not state whether slashing authority is
*exclusive* to the monetary authority, whether/how it can be **delegated**, or whether
the §6.1 `max_slash_per_event` cap binds the §2.4 `slash_atp` path (the pseudocode does
not reference it).
**Impact**: Two plausible authority models (monetary-authority-exclusive vs
delegable-capability) lead to different governance and security properties. This is an
architecture decision, not a wire fix.
**Classification**: **DESIGN-Q** — recorded, NOT self-resolved. Route to operator.
(Severity deflated from the finder's HIGH "contradiction": §2.4 and §6.1 are *compatible*
— the monetary authority is one holder of slashing authority — the gap is
*underspecification*, not contradiction.)
**Suggested operator question**: Is slashing authority exclusive to the monetary
authority, or a delegable capability? Does §6.1's `max_slash_per_event` bind the §2.4
path?

---

## §D — NEW LOW Findings

### L1: §3.2 `regulate_flow` — undefined `target_velocity` + `apply_demurrage` name/signature collision

**Lines**: 260 (`if metrics.velocity < target_velocity:`), 266 (`self.apply_demurrage(rate=self.law.demurrage_rate)`) vs 281 (`def apply_demurrage(entity_stakes):`)
**Issue**: Two illustrative-pseudocode inconsistencies in `regulate_flow`:
(a) `target_velocity` is referenced but never defined/sourced (clearly an external
config threshold, hence LOW);
(b) the method calls `self.apply_demurrage(rate=...)` (a `SocietyTokenPool` method taking
a `rate`), but the only `apply_demurrage` definition in the spec is the **free function**
`def apply_demurrage(entity_stakes):` in §3.3 (281) taking a stakes dict — same name, two
incompatible signatures in adjacent sections.
**Impact**: Reader/implementer confusion. (Severity deflated from the finder's HIGH
"TypeError": these are *separate* illustrative snippets across §3.2/§3.3, not one runnable
program — so it is a naming/signature *consistency* issue, not a guaranteed runtime crash.)
**Classification**: AUTONOMOUS.
**Remediation**: Either define `target_velocity` as a config/law field reference, and
disambiguate the two `apply_demurrage` forms (rename one, or make §3.3's a method).

### L2: §5.1 ↔ §5.3 exchange-rate direction/units ambiguity

**Lines**: 406 (`"initial_rate": 1000, // 1000 CITY = 1 NATION`) vs 441–448 (`rate = get_exchange_rate(source.currency, target.currency)` then `target_atp = amount * rate`)
**Issue**: §5.1 documents the rate as **1000 CITY = 1 NATION** (i.e. CITY-per-NATION),
while §5.3 computes `target_atp = amount * rate`. For a CITY→NATION conversion the
multiplication needs NATION-per-CITY (`0.001`); plugging §5.1's `1000` directly into
§5.3 inflates the result 1 000 000×. The spec never states which direction
`get_exchange_rate(source, target)` returns.
**Impact**: An implementer reconciling the two sections can pick the wrong direction.
**Classification**: AUTONOMOUS.
**Remediation**: State the return convention of `get_exchange_rate(source, target)`
(target-per-source units) and align §5.1's `initial_rate` label/example accordingly.

### L3: §2.3 / §2.4 tensor-delta notation is inconsistent across the document

**Lines**: 95–96 (`t3_delta={"training": +0.01}`, flat kwargs), 146–149 (`"v3": {"value": +0.03}`, nested), 338 (`{"v3.value": +0.05}`, dotted-string)
**Issue**: Three different notations for the same concept (a tensor delta) appear across
§2.2 / §2.3 / §4.2: flat keyword dict, nested `{"v3": {...}}`, and dotted `"v3.value"`.
**Impact**: Inconsistent illustrative convention; minor reader friction.
**Classification**: AUTONOMOUS.
**Remediation**: Pick one notation (the nested `{"t3"/"v3": {dim: delta}}` form is the
most explicit) and apply throughout.

### L4: §4.3 cross-reference "(cf. §6.3 on transfer fees)" points at the wrong section

**Line**: 380
**Issue**: The C11-M5 disclaimer fix reads "Societies SHOULD define attribution rates in
their economic laws (cf. §6.3 on transfer fees)." §6.3 covers **transfer fees**, not
fractal-value attribution. The `cf.` (compare) framing makes it a defensible *analogy*
(both are society-defined economic rates), but it misdirects a reader seeking attribution
guidance; no section actually prescribes attribution policy.
**Impact**: Minor reader misdirection (artifact of the C11-M5 remediation).
**Classification**: AUTONOMOUS.
**Remediation**: Point to §6.2 Economic Laws (the general home for society-defined rates)
or drop the parenthetical.

### L5: §2.4 slashing — destruction/conservation accounting not stated

**Lines**: 163 (heading "Slashing (ATP Destruction)"), 184–188 (`society_pool.slash(...)`); cf. SDK `check_conservation` (atp.py:310–323)
**Issue**: The heading declares slashing destroys ATP, but the spec never states that
slashed ATP is removed from `total_supply` (§3.1) and is **exempt** from the
transfer-conservation invariant (`initial == final + fees`, atp.py). §3.2
`SocietyTokenPool` also shows `mint_adp` but no `slash` method, so the pool-level effect
of slashing is undocumented.
**Impact**: An implementer cannot tell how slashing reconciles with supply accounting and
the conservation check. (Severity deflated from finder HIGH "breaks conservation": the
SDK conservation invariant is scoped to *transfers*, not slashing — so this is a
documentation gap, not a broken invariant.)
**Classification**: AUTONOMOUS.
**Remediation**: Add one sentence: slashed ATP is removed from `total_supply` (destruction)
and is outside the transfer-conservation invariant; optionally show a `slash` method on
`SocietyTokenPool`.

### L6: JSON event examples use `"type"` instead of JSON-LD `"@type"` *(C11-L2 carried)*

**Lines**: 43 (`"type": "TokenMinting"`), 123 (`"type": "R6Transaction"`)
**Issue**: Carried from C11-L2. The document-discriminator examples use bare `"type"` and
lack `@context`, while the SDK serializers (`ATPAccount.to_jsonld`, `TransferResult.to_jsonld`)
emit `"@type"` with `@context`. (The third `"type":` at line 309, `"energy_producer"`, is a
domain attribute of the producer object — a category field, not a document-type discriminator
— so it is correctly left as `"type"` and is out of scope for this finding.)
**Impact**: Minor convention divergence. *Note (refute-by-default)*: because these
examples have no `@context` at all, they read as plain illustrative JSON, not JSON-LD
documents — so `"@type"` is arguably inappropriate without also adding `@context`. The
defensible fix is a consistent choice, not a bare rename.
**Classification**: AUTONOMOUS.
**Remediation**: Either make them proper JSON-LD (`@context` + `@type`) consistent with
the SDK, or explicitly label them plain JSON event objects.

---

## §E — INFO Findings

### I1: §2.1 minting `poolAllocation` fields differ from §3.1 `allocations` fields

**Lines**: 54–58 (`poolAllocation`: `total`/`reserved`/`available`) vs 218–223 (`allocations`: `circulating`/`reserved`/`emergency`/`governance`)
The two pool-shape examples use disjoint field sets for the same concept (society pool
partitioning). Documentation-only data-shape inconsistency; reconcile the field
vocabulary across the two examples.

### I2: SDK docstring "three sub-pools" wording lags the spec two-state reconciliation *(SDK-track / C11-M6 residual)*

`atp.py` lines 49–52: *"ATP tokens exist in three sub-pools: available, locked, adp"*.
The spec §7.1 note (564–570) reconciled this conceptually (locked remains ATP; ADP is
separate tracking — matching the SDK's own line-54 invariant `total = available + locked`),
but the docstring's "three sub-pools" phrasing still reads against the two-state model.
**Classification**: CROSS-TRACK (SDK) — not edited in this audit-only turn. Suggest the
SDK docstring say "two states (ATP/ADP); ATP is sub-partitioned into available + locked".

### I3: Tensor-delta magnitudes are illustrative magic numbers

Throughout §2.2/§2.3/§2.4/§4.2, tensor deltas (`+0.01`, `+0.02`, `-0.05`, `-0.10`, …) are
illustrative with no cited basis in `t3-v3-tensors.md`. This is by-design illustration
(parallel to the §4.3 attribution disclaimer), recorded for completeness — no action
required unless a normative delta model is later introduced.

---

## §F — CROSS-TRACK (open C33 decision)

### X1: `lct:web4:` identifier scheme — part of the open C33 B-H1 corpus

**Lines**: 44+ occurrences (e.g. 46, 50, 52, 143–145, 211, 308, 311, 392–393, 474–475, 491)
atp-adp uses the `lct:web4:<class>:<id>` instance-identifier form consistently
(`society`/`entity`/`witness`/`authority`/`producer`/`auditor`). This is the **same form**
the **open C33 finding B-H1** is consolidating corpus-wide (635 occurrences; two forms;
undefined canonical grammar). Per the C33 audit, the canonical LCT-instance identifier
form is an **operator decision** (A-H1/B-H1/C-H1/D-M1 already routed). This audit records
atp-adp as part of that corpus and **does not** propose a resolution or a new design-Q —
it carries to the existing C33 B-H1 decision. When the operator settles B-H1, atp-adp's
identifiers normalize alongside the rest of the corpus.

---

## §G — Refuted / Deflated (anti-overcall record)

Documented to honor the C7/C9/C10/C11 cross-doc overcall discipline (`feedback_audit_workflow_adversarial_verify`).

**Refuted outright (2)**:
- *Demurrage/decay apply differently to slashed vs discharged ATP* — REFUTED. Demurrage
  acts on held `entity_stakes`; slashed ATP is removed from holdings, so the two
  mechanisms do not interact as claimed.
- *V3 Valuation range inconsistent with `charge_rate` definition* — REFUTED. The policy
  `charge_rate`, the metrics `charge_rate` (§3.1), and V3 `valuation` are already
  semantically distinct primitives; no gap exists.

**Severity-deflated under refute-by-default (key ones)**:
- *ATP/ADP exception names not in error taxonomy* — finder HIGH → **demoted to a non-finding/INFO**.
  The §2.2/§2.3/§3.2 pseudocode exceptions (`UnauthorizedProducer`, `InvalidValueProof`,
  `UnauthorizedSlashing`, `InsufficientEvidence`, `UnauthorizedMinting`) are **illustrative
  pseudocode**, not wire errors; `errors.md` is the *wire* `W4_ERR_*` registry and does not
  claim to enumerate pseudocode exception names. Reported only as an optional doc-completeness
  note (the spec MAY add a mapping table from illustrative conditions to `W4_ERR_*` codes);
  not carried as an actionable finding. **This was the single largest overcall deflation.**
- *Slashing-authority "contradiction"* — HIGH → **M2 (MEDIUM, DESIGN-Q)** (underspecification, not contradiction).
- *`apply_demurrage` "TypeError"* — HIGH → **part of L1 (LOW)** (separate snippets, not one program).
- *Same-society no-op in `cross_society_transaction`* — MEDIUM → folded as a minor note under
  spec-pseudocode style; not separately carried (the section is explicitly cross-society only).
- *Slashing-destination "breaks conservation"* / *discharge-vs-slash ADP destination* — HIGH → **L5 (LOW)**
  (transfer-conservation invariant is not slashing's scope; the §2.4 heading resolves the discharge/destroy question).
- *Exchange-rate state-transition ambiguity* — captured precisely as **L2** (rate direction/units).

---

## §H — Methodology Note

This audit was produced by a deterministic multi-agent workflow: 5 finder agents
(delta-persistence, internal-consistency, SDK-alignment, cross-spec-drift,
primitive-clustered blindspot) fanned out, then **every** raw finding was independently
re-verified by an adversarial agent prompted to **refute by default**. 19 raw → 9
confirmed / 8 downgraded / 2 refuted at the workflow layer; the auditor then applied a
further judgment pass (severity deflation, DESIGN-Q vs AUTONOMOUS classification, C33
cross-track routing, consolidation of overlapping blindspot findings) to produce the 12
actionable findings above. The delta finder returned zero findings (all 9 C11 items
HELD), independently corroborated by the auditor's own re-read of the live spec.

---

*Audit complete. Recommended next step: a remediation turn applying the 9 AUTONOMOUS
findings (H1, M1, L1–L6, I1) and the I3/L6 hygiene items; M2 (DESIGN-Q) and X1
(C33 cross-track) await the operator. I2 is SDK-track.*
