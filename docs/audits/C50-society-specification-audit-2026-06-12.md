# C50 — Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-06-12
**Auditor**: Legion autonomous web4 track (slot 000047, v2 protocol; THIRD execution attempt — slots 060047 and 120047 died at session limits with zero artifacts)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (446 lines, head `c76d6e70`)
**Prior audit**: C22 (`docs/audits/C22-society-specification-audit-2026-05-30.md`, PR #251)
**Prior remediation**: PR #252 (`252e77bd`, 2026-05-30) — 8 autonomous-actionable findings applied (H1, H2, H3, M1, M2, L1, L2, I1); 2 design-Q deferred (M6, I2); 5 cross-track deferred (M3, M4, M5, I3, I4)
**Staleness at audit**: 13 days since #252; no commits have touched the target or sister specs since (`git log 252e77bd..c76d6e70 -- <target>` empty beyond #252 itself)
**Method**: §A LEAD-direct re-verification of all 8 applied findings + #252 regression sweep; §B multi-agent finder sweep with refute-by-default adversarial verification; §C carries record-only.

---

## §A — Prior-Finding Verification (held / regressed)

Verdict summary: **7 of 8 HELD, 1 REGRESSED (H1 → C50-R1, remediation-introduced)**.
The §A clean streak (C40 / C42 / C44 / C46 / C48) **BREAKS at C50**.

All line cites below are against today's checkout (head `c76d6e70`).

### C50-R1 (flagship) — C22-H1 remediation §1.2.5 mis-cites ISP §6.2 as home of the 7 base-mandatory roles and asserts protocol enforcement that ISP explicitly disclaims — REGRESSED (remediation-introduced)

**What #252 added (for C22-H1)**: §1.2.5 "Operational-Minimum Cross-Reference" (L55–62), distinguishing the §1.2 *conceptual* minimum from the *operational* minimum, cross-referencing SAL §3.1 and `inter-society-protocol.md` §6.2.

**Defect component (a) — wrong citation for the role enumeration.**
- `SOCIETY_SPECIFICATION.md` L60 claims: *"`inter-society-protocol.md` §6.2 (referenced by the SDK's `validate_minimum_viable`) enumerates **seven base-mandatory roles** — Sovereign, Law Oracle, Policy Entity, Treasurer, Administrator, Archivist, and Citizen…"*
- Actual ISP §6.2 (`inter-society-protocol.md` L324–330) is titled **"Minimum Viable Semantic Society"** and contains exactly three *semantic* criteria — internal differentiation, witnessing capacity, externally-grounded ATP referent. It enumerates **no roles**.
- The seven base-mandatory roles actually live in **`society-roles.md` §2** (L49–51: *"Every Web4-compliant society MUST have these seven roles filled"*, listing Sovereign + Law Oracle + Policy-Entity + Treasurer + Administrator + Archivist + Citizen).
- The SDK confirms the split: `role.py` module header (L2, L19) and class docstring (L44) anchor the taxonomy to `society-roles.md §2-§4`; `BASE_MANDATORY_ROLES` (role.py:118–126) implements that list. `validate_minimum_viable` (role.py:341–353) cites ISP §6.2 **only for the semantic criteria** ("items 1 and 2 from §6.2"), not for any role list. §1.2.5 conflated the SDK's semantic-viability citation with the role-enumeration home.

**Defect component (b) — false enforcement claim.**
- L62 claims: *"Conformance to the role-structural minimum is checked by `inter-society-protocol.md §6.2` at federation-admission time"*.
- ISP §6.3 (L338) states the direct opposite: *"These are GUIDANCE, not protocol enforcement. The Web4 protocol does not adjudicate whether a society is 'real enough.'"* — viability is discovered socially via first-contact (§3) outcomes, not checked at admission.

**Wrong at birth, seeded by the audit itself.** ISP §6.2 never enumerated roles — at #252 time it already read exactly as today (verified via `git show 252e77bd:…inter-society-protocol.md`), and `society-roles.md` predates #252 (C7 audit cycle #217). The seed error is in C22-H1's own text, which described `role.py:341` as referencing "`inter-society-protocol.md §6.2`: 7 base-mandatory roles" — a mis-reading that #252 faithfully propagated into normative spec prose.

**Classification**: REGRESSED, remediation-introduced (the C36 lesson firing on live data — second confirmed instance of the class). Routed to **C51 remediation** per policy execution notes (twice-carried from slots 060047/120047): NOT a design-Q, NOT fixable in this audit-only session. Suggested C51 shape: re-point the role-enumeration citation at `society-roles.md` §2; replace the enforcement claim with ISP §6.3-faithful language (guidance + social discovery, with `validate_minimum_viable` as the SDK's *voluntary* conformance check); keep the SAL §3.1 sentence (verified accurate — see C50-A2 note below). Note the relationship to carry-C39/C25-H1 (7-role normative home): C51 should cite the role home as it stands today; the carry's open question (whether ISP should *also* normatively reference the list) remains operator-owned.

### C50-A2 — C22-H1 (the cross-reference scaffold itself): PARTIALLY HELD

The §1.2.5 paragraph #252 added does what C22-H1 asked structurally — §1.2 now acknowledges the conceptual-vs-operational distinction and points at the sister specs. The SAL half is accurate: `web4-society-authority-law.md` §3.1 does require Authority Role LCT + Quorum Policy (spot-verified this session). The ISP half is the regression above. Recorded as PARTIALLY HELD with the defect carried as C50-R1; not double-counted.

### C50-A3 — C22-H2 (economic event vocabulary): HELD

- L287: `"action": "deposit|allocate|reclaim"`; L288: `"token_type": "ATP"`; L292: the layer-separation disclaimer (treasury vocabulary vs R6/cycle-layer charge/discharge per `atp-adp-cycle.md` §2) — all present and intact.
- SDK still matches: `society.py:94` `ECONOMIC = "economic"  # allocate/deposit/reclaim`. No drift.

### C50-A4 — C22-H3 (Rejection non-record note): HELD

- L130: the Note on `Rejection` present, naming the exact 5-value `CitizenshipStatus` enum and the no-record semantics.
- SDK still matches: `federation.py:91–98` — APPLIED / PROVISIONAL / ACTIVE / SUSPENDED / TERMINATED, no REJECTED. No drift.

### C50-A5 — C22-M1 (§7.1 false-future framing): HELD

- L429: intro paragraph present, routing core inter-society primitives to `mcp-protocol.md` §7 + `inter-society-protocol.md` and scoping the bullets to further extensions. Bullets (L431–433) preserved with the "beyond §7.4 reputation envelopes" qualifier.

### C50-A6 — C22-M2 (minimum-record categories): HELD

- §1.2.2 (L33–39): 5 categories (citizenship / law / economic / metabolic / formation), "Witness attestations" removed, participant-not-event note present (L39) with cross-ref to §4.2.1 as canonical enumeration.
- §4.2.1 items 4–5 (L294–320): metabolic + formation JSON with SDK-exact strings.
- SDK still matches: `society.py:95–96` `METABOLIC = "metabolic"` / `FORMATION = "formation"` (BC#14 strings un-suffixed); recording sites unchanged (society.py:340/372/385/596/792). No drift.

### C50-A7 — C22-L1 (participatory validators inheritance): HELD

- L248: inheritance paragraph present under the §4.1.3 JSON, cross-refs §3.2.1 + §4.1.2, explains the intentional absence of `validators`.

### C50-A8 — C22-L2 (T3/V3 tensor naming): HELD

- L53: "Holds society-level T3 (trust) and V3 (value) tensors (see `t3-v3-tensors.md` and §5.3)". Consistent with corpus-wide V3-vocabulary remediations (C47/C49) — no `value`-tensor vocabulary drift here.

### C50-A9 — C22-I1 (date staleness, 2-file): HELD

- `SOCIETY_SPECIFICATION.md` L4: `## Date: 2026-05-30`; `SOCIETY_METABOLIC_STATES.md` L4: `## Date: 2026-05-30`. Both bumped, both intact.

### #252 regression sweep (beyond the 8 finding sites)

The full #252 diff (+58/−10, 2 files) was re-walked hunk-by-hunk against current head. Apart from §1.2.5 (C50-R1), every inserted hunk is internally accurate and SDK-verified above. The sister-file change was date-only. **No second remediation-introduced defect found in the diff.**

---

## §B — Fresh Delta Findings

*(appended after multi-agent finder sweep + refute-by-default verification — see commit history)*

---

## §C — Carries (record-only)

*(appended with §B)*
