# Operator memo — the C-series audit cadence

**Date**: 2026-08-06
**From**: Legion web4 track, session `legion-web4-20260806-120032` (audit slot C324)
**Decision requested from**: dp
**Status**: **awaiting operator decision — the track will NOT self-apply either branch**

---

## Why this is a separate file

The cadence question has been recorded in **nine consecutive audit passes** and has produced no decision in any of them. The policy review for this session ruled that escalating it as a tenth line inside a tenth audit document was not an option, for a structural reason this same session then documented independently: **a line in an audit doc is not a decision request.** So it is filed here, once, with the measured case attached.

This memo asks for one decision. It proposes no change and applies none.

---

## The cadence as it stands

The C-series rotation audits one frozen spec file per fire, choosing the slot arithmetically as **that file's last-pass C-number + 40**. Eighteen files are in rotation. The interval is fixed and is indifferent to whether the file has changed.

## The measured case, from this slot

`web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md`, audited today as C324 — the 8th delta:

| Measure | Value |
|---|---|
| Audit documents in the lineage | **8** (C21, C54, C96, C133, C168, C206, C244, C284) + this one |
| Target blob | `5e3f7203`, unchanged since 2026-06-14 — **53 days, 8 consecutive frozen windows** |
| Consecutive passes returning **0 net-new against the spec** | **8** (C96 through C324) |
| Commits in this window touching the spec, the SDK mirror, the crate, the vectors or the ontology | **0** (42-commit window from `1acf7bd2`; the 3 lexicon hits are prose in three other trees) |
| Tracked mirror artifacts byte-identical to the previous pass | **8 of 8** |

On the file itself, the last useful pass was C54, in June.

## What the passes *did* find, once they stopped looking at the file

| Pass | Yield |
|---|---|
| C284 | a 979-line implementation nobody had read, which confirmed a 61-day-old spec ambiguity; a reach-escalation on a mis-cited enum now shipped across two published WASM faces |
| C320 (society-spec) | **4 carry rows** stopped being typed at C164 and were never dispositioned; 3 still true |
| C322 (dictionary) | **9 carry rows** dropped; 4 machine-readable artifacts the spec never cites, unexamined for 8 passes |
| **C324 (this pass)** | **5 carry rows** (`C54-B5…B9`) stopped being typed at C284; **all 5 re-verified true** against the byte-frozen spec |

**Three lineages reconstructed, three lineages lost rows — 18 in total.** None of these findings came from re-reading the spec. All came from auditing the *record*.

## The finding that makes this decision-relevant now

C324's mechanism is documented in the previous pass's own section header. C284's carry ledger is titled *"§C — Carries reconciliation (**collapsed to one table, per policy review**)"* and opens *"Carry-by-carry re-narration would be the same padding §A avoids."* The collapse was correct — a 7th consecutive re-narration of a frozen blob would have been worthless — but the `Design-Q (14)` count, which five prior passes had published verbatim and which made the row set self-checking, was removed in the same edit. Nine rows then appeared under a header that no longer said fourteen.

**The remedy for padding is the row-dropping mechanism.** That is not an argument for padding; it is an argument that the cadence is currently pointed at the wrong artifact. The spec is not decaying. The ledger is.

---

## The decision

Both branches were prepared before the row-set result was known, so that the result could not be fitted to a preferred answer. As it happens the result landed positive, which selects branch A — but branch B is recorded as it was written.

### Branch A — the row-set result was positive (this is the live branch)

**Retarget the cadence from the file to the ledger.** Concretely:

1. Keep the 40-slot rotation, but make the *spec re-read* conditional on the blob having moved. When the blob is frozen, §A is two lines (it already is, under this session's policy review).
2. Make the **row-set reconstruction the mandatory spine** of every delta, not an optional method carry. It is three for three across lineages.
3. Adopt the cheap structural fix this pass proposes: **a ledger may collapse its narration, but must publish its row count, and any pass that reduces the row count must name the disposition of every row it drops.** This costs one number per document and would have prevented all three drops.
4. Consider whether the fifteen lineages not yet reconstructed should get a one-time row-set sweep rather than waiting ~40 slots each. At three-for-three, the expected yield is on the order of 5–9 rows per lineage.

**Cost**: roughly unchanged per pass; the reconstruction replaces the spec re-read rather than adding to it.

### Branch B — had the row-set result been negative

Eight passes on a file frozen 53 days would have produced nothing at all, and the honest conclusion would have been to **lengthen the interval or make it event-triggered on blob change**, with a floor (e.g. re-audit on blob change, or every 120 slots, whichever comes first) so a file cannot fall out of rotation entirely.

### Branch C — do nothing

Also a legitimate answer. The rotation is cheap and it is currently the only thing that reads these files at all. If the answer is C, please say so explicitly, so the track can stop re-raising it: **nine passes of unanswered escalation cost more than one recorded "no".**

---

## Related, and deliberately not bundled

- `docs/SPRINT.md` exists, was last updated 2026-05-19, and names the MetabolicState operator decision. C168 recorded the same item in its §D. **It is recorded in two places and executed in neither** — the same failure mode as this memo, one layer down.
- The C168-N1 enum rename (`web4-core/src/society.rs` `MetabolicState{Genesis, Bootstrap, Operational, Dormant, Sunset}` mis-citing the 8-state spec) is a **breaking change across two published WASM faces and a committed `.d.ts`**, and is getting monotonically more expensive. It is operator-gated and the track will not self-apply it. It is a *different* decision from this one and is not bundled here.
- The flagship **B-D1** SSOT-inversion question remains unanswered and is likewise not bundled.

---

*Filed under Autonomous Session Protocol v2. The policy reviewer for this session made this artifact a required deliverable and specified that both branches be presented with neither self-applied. Evidence and instruments: `C324-society-metabolic-states-8th-delta-2026-08-06.md` §B, §F, §G.*
