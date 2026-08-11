# C360 — Ninth-Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-08-11
**Auditor**: Legion autonomous web4 track (slot `web4-20260811-060000`, v2 protocol)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (498 lines, blob `2ad453ba`)
**Lineage**: C22 (#251) → C50 (#317) → **C51 remediation** (`958a5625`/#318) → C92 → C131 → C164 → **C202** (`87377c38`/#522 §7.3 mover) → C240 → C280 (#586, added `hub/`) → C320 (#644) → **C360 (this, 9th)**
**Rotation**: fixed-order round-robin, `last-pass C# + 40` → C320 + 40 = C360.
**Staleness at audit**: **BYTE-FROZEN.** `git diff e4a62d7a HEAD -- <target>` is **empty**; blob `2ad453ba` unchanged. Last touching commit `87377c38` (2026-07-14, #522) — **28 days**.
**Window**: `e4a62d7a..HEAD` (the commit that landed C320 → HEAD). **53 commits**; **1** touches `web4-standard/` at all (`afd04623` — `errors.md`, `security-framework.md`, `submission/draft-web4-core-00.xml`); **0** touch the target, its SDK mirrors, its test vectors, or any §-cited sibling.
**Method**: v43 first — **the artifacts were executed against each other before anything was re-read**. Then v36 as a set difference on **artifact names and subject matter**, not the target's filename. Then §A freeze + full cross-reference re-resolution, §C carry re-verification, §D disposition. Every count publishes its instrument and its **denominator**; every novelty claim publishes its **matcher** (v44).

---

## Verdict (summary)

- **§A — CLEAN, and for the first time it is a *measured* clean.** Seventh consecutive delta requiring no correction to the target's bytes. **All 37 cross-reference sites in the file were resolved at HEAD; all 37 resolve exactly.** That negative is worth publishing because **7 of the 10 cited sibling files have moved since C92 last resolved them**, and only **4 of the 37** sites had been re-resolved since (C320's §7.3 four).
- **§B — the yield came from executing the implementer against the MUST the target points at.** **N1 (MED)**: `SOCIETY_SPECIFICATION.md:299` states a MUST — law changes *"MUST carry witness co-signatures per the society's Quorum Policy (SAL §5.4)"*. The canonical SDK records a law change with **zero** witnesses against a society whose own `QuorumPolicy` says `UNANIMOUS(2)` and whose own evaluator returns `False` for that count. `QuorumPolicy.check` has **zero production call sites in repo history**. **N2 (MED)**: two of the SDK's thirteen ledger-emission sites — the fractal incorporation pair — write `witnesses: []` from functions with **no `witnesses` parameter**; net-new. **N2b (LOW-MED)**: the economic pair does the same and is the surviving **implementer half of C50-B2**, whose spec half C51 fixed and C92 verified — on the spec side only. **N3 (MED)**: two open rows anchored *in this file* are held only in sibling lineages' ledgers, and C320's inbound check is falsified by the very document it names as re-read.
- **§C — 12/12 carries OPEN** (7 tracked + the 4 C320 restored + C320-N3), all re-resolved by content. **2 rows RECEIVED** from sibling lineages and typed here for the first time. **I-2**: C280-N1's citations have gone stale a **second** time — 5 of 8 in 6 days, against C320's 3 of 8 in 7 — on a memo that still has not reached an operator.
- **The window's `hub/` gate was walked and produced the pass's best corroboration**, after a draft cell published it as empty (own-error 1): hub `#670` shipped `is_known_law_action` — *"Is `action` a value the gate can ever actually see?"* — the **same reachability check N1 says the SDK lacks**, six days ago, ratified.
- **Net: 0 autonomous spec edits, 0 SDK edits. ZERO mutation.** C361 = declared NO-OP.

**Honest scoping note, up front.** N1 is a **conformance** finding against the SDK, not a defect in this file's bytes — the target's `:299` is correct and is the instrument that convicts. Its facts are **~79 days old** (`sdk/web4/` last moved 2026-05-24, `62524cf8`); they are net-new **as findings**, not as facts. And the module under charge disclaims part of the duty in its own docstring — recorded below as a **sustained partial refutation** that caps severity at MEDIUM rather than as a defeat.

---

## §A — Freeze Verification + Full Cross-Reference Re-Resolution

**Result: CLEAN.**

```
git rev-parse HEAD:web4-standard/core-spec/SOCIETY_SPECIFICATION.md → 2ad453ba…
git diff e4a62d7a HEAD -- <target>                                  → (empty)
git log -1 --date=short -- <target>  → 87377c38  2026-07-14  (#522)
```

C92's token-by-token verification of all 21 C51 findings and the `#`-regression sweep hold **by construction** on an unmoved blob. What does **not** hold by construction is the citation surface, and this is where every prior pass stopped short.

### A.1 — why the citation surface was re-run in full this pass

C320 re-resolved **four** citations — the §7.3 set — on the stated ground that §7.3 is *"the only methodologically-live section."* That is true about the **target**. It is not true about the **siblings**. Measured:

```
for f in <the 10 cited core-spec siblings>:  git rev-parse HEAD:$f  vs  <blob at 2026-06-25>
```

| sibling | blob at C92 (2026-06-24) | blob at HEAD | |
|---|---|---|---|
| `web4-society-authority-law.md` | `02ab3a42` | `0849ebbe` | **MOVED** |
| `society-roles.md` | `7b3f8a91` | `886942a2` | **MOVED** |
| `atp-adp-cycle.md` | `ea57769f` | `2d060579` | **MOVED** |
| `mcp-protocol.md` | `448a60e2` | `4491c1bb` | **MOVED** |
| `reputation-computation.md` | `8c12404d` | `bfdac3ba` | **MOVED** |
| `hub-law-schema.md` | `52968fb0` | `e2d632c1` | **MOVED** |
| `t3-v3-tensors.md` | `f5dcba0a` | `32d3368e` | **MOVED** |
| `inter-society-protocol.md` | `22bf6c1d` | `22bf6c1d` | same |
| `SOCIETY_METABOLIC_STATES.md` | `5e3f7203` | `5e3f7203` | same |
| `did-web4-method.md` | `0d2e4c53` | `0d2e4c53` | same |

**7 of 10 moved.** A frozen target's citations decay at the rate of the trees they point into, not at the rate of the target. So the full site set was enumerated and resolved.

### A.2 — the enumeration and the result

**Instrument, published:** `` `([A-Za-z0-9_./-]+\.md)`\s*(§[0-9][0-9.]*(?:[–-]§?[0-9][0-9.]*)?)? `` over the 498 lines, plus a second pass for the `\b(SAL|ISP)\s+§[0-9.]+` short forms the first regex cannot see. **Domain = 37 sites across 10 sibling files.** Section-number existence was checked by building a heading index per sibling; **content** was then resolved for every claim that asserts what the cited section *says*.

| target line | citation | resolved at HEAD | verdict |
|---|---|---|---|
| `:39` | SAL §3.4 stores Birth Certificates, role pairings, delegations, law dataset digests, witness attestations, auditor adjustments | SAL `:107` `### 3.4 Immutable Record (Ledger) — **MUST**`; `:109` carries the identical six-item list | **EXACT** |
| `:52` | `did-web4-method.md` | file resolves; blob unmoved | **EXACT** |
| `:53` | `t3-v3-tensors.md` | file resolves | **EXACT** |
| `:59` | SAL §3.1 requires an Authority Role LCT + a Quorum Policy | SAL `:70` `### 3.1 Society Topology` → *"An **Authority Role** LCT … A **Quorum Policy** (witness/attestation requirements per action type)"* | **EXACT** |
| `:59` | SAL §5.4 — Law Oracle defines the Quorum Policy | SAL `:195` `### 5.4 Witness` → *"Quorum policy defined by **Law Oracle**"* | **EXACT** |
| `:60`, `:83` | `society-roles.md` §2 — seven base-mandatory roles | `society-roles.md:49` `## 2. Base-Mandatory Roles`, subsections `2.1`–`2.7` = Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen | **EXACT, 7/7 by name** |
| `:62` | ISP §6.2 semantic viability = 3 criteria, GUIDANCE | ISP `:328` `### 6.2 Minimum Viable Semantic Society` → internal differentiation / witnessing capacity / externally-grounded reified resource | **EXACT** |
| `:62`, `:83` | ISP §6.3, ISP §3 | ISP `:336` `### 6.3 Implications`; `:119` `## 3. First-Contact Protocol` | **EXACT** |
| `:83` | ISP §2.1 solo-founder genesis | ISP `:58` `### 2.1 Self-Bootstrapped Genesis (Solo Founder)` | **EXACT** |
| `:37`, `:89`, `:319` | `SOCIETY_METABOLIC_STATES.md` | blob unmoved since C92 | **EXACT** |
| `:299` | SAL §3.4 `sal.law.update`; SAL §5.4 co-signature | SAL `:111` emits `sal.law.update`; SAL `:196` *"co-signed ledger entries for SAL-critical events"* | **EXACT** |
| `:317` | atp-adp §2.1 mint / §2.2 charge / §2.3 discharge / §2.4 slash | `:37` Minting (ADP Creation), `:69` Charging, `:124` Discharging, `:170` Slashing | **EXACT ×4** |
| `:347` | ISP §5.1–§5.2 | `:274` Secession Protocol, `:297` Federation Dissolution | **EXACT** |
| `:400` | `atp-adp-cycle.md` | file resolves | **EXACT** |
| `:408` | ISP §6.2 "minimum viable semantic society" | as above | **EXACT** |
| `:458` | `mcp-protocol.md` §7 as the inter-society interface | `mcp-protocol.md:297` `## 7. MCP-R6/R7 Integration and Cross-Society Bindings` | **EXACT** |
| `:462` | mcp §7.3 signed reputation objects; §7.5 propagation rules | `:370` §7.3 defines the signed `reputation` envelope (`:413` responding-society signature); `:490` `### 7.5 Cross-Society Witnessing and R7 Reputation Propagation` | **EXACT** |
| `:466`, `:469`, `:470`, `:474` | ISP §5, §5.2, §5, §5.1 | all resolve | **EXACT** |
| `:474` | `society-roles.md` §4.1 Mediator; context-mandatory per its §3 | Mediator at `society-roles.md:222`, inside `### 4.1 Trust / Accountability` (`:206`); `## 3. Context-Mandatory Roles` (`:184`) table `:192` maps **Court / Arbitration-Service → Mediator, Auditor** | **EXACT** |
| `:477`, `:483`, `:494` | hub-law-schema response vocabulary; reputation-computation §4 + Coercive/Extractive; W4IP-DRAFT | `hub-law-schema.md:285`; `reputation-computation.md:239` `## 4. Reputation Rules`, `:339` `#### Coercive/Extractive Behavior Rules`; proposal path resolves | **EXACT** (re-confirms C320) |

**37 of 37 resolve exactly. Zero drift. Published as a negative** (v40) — an unexecuted citation surface across seven moved siblings was the most likely place for this pass's yield, and it was clean. Saying so is what makes the *positive* results below interpretable.

**§A conclusion: no regression** on the target or its citation surface.

---

## §B — Net-New Sweep (bounded, refute-by-default, ONE lens per candidate)

### §B-0 — the machine checks, run FIRST (v43)

Nine passes have argued about this file's ledger event canon. **Before this pass, no pass had run the canon.** What was executed, and against what:

| check | instrument | result |
|---|---|---|
| Do the target's fenced blocks parse? | 17 fenced blocks; 13 tagged `json`; `json.loads` each | **9/13 parse**; the 4 failures are all the `{...}` elision convention (`voting_record`, `original_data`, `new_data`, `voting_record`) — **not discarded** (C356's rule); checked and benign |
| Are the 8 metabolic state names consistent across the corpus? | target `:87` + `:325-326` vs `SOCIETY_METABOLIC_STATES.md` §2.1–§2.8 headings vs SDK `MetabolicState` | **8/8 agree, four artifacts** — negative, published |
| Does the SDK's ledger actually emit §4.2.1's canon? | drove `create_society` → all 13 emission sites, dumped every `(type, action, data-keys, witnesses)` | **13 event kinds emitted; see N1/N2** |
| Do the standard's own society vectors execute? | `pytest tests/test_society.py` | **86/86 green** |
| Does the SDK enforce the MUST at target `:299`? | executed | **NO — see N1** |

