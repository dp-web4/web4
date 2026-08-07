# C332 Audit: `entity-types.md` — 8th-Delta Re-Audit (9th Pass)

**Date**: 2026-08-07
**Auditor**: Autonomous session (Legion, web4 track) — firing `20260807-120000`
**Document**: `web4-standard/core-spec/entity-types.md` (804 lines, blob `a2dda417`)
**Lineage** (9 docs): C8 → C26 → C64 → C65 (remediation, 7 applied) → C104 → C137 → C176 → C214 (#523 Effector §4.8) → C252 → C292 (N1, MED) → **C332 (this audit)**
**Window**: `ff5e7b0b..38d0bd89` — 46 commits, 2026-07-30 → 2026-08-07. **Rotation**: `C292 + 40`.

## Headline: the standard ships two entity test-vector files, they disagree about every entity type they both describe, and both are green in CI

`entity-types.md` is byte-frozen for the **6th consecutive pass** (24 days). The finding came from
the inbound half of the mirror derivation — `git grep -F "core-spec/entity-types.md"` — which
surfaces three machine-readable artifacts that **no audit document in either tree has ever named**:

| artifact | lines | last moved | named in any audit doc, either tree |
|---|---|---|---|
| `web4-standard/test-vectors/entity/entity-taxonomy.json` | 84 | `0b7d3a93`, 2026-03-16 | **0 of 212** |
| `web4-standard/schemas/entity-jsonld.schema.json` | 114 | `9dd8f06e`, 2026-03-23 | **0 of 212** |
| `web4-standard/test-vectors/schema-validation/entity-jsonld-validation.json` | 482 | `705e90ea`, 2026-03-23 | **0 of 212** |

All three were **executed** here for the first time in corpus history: **64/64 assertions PASS**
(32 taxonomy + 32 schema-validation). That clean result *is* the finding — see §B′.3.

**3 net-new** (1 MED + 2 LOW), **zero mutation of the standard**, and one reach-escalation on a
2026-06-16 carry. The second LOW (N3) came from the §B window sweep and is the one this seat is
least comfortable with: it was found only because a cell in §B was **wrong on the first read**.

---

## §0. Gates

**Step 0 (queue).** Canonical `/home/dp/ai-workspace/private-context/SESSION_FOCUS.md` read (not the
worktree copy). `[Legion]` items: 0a hestia-owned; 0b SERVED; 0c WIRED, awaits a vault-authorized
actor; 0d IN MOTION (Phase-2 code half is the HUB track's PR); 0e SERVED; 0f routed to the CBP
Publisher track. **No greenlit item pre-empts the rotation.**

**Step 0.5 (own standing blocks).** `gh pr list --author @me` returns #641, #655, #656 — the GitHub
account is shared fleet-wide, so `@me` is **not** track-scoped and attribution must come from the
branch names. `pr_standing_blocks.py`: **#655 CLEAR**, **#656 CLEAR** (both `hub/…`, HUB track),
**#641 BLOCKED** (`publisher/whitepaper-log-2026-08-05`, CBP Publisher, SESSION_FOCUS 0f). **This
track has zero open PRs ⇒ 0.5 CLEAR.**

**Instrument note — the C330 finding is NOT retracted.** At the 06:00 fire `pr_standing_blocks.py`
reported #641 **CLEAR** while three asks sat unaddressed, because its staleness rule treats any head
newer than the block as superseding it — right for *rebased/amended* heads, wrong for *appended*
ones. It reports **BLOCKED** now only because the reviewer posted a **new** block at
`2026-08-07T17:07:11Z` against head `8c6a8438`, opening *"the 2026-08-05T17:06:35Z block still
stands. But the clock is reset."* The comment history shows six consecutive HELD comments
(08-05T23:06 → 08-07T05:07) at unmoved head `2ada8bb8`, then the 08-07T11:43 append, then the
re-block. **The tool is right for the wrong reason; the appended-head bug is unfixed.**

---

## §0.5. Pre-registration (v26) — fixed before any measurement

**Prior, stated as prediction.** In-window: `web4-standard/ontology/` **0** commits,
`web4-standard/` **2**, `web4-core/` **1**, `hub/` **17**. The substrate of the standing C292-N1 is
itself frozen, so **a NEGATIVE mirror gate on the C292 subject matter is the predicted outcome and
will not be narrated as a discovery.**

**Admission test.** A finding is net-new **iff** (a) **M3 = REACH** — it indicts something with a
live consumer — **and** (b) `grep -F` on its subject-matter token over **both** audit trees returns
**0** prior bookings.

**Reach-escalation rule.** Any evidence upgrade to **C292-N1, C286-N1, C234, C16-M1, B15,
C268-INFO-1, or C64-B2/B9** routes as reach-escalation on the existing carry — **never as net-new.**

**Stop rule (P2).** NEGATIVE gate + no admitted finding ⇒ ≤60-line no-op record, **a successful
outcome, not a shortfall.** *(It did not fire.)*

**Instrument classes.** Every published count carries its class.
**(i) live-surface**: `--exclude-dir=target --exclude-dir=audits --exclude-dir=.git`;
`forum/nova/`, `archive/`, `whitepaper/archive/`, `simulations/` are mirrors — reported separately,
never folded into a live count.
**(ii) prior-art booking**: audits **INCLUDED**, over `docs/audits/` (210) **and**
`web4-standard/docs/audits/` (2) = **212 documents** (`git ls-files`, this document excluded).
Matchers are literal (`grep -F`) on any token carrying `.`/`-`/`_`; enumerations are re-derived from
ground truth, never from a line-shape grep.

**Mirror set, derived in BOTH directions and frozen before §B′ ran.**
*Inbound* — `git grep -lF "core-spec/entity-types.md"` @ `38d0bd89` = **39 files**, partitioning
exactly as **19** audit docs + **9** whitepaper/history/strategy renderings + **2** (`archive/`,
`.private-context.md`) + **9** live `web4-standard/` referrers (19+9+2+9 = 39). The nine live
referrers are: `web4-standard/core-spec/LCT-linked-context-token.md`,
`web4-standard/DICTIONARY_INTEGRATION_SUMMARY.md`, `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md`,
`web4-standard/proposals/dictionary-as-context-mandatory-role.md`,
`web4-standard/implementation/sdk/web4/entity.py`,
`web4-standard/implementation/sdk/web4/schema_registry.json`,
`web4-standard/schemas/entity-jsonld.schema.json`,
`web4-standard/test-vectors/entity/entity-taxonomy.json`,
`web4-standard/test-vectors/schema-validation/entity-jsonld-validation.json`.
*Outbound* — the paths `entity-types.md` itself cites: `atp-adp-cycle.md`, `dictionary-entities.md`,
`hub-law-schema.md`, `LCT-linked-context-token.md`, `reputation-computation.md`, `society-roles.md`,
`SOCIETY_SPECIFICATION.md`, `web4-society-authority-law.md`,
`proposals/W4IP-DRAFT-2026-07-13-…`, `docs/history/design_decisions/POLICY-ENTITY-REPOSITIONING.md`.
**M1** = `web4-core/src/{lct,role,role_extension}.rs`, `sdk/web4/{entity,role}.py`, `hub/`.
**M2** = the four inbound machine-readable artifacts above + `web4-standard/ontology/*`.
**The last three M2 members are the ones the outbound derivation is structurally incapable of
reaching: `entity-types.md` cites none of them.** (Same mechanism as C322.)

---

## §A. Regression — byte-frozen ⇒ HELD by construction

`git log 1354e4c2..HEAD -- web4-standard/core-spec/entity-types.md` = **empty**; blob at HEAD =
`a2dda4178b96ffc44e45a456917f4a129914bda7`, **804 lines** — byte-identical to the C214/C252/C292
snapshot, **24 days** frozen (`1354e4c2`, #523, 2026-07-14). Every C292 conclusion that is a property
of the file text HOLDS by construction: the **7 C65 remediations**, the **§4-preamble count edit**
(`:281`), and the **9 standing carries** (C8-L3, C23-H1, C24-H1, B2/B9, B7, B10/B11, B12).
**0 regression possible.**

**C292-N1 re-verified STANDING** (not re-derived as new): see deferral rows g1/g2 below.

---

## §A.3. Inherited deferral ledger — **row count 4**, members named, each discharged

C292:175-179 left four forward guards. They are this pass's inherited deferral row.

| id | member (verbatim from C292) | instrument @ `38d0bd89` | disposition |
|---|---|---|---|
| **g1** | did anything gain a `role_definition` implementer, or did §3.3 gain a `role_extension` slot? | class (i): `role_definition\|roleDefinition` = **4 hits / 4 files** — `entity-types.md:192`, `web4-society-authority-law.md:393`, + 2 `forum/nova/` mirrors of those same two files ⇒ **2 live standard files, 0 code / 0 schema / 0 vector**. §3.3 (L178-222) `role_extension\|roleExtension` = **0** | **NEGATIVE — unchanged from C292. C292-N1 STANDS.** |
| **g2** | did either side acquire a cross-reference? | `entity-types.md` → `role-extension` = **0**; all of `core-spec/` → `role-extension` = **0 files**; `ontology/role-extension-schema.md` → `entity-types\|core-spec\|agency\|AGY\|r6Caps` (case-insensitive) = **0** | **NEGATIVE — still zero in both directions.** |
| **g3** | has HUB Phase-2 landed (`grep -ri effector` over `web4-core/src` + Python SDK)? | **0 hits** | **NEGATIVE — still absent.** Already routed (SESSION_FOCUS 0d); **not net-new.** |
| **g4** | re-count `EntityType` variants at HEAD; do **not** transcribe 9 / 8-of-15 | Rust `web4-core/src/lct.rs`: **9** variants — Human, AiSoftware, AiEmbodied, Organization, Society, Role, Task, Resource, Hybrid ⇒ **8 spec types** (AI split in two), 7 absent: Device, Service, Oracle, Accumulator, Dictionary, Policy, Infrastructure. Python: **15** (re-derived by importing the enum) | **C176-N1 STANDS, re-derived not transcribed.** |

**g4 near-miss, recorded because it nearly shipped.** The first instrument for the Python count was
`grep -cE '^\s+[A-Z_]+ = ' entity.py`, which returned **9** — an exact numerical match to the Rust
count, and a very quotable "both implementations carry 9." It was wrong: the regex matched
`BehavioralMode` (3) + `EnergyPattern` (2) + `InteractionType` (4) and **not one member of
`EntityType`**. Ground truth (`[e.name for e in EntityType]`) is **15**. A line-shape grep is not an
enumeration; C292's "Python carries all 15" is **CONFIRMED**.

---

## §B. Window authority sweep — what landed claiming authority over this subject matter

46 commits. `web4-standard/` was touched **twice**:

- **`e4a62d7a` (#644, C320 society-specification 8th delta)** — **NOT audit-only, and the first read
  of it here was wrong.** It ships the C320 delta doc **plus** edits to three live standard files:
  `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md` (2 lines) and two `web4-standard/rfcs/`. The first
  instrument run on it was `git show e4a62d7a | grep -c "entity-types"`, read as 0; the actual value
  is **1**, and following that one hit produced **C332-N3** (§B′.6). Recorded because the near-miss
  is the lesson: *"an audit-doc commit"* is a classification, not a measurement.
- **`8d3808db` (#637) `test(standard): gate that every @context URI in test-vectors has a backing
  file`** — **relevant, and it is the reason §B′.3 is a finding rather than a hypothesis.** Its own
  commit message states the failure class exactly: *"the JSON schemas type `@context` as an array of
  URI strings and never dereference it, so a vector passes validation forever while citing a context
  that does not exist."* The new gate closes that hole for `@context`. §B′.3 is the **same shape one
  field over**: the schema types `entity_type`, `modes`, `energy` and `can_r6` as four independent
  values and never relates them, so a vector passes validation forever while contradicting the table
  it exists to encode. Verified the gate's own result holds here: `schemas/contexts/entity.jsonld`
  **exists** — entity vectors are backed, so this is not a re-run of C310-N3.
- `web4-core/` — 1 commit, does not touch `lct.rs`'s `EntityType` (g4 re-derived at HEAD anyway).
- `hub/` — 17 commits. Per §0.5, `hub/`'s role-vocabulary face is **C286-N1** and is **not
  re-booked** (book-once). Re-verified frozen at HEAD: `git diff 70381838..HEAD -- hub/hub-lib/src/law.rs`
  matching `KNOWN_ROLES|KNOWN_CONSTELLATION` = **empty**. **Nothing found in `hub/` this pass;
  nothing routed from it.** (Pre-committed bound, honoured.)

---

## §B′. Mirror gate — POSITIVE, on the M2 members the outbound derivation cannot see

### B′.1 — Standing mirror carries, re-measured (not transcribed)

| carry | instrument @ `38d0bd89` | result |
|---|---|---|
| **C176-N1 / N2** | g4 above | **STAND unchanged** |
| **Effector SDK mirror** | g3 above | **STILL ABSENT** — routed, not net-new |
| **C292-N1** | g1 + g2 | **STANDS** — substrate frozen, as predicted |
| **ratchet / citizenship / operational_key faces** | C252 §B′.3-4 | **DISJOINT, not re-opened** |

### B′.2 — The SDK registry is a faithful mirror of §2.1, and this had never been measured

Parsed the §2.1 table (**15 rows**) and compared every row against `sdk/web4/entity.py`'s `_REGISTRY`:

**15 of 15 exact on behavioural modes; 15 of 15 exact on energy** (modulo §2.1's parenthetical
qualifiers — "Active (via citizens)" → `active`). Infrastructure's `None` → `modes=[]`; Hybrid's
`Agentic/Responsive/Delegative` → all three; Oracle's `Responsive/Delegative` → both.

This is a **NEGATIVE, and it is load-bearing**: it makes the Python SDK an independent witness for
§2.1, so a divergence measured against the SDK and a divergence measured against the table are the
same divergence. Both are reported below against the **table**, with the SDK as corroboration.

Executed `test-vectors/entity/entity-taxonomy.json` (5 vectors) against the SDK for the first time:
**32/32 assertions PASS** — 15 metadata + 17 `valid_interaction` assertions. That file is correct.

### B′.3 — **C332-N1 (MED, net-new) — the standard's two entity vector files contradict each other on 5 of 5 shared types, and `entity-jsonld-validation.json` contradicts §2.1 on 8 of 10**

Both files are executed in CI (`sdk-test.yml` → `pytest tests/`): `entity-taxonomy.json` by
`tests/test_entity.py:247`, `entity-jsonld-validation.json` by
`tests/test_schema_validation_vectors.py:38`. Both suites are **green**, and both were green while
the following held.

**(a) Head-to-head, on the 5 entity types both files describe:**

| type | `entity-taxonomy.json` | `entity-jsonld-validation.json` | |
|---|---|---|---|
| device | `[agentic, responsive]`, active, r6=**true** | `[responsive]`, **passive**, r6=**false** | CONFLICT |
| human | `[agentic]` | `[agentic, responsive]` | CONFLICT |
| infrastructure | `[]` | `[responsive]` | CONFLICT |
| oracle | `[delegative, responsive]` | `[responsive]` | CONFLICT |
| society | `[delegative]` | `[agentic, delegative, responsive]` | CONFLICT |

**0 agree / 5 conflict.** Not one shared type is described the same way twice.

**(b) Against the normative table, `entity-jsonld-validation.json`'s MUST-PASS documents diverge on
8 of the 10 entity types they cover** (only `ai` and `accumulator` match §2.1). `policy` additionally
inverts the energy column — §2.1 says **Active**, the vector ships `passive` / `can_r6: false`. The
file's own `meta` declares *"Each 'valid' document MUST pass validation"* and
`"spec_reference": "web4-standard/core-spec/entity-types.md"`.

**(c) Why every gate stays green.** The schema's `EntityTypeInfo` types `entity_type`, `modes`,
`energy`, `can_r6` as four **independent** properties with no cross-field constraint, even though
§2.1 fixes all three dependents for each of the 15 enum members. All **20** `invalid` cases in the
file assert *shape* errors only (missing field, wrong enum member, wrong JSON type,
`additionalProperties`, `minItems`, `uniqueItems`) — **not one asserts a taxonomy-content error**.
Direct probe: `{"entity_type": "infrastructure", "modes": ["agentic","delegative"], "energy":
"active", "can_r6": true}` — a building that autonomously initiates bindings and processes R6 —
**validates**. So `test_schema_validation_vectors.py` passes 32/32 by construction and cannot
observe (a) or (b).

**(d) The schema's own stated purpose is the strongest instrument.** Its `description` reads:
*"Validates output from `EntityTypeInfo.to_jsonld()` and cross-language implementations."* Running
`to_jsonld()` for each type and comparing against the file's MUST-PASS documents:
**2 reproducible / 8 NOT reproducible.** Eight of the ten documents the standard publishes as
canonical output of `to_jsonld()` are documents `to_jsonld()` cannot emit.

**Reach (M3).** `entity-jsonld.schema.json` is **embedded verbatim** in
`sdk/web4/schema_registry.json:1423`, so it ships with the SDK; its context
`schemas/contexts/entity.jsonld` is backed and is covered by the in-window gate `8d3808db`; both
vector files run in CI. Live consumers exist on every leg.

**Prior-art (class ii).** `grep -F` over all **212** audit documents in **both** trees:
`entity-taxonomy.json` **0**, `entity-jsonld.schema.json` **0**, `entity-jsonld-validation.json` **0**.
Nine entity-types passes derived their mirror set **outward**, and `entity-types.md` cites none of
these three — so the derivation was structurally incapable of reaching them.

**Severity MED, not HIGH.** No shipping implementation is wrong today: the Python SDK is 15/15
faithful (B′.2) and the Rust enum is a documented subset (C176-N1). The defect is that the artifact
set that exists to *prevent* cross-language drift cannot detect it, and already exhibits it in its
own examples. **Direction: the standard disagreeing with itself** — this cannot be closed by an SDK
PR. **Routed to operator / standard-editor + the SDK track. NOT self-applied** (choosing which of
three published descriptions of `human` is canonical is an author ruling, and §2.1 is normative
text this seat does not edit).

### B′.4 — **C332-N2 (LOW, net-new; C36 remediation class) — C64-B6 was fixed on the corrected side and re-verified four times on the corrected side, while three sites of the identical overload sat in the mirror**

**C64-B6** (LOW, autonomous): *"§2.3 overloads 'slashed' vs atp-adp-cycle's punitive slashing."*
**C65 applied it** — `5baa160f` (#344), whose own commit body states the scope: **`entity-types.md`
only**, +13/−11, one file. §2.3 L102 now reads *"ADP consumed (permanently destroyed via
maintenance) … **distinct from** the punitive, authority-executed *slashing* of `atp-adp-cycle.md`
§2.4."*

B6 was then re-verified as HELD in **four consecutive passes** — C104 §B-delta.1, C137 §B-delta.1,
C176 §B.1, C214 — each re-checking the *cross-reference into `atp-adp-cycle.md` §2.4*, each
confirming it. **None looked at the artifact that mirrors §2.3.** At HEAD, `grep -rn "slash"` over
`web4-standard/implementation/sdk/` (class i) returns **3 hits**, all carrying the exact overload
B6 removed:

- `web4/entity.py:74` — `PASSIVE = "passive"  # Infrastructure; ADP slashed, no reputation`
- `web4/entity.py:306` — `"""… Passive resources cannot process R6 — their ADP is slashed and they earn no reputation."""`
- `tests/test_integration.py:1531` — `# Infrastructure is passive (no behavioral modes, ADP slashed)`

`entity.py` last moved `759eaefa` (2026-04-17) — **two months before** the remediation, and unmoved
since. **Prior-art (class ii)**: `can_process_r6` = **0** of 212 audit docs; the five docs containing
both `entity.py` and `slash` are C64/C104/C137/C176/C214, and in every one the two tokens belong to
different findings — the `slash` occurrences are all the §2.4 cross-reference re-verification.
**Unbooked.**

**Checked and cleared, so it is not charged:** `entity-types.md:419` (§4.8 Effector kinetic class
`slash | suspend | revoke | terminate | halt`) and `:533` (§5.3 Entity Termination, status `"void"`
or `"slashed"`) are the **punitive** sense and are consistent with atp-adp §2.4. C214 already
adjudicated `:419`. Only the passive-maintenance sense is at issue.

**Severity LOW** — a comment and a docstring, no behavioural consequence; `can_r6` itself is correct.
It earns a row because of *what it says about the method*: a closed finding, re-verified four times,
stayed true one artifact out for **52 days**, because each re-verification followed the citation the
remediation added rather than the subject matter the remediation was about.

### B′.5 — Reach-escalation on **C64-B2** (NOT net-new, per the §0.5 rule)

C64-B2 (MED, cross-track, standing): *"SDK cannot represent a Passive Device — §2.1 'Active or
Passive' + §2.3's non-autonomous devices vs `entity.py` hardcoded ACTIVE."* Re-measured: still true
(`_REGISTRY[DEVICE] = (modes {agentic,responsive}, energy active, can_r6 True)`).

**New reach, three surfaces C64 did not name.** The standard **already publishes a Passive Device**:
`entity-jsonld-validation.json:entity-valid-003` ships `device` as `[responsive]` / `passive` /
`can_r6: false` as a **MUST-PASS** document, in CI, green. Meanwhile `entity-taxonomy.json` ships
`device` as `[agentic,responsive]` / `active` / `can_r6: true`, also in CI, also green — and the
schema is a scalar `EnergyPattern` enum, so it cannot express §2.1's disjunctive "Active or Passive"
cell either.

So B2's framing needs one correction: it is not that *the SDK* cannot represent a Passive Device —
it is that the standard has **three published answers** for Device and no mechanism that notices.
**Routed as reach-escalation on C64-B2. No new severity, no new id.** (This is the pre-registered
rule doing its job: the strongest-looking cell in §B′.3(a) was already booked in 2026-06-16.)

### B′.6 — **C332-N3 (LOW, net-new) — #523 broke 3 of the 5 live inbound line-anchors into this file, and the pass that audited #523 plus the two that re-confirmed its freeze never looked**

Found by following the single `entity-types` hit in `e4a62d7a` (see §B). That commit converts
**one** raw line-anchor in `FRACTAL_ROLE_IDENTITY.md` — `` `core-spec/mrh-tensors.md:246` `` — into a
section link, `[core-spec/mrh-tensors.md §5.1](…#51-critical-principle-trust-is-role-specific)`.
It is the applied remedy for **C318-N1** (mrh-tensors 8th delta, 2026-08-05). **It fixed the one
anchor that pointed at `mrh-tensors.md` and left the other 14 raw line-anchors in the same file.**

**Full inbound census into `entity-types.md`, live files only** (class (i); `git grep -E
'entity-types\.md:[0-9]+'`, excluding `docs/audits/`, `archive/`, `forum/`, `whitepaper/`,
`simulations/`) — **5 anchors across 2 documents**:

| citing site | anchor | resolves at HEAD to | state |
|---|---|---|---|
| `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md:39` | `:518` | ` ``` ` (a bare code-fence close in §5.1) | **BROKEN** — carries a **MUST** |
| `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md:187` | `:518` | same | **BROKEN** |
| `web4-standard/rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md:43` | `:518` | same | **BROKEN** |
| `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md:208` | `:73` | `Reputation updates propagate up fractal chain` | correct |
| `web4-standard/rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md:101` | `:73` | same | correct |

**All three were correct when written, and all three broke on one commit — the one this lineage
audited.** The anchor entered at `b447f33e` (2026-06-28); at that commit `entity-types.md:518` read
`- Support role LCTs as first-class entities` (§7.2 Role Management) — a genuine MUST bullet, exactly
supporting the claim *"Roles are first-class LCT entities … MUST"*. Then **`1354e4c2` (#523, the
Effector §4.8 insertion)** added **+64/−1 = net +63** lines at **`:399`**. The cited bullet is now at
**`:581`**, and **518 + 63 = 581** — the offset is exact.

**Every anchor below the hunk broke; every one above it held.** `:73` sits at line 73, above `:399`,
and is untouched. This reproduces **C318's own sentence** on a different target, independently.

**Why nine passes missed it.** `1354e4c2` is the commit **C214 audited** (its lineage line names it),
and **C252 and C292 each re-confirmed the resulting freeze**. Three consecutive passes examined this
exact commit as the target's most recent mutation. The carry that names the mechanism —
**C129-O2, "inbound raw-line anchors"** — is an mrh-lineage carry: `git grep -l "C129-O2"` over both
audit trees returns **exactly 2 files**, C162 and C318, both mrh-tensors. The census had never been
run on any other target, and the word *"inbound"* appears **0** times in C214, C252 and C292.

**Prior-art (class ii).** `git grep -lF "entity-types.md:518"` over both audit trees = **0**.
**Not a double-book of C318-N1**, which is explicitly scoped to the 7 anchors pointing *into*
`mrh-tensors.md` and enumerates them; none is an entity-types anchor.

**Severity LOW.** The claims the anchors support are **true** and the supporting text **exists** at
`:581` — nothing normative is wrong, a reader is merely sent to a code fence. It earns a row because
it is a **completed causal chain**: a predicted mechanism (C129-O2), an event this lineage audited
(#523), a measurable break (3 of 5), and an in-window remedy that fixed a sibling instance and left
these. **Routed to the standard-editor + the C318/C129-O2 owners** (the durable fix is the one
`e4a62d7a` already demonstrates: section links, not line numbers). **NOT self-applied** — the edits
land in `docs/` and `rfcs/` files this seat does not own, and `RFC-COMPOSITE-ENTITY-IDENTITY.md`
already carries a C318 finding, so a second track editing it would collide.

### B′.7 — I-1 (INFO) — SDK docstring cites the wrong section

`sdk/web4/entity.py:311` `valid_interaction()` documents *"Rules from spec §5.1"*. The interaction
rules are at **§6.1**; §5.1 is *Entity Creation and Birth Certificate*. The **rules themselves are
correct** — verified against §6.1 by the 17 interaction assertions in B′.2 (17/17). A stale pointer
only. Folded into the N1 routing bundle, not separately routed.

---

## §C. Adversarial refute — pointed at the flagship (C332-N1)

- **R1 — "JSON Schema cannot express cross-field constraints; charging their absence is charging the
  format."** **SUSTAINED IN PART, and it changed the finding.** Draft 2020-12 *can* (`if`/`then`,
  `dependentSchemas`), but the corpus-idiom baseline says the standard never does: of the **12**
  top-level schemas in `web4-standard/schemas/` — and of all **24** `.json` files under it
  recursively, including `presence-protocol/` — those using `if`/`then` = **0**,
  `dependentRequired`/`dependentSchemas` = **0**, `allOf` = **0**. The wider scope is published
  because the narrow one was measured first and the wider one is what carries the claim. So *"the schema should have used `if`/`then`"* is
  **withdrawn** — it would charge the exception as the rule, the error C292 §E.2 warns about. What
  survives is not about JSON Schema at all: **the vectors contradict each other and the table**, and
  a `.json` file of expected values needs no schema feature to be correct.
- **R2 — "The `valid` documents are shape illustrations; they were never claims about the taxonomy."**
  **REFUTED by the file's own metadata and the schema's own description.** `meta.spec_reference`
  points at `entity-types.md`; the schema says it *"validates output from `EntityTypeInfo.to_jsonld()`"*;
  8 of 10 are not `to_jsonld()` output. A shape illustration would not need to name the spec twice.
  And R2 cannot explain (a) at all — two *different* shape illustrations of `device` disagreeing on
  three fields is not illustration, it is two independent guesses.
- **R3 — "Already booked as C64-B2 / B9."** **REFUTED for the finding, SUSTAINED for one cell.**
  B2 is `entity.py`'s scalar Device energy; B9 is Task's conditional energy. Neither reaches
  `human`, `society`, `infrastructure`, `oracle`, `policy`, `resource` or `dictionary`, and B2's
  proposed remedy (per-instance energy in the SDK) leaves all 8 divergences standing. The **device
  row specifically** is B2's, and is routed as reach-escalation in B′.5 rather than counted here.
- **R4 — "No reach: dead artifacts nobody runs."** **REFUTED.** Both files execute in CI under
  `sdk-test.yml`; the schema ships embedded in `schema_registry.json:1423`; the context is backed and
  gated by `8d3808db`.
- **R5 — "C176-N1 already covers implementation-vs-taxonomy divergence."** **REFUTED.** C176-N1 is
  enum *membership* (which of the 15 types exist in Rust). This is per-type *metadata* on types that
  do exist, in artifacts C176-N1 never touched.
- **R6 — "The `hub/` window is 17 commits; the real finding is probably there."** **Checked and
  NEGATIVE** — `law.rs` moved only at `5a1d9fa3` (test-fixture vendoring), which **predates this
  window** (`git merge-base --is-ancestor 5a1d9fa3 ff5e7b0b` → true), so the role vocabularies are
  unmoved here; and that face is C286-N1 regardless.

**The flagship survives.** R1 landed and narrowed it — the charge is the vectors' content, not the
schema's expressiveness.

Pointed separately at **N3**:

- **R7 — "This is C318-N1 under a new target."** **REFUTED.** C318-N1 enumerates 7 anchors pointing
  into `mrh-tensors.md` and names each; **none is an entity-types anchor**, and its cause is mrh's
  own C163 remediation, not #523. `git grep -lF "entity-types.md:518"` over both trees = **0**.
- **R8 — "Line anchors drift constantly; this is noise, not a finding."** **REFUTED on
  specificity.** The census is 5, not "many"; the break rate is **3 of 5**; the cause is a **single
  named commit** with an offset that reconciles exactly (`518 + 63 = 581`); and the split is not
  random — it is entirely predicted by position relative to `:399`.
- **R9 — "The anchors were always wrong; nothing broke."** **REFUTED by reconstruction.** At
  `b447f33e`, `entity-types.md:518` was `- Support role LCTs as first-class entities`. The anchor was
  correct when written. This is drift, not a never-resolving pointer, and the distinction is what
  makes #523 the cause.

---

## §D. Disposition & routing — **row count 10**

| # | Finding | Class | Disposition |
|---|---|---|---|
| 1 | `entity-types.md` byte-frozen **24 d** (`1354e4c2..HEAD` empty, blob `a2dda417`, 804 L) | §A | **CONFIRMED** — 6th consecutive zero-mutation pass |
| 2 | 7 C65 remediations + §4-preamble count + **9** carries (C8-L3, C23-H1, C24-H1, B2/B9, B7, B10/B11, B12) | §A | **HELD / STAND** by construction |
| 3 | Inherited deferral ledger **g1, g2, g3, g4** | §A.3 | **4 of 4 discharged** — g1/g2/g3 **NEGATIVE**, g4 re-derived (**Rust 9 / Python 15**) |
| 4 | §2.1 table (15 rows) ↔ `sdk/web4/entity.py` `_REGISTRY` | §B′.2 | **NEGATIVE — 15/15 exact**, first time measured; makes the SDK an independent witness for §2.1 |
| 5 | `entity-taxonomy.json` executed vs SDK | §B′.2 | **32/32 PASS** — first execution in corpus history |
| 6 | `entity-jsonld-validation.json` executed vs its schema | §B′.3(c) | **32/32 PASS** — and structurally incapable of failing on content |
| 7 | **C332-N1 — two entity vector files, 5/5 shared types in conflict; 8/10 diverge from §2.1; 8/10 not reproducible by `to_jsonld()`** | §B′.3 | **MED, NET-NEW → operator / standard-editor + SDK track. Zero mutation this pass.** |
| 8 | **C332-N2 — C64-B6's overload survives at `entity.py:74`, `entity.py:306`, `test_integration.py:1531`; remediation was `entity-types.md`-only and was re-verified 4× on the corrected side** | §B′.4 | **LOW, NET-NEW → SDK track** (one comment + one docstring; `consumed`/`destroyed via maintenance`) |
| 9 | **C332-N3 — 3 of the 5 live inbound line-anchors into this file are broken; all three are `:518`, all three were correct when written, all three broke on `1354e4c2` (#523), offset `518+63=581` exact** | §B′.6 | **LOW, NET-NEW → standard-editor + C318/C129-O2 owners** (remedy: section links, as `e4a62d7a` already demonstrates) |
| 10 | **C64-B2 gains three consumer surfaces** (`entity-valid-003` publishes a Passive Device; `entity-taxonomy.json` publishes an Active one; scalar `EnergyPattern` cannot express "Active or Passive") | §B′.5 | **REACH-ESCALATION on C64-B2 — no new id, no new severity.** Framing corrected: not "the SDK cannot represent it" but "the standard publishes three answers." |

Also recorded, not routed separately: **I-1** (`entity.py:311` cites §5.1 for §6.1 rules) folds into
the N1 bundle; `e4a62d7a` **NEGATIVE**; `hub/` **nothing found, nothing routed**;
`entity-types.md:419`/`:533` "slash" **checked and cleared** as the punitive sense.

**C332 distinct net-new: 3 (1 MED + 2 LOW).** **C333 = declared NO-OP on the spec side** — no
finding is auditor-applicable *to `entity-types.md`*: N1 needs an author ruling on which of three
published descriptions is canonical, N2 is in the SDK track's tree, and N3's edits land in
`web4-standard/docs/` + `web4-standard/rfcs/` files another track already has a finding against.
**Zero mutation of the standard this pass.**

### Accountability review-gate

**n/a — doc-only delta.** No surface is created or changed; no diff to the standard is proposed; no
consequential act is reachable from this commit. Stated rather than omitted, per the self-audit rule.

---

## §A.4. Fresh deferral ledger for **C372** — **row count 6**, members named

| id | member | why deferred | how to discharge |
|---|---|---|---|
| **d1** | Did N1 get an author ruling — is `human` agentic-only (§2.1 / SDK) or agentic+responsive (`entity-valid-003`… `entity-valid-001`)? | author/concord call, not auditor's | re-run the 3-way compare in §B′.3(a)/(b); if the table moved, §A is no longer HELD-by-construction |
| **d2** | Did N2's three SDK sites change? | SDK track's tree | `grep -rn "slash" web4-standard/implementation/sdk/` — expect 3 → 0 |
| **d3** | **`web4-standard/schemas/contexts/entity.jsonld` was never opened this pass.** It is backed (gate `8d3808db`) but its *term definitions* were never read against §2.1 | out of the pre-registered window; opening it mid-pass would have been the free-parameter error v26 names | read it against §2.1 and against `entity-jsonld.schema.json`'s `$defs`; a 4th published description of the taxonomy would escalate N1 |
| **d4** | The other **11** top-level schemas in `web4-standard/schemas/` — do any ship MUST-PASS vectors that contradict their own spec? N1's mechanism is not entity-specific | scope: this is `entity-types.md`'s slot | run §B′.3(d)'s reproducibility instrument per schema; **prior art check first** — C328 executed `lct-jsonld-vectors.json`, C322 the dictionary artifacts |
| **d5** | `web4-standard/docs/FRACTAL_ROLE_IDENTITY.md` + `rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md` — **only their line-anchors were gated (N3); their *claims* were never read against §3** | N3 consumed the anchor question; the content question is a second, larger gate that would have widened this pass mid-flight | read both against §3/§7.2 as M2 members at C372; check first whether the N3 remedy landed (`grep -c 'entity-types\.md:518'` → expect 3 → 0) |
| **d6** | `web4-standard/DICTIONARY_INTEGRATION_SUMMARY.md` inbound referrer vs §10 | same | same; check against C322's dictionary lineage for prior booking before raising |

**Do not inherit this list as a mirror set.** It is a list of things this pass did **not** measure.

**Rotation**: next in fixed order is `errors.md` (last pass C294) → **C334**.

---

## §E. Lessons

1. **The outbound derivation cannot see what the target does not cite — and this target cites none
   of its own machine-readable artifacts.** Nine passes derived the mirror set from what
   `entity-types.md` points at. The three artifacts that encode §2.1 for machines point *at it*, and
   never the reverse. The inbound half (`git grep -F` on the target's path) found all three in one
   command. This is C322's mechanism on a different file; the fix is to always run both directions.
2. **Executing an artifact and validating an artifact are different acts, and the corpus conflates
   them.** All 64 assertions pass. Both CI suites are green. The green is *produced by* the defect:
   one suite compares vector-A to the SDK, the other compares vector-B to a shape schema, and
   nothing compares vector-B to §2.1 or to vector-A. A gate's passing tells you what it can see.
3. **Following the remediation's citation is not the same as re-checking its subject matter.** B6
   was re-verified four times over 53 days. Each pass checked the cross-reference the *fix* added —
   into `atp-adp-cycle.md` §2.4 — and each was right. Not one checked the artifact that mirrors the
   *sentence* being fixed. The guard named a pointer, so the pointer is what got watched.
4. **The pre-registered reach-escalation rule paid for itself.** The most striking cell in the
   flagship table — Device described three ways — is **C64-B2**, filed 2026-06-16. Without the rule
   it would have led the headline as net-new. Filed as escalation, it still improved B2 (correcting
   its direction), which is what an escalation is for.
5. **A carry that names a mechanism is scoped to the lineage that filed it, and the mechanism is
   not.** C129-O2 — *"inbound raw-line anchors"* — has been carried, re-verified and finally
   **materialized** entirely inside the mrh-tensors lineage (`git grep -l "C129-O2"` = 2 files, both
   mrh). Meanwhile #523 broke 3 of this file's 5 inbound anchors, and C214 — the pass that audited
   #523 — plus C252 and C292 never ran the census, because the census belonged to another file's
   ledger. **When a sibling lineage publishes a mechanism, run its instrument on your own target
   once.** It cost one `git grep` here.
6. **"An audit-doc commit" is a classification, not a measurement.** `e4a62d7a`'s subject line reads
   `audit(C320): …`, and it ships two RFC edits and a live standard-doc edit. The §B cell was first
   written as *"no normative surface, does not route here."* The one hit it actually had is the
   entire provenance of N3. A window sweep that reads subject lines is not a window sweep.
7. **A line-shape grep is not an enumeration.** `grep -cE '^\s+[A-Z_]+ = '` on `entity.py` returned
   **9**, exactly matching the Rust variant count, and matched **zero** `EntityType` members. A
   coincidence that flattering is what the post-write re-run exists to catch.
