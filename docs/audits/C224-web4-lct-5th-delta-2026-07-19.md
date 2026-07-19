# C224 — 5th-Delta Re-Audit of `protocols/web4-lct.md` (the frozen LCT sister-doc)

**Date**: 2026-07-19
**Auditor**: Legion autonomous web4 track (slot `060036`, LEAD)
**Target**: `web4-standard/protocols/web4-lct.md` (278 lines)
**Type**: **5th-delta re-audit**. Read-only — produces this audit doc, makes **no file edits** (the target is D0-gated).
**Lineage**: C60-B13 → **C74** first audit (#363, 28 findings B1–B28) → **C75** `protocols/` cluster triage (#364) → **C114** 2nd-delta (+N1) → **C146** 3rd-delta (3.1 path correction) → **C186** 4th-delta (C172-N1 scope-widening) → **C224**.
**Snapshot baseline**: target blob `5f68a5c7bda9b1dbcfd81f0324df61243efbaab7` — **byte-frozen since `27b85624` (2026-02-17); unchanged since C74/C114/C146/C186** (verified this delta via `git rev-parse HEAD:web4-standard/protocols/web4-lct.md` = `5f68a5c7`). C186 corpus baseline was 2026-07-12.
**Method**: §A prior-finding persistence verification (C74 B1–B28, C75 3.1/3.2, C114-N1) with the two frozen-target re-read disciplines (C56 claim-vs-canonical; C108/C112 cross-section blindspot) + **live-HEAD locus re-confirmation** (C146 path-provenance lesson — this cycle it fired). §B corpus-delta scan since the C186 baseline. **§B′ SDK-mirror gate** (the C178–C222 verdict ladder) applied to the heavily-moved `web4-core/src/lct.rs` and the new on-subject module `attestation.rs`. Single refute-by-default adversarial verifier on the one substantive candidate. The 49-agent C74 finder workflow was deliberately **not** re-run (proportionality: byte-frozen target — same call as C186).

---

## Headline (read this first)

`protocols/web4-lct.md` is **byte-identical to its C74/C114/C146/C186 snapshot** (blob `5f68a5c7`). §A confirms **28/28 C74 findings HELD, 0 regression**, C114-N1 HELD, and both C75 structural defects re-verified at **live HEAD**. **0 net-new internal findings** — web4-lct's substantive-clean **5th consecutive** delta.

This cycle the corpus moved **more than any prior web4-lct delta**: the SDK mirror `web4-core/src/lct.rs` grew **368 → 1114 lines** (#527 attestation schema, #538 citizenship-as-references, #540 operational-key vouching, #544 authority_ratchet-on-LCT), two new on-subject modules landed (`attestation.rs` #527/#538, `ratchet.rs` #529), and the **canonical** LCT spec moved via #531 ("Inspectable Evidence, Not Prescribed Trust"). Applying the delta method to all of this yields **two routed calibrations and a strengthened D0 recommendation — no net-new sister defect**:

> **(1) 3.2 locus correction (C146-class provenance calibration).** #531 inserted §1.2 into canonical `LCT-linked-context-token.md`, renumbering it. The C75-defect-3.2 back-pointer (canonical → frozen sister) that C186 recorded at `LCT-linked-context-token.md:689` now lives at **`:718`**. The defect is **HELD-REAL** (canonical still defers `- **LCT Protocol Details**: \`protocols/web4-lct.md\``); only the audit-recorded line number was stale. Updated here, not a regression.

> **(2) C114-N1 gains a live second witness — routed as scope-widening, not net-new.** The shipped, ratified `attestation::Attestation` struct carries **exactly the four §2.6 fields** (`witness`, `type`, `ts`, `sig`) and **no `claims`**; its signature preimage (`Attestation::message` = `subject_id + type + ts`) omits claims too, and `AttestationType` is a **payload-free enum** of the seven §6.1 classes. So the code implements the §2.6 four-field model + the §6.1 class *taxonomy* while **dropping the §6.1 "Required Claims" column and the §6.2 `claims:{}` object entirely**. This is a live vote on the direction of C114-N1's internal §2.6-vs-§6.1 contradiction — it belongs to C114-N1's scope, sharpening it, not a novel C224-N1.

**SDK-mirror gate verdict for this file: `lct.rs` + `attestation.rs` are a GENUINE, on-subject mirror that tracks CANONICAL's descendant, moving further from the frozen sister every cycle.** This is **a 4th independent D0 = SUPERSEDE witness** (after C186's three): the birth-certificate model is now concrete and *plural/reference-based* (`citizenships: Vec<BirthCertificateRef>`, #538), the LCT now carries an `authority_ratchet` field (#544) and operational-key vouching (#540) — surfaces the frozen sister has no counterpart for. The shipped code follows canonical's line; the sister diverges from both the spec and the shipped direction.

**Honesty caveats (adversarially verified):**
1. **HEAD-only, not published.** The concrete `attestation.rs`/`citizenships`/`authority_ratchet` surface is ratified HEAD (0.4.x-material), **not** in the published crate. Do not claim "the published SDK contradicts the sister."
2. **No net-new normative floor inside the sister.** Both calibrations attach to existing carries (3.2 = C75 defect; the claims witness = C114-N1). `:147`-class pseudocode carries no binding MUST of its own.

**D0 remains operator-unanswered and gates all remediation. Nothing here edits any file or re-decides D0 or the flagship B-D1.**

---

## §A — Prior-finding verification

### A.1 — C74 findings (B1–B28): 28/28 HELD, 0 regression
The target blob is byte-identical to the C74/C114/C146/C186 snapshot (`5f68a5c7`), so all line-anchored findings hold by construction. Spot-re-verified the load-bearing ones token-for-token at HEAD:
- **B1** (§1 JSON still does not close) — HELD.
- **B7** (`entity_type` = 12 vs canonical 15) — HELD; canonical `entity-types.md` frozen C65 `5baa160f`. (Note: `lct.rs::EntityType` now includes `Society` #516 — still tracking canonical's superset direction, not the sister's 12.)
- **B8** (`t3_tensor`/`v3_tensor` absent) — HELD; and `lct.rs` *still* omits tensor fields (canonical-lag, C172/C180 scope), so this is not a sister-only gap.
- **B9** (birth-cert shape divergence) — HELD; see §B′ (the SDK now has a *concrete, plural-reference* birth-cert model — a fresh SUPERSEDE witness, not a new sister defect).
- **B13/B14/B15** (identifier model — signature-hash `lct_id`) — HELD; see §B′.
- **B16** (SAL `Web4BirthCertificate`; SAL frozen C59 `0d756773`) — HELD.
- **B25** (§1 "COSE Sig" vs §3 signing scope) — HELD.
No remediation has landed (D0-gated) → §A is pure persistence verification. The 5 C74-refuted items remain correctly refuted.

### A.2 — C75 structural defects — both HELD; 3.2 locus CORRECTED at live HEAD
Per C146's path-provenance lesson, both defects were re-verified against **live HEAD bytes**, not carried from snapshot text. **This cycle the discipline fired: the 3.2 locus moved.**

| C75 defect | C186 recorded locus | C224 verification at HEAD | Disposition |
|------------|---------------------|---------------------------|-------------|
| **3.1 README SSOT inversion** | `web4-standard/README.md:64` | `sed -n '64p'` → `- [**protocols/web4-lct.md**](protocols/web4-lct.md) - Linked Context Token specification`. Present verbatim; `README.md` frozen `27b85624`. | **HELD — REAL** at the same sub-README locus. Root `README.md` still routes to canonical (no regression). |
| **3.2 Canonical-defers-to-frozen** | `LCT-linked-context-token.md:689` (C186) | `grep -n "protocols/web4-lct.md"` → **`:718`** `- **LCT Protocol Details**: \`protocols/web4-lct.md\``. Line **shifted 689→718** because #531 (`d89595e8`, 2026-07-16) inserted §1.2 "Inspectable Evidence" into canonical (694→726 lines). | **HELD — REAL** (canonical still defers to the frozen sister). **Audit-recorded locus updated 689→718.** A C146-class provenance calibration, not a regression. |

### A.3 — C114-N1 (internal `claims` cross-section contradiction): HELD (+ live SDK witness, §B′)
Byte-frozen → holds by construction. §2.6 "Attestation Fields" (L107) enumerates four fields (`witness`/`type`/`sig`/`ts`) with **no** `claims`; §6.1 (L221) carries a "Required Claims" column mandating per-class members, and §6.2 (L237) shows a `claims:{}` object. The two normative halves remain inconsistent. **New this cycle:** the shipped SDK votes on the resolution direction (§B′) — routed as a C114-N1 scope-widening. N1 stays **blocked-on-D0 / queued-for-the-maintain-path** (not self-applied).

### A.4 — C56 claim-vs-canonical re-read
Every cited canonical *doc* source is frozen at or before C186's baseline (entity-types C65 2026-06-16, SAL C59 2026-06-15, witnessing 2025-09-14) — **except** canonical `LCT-linked-context-token.md`, which moved via #531 (§1.2 insert + renumber). That motion (a) shifted the 3.2 back-pointer (A.2, corrected) and (b) canonized "Inspectable Evidence, Not Prescribed Trust" at `:26`. The frozen sister has **zero** `prescrib|threshold|inspectable` tokens → #531's principle has no sister surface to contradict → **DISJOINT, inbound-consumed by C210** (the canonical-LCT 5th delta that audited #531). No B-line cross-doc claim went stale on the doc surface.

---

## §B — Corpus-delta scan (net-new from moving mirrors)

### B.1 — Corpus-delta surface since C186 (2026-07-12): the SDK mirror moved HARD; one canonical doc moved

| Referent / sibling | last commit | moved since C186 baseline? |
|--------------------|-------------|----------------------------|
| `protocols/web4-lct.md` (target) | `27b85624` 2026-02-17 | **no** (byte-frozen, blob `5f68a5c7`) |
| `web4-standard/README.md` (3.1 locus) | `27b85624` 2026-02-17 | no |
| `core-spec/entity-types.md` | `5baa160f` 2026-06-16 | no |
| `core-spec/LCT-linked-context-token.md` (3.2 locus host) | **`d89595e8` 2026-07-16** | **YES — #531** (§1.2 insert + renumber; shifted 3.2 locus 689→718; audited by C210) |
| **`web4-core/src/lct.rs` (SDK mirror)** | **`2ec6ae09` 2026-07-18** | **YES — #527/#538/#540/#544** (368→1114 lines) |
| **`web4-core/src/attestation.rs` (NEW on-subject module)** | `0e997079` 2026-07-17 | **YES — #527/#538** |
| `web4-core/src/ratchet.rs` (NEW module) | `7b048a78` 2026-07-16 | YES — #529 (society ratchet; C222 established = governance, not session-key/LCT-identity) |

The doc surface is stable except canonical LCT (moved, but the only web4-lct-scoped consequence is the 3.2 renumber, corrected in A.2). The real motion is the **SDK mirror**, which is exactly the SDK-GROWS surface the delta method exists to catch — and, per C186, the first question is whether it lands a *web4-lct-scoped* finding its own-file delta (C210 for canonical, C214 for entity-types) did not path here.

### B.2 — Cross-section blindspot sweep: no new internal contradiction
Re-ran the §6-vs-§2.6/§1 cross-section comparison that produced C114-N1, extended to §2.7/§2.8 vs §1 inline examples. All internal contradictions reduce to already-recorded B2–B5 / N1. **0 net-new internal findings.**

---

## §B′ — SDK-mirror gate (the C178–C222 verdict ladder), applied to `lct.rs` + `attestation.rs`

**Gate step 1 — is the mirror genuine and on-subject?**
Verdict: **GENUINE and ON-SUBJECT.** `lct.rs` implements the LCT primitive (`Lct`, `EntityType`, `binding_proof`, key-derived `derive_lct_id`, structured `Mrh`, and now `attestations`/`citizenships`/`authority_ratchet`). `attestation.rs` implements the §2.6/§2.3 attestation + birth-certificate surface directly. Both cite **canon §2.3** in their doc-comments. **Method note:** this is the *first* audited file for which `attestation.rs` is a **genuine on-subject mirror** — for errors/security/handshake (C216/C218/C222) it was DISJOINT or false-for-that-lens. For web4-lct it is squarely on the LCT attestation/birth-cert subject.

**Gate step 2 — does the mirror track the frozen sister or canonical?**
**Canonical, and moving further from the sister every cycle.** The axes on which the sister diverges from canonical all resolve *toward canonical* — and this cycle the code added whole surfaces the frozen sister has no counterpart for:

| Axis | Sister `web4-lct.md` (frozen) | Canonical | `lct.rs`/`attestation.rs` (ratified HEAD) | Mirror tracks |
|------|-------------------------------|-----------|-------------------------------------------|---------------|
| `lct_id` preimage | `MB32(SHA256(binding_proof))` — signature (`:147`) | signature (`:260`) | `sha256(public_key)` — **key** (`lct.rs:361`) | *neither* — **C172-N1 carry** (C186 widened to sister `:147`) |
| birth certificate | prose `Web4BirthCertificate` shape (B9) | inline `birth_certificate` | **concrete + plural REFERENCES** `citizenships: Vec<BirthCertificateRef>` (#538) | canonical descendant (reshaped) |
| attestation record | §2.6 4 fields; §6.1/§6.2 add `claims` (**C114-N1**) | canon §2.3 | `Attestation{witness,type,ts,sig}` — **4 fields, no claims**; `AttestationType` payload-free (#527) | **§2.6 side** (see below) |
| authority ratchet | absent | canon (society ratchet) | `authority_ratchet: Option<RatchetRequirement>` (#544) | canonical/SOCIETY_SPEC — SUPERSEDE evidence |
| operational-key vouching | absent | canon §2.3 op key | present (#540) | canonical — SUPERSEDE evidence |
| entity types | 12 | 15 | 8 (7/15 + `Hybrid`; now +`Society`, C176/#516) | canonical direction |
| tensors | absent | required | absent | — (canonical-lag, C172/C180 scope) |

**The load-bearing new evidence is the attestation `claims` axis — and it is a C114-N1 scope-widening, not a C224 finding.**

The shipped, ratified `attestation::Attestation` struct carries **exactly the four §2.6 fields** and **no `claims`**. Its signed message (`Attestation::message` = `"web4:lct:attestation:v1\n" + subject_lct_id + "\n" + type + "\n" + ts`) omits claims from the signature preimage; `AttestationType` is a **payload-free enum** of the seven §6.1 classes (`Time`/`Audit`/`Oracle`/`Existence`/`Action`/`State`/`Quality`). So the code keeps the §6.1 *class taxonomy* while **dropping the §6.1 "Required Claims" column and the §6.2 `claims:{}` object entirely — claims are not attested at all.**

This is a **live second witness that resolves the direction of C114-N1's §2.6-vs-§6.1 contradiction toward the §2.6 four-field model** (and sharpens it: under D0=MAINTAIN, the remediation choice is now concretely informed — either §2.6 must gain a signed `claims` field to match §6.1 [SDK lags], or §6.1/§6.2's claims are advisory/descriptive and §2.6 is authoritative [SDK is correct, §6.1 needs a "claims not in the signed preimage" note]).

**C224 disposition (prose-is-not-ledger self-catch):** the candidate *presented* as a fresh sister-vs-code contradiction worth a C224-N1. Asking "is it NEW?" before "is it TRUE?" ([[feedback_prose_is_not_ledger]]) resolves it: **C114-N1 already owns the §2.6-vs-§6.1 `claims` contradiction.** C224 only adds the live SDK vote to its coverage — a scope-widening of C114-N1, exactly the class of yield C186 produced for C172-N1.

**Adversarial refutation of the best finding ([[feedback_refute_your_best_finding]]) → CONFIRMED with a correction:**
- *Refutation tried:* "the `claims` live inside `AttestationType` as an enum payload, so the SDK does carry them." **Refuted:** `AttestationType` is a plain fieldless enum (verified `attestation.rs:37-45`); no variant carries data. The four struct fields are the whole record; claims are genuinely absent from both the struct and the signature preimage.
- *Correction banked:* do NOT overclaim "the SDK contradicts §6.1." The seven §6.1 *classes* survive as the enum; what is dropped is the per-class *claims payload*. The precise statement is "the shipped attestation carries the §6.1 class label but not its Required-Claims content, and does not sign claims."
- *Honesty caveat:* this is ratified HEAD, not the published crate. Baseline "is it shipped?" on the published tag, not HEAD ([[feedback_enumeration_and_grep_hypotheses]]).

**Verdict ladder placement:** GENUINE, on-subject mirror, **tracking canonical away from the frozen sister** → **corroborating D0 = SUPERSEDE evidence** (4th independent witness). It is *not* a new defect against the sister. The `ratchet.rs` name (#529) is the **society/governance** ratchet (C202/C222), orthogonal to the LCT-identity subject — the `authority_ratchet` *field on the LCT* (#544) is the LCT carrying a *reference* to that society-ratchet level, a canonical/SOCIETY_SPEC surface, not a web4-lct-sister defect.

---

## §C — Routing

### D0 — FLAGSHIP DESIGN-Q (operator; UNCHANGED, still gates everything)
**Is `protocols/web4-lct.md` a maintained sister-doc, or superseded by canonical `core-spec/LCT-linked-context-token.md`?** Operator-unanswered. Auditor recommendation remains **SUPERSEDE** — now with a **fourth independent witness** (after C186's three: canonical structural divergence B7/B8/B9; the README/back-pointer inversion 3.1/3.2; the key-derived-id SDK direction C172): **(d) the ratified SDK this cycle added concrete, plural, reference-based birth certificates (#538), an `authority_ratchet` field (#544), and operational-key vouching (#540) — whole surfaces the frozen sister has no counterpart for, all descending from canonical, none from the sister.** The gap between the shipped code and the frozen sister is *widening*, not closing. **No remediation may touch this file until D0 resolves.**
- If D0 = **SUPERSEDE**: deprecation/SSOT banner on `web4-lct.md` + fix `web4-standard/README.md:64` → link canonical + delete canonical `LCT-linked-context-token.md:718` deferral. N1 and all B-line items become moot.
- If D0 = **MAINTAIN**: the C74 autonomous list + N1 (now with the shipped-SDK direction vote) + B25 COSE_Sign1 sharpening + the C172-N1 key-derived-id update (covering `web4-lct.md:147`) define the remediation.

### This delta's deliverables — routed, NOT self-applied
1. **3.2 locus correction:** the C75-defect-3.2 back-pointer is at canonical **`LCT-linked-context-token.md:718`** (was `:689` at C186; #531 renumber). Audit-record updated; defect HELD-REAL; under D0=SUPERSEDE this is the line to delete.
2. **C114-N1 scope-widening:** the shipped `attestation::Attestation` (4 fields, no `claims`, payload-free `AttestationType`) is a live witness voting the §2.6 four-field model over the §6.1/§6.2 claims model. Under D0=MAINTAIN this concretely informs N1's remediation; under D0=SUPERSEDE it is moot. HEAD-only caveat noted.
No file is edited by this audit.

### Carries — UNCHANGED (re-confirmed open at live HEAD)
D0 (flagship); C114-N1 (blocked-on-D0, now with SDK direction-witness); C172-N1 (MED, covering sister `:147`); identifier-model design-Q (B13/B14/B15, couples C60-H1 / C24-H1); revocation propagation / future-timestamp (B26/B27); REQUIRED-vs-OPTIONAL presence (B10); cross-track to SAL (B16/B18), witnessing registry (B17), registries-canonicity (B19). The 6 other `protocols/` sisters remain triaged-not-audited per C75 while D0 pends.

---

## §D — Method notes (for the next AUDIT turn = C226, web4-lct's rotation successor is `mcp`; web4-lct returns at its next slot)

1. **The path-provenance discipline fired for real this cycle.** #531's insertion into canonical renumbered the 3.2 back-pointer 689→718. Re-running the `grep` at live HEAD (not carrying the C186 line number) caught it — exactly the [[feedback_prior_finding_path_provenance]] / C146 lesson. A frozen *target* does not mean a frozen *inbound locus*; a sibling's insertion moves your recorded line.
2. **The prose-is-not-ledger self-catch fired a second consecutive web4-lct delta — and correctly.** The attestation-claims contradiction *presented* as a net-new C224-N1. "Is it NEW?" surfaced that C114-N1 already owns it; the honest yield is a scope-widening with a live SDK vote, not a manufactured finding. Check the carry ledger before minting a finding ([[feedback_prose_is_not_ledger]]).
3. **`attestation.rs` is finally a GENUINE on-subject mirror.** For errors/security/handshake it was DISJOINT/false-for-lens (C216/C218/C222). For web4-lct it is squarely on-subject — the mirror-gate's outcome is a function of the *audited file's* subject, not a fixed property of the module. Re-derive on-subject-ness per file ([[feedback_refute_your_best_finding]]).
4. **SDK-mirror gate votes on D0's direction, cumulatively.** Each web4-lct delta the ratified code adds another canonical-descendant surface with no sister counterpart (C186: key-derived id; C224: plural birth-cert refs + authority_ratchet + op-key vouching). "Which way is the ratified code moving?" is now a 4-witness SUPERSEDE vote. For a supersede-vs-maintain DESIGN-Q, the mirror gate is not just a classifier — it is a trend meter.
5. **Frozen ≠ clean, confirmed a fifth consecutive time on this file** (C114/C146/C186, now C224). Byte-frozen target + the *largest* corpus-delta yet (SDK +746 lines, canonical +32 lines) still yielded no net-new sister defect — only two carry calibrations — because the moving mirrors were already audited by their own-file deltas (C210 canonical, C214 entity-types) and the SDK motion tracks canonical, not the sister.
6. **Snapshot baseline recorded** (target blob `5f68a5c7`, unchanged; `lct.rs` at `2ec6ae09`, `attestation.rs` at `0e997079`) so the next delta detects motion in one `git rev-parse`. Whichever pass next reaches **canonical LCT** owns C172-N1's remediation; this file only inherits it under D0 = MAINTAIN.
