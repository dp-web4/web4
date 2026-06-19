# C74 — First Audit of `protocols/web4-lct.md` (the LCT sister-doc)

**Date**: 2026-06-19
**Auditor**: Legion autonomous web4 track (slot `000047`, exit-pending)
**Target**: `web4-standard/protocols/web4-lct.md` (278 lines, last touched `27b85624` 2026-02-17)
**Type**: **First C-series audit** of this file (NOT a delta — no prior C74). Bidirectional carry re-verification of C60-B13 / C61 against the current corpus.
**Method**: §A carry re-verification (hand-grep verified); §B 5-lens refute-by-default finder workflow (`wf_c9e512b0-6b2`, 49 agents, 44 raw → 39 upheld → **26 distinct** after synthesis dedup), every cross-doc contradiction independently grep-verified.

---

## Headline (read this first)

`protocols/web4-lct.md` is a **frozen parallel LCT specification** that predates the entire `C9 → C24 → C60 → C61` remediation cycle of the canonical `core-spec/LCT-linked-context-token.md`. It was last edited 2026-02-17; the canonical doc's most recent remediation (C61, `e8be6b6c`) landed 2026-06-15. The two now disagree **structurally**, not cosmetically:

- canonical requires `t3_tensor` + `v3_tensor` on every LCT — **the sister-doc has neither**;
- canonical enumerates **15** entity types — the sister-doc lists **12** (missing Society, Policy, Infrastructure);
- canonical's `birth_certificate` carries `issuing_society` / `genesis_block_hash` / `birth_context` and is society-gated — the sister-doc's carries `parent_entity` / `context`, is keyed differently, and marks fields REQUIRED that canonical scopes OPTIONAL;
- canonical's `lct_id` is `lct:web4:mb32:…` (segmented) and the `did:web4` method binds it to an **RFC 4122 UUID** — the sister-doc derives it as a bare `MB32(SHA256(binding_proof))` content hash with no segment colon.

Plus the sister-doc carries **internal** self-contradictions (a §1 "canonical" JSON object that does not parse; three inline-vs-§2 enum mismatches; a field definition that reads backwards).

**This is the root cause of nearly every finding below: two normative LCT specs are being maintained in parallel and one of them stopped tracking 4 months and one full remediation cycle ago.** C60-B13 already flagged this exact file and offered the operator two paths — *sync the enums* OR *mark it superseded by the core spec*. C74's evidence is that the divergence is now far past "the enums": it is the whole object shape. **Auditor recommendation: SUPERSEDE** (add a deprecation/SSOT-pointer banner to `protocols/web4-lct.md` directing implementers to `core-spec/LCT-linked-context-token.md`) rather than chase 20+ sync edits that will re-drift the next time the canonical doc moves. The flagship DESIGN-Q below (**D0**) puts that decision to the operator; all other routing is **contingent on D0**.

---

## §A — Bidirectional carry re-verification

