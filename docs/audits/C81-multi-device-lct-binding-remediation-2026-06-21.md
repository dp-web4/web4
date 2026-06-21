# `multi-device-lct-binding.md` — C80 Remediation (C81)

**Remediated file**: `web4-standard/core-spec/multi-device-lct-binding.md`
**Date**: 2026-06-21
**Series**: C-series, C81 (remediation). Chain: **C19** (first-pass) → #246 → **C36** (first delta) → #281 → **C80** (second delta, PR #371) → **C81** (this).
**Source audit**: `docs/audits/C80-multi-device-lct-binding-delta-audit-2026-06-21.md` ("Implementation-track flag" table).
**Scope**: apply ONLY C80's **Autonomous**-routed findings. Design-Q / operator / deferred items are explicitly held (see "Not applied" below).
**Authority aligned to** (canonical precedence: SDK + shipped vectors > spec text): `implementation/sdk/web4/binding.py`, `test-vectors/binding/binding-vectors.json`.

---

## Findings applied (7)

| C80 | Sev | Site(s) | Change |
|-----|-----|---------|--------|
| **§A flagship** | HIGH | §3.2 enrollment, L490 | `cross_witness(existing_device, new_device)` → `cross_witness(root_lct.device_constellation, existing_device, new_device)`. #281 changed `cross_witness` from 2→3 params and swept §3.6 (L840) but missed this call site → a spec-faithful enrollment `TypeError`s. Now matches the §3.3 signature + §3.6 caller. |
| **N3** | MED | §2.4 example, §3.3 comment, §3.4 algo, §7.1 summary | Renamed `cross_device_witnesses` → `cross_witnesses` at **all 4 sites** and reshaped the §2.4 example from object entries (keyed `device_lct_id` + `last_witness`/`witness_count`) to a **bare device-LCT-ID string list**. §3.4 `compute_cross_witness_density` now iterates `for w_id in d.cross_witnesses` over strings. Matches SDK `DeviceRecord.cross_witnesses: List[str]` (binding.py:184) and the shipped `constellation_trust_multi_device` vector (`["dev1","dev2"]`). Before: spec-faithful `compute_cross_witness_density` evaluated `"dev1"["device_lct_id"]` → crash on the canonical vector. |
| **N4** | MED | §2.4 example, §3.4 comment | Removed the orphaned `device_trust` block (`anchor_strength`/`attestation_freshness`/`cross_witness_score`) — read by no algorithm, no SDK counterpart. Updated the §3.4 comment that pointed at it (now: "not also contained in a separate pre-aggregated trust block"). |
| **N5** | MED | §2.3 / §2.4 boundary | Added a **"Constellation entry → resolved device record"** note: the §2.3 entries are the membership index; the trust algorithms operate over the resolved record (entry joined with the §2.4 Device LCT) = the single flat SDK `DeviceRecord` shape, which additionally exposes `cross_witnesses` (bare strings) + optional `latest_attestation`. Documents the projection so the §3.4 reads (`cross_witnesses`, `latest_attestation`) have a declared home. Root cause of N3/N4 — applied together. |
| **N6** | LOW | §2.4 lifecycle bullet | Scope-note: the 4 user-initiated reasons (`lost`/`sold`/`compromised`/`upgrade`) are set via §3.5 and are the only values the SDK `remove_device` guard accepts; `recovery_revoked` is **set only by the §3.6 recovery path**, never a `remove_device` reason — so the §3.5/SDK 4-value guard is correct by construction. **SDK left unchanged** (see decision note). |
| **N7** | LOW | §3.5 L747 | Signature-collection loop iterates `authorizing_active` (the quorum-filtered set) instead of raw `authorizing_devices`, consistent with the quorum check the same function enforces (C36-N8 fix). Added a one-line rationale comment. |
| **N8** | LOW | §5.2 docstring + comment | "true majority: ceil(device_count/2)" → "at least half the devices: ceil(device_count/2)" with an explicit even-n note (n=6→3 is exactly half, not strict majority); comment `# ceil(n/2) = majority` → `# ceil(n/2): at least half`. Numbers were already correct (vectors n=5→3, n=6→3, n=10→5 unchanged); only the word was imprecise. |

