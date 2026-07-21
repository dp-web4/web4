# C242 — Delta Re-Audit: dictionary-entities.md (6th delta)

**Date**: 2026-07-21
**Auditor**: Legion autonomous web4 track (slot `120036`, v2 protocol)
**Target**: `web4-standard/core-spec/dictionary-entities.md` (603 lines)
**Lineage**: C17 (`dictionary-entities-internal-consistency-2026-05-27.md`, #241/#242) → C52 (81-agent exhaustive, #323) → **C53 remediation** (#324, `95d20919`, 9 findings) → C94 (2nd delta, 9/9 held, 0 net-new) → C132 (3rd delta, clean) → C166 (4th delta, clean, #497) → C204 (5th delta, clean, #534) → **C242** (this doc)
**Window**: C204 head `4693e465` → HEAD `45082055`. **35 commits.**
**Staleness**: **Frozen target, moving corpus** — identical shape to C204 and the recent 6th-delta cohort (C234 acp, C236 presence, C238 mrh, C240 SOCIETY_SPEC).

**Method**: §A prove-the-freeze by blob identity + prior-finding verification at live bytes. §B refute-by-default sweep **bounded to the corpus delta** — one intersect-or-disjoint adjudication per moved surface, each citing the moved hunk (C120/C123 discipline); **no finder agent pointed at the 603 frozen lines** (C164 manufacture-findings ruling). SDK/Rust-mirror gate **re-derived at live HEAD** (the METHOD GUARD: the mirror set is not fixed). §C carry ledger re-derived from **lineage prose, not from C204's §C** ([[prose is not the ledger]]), with the C98 snapshot-presence guard and the C90 inbound-carry read.

---

## Summary

| | Count |
|---|---|
| **§A** C53 findings re-verified at live lines | **9 / 9 HELD**, 0 regressed (byte-freeze proven cryptographically) |
| **§B** moved spec/ontology surfaces adjudicated | **2** — both DISJOINT (0 reverse-intersection, both cited) |
| **§B** candidates raised | **1** |
| **§B** candidates surviving refutation | **0** |
| **§B** NET-NEW autonomous spec defects | **0** |
| **SDK/Rust-mirror gate** | **NEGATIVE** (Python byte-frozen; Rust absent — 0 hits / 23 files) |
| **§C** net-new **ledger** findings | **0** |
| Autonomous-in-file items for C243 | **0** → **C243 = DECLARED NO-OP** |

**Health verdict**: `dictionary-entities.md` is in **excellent health** — the **fifth consecutive fully-clean delta** (C94, C132, C166, C204, C242). The C204→HEAD window landed no `dictionar`-touching change other than C204's own audit doc; the two moved spec/ontology surfaces (role-extension oracle-sets, reputation §4 W4IP-status note) are disjoint by reverse-intersection. Recorded as a positive result, not padded.

---

## §A — Prior-Finding Verification

**Freeze proven, not asserted.** The target's blob SHA is byte-identical across the whole lineage:

```
C53  95d20919:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
C94  8c581465:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
C132 286e5600:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
C166 65631861:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
C204 4693e465:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
HEAD 45082055:  8e06a23cc2cc9f87e53c34e4f2ed25c82f130771
```

⇒ the 9 C53 findings hold **by construction**, and the `#324` regression sweep is clean by construction. Re-confirmed first-hand at live line numbers (not copied from C204):

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

**Mirror freshness** (`#324` regression sweep, re-derived at HEAD): SDK `web4/dictionary.py` blob `edd97183`, `tests/test_dictionary.py` blob `d8f71420`, and `protocols/web4-dictionary-entities.md` sister doc blob `b28d8f9e` are **byte-identical at C204 and HEAD**. `git log 4693e465..HEAD -- '*dictionar*'` returns **only** C204's own audit doc (`53d8f038`, #534). ⇒ the SDK cross-track bundle (B15–B18, B24, B25) stands verbatim.

---

## §B — Fresh Sweep (corpus-delta surface, refute-by-default)

**Verdict: 0 net-new autonomous target defects.**

The target has **zero outbound `.md` links** (`grep -cE '\]\([^)]*\.md'` = 0; a pre-existing corpus idiom of this document, re-confirmed live). Intersection is therefore measured against concept usage and **reverse-intersection** (does a moved sibling *name* `dictionar`?). The 35-commit window is dominated by sibling audit docs (C206–C240) and hub/lct feature work; only **two** spec/ontology files moved.

### B.1 — Adjudication of the 2 moved spec/ontology surfaces

| # | Moved surface | Commit | Moved hunk (cited) | Verdict |
|---|---|---|---|---|
| 1 | `ontology/role-extension.ttl` | `4f76f110` (#547, "oracle consult/write sets") | +`role:oracleConsultSet` / +`role:oracleWriteSet` properties on `role:Scope` (L138–147) | **DISJOINT** |
| 2 | `core-spec/reputation-computation.md` | `#541` (C214-N1 §4 note) | §4 "Evidence-basis role" note: W4IP response side re-worded from *proposed* → *partially ratified* (Effector + response vocabulary) | **DISJOINT** |

Disjointness proofs (per policy condition 1: *disjoint ⇒ record and stop; do not spider*):

- **#1 (role-extension oracle-sets)** — `grep -in dictionar role-extension.ttl` = **0**. The two new properties gate an entity-role's **oracle** consult/write access (frozen-at-grant, reputation-blind set membership); dictionary is never registered as an oracle Scope and the addition does not touch the custom-role mechanism. Ontology sweep for the target is unchanged (see §C, C17-M1 still 0 hits). This is the sibling of the C17-H2 **resolution path** (`role-extension` custom-role), not a change to it — the oracle-set properties are orthogonal to `SocietyRole::Custom`. No intersection.
- **#2 (reputation §4 note)** — `grep -c dictionar reputation-computation.md` = **0** (reverse-intersection empty, exactly as at C204). The diff only updates the W4IP-status prose ("The response side has since been partially ratified… response vocabulary… Effector role…"); it introduces **no new taxonomy** dictionary consumes. Dictionary's reputation sites (L333/L339 scores, L344–345 thresholds, L455 threat table, §11 heading) are byte-unmoved and do not reference the Coercive/Extractive category or the response vocabulary. This is the same surface C204 §B ruled DISJOINT; the note-refresh does not reach the target.

Both surfaces are the **W4IP-vocab lineage** that the C204 "6th-delta guard" (§D) explicitly fences: *do not re-open the Effector / W4IP-vocab charge on the dictionary side — ruled CLEAN-BY-LAYER at C204, unless a commit registers Dictionary as an Effector or edits dictionary §8.1/§11.2.* Neither happened. The dictionary spec is byte-frozen; neither moved sibling names it.

### B.2 — Candidate raised, and its refutation

Per [[refute your BEST finding]], one candidate was raised and pointed at the strongest available lens.

#### Candidate (FLAGSHIP) — "the W4IP response side is now *ratified* (no longer merely proposed, per reputation §4 #541); dictionary §8.1 threat mitigations / §11.2 partial-slash are enforcement surfaces that should now route through Effector enactment or are contradicted by it" → **REFUTED**

This is the C204 flagship re-armed with a genuine in-window delta: at C204 the Effector/response-vocab was *newly ratified*; this cycle the **reputation §4 note itself was rewritten** (#541) to reflect that ratification — arguably strengthening the "response side is real, so dictionary's self-defense surfaces should route through it" charge.

**Refutation — three independent grounds (unchanged in force from C204, re-verified live):**
1. **Layer separation.** The Effector (entity-types §4.8, society-roles §4.1, SAL §5.6) is a **SAL / society-law-scoped enactment role**. Dictionary is a **Responsive/Agentic** semantic bridge, **never registered as an Effector** (grep of the moved siblings: dictionary named 0×). §8.1 lists **mitigations against attacks on dictionaries** (self-defense), not **graded responses a society enacts** (Effector enactment). Different layer; no contradiction — the identical partitioned-layer verdict the acp/presence/SOCIETY_SPEC/atp-adp W4IP passes reached (C196/C198/C202/C228).
2. **Reverse-intersection is empty.** The #541 note lives in `reputation-computation.md`, which names `dictionar` **0** times; the response vocabulary lives in `hub-law-schema.md`, which the dictionary spec does not consume.
3. **B9 anchor is byte-frozen, not hardened.** B9's canonical anchor is `atp-adp-cycle.md` §2.4 `slash_atp`, blob `2d060579` — **byte-frozen C204→HEAD** (C228 confirmed atp-adp zero-routed). The reputation §4 note refresh touches no slash bookkeeping. B9 remains OPEN (hardened-by-C79/-C151 from prior cycles), **not further hardened** here.

**Residue (routed, not asserted).** The same DESIGN-Q C204 routed survives: whether a society *should* wire ratified Effector enactment to dictionary §8.1 threat responses is an open governance-design question — **not a dictionary spec defect** (§8.1 predates the freeze), operator-owned. Carried, not re-asserted.

### B.3 — Overcall guard

The target is byte-identical to bytes cleared by C52 (81-agent exhaustive), C94, C132, C166, and C204. The single candidate died on three live greps. **No candidate is promoted; none is demoted-but-recorded as a spec defect.**

---

## §C — Carry Ledger (re-derived from lineage prose, not from C204's §C)

Per policy condition 3 this section is **additive only**. C204 and all prior audit docs are left byte-unchanged (C163 no-retro-edit ruling). Deltas this cycle:

### C.1 — Carry status updates (evidence-backed)

| Carry | Class | Status this cycle |
|---|---|---|
| **C52-B9** | operator DESIGN-Q | OPEN — anchor `atp-adp §2.4` blob `2d060579` **byte-frozen C204→HEAD** ⇒ not further hardened (reputation §4 note is response-status prose, not slash bookkeeping) |
| **C17-M1** | operator DESIGN-Q | OPEN — sweep refreshed: `grep -riE dictionar web4-standard/ontology/` = **0 hits**; `role-extension.ttl` moved (+oracle-sets, #547) but names no `dictionar` predicate; six `web4:*` dictionary predicates remain undefined |
| **C17-H2** | operator DESIGN-Q | OPEN — candidate resolution path (`role-extension` `SocietyRole::Custom`) unchanged; #547's oracle-set properties are orthogonal to the custom-role mechanism |
| **B26** (root: B12/B13/B14) | INFO design-Q, 3-doc canonicity | OPEN — all three anchors frozen: target (`8e06a23c`), `protocols/` sibling (`b28d8f9e`), entity-types §10.2 `"entity_type": "dictionary"` (live **L635**, untouched in-window). B13 not widened — both sides frozen |
| **B3d** | INFO design-Q → C33 id-scheme bundle | OPEN — carried in `carries.md` |
| **C158 `//`-fence** | INFO-corpus (inbound) | OPEN — target frozen ⇒ count unchanged |
| **B2/B6/B7/B8/B10/B11/B22/B23**, **C17-M4/M6**, **C64-B7**, **C17-INFO3**, **B15–B18/B24/B25** | operator DESIGN-Q / cross-doc / SDK | OPEN, unchanged (all anchors frozen) |

### C.2 — Inbound carry (C90 read of sibling audit docs since C204)

The 18 in-window sibling audits (C206 metabolic, C208 SAL, C210 LCT, C212 ISP, C214 entity-types, C216 errors, C218 security, C220 registries, C222 handshake, C224 web4-lct, C226 mcp, C228 atp-adp, C230 t3-v3, C232 reputation, C234 acp, C236 presence, C238 mrh, C240 SOCIETY_SPEC) route **no item to a dictionary pass**. Five name `dictionar` incidentally, all confirmed non-routing:
- **C202/C206/C216** — rotation-order / provenance notes ("advances to dictionary", "C204 declared C205 no-op").
- **C218** — consistency note ("C204 dictionary → 0 dictionar" as one of four disjointness precedents on `attestation.rs`).
- **C214** — (i) entity-types cites dictionary-entities as a sibling that "has not moved"; (ii) **C176-N1** SDK `EntityType` absence list includes "Dictionary" — this is an **SDK/Rust-core** item (the Rust `EntityType` enum lacks a Dictionary variant), already travelling in the C172/C174/C176 SDK-mirror bundle, **not a `dictionary-entities.md` spec defect**. Noted for provenance; not a new dictionary carry.

**Outbound this cycle (INFO, routed — NOT asserted, NOT self-applied):** the §B.2 residue (whether ratified Effector enactment should wire to dictionary §8.1 threat responses) remains an operator governance DESIGN-Q. Unchanged from C204; not re-raised as a defect.

### C.3 — NET-NEW

**None.** Applying [[prose is not the ledger]] to the full lineage prose surfaced no absent-by-ID carry that is a true silent drop. No new ledger finding this cycle.

---

## §D — Disposition

**There are NO autonomous spec defects to remediate.** §A: 9/9 held on a cryptographically-frozen file. §B: 2 moved spec/ontology surfaces adjudicated (both DISJOINT, 0 reverse-intersection), 1 flagship candidate raised and **refuted** on three live grounds, 0 net-new. SDK/Rust-mirror gate NEGATIVE (Python frozen; Rust absent, 0/23). §C: 0 net-new ledger findings.

- **C243 = DECLARED NO-OP on the spec side** (precedent: C131→C132, C203→C204's C205, C205, C207, …; policy condition 4). Zero bytes of `dictionary-entities.md`, any sibling, any `.ttl`, any schema, any SDK source, any test vector, or the whitepaper were mutated by this turn.
- **Rotation advances (+2)** to `SOCIETY_METABOLIC_STATES` = **C244** (lineage C21 → C54/C55 → C96 → C133 → C168 → C206 → next).
- **Fifth consecutive fully-clean dictionary delta** (C94, C132, C166, C204, C242). The file churns far slower than the audit cadence; steady state, recorded as a positive result.

**"At the NEXT (7th) dictionary delta" guards** (do NOT re-flag):
- Do **not** re-open the **Effector / W4IP-vocab** charge on the dictionary side — ruled CLEAN-BY-LAYER at C204 **and again at C242** (the reputation §4 ratification-status refresh #541 does not reach the target). Re-examine only if a future commit registers Dictionary *as* an Effector or edits dictionary §8.1/§11.2.
- Do **not** re-open the **LCT §1.2** charge — dictionary's `0.95` witness-trigger is evidence-raising, not threshold-prescribing (C204 §B.2 Candidate 2).
- **B9** is anchored at `atp-adp §2.4` (frozen `2d060579`); re-check hardening only if that section moves.
- **C17-M1** ontology sweep = 0 hits; the `role-extension.ttl` oracle-set additions (#547) do **not** name a dictionary predicate — re-run only if a new `.ttl` lands or an existing one gains a `dictionar` token.
- **C17-H2** resolution path (`role-extension` custom-role) is orthogonal to the #547 oracle-set properties — re-check only if the custom-role mechanism itself moves.
- The frozen-target guards from C166/C204 still apply (all prior candidates REFUTED; do not re-manufacture).

**Standing frontier** (nothing autonomously actionable): see C204 §C.1 / C166 §C.4, updated by §C.1 above.

---

## §E — Method & Governance Notes

1. **Frozen target, moving corpus — sized to the delta.** 35 commits moved; the target's 603 lines did not. §B was bounded to the **two** moved spec/ontology surfaces (one adjudication each); no agent was pointed at the cleared lines (C164 proportionality). The honest yield of a clean delta *is* the refutations.

2. **Prove the freeze; don't inherit it.** Blob identity was re-checked across six lineage commits (C53/C94/C132/C166/C204/HEAD), not copied from C204's assertion.

3. **Refute your best finding — and it was the same flagship, re-armed.** The reputation §4 note (#541) rewrote the W4IP response side from *proposed* to *partially ratified* — a genuine in-window strengthening of the C204 flagship charge. It died on the same three independent greps: society-law-scoped role vs Responsive entity (layer), 0 reverse-intersection in `reputation-computation.md`, and a byte-frozen B9 anchor. A ratification-status refresh is not a new intersection.

4. **Re-derive the mirror at live HEAD (the METHOD GUARD).** SDK `dictionary.py`/`test_dictionary.py`/protocols sibling all byte-frozen; `web4-core/src/` NEGATIVE (0 `dictionar` hits / 23 `.rs` files, re-confirmed at HEAD). A dictionary with no Rust mirror cannot acquire a Rust-mirror divergence — recorded, not assumed. (The SDK-track `EntityType`-enum "Dictionary absent" item surfaced at C214 is a Rust-core enum gap in the C172/C174/C176 bundle, not a `dictionary-entities.md` defect — routed, not duplicated.)

5. **An ontology mover that names nothing about the target is disjoint.** `role-extension.ttl` gained two oracle-scope properties (#547) — a real ontology delta — but it names no `dictionar` predicate and is orthogonal to the C17-H2 custom-role resolution path. Ontology motion ≠ dictionary-ontology motion; check the token before re-opening C17-M1/C17-H2.
