# C410 — `inter-society-protocol.md`, 10th delta

**Date**: 2026-08-19 · **Track**: legion/web4 · **Slot**: `web4-20260819-000000`
**Target**: `web4-standard/core-spec/inter-society-protocol.md` (384 L, blob `22bf6c1d`)
**Predecessor**: C370 (PR #696, `ca917da1`, 2026-08-12) · **Next ISP delta**: C450
**Mutation**: ZERO. This pass edits no spec, no code, no test, no vector.

---

## §A — Window and target state (COLLAPSED per the C344/C346 precedent)

Pre-registered before any measurement (**v26**): span `ca917da1..HEAD`, root = repo, all
filetypes, no glob restriction.

| Cell | Value | Command |
|---|---|---|
| Commits in window | **32** | `git log --oneline ca917da1..HEAD \| wc -l` |
| …in `web4-standard/` | **0** | `git log --oneline ca917da1..HEAD -- web4-standard/ \| wc -l` |
| …in `sdk/` | **0** | `git log --oneline ca917da1..HEAD -- sdk/ \| wc -l` |
| …in `hub/` | **11** | `git log --oneline ca917da1..HEAD -- hub/ \| wc -l` |
| Target commits in window | **0** | `git log --oneline ca917da1..HEAD -- web4-standard/core-spec/inter-society-protocol.md \| wc -l` |
| Target blob | `22bf6c1d` | `git rev-parse HEAD:web4-standard/core-spec/inter-society-protocol.md` |
| Target last moved | `0405f331`, 2026-06-16 | `git log -1 --format='%H %ci' -- <target>` |

**Target byte-frozen 64 days — 5th consecutive frozen delta. 13th consecutive empty window.**
Per the C370 guard, §A is collapsed to the blob table: C330 verified all 11 C63 anchors by
content and C370 published the 20-claim outbound cross-reference resolution as a NEGATIVE. On an
unchanged blob neither is re-run. Lineage = **11 docs** (inclusive rule, origin `# C6:`).

The pass was therefore spent entirely on C370's **pre-registered 5-row deferral row** (**v25**)
and on the residue. Every row is dispositioned in §C.

---

## §B — Findings

### N1 (LOW-MED → SDK track) — `validate_minimum_viable` is the one membership site in either language that reads the bare filler field, so a society using the committee/federation pattern the same module provides is told it has fewer than 2 role-filling entities while 4 entities are authorized to act in its roles

**Loci**: `web4-standard/implementation/sdk/web4/role.py:382` · `web4-core/src/society.rs:232`
**Hook**: ISP §6.2 (`:330-334`) — the sole normative source both implementations cite.

`RoleAssignment` models a role as a **holder set**, not a single entity. `additional_holders`
(`role.py:178`) exists, is documented as "committee/federation pattern" (`:200`), is written by
`add_holder` (`:199`), flips `multi_holder` (`:212`), is serialized both ways (`:259`, `:284`),
and is read by the module's two accessors for the question "who may act in this role":

- `is_authorized` (`role.py:233`) — `primary OR entity in additional_holders`
- `all_holders` (`role.py:236-238`) — `[primary] + additional_holders`

`validate_minimum_viable` answers the same question with `{ra.filling_entity_lct_id for ra in
roles}` (`:382`) — the bare field, `additional_holders` never consulted.

**Executed.** Fixture is `society-roles.md:356`'s own worked example — "a multinational
corporation's Treasurer might be a federation of regional Finance Societies (US-Finance,
EU-Finance, APAC-Finance)":

```
entities AUTHORIZED to act in a role (module's own all_holders): 4 ['apac-finance','eu-finance','founder','us-finance']
entities counted by validate_minimum_viable (bare field)      : 1 ['founder']
is_authorized('eu-finance') on Treasurer? -> True
multi_holder flag on Treasurer?           -> True
validate_minimum_viable(..., is_operational=True) ->
   - Minimum viable society requires at least 2 distinct role-filling entities
```