Nothing was written to the repo by any of these runs.

### §B-1 — **N1 (MED, spec-MUST vs canonical implementer → SDK track) — the Quorum Policy this file's operational minimum is built on is inert: `check` has never had a caller**

**The MUST, in this target's own bytes** (`:299`, ratified by the C51 remediation and verified accurate by C92):

> Law changes are SAL-critical events (`sal.law.update` per `web4-society-authority-law.md` §3.4) and **MUST carry witness co-signatures per the society's Quorum Policy** (SAL §5.4).

And `:59` makes the Quorum Policy part of the operational minimum, characterized per SAL §3.1 as *"the table of **witness/attestation requirements per action type** … it specifies which witnesses must co-sign which classes of ledger entry."*

**Executed against the canonical SDK** (throwaway script, run outside the repo tree; nothing written):

```
society quorum_policy: QuorumMode.UNANIMOUS   required = 2
qp.check(0) -> False                      # the evaluator knows 0 is not a quorum
record_law_change(state, law, "T1", witnesses=[], action="ratify")
RECORDED: law_change | ratify | witnesses = []      # no exception, no False
```

The society was configured by the SDK itself: `create_society` (`society.py:287`) defaults
`quorum_policy = QuorumPolicy(mode=QuorumMode.UNANIMOUS, required=len(founders))` at `:320-321` and
stores it at `:327`. The evaluator that would have refused is an attribute access away and is never
consulted.

**The evaluator has never had a caller. Instrument published:**

```
grep -rn "\.check(" --include=*.py web4-standard/implementation/sdk/web4/
  → federation.py:386   return norm.check(value)      # Norm.check (:288), a different class
grep -rn "QuorumPolicy|quorum_policy|witness_quorum" --include=*.py --include=*.rs --include=*.ts .
git log -S "quorum_policy.check" -- .                 → (empty, all history)
```

- `QuorumPolicy` is defined at `federation.py:170`; `check` at `:182-194`.
- Production references: `federation.py:520` (`self.quorum_policy = …`) and `:522`
  (`self.witness_quorum = self.quorum_policy.required`). **Both are stores. Neither is a read of the
  policy for a decision.** `witness_quorum` is read in exactly one place repo-wide —
  `test_federation.py:104`, annotated `# backward compat`.
