# C440 — SOCIETY_SPECIFICATION.md 11th delta audit

**Date**: 2026-08-26 · **Slot**: `web4-20260826-000032` · **Prior pass**: C400 (PR #721, merged `109df97a`)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` — blob `2ad453ba`, 498 lines,
byte-frozen since `87377c38` (2026-07-14). **Zero mutation this pass.**

> **Retry note.** The 2026-08-25 18:00 fire (PR #783) was blocked by a hestia pre-tool-use hook
> with an **empty** MRH grant set; C440 went unserved and memory instructed a retry without
> advancing the rotation. This session's grant set is populated (worktree, workspace repo,
> private-context all granted); one relative-path command was denied and absolute paths were used
> throughout. No circumvention.

**Pre-registration (v26).** Window span `109df97a..8a0ef6e7` (HEAD at open). Root: repo. Filetypes:
all. Standing path-bind on every `git log -S` probe: `-- . ':!docs/audits'`. Enumeration rule
(inclusive): this lineage's docs = `C{50,92,131,164,202,240,280,320,360,400}-society-specification*`
plus the non-C-numbered founding member the standing rule predicts; the bundle-citation sweep below
uses literal-id greps over **both** audit trees (`docs/audits/`, `web4-standard/docs/audits/`).

| measurement | command | result |
|---|---|---|
| window commits | `git rev-list --count 109df97a..HEAD` | **59** |
| … in `web4-standard/` | `git log --oneline 109df97a..HEAD -- web4-standard/ \| wc -l` | **1** (`2462881f`, interface-planes canon, #727) |
| … on target | `git log --oneline 109df97a..HEAD -- <target>` | **0** |
| … in SDK | `git rev-list --count 109df97a..HEAD -- web4-standard/implementation/sdk/` | **0** (frozen at `62524cf8`, 2026-05-24) |
| … in `web4-policy/` | `git rev-list --count 109df97a..HEAD -- web4-policy/` | **0** (last mover `1fa86e09`, 2026-07-27) |
| … in `hub/` | `git rev-list --count 109df97a..HEAD -- hub/` | **27** |

---

## §A — Movement check (per the C400 guard: do NOT re-run §A in full)

C400 established that C360's 37/37 cross-reference resolution holds **by blob identity** when the
target and its tracked siblings are unmoved. Re-applied: all **10 of 10** tracked files have **0**
commits in-window (`git rev-list --count 109df97a..HEAD -- <file>` per file; hashes via
`git hash-object`):

| file | window commits | blob (8) |
|---|---|---|
| target (`SOCIETY_SPECIFICATION.md`) | 0 | `2ad453ba` |
| `web4-society-authority-law.md` | 0 | `0849ebbe` |
| `society-roles.md` | 0 | `886942a2` |
| `atp-adp-cycle.md` | 0 | `2d060579` |
| `mcp-protocol.md` | 0 | `4491c1bb` |
| `reputation-computation.md` | 0 | `bfdac3ba` |
| `hub-law-schema.md` | 0 | — |
| `t3-v3-tensors.md` | 0 | — |
| `SOCIETY_METABOLIC_STATES.md` | 0 | `5e3f7203` |
| `inter-society-protocol.md` | 0 | `22bf6c1d` |
| `did-web4-method.md` | 0 | `0d2e4c53` |

**§A verdict: NEGATIVE by movement — C360's 37/37 holds by blob identity.** (11 rows shown because
hub-law-schema and t3-v3 are counted inside the 7-moved-sibling set; the tracked set is the C400
one, unchanged.)

---

## §B — The window: one normative event, examined from this lineage's side

### B.1 — `interface-planes.md` (#727, `2462881f`, dp-directed, **Status: proposed**)

The only in-window `web4-standard/` commit adds `core-spec/interface-planes.md` (+ GLOSSARY and
README registration). Its §9 "Relationship to other specifications" **names the target**:

> `SOCIETY_SPECIFICATION.md`, `inter-society-protocol.md` — a federation edge is a member-exposure
> surface between societies; what crosses it is classified by plane like any other surface. (`:195-196`)

**Pre-registered hazard resolved as a NEGATIVE (record per C434's instruction).** C424 (mcp), C432
§C.5 (reputation) and C434 §C.4 (acp) filed B-D1-corroborating datapoints 1–3 on this file, each
with the predicate *"the clause has no inbound path — the sibling is absent from §9 / never named."*
C434 pre-registered that a **fourth** datapoint makes the routing failure itself the finding. **That
predicate does not fire from this locus: `SOCIETY_SPECIFICATION.md` IS named in §9** (`grep -n
"SOCIETY_SPECIFICATION" web4-standard/core-spec/interface-planes.md` → `:195`). The datapoint
counter stays at **3**. C440-N1 below is a **different predicate** (expressiveness, inside a named
relationship) and is explicitly NOT filed as a datapoint.

### B.2 — `hub/` (27 commits): admission-domain motion, no carry discharged

`7b37cb6d` (#781, dp-authored, 2026-08-24) makes both public admission surfaces **Escalate to the
witnessed MemberJoinRequested queue when no law is loaded** ("Absence of law removes admission
authority without discarding the applicant"). Checked against this lineage's ledger: **C280-N1**'s
predicate (target §2.3 `:130` "Rejection is a non-record outcome" vs hub's `Denied` record
vocabulary) is untouched — the change governs the absent-law path, not rejection records. Both
C280-N1 constructs re-resolved **live at HEAD by name** (v22; hub anchors moved again):
`MemberJoinResolved` now `events.rs:152` (was `:119` at C280), `JoinStatus::Denied` projection now
`state.rs:727` (was `:344-346`, then `:355` at C360's I-2). **Row STANDS, operator-owned, cite by
construct name only.** No other window commit touches a carried construct
(opening-sequence step 4: receivers' ledgers probed, not their spec files; SDK 0 commits ⇒ no SDK
bundle row can have been discharged).

---

## §C — Findings

| id | severity | class | route |
|---|---|---|---|
| **N1** | **LOW**, modality-capped | v81: ratification without propagation — expressiveness gap | standard editor (interface-planes) + operator — **do not self-apply** |
| **N2** | **INFO-LOW**, process | root cause of C400-N2, one pass earlier (d6 yield) | this ledger |

### C.1 — N1 (LOW): the proposed exposure enum cannot express §4.1's witness-scoped ledger access, and §9's reconciliation bullet reaches only the federation edge

`interface-planes.md` §2.2: *"Every surface **MUST** declare exactly one exposure class"* over the
closed set `{public, member, operator, internal}`, where **member** = *"admitted members of the
society"*; §8.1 conditions conformance on *every* externally reachable surface being documented
with its (plane, exposure) pair. Its §2.1 plane **D** is *"the hash-chained record and its
projections"*, and its own §6 worked table classifies *"historical and attribution queries"* as a
surface.

The target's §4.1 is the standard's only pre-existing exposure-adjacent vocabulary for exactly
those surfaces, and it predates the canon by the full life of the file
(`git log -S "citizens_plus_witnesses" -- . ':!docs/audits'` → born `ebfb3343`, "Add Society as
foundational Web4 concept"). Testing **every** member of the block (v76/v82 — not just the failing
one):

| §4.1 class | `access` value | expressible as one §2.2 exposure? |
|---|---|---|
| 4.1.1 Confined | `citizens_only` | **yes** — `member` |
| 4.1.2 Witnessed | `citizens_plus_witnesses` | **NO** — an external witness is definitionally not an *admitted member* (that non-membership is what distinguishes 4.1.2 from 4.1.1); not `operator`; not `internal`; `public` contradicts 4.1.2's own `"visibility": "restricted"` |
| 4.1.3 Participatory | `via_parent_society` | **yes, derivatively** — the records ride the parent's ledger, whose surfaces carry their own exposures; no new surface is created |

So a future implementation conforming to **both** documents cannot express a witnessed ledger's
witness-facing query/validation surface **as one exposure class under the natural
restricted-channel binding**: §2.2 offers no class for a named non-member party, and the §9 bullet
that names this file reconciles only the federation edge, not §4.1. This is the v81 shape — the
finding is the artifact the ratification did **not** reach. (Adversarial review weakened the first
draft's "cannot document" — §5's own exposure≠authorization doctrine (`:119-122`) permits an
escape route: outbound push of entries plus a (D, public) attestation-intake surface authorized by
witness signature. The single-class expressiveness gap stands; the deadlock is escapable by
rebinding, and that route is added to the fork as option (d).)

**Severity honestly capped at LOW, three independent caps:** (1) `interface-planes.md` line 3 is
**`Status: proposed`** — the same modality cap C434-N2 took; (2) the §4.1 `access` vocabulary has
**zero implementers** (`git grep -ln "citizens_only\|via_parent_society" -- . ':!docs/audits'
':!web4-standard/docs/audits'` → **1 file, the target**; corroborates C400-d1's completed-negative —
hub's `LedgerEntry` has no class field), so nothing sits on the wrong side today; (3) both artifacts
are spec-side, no executable path. **Novelty matcher published (v44):**
`citizens_plus_witnesses` = 1 hit corpus-wide (the target); `"exposure class"` in both audit trees =
C432 + C434 only, both at different loci (the reputation-delta classification clause and the §9
absence respectively). **What is NOT charged:** "§4.1 is unimplemented" (C400-d1 closed that — no
document claims the coverage); the canon's motivation claim `:15-17` (*"missing from canon"* refers
to the general plane vocabulary, which §4.1 is not — the claim survives as written).

**Fork for the owner (report, not resolve; #727 is operator-attested):** (a) add a witness-scoped
exposure class or an explicit extension mechanism to §2.2; (b) widen §2.2's `member` definition to
cover parties in a standing witnessed relationship (costs the *"admitted members"* wording); (c)
declare ledger `access` a distinct axis from exposure — which then owes the GLOSSARY's new
*"Exposure class: who may reach a surface"* entry a disambiguation note; (d) ratify the
rebinding reading — witnessed ledgers publish outbound + take attestations on a (D, public)
intake gated by witness signature per §5 — and say so in the §9 bullet, since nothing in either
document currently states it. When interface-planes leaves `proposed`, cap (1) lapses and this
should be re-rated.

### C.2 — N2 (INFO-LOW, process): the C400-N2 collision's enabling condition is one pass earlier — C320 restored B16(c) by disposition-line only, with no evidence cell

Deferral row **d6** ("audit the other sub-row labels for the same collision") served in full.
Method: each label's originating predicate taken from `C50:156-175` verbatim, compared against
every later citation in **both** audit trees (`grep -rlF` per literal id; this lineage's citing set
= C50, C92, C131, C320, C360, C400 — bare `B1x` hits in other lineages' docs are their own rows,
the known C54-B14-class collision, excluded by the lineage-scoped id forms).

| label | C50 predicate (abbrev.) | citation record | verdict |
|---|---|---|---|
| B16(a) | SDK never records §4.2.1 MUST min fields (5 tokens) | C320`:121` ✓, C360`:447` ✓, C360`:205` R2 ✓ | **CLEAN** |
| B16(b)/(c) | (b) §4.2.2 wire-shape / (c) `create_society` bypasses 3 MUST-record categories | C360`:448` filed (b)'s content under (c)'s id — **known, = C400-N2** | see root cause below |
| B17 | §2.3 lifecycle vs `_CITIZENSHIP_TRANSITIONS` | REFUTED born-false at C320-N2; consistently cited as refuted since | **CLEAN** |
| B18 | fractal tree ⟂ citizenship machinery | C320`:123` ✓, C360`:449` ✓; C400-N1 widening carries a written v37 disposition (`C400:244`) | **CLEAN** |
| B19 | `merge_law` no contradiction check | C320`:124` ✓ (construct identical, range narrowed `:389-403` ⊂ C50's `:389-416`), C360`:450` ✓ | **CLEAN** |
| B20 | id examples → C33 bundle | compound `C92-N3/C50-B20` is a **declared identity at birth** (`C92:101` "re-confirmed present as §B C92-N3", `C92:113` "(= C50-B20)") | **CLEAN** |

**The increment:** C320's §B-1 table (`:121-125`) holds evidence rows for **(a), (b), B17, B18,
B19 — and no (c) row** — while its disposition line (`:136`) restores *"B16(a), **B16(c)**, B18 and
B19"* to the SDK bundle. Sub-row (c) re-entered the ledger **by name only, with no predicate or
evidence cell of its own**. A name-only row is exactly what invites a successor building the next
§C table to fill it with the nearest sibling's content — which is what C360`:448` then did. This
does not re-open C400-N2 (its per-arm disposition stands, arm 3 holds the row at MED); it locates
the mechanism one pass earlier and sharpens the rule: **a restoration is a disposition, and a
disposition must carry its predicate (v65's mechanism + v24's members rule applied to
restorations).** Five of six labels clean; the ledger's collision was a single event with a single
enabling condition, not a class in active recurrence.

---

## §D — Deferral row d2 served: `web4-policy` §7.3 faithfulness, re-executed

Last executed test was ≥3 passes old (deferred at C360 and C400). The crate is unmoved in-window
(0 commits; last mover `1fa86e09` 2026-07-27) but the test was **re-executed, not inherited**:

| cell | command | result |
|---|---|---|
| vocabulary | read `web4-policy/src/lib.rs:157-189` | 9-verb `Response` enum = §7.3's `notice/quarantine/correct/rehabilitate` + kinetic `slash/suspend/revoke/terminate/halt`, exact |
| kinetic split | `is_kinetic` (`:197-205`) + test `:889-895` | 5 kinetic / 4 ladder, matches §7.3's class boundary |
| parse-don't-enact | `awk 'NR>=607 && NR<=700' src/lib.rs \| grep -c responses` | **0** — `evaluate` (`:607`) and `evaluate_outcome` (`:618`) bodies never read `responses`; kinetic verbs parse (`:862` validator test) but remain law-inert, as §7.3's *"kinetic verbs parse but remain law-inert until individually ratified"* requires |
| suite | `cargo test --quiet` | **10 passed / 0 failed** |

**d2 verdict: web4-policy remains a FAITHFUL §7.3 implementer. Row CLOSED for this cycle**
(re-opens on any `web4-policy/` commit — event trigger, not cadence).

---

## §E — Carry ledger, binary re-verification (v10 rule 5: cite the owning pass, no re-argument)

Target blob-frozen + SDK blob-frozen (0 window commits each) ⇒ every row anchored in those trees
holds **by blob identity**. Enumerated, not waved at:

- **Operator DESIGN-Q:** C50-B13, C50-B14, C50-B15 — target + SAL + society-roles unmoved ⇒ HOLD.
- **SDK bundle (twelve rows, C400's set):** C92-N1, C164-N1, C22-M3, C92-N3/C50-B20, C50-B16(a),
  C50-B16(b) (w/ C320-N3, operator), C50-B16(c) (MED on arm 3), C50-B18 (+C400-N1 widening),
  C50-B19, C320-N3, C360-N1, C360-N2/N2b — SDK frozen at `62524cf8` ⇒ ALL HOLD.
- **C280-N1** (operator, adjudicate with B-D1): constructs re-resolved live by name (§B.2). HOLD.
- **Received rows (C360-N3, carried forever):** C54-B14 (anchor `SOCIETY_SPECIFICATION.md:89`,
  metabolic lineage) and SAL `L1-residual` — anchors frozen ⇒ carried, not re-derived (C404 did the
  same at its `:380`).
- **Inbound sweep (v36, run first):** `grep -rln "SOCIETY_SPECIFICATION" docs/audits/
  web4-standard/docs/audits/` restricted to docs postdating C400 → C404, C410, C434. All three use
  the target as **evidence or anchor** (C404 B14 anchor row; C410 `:62` prior-art quote; C434 §9
  enumeration). **Zero rows addressed to this lineage. Negative recorded.**
- **No carry discharged by anyone else** (step 4): SDK 0 commits; hub motion examined in §B.2.

**Do-not-re-open list honoured in full** (C400 guard): d1 completed-negative; the killed
`recipient_lct`/`entity_lct` fork; the "vectors pin non-conformance" claim; C320-refuted B17;
the C284-R1 note; the 0-of-7 witness-gating idiom (C404 I-2's class routing).

---

## §F — Deferral ledger for C480 (next SOCIETY_SPEC delta)

1. **d7 (event-triggered):** `interface-planes.md` is `Status: proposed`. If it ratifies, N1's cap
   (1) lapses — re-rate N1 and check whether the ratification edit stated the §4.1 mapping.
2. **d8 (event-triggered):** if `hub/` grows a ledger-class field or any artifact starts consuming
   `citizens_only`/`citizens_plus_witnesses`/`via_parent_society`, both C400-d1's
   completed-negative and N1's cap (2) need re-derivation.
3. **d2 re-arm rule:** re-run §D only on a `web4-policy/` commit.
4. d4 remains the metabolic lineage's (C404 handled the vectors file; unchanged).

## §G — Method note

Post-write re-run at a different scope/tool (v17 amended): window count re-derived via
`git log --oneline 109df97a..HEAD | wc -l` = 59 ✓; the `citizens_plus_witnesses` zero re-run with
`grep -rln` over the working tree (vs `git grep` over the index) — same single file ✓; the §A
sibling table re-checked by `git diff --name-only 109df97a..HEAD -- web4-standard/core-spec/ | sort
-u` → **1 file, `interface-planes.md`** ✓ (one command confirming ten cells). Every gate cell above
carries its command (v45.5). This pass's own findings do not enter its own carry table (v62).

**Adversarial policy review (standing rule): 4 of 4 items CONFIRMED, one sentence WEAKENED and
adopted** (N1's "cannot document" → single-class expressiveness under the restricted binding; §5
escape route added as fork option (d) — reviewer cites re-verified by command before adoption,
v52). The review also **strengthened d2**: the crate's ConsequenceClass assignments are grounded in
`hub-law-schema.md:185-189` (notice/quarantine/rehabilitate = Reversible, correct = Costly, kinetic
= Costly/Irreversible → crate returns `None` and defers to source primitives), and `validate()`
(`lib.rs:355-364`) rejects `r6.*` response selectors — the Reference clause's parse-scope form.

**Routed observation (INFO → reputation lineage, next pass ~C472):** `C432:39`'s carry-table cell
cites "§C.3" for B-D1's second datapoint; the datapoint lives in C432 **§C.5**. Pointer typo
internal to C432, no substantive effect — one-line disposition fix, same class as C374-N4.

**Cadence datapoint:** 12th consecutive zero-target-commit window for this lineage; both findings
came from a window event and a ledger audit, none from re-reading the frozen file — consistent with
the C270 cadence question (operator-owned, not self-decided).
