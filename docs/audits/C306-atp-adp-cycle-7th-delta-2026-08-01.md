# C306 Audit: `atp-adp-cycle.md` Seventh Delta Re-Audit (prior C118/C119 · C150/C151 · C190 · C228 · C266)

**Date**: 2026-08-01
**Auditor**: Autonomous session (Legion, web4 track) — single-auditor refute-by-default; independent policy-review subagent approved the scope before any evidence was gathered.
**Document**: `web4-standard/core-spec/atp-adp-cycle.md` (804 lines, blob `2d060579`)
**Lineage**: C11 (#224) → C34 (#276/#277) → C78/C79 (#367/#368) → C118 (#418) → C119 (#420) → C150 (#475) → C151 (#477 `256ab51d`) → C190 (#514) → C228 (#551) → C266 (#575 `ba2426bd`) → **C306** (this, 7th delta).
**Baseline**: C266 audit doc; baseline commit `ba2426bd` (2026-07-24).
**Method**: method carries **v2–v12** applied. The pass's centre of gravity is **v7/v12**: the standard's own published **non-prose** artifacts (schemas, JSON-LD contexts, test vectors, conformance suites, deployment configs) are normative **PEERS**, not lagging mirrors — and a census showed **0 of 7** lineage passes had ever read any of them.
**Mutation**: **ZERO.** Read-only audit turn. No spec, SDK, schema, vector or config byte was changed. Every finding routes to an owner.

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 0 | — |
| **MEDIUM** | **2** | **N1** (dual ATP vector suites share the `atp-001`–`atp-005` identifier namespace for five different tests; SDK cites bare IDs into it) · **N2** (the standard's production deployment guide installs two files from a path they were deleted from on 2026-05-12) |
| LOW | 0 | — |
| INFO | 3 | I-3 (proposal #580's suspended-action ATP-reservation question — forward note) · I-4 (carry row `B6-SDK` gapped for two consecutive passes, recovered) · I-5 (C158's JSONC INFO-corpus carry never reached this ledger — binary re-verification) |
| **Refuted / deflated in-pass** | **3** | ontology term non-resolution · unparseable `json` fences · schema-validation vector disagreements (all three died on their own baselines — see §F) |

**Result: the "3rd consecutive zero-routed / first fully-EMPTY corpus-delta" certification at C266 was computed over a mirror set that never contained the standard's own ATP artifacts.** The target is byte-frozen (25 days), `web4-core/` moved zero bytes, and the spec-side corpus delta is 3 commits — none touching ATP. Every one of those facts is confirmed below. They are also exactly why the prose-and-SDK surface yields nothing: the **remaining** surface is the standard's own published non-prose artifacts, and this pass reads them for the first time in the lineage's history. Two MEDIUMs live there.

---

## §0 — The blind spot, measured

Instrument (run at `0fb9d952`, from repo root):

```bash
for d in C34 C78 C118 C150 C190 C228 C266; do
  f=$(ls docs/audits/${d}-*.md | head -1)
  grep -c -E "atp-jsonld|contexts/atp|test-vectors/atp|conformance/atp|demurrage\.example|schema-validation/atp" "$f"
done
```

| Standard-internal ATP artifact | Lines | C34 | C78 | C118 | C150 | C190 | C228 | C266 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `schemas/atp-jsonld.schema.json` | 127 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `schemas/contexts/atp.jsonld` | 55 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `test-vectors/atp/transfer-operations.json` | 302 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `test-vectors/schema-validation/atp-jsonld-validation.json` | 347 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `testing/conformance/atp-operations.json` | 137 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `deployment/config/demurrage.example.json` | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **total** | **993** | | | | | | | |

**993 lines, 0/7 passes.** Widened per the policy reviewer's independent re-measurement: those tokens return **zero hits across all 196 audit docs in the repo**. The `deployment/` tree is cited by **1 of 196** audit docs and **0 of 7** in this lineage:

```bash
grep -rl "deployment/" docs/audits/ | wc -l          # → 1
for d in C34 C78 C118 C150 C190 C228 C266; do        # → 0 0 0 0 0 0 0
  grep -ciE 'demurrage_service|deployment/|systemd|web4-demurrage' $(ls docs/audits/${d}-*.md|head -1); done
```

This is the C288 trap (frozen target + frozen *known* mirrors is not a clean bill) and the C304 shape (the evidence lived in an artifact read by 0/7 of the lineage) firing a third time on a third lineage.

---

## §A — Prior-finding persistence at LIVE HEAD

Target **byte-frozen since C151** (`256ab51d`, 2026-07-07): `git diff 256ab51d..HEAD -- web4-standard/core-spec/atp-adp-cycle.md` is empty; HEAD blob `2d060579` == the C266-recorded blob. All C151 / C119 / C79 fixes **HELD by byte-identity**, re-read live. C118-N2 remains CLOSED (t3-v3 C122); C166 GUARD remains CONSUMED (C190) — neither re-opened.

### §A.1 — Anchor re-resolution (method carry **v11**: grep the anchor's CONTENT, not the line)

Every `<file>:<line>` this ledger holds, re-resolved at live HEAD rather than re-asserted:

| Carry | Recorded anchor | Live-HEAD grep | Verdict |
|---|---|---|---|
| M2 (authority check) | `:184` | `has_slashing_authority` → **L184** | **CORRECT** |
| M2 (slash cap) | `:194` | `amount=min(amount, get_entity_stake(violator))` → **L194** | **CORRECT** |
| M2 / I-1 (governance cap) | `:547` | `max_slash_per_event` → **L547** | **CORRECT** |
| I-1 (`slash_violations` power) | `:541` | `slash_violations` → **L541** | **CORRECT** |
| B8-inbound (MUST #5 referent) | `:621` | `Discharging MUST occur through R6` → **L621** (+ L326 carve-out back-ref) | **CORRECT** |
| B2b (§5.3 exchange) | `:511-512` | `source_society.pool.discharge` / `target_society.pool.charge` → **L511-512** | **CORRECT** |

**No anchor drift.** Expected — the target is byte-frozen and all six anchors are target-internal. Per v11, this is the *correct* result to publish: byte-freeze warrants internal rows and does **not** warrant cross-doc rows.

### §A.2 — Direction re-derivation (method carry **v12**)

Each carry re-asked *which side the corpus agrees with*, not merely whether the divergence is still present:

| Carry | Direction re-derived | Status |
|---|---|---|
| **B1** (§5 abstract-FX vs mcp §7.7 referent-grounding) | Neither side moved; mcp byte-frozen since C226 (C264, C304 confirm). Direction **unchanged** — genuinely a design question, not a stale-side defect. | STILL OPEN (DESIGN-Q) |
| **B2b** (§5.3 exchange bypasses MUST #4/#5/#6) | atp-adp-internal; §5.3 and §7.1 are both frozen in the same blob. No external peer to invert against. | STILL OPEN (DESIGN-Q) |
| **M2** (§2.4 cap never references §6.1 `max_slash_per_event`) | Re-verified at L194 vs L547: the §2.4 cap is **entity-stake-bounded**, the §6.1 constant is a **governance** cap, and nothing links them. Direction **confirmed** — this is a gap, not an inversion. | STILL OPEN (DESIGN-Q) |
| **ISP-B10** (commitment-ATP charged-vs-allocated) | ISP frozen since C63 (C250, C290 confirm). Unchanged. | STILL OPEN (DESIGN-Q) |
| **B3 / B4 / I2 / B6-SDK** | `atp.py` blob `efa5de3c` byte-identical to C228/C266; `web4-core/` zero bytes since C228. **New this pass:** §B″.1 confirms `atp.py`'s JSON-LD output validates **cleanly** against the standard's own schema, so none of these is a schema-direction defect. | STILL OPEN (SDK-track) |
| **X1** (`lct:web4:` identifier) | C33 corpus decision, corpus-wide. Unchanged. | STILL OPEN (CROSS-TRACK) |
| **B8** (inbound, acp C158) | Re-derived: atp-adp §7.1 MUST #5 at **L621** is the correct-side referent; the gap is acp-side. **Direction confirmed, atp-adp is the correct side.** | STANDS (acp-owned) |

**No inversions found.** Publishing that explicitly: v12 was born from an inverted carry at C304, and a pass that applies it and finds nothing must say so rather than let silence imply the check was skipped.

### §A.3 — Carry-ROW survival census (method carry **v10**), with collider baselining

Counts are `re.findall` over each doc with negative-lookaround boundaries; the collider column is the count of the label's confusable neighbours (`B1[0-9]`, `M2[0-9]`, …) that a naive `\bB1\b` would absorb.

| label | C34 | C78 | C118 | C150 | C190 | C228 | C266 | collider hits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 | 0 | 15 | 6 | 2 | 2 | 3 | 3 | **23** |
| B2b | 0 | 4 | 5 | 4 | 3 | 3 | 3 | 0 |
| M2 | 6 | 8 | 4 | 2 | 2 | 6 | 3 | 0 |
| ISP-B10 | 0 | 5 | 4 | 2 | 2 | 3 | 3 | 0 |
| B3 | 0 | 8 | 4 | 2 | 2 | 4 | 4 | 0 |
| B4 | 0 | 6 | 4 | 2 | 2 | 4 | 4 | 0 |
| **B6** | 0 | 4 | 2 | **0** | **0** | 1 | 1 | 0 |
| X1 | 4 | 6 | 4 | 2 | 2 | 3 | 3 | 0 |
| B8 | 0 | 6 | 3 | **0** | 2 | 3 | 3 | 0 |

**No emptied ledger** — unlike C300's finding, this lineage's rows survive. Two rows **gapped and recovered**: `B6-SDK` was absent from C150 **and** C190 and reappeared at C228; `B8` was absent from C150. Routed as **I-4** (continuity INFO), not as a re-opened defect. `B1`'s 23 collider hits are the reason its raw counts must not be read as tracking strength — stated so the number is not reused naively.

### §A.4 — §7.1 normative-summary blindspot re-check (DOC-SPECIFIC, C121 KEY SIGNAL)

§7.1 (L615–641) untouched since C151. The three MUST-scope carve-out notes (§3.3 demurrage → MUST #5/#6; §7.1 escrow → two-state; §7.1 society-aggregate → MUST #6) re-read live and remain mutually consistent. **No corpus-wide MUST sweep run** — per C121, that defect class is doc-specific.

---

## §B — Corpus delta since `ba2426bd` (3 commits, none ATP)

`git log ba2426bd..HEAD -- web4-standard/` = **3 commits** (vs 69 repo-wide; `web4-core/` **0**, `hub/` 30):

| Commit | Touches | ATP relevance |
|---|---|---|
| `01f410db` fix(ontology): `web4:Tensor` superclass + `web4:observationCount` (closes #581) | `ontology/t3v3-ontology.ttl` only (+14/−4) | **None.** T3/V3 ontology; contains zero ATP terms (§B″.2). Method carry **v6** discharged: the ontology mover does not touch any ATP emitted example. |
| `954ee391` proposal #580 — resilience to incomplete/malformed/contradicting information | `proposals/` (new, 170L) | Non-normative draft. Raises *"does a suspended action hold resources?"* — touches ATP reservation semantics. → **I-3** forward note. |
| `4665a430` proposal #579 — Dictionary as context-mandatory society role | `proposals/` (new, 163L) | Non-normative draft; no ATP authority claim. |

Method carry **v2** applied (what landed that *claims authority* over this file's subject matter): both new artifacts are in `proposals/`, the standard's explicitly non-ratified tier. Neither re-scopes atp-adp. **§B yield: zero net-new.**

---

## §B′ — SDK / implementation mirror gate, re-derived at LIVE HEAD

- **`web4-core/src/atp.rs`** — `web4-core/` moved **zero bytes** since C266 (`git log ba2426bd..HEAD -- web4-core/` empty). C190/C228/C266 verdict **GENUINE account-primitive mirror, LAYER-SPLIT** (pool / minting / slashing / demurrage / exchange ABSENT) HELD by byte-identity. C190 I-1 (fee has no pool recipient in the two-account primitive) HELD.
- **`web4-standard/implementation/sdk/web4/atp.py`** (blob `efa5de3c`) — byte-identical. B3/B4/I2/B6-SDK STAND.
- **FALSE-mirror exclusions re-confirmed, NOT re-counted** (per the standing per-file guard): `lct.rs:585 slash()` = `LctStatus::Slashed`, LCT-lifecycle, **not** `slash_atp`; `ledger.rs mint()`/`MintReceipt` = LCT-genesis anchoring, **not** `mint_adp`.
- **`hub/` growth edge (30 commits) — ZERO ATP primitive.** Re-run at HEAD: `git log -p ba2426bd..HEAD -- hub | grep -E 'slash_atp|mint_adp|demurrage|society_pool|discharge_atp'` = empty. `hub-lib/src/lib.rs:19` explicitly disclaims ATP. The only `atp` tokens in `hub/` remain **governance-config selectors** in `law.rs` (`r6.resource.atp`) — DISJOINT, per the C228 adjudication.
- **Mirror-set contraction check (v8):** no tracked mirror disappeared this interval. **Mirror-set expansion (v7):** the six artifacts in §B″ are added to this lineage's tracked set for the first time.

**Gate verdict:** GENUINE (account layer) + ABSENT (pool/governance layer) + FALSE-mirror-excluded + DISJOINT (hub). Spec CORRECT on every mirrored *code* surface. The defects are in the *artifact* surface below.

---

## §B″ — The standard's own ATP artifacts (first read in 7 passes)

### §B″.1 — What is CLEAN (published so the negatives are inspectable, not implied)

**Schema ↔ SDK.** `atp.py`'s `ATPAccount.to_jsonld()` and `TransferResult.to_jsonld()` (both with and without the conditional `overflow` field) validate **cleanly** against `schemas/atp-jsonld.schema.json`. Instrument:

```python
from web4.atp import ATPAccount, TransferResult
schema = json.load(open('web4-standard/schemas/atp-jsonld.schema.json'))
jsonschema.validate(ATPAccount(available=100.0, locked=0.0, adp=0.0,
                               initial_balance=100.0).to_jsonld(), schema)   # VALID
```
3/3 documents VALID. The genuine-mirror verdict now has schema-level corroboration it never had in six prior passes.

**Schema ↔ schema-validation vectors.** All **23** cases in `test-vectors/schema-validation/atp-jsonld-validation.json` (8 `valid`, 15 `invalid`) behave exactly as declared, **including** every declared `error_kind`. 0 disagreements. See §F for why the first run of this instrument reported 14 false disagreements.

**Conformance harnesses green.** `pytest tests/test_conformance.py tests/test_vectors.py` → **71 passed, 5 xfailed**.

### §B″.2 — N1 (MEDIUM) — two published ATP vector suites share one identifier namespace for five different tests

The standard publishes **two** ATP vector suites. They collide on `atp-001`–`atp-005`, and on all five the collision names an **entirely different test**:

| ID | `testing/conformance/atp-operations.json` (added `92454d65`, **2026-05-14**) | `test-vectors/atp/transfer-operations.json` (added `a3b93713`, **2026-02-27**) |
|---|---|---|
| `atp-001` | New account with initial balance (`new`) | Basic transfer with 5% fee (`transfer`) |
| `atp-002` | Lock tokens / escrow (`lock`) | Transfer with MAX_BALANCE cap and overflow return |
| `atp-003` | Commit locked tokens (`commit`) | Transfer to already-full receiver |
| `atp-004` | Rollback locked tokens (`rollback`) | **Conservation invariant check** |
| `atp-005` | Zero-balance energy ratio returns neutral | Sliding scale payment — below threshold |

**The SDK cites these identifiers bare, with no file qualifier** — **15 occurrences on 9 distinct lines** (L79, 119, 241, 293, 317, 331, 351, 358, 377) across 8 functions in `web4/atp.py`. Every one of them resolves against `transfer-operations.json`; **not one** resolves correctly against the conformance suite:

| Site | Citation | `transfer-operations.json` | `conformance/atp-operations.json` |
|---|---|---|---|
| `atp.py:241` `transfer()` | "test vectors atp-001 through atp-003" | transfer / capped / full-receiver ✅ | new / lock / commit ❌ |
| `atp.py:317` `conservation_check()` | "test vector atp-004" | conservation invariant ✅ | rollback ❌ |
| `atp.py:293` `sliding_scale()` | "atp-005 through atp-007, atp-015" | sliding-scale series ✅ | energy_ratio; **007/015 absent** ❌ |
| `atp.py:119` `recharge()` | "atp-009, atp-010" | present ✅ | **absent** ❌ |
| `atp.py:79`,`:331` `energy_ratio` | "atp-012, atp-013" | present ✅ | **absent** ❌ |
| `atp.py:351` sybil / `:377` fee-sensitivity | "atp-011" / "atp-014" | present ✅ | **absent** ❌ |

**The deflation test — and why this one survives it.** Every attractive finding in this corpus dies on an idiom baseline (C158 JSONC, C234 "Scope", C274 `witnesses`), so the namespace was measured across the standard's **entire** published vector corpus — 5 conformance suites + 35 test-vector suites:

```python
# collect every {"id": ...} in web4-standard/testing/conformance/*.json
# and web4-standard/test-vectors/**/*.json; report ids appearing in >1 file
```

**Exactly 6 identifiers collide corpus-wide. Five of them are these.** The sixth is `s1`, which is an *intra-document plan-step id* appearing in two acp documents (`{"id":"s1","mcp":"m"}`) — not a suite-level test identifier, so it is not comparable. **ATP owns 5 of 5 suite-level vector-ID collisions in the standard.** This is not corpus style; it is unique to this domain.

**Direction (v12).** `transfer-operations.json` predates the conformance suite by ~2.5 months, owns a contiguous `atp-001`–`atp-015` block, and is what every SDK citation means. The **later** conformance suite minted `atp-001`–`atp-005` into an already-occupied namespace. That establishes which artifact introduced the collision; it does **not** by itself establish which one should change — see routing.

**Severity bounded to MEDIUM, not HIGH — the refutation that worked.** All three harnesses load by **path**, not by global ID (`load_vectors(filename)` / `load_suite(filename)` in `test_atp.py`, `test_vectors.py`, `test_conformance.py`), so nothing mis-resolves at runtime and both suites pass. `test-vectors/validate_vectors.py` has no duplicate-ID check, so nothing would catch a future collision either. The defect is **citation integrity for a human implementer**: a reader following `atp.py:293` into the file that describes itself as the canonical conformance suite gets the wrong test for `atp-005` and no test at all for `atp-007`/`atp-015`.

### §B″.3 — N2 (MEDIUM) — the production deployment guide installs two files from a path they were deleted from

`web4-standard/deployment/` ships a systemd unit, a cron entry and two configs for a `web4-demurrage` service. Its README (`deployment/README.md`, "Production deployment configurations for Web4 services", **"Option 1: Systemd Service (Recommended for Production)"**) instructs, at **L33–34** and again at **L83–84**:

```bash
sudo cp ../implementation/reference/demurrage_service.py /opt/web4/
sudo cp ../implementation/reference/atp_demurrage.py /opt/web4/
```

Both paths are **empty at HEAD**:

```
MISSING web4-standard/implementation/reference/demurrage_service.py
MISSING web4-standard/implementation/reference/atp_demurrage.py
# implementation/reference/ contains only:
#   web4_crypto_stub.py  web4_demo.py  web4_reference_client.py
```

The two files were **deleted from that path on 2026-05-12** by `12ee197c` (the drift-cleanup archival sweep) and now live at `archive/reference-implementations/{demurrage_service.py,atp_demurrage.py}`. `deployment/README.md` was last touched **2025-12-05** (`0e547127`) and has never been updated since. The systemd unit's `ExecStart=/usr/bin/python3 /opt/web4/demurrage_service.py` therefore targets a file the documented install procedure cannot produce: **following the standard's own production guide verbatim yields a unit that fails to start.**

Every pass in this lineage post-dates the breakage (earliest, C34, is 2026-06-06 — 25 days after) and none read `deployment/`.

**Direction (v12) — genuinely open, and NOT this audit's to settle.** Two readings, both coherent:
- **(a) the README is stale** — it should point at `archive/reference-implementations/`. But that documents a *production* service as running out of an archive directory, which is its own smell.
- **(b) the archival over-reached** — the sweep archived by directory pattern and caught two files that are a live dependency of the standard's shipped deployment surface. Under this reading they belong back in `implementation/reference/` (or in a supported services path), and `deployment/` is correct as written.

**Deflations published in full.** `deployment/` is **not** referenced from `web4-standard/README.md` — it is an orphan directory, which lowers its discoverability and therefore the practical blast radius. Against that: it carries **no** deprecation, archival or non-normative marker anywhere in the tree, it ships inside `web4-standard/`, and it presents itself as production guidance. Both facts are stated so the owner weighs them; this audit does not encode the verdict.

---

## §C — INFO / forward notes

- **I-1 — Effector/slashing-authority forward-harmonization note** (W4IP/SAL-owned, not an atp-adp defect). HELD from C228/C266; no W4IP mover this interval. Not routed.
- **I-2 — `lct.rs:585 slash()` + `ledger.rs mint()` name-collision false-mirrors.** HELD. **Carry-guard for the next delta: do NOT re-count either as an ATP mirror.**
- **I-3 (new) — proposal #580 raises an unanswered ATP-reservation question.** "*Does a suspended action hold resources? … whether the reservation is held or released across the suspension.*" atp-adp §7.1's escrow note specifies lock → commit/rollback but says nothing about a *suspended* (correction-pending) action. Non-normative proposal tier; **forward note only**, no atp-adp obligation today. Owner: W4IP / proposal author.
- **I-4 (new) — carry row `B6-SDK` gapped for two consecutive passes and recovered.** Absent from C150 **and** C190, back at C228/C266 (`B8` similarly absent at C150). Per v10 this is a **continuity** observation, recorded as a binary re-verification: `atp.py` is byte-frozen, so B6-SDK's live-HEAD status is unchanged and owned by C118/C228. No fresh finding number, no re-argued merits.
- **I-5 (new) — C158's JSONC INFO-corpus carry never reached this ledger.** C158 (acp, 2026-07-08) adjudicated `//`-annotated `json` fences as corpus style and explicitly counted "atp-adp 2" among the affected files. **0 of 9** atp-adp lineage docs (7 deltas + C119 + C151) mention it. Binary re-verification only, citing C158 as owner — see §F for the live re-measurement. Not a new finding.

---

## §D — SDK wire-layer-readiness synthesis (held, one addition)

The C188/C190/C228/C266 synthesis holds verbatim: web4-core has **primitive/type layers** but **not** the pool/governance/wire layer (no `SocietyTokenPool`, no COSE/CBOR codec, no registry loader, no HPKE handshake, no MCP wire assembly). Whichever form flagship **B-D1** declares canonical owes a from-scratch build of that set.

**Addition from this pass:** the standard's ATP schema, context and vectors describe **only** the account-primitive layer (`ATPAccount`, `TransferResult`) — there is no published schema, context or vector for minting, slashing, demurrage, pools or inter-society exchange. The artifact layer is therefore **layer-split in exactly the same place as the code layer**, which is coherent, and is a third recorded integration constraint: when the pool/governance layer is built it will need its schemas and vectors authored alongside, into a namespace that N1's routing has by then made unambiguous.

---

## §E — Routing summary

| ID | Severity | Classification | Owner / next step |
|----|----------|----------------|-------------------|
| **N1** | **MEDIUM** | standard-internal (**M2c**: in-standard normative siblings, regardless of `testing/` vs `test-vectors/` path) | **Operator/author decision — do not self-apply.** Options, not a verdict: (i) renumber the conformance suite out of the occupied block (e.g. `atpc-001…`); (ii) qualify the SDK's 9 bare citations with their file; (iii) both; (iv) accept and document the two namespaces. A duplicate-ID check in `test-vectors/validate_vectors.py` would make any choice self-enforcing. |
| **N2** | **MEDIUM** | standard-internal, deployment surface | **Operator decision — do not self-apply.** Direction genuinely open: (a) repoint `deployment/README.md` L33-34/L83-84 at `archive/reference-implementations/`, or (b) restore the two files to a supported path because the shipped deployment surface depends on them. Either way `deployment/README.md` (last touched 2025-12-05) needs an owner. |
| I-1 | INFO | cross-doc forward note | W4IP/SAL track. No atp-adp action. |
| I-2 | INFO | SDK growth-edge | Standing false-mirror guard. No action. |
| I-3 | INFO | forward note | Proposal #580 author / W4IP. No atp-adp obligation. |
| I-4 | INFO | continuity | Recorded; B6-SDK re-verified frozen, owned by C118/C228. |
| I-5 | INFO | inbound continuity | C158-owned (corpus-wide JSONC DESIGN-Q). Recorded here so the row exists in *this* ledger. |
| B1 / B2b / M2 / ISP-B10 | — | DESIGN-Q | **Operator** (open; directions re-derived §A.2, no inversions). |
| B3 / B4 / I2 / B6-SDK | — | SDK-track | SDK (open; `atp.py` frozen; schema-clean per §B″.1). |
| X1 | — | CROSS-TRACK | C33 corpus identifier decision (open). |
| B8 (inbound) | — | CROSS-TRACK (acp-owned) | atp-adp §7.1 #5 (L621) is the correct-side referent. STANDS. |
| C166 GUARD | — | **CONSUMED (C190)** | Not re-opened. |
| C118-N2 | — | **CLOSED (t3-v3 C122)** | Not re-opened. |

**Autonomous remediation set (C307-candidate): EMPTY. C307 = NO-OP.** Both MEDIUMs are operator/author-owned direction decisions; neither is self-applicable, and the target plus every mirror is byte-frozen. Do **not** self-fix.

**Rotation:** next slot advances to **`multi-device-lct-binding.md` at C308** (last audited C268; 268+40).

---

## §F — Lessons / method notes

**Three attractive findings died on their own baselines this pass. Publishing the corpses is the point.**

1. **Ontology term non-resolution — deflated by idiom.** All 13 `web4:` terms in `schemas/contexts/atp.jsonld` (`ATPAccount`, `available`, `energyRatio`, …) are undefined in `web4-standard/ontology/*.ttl`. Measured across **all 10** published contexts: `capability` **0/15**, `entity` **0/8**, `atp` **0/13**, `attestation-envelope` 1/31, `dictionary` 1/37, `acp` 3/34, `lct` 11/47, `t3` 16/18, `v3` 16/18, `r7-action` 61/86. atp is mid-pack in a corpus-wide pattern. **Charging atp-adp specifically would be the exact overcall that killed C234's flagship.** (The corpus-wide gap may itself be worth an operator memo — but it is not an atp-adp finding and is not routed here.)
2. **Unparseable `json` fences — deflated by idiom, twice.** 3 of atp-adp's 6 `json` fences fail strict parse. Corpus-wide: **51 of 148** fail across 14 of 16 core-spec files. Suspecting that atp-adp's third failure (L129, `"valuation": +0.03`) escaped C158's `//`-comment framing, the residue was re-measured after stripping `//` comments and trailing commas: **39 still fail, spread across 13 files**, atp-adp's among them. So even the narrowed charge is idiom. C158 already owns this as an INFO-corpus operator DESIGN-Q → recorded as **I-5**, not re-litigated.
3. **Schema-validation vectors — deflated by my own instrument.** The first run reported **14 of 23** vectors disagreeing with their declared `error_kind`. All 14 shared one shape, which is the tell. The schema's root is `oneOf`, so every failure surfaces at the root as `oneOf` and the real cause lives in `ValidationError.context`. Recursing into sub-errors: **0 disagreements — the suite is perfectly clean.** [[feedback_ledger_emptied_not_closed]]'s corollary says a verification run that *agrees* with your draft has confirmed nothing until you confirm the verifier ran. **The inverse is equally true and is what fired here: a run that *disagrees* can also be your instrument, and 14 identically-shaped disagreements is the signature.** An earlier version of this same instrument silently tested **0** cases (`agree=0, MISMATCH=0`) because it guessed the wrong document shape — caught only because zero-and-zero is impossible for a 23-case file.

**What the pass is actually evidence of.** The lineage's *scope* was inherited, not derived, for seven consecutive passes. Three of those certified "zero-routed" and one certified a "first fully-EMPTY corpus-delta" — all true statements about the prose and the code mirrors, and all silent about 993 lines of the standard's own normative artifacts plus a shipped deployment tree. This is the fourth lineage where re-deriving the mirror set from **subject matter** rather than from the last pass's list produced the pass's entire yield (C280 `hub/`, C292 `ontology/`, C294 `hub/`, C304 schema — now C306 schema + vectors + `deployment/`). The generalisable form: **a frozen target is a signal to widen the surface, not to certify.**

**A method carry is proposed, not asserted (v13-candidate, operator to ratify):** *when a lineage's target and code mirrors are both byte-frozen, the next surface to derive is the standard's own **operational** artifacts — deployment configs, service units, cron entries, install guides — which no C-series lineage has ever gated (1 of 196 audit docs cite `deployment/`).* N2 is the first defect found there, and it was introduced by a **cleanup commit** — the archival sweep that removed drift also removed a live dependency of a shipped surface, and nothing in the corpus was watching that seam. → [[feedback_mirror_set_underderived]], [[feedback_carry_direction_not_presence]], [[feedback_refute_your_best_finding]]

---

## §G — Instrument index (every count above, re-run AFTER the findings were written)

All at `0fb9d952`, from repo root, scope stated per row.

| Claim | Instrument | Scope | Result |
|---|---|---|---|
| target frozen 25d | `git log -1 -- core-spec/atp-adp-cycle.md` | 1 file | `256ab51d`, 2026-07-07, blob `2d060579` |
| spec corpus delta | `git log ba2426bd..HEAD -- web4-standard/` | tree | 3 commits |
| SDK delta | `git log ba2426bd..HEAD -- web4-core/` | tree | 0 commits |
| artifact blind spot | grep 6 tokens × 7 docs | `docs/audits/` | 0/7 (and 0/196) |
| `deployment/` coverage | `grep -rl "deployment/" docs/audits/` | `docs/audits/` | 1 of 196 |
| vector-ID collisions | id-collect over 5 conformance + 35 vector suites | `testing/conformance/*.json` + `test-vectors/**/*.json` | 6 total; 5 are ATP; 1 (`s1`) is an intra-doc step id |
| SDK bare citations | occurrences: `grep -oE '(atp\|xfer\|scale)-[0-9]{3}' … \| wc -l`; lines: same `-n` then `cut -d: -f1 \| sort -un \| wc -l` | 1 file | **15 occurrences on 9 distinct lines**, all resolving to `test-vectors/`. *Both numbers published because `-c` is ambiguous across grep implementations — it counts matching lines in GNU grep and occurrences under `-o` in ugrep (the shell here), which is how the two figures can both read "15".* |
| schema ↔ SDK | `jsonschema.validate(to_jsonld(), schema)` | 3 documents | 3/3 VALID |
| schema ↔ vectors | `Draft202012Validator` + recursive `oneOf` sub-error kinds | 23 cases | 0 disagreements |
| harnesses | `pytest tests/test_conformance.py tests/test_vectors.py` | 2 files | 71 passed, 5 xfailed |
| README paths | file-existence test on the 2 cited paths | 2 paths | both MISSING; deleted `12ee197c` 2026-05-12 |
| context terms | resolve `web4:` ids against `ontology/*.ttl` | all 10 contexts | atp 0/13; corpus range 0/15 → 61/86 |
| json fences | strict `json.loads` per fence, then JSONC-strip | 16 core-spec files | 148 total, 51 fail, 39 residue across 13 files |
| carry rows | bounded `re.findall` + collider counts | 7 lineage docs | table §A.3 |
| hub ATP primitive | `git log -p ba2426bd..HEAD -- hub \| grep -E 'slash_atp\|mint_adp\|demurrage\|society_pool\|discharge_atp'` | `hub/` | empty |
