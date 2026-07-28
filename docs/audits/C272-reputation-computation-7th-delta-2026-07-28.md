# C272 — reputation-computation.md 7th Delta Re-Audit

**Date**: 2026-07-28 (00:00 slot `web4-20260728-000011`)
**Target**: `web4-standard/core-spec/reputation-computation.md` (blob `bfdac3ba`, 870 lines, at HEAD)
**Lineage**: C15 → C44/C45 → C84/C85 → C123/C124 → C156/C157 → C194/C195 → C232 → **C272**
**Method**: v2 protocol; delta re-audit of a byte-frozen target, refute-by-default, all
citations re-derived at live HEAD.

---

## Headline

The target is **byte-frozen since `2bc3bafb` (#541)** — the same blob C232 audited. Per the
method carry born at C268 and generalized at C270, the yield on a frozen file is in **what
landed in the window claiming authority over the target's subject matter**. This window
supplies the carry's **third variant**, and the sharpest one yet:

> **An operator-authored artifact answered a DESIGN-Q that this file's own ledger has held
> open for 27 days, and the answer was never routed back to the question.**

`web4-standard/proposals/resilience-to-incomplete-information.md` (#580, `954ee391`, dp's
direction, 2026-07-25) states: **"Defaults resolve conservatively with respect to capability.
Absence NEVER grants."** Reputation §4 `:290-301` ratifies the opposite as an implementation's
free choice: an unrecognized `trigger_conditions` key is **ignored**, the rule fires anyway,
and treating it as fail-closed is "a stricter local choice … **not currently required** for
conformance." For a Success Rule that is *unearned positive trust produced by the
implementation's inability to evaluate a constraint the Law Oracle wrote*.

That collision is **C272-N1 (MEDIUM)**. Its authority is **prospective** — #580 is a proposal,
not ratified law, so it cannot render a verdict against a ratified spec the way the ratified
LCT §1.2 principle did at C268. What it *can* do, and what this audit routes, is that **#580's
own "already canon in two places" survey is incomplete in the direction that matters**: it
enumerates where its principle already holds and never enumerates where the ratified corpus
explicitly holds the opposite. A parent principle ratified without its counter-examples named
has no migration path for them.

Two prior-audit candidates were **refuted by my own checks** (§B.3): the method-carry-v3
enforcement-mechanism grep, which killed a would-be finding, and a witness-side charge.

**§A: 0 regressions, all carries HELD.** **§B: 1 net-new MEDIUM, routed, zero mutation.**
**C273 disposition: NO remediation owed** — C272-N1 is not this file's to apply.

---

## §A — Regression Verification (all HELD; 3 recorded paths corrected at live HEAD)

**Owed-set reconciliation (policy-review condition 1).** The reviewer asserted C194-N4 is
unattested in C232 and that C194-N2/N6 are the live items instead. **The reviewer's premise is
wrong**: C232 attests C194-N3/N4 twice (`:124` "§7 Talent-decay … → C194-N3/N4", `:151`
standing-carry list), and C194-N2/N6 are *closed* (remediated by #526, verified at C232). The
proposed owed set was correct as written. Recorded because a mis-derived owed set is the
[[feedback_prose_is_not_ledger]] failure mode and the correction belongs in the ledger, not in
this session's prose.

| Carry | Live-HEAD result |
|---|---|
| **C194-N1** (HIGH, SDK) — Rust `ReputationDelta` wire shape | **STANDS** — `web4-core/src/r6.rs:257-266+` unchanged; struct still carries `sovereign_strength` + the divergent field set. Mirror byte-frozen (`3f941988`, 07-09). |
| **C194-N3/N4** (operator DESIGN-Q) — §7 Talent-decay layer split + 10× rate divergence | **STAND** — target §7 untouched; `t3-v3-tensors.md` frozen since `d89595e8` (07-16, pre-C232). Neither side moved; adjudication unchanged. |
| **C194-N5** (W4IP-N5) — bad-faith-emergency lacks the disclaimer its sibling carries | **HELD** — re-read `:367-371`: the bad-faith bullet still carries no unratified-dependency disclaimer, while boundary intrusion at `:363-366` still does ("its adjudication protocol is proposed separately"). Asymmetry intact. |
| **C194-N7** (SDK) — `r6.py to_jsonld()` truthiness-drops Required:Yes fields | **HELD** — `r6.py:649 if self.rule_triggered:` still gates emission. Frozen `766611ef`. |
| **C194-N8** (SDK) — wasm hardcodes empty factors | **HELD** — `web4-trust-core/src/bindings/wasm.rs:848` still `…, reason, vec![])`. |
| **C156-3** (spec + Python-SDK owners) — Rust `sovereign_strength` ahead of both | **STANDS** — gate re-run: `grep -rn sovereign_strength web4-standard/` = **0**. **Path corrected**: the hub fold cited at `state.rs:615` is now `state.rs:788`; emit sites `rest.rs:3054`/`:3170`. (My memory's shorthand "r6.rs-only" was lossy — C156-3's own text already cited the hub emit sites. The audit was right; the memory line was not.) |
| **C156-4** (hub track) — temporal fold is code-triggered, not Law-Oracle-rule-triggered | **HELD, and re-derived after a ~1.1k-line in-window `rest.rs` delta.** `temporal_delta` now at `rest.rs:3014` (was `:3020`), callsite `:3570` (was `:3020-3057`). Decisive re-check: `grep -n temporal hub/hub-lib/src/law.rs` = **0** — still no temporal law section. Carry unchanged. |
| **carry-C46** — `role_pairing_in_mrh` denormalized convenience | **STANDS** — `:26` and `:72` byte-identical; absent from both SDK deltas. |
| **C232-N1** (LOW, 2-referent) — `reputation.delta.category` has no producer-side field | **STANDS, unbridged.** §1 field table `:68-84` re-read: 15 fields, no `category`; `grep coercive_extractive` in target = 0. Consumers re-derived: `web4-policy/src/lib.rs` (`:135/:359/:869-881/:909-953`), `hub-law-schema.md:240/:292`, **and `hub/hub-lib/src/law.rs:471`** — the last not cited by C232, but same commit `cb788768` (#525, 07-15), so **not net-new**, an additional referent only. |
| C194-N2 / C194-N6 | **remain CLOSED** (#526); C214-N1 application remains VERIFIED; C154-N1 remains consumed; C192-N1 remains closed. |

### §B′ — genuine-mirror gate, re-derived at live HEAD

Delta-shape mirrors (compute or carry a `ReputationDelta`): `reputation.py` `759eaefa`,
`r6.py` `766611ef`, `r6.rs` `3f941988`, `wasm.rs` `3f941988` — **all four byte-frozen since
C194**, so every C194 SDK carry stands by construction. `web4-policy` is a **CONSUMER, not a
mirror** (guard held: it selects over `reputation.delta.category`, computes no delta); its last
commit is `cb788768` (07-15), **pre-C232** — no in-window movement. Hub is an emitter/consumer.

**Policy-review condition 5** (in-window CI commits): `1fa86e09` refreshes `web4-policy`'s
Cargo.lock; `206dd004` arms `cargo test --locked` over the four crate roots (pre-arming counts
recorded: web4-policy 10, web4-core 193+4, web4-trust-core 49+3, hub 81+196+3). Neither touches
a mirror's *content*. Effect on this file: the Rust crates carrying C194-N1's divergent shape
are now CI-executed, which makes N1's semver-sensitivity **more** actionable, not less. No new
finding; recorded as a status change on N1.

**§A verdict: 0 regressions, 0 carries closed, 0 carries invalidated; 3 recorded paths drifted
and are corrected above.**

---

## §B — Net-New Finding

### C272-N1 (MEDIUM, prospective authority — route to #580's author + operator; do NOT self-apply) — #580's "Absence NEVER grants" collides with reputation §4's ratified fail-open delegation, and #580 does not name it

**Provenance (net-new, in-window).** `web4-standard/proposals/resilience-to-incomplete-information.md`
landed `954ee391` (2026-07-27, authored by CBP on dp's direction, dated 2026-07-25). It is
explicitly a **parent principle** ("`dictionary-as-context-mandatory-role.md` (#579) is an
*instance* of this") and it surveys where its principle is already canon. No prior audit could
have seen it; C232 predates it by 7 days.

**The two texts.**

- **#580, §"The sharp edge: resilience MUST NOT become privilege escalation":**
  *"Defaults resolve conservatively with respect to capability. **Absence NEVER grants.**
  Missing evidence → *less* trust, never assumed trust."* And: *"'unmeasurable' resolves to
  UNKNOWN, never to a favourable value … **absence is represented, not imputed**."*
- **Target §4 `:290-301`:** *"The reference SDK (`reputation.py` `ReputationRule.matches()`)
  evaluates only the recognized conditions above and **ignores** any it does not recognize
  (**fail-open**): a rule matches when all recognized conditions pass, regardless of extra
  keys. An implementation MAY instead treat an unrecognized condition as fail-closed; this is a
  stricter local choice and is **not currently required** for conformance."*
  Verified in the reference implementation: `reputation.py matches()` `:90-115` reads exactly
  four keys and falls through to unconditional `return True` at `:115`.

`trigger_conditions` is a **conjunctive narrowing** set (`:285-286`: "a rule matches only when
**all** stated conditions hold"). Ignoring an unrecognized conjunct therefore *widens* the
rule's match set. On a **Success Rule** (`:305-311`, e.g. `training +0.01`, `veracity +0.02`)
the outcome is a positive delta the Law Oracle's own rule text was written to withhold. That is
absence granting — the precise failure #580 exists to close. C123 saw the mechanism ("under
fail-open, a rule carrying a typo'd or unknown condition still fires") and rated it a *mild*
security property; #580 is the corpus deciding it is not mild.

**Why this is more than a restatement of the standing DESIGN-Q.** The "NEW-1-SDK-face" carry
(*should `matches()` be tightened to fail-closed? — operator decision*) has been open since
**C123, 2026-07-01**, and is recorded STANDS at C156 (`:59`), C194 and C232. It has been framed
as a **binary** for 27 days. #580 supplies a **third option neither branch offers**: *absence is
represented, not imputed* — the unevaluated condition is neither silently satisfied (fail-open)
nor silently unsatisfied (fail-closed), but **recorded**. Applied here that means §1's
`ReputationDelta` would carry the fact that a condition went unevaluated. It does not: the field
table `:68-84` has 15 fields and no such field, so a fail-open match is **indistinguishable
downstream from a clean match**. That is the second half of the finding, and it is what couples
this to the in-window `README.md` worked example (`5df662a5`, dp-directed): *"equipping the
relying party with the evidence to compute trust in context, rather than the originating
party's declaration"*. A delta that does not represent its own evidentiary gap hands the relying
party a declaration.

**Authority is prospective, and this is stated as a limit, not a hedge.** #580's status line
reads *"proposal, for fleet review."* It therefore does **not** make §4 defective today; §4 is a
ratified delegation and §4 is internally honest about being one (C124 earned that honesty by
converging the spec to the SDK rather than elaborating past it — see C123-NEW-1). The defect
this audit charges is in the **proposal**: a parent principle that surveys its own precedents
("already canon in two places") and omits the ratified counter-example will be ratified without
a migration path for it. That omission is cheap to fix now and expensive after ratification.

**Governance-tier check (policy-review condition 4), and what it changed.** §4 explicitly
delegates: fail-closed is "a stricter **local** choice." Under a tier reading the spec is
*correct as written* — it delegates a choice. This **did not kill the finding; it relocated
it**: the charge is not "the spec picked wrong" but "the corpus delegates a choice one branch of
which #580 forbids outright." Recorded because the C270 v3 lesson is that the tier check must be
run *before* calling a mismatch a defect, and here it changed the finding's wording and owner.

**Sign asymmetry (stated so the fix is not written one-directional).** Fail-open is unsafe in
one direction and over-strict in the other: on a **Violation/Failure** rule (`:313+`) the same
mechanism fires a *penalty* the oracle's rule text withheld. "Absence never grants" resolves the
positive case cleanly; the negative case needs its own sentence. Any remediation that only
flips a boolean will get one of the two directions wrong.

**Route (do NOT self-apply — design content, cross-track, unratified dependency):**
- **referent A — #580's author (CBP) + operator:** add reputation §4 `:290-301` to the
  proposal's precedent survey as its **counter-example**, and state which of {conform §4 to
  "absence never grants", carve §4 out, represent-the-gap} ratification implies. #579's
  Dictionary-published materiality statement is the natural carrier for "which trigger
  conditions are material," which is the same question in #580's vocabulary.
- **referent B — the standing NEW-1-SDK-face DESIGN-Q holder (operator memo):** the question is
  no longer binary; record the third option before answering it.

### §B.2 — INFO ledger

- **INFO-1 (carry received cross-track, no action).** `docs/strategy/hub-position-review-and-plan-2026-07-28.md:51`
  names **C232-N1** by ID as "named and open" — the seam reached the hub track's planning
  surface without this rotation routing it. First observed instance of a C-series carry being
  picked up by a non-audit track under its own identifier. Corroborates the carry; changes
  nothing about it.
- **INFO-2 (corroboration, explicitly NOT charged).** The in-window `README.md` worked example
  records, as *measured* fleet evidence, *"reputation is writable by third parties — 22 denials
  accrued to a well-behaved member for acts it never performed; a human, not the system,
  noticed."* The target's §1 `witnesses` field is `Required: No` (`:81`) and §6 opens "Reputation
  changes **should** be witnessed." The shapes rhyme. **Not charged as a defect**: §6's
  `select_reputation_witnesses` machinery exists (`:607-633`), `witnesses_required` was verified
  a real, consumed §4 field at C194 (`:53`), and the README attributes the failure to
  declaration-based trust in a sibling system, not to this spec. Recorded so the next delta can
  test it against a *ratified* obligation rather than an anecdote.

### §B.3 — Self-refuted candidates (2 killed by my own checks)

Per [[feedback_refute_your_best_finding]] and the policy reviewer's padding warning.

- **Candidate (would have been MEDIUM): "the target names conformance vectors as its
  authority (`:485`, `:593`) and nothing consumes them" — the C270-N2 shape, transplanted.**
  **REFUTED.** The method-carry-v3 grep was run and came back *positive*:
  `web4-standard/implementation/sdk/tests/test_reputation.py:661-672` loads
  `test-vectors/reputation/reputation-operations.json` and asserts **rep-001 through rep-005**
  by id (`:674`, `:723`, `:735`, `:767`, `:792`). Unlike t3-v3 §10.2, the target makes **no
  cross-language enforcement claim** — `:485` says the pseudocode matches "the conformance
  vectors" (true) and `:593` uses `rep-001` only as a deliberately-contrasted baseline. There is
  no Rust reputation-vector harness, but the spec never claims one, so **no defect**. C270-N2
  stays t3-v3-scoped; it is **not** a corpus-wide finding and must not be batched as one.
- **Candidate: "§4 fail-open is what #580's own table endorses — *'present but malformed →
  treat as unrecognized, not invalid'*."** This is the strongest attack on C272-N1 and it
  **fails**, but it sharpened the finding. #580 separates two obligations: do not *reject* on
  form (unknown ≠ malformed), and do not *grant* on absence. Fail-open satisfies the first by
  violating the second — it converts "I cannot evaluate this constraint" into "this constraint
  is satisfied." #580 does not pick fail-closed either; it rejects the binary. That refutation
  is what produced the third-option half of N1 above.

**Also tested and clean:** #579 (dictionary-as-context-mandatory-role) does not reach this file
— no reputation cross-ref, and its Dictionary-publishes-materiality step is upstream of rule
matching. The whitepaper §11 corrections (`b2e28887`, `ad6e35cd`, `77fe3d7c`) and the hub delta
(`5c2dd39f` #578 notice-drop alarm; rate_limit/constellation/store) are DISJOINT from the
target's surface. No redefinition of a protected term was charged, so no glossary check applied.

---

## §C — Carry Ledger (post-C272)

**Consumed/closed this audit**: none. (C194-N2/N6 remain closed; C214-N1 remains verified;
C154-N1 remains consumed; C192-N1 remains closed.)

**New outbound route — TWO named referents, both recorded so neither drops into prose:**
- **C272-N1 → referent A: #580's author (CBP) + operator** — name reputation §4 `:290-301` in
  the proposal's precedent survey as its counter-example; state what ratification implies for it.
- **C272-N1 → referent B: operator DESIGN-Q memo (NEW-1-SDK-face)** — the fail-open/fail-closed
  question is no longer binary; record #580's represent-the-gap third option before answering,
  and note the Violation-rule sign asymmetry.

**Standing carries re-verified and unchanged**: C194-N1 (HIGH, SDK wire shape — now
CI-executed, see §B′), C194-N3/N4 (operator DESIGN-Q, §7 decay), C194-N5 (W4IP-N5), C194-N7,
C194-N8; C156-3 (`sovereign_strength`; hub path 615→788), C156-4 (temporal fold; path
3020→3014, still law-ungated), carry-C46; **C232-N1** (unbridged, +1 referent `law.rs:471`).

**C273 disposition: NO remediation owed** — the target is substantive-clean and C272-N1 is not
this file's to apply.

**Rotation** → next fire = **acp = C274** (fixed round-robin; reputation followed by acp).

---

*Audit instrument: the C268/C270 method carry fired a **third consecutive time**, in a third
variant — after a canonized principle (C268) and an operator ruling on an implementation
(C270), now an **operator-authored proposal that answers a DESIGN-Q the file's own ledger had
been holding open for 27 days**. Three fires running, the frozen target has been the least
informative artifact in its own audit. The subtractive half matters as much: the v3
enforcement-mechanism grep was run and came back positive, killing a MEDIUM that would have
transplanted C270-N2 onto a file that never made the claim.*