**N3 four-site sweep (the flagship's own lesson, honored):** `cross_device_witnesses` grep → **0** post-edit; `cross_witnesses` present at §2.3 note, §2.4 example + note, §3.3 comment, §3.4 algo, §7.1 summary. An incomplete rename here would have reproduced exactly the incomplete-sweep regression that *was* C80's flagship.

## Decision note — N6 (spec-note only, SDK guard unchanged)

C80 flagged N6 as "Autonomous (spec note) + SDK-track (add `recovery_revoked` to `valid_reasons`)" with the resolution offering an explicit **"or"**: loosen the SDK guard, **or** scope `recovery_revoked` in §2.4 so the 4-value guard is correct by construction. I took the **scope-note arm only** and deliberately left the SDK guard at 4 values, because `recovery_revoked` is a **recovery side-effect** (§3.6 sets `device.revocation_reason` directly), not a user-initiated removal reason — loosening `remove_device`'s guard would mis-model it (it would let a caller "remove" a device citing a reason that only the recovery path may set). The conservative arm preserves the guard's tightness. The policy reviewer confirmed this is within the auditor's explicit either-or, not under-delivery. Result: **no SDK change**; the 95 `test_binding*.py` tests stay green and remain the canonical authority the spec now matches.

## Not applied (held — out of C81 scope)

| C80 | Type | Why held |
|-----|------|----------|
| **N1** (T3 flat 8-dim vs canonical 3-root) | Design-Q / cross-spec | Requires coordinated t3-v3 + ontology edits (closes deferred C19-M5); not unilaterally applicable to multi-device alone. |
| **N2** (T3 no entity-role binding) | Design-Q / cross-spec | Same edit site as N1; couples the role-context invariant in `t3-v3-tensors.md`. |
| **C36-N9** (Society reciprocity; birth-cert authority now SAL) | Operator / cross-track | Couples carry-C23-H1; canonical owner is `web4-society-authority-law.md §3.4`. |
| **C36-N11** (entity-segmented LCT IDs) | Design-Q | Feeds carry-C33 B-H1 (`lct:web4:` surface form). |
| **C19-M3** (3 exception classes vs `errors.md`) | Deferred | `NoHardwareAnchorError` is the true gap; quorum reuse path (`W4_ERR_WITNESS_QUORUM`) intact. Fold into carry-C30. |
| **C19-M4** (LCT-core does not acknowledge §7.1 extension) | Deferred | Cross-spec LCT-reciprocity. |
| **C19-M5** (8 T3 sub-dims absent from ontology) | Deferred / Design-Q | Couples N1 — resolve together. |
| **C19-M7** (§7.3 ATP costs vs `atp-adp-cycle.md`) | Deferred | Cross-spec design-Q; no atp-adp counterpart exists. |

These remain in the standing carry ledger for an operator / cross-track turn. With C81, the **autonomous** remainder of the multi-device C19→C36→C80 chain is closed; only the cross-spec/design-Q/operator carries persist.

## Verification

- `cross_device_witnesses` grep = 0; `cross_witnesses` at all intended sites; `device_trust` block gone (only the local `device_trust`/`device_trusts` variables remain in `compute_constellation_trust`, correct); §3.2 call now 3-arg; §3.5 loop iterates `authorizing_active`; §5.2 wording fixed at both sites.
- `binding.py` parses; `tests/test_binding.py` + `tests/test_binding_attestation.py` → **95 passed**. SDK + vectors unchanged (the spec was aligned to them, not vice-versa).

---

*"An arity change is a rename of the call contract — sweep every call site. A field rename is the same — sweep every site, then grep to zero."*
