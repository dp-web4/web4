# C226 — `mcp-protocol.md` Fifth Delta Re-Audit (first non-frozen delta since C117 — §7.8 mailbox)

**Date**: 2026-07-19
**Auditor**: autonomous web4 session (legion, slot `120036`, C-series)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` (1020 lines, 16 sections)
**Instrument**: proportioned single-file re-read + live-HEAD anchor re-verification (loci re-resolved for the +56-line shift, not cached byte-identity) + **net-new normative-section audit** (§7.8, the first substantive mcp motion since C117) + **accountability self-audit (RWOA+S+V)** on the new mailbox surface + **SDK-mirror gate** (the C172–C220 discipline) at live HEAD + corpus-delta disjointness. Not a fan-out — one moved section, targeted.
**Scope**: §A delta re-verification of **C188** (4th delta) + its lineage; §B new findings — primarily the net-new **§7.8 Asynchronous Mailbox** (commit `3e765345`, 2026-07-13); SDK-mirror gate; corpus-delta since C188.
**This audit RECOMMENDS ONLY — no spec mutation this turn.** The one substantive finding (N1) introduces a *new normative obligation* (idempotency), which is not a zero-semantic-stretch citation fix → routed to author/operator, not self-applied. Two new files (this doc + session log).

**Lineage**: C35 (2026-06-06, #279) → C76 (#365) → C77 (`f3d2613d`, remediated 8) → C116 (#406) → C117 (`afab0c43`, applied N1) → C148 (CLEAN) → C188 (`91225131`, applied C154-N1, SDK PARTIAL) → **C226** (this audit).

---

## Headline

1. **First non-frozen mcp delta since C117 — §7.8 "Asynchronous Mailbox" is net-new normative content** (`3e765345`, 56 lines, 964→1020). Every prior mcp delta (C116/C148/C188) found the target byte-frozen and did §A-only ceremony; **this turn there is real new normative surface to audit.** §7.8 defines the entity-boundary queue that absorbs cross-society async: 7.8.1 accept-and-defer (`202` = delivery, not completion), 7.8.2 six queue-conformance MUST/SHOULD clauses, 7.8.3 push/poll unification.

2. **§7.8 is authored ACCOUNTABILITY-AWARE — the RWOA+S+V gate returns PASS with one recorded gap.** The section explicitly encodes the R-clause (*"every crossing is gated on receipt … rather than trusted on reachability"*, *"deliver only to that authenticated LCT"*), separates admission (non-consequential, *"not a ledger act"*) from witnessed completion (A-clause), and provides an escalation signal (overflow). This is the rare spec section that reads like it passed its own gate. **The single gap is on the O-clause once-only property (N1).**

3. **§B N1 (MEDIUM, spec under-specification — route to author/operator, do NOT self-apply).** §7.8.2 mandates **at-least-once** delivery bias + **consume-once** drain, and §7.8.1 generalizes the mailbox to deferred **R6/R7 actions** whose completion is a witnessed event. But §7.8 states **no consumer idempotency/dedup requirement**. A crash in the window *after an action completes (witnessed) but before its drain-removal is durable* triggers at-least-once **redelivery → double-completion** = a second witnessed reputation event / second ATP discharge. The dedup key already exists in the corpus (`action_id`, `r7-framework.md` §1.7 — note mcp itself never mentions `action_id`), so the remedy is one clause. Because it introduces a **new normative obligation** (not a zero-stretch citation fix), it is **not** auditor-applicable → operator/author ratification.

4. **SDK-mirror gate = GENUINE (hub-side, mailbox slice) — updates C188's "absent wire-layer" for this surface.** §7.8's named reference impl `hub/hub-lib/src/store.rs` + `hub-daemon/src/rest.rs` (`f62c9e6`) is a **genuine mirror** of §7.8.2's MUSTs (per-recipient-LCT keying, encrypted-at-rest via SQLCipher, durability flag with loud non-durable announcement, queue≠ledger, write-through park). **Divergence-by-narrowing:** the impl carries hub→citizen *notices* (delivery items), while the spec generalizes to inbound *R6/R7 actions* — so the impl does not exercise the N1 double-execution surface. hestia's deferred inbox (hestia #33) is external/private, not inspectable here.

5. **§A CLEAN — 8/8 C188 findings HELD, C154-N1 remediation HELD & CORRECT, 0 regression.** Anchors below §8 shifted **+56** (path-provenance discipline applied: every grep re-run at live HEAD, not trusted cached). The C154-N1 anchor (`reputation-computation.md` §4, L239/241) is **stable** — the intervening C195 edit (`062fd24b`) touched §5+ code (L413/L521/L534/L555), never §4.

---

## Severity legend

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR a normative value/structure is rejected by the canonical taxonomy/SSOT. |
| **MEDIUM** | Normative guidance self-contradicts / under-specifies enough that two good-faith implementations diverge. |
| **LOW** | Maintainability / precision / SDK-lag hazard; recoverable by a careful reader; not a blocking contradiction. |
| **INFO** | Observation; recorded for completeness or to confirm a seam was inspected and found bounded. |

---

## §A — Delta re-verification of C188 (+ lineage)

### A.1 — Prior findings, re-verified at LIVE HEAD (greps re-run; +56 shift accounted below §8)

| ID | Origin | Sev | Verdict | Current site (live HEAD) | Evidence re-run |
|----|--------|-----|---------|--------------------------|-----------------|
| **N1** | C116→C117 | LOW | **HELD** | §12 MUST #6, **L958** (was L902, +56) | *"for high-consequence actions … MUST NOT proceed without witnessing (§7.5) … `reputation.witnesses` … at least one Witness-role entry (§7.3)"*. |
| **C154-N1** | C154/C156-1, applied C188 | LOW | **HELD & CORRECT** | §7.3 **L415** (unchanged — above §8, no shift) | cites `reputation-computation.md` §4; anchor §4 present at repcomp L239/241 and **untouched by C195** (`062fd24b` edited L413/L521/L534/L555 = §5+). Old broken `t3-v3 … parameter governance` cite absent (grep-empty). |
| **B1+B11** | C76→C77 | HIGH | **HELD** | §3.1 L76 / note L119 | `entity_type:service`; *"`mcp_server`/`mcp_client` … MUST NOT be used"*. Both above §8 → loci unshifted. |
| **B3** | C76→C77 | MED | **HELD** | §7.3 L404 / L417 | `witnesses` array; each entry `{lct, signature, timestamp}` × `r7-framework.md` §1.7. (Still doubly load-bearing — §B C188-N1 SDK divergence unchanged.) |
| **B7** | C76→C77 | LOW | **HELD** | §7.3 (L395–419 band) | four `outcome_class` values inline. |
| **B8** | C76→C77 | LOW | **HELD** | §9.1 (+56) | `t3_in_role`; `.average()` scoped to present dims. |
| **B9** | C76→C77 | LOW | **HELD** | §7.4 L~423 | `responding_role_expected` OPTIONAL/advisory. |
| **B10** | C76→C77 | LOW | **HELD** | §7.1 | role harmonization note. |
| **N14** | C76→C77 | LOW | **HELD** | §7.4 | interim conformance note × §7.7.1. |

**A.1 tally**: 8 HELD · 0 REVERTED · 0 regression. C154-N1 remediation intact & its anchor stable. Every locus re-resolved at live HEAD; the +56 shift (from §7.8's insertion before §8) verified only affects anchors ≥ §8 (N1/C117 at L902→L958).

### A.2 — Cross-track / design-Q carries (cited siblings still frozen → dispositions unchanged)

All C188/C148 carries STAND: **B2+B6** (r7-reputation envelope shape — see §B C188-N1 re-verify), **B5+B12** (registry-home §7.6/§7.7 codes), **N5/N9/N13** (§7.7 promotion, WIP-fenced), **N12** (§10 vs RFC-9457), **N15** (`lct:web4:` id), **F5/C62-B1** (interaction_type home), **F9-inverted** (corpus PolicyEntity form), **B1-family** (`MCP_ENTITY_SPECIFICATION.md` `entity_subtype`). No self-resolution.

---

## §B — New findings since C188 (2026-07-12)

### B.0 — The delta: §7.8 Asynchronous Mailbox (`3e765345`)

Single-file, single-commit, +56 lines, no sibling touched (`git show --stat` = 1 file). Content: 7.8 preamble (mailbox = entity boundary interface, gated on receipt not reachability) + 7.8.1 accept-and-defer + 7.8.2 six conformance clauses + 7.8.3 push/poll = one mailbox.

### B.1 — Accountability self-audit (RWOA+S+V) of the §7.8 mailbox surface

```
surface: mcp §7.8 asynchronous mailbox
act: accept + durably defer + later complete an inbound cross-society R6/R7 action
S: mixed/mostly-reversible — low (R6 read / notice) to high (deferred R7 w/ reputation+ATP); the double-execution window (N1) is the one irreversibility risk [construct: §7.8.1 "R6/R7 outcome is witnessed when the action completes"]
R: pass [construct: §7.8.1 "gated on receipt … rather than trusted on reachability"; §7.8.2 "deliver only to that authenticated LCT"]
W: pass [construct: §7.8.2 per-recipient-LCT keying + §7.3 witness-on-completion + §7.2 delegated authority]
O: pass-with-gap [construct: admission is non-consequential — §7.8.1 "202 = delivery, not completion", "MAY be tracked entity-locally but is not a ledger act" — so R+W dominate the *execution*; BUT the at-least-once redelivery path (N1) does not guarantee the once-only property for a deferred consequential action]
A: pass [construct: §7.8.2 "completions project into the ledger, queue contents never do"]
V: present [construct: §7.8.2 overflow = "a load/stakes signal an entity MAY escalate on" + §7.3 witness/law gate at completion]
verdict: PASS with one recorded gap (N1) — surface is authored accountability-aware (R/W/A strong); the gap is the O-clause once-only property under the mandated at-least-once bias
```

### B.2 — N1 (MEDIUM, spec under-specification; route author/operator; do NOT self-apply)

**Finding.** §7.8.2 mandates two coupled failure semantics — **at-least-once** (*"If the park fails, the server MUST NOT acknowledge … at-least-once is the mandated failure bias"*; *"a failed drain leaves items queued for redelivery rather than risking loss"*) and **consume-once** (*"an item delivered to the consumer is atomically removed"*) — over a queue that §7.8.1 defines as carrying deferred **R6/R7 actions** whose **completion is a witnessed event**. The section states **no consumer idempotency / dedup requirement.**

**Failure scenario.** A consumer drains a deferred R7 action, **processes it to completion (witnessed → ledger)**, then crashes *before the atomic drain-removal is durable*. On restart, at-least-once redelivers the same item → the consumer **re-completes** it → a **second witnessed reputation event / second ATP discharge** for one logical action. `consume-once` governs only the happy-path removal; the section itself admits the redelivery window ("at-least-once bias"). This is the accountability-critical mirror of the park-before-ACK reasoning the section already performs at the *ingress* end — but at the *egress* (drain) end and for *consequential* items.

**Why it is genuinely under-specified (refutation survived):**
- Not covered elsewhere — mcp-protocol.md never mentions `action_id`; the corpus has **no** normative "ledger/witness dedups by `action_id`" statement (grep across core-spec = the sole hit is multi-device's unrelated idempotent witness-refresh).
- Not out of scope — §7.8.2 already legislates consumer behavior in detail (park-before-ACK, atomic consume-once, drop-oldest); idempotency-on-redelivery is the naturally-paired obligation to at-least-once, not a separable concern.
- The reference impl does not disprove it — the hub mailbox (§B.3) sidesteps double-execution only by **narrowing** to hub→citizen *notices* (idempotent-ish delivery), whereas the spec's normative scope is inbound *actions*.

**Remedy (recommended, for author/operator — NOT applied):** one clause in §7.8.2, e.g. *"A consumer completing a deferred R6/R7 action MUST make completion idempotent under redelivery (dedupe by the action's `action_id` per `r7-framework.md` §1.7); a redelivered item whose action already has a completion witness MUST be drained without re-execution."* This introduces a new normative obligation, so it is **not** auditor-applicable (a citation fix is; a new MUST is not) → routes to the author/operator alongside the standing **B2+B6** r7-envelope bundle (which already owns `action_id` as the cross-layer key).

### B.3 — SDK-mirror gate (C172–C220 discipline) — §7.8 has a GENUINE hub-side mirror

Re-derived §7.8's implementers at live HEAD. Ladder verdict for the **mailbox slice** = **GENUINE**.

| Candidate | Verdict | Evidence |
|-----------|---------|----------|
| `hub/hub-lib/src/store.rs` + `hub-daemon/src/rest.rs` (`f62c9e6`, "durable encrypted-at-rest mailbox", 326 LoC) | **GENUINE (mailbox surface, narrowed scope)** | `Mailbox (durable per-recipient sealed-notice queue)`; *"Each recipient LCT has one serialized queue"* = §7.8.2 per-LCT keying MUST; *"written at rest inside the SQLCipher-encrypted state DB … each notice body … additionally channel-sealed"* = §7.8.2 encrypted-at-rest + two-independent-layers; `mailbox_is_durable()` + loud non-durable startup warning = §7.8.2 durability MUST; `hydrate_mailbox` re-delivers across restart; *"the mailbox is durable delivery state, NOT the ledger"* = §7.8.1/7.8.2 queue≠ledger. **Narrows to hub→citizen notices** (*"delivery concerns … never the witnessed Act on the ledger"*) → does not exercise N1's deferred-action double-execution surface. |
| hestia deferred inbox (hestia #33) | **EXTERNAL — not inspectable** | private repo, not in this worktree; §7.8 names it as the other side of the wire. Recorded, un-verified here. |
| `implementation/sdk/web4/mcp.py` | **N/A for §7.8** | no mailbox surface; still the C188 types-layer mirror (see B.4). |

**Significance.** C188 recorded the wire layer as *absent* for mcp. For the **mailbox slice specifically**, §7.8 now ships **with** a genuine reference implementation — the first §7.8-surface mirror on the ladder. This is a *delivery-substrate* mirror, not the full R7-wire (no code path still assembles a Web4 Context Header + signs an R7 envelope + emits §7.6/§7.7 codes — the C180/C182/C184/C188-N2 wire-layer synthesis stands for everything except the mailbox queue).

### B.4 — C188-N1 re-verify (mcp.py ReputationEnvelope) — STANDS unchanged

`mcp.py` last touched `b6c243c2` (2026-05-19), **pre-C188** → the two §7.3 divergences (`witness_signatures: List[str]` flat vs structured `witnesses`; `trust_dimension_updates: Dict[str,float]` vs nested `{talent:{delta,context}}`; extra `action_id`) are **unchanged**. C188-N1 STANDS, routes the standing **B2+B6** bundle (SDK-side). No spec action.

### B.5 — Corpus-delta since C188 (`91225131..HEAD`, core-spec movers) — all DISJOINT

| Sibling | Commit | What moved | Cited by mcp? | Disposition |
|---------|--------|------------|---------------|-------------|
| entity-types / society-roles / SAL | `1354e4c2` #523 (Effector) | first-class Effector role | **not cited** (grep-empty) | **DISJOINT by non-citation** |
| SOCIETY_SPEC / hub-law-schema | `87377c3`/`cb78876` #522/#525 | response vocabulary (warn/quarantine/…) | not cited | **DISJOINT** |
| reputation-computation | `062fd24b` #526 (C195) | §5 no-match→None; `analyze_factors` :572 | **cited at L415** (via C154-N1, → §4) | **DISJOINT** — C195 edited §5+ (L413/521/534/555); C154-N1 anchors §4 (L239, untouched) |
| LCT | `d89595e8` #531 (Inspectable Evidence) | new §1.2 principle | **not cited** (grep-empty) | **DISJOINT by non-citation** |
| reputation-computation | `767eb564` #521 (Coercive/Extractive) | §4 rule category | cited at L415 (→ §4) | **DISJOINT** — adds a rule *category*; does not disturb the L241 "Law Oracles define reputation rules" sentence C154-N1 depends on |

Two further movers (`d1759397`, `6b66c949`) are **hub law/code**, not spec — DISJOINT to the spec surface. No corpus motion touched a normative mcp surface.

---

## §C — Routing

### Applied this turn
- **None.** No spec mutation. §7.8 is substantively sound; the one finding (N1) is a new-obligation recommendation, not an auditor-applicable citation fix.

### Cross-track / operator (do NOT self-resolve)
- **N1 (MEDIUM)** → author/operator: add one idempotency-on-redelivery clause to §7.8.2, keyed to `action_id`. Couples with the standing **B2+B6** r7-envelope bundle (which already owns `action_id` as the cross-layer key). This is the first *accountability* finding the mcp rotation has surfaced on a genuinely-new surface, not an inherited carry.
- **C188-N1** (mcp.py `ReputationEnvelope` divergence) → standing **B2+B6** SDK-track bundle, unchanged.
- All C188/C148 cross-track/design-Q carries STAND (§A.2): B5+B12, N5/N9/N13, N12, N15, F5/C62-B1, F9-inverted, B1-family.

### Confirmed-bounded (no action)
- **N2 (INFO)** — §7.8.1 L714 *"gated on receipt (§7.2)"*: §7.2 is "MCP Server Authority" (delegated-authority scope), which has no "receipt"/admission-gate concept. **Refuted as a defect** — the receiving server checking an inbound action against its §7.2 delegated-authority scope *upon receipt* is a coherent reading ("at receipt", not "§7.2 defines a receipt-gate"). A reader chasing the *reachability≠authority* point might expect §7.3 (R7 witnessing) or §7.8.2 (*"deliver only to that authenticated LCT"*); a one-word clarification would help, but the cite is defensible → INFO, not routed for action.
- B.5 corpus-delta (7 movers) — disjoint. §7.8 SDK-mirror GENUINE (hub-side) — recorded.
- Operator-gated flagships (B-D1/C-M1, D0) — untouched.

---

## Out of scope (handed off, not closed here)
- SDK reconciliation of the C188-N1 `ReputationEnvelope` divergences (SDK-alignment track; couples r7+mcp+SDK).
- Author/operator ratification of the N1 idempotency clause (new normative obligation — not auditor-applicable).
- §7.7 promotion to v0.1.0-final (operator/fleet-review gated).
- hestia deferred inbox (hestia #33) — external private repo, named by §7.8 but not inspectable from this worktree.
- Frozen cited siblings + the 7 corpus-delta movers — inspected only for disjointness, not re-audited on their own terms.

---

*Fifth delta re-audit — the first with real motion since C117. §A 8/8 HELD + C154-N1 remediation intact & anchor-stable (0 regression, +56 shift verified). §B: the net-new §7.8 mailbox is authored accountability-aware (RWOA+S+V = PASS) with one genuine under-specification (N1, MEDIUM — at-least-once + no idempotency clause permits double-completion of a deferred consequential action; routed to author/operator, NOT self-applied because it is a new obligation). SDK-mirror gate returns a GENUINE hub-side mirror for the mailbox slice (`f62c9e6`), narrowed to notices — the first §7.8-surface mirror, updating C188's "absent wire-layer" for this slice only. Corpus-delta disjoint; C188-N1 SDK divergence STANDS. See [[feedback_prior_finding_path_provenance]], [[feedback_prose_is_not_ledger]], [[feedback_refute_your_best_finding]], [[feedback_cross_doc_carry_inbound]].*
