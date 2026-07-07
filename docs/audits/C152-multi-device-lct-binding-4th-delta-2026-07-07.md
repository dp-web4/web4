# `multi-device-lct-binding.md` — Fourth Delta Re-Audit (C152)

**Audited file**: `web4-standard/core-spec/multi-device-lct-binding.md` (1126 lines, current `main`)
**Audit date**: 2026-07-07
**Audit series**: C-series, C152 (fourth delta re-audit). Chain: **C19** (first-pass, 2026-05-28, #246) → **C36** (first delta, 2026-06-07, #281) → **C80** (second delta, #371) / **C81** (remediation, #372, 2026-06-21) → **C120** (third delta, #421, 2026-06-30) → **C152** (this).
**Instrument**: proportioned single-auditor **refute-by-default** + git-snapshot verification + **adversarial verification subagent** on every candidate that survived initial refutation (2/2 candidates independently verified with cited evidence). Target is **byte-frozen since C81** (HEAD blob `b979ea7d`) and — new this delta — the **canonical authorities are frozen too** (SDK `binding.py` + `binding-vectors.json`: zero commits since C120), so the C56 claim-vs-canonical re-read is closed by byte-identity on *both* sides; §B (corpus delta + inbound-carry surface) is where all yield lives, per the C150 lesson: *on a clean delta, ask what the delta now leans on — and what leans on the target.*

**Corpus-delta window**: since C120 merge (2026-06-30T17:02Z). Spec movers: **7** — C117 mcp (`afab0c43`), C122 t3-v3 (`b2a98f7c`), C124 reputation (`4d1594ea`), C126 acp (`aabe4457`), C128 presence-README (`cf0d6cc5`), C130 FRACTAL (`4e3feb26`), C151 atp-adp (`256ab51d`). Non-spec movers checked (bounded, read-only): `web4-core/src/t3.rs`/`v3.rs` (P3b #445), `hub/` (constellation attestation + PAIRED-CHANNELS).

**Result**:
- **§A** — 7/7 C81 fixes HELD (byte-frozen target + byte-frozen SDK/vectors ⇒ every C120-verified claim carries by identity; t3-v3 anchors spot-re-read live). All **8 deferred carries STILL-OPEN**; none closed; **N1/C19-M5 HARDENED** on the canonical side (P3b deleted the last parallel tensor in the Rust crates).
- **§B** — **2 confirmed findings** (both cross-track, neither autonomous on this file, both adversarially verified) + 1 lineage-ledger adoption: **C152-1** — the inbound **B-10** carry's multi-device arm is an **overreach that would make the spec wrong if applied mechanically** (the file is hardware-P-256 by construction); **C152-2** — `hub/docs/PAIRED-CHANNELS.md:420` frames the already-specified constellation architecture as an open question.

---

## Executive Summary

1. **Doubly-frozen is a new (and stronger) verification state.** At C120 the target was frozen but the authorities had churned, so each claim needed a live re-read. At C152 target AND authorities (SDK, vectors) are all byte-identical to their C120-verified state — the 7 C81 fixes and 5 C120 refutations carry by identity, not by re-derivation. The spot-checks that remained (t3-v3 L14 role-context invariant, L135 3-root mandate — its file DID move at C122) both pass: the C122 hunk is the §10.2 conservation-row citation (L640), line-disjoint from every anchor multi-device's carries cite.

2. **The audit's entire yield came from the inbound surface, and both findings are "carried finding is wrong/incomplete" class, not "target is wrong" class.** C152-1 sharpens a cross-track carry owned by the security/handshake ledger *before* it becomes a wrong fix; C152-2 catches a hub PRD not citing the spec it needs. The target file itself remains clean — its autonomous remainder closed at C81 and stays closed.

3. **C152-1 (the flagship): B-10's multi-device arm prescribes a fix that is wrong for this file.** B-10 (born **C31 as B-L5**, scoped to `lct-capability-levels.md` + `LCT-linked-context-token.md`; **widened to multi-device at C68** as "example placeholders only — LOW") prescribes `cose:ES256` → `cose:EdDSA` at multi-device L257/L270. But multi-device is **hardware-P-256 end-to-end by construction**: L86 (`SecKeyCreateSignature` ECDSA P-256), L348/L446 (`algorithm="ES256"` at both enrollment ceremonies), L1022 (Secure Enclave ECSECPrimeRandom), L1043 (`secp256r1` StrongBox), L1072 (WebAuthn `alg: -7` — which **is** ES256-in-COSE, natively). Secure Enclave / StrongBox / FIDO2 **cannot produce Ed25519 signatures**. Both B-10 sites are signatures by such keys: L257 `binding_proof` is by the `phone_secure_element` key; L270 `attestation_chain[].sig` is by an existing device's SE key per §3.2 step 7 (`existing_device.sign_enrollment`, L466-470). And the corpus canon does **not** mandate EdDSA universally: security-framework L44 makes COSE/EdDSA mandatory-to-**implement** (not mandatory-to-use), the **W4-FIPS-1 profile sanctions ECDSA-P256** (security-framework L35-36, handshake L23/L150), and LCT-core itself allows "**Ed25519 or P-256**" (LCT-linked-context-token L224; lct-capability-levels L96). The C68 widening was a label-pattern sweep — no audit doc in the B-10 lineage (C31/C68/C108/C109/C140) ever engages the hardware-key constraint. **Applying B-10 as written would make the spec self-contradictory.** → Route: cross-track memo to the B-10 owner (security/handshake carry ledger); adjudication options in §D.

4. **C152-2: hub PRD treats specified architecture as an open question.** `PAIRED-CHANNELS.md` §8 item 6 (latent since 2026-06-08 — predates C120; newly observed because this is the first multi-device delta to read the hub docs, per this window's hub churn): "multi-device… probably needs LCT split — separate sub-LCTs per device — which is its own architectural question." That parenthetical is answered verbatim by multi-device §2.1–2.4 (root LCT + per-device LCTs = device constellation) — and hub's own §10.5 already builds on `ConstellationAttestation`. The verifier's honest narrowing: the item's *leading* question (do both devices receive paired messages?) is **genuinely open** — multi-device §7 has no message-delivery surface. Fix (hub-track): cite the spec for identity structure; keep only delivery semantics open.

---

## §A — Delta Status of Prior Findings

### A.1 — C81 fixes (7/7 HELD, by double byte-identity)

Target blob `b979ea7d` = C81 = C120 state; SDK `binding.py` + `binding-vectors.json` have **zero commits** since C120 (`git log --since=2026-06-30T17:02Z` empty). Every claim C120 verified live (3-arg `cross_witness`, 4-param `record_cross_witness`, `compute_device_trust` formula mirror, bare-string `cross_witnesses`, orphan-block removal, `recovery_revoked` scope note, ceil(n/2) quorum wording) is byte-identical on both the claiming and the canonical side ⇒ HELD with no re-derivation possible or needed. This is the first doubly-frozen wrap in the lineage.

### A.2 — Deferred carries (8/8 STILL-OPEN; 1 hardened) — snapshot anchors recorded for C154+

| Carry | Status | Snapshot-guard evidence (2026-07-07, post-C151 corpus) |
|-------|--------|--------------------------------------------------------|
| **N1** (flat 8-dim `t3_tensor`) | **STILL-OPEN, HARDENED** | t3-v3 L135 3-root mandate re-read post-C122, intact; `t3v3-ontology.ttl` zero commits since C120 (3 roots only). **Hardening**: P3b `20ef29f5` (#445, 2026-07-03) deleted web4-trust-core's parallel `T3Tensor`/`V3Tensor`, converging `EntityTrust` onto canonical 3-root `web4_core::t3::T3` ("There is now ONE tensor in the crate") — one more implementation on the 3-root side, one fewer parallel structure anywhere in the repo; multi-device §2.3/§4.1 flat-8 is now the corpus's sole surviving flat-form tensor block. Still **DESIGN-Q** (attach-strategy = t3-v3-side D2, per C121). |
| **N2** (no entity-role binding) | STILL-OPEN | t3-v3 L14 role-context invariant re-read post-C122, intact. Same DESIGN-Q site as N1. |
| **C36-N9** (Society MUSTs / birth-cert owner) | STILL-OPEN | `SOCIETY_SPECIFICATION.md` + `web4-society-authority-law.md`: zero commits since C120. Operator/cross-track. |
| **C36-N11** (entity-segmented LCT IDs) | STILL-OPEN | LCT-core: zero commits since C120. DESIGN-Q (carry-C33 B-H1). |
| **C19-M3** (3 exception classes absent from errors.md) | STILL-OPEN | `errors.md`: zero commits since C120 (C138 was audit-only). Deferred (carry-C30). |
| **C19-M4** (LCT-core doesn't acknowledge §7.1 extension) | STILL-OPEN | LCT-core: zero commits since C120. Cross-spec (LCT-recip). |
| **C19-M5** (8 sub-dims absent from ontology) | STILL-OPEN | Ontology: zero commits since C120. Couples N1 (hardened jointly). |
| **C19-M7** (§7.3 ATP costs free-floating) | STILL-OPEN | atp-adp moved at C151 but the hunk is the §2.4 L214 conservation-note phrase; `grep -icE "device|enroll|constellation"` on atp-adp = **0**, unchanged. The C151 reword does not touch cost semantics; §7.3 costs remain without a counterpart. |

**Lean-on lens (both directions, per C150)**: nothing in the 7 movers newly leans on multi-device (the only new references to it in the window are audit-doc prose); multi-device leans on nothing the movers changed (its outbound citations are t3-v3 L1112 / SOCIETY_SPEC L1113 / atp-adp L1114 — the two that moved changed at hunks its citations don't read).

## §B — Findings (2 confirmed, both cross-track; 0 on the target file itself)

### C152-1 — B-10's multi-device arm is an overreach; mechanical application would break the spec (LOW-MED · CROSS-TRACK to B-10 owner · adversarially CONFIRMED-SHARPENED)

Full statement in Executive Summary #3. Additional verifier sharpenings, all evidence-cited:
- **Provenance corrected**: born **C31 B-L5** (`C31-security-framework-audit-2026-06-04.md:42,126-128`), widened at **C68** (`C68-security-framework-delta-audit-2026-06-17.md:132-135`, "example placeholders only — LOW"), carried verbatim through C108/C109/**C140** (`cose:ES256 → cose:EdDSA` in 3 files). The multi-device lineage never listed it (C120 doc: zero `cose` mentions) — **adopted into this file's carry table as of C152** (9th carry) so future deltas snapshot-guard it here. [[feedback_cross_doc_carry_inbound]] + [[feedback_prior_finding_path_provenance]] both fire.
- **B-10's premise is profile-relative, not a COSE error**: COSE `alg -7` IS ES256 — exactly what WebAuthn/FIDO2 natively emits and what the file's own L1072 uses. `cose:ES256` may be correct **as-is**.
- **Residual genuine gap**: §2.4 never states the **genesis** attestation-chain entry's signer (society vs first device) — L262-271 entry is signer-implicit; §3.2 resolves it only for enrollment entries.
- **What the adjudication must decide** (owner: security/handshake carry cluster, operator-gated with B-7/B-8/etc.): split B-10 per-file. For multi-device's 2 sites choose (i) retain `cose:ES256`, (ii) relabel `jose:ES256` per the W4-FIPS-1/JOSE pairing, or (iii) retain + add an explicit hardware-anchor COSE+ES256 allowance to security-framework §1.3 — **not** `cose:EdDSA`. Separately: make the §2.4 genesis signer explicit. Note `lct-capability-levels.md:96` ("Ed25519 or P-256") softens the EdDSA rename for the *other* B-10 sites too — the owner may want to re-examine the whole carry.

### C152-2 — `hub/docs/PAIRED-CHANNELS.md:420` frames specified architecture as open (LOW · CROSS-TRACK to hub · latent 2026-06-08 · adversarially CONFIRMED, narrowed)

Full statement in Executive Summary #4. Fix is one sentence in a hub PRD: cite `multi-device-lct-binding.md` §2 for the identity structure (root LCT + per-device LCTs — the exact "LCT split / sub-LCTs per device" the item speculates about), keep open only the delivery-semantics question, which the spec genuinely does not answer (§7 has no message-routing surface — noted as a possible future §7 integration point, not a defect). Bonus evidence: the same doc's §10.5 already consumes `ConstellationAttestation` from hub's own stack.

### INFO (no action)
- Hub `constellation.rs` assurance tier wire value `multi_device` (single_device/multi_device/hardware_backed) — vocabulary overlap with this spec's "Device Constellation", different concept (co-sign count tier vs device-LCT set), no conflict, no protected term redefined.
- 5 of 7 movers (mcp, reputation, acp, presence-README, FRACTAL) are **zero-of-concept disjoint**: multi-device cites none of these files and their hunks (mcp L899, reputation L292/L649/L700, acp L74/L309, presence L41, FRACTAL L50) contain zero device/constellation content.
- Inbound-carry read of the movers' audit docs: C121's D2/N1-N2 attach-strategy is the existing N1/N2 coupling seen from t3-v3's side (no new adoption needed); C117's multi-device mention is the file-by-file lesson citation; C151's is rotation context.

## §C — Refuted candidates (1)

| Candidate | Why refuted |
|-----------|-------------|
| Hub "constellation" naming collision as a terminology-protection defect | "Constellation" is not a protected term; the two usages are hub-internal wire vocabulary (greenlit wire-shape memo) vs spec structure; no redefinition of Device Constellation occurs. Downgraded to INFO. |

## §D — Cross-audit signals

- **A carried finding can be wrong about a file it was widened into.** B-10 was correct-shaped at its C31 birth sites and became wrong when C68 pattern-swept it into a hardware-constrained doc without reading the signer key material. Delta audits of a target should re-adjudicate inbound carries against the target's own constraints, not just adopt them. (Extends [[feedback_prior_finding_path_provenance]]: not just the *path* but the *prescription* of a carried finding can be stale/overreaching while the observation stays real.)
- **Doubly-frozen (target + authorities) closes §A by identity** — the C56 re-read has nothing to re-derive when both sides are byte-stable; audit effort correctly shifts 100% to the inbound/corpus surface. 7th consecutive frozen-target confirmation that frozen ≠ skip: this wrap still yielded two confirmed cross-track findings.
- **First multi-device wrap to read hub/** — the window's hub churn (constellation attestation, PAIRED-CHANNELS) made hub part of this target's citation-adjacent surface for the first time. Both findings came from exactly that expansion. When a target's *concepts* (not citations) gain implementations elsewhere in the repo, the delta surface includes them.

## Routing summary

| Item | Route |
|------|-------|
| C152-1 (B-10 multi-device arm overreach + genesis-signer gap) | **CROSS-TRACK** → security/handshake B-10 owner (carries.md cluster, operator-gated); do NOT apply cose:EdDSA to multi-device |
| C152-2 (PAIRED-CHANNELS.md:420 citation) | **CROSS-TRACK** → hub track (one-sentence PRD fix) |
| N1+C19-M5 hardening note | Recorded on existing DESIGN-Q; no new route |
| C153 remediation slot | **Expected NO-OP** on this file — zero autonomous findings; rotation advances (t3-v3 4th delta next) |

Audit-only: **0 spec mutation**, 0 SDK mutation, 1 new file (this document).

---

*"The ninth carry arrived from another file's ledger, prescribing a fix this file must refuse — adopting a carry and adjudicating it are different acts."*
