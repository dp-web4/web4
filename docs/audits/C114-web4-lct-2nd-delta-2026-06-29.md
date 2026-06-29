# C114 — 2nd-Delta Re-Audit of `protocols/web4-lct.md` (the frozen LCT sister-doc)

**Date**: 2026-06-29
**Auditor**: Legion autonomous web4 track (slot `060036`, LEAD)
**Target**: `web4-standard/protocols/web4-lct.md` (279 lines)
**Type**: **2nd-delta re-audit** (first delta since the C74 first audit + C75 cluster triage). Read-only — produces this audit doc, makes **no file edits** (the file is D0-gated; see below).
**Lineage**: C60-B13 (cross-track flag) → **C74** first audit (#363, 28 findings B1–B28) → **C75** `protocols/` cluster lifecycle triage (#364) → **C114**.
**Snapshot baseline**: corpus HEAD `175498b4`; target blob `5f68a5c7bda9b1dbcfd81f0324df61243efbaab7` (byte-frozen since `27b85624`, 2026-02-17 — **unchanged since C74**).
**Method**: §A prior-finding verification + the two frozen-target re-read disciplines (C56 claim-vs-canonical re-read; C108/C112 cross-section blindspot sweep). §B corpus-delta scan. Single adversarial verifier (refute-by-default) on the one net-new candidate — the 49-agent C74 finder workflow was deliberately **not** re-run (proportionality: frozen file + empty corpus-delta surface).

---

## Headline (read this first)

`protocols/web4-lct.md` is **byte-identical to its C74 snapshot** and every doc it diverges from (canonical `LCT-linked-context-token.md`, `entity-types.md`, SAL, `web4-witnessing.md`, `README.md`) is **also frozen at or before C74's 2026-06-19 snapshot**. The corpus-delta surface is therefore **empty**: no C74 finding could have drifted, no new cross-doc divergence could have appeared from a moving sibling.

That makes this the canonical "frozen ≠ clean" case (C108/C112 lesson). §A confirms **28/28 C74 findings hold** and both C75 structural defects persist. §B's corpus-delta yield is **0**, exactly as predicted — **but the cross-section blindspot re-read surfaced 1 net-new finding (N1, MED)** that the C74 section-by-section finder workflow missed: an **internal** contradiction where §6 requires an attestation `claims` object that §2.6/§1 of the same doc define no field for. This reproduces the C112-N2 pattern precisely — a contradiction *between* sections that section-anchored finders don't see.

**The flagship gate is unchanged: D0 (supersede-vs-maintain the parallel LCT spec) remains operator-unanswered and gates all remediation.** N1 is routed *into* the D0=maintain remediation path — it is **not** self-applied here. Nothing in this audit edits the file or re-decides D0.

---

## §A — Prior-finding verification

### A.1 — C74 findings (B1–B28) against the frozen file

The target blob is byte-identical to C74's snapshot, so all line-anchored findings hold by construction. Spot-verified the load-bearing ones token-for-token:

| C74 ID | Sev | Status at C114 | Verification |
|--------|-----|----------------|--------------|
| B1 | HIGH | **HELD** | §1 JSON still does not close — outer `{` opens L10, no closing `}` before the L50 fence. Malformed flagship example. |
| B2 | MED | **HELD** | `birth_certificate.context`: §1 L22 = 3 values; §2.3 L74 = 5. |
| B3 | MED | **HELD** | `lineage.reason`: §1 L48 `"rotate"` ∉ §2.7 L121 enum (`genesis\|rotation\|fork\|upgrade`). |
| B4 | MED | **HELD** | `revocation.reason`: §1 L49 = 2 values; §2.8 L130 = 3 (adds `expired`). |
| B5 | MED | **HELD** | §2.4 L91 `permanent` definition still reads backwards vs its `permanent:true` usage. |
| B6 | LOW | **HELD** | `mrh.witnessing[].role` (§2.4, 3 values) vs attestation `type` (§2.6/§6.1, 7 values) — same witness-class concept, two unreconciled fields. |
| B7 | HIGH | **HELD** | `entity_type` = 12 (§1 L14 / §2.2 L63); canonical + `entity-types.md` = 15 (missing Society, Policy, Infrastructure). Canonical frozen at C65 → claim valid. |
| B8 | MED | **HELD** | `t3_tensor`/`v3_tensor` absent; canonical "Every LCT MUST contain a t3_tensor" unchanged (frozen C61). |
| B9 | HIGH | **HELD** | birth-cert shape divergence (`parent_entity`+`context` vs canonical `issuing_society`/`genesis_block_hash`/`birth_context`). |
| B16 | MED | **HELD** | SAL `Web4BirthCertificate` §2.2 still requires `society`/`lawOracle`/`lawVersion`/`genesisBlock`/`rights`/`obligations` (re-read current SAL L48-59, frozen C59) — sister carries none. |
| B13/B14/B15 | MED | **HELD** | identifier-model divergence (segment colon / hash-vs-UUID / `subject` DID form) unchanged. |
| B17 | MED | **HELD** | `mrh.witnessing[].role` value `audit` still not in the `web4-witnessing.md` §6 registry (`time`/`audit-minimal`/`oracle`); registry frozen 2025-09-14. |
| B19 | MED | **HELD** | §9 IANA still claims entity-type/revocation registry homes that duplicate canonical (folds into C70 registries-canonicity bundle). |
| B20–B24 | MED/LOW | **HELD** | RFC-2119 gaps in §3/§5.1/§4.3/§5.2; B24 24h-vs-48h overlap tension persists. |
| B25 | MED | **HELD (+ sharpened, see A.3)** | §1 L18 "COSE Sig over canonical LCT fields" vs §3 signing only the 4 `binding` sub-fields. |
| B26/B27/B28 | MED/LOW/INFO | **HELD** | revocation propagation gap; future-timestamp unenforceability; `lct_id` stable-correlator privacy note. |
| B10/B11/B12/B18 | MED/LOW | **HELD** | REQUIRED-vs-OPTIONAL presence; revocation `violation`; attestation shape vs canonical; snake-vs-camel naming. |

**Result: 28/28 HELD, 0 regression** (no remediation has landed — the file is D0-gated — so there is no "applied fix" to re-verify; this is pure persistence verification). The 5 C74-refuted items remain correctly refuted (re-checked the overlap-window and `horizon_depth` items: still non-defects).

### A.2 — C75 structural defects (the D0 evidence packet)

| C75 defect | Status at C114 | Verification |
|------------|----------------|--------------|
| **3.2 Canonical-defers-to-frozen** (`LCT-linked-context-token.md:689` → `protocols/web4-lct.md`) | **PERSISTS** | `:689` deferral pointer present verbatim; canonical frozen since C61, so the SSOT inversion is unchanged. |
| **3.1 README SSOT inversion** | **PERSISTS** | `README.md` L64 still links `protocols/web4-lct.md` as "Linked Context Token specification"; canonical `core-spec/LCT-linked-context-token.md` link count in README = **0**. README frozen 2026-02-17. |

### A.3 — C56 claim-vs-canonical re-read (frozen-target discipline #1)

Re-read C74's cross-doc *claims* against the canonical sources token-by-token (not just "is the edit present" — there is no edit; this checks whether any C74 claim went stale as a sibling moved). **No claim went stale** — every cited canonical source (canonical LCT C61, entity-types C65, SAL C59, witnessing 2025-09) is frozen at or before C74's snapshot, so B7/B8/B9/B16/B17's cross-doc assertions all still describe the current corpus.

One **sharpening** (not net-new — folds into B25, recorded for the remediation path): §3 step 4 specifies `binding_proof = Sign(sk, CBOR(binding))` (a raw signature over deterministic CBOR), while §1 L18 labels the field `"cose:Sig_structure"` and §2.2 L67 calls it a "COSE signature." A COSE_Sign1 envelope is not the same artifact as a bare `Sign(sk, CBOR(binding))`, so the §1/§2.2 "COSE" framing and the §3 algorithm describe different signing *envelopes*, not just B25's different signing *scope*. This is the same envelope-vs-method axis as handshake C112-N2 but is a refinement of the existing B25, so it is **not** counted as net-new; it is noted so the D0=maintain remediation states the actual COSE_Sign1 construction.

---

## §B — Corpus-delta scan + blindspot sweep (net-new findings)

### B.1 — Corpus-delta surface: EMPTY

| Referent / sibling | last commit | moved since C74 (2026-06-19)? |
|--------------------|-------------|-------------------------------|
| `protocols/web4-lct.md` (target) | `27b85624` 2026-02-17 | **no** (byte-frozen) |
| `core-spec/LCT-linked-context-token.md` | C61 2026-06-15 | no |
| `core-spec/entity-types.md` | C65 2026-06-16 | no |
| `core-spec/web4-society-authority-law.md` (SAL) | C59 2026-06-15 | no |
| `protocols/web4-witnessing.md` | 2025-09-14 | no |
| `README.md` / `INTEGRATION_STATUS.md` | 2026-02-17 | no |

Every doc on the divergence/inbound surface is frozen at or before C74's snapshot → **corpus-delta yield = 0**. Reported honestly (C110 lesson: clean re-read = report 0).

### B.2 — Cross-section blindspot sweep (frozen-target discipline #2) → **1 NET-NEW**

> **N1 — MED — internal cross-section `claims` contradiction (C112-N2 class).**
> §6.1 "Witness Classes" (L221-229) has a column literally titled **"Required Claims"** mandating per-class members (`time`→`ts,nonce`; `audit`→`policy_met,evidence`; `oracle`→`source,data`; …), and §6.2's attestation example (L237-240) carries those inside a `"claims": {…}` object. **But §2.6 "Attestation Fields" (L111-114) — the doc's own normative field list — enumerates exactly four fields (`witness`, `type`, `sig`, `ts`) with no `claims`, and §1's canonical attestations example (L45-47) likewise omits `claims`** (and omits the `nonce` the `time` class requires). The word `claims` is never *defined* as a field anywhere in the document; it appears only in §6's table header and §6 example.
>
> **Consequence**: an attestation built to the §2.6/§1 schema (whose fields are marked REQUIRED) is structurally incapable of carrying the §6.1-required claims — the two normative halves of the spec are inconsistent. **Resolution** (D0=maintain path): add `claims` (and `nonce` for the `time` class) to §2.6 and the §1 example; or downgrade §6.1's "Required Claims"/§6.2 example to reference the defined field set.
> **Location**: §6.1 L221-229 / §6.2 L237-240 vs §2.6 L111-114 / §1 L45-47.
> **Distinctness**: C74-B12 saw only the *external* divergence ("sister omits the `nonce`/`claims` that **canonical** carries"). N1 needs no sister doc — it is a contradiction *within* `web4-lct.md` between §6 and §2.6/§1. Adversarially verified **REAL-AND-DISTINCT** (refute-by-default verifier, quoted evidence).

**Why C74 missed it**: the C74 workflow's 5 lenses were section-anchored — internal-consistency finders compared §1↔§2.x (the inline-JSON-vs-field-definitions axis, which produced B2-B5), and cross-doc finders compared §2.6↔canonical (which produced B12). No lens compared **§6 (the witness-attestation chapter) against §2.6/§1 (the schema sections)**. The cross-section blindspot sweep is precisely the discipline that closes that gap — the same way C112-N2 was found on a byte-frozen handshake doc.

---

## §C — Routing

### D0 — FLAGSHIP DESIGN-Q (operator; UNCHANGED, still gates everything)
**Is `protocols/web4-lct.md` a maintained sister-doc, or superseded by `core-spec/LCT-linked-context-token.md`?** Operator-unanswered as of C114. Auditor recommendation remains **SUPERSEDE** (C74/C75): the divergence is structural (B7/B8/B9), the canonical defers to the frozen sister (`:689`), and the README routes readers to the stale doc — all unchanged. **No remediation may touch this file until D0 resolves.**

- If D0 = **SUPERSEDE**: C115-equivalent = deprecation/SSOT banner on `web4-lct.md` + fix README L64 to link canonical + delete canonical `:689` deferral. N1 and all B-line items become moot.
- If D0 = **MAINTAIN**: the C74 autonomous list **plus N1** (and the B25 envelope sharpening from §A.3) define the remediation.

### N1 — routed to the D0=maintain remediation path (NOT self-applied)
Per policy-review instruction: N1 is recorded here as **blocked-on-D0 / queued-for-the-maintain-path**, so it (a) is not silently re-surfaced as "net-new" at C116, and (b) is not mistaken for a self-applicable fix. It is a no-regret in-file correction *if and only if* the operator chooses MAINTAIN.

### Carries — UNCHANGED (re-confirmed open)
All C74 §C routing stands: D0 (flagship); identifier-model design-Q (B13/B14/B15, couples with C60-H1); revocation propagation/future-timestamp (B26/B27, canonical-shared); REQUIRED-vs-OPTIONAL presence (B10); cross-track to SAL (B16/B18), witnessing registry (B17), registries-canonicity (B19, C70 bundle). The 6 other `protocols/` sisters remain triaged-not-audited per C75 (do not audit them while D0 pends).

---

## §D — Method notes (for the next AUDIT turn)

1. **Frozen ≠ clean, confirmed a third time** (after C108-N1, C112-N1/N2). A byte-frozen target with an *empty* corpus-delta surface still yielded N1 — entirely from the cross-section blindspot sweep, the one discipline a section-anchored finder workflow cannot reproduce. The §B value on a frozen delta is the two re-read disciplines, not the corpus diff.
2. **No-remediation-landed deltas are lighter on §A**: unlike the registries/security/errors 2nd-deltas (which verify that a *prior remediation's* fixes held), web4-lct has had no remediation (D0-gated), so §A is pure persistence verification (28/28 HELD by byte-identity) — the analytic weight shifts almost entirely to §B's blindspot sweep.
3. **Proportionality on a frozen target**: the 49-agent C74 workflow was deliberately not re-run — a single adversarial verifier on the one blindspot candidate is the right cost for a frozen file + empty corpus delta. Re-running the heavy finder would have been token-drift for predictable 0 corpus-delta yield.
4. **Snapshot baseline recorded** (blob `5f68a5c7`) so the next delta (C116) can detect motion in one `git rev-parse`.

---

*C114 makes no file edits and settles no design question. It verifies the C74/C75 snapshot held byte-for-byte, reports the corpus-delta surface empty, surfaces one net-new internal cross-section contradiction (N1) via the blindspot re-read, and re-confirms that D0 still gates every remediation on this file.*
