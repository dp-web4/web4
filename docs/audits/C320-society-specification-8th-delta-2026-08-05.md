# C320 — Eighth-Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-08-05
**Auditor**: Legion autonomous web4 track (slot `web4-20260805-180032`, v2 protocol)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (498 lines, blob `2ad453ba`)
**Lineage**: C22 (first audit, #251) → C50 (1st delta, #317) → **C51 remediation** (`958a5625`/#318) → C92 (2nd) → C131 (3rd, first fully-clean) → C164 (4th) → **C202** (5th, `87377c38`/#522 §7.3 mover) → C240 (6th) → C280 (7th, #586 — added `hub/` to the mirror set) → **C320 (this, 8th)**
**Rotation**: fixed-order round-robin, `last-pass C# + 40` → C280 + 40 = C320. Paired remediation slot **C319 applied C318-N1** (five stale `mrh-tensors:246` anchors) and is committed ahead of this document.
**Staleness at audit**: **BYTE-FROZEN.** `git diff 5606485f HEAD -- <target>` is **EMPTY**; blob `2ad453ba` is byte-identical to C240's and C280's snapshots. Last touching commit `87377c38` (2026-07-14, the #522 §7.3 mover) — **22 days**.
**Window**: `087e5ab3..HEAD` — the commit that landed C280 → HEAD. **59 commits.**
**Method**: freeze-verification delta. **§A** freeze + §7.3 citation re-resolution at live sibling bytes. **§B** bounded net-new sweep, refute-by-default, ONE lens per candidate, mirror gate re-derived at live HEAD in **both** citation directions (v14) plus the frozen-target artifact sweep (v13). **§C** bidirectional carry re-verification with every anchor **re-resolved by content** (v18), counts re-run post-write at a different scope (v17), and **both** `docs/audits/` trees searched (v17).

---

## Verdict (summary)

- **§A — CLEAN.** Sixth consecutive delta in which the target's own bytes require no correction. Zero §7.3-cited siblings moved; all four citations re-resolve exact.
- **§B — the result is not on the spec side. It is the carry ledger.** **N1 (MED)**: this file's SDK-track carry bundle **lost four rows**. At C131 the bundle was explicitly `C50-B16 – B19` + C92-N1; from **C164** onward every pass has described it as `C92-N1, C164-N1, C22-M3, C92-N3/C50-B20`. **B16, B17, B18 and B19 have zero mentions across C164, C202, C240 and C280** — four consecutive passes — and they exist **nowhere else in the repository**. Three of the four are **verifiably still true at HEAD** against an SDK that has not moved since 2026-04-17. **N2 (INFO)**: the fourth, **C50-B17, was false the day it was written**, machine-verified against a byte-identical blob — and its underlying divergence is *inverted*. **N3 (LOW)**: §4.2.2's `All ledgers MUST support law-driven amendments` has **zero conformant implementers**.
- **§C — 7/7 carries OPEN**, all re-resolved by content. **I-1**: three of C280-N1's five cited sites went stale **within seven days** of being routed to the operator; re-resolved here.
- **Net: 0 autonomous spec edits. ZERO mutation.** C321 = declared NO-OP on the spec side.

**Honest scoping note, up front.** N1 is a **process** finding, not a spec defect. It reports nothing about `SOCIETY_SPECIFICATION.md`'s bytes, which are correct. Its severity comes from what the dropped rows *contain*, not from the drop being novel — and from the fact that the drop is silent by construction: a row that vanishes leaves no zero to count. Also stated plainly: the underlying facts in B16/B18/B19 are ~54 days old and predate four deltas of this file. They are net-new **as tracked items**, not as facts. Reporting them as fresh discoveries would be exactly the overclaim the snapshot-presence guard exists to prevent.

---

## §A — Freeze Verification + §7.3 Citation Re-Resolution

**Result: CLEAN.**

```
git rev-parse HEAD:web4-standard/core-spec/SOCIETY_SPECIFICATION.md → 2ad453ba…
git diff 5606485f HEAD -- <target>                                  → (empty)
git log -1 --date=short -- <target>  → 87377c38  2026-07-14  (#522, §7.3 mover)
```

The 498-line body is byte-identical to C240's and C280's snapshots, so C92's token-by-token verification of all 21 C51 findings and the `#`-regression sweep hold **by construction** — no new prose exists to regress.

§7.3 (`:472–495`), the only methodologically-live section, is itself byte-unchanged. Re-verification is therefore limited to §7.3-cited siblings that moved in the window:

```
git log --oneline --since=2026-07-28 -- reputation-computation.md hub-law-schema.md \
    society-roles.md inter-society-protocol.md web4-society-authority-law.md
→ (empty)
```

**Zero cited siblings moved.** Re-resolved anyway at live HEAD:

| §7.3 citation | Live ground truth (HEAD) | vs C280 | Verdict |
|---|---|---|---|
| `reputation-computation.md` §4 | `:239` `## 4. Reputation Rules` | `:239` | **EXACT, unmoved** |
| Coercive/Extractive Behavior Rules | `:339` `#### Coercive/Extractive Behavior Rules` | `:339` | **EXACT, unmoved** |
| `hub-law-schema.md` response vocabulary | `:285` `` `response` is one of `notice`, `quarantine`, `correct`, `rehabilitate`, `` | present | **EXACT** |
| `proposals/W4IP-DRAFT-2026-07-13-….md` (informative) | path resolves | present | **EXACT** |

**§A conclusion: no regression** on the target or its citation surface.

---

## §B — Net-New Sweep (bounded, refute-by-default, ONE lens per candidate)

### §B-0 — mirror set re-derived at live HEAD, in both citation directions (v14)

**Outward** — what implements this spec's subject matter:

1. **Python SDK** (`society.py` / `federation.py` / `role.py`) — blob-frozen since `759eaefa` (2026-04-17). **This is where N1/N2/N3 live.**
2. **web4-core** (`society.rs` / `ledger.rs`) — unchanged since C202. C202 §B-2's refutation stands.
3. **`web4-policy`** — gated at C240 as a **faithful** §7.3 implementer; unchanged (`cb788768`, 2026-07-15). Guard honored, **re-tested rather than assumed** (§B-5), **not re-flagged**.
4. **`hub/`** — in the mirror set since C280; **30 files moved in this window.** Gated in §B-4 and §C.

**Inbound** — what cites the target. Measured with a loose matcher over the whole tree:

```
grep -rlE 'SOCIETY_SPECIFICATION|SOCIETY_SPEC' .  (excl. .git, node_modules, hub/target)
→ 75 in docs/audits/ ; 9 in web4-standard/core-spec/ ; 2 in web4-standard/implementation/ ;
  2 in docs/reference/ ; 2 in archive/reference-implementations/ ; 1 each in
  web4-standard/{README.md, proposals/, test-vectors/}, web4-policy/src/, whitepaper/,
  review/, README.md, docs/{what,SPRINT.md,history}/
```

The inbound direction surfaced one artifact no prior pass in this lineage had gated: **`web4-standard/test-vectors/society/society-vectors.json`**, which declares `"spec": "web4-standard/core-spec/SOCIETY_SPECIFICATION.md"` — the standard's own test vectors *for this target*. **Refuted as a finding** (§B-5): it is consumed, by `test_society.py`'s `TestVectors` class, and C22-I3 already recorded its coverage gap.

### §B-1 — **N1 (MED) — this file's SDK-track carry bundle lost four rows at C164, and has carried the loss for four consecutive passes**

**What the bundle was.** C50 (2026-06-12) raised four cross-track findings and routed them as one bundle:

| id | C50 heading (`C50-…md:156`, `:160`, `:164`, `:168`) |
|---|---|
| **C50-B16** | SDK ledger-conformance: canonical MUST field-sets and amendment machinery unimplemented (3 raw findings consolidated) |
| **C50-B17** | §2.3 lifecycle vs SDK `_CITIZENSHIP_TRANSITIONS` |
| **C50-B18** | §3.1/§3.2.2 "societies are citizens of other societies" has no SDK surface |
| **C50-B19** | SDK `merge_law`/`effective_law` lets child law override parent with no conflict check |

C50 booked them (`:229`): *"**NEW cross-track from §B**: B16–B19 … join the SDK-track backlog."*
C92 carried them (`:100`): *"**C50-B16–B19** … — SDK-track, unchanged; **C92-N1 … joins this SDK-track bundle**."*
C92's own verdict line (`:128`) made them **half the file's stated open frontier**: *"The file's open frontier is entirely operator-DESIGN-Q (B13/B14/B15) and SDK-track (**B16–B19** + N1)."*
C131 carried them once more (`:74`): *"Routes to the SDK-track bundle (**joins C50-B16–B19**)."*

**What happened next — measured, not asserted.** Occurrence counts by `grep -oF <id> <doc> | wc -l`, one row per id, one column per subsequent pass in this lineage:

| id | C92 | C131 | C164 | C202 | C240 | C280 |
|---|---|---|---|---|---|---|
| C50-B16 | 1 | 1 | **0** | **0** | **0** | **0** |
| C50-B17 | 0 | 0 | **0** | **0** | **0** | **0** |
| C50-B18 | 0 | 0 | **0** | **0** | **0** | **0** |
| C50-B19 | 0 | 0 | **0** | **0** | **0** | **0** |

From C164 onward, every pass describes the SDK-track bundle as `C92-N1, C164-N1, C22-M3, C92-N3/C50-B20`. The four rows are simply not there. **No pass records a closure, a refutation, or a hand-off.**

**They exist nowhere else in the repository.** Searched **both** audit trees and every other tracked path. **Instrument stated exactly** (v17): the search ran at **203** files in `docs/audits/` and **2** in `web4-standard/docs/audits/`; re-running it after this document was written returns **204 / 2**, the extra file being C320 itself. The four results below are from the 203-file state:

```
grep -rlF 'C50-B16' .  → C50, C92, C131        (this lineage only)
grep -rlF 'C50-B17' .  → C50                   (one file)
grep -rlF 'C50-B18' .  → C50                   (one file)
grep -rlF 'C50-B19' .  → C50                   (one file)
```

**Three of the four are still true at HEAD.** The SDK has not moved since `759eaefa` (2026-04-17), *before* C50 was written, so "unchanged since C50" is a blob fact, not an inference. Each re-run at live HEAD rather than inherited:

| row | re-verification at HEAD | status |
|---|---|---|
| **B16(a)** — SDK never records §4.2.1's MUST minimum fields | `grep -rnoF` over `sdk/web4/`: `law_reference` **0**, `change_description` **0**, `voting_record` **0**, `effective_date` **0**, `recipient_lct` **0** — **0 of 5** present anywhere in the SDK | **PERSISTS** |
| **B16(b)** — §4.2.2 amendment wire-shape has no SDK counterpart; `amend()` not law-driven | `amendment_type` **0**, `law_authorization` **0**; `SocietyLedger.amend(self, original_id, amendment)` (`society.py:155`) takes **no** law reference | **PERSISTS** (and sharpened → **N3**) |
| **B17** — §2.3 lifecycle vs `_CITIZENSHIP_TRANSITIONS` | see **N2** | **REFUTED — born false** |
| **B18** — fractal tree disjoint from citizenship machinery | `incorporate_child` (`society.py:773–815`) appends a `LedgerEntry` to both ledgers and creates **no** `CitizenshipRecord` | **PERSISTS** |
| **B19** — `merge_law` has no contradiction check | `federation.py:389–403`: `merged_norms = list(child.norms) + [n for n in parent.norms if n.norm_id not in child_norm_ids]` — child overrides by id, no check against §3.2.1's *"can extend but not contradict"* | **PERSISTS** |

**Refutations attempted (refute-your-best-finding discipline) — four, three refuted, one sustained as a scope limit:**

- **R1 — "the rows were closed, not dropped."** **REFUTED.** No pass records a closure. C131's last mention routes them as *open*. And B16/B18/B19 are demonstrably still true at HEAD, so they cannot have been closed on the merits. A silent disappearance is not a disposition.
- **R2 — "SDK-track items don't belong in this file's §C."** **REFUTED.** C280's §C carries three SDK-track rows (C92-N1, C164-N1, C22-M3) explicitly. B16–B19 are the same class, routed by the same bundle, in the same lineage.
- **R3 — "they're tracked in the SDK lineage's own ledger; measuring only this file's lineage is a wrong-tree gate (v9/v17)."** **REFUTED, and this was the decisive check.** Both audit trees plus the whole repo were searched with `grep -rlF` on each literal id. B17, B18 and B19 appear in **exactly one file each — C50 itself.** There is no other ledger.
- **R4 — "the facts are ~54 days old, so this is not net-new (C98 snapshot-presence)."** **SUSTAINED**, and it caps the claim. B16/B18/B19 were true at C92, C131, C164, C202, C240 and C280. Nothing about the *code* is new. What is new is the measurement that the rows tracking them **stopped existing** — and that is net-new as of C164, discovered here. Severity is **MED** on the process, not on any single SDK gap.

**Why this is the finding and not a footnote.** C164's own verdict line advertises: *"**1 net-new class-a finding — a C92 cross-track item that was dropped from the carry ledger — restored here**."* C164 is also the pass at which B16–B19 vanish. It restored one dropped row while dropping four, and then certified the ledger. The failure mode is structural, not careless: **a dropped row leaves no zero to count.** v10 says a column of zeros is the finding; C318 sharpened it to *a carry folded into another carry loses its own row*. This is the third form — **a carry that is simply not re-typed leaves no trace at all**, and every subsequent pass inherits the shortened list as if it were the ledger.

**Disposition: routed. No spec change requested.** B16(a), B16(c), B18 and B19 return to the SDK-track bundle; B17 is closed as REFUTED by **N2**. The row-loss itself is a method finding for the rotation, recorded in §D.

### §B-2 — **N2 (INFO, instrument) — C50-B17 was false the day it was written, and its underlying divergence is inverted**

C50-B17 asserts (`C50-…md:162`):

> `federation.py:102–108`'s graph **cannot express** §2.3's Provisional→Active progression **or** direct Active→Termination.

Ground truth at `federation.py:102–108`:

```python
CitizenshipStatus.APPLIED:     frozenset({PROVISIONAL, ACTIVE}),
CitizenshipStatus.PROVISIONAL: frozenset({ACTIVE, TERMINATED}),   # ← Provisional→Active IS expressible
CitizenshipStatus.ACTIVE:      frozenset({SUSPENDED, TERMINATED}),# ← direct Active→Terminated IS expressible
CitizenshipStatus.SUSPENDED:   frozenset({ACTIVE, TERMINATED}),
CitizenshipStatus.TERMINATED:  frozenset(),
```

**Both clauses are false, and were false on 2026-06-12.** Machine-verified rather than argued:

```
git rev-parse HEAD:…/federation.py                            → 482a2148…
git rev-parse $(git rev-list -1 --before=2026-06-13 HEAD):…/federation.py → 482a2148…
```

Identical blobs. C50 read the file it cites, at the lines it cites, and recorded the opposite of what they say.

**And the direction is inverted (v12).** §2.3's ASCII diagram draws *no* Provisional→Active arrow, and routes Termination through Suspension. So the **spec's diagram** is the restrictive artifact and the **SDK's graph is a strict superset of it** — the reverse of B17's framing. There is nonetheless no live divergence to route: §2.3's own Note defers the diagram's branches to *"the §4.2.1 action-to-status mapping"*, and §4.2.1 maps `terminate` → Terminated without a predecessor constraint. **The normative text agrees with the SDK.** B17 is closed REFUTED, not reopened.

**Why an INFO rather than a shrug.** The row-loss in N1 did *not* correct this — it concealed it. Had any of C164/C202/C240/C280 re-verified the bundle, B17 would have been closed on its merits and the two true rows kept. Instead the same drop took all four indiscriminately, and the corpus lost B16/B18/B19 as the price of losing an error it never knew it had. *"A finding can have been false the day it was written"* ([[feedback_remediation_born_false]], v15) is here extended: **so can a carry — and an unreviewed carry ledger cannot tell the two apart.**

### §B-3 — **N3 (LOW, spec-vs-implementer; reach escalation on C50-B16(b), not net-new)**

§4.2.2 (`:351`) states a **MUST** on *all* ledgers:

> All ledgers MUST support law-driven amendments that: 1. Preserve Original Entry … 2. Record Amendment … 3. Maintain Provenance Chain

The corpus's two society ledger implementers:

| implementer | §4.2.2 support | evidence |
|---|---|---|
| **Python SDK** `SocietyLedger` | partial, and **not** law-driven | `amend(original_id, amendment)` — `society.py:155`, no law reference; `amendment_type` / `law_authorization` **0** hits SDK-wide |
| **hub** `Ledger` | **absent** | public API is `build_genesis` / `build_entry` / `build_entry_with_proposal_ref` / `verify_chain` (`ledger.rs:203,248,263,364`); `superseded_by` **0**, `amendment_type` **0**, `original_data` **0**, `supersede` **0** across `hub/hub-lib/src` + `hub/hub-daemon/src` |

**Zero conformant implementers of a MUST.** The hub is not short of amendment vocabulary — `grep -rIoiE 'amend[a-z_]*'` returns **153** over `hub/hub-lib/src` + `hub/hub-daemon/src`, and **194** over all of `hub/` excluding `target/` — but every one of them is a **law/charter** amendment (`LawAmended`, `amend_charter`, `amended_by` at `events.rs:184,282`): amending the *law*, not amending a *ledger entry*. Different act. The four tokens that would indicate §4.2.2 support return **0** at both scopes.

**The sharpening that makes this worth a row (net-new observation, not a new fact).** The SDK's implementation contradicts its own class docstring, ~50 lines apart in one file:

- `society.py:122` — *"**Append-only** society ledger per spec §4."*
- `society.py:169–177` — `amend()` does `self.entries[idx] = LedgerEntry(…, superseded_by=amendment.entry_id)` — it **replaces a recorded entry in place**.

§4.3 is titled *"Immutability with Corrections"* and its model is explicitly appended (`Block N` original, `Block N+1` amendment, `Block N+2` context). The SDK satisfies §4.2.2's *record shape* by violating §4.3's *immutability model*. It gets away with it because `SocietyLedger` has **no hash chain at all** (`sha256|hashlib|prev_hash|head_hash` → **0** hits in `society.py`); the hub, which does chain (`head_hash`, `verify_chain`), cannot do the same thing and does not try. **The one implementer that can satisfy §4.2.2 as written is the one with nothing to break.**

**Refutations — two, both partly sustained, and they hold this at LOW:**

- **R1 — "§4.2.2's block 1 is a *new appended record about* the original, not a mutation."** **PARTLY SUSTAINED.** That reading is available and would make §4.2.2 chain-compatible. But it is not stated, `entry_id: "original-123"` reads as the original's own id, and it is not how the corpus's only implementer read it. This is a **spec-clarity** question, which is why it routes rather than corrects.
- **R2 — "the hub is a hub, not a §4 society ledger."** **REFUTED** on C280's evidence, re-resolved by content at HEAD: `hub/docs/PRD.md:38` still gives the base-mandatory seven verbatim.
- **Severity discipline:** this is **LOW**, not MED. §4.2.2's amendment machinery is unexercised in both implementers — no caller invokes it in the SDK's ledger path, and the hub has no path at all — so nothing is currently *mis*-recorded. The defect is latent.

**Disposition: routed with C50-B16(b), which N1 restores.** No spec change requested — which of §4.2.2 or §4.3 governs on a chained ledger is a design call.

### §B-4 — window gate: 59 commits, `hub/` re-derived

The window is dominated by `hub/` (30 files: the public-release hardening, the public/operator plane split, the atomic-write sweep, the assurance-receipt v3 work). Gated against this file's subject matter — society lifecycle, citizenship, ledger classes, law, the base-mandatory seven:

- **`hub/hub-lib/src/ledger.rs`** (`63825674`, #607) — the four integrity checks gained tests. Read against §4.1/§4.2: no change to the recorded event classes; feeds **N3** above, no separate finding.
- **`hub/docs/PRD.md`** (`724bf8cf`, #627) — moved; `:38` re-resolved **by content**, holds exact (§C).
- **`hub/hub-lib/tests/fixtures/hub-law/`** (`5a1d9fa3`, #597) — **new in-repo copy** of the fleet-canonical law interop fixtures, vendored so a public repo's tests stop `include_str!`-ing a private one. → **I-2** below.
- **whitepaper logs, `docs/why/PURPOSE_IS_RELATIONAL.md`, `web4-trust-core` lockfile, `.github/workflows/vector-context-refs.yml`, `web4-standard/test-vectors/validate_context_refs.py`** — checked for claims over this file's subject matter; none restates or re-scopes it. No candidate. (`validate_context_refs.py` gates `@context` URIs; this target emits none — 9 fenced blocks, `grep -n "@context"` → 0.)
- **The two proposals (#579 `dictionary-as-context-mandatory-role.md`, #580 `resilience-to-incomplete-information.md`)** were already adjudicated at C280 as N3 and N2 and routed to CBP. **Not re-walked** (v-guard: adjudicated, not imported).

**I-2 (INFO, routed to the hub track) — the shared law interop fixtures have zero coverage of the response vocabulary §7.3 delegates to.** `hub/hub-lib/tests/fixtures/hub-law/README.md` states the fixtures exist so *"[b]oth sides assert against the same fixture content so divergence is caught early"* and names `full-featured.yaml` as *"Exercises all predicate types."* `grep -c 'responses:'` over all four fixtures returns **0, 0, 0, 0**. The hub *does* parse and validate response rules — `law.rs:483 hub_law_parses_response_rules_and_stays_inert` — but that test uses an **inline YAML literal**, which the other side cannot assert against by construction. So §2 rules 11–13 of `hub-law-schema.md`, including rule 13's **MUST NOT** on response selectors, are covered on one side only. This is the mechanism `SOCIETY_SPECIFICATION.md §7.3` — this target's *only* methodologically-live section, ratified 2026-07-14 — delegates its entire Correction & Enforcement semantics to. **Confidence split, stated honestly:** the fact (zero fixture coverage, one-sided assertion) is certain; whether it contradicts the README's "all predicate types" depends on whether a response rule counts as a predicate type, which is genuinely ambiguous. Routed as INFO on the fact, not the wording.

### §B-5 — REFUTED candidates (recorded so future deltas do not re-walk them)

- **"§7.3's ratified response vocabulary has no implementer."** **REFUTED.** `web4-policy/src/lib.rs` parses all nine verbs (`responses_parse_all_nine_verbs_including_kinetic`, `:862`), and **enforces §2 rule 13** — `if rule.selector.starts_with("r6.") || rule.selector == "r6"` → error *"deliberately disjoint"* (`:355`), with a negative test at `:928`. C240/C280's guard — `web4-policy` is a **faithful** §7.3 implementer — **re-tested at HEAD rather than assumed, and holds.** Not re-flagged.
- **"`society-vectors.json` is an unread orphan."** **REFUTED.** It is consumed by `test_society.py`'s `TestVectors` class (`:796`+), which loads it by path and asserts five of the six vectors field-by-field. Its *coverage* gap is C22-I3, already recorded. **The lesson C318 published applies verbatim: a coverage census is not a finding, and "0 of 8 passes read it" is a fact about the passes, not about the artifact.**
- **"`minimal_society` expects `phase: operational` with 2 founders and no roles, contradicting §1.2.5's seven base-mandatory roles."** **REFUTED by the spec's own meta-structure.** §1.2.5 `:62`: *"Conformance to the operational minimum is **not protocol-enforced**"*, and the SDK's `validate_minimum_viable` is *"a **voluntary** conformance check."* §5.1 `:408` names exactly this case — *"A minimal bootstrap society — the conceptual minimum of §1.2, distinct from … the operational minimum of §1.2.5."* The vector is conformant.
- **§4.2.1's "Every event uses the common envelope `{type, action, data, witnesses, timestamp}`" vs §4.2.2's three JSON records, which carry none of it at top level.** **RAISED AND WITHDRAWN.** The envelope sentence (`:263`) was added by the C51 remediation `958a5625` (2026-06-12) and *names* §4.2.2 — *"`witnesses` + `timestamp` carry the provenance that **§4.2.2's amendment machinery depends on**"* — while §4.2.2's blocks date to `ebfb3343` (2025-09-17) and were only partly harmonized by C50-B23. But block 3 (`amendment_context`) does carry `witnesses` and `ratified_timestamp`: the provenance §4.2.1 names **is** present, in a nested shape. This is a shape mismatch with no consequence, on a section with no live caller (§B-3), and C50-B23 already moved this ground once. **Not worth a row; recorded so the next delta does not re-raise it.**
- **`docs/why/PURPOSE_IS_RELATIONAL.md`, the whitepaper §11 package-matrix correction, the hub assurance-receipt v3 work, `#631`/`#630`/`#627`** — checked; none restates or re-scopes this file's subject matter. No candidate.

**§B conclusion: 0 autonomous spec edits; 1 MED (process/ledger) routed; 1 INFO instrument correction; 1 LOW spec-vs-implementer routed; 1 INFO routed to the hub track; 5 candidates refuted.**

---

## §C — Carry Re-Verification (bidirectional; every anchor re-resolved by content, v18)

**7/7 OPEN**, all re-resolved by content at live HEAD rather than inherited from C280:

| Carry | Anchor re-resolved at HEAD | Status |
|---|---|---|
| **C50-B13** Law Oracle name collision | target `:24` *"Codified rules governing entity behavior…"* ✓ ; `society-roles.md:71` `### 2.2 Law Oracle` ✓ | **OPEN, unmoved** — operator DESIGN-Q |
| **C50-B14** citizenship revocability vs SAL §5.1 | `web4-society-authority-law.md:180` `### 5.1 Citizen (Genesis, Immutable)` ✓ | **OPEN, unmoved** — operator DESIGN-Q |
| **C50-B15** law inheritance model | target `:178` *"Local laws can extend but not contradict inherited laws"* ✓ | **OPEN, unmoved** — operator DESIGN-Q |
| **C92-N1** solo-founder guard (half-closed) | `society.py:317–318` `if len(founders) < 2: raise` **still live**; `role.py:303–305` docstring still claims the gap resolved | **OPEN, unmoved** — SDK-track |
| **C164-N1** enum-comment stale vocab | `society.py:92` `# join/leave/suspend/reinstate`, `:94` `# allocate/deposit/reclaim` — still pre-C51 | **OPEN, unmoved** — SDK-track |
| **C22-M3** `type` ↔ `event_type` | `society.py:111` `event_type: LedgerEventType` | **OPEN, unmoved** — SDK-track |
| **C92-N3 / C50-B20** id-scheme example strings | frozen body, present | **OPEN** — C33 id-scheme bundle |

**Restored this delta (§B-1):** **C50-B16(a)**, **C50-B16(c)**, **C50-B18**, **C50-B19** → SDK-track bundle. **C50-B17** → closed **REFUTED** (§B-2). The SDK-track bundle is therefore `C92-N1, C164-N1, C22-M3, C92-N3/C50-B20, C50-B16(a), C50-B16(c), C50-B18, C50-B19` — **eight rows, not four.**

### I-1 (instrument) — three of C280-N1's five cited sites went stale within seven days

C280-N1 is routed to the operator as a DESIGN-Q, and its load-bearing claim ("these are the same act") is evidenced by five citations. The hub moved 30 files in the seven days since. Re-resolved by content:

| C280-N1 citation | at HEAD | drift |
|---|---|---|
| `hub/hub-lib/src/events.rs:119` `MemberJoinResolved` | `:119` | **exact** |
| `hub/hub-lib/src/state.rs:344–346` `JoinStatus::Denied` | enum at `:340`, `Denied,` at `:346` | in range ✓ |
| `hub/hub-lib/src/state.rs:604–609` projection | `jr.status = if *approved {…} else { Denied }` at `:609` | in range ✓ |
| `hub/docs/PAIRED-CHANNELS.md:338` *"caller is `sovereign` / `citizen` (member)"* | `:338` | **exact** |
| `hub/docs/PRD.md:38` base-mandatory seven | `:38` | **exact** (file moved, line held) |
| `hub/README.md:264` *"An external entity calls `request_citizenship`…"* | **`:286`** | **+22, STALE** |
| `hub/hub-lib/src/law.rs:1183–1190` *"Citizenship is not open-admission"* | **`:1283–1286`** (`member_join_request` at `:1283`) | **+100, STALE** |
| `hub/hub-daemon/src/rest.rs:2658` *"the external→citizen bootstrap"* | **`:3105`** | **+447, STALE** |

**Three of eight anchors stale in seven days**, on a finding that has not yet reached an operator. Corrected here so the memo resolves when it is read. This is C318's v18 turned inward on the rotation's own output: **a routed finding's evidence decays at the rate of the tree it cites, not at the rate of the audit that wrote it** — and `hub/` is the fastest-moving tree in the corpus.

**Inbound (bidirectional) check:** no sibling audit doc in the window routed a carry back to this target. C284 (society-metabolic-states) and C286 (society-authority-law) were re-read; neither routes here.

---

## §D — Disposition

- **Spec side: NO ACTION. ZERO mutation.** Target byte-frozen 22 days; no autonomous edit is warranted or authorized. The file sits under an unanswered operator DESIGN-Q bundle.
- **N1 → the rotation + the SDK track.** Restore **C50-B16(a)**, **C50-B16(c)**, **C50-B18**, **C50-B19** to the SDK-track bundle; carry them by id in every subsequent §C of this file. Close **C50-B17** as REFUTED per N2.
- **N2 → recorded, closed.** No further action; the correction is the deliverable.
- **N3 → operator, LOW, adjudicate with C50-B16(b).** The question to put: *on a hash-chained ledger, does §4.2.2's "Preserve Original Entry" record mutate the original or append a record about it?* Whichever way it resolves, either §4.2.2/§4.3 moves or `society.py`'s "Append-only" docstring does — not autonomously.
- **I-1 → applied here** (C280-N1's three stale anchors re-resolved by content). C280 is **not** rewritten (v11); the correction is published in this document.
- **I-2 → hub track**, INFO: no fixture in the shared law interop set carries a `responses:` key.
- **Operator DESIGN-Q bundle (unchanged):** C50-B13, C50-B14, C50-B15, plus **C280-N1** (adjudicate WITH B-D1) and now **N3**.
- **Guards carried forward:** `web4-policy` remains a **faithful** §7.3 implementer (re-tested at HEAD this pass — do NOT re-flag). The `95683868` hardening wave remains a **FALSE MIRROR** for this target. C280's two REFUTED candidates (admission-law theater; the t3v3 ontology reach) stay closed. C232-N1 does not intersect §7.3.
- **No review-gate block is owed for C320.** This audit proposes no diff to any surface; its deliverable is one document. (C319, the paired remediation, carries its own justification in its commit message: five documentation citation tokens, no surface, no consequential act.)
- **C321 = declared NO-OP on the spec side.** Next SOCIETY_SPEC delta ≈ C360.

### Post-write re-run: three of this pass's own cells corrected (v17, working as designed)

Every count above was re-run after the document was written, at a **different scope** than it was drafted with. Three cells did not survive, and are corrected in place rather than quietly adjusted:

1. **`docs/audits/` file count** was drafted as **203**. Re-run post-write it is **204** — because this document is now in it. Both numbers are published in §B-1, with the search state named, because the R3 result depends on which of the two the reader assumes. A file count taken before you add a file to the directory is a fact with an expiry date.
2. **The hub's `amend*` occurrence count** was drafted as **153**, measured over `hub/hub-lib/src` + `hub/hub-daemon/src`. Re-run over all of `hub/` (excluding `target/`) it is **194**. The *finding* is unaffected — all four §4.2.2 tokens are 0 at both scopes — but a bare "153" implied a repo-wide census it was not. Scope now published with the number.
3. **The C50 heading citation** was drafted as a range, `C50-…md:160–170`. `:160` is **B17's** heading; B16 begins at **:156**. The range silently excluded the row the finding leads with. Replaced with the four exact heading lines (`:156`, `:160`, `:164`, `:168`).

None of the three changes a verdict. All three are published because a document whose central finding is *"a row disappeared and nobody noticed"* has no standing to file its own instrument errors quietly.

### Method lesson (carry forward to EVERY delta)

**Proposed method carry v19 — measure the ledger's *row set*, not its rows.**

Every guard this rotation has built measures a carry that is *present*: re-resolve its anchor (v11, v18), re-derive its direction (v12), re-run its grep at live HEAD (path-provenance), count its zeros (v10). All of them take the ledger's row set as given. **C50-B17, B18 and B19 were never re-verified by anything, because after C131 there was nothing to re-verify — the rows had stopped being typed.** A dropped row leaves no anchor to re-resolve, no zero to count, and no name to grep. It is invisible to every instrument the lineage owns.

The operative form: **at each delta, reconstruct the carry set from the lineage's *earliest* full ledger and diff it against the current one; every id that appears in an older pass and not in the newer must show a recorded disposition, or it is a finding.** C318 reached the adjacent case — a carry *folded into* another carry loses its own row — from the same lineage-oldest-ledger direction. This is the more basic form: a carry that is simply **not re-typed** loses its row with no fold, no note, and no successor.

Two sharpenings this pass earned:

1. **The drop is not random with respect to truth.** It took one false row (B17) and three true ones. An unreviewed ledger has no way to prefer the error — so the expected effect of silent attrition is to lose correct findings at the base rate and keep incorrect ones at the same rate. Attrition does not clean a ledger; it thins it.
2. **The pass that dropped them is the pass that advertised catching a drop.** C164's verdict line reads *"1 net-new class-a finding — a C92 cross-track item that was dropped from the carry ledger — restored here."* Finding one instance of a defect class is not coverage of it, and the discipline of restoring a row does not transfer to the rows you did not think to look for. The generalization is uncomfortable and worth stating: **a pass is most likely to drop a row in the same delta in which it congratulates itself for restoring one**, because the restoration consumes the attention the sweep needed.

*Method references: [[feedback_prose_is_not_ledger]] (§B-1 — the bundle lived in prose at C92/C131 and never had its own §C rows), [[feedback_ledger_emptied_not_closed]] (§B-1 — the shortened list read as a clean ledger), [[feedback_census_is_not_a_resolution]] (§C I-1, v18 turned inward on the rotation's own routed output), [[feedback_remediation_born_false]] (§B-2 — extended from remediation notes to carries), [[feedback_carry_direction_not_presence]] (§B-2 — B17's divergence is inverted), [[feedback_two_audits_trees]] (§B-1 R3 — both trees searched, 203 + 2 files), [[feedback_refute_your_best_finding]] (§B-1 R1–R4, one sustained as a scope limit), [[feedback_read_the_specs_meta_structure]] (§B-5 — §1.2.5's own "not protocol-enforced" clause refutes the vector charge), [[feedback_publish_the_instrument]] (every count above carries its grep and scope).*

---

*C320 verdict: `SOCIETY_SPECIFICATION.md` is byte-frozen and correct — the sixth consecutive delta requiring zero spec-side mutation, and the eighth pass overall. §A holds by construction on an unmoved blob with four exact citations and zero moved siblings. The result is not on the spec side at all: this file's SDK-track carry bundle **lost four rows at C164** and has carried the loss through C202, C240 and C280 — measured at 0 occurrences per pass, present nowhere else in either audit tree, with three of the four still verifiably true at HEAD against an SDK frozen since before C50 was written. The fourth, C50-B17, turns out to have been **false the day it was written** — machine-verified against a byte-identical blob — with its divergence inverted; the row-loss concealed the error rather than correcting it, and took three true rows as the price. §4.2.2's `All ledgers MUST` is found to have **zero conformant implementers**, the SDK satisfying its record shape only by mutating a ledger it calls append-only, on the one implementation with no hash chain to break. Three of C280-N1's own citations went stale within seven days of being routed and are re-resolved here. Zero mutation; C321 = no-op.*
