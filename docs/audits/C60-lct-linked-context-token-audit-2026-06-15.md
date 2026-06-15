# C60: LCT-linked-context-token.md Internal Consistency RE-Audit (2nd delta)

**Date**: 2026-06-15
**Auditor**: Autonomous session (legion-web4-20260615-120002)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (693 lines, HEAD `7b49a08a`)
**Prior audits**: C9 (`lct-internal-consistency-2026-05-22.md`, 8 findings → PR #225, clean 8/8) → **C24** (`C24-lct-linked-context-token-audit-2026-05-31.md`, 12 NEW → PR #256, 6 autonomous applied / 4 design-Q + 2 SDK deferred)
**Spec mutations since C24**: 1 — PR #256 (`8679a80d`, the C24 remediation itself). File **byte-identical since #256**.

**Framing**: This is the **second delta re-audit** of the LCT spec (third audit overall: C9 → C24 → C60). Because the file is byte-identical to its C24 remediation, the **C56 completeness+mirror method** applies: §A audits the remediation's own site-enumeration AND its mirrors (SDK strings, sister-docs, test vectors), not merely "did each finding hold." §B is a 10-lens refute-by-default finder workflow fed the full C24 known-list + DEMOTED list so nothing is re-derived.

**Counts**:
- **§A**: 6/6 autonomous C24 remediations **HELD**; 4 DESIGN-Q + 2 SDK cross-track re-confirmed **OPEN**; **2 fresh §A findings** (A1 remediation-introduced SSOT, A2 residual annotation tension).
- **§B**: 10 lenses → 20 confirmed (refute-by-default) → **19 distinct** after dedup.
- **C60 distinct total**: **21** (0 HIGH / 13 MEDIUM / 7 LOW / 1 INFO).
- **DEMOTED (carried, not re-issued)**: 2 (C24-D1 ontology cluster, C24-D2 AI/ai).
- **Cross-track cite-only**: 1 (C23-H1 birth-cert shape).

Per BC-C23-5 (anti-padding): the elevated count vs recent deltas (C58=15, C54=16) is honest — C60 ran two lenses prior LCT passes never applied (**security-claims-vs-mechanism** §8/§9, and **deep cross-doc** against `lct-capability-levels.md` / `t3-v3-tensors.md` / `protocols/web4-lct.md`). Every finding is independently refute-by-default verified with exact quotes. The two largest fresh clusters (security-properties §8/§9, and LCT-vs-sister-doc structural contradictions) are net-new surface, not regression.

---

## Authority hierarchy used for this audit

| Claim class | Authority | File(s) |
|-------------|-----------|---------|
| Spec internal coherence | spec | `core-spec/LCT-linked-context-token.md` (HEAD `7b49a08a`) |
| Canonical wire shape / dataclass | SDK | `implementation/sdk/web4/lct.py`, `trust.py`, `capability.py` |
| Tensor SSOT | sister spec | `core-spec/t3-v3-tensors.md` (§10.2 "protocol-invariant parameters" — self-declared normative source) |
| Capability gating / extended types | sister spec | `core-spec/lct-capability-levels.md` |
| Cross-language interop reality | test vectors | `test-vectors/lct/` (5 files) |
| Witness/entity enums | protocol detail | `protocols/web4-lct.md` |
| Birth-certificate 3-way shape | (cross-track) | C23-H1 — cite-only per BC-C23-1 firewall |
| Subordinate ontology | (cluster carry) | `ontology/web4-core-ontology.ttl` L219 — C16-M8 / C24-D1, DEMOTED |

Every cited line was re-read against the live file before the finding text was written (BC#2/BC#3).

---

## Summary

| Severity | Count | Theme |
|----------|-------|-------|
| HIGH | 0 | — |
| MEDIUM | 13 | A1 (**flagship-A** remediation-introduced tensor-weight SSOT duplication vs t3-v3 §10.2); B1 (broken `valid-birth-certificate.json` vector); B3 (§4.2 membership-MUST unenforced); B5 (rotation overlap state-machine gap); B6/B7 (SDK V3-clamp / no-bootstrap-path); B9/B10/B11/B13 (**flagship-B** LCT-vs-sister-doc structural contradictions: per-role tensor cardinality, `dimensions`-wrapper shape, birth_timestamp gating, witnessing-role enum); B14/B15/B17 (**flagship-C** §8/§9 security claims without mechanism) |
| LOW | 7 | A2 (§6.2 composite annotation vs new prose); B2 (paired.context unmodeled); B4 (§11.2 `witness_attested` undefined — C24-L1 fixed §11.1 only); B8 (SDK no quorum guard); B12 (entity_type closed-15 vs extended types); B16 (selective-attestation claim); B19 (future-timestamp MUST unverifiable) |
| INFO | 1 | B18 (§8.1 blockchain-anchor bullet lacks the "Optional" qualifier its sibling hardware-anchor bullet has) |

**Severity calibration** (anchored to C12–C58): MEDIUM = normative MUST contradiction across co-equal sources, behavioral-shape SDK gap on a spec-MUST step, or wire-shape divergence converging on a normative requirement. LOW = doc-hygiene / unverifiable-but-non-exploitable MUST / additive modeling gap. INFO = editorial asymmetry with no guarantee error.

---

## §A. Completeness + Mirror Verification (C56 method)

### A.0 — C24 autonomous remediations (6/6 HELD)

| C24 ID | Site | Verification @ `7b49a08a` |
|--------|------|---------------------------|
| M1 | §3.3 | `binding["binding_proof"]` embedded (L257); return `(lct_id, binding)` (L262); docstring updated (L241). HELD. |
| M5 | §6.1/§6.2 | Normative formulas present (T3 0.4/0.3/0.3 L388; V3 0.3/0.35/0.35 L425); §2.3 example composites 0.84/0.81→**0.85/0.85** (L141/L156). Reproduces: T3=0.850; V3=0.8515→0.85 within the ±0.01 tolerance §11.1 introduced; sub-dims also reproduce roots. HELD. |
| L1 | §11.1 | Helper calls annotated `# implementation-defined` (L611/612/615) + expected-semantics paragraph (L620-624). HELD. |
| L2 | §13 | +`entity-types.md` (L683) +`lct-capability-levels.md` (L684). HELD. |
| L4 | §2.3 | +`@context` (L62) +`@type` (L63). HELD. |
| INFO1 | L4/L691 | Dates → May 31 2026. HELD. |

### A.1 — Mirror checks (Bash-verified, per policy binding-note 1)

- **#256 provenance** (`git show 8679a80d`): touched the LCT spec ONLY (6 findings + dates); commit body explicitly states "no sister-doc date bumps." Per-file provenance clean — not a date-bump-only false-innocent (cf. the C50 #252 regression-class trap).
- **Test vectors**: composites in `test-vectors/lct/*.json` reproduce from the new §6.1/§6.2 weights (full-precision floats, e.g. `0.8574999…`); the OLD example values `0.84`/`0.81` appear nowhere → no M5 mirror lag.
- **SDK weights**: `trust.py:77-78` `T3_WEIGHTS={0.4,0.3,0.3}`, `V3_WEIGHTS={0.3,0.35,0.35}` exactly match §6.1/§6.2. Mirror-consistent.

### A.2 — Carried items re-confirmed OPEN

| C24 ID | Class | Re-verification |
|--------|-------|-----------------|
| H1 | DESIGN-Q | §3.3 L260 still 2-segment `lct:web4:<hash>`; SDK still `lct:web4:<entity>:<hex16>`. Divergent. OPEN. |
| M2 | SDK cross-track | `LCT.create()` still does not populate `mrh.witnessing`. OPEN. |
| M3 | SDK cross-track | `LCT.create()` still does not build `attestations` from witnesses. OPEN. |
| M4 | DESIGN-Q | SDK still `RevocationStatus.SUSPENDED`; spec still does not enumerate `revocation.status`. OPEN. |
| M6 | DESIGN-Q | §7.3 "Mark as superseded" (status) vs §7.4 reason-list (superseded as reason); SDK has neither. OPEN. |
| L3 | DESIGN-Q | §6.2 `valuation 0.0+` vs `composite_score 0.0-1.0`. OPEN (and see A2/B6). |

### A.3 — Fresh §A findings

**A1 (MEDIUM — flagship-A, remediation-introduced SSOT duplication)**
The M5 remediation declared the LCT §6.1/§6.2 composite weights "(normative)". But `t3-v3-tensors.md §10.2` (L552-558) states verbatim **"This table is the normative source for all protocol-invariant formulas"** and lists the T3/V3 composite weights as protocol-invariant (MUST use exactly these). LCT §6.1/§6.2 now independently asserts normativity for the same constants **without deferring to or cross-referencing that declared sole SSOT** — two normative homes for one protocol-invariant. Values currently agree (no live break) → MEDIUM not HIGH, but this is a textbook latent-drift seam introduced by a remediation. Distinct axis from B9 (which is tensor *cardinality*, not weights).
*Class*: autonomous. *Fix*: change LCT §6.1/§6.2 to cite `t3-v3-tensors.md §10.2` as authoritative ("per the protocol-invariant weights in `t3-v3-tensors.md` §10.2") rather than re-declaring normativity.

**A2 (LOW — residual L3 annotation tension)**
§6.2 JSON block (L407) still annotates `"composite_score": 0.0-1.0` while the same-remediation §6.2 prose (L428) and the §11.1 validator semantics (L623) both acknowledge composite **can exceed 1.0** under high valuation. The annotation contradicts the prose the remediation added.
*Class*: autonomous (coordinate with L3 design-Q resolution).

---

## §B. NEW Findings (10-lens refute-by-default workflow)

Workflow `wf_9e3a89ea-cd3`: 10 lenses (wire-shape, rfc2119, xref, numeric, lifecycle, sdk-align, cross-doc, terminology, security, remediation) → per-candidate refute-by-default verifier; 20 confirmed → 19 distinct.

### Cluster 1 — Test-vector corpus defects (vs the spec's OWN validators)

**B1 (MEDIUM, cross-track) — `valid-birth-certificate.json` fails the spec's own §11 validators (3 ways)**
`test-vectors/lct/valid-birth-certificate.json` declares `should_succeed: true` (L48) yet violates the spec's own validators:
1. **No `issuing_society`** — substitutes the spec-undefined `parent_entity` (L23); §4.2 L281 makes `issuing_society` a MUST, §11.2 L635 `assert "issuing_society" in bc`. (`grep -c issuing_society` = 0; other 4 vectors = 1/1/1/9.)
2. **No `t3_tensor`/`v3_tensor`** — §2.1 L46-47 MUST; §11.1 L599-600 asserts both. (Lone vector missing both.)
3. **Only 2 `birth_witnesses`** vs §4.2/§11.2 MUST-≥3.
The vector was authored against an older/divergent shape. *Fix*: regenerate the vector to the current normative shape (vector-corpus track).

**B2 (LOW, design-q) — `mrh.paired[].context` is unmodeled**
`interop-human-full.json` L60-66 carries `"context": "project-alpha"` in a paired entry. SDK `MRHPairing` (lct.py L102-109) has no `context`; `from_jsonld`/`to_jsonld` silently drop it; §2.3 paired example omits it. Contrast: §2.3 `bound` entries DO carry `binding_context` (L93) — so context is modeled for bound but not paired. *Resolution*: add to spec+SDK, drop from vector, or align with bound-level `binding_context`.

### Cluster 2 — §11 validator gaps (one is remediation-incompleteness)

**B3 (MEDIUM, autonomous) — §4.2 #3 "Witnesses MUST be members of issuing society" has no enforcement**
The §11.2 validator (L628-655) enforces witness *count* (L641) and per-witness *attestation* (L652-653 via `witness_attested`) but never checks society membership (`grep "member"` → only L301). Asymmetric with sibling MUST L299 (enforced). *Fix*: add a membership predicate/helper, or soften L301, or document it implementation-defined.

**B4 (LOW, autonomous) — §11.2 calls undefined `witness_attested` (C24-L1 fixed §11.1 only)**
`witness_attested` (L653) is called in the birth-cert validator but never defined, never annotated `# implementation-defined`, and absent corpus-wide — **unlike** the §11.1 trio that C24-L1 explicitly annotated + documented (L611-624). This is **remediation incompleteness**: C24-L1's scope was "§11.1 helper calls", leaving §11.2's dangling helper untouched. *Fix*: annotate `witness_attested` + add its expected semantics (present-only vs COSE-verified; which collection it consults) — completes C24-L1.

### Cluster 3 — Lifecycle / state-machine

**B5 (MEDIUM, autonomous) — Rotation overlap window has no defined new-LCT status + no uniqueness invariant**
§7.3 L470-482 creates a new LCT, runs a 24-48h window where "Both LCTs valid" with the "Same subject DID", then retires the parent. The only defined status values are `active` (§2.3 L183) and `revoked` (§7.4 L495) — the new LCT's status during overlap is unstated, two LCTs are simultaneously active for one subject DID, and there is no active-count/uniqueness invariant or relying-party disambiguation rule (`grep "uniqu"` → nothing). *Split*: new-LCT-status (autonomous: state `active`) vs uniqueness invariant + disambiguation (design-Q).

### Cluster 4 — SDK behavioral-shape gaps (extends C24-M2/M3)

**B6 (MEDIUM, cross-track) — SDK V3.valuation hard-clamps to 1.0, contradicting spec "can exceed 1.0"**
`trust.py` `V3.__post_init__` L289 `_clamp(valuation)` with `hi=1.0` (L140) caps valuation at 1.0; the spec §6.2 L406/L428 + §11.1 L623 say valuation MAY exceed 1.0. SDK cannot represent the spec-legal state; `V3.calculate` (L324) naturally produces >1.0 then caps it. (This is the SDK-side facet of the L3 design-Q.) *Fix*: SDK-track decision (couple with L3).

**B7 (MEDIUM, cross-track) — SDK `LCT.create()` has no §3.2 self-issued/bootstrap path**
The sole factory (lct.py L263) unconditionally builds a `BirthCertificate` + permanent pairing; there is no Regular/self-issued path despite §3.2 step 5 + §4.3 ("Issuer: Self or Society"). Field `birth_certificate: Optional[...] = None` (L255) shows the model allows omission; the factory does not.

**B8 (LOW, cross-track) — SDK `LCT.create()` accepts 0 witnesses (no §3.1/§4.2 quorum guard)**
`witnesses or []` (L283) → `birth_witnesses=list(witnesses)` (L307) with no `>=3` guard; `LCT.create(EntityType.AI, 'pk')` yields a birth cert with `birth_witnesses=[]` and no error, though it fails §11.2 L641. Quorum IS enforced elsewhere (`capability.py` L276, `federation.py` QuorumPolicy) — so this is a missing guard at the genesis factory specifically.

### Cluster 5 — LCT-vs-sister-doc structural contradictions (flagship-B)

**B9 (MEDIUM, cross-track) — single-tensor-per-LCT vs per-role-tensor SSOT**
LCT §6.1 L364 / §6.2 L401 "Every LCT MUST contain a `t3_tensor`/`v3_tensor`" + the §2.3 canonical structure embeds exactly ONE of each with a single composite. But `t3-v3-tensors.md §6.3` mandates the opposite cardinality: L412 "Implementations MUST NOT compute global (role-agnostic) trust scores — only role-specific tensors"; L413 "Each role MUST maintain separate T3/V3 tensors" (its model keys tensors by entity+role — one entity holds multiple T3Tensors). A multi-role entity cannot satisfy both. LCT §6.x cross-refs only the ontology TTL, never `t3-v3-tensors.md §6.3`. *Fix*: reconcile cardinality (SSOT vs LCT body).

**B10 (MEDIUM, cross-track) — `t3_tensor`/`v3_tensor` JSON shape: flat roots vs `dimensions` wrapper**
LCT puts roots as DIRECT keys everywhere (§2.3, §6.1 L368-371, §11.1 L622 asserts `talent`/`training`/`temperament` present as direct members); `grep '"dimensions"'` in the LCT spec = 0. `lct-capability-levels.md` NESTS them under a `"dimensions"` wrapper in every example (L131-136…) AND in normative text (§2.4 L170 `t3_tensor.dimensions: All 3 root dimensions non-zero`, §2.5 L221 `v3_tensor.dimensions.valuation`). An LCT built to either shape fails the other doc's validator. The TTL doesn't adjudicate JSON nesting. *Fix*: pick one wire shape across both core-spec files.

**B11 (MEDIUM, cross-track) — `birth_timestamp`: MUST+asserted in LCT, "recommended, not gating" in capability-levels**
LCT §4.2 L284 lists `birth_timestamp` under MUST (no RECOMMENDED qualifier, unlike adjacent `birth_context`/`genesis_block_hash`); §11.2 L637 `assert "birth_timestamp" in bc`. But `lct-capability-levels.md §2.6 L284` says the Level-4 gate is `issuing_society + citizen_role`, "remaining certificate fields are recommended, not gating"; SDK `capability.py` `_has_birth_certificate` (L271-276) checks only those two + witnesses≥3, NOT `birth_timestamp`. An LCT lacking `birth_timestamp` passes the capability gate but fails the §11.2 validator.

**B13 (MEDIUM, cross-track) — `mrh.witnessing[].role` enum: 7 values (LCT) vs 3 (`web4-lct.md`)**
LCT §2.3 L108 + §5.2.3 L337 enumerate 7 roles (`time|audit|oracle|existence|action|state|quality`). `protocols/web4-lct.md:36,97` defines the SAME field as only 3 (`time|audit|oracle`) — its 7-value list at L112 is for the attestation `type` field, not the witnessing role. *Related (same root cause, `web4-lct.md` predates the expansion)*: `web4-lct.md:14,63` also carries a stale **12-type** `entity_type` enum vs the canonical 15. *Fix*: update `web4-lct.md` to the 7-role + 15-type sets, or mark it superseded by the core spec.

### Cluster 6 — §8/§9 security claims without mechanism (flagship-C)

**B14 (MEDIUM, autonomous) — §8.1 "independent witnesses" contradicted by §4.2 #3 society-membership rule**
§8.1 L508 rests unforgeability partly on "multiple **independent** witnesses", but the only normative witness-qualification rule (§4.2 L301) forces every witness to be a member of the issuing society — which for a birth cert IS the minting authority (§4.3 L307). `grep "independent|collusion|distinct|sybil"` → only L508; no distinctness/anti-collusion requirement exists. *Fix*: add an anti-collusion/distinctness requirement (design-Q) or soften §8.1 prose (autonomous).

**B15 (MEDIUM, autonomous) — §8.3 "Minimal disclosure: Only expose necessary capabilities" contradicted by required inlined Policy**
§8.3 L522 claims minimal capability disclosure, but `policy` is a REQUIRED component (§2.1 L45) fully inlined in the canonical LCT (§2.3 L117-129) — any validator receives the complete capability set. No selective-disclosure mechanism exists (ZKP is §12.2 Research Directions, tensor-scoped, future). *Fix*: design-Q (presentation/derivation layer) or soften the claim.

**B16 (LOW, autonomous) — §8.3 "Selective attestation: Share only relevant witnesses" unrealizable**
§8.3 L524; but §11.1 L604 + §11.2 L641/L652 require the FULL `birth_witnesses` set, so a conformant birth cert cannot "share only relevant witnesses". No presentation primitive in the normative body. (Leaked data is pseudonymous witness LCT IDs → LOW.)

**B17 (MEDIUM, autonomous) — §9.3 "Revoke compromised attestations" is unimplementable**
§9.3 L551 requires witnesses to revoke compromised attestations, but the attestation object (§2.3 L161-172: witness/type/claims/sig/ts) has no status/revocation field; the only revocation construct is LCT-level (§2.3 L182-186, §7.4) and revokes the whole LCT. No per-attestation revocation path exists (spec or SDK). *Fix*: define a per-attestation revocation mechanism (design-Q) or scope the MUST to LCT-level.

**B18 (INFO, autonomous) — §8.1 blockchain-anchor bullet lacks the "Optional" qualifier**
§8.1 L507 marks "Hardware anchors" as "Optional" but L509 "Blockchain anchor … temporal proof" carries no qualifier, while `genesis_block_hash` is RECOMMENDED/omittable (§4.2 L286, §4.3 L312) and never checked by §11.2. Editorial asymmetry. *Fix*: add "(when present)".

**B19 (LOW, autonomous) — §9.3 "Never attest to future timestamps" is unverifiable**
§9.3 L548 is a behavioral MUST with no trusted/reference clock, no verifier comparison, no clock-skew tolerance, and no error path (errors.md has no timestamp-validation code). *Fix*: define an implementation-defined verification + error reference, or scope as advisory.

---

## §C. Routing for C61 remediation

**Autonomous-actionable (spec-only, next remediation turn)** — A1 (cite t3-v3 §10.2 SSOT), A2 (fix §6.2 composite annotation), B4 (annotate §11.2 `witness_attested` + semantics — completes C24-L1), B18 (blockchain-anchor "(when present)"), and the prose-softening / state-stating halves of B3 (soften L301 or mark impl-defined), B5 (state new-LCT status `active`), B14 (soften "independent"), B16 (soften selective-attestation), B19 (mark verification impl-defined). **Recommend bundling B4 + the §8/§9 prose-precision set as the C61 autonomous PR.**

**DESIGN-Q (operator-engagement bundle)** — carried H1/M4/M6/L3 (+ A2 couples to L3); B2 (paired.context), B5-uniqueness (active-count invariant + disambiguation), B12 (entity_type closed-15 vs extended types), B14-requirement (anti-collusion rule), B15 (selective-disclosure/presentation layer), B17 (per-attestation revocation mechanism).

**Cross-track** —
- *Vector corpus*: B1 (regenerate `valid-birth-certificate.json`).
- *SDK*: carried M2/M3 + B6 (V3 clamp ↔ L3), B7 (bootstrap factory), B8 (quorum guard).
- *Sister-doc reconciliation*: B9 (tensor cardinality vs t3-v3 §6.3), B10 (`dimensions`-wrapper vs flat — t3-v3/capability-levels/LCT), B11 (`birth_timestamp` gating vs capability-levels + capability.py), B13 (`web4-lct.md` 7-role + 15-type staleness).

**DEMOTED / firewall** — C24-D1 (ontology L219 cluster, capped), C24-D2 (AI/ai), C23-H1 (birth-cert shape, cite-only).

---

## Cross-Reference to Prior Audits

| Audit | Spec | Findings | Remediated |
|-------|------|----------|------------|
| C9 | LCT (1st) | 8 | PR #225 (8/8 clean) |
| C24 | LCT (re-audit) | 12 NEW + 0 carried | PR #256 (6 autonomous; 4 DQ + 2 SDK deferred) |
| **C60** | **LCT (2nd delta)** | **21 distinct** (0H/13M/7L/1I): 2 §A + 19 §B; 6/6 C24-autonomous HELD, 6 carried OPEN | **Pending** |

---

## §D. Lessons

1. **Remediation-incompleteness has a partner-site signature.** C24-L1 fixed the §11.1 undefined-helper trio but left the structurally-identical §11.2 `witness_attested` dangling (B4). A "fix all undefined helpers" finding should be checked against EVERY validator block in the file, not just the one the finding cited. (Extends [[feedback_remediation_introduced_regression]]: remediation-completeness must sweep sibling code blocks of the same class.)
2. **A "(normative)" assertion added by remediation can create an SSOT collision** even when values agree (A1). When a remediation promotes a constant to normative, it must check whether another doc already claims sole normativity for it — and defer rather than duplicate.
3. **New lenses on an old file are not padding.** The §8/§9 security-claims-vs-mechanism lens and the deep cross-doc lens (vs capability-levels/t3-v3/web4-lct) produced 10 of 19 §B findings — surface that C9 (internal-only) and C24 (SDK+vector) never covered. A third audit pass earns its keep by changing the instrument, not re-running the same one.
4. **The `dimensions`-wrapper vs flat-roots split (B10) is a latent corpus-wide wire hazard** — two co-equal core-spec files specify incompatible JSON for the same embedded object. Worth elevating in the operator cross-doc bundle alongside C23-H1.

---

*"An LCT is not an identity. It is a presence — witnessed, contextualized, and witness-hardened."* — and across three audits (C9 → C24 → C60), progressively pinned down where its witnesses, tensors, and security claims actually live.
