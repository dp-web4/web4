# C186 — 4th-Delta Re-Audit of `protocols/web4-lct.md` (the frozen LCT sister-doc)

**Date**: 2026-07-12
**Auditor**: Legion autonomous web4 track (slot `120036`, LEAD)
**Target**: `web4-standard/protocols/web4-lct.md` (278 lines)
**Type**: **4th-delta re-audit**. Read-only — produces this audit doc, makes **no file edits** (the file is D0-gated).
**Lineage**: C60-B13 → **C74** first audit (#363, 28 findings B1–B28) → **C75** `protocols/` cluster triage (#364) → **C114** 2nd-delta (+N1) → **C146** 3rd-delta (3.1 path correction, #491-era) → **C186**.
**Snapshot baseline**: target blob `5f68a5c7bda9b1dbcfd81f0324df61243efbaab7` — **byte-frozen since `27b85624` (2026-02-17); unchanged since C74** (verified this delta via `git rev-parse HEAD:web4-standard/protocols/web4-lct.md`). C146 corpus baseline was 2026-07-06.
**Method**: §A prior-finding persistence verification (C74 B1–B28, C75 defects 3.1/3.2, C114-N1) with the two frozen-target re-read disciplines (C56 claim-vs-canonical; C108/C112 cross-section blindspot) + live-HEAD locus re-confirmation (C146 path-provenance lesson). §B corpus-delta scan since the C146 baseline. **§B′ SDK-mirror gate** (the C178–C184 verdict ladder) applied to `web4-core/src/lct.rs`. Single refute-by-default adversarial verifier on the one substantive candidate. The 49-agent C74 finder workflow was deliberately **not** re-run (proportionality: byte-frozen target).

---

## Headline (read this first)

`protocols/web4-lct.md` is **byte-identical to its C74/C114/C146 snapshot** (blob `5f68a5c7`). §A confirms **28/28 C74 findings HELD, 0 regression**, C114-N1 HELD, and both C75 structural defects re-verified at **live HEAD** (3.1 = `web4-standard/README.md:64` present; 3.2 = `LCT-linked-context-token.md:689` present). **0 net-new internal findings** — web4-lct's substantive-clean 4th consecutive delta.

Unlike C146, the corpus-delta this cycle is **NOT empty**: the SDK mirror `web4-core/src/lct.rs` moved via PRs #499/#503/#504 and web4-core **0.3.0 published** to crates.io + PyPI 2026-07-09. Applying the SDK-mirror gate to this motion yields **one calibration, routed to the D0 packet — not a net-new defect**:

> **The sister-doc's `lct_id` derivation (`web4-lct.md:147` = `"lct:web4:" + MB32(SHA256(binding_proof))`, i.e. hash-of-the-signature) is *byte-equivalent in preimage* to canonical `LCT-linked-context-token.md:260`, and both are the stale model that C172-N1 flagged against the ratified key-derived `derive_lct_id` (`lct.rs:286`, `sha256(public_key)`).** C172-N1 was pathed to canonical §3.3/§11.1 only (C172 logged its sibling-doc surface as "0 net-new" and never cited `web4-lct.md:147`). **C186's yield is to widen C172-N1's scope to include the sister-doc line** — a provenance/scope calibration in the same class as C146's README-path correction, **not** a novel C186-N1.

**SDK-mirror gate verdict for this file: `lct.rs` is a GENUINE mirror (C172) that tracks CANONICAL's descendant, NOT the frozen sister.** The ratified key-derived id + structured `mrh` field descend from canonical §2.3, not from the sister's content-hash id model. This is **standing D0 = SUPERSEDE evidence**: the sister diverges from *both* the canonical spec and the direction the shipped/ratified code is moving.

**Two honesty caveats (from adversarial verification):**
1. **No published-SDK contradiction.** The key-derived `derive_lct_id` is **HEAD-only / unreleased**: the published tag `web4-core-rust-v0.3.0` (2026-07-09) carries `lct.rs` at 368 lines with **no `derive_lct_id`** (only a `fingerprint()` helper). The sister-vs-key divergence is against **ratified HEAD**, not against published 0.3.0.
2. **No net-new normative floor inside the sister.** `web4-lct.md:147` is *pseudocode*; the widened scope inherits C172-N1's MED severity via canonical §11.1 `verify_binding_proof`'s **MUST**, not via anything binding in the sister-doc itself.

**D0 remains operator-unanswered and gates all remediation. Nothing here edits any file or re-decides D0.**

---

## §A — Prior-finding verification

### A.1 — C74 findings (B1–B28): 28/28 HELD, 0 regression
The target blob is byte-identical to the C74/C114/C146 snapshot (`5f68a5c7`), so all line-anchored findings hold by construction. Spot-re-verified the load-bearing ones token-for-token at HEAD: **B1** (§1 JSON still does not close), **B7** (`entity_type` = 12 vs canonical 15 — canonical `entity-types.md` frozen C65 `5baa160f`), **B8** (`t3_tensor`/`v3_tensor` absent; canonical frozen C61 — and note `lct.rs` *also* omits tensor fields, so this is not a sister-only gap), **B9** (birth-cert shape divergence), **B13/B14/B15** (identifier model — see §B′), **B16** (SAL `Web4BirthCertificate`; SAL frozen C59 `0d756773`), **B25** (§1 "COSE Sig" vs §3 signing scope). No remediation has landed (D0-gated) → §A is pure persistence verification. The 5 C74-refuted items remain correctly refuted.

### A.2 — C75 structural defects — both HELD, loci re-confirmed at live HEAD
Per C146's path-provenance lesson, both defects were re-verified against **live HEAD bytes**, not carried from snapshot text:

| C75 defect | C146 corrected locus | C186 verification at HEAD | Disposition |
|------------|----------------------|---------------------------|-------------|
| **3.1 README SSOT inversion** | `web4-standard/README.md:64` | `sed -n '64p'` → `- [**protocols/web4-lct.md**](protocols/web4-lct.md) - Linked Context Token specification`. Present verbatim; `web4-standard/README.md` frozen `27b85624`. | **HELD — REAL** at the C146-corrected sub-README locus. Root `README.md` still routes to canonical (no regression). |
| **3.2 Canonical-defers-to-frozen** | `LCT-linked-context-token.md:689` | `sed -n '689p'` → `- **LCT Protocol Details**: \`protocols/web4-lct.md\``. Canonical frozen C61. | **HELD — REAL.** Exact line 689 confirmed. |

### A.3 — C114-N1 (internal `claims` cross-section contradiction): HELD
Byte-frozen → holds by construction. §2.6 "Attestation Fields" enumerates four fields with no `claims`; §6.1 carries a "Required Claims" column mandating per-class members. The two normative halves remain inconsistent. N1 stays **blocked-on-D0 / queued-for-the-maintain-path** (not self-applied).

### A.4 — C56 claim-vs-canonical re-read
Every cited canonical source is frozen at or before C146's baseline (canonical LCT C61 2026-06-15, entity-types C65 2026-06-16, SAL C59 2026-06-15, witnessing 2025-09-14), so no B-line cross-doc claim went stale on the *doc* surface. The one moving source is the **Rust SDK** (§B/§B′).

---

## §B — Corpus-delta scan (net-new from moving mirrors)

### B.1 — Corpus-delta surface since C146 (2026-07-06): the SDK mirror MOVED

| Referent / sibling | last commit | moved since C146 baseline (2026-07-06)? |
|--------------------|-------------|------------------------------------------|
| `protocols/web4-lct.md` (target) | `27b85624` 2026-02-17 | **no** (byte-frozen, blob `5f68a5c7`) |
| `core-spec/LCT-linked-context-token.md` | `9d1933f8` 2026-06-15 | no |
| `core-spec/entity-types.md` | `5baa160f` 2026-06-16 | no |
| `web4-standard/README.md` (3.1 locus) | `27b85624` 2026-02-17 | no |
| `core-spec/…:689` back-pointer (3.2 locus) | frozen C61 | no |
| **`web4-core/src/lct.rs` (SDK mirror)** | **`81788f35` 2026-07-10** | **YES — #499/#503/#504** |

Every *doc* on the divergence/inbound surface is frozen. The **only** motion is the Rust mirror — which is exactly the SDK-mirror-GROWS surface the delta method exists to catch. **That motion was already audited by C172** (2026-07-10, the canonical-LCT 4th delta). C186's job is to check whether any of it lands a *web4-lct-scoped* finding C172 did not path here.

### B.2 — Cross-section blindspot sweep: no new internal contradiction
Re-ran the §6-vs-§2.6/§1 cross-section comparison that produced C114-N1, extended to §2.7/§2.8 vs §1 inline examples. All internal contradictions reduce to already-recorded B2–B5 / N1. **0 net-new internal findings.**

---

## §B′ — SDK-mirror gate (the C178–C184 verdict ladder), applied to `lct.rs`

**Gate step 1 — is `lct.rs` a genuine mirror of this file's subject?**
Verdict: **GENUINE** (established C172/C176). `lct.rs` implements the LCT primitive with `EntityType`, `binding_proof`, key-derived `lct_id`, and a structured `Mrh` field. It cites **canon §2.3** in its doc-comments (`lct.rs:118` "canon §2.3", `lct.rs:284` "canon §2.3"). It mirrors the **canonical** `LCT-linked-context-token.md`, which is `web4-lct.md`'s divergence counterparty — so it is a *live second witness* to the sister-vs-canonical gap.

**Gate step 2 — does the mirror track the frozen sister or canonical?**
**Canonical.** The three axes on which the sister diverges from canonical (C74 B7/B8/B9/B13) all resolve *toward canonical* in `lct.rs`:

| Axis | Sister `web4-lct.md` | Canonical | `lct.rs` (ratified HEAD) | Mirror tracks |
|------|----------------------|-----------|--------------------------|---------------|
| `lct_id` preimage | `MB32(SHA256(binding_proof))` — signature (`:147`) | `mb32(sha256(binding["binding_proof"]))` — signature (`:260`) | `sha256(public_key.to_bytes())` — **key** (`:286`) | *neither* (see below) |
| `mrh` as structured field | absent (prose only) | canon §2.3/§5 | present `Mrh {bound,paired,witnessing}` (`:132,148`) | canonical |
| entity types | 12 | 15 | 8 (7/15 + `Hybrid`; C176) | canonical direction (superset intent) |
| tensors | absent | required | absent | — (canonical-lag, C172/C180 scope) |

**The `lct_id` axis is the load-bearing one and it is a C172 carry, not a C186 finding.** Sister `:147` and canonical `:260` are **byte-equivalent in preimage** (both hash the signature). C172-N1 flagged that *both* are stale vs the ratified key-derived `derive_lct_id` — but C172 pathed it to `LCT-linked-context-token.md §3.3/§11.1` only and logged its sibling-doc surface as "0 net-new," never citing `web4-lct.md:147`.

**C186 disposition (prose-is-not-ledger self-catch):** the sister `:147` divergence is **the sister-doc-scoped instance of C172-N1, routed as a SCOPE-WIDENING**, not a novel C186-N1. This is the [[feedback_prose_is_not_ledger]] discipline working: the candidate *looked* net-new (a fresh sister-vs-code contradiction), but "is it NEW?" resolved before "is it TRUE?" — C172-N1 already owns the preimage divergence; C186 only adds the un-pathed sister line to its coverage.

**Honesty caveats (adversarially verified, refute-by-default → CONFIRMED):**
1. **HEAD-only, not published.** `derive_lct_id` is absent from the published tag `web4-core-rust-v0.3.0` (2026-07-09): that tag's `lct.rs` is 368 lines with only a `fingerprint()` helper. The sister-vs-key divergence is against **ratified HEAD** (0.4.0-material), not published 0.3.0. Do not claim "the published SDK contradicts the sister."
2. **No normative floor inside the sister.** `:147` is pseudocode; the widened scope inherits C172-N1's **MED** severity via canonical §11.1 `verify_binding_proof`'s MUST, not via anything binding in `web4-lct.md`.

**Verdict ladder placement for `lct.rs` vs `web4-lct.md`:** GENUINE mirror, **tracking canonical away from the frozen sister** → this is **corroborating D0 = SUPERSEDE evidence** (the code follows canonical's line; the sister is diverging from both the spec and the shipped direction). It is *not* a new defect against the sister.

---

## §C — Routing

### D0 — FLAGSHIP DESIGN-Q (operator; UNCHANGED, still gates everything)
**Is `protocols/web4-lct.md` a maintained sister-doc, or superseded by canonical `core-spec/LCT-linked-context-token.md`?** Operator-unanswered. Auditor recommendation remains **SUPERSEDE** — now with a **third independent witness**: beyond (a) canonical's structural divergence (B7/B8/B9) and (b) canonical `:689` deferring to the frozen sister while the sub-README `:64` routes to it, C186 adds (c) **the ratified Rust SDK `lct.rs` implements canonical's descendant (key-derived id, structured `mrh`), moving further from the sister with every cycle.** **No remediation may touch this file until D0 resolves.**
- If D0 = **SUPERSEDE**: deprecation/SSOT banner on `web4-lct.md` + fix `web4-standard/README.md:64` to link canonical + delete canonical `LCT-linked-context-token.md:689` deferral. N1 and all B-line items become moot.
- If D0 = **MAINTAIN**: the C74 autonomous list + N1 + the B25 COSE_Sign1 sharpening + **the C172-N1 key-derived-id update (now covering `web4-lct.md:147`)** define the remediation.

### This delta's deliverable — routed, NOT self-applied
**C172-N1 SCOPE-WIDENING:** the signature-derived `lct_id` preimage divergence C172-N1 recorded against canonical `LCT-linked-context-token.md:260` (§3.3 step 4) **also covers the frozen sister `protocols/web4-lct.md:147`** (byte-equivalent preimage). Under D0 = MAINTAIN this line joins the canonical §3.3 update; under D0 = SUPERSEDE it is moot. HEAD-only caveat noted (absent from published 0.3.0). No file is edited by this audit.

### Carries — UNCHANGED (re-confirmed open)
D0 (flagship); C114-N1 (blocked-on-D0); **C172-N1 (MED, now covering sister `:147`)**; identifier-model design-Q (B13/B14/B15, couples C60-H1 and now widened C24-H1); revocation propagation / future-timestamp (B26/B27); REQUIRED-vs-OPTIONAL presence (B10); cross-track to SAL (B16/B18), witnessing registry (B17), registries-canonicity (B19). The 6 other `protocols/` sisters remain triaged-not-audited per C75 while D0 pends.

---

## §D — Method notes (for the next AUDIT turn)

1. **The prose-is-not-ledger self-catch fired again — and correctly.** The lct_id signature-vs-key divergence *presented* as a fresh sister-vs-code defect worth a C186-N1. Asking "is it NEW?" before "is it TRUE?" ([[feedback_prose_is_not_ledger]]) surfaced that C172-N1 already owns the preimage divergence (pathed to canonical, sibling surface logged "0 net-new"). The honest output is a **scope-widening of an existing carry**, not a manufactured net-new finding. A delta that finds "the mirror moved" is not automatically a delta with a net-new finding — check the sibling audit that *audited that same motion* first ([[feedback_cross_doc_carry_inbound]]).
2. **Refute-the-best-finding caught two over-claims.** The adversarial verifier confirmed the disposition but corrected (a) "published SDK contradicts sister" → HEAD-only, absent from tag `web4-core-rust-v0.3.0`; (b) the widening does not create a normative floor inside the sister (pseudocode-only; MED inherited via canonical's §11.1 MUST). Baseline the "is it shipped?" claim on the **published tag**, not HEAD ([[feedback_refute_your_best_finding]] / [[feedback_enumeration_and_grep_hypotheses]]).
3. **SDK-mirror gate can adjudicate a DESIGN-Q's direction.** For a supersede-vs-maintain question, "which way is the ratified code moving?" is load-bearing evidence: `lct.rs` tracking canonical (not the frozen sister) is a third SUPERSEDE witness. The gate is not only a genuine/false/absent/divergent classifier — for a frozen parallel spec it also **votes on D0**.
4. **Frozen ≠ clean, confirmed a fifth time on this file** (C108/C112/C114/C146, now C186). Byte-frozen target + this cycle a *non-empty* corpus-delta (the SDK moved) still yielded no net-new defect — only a carry-scope calibration — because the moving mirror had already been audited by its own-file delta (C172).
5. **Snapshot baseline recorded** (target blob `5f68a5c7`, unchanged; `lct.rs` at `81788f35`) so the next delta detects motion in one `git rev-parse`. Note: whichever pass next reaches **canonical LCT** (the "LCT" rotation slot) owns C172-N1's remediation; this file only inherits it under D0 = MAINTAIN.

---

*C186 makes no file edits and settles no design question. It verifies the C74/C75/C114/C146 snapshot held byte-for-byte (28/28 + N1 + 3.1@`web4-standard/README.md:64` + 3.2@`:689`), and — on a non-empty corpus-delta (the Rust mirror `lct.rs` moved via #499/#503/#504, 0.3.0 published) — applies the SDK-mirror gate to find that `lct.rs` is a GENUINE mirror tracking CANONICAL away from the frozen sister (a third D0 = SUPERSEDE witness), while the one candidate finding (sister `:147` signature-derived `lct_id`) resolves to a SCOPE-WIDENING of the existing C172-N1 carry, not a net-new defect. 0 net-new internal. D0 still gates every remediation.*