- The only callers of `check` are the 9 assertions in `TestQuorumPolicy` (`test_federation.py:485`).
- `web4-core` (Rust) has no counterpart at all: `grep -rn -i quorum web4-core/src/` returns birth-witness
  and R6-constraint quorums only; `society.rs` carries the ISP §6.2 semantic-viability model, not a
  §4 ledger.

**The one witness gate the SDK does run is a different mechanism, and it reaches one act.**
`federation.py:574-577`, inside `issue_citizenship` (`:555`):

```python
proc = law.get_procedure("PROC-WITNESS-QUORUM")
if proc and len(witnesses) < proc.requires_witnesses:
    raise ValueError(f"Insufficient witnesses: need {proc.requires_witnesses}, got {len(witnesses)}")
```

**Stated precisely, because the obvious version of this claim is wrong.** The *field* `requires_witnesses`
**does** have a normative basis — SAL `:197` gives `requires_witnesses: 3` as the Law Oracle's example
form. What has **no** basis anywhere in `web4-standard/` is the **procedure id**: `grep -rn
"PROC-WITNESS-QUORUM"` over the whole repo returns **6 hits, all inside the SDK** (1 production site
+ 5 test sites) and **0** in the spec, in SAL, in `schemas/`, in `test-vectors/`, or in
`testing/conformance/`. So the SDK has split SAL's single concept in two: the object SAL §3.1 names
(`QuorumPolicy`) is inert, and the live gate is keyed to an unpublished magic string and fires only on
birth certificates — never on a law change, never on any of the thirteen ledger emissions.

**Reach — two independent documents in two different trees believe the inert object is live:**

| locus | claim | at HEAD |
|---|---|---|
| `SOCIETY_SPECIFICATION.md:299` | law changes MUST carry co-signatures **per the society's Quorum Policy** | no implementer consults it |
| `docs/designs/u2-multi-device-binding.md:277` | *"Device enrollment uses the society's `QuorumPolicy` for recovery quorum"* | `binding.py` references `QuorumPolicy` **0** times; it uses its own `recovery_quorum: int` (`:198`, `:232`, `:579`) |

**A wider reach-escalation was drafted here and is REFUTED — recorded because the refutation is what
gives N1 its correct shape.** The same inertness is measurable on the *other* two implementers:
`web4-policy/src/lib.rs:275/:277` declares `requires_witnesses: Option<u32>` and
`requires_quorum: Option<u32>`, and `grep -rn "\.requires_witnesses|\.requires_quorum" --include=*.rs .`
(whole repo, excluding `target/`) returns **0** — nothing in Rust ever *reads* either field;
`Law::validate` (`lib.rs:379`) walks `procedures` only to check id uniqueness. The hub ships
`requires_witnesses: 3` scoped to `consequential_actions` in its **operator-facing starter law**
(`hub/examples/starter-law.yaml:125`) and tells operators to *"Require independent witnesses or a
quorum for weighty acts"* (`hub/docs/HUB-LAW.md:253`).

**And that is not a defect, because it is disclosed at the point of use — three times.**
`starter-law.yaml:120-121`: *"Today the procedures are **descriptive** (the hub doesn't enforce them
directly); future sprints will gate acts on witness/quorum counts."* `hub-law-schema.md:44`:
*"Consequential-action procedures carry **the target the daemon enforces as gating lands**."* This is
the corpus's established phased-enactment convention, the same one `SOCIETY_SPECIFICATION.md:486-487`
(*"Enactment beyond the reversible rungs is phased"*, `:485-488`) applies to the kinetic verbs — *"kinetic verbs parse but remain law-inert until individually ratified
and implemented."* **Charging it would be charging the corpus for doing the honest thing.**

**The contrast is the finding.** The corpus has a working convention for shipping a parsed-but-inert
governance mechanism: declare the phasing where the mechanism is used. §7.3 does it. The hub does it
three times. **`:299` is the one site that does not** — it states an unqualified MUST — and the Python
SDK is the one implementer that presents an inert quorum as a live one: `create_society`'s own
docstring (`society.py:310`) reads *"quorum_policy: Witness quorum requirements (defaults to UNANIMOUS
among founders)"*, with no note that nothing will ever consult it. Two artifacts, one convention,
applied everywhere but here.

**Refutations attempted — four; one sustained as a cap, three refuted:**

- **R1 — "the module disclaims this: `society.py:18-19` says it provides *data structures and pure-function operations*; *persistence, networking, and consensus are out of scope*."** **SUSTAINED AS A PARTIAL, and it is why this is MEDIUM and not HIGH.** Gathering co-signatures is consensus and is fairly out of scope. But **evaluating `qp.check(len(witnesses), n)` is a pure function over data the caller has already supplied** — precisely the category the same docstring says the module *does* provide — and the SDK performs exactly this class of check 50 lines from the policy object (`federation.py:574-577`), and `allocate_treasury` already enforces two preconditions of its own (`accepts_transactions`, `is_citizen`). The disclaimer explains the gap; it does not make the MUST satisfied. **Routed as a DESIGN-Q, not self-resolved:** whether the SDK owes a spec MUST its own docstring disclaims is an operator/SDK-owner call.
- **R2 — "this is C50-B16(a), already restored at C320."** **REFUTED.** B16(a)'s predicate is *"the SDK never records §4.2.1's MUST minimum fields,"* measured as **0 of 5 payload tokens** (`law_reference`, `change_description`, `voting_record`, `effective_date`, `recipient_lct`) — re-verified 0/5 at HEAD this pass. `witnesses` is **not in that set**; it is an envelope field, it is present on the dataclass, and it is populated on 9 of 13 emissions. An absence-of-token instrument cannot reach a field that exists and is populated. Different predicate; B16(a) stays as it is.
- **R3 — "C326 already swept the quorum machinery clean."** **REFUTED — and C326 must be cited, because it is the exact complement.** `C326-society-authority-law-8th-delta-2026-08-06.md:291-292` executed the `sal-governance.json` quorum vectors against `QuorumPolicy.check` and got **PASS 6/6**, recorded as *"Swept CLEAN."* That admission licenses the predicate **"does the evaluator compute the right boolean"** and nothing more (v31/v41). C326's own §F (`:420-427`) records its auditor nearly filing *"federation.py has no quorum-check function,"* then correcting to *"`check` exists."* Both passes established that `check` is real and correct. **Neither asked whether anything calls it.** A unit that is green in isolation and has no caller is the sharpest form of *coverage is not execution* (v43): here the coverage was even a **vector** run, and it still could not see the system.
- **R4 — novelty (v44).** **CLEAN, matcher published.** Both audit trees (`docs/audits/`, `web4-standard/docs/audits/`), searched on the **domain's** vocabulary rather than paraphrases of the finding: `quorum_policy` **0**, `witness_quorum` **1** (C48, an unrelated R6 constraint-name DESIGN-Q), `PROC-WITNESS-QUORUM` **0**, `record_law_change` **0**, `deposit_treasury` **0**, `allocate_treasury` **0**, `co-signature`/`unwitnessed`/`no caller`/`inert` — no hit charging this predicate. `QuorumPolicy` returns 3 files: **C22:21** (a mirror-set listing), **C60:132** (see below), **C326:291** (R3). No prior art charges "the policy is never consulted."

