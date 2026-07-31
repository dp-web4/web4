# C292 Audit: `entity-types.md` — 7th-Delta Re-Audit (8th Pass)

**Date**: 2026-07-30
**Auditor**: Autonomous session (Legion, web4 track) — firing `20260730-180011`
**Document**: `web4-standard/core-spec/entity-types.md` (804 lines, blob `a2dda417`)
**Lineage**: C8 → C26 → C64 → C65 (remediation, 7 applied) → C104 → C137 → C176 → C214 (#523 Effector §4.8) → C252 (RE-FROZEN, 0 net-new) → **C292 (this audit)**
**Window**: `ea68934c..ff5e7b0b` — 62 commits, 2026-07-22 → 2026-07-30. **Rotation**: `C252 + 40`; step 0 (queue) and step 0.5 (own standing blocks) both clear, #589/#590 merged.

## Headline: 1 MED net-new — the standard publishes two incompatible structures for the Role LCT, and the one in the core-spec has zero implementers

`entity-types.md` is still byte-frozen. The finding did not come from the target; it came from
**re-deriving the mirror set from subject matter** (method carry v7). `entity-types.md` §3 is the
canonical home of "Roles as First-Class Entities." `web4-standard/ontology/role-extension-schema.md`
+ `role-extension.ttl` — **promoted into the standard on 2026-07-08** (`7201a765`) — define the law
attached to a role LCT. **Neither has ever been read against the other**: `grep -c 'role-extension'`
over all seven prior entity-types audit docs = **0, 0, 0, 0, 0, 0, 0** (C26/C64/C104/C137/C176/
C214/C252). This is the same shape as C280 (`hub/` never gated in 7 society-spec passes).

**Pre-registered before the sweep** (v7 + policy conditions 1/3): **M1** = artifacts independently
realizing the entity-type taxonomy or the role registry — `web4-core/src/{lct,role,role_extension}.rs`,
`web4-standard/implementation/sdk/web4/{entity,role}.py`, and (never gated here) `hub/`. **M2** =
`web4-standard/ontology/*.{ttl,jsonld,md}`, schemas, vectors. **M3 = admission by REACH, not by
verdict** — admitted iff a divergence would be a finding against *something*. **P2 stop rule
(C274/C282) pre-registered**: NEGATIVE gate + no routable §B′ finding ⇒ short no-op record. It did
not fire — the gate returned POSITIVE.

---

## §A. Regression — byte-frozen ⇒ HELD by construction

`git log 1354e4c2..HEAD -- web4-standard/core-spec/entity-types.md` = **empty**; blob at HEAD =
`a2dda4178b96ffc44e45a456917f4a129914bda7`, 804 lines — byte-identical to the C214/C252 snapshot,
**16 days** frozen. Every C214/C252 conclusion that is a property of the file text HOLDS by
construction: the **7 C65 remediations**, the **§4-preamble count edit** (`:281`), and the **9
standing carries** (C8-L3, C23-H1, C24-H1, B2/B9, B7, B10/B11, B12). **0 regression possible.**
C214-N1 not re-opened; `git log ea68934c..HEAD -- .../reputation-computation.md` = empty.

---

## §B. Window authority sweep — what landed claiming authority over this subject matter

**#579 `dictionary-as-context-mandatory-role.md` (`4665a430`) — ALREADY BOOKED, not net-new.**
The proposal would move Dictionary from entity-types §10's "Specialized Entity" framing into a
society role tier. Its effect on `entity-types.md:281` is **already adjudicated at C280-N3**, which
enumerated that line as one of eight sites going stale *only under the base-mandatory branch* of
the proposal's own open question 1, and routed it to the proposal author. Re-raising it here would
double-book. **Status confirmed, reach unchanged**; authority remains PROSPECTIVE.

**#580 `resilience-to-incomplete-information.md` (`954ee391`) — precedent survey, 1 positive.**
entity-types' fail-closed sites agree with "absence never grants": §8.1 type immutability
(`MUST NOT change`), §3.4 step 1 and §7.2 "Verify citizen role exists before other role
assignments." Recorded as a **positive** (same polarity as C284-N2), not as a finding.

**`01f410db` `fix(ontology): web4:Tensor superclass + web4:observationCount` — NEGATIVE, and here
is the token.** The commit touches `web4-standard/ontology/t3v3-ontology.ttl` **only**
(`git show --stat`: 1 file, +14/−4). entity-types' entire tensor surface in an emitted example is
`:209 "t3_scores": {...}` and `:210 "v3_outcomes": {...}` — grep for `web4:Tensor|observationCount`
over `entity-types.md` = **0**. Both example values are **elided**, so no `rdfs:domain` correction
can falsify them. Schema-vs-emitted-examples (method carry v6) returns **NEGATIVE**.

**`a135a597` (#587) / `780af6ef` / #591-#592 (AssuranceReceipt) / #601** — read; their
role-vocabulary face is adjudicated in §B′.2, their assurance face is booked at SAL C246-N1/C286-N3,
and neither touches the entity **taxonomy**.

---

## §B′. Mirror gate — POSITIVE

### B′.1 — Standing mirror carries, re-measured at HEAD (not transcribed)

| Carry | Instrument @ `ff5e7b0b` | Result |
|---|---|---|
| **C176-N1** (Rust `EntityType` coverage) | `lct.rs:28-53` variants: Human, AiSoftware, AiEmbodied, Organization, Society, Role, Task, Resource, Hybrid = **9 variants / 8 spec types** | **STANDS unchanged** — 7 absent: Device, Service, Oracle, Accumulator, Dictionary, Policy, Infrastructure. Python `entity.py` carries all 15. |
| **C176-N2** (AI-split vs `HardwareBinding` axis) | same enum, unmoved | **STANDS** (INFO) |
| **Effector SDK mirror** (C252 §B′.1) | `grep -ri effector web4-core/src web4-standard/implementation/sdk/web4` = **0 hits** (token: `effector`) | **STILL ABSENT** — HUB-track Phase-2 not landed; already routed (SESSION_FOCUS 0d). **NOT net-new.** |
| **ratchet / citizenship / operational_key faces** | C252 §B′.3-4 | **DISJOINT, not re-opened** (booked LCT C248-N1/N2, SAL C246-N1) |

### B′.2 — `hub/` admitted by REACH, and it is already-booked on one leg, disjoint on the other

Applying [[feedback_does_the_impl_agree_with_itself]] first (policy condition 4): the hub carries
**two** role vocabularies in one binary — `law.rs:41 KNOWN_ROLES` (7 society-role names, including
`applicant`, which no spec registers) and `law.rs:83 KNOWN_CONSTELLATION_ROLES` (5
`role:constellation:*` session-capacity strings). Their mutual disagreement is **C286-N1**, routed
to HUB two days ago and **re-verified frozen here**: `git diff 70381838..HEAD -- hub/hub-lib/src/law.rs`
matching `KNOWN_ROLES|KNOWN_CONSTELLATION|"sovereign"|applicant` = **empty** (the one in-window
touch, `5a1d9fa3`, vendors test fixtures). **Not re-booked** — book-once.

The *constellation* namespace is **not** disjoint from this target, but not net-new either: it is
published in-standard at `ontology/role-extension-schema.md:190-194`, and C268-INFO-1 holds the
"constellation vocabulary is now in-standard" watch-item. Net-new is what that same document does
to §3.3 — below.

### B′.3 — **C292-N1 (MED, net-new) — `entity-types.md` §3.3 and `ontology/role-extension.{md,ttl}` describe the same object incompatibly; only the unimplemented one is in the core-spec**

Both structures attach the role's law to **the same object**: §3.3 nests `role_definition` *inside*
the Role LCT; `role:boundToRoleLct` binds an extension *to* a Role LCT id. Measured at `ff5e7b0b`:

| | core-spec side | ontology side |
|---|---|---|
| site | `entity-types.md:192` §3.3 "Each Role LCT contains:" | `ontology/role-extension.ttl` + `-schema.md` (promoted `7201a765`, 2026-07-08) |
| capability shape | `permissions: ["capability:read", …]` — **free-text strings** | 5 typed `role:Affordance` subclasses (Tool/Channel/Repo/WriteClass/CliFlag) |
| scope shape | `scope: {domain: "specific area of responsibility", boundaries: "limits of authority"}` — **prose** | `role:Scope{rangesOver, oracleConsultSet, oracleWriteSet, atpBudget}`, fail-closed defaults |
| composition | absent | `defaultVerdict` (REQUIRED), `foldsUnder` (REQUIRED, non-empty), `authoredUnder`/`lintVerdict` witness |
| implementers | **0** | `web4-core/src/role_extension.rs` — `RoleExtension`, `RoleEntity::issue`, `RoleRegistry` (deployed) |

**Instruments** (all re-run after this finding was written, @ `ff5e7b0b`):
1. `grep -rn "role_definition\|roleDefinition" . --exclude-dir=target --exclude-dir=audits` → **4 hits in 4 files**: `web4-standard/core-spec/entity-types.md:192`, `web4-standard/core-spec/web4-society-authority-law.md:393` (only `{"purpose": …}`), and 2 `forum/nova/web4-sal-bundle/` mirrors of those same two files — so **2 live standard files, 0 elsewhere**. **Zero code, zero JSON schema, zero test vector.**
2. `grep -rn "role-extension\|role_extension" web4-standard/core-spec/` → **0 files**. Reverse: `grep -ic "entity-types\|core-spec\|agency\|AGY\|r6Caps" ontology/role-extension-schema.md` → **0**. Cross-citation is **zero in both directions**.
3. Idiom baseline (so the silence is not charged as idiom): core-spec files citing *any* `ontology/` artifact = **6 of 30** (`atp-adp-cycle`, `hub-law-schema`, `lct-capability-levels`, `LCT-linked-context-token`, `mrh-tensors`, `t3-v3-tensors`). The corpus **does** cross-reference its ontology; entity-types is the exception on the one ontology artifact that is its own subject matter.
4. The Rust `Lct` struct (`lct.rs:98-181`, **16** public fields — `id, entity_type, status, public_key, created_at, created_by, hardware_binding, parent_id, lineage_depth, binding_proof, mrh, legacy_alias, attestations, citizenships, operational_keys, authority_ratchet`) has **no** role-definition field — the deployed model *separates* the extension and binds by id, where §3.3 *nests* it. **(This cell was published as "11" in the draft and corrected by the mandated post-write re-run — the instrument is the finding's audit trail, [[feedback_publish_the_instrument]].)**

**What makes it a finding rather than a version skew**: `role-extension-schema.md` §1.2 states the
load-bearing requirement verbatim — *"an affordance is **not free text**. It is a typed grant the
launcher can check a concrete launch invocation against **before** spawning"* — i.e. the promoted
document diagnoses exactly the shape its own standard still publishes at §3.3, **without naming
it**. And §7.2's RFC2119 **MUST** "Track performance history within role LCTs" is a **non-join, not
an absence** (the C274 lesson): the dimension *is* implemented — `RoleAssignment{role_trust: T3,
role_value: V3}` plus the un-collapsed `(role_lct, occupant_instance_lct)` reputation stream that
role-extension-schema's own H1 makes concord-binding — but **not "within role LCTs."**
`grep -rl "performance_history\|performanceHistory" . --exclude-dir=target --exclude-dir=audits`
→ 7 files, of which the only non-`archive/`, non-`simulations/`, non-`whitepaper/archive/`,
non-`forum/` hit is **`entity-types.md` itself**. Live implementers: **0**.

**Severity MED, not HIGH**: §3.3 carries no RFC2119 keyword (the doc's Notation §, `:5-7`, scopes
normativity to all-caps keywords), and nothing implements §3.3, so no shipping interop breaks
today. **Direction is not "SDK lags spec"** — this is the standard disagreeing with itself
([[feedback_standard_disagrees_with_itself]]), so it cannot be closed by an SDK PR; it needs a
ruling on which shape is canonical. **Routed to operator/standard-editor (dp) + the Phase-0 concord
holders (HUB/CBP). NOT self-applied.**

---

## §C. Adversarial refute — pointed at the flagship

- **R1 — "This is C234's REFUTED `RoleExtension::Scope` collision under a new name."** **REFUTED.**
  C234 anchored on **§4.7's Agency Grant** (`grant.scope.r6Caps.resourceCaps`) — a `Web4AgencyGrant`
  with `grantId`/`client`/`agent`/`duration`/`signatures`, i.e. a **Client→Agent delegation**, a
  different object from the Role LCT. N1 anchors on **§3.3**, and its claim is structural (two
  structures claim to be the law of the *same* role LCT), not lexical. The guard does not reach it.
- **R2 — "Missing cross-citation is a corpus idiom."** **REFUTED by baseline**: 6 of 30 core-spec
  files cite an `ontology/` artifact, each its *own* counterpart. Silence here is the exception.
  (The check that killed the C274 flagship; it does not kill this one.)
- **R3 — "§3.3 is illustrative JSON; an example cannot conflict with a schema."** **PARTIALLY
  SUSTAINED**, and priced in: it is why severity is MED and the charge is *canonical-structure
  divergence*, not *normative violation*. It does not dissolve the finding — §7.2 carries MUSTs over
  the same object, one of which ("performance history within role LCTs") the deployed model declines.
- **R4 — "Already booked (B15 / C268-INFO-1 / C16-M1 / C286-N1)."** **REFUTED, four ways.** B15 is
  composition *ordering*; C268-INFO-1 is the *word* "constellation" moving in-standard; C16-M1 is
  the role-*name* taxonomy; C286-N1 is `KNOWN_ROLES` vs `society-roles.md`. None is the Role-LCT
  *field structure*: `grep -c "role_definition"` over every prior entity-types audit = **0**.
- **R5 — "`role_definition` is implemented under another name."** **REFUTED**: the `Lct`'s 16 fields
  contain no role-definitional slot; the deployed role law lives in a separately-bound `RoleExtension`.

**The flagship survives.** One refutation (R3) lands partially and is reflected in the severity.

---

## §D. Disposition & routing

| Finding | Class | Disposition |
|---|---|---|
| `entity-types.md` byte-frozen 16d (`1354e4c2..HEAD` empty, blob `a2dda417`) | §A | **CONFIRMED** |
| 7 C65 remediations + §4-preamble count + 9 carries | §A | **HELD / STAND** by construction |
| #579 → `entity-types.md:281` | §B | **ALREADY BOOKED at C280-N3** — not re-raised |
| #580 precedent survey | §B | **1 positive** recorded (§8.1, §3.4 step 1, §7.2) |
| `01f410db` ontology mover | §B | **NEGATIVE** — touches `t3v3-ontology.ttl` only; §3.3's tensor values elided |
| hub `KNOWN_ROLES` ↔ `KNOWN_CONSTELLATION_ROLES` | §B′.2 | **C286-N1, re-verified frozen; not re-booked** |
| C176-N1 / C176-N2 / Effector mirror / ratchet+LCT faces | §B′.1 | **STAND / DISJOINT** — unchanged routing |
| **C292-N1 — §3.3 `role_definition` vs `ontology/role-extension.{md,ttl}`** | §B′.3 | **MED, NET-NEW → operator/standard-editor (dp) + Phase-0 concord holders. Zero mutation this pass.** |

**C292 distinct net-new: 1 (MED).** **C293 = NOT a no-op, but NOT self-executable**: N1 asks which
of two published structures is canonical — an author/concord ruling. Do **not** manufacture an
entity-types edit; carry N1 into the operator DESIGN-Q memo alongside C23-H1/C24-H1/B7/B2/B9/B10/B11.

**Forward guards (next entity-types delta ~C332):** (1) re-run instrument 1 — did anything gain a
`role_definition` implementer, or did §3.3 gain a `role_extension` slot? (2) re-run instrument 2
both directions — did either side acquire a cross-reference? (3) `grep -ri effector` over
`web4-core/src` + Python SDK — has HUB Phase-2 landed? (4) re-count `EntityType` variants at HEAD;
do not transcribe **9/8-of-15** from here.

**Rotation**: next in fixed order is `errors.md` (last pass C254) → **C294**.

---

## §E. Lessons

1. **A seven-pass blind spot is found by asking what *implements the subject matter*, not by
   re-running last pass's mirror list.** `role-extension.{md,ttl}` has been inside `web4-standard/`
   since 2026-07-08 and is cited by nine *other* files' audits — never by this file's, whose §3 it
   directly re-shapes. The frozen target was never the place to look.
2. **The corpus-idiom baseline cuts both ways.** The discipline that *killed* the C274 flagship
   (bare `witnesses` is the majority idiom) here *sustained* one: 6 of 30 core-spec files cite their
   ontology counterpart, so this silence is the exception. Run the baseline before deciding whether
   a silence is a defect — the answer is not predictable from the charge.
3. **Non-join, not absence** (C274 discipline, second application). §7.2's "performance history
   within role LCTs" MUST is unimplemented, but the *dimension* is implemented deliberately
   elsewhere — un-collapsed `(role_lct, occupant_instance_lct)` by concord. Charging an absence
   would have hidden the real question: *where does the role's law live*.
4. **The mandated post-write re-run is not ceremony.** It caught this pass's own `Lct` field count
   (11 → **16**) before commit — the exact cell-class that blocked #589 and #590.
