# `multi-device-lct-binding.md` — Third Delta Re-Audit (C120)

**Audited file**: `web4-standard/core-spec/multi-device-lct-binding.md` (1126 lines, current `main`)
**Audit date**: 2026-06-30
**Audit series**: C-series, C120 (third delta re-audit). Chain: **C19** (first-pass internal-consistency, 2026-05-28, #246) → **C36** (first delta, 2026-06-07, #281) → **C80** (second delta, 2026-06-21, #371) → **C81** (remediation, 2026-06-21, #372) → **C120** (this).
**Instrument**: proportioned single-auditor **refute-by-default** + **git-snapshot verification**. The target is BYTE-FROZEN since C81 (HEAD blob `b979ea7d` == C81 blob `b979ea7d`), so §A is a persistence-verification + the **C56 claim-vs-canonical re-read** (verify the *claim*, not just that the *edit* landed) against the live SDK + vectors; §B is the corpus-delta / inbound-carry surface (snapshot-presence guard) PLUS the cross-section internal-blindspot sweep PLUS the **C116-N1/C118-N1 MUST-vs-reference-impl enumeration**. NOT the C80 3-finder fan-out — that is over-instrumentation for a frozen target with a bounded sibling delta (the C108/C112/C114/C116/C118 proportioning precedent).

**Authority sources** (canonical precedence: SDK + shipped test vectors > spec text):
- **SDK** — `web4-standard/implementation/sdk/web4/binding.py`
- **Test vectors** — `web4-standard/test-vectors/binding/binding-vectors.json`
- **Sibling specs** (corpus-delta diff target) — `t3-v3-tensors.md` (C83), `atp-adp-cycle.md` (C79/C119), `errors.md`, `LCT-linked-context-token.md`, `SOCIETY_SPECIFICATION.md`, `web4-society-authority-law.md`
- **Ontology** — `web4-standard/ontology/t3v3-ontology.ttl`

**Result**:
- **§A** — All **7/7** C81 autonomous fixes HELD by byte-identity, and the C56 claim-vs-canonical re-read confirms each still matches the live SDK + vectors (0 regression). The **8 deferred carries** (N1, N2, C36-N9, C36-N11, C19-M3, C19-M4, C19-M5, C19-M7) re-verified **ALL STILL-OPEN** against the *current* (post-C83/C119) corpus; **none resolved, none hardened, none sharpened** since C81 — siblings churned but none touched multi-device's carry surface.
- **§B** — **0 net-new confirmed findings.** 5 candidates raised and REFUTED (documented in §C), including the full C116-N1/C118-N1 **MUST-vs-reference-impl sweep**: multi-device does **NOT** exhibit the defect class. Every normative requirement is backed by its implementing section.

---

## Executive Summary

Three headline conclusions.

1. **Clean persistence — the C81 remediation holds entirely.** The file has not changed a byte since C81 (#372, 2026-06-21). Per the C108 lesson (*frozen ≠ unverified*), §A re-reads each of the 7 applied fixes' **claims** against the live SDK/vectors rather than just confirming the edit is present. All 7 still match canonical authority: the §3.2/§3.6 `cross_witness` call sites are 3-arg; the §3.3 `record_cross_witness` reference matches the SDK 4-param signature; the §3.4 device-trust formula (`anchor_weight × witness_freshness × attestation_freshness`) byte-mirrors SDK `compute_device_trust`; `cross_witnesses` is a bare-string list at every site matching `DeviceRecord.cross_witnesses: List[str]` + the `constellation_trust_multi_device` vector; the `device_trust` orphan block is gone; the §2.4 `recovery_revoked` scope note matches the §3.6 recovery path; the §5.2 quorum wording fix is present at both sites.

2. **No carry moved.** At C80, two deferred carries had *moved* (C36-N9 hardened — SOCIETY_SPEC began deferring birth-certs to SAL; C19-M5 sharpened — coupled the §B-N1 wire example). At C120 there is **no further movement**: the snapshot-presence guard against the post-C83/C119 siblings confirms `t3v3-ontology.ttl` still declares only 3 T3 roots (the 8 multi-device flat dims remain absent — C19-M5/N1/N2 open); `atp-adp-cycle.md` still has **no** device/enroll/constellation cost counterpart (C19-M7 open); `errors.md` still has only `W4_ERR_WITNESS_QUORUM` and no `HARDWARE_ANCHOR`/`NoHardwareAnchorError` code (C19-M3 open); LCT-core / SOCIETY_SPEC unchanged for their carries. The t3-v3 C83 reword and atp-adp C119 remediation did not touch any field multi-device's carries depend on.

3. **The MUST-vs-reference-impl signal does NOT recur here — and that is the informative result.** C116-N1 (mcp §12) and C118-N1 (atp-adp §7.1) were the *same* defect: an unconditional summary-level "X MUST…" requirement narrower in the section that actually implements X. C120 enumerated **every** normative keyword in multi-device (only 7 lines — a thin normative surface) and checked each against its implementing section. **All are backed**: §2.2.4 software-anchor MUSTs → §3.4 ceiling (0.40) + §3.6 hardware-requirement guard (`NoHardwareAnchorError`); §4.2 "MUST use anchor-composition-derived ceiling" → §3.4 `constellation_trust_ceiling`; §2.4 "revoked keys MUST NOT authorize" → §3.5/§3.6 status guards; §4.4 "MUST NOT cite as canonical" → self-contained. The only cross-spec MUST (§7.2 "Societies MUST…") is the **existing** C36-N9 carry, not net-new. **multi-device is the third file checked for this defect class and does not add a fourth instance.** This is direct evidence the defect is **not corpus-wide-universal** but specific to docs carrying a *normative-summary* section (mcp §12, atp-adp §7.1) that restate entity-level requirements unconditionally; multi-device's §7 is a thin integration pointer, not a normative summary. → argues for clearing C116-N1 (the pending C117 remediation) **file-by-file**, NOT presuming a corpus-wide MUST sweep.

**Refute-by-default earned its keep again — against the auditor's own candidates.** Five §B candidates were raised and all five refuted on the live SDK/vectors (§C). The most tempting (an apparent §4.3 `witness_freshness` orphan, mirroring the C80-N4 `device_trust` orphan) collapsed the moment §3.4 L572 was read: it *is* wired in (`w_fresh = witness_freshness(days_since_last_witness(device))`). Verifying the *claim* (is the function called / does the formula match the canonical inputs?) beats pattern-matching the *shape*.

---

## §A — Delta Status of C81 / C80 / C36 / C19 Findings

### A.1 — C81-remediated findings (7/7 HELD; 0 regression) — byte-frozen + C56 claim re-read

The file is byte-identical to its C81 state, so each edit trivially persists. Per C108 the value-add is re-reading the *claim* against canonical authority that may itself have moved:

| C80 | Topic | Status | C56 claim re-verification (live SDK/vectors, 2026-06-30) |
|-----|-------|--------|----------------------------------------------------------|
| **§A flagship** | §3.2 `cross_witness` 3-arg | **HELD** | §3.2 L484 `cross_witness(root_lct.device_constellation, existing_device, new_device)` — 3 args; matches §3.3 L494 `def cross_witness(constellation, device_a, device_b)` + §3.6 L839 caller. No 2-arg call site remains (grep). |
| **N3** | `cross_device_witnesses`→`cross_witnesses` (4 sites) + bare-string reshape | **HELD** | `cross_device_witnesses` grep = 0. `cross_witnesses` present §2.3 note / §2.4 example+note / §3.3 / §3.4 / §7.1. §3.4 L699 iterates `for w_id in d.cross_witnesses` over strings. Matches SDK `DeviceRecord.cross_witnesses: List[str]` (binding.py:184) + the `constellation_trust_multi_device` vector (`["dev1","dev2"]`). |
| **N4** | `device_trust` orphan block removed | **HELD** | No `device_trust` JSON block in §2.4; only the local `device_trust`/`device_trusts` variables in `compute_constellation_trust` (correct). SDK `DeviceRecord` has no such field. |
| **N5** | "constellation entry → resolved device record" note | **HELD** | §2.3 L234 note present; documents that the algorithms read `cross_witnesses` + optional `latest_attestation` off the resolved record. Both reads exist in §3.4 (L578-579, L699) and have a declared home. |
| **N6** | §2.4 `recovery_revoked` scope note | **HELD** | §2.4 L290 note matches §3.6 L835 (`revocation_reason = "recovery_revoked"` set only by recovery). SDK `remove_device` guard remains 4-value (`lost`/`sold`/`compromised`/`upgrade`) — correct by construction, no SDK change (the C81 decision-note arm). |
| **N7** | §3.5 loop over `authorizing_active` | **HELD** | §3.5 L746 `for device in authorizing_active:` (quorum-filtered), consistent with the L726/L728 quorum check (C36-N8). |
| **N8** | §5.2 "true majority" → "at least half" + even-n note | **HELD** | §5.2 L983-984 "at least half the devices: ceil(device_count/2). (For even n this is exactly n/2…)"; L994 comment `# ceil(n/2): at least half`. Vectors n=5→3, n=6→3, n=10→5 recompute under `(device_count+1)//2`. |

**Remediation quality at one generation's remove: 7/7 clean, 0 regression.** Unlike C80 (which caught the §3.2 call-site miss that C36-N6's remediation introduced), C120 finds no remediation-introduced regression — the C81 four-site `cross_witnesses` sweep (its own flagship lesson, honored) grepped to zero and stayed there.

### A.2 — Deferred carries (8/8 STILL-OPEN; 0 moved) — snapshot-presence-guarded against the post-C83/C119 corpus

| Carry | Topic | Status (re-verified 2026-06-30) | Snapshot-guard evidence |
|-------|-------|----------|----------|
| **N1** | §2.3/§4.1 `t3_tensor` flat 8-dim vs canonical 3-root | **STILL-OPEN** | §2.3 L218-230 + §4.1 L851-858 unchanged (flat 8 dims). `t3v3-ontology.ttl` still declares only 3 roots + commented sub-dim examples; none of the 8 dims declared. `t3-v3-tensors.md` (post-C83) unchanged on the 3-root mandate (L135). **Design-Q (couples C19-M5).** |
| **N2** | §2.3 `t3_tensor` no entity-role binding | **STILL-OPEN** | §2.3 attaches `t3_tensor` to the root LCT object with no role qualifier; `t3-v3-tensors.md:14` role-context invariant unchanged post-C83. **Design-Q (same site as N1).** |
| **C36-N9** | §7.2 Society MUSTs unimplemented + birth-cert wrong owner | **STILL-OPEN** | `SOCIETY_SPECIFICATION.md` still carries zero device/constellation content; Birth Certificates still a SAL record class (`web4-society-authority-law.md §3.4`). §3.1 L369 + §7.2 + §8 still cite SOCIETY_SPEC (canonical owner = SAL). **Operator/cross-track (couples carry-C23-H1).** |
| **C36-N11** | entity-segmented LCT IDs (`lct:web4:root:`, `…:device:phone:`) | **STILL-OPEN** | §2.3/§2.4 unchanged; LCT-core generator still emits `lct:web4:<mb32>` with no entity segment. **Design-Q (carry-C33 B-H1).** |
| **C19-M3** | 3 exception classes absent from `errors.md` | **STILL-OPEN** | `errors.md` still has only `W4_ERR_WITNESS_QUORUM` (L66); no `HARDWARE_ANCHOR` code. §3.5/§3.6 raise bare `InsufficientQuorumError`/`InsufficientRecoveryQuorum` (reuse path → `W4_ERR_WITNESS_QUORUM` 409, intact) + `NoHardwareAnchorError` (the **true gap**). **Deferred (carry-C30).** |
| **C19-M4** | LCT-core does not acknowledge the §7.1 extension | **STILL-OPEN** | `LCT-linked-context-token.md` still carries zero `device_constellation`/`cross_witnesses`/`root_attestation` content. **Cross-spec (LCT-recip).** |
| **C19-M5** | 8 T3 sub-dims absent from `t3v3-ontology.ttl` | **STILL-OPEN** | Ontology unchanged (3 roots + open `subDimensionOf`; none of the 8 declared). **Cross-corpus design-Q (couples N1).** |
| **C19-M7** | §7.3 ATP costs not aligned with `atp-adp-cycle.md` | **STILL-OPEN** | `atp-adp-cycle.md` post-C79/C119 still has **no** device/enroll/constellation cost counterpart (grep = 0). §7.3 costs (enroll 10 / witness 1 / removal 5 / recovery 20) remain free-floating. **Cross-spec design-Q.** |

**No carry resolved, hardened, or sharpened since C81.** This is a *quieter* corpus-delta than C80 (which saw C36-N9 harden + C19-M5 sharpen). The named siblings that changed since 2026-06-21 — t3-v3 (C83 reword), atp-adp (C119 §7.1 MUST-scope remediation), security (C109), handshake (C113) — touched fields unrelated to multi-device's carry surface. Snapshot-presence guard ([[feedback_snapshot_presence_guard]]) confirms each carry's blocking condition is byte-present and unmoved in the current sibling, not merely "still listed."

---

## §B — New Confirmed Findings (0)

No net-new confirmed findings. The cross-section internal-blindspot sweep and the C116-N1/C118-N1 MUST-vs-reference-impl enumeration both came up empty — every candidate refuted on the live SDK/vectors (§C).

This is the 10th frozen-target wrap to yield ≤1 net-new (C92/94/96/98/100/102/104/106/C110 = 0; C108 = 1; C114 = 1; C116 = 1; C118 = 2; **C120 = 0**), and the **negative result on the MUST sweep is itself the finding** (see §D).

---

## §C — Refuted Candidates (5, documented for honesty — refute-by-default)

| # | Candidate | Severity if real | Why refuted |
|---|-----------|------------------|-------------|
| **R1** | §4.3 `witness_freshness`/`days_since_last_witness` is an orphan function — defined but never called (mirroring the C80-N4 `device_trust` orphan) | MED | §3.4 L572 calls it directly: `w_fresh = witness_freshness(days_since_last_witness(device))`, applied as `device_trust = anchor_weight * w_fresh * a_fresh` (L580). Wired in, not orphaned. The §4.3 docstring claim "applied to per-device trust in §3.4" is accurate. |
| **R2** | §3.4 applies `witness_freshness` but the SDK `compute_device_trust` omits it → spec/SDK divergence | HIGH (wire) | SDK `compute_device_trust` (binding.py:445-472) is `base * w_fresh * a_fresh` with `w_fresh = witness_freshness(days_since_witness)` (L466). Witness-freshness IS canonical in the SDK; spec matches. (Structural note: the SDK threads `days_since_witness` as an external param/dict defaulting to 0 while the spec computes it from `device.last_witnessed` via `utc_now()` — same value, INFO at most, not a defect.) |
| **R3** | §2.2.4 L155 / §5.1 L970 hardware-requirement-for-recovery is asserted but never enforced (a MUST-vs-impl gap) | MED | §3.6 `recover_identity` step 2 (L795-801) enforces it: `hardware_devices = [d for d in recovery_devices if d.anchor_type != "software"]; if len(hardware_devices) == 0: raise NoHardwareAnchorError`. The constraint is implemented. |
| **R4** | §3.3 L533 references `record_cross_witness` "in the SDK" with a 4-arg call — phantom/arity-mismatched reference | HIGH (wire) | SDK `record_cross_witness(constellation, device_a_id, device_b_id, timestamp)` exists at binding.py:534 with exactly 4 params and is idempotent (matches the spec comment L532). Reference is accurate. |
| **R5** | §2.2.4 L153 "Software anchors MUST be marked in T3 tensor" — narrower/unbacked summary MUST (C116-N1/C118-N1 class) | LOW | The "marking" is realized via the `hardware_binding_strength` T3 dimension (§4.1: "<0.40 for software-only, capped") + `anchor_type:"software"` at the anchor level, which §3.4 excludes from hardware-diversity counting. Plausibly satisfied; vague but folds into the *existing* N1 (whole T3 structure is the deprecated flat schema), not net-new. |

---

## §D — Cross-audit signals

- **The MUST-vs-reference-impl defect class is NOT corpus-wide.** This audit ran the full C116-N1/C118-N1 enumeration on a third file and found **zero** instances. The class recurs only in docs with a *normative-summary* section (mcp §12 "Conformance", atp-adp §7.1 "Requirements") that restates entity-level MUSTs unconditionally; multi-device's §7 is a thin integration pointer with no such summary, and its inline MUSTs (§2.2.4/§2.4/§4.2/§4.4) sit adjacent to their implementing code. **Implication for C117 (pending mcp C116-N1 remediation):** clear N1s **file-by-file** as the rotation reaches each normative-summary doc, rather than batching a speculative corpus-wide MUST sweep — the surface is narrower than two consecutive hits suggested. (Directly answers the C120 policy-reviewer's non-blocking note.)
- **Frozen ≠ unverified, 6th confirmation (C108/C112/C114/C116/C118/C120).** A byte-frozen target still warranted the C56 claim-re-read (the §3.4 formula, the `record_cross_witness` arity, the SDK guard all had to be re-checked against the *current* SDK, not the C81-era one) — but this time everything held and §B was empty, the honest outcome of a thoroughly-audited (C80 3-finder) doc that has since stood still while its siblings churned away from its carry surface.
- **Carry stillness is a state, not an absence of work.** C80 found carry *movement* (N9 hardened, M5 sharpened); C120 found carry *stillness*. The snapshot-presence guard is what distinguishes "still open and unmoved" (this audit) from "still listed but silently resolved downstream" (the C106 failure mode) — both require reading the *current* sibling byte, not trusting the carry ledger's last note.
- **Refute-by-default, applied to the auditor's own hypotheses.** 5/5 §B candidates refuted. The orphan-function pattern (R1) is the cautionary one: it looked exactly like the C80-N4 `device_trust` orphan the prior audit confirmed, but the analogy was false — the function is called. Pattern-resemblance to a prior *confirmed* finding is not evidence; the call-site read is.

