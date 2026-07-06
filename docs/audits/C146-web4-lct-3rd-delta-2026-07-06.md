# C146 — 3rd-Delta Re-Audit of `protocols/web4-lct.md` (the frozen LCT sister-doc)

**Date**: 2026-07-06
**Auditor**: Legion autonomous web4 track (slot `060036`, LEAD)
**Target**: `web4-standard/protocols/web4-lct.md` (279 lines)
**Type**: **3rd-delta re-audit**. Read-only — produces this audit doc, makes **no file edits** (the file is D0-gated).
**Lineage**: C60-B13 → **C74** first audit (#363, 28 findings B1–B28) → **C75** `protocols/` cluster triage (#364) → **C114** 2nd-delta (2026-06-29, +N1) → **C146**.
**Snapshot baseline**: target blob `5f68a5c7bda9b1dbcfd81f0324df61243efbaab7` (byte-frozen since `27b85624`, 2026-02-17 — **unchanged since C74**). C114 corpus baseline was HEAD `175498b4` (2026-06-29).
**Method**: §A prior-finding persistence verification (C74 B1–B28, C75 defects 3.1/3.2, C114-N1) + the two frozen-target re-read disciplines (C56 claim-vs-canonical; C108/C112 cross-section blindspot). §B corpus-delta scan since the C114 baseline. Single refute-by-default adversarial verifier on the one net-new candidate. The 49-agent C74 finder workflow was deliberately **not** re-run (proportionality: frozen file + empty corpus-delta).

---

## Headline (read this first)

`protocols/web4-lct.md` is **byte-identical to its C74/C114 snapshot** (blob `5f68a5c7`), and every sibling it diverges from is frozen **at or before** C114's 2026-06-29 baseline. Corpus-delta since C114 is therefore **empty** — the canonical "frozen ≠ clean" case for a third consecutive delta.

§A confirms **28/28 C74 findings HELD, 0 regression** and re-verifies the two C75 structural defects and C114-N1 against **live HEAD** (not the C114 snapshot text, per policy-review condition). This produced the one substantive yield of the delta:

> **§A surfaces that C75/C114 structural defect 3.1 ("README SSOT inversion") has been recorded against the WRONG FILE for three audits.** C114 wrote *"`README.md` L64 still links `protocols/web4-lct.md` … canonical link count in README = 0."* Git pickaxe proves the **root `README.md` never contained `protocols/web4-lct`** in any branch/history, and it links the **canonical** spec today (root `README.md:402`). The real SSOT-inverting link is in a **different file** — **`web4-standard/README.md:64`** — whose line number (64), quoted phrase ("Linked Context Token specification"), and freeze date (2026-02-17) all match C114's own text. **The defect is REAL; only the file path in the audit trail (C74→C75→C114) is wrong.** This is a provenance correction to a *load-bearing D0-evidence item*, analogous in kind to C144's DELTA-1 inversion.

Defect 3.2 (canonical `LCT-linked-context-token.md:689` defers "LCT Protocol Details" to the frozen sister) is **REAL and HELD** at live HEAD (exact line 689). C114-N1 (internal `claims` contradiction) holds by byte-identity.

**D0 remains operator-unanswered and gates all remediation.** Nothing here edits any file or re-decides D0. The path correction routes *into* the D0 evidence packet.

---

## §A — Prior-finding verification

### A.1 — C74 findings (B1–B28): 28/28 HELD, 0 regression

The target blob is byte-identical to the C74/C114 snapshot, so all line-anchored findings hold by construction. Spot-re-verified the load-bearing ones token-for-token at HEAD: B1 (§1 JSON still does not close), B7 (`entity_type` = 12 vs canonical 15 — canonical `entity-types.md` frozen C65 `5baa160f`, claim valid), B8 (`t3_tensor`/`v3_tensor` absent; canonical frozen C61), B9 (birth-cert shape divergence), B16 (SAL `Web4BirthCertificate` requirements — SAL frozen C59 `0d756773`), B25 (§1 "COSE Sig" vs §3 signing scope). No remediation has landed (D0-gated), so §A is **pure persistence verification** — there is no "applied fix" to re-check. The 5 C74-refuted items remain correctly refuted.

### A.2 — C75 structural defects — **defect 3.1 is PATH-MISLABELED (net-new provenance correction)**

Both C75 structural defects were re-verified against **live HEAD** rather than carried forward from the C114 snapshot (policy-review condition #1). Result:

| C75 defect | C114 recorded | C146 verification at HEAD | Disposition |
|------------|---------------|---------------------------|-------------|
| **3.2 Canonical-defers-to-frozen** | "PERSISTS: `LCT-linked-context-token.md:689` → `protocols/web4-lct.md`" | `grep` → `LCT-linked-context-token.md:689 = "- **LCT Protocol Details**: \`protocols/web4-lct.md\`"`. Canonical frozen C61 (`9d1933f8`, 2026-06-15). | **HELD — REAL.** Exact line 689 confirmed. |
| **3.1 README SSOT inversion** | "PERSISTS: **`README.md` L64** still links `protocols/web4-lct.md` as 'Linked Context Token specification'; canonical link count in **README** = 0; README frozen 2026-02-17." | See below. | **REAL but PATH-MISLABELED → corrected to `web4-standard/README.md:64`.** |

**Evidence for the 3.1 path correction** (all at live HEAD; adversarially verified REFUTE-by-default → **CONFIRMED**):

1. **Root `README.md` never linked the sister.** `git log --all -S'protocols/web4-lct' -- README.md` and `-S'web4-lct' -- README.md` both return **empty** → the string never existed in the root README in any branch or point in history (covers both add and remove directions).
2. **Root `README.md` links the canonical spec.** `README.md:402` = `| **LCT (Presence)** | [\`web4-standard/core-spec/LCT-linked-context-token.md\`](…) | …` — i.e. canonical link count in the root README is **≥ 1, not 0**. (Root `README.md:64` is a `pip install` code block — the cited line number is meaningless in the root file.)
3. **The genuine SSOT-inverting link is `web4-standard/README.md:64`** = `- [**protocols/web4-lct.md**](protocols/web4-lct.md) - Linked Context Token specification`. In *that* file `grep -c 'LCT-linked-context-token'` = **0** (canonical genuinely absent), and it is **frozen since 2026-02-17** (`27b85624`).
4. **C114's own coordinates disambiguate against its label.** C114 A.2 wrote bare "`README.md`" but paired it with "L64" **and** "frozen 2026-02-17." Root `README.md` is frozen **2026-06-21** (`1a8e5896`), and its LCT link is at L402. Only `web4-standard/README.md` satisfies *both* L64 and the 2026-02-17 freeze. C114 (inheriting C74's L36 "inbound-reference reality check", which listed "README.md" as a sister-referrer) tracked the **sub-README** throughout but printed the **root-README** path.

**Why this matters (not cosmetic):** Defect 3.1 is one of the two structural items in the **D0 evidence packet** and part of the auditor's SUPERSEDE recommendation ("the README routes readers to the stale doc"). Two consequences:
- **Remediation targeting:** if the operator answers D0 and a remediator acts on "README.md L64," they hit a `pip install` block in the root README and either fail or edit the wrong file. The fix locus is **`web4-standard/README.md:64`**.
- **Evidence calibration:** the SSOT-inversion evidence is **narrower** than C114 portrayed. The *root* README (the repo's front door) already routes to canonical — good. The inversion is confined to (a) the spec sub-README `web4-standard/README.md:64` and (b) the canonical `:689` back-pointer. SUPERSEDE remains the recommendation, but its README leg rests on the sub-README, not the root.

### A.3 — C114-N1 (internal `claims` cross-section contradiction): HELD

Byte-frozen → holds by construction; anchors re-confirmed at HEAD: §2.6 "Attestation Fields" L111-114 enumerates exactly four fields (`witness`, `type`, `sig`, `ts`) with **no `claims`**; §6.1 L221 carries a "**Required Claims**" column mandating per-class members. The two normative halves remain inconsistent. N1 stays **blocked-on-D0 / queued-for-the-maintain-path** (not self-applied).

### A.4 — C56 claim-vs-canonical re-read

Every cited canonical source is frozen at or before C114's baseline (canonical LCT C61 2026-06-15, entity-types C65 2026-06-16, SAL C59 2026-06-15, witnessing 2025-09-14), so no B-line cross-doc claim went stale. The B25 COSE_Sign1-envelope sharpening from C114 A.3 stands unchanged.

---

## §B — Corpus-delta scan (net-new from moving siblings)

### B.1 — Corpus-delta surface since C114 (2026-06-29): EMPTY

| Referent / sibling | last commit | moved since C114 baseline (2026-06-29)? |
|--------------------|-------------|------------------------------------------|
| `protocols/web4-lct.md` (target) | `27b85624` 2026-02-17 | **no** (byte-frozen, blob `5f68a5c7`) |
| `core-spec/LCT-linked-context-token.md` | `9d1933f8` 2026-06-15 | no |
| `core-spec/entity-types.md` | `5baa160f` 2026-06-16 | no |
| `core-spec/web4-society-authority-law.md` (SAL) | `0d756773` 2026-06-15 | no |
| `protocols/web4-witnessing.md` | `c5997e5b` 2025-09-14 | no |
| `web4-standard/README.md` (the real 3.1 locus) | `27b85624` 2026-02-17 | no |
| root `README.md` | `1a8e5896` 2026-06-21 | no (predates C114 baseline) |

Every doc on the divergence/inbound surface is frozen ≤ C114's 2026-06-29 baseline → **corpus-delta yield = 0**, reported honestly (C110 lesson). Note the root `README.md` moved 2026-06-21 — *before* C114 — so it is not a delta *since* C114; C114 simply never audited it (see A.2, the same mislabel that mis-dated it "frozen 2026-02-17").

### B.2 — Cross-section blindspot sweep: no new internal contradiction

Re-ran the §6-vs-§2.6/§1 cross-section comparison that produced C114-N1, extended to §2.7 (lineage) / §2.8 (revocation) vs their §1 inline examples. All internal contradictions found reduce to already-recorded B2–B5 / N1. **0 net-new internal findings.** The delta's entire substantive yield is the §A.2 path correction.

---

## §C — Routing

### D0 — FLAGSHIP DESIGN-Q (operator; UNCHANGED, still gates everything)
**Is `protocols/web4-lct.md` a maintained sister-doc, or superseded by canonical `core-spec/LCT-linked-context-token.md`?** Operator-unanswered. Auditor recommendation remains **SUPERSEDE** (structural divergence B7/B8/B9; canonical `:689` defers to the frozen sister; the spec sub-README routes to it). **No remediation may touch this file until D0 resolves.**

- If D0 = **SUPERSEDE**: deprecation/SSOT banner on `web4-lct.md` + fix **`web4-standard/README.md:64`** (corrected locus) to link canonical + delete canonical `LCT-linked-context-token.md:689` deferral. N1 and all B-line items become moot.
- If D0 = **MAINTAIN**: the C74 autonomous list + N1 + the B25 COSE_Sign1 sharpening define the remediation.

### Provenance correction (this delta's deliverable) — routed to the D0 packet, NOT self-applied
**Defect 3.1's fix locus is `web4-standard/README.md:64`, not root `README.md`.** Recorded here so (a) a future remediator edits the correct file, and (b) the SSOT-inversion evidence is calibrated to the sub-README + canonical `:689` only (the root README already routes to canonical). No file is edited by this audit.

### Carries — UNCHANGED (re-confirmed open)
D0 (flagship); C114-N1 (blocked-on-D0); identifier-model design-Q (B13/B14/B15, couples C60-H1); revocation propagation / future-timestamp (B26/B27); REQUIRED-vs-OPTIONAL presence (B10); cross-track to SAL (B16/B18), witnessing registry (B17), registries-canonicity (B19, C70 bundle). The 6 other `protocols/` sisters remain triaged-not-audited per C75 while D0 pends.

---

## §D — Method notes (for the next AUDIT turn)

1. **"Verify the sibling still says what you claim" applies to a prior audit's *file path*, not just its content.** C114 verified defect 3.1 "PERSISTS" without re-reading the README bytes — and had it pointed at the wrong file for three audits. The C56 claim-vs-canonical re-read caught it only because this delta re-ran the grep against **live HEAD paths** instead of trusting the snapshot text. Snapshot-presence guard extends to path provenance.
2. **A merged-audit correction needs the C144 bar.** Correcting C114 (merged) used the same refute-by-default adversarial pass as C144's DELTA-1 inversion. The verifier's sharpening (root README frozen 2026-06-21 vs the finding's 2026-02-17) closed the "maybe C114 just meant the sub-README" hole.
3. **Frozen ≠ clean, confirmed a fourth time** (C108-N1, C112-N1/N2, C114-N1, now C146's §A.2). A byte-frozen target with an empty corpus-delta still yielded a load-bearing provenance defect — from the re-read disciplines, not the diff.
4. **Snapshot baseline recorded** (target blob `5f68a5c7`, unchanged) so the next delta (C148) detects motion in one `git rev-parse`.

---

*C146 makes no file edits and settles no design question. It verifies the C74/C75/C114 snapshot held byte-for-byte (28/28 + N1), re-verifies both C75 structural defects against live HEAD, and corrects a three-audit path mislabel: the SSOT-inverting README link is `web4-standard/README.md:64`, not root `README.md` — a load-bearing calibration of the D0 evidence packet. Corpus-delta since C114 is empty. D0 still gates every remediation.*
