# C282 — `dictionary-entities.md`, 7th delta audit

**Date:** 2026-07-29 · **Track:** web4 (Legion, autonomous) · **Protocol:** v2
**Target:** `web4-standard/core-spec/dictionary-entities.md`
**Prior pass:** C242 (2026-07-21, PR #562) — 5th consecutive fully-clean
**Window:** `C242 (2026-07-21) .. HEAD 8bc3ef39 (2026-07-29)`
**Mutation of `web4-standard/`:** **ZERO** (all findings routed, none self-applied)

---

## Preconditions (stated before the work, per policy review)

The policy reviewer approved this pass as **REVISE → APPROVED** with three binding changes.
Both preconditions below are recorded *before* their results so neither can be retrofitted.

**P1 — Freeze proof is a precondition, not a conclusion.** If the target blob is **not**
`8e06a23c` / 603 lines at HEAD, the §A collapse authorized by the review is void, §A reopens
at full scope, and the approval does not cover that shape.

> **Result: CONFIRMED.** `git rev-parse HEAD:…/dictionary-entities.md` =
> `8e06a23cc2cc9f87e53c34e4f2ed25c82f130771`, 603 lines. Byte-frozen since `95d20919`
> (C53, 2026-06-12) — 47 days, 7 rotation passes. §A collapse is authorized.

**P2 — Stop rule (C274 forward ruling, extended to this fire as binding).** If the v7 mirror
gate returns NEGATIVE **and** §B′ produces no routable finding, the deliverable is a **short
no-op record**, not a full delta doc.

> **Result: the gate returned NEGATIVE, but §B′ produced a routable finding.** The stop rule
> was live and did not fire. See §B.3 and §C-N1.

**P3 — Subject-matter derivation is written before the gate is run** (§B.1 below), so the
mirror set cannot be retrofitted to whatever the gate returns.

---

## §A — Freeze proof (collapsed per policy review change 1)

Target blob unchanged ⇒ the **9 C53 findings HOLD BY CONSTRUCTION**. This is not re-derived
here; it is the same derivation C204 and C242 each performed and each labelled "clean **by
construction**" in their own text. Re-running nine finding-verifications at live line numbers
against 603 byte-identical lines for a sixth time was ruled padding and is not done.

Two reads are **not** settled by blob identity and therefore still ran:

| Check | Result |
|---|---|
| **SDK / sister-doc mirror freshness** | `sdk/web4/dictionary.py` = `edd97183`, `tests/test_dictionary.py` = `d8f71420`, `protocols/web4-dictionary-entities.md` = `b28d8f9e` — **all three byte-identical to C242's recorded blobs.** The SDK cross-track bundle (B15–B18, B24, B25) stands verbatim. |
| **C90 inbound-carry read** (sibling audit docs C270–C280) | **C280-N3 inbound and APPLIED** — see §B′. C280-N2 (#580's survey misses a ratified counter-precedent) is inbound and is **independently corroborated from a second direction** by N1 below; recorded, not re-booked. No other sibling carry routes here. |

---

## §B — Corpus delta, with the v7 mirror re-derivation

### B.1 Subject-matter derivation (written before the gate)

Method carry v7 (born C280) requires deriving the genuine-mirror set from the spec's
**subject matter** — *which artifacts NOW implement this?* — not by re-running C242's list.
`dictionary-entities.md`'s subject matter, taken from the spec's own section structure:

1. **Semantic translation across domain boundaries** (§1, §3, §4) — the translate/map/
   disambiguate/generate pipeline.
2. **Compression-trust management** (§1.1, §1.2, §3.3) — codebooks, compression ratio,
   reconstruction fidelity.
3. **Confidence & degradation tracking** (§4.2, §4.3) — per-hop and cumulative.
4. **Dictionary discovery and selection** (§6) — MRH/SPARQL discovery, ranked selection.
5. **Dictionary reputation economy** (§11) — earning, staking, slashing.

An artifact is a genuine mirror if it *implements one of these five*, regardless of whether
it contains the token `dictionar`.

### B.2 Gate results

| Candidate mirror | Basis | Verdict |
|---|---|---|
| `sdk/web4/dictionary.py` + `tests/` | implements 1–5 | **GENUINE** (byte-frozen; see §A) |
| `protocols/web4-dictionary-entities.md` | sister spec | **GENUINE** (byte-frozen) |
| **`hub/`** (31 tracked `.rs` files, incl. `law.rs`, `state.rs`, `events.rs`, `rest.rs`) | **v7 suspicion — the directory C280 found had never been gated in 7 society-spec passes** | **NEGATIVE on subject matter, not on token absence** — see the measured cluster below. Hub publishes act kinds, event types and role vocabularies, but it performs **no cross-domain translation, no compression-trust accounting, and no dictionary selection**. It is not a mirror by analogy and is **not widened into one**. |
| `web4-policy/`, `web4-trust-core/` | new crates since C242 | **NEGATIVE** — 0 `dictionar` each (`git grep -io dictionar 8bc3ef39 -- <crate>/`). The wider cluster is **not** zero here either and is disambiguated deliberately: `web4-policy/` carries `vocabular` 13 / `semantic` 2, `web4-trust-core/` `vocabular` 0 / `semantic` 11 — all of it the crates' own role/response vocabularies (`lib.rs:9/26/47/130/157/546/923`) and tensor-update semantics (`tensor/mod.rs:1/13/102/209`, `entity/trust.rs:17`). Same subject-matter ruling as `hub/`. |
| `web4-core/` (Rust `src/*.rs`) | 4 window commits (#538/#540/#544, `4f76f110`) | **NEGATIVE** — 0 `dictionar` in any `.rs`; the four commits are LCT-structure / oracle-scope faces already booked elsewhere (C248-N1/N2, SAL C246-N1). |
| `web4-core/python/…/trust/attestation/` | 2 raw token hits | **FALSE MIRROR** — see I-1. |
| `web4-standard/ontology/*.ttl` | method carry v6 (window touched `t3v3-ontology.ttl` at `01f410db`) | **NEGATIVE for net-new** — see the refuted candidate R-1. |

#### The `hub/` cluster, measured — instrument published beside the number

**Instrument:** `git grep -nio -e <token> 8bc3ef39 -- 'hub/**/*.rs'`. **Scope:** the 31 tracked `.rs`
files under `hub/` at `8bc3ef39`; `hub/target/` is **untracked** at this commit, so it is outside the
instrument by construction rather than by exclusion.

| token | hits (`-i`) | case-sensitive | what they are |
|---|---:|---:|---|
| `dictionar` | **0** | 0 | — |
| `vocabular` | **11** | 11 | hub's *own* role vocabularies (`law.rs:53/60/66/77/97/196/252/449/485`) and the `notify:*` sub-vocabulary (`events.rs:464`) |
| `semantic` | **15** | 13 | ledger / ring-buffer / write-through **semantics** (`ledger.rs:17`, `rest.rs:954/1024/7408`, `store.rs:1482`), r7 semantics (`rest.rs:3480`), and "**semantic** member discovery" — profile/interest lookup (`main.rs:349`, `rest.rs:2031/3288/3766`, `events.rs:251`, `session.rs:227`, `state.rs:439`) |
| `translat` | **1** | 1 | `rest.rs:1969`, prose: *"can deserialize without translation"* |
| `compress` | **0** | 0 | — |
| `codebook` | **0** | 0 | — |
| **total** | **27** | 25 | |

Two of the `semantic` hits are capitalized (`rest.rs:3288`, `rest.rs:3480`), so a plain `git grep -n`
returns 13 and `-i` returns 15. Both figures are published so that a future auditor's re-grep lands
whichever flag they use.

**27 hits, not zero — and the verdict is unchanged.** Every one of the 27 is hub's own role/event
vocabulary, its ledger and buffer semantics, its profile-based member discovery, or one line of
serialization prose. **None** implements any of the five subject-matter faces: no cross-domain
translation (the sole `translat` hit asserts the *absence* of translation), no compression-trust
accounting, no codebook, no dictionary selection, no dictionary reputation economy.

The NEGATIVE rests on that derivation — written in §B.1 **before** this gate was run — and never
needed the zero. This cell originally published one, which was a reflex to token-counting under a
method that is explicitly derivation-based, and token-counting is what produced the wrong number.
Recorded as such in §F.

**This answers goal (1) of the approved scope, and the answer is the negative one.** The
`hub/`-shaped blind spot C280 found is **society-lineage-specific, not corpus-wide.** Hub is
a society/law/ledger daemon, so it genuinely mirrored the society spec; it implements none of
dictionary's five subject-matter faces. Booked **INFO** per the C182/C220 negative-gate
precedent. The v7 carry stays live for the remaining lineages, but its first out-of-lineage
test is negative — which is worth as much as a positive would have been, and costs the
rotation the temptation to gate `hub/` reflexively everywhere.

### B.3 Window artifacts that claim authority over this subject matter (method carry v2)

Two, both authored by CBP **on dp's direction**, both 2026-07-25, both landed 2026-07-27:

- **#579 `dictionary-as-context-mandatory-role.md` (`4665a430`)** — aimed squarely at this
  lineage; carries inbound carry C280-N3.
- **#580 `resilience-to-incomplete-information.md` (`954ee391`)** — declares itself the
  **parent principle** and names #579 as an *instance* of it.

Both have **PROSPECTIVE authority** (status: *proposal, for fleet review*). Per the standing
v2 method carry, no charge may land on the ratified spec from either. The charge, where one
exists, lands on **the proposal's own precedent survey**.

---

## §B′ — Adjudication of #579 and #580

### N1 — [MEDIUM → CBP (proposal author) + SDK track (conditional)] · **FLAGSHIP**

**#580's precedent survey misses a live, exported counter-example in the corpus's own
canonical SDK — and it is in the dictionary module, the one #580 names as its lead instance.**

#580's sharpest corollary, the one that closes its privilege-escalation edge:

> **"Defaults resolve conservatively with respect to capability. Absence NEVER grants."**
> "Missing evidence → *less* trust, never assumed trust."
> **"'unmeasurable' resolves to UNKNOWN, never to a favourable value."** … "That is the
> pattern to generalize: **absence is *represented*, not *imputed*.**"
> "An attacker who omits fields must land in a strictly weaker position than one who
> supplies them — **otherwise omission becomes an attack.**"

#580 cites **hestia** — an implementation in a *different repo* — as the exemplar that
"already does this correctly," and claims the principle is "already canon in two places"
(r6-framework's corrective-R6, data-formats' unknown≠malformed).

The canonical SDK does the **exact inverse**, in the dictionary selection path, and says so
in its own docstring:

`web4-standard/implementation/sdk/web4/dictionary.py:750-773`
```python
    Filters candidates by domain coverage, then ranks by composite score.
    coverage_scores, recency_scores, cost_scores are keyed by lct_id.
    If not provided, defaults to 1.0 (assume perfect).
    ...
            coverage_ratio=coverage_scores.get(d.lct_id, 1.0),
            recency_score=recency_scores.get(d.lct_id, 1.0),
            cost_score=cost_scores.get(d.lct_id, 1.0),
```

An absent measurement is imputed not to UNKNOWN, not to a 0.5 prior, but to **the maximum**.
Sized against the module's own weights (`:716-719`, `TRUST 0.4 / COVERAGE 0.3 / RECENCY 0.2 /
COST 0.1`): **0.6 of the selection score defaults to ceiling.** Only `trust_composite` (0.4)
reads a real measurement (`d.t3.composite`). A Dictionary that supplies *no* coverage, *no*
recency and *no* cost data scores `0.6 + 0.4·t3` — strictly above a fully-measured peer with
honest but imperfect values. This is #580's own failure mode, stated in #580's own words:
omission is rewarded.

`select_best_dictionary` is **not** dead illustrative code: it is exported in `__all__`
(`dictionary.py:51`, `__init__.py:233/688`) and exercised by `test_dictionary.py:345-389`
and `test_integration.py:1171`.

**Corroborating negative:** the token `unmeasured` — the representation #580 says to
generalize — occurs **zero times anywhere in the SDK** (`grep -rn "unmeasured\|UNKNOWN"
sdk/web4/*.py` → 0). The corpus has no way to *represent* absence at all, so imputation is
not a local slip; it is the only available behaviour.

**Instrument scope, published with the number (method carry v4).** A `.get(…, 1.0)` fallback
appears in **3 of the SDK's modules** — but I am *not* claiming three counter-examples. Two
of them are neutral: `trust.py:508-513` and `mrh.py:189` default *relative weights*, which
normalize away (`/ total_w`), so absence means "equal weight," not "advantage." The honest
count of sites where **absence imputes advantage in an unnormalized score that decides an
outcome** is **two**: `dictionary.py:771-773`, and `binding.py:468` (`a_fresh = 1.0`).

**The second site is the sharp part, and it cuts at the remedy.** `binding.py:468` was
already adjudicated once — **C36-N5 [MEDIUM]**, 2026-06-07 — and the ratified remedy was
*"state that `attestation_freshness` defaults to 1.0 when no attestation proof is present."*
That is: **document the imputation.** If #580 ratifies as written, C36-N5's remedy becomes
the canonization of the anti-pattern #580 exists to remove. The two are in direct conflict
and nothing currently connects them.

**Refutation attempts, and why the finding survives (per [[feedback_refute_your_best_finding]] — this is the flagship, not a leftover):**

1. *"The caller is supposed to supply the scores; the default is API ergonomics."* — Fails.
   The docstring does not say "caller must supply"; it says **"assume perfect."** And #580's
   rule is precisely about behaviour when data is *absent*, which is exactly the
   first-contact case #579 exists to serve.
2. *"#580 is a proposal — prospective authority. You cannot charge a frozen SDK with
   violating unratified law."* — **Correct, and it reshapes the finding rather than killing
   it.** The charge is NOT "the SDK violates ratified law." It is: **#580's completeness
   claim ("already canon in two places") and its choice of an out-of-repo exemplar are
   falsified by its own lead instance's canonical implementation.** Charge lands on the
   precedent survey. Same shape as C280-N2 and C274-I1.
3. *"Corpus idiom — the SDK does this everywhere, so it is not a dictionary defect."* — The
   idiom baseline is what usually deflates a charge here (C158-JSONC, C234-"Scope",
   C274-witnesses). It **does not deflate this one, because the charge is not a deviation
   charge.** #580 asserts the corpus already embodies the principle; an idiom of the
   *opposite* behaviour makes that assertion more wrong, not less. Sized honestly above at
   two genuine sites, not three.

**Net-new as a FINDING, not as a FACT** (method carry v7, and stated so it cannot be
mistaken): the `1.0` default dates to `df1fca78` (#10) — the original module commit,
**~14 months old**, and no prior dictionary pass (C52/C53, C94, C132, C166, C204, C242) ever
examined it. What is 4 days old is the principle that makes it a defect. The FACT is old;
the FINDING is new.

**Routing.** CBP owns the proposal half (survey completeness + the C36-N5 collision). The SDK
half is **conditional** — it becomes actionable only if/when #580 ratifies, and even then the
fix is a design question (represent UNKNOWN vs. default conservative-low), not a mechanical
edit. **Not self-applied.**

### N2 — [INFO → CBP] #579 inherits a discovery mechanism that cannot satisfy #579's own MUST

#579 states: *"`dictionary-entities.md` §6 already specifies Discovery via MRH … **This
proposal does not alter that mechanism**."* It also requires: *"A discovery response MUST
distinguish 'not in vocabulary' from 'vocabulary unavailable' … an empty answer must not be
readable as 'nothing is accepted.'"*

The inherited mechanism is a SPARQL `SELECT` (`dictionary-entities.md:363-380`). A SPARQL
solution sequence is empty in all of these cases, indistinguishably: no Dictionary exists;
one exists but scores `≤ 0.8`; one exists but was last updated >30 days ago; the MRH graph
was unreachable. Further, an unmeasured Dictionary has **no `web4:trustScore` triple at all**,
so the basic graph pattern fails to match *before* any FILTER is reached — absence removes
the row silently. Combined with #580's "unmeasured → UNKNOWN, never favourable," a brand-new
society's Dictionary — **exactly the case #579 exists to serve** — is structurally
undiscoverable through the mechanism #579 declares adequate and unaltered.

Booked INFO, not MED: the charge is against a *proposal's* survey of a mechanism, both
proposals are drafts under fleet review, and the same `FILTER(?trust > 0.8)` shape is corpus
idiom (`mrh-tensors.md:352`, `mcp-protocol.md:798`) rather than a dictionary defect. **The
ratified spec is not charged.** Carries inbound **C280-N3** (#579's target list is complete
only under the context-mandatory branch of its own open question 1) — still open, CBP-owned.

### I-1 — [INFO] False mirror, recorded so a later pass does not re-acquire it

`web4-core/python/web4_core/trust/attestation/{__init__.py:4, envelope.py:79}` describe
`AttestationEnvelope` as *"the dictionary entity for hardware trust."* This is **metaphorical
borrowing of the term**, not an implementation of any of the five subject-matter faces; the
remaining two hits (`envelope.py:155/164`) are `dict` serialization docstrings. **Excluded
from the mirror set** per the C178/C216 false-mirror precedent. A future pass grepping
`dictionar` across `web4-core/` will hit these — they are not a mirror.

---

## §C — Findings and disposition

| # | Sev | Finding | Owner | Mutation |
|---|-----|---------|-------|----------|
| **N1** | **MED** | #580's precedent survey is falsified by its own lead instance's SDK (`select_best_dictionary` imputes absence to ceiling, 0.6 of score weight); collides with C36-N5's ratified "document the 1.0 default" remedy | **CBP** (survey) + SDK track (conditional on #580 ratifying) | none |
| **N2** | INFO | #579's inherited §6 discovery mechanism cannot satisfy #579's own "empty ≠ absent" MUST; new-society Dictionary structurally undiscoverable | **CBP** | none |
| **I-1** | INFO | `web4-core` attestation "dictionary entity" is a metaphor — false mirror, excluded | — | none |
| **I-2** | INFO | v7 `hub/` gate **NEGATIVE** — the C280 blind spot is society-lineage-specific | — | none |

**Net-new findings: 2 (1 MED, 1 INFO) + 2 INFO records. Both net-new findings came from
§B′ (the proposal adjudication). §A produced zero, as the freeze proof predicted. The
mirror gate produced zero *positive* results and one valuable negative.**

**Refuted candidates** (recorded so they are not re-acquired):

- **R-1 — "dictionary §6.1's SPARQL emits `web4:Dictionary`/`sourceDomain`/`targetDomain`/
  `coverage`/`trustScore`/`lastUpdated`, none of which are defined in `web4-standard/
  ontology/`" → REFUTED, not net-new.** Baselined (method carry v4): **84 of 114** `web4:`
  predicates emitted across `core-spec/` are undefined in the ontology — **74%, corpus-wide.**
  This is the already-open **C17-M1 / C16-M8 / C18-M6** ontology-cluster DESIGN-Q, not a
  dictionary defect and not new. The window's ontology commit (`01f410db`, `web4:Tensor`)
  adds no dictionary predicate; method carry v6's emitted-example diff comes back clean here.
- **R-2 — "§6.1's hardcoded `FILTER(?trust > 0.8)` prescribes a trust threshold, violating
  LCT §1.2 'Inspectable Evidence, Not Prescribed Trust'" → REFUTED.** Corpus idiom: the
  identical construct is at `mrh-tensors.md:352` and `mcp-protocol.md:798`. Also fenced by
  the standing C204/C242 guard on the LCT §1.2 charge. (The *bootstrap* consequence of the
  same filter survives, relocated onto #579's survey — that is N2, and it is INFO.)
- **Guarded, not re-opened:** Effector/W4IP-vocab CLEAN-BY-LAYER (C204 + C242 — no commit
  registered Dictionary as an Effector, no edit to §8.1/§11.2); LCT §1.2 `0.95`
  witness-trigger; B9 anchored at atp-adp §2.4; C17-H2 custom-role path.

---

## §D — Routing (routes, never applies)

### D.1 To the operator memo — cadence datapoint (policy review change 3)

**Proposal: move `dictionary-entities.md` from fixed-order rotation to event-triggered
delta** — firing when a commit (a) edits the spec, (b) names it, or (c) lands a proposal
aimed at it. **Evidence:** five consecutive fully-clean passes on a byte-frozen file
(C94 → C132 → C166 → C204 → C242), and this sixth pass's §A again yielded zero **by
construction from a blob hash**. Every finding this lineage has produced since C53 came from
the *window*, never from the file. An event trigger would have fired this pass anyway —
#579 and #580 are exactly condition (c) — at a fraction of the cost, and would have skipped
C132/C166/C204/C242's §A entirely.

Routed to the already-open **CADENCE DESIGN-Q** (fixed-order rotation vs. event-triggered,
opened at C270). **Not self-applied. Rotation order is unchanged this fire: C284 remains
SOCIETY_METABOLIC per the standing order.**

### D.2 To the operator memo — policy-review observation, carried verbatim

> "The C-series has consumed a large share of this track's exits while the flagship
> operator-gated item (B-D1 SSOT-inversion) remains UNANSWERED and the carry ledger grows
> faster than it retires. The rotation is producing genuine signal from windows, but it is
> also the only thing this track does. That is worth an operator decision independent of
> this fire."
> — policy reviewer, C282 scope review, 2026-07-29

### D.3 Carries unchanged

Operator DESIGN-Q C52-B9; C17-M1/H2/M4/M6; B26 (=B12/B13/B14 3-doc canonicity); C64-B7;
INFO B3d/B3c→C33 id-scheme, C158 `//`-fence; SDK bundle B15–B18/B24/B25 (stands verbatim —
mirror byte-frozen). **C280-N3 inbound, still open, CBP-owned.**

---

## §E — Guard for the next dictionary delta (~C322, or on event trigger)

- Target byte-frozen at `8e06a23c` since `95d20919`; SDK `edd97183` / `d8f71420`; sister doc
  `b28d8f9e`. If all four are unchanged, §A is a freeze proof — **do not re-derive the 9 C53
  findings a seventh time.**
- **N1 regression check (one grep):** did `select_best_dictionary`'s `.get(…, 1.0)` defaults
  change, and did #580 ratify? If #580 ratified and the SDK is unmoved, N1 escalates from
  survey-completeness to a live spec-vs-implementation conflict, and **C36-N5's remedy must
  be re-adjudicated with it, not separately.**
- **N2 regression check:** did #579 gain an "empty ≠ absent" affordance, or did §6 move?
- **Do not re-open** R-1 (C17-M1 ontology cluster, 74% corpus-wide) or R-2 (SPARQL FILTER
  idiom) as net-new. Do not re-open the Effector/W4IP or LCT §1.2 charges.
- **Do not re-gate `hub/` on this lineage** without new evidence — ruled NEGATIVE here on
  subject-matter grounds (I-2), not on token grounds.
- **I-1 false mirror** will re-appear to any `dictionar` grep over `web4-core/`. It is a
  metaphor. Do not acquire it.

---

## §F — Method lesson from this pass

**A negative gate and a positive finding came from opposite directions, and the *expected*
source produced neither.** The policy reviewer predicted the `hub/` gate would return
negative, and it did — that was the pass's stated primary goal and it cost little. The MED
finding came from the **oldest, most-read mirror in the lineage** (`dictionary.py`, examined
by six prior passes, byte-frozen for 47 days) — because a 4-day-old *principle* gave it a
lens no prior pass had. Method carry v7 says re-derive the mirror set; this pass adds the
converse: **a frozen mirror is not a read mirror.** Re-reading a known artifact under a new
normative lens is as productive as discovering an unknown one, and considerably cheaper.

Corollary for [[feedback_prose_is_not_ledger]]: N1 was reachable only by asking *"what does
this week's principle forbid?"* and then grepping the corpus for the forbidden **behaviour**
— not for the principle's **vocabulary**. A vocabulary grep (`unmeasured`) returned zero and
would have closed the question as "not applicable." The zero *was* the finding.

**Second lesson, added under review — the number and the derivation were not held to the same
standard.** §B.2's `hub/` cell originally published *"0 hits … for the whole subject-matter
cluster."* Measured, the cluster is **27**. The verdict was never wrong — it rests on the §B.1
subject-matter derivation, written before the gate ran — but the *count* was asserted from a grep
run once, early, and not re-run as the cell was written around it. The cell then contradicted itself
two clauses later, in its own prose (*"Hub publishes … role vocabularies"*), which is the tell.

Three compounding failures, all in one cell: (1) the zero was doing gate-work the derivation already
does better, under a method that is explicitly derivation-based; (2) the scope descriptor said
"35 files" — that is `.rs` **+** `.toml`, while the instrument only ever read `.rs` (31), so the
counts were published against a denominator the grep never used; (3) no instrument was published
beside the number, and the case-sensitivity of the grep moves `semantic` between 13 and 15.

**The rule this pass earns: publish the instrument next to the number, and re-run it *after* the
finding is written, not before.** §B′ of this same document already does exactly that for its
`.get(…, 1.0)` scope — the document held itself to a standard in one section that it did not carry
into another. The cost is not cosmetic: §E issues a forward ruling (*"do not re-gate `hub/` on this
lineage"*), and a future auditor cites the **cell**, not this thread — they would have re-grepped,
found 27, and read a correct ruling as contradicted.

The same sweep found the adjacent `web4-policy/` / `web4-trust-core/` row carrying an unqualified
*"0 hits each"* — true of `dictionar`, but those crates hold 13 and 11 wider-cluster hits
respectively. It was disambiguated in the same pass rather than left as the next instance of this,
and its NEGATIVE likewise rests on subject matter. **Every published zero should name the token it
is a zero of.**

---

*C282 — 2 net-new findings (1 MED, 1 INFO), 2 INFO records, 2 candidates refuted, zero
mutation of `web4-standard/`. Sixth consecutive pass with the target byte-frozen; first pass
on this lineage to route a MEDIUM.*
