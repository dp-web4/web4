# C204 — Delta Re-Audit: dictionary-entities.md (5th delta)

**Date**: 2026-07-16
**Auditor**: Legion autonomous web4 track (slot `180036`, v2 protocol)
**Target**: `web4-standard/core-spec/dictionary-entities.md` (603 lines)
**Lineage**: C17 (`dictionary-entities-internal-consistency-2026-05-27.md`, #241/#242) → C52 (81-agent exhaustive, #323) → **C53 remediation** (#324, `95d20919`, 9 findings) → C94 (2nd delta, 9/9 held, 0 net-new) → C132 (3rd delta, 2nd consecutive clean, #444) → C166 (4th delta, 3rd consecutive clean, #497) → **C204** (this doc)
**Window**: C166 head `65631861` → HEAD `4693e465`. **58 commits.**
**Staleness**: **Frozen target, moving corpus** — the same shape as C166 (and the recent 5th-delta cohort: C196 acp, C198 presence, C200 mrh, C202 SOCIETY_SPEC).

**Method**: §A prove-the-freeze by blob identity + prior-finding verification at live bytes. §B refute-by-default sweep **bounded to the corpus delta** — one intersect-or-disjoint adjudication per moved surface, each citing the moved hunk (C120/C123 discipline); **no finder agent pointed at the 603 frozen lines** (C164 manufacture-findings ruling). SDK/Rust-mirror gate **re-derived at live HEAD** (the METHOD GUARD: the mirror set is not fixed; net-new has historically lived there). §C carry ledger re-derived from **lineage prose, not from C166's §C** ([[prose is not the ledger]]), with the C98 snapshot-presence guard and the C90 inbound-carry read.

---

## Summary

| | Count |
|---|---|
| **§A** C53 findings re-verified at live lines | **9 / 9 HELD**, 0 regressed (byte-freeze proven cryptographically) |
| **§B** moved surfaces adjudicated | **7** — 3 INTERSECT (clean-by-layer / untouched), 4 DISJOINT (all cited) |
| **§B** candidates raised | **2** |
| **§B** candidates surviving refutation | **0** |
| **§B** NET-NEW autonomous spec defects | **0** |
| **SDK/Rust-mirror gate** | **NEGATIVE** (Python byte-frozen; Rust absent — 0 hits / 29 files) |
| **§C** net-new **ledger** findings | **0** (1 INFO routed off-spec, not asserted) |
| Autonomous-in-file items for C205 | **0** → **C205 = DECLARED NO-OP** |

**Health verdict**: `dictionary-entities.md` is in **excellent health** — the **fourth consecutive fully-clean delta** (C94, C132, C166, C204). The largest inbound surface this cycle (the W4IP governance-vocab ratifications: Effector role, response vocabulary, Coercive/Extractive category) produces **no drift** on the target. Recorded as a positive result, not padded.

---

## §A — Prior-Finding Verification

**Freeze proven, not asserted.** The target's blob SHA is byte-identical across the whole lineage:

```
C53  95d20919:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
C94  8c581465:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
C132 286e5600:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
C166 65631861:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
HEAD 4693e465:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
```

⇒ the 9 C53 findings hold **by construction**, and the `#324` regression sweep is clean by construction. Re-confirmed first-hand at live line numbers (not copied from C166):

| C53 finding | Claim | Live line | Status |
|---|---|---|---|
| **B1** [MED] | `witness_required = confidence < 0.95 or request.trust_requirements.require_witness` | L246 | **HELD** |
| **B3a** [MED] | `lct:web4:dictionary:medical-legal` long form | L48 / L162 / L259 / L417 | **HELD** |
| **B3b** [MED] | `lct:web4:dictionary:legal-insurance` | L164 / L267 / L512 | **HELD** |
| **B3c** [LOW] | §10.2/§10.3 ids long form | L531 / L545 | **HELD** |
| **B4** [MED] | §2.1 V3 = `(Valuation, Veracity, Validity)` | L41 | **HELD** |
| **B5** [MED] | §7.1 R6 role keyed `"actor":` | L417 | **HELD** |
| **B19** [LOW] | §7.1 rules `"minimum_fidelity":` | L413 | **HELD** |
| **B20** [LOW] | `request.source_domain, request.target_domain` | L202 | **HELD** |
| **B21** [LOW] | `stake_on_translation(self, amount, confidence_claim, actual_confidence)` | L565 | **HELD** |

**Mirror freshness** (`#324` regression sweep): SDK `web4/dictionary.py` blob `edd97183` and `tests/test_dictionary.py` blob `d8f71420` are byte-identical at C166 and HEAD; the `protocols/web4-dictionary-entities.md` sister doc blob `b28d8f9e` is unchanged. `git log 65631861..HEAD -- '*dictionar*'` returns **only** C166's own audit doc (#497) and a whitepaper rewrite (`4bd36e8a`, a **0-insertion/0-deletion** touch of `dictionaries.md` — content-frozen). ⇒ the SDK cross-track bundle (B15–B18, B24, B25) stands verbatim.

---

## §B — Fresh Sweep (corpus-delta surface, refute-by-default)

**Verdict: 0 net-new autonomous target defects.**

The target has **zero outbound `.md` links** (a pre-existing corpus idiom of this document). Intersection is therefore measured against concept usage and **reverse-intersection** (does a moved sibling *name* `dictionar`?).

### B.1 — Adjudication of the 7 moved surfaces

| # | Moved surface | Commit | Moved hunk (cited) | Verdict |
|---|---|---|---|---|
| 1 | `entity-types.md` | `1354e4c2` (#523, W4IP N2) | **§4.8** Effector Role (+65) inserted at L~396 + a §4-subsection-count note at L278 | **INTERSECT — clean-by-layer** |
| 2 | `society-roles.md` | `1354e4c2` (#523) | **§231** Effector added to the *illustrative* role list; **§375** SAL-crosswalk row gains "Effector" | **INTERSECT — untouched** |
| 3 | `LCT-linked-context-token.md` | `d89595e8` (#531) | **§1.2** "Inspectable Evidence, Not Prescribed Trust" design principle | **INTERSECT — consistent** |
| 4 | `reputation-computation.md` | `767eb564` (#521, W4IP N1) | **§4** Coercive/Extractive rule category + decision-vocabulary sync | **DISJOINT** |
| 5 | `hub-law-schema.md` / `hub-law.ttl` | `87377c38` (#522) / `767eb564` | response vocabulary `notice\|quarantine\|correct\|rehabilitate` | **DISJOINT** |
| 6 | `web4-core/src/*.rs` (`ratchet.rs`, `society.rs`, `attestation.rs`, `lct.rs`, …) | `7b048a78` (#529), #499/#504/#527 | Rust primitives | **DISJOINT** — `grep -rilE dictionar web4-core/src/` = **0 hits / 29 files** |
| 7 | `whitepaper/…/dictionaries.md` | `4bd36e8a` | **0-line** change (mode/touch only) | **DISJOINT** — content-frozen (C98 guard) |

Disjointness / clean-by-layer proofs (per condition 1: *disjoint ⇒ record and stop; do not spider*):

- **#1 (Effector, entity-types §4.8)** — the insertion lands **above §10**, so dictionary's §10.1–10.3 (L621–683) are byte-unmoved and §10.2 still holds `"entity_type": "dictionary"` — the **C64-B7 / B26 sibling-canonicity carry is undisturbed** (a section-number cross-ref, not a line-number one). Layer separation: entity-types L80 lists Dictionary among **R6-capable Responsive** entities; the Effector is **always-R7** (response-side enactment). Dictionary is never registered as an Effector, and the §4.8 hunk does not touch the entity-type→role assignment tables (L258/265/268). No renumber of dictionary's §10, no role-table change, no contradiction.
- **#2 (Effector, society-roles §231)** — added inside the *"commonly defined when needed … illustrative, not exhaustive"* list, **after** the Oracle entry and **before** Steward; dictionary's role entry (§302–306) is byte-unmoved. Effector's function ("enacts the society's graded responses to witnessed violations") is disjoint from Dictionary's ("living semantic bridges managing compression-trust"). No contradiction.
- **#3 (LCT §1.2)** — the only in-window change to the LCT spec doc is #531's §1.2 principle; the dictionary references in LCT (entity_type enum L57/L97; §10.4 "LCT and Dictionary Entities" L606–609) are **untouched**. The principle ("a verification surface's job is to make evidence inspectable, not to encode a universal trust threshold") is **consistent** with dictionary's evidence-producing confidence model — see B.2 Candidate 2.
- **#4 (reputation Coercive/Extractive)** — `grep -c dictionar reputation-computation.md` = **0**. Dictionary's reputation sites (L333/L339 scores, L344–345 thresholds, L455 threat table, L551 §11 heading) do not consume the rule-category taxonomy. This is the same surface C166 Candidates 2/4 cleared; the §4 addition does not reach it.
- **#5 (response vocabulary)** — society-law-scoped enactment verbs; dictionary defines no enforcement/response surface (its `require_witness`/`stake_on_translation` are self-defense, not society enactment).
- **#6** — the ratchet (#529) and the LCT schema evolution (#499/#504/#527: key-derived `lct_id`, `binding_proof`, birth-certificate, attestation) landed as **Rust + schema**, with **no** dictionary representation anywhere in `web4-core/src/` (0 hits). Dictionary has no Rust mirror to diverge.
- **#7** — the whitepaper `dictionaries.md` diff is `0 insertions(+), 0 deletions(-)`; content byte-identical (C98 snapshot-presence guard).

### B.2 — Candidates raised, and their refutations

Two candidates were raised. **Both refuted.** Per [[refute your BEST finding]], the refuter was pointed at the strongest one first.

#### Candidate 1 (FLAGSHIP) — "the ratified Effector role + Coercive/Extractive category now constitute a response-side governance layer that dictionary §8.1's threat table and §11.2 partial-slash bypass / contradict" → **REFUTED**

The strongest available charge, and the one with the best prior: this window landed the **largest single governance-vocabulary expansion** of the whole rotation (Effector role across three docs, response vocabulary in hub-law, Coercive/Extractive rule category), and dictionary carries a live governance-adjacent gap already on the books — **C52-B9** (§11.2 *authority-less* partial slash). The charge: dictionary §8.1 (L455 `| Reputation gaming | ATP staking, temporal decay |`) and §11.2's `return amount * (actual_confidence / confidence_claim)  # Partial slash` are enforcement surfaces that should now route through — or are contradicted by — the Effector's `parse-don't-enact` response vocabulary and the Coercive/Extractive taxonomy.

**Refutation — three independent grounds.**
1. **Layer separation (identical to the C196/C198/C202 W4IP rulings).** The Effector (entity-types §4.8, society-roles §231, SAL §5.6) is a **SAL / society-law-scoped enactment role** — *"Who fills it, its thresholds, and when it acts are society law."* Dictionary is a **Responsive/Agentic** semantic bridge, never registered as an Effector. §8.1 lists **mitigations against attacks on dictionaries** (dictionary self-defense), not **graded responses a society enacts** (Effector enactment). Different layer; no contradiction — the same partitioned-layer verdict acp/presence/SOCIETY_SPEC reached for their W4IP inbounds.
2. **Reverse-intersection is empty.** `reputation-computation.md` (Coercive/Extractive) names `dictionar` **zero** times; the Coercive/Extractive category classifies **society rules**, which dictionary's threat table does not consume.
3. **B9 is unchanged, not hardened, this cycle.** B9's canonical anchor is `atp-adp-cycle.md` §2.4 `slash_atp`, whose blob (`2d060579`) is **byte-frozen C166→HEAD**. The Effector landing adds a response-*enactment* role; it does not touch §2.4's slash bookkeeping. B9 remains OPEN (hardened-by-C79 and -C151 from prior cycles), **not further hardened** here.

Also per [[refute your BEST finding]]: is "Effector" a **redefinition** colliding with a dictionary term? Dictionary has no effector/enforcement concept — no collision. Is the R6/R7 split consistent? L80 marks Dictionary R6-**capable**; the Effector is a distinct R7 role an entity may additionally fill. Coexistent. The charge does not survive.

**Residue (routed, not asserted).** A genuine **DESIGN-Q** survives the refutation of the *defect*: now that the Effector role and response vocabulary are ratified, whether a society *should* route dictionary-threat responses (§8.1) through Effector enactment is an open governance-design question — but it is **not a dictionary spec defect**, it is **pre-existing in spirit** (§8.1 predates the freeze), and it is **operator-owned**. Routed as INFO to the operator memo (§C.2); not asserted here.

#### Candidate 2 — "LCT §1.2 'Inspectable Evidence, Not Prescribed Trust' is now ratified; dictionary's `witness_required = confidence < 0.95` (L246) prescribes a trust threshold, violating the new principle" → **REFUTED**

The newest ratified norm in the corpus (baked into `CLAUDE.md`'s accountability self-audit and canonized specifically to prevent the "smuggle a trust threshold into a verification surface" bug — the ratchet `satisfied_by` regression of 2026-07-16). A frozen file predating it is a legitimate corpus-delta lens.

**Refutation — two grounds.** (i) The `0.95` is a **witness-trigger**, not an exclude/admit verdict: crossing it *escalates to produce more evidence* (a witness), which is exactly the behaviour §1.2 endorses — "make evidence inspectable," not "encode a threshold that decides trust." It never denies a translation; it raises the evidence bar. (ii) **Scope**: §1.2 governs **LCT verification surfaces** (key-binding, identity, quorum proofs); dictionary's `witness_required` gates **translation-confidence witnessing**, a different surface. C52-B1 already certified L246's exact form. The whitepaper/principle claim is backed; the target is consistent. Refuted.

### B.3 — Overcall guard

The target is byte-identical to bytes cleared by C52 (81-agent exhaustive), C94 (full-file refute-by-default), C132, and C166. No candidate cleared the guard. **No candidate is promoted; none is demoted-but-recorded as a spec defect.**

---

## §C — Carry Ledger (re-derived from lineage prose, not from C166's §C)

Per policy condition 3 this section is **additive only**. C166 and all prior audit docs are left byte-unchanged (C163 no-retro-edit ruling). The C166 §C.4 frontier is the current one; deltas this cycle:

### C.1 — Carry status updates (evidence-backed)

| Carry | Class | Status this cycle |
|---|---|---|
| **C52-B9** | operator DESIGN-Q | OPEN — hardened-by-C79 and -C151; **anchor `atp-adp §2.4` byte-frozen C166→HEAD ⇒ not further hardened this cycle** (Effector landing is response-enactment, not slash bookkeeping) |
| **C17-M1** | operator DESIGN-Q | OPEN — sweep refreshed: `grep -riE dictionar web4-standard/ontology/` = **0 hits**; **no new `.ttl` added since C166**; `hub-law.ttl` (#521 touch) adds no dictionary predicate. Six `web4:*` dictionary predicates remain undefined. |
| **C17-H2** | operator DESIGN-Q | OPEN — candidate resolution path (role-extension `SocietyRole::Custom`) unchanged in-window; `role-extension.{ttl,md}` not moved by #523 (which touched entity-types/society-roles/SAL) |
| **B26** (root: B12/B13/B14) | INFO design-Q, 3-doc canonicity | OPEN — all three anchors frozen: target (`8e06a23c`), `protocols/` sibling (`b28d8f9e`), entity-types §10.2 (**untouched by #523**, insertion above §10). B13 (Dictionary LCT wire-structure) **not widened** — both sides frozen in-window. |
| **B3d** | INFO design-Q → C33 id-scheme bundle | OPEN — re-inlined at C166; carried in `carries.md` |
| **C158 `//`-fence** | INFO-corpus (inbound) | OPEN — count verified = 4 at C166; target frozen ⇒ unchanged |
| **B2/B6/B7/B8/B10/B11/B22/B23**, **C17-M4/M6**, **C64-B7**, **C17-INFO3**, **B15–B18/B24/B25** | operator DESIGN-Q / cross-doc / SDK | OPEN, unchanged (all anchors frozen) |

### C.2 — Inbound carry (C90 read of sibling audit docs since C166)

The in-window sibling audits (C168 metabolic, C172 LCT, C174 ISP, C176 entity-types, C178 errors, C180 security, C182 registries, C184 handshake, C186 web4-lct, C188 mcp, C190 atp-adp, C192 t3-v3, C194/C195 reputation, C196 acp, C198 presence, C200 mrh, C202 SOCIETY_SPEC) route **no item to a dictionary pass**. Confirmed by reverse-grep: none of their remediations touch a dictionary line (the only `dictionar`-naming movers — entity-types, society-roles, LCT — were adjudicated in §B, all untouched-or-clean-by-layer).

**Outbound this cycle (INFO, routed — NOT asserted, NOT self-applied):** the §B.2-Candidate-1 residue — whether ratified Effector enactment should be wired to dictionary §8.1 threat responses is an **operator governance DESIGN-Q**, added to the operator memo. It is not a dictionary spec defect.

### C.3 — NET-NEW

**None.** Applying [[prose is not the ledger]] to the full lineage prose surfaced no absent-by-ID carry that is a true silent drop (the B3d and B12/B13/B14 locality question was resolved and re-inlined at C166; unchanged here). The C166-N1 ledger-locality remedy stands. No new ledger finding this cycle.

---

## §D — Disposition

**There are NO autonomous spec defects to remediate.** §A: 9/9 held on a cryptographically-frozen file. §B: 7 surfaces adjudicated (3 INTERSECT clean, 4 DISJOINT), 2 candidates raised, **2 refuted**, 0 net-new. SDK/Rust-mirror gate NEGATIVE (Python frozen; Rust absent). §C: 0 net-new ledger findings; 1 INFO routed off-spec.

- **C205 = DECLARED NO-OP on the spec side** (precedent: C131→C132, C155, C161, C165, C167, C203; policy condition 4). Zero bytes of `dictionary-entities.md`, any sibling, any `.ttl`, any schema, any SDK source, any test vector, or the whitepaper were mutated by this turn.
- **Rotation advances (+2)** to `SOCIETY_METABOLIC_STATES` = **C206** (lineage C21 → C54/C55 → C96 → C133 → C168 → next).
- **Fourth consecutive fully-clean dictionary delta** (C94, C132, C166, C204). The file churns far slower than the audit cadence; this is steady state and is recorded as a positive result.

**"At the NEXT (6th) dictionary delta" guards** (do NOT re-flag):
- Do **not** re-open the **Effector / W4IP-vocab** charge on the dictionary side — ruled CLEAN-BY-LAYER at C204 (§B.2 Candidate 1), consistent with the acp/presence/SOCIETY_SPEC W4IP rulings. Re-examine only if a future commit registers Dictionary *as* an Effector or edits dictionary §8.1/§11.2.
- Do **not** re-open the **LCT §1.2** charge — dictionary's `0.95` witness-trigger is evidence-raising, not threshold-prescribing (§B.2 Candidate 2).
- **B9** is anchored at `atp-adp §2.4` (frozen `2d060579`); re-check hardening only if that section moves.
- **C17-M1** ontology sweep = 0 hits; re-run only if a new `.ttl` lands or an existing one gains a `dictionar` token.
- The frozen-target guards from C166 still apply (Candidates 1–4 there all REFUTED; do not re-manufacture).

**Standing frontier** (nothing autonomously actionable): see C166 §C.4, updated by §C.1 above.

---

## §E — Method & Governance Notes

1. **Frozen target, moving corpus — sized to the delta.** 58 commits moved; the target's 603 lines did not. §B was bounded to the moved surfaces (one adjudication each), and no agent was pointed at the cleared lines — the C164 proportionality/manufacture-findings discipline. The honest yield of a clean delta *is* the refutations.

2. **Prove the freeze; don't inherit it.** Blob identity was re-checked across five lineage commits (C53/C94/C132/C166/HEAD), not copied from C166's assertion. One command; removes an inherited premise from §A's foundation.

3. **Refute your best finding — and it was the biggest inbound.** The flagship was the largest governance-vocab expansion of the rotation (Effector + response vocabulary + Coercive/Extractive) against dictionary's live B9 gap. It died on three independent greps: society-law-scoped role vs Responsive entity (layer), 0 reverse-intersection in reputation-computation, and a byte-frozen B9 anchor. Big inbound ≠ big drift.

4. **Re-derive the mirror at live HEAD (the METHOD GUARD).** The SDK/Rust-mirror set is not fixed. This cycle: Python `dictionary.py`/`test_dictionary.py` byte-frozen; `web4-core/src/` NEGATIVE (0 `dictionar` hits / 29 `.rs` files, re-confirmed at HEAD — the ratchet/LCT-schema Rust work landed no dictionary representation). A dictionary with no Rust mirror cannot acquire a Rust-mirror divergence — recorded, not assumed.

5. **A section-number cross-reference survives an above-it insertion.** #523 inserted Effector at entity-types §4.8, shifting dictionary's §10 *down by line* but not *by section number*. The C64-B7/B26 canonicity carry (which cites "§10.2") is undisturbed. Line drift ≠ reference breakage; check which kind of anchor the carry uses.

6. **A new principle is a lens, not a verdict.** LCT §1.2 ("Inspectable Evidence, Not Prescribed Trust") is the newest ratified norm and was applied as an adversarial lens to the target's `0.95` gate — which passed, because a witness-*trigger* raises evidence rather than deciding trust. The principle's own definition supplied its refutation.
