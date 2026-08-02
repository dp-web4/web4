# `multi-device-lct-binding.md` — Sixth Delta Re-Audit (C308)

**Audited file**: `web4-standard/core-spec/multi-device-lct-binding.md` (1126 lines, current `main`)
**Audit date**: 2026-08-01
**Audit series**: C-series, C308 (sixth delta re-audit). Chain: **C19** (first-pass, 2026-05-28, #246) → **C36** (first delta, 2026-06-07, #281) → **C80** / **C81** (second delta + remediation, 2026-06-21, #371/#372) → **C120** (third delta, 2026-06-30, #421) → **C152** (fourth delta, 2026-07-07, #478) → **C268** (fifth delta, 2026-07-24, #576) → **C308** (this).
**Authorization basis**: `docs/SPRINT.md` Sprint 54 records the C-series as *"not formally defined in advance. Work was proposed and policy-reviewed per session under v2 protocol."* Proposed and policy-reviewed before execution per that precedent (v2 protocol Steps 3–5; **APPROVED with seven binding conditions**, all honored — see §E).
**Instrument**: proportioned single-auditor **refute-by-default**, with in-line adversarial refutation of the flagship (six independent refutation attempts, §B.1.4). Subagent use restricted to the protocol-mandated policy review, matching the C268 instrument. Every count published below states its matcher, its scope, and the commit it was taken at, and was **re-run after the finding text was written**.

**Window**: `0e375556..HEAD` (`0e375556` = C268's own merge commit, 2026-07-24T14:57-0700 → HEAD `69a5f471`, 2026-08-01T16:09-0700) = **71 commits** (`git rev-list --count 0e375556..HEAD`). Stated as a commit range, not a date bound, per policy condition 6 — the reviewer's date-bounded probe returned 70 and the two must not be conflated.

**Result**:
- **§A** — target **byte-frozen since C81** (`a6cbde92`, blob `b979ea7d`); `binding.py`, `binding-vectors.json`, and `ratchet.rs` all **0 commits** in the window ⇒ **quadruple-frozen**. **11/11 carries re-adjudicated at live HEAD, all STILL-OPEN, 0 closed**, one with its *basis* changed (C19-M5's anchor file moved; the carry now stands on a live measurement, no longer on byte-identity).
- **§B** — **2 confirmed net-new findings** (`C308-N1`, `C308-N2`, both **MEDIUM**, both **routed — NOT auditor-applicable**), 3 refuted candidates, 2 INFO. Both findings live in a **mirror layer this lineage has never read in seven passes**.
- **§B′** — the mirror set was **under-derived by ~18 artifacts**. This is the pass's method result.
- **0 spec mutation, 0 SDK mutation, 0 code mutation, 0 hub mutation. 1 new file (this document).**

---

## Executive Summary

1. **The headline is not a new defect in the spec — it is that this spec has a second ceiling authority, and seven passes never looked at it.** `multi-device-lct-binding.md` §4.2 (`:871-887`) publishes a **normative** trust-ceiling table indexed by anchor composition, closing with a MUST: *"Implementations MUST use the anchor-composition-derived ceiling (**not a universal `1.0` cap**) when clamping the final constellation trust."* Elsewhere in the same repository, the **AttestationEnvelope** primitive publishes a **different** trust-ceiling table indexed by anchor type, whose top row is **`tpm2` + PCR → 1.0**. Four of five comparable cells disagree. The one that agrees is `software → 0.4`.

2. **The two tables are not merely adjacent — the spec composes with the envelope by name, and the SDK ships the bridge.** multi-device `:234` states the resolved device record carries *"an optional `latest_attestation` (an `AttestationEnvelope`)"*; §3.4 `:575-579` reads `device.latest_attestation.freshness_factor`. And `binding.py:126-136` — a file every one of the seven passes read — ships `ANCHOR_TYPE_TO_ATTESTATION` / `ATTESTATION_TO_ANCHOR_TYPE`, an explicit bidirectional map between binding's `AnchorType` and the attestation anchor-type strings, sitting **20 lines below** `CONSTELLATION_TRUST_CEILING` (`:106-114`). The bridge between the two vocabularies was in the tracked mirror the whole time; the two ceiling tables on either side of it were never compared.

3. **`C308-N1` (flagship, MEDIUM): the standard holds two answers for the maximum trust of one device.** For a single-TPM2 constellation, §4.2 `:877` says **0.75**; `attestation.py:63` / `envelope.py:21` / `docs/specs/attestation-envelope.md:87` say **1.0** — the exact value §4.2's MUST names as the thing not to use, and above §4.2's global maximum of `0.98` (`:881`). The standard's own **published conformance vector** asserts it: `test-vectors/attestation/attestation-vectors.json:57` `"trust_ceiling": 1.0`. This is not a prose slip in a draft — it is a machine-checkable expectation inside `web4-standard/`.

4. **`C308-N2` (MEDIUM): the Rust core's default hardware-binding ceiling is 0.85 on an LCT it labels *software*, and a live daemon persists it.** `web4-core/src/lct.rs:85-93` — `impl Default for HardwareBinding` — sets `level: 4` with description *"Software-bound keys (development)"* and `trust_ceiling: 0.85`. multi-device `:154` caps software-only at **0.4** — a clause C268 explicitly re-ratified as correct (*"the defect is the exclusion, not the scoring"*). `hub/hub-lib/src/hub.rs:168` constructs real hub LCTs with `HardwareBinding::default()`, so the running daemon's LCT records carry a software ceiling **2.1×** the spec's cap.

5. **Direction is derivable here, and it points away from the spec — which is why both findings route rather than get applied.** The §4.2 table and its no-universal-`1.0`-cap MUST are the **product of this lineage's own audited remediation**: C19's M2 established *"the cap is the anchor-composition-derived ceiling … NOT 1.0 (universal cap)"* (2026-05-28), and `d4f926ad` (#281, 2026-06-07) landed the MUST. The AttestationEnvelope ceilings predate that correction (`61836cad`, 2026-03-18) and were never revisited. The spec side is the *corrected* side; the envelope side carries the pre-correction shape. But **which artifact should move is an author call, not an auditor call** — see the R5/R6 fork in §B.1.4, where the two live outcomes are "align the envelope table" versus "the envelope's `constellation_trust` block is mislabelled," and they have different owners.

6. **This is C268's mechanism inverted, and the pairing is the lesson.** C268 found a frozen file made defective by a *new* principle landing above it. C308 finds a frozen file already flanked by an *old*, never-read sibling implementation below it. In both cases the target was byte-frozen and the finding was real; in neither case did re-reading the target produce it. **A byte-frozen target is a statement about one file, never about its subject matter.**

7. **Nothing in the 71-commit window touches this file's subject matter, and that is recorded so C348 need not re-derive it.** `web4-standard/core-spec/` has **0 changed files** in the window (`git diff --name-only 0e375556..HEAD -- web4-standard/core-spec/` → 0). The window's substantive motion is 20 files in `hub/hub-lib` (the `AssuranceReceipt` wave), 19 audit docs, and one ontology fix. Each was adjudicated for-or-against this file's surface in §B.3 — and every one of them is **disjoint or already routed by a sibling lineage**.

---

## §A — Delta Status of Prior Findings

### A.1 — C81 fixes (7/7 HELD, by quadruple byte-identity)

| Surface | Blob / last commit | Commits in window |
|---|---|---|
| `web4-standard/core-spec/multi-device-lct-binding.md` | `b979ea7d`, `a6cbde92` (2026-06-21) | **0** |
| `web4-standard/implementation/sdk/web4/binding.py` | `857f8040` | **0** |
| `web4-standard/test-vectors/binding/binding-vectors.json` | `dc969641` | **0** |
| `web4-core/src/ratchet.rs` | `7b048a78` (2026-07-16) | **0** |

All four byte-identical to their C268 state ⇒ the 7 C81 remediations (3-arg `cross_witness`, 4-param `record_cross_witness`, `compute_device_trust` formula mirror, bare-string `cross_witnesses`, orphan-block removal, `recovery_revoked` scope note, `ceil(n/2)` quorum wording) **HELD with no re-derivation possible or needed.** Third consecutive frozen wrap; first **quadruple**-frozen one.

### A.2 — Carries (11/11 re-adjudicated at live HEAD; 11 STILL-OPEN, 0 closed)

No carry is passed through on a C268-era status. Each row states the probe re-run at HEAD `69a5f471`.

| Carry | Probe re-run at HEAD | Live-HEAD adjudication (2026-08-01) |
|-------|----------------------|--------------------------------------|
| **N1** (flat 8-dim `t3_tensor`, §2.3/§4.1) | `git log --oneline 0e375556..HEAD -- web4-standard/core-spec/t3-v3-tensors.md` → **0**; `sed -n '137p'` = *"T3 dimensions are **root nodes in an open-ended RDF sub-graph**…"* | **STILL-OPEN. Anchor `:137` verified verbatim** — the C268 re-anchoring (`:135`→`:137`) is confirmed stable, no further shift. DESIGN-Q (attach-strategy = t3-v3-side D2, per C121) — **idle, no self-decision.** |
| **N2** (no entity-role binding) | `sed -n '14p' t3-v3-tensors.md` = *"**T3/V3 tensors are not absolute properties - they exist only within role contexts.**…"* | **STILL-OPEN, ANCHOR VERIFIED VERBATIM.** Same DESIGN-Q site as N1. |
| **C36-N9** (Society MUSTs / birth-cert owner) | `git log --oneline 0e375556..HEAD -- SOCIETY_SPECIFICATION.md web4-society-authority-law.md` → **0** | **STILL-OPEN, HELD by byte-identity.** Owner ledger unmoved. Operator/cross-track. |
| **C36-N11** (entity-segmented LCT IDs) | `git log --oneline 0e375556..HEAD -- LCT-linked-context-token.md` → **0** | **STILL-OPEN, HELD by byte-identity.** DESIGN-Q (carry-C33 B-H1). |
| **C19-M3** (3 exception classes absent from `errors.md`) | `grep -cE "InsufficientRecoveryQuorum\|NoHardwareAnchorError\|DeviceLimitExceeded\|insufficient_recovery_quorum\|no_hardware_anchor\|device_limit_exceeded" errors.md` → **0** (both casings, per v11's rider); `errors.md` window commits → **0** | **STILL-OPEN.** Remains coupled to C268-N1: `NoHardwareAnchorError` is both an undocumented class here and the construct C268-N1 convicts. **Adjudicate jointly.** |
| **C19-M4** (LCT-core doesn't acknowledge §7.1 extension) | `grep -n -i "multi-device\|multi_device" LCT-linked-context-token.md` → **1 hit, `:41`** (inside §1.2's illustrative clause) | **STILL-OPEN, UNCHANGED.** LCT-core's only reference to this spec is still the §1.2 example, not an acknowledgment of the §7.1 protocol extension. Cross-spec (LCT-recip). |
| **C19-M5** (8 sub-dims absent from ontology) | ⚠️ **BASIS CHANGED.** `t3v3-ontology.ttl` **moved** (`01f410db`, #581) — C268 held this carry *by byte-identity*, and that basis is now void. Re-measured live: `grep -cE "hardware_binding_strength\|constellation_coherence\|hardwareBindingStrength\|constellationCoherence"` → **0** | **STILL-OPEN on a live measurement, not on a freeze.** `01f410db` added `web4:Tensor` (superclass) + `web4:observationCount`; it added **no** sub-dimensions. Recorded because "held by byte-identity" would have been a **false** status this pass — the exact [[feedback_anchor_not_paragraph]] failure mode. |
| **C19-M7** (§7.3 ATP costs free-floating) | `git log --oneline 0e375556..HEAD -- atp-adp-cycle.md` → **0** | **STILL-OPEN, HELD.** Independently re-confirmed by C306 (this file's previous rotation neighbour, 2026-08-01). |
| **B-10 arm** (`cose:ES256`→`cose:EdDSA` at `:257`/`:270`) | `grep -n "cose:ES256"` → **`:257`, `:270`** verbatim; `git log --oneline 0e375556..HEAD -- security-framework.md protocols/` → **0** | **STILL-OPEN — STATUS-CHECK ONLY** (policy condition 3). Owner ledger unmoved ⇒ no adjudication has occurred. C152's sharpening (the prescription overreaches on this hardware-P-256 spec) stands unconsumed. Not re-litigated. |
| **C152-1** (B-10 arm overreach + §2.4 genesis-signer gap) | owner ledger 0 commits | **STILL-OPEN, unconsumed.** Status-check only. |
| **C152-2** (`hub/docs/PAIRED-CHANNELS.md` §8 item 6) | `grep -n "multi-device is later" hub/docs/PAIRED-CHANNELS.md` → **`:425`** verbatim | **STILL-OPEN.** Item 6 unchanged despite the window's 20-file `hub/hub-lib` wave (`PAIRED-CHANNELS.md` itself is not in the window diff). Routed to the hub track at C152 — **status-checked, not re-opened, not fixed.** |

### A.3 — C268's own finding

| C268 finding | Live-HEAD status |
|---|---|
| **C268-N1** (§2.2.4 `:155` + §3.6 `:795-801` render a protocol verdict of exclusion, contra LCT §1.2 cl.1) | **STILL-OPEN, unconsumed, and re-corroborated.** `:155` and the `raise NoHardwareAnchorError` block are byte-identical (target frozen). Two window movers strengthen it without changing it: (i) `01f410db` added `web4:observationCount` to the ontology with the rationale *"a relying party weighs a score by its evidence, not just its value"* — §1.2 discipline landing in **another** layer while the spec stays behind; (ii) proposal #580 `resilience-to-incomplete-information.md` (2026-07-25, **status: "proposal, for fleet review" — NOT ratified**) is the same principle at parent scope. Per policy condition 7 (ratified normative text only), both are **status notes on C268-N1, not net-new.** Routing unchanged: **author + operator DESIGN-Q, adjudicate jointly with C19-M3.** |

---

## §B — Findings

### B.1 — C308-N1 · The standard publishes two contradicting trust-ceiling authorities for the same device (MEDIUM · **route: author + operator DESIGN-Q** · NOT auditor-applicable)

#### B.1.1 — The two tables, side by side

`multi-device-lct-binding.md` §4.2 `:871-887` (**normative**, closing MUST at `:886-887`):

| Configuration | Max Trust |
|---|---|
| Single software key | **0.40** |
| Single phone SE | **0.75** |
| Single TPM2 | **0.75** |
| Single FIDO2 | **0.80** |
| Phone + FIDO2 | 0.90 |
| Phone + FIDO2 + TPM | 0.95 |
| 3+ diverse hardware anchors | **0.98** ← global maximum |

> `:886-887` — *"Implementations MUST use the anchor-composition-derived ceiling (not a universal `1.0` cap) when clamping the final constellation trust."*

AttestationEnvelope, published in **four** places (`docs/specs/attestation-envelope.md:87-91`; `web4-standard/implementation/sdk/web4/attestation.py:62-68`; `web4-core/python/web4_core/trust/attestation/envelope.py:20-26`; asserted by `web4-standard/test-vectors/attestation/attestation-vectors.json:57`):

| Anchor | Trust Ceiling |
|---|---|
| `tpm2` + PCR | **1.0** |
| `tpm2` (no PCR) | 0.85 |
| `fido2` | **0.9** |
| `secure_enclave` | **0.85** |
| `software` | **0.4** |

**Cell-by-cell, mapped through `binding.py:129-134`'s own `ANCHOR_TYPE_TO_ATTESTATION`:**

| Anchor | §4.2 (single-device row) | AttestationEnvelope | Δ |
|---|---|---|---|
| software | 0.40 | 0.40 | **agree** |
| `PHONE_SECURE_ELEMENT` ↔ `secure_enclave` | 0.75 | 0.85 | +0.10 |
| `FIDO2` ↔ `fido2` | 0.80 | 0.90 | +0.10 |
| `TPM2` ↔ `tpm2` | 0.75 | **1.0** | **+0.25** |
| best achievable | 0.98 | **1.0** | +0.02, and equal to the forbidden universal cap |

The single agreeing cell is itself evidence: if these were unrelated quantities, agreement on `software → 0.4` would be coincidence.

#### B.1.2 — Why this is one quantity, not two

The strongest defence is *"per-anchor device assurance and per-constellation identity trust are different quantities that may legitimately differ."* The envelope spec closes that door itself, at `docs/specs/attestation-envelope.md:174-178`:

```python
# Device constellation trust
constellation_trust = geometric_mean([
    device.envelope.trust_ceiling
    for device in constellation.active_devices
])
```

That computes a variable **named `constellation_trust`** by aggregating the per-anchor ceilings. For a one-device constellation it returns that device's anchor ceiling — precisely the quantity §4.2's table indexes and §3.4 `:599-600` clamps (`ceiling = constellation_trust_ceiling(...)`; `min(ceiling, raw_trust)`). Two specifications, one variable name, one input, two answers. For three TPM2 devices it returns `geometric_mean([1.0,1.0,1.0]) = 1.0` — above §4.2's declared global maximum and exactly the universal cap §4.2's MUST forbids.

#### B.1.3 — Consumption, and why this is MEDIUM rather than HIGH

Bounded by the consumption mechanism (method carry v13):

- **No single executable path computes both.** `binding.py:395-415` `constellation_trust_ceiling()` reads only `CONSTELLATION_TRUST_CEILING` (`:106-114`); §3.4/`compute_device_trust` touch the envelope only for `freshness_factor`. `grep -rn "TRUST_CEILINGS" web4-standard/implementation/sdk/web4/binding.py` → **0**.
- **But it is published as conformance evidence.** `test-vectors/attestation/attestation-vectors.json:57` ships `"trust_ceiling": 1.0` as an *expected* value inside `web4-standard/`, and `docs/specs/attestation-envelope.md:159` instructs consumers to gate on it (`if result.trust_ceiling < required_ceiling:`). A third-party verifier built to the published vectors admits a single-TPM2 identity at ceiling 1.0 that the constellation spec caps at 0.75.
- **The schema does not constrain it.** `schemas/attestation-envelope-jsonld.schema.json:165-169` — `trust_ceiling`, `"maximum": 1` — permits 1.0 and requires the field.

⇒ **MEDIUM: latent in code, live in the published artifact layer.** It becomes **HIGH** the moment any consumer composes the two — e.g. if `compute_device_trust` ever reads `latest_attestation.trust_ceiling`, or if a relying party gates a recovery/high-stakes act on the envelope value. That composition is one line away and the bridge already exists.

#### B.1.4 — Adversarial refutation (six attempts, refute-by-default)

| # | Attempt | Outcome |
|---|---|---|
| **R1** | *"Different quantities — per-anchor device assurance vs constellation identity trust."* | **REFUTED** by `attestation-envelope.md:174-178`, which aggregates per-anchor ceilings into a variable literally named `constellation_trust`. See §B.1.2. |
| **R2** | *"`docs/specs/` is a v0.1 draft, not the standard — no standard-internal conflict."* | **REFUTED as an existence defence; survives only as a venue note.** Three of the four disagreeing artifacts are inside `web4-standard/`: `implementation/sdk/web4/attestation.py:62-68`, `test-vectors/attestation/attestation-vectors.json:57`, `schemas/attestation-envelope-jsonld.schema.json:165-169`. `web4-standard/core-spec/inter-society-protocol.md` cites the primitive (C290 `:152` calls it *"the spec's only citation of a non-prose artifact"*). The prose lives in `docs/specs/`; the conflict does not. |
| **R3** | *"Nothing executes both, so there is no defect."* | **NOT REFUTED — adopted as the severity bound.** This is why N1 is MEDIUM and not HIGH (§B.1.3). It is not a reason for the standard to hold two answers. |
| **R4** | *"Granularity mismatch — §4.2's `Single TPM2` should be compared to `tpm2 (no PCR)` = 0.85, not 1.0."* | **REFUTED, and it widens the gap.** §2.2.3 `:117-121` specifies multi-device's TPM2 as PCR-bound (*"Bind to PCR values for device state"*), so the correct comparand is `tpm2` + PCR = **1.0**, Δ = 0.25 not 0.10. |
| **R5** | *"A constellation of one is riskier than its device — a lower constellation cap than device cap is intentional and monotone."* | **REFUTED as a reconciliation.** No monotone reading survives: §4.2's global maximum over *all* compositions is 0.98 (`:881`), while the envelope's aggregate reaches 1.0 for any all-TPM2 set. The envelope's best case exceeds the spec's best case. |
| **R6** | *"Already filed by this or a sibling lineage."* | **REFUTED by measurement.** `grep -l -iE "TRUST_CEILINGS\|attestation-envelope\|universal 1"` over **all seven** prior multi-device lineage docs (C19 first-pass, C36, C80, C81 remediation, C120, C152, C268) → **0 files match**. `docs/audits/` cites `attestation-envelope` in **6** docs excluding this one (`grep -rln … \| grep -v C308`), all inter-society-protocol lineage + C290 + C306, none charging the ceiling conflict; C290 `:169` reached the envelope doc and evaluated only its *example substrate*. **Never filed.** |

#### B.1.5 — Direction, and the fork the author must resolve

Provenance (all via `git log -S`):

| Artifact | Landed | Audited by this lineage? |
|---|---|---|
| §4.2 table (base) | `8d9ad13b`, 2026-01-13 | yes |
| AttestationEnvelope ceilings | `61836cad`, 2026-03-18 | **no** |
| SDK `TRUST_CEILINGS` | `d9f4ba36`, 2026-03-19 (#44) | **no** |
| §4.2 *"not a universal `1.0` cap"* MUST | `7a8e3d3f` 2026-05-29 (#246) → `d4f926ad` 2026-06-07 (#281) | yes — it **is** this lineage's remediation |

C19's own first-pass audit (2026-05-28, `:274`) established the position the MUST encodes: *"Test vector explicitly states the cap is 0.75 … NOT 1.0 (universal cap)."* The spec side is the audited, corrected side; the envelope side carries the pre-correction shape and was never revisited. **But the remedy forks, and the two branches have different owners:**

- **(a)** If the two tables measure the same thing, the envelope ceilings should be reconciled to §4.2 — owner: AttestationEnvelope / hardware-binding track, and it touches a published schema, four artifacts, and a conformance vector.
- **(b)** If they measure different things, then `attestation-envelope.md:174-178` mislabels a per-anchor aggregate as `constellation_trust` and silently overrides a normative MUST — owner: the envelope doc's author, and the fix is local.

Either way there is a defect; only its location changes. **Choosing between (a) and (b) is a normative call about what `trust_ceiling` means, which is exactly why this routes and is not applied.** Adjudicate alongside **C19-M5** (both concern how hardware assurance enters T3) and the **C302** routing of `core/lct_binding/` to the AttestationEnvelope / hardware-binding track — that track now has a second inbound.

---

### B.2 — C308-N2 · `web4-core`'s default hardware-binding ceiling is 0.85 on an LCT it labels *software*; a live daemon persists it (MEDIUM · **route: web4-core / hub track** · NOT auditor-applicable)

**Statement.** `web4-core/src/lct.rs:85-93`:

```rust
impl Default for HardwareBinding {
    fn default() -> Self {
        // Default to software binding (level 4)
        Self {
            level: 4,
            description: "Software-bound keys (development)".into(),
            trust_ceiling: 0.85,
        }
    }
}
```

The struct's own doc comment (`:72-76`) defines `level` as *"4: Software (encrypted keys) / 5: Hardware (TPM/SE)"*. So this default is, by its own labelling, a **software** binding carrying `trust_ceiling: 0.85`.

multi-device `:154` — **"Maximum trust ceiling for software-only: 0.4"** — and §4.2 `:875` — `Single software key | 0.40`. The default is **2.1×** the spec's cap. Note this clause is not in dispute: C268 explicitly re-ratified `:153`/`:154` as §1.2-conformant (*"A computed ceiling **is** the evidence. The defect is the **exclusion**, not the **scoring**"*), so the spec side here is settled.

**Consumption.**
- `web4-core/src/coherence.rs:299` — `let effective_threshold = threshold.max(1.0 - lct.trust_ceiling());` — executable, and inverts the ceiling into an admission floor. At 0.85 the floor is **0.15**; at the spec's 0.40 it would be **0.60**. `check_coherence` returns `Err(Web4Error::CoherenceBelowThreshold)`, i.e. it is a gate.
- `hub/hub-lib/src/hub.rs:168` — `hardware_binding: HardwareBinding::default()` — the running hub constructs real LCTs with this value, so it is persisted in a shipped product's records.
- `grep -rn "check_coherence" --include='*.rs' .` (excluding `target/`) → definition + 2 in-crate tests; **no non-test caller in this repo**. `grep -rn "trust_ceiling" hub/ --include='*.rs'` (excluding `target/`) → **0** — the hub writes the field and never reads it.

⇒ **MEDIUM**, on the same v13 rule as N1: the wrong value is *stored* by a live daemon and *readable through a public API* (`web4_core::check_coherence` is re-exported at `lib.rs:87`), but no shipped caller currently computes with it.

**Never previously charged.** Prior lineage docs do contain the string `hardware_binding` — every occurrence is `hardware_binding_strength`, the §4.1 **T3 dimension**, a different construct. `grep -n -B2 -A4 "hardware_binding\|0\.85"` over the five narrative lineage docs returns no reference to `HardwareBinding`, to `lct.rs`, or to the 0.85 default (C81, the remediation record, likewise: `grep -ciE "TRUST_CEILINGS\|attestation-envelope\|universal 1\|HardwareBinding"` → **0**). The substring collision is precisely why it was invisible: a token that *looks* covered.

**Direction.** Unambiguous — the spec clause is ratified and re-ratified; the Rust default is the outlier. **Still routed, not applied**: `web4-core` is another track's crate, and the fix is a judgement about whether the default should be `0.4` (spec-conformant software), or the struct should stop defaulting to a ceiling at all (evidence-shaped, per LCT §1.2 — a default ceiling is a prescribed trust value in a struct literal). The second option is the more interesting one and is the author's to take.

---

### B.3 — Window adjudication (71 commits; 0 touch this file's subject matter)

`git diff --name-only 0e375556..HEAD -- web4-standard/core-spec/` → **0 files**. The whole core-spec layer is frozen across this window.

| Window mover | Verdict vs this file |
|---|---|
| **`AssuranceReceipt` wave** — `d5bd10b2` (#591), `8b0b133d` (#592), `694584e6` (#598), `33f9b03a` (#601), `bec588c9` (#594), `e1f440bf` (#626); `hub/hub-lib/src/constellation.rs` + `hub/tools/verify_assurance_receipt.py` + golden vectors | **DISJOINT — reach-escalation on an already-refuted item, NOT net-new.** C152 `:64` ruled the hub's `AssuranceLevel` tier (`single_device`/`multi_device`/`hardware_backed`) a *"different concept (co-sign count tier vs device-LCT set), no conflict, no protected term redefined."* The wave makes the tier portable and third-party-verifiable, which widens its reach, and per [[feedback_carry_gains_reach_not_truth]] reach never converts a refutation into a finding. It is **already routed twice** by sibling lineages in this window: **C286-N3** (second assurance primitive beneath SAL §4) and **C288-N2** (`lct_id` shape on the portable surface). **Do not re-open.** |
| `01f410db` (#581) `web4-standard/ontology/t3v3-ontology.ttl` | **Carry-relevant, not net-new.** Voids C19-M5's byte-identity basis (§A.2) and adds `web4:observationCount` as a §1.2-shaped corroboration of C268-N1 (§A.3). Adds no sub-dimension. |
| `954ee391` (#580) `proposals/resilience-to-incomplete-information.md` | **NOT ratified** (header: *"Status: proposal, for fleet review"*). Subject-matter grep `-icE "device\|constellation\|hardware\|anchor\|revocation\|quorum"` → **1 hit** (`:77`, "no quorum" in an adjudication-escalation clause). Status note on C268-N1 only. |
| `4665a430` (#579) `proposals/dictionary-as-context-mandatory-role.md` | Same grep → **0 hits.** Disjoint. |
| `#521` (`767eb564`) / `#522` (`87377c38`) W4IP Effector role + decision verbs | **PRE-WINDOW — condition 7's premise corrected.** Both landed **2026-07-14**, ten days *before* the C268 snapshot (2026-07-24), and were adjudicated at C268 §B.3. Not window movers. Recorded per condition 7 rather than silently dropped. |
| `hub/docs/` wave (PRD, V2-V3-ARCHITECTURE, HESTIA-MODE, TROUBLESHOOTING) + `docs/PRD_ACTION_EVIDENCE.md` | **Disjoint.** Subject-matter diff grep over `hub/docs/ hub/README.md docs/PRD_ACTION_EVIDENCE.md whitepaper/sections/` → 5 hits, all hub-ignition/anchoring vocabulary (`A3` OS-isolated / `A4` hardware-attested tiers, ledger head anchoring), none touching device-LCT constellations. `hub/docs/PAIRED-CHANNELS.md` (the C152-2 anchor) is **not in the window diff**. |
| 19 audit docs, whitepaper build artifacts, `web4-trust-core/README.md`, Cargo.lock ×2, `.github/workflows/ci.yml` | Disjoint by construction. |

### B.4 — Refuted candidates (3)

| # | Candidate | Verdict |
|---|---|---|
| **C.1** | *"`AssuranceLevel` is standard vocabulary the standard never defines"* — LCT §1.2 `:33` names *"a constellation's device assurance"* and `:50` *"assurance levels are recomputed from structure"* as normative terms, yet `grep -ic "assurance" multi-device-lct-binding.md` = **0** and `grep -rn "AssuranceLevel"` (excluding `target/`) = 37 `constellation.rs` + 3 `rest.rs` + 2 `ratchet.rs` + 0 in `web4-standard/`. | **REFUTED — resurrection of a C152 ruling.** C152 `:64` already adjudicated exactly this vocabulary overlap as *"different concept … no protected term redefined."* #531 changed the *premise* (making "assurance" normative) but not the ruling's basis (the two constructs remain a co-sign-count tier and a device-LCT set). Filing it would be the [[feedback_refute_your_best_finding]] failure. **Do not resurrect.** |
| **C.2** | *"`docs/specs/attestation-envelope.md:172` `t3.talent = min(t3.talent, envelope.trust_ceiling)` conflicts with §4.1's `hardware_binding_strength` dimension."* | **REFUTED as separate — folds into carry N1.** Both are statements about how hardware assurance enters T3, which is the open flat-vs-3-root DESIGN-Q. Filing it separately would double-count a carry. Recorded as an adjacency on N1, not a finding. |
| **C.3** | *"`web4-core/python/web4_core/trust/attestation/` duplicates `web4-standard/implementation/sdk/web4/attestation.py` — two copies of one table."* | **REFUTED as a defect; recorded as INFO-2.** Diffed at HEAD: the `TRUST_CEILINGS` tables are value-identical (sole textual difference is the `Dict[str, float]` annotation). Two agreeing copies are a drift *risk*, not a divergence. Per [[feedback_does_the_impl_agree_with_itself]] the check was run before the finding was written, and it came back clean — which is what makes N1 a spec-vs-envelope disagreement rather than an impl-vs-itself one. |

### B′ — Genuine-mirror gate: **GENUINE, and the mirror set was UNDER-DERIVED BY ~18 ARTIFACTS**

Explicit diff against C268's list (policy condition 5), including the negative direction:

| C268's mirror set | Status at C308 |
|---|---|
| `implementation/sdk/web4/binding.py` | **retained**, frozen |
| `test-vectors/binding/binding-vectors.json` | **retained**, frozen |
| `web4-core/src/ratchet.rs` | **retained**, frozen |
| *(false mirrors: `sd_jwt_vc.rs`, `oid4vc.rs`, `role_extension.rs`, `vault/document.rs`)* | **re-verified FALSE**, unchanged |

**Nothing dropped** (v8's contraction direction checked and negative). **Added at C308 — the AttestationEnvelope surface, derived by asking what else *specifies or implements* hardware anchoring, not what cites this file:**

| Newly-derived mirror | Why it is in the set | Read by this lineage before? |
|---|---|---|
| `docs/specs/attestation-envelope.md` (222L) | cited by the target at `:234`, `:575`; defines a competing ceiling table + a `constellation_trust` formula | **no** (0/7 passes) |
| `web4-standard/implementation/sdk/web4/attestation.py` | ships `TRUST_CEILINGS`; imported by `binding.py:33` | **no** |
| `web4-standard/test-vectors/attestation/attestation-vectors.json` | asserts `trust_ceiling` per anchor as conformance expectation | **no** |
| `web4-standard/schemas/attestation-envelope-jsonld.schema.json` + `schemas/contexts/attestation-envelope.jsonld` | make `trust_ceiling` a required, `maximum: 1` field | **no** |
| `web4-core/python/web4_core/trust/attestation/**` (11 files, incl. `anchors/{tpm2,fido2,secure_enclave,software}.py`) | a per-anchor-type implementation of §2.2.1–§2.2.4, one module per subsection | **no** — `grep -rln "web4-core/python"` over `docs/audits/` → 5 docs, **none in this lineage** |
| `web4-core/src/lct.rs` (`HardwareBinding`) + `web4-core/src/coherence.rs` | a third ceiling authority, executable | **no** (the string `hardware_binding` in prior docs is always `hardware_binding_strength`) |

**Why seven passes missed it.** The mirror set was derived by asking *"what cites `multi-device-lct-binding.md`?"* and *"what implements `binding.py`'s functions?"* The AttestationEnvelope surface answers neither: it is cited *by* the target rather than citing it, and it lives under `attestation`, not `binding`. The bridge (`binding.py:126-136`) was read seven times and never followed. → **method carry v14**, §D.

### B.5 — INFO (2, not net-new, not routed as findings)

- **INFO-1.** `web4-standard/` has **no binding conformance suite**. `ls testing/conformance/` → `atp-operations.json`, `presence-protocol-conformance.json`, `r6-r7-actions.json`, `society-roles.json`, `tensor-operations.json`, `README.md`, `VECTOR-FRESHNESS.md` — 5 suites, none for device binding; the binding surface's only artifact is `test-vectors/binding/binding-vectors.json`. Recorded as a coverage observation for the operator's conformance ledger, **not** charged against this spec (C276's precedent: conformance-execution burden sits with the implementer, not this repo's CI).
- **INFO-2.** The duplicate attestation module (§B.4 C.3) — two published packages carrying one ceiling table, currently in agreement. If N1 is resolved by editing the table, **both copies plus the vector plus the schema must move together**; a partial fix converts N1 into an impl-vs-itself divergence.
- **Explicitly NOT re-opened per policy condition 1:** C306-N2 (`web4-standard/deployment/README.md:33-34,83-84` installing files deleted 2026-05-12). Re-confirmed present at HEAD; it is a sibling lineage's open operator-routed finding from one fire ago. **Status-check only.**

---

## §C — Instrument

Every count below states its matcher, its scope, and the commit; every zero names its token **and its casing**. All were re-run at HEAD `69a5f471` **after** §B was written.

| # | Matcher | Scope | Result |
|---|---|---|---|
| 1 | `git rev-list --count 0e375556..HEAD` | repo | **71** |
| 2 | `git log --oneline 0e375556..HEAD -- <target>` | target | **0** (also for `binding.py`, `binding-vectors.json`, `ratchet.rs`) |
| 3 | `git diff --name-only 0e375556..HEAD -- web4-standard/core-spec/` | core-spec | **0 files** |
| 4 | `grep -ic "assurance"` | `multi-device-lct-binding.md` | **0** |
| 5 | `grep -rn "AssuranceLevel"` (`--include=*.rs,*.py,*.md,*.json,*.ttl`, excl. `*/target/*`) | repo | 37 `constellation.rs` · 3 `rest.rs` · 2 `ratchet.rs` · 2 C268 doc · **0 in `web4-standard/`** |
| 6 | `grep -cE "InsufficientRecoveryQuorum\|NoHardwareAnchorError\|DeviceLimitExceeded\|insufficient_recovery_quorum\|no_hardware_anchor\|device_limit_exceeded"` (CamelCase **and** snake_case) | `errors.md` | **0** |
| 7 | `grep -cE "hardware_binding_strength\|constellation_coherence\|hardwareBindingStrength\|constellationCoherence"` (snake **and** camel) | `t3v3-ontology.ttl` | **0** |
| 8 | `grep -l -iE "TRUST_CEILINGS\|attestation-envelope\|universal 1"` | all **7** prior lineage docs (C19, C36, C80, C81, C120, C152, C268) | **0 files match** |
| 9 | `grep -rln "attestation-envelope" docs/audits/ \| grep -v C308` | `docs/audits/`, **excluding this document** | **6** (ISP ×4, C290, C306) — none charging the ceilings. *Raw count is 7 once this document lands; the exclusion is stated because the re-run after writing changed the cell.* |
| 10 | `grep -rln "web4-core/python\|web4_core/trust/attestation" docs/audits/ \| grep -v C308` | `docs/audits/`, **excluding this document** | **5** — none in this lineage. *Same self-inclusion correction as row 9.* |
| 11 | `grep -rn "TRUST_CEILINGS"` | `binding.py` | **0** (the two tables never meet in code) |
| 12 | `grep -rn "trust_ceiling" hub/ --include='*.rs'` (excl. `target/`) | hub | **0** (written at `hub.rs:168`, never read) |
| 13 | `grep -n "cose:ES256"` | target | `:257`, `:270` |
| 14 | `grep -n "multi-device is later"` | `hub/docs/PAIRED-CHANNELS.md` | `:425` |
| 15 | `grep -n -i "multi-device\|multi_device"` | `LCT-linked-context-token.md` | **1** (`:41`) |
| 16 | `git log -S "not a universal" -- <target>` | target | `7a8e3d3f` (2026-05-29) → `d4f926ad` (2026-06-07) |
| 17 | `git log --format=... -- docs/specs/attestation-envelope.md` | that file | **1 commit**, `61836cad` 2026-03-18 |

**Instrument note (v10's corollary, run both ways).** N1 rests on four disagreeing cells of the same shape, which is also the signature of a broken verifier. Checked: the values were read as **literal constants** from four separate files (`:87-91`, `:62-68`, `:20-26`, `:875-881`), not computed by any script of mine; the fifth cell **agrees**, which a systematically-broken comparison would not produce. Verifier cleared.

---

## §D — Method carries

**v14 (NEW, born C308) — derive the mirror set in BOTH citation directions, and follow the bridge.**
Seven passes derived this file's mirrors by asking *what cites the target* and *what implements the target's functions*. Both questions are outbound. The defect lived in an artifact the **target itself cites** (`:234`, `:575`) — inbound — and under a different noun (`attestation`, not `binding`), so no name-based sweep reached it. Three concrete rules:
1. **Grep the target for the proper nouns it names** (`AttestationEnvelope`, `NoHardwareAnchorError`, …) and add every artifact that defines one to the mirror set. A spec's own citations are a mirror-set input, not just a lean-on check.
2. **When the tracked mirror contains a translation table between two vocabularies** (`binding.py:126-136`), the *other* vocabulary's home is in the mirror set by construction. A bridge in a file you read every pass is an unfollowed edge.
3. **A substring hit is not coverage.** `hardware_binding` matched `hardware_binding_strength` in five prior docs and made a distinct construct look already-read. Where a token is a prefix of another token, state which one you measured.

Standing carries re-affirmed this pass: **v13** (frozen target ⇒ widen the surface) is what produced both findings — with the correction that for *this* file the productive widening was the **artifact/sibling-implementation** tree, not the operational tree the reviewer measured at 5 files. **v12** (re-derive direction) produced §B.1.5's provenance fork. **v11**'s casing rider produced counts 6 and 7. **v8** (mirror sets contract) was checked and came back negative — the set only grew.

---

## §E — Policy conditions (7/7 honored)

| # | Condition | Where honored |
|---|---|---|
| 1 | Do not re-open C306-N2 as net-new | §B.5, status-check + citation only |
| 2 | Zero net-new is acceptable; do not pad around the widening | Not exercised — but the padding pressure was real and refused three times: §B.4 C.1/C.2/C.3 are the candidates that would have inflated this pass |
| 3 | Routing only; no mutation | 0 files changed outside this document; N1, N2, and all 11 carries routed |
| 4 | Exactly 1 repo file | this document |
| 5 | Publish the mirror-set re-derivation as an explicit diff, both directions | §B′ |
| 6 | Bound the window by commit range | header + §C row 1 |
| 7 | Bound the principle sweep to ratified text; check #521/#522 explicitly | §B.3 — both pre-window (2026-07-14), verdict recorded; #580 recorded as unratified |

---

## §F — Routing summary

| Item | Severity | Owner | Action |
|---|---|---|---|
| **C308-N1** — two ceiling authorities for one device | MEDIUM | author + operator (AttestationEnvelope / hardware-binding track) | DESIGN-Q: resolve the (a)/(b) fork in §B.1.5. Adjudicate with **C19-M5** and the **C302** `core/lct_binding/` routing. **Do NOT self-apply** |
| **C308-N2** — `HardwareBinding::default().trust_ceiling = 0.85` on a software binding | MEDIUM | web4-core / hub track | Set to 0.4, or remove the defaulted ceiling entirely (the §1.2-shaped option). **Do NOT self-apply** |
| **C268-N1** | MEDIUM | author + operator | Unconsumed, re-corroborated. Adjudicate jointly with **C19-M3** |
| 11 carries | — | as previously routed | All STILL-OPEN; C19-M5's basis changed (§A.2) |
| INFO-1 (no binding conformance suite), INFO-2 (duplicate attestation module) | INFO | operator conformance ledger | Observation only |

**Next multi-device delta: C348** (C308 + 40). Re-baseline from blob `b979ea7d`; the mirror set to re-derive from is **§B′'s expanded table, not C268's three-entry list**; check first whether the N1 fork was resolved and in which direction, and whether `HardwareBinding::default()` still carries 0.85.
