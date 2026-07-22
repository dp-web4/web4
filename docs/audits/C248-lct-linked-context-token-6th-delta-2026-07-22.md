# C248: LCT-linked-context-token.md 6th-Delta Re-Audit (7th pass)

**Date**: 2026-07-22
**Auditor**: Autonomous session (legion-web4-20260722-060036)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (726 lines, blob `231d70b5` — **byte-frozen since C210**)
**Prior audits**: C9 (8 → #225) → C24 (12 NEW → #256) → **C60** (21 → #338) → **C61 remediation** (`9d1933f8`: 9 autonomous) → **C100** (0 net-new) → **C135** (0 net-new) → **C172** (byte-frozen: 3 Rust-mirror net-new, routed) → **C210** (#531 mover, regression-CLEAN, 1 net-new C210-N1).
**Spec mutations since C210**: **0**. `git diff d89595e8..HEAD -- <target>` = empty (last touch #531 `d89595e8`, 2026-07-16 — the C210 mover). This is a byte-frozen delta; the audit surface is the **moved SDK mirror**.

---

## Framing — frozen target, moved Rust mirror; the yield is two spec-vs-ratified structure divergences, both LCT-side faces of open carries

C210 was the first non-frozen LCT delta since C61; #531 inserted §1.2 "Inspectable Evidence" and surfaced C210-N1. **C248 is a frozen-target delta** — but per the standing method guard ("the SDK mirror is not a fixed set — re-derive implementers at live HEAD"), the surface that moved is the **Rust web4-core mirror**, which grew two ratified structural fields on the `Lct` struct *after* the C210 snapshot:

- **#538** (`0e997079`, 2026-07-17 18:04 — after C210 noon): `attestation.rs` birth-certificate/citizenship, reshaped to **plural + ledger-resident** (`Lct::citizenships: Vec<BirthCertificateRef>`; the authoritative `CitizenshipRecord` lives in the **society's ledger**, the LCT carries only a tamper-evident ref).
- **#544** (`2ec6ae09`, 2026-07-18): `lct.rs:180` `authority_ratchet: Option<RatchetRequirement>` — the society ratchet level, "a **provable part of the LCT**."

Both are ratified code adding structure the **frozen §2 (LCT Structure) does not enumerate**. Per the reviewer's caution and `[[feedback_prose_is_not_ledger]]` ("is it NEW before is it TRUE"), each is written as the **LCT-canonical-spec-side face of an already-open carry**, not net-new inventory:

- **C248-N1** (LOW, birth-cert SHAPE) — LCT §2.3-side face of **C23-H1** (canonical BirthCertificate shape design-Q), refreshed by #538's plural/ledger-resident reshape.
- **C248-N2** (LOW, structure enumeration) — LCT §2-structure-side face of the **#544 ratchet** question (C246-N1 is the SAL-side face of the same primitive).

**Counts**: §A — 0 spec motion; C210-N1, C172-N1/N2/N3, all C24/C60 Python+vector carries **HELD by construction**. §B — corpus-delta CLEAN (no spec LCT cites moved); Rust-mirror re-derivation yields **two routed spec-lag findings** (C248-N1, C248-N2), both refute-survived, both LOW, both routed (NOT self-applied).

---

## §A. Verification (frozen target → HELD by construction)

### A.0 — Freeze confirmation
- `git diff d89595e8..HEAD -- LCT-linked-context-token.md` → **empty**. Target byte-identical to the C210 snapshot (blob `231d70b5`). Last touch = #531 (the C210 mover). No motion, 0 HTML-entity artifacts introduced.

### A.1 — C210-N1 HELD (§1.2 "key-derived" vs §3.3 signature-preimage `lct_id`)
- §3.3 unchanged (frozen): `lct_id = "lct:web4:" + multibase32_encode(sha256(binding["binding_proof"]))` — **signature-preimage** (L289).
- Ratified Rust `derive_lct_id` unchanged: `lct.rs:361-363` = `"lct:web4:mb32:b" + base32_lower_nopad(sha256(public_key.to_bytes()))` — **key-derived**. Neither #538 nor #544 touched it.
- §1.2 (L47-50) still asserts "identifiers are key-derived … recomputed from structure — never trusted from a claimed field." The internal contradiction (§1.2 endorses key-derivation; §3.3 signature-preimages) **STANDS unchanged**. Routes into the C172-N1 reconciliation bundle; do NOT self-fix §3.3.

### A.2 — C172-N1/N2/N3 HELD
- The C172 flagship contract (`lct_id = sha256(public_key)`, verifier-reproducible pre-signing) is intact at `lct.rs:361-363`. #544/#538 are additive (new fields), leaving the derivation untouched. C172-N1/N2/N3 STAND, routed off-spec.

### A.3 — Python + vector carries HELD
- Python `lct.py` **frozen since 2026-04-17** (`759eaefa`, #162) → every C24/C60 Python+vector carry (C24-H1 lct_id form, C24-M2/M3/M4/M6, C24-L3, C60-B1 3-way vector, C60 design-Q set B2/B5/B6/B7/B8/B12/B14-req/B15/B17, sister carries B9-B13) STANDS by construction. None gate this turn.

### A.4 — Sister cross-refs (§10.2/§10.3/§10.4) re-resolve
- SAL (`web4-society-authority-law.md` `1354e4c2`, byte-frozen since #523 per C246), atp-adp (`256ab51d`), dictionary (`95d20919`), entity-types (`1354e4c2`) — all frozen at or before the C210 snapshot. LCT's §10.2 (LCT↔SAL), §10.3 (LCT↔ATP/ADP), §10.4 (LCT↔Dictionary) cross-refs target unmoved siblings → resolve. CLEAN.

---

## §B. Corpus-Delta + SDK-Mirror Re-Derivation

### B.0 — Corpus-delta since C210 (CLEAN)
- `git log --since=2026-07-17 -- web4-standard/core-spec/ ontology/`: exactly two entries — `4f76f110` (oracle consult/write sets on `RoleExtension::Scope`) and `2bc3bafb` (C214 audit doc). `4f76f110` is a role-extension data-plane edit (the "oracle-scope" lexical collision ruled DISJOINT from every trust-family predicate at SAL C246); it adds **0** LCT tokens and is not cited by LCT. **No spec file that LCT cites moved.** Corpus surface clean.

### B.1 — Rust-mirror re-derivation at live HEAD (the moved surface)
Per the method guard, the mirror set is re-derived at HEAD: Python `lct.py` (frozen), Rust `web4-core/src/lct.rs` (**moved**, #544), `attestation.rs` (**moved**, #538), `ratchet.rs` (**new dependency of #544**). The `Lct` struct now carries two fields with no §2 counterpart:
- `lct.rs:164` `pub citizenships: Vec<crate::attestation::BirthCertificateRef>` (#538)
- `lct.rs:180` `pub authority_ratchet: Option<crate::ratchet::RatchetRequirement>` (#544)

### B.2 — C248-N1 (LOW, spec-lag, ROUTED) — §2.3 singular embedded `birth_certificate` vs ratified #538 plural/ledger-resident `citizenships`
**Finding.** The frozen canonical structure embeds a **singular** birth certificate directly on the LCT:
- §2.2 Optional Components: "1. **Birth Certificate** (society-issued foundational identity)" (singular).
- §2.3 canonical JSON (L104-115): one `"birth_certificate": { issuing_society, citizen_role, birth_timestamp, birth_witnesses[], genesis_block_hash, birth_context }` object **inline on the LCT**.

Ratified #538 **reshaped** this. `attestation.rs:213-216` is explicit: the `BirthCertificateRef` is "what an LCT carries (**canon §2.3 `birth_certificate`, reshaped per dp 2026-07-16 + HUB's two flags**) … (**plurality** — see `Lct::citizenships`)." Concretely:
- **Plural**: `Lct::citizenships: Vec<BirthCertificateRef>` (an entity can be a citizen of ≥1 society) vs the spec's single embedded object.
- **Ledger-resident**: the authoritative `CitizenshipRecord` (`attestation.rs:157-167`, quorum attestations) "lives in the **birthing society's ledger, not on the** [LCT]"; the LCT carries only a tamper-evident `BirthCertificateRef` (society + ledger entry id + `CitizenshipRecord` content hash — HUB flag 1: bind content) vs the spec's full inline object.

So the ratified data model (plural, referenced, ledger-resident) diverges from the frozen §2.3 model (singular, embedded).

**Is it NEW?** The *design question* is not — this is the **LCT-canonical-spec-side face of open carry C23-H1** ("canonical BirthCertificate shape … SAL §2.2 vs entity-types extensions"), which SAL C246 refreshed with "web4-core Rust `BirthCertificate`/`CitizenshipRecord` leg + dp ledger-resident/plural ruling; still OPEN, un-reconciled w/ frozen SAL §2.2." What is fresh at C248 is the **anchor**: no prior LCT-audit-line entry has bound C23-H1 to LCT §2.3 with the #538 reshape (C210 predates #538 by hours; C172 predates it entirely). Recorded as a C23-H1 refresh at its LCT §2.3 home, not net-new inventory.

**Refute (survives).** *Is #538 just an implementation detail free to differ from a JSON example?* No — §2.2 is a normative component list and §2.3 is the canonical structure; #538's own comment frames itself as a *reshape of canon §2.3*, i.e. the ratified code asserts the spec shape is superseded, not merely realized differently. *Is the plurality already in the spec?* No — §2.2/§2.3 are singular; §4.2/§11.2 speak of "a birth certificate" throughout. The divergence is real on both axes (cardinality + residence).

**Severity/route.** LOW. Does not gate (reversible, no exploit; §11.2 validator is `# implementation-defined`, B4/C61-carried). Routes to the **C23-H1 bundle** (operator/HUB, ratified cross-impl surface): reconcile §2.2/§2.3/§4/§11.2 to the plural, ledger-resident `citizenships`/`BirthCertificateRef` shape, or record why the spec keeps the singular-embedded model. **Do NOT self-fix** (normative structure change).

### B.3 — C248-N2 (LOW, spec-lag, ROUTED) — ratified `authority_ratchet` LCT field is unenumerated in §2
**Finding.** #544 adds `lct.rs:180 pub authority_ratchet: Option<crate::ratchet::RatchetRequirement>` with the doc contract (lct.rs:173-180): "the sovereign-authority requirement … **ratchet level is a provable part of the LCT**, resolvable from the registry." §1.2 (L33-34) already names "**a society's authority ratchet**" as one of the "verifiable structures in this standard [that] is evidence a relying party weighs." But **§2 (LCT Structure) does not enumerate it**:
- §2.1 Required Components: 6 items (Identity, Binding, MRH, Policy, T3, V3) — closed MUST list, no ratchet.
- §2.2 Optional Components: 4 items (Birth Certificate, Attestations, Lineage, Revocation) — no ratchet.
- §2.3 canonical JSON: no `authority_ratchet` key.

So §1.2 *references* the concept while §2 gives it no structural home, and the ratified LCT now carries it as an optional field. The spec §2 lags **both** the ratified mirror and its own §1.2 reference.

**§1.2 fidelity (the ratchet is NOT a §1.2 violation).** `RatchetRequirement::level()` is "a **derived ordinal summary** … recomputed from `SovereignStructureProof`" (recomputed from constellation co-signatures — `ratchet.rs:44-46`), i.e. it is *recomputed from structure, not trusted from a claimed field* — exactly what §1.2 point 2 demands. The finding is purely the **§2 enumeration gap**, not a principle conflict.

**Is it NEW?** Yes at the LCT-structure line. #544 landed 2026-07-18 (after C210); it is in **no** LCT carry. C246-N1 is the **SAL-side** face of the same primitive ("should SAL §5.2/§4.2 NAME the ratchet?"); C248-N2 is the **LCT-structure-side** face ("should LCT §2.2 enumerate the `authority_ratchet` component?"). Recorded as the LCT face of that ratchet question, cross-linked to C246-N1.

**Refute (survives).** *Does §1.2's mention already cover it?* No — §1.2 is a design principle (how to treat the ratchet as evidence), not a structure definition (where the field lives on the LCT). A relying party reading §2 to construct/validate an LCT finds no ratchet slot. *Is `authority_ratchet` really on the LCT vs external?* It is a field on the `Lct` struct (`Option<>`, absent for non-sovereign LCTs), resolvable-from-registry but structurally carried — the comment says "provable part of the LCT."

**Contrast (direction).** This is the **inverse** of C176-N1 (Rust `EntityType` enum *lags* spec §2.1 → direction: extend Rust). Here Rust *extends beyond* spec §2 → direction: **spec §2.2 should enumerate the optional `authority_ratchet` component** (or the operator records the field as SDK-only/deferred).

**Severity/route.** LOW. Does not gate (optional field, §1.2-faithful, no exploit). Routes to operator/HUB (spec §2.2 addition, ratified cross-impl surface); cross-linked to C246-N1. **Do NOT self-fix.**

### B.4 — #538 birth-cert VALIDATOR / witness-quorum path is otherwise FAITHFUL
Beyond the shape divergence (N1), #538's mechanics mirror the frozen spec faithfully: `BirthCertificate::quorum_structurally_ok` + `verify_quorum` enforce the **≥3 witnesses** §4.2/§11.2 require (`attestation.rs:118-121` `birth_witnesses: Vec` "≥3, canon-required"); "absence is always the closed pole" matches §4.3/§8.1 unforgeability. So the birth-cert *substance* is a genuine mirror; only the *container shape* (N1) lags. No additional finding.

---

## §C. Carry Ledger (for the next LCT delta ~C284)

- **C248-N1 (NEW anchor, LOW, OPEN, routed)** — §2.3 singular embedded `birth_certificate` vs ratified #538 plural/ledger-resident `citizenships`; LCT §2.3 face of **C23-H1**. Route to C23-H1 bundle (operator/HUB). Do NOT self-fix. Do NOT re-discover #538 as net-new next delta.
- **C248-N2 (NEW, LOW, OPEN, routed)** — ratified `authority_ratchet` (`lct.rs:180`, #544) unenumerated in §2; §1.2 names it but §2 gives no structural home. LCT-structure face of the ratchet question (cross-link **C246-N1** SAL-side). Route to operator/HUB (§2.2 optional-component addition). §1.2-faithful (`level()` recomputed from structure). Do NOT self-fix; do NOT re-discover #544 as net-new.
- **C210-N1 HELD** (§1.2 key-derived vs §3.3 signature-preimage) — folds into C172-N1 reconciliation bundle. Do NOT self-fix §3.3.
- **C172-N1/N2/N3 STAND** (Rust key-derived contract unchanged, `lct.rs:361-363`). Routed off-spec.
- **Rust mirror growth edge** = `citizenships` (#538) + `authority_ratchet` (#544). Both now carried above (N1/N2). Re-derive both Python+Rust mirrors at the next delta before declaring §B clean.
- **All C24/C60 design-Q + C60-B1 vector carries STAND** by Python/vector freeze. None gate.
- **#531 CONSUMED** (C210) — do NOT re-open the §1.2 insertion / §1.2→§1.3 renumber.
- **Method note**: byte-frozen target ≠ frozen neighborhood — the mirror moved, and the yield came from re-deriving it at live HEAD and placing each finding as the **LCT-side face of an existing carry** (C23-H1, C246-N1) rather than net-new inventory (`[[feedback_prose_is_not_ledger]]` / `[[feedback_prior_finding_path_provenance]]`).

---

## Verdict

**Target byte-frozen since C210, regression-CLEAN; corpus-delta CLEAN.** The audit surface was the ratified Rust mirror, which grew two structural `Lct` fields after C210 — plural/ledger-resident `citizenships` (#538) and `authority_ratchet` (#544) — neither enumerated in the frozen §2. **Two net-new LOW spec-lag findings, both routed, both LCT-side faces of open carries**: C248-N1 (§2.3 singular vs plural/ledger-resident birth-cert → C23-H1) and C248-N2 (`authority_ratchet` unenumerated in §2, §1.2-faithful → cross-links C246-N1). C210-N1 + C172-N1/N2/N3 HELD. Zero autonomous spec mutation (both findings route to the operator/HUB ratified-contract bundle; the guardrail forbids the auditor rewriting §2/§3.3). Rotation advances to **ISP (`inter-society-protocol.md`) 6th delta = C250**.