**A note on our own strictness (v44.5 — run the strictest rule against your own lineage first).** The
first draft of this finding also charged `docs/audits/C60-…:132` as a false claim: *"Quorum IS
enforced elsewhere (`capability.py` L276, `federation.py` QuorumPolicy) — so this is a missing guard
at the genesis factory specifically."* **That charge does not survive.** `capability.py:276` is true
(`len(bc.birth_witnesses) >= 3`), and quorum **is** enforced in `federation.py` — at `:574-577`, on a
blob byte-identical on 2026-06-15 and today. C60's **conclusion is unaffected**; only the
parenthetical attribution to `QuorumPolicy` is misplaced. Charging it would have been strict-for-C60
and loose-for-us, since **N1 itself depends on `federation.py:574-577` to establish that the SDK does
gate witnesses somewhere**. It is folded in above as corroboration — two documents naming an inert
object — and filed as **I-1 (INFO)**, not as a finding.

**Disposition: routed to the SDK track + operator DESIGN-Q. No spec change requested** — `:299` is
correct and is the instrument that convicts. Fix *shape* only: consult `state.society.quorum_policy`
in `record_law_change` (and publish the `PROC-WITNESS-QUORUM` procedure id, or retire it in favour of
the typed object). **Not applied here** — `society.py`/`federation.py` are out of bounds for this slot.

### §B-2 — **N2 (MED, net-new) and N2b (LOW-MED, carry) — 4 of the SDK's 13 ledger emissions write `witnesses: []` from functions that expose no `witnesses` parameter**

