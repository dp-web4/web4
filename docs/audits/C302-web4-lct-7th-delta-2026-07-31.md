# C302 — 7th-Delta Re-Audit of `protocols/web4-lct.md` (the frozen LCT sister-doc)

**Date**: 2026-07-31
**Auditor**: Legion autonomous web4 track (slot `web4-20260731-180032`)
**Target**: `web4-standard/protocols/web4-lct.md` (278 lines)
**Type**: **7th-delta re-audit**. Read-only — produces this audit doc, makes **no file edits** (the target is D0-gated).
**Lineage**: C60-B13 → **C74** first audit (#363, 28 findings B1–B28) → **C75** `protocols/` cluster triage (#364) → **C114** 2nd (+N1) → **C146** 3rd (3.1 path correction) → **C186** 4th (C172-N1 scope-widening) → **C224** 5th (3.2 locus 689→718) → **C262** 6th (first empty corpus-delta) → **C302**.
**Snapshot baseline**: target blob `5f68a5c7bda9b1dbcfd81f0324df61243efbaab7` — **byte-frozen since `27b85624` (2026-02-17), 5.5 months**; unchanged since C74/C114/C146/C186/C224/C262 (re-verified: `git rev-parse HEAD:web4-standard/protocols/web4-lct.md` = `5f68a5c7`).
**Corpus window**: C262's audit commit `6d3e0566` (2026-07-24) → HEAD `a6959a8c` (2026-07-31) = **67 commits**.
**Method**: §A prior-finding persistence (binary re-verification, citing the owning pass — not re-litigation). **§A′ carry-row survival census** (method carry v10, born C300 — first ever run on this lineage). §B corpus-delta scan. **§B′ mirror gate re-derived from scratch in BOTH directions** — backward to the lineage's first pass (v8, mirror sets contract) and outward to trees never in the set (v9, a gate is only as good as the tree it is pointed at). Refute-by-default on every candidate; every count and every zero carries its instrument.

---

## Headline (read this first)

The target is byte-identical to its C74→C262 snapshot. §A holds. §B is materially empty. **All four net-new findings come from the instrument, and the two that matter come from the same root cause: for six passes this lineage measured the wrong things well.**

- **N1 (MED, instrument, auditor-applicable):** three C74 findings carry **line anchors into the canonical spec, and all three have been stale since 2026-07-16** — staled by the *same* `#531` insert whose renumber C224 detected and corrected for exactly **one** row. B12's stale anchor now points at the `t3_tensor` block, i.e. at **B8's** evidence.
- **N2 (MED → operator; reach-escalation on B7/B8/B9, **NOT** net-new defects):** the tracked mirror set omitted **every machine-readable LCT artifact in the standard** for six passes (`lct.schema.json`, `schemas/contexts/lct.jsonld`, `test-vectors/lct/`, SDK `lct.py`) — measured zero, 0 mentions in 6/6 audit docs. `web4-standard/schemas/lct.schema.json` is wired into the SDK validator (`validation.py:67`) and **already adjudicates B7, B8 and B9 in canonical's favour, from inside the standard.**
- **N3 (LOW, net-new from §B′):** `lct.schema.json` mints an **8th witnessing role, `peer`**, which no prose spec in the corpus defines and which `web4-witnessing.md:17`'s "new roles MUST be registered" forbids.
- **N4 (LOW, metadata):** C262 §D predicted this file's next slot as "~C296"; the rotation arithmetic gives **C302**.

**The flagship candidate was killed before it was written.** Machine-validating the standard's five LCT test vectors against `lct.schema.json` produces four clean failures — and every one is **C288-N1**, filed *one day earlier* by the sibling canonical-LCT lineage (§E.1). Recorded as a kill, not a finding.

**D0 remains operator-unanswered and gates all remediation. Nothing here edits any file, and nothing here re-decides D0 or the flagship B-D1.**

---

## §A — Prior-finding verification

### A.1 — C74 B1–B28: 28/28 HELD, 0 regression

The target blob is byte-identical to the C74 snapshot, so every **target-internal** line-anchored finding holds by construction. Binary re-verification of the load-bearing rows at live HEAD (owning pass cited; **not** re-argued on the merits, per v10):

| Row | Owner | Binary check at HEAD | State |
|---|---|---|---|
| B1 | C74 | §1 object opens `:10`, no closing `}` before the `:50` fence | HELD |
| B7 | C74 | §2.2 `:63` enumerates **12**; canonical taxonomy **15** | HELD — **reach widened, see N2** |
| B8 | C74 | `t3_tensor`/`v3_tensor` absent from the whole target | HELD — **reach widened (N2); anchor stale (N1)** |
| B9 | C74 | §2.3 birth-cert lacks `issuing_society`, `genesis_block_hash` | HELD — **reach widened, see N2** |
| B11 | C74 | canonical `violation` present at `:521`; sister §2.8 `:130` lists 3 without it | HELD *(first re-verification since C114 — see §A′)* |
| B12 | C74 | canonical `claims` object present at `:194`; sister §2.6 `:107-114` flat `sig`/`ts` | HELD *(first re-verification since C114; **anchor stale**, N1)* |
| B13/B14/B15 | C74 | identifier model — `lct_id = MB32(SHA256(binding_proof))` at `:147` | HELD |
| B16 | C74 | SAL `Web4BirthCertificate` fields absent from §2.3 | HELD |
| B25 | C74 | §1 `:18` "COSE Sig over canonical LCT fields" vs §3 `:138-147` 4-field scope | HELD |
| B26 | C74 | canonical "Honor revocation status" present at `:571` | HELD — **anchor stale (N1)** |

No remediation has landed (D0-gated) → §A is pure persistence. The 5 C74-refuted items remain correctly refuted.

### A.2 — C75 structural defects — both HELD at live HEAD, loci re-grepped

| C75 defect | C262 recorded locus | C302 verification at HEAD | Disposition |
|---|---|---|---|
| **3.1 README SSOT inversion** | `web4-standard/README.md:64` | `grep -n "protocols/web4-lct.md" web4-standard/README.md` → `64:- [**protocols/web4-lct.md**](protocols/web4-lct.md) - Linked Context Token specification`. Verbatim. README freeze `d89595e8` unchanged. | **HELD — REAL**, locus stable |
| **3.2 Canonical-defers-to-frozen** | `LCT-linked-context-token.md:718` | `grep -n "protocols/web4-lct.md"` → **`:718`**. Canonical frozen `d89595e8`; no insert this cycle. | **HELD — REAL**, locus stable |

### A.3 — C114-N1 (internal `claims` cross-section contradiction): HELD

Byte-frozen → holds by construction. §2.6 `:107-114` enumerates four attestation fields (`witness`/`type`/`sig`/`ts`) with **no** `claims`; §6.1 `:221` carries a "Required Claims" column and §6.2 `:237` shows a `claims:{}` object. Both normative halves unchanged. `web4-core/src/attestation.rs` did not move (§B). N1 stays **blocked-on-D0**, not self-applied.

### A.4 — C56 claim-vs-canonical re-read

Every cited canonical source is frozen at or before the C262 baseline: canonical `LCT-linked-context-token.md` `d89595e8` (2026-07-16), `entity-types.md` `5baa160f`, SAL, `forum/nova/web4-witnessing.md` (2025-09-14). **No canonical doc moved in this window** → no B-line cross-doc *claim* went stale on the content axis this cycle. (The *anchors* were already stale before this cycle opened — that is N1, and it is a debt from the C224 window, not a C302-window event.)

---

## §A′ — Carry-row survival census (method carry v10 — first run on this lineage)

C300 established that a clean streak can be a carry ledger silently *emptying*. This lineage has published **"28/28 HELD, 0 regression"** in five consecutive passes (C114, C146, C186, C224, C262) while individually naming at most nine rows. The census asks whether the 28 rows are actually being carried.

**Instrument:** `grep -oE '\bB<n>\b' <audit-doc> | wc -l`, run over the six lineage docs at HEAD `a6959a8c`.
**Collider baseline (v10):** `\bB1\b` does **not** match `B10`–`B19` (trailing `\b` fails against a digit) — verified. `\bB7\b` does **not** match the other lineages' hyphenated carry labels `B-7`/`B-D1` — verified. No label in this lineage was re-bound mid-lineage.

| row | C74 | C114 | C146 | C186 | C224 | C262 | class |
|---|---|---|---|---|---|---|---|
| B1 | 2 | 3 | 4 | 4 | 4 | 4 | internal |
| B2 | 3 | 2 | 1 | 1 | 1 | 1 | internal |
| **B3** | 2 | 1 | **0** | **0** | **0** | **0** | internal |
| **B4** | 5 | 1 | **0** | **0** | **0** | **0** | internal |
| B5 | 2 | 2 | 1 | 1 | 1 | 1 | internal |
| **B6** | 2 | 1 | **0** | **0** | **0** | **0** | internal |
| B7 | 3 | 3 | 2 | 3 | 2 | 3 | cross-doc |
| B8 | 4 | 3 | 2 | 3 | 2 | 2 | cross-doc |
| B9 | 2 | 3 | 2 | 3 | 3 | 3 | cross-doc |
| B10 | 2 | 2 | 1 | 1 | 1 | 1 | cross-doc |
| **B11** | 2 | 1 | **0** | **0** | **0** | **0** | **cross-doc** |
| **B12** | 3 | 3 | **0** | **0** | **0** | **0** | **cross-doc** |
| B13 | 8 | 3 | 2 | 4 | 3 | 3 | cross-doc |
| B14 | 2 | 2 | 1 | 2 | 2 | 2 | cross-doc |
| B15 | 2 | 2 | 1 | 2 | 2 | 2 | cross-doc |
| B16 | 2 | 3 | 2 | 2 | 2 | 2 | cross-doc |
| B17 | 2 | 3 | 1 | 1 | 1 | 1 | cross-doc |
| B18 | 2 | 2 | 1 | 1 | 1 | 1 | cross-doc |
| B19 | 3 | 2 | 1 | 1 | 1 | 1 | cross-doc |
| **B20** | 2 | 1 | **0** | **0** | **0** | **0** | internal |
| **B21** | 2 | **0** | **0** | **0** | **0** | **0** | internal |
| **B22** | 1 | **0** | **0** | **0** | **0** | **0** | internal |
| **B23** | 1 | **0** | **0** | **0** | **0** | **0** | internal |
| **B24** | 3 | 2 | **0** | **0** | **0** | **0** | internal |
| B25 | 2 | 5 | 3 | 2 | 2 | 2 | internal |
| B26 | 2 | 2 | 1 | 1 | 1 | 1 | cross-doc |
| B27 | 2 | 2 | 1 | 1 | 1 | 1 | internal |
| B28 | 1 | 3 | 3 | 3 | 3 | 3 | internal |

**Result: 10 of 28 rows went to zero mentions and stayed there.** But the census does **not** reproduce C300's finding, and saying so is the honest reading:

- **8 of the 10 silent rows are target-internal** (B3, B4, B6, B20–B24, and B12's internal half). For these, byte-identity of the target genuinely *is* a sufficient warrant. The "28/28 by construction" claim is sound for them. **No finding.**
- **2 of the 14 cross-doc rows fell silent: B11 and B12.** For a cross-doc finding, byte-freeze of the target holds only *one* half — if the canonical had dropped `violation` (B11) or flattened its `claims` object (B12), the finding would dissolve unnoticed. Both were re-verified here at live HEAD for the first time since C114: **both HELD** (canonical `:521`, `:194`). So no defect was missed.
- **C224's §A.4 partially covers the gap** by checking that the *sources* were frozen rather than the rows — a weaker but non-empty warrant, and it is why the ledger did not actually empty.

**The census's real yield is not a dropped row. It is N1** — the discovery that going silent stopped the rows from being *maintained*, which is a different failure from being dropped, and which the mention-count exposed.

---

## §B — Corpus-delta scan

### B.1 — The window: 67 commits, 3 files in `web4-standard/`, **0 in `web4-core/`**

**Instrument:** `git diff --stat 6d3e0566..a6959a8c -- <tree>`.

| File | Change | web4-lct relevance |
|---|---|---|
| `web4-standard/proposals/dictionary-as-context-mandatory-role.md` | +163 (new) | **none** — `lct_id` hits: 0 |
| `web4-standard/proposals/resilience-to-incomplete-information.md` | +170 (new) | **none** — `lct_id` hits: 1, incidental |
| `web4-standard/ontology/t3v3-ontology.ttl` | +18/−4 | adds `web4:Tensor`, re-domains `web4:entity` ("The LCT entity this tensor measures") |

**Tier check before charging anything (per [[feedback_read_the_specs_meta_structure]] and the C268/C270/C272 "canonized principle re-scopes a frozen file" pattern):** both movers are `proposals/` tier, fleet-review status. **They claim no authority over canon**, so the re-scoping pattern does **not** fire and no defect is charged against the frozen sister for either. Stated explicitly because the pattern's trigger is "what landed claiming authority over the target's subject matter" — and here the answer, checked, is *nothing*.

The `t3v3-ontology.ttl` change sits on the **B8 axis** (sister omits `t3_tensor`/`v3_tensor`). It is owned by the **t3-v3 lineage**; noted and routed, **not annexed**.

### B.2 — `web4-core/` — a measured zero, not a re-confirmation

```
git log --oneline 6d3e0566..a6959a8c -- web4-core/   →  0
```

**`web4-core/` received 0 commits in this window.** Per binding condition 2 of this session's policy review, this is published as a measured zero rather than reported as a "gate re-confirmed": re-running an SDK gate over an unmoved tree and calling the result a fresh verdict is the C298/C300 error verbatim. Freeze commits re-derived at HEAD (not inherited from C262):

| Artifact | Last-touching commit | Blob at HEAD |
|---|---|---|
| `web4-core/src/lct.rs` | `2ec6ae09` 2026-07-18 | `2e9d4586` |
| `web4-core/src/attestation.rs` | `0e997079` 2026-07-17 | `8bffe03a` |
| `web4-core/src/ratchet.rs` | `7b048a78` 2026-07-16 | `806882b1` |
| `core-spec/LCT-linked-context-token.md` | `d89595e8` 2026-07-16 | `231d70b5` |
| `web4-standard/README.md` | `d89595e8` 2026-07-16 | `a8eb4120` |

Consequences, stated as entailments rather than findings: C114-N1's SDK direction-witness holds by construction; C172-N1 holds; and — per binding condition 4 — **no 5th D0=SUPERSEDE witness is claimed**, because the code did not move. (N2 has something to say about what that witness *count* is actually measuring.)

---

## §B′ — Mirror gate, re-derived in both directions

C262 tracked **six** artifacts: the target, canonical, `README.md`, `lct.rs`, `attestation.rs`, `ratchet.rs`. Per v8/v9 that set is not inherited here; it is re-derived from the question *"what, at HEAD, specifies or implements the LCT object the target defines?"*

### B′.1 — Outward sweep: trees searched, with counts

**Instrument:** `git grep -l <token> HEAD -- <tree> | wc -l` at HEAD `a6959a8c`. Tokens are the target's own §1 field names. Every tree searched is listed, including the ones that came back empty — a negative gate must publish its paths ([[feedback_gate_scoped_to_wrong_tree]]).

| tree searched | `birth_certificate` | `entity_type` | `lct_id` | cites `protocols/web4-lct.md` | in C262 set? |
|---|---|---|---|---|---|
| `web4-standard/schemas/` | 4 | 6 | 8 | 0 | **NO** |
| `web4-standard/test-vectors/` | 7 | 11 | 10 | 0 | **NO** |
| `web4-standard/implementation/sdk/web4/` | 3 | 8 | 8 | 0 | **NO** |
| `web4-standard/ontology/` | 1 | 0 | 0 | 0 | **NO** |
| `core/` (`core/lct_binding/`, 13 files) | 5 | 8 | 8 | 0 | **NO** |
| `hub/` | 0 | 6 | 17 | 0 | **NO** |
| `web4-core/` | 2 | 5 | 13 | 0 | yes |
| `mcp-server/` | 0 | 1 | 2 | 0 | no |
| `mcp-servers/` | 0 | 0 | 1 | 0 | no |
| `demos/` | 0 | 2 | 2 | 0 | no |
| `integration/` | 0 | 0 | 0 | 0 | no |
| `governance/` | 0 | 0 | 0 | 0 | no |

**Gate rulings.**
- `hub/` — **M-DECLINED on subject matter.** 0 `birth_certificate` hits; its `entity_type` surface is `hub-daemon/src/main.rs:517-541` `CliEntityType`, whose own comment declares it a *"Subset of `web4_core::EntityType` exposed via CLI"*. A declared subset of an already-audited enum is not an independent LCT definition. Re-run only if `hub/` gains its own birth-certificate or LCT-object construction.
- `core/lct_binding/` — **M-DECLINED, routed.** Real LCT surface, but it is the **hardware-binding / TPM2** lane (`ek_attestation.py`, `tpm2_provider.py`, `trustzone_provider.py`), last touched `5ddbfd9b` 2026-04-27. Its subject is §2.2 `hardware_anchor`, not the §1 object. Routed to the AttestationEnvelope / hardware-binding track; **not annexed**.
- `mcp-server*/`, `demos/`, `integration/`, `governance/` — **M1-FAIL**, below threshold.
- `web4-standard/schemas/` + `test-vectors/` + `implementation/sdk/web4/` — **M-ADMITTED.** See B′.2.

### B′.2 — The admitted set, and the measured zero that matters

**Instrument:** `grep -c '<token>' <audit-doc>` over all six lineage docs.

| token | C74 | C114 | C146 | C186 | C224 | C262 |
|---|---|---|---|---|---|---|
| `lct.schema.json` | 0 | 0 | 0 | 0 | 0 | 0 |
| `schemas/` | 0 | 0 | 0 | 0 | 0 | 0 |
| `test-vectors` | 0 | 0 | 0 | 0 | 0 | 0 |

**Zero mentions in 6 of 6 passes.** The lineage that audits the LCT *object definition* has never once looked at the standard's machine-readable definition of that object. This is the C296 contracting-mirror-set mechanism in its more embarrassing form: the set did not contract — **these artifacts were never in it.**

What is in there (`web4-standard/schemas/lct.schema.json`, last touched `9bcfe598` 2026-02-22; `title: "Linked Context Token (LCT)"`, `additionalProperties: false`):

| construct | value at HEAD |
|---|---|
| `required` (root) | `lct_id`, `subject`, `binding`, `birth_certificate`, `mrh`, `policy` |
| `properties` | …+ **`t3_tensor`**, **`v3_tensor`**, `attestations`, `lineage`, `revocation` |
| `binding.entity_type.enum` | **15** — `human, ai, society, organization, role, task, resource, device, service, oracle, accumulator, dictionary, hybrid, policy, infrastructure` |
| `birth_certificate.required` | **`issuing_society`**, `citizen_role`, `context`, `birth_timestamp`, `birth_witnesses` |
| `mrh.witnessing.role.enum` | **8** — `time, audit, oracle, **peer**, existence, action, state, quality` |

And it is **live, not decorative**: `implementation/sdk/web4/validation.py:67` maps `"lct-raw" → "lct.schema.json"`, and the schema is bundled byte-for-byte into `implementation/sdk/web4/schema_registry.json`.

**Self-consistency check of the two copies** (per [[feedback_does_the_impl_agree_with_itself]] — two copies of one enumeration in one artifact *is* the finding, so it must be tested before anything else): `json.dumps(src, sort_keys=True) == json.dumps(registry_copy, sort_keys=True)` → **True**. **Negative result, published.** The copies agree; the source and its bundle are not a divergence axis here.

---

## §C — Net-new findings

### N1 — MED (instrument, auditor-applicable). Three C74 canonical line-anchors have been stale since 2026-07-16; C224 fixed exactly one of the four and re-verified a second in the same pass without noticing

Four C74/C75 rows carry a **line number into `core-spec/LCT-linked-context-token.md`**. `#531` (`d89595e8`, 2026-07-16) inserted §1.2 near line 23, growing the file 694→726 lines and shifting everything below by **+29**.

| row | anchor as recorded | correct at `d89595e8^` | actual at HEAD | drift | corrected by |
|---|---|---|---|---|---|
| C75 **3.2** | `:689` | `:689` ✓ | `:718` | +29 | **C224** ✓ |
| **B8** | "canonical §364" (`Every LCT MUST contain a \`t3_tensor\``) | `:364` ✓ | **`:393`** | +29 | **never** |
| **B12** | "canonical §2.3 **L161-172**" (`claims` object) | `:161-172` ✓ *(exact match)* | **`:190-201`** (`claims` at `:194`) | +29 | **never** |
| **B26** | "canonical §7.4 **L542**" (`Honor revocation status`) | `:542` ✓ | **`:571`** | +29 | **never** |

Verified by reading both revisions: `git show d89595e8^:…| sed -n '158,175p'` returns the `attestations`/`claims` block; `sed -n '158,175p'` at HEAD returns the **`t3_tensor`** block.

**Two things make this a finding rather than a typo.**

1. **B12's stale anchor now points at B8's evidence.** A remediator following the ledger to "canonical §2.3 L161-172" for the attestation-shape divergence lands on the tensor block — the subject of a *different* open row in the same ledger. It reads as correct and is not.
2. **The discipline existed and fired, and was still applied per-narrated-row rather than per-anchor.** C224 §A.2 corrected 3.2 689→718, and C224 §lesson-1 wrote the general rule: *"A frozen target does not mean a frozen inbound locus; a sibling's insertion moves your recorded line."* In that same pass C224 named **B8 twice** — and B8's anchor into the same file, moved by the same insert, was not re-resolved. B12 and B26 had been silent since C146, so they were not in the set the discipline was applied to at all.

**All three underlying findings HELD** (B8: `:393`; B12: `:194`; B26: `:571`) — nothing was missed. The defect is in the ledger's navigability under D0=SUPERSEDE, where these anchors are the lines a remediator would work from.

**Correction issued here, in the lineage's own C224 precedent** ("audit-record updated 689→718"; past audit docs are not rewritten): **B8 → `LCT-linked-context-token.md:393`; B12 → `:190-201` (`claims` at `:194`); B26 → `:571`.** Inherit these verbatim.

**Method carry v11 (proposed).** When a sibling artifact moves, re-resolve **every anchor the ledger holds into that artifact**, not just the anchors in rows you are narrating this pass. The unit of the path-provenance discipline is the *anchor*, not the *paragraph*. → extends [[feedback_prior_finding_path_provenance]].

### N2 — MED → OPERATOR (reach-escalation on B7/B8/B9; **NOT** net-new defects). The standard's own machine-readable LCT schema already adjudicates three of this lineage's structural rows, and six passes never read it

Per [[feedback_carry_gains_reach_not_truth]], a carry that acquires new consumer surfaces routes as reach-escalation, never as net-new. B7, B8 and B9 are C74's; their **truth** is unchanged. What changed is that the gate finally looked where the evidence was.

| row | as recorded by C74 | evidence added at HEAD |
|---|---|---|
| **B7** — `entity_type` 12 vs 15 | doc-vs-doc lag against `entity-types.md` | `lct.schema.json` `binding.entity_type.enum` = **15**, and SDK `lct.py` `EntityType` = the **same 15**, `additionalProperties:false` |
| **B8** — sister omits `t3_tensor`/`v3_tensor` | prose gap against canonical `:393` | `lct.schema.json` declares **both** as properties |
| **B9** — sister birth-cert lacks `issuing_society` | prose gap against canonical | `lct.schema.json` `birth_certificate.required` **includes `issuing_society`** |

Three of the lineage's four HIGH/MED structural cross-doc rows are already decided, in canonical's favour, by an executable artifact **inside `web4-standard/` and wired into the SDK's validator**. The sister is not lagging a sibling prose document pending a design decision; it contradicts the standard's own conformance surface. That is a materially different posture for D0 — argued both ways below.

**Argued both ways (per v10).**
- *For MED:* it strengthens the SUPERSEDE case at zero cost to the MAINTAIN case, and it changes what a remediator must reconcile — three rows resolve by deletion rather than by adjudication.
- *For LOW:* nothing is newly broken; the schema has been at 15 since `9bcfe598` (2026-02-22), five days after the sister froze. This is entirely an instrument failure. **MED is chosen** because the mis-scoped gate suppressed evidence bearing on an open operator decision for six passes, which is the same harm class as C298-N1.

**A note on the D0 trend meter, and it is uncomfortable.** C186 and C224 built the SUPERSEDE case as a *witness count* (now 4), where each witness is a **code motion** in `web4-core/`. C302 adds no 5th witness, correctly, because the code did not move. But this pass shows the evidence base was **already wider than 4 the whole time** — it was sitting unread in the standard's own schemas. The meter was measuring *how often the Rust moved*, not *how much evidence exists*. That is a defect in the metric, not in D0. **Flagged to the operator alongside D0; deliberately not folded into the witness count.**

### N3 — LOW (net-new from §B′). `lct.schema.json` mints an 8th witnessing role, `peer`, that no prose spec defines

`mrh.witnessing[].role` is enumerated four incompatible ways at HEAD:

| artifact | values | n |
|---|---|---|
| sister `web4-lct.md` §2.4 `:97` | `time`, `audit`, `oracle` | 3 |
| canonical `LCT-linked-context-token.md` §5.2.3 `:366` | `time`, `audit`, `oracle`, `existence`, `action`, `state`, `quality` | 7 |
| `schemas/lct.schema.json` | the above 7 **+ `peer`** | **8** |
| `forum/nova/web4-witnessing.md` §6 IANA `:101-104` | `time`, `audit-minimal`, `oracle` | 3 |

The 3-vs-7 axis is **B6**; the `audit` vs `audit-minimal` axis is **B17**; both are C74's and are **not** re-opened. The net-new content is exactly one token: **`peer`**. It appears in the standard only in `lct.schema.json`, its `schema_registry.json` bundle, and three `demos/hello-web4/` files. **No prose spec in the corpus defines it** — and `web4-witnessing.md:17` states *"Roles are extensible; new roles MUST be registered in the Web4 Witness Role Registry."* `peer` is not in the registry's initial entries and has no registration record.

**Prior-art refutation (published):** `grep -rln '"peer"' docs/audits/` → **0 files**. `grep -c -w peer` over C288 (the sibling canonical-LCT 7th delta, 2026-07-30) → **0**. No pass in any lineage has recorded this.

Severity **LOW**, argued down deliberately: `additionalProperties:false` means the schema is *permissive* here relative to the specs, so nothing valid is rejected; the harm is registry drift, not interoperability failure. Routed to the **witness-registry track**, not to D0.

### N4 — LOW (metadata calibration)

C262 §D records this file's next slot as **"~C296"**. The rotation arithmetic (last-pass C# + 40) gives **C302**; C296 was in fact the security 7th delta. Recorded because C262's own lesson 3 was that audit metadata drifts — and it then committed that error class in its own next-delta guard. **Next web4-lct delta: C342** (see §D for why that should be conditional).

---

## §E — Killed candidates (published, per "refute your BEST finding")

### E.1 — THE FLAGSHIP, KILLED: LCT test vectors fail the standard's own LCT schema

Machine-validating `test-vectors/lct/*.json` (`expected_output`) against `schemas/lct.schema.json` with `jsonschema.Draft7Validator`:

```
interop-human-full.json      should_succeed=true  → 2 errors
   /binding/hardware_anchor : 'tpm2:sha256:abcdef1234' does not match '^eat:[A-Za-z0-9_-]+$'
   /birth_certificate       : 'context' is a required property
interop-minimal-interop.json should_succeed=true  → 1 error  (same 'context')
interop-revoked-agent.json   should_succeed=true  → 1 error  (same 'context')
```

Three vectors asserting `should_succeed: true` fail the standard's own schema, and the missing field is `birth_certificate.context` — **REQUIRED by the target's own §2.3 `:74`**. This was the strongest candidate of the pass by a wide margin.

**It is C288-N1**, filed **2026-07-30 — one day before this pass** — by the sibling canonical-LCT lineage (`docs/audits/C288-lct-linked-context-token-7th-delta-2026-07-30.md:119-126`), which also identified the root cause (`650518d9` renamed `context`→`birth_context` across `lct.py`, 3 test files and all 5 vectors, and **did not touch `lct.schema.json`**) and the second arm (`9bcfe598` fixed the colon class for `lct_id` only, leaving `hardware_anchor`'s pattern colon-hostile).

**KILLED as net-new. Not re-filed, not co-claimed, not restated as a "reach escalation."** It is the sibling's finding, one day old, already routed. The sibling-doc guard ([[feedback_cross_doc_carry_inbound]]) caught it *before* it was written into §C — which is the only reason this document does not open with a duplicate.

The honest note is that this pass would have found it independently, from the mirror gate, had the gate been correctly scoped six passes ago. The instrument failure N2 records is real and this is its cost: **the sister lineage had to be told by its sibling.**

### E.2 — Rust `EntityType` = 9 vs schema/SDK = 15

Genuine divergence, **owned by the entity-types lineage**: C176-N1, re-verified as "STANDS unchanged" by **C292** on 2026-07-30 (`docs/audits/C292-entity-types-7th-delta-2026-07-30.md:73`), first noted in C172. **Not annexed.**

### E.3 — Sister-internal enum mismatches surfaced during the schema diff

`§1 :48 "reason":"rotate"` vs §2.7 `:121` `rotation` = **B3**. `§1 :22` context 3-vs-5 = **B2**. `§1 :49` revocation reason 2-vs-3 = **B4**. All C74's, all HELD, none re-opened. Noted only because the schema comparison re-surfaced them and a reader deserves to know they were checked and correctly attributed.

### E.4 — No 5th D0=SUPERSEDE witness

`web4-core/` = 0 commits. Declined by construction, per §B.2.

### E.5 — `proposals/` movers

Both window movers are `proposals/` tier and claim no authority over canon. **No defect charged.**

---

## §F — Self-corrections made during this pass

1. **The `peer` finding was initially drafted at MED** on the strength of the four-way enumeration table. Re-reading the table, three of the four axes are B6 and B17. Downgraded to **LOW** and the net-new claim narrowed to the single token `peer`.
2. **The census was initially drafted as a C300-style "the ledger emptied" finding** on the strength of 10 zero-rows. Classifying internal vs cross-doc collapsed it to 2 rows, both of which HELD on re-verification. The census's yield was re-framed from *ledger emptying* to *anchor decay* — a different and smaller finding (N1). Publishing the deflation because the first draft was the more impressive claim and it was wrong.
3. **`hub/` was initially admitted to the mirror set** on `entity_type`=6 / `lct_id`=17. Reading the hits showed `CliEntityType` self-declares as a subset of an already-audited enum. **M-DECLINED**, and the counts published anyway so the ruling is checkable.
4. **The post-write verification pass caught three wrong cells in N1 and N3 — in the very finding that is *about* wrong line numbers.** Drafted: B12 pre-`#531` block "`:161-175`", B12 at HEAD "`:190-200`", registry "`:101-103`". Re-measured: **`:161-172`** (an *exact* match to C74's recorded L161-172, which strengthens N1 — C74's anchor was precisely right when written), **`:190-201`**, and **`:101-104`** (§6 IANA Considerations). Corrected above. The verifier was confirmed to have actually run (`exit=0`, four anchor values returned) before its agreement was accepted — per v10, a verification run that agrees with the draft has confirmed nothing until you confirm the verifier ran.

---

## §G — Carry ledger (restored in full; inherit verbatim)

| ID | Class | State after C302 |
|---|---|---|
| **B1–B28** | C74 | **28/28 HELD, 0 regression.** Anchors for **B8/B12/B26 corrected** — see N1 |
| **C75 3.1 / 3.2** | structural | HELD-REAL; loci `README.md:64`, canonical `:718` |
| **C114-N1** | internal `claims` contradiction | HELD; D0-blocked |
| **C172-N1** | `derive_lct_id` key-derived | HELD (`web4-core/` unmoved) |
| **C302-N1** | instrument, auditor-applicable | **DISCHARGED by this doc** (anchor corrections published); method carry v11 proposed |
| **C302-N2** | reach-escalation on B7/B8/B9 | **→ OPERATOR**, adjudicate **WITH D0 and B-D1**. Do not self-resolve |
| **C302-N3** | witness-role registry drift | **→ witness-registry track** |
| **C302-N4** | metadata | discharged here |
| **D0** | DESIGN-Q | **operator-unanswered; gates all `protocols/` remediation** |
| **B-D1** | flagship SSOT inversion | unanswered |

---

## §D — Guards for the next delta

1. **Mirror set for the 8th delta = the C302 B′.1 table, RE-DERIVED not re-read.** Inheriting even this corrected 12-tree list reproduces the exact mechanism N2 records ([[feedback_mirror_set_contracted]]).
2. **Re-run the anchor sweep, not just the two 3.1/3.2 greps.** The ledger holds four line-anchors into `LCT-linked-context-token.md` (3.2 `:718`, B8 `:393`, B12 `:190-201`, B26 `:571`). If canonical moves at all, re-resolve **all four**. This is N1's method carry v11 and it is the single most likely thing to rot again.
3. **Check C288's successor before writing §C.** The canonical-LCT lineage audits the same subject matter one slot ahead and beat this pass to its own flagship by one day (§E.1). Read the sibling's latest audit doc *first*.
4. **`web4-core/` must be re-measured, not assumed.** It has been at 0 commits for one window; two consecutive zeros would make the SDK half of the gate a formality that should be stated as such rather than performed.
5. **Do not mint a 5th D0=SUPERSEDE witness from N2.** N2 widens the *evidence base*; the witness count measures *code motion*. Conflating them would double-count.

**Cadence recommendation (feeds the open CADENCE design-Q).** This pass fully exercised the instrument on this lineage: the mirror set is now derived outward across 12 trees, the ledger has its first survival census, and every canonical anchor has been re-resolved. The target has been byte-frozen 5.5 months and `web4-core/` is at zero. **The 8th delta (C342) should be justified by an event trigger — motion in the target, the canonical, `web4-core/`, or `schemas/lct.schema.json` — rather than taken automatically by rotation.** If nothing in that set has moved by C342, a one-line no-motion attestation is the proportionate output. Recorded for the operator; **not self-applied** — the rotation stands until the operator rules.

---

## Accountability self-audit

```
surface: C302 audit document   act: publish audit findings that route an operator decision
S: low/reversible [construct: read-only doc; zero file mutations outside docs/audits/]
R: n/a [construct: no caller-driven path created]
W: n/a [construct: no identity or authority asserted; findings route, do not decide]
O: pass [construct: refutation checks (§E) precede §C authorship; the flagship was killed pre-write]
A: pass [construct: every count carries its grep + tree + commit; every zero names its token; §F publishes the self-corrections]
V: present [construct: §E kill-list + §D guard 5 — the pass can and did veto its own strongest finding]
verdict: PASS
```

*No file outside `docs/audits/` was created or modified. `protocols/web4-lct.md` is untouched; D0 is unanswered and stands.*