The error string is **false about its own input**: it names a quantity ("distinct role-filling
entities") that the module computes as 4 through its own accessor and as 1 inside the check.

**Denominator, and why this is not a base rate (v40/v46/v68).** The predicate is *sites that
answer "which entities hold/act-in this role"*. Every such site in both languages is
holder-aware except this one:

| Site | Holder-aware? |
|---|---|
| `role.py:233` `is_authorized` / `role.rs:367` | yes |
| `role.py:236` `all_holders` / `role.rs:360` | yes |
| `role.rs:355` `holder_count` (`1 + additional_holders.len()`) | yes |
| `role.py:199` `add_holder` / `role.rs:304` | yes |
| `role.rs:343` `set_threshold` — M-of-N quorum `n` | yes |
| `role.rs:377-379` signer check | yes |
| `society.rs:203` `has_role_authority` | yes |
| **`role.py:382` / `society.rs:232` `validate_minimum_viable`** | **no** |

**1 of 8.** Sharpest form: Rust defines `holder_count()` — precisely the quantity the check
needed — in the same crate, and `society.rs:232` maps `.filling_entity_lct_id` instead.

**Two languages, ONE derivation event (v69).** `role.py:354` states "Cross-language parity with
``web4-core/src/society.rs::validate_minimum_viable()``". Python was derived from Rust; they are
not two independent confirmations. `web4-trust-core/src/bindings/wasm.rs:602` is a **binding**
(`self.inner.validate_minimum_viable()`), not a third implementation.

**Disclosure polarity (v45/v57).** The docstring (`role.py:348-351`) discloses that §6.2 item 3
(ATP reification) is out of scope. It says nothing about `additional_holders`. The disclosure
protects "we do not check ATP"; it does not protect "we undercount holders" — and per **v57** the
same sentence affirms items 1 and 2 as in-scope.

**Why the guards cannot see it.** `TestValidateMinimumViable` (`test_role.py:511-620`) = **12
tests**; `add_holder`/`multi_holder` are tested at `test_role.py:225-304`. The two are **never
combined** — `grep -n add_holder` returns no hit inside `511-620`. Cross-language conformance:
`testing/conformance/society-roles.json` `minimum_viable_vectors` = **2 vectors**, both
`expected.valid: false` (`mvs-001` single-filler, `mvs-002` missing base-mandatory), neither
multi-holder.

**Severity LOW-MED, argued down from MED.** It fails **closed** — a viable federation is
rejected; nothing is wrongly admitted. **v45 caller census: 0 internal callers**
(`git grep validate_minimum_viable` = tests, `__all__`, docs only). ISP §6.3 (`:342`) is explicit
that these criteria are "GUIDANCE, not protocol enforcement", and `SOCIETY_SPECIFICATION.md:62`
calls the check *voluntary*. It is not INFO because it reaches **3 published export surfaces**
(`web4/__init__.py:830`, `wasm.rs:601` `validateMinimumViable`, `pkg/web4_trust_core.d.ts:315`)
and because the emitted string misstates its own input.

**Residual risk, stated rather than left for the next pass.** The strongest defense is that
"role-*filling* entity" means the primary filler *by definition* and `additional_holders` are
supplementary. The answer is the module's own: `is_authorized`/`all_holders`/`holder_count` treat
additional holders as entities that act in the role, `role.rs:343` counts them in the M-of-N
quorum denominator, and `society-roles.md:356` describes a role **filled by** a federation.
`society-roles.md:51` also puts the entity-count axis out of bounds — "The roles must exist; how
many entities fill them is per-society scale."

**Direction test.** ISP §6.2 authored `17d64712` (2026-05-13 22:19); the SDK export landed
`7f6c38aa` (2026-05-14 12:03) — the implementation postdates the spec by ~14 h, so this is not a
spec-drifted-away case. `role.py` frozen at `d155b6a6` since 2026-05-15 (**96 d**).

**Route**: SDK track. **Not ISP-side** — no spec change is implied; ISP §6.2 is not at fault.

---

### N2 (INFO, nothing charged) — a core-spec sentence about SDK coverage that no audit has ever read

`SOCIETY_SPECIFICATION.md:62` asserts "The SDK's `validate_minimum_viable` is a *voluntary*
conformance check covering the role-structural side of those criteria." This is the only place
in `web4-standard/core-spec/` that makes a coverage claim about a named SDK symbol.
`grep -rn "validate_minimum_viable" docs/audits/` shows no pass has cited `:62`.

**Not charged.** Read whole, the sentence hedges four ways — GUIDANCE, "not protocol-enforced",
*voluntary*, "viability is discovered socially through first-contact outcomes" — and `:60` three
lines up blesses a solo founder filling all seven roles. Quoting the 14 words "covering the
role-structural side" as a severity multiplier would be a clause-scoped misreading; this pass
drafted exactly that and withdrew it (§F). Filed as INFO because it is adjacent to deferral
item 3 (`sdk/CHANGELOG.md` as a conformance-claim surface) and is now on the record as read.

---

## §C — Deferral row disposition (C370 pre-registered 5; **all 5 closed**)

**(1) The other F-rows; F8 (§4.1↔§7.4 headers) as the strongest SDK-locus candidate —
DISCHARGED BY ANOTHER LINEAGE, not by this pass.**
`C384-mcp-protocol-9th-delta-2026-08-14.md:312-343` (**five days ago**) ran exactly this check
and published it as its §C N-1: *"Answer: yes, and it is NEGATIVE for the single-hop case only."*
`\bagency_chain\b` = 3 occurrences, all in the spec (`:452`, `:484`, `:487`), 0 implementation
— confirmed independently here. C384's §D item 4 reads **"Do NOT re-charge … F8's single-hop
case."** C384 also disposed of the multi-hop half by folding it into standing **`B-AGENCY / L1`**
(`C126:60`, carried at `C86:107`, `C158:44`, `C196:45`, `C234:55`).

This is **opening-sequence step 4** firing as designed: C370 routed the item to its own next
pass, and the mcp lineage reached it first. Had this pass not probed the receiver's ledger before
measuring, it would have re-filed another lineage's work as net-new. **Reported, not claimed.**

**(2) `SUPERSEDED`-scope as a class — PARTIALLY discharged, re-deferred.**
C35 closed **9** rows SUPERSEDED (F1, F2, F3, F4, F5, F8, F12, F15, F16 — `C35:59` tally). C370
did F3/F4; C384 did F8. **F1, F2, F5, F12, F15, F16 remain unexamined.** Re-deferred to C450 with
the denominator now stated (was implicit "the other four" in C370; it is **six**).

**(3) `sdk/CHANGELOG.md` as a conformance-claim surface — PAID OUT → N1 + N2.**
Two of its claims cite ISP by name: `:53` (`bootstrap_society_roles()`, §2.1) and `:55-59`
(`validate_minimum_viable()`, §6.2, "Cross-language parity with Rust"). Following the second is
what produced N1. The surface is **not exhausted** — the enumeration of every `implements §X`
claim against current spec text (the C362 `dictionary.py:20` shape) was not completed; re-deferred.

**(4) ISP's 7 unlabeled fences / has a modality extractor appeared? — NEGATIVE.**
7 fences confirmed unchanged at `:62`, `:91`, `:139`, `:154`, `:166`, `:278`, `:301`
(`awk '/^```/{n++; if(n%2==1) print NR}'`). Extractor sweep over `.github/workflows/`,
`web4-standard/tools/`, `scripts/` for `RFC 2119|MUST` returns **0 files**. C370-N3's finding
(19/19 ISP MUST/SHALL fence-resident, and no corpus instrument has a fence-excluding domain)
is unchanged. Do not re-run on an unchanged blob.

**(5) `docs/what/specifications/FEDERATION_CONSENSUS_ATP_INTEGRATION.md` — READ. Nothing charged.**
756 L, dated **2025-12-01** — it *predates* ISP (2026-05-13) by five months, so it cannot be an
ISP implementer and is not a mirror. Header status: "Design document - implementation in
progress". Cited in 5 files; its only implementer, `archive/reference-implementations/
federation_consensus_atp.py`, was **archived** at `65cd5488` (2026-04-11, Sprint 32 T1 sprawl
archival), while `docs/reference/FEDERATION_DOCUMENTATION_GAPS.md:19` still marks it "✅ Complete"
and `docs/what/README.md:32` still indexes it live. Two name collisions with live specs, both
stale rather than contradictory: `:567` uses `atp_settlement` as a **string** (`== "COMMIT"`)
where mcp §7.4 makes it an object; `:153` carries `quality_threshold`, the key C392 charged in
the reputation lineage. **Neither is re-filed here** — a pre-ISP design doc whose implementer is
archived is a docs-index question, not an ISP conformance question. Closed; do not re-defer.

### Other negatives published so C450 does not re-run them

- **v36 set-difference residue** (domain word `minimum.viable|semantically viable|semantic
  viability`, 33 hits, minus the `inter-society-protocol` filename sweep, 24 hits): 21-path
  residue. Read. Two paths carried the yield —
  `web4-standard/testing/conformance/society-roles.json` (the 2 vectors in N1) and
  `web4-trust-core/src/bindings/wasm.rs` (established as a *binding*, which is what kept N1's
  derivation count honest). The rest are prose.
- **ISP's own rate-stability enumeration** `Fixed | Market-derived | Pegged` (`:142-145`) has
  **0 implementers** — 3 corpus hits, 2 in ISP itself, 1 in `mcp-protocol.md:666` (a *different*
  five-item list, about Treasurer strategy, not rate stability). **Not charged**: the fence is
  descriptive ("The exchange rate MAY be"), ISP has 0 RFC 2119 declarations (C370-N3), and a
  non-normative enumeration with no enforcer is corpus-idiomatic. Recorded so the absence is not
  re-discovered as a finding.
- **`atp:commit` / `atp:record`** (`:227`) — 0 implementers; explicitly `MAY` and "The protocol
  does not mandate the distinction". Not chargeable. Recorded.
- **`rubber-stamp` / `identical-twin`** — **1 corpus hit**, ISP `:333` itself, 0 implementers.
  This *is* §6.2 item 2's normative discriminator and it *is* unimplemented — but that is
  **`C62-B12`**, HELD (see §D). Recorded as evidence on the held row, **not charged**.

---

## §D — `C62-B12` — HELD, evidence added, NOT re-charged

This pass independently re-derived `C62-B12` **cold** and drafted it as a MED finding before the
prior-art check. It is the same row, verbatim in both cells:

> `C62:164` — "The SDK approximates item 1 as a distinct-entity/filler count and item 2 as mere
> presence of a Witness/Auditor role — dropping the authority-difference and independent-judgment
> discriminators. **Mitigant**: ISP §6.3 states explicitly these criteria are 'GUIDANCE, not
> protocol enforcement'…"

Chain: `C102:100` STANDS verbatim → `C174-N1` widened to Rust → `C212:115`/`C250:107` HELD →
`C330:490-503` **declined a re-file with a written rationale naming both cells** → `C370 §H`
"HELD by byte-freeze, do NOT re-derive". The per-file guard says **"HELD, do NOT re-open:
`C62-B12`"**. C330 wrote the warning for precisely this: *"Re-running that defense without naming
C62-B12 would have quietly reversed an adjudication."* Re-filing it as net-new at MED would
reverse it in the other direction.

**Contribution to the held row (evidence, not a charge — v60).** C330's disposition was a
**static read**; these arms are executed, which is the v68 upgrade:

| Arm | Configuration | Result |
|---|---|---|
| 2 | `bootstrap_society_roles()`, `is_operational=True` | 2 errors (differentiation + witnessing) |
| 3 | `society-roles.md`-style founder + 3 identical worker keypairs | differentiation check **passes** (4 fillers); fails on witnessing only |
| 4 | 7 base-mandatory + WITNESS under `founder`, + a 2nd entity on CITIZEN | `[]` — **viable**; item 2's independence discriminator never consulted |
| 5 | one entity, 8 authority-distinct roles | differentiation error — the check is entity-count, not authority |

**Correction to this pass's own draft, on the record**: arm 3 was first written up as returning
VIABLE. It does not — it returns the witnessing error, because `WITNESS`/`AUDITOR` are **not** in
`BASE_MANDATORY_ROLES` (`role.py:118-126`: sovereign, law_oracle, policy_entity, treasurer,
administrator, archivist, citizen). Flipping it to viable needs a WITNESS added. Stated because
the uncorrected cell was in the premise submitted to review.

**`RoleAssignment` cannot express item 2's disqualifier at all** — the spec's discriminator is
two distinct LCTs under **one controller**, and the dataclass has no controller or key field. So
item 2 is not merely unimplemented; it is unrepresentable in the current data model. New evidence
on the held row; it strengthens C62-B12's "route to SDK, no ISP-side fix" disposition.

---

## §E — Deferral row, pre-registered for C450 (do NOT backfill)

1. **The six unexamined C35 SUPERSEDED rows** — F1, F2, F5, F12, F15, F16. For each: did its
   remediation touch anything but `*.md`? F3/F4 done (C370), F8 done (C384). Denominator is
   **six**, stated, not "the others".
2. **Finish `sdk/CHANGELOG.md`** — enumerate every `implements §X` / `per <spec> §X` claim in the
   file and check each against current spec text (C362's `dictionary.py:20` shape). This pass
   followed 2 of them; the file has **12** section-citing lines (`grep -c "§"`).
3. **`bootstrap_society_roles()` vs ISP §2.1** — the *other* CHANGELOG claim (`:53`), untouched
   here. §2.1 is a 6-step SHALL sequence; the function emits role assignments only. Ask what the
   other 5 steps' implementers are before assuming an absence.
4. **Does anything consume `validate_minimum_viable`'s return value outside the SDK?** N1 measured
   0 *internal* callers but 3 export surfaces. The unasked question is whether `hestia`/`hub` (out
   of this tree) call `validateMinimumViable` through the wasm/npm boundary — a `C174-N1`-shaped
   question this pass could not answer from inside the repo.
5. **Do NOT re-run**: F8's single-hop case (C384 §D-4), deferral item 5 (closed above), the 7
   unlabeled fences, the ISP outbound cross-reference resolution, `C62-B12` as net-new.

---

## §F — Method

**DRAFTED HEADLINE KILLED — 19th consecutive.** The draft was *"the shipped implementer of §6.2
tests a predicate that inverts §6.2 on §6.2's own two worked examples"* at MED, with
`SOCIETY_SPECIFICATION.md:62` as a severity multiplier. Policy review killed it on **prior art**:
it is `C62-B12`, charged nine passes ago, adjudicated three times, and on the do-not-re-open list.
It also broke three supporting cells (arm 3's verdict, "8 tests" for 12, and the `:62` quote read
out of its hedges) and rejected the offered control — `attestation.rs`'s ≥3-distinct-birth-witness
check — as **mis-scoped under v68** *and* as itself sitting on the ISP guard's REFUTED /
do-not-re-file list. Submitting a **measured** premise rather than a plan is what made all of that
findable before it shipped.

**The carry (v70): re-deriving a row cold is evidence about the ledger, never a licence to
charge it.** v62 established that rediscovering your own charged row cold proves the ledger lost
it. The dual is sharper and this pass nearly failed it: **when a cold re-derivation lands on a row
the ledger did NOT lose — one that is indexed, HELD, and explicitly marked do-not-re-open — the
strength of the re-derivation is not evidence for the charge.** It felt like the strongest finding
of the pass precisely because it was re-derived from the artifacts with no memory of the
adjudication; that independence is what a *confirmation* is made of, and a confirmation of a held
row is worth an evidence line, not a finding. The check that separates the two costs one grep of
the target's own guard entry, and it must run **before** the write-up, not after — because a
drafted MED with executed arms creates its own momentum.

Two corollaries this pass paid for:
- **A control can be disqualified twice.** The `attestation.rs` control failed v68 (wrong
  predicate: birth-witness quorum, not role viability) *and* appeared on the target's REFUTED
  list. Check a control against the do-not-re-file list before offering it — an exonerating
  instrument can re-open a closed row just by being cited.
- **Quote the whole sentence or do not quote it.** `SOCIETY_SPECIFICATION.md:62` reads as a
  coverage claim in its 14-word middle and as a four-way hedge in full. A severity multiplier
  extracted from a clause is a manufactured multiplier.

And the step-4 result stands on its own: **deferral item 1 was discharged by the mcp lineage five
days before this pass reached it.** C370 pre-registered it, C384 answered it. Probing the
receiver's ledger before measuring cost one grep and saved a false net-new.

---

## §G — Guards carried to C450

- Target byte-frozen **64 d / 5 consecutive deltas** at blob `22bf6c1d`. Check the blob first; if
  unchanged, collapse §A to the table above and spend the pass on the deferral row. All 6 siblings
  unmoved since C330 ⇒ C212/C250 DISJOINT verdicts carry verbatim.
- **CADENCE**: 13th consecutive empty window (`web4-standard/` = 0). The target is a spent surface;
  four of the last five ISP yields came from the SDK/vector periphery, not the spec.
- **`C62-B12` is the trap on this file.** It is re-derivable cold from `role.py` + §6.2 in about
  twenty minutes and it feels net-new every time. Read the guard entry first.
- HELD / do-not-re-open unchanged: `C62-B12`, `C174-N1`, `C290-N1`, `C330-N1`, `C330-N2`.
  REFUTED / do-not-re-file unchanged, **and now includes** F8's single-hop case (C384 §D-4).
- Baselines: target `22bf6c1d`; `role.py` `d155b6a6` (2026-05-15, 96 d); `society.rs` +
  `role.rs` unmoved in window; `society-roles.json` 4 suites (2/4/1/2 vectors).
- **Standing routings unchanged**: `C374-N4` and `C390-N2` remain RE-ROUTED to acp `C434` (now 5
  passes old). Not this pass's to serve.