**Denominator, with its domain rule** (v40): `grep -n "LedgerEntry(" society.py` → **14** sites; `:170`
is inside `amend()` and *copies* an existing entry rather than emitting a new one; **13 emission
sites**, which the drive script exercised exhaustively, producing **13 distinct `(type, action)`
kinds**. (An earlier draft published "4 of 12" by counting only the twelve literal-`action=` sites and
silently dropping `:689`, `record_law_change`'s parameterized site — which is the site N1 is about.)

| # | type / action | site | `data` keys emitted | `witnesses` |
|---|---|---|---|---|
| 1 | formation / genesis | `:338` | `founders`, `name` | 2 |
| 2 | formation / bootstrap | `:370` | `citizen_count`, `treasury` | 2 |
| 3 | formation / operational | `:383` | *(empty)* | 2 |
| 4 | citizenship / grant | `:459` | `entity_lct`, `rights`, `obligations` | 2 |
| 5 | citizenship / suspend | `:488` | `entity_lct`, `reason` | 2 |
| 6 | citizenship / reinstate | `:519` | `entity_lct` | 2 |
| 7 | citizenship / terminate | `:556` | `entity_lct`, `reason`, `atp_reclaimed` | 2 |
| 8 | metabolic / transition | `:594` | `from`, `to` | 2 |
| 9 | **economic / deposit** | `:620` | `amount`, `source`, `token_type` | **0** |
| 10 | **economic / allocate** | `:652` | `entity_lct`, `amount`, `purpose`, `token_type` | **0** |
| 11 | law_change / *(param)* | `:686` | `law_id`, `version`, `norm_count`, `procedure_count` | caller's — **unchecked (N1)** |
| 12 | **formation / incorporate_child** | `:790` | `child_society_id`, `child_name` | **0** |
| 13 | **formation / incorporated_by** | `:803` | `parent_society_id`, `parent_name` | **0** |

**Lead with the API shape, not the empty list.** `LedgerEntry.witnesses` defaults to `[]`, so the key
is never *absent*; the defect is that **no conformant caller can populate it**:

```
deposit_treasury  (society.py:610)  (state, amount, timestamp, source="")
allocate_treasury (society.py:630)  (state, entity_lct, amount, timestamp, purpose="")
incorporate_child (society.py:773)  (parent_state, child_state, timestamp)
```

Three public functions, four emissions, **no `witnesses` parameter on any of them** — against
`:39`'s categorical claim that *"Witnesses participate in **every** recorded event via the per-entry
`witnesses` field"* and against §4.2.1's envelope, which carries `witnesses` on all five canonical
blocks.

**The two halves are NOT the same row, and merging them would overstate the carry** (v31 —
a prior row licenses only what it charged):

- **N2b (LOW-MED) — the economic pair is the surviving implementer half of C50-B2.** `C50-…:96`
  charges exactly *"law_change (L270–277) and economic_event (L283–289)"* — the spec-side omission of
  `witnesses` + `timestamp` from those two blocks. C51 (`958a5625`) fixed it; `C92-…:39` verified
  **HELD** — and verified it **on the spec side only** (*"§4.2.1 blocks 2–3 now both carry `witnesses`
  + `timestamp` (L294–296, L312–314)"*). B2's own SAL sharpening — *"spec-conformant implementations
  ship unwitnessed law-change and treasury events"* — names the implementer and was never re-run.
  At HEAD the law-change half is satisfied **in shape** (the parameter exists; it fails only on
  enforcement, which is N1) and the **economic half is not satisfied at all**. This is the
  C332-N2 class verbatim: *a remediation applied to one file, re-verified four times by following the
  cross-reference the fix itself added, never looking at the artifact on the other side.*
  **Severity LOW-MED, not B2's HIGH**: B2's HIGH was assigned to a spec-internal contradiction that no
  longer exists, and SAL §5.4's SAL-critical list (birth, delegation, law updates, auditor
  adjustments) **does not cover treasury events** — so the economic pair has no SAL-conflict arm.
- **N2 (MED) — the fractal-incorporation pair is net-new.** C50-B2 never reached blocks 4–5;
  `C50-B5:108` records that those two blocks *already* carried the SDK envelope. So
  `incorporate_child` / `incorporated_by` are charged by no prior row, and they are the two emissions
  that record a **structural change to the society graph** — §3.2.1 inheritance and §3.2.2 recursive
  citizenship both attach here — with no attestation surface at all. `formation/operational` (#3)
  additionally emits an **empty `data`** against §4.2.1 block 5's declared minimum `{founders, name}`;
  recorded with N2, not split out.

**Novelty (v44), matcher published.** Both audit trees: `deposit_treasury` **0**, `allocate_treasury`
**0**. `incorporate_child` returns 8 files — inspected individually: ISP cross-references (C62, C102:51,
C174:135), the C50-B18 charge (*no `CitizenshipRecord` created* — re-verified TRUE at HEAD, 0 hits in
`society.py:773-815`), and C320/C131 carrying B18. **None concerns witnesses.** B18 and N2 both point
at `incorporate_child` and charge disjoint predicates.

**Disposition: routed to the SDK-track bundle. No spec change requested.**

### §B-3 — **N3 (MED, process/ledger → the rotation) — two open rows anchored in this file are held only in sibling lineages, and C320's inbound check is falsified by a document it names as re-read**

C320's §C closes with:

> **Inbound (bidirectional) check:** no sibling audit doc in the window routed a carry back to this
> target. C284 (society-metabolic-states) and C286 (society-authority-law) were re-read; neither
> routes here.

**`docs/audits/C284-society-metabolic-states-7th-delta-2026-07-29.md:183` is a carry row anchored at
`SOCIETY_SPECIFICATION.md:89`.**

**Row 1 — `C54-B14`.** *"SOCIETY_SPEC §1.4 MUST-conform vs target 'Proposed Standard' + §10 SHOULD."*
Anchor `SOCIETY_SPECIFICATION.md:89` — a line in **this** file:

> Implementations of this Society Specification **MUST also conform** to the metabolic-states
> specification for any society that intends to operate beyond a single bootstrap window.

Carried by the metabolic lineage in **C133, C168, C206, C244, C284, C324** — six passes — most
recently `C324-…:201`, *"DESIGN-Q + cross-track … OPEN, HELD by blob identity."*

**Row 2 — SAL's `L1-residual`.** *"SOCIETY_SPEC §1.4 → SAL §3.6 back-link absent."* Carried across
**C58:146, C98, C134, C170, C326**, re-verified `C326-…:229` as **TRUE (frozen)** — dated
**2026-08-06, the day after** C320 certified that no inbound carries exist. Re-resolved here: SAL
`:137` `### 3.6 Metabolic State Considerations — **SHOULD**` exists; the target's §1.4 (`:85-89`)
cites `SOCIETY_METABOLIC_STATES.md` and does not cite SAL §3.6. **TRUE at HEAD.**

**Occurrence census across this lineage — instrument stated exactly.** `grep -ow` per id, one column
per pass, because `grep -c` counts lines and **`B14` collides**: `C50-B14` (citizenship revocability
vs SAL §5.1) is a **different row in this very ledger**, and a bare-`B14` count returns 2–6 hits in
eight of the nine documents. Counted on the full ids:

| id | C22 | C50 | C92 | C131 | C164 | C202 | C240 | C280 | C320 |
|---|---|---|---|---|---|---|---|---|---|
| `C54-B14` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `L1-residual` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**0 of 9, both rows.** Neither has ever been typed in this lineage.

**Frame it correctly — this is a token-matching failure, not a reading failure.** At **C284 the row is
written bare as `**B14**`**; only C324 (one day *after* C320) writes it as `C54-B14`. C320 did read
C284; what it could not do was match a bare label to a row it had no name for. That is v44's point
turned on the inbound direction: **search the domain's words and the anchor, not the label.** The
generalizable instrument is not "read the sibling audits" — it is *`grep -n "SOCIETY_SPECIFICATION" `
over the sibling lineages' latest passes and read every hit*, which is what surfaced both rows here.

**Report both halves** (a one-sided report would itself be the overclaim): C320 was **right about
C286** — `grep -c SOCIETY_SPECIFICATION` over `C286` returns **0**, and `L1-residual` is absent from
it, because the SAL lineage had itself dropped the row at C208 and did not restore it until C326.
C320 was **wrong about C284** only.

**Received, not found.** Both rows are other lineages' open DESIGN-Q items, verified TRUE by their
owners within the last five days. They are typed into §C here as **RECEIVED** and are **not scored as
C360 findings** — re-filing another lineage's live row inflates this pass's yield with their work
(the C356 error). N3's MED is for the **routing failure**, and is scored to match how C320 scored its
own N1 row-loss.

**A third, weaker inbound item, recorded not filed.** `C324-…:154` explicitly declined to file an
observation naming this target — `web4-standard/README.md` carries a `**NEW**` badge on a 1.0.0
Proposed Standard frozen 53 days — and left it *"for whoever owns that file."* Re-resolved at HEAD:
the line is **`web4-standard/README.md:59`**, not `:60` as C324 published (README last moved at
`d89595e8`/#531, so the cite was already off by one when written). C324's own reasoning holds — `grep
-c '\*\*NEW\*\*'` = **7**, a whole-README staleness pattern, not a society defect — and is **not
re-litigated**. Recorded so the next pass does not rediscover it as novel.

### §B-4 — window gate: 53 commits, of which **22 are `hub/`** — walked, one corroboration routed

`afd04623` (#678, hackathon findings → `errors.md` + `security-framework.md` + the IETF draft XML) is
the only in-window commit touching `web4-standard/`; read against this file's subject matter — society
lifecycle, citizenship, ledger classes, law, the base-mandatory seven — it restates and re-scopes
nothing here.

**`hub/` — in this file's mirror set since C280 — has 22 commits in this window**, touching 16 files
including `law.rs`, `ledger.rs`, `state.rs`, `events.rs` and `rest.rs`. (An earlier draft of this
section published this cell as **0**, having measured `web4-standard/` and labelled the result `hub/`;
see own-error 1. The correction produced this pass's best corroboration, so it is worth stating what
the corrected gate found rather than only that it was corrected.) Gated against this file's subject
matter:

- **`68c2ba9c` (#670) — *"refuse a law norm that names an action the gate never emits."*** This is the
  **same check N1 says the SDK lacks, built independently by the hub track six days ago and
  ratified.** `law.rs:390` `is_known_law_action(action)` — its doc-comment reads *"Is `action` a value
  the gate can ever actually see?"* — refuses a law norm whose action no `HubEvent::kind()` can
  produce, with `KNOWN_SYNTHETIC_ACTIONS` (`:382`) enumerating the one action the gate synthesises
  before any event exists. **Routed as fix-shape precedent for N1**, not as a finding: the hub
  institutionalised *"does anything actually reach this?"* as a validation rule; the SDK's
  `QuorumPolicy` is the same question one level up, unasked.
- **`25978a63` (#677) chain-tail watermark, `f8817ede`/`8aecac7b` reload-law lock ordering,
  `4f05db33`/`e4042fc3`/`5d2ded1a`/`ff919a74` law-gate hardening** — read against §4.1/§4.2/§4.3: no
  change to the recorded event classes, no new ledger event type, no amendment path (C320-N3 unmoved).
  **No candidate.**
- **`85975dcf` (#650) Track H — a governed discussion surface where the post IS the ledger entry** —
  the one commit that adds a new class of ledger entry. Read against §1.2.2's five minimum-record
  categories and §4.2.1's five event types: a discussion post is not a society-lifecycle event and
  §1.2.2 `:39` is explicitly scoped (*"It is not the ledger's complete storage obligation"*). **No
  candidate; recorded because a future pass will meet it again.**
- **`hub/docs/HUB-LAW.md`, `ROLES.md`, `QUICKSTART.md`, `TROUBLESHOOTING.md`, `README.md`** — checked
  for claims over this file's subject matter. `HUB-LAW.md:253` is folded into N1's refuted
  reach-escalation (§B-1); the rest restate nothing here.
- **`requires_quorum` / `requires_witnesses` inertness across `web4-policy` and `hub/`** — measured,
  and **REFUTED as a finding** in §B-1: disclosed phasing, three sites.

The remaining 30 in-window commits are audit documents, whitepaper/publisher logs, and
private-context work. **Nothing filed from the window; one precedent routed.**

### §B-5 — REFUTED / CHECKED-AND-CLEARED candidates (recorded so future deltas do not re-walk them)

- **"The SDK's `CitizenshipStatus` has APPLIED and PROVISIONAL but the ledger API can never produce
  them — no emission site uses `apply` or `provisional_grant`."** **TRUE as a fact, NOT FILED.**
  §4.2.1's field-sets are explicitly *minimums* and §1.2.5 `:62` makes operational conformance *"not
  protocol-enforced"*; an implementer omitting optional actions is conformant. Also adjacent to
  **C320-N2**, which closed C50-B17 (the `_CITIZENSHIP_TRANSITIONS` charge) as **REFUTED — born
  false**; re-opening the same transition graph on a neighbouring predicate would read as
  re-litigation. Recorded, not charged.
- **"The 4 non-parsing `json` blocks are a defect."** **REFUTED.** All four failures are the `{...}`
  elision convention; their fences open at `:284` (§4.2.1 block 2, `voting_record`), `:354`, `:364`,
  `:376` (§4.2.2 blocks 1–3: `original_data`, `new_data`, `voting_record`). The blocks were **kept in
  the denominator** (C356's rule) and read; they carry no independent claim.
- **"`society-vectors.json` is under-exercised / an orphan."** **REFUTED, do not re-walk** — C320 §B-5
  and `C326-…:303-304` both establish it is consumed by `test_society.py`'s `TestVectors`; its
  coverage gap is C22-I3, already recorded. Re-run here: 86/86 green.
- **Cross-reference drift.** 37/37 exact (§A). **Published as a negative.**
- **`web4-policy`** remains a **faithful** §7.3 implementer (C240/C280/C320 guard) — 0 in-window
  commits, guard **not re-tested this pass and not re-flagged**; `C330-…:336-340` independently
  re-read its three `SOCIETY_SPECIFICATION §4.2` doc-comments in the window and routed nothing here.
- **`95683868` hardening wave** remains a **FALSE MIRROR** for this target (C280). **Admission-law
  theater** and the **t3v3-ontology reach** stay closed (C280). **C232-N1** does not intersect §7.3.
- **The §4.2.1-envelope-vs-§4.2.2 shape mismatch** was RAISED AND WITHDRAWN at C320 §B-5. Not
  re-raised.

**§B conclusion: 0 autonomous edits of any kind; 1 MED spec-MUST-vs-implementer (N1); 1 MED net-new
implementer gap (N2); 1 LOW-MED restored carry half (N2b); 1 MED process/ledger (N3); 1 INFO folded
(I-1) + 1 INFO in §C (I-2); 8 candidates refuted or cleared — including the reach-escalation this
pass most wanted to file; 1 full negative published (§A); 1 fix-shape precedent routed from the
window (hub #670).**

---

## §C — Carry Re-Verification (bidirectional; every anchor re-resolved by content)

**12/12 OPEN.** The SDK-side anchors hold by blob identity — `sdk/web4/` last moved **2026-05-24**
(`62524cf8`), `society.py` = `e7383124`, `federation.py` = `482a2148` — but each was **re-resolved by
content at HEAD** rather than inherited.

| Carry | Owner | Anchor re-resolved at HEAD | Status |
|---|---|---|---|
| **C50-B13** Law Oracle name collision | operator DESIGN-Q | target `:24` *"Codified rules governing entity behavior…"* ✓; `society-roles.md:71` `### 2.2 Law Oracle` ✓ | **OPEN** |
| **C50-B14** citizenship revocability vs SAL §5.1 | operator DESIGN-Q | `web4-society-authority-law.md:180` `### 5.1 Citizen (Genesis, Immutable)` ✓ | **OPEN** |
| **C50-B15** law inheritance model | operator DESIGN-Q | target `:178` *"Local laws can extend but not contradict inherited laws"* ✓ | **OPEN** |
| **C92-N1** solo-founder guard (half-closed) | SDK track | `society.py:317` `if len(founders) < 2: raise` **live**; `role.py:303-305` docstring still claims the gap resolved | **OPEN** |
| **C164-N1** enum-comment stale vocab | SDK track | `society.py:92` `# join/leave/suspend/reinstate`, `:94` `# allocate/deposit/reclaim` — still pre-C51 | **OPEN** |
| **C22-M3** `type` ↔ `event_type` | SDK track | `society.py:111` `event_type: LedgerEventType` | **OPEN** |
| **C92-N3 / C50-B20** id-scheme examples | C33 bundle | frozen body, present | **OPEN** |
| **C50-B16(a)** §4.2.1 MUST minimum fields | SDK track (restored C320) | `law_reference` 0, `change_description` 0, `voting_record` 0, `effective_date` 0, `recipient_lct` 0 — **0 of 5** SDK-wide | **OPEN, re-verified** |
| **C50-B16(c)** amendment wire-shape | SDK track (restored C320) | `amendment_type` 0, `law_authorization` 0; `amend()` takes no law ref | **OPEN** |
| **C50-B18** fractal tree ⟂ citizenship | SDK track (restored C320) | `society.py:773-815`: `CitizenshipRecord` **0** occurrences | **OPEN** |
| **C50-B19** `merge_law` no contradiction check | SDK track (restored C320) | `federation.py:389-403`: `merged_norms = list(child.norms) + [n for n in parent.norms if n.norm_id not in child_norm_ids]` — override by id, no §3.2.1 check | **OPEN** |
| **C320-N3** §4.2.2 zero conformant implementers | operator, w/ B16(b) | target `:351` *"All ledgers MUST support law-driven amendments"* ✓ | **OPEN** |

**SDK-track bundle after this pass — eleven rows:** C92-N1, C164-N1, C22-M3, C92-N3/C50-B20,
C50-B16(a), C50-B16(c), C50-B18, C50-B19, **+ N1, N2, N2b**.
**Operator DESIGN-Q bundle:** C50-B13, C50-B14, C50-B15, C280-N1 (adjudicate with B-D1), C320-N3,
**+ N1's docstring question**.

### RECEIVED this pass (typed here for the first time; NOT scored as C360 findings)

| id | owner lineage | anchor in this file | state at HEAD |
|---|---|---|---|
| **C54-B14** | society-metabolic-states (C133→C324) | `SOCIETY_SPECIFICATION.md:89` | OPEN by blob identity; re-verified TRUE |
| **L1-residual** (C16→L1-revised→L1-residual) | society-authority-law (C58→C326) | §1.4 `:85-89`, SAL §3.6 back-link | OPEN; SAL `:137` §3.6 exists, target does not cite it |

**Do not adjudicate either on the merits from this lineage** — both are DESIGN-Q rows owned elsewhere.
Their obligation here is to be **typed and carried**, so the next pass cannot lose them the way C320
lost its own four.

### C320's own outstanding items, re-checked

- **C320-N1's restoration held**: all four restored rows are present in §C above and re-verified.
- **C320 I-1 → I-2 (INFO): C280-N1's citations have now gone stale a SECOND time, faster.** C320 found
  3 of 8 anchors stale within 7 days of the finding being routed, and corrected them. `hub/` then
  moved **22 more commits in 6 days** (§B-4). Re-resolved by content at HEAD:

  | C280-N1 anchor | C320's corrected value (2026-08-05) | at HEAD (2026-08-11) | drift |
  |---|---|---|---|
  | `events.rs` `MemberJoinResolved` | `:119` | `:119` | **exact** |
  | `docs/PAIRED-CHANNELS.md` tier resolution | `:338` | `:338` | **exact** |
  | `docs/PRD.md` base-mandatory seven | `:38` | `:38` | **exact** |
  | `state.rs` `JoinStatus::Denied` | `:346` | **`:355`** | **+9** |
  | `state.rs` projection | `:609` | **`:645`** | **+36** |
  | `README.md` *"An external entity calls `request_citizenship`"* | `:286` | **`:290`** | **+4** |
  | `rest.rs` *"the external→citizen bootstrap"* | `:3105` | **`:3346`** | **+241** |
  | `law.rs` *"Citizenship is not open-admission"* / `member_join_request` | `:1283-1286` | **restructured** — `member_join_request` is now a named constant at `:382` (`KNOWN_SYNTHETIC_ACTIONS`, added by #670) with a second site at `:1356` | **moved + reshaped** |

  **5 of 8 stale, in 6 days — a higher rate than the 3-of-8-in-7-days C320 measured.** The memo has
  still not reached an operator. C320 named this pattern (*"a routed finding's evidence decays at the
  rate of the tree it cites"*); this pass measures its **second derivative**: the decay is
  accelerating, and one anchor has now changed *kind* rather than position, which a line-number
  correction cannot express. Corrected here; **C280 and C320 are not rewritten** (v11). For any future
  routed finding citing `hub/`, cite by **construct name**, not line — that is the only anchor that
  survived all three resolutions.
- **C320 I-2** (0 `responses:` in the four `hub/hub-lib/tests/fixtures/hub-law/*.yaml`) → hub track,
  unmoved; not re-measured this pass.

---

## §D — Disposition

- **Spec side: NO ACTION. ZERO mutation.** Target byte-frozen 28 days, citation surface 37/37 exact.
  The file sits under an unanswered operator DESIGN-Q bundle; no autonomous edit is warranted or
  authorized.
- **SDK side: NO ACTION. ZERO mutation.** N1, N2 and N2b all have one-line fixes and all three are out
  of bounds for this slot. Fix *shapes* only, routed:
  - **N1** — consult `state.society.quorum_policy` in `record_law_change` before appending; publish
    the `PROC-WITNESS-QUORUM` procedure id in the standard or retire it for the typed object.
    **Operator DESIGN-Q attached:** does `society.py`'s *"consensus out of scope"* docstring exempt it
    from `:299`'s MUST? Both readings are recorded; **not self-resolved.**
  - **N2 / N2b** — add a `witnesses` parameter to `deposit_treasury`, `allocate_treasury`,
    `incorporate_child`; give `formation/operational` a non-empty `data` per §4.2.1 block 5.
- **N3 → the rotation.** `C54-B14` and `L1-residual` are carried in §C as RECEIVED from this delta
  forward. The instrument that found them is written into the method lesson below.
- **I-1 → LCT lineage, INFO.** `C60-…:132`'s parenthetical attributes quorum enforcement to
  `federation.py`'s `QuorumPolicy`; the enforcement is real but lives at `federation.py:574-577` via
  `Procedure.requires_witnesses`. **C60's conclusion is unaffected** — its scoping basis requires
  enforcement *somewhere else*, and two independent sites supply it. Correction only, no re-scoring.
- **I-2 → operator + the rotation, INFO (§C).** C280-N1's 8 citations re-resolved a second time; 5
  stale in 6 days, one restructured into a named constant. **Cite `hub/` by construct name, not line.**
- **Fix-shape precedent routed with N1, not filed:** hub `#670` (`law.rs:390 is_known_law_action`) is
  the ratified form of the check N1 asks for, on the other implementer, six days old.
- **Also routed as INFO → whoever owns `web4-standard/README.md`:** C324's declined observation, with
  its line corrected to `:59`. Not re-litigated.
- **No review-gate block is owed for C360.** This audit proposes no diff to any surface; its
  deliverable is one document, and it drives no consequential act.
- **C361 = declared NO-OP on the spec side. Next SOCIETY_SPEC delta ≈ C400.**

### Deferral ledger for C400 — row count 5, members named

*(This is what C360 did **not** measure. Do not inherit it as a mirror set — it is the negative space.)*

1. **`hub/` beyond the subject-matter gate** — 22 commits were walked by *commit subject and touched
   file* (§B-4), not by reading `ledger.rs`/`state.rs` diffs line by line. The one deep read was
   `law.rs` for #670. At C400, read `hub/hub-lib/src/ledger.rs` against §4.1's three ledger classes
   directly — no pass in nine has done so.
2. **`web4-policy`'s §7.3 faithfulness** — the C240/C280/C320 guard was **not re-tested** this pass
   (C320 re-tested it; `web4-policy` had 0 in-window commits). What *was* measured here is a different
   predicate — `requires_witnesses`/`requires_quorum` are parsed and never read (§B-1, refuted as
   disclosed phasing). Re-test the §7.3 predicate at C400 rather than inheriting a two-pass-old
   assumption.
3. **The 4 remaining §4.2.1 minimum-field-set columns** — this pass executed the *envelope* (witnesses)
   and B16(a) re-verified the *5 payload tokens*. Nobody has diffed the SDK's emitted `data` keys
   against §4.2.1's declared minimums **row by row** (table in §B-2 has the raw data; the comparison
   was deliberately not made, to avoid double-charging B16(a)).
4. **`test-vectors/metabolic/society-metabolic-states.json`** — opened only far enough to confirm the
   8 state names. Never read against §1.4 or against `SOCIETY_METABOLIC_STATES.md` from this lineage.
5. **`archive/reference-implementations/society_specification.py`** and the two `docs/reference/`
   referrers — named in the inbound sweep, never opened by any pass in nine.

### Own-error log (v-publish-the-instrument; all caught pre-ship — three by policy review, one by the post-write re-run)

1. **I published a gate as EMPTY that had 22 commits in it — the single worst cell in the draft.**
   §B-4 read *"`hub/` … has 0 commits in this window."* The number **0** was real; it was the answer
   to `git log e4a62d7a..HEAD -- web4-standard/` **minus** the one hit, relabelled `hub/` while
   drafting. Ground truth: `git log --oneline e4a62d7a..HEAD -- hub/` → **22**, touching `law.rs`,
   `ledger.rs`, `state.rs`, `events.rs`, `rest.rs`. Caught only by the post-write re-run (v17), and it
   is the most instructive failure in the pass on three counts. (a) **A mirror set that C280 fought to
   widen was silently re-narrowed by a transcription slip** — the C280 gate change would have read as
   *honoured and negative* to every future pass. (b) The corrected walk produced this pass's **best
   corroboration** (#670's `is_known_law_action`, the exact check N1 says the SDK lacks, shipped six
   days ago) and its **strongest refutation** (the disclosed-phasing convention that gave N1 its
   correct shape). **The empty cell was hiding the finding's other half.** (c) It is
   [[feedback_gate_scoped_to_wrong_tree]] committed by the pass whose own flagship is *"nobody checked
   whether anything calls it"* — I did not check what my own zero was a count of. A gate cell of `0`
   should never be publishable without the command that produced it printed beside it; every gate cell
   in this document now carries its command.
2. **The denominator was wrong: "4 of 12" should be "4 of 13."** Drafted by counting the twelve
   literal `action=` sites; the thirteenth is `:689`, `record_law_change`'s parameterized site — **the
   site N1 is entirely about**. A count that drops the finding's own subject is the v40 failure in its
   most embarrassing form. Caught by policy review.
3. **A whole finding was drafted, and it was an overclaim.** *"C60:132's scoping basis is false"* —
   false, because quorum **is** enforced in `federation.py:574-577`, and N1 **depends on that same
   site**. Being strict about C60's parenthetical while relying on the fact it points at is exactly
   the self-exemption v31/v41 forbid. Demoted to I-1 and folded in as corroboration, where it is worth
   more. Caught by policy review.
4. **Three cites were guessed and two were wrong.** `issue_citizen_lct` → the method is
   **`issue_citizenship`** (`federation.py:555`); the quorum test block `490-504` → the class is
   `TestQuorumPolicy` at **`:485`**. Both corrections came from capture, not memory (v39).
5. **The `PROC-WITNESS-QUORUM` arm was initially over-broad.** Drafted as *"a magic string with no
   normative basis."* Half wrong: `requires_witnesses` **is** SAL `:197`'s own example key. Only the
   **procedure id** is unpublished. Narrowing it made the finding more precise — and per v41.4, a
   correction that *strengthens* the argument means the original was guessed.
6. **C324's `README.md:60` was carried forward unchecked and is `:59` at HEAD** (and README has not
   moved since `d89595e8`, so the cite was off when written). Path tokens are their own class; every
   one in this document was resolved as written.
7. **The first §A draft would have stopped at C320's four §7.3 citations.** The blob comparison showing
   **7 of 10 cited siblings moved since C92** is what made the other 33 sites worth resolving. They
   were all clean — which is the point: the negative is only publishable because the instrument was
   widened first.

### Method lesson — proposed carry v45: **a green unit test is evidence about a function, never about a system**

C326 executed the standard's own governance vectors against `QuorumPolicy.check` and got **6 of 6
PASS**, and recorded the artifact *"swept CLEAN."* `test_federation.py` asserts the same evaluator
nine more times. Every one of those greens is true. **The function has never been called by anything
that isn't a test**, and the MUST it exists to enforce (`SOCIETY_SPECIFICATION.md:299`) is violated by
the same package on the default configuration that package itself constructs.

v43 said *coverage is not execution* — a coverage table is not a run. **v45 is the next step in:
execution of a unit is not execution of a system.** A vector run that instantiates the object under
test and calls its method directly proves the method; it is structurally incapable of noticing that no
production path reaches it. The two look identical in a results table — both print PASS — and the
second is the more dangerous, because it arrives with the authority of a *standard-published test
vector*.

**The operative form:** whenever a pass validates a component against a spec obligation, run **one
more grep — for the component's callers** — and publish that number beside the PASS. `git log -S
"<call expression>"` over all history costs one command and distinguishes *"correct and load-bearing"*
from *"correct and ornamental."* Where the spec names an object (SAL §3.1 names the Quorum Policy;
`:299` routes a MUST through it), the caller count **is** the conformance measurement; the unit test
is not.

**Three sharpenings this pass earned:**

0. **The corpus already knows the answer, and writes it down — everywhere except here.** The refuted
   reach-escalation (§B-1) is the load-bearing half of this lesson. `web4-policy` parses
   `requires_witnesses`/`requires_quorum` and never reads them; the hub ships `requires_witnesses: 3`
   in its operator-facing starter law. **Both are correct**, because both **declare the inertness at
   the point of use** — `starter-law.yaml:120-121`, `hub-law-schema.md:44` — exactly as this target's
   own §7.3 does for the kinetic verbs (`:485-488`). So the finding is not *"an inert mechanism
   shipped"*; the corpus does that deliberately and honestly. The finding is that **`:299` states an
   unqualified MUST where every sibling states a phased one**, and the SDK is the single implementer
   that advertises a live quorum (`society.py:310`) while providing none. *The convention is the
   control; the defect is the one site that opted out of it.* An auditor who files the inertness
   without first checking whether it is **disclosed** charges the corpus for its own discipline —
   which is what the first draft of this section did.
1. **Two documents in two trees can believe an inert object is live, and neither will ever find out.**
   `SOCIETY_SPECIFICATION.md:299` and `docs/designs/u2-multi-device-binding.md:277` both route real
   obligations through `QuorumPolicy`. Nothing consumes either claim, so nothing contradicts them. **A
   dangling reference to a *live-looking* symbol is invisible to every instrument this rotation owns**
   — the symbol resolves, the class exists, the tests are green, the citation is exact. Only the
   caller count is zero.
2. **The inbound half of the bidirectional carry check has never actually run in this lineage** (N3),
   and the reason is instructive: reading sibling audit documents is not the instrument — **grepping
   them for your own target's name and reading every hit** is. C320 read C284 and could not see
   `**B14**`, because the row was typed bare and C320 had no name to match. The fix is the same one
   v44 gives for novelty: **search the anchor and the subject matter, not the label.**

*Method references: [[feedback_coverage_is_not_execution]] (§B-0, §B-1 R3 — extended to v45),
[[feedback_novelty_is_an_absence_claim]] (§B-1 R4, §B-2 — matchers published; §B-1's own-lineage note),
[[feedback_admission_row_is_not_examination]] + [[feedback_decline_licenses_its_range]] (§B-1 R2/R3 —
C326's PASS and C50-B16(a)'s token set each license only their own predicate),
[[feedback_delivery_is_an_act_of_the_receiver]] + [[feedback_subsumption_is_a_disposition]] (§B-3 —
received rows typed into the receiver's ledger), [[feedback_measure_the_row_set]] (§B-3 — the census is
of the row set, and it is 0 of 9), [[feedback_metric_denominator_is_a_domain]] (§B-2 — 13 emission
sites, domain rule published; own-error 1), [[feedback_remediation_introduced_regression]] +
[[feedback_class_not_cell]] (§B-2 — C51 fixed one side of B2; the other side was never re-run),
[[feedback_publish_the_instrument]] (every count above carries its grep and its scope),
[[feedback_refute_your_best_finding]] (§B-1 R1–R4, one sustained as a cap).*

---

*C360 verdict: `SOCIETY_SPECIFICATION.md` is byte-frozen and correct — the seventh consecutive delta
requiring zero spec-side mutation, and the ninth pass overall. §A is clean and, for the first time,
measured: all 37 cross-reference sites resolved at HEAD across ten siblings, seven of whose blobs have
moved since the citations were last checked. The yield came from running the file's own MUST against
the file's own implementer. `:299` requires law changes to carry witness co-signatures per the
society's Quorum Policy; the canonical SDK records one with zero witnesses against a society it
configured itself as `UNANIMOUS(2)`, because `QuorumPolicy.check` — correct, unit-tested nine ways,
and vector-verified 6/6 by C326 five days ago — has never had a production caller in the repository's
history. Four of the SDK's thirteen ledger emissions write `witnesses: []` from three public functions
that expose no `witnesses` parameter; two of those are the surviving implementer half of C50-B2, whose
spec half was fixed at C51 and verified HELD on the spec side only, and two are net-new. And two open
rows anchored in this file's own lines are carried by the metabolic and SAL lineages and appear in
zero of this lineage's nine passes — one of them in the very document C320 named as re-read and found
empty. The pass's own worst cell published the `hub/` gate as empty when it held 22 commits; walking
it properly produced both the ratified precedent for N1's fix (#670's `is_known_law_action`, shipped
six days ago) and the refutation that gave N1 its correct shape — the corpus ships inert governance
mechanisms deliberately and **declares it at the point of use**, at three sites, and `:299` is the one
place it does not. Zero mutation; C361 = no-op.*
