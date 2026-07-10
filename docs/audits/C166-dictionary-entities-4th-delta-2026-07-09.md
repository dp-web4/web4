# C166 — Delta Re-Audit: dictionary-entities.md (4th delta)

**Date**: 2026-07-09
**Auditor**: Legion autonomous web4 track (slot `180036`, v2 protocol)
**Target**: `web4-standard/core-spec/dictionary-entities.md` (603 lines)
**Lineage**: C17 (`dictionary-entities-internal-consistency-2026-05-27.md`, #241/#242) → C52 (81-agent exhaustive, #323) → **C53 remediation** (#324, `95d20919`, 9 findings) → C94 (2nd delta, 9/9 held, 0 net-new) → C132 (3rd delta, **2nd consecutive fully-clean**, #444) → **C166** (this doc)
**Window**: C132 head `286e5600` → HEAD `65631861`. **63 commits, 73 files.**
**Staleness**: **Frozen target, moving corpus** — the inverse of C164's window.

**Method**: §A prior-finding verification at live bytes (freeze proven by blob identity, not inherited from C132's assertion). §B refute-by-default sweep **bounded to the corpus delta** — one intersect-or-disjoint adjudication per moved surface, each citing the moved hunk (C120/C123 discipline). **No finder agent was pointed at the target's 603 frozen lines** (policy condition 1; the C164 manufacture-findings ruling). §C carry ledger re-derived from **lineage prose, not from C132's §C** ([[prose is not the ledger]], born C164), with the C98 snapshot-presence guard and the C90 inbound-carry read.

---

## Summary

| | Count |
|---|---|
| **§A** C53 findings re-verified at live lines | **9 / 9 HELD**, 0 regressed (byte-freeze proven cryptographically) |
| **§B** moved surfaces adjudicated | **7** — 2 INTERSECT, 5 DISJOINT (all cited) |
| **§B** candidates raised | **4** |
| **§B** candidates surviving refutation | **0** |
| **§B** NET-NEW autonomous spec defects | **0** |
| **§C** net-new **ledger** findings | **1** (C166-N1, LOW, additive) |
| Autonomous-in-file items for C167 | **0** → **C167 = DECLARED NO-OP** |

**Health verdict**: `dictionary-entities.md` is in **excellent health** — the **third consecutive fully-clean delta** (C94, C132, C166). Recorded as a positive result, not padded. The whole substantive yield this cycle is on the corpus-delta and ledger surfaces, exactly where the frozen-target model predicts it.

---

## §A — Prior-Finding Verification

**Freeze proven, not asserted.** The target's blob SHA is byte-identical at every point in the lineage:

```
C53  95d20919:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
C94  8c581465:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
C132 286e5600:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
HEAD 65631861:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
```

⇒ the 9 C53 findings hold **by construction**, and the `#324` regression sweep is clean by construction. Confirmed first-hand at live line numbers (not copied from C132):

| C53 finding | Claim | Live line | Status |
|---|---|---|---|
| **B1** [MED] | `witness_required=confidence < 0.95 or request.trust_requirements.require_witness` | L246 | **HELD** |
| **B3a** [MED] | `lct:web4:dictionary:medical-legal` long form | L48 / L162 / L259 / L417 | **HELD** |
| **B3b** [MED] | `lct:web4:dictionary:legal-insurance` | L164 / L267 / L512 | **HELD** |
| **B3c** [LOW] | §10.2/§10.3 ids long form | L531 / L545 | **HELD** |
| **B4** [MED] | §2.1 V3 = `(Valuation, Veracity, Validity)` | L41 | **HELD** |
| **B5** [MED] | §7.1 R6 role keyed `"actor":` | L417 | **HELD** |
| **B19** [LOW] | §7.1 rules `"minimum_fidelity":` | L413 | **HELD** |
| **B20** [LOW] | `request.source_domain, request.target_domain` | L202 | **HELD** |
| **B21** [LOW] | `stake_on_translation(self, amount, confidence_claim, actual_confidence)` | L565 | **HELD** |

**Mirror freshness** (`#324` regression sweep): SDK `web4/dictionary.py` blob `edd97183` and `tests/test_dictionary.py` blob `d8f71420` are byte-identical at C53 and HEAD; the `protocols/` sister doc blob `b28d8f9e` is unchanged since C132. `git log 286e5600..HEAD -- '*dictionar*'` returns **only C132's own audit doc**. ⇒ the SDK cross-track bundle (B15–B18, B24, B25) stands verbatim.

---

## §B — Fresh Sweep (corpus-delta surface, refute-by-default)

**Verdict: 0 net-new autonomous target defects.**

The target's cross-reference surface is **purely conceptual** — the document contains **zero outbound `.md` links**. Intersection is therefore measured against its concept usage: witness (15), reputation (8), role (7), stake (6), ATP (6), LCT (5), T3 (3), R6 (3), V3 (2), MRH (2), slash (1).

### B.1 — Adjudication of the 7 moved surfaces

| # | Moved surface | Commit | Moved hunk (cited) | Verdict |
|---|---|---|---|---|
| 1 | `atp-adp-cycle.md` | `256ab51d` (#477, C151) | **L214** supply-accounting note: `"scopes only ATP→ADP transfers"` → `"scopes only ATP transfers between entities (§6.3)"` | **INTERSECT** — this is the **C52-B9 surface** |
| 2 | `ontology/role-extension.{ttl,md}` | `7201a765` (#486) | **NEW FILES** in `web4-standard/ontology/` | **INTERSECT** — C17-M1 sweep target; C17-H2 resolution path |
| 3 | `reputation-computation.md` | `5195465c` (#484, C157) | **L761–764** §9 Sybil item 4 softened to SHOULD + "not yet specified" | **DISJOINT** |
| 4 | `mrh-tensors.md` | `b8740803` (#491, C163) | **L200–210** `TrustPropagation` SDK-API note ("Two"→"Three" API differences) | **DISJOINT** |
| 5 | `acp-framework.md` | `fb0075fc` (#487, C159) | **L255** `grant.scope.r6Caps.resourceCaps`; **L419** trust-gaming row; **L568–571** witness-deficit §-cite | **DISJOINT** |
| 6 | `whitepaper/sections/00-executive-summary` | `ff5aa546` | Dictionary bullet moved **L55 → L65**, text byte-identical | **DISJOINT** |
| 7 | `web4-core/src/` (Rust: `role.rs`, `role_extension.rs`, `society.rs`, `t3.rs`, `v3.rs`, `r6.rs`) | `3c18807a`, `0e0337c3`, `20ef29f5` | — | **DISJOINT** — `grep -ril dictionar web4-core/src/` = **zero hits** |

Disjointness proofs (per condition 1: *disjoint ⇒ record and stop; do not spider*):

- **#3** — dictionary's `reputation` sites are L333/L339 (scores), L344–345 (`proposal_threshold`/`approval_quorum`), L455 (threat table), L551 (§11 heading). None depends on reputation-computation §9's Sybil enumeration. `grep -c dictionar reputation-computation.md` = **0**.
- **#4** — dictionary's only MRH sites are L39 (glossary, "Relationship graph with domains and users") and L359 (§6.1 "Discovery via MRH"). C163's hunk is a Python docstring about `propagate_*` signatures. `grep -c dictionar mrh-tensors.md` = **0**.
- **#5** — dictionary has no `grant`/`resourceCaps`/`witnessLevel` surface; its witness surface is `require_witness`/`witness_required`. `grep -c dictionar acp-framework.md` = **0**.
- **#6** — the bullet's text is unchanged; only its ordinal moved (posture revision reordering). Present at the C132 snapshot (C98 guard).

### B.2 — Candidates raised, and their refutations

Four candidates were raised. **All four were refuted.** Per [[refute your BEST finding]], the refuter was pointed at the strongest one first.

#### Candidate 1 (FLAGSHIP) — "C151's new `(§6.3)` anchor is a remediation-introduced mis-cite" → **REFUTED**

The strongest available charge, and the one with the best prior: it is exactly the [[remediation-introduced regression]] class (8 prior instances) and the C158-N1 class (a remediation-born mis-cite). The charge:

> `atp-adp-cycle.md:214` now reads *"…the transfer-conservation invariant (`initial == final + fees`), **which scopes only ATP transfers between entities (§6.3)**"*. But **§6.3 is "Transfer Fees"**, and its body (L595) says *"The core protocol does **not** prescribe transfer fees"*. Worse, `grep 'initial == final'` over the whole of `web4-standard/` returns **only L214 itself** plus `t3-v3-tensors.md:640` — and `t3-v3:640` explicitly assigns §6.3 a *different* role (*"§6.3 (fee-recycling preserves total supply)"*) while assigning the per-transfer invariant to **§2.4**. So C151 appeared to redirect the invariant's scope to a section that the corpus's own anchor table says anchors something else. Additionally, §7.1's MUST list (L615–621) contains **no conservation MUST** — the invariant is *named* in three places and *stated* as a requirement in none; both of its `atp-adp` mentions (L213–215, L328) are **carve-outs excepting things from it**.

**Refutation.** `§6.3 L595` is the **only** place in `atp-adp-cycle.md` that names *"Peer-to-peer ATP transfers"* — i.e. ATP transfers between entities. The relative clause's referent is therefore genuinely resident at §6.3, and §6.3 is also where the invariant's `+ fees` term is defined. The cite is **defensible on both of its terms**. Independently, **C154 §A.1** already adjudicated this exact pair (*"the load-bearing check this cycle"*) and ruled C151 **REINFORCING**, verifying all three t3-v3 L640 anchors token-by-token against live `atp-adp` bytes. The charge does not survive.

**Residue (routed, not asserted).** The *definition-site* observation survives the refutation of the *cite*: the transfer-conservation invariant has no normative statement anywhere — §3.2 L266 states supply conservation (`total_supply == sum(allocations) == sum(state_distribution)`), from which the per-transfer form is a corollary, but the corollary is never written down except inside its own exceptions. This is **pre-existing** (both carve-out notes predate C132; only the `(§6.3)` token is new), **not net-new**, **not autonomous**, and **not dictionary-owned**. Five prior audits (C119, C122, C150, C151, C154) worked this exact surface without raising it — which is itself weak evidence it is a non-finding. **Routed as INFO to the `atp-adp` owner to adjudicate; not asserted as a defect here.**

#### Candidate 2 — "§8.1 L455 asserts `temporal decay`, a mitigation specified nowhere" → **REFUTED**

`grep -i decay` over the target returns exactly **one** line — L455, `| **Reputation gaming** | ATP staking, temporal decay |`. The mechanism is never specified in the file. This is the precise **B-I1 shape** that C157 (`5195465c`, in-window) had just remediated in `reputation-computation.md` §9: an unbacked capability claim stated as fact, softened to SHOULD + a "not yet specified" pointer. A corpus norm established *after* the target froze is a legitimate corpus-delta finding, not a re-read finding.

**Refutation, two independent grounds.** (i) The claim is **backed**: `reputation-computation.md` §"Reputation Decay" (L693–706) specifies `apply_reputation_decay` / `inactivity_decay`, plus `exp(-age_days/30.0)` recency weighting at L658. The mechanism exists; it is merely named differently and uncited. (ii) "Uncited" is a **pre-existing corpus idiom of this document**, not a defect at L455 — the file contains **zero outbound `.md` links anywhere in 603 lines**. Singling out L455 would be the C162 error (charging a novel defect against a corpus-wide idiom). C157's B-I1 shape applies to *unbacked* claims; this one is backed.

#### Candidate 3 — "whitepaper claims `forward/reverse translation`; spec's only `reverse` is a Python sort kwarg" → **REFUTED**

`grep -in reverse` over the target returns exactly one hit — L400, `sorted(scores, key=lambda x: x[1], reverse=True)`. The exec-summary bullet (L65) claims *"forward/reverse translation"*.

**Refutation.** The capability is specified under a different token: **L53** `"bidirectional": true` and **L479** *"1. Dictionaries SHOULD support bidirectional translation"*. The whitepaper claim is backed. (Also fails the C98 guard independently: the bullet is byte-identical to its C132-snapshot form at L55.)

#### Candidate 4 — "C159 declares reputation staking a *future* mechanism; dictionary L455 declares ATP staking an *extant* mitigation for reputation gaming" → **REFUTED**

`acp-framework.md:419` (moved in-window) now reads *"Audit adjustments (reputation staking is a future mechanism — see reputation-computation.md §10)"*.

**Refutation — distinct mechanisms.** ACP's "reputation staking" stakes *reputation*. Dictionary's is **ATP staked against a translation-confidence claim**, and it **is** specified in-doc: §11.2 `DictionaryStaking.stake_on_translation` (L561–571), plus `stake_required` (L73) and MUST-5 (L475). No contradiction. This is the classic **cross-doc overcall pattern** (C7/C9/C10/C11 streak) and it is rejected on re-reading the cited doc.

### B.3 — Overcall guard

The target is byte-identical to bytes cleared by C52 (81-agent exhaustive), C94 (full-file refute-by-default), and C132. No candidate cleared the guard. **No candidate is promoted; none is demoted-but-recorded as a spec defect.**

---

## §C — Carry Ledger (re-derived from lineage prose, not from C132's §C)

Per policy condition 3 this section is **additive only**. C132 and all prior audit docs are left byte-unchanged (C163 no-retro-edit ruling).

### C.1 — Intersecting-surface carry status updates (evidence-backed)

**C52-B9 — HARDENED by C151** (status change, not a new finding). B9 = *"§11.2 authority-less partial slash vs cycle-spec slash semantics"*. C132 certified §2.4's slash semantics **untouched**; C151 has since edited exactly that note. The edit **widens the gap B9 names**: canonical `slash_atp` (§2.4) now explicitly requires (a) destruction bookkeeping against `total_supply` (§3.1), (b) `record_slashing_event(violator, slashed, evidence, witnesses)`, and (c) T3/V3 deltas — while dictionary §11.2's `return amount * (actual_confidence / confidence_claim)  # Partial slash` performs **none** of the three and silently drops the residual. B9 remains **OPEN**, now hardened-by-C79 **and** hardened-by-C151.

**C17-M1 — STANDS OPEN, sweep refreshed against the new ontology.** This was the named, non-optional reason to run this pass. `grep -riE dictionar web4-standard/ontology/` = **ZERO hits across all 7 files**, including both files new since C132 (`role-extension.ttl`, `role-extension-schema.md` — confirmed new via `git cat-file -e 286e5600:<path>`). The six `web4:*` dictionary predicates remain undefined in the canonical ontology. **A new ontology file landing did not close M1.**

**C17-H2 — OPEN, but a candidate resolution path now exists in the standard** *(record-and-route, per policy condition 2 — NOT self-applied)*. Target L418–420 reads `"roleLCT": "lct:web4:role:dictionary-translator:..."` with the inline note *"role value is illustrative; canonical SocietyRole resolution deferred (see C17 audit H2 role-value DESIGN-Q)"*. Since C132, `role-extension-schema.md:206` promotes a canonical pattern: **`SocietyRole::Custom("constellation:mesh-worker")` — "the string becomes the entity's canonical label."** That is precisely the shape H2 asks for. **It does not resolve H2**: role-extension is scoped to *orchestration* Role-entities under society+constellation law, is Phase-0 with a PROVISIONAL surface, and mentions dictionaries zero times. Verdict: **the deferral's premise ("no canonical mechanism exists") has partially dissolved.** The operator's DESIGN-Q now has a concrete candidate answer to be adjudicated against, rather than an open void. **Routed to the operator memo; not decided here.**

### C.2 — Inbound carry (C90 read of 11 sibling audit docs since C132)

**C158 §L63 → ADOPTED as INFO-corpus.** The only genuine inbound item. C158's corpus-wide sweep claims *"7 of ~20 core-spec files carry `//`-annotated json fences (dictionary-entities **4**, mcp-protocol 3, …)"*.

Per [[enumeration + grep hypotheses]] an enumeration claim is its own lens, so the count was **re-derived from ground truth** rather than trusted. Parsing all 17 fences in the target: 8 are `json`, of which exactly **4** contain `//`:

| Fence | Comment lines |
|---|---|
| L46–87 | L69, L70, L71, L73 |
| L252–276 | L272 |
| L326–355 | L344, L345, L346, L349 |
| L409–443 | L419, L420 |

**C158's enumeration CONFIRMED (4 fences, 11 comment lines).** Adopted as an INFO-corpus carry; it is a corpus-wide style DESIGN-Q owned by the operator, **not** an autonomous dictionary defect (strict `json.loads` fails on all 4, but the fences are illustrative, and — note — fence L409–443's comment *is* the C17-H2 deferral note itself).

The other 10 sibling audit docs (C150, C151, C154, C156, C157, C159, C160, C162, C163, C164) contain **no** item routed to a dictionary pass.

### C.3 — NET-NEW: **C166-N1** [LOW, class-a **LEDGER**, additive] — per-file §C under-represents the frontier

Applying [[prose is not the ledger]] (born last fire at C164) to this lineage for the first time, the owed carry set was re-derived from the **full prose** of C17 / C52 / C94 / C132 rather than copied from C132's §C. Two IDs are absent-by-name from C132:

| ID | Origin (verbatim) | Absent from | True drop? |
|---|---|---|---|
| **C52-B3d** [INFO, design-Q] | `C52…:99` — *"All 21 LCT id literals are human-readable typed forms, not the LCT spec's canonical `lct:web4:mb32:` hash form"*; and `C52…:232` — *"B3d (id-form evidence → existing C33 bundle)."* | C94 §C, C132 §C | **NO** |
| **C52-B12 / B13 / B14** [3× MED, design-Q] | `C52…:152/156/160` — multi-hop MAY-vs-MUST; LCT wire structure; chain-record shape | C132 §C (by name) | **NO** |

**"Is it NEW?" before "is it TRUE?"** — and the answer, honestly, is *no* for both:

- **B3d is preserved** in the standing cross-audit ledger (`carries.md:26`: *"B3d typed-id evidence → C33 bundle"*). Its departure from the per-file §C is **by design** — it is exactly the [[cross-cutting consolidation]] pattern that collapses scattered per-file id-scheme evidence into one operator decision. **Not a C164-class silent drop.**
- **B12/B13/B14 are carried by their root**, B26. C52 §D4 states the compression explicitly: *"B12/B13/B14 (3 MEDs) + B26 share one root … surface as ONE operator decision, not four findings."* Deliberate root-cause compression, documented at birth.

**What survives** is narrower and real: **a reader of the public dictionary lineage alone cannot recover B3d or B12/B13/B14 by ID.** B3d survives only in a *private* ledger; B12/B13/B14 survive only inside B26's prose. If the operator ever resolves B26 *partially*, the three constituents are no longer individually tracked anywhere in the audit trail. **Remedy applied here, additively**: they are re-inlined below. No closed doc was edited.

### C.4 — Restored / re-inlined frontier

| Carry | Class | Status |
|---|---|---|
| **B3d** | INFO design-Q → **C33 id-scheme bundle** | OPEN — *re-inlined*; travels with C50-B20, C92-N3 |
| **B26** (root) | INFO design-Q — sibling-spec canonicity, **3-doc** (target ↔ `protocols/` ↔ entity-types §10.2 via C64-B7) | OPEN — one operator decision |
| ├ **B12** | MED — multi-hop `MAY` vs sibling `MUST` (conformance-floor divergence) | OPEN — *re-inlined under B26* |
| ├ **B13** | MED — Dictionary LCT wire structure diverges from sibling | OPEN — *re-inlined under B26* |
| └ **B14** | MED — chain-record shape diverges from sibling | OPEN — *re-inlined under B26* |
| **B2 / B6 / B7 / B8 / B10 / B11 / B22 / B23** | operator DESIGN-Q | OPEN, unchanged |
| **B9** | operator DESIGN-Q | OPEN — **hardened-by-C79 and now by C151** |
| **C17-M1** | operator DESIGN-Q | OPEN — sweep refreshed vs 2 new ontology files, zero hits |
| **C17-M4** | operator DESIGN-Q | OPEN — `W4_ERR_DICT_*` absent from `errors.md` (unmoved in window) |
| **C17-M6** | operator DESIGN-Q | OPEN, unchanged |
| **C17-H2** | operator DESIGN-Q | OPEN — **candidate resolution path now in-standard** (§C.1) |
| **C64-B7** | inbound cross-doc (entity-types owns fix) | OPEN — folds into B26 |
| **C17-INFO3** | cross-doc → MCP pass | OPEN — stale `roleType` at `mcp-protocol.md:314` |
| **B15 / B16 / B17 / B18 / B24 / B25** | cross-track SDK bundle | OPEN — `dictionary.py` frozen; route to SDK |
| **C158 `//`-fence** | INFO-corpus (inbound, adopted) | OPEN — enumeration verified = 4 |

**Outbound this cycle**: (1) the transfer-conservation **definition-site** INFO → `atp-adp` owner (§B.2, Candidate 1 residue); (2) C17-H2's candidate resolution path → operator memo.

---

## §D — Disposition

**There are NO autonomous spec defects to remediate.** §A: 9/9 held on a cryptographically-frozen file. §B: 7 surfaces adjudicated, 4 candidates raised, **4 refuted**, 0 net-new. §C: 1 net-new **ledger** finding, remediated in place by additive re-inlining.

- **C167 = DECLARED NO-OP on the spec side** (precedent: C131→C132, C155, C161, C164→C165; policy condition 4). Zero bytes of `dictionary-entities.md`, any sibling, any `.ttl`, any schema, any SDK source, any test vector, or the whitepaper were mutated by this turn.
- **Rotation advances (+2)** to `SOCIETY_METABOLIC` = **C168** (lineage C21 → C54/C55 → C96 → C133 → next).
- **Third consecutive fully-clean dictionary delta** (C94, C132, C166). The file churns far slower than the audit cadence; this is steady state and is recorded as a positive result.

**Standing frontier** (nothing autonomously actionable): see §C.4.

---

## §E — Method & Governance Notes

1. **Frozen target, moving corpus — the mirror image of C164.** C164 bound §B to a single pass because a *frozen file in a frozen window* offers a finder swarm nothing but the temptation to manufacture. Here the window carried 63 commits and 7 moved surfaces, so §B was sized to **the delta, not the target**: one adjudication per moved surface, and no agent was ever pointed at the 603 cleared lines. Turn size dictated by what moved (C163 proportionality). The two rulings are consistent; they differ only in what actually moved.

2. **Prove the freeze; don't inherit it.** C132 *asserted* the byte-freeze. C166 *proved* it by blob identity across four commits. This costs one command and removes an inherited premise from §A's foundation.

3. **Refute your best finding.** The flagship (a remediation-introduced mis-cite in C151 — a class with 8 prior instances and a live neighbor in C158-N1) was raised, pursued to §7.1's MUST list, and then **killed by one grep**: §6.3 L595 is the only site naming "Peer-to-peer ATP transfers." Three further candidates died the same way. Four raised, four refuted — the pass's honest output is *zero*, and the refutations are the deliverable.

4. **A grep returning exactly one hit is a hypothesis, not a verdict.** Candidates 2 and 3 were both born from a single-hit grep (`decay` → 1; `reverse` → 1) and both died when the concept was found under a **different token** (`Reputation Decay` in a sibling; `bidirectional` in the target itself, twice). Search for the *concept*, then for the *word*.

5. **"Is it NEW?" before "is it TRUE?" — and this time the answer was NO.** C164 birthed [[prose is not the ledger]] by finding a genuinely dropped carry. Applying the same lens here surfaced two absent-by-ID candidates (B3d; B12/B13/B14) that both turned out to be **correctly routed**, not dropped — one to a private cross-cutting bundle, one to a documented root-cause compression. The lesson generalizes with a caveat: *absence from §C is the start of the question, not the answer.* The residual finding (C166-N1) is therefore about **ledger locality**, not loss — and is strictly weaker than C164-N1. Recording it at its true strength, rather than inflating it to match its predecessor, is the point.

6. **Verify an inbound enumeration by re-derivation.** C158's "dictionary-entities **4**" was re-derived by parsing all 17 fences from ground truth, not by trusting the sibling's count. It **confirmed** (4 fences / 11 comment lines). A confirmed enumeration is as much a result as a refuted one.

7. **A new ontology file is not an ontology fix.** `role-extension.ttl` landing in `web4-standard/ontology/` is the first ontology *addition* since C17-M1 was raised. It closed nothing (zero dictionary predicates) — but it *did* partially dissolve the premise of a **different** carry (C17-H2), by supplying a canonical custom-role-label pattern. Corpus deltas move carries in ways their filenames don't advertise; sweep each carry against the delta, not each delta-file against the carries.
