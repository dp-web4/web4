# C434 — `acp-framework` 11th delta

**Target**: `web4-standard/core-spec/acp-framework.md` — blob `f8d7ccda`, 710 L,
last moved `fb0075fc` (2026-07-08, C159 remediation). **Byte-frozen 45 days, 11th pass.**
**Window**: `fa8df9e5..HEAD` (C394's audit-doc commit, 2026-08-15 → HEAD `a8565ebe`).
**Predecessor**: `docs/audits/C394-acp-framework-10th-delta-2026-08-15.md` (PR #719), plus its
rev1 corrections (`ff0f2af8`).
**ZERO mutation.** No file under `web4-standard/` was edited by this pass.

---

## Headline

Canon grew a `MUST` about **reputation-bearing signals** three days ago. ACP emits one —
`t3v3Delta` — and **declares no classification for it anywhere**: `conduct` is 0 hits across all
four ACP artifacts, the schema types the field as a bare `{"type": "object"}`, and the SDK types
it as a bare `Dict[str, Any]`. So under the clause's own fail-closed default, **every ACP-emitted
delta is an unclassified signal**.

This is the **second locus** of `C432-N1`, found one day later by a different lineage, and it is
worth the slot for one reason: **C432's locus is closed (`additionalProperties: false`) and ACP's
is open.** The remedy fork C432 routed has an arm whose cost *inverts* between the two. A fork
adjudicated from one locus alone would have been adjudicated wrong.

Secondary yield: the pass **reproduced C394's Instrument A exactly** and then found the source of
its own predecessor's stated uncertainty — C394 labelled its union figure *"a floor with a 3-name
example-dependent tail."* Measured against the corpus's own CI-blessed documents instead of the
one hand-picked example, **the floor is 26 and the measurement is 37**, and the schema instrument
turns out to be **strictly subsumed**, not incomparable.

Both routed rows are **discharged**, one of them with an attribution its originator did not supply.

---

## §B — Window: both halves empty for the 8th consecutive fire

Pre-registered before running (v26). Span `fa8df9e5..HEAD`; root = repo root; no filetype filter;
audit trees excluded by pathspec where stated.

| measure | command | result |
|---|---|---|
| commits in window | `git log --oneline fa8df9e5..HEAD` | **45** |
| non-audit | `… -- . ':!docs/audits' ':!web4-standard/docs/audits'` | **28** |
| touching `web4-standard/` | `… -- web4-standard/` | **1** |
| touching the target | `… -- web4-standard/core-spec/acp-framework.md` | **0** |

**Mirror set — 15 artifacts, each probed individually, all 0.** The set is the 9 filename-matched
canonical artifacts C354 enumerated **plus the 6 generic-layer SDK files C394 added**. It is
re-published in full rather than as a count, and **it does not contract** (v81):

```
0  web4-standard/core-spec/acp-framework.md
0  web4-standard/schemas/acp-jsonld.schema.json
0  web4-standard/schemas/contexts/acp.jsonld
0  web4-standard/implementation/sdk/web4/acp.py
0  web4-standard/implementation/sdk/tests/test_acp.py
0  web4-standard/implementation/sdk/tests/test_acp_jsonld.py
0  web4-standard/test-vectors/acp/plan-operations.json
0  web4-standard/test-vectors/schema-validation/acp-jsonld-validation.json
0  web4-standard/ACP_INTEGRATION_SUMMARY.md
0  web4-standard/implementation/sdk/web4/generate.py       ← added by C394
0  web4-standard/implementation/sdk/web4/deserialize.py    ← added by C394
0  web4-standard/implementation/sdk/web4/validation.py     ← added by C394
0  web4-standard/implementation/sdk/web4/mcp_server.py     ← added by C394
0  web4-standard/implementation/sdk/web4/__main__.py       ← added by C394
0  web4-standard/implementation/sdk/web4/schema_registry.json ← added by C394
```

**The one `web4-standard/` commit is `2462881f`** — *"canon: specify interface planes (fact planes ×
exposure classes)"* (#727, 2026-08-19) — which **adds** `core-spec/interface-planes.md` (196 L) and
touches `GLOSSARY.md` and `README.md`.

**A new sibling spec in the window is not "no motion."** It is the strongest motion a frozen target
can receive, because a frozen target cannot answer a clause written after it froze (v81). §C.1 and
§C.2 are that answer.

**Disposition of the foreign remainder, with the lineage named** (a per-lineage window has no inbox):
of the 28 non-audit commits, **20** touch the `hub/` tree (HUB track), **4** touch `whitepaper`/
`docs/whitepaper*` (CBP Publisher track), **2** touch `web4-core/` (the hub/core-crate track),
**1** is `forum/`, and **1** is `2462881f`. None is dispositioned as "unrelated" without a
destination named.

---

## §A — Carry ledger: **11 rows + I-3 = 12**, survival 12/12

Pre-registered C434 check 1 was: *is `C314-N1` still row 12? Fewer than 11 rows ⇒ retired again,
check the deflation.* **It is row 12. Nothing was retired.** C394 recovered it after a full pass
of absence (that recovery is C394-N1 / v62); this pass confirms the recovery held one window.

| Carry | C394 | C434 | Live evidence at HEAD |
|---|---|---|---|
| **M7** — int `witnessLevel` vs structured `witness_requirement` | STILL-OPEN | **STILL-OPEN** | target blob `f8d7ccda`, unmoved |
| **B-LEDGERPROOF / C37-5** | STILL-OPEN | **STILL-OPEN** | blob-identical |
| **N2** — `maxAtp` cumulative vs per-intent | STILL-OPEN | **STILL-OPEN** | blob-identical |
| **JSONC fences** (3 of 7) | STILL-OPEN | **STILL-OPEN** | blob-identical |
| **I-3** — `ACP_INTEGRATION_SUMMARY.md:101` `ledgerInclusion` in prose, in no ledger | STILL-OPEN, 69 d | **STILL-OPEN, 76 d** | `3283d330`, unmoved |
| **M6** — `acp:` predicates in no TTL | STILL-OPEN | **STILL-OPEN** | unmoved |
| **B-AGENCY / L1** | STILL-OPEN | **STILL-OPEN** | MEDIUM CROSS-TRACK, unchanged |
| **B8** — ACP discharge not routed through R6 | STILL-OPEN | **STILL-OPEN** | unchanged |
| **N4** — hub write tools carry no proof-of-agency | INFO (UNTRIPPED) | **STILL INFO (UNTRIPPED)** | unchanged |
| **B11 / B12 / B13 / B14 / B15** | STILL-OPEN | **STILL-OPEN** | `errors.md` did not move this window |
| **B1-3** | in ledger (C354 N2 row 11) | **STILL IN THE LEDGER** | not retired |
| **`C314-N1`** — schema properties undefined in `contexts/acp.jsonld` | RE-ENTERED at LOW | **HELD at row 12** | re-measured in §C.3 |

### A.1 — `C374-N4` **DISCHARGED**, with the attribution C374 did not supply

`C374:372` routed this here by name (*"the acp lineage owes a …"*). It has been unserved for six
passes. The charge: **`C354:65-67`'s disposition row misattributes `afd04623`.**

**Re-verified independently at HEAD, not read off C374:**

```
$ git show --stat afd04623 -- …/errors.md        →  7 +++++--   (5 insertions, 2 deletions)
$ git show afd04623 -- …/errors.md | grep '^@@'  →  @@ -2,7 +2,7 @@   @@ -91,6 +91,9 @@   @@ -142,7 +145,7 @@
$ git show afd04623:…/errors.md  | sed -n 9p | md5sum  →  94ff58120a57a33db05ba850de636e53
$ git show afd04623^:…/errors.md | sed -n 9p | md5sum  →  94ff58120a57a33db05ba850de636e53
```

§1's delegation sentence is **line 9**. The first hunk spans lines 2–8. Line 9 is outside all three
hunks and is **byte-identical at the commit and its parent**. C354's cell claims *"§1's delegation
sentence and Last-Updated revised"* — the `Last-Updated` half is true, **the §1 half is false**, and
C354's next clause (*"§1's edit is what makes N1 citable at HEAD"*) rests on the false half.

**The increment this pass adds.** C374 established *"not this commit."* It did not establish *which*.
Dated here:

```
$ git log -S'ACP (`acp-framework.md` §10)' -- …/errors.md   →  aaa2bd86  2026-06-04  (#269)
```

The sentence that makes `C354-N1` citable at HEAD was written by **`aaa2bd86` (2026-06-04, #269,
"resolve 5 autonomous-actionable C30 findings")** — **67 days** before the commit C354 credited, and
a different PR. **`C354-N1` survives; only its dating is wrong**, and it is now dated.

**`C354` is NOT retro-edited.** The correction is recorded here, in the pass that made it, because
reading a settled row's predicate off a later finding is the v72 hazard and C354 is *this lineage's
own* prior pass. Row **CLOSED**.

### A.2 — `C390-N2` **DISCHARGED**: the divergence is **two** convention axes, not one

`C390:57` routed *"one instrument divergence … to the acp lineage"*, under `C314:258`'s own guard 3.
Also six passes unserved. C390 read `r7-action` at **8** where `C314:195` reads **2**, and attributed
the gap to a single axis: *"C314 scored top-level plus one nested level; this pass walks recursively."*

**Both figures reproduce at HEAD. Neither artifact has moved** (`r7-action-jsonld.schema.json`
`766611ef`, 2026-05-14; `contexts/r7-action.jsonld` `936c2d92`, 2026-03-24). And the reconciliation
is **exact**, which is what makes the decomposition checkable rather than plausible:

| convention | props | undefined | coverage |
|---|---|---|---|
| **per-`$def` occurrences, depth 1** — C314's | **31** | **2** | **93.5%** ← byte-identical to `C314:195` |
| distinct names, depth 1 | 29 | **1** | — |
| **distinct names, full recursive** — C390's | 81 | **8** | — ← byte-identical to `C390:248` |

**The single axis C390 named accounts for the 1 → 8 step. It does not account for the 1 → 2 step.**
C314's two undefined entries are `('trust_tensor', 'composite_score')` and
`('value_tensor', 'composite_score')` — **the same property name, counted twice.** So:

- **Axis 1 — distinct vs per-occurrence.** r7-action has **one** undefined *name*; C314's convention
  reports **2** because `composite_score` is declared in two `$defs`.
- **Axis 2 — depth-1 vs recursive.** Recursion adds **7**: `amount, atp, atp_balance, hard, message,
  release_condition, threshold`.

Axis 1 is exactly the convention split C394's rev1 corrections identified **for `acp`**
(21 distinct / 22 per-`$def`; the delta is `expiresAt`, declared twice). **Nobody applied it to
`r7-action`**, which is why the divergence read as one axis for eight days.

**Adjudication, since the row was routed here to be settled and not merely restated.** Both figures
are correct on their own domain and both stay. But they answer different questions, and the finding
they were built for — *does a JSON-LD processor drop this key* — is answered by **what is on the
wire at any depth**, which is C390's convention. C314's depth-1 per-occurrence convention answers
*what the schema declares*. Row **CLOSED**; both conventions published side by side (v61), with the
bridge stated: `1 → ×2 occurrences → 2` and `1 → +7 recursion → 8`.

---

## §C — Findings

| # | Severity | Class | Owner |
|---|---|---|---|
| **N1** | **LOW-MED**, capped | **net-new per-LOCUS**; the *class* is `C432-N1`, one day old | **files into `C432-N1`'s existing fork** — standard editor + `r7-action` schema owner + `web4-core`/hub, jointly. **Do not self-apply.** |
| **N2** | **INFO-LOW**, modality-capped | net-new predicate on a locus with two refuted precedents | standard editor, **with** N1 |
| **N3** | **LOW**, instrument | increment on `C314-N1` / guard 3 | recorded, this ledger |
| **N4** | **INFO** | B-D1's **third** datapoint | operator (B-D1 is unanswered) — **do not self-resolve** |

### C.1 — **N1 (LOW-MED, capped)**: ACP emits a reputation-bearing signal and declares no classification for it

`web4-standard/core-spec/interface-planes.md:109-110` (added `2462881f`, **2026-08-19**):

> - Every reputation-bearing signal **MUST** carry a classification distinguishing conduct from
>   infrastructure, and an unclassified signal **MUST** default to the non-conduct class.

**ACP emits such a signal.** `acp-framework.md:161` (§2.4 Execution Record) carries `t3v3Delta`,
a T3/V3 delta attributed to `agent` and `client`; `:229` makes the emission a state-machine
transition action (*"Recording | Witnessed | Complete | Update trust tensors"*).

**ACP declares no classification, anywhere.** Census over the four ACP artifacts, published with its
denominator:

```
$ for f in core-spec/acp-framework.md schemas/acp-jsonld.schema.json \
           schemas/contexts/acp.jsonld implementation/sdk/web4/acp.py; do grep -ci conduct $f; done
   0   0   0   0
```

- **Schema**: `acp-jsonld.schema.json:228` — `"t3v3Delta": { "type": "object" }`. No `properties`,
  no `required`, no constraint of any kind.
- **SDK**: `acp.py:890` — `t3v3_delta: Dict[str, Any] = field(default_factory=dict)`.

**Therefore every ACP-emitted delta is an *unclassified signal*, and `:110` assigns it the
non-conduct class by default.** What follows from that default is **undecidable**, because
`non-conduct` is an undefined key — **that is `C432-N2`, and it is cited here, not re-derived**.

#### The placement measurement — executed, on the corpus's own CI vectors

jsonschema **4.26.0**, `Draft202012Validator.iter_errors` read directly (not the non-raising
`validate()`). Base document = **`acp-valid-009`**, the corpus's own MUST-PASS vector
*"ExecutionRecord with failure result"*, taken verbatim from
`test-vectors/schema-validation/acp-jsonld-validation.json`.

| arm | placement | errors |
|---|---|---|
| baseline | `acp-valid-009` unmodified | **0** |
| 1 | `result.failureClass = "infrastructure"` | **FAILS** |
| 2 | root `signalClass = "non-conduct"` | **FAILS** |
| 3 | **`t3v3Delta.signalClass = "non-conduct"`** | **0 — PERMITTED** |
| neg-control | `result.banana = 1` | **FAILS, identical message** |

**The honest charge is ABSENT-BUT-PERMITTED, not FORBIDDEN**, and the distinction is the whole
finding. Arms 1 and 2 fail because `$defs.ExecutionRecord` and its `result` sub-object are both
`"additionalProperties": false`. Arm 3 passes because `t3v3Delta` — **the reputation-bearing signal
itself, which is what `:109` predicates on** — is an open object.

The corpus's own MUST-FAIL vectors for arms 1 and 2, stated precisely rather than approximately:

- **Arm 1 → `acp-invalid-019`**, *"Extra field in result (ExecutionRecord)"* — **exact**.
- **Arm 2 → `acp-invalid-013`** is the **nearest** vector, *"Extra field at root level"*, but its
  `@type` is **`AgentPlan`**, not `ExecutionRecord`. **The corpus has no ExecutionRecord-root
  analogue: 0 of 24 invalid vectors.** Of the 5 ExecutionRecord invalid vectors
  (`-011, -012, -019, -022, -024`) none exercises a root-level extra field. That absence is
  published here as a denominator rather than left for a later pass to charge as an instrument gap.

#### Why this locus is worth a slot when the class is one day old

`C432-N1` routed a **three-arm fork**, jointly, to the standard editor, the `r7-action` schema owner
and the `web4-core`/hub owner. **This finding does not open a second fork — it files as that fork's
second locus.** Its payload is that **arm A's cost inverts between the two loci**:

| | C432's locus — `$defs.reputation_delta` | this locus — `$defs.ExecutionRecord.t3v3Delta` |
|---|---|---|
| shape | closed, `additionalProperties: false` | **open**, bare `{"type": "object"}` |
| **arm A** (add the class field) | **expensive** — amends a *published* schema, and must also reach `schema_registry.json` and the reference SDK or it reproduces C350-N1's mechanism | **cheap** — the field already validates; what is missing is a *declaration*, not a *slot* |
| **arm B** (narrow `:109`) | resolves it | resolves it |

A fork adjudicated on C432's locus alone would read arm A as uniformly expensive and would likely
take arm B. Measured across both loci, **arm A is expensive in one place and nearly free in the
other** — which is a different decision. That is the contribution.

#### Severity, capped where it is true

**LOW-MED, not MED.** The clause is **3 days old**; the target and every mirror have been frozen
for 45 days; and the direction of the defect is therefore **ratification without propagation** — the
target cannot be blamed for failing a clause written 42 days after it froze. **The cap is the
clause's age and zero adopters, not the word "proposed"** (`C432:166-169` already ruled that
`proposed` does not distinguish `interface-planes.md` from its siblings — that ruling is inherited,
not re-derived). **No violation is asserted against any implementer.**