---

## Implementation-track flag (per BC#6 — flag type only, no prescribed diffs)

| Finding | Type | Track |
|---------|------|-------|
| §A (7 C81 fixes) | persistence-verified, HELD | **None** (no action) |
| §B | 0 net-new | **None** (no remediation turn warranted for C120 — the audit→remediation alternation's next remediation slot remains the pending **C117** mcp C116-N1) |
| N1, N2 | T3 structural conformance + role-binding (cross-spec; couples C19-M5) | **Design-Q** (coordinate t3-v3 + ontology) |
| C36-N9 | Society reciprocity + birth-cert authority (SAL) | **Operator/cross-track** (couples carry-C23-H1) |
| C36-N11 | entity-segmented LCT IDs | **Design-Q** (carry-C33 B-H1) |
| C19-M3 | error taxonomy (`NoHardwareAnchorError` true gap) | **Deferred** (carry-C30) |
| C19-M4 | LCT-core reciprocity | **Deferred** (LCT-recip) |
| C19-M5 | ontology sub-dimensions (couples N1) | **Deferred / Design-Q** |
| C19-M7 | ATP cost reciprocity | **Deferred** (cross-spec) |

All §B carries are pre-existing and operator-gated/cross-track; **none gate any normal turn**, and C120 produced **no autonomous remediation candidate**. The multi-device autonomous remainder closed at C81 and remains closed.

---

## Authority Summary

- **SDK** (`binding.py`) — canonical for formula/shape/name/arity (§A: `cross_witness`, `record_cross_witness`, `compute_device_trust`, `remove_device` guard).
- **Test vectors** (`binding-vectors.json`) — co-equal canonical for the `cross_witnesses` wire shape + the quorum/trust values.
- **`t3-v3-tensors.md` + `t3v3-ontology.ttl`** — canonical for T3 structure (N1/N2/C19-M5).
- **`web4-society-authority-law.md §3.4`** — canonical for `Web4BirthCertificate` (C36-N9).
- **`errors.md`** — canonical for W4_ERR codes (C19-M3).

---

*"A frozen spec is not a finished one — but when its siblings drift away from its seams instead of into them, the honest audit is a short one."*