| Carry | Source | Verdict against current corpus |
|-------|--------|--------------------------------|
| **C60-B13** — `mrh.witnessing[].role` enum 7 (LCT) vs 3 (`web4-lct.md`); plus stale 12-type `entity_type` vs canonical 15. Fix: sync OR mark superseded. | C60 §B Cluster 5 (flagship-B), routed CROSS-TRACK | **HARDENED + WIDENED.** Both halves confirmed verbatim (sister §2.4 L97 role = `time\|audit\|oracle` = 3; canonical §108 = 7; sister §2.2 L63 = 12 types; canonical 15). C74 finds the divergence is **not limited to these two enums** — it now spans tensors, birth-cert shape, id form, field names, and revocation reasons (see §B). C60-B13's deferred "sync vs supersede" choice is escalated to **D0** with a supersede recommendation. |
| **C61 remediation** (9 fixes to canonical LCT: A1 tensor-weight SSOT citation, B4 `witness_attested`, A2 composite 0.0+, §8/§9 prose precision) | C61 PR #338 `e8be6b6c` | **NONE reflected here** — and *cannot* be: the sister-doc is frozen at 2026-02-17, predating C61 (2026-06-15). A1/A2/B4 are tensor-scoped and **moot** in the sister-doc, which has no tensor block at all (a deeper divergence than the ones C61 fixed). Confirms the freeze: the sister-doc never received any of the C24/C60/C61 work. |
| **C60 design-Q carries** (lct_id segment count H1; revocation enum M4/M6; `entity_type` closed-15 B12; `paired.context` B2) | C60 §C | **Re-instantiated with DIFFERENT values here** — the sister-doc independently specifies these fields and disagrees with both canonical and the open design-Q (e.g. its `lct_id` is a flat hash, settling H1's "segment count" question in the *wrong* direction relative to `did:web4`). Informs the operator's D0/D1 adjudication; does not resolve the carries. |

**Provenance note**: This is a first audit, so there is no prior-C74 "held/regressed" delta. §A is strictly carry re-verification per the C56/C64 method note (memory `feedback_remediation_introduced_regression`).

**Inbound-reference reality check** (policy-review condition #1): within the live spec `web4-standard/`, the sister-doc is referenced by `README.md`, `INTEGRATION_STATUS.md`, `submission/draft-palatov-web4-core-00.txt`, and core-spec's own `LCT-linked-context-token.md`. Full-repo (any path) = 10 referrers, including archived reference-impls and prior audit docs. It is a **live, linked** sister-doc — not an orphan — which is exactly why the parallel-spec divergence matters.

---

## §B — Distinct findings (26, deduped from 39 upheld)

Severity reflects the **verifier's final** call (several finders' HIGH were down-graded on refutation). Counts are honest, not padded (per BC-C23-5): a first audit of a never-audited frozen file with a full remediation cycle of accumulated drift legitimately surfaces more than a steady-state delta (recent deltas ran 10–16). 5 findings were **REFUTED** (listed at end).

### Cluster 1 — Internal self-contradictions (§1 inline JSON vs §2.x definitions) — fixable in-file

| ID | Sev | Finding | Location |
|----|-----|---------|----------|
| **B1** | **HIGH** | §1 "canonical LCT object" JSON **does not parse** — outer object opens at L10, never closed before the L50 fence (13 `{` / 12 `}`). Verified independently. The doc's flagship example, which L7 says implementers MUST follow, is malformed. | §1 L10–50 |
| **B2** | MED | `birth_certificate.context` enum: §1 L22 lists **3** (`nation\|platform\|network`); §2.3 L74 lists **5** (adds `organization`, `ecosystem`). | §1 L22 vs §2.3 L74 |
| **B3** | MED | `lineage.reason`: §1 L48 example uses `"rotate"`, which is **not a member** of the §2.7 L121 enum (`genesis\|rotation\|fork\|upgrade`) — form differs (`rotate` vs `rotation`). | §1 L48 vs §2.7 L121 |
| **B4** | MED | `revocation.reason`: §1 L49 lists **2** (`compromise\|superseded`); §2.8 L130 lists **3** (adds `expired`). | §1 L49 vs §2.8 L130 |
| **B5** | MED | `permanent` field definition reads **backwards**: §2.4 L91 says "Boolean indicating if pairing can be revoked" — but `permanent: true` (used on the birth-cert pairing, §1 L32) should mean *non-revocable*. | §2.4 L91 |
| **B6** | LOW | `mrh.witnessing[].role` set (§2.4, 3 values) and attestation `type` set (§2.6/§6.1, 7 values) are different fields with overlapping names — the doc uses `role` and `type` for the same witness-class concept without reconciling them. | §2.4 L97 / §2.6 L112 |

### Cluster 2 — Canonical divergence (vs `core-spec/LCT-linked-context-token.md`) — evidence for D0

| ID | Sev | Finding | Location |
|----|-----|---------|----------|
| **B7** | **HIGH** | `entity_type` enum lists **12**; canonical (and `entity-types.md`) defines **15** — missing **Society, Policy, Infrastructure**. (= C60-B13 half-2.) | §1 L14 / §2.2 L63 |
| **B8** | MED | Sister-doc **omits `t3_tensor` and `v3_tensor` entirely**; canonical §364 states "Every LCT MUST contain a `t3_tensor`" (and `v3_tensor`). A core REQUIRED structure is simply absent. | whole §1 / §2 |
| **B9** | **HIGH** | `birth_certificate` shape diverges: sister has `parent_entity`+`context`, **lacks** canonical `issuing_society` and `genesis_block_hash`; canonical names the field `birth_context` (sister: `context`). | §1 L20–26 / §2.3 |
| **B10** | MED | Sister marks `birth_certificate` / `mrh.paired` / `attestations` **REQUIRED** where canonical scopes them OPTIONAL or society-gated. | §2.3/§2.4/§2.6 vs canonical §2.1–2.2 |
| **B11** | MED | `revocation.reason` lacks canonical `violation` (canonical §7.4) — couples with B4. | §2.8 L130 |
| **B12** | LOW | Attestation shape diverges: sister uses flat `sig`/`ts` and omits `nonce`/`claims`; canonical uses a `claims` object (§2.3 L161-172). | §2.6 L107–114 / §6.2 |

### Cluster 3 — Cross-doc divergence (other sibling specs) — CROSS-TRACK / DESIGN-Q

| ID | Sev | Finding | Location |
|----|-----|---------|----------|
| **B13** | MED | `lct_id` form `lct:web4:<multibase-encoded-hash>` lacks the `mb32:` colon-segment separator canonical uses (`lct:web4:mb32:…`). | §1 L11 / §2.1 L56 |
| **B14** | MED | `lct_id` defined as a **content hash** (`MB32(SHA256(binding_proof))`, §3 L147) but `did:web4` method (§3) requires `lct-id` to be an **RFC 4122 UUID** — two incompatible identifier models. | §2.1 L56 / §3 L147 |
| **B15** | MED | `subject` examples use `did:web4:key:z6Mk…`; the `did:web4` method (§3) defines syntax `did:web4:<authority>:<lct-id-UUID>` and places `z6Mk…` only as DID-Doc verification material — not as a `subject` value. | §1 L12 / §2.1 / §6.2 |
| **B16** | MED | `birth_certificate` **omits SAL-required normative fields** — `web4-society-authority-law.md` §2.2 `Web4BirthCertificate` requires `society`, `lawOracle`, `lawVersion`, `genesisBlock`, `rights`, `obligations`; sister has none. | §2.3 vs SAL §2.2 |
| **B17** | MED | `mrh.witnessing[].role` value `audit` diverges from the **Web4 Witness Role Registry** (`web4-witnessing.md` §6 IANA): registered values are `time` / `audit-minimal` / `oracle` — `audit` is not registered. | §2.4 L97 |
| **B18** | LOW | `birth_certificate` keys are snake_case; SAL canonical keys are camelCase (`citizenRole`, `lawOracle`…). Naming-form divergence. | §2.3 vs SAL §2.2 |
| **B19** | MED | §9 IANA requests an "Entity types registry" and "Revocation reason codes" that **duplicate canonical homes** (`entity-types.md`, core-spec §7.4) — second registry-home claim (cf. C70 registries-orphan headline). | §9 L277–279 |

### Cluster 4 — Normative clarity (RFC 2119) — fixable in-file

| ID | Sev | Finding | Location |
|----|-----|---------|----------|
| **B20** | MED | §3 Binding Algorithm steps (lct_id derivation, deterministic CBOR) are normatively load-bearing but stated as **bare numbered imperatives** with no MUST/SHALL. | §3 L136–150 |
| **B21** | MED | §5.1 rotation procedure (overlap window, grace end, archive) — determinative steps, no RFC 2119. | §5.1 L201–205 |
| **B22** | LOW | §4.3 MRH Query and §5.2 Split-Brain Resolution use bare imperatives where the outcome is determinative (which successor wins). | §4.3 / §5.2 |
| **B23** | LOW | §2.4 "First entry MUST be citizen role pairing" is an array-ordering MUST with no defined validation/failure behavior. | §2.4 L88 |
| **B24** | LOW | Rotation overlap stated as "24 hours" (§5.1 L203) while §7.2 caps it at "MUST NOT exceed 48 hours" — tension (default vs max) left unstated, not a hard contradiction. | §5.1 L203 vs §7.2 L256 |

### Cluster 5 — Security / integrity / privacy

| ID | Sev | Finding | Location |
|----|-----|---------|----------|
| **B25** | MED | §1 L18 comment claims `binding_proof` is a "COSE Sig over **canonical LCT fields**", but §3 signs only the 4 `binding` sub-fields. `policy`, `mrh`, `attestations`, `revocation` are **not integrity-protected**. (Canonical signs the same narrow scope — so this is a misleading *comment*, AUTONOMOUS to fix; the broader "is the whole LCT integrity-protected?" question is a real DESIGN-Q shared with canonical.) | §1 L18 / §3 L138–147 / §7.1 |
| **B26** | MED | `revocation` defines a `status` field but **no propagation/check mechanism** (no CRL/OCSP-equivalent, no verification-time MUST-check); §7/§8 assert security effects with no enforcement path. Canonical at least carries an "Honor revocation status" obligation (§7.4 L542) the sister omits. | §2.8 / §7 / §8 |
| **B27** | LOW | §7.3 "Witnesses MUST NOT sign attestations for future timestamps" is unenforceable as written — no reference clock, skew tolerance, or verification path. (C61 reframed the canonical equivalent as advisory/impl-defined; sister still states a bare MUST NOT.) | §7.3 L262 |
| **B28** | INFO | §8 "lct_id SHOULD NOT contain PII" is satisfiable, but since `lct_id = hash(binding_proof)` over a stable `public_key`, the id is a **stable lifetime correlator** across all contexts — worth a privacy note. | §8 L268 / §3 L147 |

### Refuted (5)
- "§4.1 MRH update sub-steps under a MUST header use bare imperatives" — header MUST governs the sub-steps; not a defect.
- `horizon_depth` default 3 — **consistent** between §1 and §2.4.
- "§1 inline comments vs §2 REQUIRED/OPTIONAL field-presence contradiction" — no contradiction found.
- A duplicate framing of B24 (overlap window) that asserted hard contradiction — downgraded to the B24 tension, not refuted-away but merged.
- "§9 IANA `lct:web4:` URI scheme conflicts with data-formats" — the registration request does not conflict; refuted (B19 keeps only the entity-type/revocation registry duplication).

---

## §C — Routing

### D0 — FLAGSHIP DESIGN-Q (operator; gates everything else)
**Is `protocols/web4-lct.md` a maintained sister-doc, or superseded by `core-spec/LCT-linked-context-token.md`?**
This is C60-B13's deferred "sync vs supersede" choice, now escalated because the divergence is structural (B7/B8/B9), not enum-level. **Auditor recommendation: SUPERSEDE** — add a deprecation/SSOT-pointer banner; do not maintain two normative LCT object definitions. If the operator instead chooses *keep & sync*, the AUTONOMOUS findings below define the C75 remediation.

### AUTONOMOUS — apply in C75 **only if D0 = keep/sync** (or as no-regret in-file corrections)
These are wrong under any reading and safe single-file fixes:
- **B1** (HIGH) — close the §1 JSON object (insert `}` before L50 fence).
- **B2, B3, B4** — align the §1 inline enums to the authoritative §2.x definitions (`context` 5 values, `reason` `rotation`, `revocation.reason` add `expired`).
- **B5** — rewrite the `permanent` definition to match its usage (`true` = non-revocable).
- **B25** — fix the §1 L18 comment to state the actual signing scope (the `binding` sub-object, not "canonical LCT fields").
- **B20, B21** — add RFC 2119 keywords to the §3 binding algorithm and §5.1 rotation steps.
- **B7, B8** (only meaningful if *not* superseded) — sync `entity_type` to 15 and add the `t3_tensor`/`v3_tensor` REQUIRED block. *Note: B8 in particular is so large that it is itself an argument for D0 = supersede.*

### DESIGN-Q (operator) — shared/structural, not auto-actionable
- **B14 / B13 / B15** — identifier model: hash-vs-UUID (`lct_id`), segment colon, `subject` DID form. Must reconcile with `did:web4-method.md` corpus-wide; couples with the open C60 lct_id design-Q (H1).
- **B26 / B27** — revocation propagation/check mechanism + future-timestamp enforceability (canonical-shared; C61 partially addressed the canonical side).
- **B10** — REQUIRED-vs-OPTIONAL field-presence model for birth-cert/paired/attestations.

### CROSS-TRACK (sibling-doc owners)
- **B16 / B18** — birth_certificate field set + naming-form vs SAL `Web4BirthCertificate` (§2.2). Folds into the standing SAL operator bundle.
- **B17** — `audit` vs registry `audit-minimal`: align to the Web4 Witness Role Registry (`web4-witnessing.md` §6).
- **B19** — IANA registry-home duplication (entity-types / revocation reasons): folds into the C70 registries-canonicity bundle.
- **B11 / B12 / B6** — revocation `violation`, attestation shape/`nonce`/`claims`, role-vs-type field naming: reconcile against canonical + `web4-witness.md`.

---

## §D — Method notes (for the next AUDIT turn)
1. **A frozen parallel spec generates one root-cause finding wearing 26 masks.** The highest-value output of auditing `protocols/web4-lct.md` was not the 26 line-item defects but the *recognition that maintaining two normative LCT definitions is the defect* — and routing the sync-vs-supersede decision (D0) ahead of any line-item remediation. When a sister-doc is this far behind, lead with the lifecycle question, not the diff.
2. **The `protocols/` cluster has 6 more never-audited sister-docs** (`web4-r6-framework.md`, `web4-dictionary-entities.md`, `web4-entity-relationships.md`, `web4-metering.md`, `web4-witnessing.md`, `web4-witness.md`) — each shadowing a core-spec primitive, each a candidate for the same "is this superseded?" question. Recommend a single operator-level **`protocols/` cluster lifecycle decision** (like C70 did for `registries/`) rather than 6 separate sync audits.
3. **High upheld rate (39/44) is honest here, not a verifier-laxity signal** — but synthesis dedup remained essential (39 → 26): finders independently re-found the same internal enum mismatches under both the internal-consistency and cross-doc lenses.