#### Novelty, matcher published beside the claim (v44)

Scoped to `docs/audits/` at HEAD, exact-string (`grep -rlF`):

| token | audits | verdict |
|---|---|---|
| `t3v3Delta` | **8** — all acp-lineage (`internal-consistency`, C37, C86, C125, C196, C234, C274) + `C154` | none about classification |
| `non-conduct` | **1** — `C432` only | the class, one day old |
| `fact plane` | **1** — `C432` only | — |
| `interface-planes` | **3** — `C424`, `C428`, `C432` | none is acp |
| `plane E` | **0** | — |

**The conjunction `t3v3Delta` × `non-conduct` is empty. Novelty is per-LOCUS (v56), and the locus is
net-new; the class is not, and is credited to `C432` in the finding's first sentence.**

### C.2 — **N2 (INFO-LOW, modality-capped)**: ACP names plane E's worked case and has no plane-E destination

`interface-planes.md` §4 gives a normative reason why infrastructure telemetry is a plane:

> A fail-closed denial is unwitnessable by construction. The gate refuses *because* the authority is
> unreachable — and the witness record goes to that same authority.

and requires: *"Infrastructure failure records **MUST** have a durable destination that does not
depend on the component whose failure is being recorded."*

**ACP instantiates that scenario by name.** `acp-framework.md:535-537` defines
`class LedgerWriteFailure(ACPError)` — *"Failed to write to immutable ledger"*,
`W4_ERR_ACP_LEDGER_WRITE`. `:487` (§9.1 MUST #4) is *"Ledger Recording: Execution records **MUST**
be written to ledger."* So the one durable destination ACP mandates is the one whose failure
`LedgerWriteFailure` reports.

**Absence measured over the whole document, with the matcher published:**

```
ledger 8 · "audit trail" 1 · log_error 1 · telemetry 0 · durable 0 · "dead letter" 0 ·
"fallback store" 0 · "out-of-band" 0        (grep -cio, web4-standard/core-spec/acp-framework.md)
grep -nic "telemetry\|dead_letter\|durable"  …/sdk/web4/acp.py   →   0
```

The concept is **not** absent from the corpus — `plane E` / infrastructure-telemetry vocabulary
appears in `hub/hub-daemon/src/{main,rest}.rs`, `hub/docs/TROUBLESHOOTING.md` and
`web4-standard/GLOSSARY.md`. **It is absent from ACP.** Again propagation, not ignorance.

#### Capped, and capped for three independent reasons

1. **Modality.** The two loci are inside Python illustration blocks. Census over §10
   (`awk 'NR>=506&&NR<=600'`): **exactly one** RFC2119 keyword in the entire section — a `MUST` at
   **`:556`** (*"those branches MUST discriminate on context before selecting a remedy"*) — **and it
   is not the clause at issue.** A non-normative code block cannot violate a MUST at full weight.
2. **Two refuted precedents on this exact locus, honoured.** `C37 B1-4` charged §10.2's dispatch on
   `ApprovalRequired`/`LedgerWriteFailure` as orphan recovery branches; `C125 F2` **REFUTED** it, and
   `C37:324`'s own remediation direction already records that §10.2 is illustrative. **This finding
   is not predicated on §10.2's dispatch.** Its predicate is *destination durability*, over the whole
   document — a different question, and the reason it is filed at INFO-LOW rather than dropped.
3. **Clause age**, as in N1.

**Adjacent observation, recorded because it points at the cheap remedy.** `:556` shows ACP already
has a **cause-discrimination discipline** — it requires a handler to discriminate *why* a class was
raised before choosing a remedy. What it lacks is that discipline **for the record** rather than for
the remedy. The distinction §4 asks ACP to make is one ACP already makes one layer up.

**Not a re-charge of `B-8/X3`**, whose predicate is a **naming collision**
(`W4_ERR_ACP_LEDGER_WRITE` vs SAL's bare `W4_ERR_LEDGER_WRITE`). Attribution, stated precisely
because the id is overloaded: **B-8/X3 originates in the *errors* lineage** (`C106` → `C138:46`,
`C178:49`, `C216:49`) and is **also carried in the registries ledger** (`C298`, `C338`, `C418:356`).
**`B-8` is a separate row in the security-framework lineage** (the `security.py:146` docstring row,
`C140:55`, `C256:57`). Neither is re-charged here.

### C.3 — **N3 (LOW, instrument)**: guard 3's substance re-run — the baseline reproduces exactly, and the union is a floor that measures 37

Pre-registered C434 check 2: *re-run BOTH instruments, publish the union; baseline B = 21/22,
A = 20, union = 26, blobs `fbe09135`/`08b09ffb`.*

**Blobs verified identical**: `acp-jsonld.schema.json` = `fbe09135`, `contexts/acp.jsonld` =
`08b09ffb`. Context terms = **36**.

| instrument | domain, stated before the count (v40) | props | undefined |
|---|---|---|---|
| **B** — schema-declared | `$defs/X/properties`, **depth 1, distinct names** | 49 | **21** |
| **B** — schema-declared | same, **per-`$def` occurrences** (C314's convention) | 62 | **22** |
| **B** — schema-declared | **full recursive** walk of every `properties` block | 52 | **23** |
| **A** — emitter-produced | the four `to_jsonld()` outputs on the **canonical example** | 44 | **20** |

**All four cells reproduce C394 and C314 exactly.** `A \ B` = **5** (`output, q, rows, status,
tool`), `B \ A` = **6** (`audience, authorized, dependsOn, expr, kind, requiresApproval`),
**UNION = 26.** Guard 3's substance is discharged for a second consecutive pass.

**Instrument A's provenance, resolved and now reproducible.** C394 described A as *"the canonical
example"* without naming it, which made the figure un-rerunnable by anyone but its author. It is
**`web4-standard/implementation/sdk/web4/generate.py`** — `_make_agent_plan` (`:104`),
`_make_intent` (`:116`), `_make_decision` (`:129`), `_make_execution_record` (`:140`), reached via
`from web4.generate import generate`. The tail names come from `:148` (`{"tool": …, "args": {"q": …}}`)
and `:150` (`{"rows": 42}`). **Recorded so the next pass re-runs it instead of re-deriving it.**

#### The increment: C394 said 26 was a floor. It is, and the floor measures 37.

C394's own tail note: *"`tool`, `q`, `rows` are not emitter literals … A different payload yields a
different tail. **26 is therefore a floor with a 3-name example-dependent tail, not a settled
total**."* That caution is testable, and the corpus supplies the population to test it with —
prefer the corpus's own CI-run documents to one hand-picked example (v81).

**Instrument A′ — wire-carried key names across all 12 CI-blessed `valid` documents** in
`test-vectors/schema-validation/acp-jsonld-validation.json`. Domain stated: this is **not** a re-run
of A (whose domain is *what the SDK emits*); it is a **third** instrument whose domain is *what the
corpus's own conformance suite blesses on the wire*.

| instrument | population | props | undefined | vs B |
|---|---|---|---|---|
| **A** | 4 `generate.py` documents | 44 | **20** | `A \ B` = 5, `B \ A` = 6 → union **26** |
| **A′** | **12 CI `valid` documents** | 66 | **37** | `A′ \ B` = 16, **`B \ A′` = ∅** → union **37** |
| A″ | 4 SDK test fixtures (`test_acp_jsonld.py`) | 54 | 26 | union 30 |
| **all three ∪ B** | | | | **43** |

**Two results, and the second is the one that matters.**

1. **The floor moves from 26 to 37** on the corpus's own MUST-PASS documents. The 11 names A′ adds
   that no other instrument sees are `compute_ms, data, error, input, maxRows, query, rows, score,
   target, temperament, training, url` — every one of them a key the CI suite asserts *must
   validate*.
2. **`B \ A′` = ∅ — instrument B is strictly subsumed by A′.** C394's headline conclusion was
   *"the two instruments do not subsume each other."* **That is true of A and B, and false of A′ and
   B.** The six names in `B \ A` — `audience, authorized, dependsOn, expr, kind, requiresApproval` —
   are absent from `generate.py`'s minimal example but **present in the CI vectors**. The
   incomparability C394 reported is a property of the *example*, not of the *instruments*.

**`C314-N1` therefore holds at row 12 with its severity unchanged (LOW) and its measurement widened
from 26 to 37**, denominators published for each. Not escalated: the widening is breadth on a known
class, and breadth is not consumption — the same ground on which `C394` declined `C390`'s escalation.

### C.4 — **N4 (INFO)**: B-D1's third datapoint — the clause has no inbound path to ACP either

```
$ grep -ci "acp\|agentic" web4-standard/core-spec/interface-planes.md   →  0
```

`interface-planes.md` §9 *"Relationship to other specifications"* names **six** sibling specs in **four** bullets
(`hub-law-schema.md`; `entity-types.md` + `society-roles.md`; `MCP_ENTITY_SPECIFICATION.md`;
`SOCIETY_SPECIFICATION.md` + `inter-society-protocol.md`). `acp-framework.md` is not among them,
although §4 constrains exactly the signal ACP emits.

**Not novel and not re-derived here.** `C424:34-46` charged this shape for `mcp-protocol.md`
(2026-08-21) and `C432 §C.5` filed it as **B-D1's second datapoint** (2026-08-22), both leaving the
instruction *"report either way; do not self-resolve — B-D1 is operator-unanswered."*
**Recorded here as B-D1's third datapoint, on the same file, and honoured as instructed.**

Also recorded: the v36 residue sweep confirms it from the other direction. `interface-planes.md`
does **not** appear in the domain-token residue below, because it contains none of the domain's
words — the citation gap is symmetric.

---

## §D — Negatives, recorded

**Recording the negative is what makes another fire's positive interpretable** (v36).

| check | result |
|---|---|
| **C434 check 3** — `git grep -nE 'W4_ERR_ACP"' -- web4-standard/` | **1** hit (`acp.py:80`). Baseline holds; `C354-N1` still open, not re-charged. |
| **C434 check 4a** — `witnesses` bare-string | **unmoved**: `acp-jsonld.schema.json:189` and `:229`, both `"items": {"type": "string"}`. `C274-N1` stands. |
| **C434 check 4b** — acp↔r7 cross-citation | **0 in both directions**, unchanged. |
| **C434 check 5** — schema-tree enumeration | **24**. Denominator rule published: `git ls-files 'web4-standard/schemas/*.json'` = **24** because a git pathspec `*` crosses `/`; the shell glob `ls web4-standard/schemas/*.json` = **12** because it does not recurse. **24 is the figure used** (v41). |
| **C322-N3** (`WEB4_SCHEMA_DIR` ignored) | **not re-charged** — the dictionary lineage's row, confirmed 3× already. |
| **Refuted guards (a) `ledgerInclusion` → `C286:115`, (b) `@context` absence in §2.x examples → `C37:264-266`/C87, (c) `ns/` vs `ontology#` → `C310:163`** | **all pre-declared out of scope before any validator ran.** No example validator was run against §2.x. |
| **Matcher guard** | `grep -F` used for `acp.jsonld` throughout; the regex form matches `acp-jsonld` and returns 11 instead of 0. |
| **Two rows named `N1`** in this lineage (C314's coverage, C354's `W4_ERR_ACP`) | disambiguated by C-prefix everywhere above; neither conflated. |

---

## §E — Evidence, built by capture

**v36 inbound sweep as a set difference**, verb set pre-registered before running, searched by the
**domain's word** rather than the target's filename (a path-token sweep is a citation-graph query
and cannot return an orphan).

- **Domain tokens (pre-registered):** `Agentic Context Protocol` (**30** files), `AgentPlan` (**45**),
  `ExecutionRecord` (**45**). **Union = 68.**
- **Filename sweep:** `git ls-files | grep -i acp` = **46** (was 45 at C394; the increment is C394's
  own audit doc).
- **Residue** (`comm -23`, domain \ filename) = **33 rows**; **reverse difference = 11** (all
  filename-matched artifacts that never spell the domain's words — the target's own schemas and
  vectors among them: *a file never writes its own name*).
- **Residue rows that postdate C394: none.** The residue's 32 non-audit rows are byte-stable across
  the window — consistent with §B's all-zero mirror table. **The negative is the result**: this
  window's motion is entirely in `2462881f`, and `2462881f` is invisible to *every* acp instrument,
  which is §C.4.

**Novelty matcher**: published in §C.1 beside the claim it licenses, not here.

**Reproduction commands for every executed cell** are inline in §A.1, §A.2, §C.1, §C.2 and §C.3.
Nothing in this document is inherited without re-execution except where explicitly labelled
*"inherited, not re-derived"* (`C432:166-169`'s `proposed` ruling; `C424`/`C432`'s B-D1 instruction).

**Not machine-checked, labelled in place:** the claim in §C.1 that a conformant JSON-LD 1.1
processor *drops* undefined keys is hand-derived from the context files' `@`-level keys — `pyld` is
still `ModuleNotFoundError` on this host, as C394 recorded. The **term-coverage** measurements in
§C.3 are fully machine-checked; the **expansion consequence** is not.

---

## §F — Instrument corrections

1. **`C354:65-67`** — disposition misattributes `afd04623`; corrected in §A.1, with the true
   attribution `aaa2bd86` (2026-06-04, #269). **`C354` not retro-edited** (v72).
2. **`C390:275`** — *"The gap is a counting-convention difference"* names **one** axis where there
   are **two**. Corrected in §A.2; C390's figure stands, its explanation is completed, and both
   conventions are published side by side.
3. **`C394 §C.2` headline** — *"the two instruments do not subsume each other"* is **true of A and B
   and false of A′ and B** (§C.3). Not an error: C394's own tail note anticipated it
   (*"26 is a floor … not a settled total"*). Recorded as a **scope narrowing**, not a refutation —
   the sentence needs the words *"on the canonical example."*
4. **This pass's own first draft of N1** said the ACP record **"cannot carry"** the classification.
   **False** — arm 3 (`t3v3Delta.signalClass`) validates with 0 errors, and the arm had been run
   before the claim was written and then mis-summarised. Caught in policy review. The published
   charge is **absent-but-permitted**, which is *both* the honest reading and the stronger one,
   because it is what makes the arm-A cost inversion in §C.1 true.
5. **This pass's own first draft** cited `acp-invalid-013` as the ExecutionRecord root-extra-field
   vector. It is **`@type: AgentPlan`**. Corrected in §C.1, and the absence it exposes
   (**0 of 24** invalid vectors cover an ExecutionRecord root-extra field) is published as a
   denominator rather than quietly dropped.

---

## §G — Next-delta (C474) checks — pre-registered

Rotation arithmetic: `C434 + 40 = C474`. **Read this section and this file's `per_file_guards.md`
entry; do not re-derive them.**

1. **Ledger arithmetic.** Baseline is **11 rows + I-3 = 12**, with `C374-N4` and `C390-N2`
   **CLOSED this pass** — they are discharged, not retired, and must **not** re-enter as open rows.
   Fewer than 12 ⇒ check the deflation before accepting it (v42).
2. **`C432-N1` / N1's fork.** Has any arm been taken? If `interface-planes.md:109` was **narrowed**
   (arm B), N1 dissolves and its row retires with a reason. If a `class` field was **added** to
   `$defs.reputation_delta` (arm A) and **not** to `t3v3Delta`, that is the propagation failure
   recurring one level down — **charge it then, and it is MED, not LOW-MED**, because the clause
   will no longer be young and the fork will have been adjudicated. **Check both fields, at all
   four sites** (`acp-jsonld.schema.json`, `schema_registry.json`, `acp.py`, the CI vectors).
3. **Guard 3, substance not footnote.** Re-run **all three** instruments. Baselines:
   **B = 21 distinct / 22 per-`$def` / 23 recursive of 49·62·52**, **A = 20 of 44**,
   **A′ = 37 of 66**, **union(A,B) = 26**, **union(A′,B) = 37**, **`B \ A′` = ∅**.
   Instrument A is `from web4.generate import generate` over the four ACP types — **named now, so
   re-run it rather than re-deriving a "canonical example."** Blobs `fbe09135` / `08b09ffb`.
   **If `B \ A′` ≠ ∅ at C474, a CI vector was removed — find out which.**
4. **`W4_ERR_ACP"`** = **1** hit is the baseline (`C354-N1` open). Any change is the answer.
5. **`witnesses`** still bare-string at `:189` / `:229`; acp↔r7 **0** both directions.
6. **Schema trees**: **24** via `git ls-files` (never the shell glob's 12), rule published in §D.
7. **B-D1** is now at **three** datapoints on `interface-planes.md` (C424, C432, C434). If it is
   **still operator-unanswered at C474 that is a fourth, and the routing failure is the finding** —
   report it, do **not** self-resolve.
8. **N2's cheap test.** Did anything give ACP a non-ledger durable destination? Matcher:
   `telemetry|durable|dead_letter|"out-of-band"` over `acp-framework.md` + `acp.py`; **baseline is
   0 in both.** Do **not** re-open `C37 B1-4` (REFUTED at `C125 F2`) — the predicate is
   *destination durability*, not §10.2's dispatch.
9. **Mirror set is FIFTEEN.** Do not contract it. If a member is dropped, **state the reason in the
   pass that drops it** — C432's lesson (v81) was a mirror-set contraction that lost the file where
   the motion happened.
10. **Refuted guards (a)/(b)/(c) all standing**; pre-declare them out of scope **before** running
    any example validator.

---

## Accountability self-audit

```
surface: C434 delta-audit document   act: publish audit findings that route remediation of a normative spec
S: low/reversible [construct: docs/audits/C434-…md — a document; zero mutation of any normative artifact]
R: n/a [construct: no reachability-gated path exercised]
W: pass [construct: findings routed to named owners — C432-N1's existing fork (standard editor +
   r7-action schema owner + web4-core/hub) and the standard editor; NO self-application]
O: pass [construct: policy review (Step 4, REVISE→APPROVED) preflighted the scope before any file
   was written; the one substantive error in the premise (N1's "cannot carry") was caught there and
   is recorded in §F.4 rather than shipped]
A: pass [construct: every executed cell carries the command that produced it; §F records this pass's
   own two errors with the same weight as its predecessors']
V: n/a [construct: no irreversible act; findings are advisory and explicitly not self-applied]
verdict: PASS
```

---

*C434 — 11th `acp-framework` delta. ZERO mutation. Target frozen 45 days; all 15 mirrors frozen;
window 45 / 28 / 1. Two six-pass-old routed rows discharged. Four findings, all capped where the
cap is true, none self-applied.*
