# C210: LCT-linked-context-token.md 5th-Delta Re-Audit (6th delta overall)

**Date**: 2026-07-17
**Auditor**: Autonomous session (legion-web4-20260717-120036)
**Document**: `web4-standard/core-spec/LCT-linked-context-token.md` (721 lines, HEAD `231d70b5` — **MOVED since C172** via #531)
**Prior audits**: C9 (8 → #225) → C24 (12 NEW → #256) → **C60** (21 → #338) → **C61 remediation** (`9d1933f8` #338: 9 autonomous) → **C100** (`75b808ef` #388: 0 net-new) → **C135** (`e325004f` #450: 0 net-new) → **C172** (`9d1933f8`, byte-frozen: 3 Rust-mirror net-new, all routed).
**Spec mutations since C172**: **1** — #531 (`d89595e8`, 2026-07-16). This is the **first non-frozen LCT delta since the C61 remediation** (~31 days of freeze broken).

---

## Framing — a genuine mover, regression-checked; the delta is CLEAN on every mechanical axis with ONE net-new internal-consistency finding

C100/C135 were clean frozen-target deltas; C172 broke the streak on the *Rust* SDK mirror (out of prior scope). **C210 is different again**: the spec file itself **moved** for the first time since C61. #531 inserted a **NEW normative §1.2 "Design Principle: Inspectable Evidence, Not Prescribed Trust"** (RFC-2119, two MUSTs) and **renumbered** the old `### 1.2 Terminology` → `### 1.3`. Per `[[feedback_remediation_introduced_regression]]`, the mover is regression-checked against four failure modes: (a) renumber orphaning a cross-reference; (b) the new §1.2 conflicting with existing normative text; (c) the referenced tri-surface (T3/V3 §1.1, README #9, CLAUDE.md) landing inconsistently; (d) §1.2 itself smuggling the very threshold it disclaims.

Result: **(a) CLEAN, (b) ONE net-new internal tension found (C210-N1), (c) CLEAN, (d) REFUTED.**

**Counts**:
- **§A**: #531 diff is a **pure insertion** (1 removed line = old `### 1.2 Terminology` header; 25 added). Frozen body (L1–25, L55+) byte-identical to C61 `9d1933f8` → 9/9 C61 remediations **HELD by construction**; witness floor ≥3 uniform; 0 HTML artifacts. Python `lct.py` frozen since C135 → all C24/C60 Python+vector carries **STAND**. Rust `lct.rs` moved additively (#527/#516) since C172 → C172-N1/N2/N3 **STAND** (mirror-tracking note below).
- **§B**: renumber orphan-sweep (in-file + corpus) **CLEAN**; sister tri-surface **CLEAN**; flagship §1.2-smuggles-a-threshold charge **REFUTED**. **1 net-new finding: C210-N1** (LOW-MED, internal-consistency, routed — reinforces carried C172-N1).

---

## §A. Verification

### A.0 — Mover characterization (pure insertion)
- `git diff 9d1933f8 HEAD -- LCT-linked-context-token.md`: **1** removed line (the `### 1.2 Terminology` header), **25** added (the new §1.2 block + the `### 1.3 Terminology` header). No pre-existing normative line was altered or deleted. The frozen body is intact.
- HTML-entity / `&#` / `&amp;` sweep → **0 hits**.

### A.1 — The 9 C61 autonomous remediations (9/9 HELD by construction)
Because the mover touched nothing outside the §1.2 insertion, every C61 remediation anchor re-verifies verbatim at live HEAD:
- A2 composite "CAN exceed 1.0" — L435/L439/L457 present verbatim (V3 valuation `0.0+`, `composite_score` note, pathological-case design-Q).
- B4 §11.2 impl-defined helper semantics — L639–643 present (`validate_t3_tensor` / `validate_v3_tensor` / `verify_binding_proof` all `# implementation-defined`).
- B3 §11.2 society-membership carve — L330 present ("enforcement is implementation-defined; the §11.2 reference validator … does not currently verify society membership").
- B18/B19 (blockchain-anchor RECOMMENDED; future-timestamp advisory) — L577 present.
- A1/B5/B14/B16 anchors unmoved (frozen body). **9/9 HELD.**

### A.2 — Binding-condition re-checks
- **Witness-floor uniformity (≥3)**: `minimum 2` / `two witness` / `>= 2` / `at least 2 witness` → **0 hits**. Floor uniform. Condition satisfied.

### A.3 — Carried items re-confirmed OPEN (all STAND)
- Python SDK `lct.py` **frozen since C135** (`git log` empty) + birth-cert vector frozen → every C24/C60 Python+vector carry STANDS by construction: C24-H1 (lct_id form), C24-M2/M3/M4/M6, C24-L3, C60-B1 (vector 3-way), C60 design-Q set (B2/B5/B6/B7/B8/B12/B14-req/B15/B17) and sister-doc carries (B9/B10/B11/B13). None gate this turn.
- **Rust `lct.rs` moved additively since C172** — #527 (`e8f313e4` birth-certificate + attestation schema, Phase-2 groundwork), #516 (`fed64b51` `EntityType::Society` + v0.4.0). The C172 flagship contract is **unchanged**: `derive_lct_id(public_key) = "lct:web4:mb32:b" + base32(sha256(public_key.to_bytes()))` (`lct.rs:306–308`) — still **key-derived from the public key**, verifier-reproducible pre-signing. So **C172-N1/N2/N3 STAND**. #527/#516 are additive mirror expansion (see A.4), not a new spec regression.

### A.4 — Rust-mirror movement (watch-item, not a net-new spec defect)
- #527 birth-certificate/attestation schema is **Phase-2 groundwork** (independently flagged "deferred with watch" in `whitepaper/PUBLISHER_CONTEXT.md` 2026-07-16). It moves the Rust mirror *toward* spec §11.2's birth-cert validator shape, not away from it. No spec text regresses.
- #516 `EntityType::Society` aligns with `entity-types.md §2.1` (15-type taxonomy, referenced from the new §1.3). No divergence introduced.
- **Carry**: at the next LCT delta, re-derive both mirrors (Python `lct.py` AND `web4-core/src/lct.rs`) at live HEAD before declaring §B clean — the birth-cert schema is the live growth edge (`[[feedback_prose_is_not_ledger]]`: this note IS the ledger entry, do not re-discover #527 as net-new).

---

## §B. Corpus-Delta Surface — the #531 mover

### B.1 — Renumber orphan-sweep (CLEAN)
Old `### 1.2 Terminology` → `### 1.3 Terminology`. Checked every `§1.2` reference for a now-stale pointer at LCT's Terminology:
- **In-file**: the only `1.2` hits besides the two headers (L26/L55) are `§11.2` references (L330/L553/L655) — unrelated. No self-reference to "§1.2 Terminology" exists. **No orphan.**
- **Corpus-wide**: every other `§1.2` reference points at a **different document's** §1.2 — `SOCIETY_SPECIFICATION.md §1.2/§1.2.x` (from ISP, web4-society-authority-law, entity-types, society.py), and `data-formats.md §1.2` (from security.py). **None** targeted LCT's Terminology. **No orphan.**
- **Positive confirmation**: the three pointers that *do* target LCT §1.2 — `README.md:163` (Key Innovation #9), `t3-v3-tensors.md:16`, `CLAUDE.md:192` — all intend the **new** Inspectable-Evidence §1.2 and resolve correctly. The renumber left every consumer pointing where it means to.

### B.2 — Sister tri-surface landing (CLEAN)
- **README #9**: inserted as `### 9. Inspectable Evidence, Not Prescribed Trust` (L162) with the tail correctly renumbered — `### [1..12]` is sequential with **no duplicate `### 9.`**; Value as Energy = 10, Semantic Interoperability = 11, Spatial Web = 12 (L165/168/171). The mesh-review dup-`### 9.` defect the commit's second patch fixed is **confirmed resolved**.
- **T3/V3 §1.1**: `t3-v3-tensors.md:16` — one-line cross-ref present ("Tensors are **evidence, not verdicts** … See the LCT spec §1.2"). Consistent with §1.2's tensor example (line 33). Landed.
- **CLAUDE.md §accountability**: L192 "Inspectable evidence, not prescribed trust (LCT spec §1.2)" — operational sharpening beside the RWOA self-audit. Consistent.

### B.3 — Flagship refute: does §1.2 smuggle the threshold it disclaims? (REFUTED)
§1.2's two RFC-2119 clauses are **prohibitions against prescribing trust**, not prescriptions:
- Point 1: weak evidence **MUST NOT be excluded by the protocol** (a ban on protocol-level exclusion — the opposite of a threshold).
- Point 2: a surface **MUST NOT encode a universal trust threshold** (an explicit ban on thresholds).
Neither MUST fixes a trust level; both forbid the standard from rendering a verdict, deferring who/when/how-much to the relying party scaled to stakes. §1.2 does **not** smuggle a threshold. **Charge REFUTED** — consistent with the same §1.2 candidate being refuted against *other* docs at C204 (dict 0.95 = witness-trigger) and C206 (metabolic §5 = rate modulation, not admit/exclude gate). This is its home doc, and it is internally consistent with the principle it states.

### B.4 — C210-N1 (LOW-MED, internal-consistency, routed) — §1.2 "key-derived" contradicts §3.3's signature-preimage `lct_id`
**Finding.** The new §1.2 (line 49) asserts, as a normative parenthetical, that "**identifiers are key-derived**, proofs are signature-checked, quorums … are recomputed from structure — never trusted from a claimed field." The contrast is deliberate: it buckets **identifiers with keys**, explicitly distinct from signature-checking. But the pre-existing §3.3 Binding Algorithm (L286→L289) computes:
```
binding["binding_proof"] = cose_sign1(private_key, binding_cbor)   # the SIGNATURE
lct_id = "lct:web4:" + multibase32_encode(sha256(binding["binding_proof"]))   # derived from the signature
```
i.e. `lct_id` is derived from the **COSE signature (binding_proof)**, not from the key. #531 therefore introduced a **spec-internal contradiction**: §1.2 (new, normative) places identifiers in the "key-derived" bucket, while §3.3 (existing, normative) derives them from the signature.

**Why this is net-new and not a re-discovery.** The underlying §3.3-vs-ratified-contract divergence is the *carried* **C172-N1** (spec §3.3 signature-preimage vs Rust #499 pubkey-preimage `sha256(public_key)`, `lct.rs:306–308`, pinned test vector). What is **net-new at C210** is that #531 added a canonical principle statement that §3.3 now contradicts *internally* — and that principle **endorses the ratified Rust key-derivation over the spec's own §3.3**. Previously the argument for reconciling §3.3 was only spec-vs-SDK; now it is **spec-vs-spec**. The finding (internal contradiction) is new; the remediation route is the same as C172-N1, now reinforced.

**Adversarial refutation attempted (fails).** *Could "key-derived" loosely include signature-derivation, since the binding_proof is signed by the private key?* No: (1) §1.2 deliberately separates "key-derived" (identifiers) from "signature-checked" (proofs) — a signature-preimage id straddles the wrong bucket; (2) §1.2 point 2's whole thrust is "recomputed from structure … never trusted from a claimed field," and a signature-preimage id is **not** reproducible from structure until after signing and changes on re-sign — undercutting the very invariant §1.2 asserts; (3) the ratified cross-impl contract derives from the pubkey precisely so any verifier can re-derive from the document's own binding key pre-signing. §1.2's principle is **satisfied** by Rust's key-derivation and **violated** by §3.3's signature-preimage. The tension is real.

**Severity**: LOW-MED. Does **not** gate — it is a doc-consistency + carried-SDK-divergence item, not a live exploit. Reversible, low immediate stakes; but it is a normative self-contradiction in the flagship identity primitive, so it should not sit indefinitely.

**Route (NOT self-applied — guardrail: no spec-normative rewrite by the auditor)**: fold into the **C172-N1 reconciliation bundle** — reconcile spec §3.3/§11.1's `lct_id` derivation to the ratified key-derived contract (`sha256(public_key)`, verifier-reproducible pre-signing), which simultaneously (a) resolves the C210-N1 internal contradiction, (b) closes the C172-N1 spec-vs-SDK divergence, and (c) aligns the spec with the pinned #499 cross-impl test vector. Operator/HUB-track decision (touches a ratified cross-implementation contract), same owner as C172-N1. Until then, §1.2 stands correct and §3.3 is the stale side.

---

## §C. Carry Ledger (for the next LCT delta)

- **C210-N1 (NEW, LOW-MED, OPEN, routed)** — §1.2 "key-derived" vs §3.3 signature-preimage `lct_id`; folds into C172-N1 reconciliation bundle. Do NOT self-fix §3.3 (normative, ratified-contract-touching).
- **C172-N1/N2/N3 STAND** (Rust-mirror divergence; `lct.rs` key-derived contract unchanged). Routed off-spec.
- **Rust birth-cert schema (#527) is the live mirror growth edge** — Phase-2 groundwork, "deferred with watch"; re-derive both mirrors at the next delta. Do NOT re-discover #527 as net-new.
- **#531 is CONSUMED (regression-CLEAN)** — do NOT re-open the §1.2 insertion or the §1.2→§1.3 renumber as net-new at the next delta; the renumber orphaned nothing and the sister tri-surface landed clean.
- **All C24/C60 design-Q + C60-B1 vector carries STAND** by Python/vector freeze. None gate.
- **Method note**: this was the first non-frozen LCT delta since C61; the yield came from regression-checking the mover (`[[feedback_remediation_introduced_regression]]`) and from the mover *sharpening a carried finding into an internal contradiction* — "is it NEW before is it TRUE" placed C210-N1 correctly as new-contradiction / carried-route (`[[feedback_prose_is_not_ledger]]`).

---

## Verdict

**#531 regression-CLEAN**: pure insertion, renumber orphaned nothing, sister tri-surface consistent, §1.2 flagship-charge REFUTED. **One net-new internal-consistency finding (C210-N1, LOW-MED, routed)** surfaced *by* the mover: §1.2's normative "identifiers are key-derived" contradicts §3.3's signature-preimage `lct_id`, reinforcing the carried C172-N1 reconciliation route with a spec-internal argument. Zero autonomous spec mutation this turn (C210-N1 routes to the operator/HUB-track ratified-contract bundle; the guardrail forbids the auditor rewriting §3.3). Rotation advances to **ISP (`inter-society-protocol.md`) 5th delta = C212**.
