# C428 — `multi-device-lct-binding.md` Ninth Delta Re-Audit (the quorum that protects a constellation from one compromised device becomes unsatisfiable exactly when the constellation is small enough to need it)

**Target**: `web4-standard/core-spec/multi-device-lct-binding.md`
**Date**: 2026-08-21 · **Slot**: C428 (rotation arithmetic: C388 + 40)
**HEAD**: `cfc7f96d` · **Prior pass HEAD**: `cd39cfab` (C388, PR #716)
**Lineage** (inclusive rule — every lineage has a non-C-numbered
`…-internal-consistency-…` member, and it counts):
`multi-device-lct-binding-internal-consistency-2026-05-28`, C36, C80, **C81 (remediation)**,
C120, C152, C268, C308, C348, C388 = **10 prior members**; deltas C80 (1st) … C388 (8th)
⇒ **C428 is the 9th delta**. (The file skipped one rotation cycle, recorded at C268.)

**Mutation: ZERO.** One new file: this one.

---

## Headline

**Six passes have asked whether `remove_device`'s quorum is computed correctly. None asked
whether it can be met.** It cannot, below a device-count floor that the standard never names
and that every shrinking constellation reaches and then never leaves. At two devices the
answer is absolute: **a two-device constellation can never remove either device, ever** —
because §3.5 excludes the device being removed from the authorizing set (`:722`) while §5.2
requires *all* devices at `n ≤ 2` (`:989-990`), so the quorum is one larger than the set that
can satisfy it. The floor is in the **spec's own pseudocode** (`:728`), not only in the SDK
(`binding.py:340`), and it survives **both** horns of C376-N1's unresolved
stored-vs-derived reading of `recovery_quorum` — it merely moves: under the *stored* reading
a constellation of `n₀` devices freezes with **exactly `default_recovery_quorum(n₀)`**
devices permanently unremovable (verified closed-form for every `n₀ ∈ [2,20]`; a 10-device
constellation freezes at **5**), and under the *derived* reading it freezes at **2**.

**The consequence is not decorative.** §5.1's threat table (`:966`) answers the threat
*"Single device compromise"* with the mitigation *"Quorum requirement for sensitive ops"*.
At the floor the compromised device is a member of **every** satisfying quorum, so the
mitigation names the attacker as a required signatory. §5.3's compromise response opens with
*"**Immediate**: Revoke device LCT"* (`:1001`) and there is no path from that sentence to a
revoked device. The one escape that survives execution — enrol a replacement device *first*,
then remove — is written down **nowhere**, contradicts the word *Immediate*, and returns the
constellation to the same terminal state.

**Severity is capped honestly, and the cap is the interesting part.** No `MUST` in the target
is violated: §7.2 `:1095`'s *"Enforce recovery quorum for identity recovery"* is **satisfied**
— enforcing the quorum is precisely what makes removal unsatisfiable. What bites is one rung
down: the corpus's two revocation-conditioned prohibitions — target `:290` (*"A revoked
device's keys MUST NOT authorize any further operations"*) and `security-framework.md:81`
(*"stale replicas MUST NOT restore authority to a revoked device"*) — have an **antecedent
`§3.5` cannot produce** at the floor. A prohibition whose trigger is unreachable is not
enforcement; it is decoration. **MEDIUM.**

---

## Severity legend (this lineage's own rubric, C348 `:55-61`)

| level | meaning |
|---|---|
| HIGH | a conformant implementation reading the spec is led into a wire-incompatible or unsafe result |
| MEDIUM | a normative statement is unsatisfiable, self-contradictory, or contradicted by the standard's own machine-readable artifacts; **or** a ledger row's live status is false at HEAD, or rests on evidence that cannot reach it |
| LOW | a defect in an in-standard or in-ledger artifact that does not change what a conformant implementation emits |
| INFO | a re-verification, an exclusion re-held, a routed guard discharged, or an instrument note |

---

## §A — Freeze, measured against C388's published 12-blob baseline

Window `cd39cfab..cfc7f96d` = **28 commits** (`git rev-list --count`), by tree:
`web4-standard/` **1**, `web4-core/` **0**, `hub/` **4**, `docs/` **19**, `sdk/` **0**,
`simulations/` **0**.

| artifact | C388 baseline | HEAD `cfc7f96d` | |
|---|---|---|---|
| `web4-standard/core-spec/multi-device-lct-binding.md` | `b979ea7d` | `b979ea7d` | frozen |
| `web4-standard/implementation/sdk/web4/binding.py` | `857f8040` | `857f8040` | frozen |
| `web4-standard/test-vectors/binding/binding-vectors.json` | `dc969641` | `dc969641` | frozen |
| `web4-standard/implementation/sdk/tests/test_binding.py` | `ad7fd3dd` | `ad7fd3dd` | frozen |
| `web4-standard/implementation/sdk/tests/test_integration.py` | `e3c23c00` | `e3c23c00` | frozen |
| `web4-core/src/ratchet.rs` | `806882b1` | `806882b1` | frozen |
| `docs/specs/attestation-envelope.md` | `c2f604aa` | `c2f604aa` | frozen |
| `web4-standard/implementation/sdk/web4/attestation.py` | `37a7c673` | `37a7c673` | frozen |
| `web4-core/python/web4_core/trust/attestation/envelope.py` | `c3046043` | `c3046043` | frozen |
| `web4-standard/test-vectors/attestation/attestation-vectors.json` | `fecbc695` | `fecbc695` | frozen |
| `web4-core/src/lct.rs` | `2e9d4586` | `2e9d4586` | frozen |
| `hub/hub-lib/src/hub.rs` | `fd45f9ce` | `fd45f9ce` | frozen |

**12 of 12 identical.** Target byte-frozen at `a6cbde92` (2026-06-21, C81 remediation, #372)
— **61 days, 9 passes**. `security-framework.md` `63889457` at both ends (see INFO-1).

**C388 guard 1 — which N1 fork landed? Neither.**
`trust_ceiling_by_config` case 6 still reads `{"input_anchor_types": [phone_secure_element,
fido2, tpm2, software], "expected_ceiling": 0.98}`; §4.2 precedence rule 2 (`:897-900`) is
unchanged word for word. Per C388's own test — *"If vector case 6 still reads `0.98`, fork (a)
did not land regardless of what the spec text says"* — **C388-N1 stands open after one full
window**, jointly with C308-N1.

**A frozen target is not an exhausted target (v69).** Nine passes have certified this file
against its table, its vectors, its mirror and a rival table. This pass asked the other
question: *what does the spec declare that nothing can execute?*

---

## §B — The inbound sweep as a set difference (C388 guard 5, matcher unchanged so counts compare)

Verb/term set pre-registered before running: domain word = `constellation` (the domain's own
word — the target never writes its own filename, so a filename sweep is a citation-graph
query and structurally cannot return an orphan). Same 7 roots, same 5 exclusions as C388.

| | command | C388 | C428 |
|---|---|---|---|
| filename sweep (citation query) | `git grep -li "multi-device-lct-binding" -- .` minus `docs/audits/` | 21 | **21** |
| domain-word sweep, tree-bounded | `git grep -li -E "constellation" -- web4-standard/ web4-core/ hub/ docs/specs/ docs/designs/ core/ forum/`, minus `archive/ sessions/ simulations/ **/target/ docs/audits/` | 48 | **50** |
| **residue** = domain ∖ filename (`comm -23`) | | 41 | **43** |
| residue rows with ≥1 commit in window | `git rev-list --count cd39cfab..HEAD -- <f>` per row | 8 | **3** |

The two **new** residue rows (`comm -23` of the domain sweep at HEAD against the same sweep
run at `cd39cfab`):

| row | classification |
|---|---|
| `hub/docs/PRD_ROLE_SCOPE_BRIDGE.md` (added `5f011de5`, 2026-08-18, in-window) | **The hub constellation-MFA / assurance-tier cluster.** C308 ruled this reach-escalation; **C286-N3 and C288-N2 own it** (C388 guard 7). **NOT re-charged.** |
| `web4-standard/core-spec/interface-planes.md:73` (added `2462881f`, 2026-08-19, in-window) | *"only the process or constellation itself"* — the word in its **generic process** sense, not this target's subject matter. Not a claim about device constellations. |

The third postdating row is `hub/README.md` (same cluster).

**Recorded negative, second consecutive.** C388's guard 5 pre-registered the reading: *"a
negative followed by a negative is a fact about the target; a negative followed by a positive
dates the change."* This is the negative. In 28 commits nothing outside the hub cluster made
a claim about device constellations. **This pass's yield is entirely from §C's machine
checks** — as C388's was.

### B.2 — Third direction (v28) / outward trees (v29), and an instrument note

`git log -S "constellation_trust_ceiling" cd39cfab..HEAD` returns **1** commit — and the
commit is **`a68adb93`, C388's own audit document**. Path-bounded
(`-- . ':!docs/audits'`) it returns **0**. See INFO-3: a `-S` probe over a window becomes
self-contaminating the moment the pass that ran it commits its own findings.

`git log -S "default_recovery_quorum" cd39cfab..HEAD` = **0**.
`git log -S "remove_device" cd39cfab..HEAD` = **0**.

---

## §C — Machine checks, run before any re-reading (v43)

### C.1 — Every fenced `python` block in the target, executed

`git grep -n '^```'` over the target yields **21** fenced blocks, **8** of them `python`.
All 8 were extracted and `exec`'d in a bare namespace:

| block | lines | result | defines |
|---|---|---|---|
| §3.1 genesis | `:337-378` | **EXEC OK** | `genesis_enrollment` |
| §3.2 additional enrolment | `:428-486` | **EXEC OK** | `enroll_additional_device` |
| §3.3 cross-witness | `:494-535` | **EXEC OK** | `cross_witness` |
| §3.4 trust computation | `:549-703` | **EXEC OK** | `compute_constellation_trust`, `ANCHOR_TRUST_WEIGHT`, `constellation_trust_ceiling`, `compute_coherence_bonus`, `compute_cross_witness_density` |
| §3.5 device removal | `:711-769` | **EXEC OK** | `remove_device` |
| §3.6 identity recovery | `:777-841` | **EXEC OK** | `recover_identity` |
| §4.3 trust decay | `:906-927` | **EXEC OK** | `witness_freshness`, `days_since_last_witness` |
| §5.2 recovery quorum | `:978-994` | **EXEC OK** | `default_recovery_quorum` |

**8 of 8 parse and define.** Recorded as a negative — no prior pass in this lineage had
executed the blocks outside §3.4.

### C.2 — The spec's own fenced functions against the shipped vectors *and* the SDK mirror

`binding-vectors.json` publishes **6** groups; **4** carry `cases` (18 cases total), 2 are
single scenarios. The two groups whose spec-side implementation had never been executed:

| group | cases | spec fenced fn | SDK | agreement |
|---|--:|---|---|---|
| `witness_freshness_decay` (§4.3) | 10 | `:906` `witness_freshness` | `binding.py:214` | **10/10 · 10/10** |
| `recovery_quorum_calculation` (§5.2) | 8 | `:978` `default_recovery_quorum` | `binding.py:232` | **8/8 · 8/8** |

**18 of 18, three-way.** Published as a negative: on this target, the spec text, the reference
implementation and the machine-readable vectors *do* agree about every number they name. **The
defect this pass charges is not a disagreement about a value. It is a question none of the
three artifacts asks.**

### C.3 — SDK suite baseline

`python3 -m pytest -q` in `web4-standard/implementation/sdk/` → **2750 passed, 5 xfailed**
(2755), 4.38 s. Identical to C388's count under identical blobs.

---

## §D — Findings

### N1 (MEDIUM → standard editor + SDK owner; adjudicate **after** C376-N1's fork, not before) — `§3.5` device removal is unsatisfiable below a device-count floor the standard never names, and every shrinking constellation ends there

**Locus.** The quorum test is published **twice, in agreement**:

- spec §3.5 `:722-733` — `remaining_active` excludes `device_to_remove` (`:722-724`), then
  `if len(authorizing_active) < root_lct.device_constellation.recovery_quorum: raise
  InsufficientQuorumError` (`:728`);
- SDK `binding.py:338-345` — `active_ids = {… if d.device_lct_id != device_lct_id}` (`:338`),
  then `if len(authorizing_active) < constellation.recovery_quorum: raise ValueError` (`:340`).

The threshold comes from §5.2 `:978-994` / `binding.py:232-245`, whose first branch is
`if device_count <= 2: return device_count  # All devices required` (`:989-990`).

**The arithmetic.** Removing one device from `n` active leaves at most `n − 1` devices that
can authorize. The removal succeeds iff `recovery_quorum ≤ n − 1`. At `n ≤ 2` the quorum *is*
`n`, so the condition is `n ≤ n − 1` — **false for every n**. The exclusion rule and the
"all devices required" rule are individually reasonable and jointly unsatisfiable.

**Executed, both readings of `recovery_quorum`.** C376-N1 established that the corpus holds
two incompatible readings and left the fork open: a **stored field** (spec §2.3 `:203`
`"recovery_quorum": 2`; §3.5 `:728` and §3.6 `:790` *read* it; the spec has **no** assignment
site) versus a **derived function of live membership** (`binding.py:304` and `:352` assign it).
The floor exists under both; only its height moves. Drain procedure: remove one device at a
time, **all** remaining actives authorizing — the most permissive possible caller.

| `n₀` | `q₀` | **STORED**: removals possible / terminal active | **DERIVED**: removals possible / terminal active |
|--:|--:|---|---|
| 2 | 2 | **0** / 2 | **0** / 2 |
| 3 | 2 | 1 / 2 | 1 / 2 |
| 4 | 2 | 2 / 2 | 2 / 2 |
| 5 | 3 | 2 / **3** | 3 / 2 |
| 6 | 3 | 3 / **3** | 4 / 2 |
| 8 | 4 | 4 / **4** | 6 / 2 |
| 10 | 5 | 5 / **5** | 8 / 2 |
| 20 | 10 | 10 / **10** | 18 / 2 |

**Closed form, verified for every `n₀ ∈ [2,20]`:** under the stored reading the terminal
active count is **exactly `default_recovery_quorum(n₀)`** — *half the constellation is
permanently unremovable*. Under the derived reading it is **2**, always. At `n₀ = 2` — phone
plus laptop, the modal consumer constellation and the one §2.1's own diagram is drawn one
device larger than — **zero removals are possible, ever, under either reading**.

**What the floor breaks.**

| site | text | at the floor |
|---|---|---|
| §5.1 `:966` | threat *"Single device compromise"* → mitigation *"Quorum requirement for sensitive ops"* | the compromised device is a member of **every** satisfying quorum; the mitigation names the attacker as a required signatory |
| §5.3 `:1001` | *"**Immediate**: Revoke device LCT"* | no path from this sentence to a revoked device (**non-normative** — see the severity note) |
| §2.4 `:290` | *"A revoked device's keys **MUST NOT** authorize any further operations"* | **antecedent unreachable** — §3.5 cannot produce a revoked device at the floor (v54) |
| `security-framework.md:81` | *"stale replicas **MUST NOT** restore authority to a revoked device"* | same antecedent, same unreachability, in a different core-spec (see INFO-1) |

**Rescues, adjudicated by execution rather than by argument.**

| # | rescue | verdict |
|---|---|---|
| R1 | *"The floor **is** the security property — quorum means quorum."* | **Does not survive as a silent property.** §5.2 `:982` states the tradeoff as *"Balances security vs. **recoverability**"*, and a census of `at least` / `minimum` / device-count language across the target returns **no floor statement anywhere** (`:40`, `:980` are quorum *size*; `:795` is anchor *type*). An undocumented terminal state is a defect even if the arithmetic is intended. |
| R2 | *"§3.6 recovery is the escape."* | **FALSIFIED by execution.** `can_recover(c, ["healthy"])` at `n=2` returns verbatim `(False, 'Quorum not met: need 2, have 1 active')` (`binding.py:589`). And if **both** devices participate, §3.6 step 6 (`:831-833`) revokes only devices **not** in `recovery_devices` — i.e. **nobody**. Recovery at the floor cannot exclude the compromised device either. |
| R3 | *"Enrol a replacement device first, then remove."* | **SURVIVES — and it is what narrows the charge.** Executed: `enroll_device(c, "d2", …, witnesses=["d1"])` succeeds with the healthy device as sole witness → `n=3` → `remove_device(c, "d0", "compromised", ["d1","d2"])` succeeds. **But**: it is documented in no section (§3.5, §5.2, §5.3 and `binding.py` are all silent); it contradicts §5.3's word *Immediate*; it requires enrolling a device witnessed by a set that may include the compromised one; and it returns the constellation to `n=2, q=2` — **the same terminal state**. The charge is therefore *undocumented mandatory ordering*, **not** *impossibility*. |
| R4 | *"A deployment can just configure a lower quorum."* | Survives **only** under the stored reading, and `binding.py:352` overwrites the configured value on the first removal. **That recompute is already charged — `C376-N1` owns it, routed to operator + this lineage's owner. NOT re-charged here** (v44: running the strictest rule against oneself first). |
| R5 | *"`DeviceStatus.SUSPENDED` neutralizes a compromised device without passing the quorum gate."* — `active_devices` (`binding.py:203`) filters on ACTIVE, so a suspended device leaves every quorum. | **Dies twice, and the polarity check (v57) makes it strengthen N1.** (i) **SDK**: `SUSPENDED` is declared at `binding.py:85` and **never assigned** — the module's only status assignment is `:347 target.status = DeviceStatus.REVOKED`. (ii) **Spec `:289`** discloses it: *"Re-activation by quorum is a future extension; **this spec does not define entry/exit transitions for `suspended`**."* Disclosed inertness is not charged — but the disclosure's polarity cuts *against* the corpus here: it **confirms** that no non-quorum path to neutralizing a compromised device exists. |
| R6 | *"`binding.py:17-19` discloses the module is data-structures-only."* | **Polarity fails for this charge.** The disclosure scopes out *"Actual cryptographic operations"*; `:17` affirms the module **does** provide *"pure-function computations"* — the quorum arithmetic is the in-scope half. And the **spec's** §3.5 carries the identical floor, and the spec is not data-structures-only. |

**Severity: MEDIUM, and the cap is recorded rather than argued around (v74).** No `MUST` in
the target is violated. §7.2 `:1095` — *"Societies implementing this protocol MUST … Enforce
recovery quorum for identity recovery"* — is **satisfied**; enforcing the quorum is exactly
what makes removal unsatisfiable. §5.3 `:997-1006` carries **no RFC-2119 modality** (the
target holds 5 `MUST`, 2 `MUST NOT`, 1 `SHOULD`, 1 `RECOMMENDED`; none is in §3.5 or §5.3),
so §5.3 **cannot itself carry the severity** and is cited as consequence, not as violation.
The MEDIUM rests on this lineage's own rubric — *"a normative statement is unsatisfiable"* —
applied at the rung where it is true: the two revocation-conditioned `MUST NOT`s (`:290`,
`security-framework.md:81`) have an antecedent §3.5 cannot produce. Not HIGH: R3 survives, so
a determined operator has a path, and nothing on the wire is malformed.

**Prior art, cited rather than absorbed (v56/v74).** C376-N1 prints the derived number, under
its own heading *"Bounds published honestly"*: *"Via `remove_device` the recompute floors at
2 … so the observed reduction is 3 → 2, not 3 → 1."* **The polarity is opposite** — C376
deploys the floor as a *mitigating bound that limits its own charge*, on a different target
(`security-framework.md`), and never computes the stored-reading floor, never reaches
§5.1/§5.3, never says *unsatisfiable*. **N1 is novel in exactly three limbs and no more:**
(i) the stored reading's `default_recovery_quorum(n₀)` closed form, (ii) the floor living in
the **spec's** §3.5 pseudocode independent of the SDK, (iii) the §5.1/§2.4 unsatisfiability
consequence. (See §F.2 — C376's parenthetical arithmetic is also wrong, and is corrected.)

**Direction tested, and it killed the nicer framing (standing rule).** The first draft blamed
C81's remediation (`a6cbde92`, #372) for creating the lock. **False.** `git log -S
"remaining_active" -- <target>` returns **`d4f926ad`** (#281, **2026-06-07** — the *C36*
remediation), and `git log -S "active_ids & set(authorizing_devices)" -- binding.py` returns
**`441b12f0`**, the SDK module's **birth commit**. C81 changed only the *signature-collection
loop* (`for device in authorizing_devices` → `authorizing_active`). The floor has been in the
SDK since the module existed and in the spec since 2026-06-07. **C36 charged the spec for not
matching the SDK's intersection; the remediation aligned the spec to the SDK — and thereby
aligned it to the SDK's unreachability.**

**Remedy forks — do NOT self-apply, and this fork sits *downstream* of another lineage's
open one.** (a) exempt removal from the "all devices" branch (`§5.2 :989-990` returns `n−1`
for `n=2`); (b) state a device-count floor normatively and require enrol-before-remove in
§5.3; (c) give §5.3 a non-quorum path by defining `suspended`'s entry transition (`:289`
declares it a future extension). **Every one of these is a different answer to C376-N1's
stored-vs-derived question**, so choosing here would pick a side of an open DESIGN-Q that is
not this pass's to close. → **operator, jointly with C376-N1 and C308-N1/C388-N1.**

### N2 (LOW, coverage/instrument → SDK owner) — the `n ≤ 2` branch is guarded by three assertions and all three restate the constant

**v59 probe, plausible value not sentinel.** `default_recovery_quorum`'s first branch was
mutated in place from `return device_count` to `return max(1, device_count - 1)` — a
*plausible* alternative design (*"the one remaining device may authorize"*), not a sentinel.
Full suite:

```
3 failed, 2747 passed, 5 xfailed
FAILED tests/test_binding.py::TestRecoveryQuorum::test_quorum_two          (:274  assert == 2)
FAILED tests/test_binding.py::TestVectors::test_recovery_quorum_calculation (:664  vector replay)
FAILED tests/test_binding.py::TestConstellationManagement::test_additional_enrollment_with_witness (:179  post-enrolment field read)
```

**All three restate the constant.** Two assert `default_recovery_quorum(2) == 2` (once
directly, once via the vector); the third reads `constellation.recovery_quorum == 2` after an
enrolment. **Zero behavioural tests fail** — nothing in 2755 tests asks whether the value the
constant produces can be *satisfied*.

**Backed control, so the probe's silence is evidence and not an artifact (v68).** Mutating
`remove_device`'s comparison `<` → `<=` (`binding.py:340`) fails **2 behavioural** tests:
`test_remove_device` (`:211`) and `test_witness_revoked_device_raises` (`:545`). The
instrument discriminates; it simply has nothing to say about the `n≤2` branch.

**The coverage shape, stated correctly.** The suite's positive removal test (`:211`) asserts
three things — `device_count == 2` (`:222`), `status == REVOKED` (`:224`), and
`revocation_reason == "sold"` (`:225`) — and it **leaves the constellation in exactly the
terminal state** N1 describes, `n=2, q=2`. Its negative sibling
`test_remove_device_quorum_enforcement` (`:227`) *is* a behavioural quorum-rejection test, and
it passes for the intended reason at `n=3`; what neither can distinguish is *quorum correctly
enforced* from *quorum unsatisfiable*, because both are the same `ValueError`. **The missing
vector is a removal group** — `binding-vectors.json` publishes 6 groups and **none** covers
`remove_device`; this is the Nth member of `remediation-incompleteness` on this lineage
(cf. C388's missing `Single TPM2 → 0.75` row).

**Routes to the SDK owner, after N1's fork resolves** — adding a removal vector before the
floor's disposition is settled would pin the wrong expectation, exactly as C388 declined to
pin the ceiling.

### N3 (LOW, instrument → operator + the C330/ISP lineage) — C348-N2 has now missed delivery three times, and per its own pre-registration the instrument is the finding

C388's disposition pre-registered the test verbatim: *"Next ISP slot ≈ **C410**. If it is
still open at C410 that is three misses on one row across three passes, and the instrument —
not the row — is the finding."*

**C410 has run.** `docs/audits/C410-inter-society-protocol-10th-delta-2026-08-19.md`:

| probe | count |
|---|--:|
| `grep -c "C330"` | **6** |
| `grep -ci "C348"` | **0** |
| `grep -ci "orphan"` / `"orphaned-by-id"` | **0** / **0** |
| `grep -ci "remediated lineage"` / `"dropped one"` (the routed **predicate**, v65) | **0** / **0** |
| `grep -ci "Poisson"` / `"clustering"` / `"0.0147"` (C330's instrument itself) | **0** / **0** / **0** |

Re-resolved by predicate and not by id (v65), and the answer is the same by both routes.
C410's `## §B` is a **findings** section — the pass ran no inbound set-difference sweep at
all, which is the mechanism: **the row was invisible because the receiving pass's instrument
has no inbound channel**, not because anyone judged it. That is the third consecutive miss,
and it is now the second time on this row that a receiver held the relevant ledger open while
the row sat unread (C388 recorded the first, at C370).

**Charged as the instrument, per the pre-registration.** The row itself (*an id-citation
sweep is structurally blind to findings consumed by a remediation commit*) is unchanged and
still LOW. What is net-new is that **three independent routings — by slot number (C330→C348),
by id-plus-subject-matter (C348→C410), and by forward guard (C388 guard 4) — all failed
against the same receiver.** Routing that survives only when the receiver happens to run a
sweep is not delivery (v36: delivery is an act of the receiver). → **operator**: this needs a
channel, not a fourth routing.

### INFO-1 (recorded; a correction to this lineage's own prior pass) — C388 guard 6 answered, and its premise was wrong

C388 registered `security-framework.md:78` as INFO-1, *"constellation membership replication,
a `MAY`"*, and asked C428 to *"check whether it acquired normative force. It is a `MAY` today.
Do not charge it otherwise."*

**Measured**: `security-framework.md` is `63889457` at `cd39cfab` **and** at HEAD —
byte-identical, so nothing was acquired. **But the premise was wrong when it was written.**
`:78` is one bullet inside a block whose **lead sentence `:76` is a `MUST`** (*"For
multi-device identities, implementations **MUST** distinguish replicated identity state from
device-local custody"*) and whose three sibling bullets carry `MUST` / `MUST NOT` / `SHOULD`:

| line | modality |
|---|---|
| `:76` | **MUST** (block lead) |
| `:78` | MAY — *the one bullet C388 quoted* |
| `:79` | **MUST** + **MUST NOT** |
| `:80` | **MUST** + **MUST NOT** |
| `:81` | **SHOULD** + **MUST NOT** |

**C388 read the bullet, not the block (v76 — enumerate the whole block; the uncharged
member's modality is often the opposite one).** The correct disposition of that INFO row is
not *"still a MAY"* but *"never was a bare MAY"*, and it is **load-bearing for N1**: `:81`'s
*"stale replicas MUST NOT restore authority to a **revoked** device"* is one of the two
prohibitions whose antecedent §3.5 cannot produce at the floor.

### INFO-2 (recorded) — the target's normative surface, published as a denominator

`grep -no "MUST NOT\|MUST\b"` over the target returns **5** matches at **5 distinct
lines**: **3 bare `MUST`** (`:153`, `:886`, `:1095`) and **2 `MUST NOT`** (`:290`, `:953`).
Plus **1 `SHOULD`** (`:957`), **1 `RECOMMENDED`** (`:1004`), **4 `MAY`**. (A `\bMUST\b`
matcher counts the `MUST` inside `MUST NOT` — publish the disambiguation rule with the count.) **None is in §3.5, §3.6, §5.1 or §5.3** — the
four sections this pass's finding traverses are, as a body, non-normative prose and
pseudocode. Recorded because it is what caps N1 at MEDIUM, and because a future pass
proposing to charge §5.3 as a violated requirement should see this count first.

### INFO-3 (recorded, instrument) — a `git log -S` window probe self-contaminates once the pass commits

C388's B.2 published `git log -S "constellation_trust_ceiling"` over its window = **0
commits**, correctly. The identical command over **this** window returns **1** — and the 1 is
`a68adb93`, *C388's own audit document*, which quotes the token nine times. Path-bounding
(`-- . ':!docs/audits'`) restores **0**. Every `-S` probe published by an audit becomes false
for its successor at the moment the audit is merged, unless the audit tree is excluded. The
corrected form is registered in §H guard 5.

---

## §E — C388's guards and carries, re-adjudicated at HEAD `cfc7f96d`

| # | C388 guard | disposition at C428 |
|---|---|---|
| 1 | *Re-run I6/I7 first; identify which N1 fork landed. If vector case 6 still reads `0.98`, fork (a) did not land.* | **DONE — NEITHER.** Case 6 = `0.98`; §4.2 `:897-900` unchanged; both blobs frozen. **C388-N1 open after one window**, with C308-N1. |
| 2 | *Mutate to a plausible wrong value; check whether `test_integration.py:1597`'s `assert ceiling > 0.7` is still a bound.* | **Verified as a freeze, not re-run — and the guard's own anchor is off by one.** The bound assert is at **`:1598`**, not `:1597`; `:1597` is `assert 0.0 < trust_score <= ceiling`. `test_integration.py` is `e3c23c00` at both ends, so C388's anchor was wrong **when it was written**, and its range `:1596-1597` does not contain the line it names (see §F.7). The assert itself is unchanged: `assert ceiling > 0.7  # Two hardware devices = high ceiling`. Re-running C388's 4-arm poison against byte-identical blobs is a **rediscovery** (v78) and is declined as such; the v59 method was spent on an **unprobed** branch instead — see N2. |
| 3 | *Add vector-case vocabulary to the novelty matcher before claiming net-new.* | **DONE.** Matcher published in §F.1; it is what surfaced C376's prior-art sentence and what kept N1's novelty scoped to three limbs. |
| 4 | *Check C348-N2 at the ISP ledger (≈C410) before re-routing a third time; if still open report the instrument, not the row.* | **DONE — still open. Reported as the instrument.** → **N3.** |
| 5 | *Re-run the §B set difference with the same matcher; a negative followed by a negative is a fact about the target.* | **DONE — negative again.** 21 / 50 / 43 / 3 vs 21 / 48 / 41 / 8. §B. |
| 6 | *Check whether `security-framework.md:78` acquired normative force; it is a `MAY` today; do not charge it otherwise.* | **DONE — blob byte-identical, nothing acquired; and the premise is corrected.** → **INFO-1.** Not charged. |
| 7 | *Do not re-open: `C80:134`'s completeness predicate; the 9-of-9 C80 accounting; C308-N1/N2's mirror layer while frozen; the hub constellation-MFA cluster; the binding conformance-suite absence.* | **HONOURED, all five.** The hub cluster appears in §B's postdating rows and is explicitly not re-charged; the mirror-layer blobs are certified frozen in §A and not re-read; `test_binding.py:646-748` does run the vectors, so the conformance-suite absence is not re-raised. |

| carry | status at HEAD |
|---|---|
| **C388-N1** (ceiling non-monotone under enrolment) | **STILL-OPEN**, 1 window, neither fork landed |
| **C388-N2** (2 of 3 fallback arms unguarded) | **STILL-OPEN**, blobs frozen |
| **C308-N1 / C308-N2** (two ceiling authorities; `lct.rs` `0.85` software default) | **STILL-OPEN**, all mirror blobs frozen |
| **C348 N1 held carries** (flat 8-dim `t3_tensor`; no entity-role binding) | **STILL-OPEN** — `t3-v3-tensors.md` unmoved in window |
| **C348-N2** (orphaned-by-id instrument) | **STILL-OPEN, 3rd miss** → **N3** |
| **C376-N1** (the `recovery_quorum` recompute; stored-vs-derived fork) | **STILL-OPEN** — and N1 is now downstream of it |

---

## §F — Own errors

**F.1 — The novelty matcher, published beside the claim (v44).** Denominator: **256** docs
under `docs/audits/`. Terms run: `unreachable`, `cannot be removed`, `never be removed`,
`no executable path`, `terminal state`, `unsatisfiable quorum`, `quorum can never`,
`two-device`, `2-device`, `removal is impossible`, `floor at 2`, `authorize its own removal`,
plus the domain's own identifiers `remove_device`, `recovery_quorum`,
`default_recovery_quorum`, `recover_identity`, `can_recover`, `recompute`, `overwrit`,
`reassign`. Nine of the twelve prose terms return **∅**. The three that hit
(`unreachable`, `no executable path`, `terminal state`) hit **17 / 4 / 2** documents, none
about this target. `default_recovery_quorum(constellation` returned exactly one document —
**C376** — which is how the prior art in N1 was found *before* drafting rather than after.

**F.2 — A corrected cell in a sibling lineage, offered as a correction not a charge.**
C376-N1's parenthetical reads: *"removing the 4th of 4 active devices needs 2 authorizing
remaining actives, and only 1 remains."* The **conclusion** (floor = 2 under the derived
reading) is **correct and independently reproduced here**. The **arithmetic** is not: from 4
active devices the drain yields exactly **2** successful removals, and the block occurs on the
**third** attempt, made at **2** active devices with 1 remaining. There is no "4th of 4"
removal available from a 4-device constellation. Routed to the security lineage as a cell
correction; it changes nothing in C376's charge.

**F.3 — My first framing was wrong and execution killed it.** I drafted N1 as *"the C81
remediation created the lock"* — a tidy v53 story (*run the guard against the fix*). `git
log -S` on both artifacts refuted it: the exclusion entered the spec at `d4f926ad` (#281,
2026-06-07, the **C36** remediation) and the SDK carried it from birth (`441b12f0`). The true
story is less tidy and more useful: the C36 remediation aligned the spec **to** the SDK, and
inherited the SDK's unreachability along with its correctness. Recorded because this is the
second consecutive pass on this lineage where testing the direction killed the nicest framing.

**F.4 — I nearly charged a finding another ledger already owns.** The quorum **overwrite**
(`binding.py:352` replacing a deployment-configured `recovery_quorum` with the library
default — measured here: `n=10, q=8` → `q=5` after one removal) was drafted as a second
finding. `grep` over the audit tree returned C376-N1, which owns it completely and routed it.
Dropped before drafting. This is the second time in three passes on this lineage that the
near-miss lived in a **sibling** lineage's audit of a **different** file (C388's was `C80:50`).

**F.5 — A false evidence cell, caught in policy review.** The draft asserted that
`test_binding.py:211` *"asserts nothing further"* than `device_count == 2`. It asserts two
more things (`:224`, `:225`), and the immediately following test (`:227`) **is** a behavioural
quorum-rejection test. N2's core claim survives the correction unchanged — the mutation still
fails zero behavioural tests — but the characterization was wrong and is rewritten above.

**F.6 — A rescue I did not adjudicate until review raised it.** `DeviceStatus.SUSPENDED`
(`binding.py:85`) is the obvious non-quorum route to neutralizing a compromised device and I
had not tested it. It dies twice (R5) and, on the polarity check, **strengthens** N1. Missing
it would have left N1 open to a one-line refutation.

**F.7 — Anchors, mine and my predecessor's.** **94** distinct line anchors are cited in this
document across 6 files. All 94 were range-checked and **93 content-verified** by
`sed -n "<n>p"` at HEAD after drafting — **93 exact**; the 94th (`<target>:900`) is a blank
line serving as a range terminus for §4.2 `:871-900` and is left as inherited. This includes
the anchors handed to me by policy review (path tokens are their own class — verify every one,
*including a reviewer's*) and the **21 anchors inherited verbatim from C388's baseline**
(`:611`, `:616-618`, `:653-657`, `:871`, `:155`, `:257`, `:270`; `binding.py:395`, `:396`,
`:419-426`, `:437-442`; `test_binding.py:464,478,481,491,494,507,705`) — **20 of 21 exact**.

**One inherited anchor is not.** C388 cites `test_integration.py:1597` **four times**
(`:44`, `:430`, `:466`, `:483`) as the site of `assert ceiling > 0.7`. The assert is at
**`:1598`**; `:1597` is `assert 0.0 < trust_score <= ceiling`, and C388's baseline range
`:1596-1597` therefore does **not** contain the line it names. The blob is `e3c23c00` at
`cd39cfab` and at HEAD, so this is not drift — it was wrong when written, which also makes
C388 `:430`'s claim (*"6 of 6 exact, the first no-off-by-one pass in four"*) false by one.
Corrected in §E guard 2 and in the C468 baseline. **The lesson is the standing one and it now
has a fourth firing on this lineage: an anchor you inherit is an anchor you have not
verified.**

---

## §G — Instrument index (built last, by capture — v39)

| # | measurement | command |
|---|---|---|
| I1 | window size + per-tree | `git rev-list --count cd39cfab..HEAD [-- <tree>]` |
| I2 | 12-blob freeze | `git rev-parse --short HEAD:<path>` per baseline row |
| I3 | target freeze age | `git log -1 --format=%ad --date=short -- <target>` → 2026-06-21 |
| I4 | fenced-block census + exec | extract by `^\`\`\`` pairs; `exec(compile(code, …))` per block |
| I5 | vectors × spec × SDK | `json.load(binding-vectors.json)`; call spec fenced fn and `web4.binding` fn per case |
| I6 | fork check | `python3 -c "json…['trust_ceiling_by_config']['cases'][5]"` + `sed -n '897,900p' <target>` |
| I7 | drain, both readings | `remove_device` in a loop, all remaining actives authorizing; stored variant restores `recovery_quorum` after each call |
| I8 | rescue R2 | `can_recover(c, ["d1"])` / `can_recover(c, ["d0","d1"])` at `n=2` |
| I9 | rescue R3 | `enroll_device(c,"d2",…,witnesses=["d1"])` then `remove_device(c,"d0",…,["d1","d2"])` |
| I10 | rescue R5 | `grep -n "\.status = " binding.py` → 1 site (`:347`, REVOKED); `sed -n '289p' <target>` |
| I11 | suite baseline | `python3 -m pytest -q` in `implementation/sdk/` → 2750 passed, 5 xfailed |
| I12 | v59 plausible mutation | in-place edit of `binding.py:240-241` → `max(1, device_count-1)`; full suite; `git checkout --` to revert |
| I13 | backed control | in-place edit of `binding.py:340` `<` → `<=`; full suite; revert |
| I14 | §B filename sweep | `git grep -li "multi-device-lct-binding" -- .` minus `docs/audits/` |
| I15 | §B domain sweep | `git grep -li -E "constellation" -- web4-standard/ web4-core/ hub/ docs/specs/ docs/designs/ core/ forum/` minus 5 exclusions |
| I16 | §B residue + postdating | `comm -23`; `git rev-list --count cd39cfab..HEAD -- <row>` |
| I17 | new residue rows | same sweep at `cd39cfab`, `comm -23` against HEAD's |
| I18 | third direction | `git log -S "<token>" cd39cfab..HEAD [-- . ':!docs/audits']` |
| I19 | direction of the floor | `git log -S "remaining_active" -- <target>`; `git log -S "active_ids & set(authorizing_devices)" -- binding.py` |
| I20 | novelty matcher | `grep -rli "<term>" docs/audits/ web4-standard/docs/audits/`, 21 terms, denominator 256 |
| I21 | guard 4 | `grep -ci "<term>" docs/audits/C410-inter-society-protocol-10th-delta-2026-08-19.md`, 8 terms |
| I22 | INFO-1 | `git rev-parse --short cd39cfab:…/security-framework.md` vs HEAD; `sed -n '76,81p'` |
| I23 | normative census | `grep -n "\bMUST\b\|\bMUST NOT\b\|\bSHOULD\b\|\bRECOMMENDED\b" <target>` |
| I24 | floor-statement census | `grep -n -i "at least\|minimum\|N device\|single device\|only device" <target>` |

**Tree state after I12/I13**: `git status --porcelain` **empty**; `binding.py` back to blob
`857f8040`. Both mutations were made in place because a `/tmp` copy breaks the tests'
relative vector paths, and both were reverted and verified.

---

## §H — Disposition

**Findings: N1 MEDIUM · N2 LOW · N3 LOW · 3 INFO. 3 net-new. ZERO mutation. 1 new file.**

- **C429 = declared NO-OP.** N1's remedy has three forks and **each is a different answer to
  C376-N1's open stored-vs-derived question**; choosing one here would close another lineage's
  DESIGN-Q from the outside. N2's fix (a removal vector group) must follow N1's disposition or
  it pins the wrong expectation. Do **not** self-fix the target, `binding.py`,
  `binding-vectors.json`, `security-framework.md`, the SDK tests, or any prior audit doc.
- **Delivered outward this fire, not merely routed** (v36 applied to this pass's own output):
  **N3 is escalated to the operator as a channel problem**, not routed a fourth time — three
  routings by three different mechanisms have now failed against the same receiver. **F.2's
  cell correction is routed to the security lineage** under C376-N1's own heading text
  (*"Bounds published honestly"*), so a sweep from either side joins them.
- **N1 routes to the standard editor + SDK owner, adjudicated jointly with C376-N1**
  (its fork is the precondition) and noted for C308-N1/C388-N1's owner (same file, same pass).

**Baseline for C468** (blob column; each basename verified unique in the tree at `cfc7f96d`;
`test_integration.py` is **not** unique — root the path):
target `web4-standard/core-spec/multi-device-lct-binding.md` `b979ea7d` (*commit* `a6cbde92`,
1126 L; **N1 loci** §3.5 `:711-769` / quorum test `:728` / exclusion `:722`, §5.2 `:978-994` /
floor branch `:989-990`, §5.1 `:966`, §5.3 `:1001`, §2.4 `:290`, §2.3 `:203`, §3.6 `:790`,
`:831-833`, `suspended` disclosure `:289`; C388-N1 loci §4.2 `:871-900`, §3.4 `:611-659`;
C268-N1 `:155`, `:795-801`; B-10 `:257`/`:270`);
`web4-standard/implementation/sdk/web4/binding.py` `857f8040` (**N1** `:232-245`, `:309-353`,
exclusion `:338`, test `:340`, recompute `:304`/`:352` — *C376-N1's, not this ledger's*;
`can_recover` `:589`; `SUSPENDED` declared `:85`, sole status assignment `:347`);
`web4-standard/test-vectors/binding/binding-vectors.json` `dc969641` (**6 groups, none for
removal**; case 6 = `0.98`, still the pinned raise);
`web4-standard/implementation/sdk/tests/test_binding.py` `ad7fd3dd` (748 L; removal `:211`,
`:227`, `:237`, `:250`; quorum table `:268-291`; vector replay `:664`);
`web4-standard/implementation/sdk/tests/test_integration.py` `e3c23c00` (bound assert **`:1598`**, corrected from C388's `:1596-1597`; **root this path — the basename is not unique**, `simulations/test_integration.py` shadows it);
`web4-core/src/ratchet.rs` `806882b1`; `docs/specs/attestation-envelope.md` `c2f604aa`;
`web4-standard/implementation/sdk/web4/attestation.py` `37a7c673`;
`web4-core/python/web4_core/trust/attestation/envelope.py` `c3046043`;
`web4-standard/test-vectors/attestation/attestation-vectors.json` `fecbc695`;
`web4-core/src/lct.rs` `2e9d4586`; `hub/hub-lib/src/hub.rs` `fd45f9ce`;
`web4-standard/core-spec/security-framework.md` `63889457` (**added to the baseline** — INFO-1
makes it load-bearing for N1; block `:76-81`).

**Guards for C468.**
1. **Re-run I6 FIRST.** If vector case 6 still reads `0.98`, C388-N1's fork (a) has not landed
   — that will then be **two full windows** on an open MEDIUM, which is the C386-N1 shape:
   a third no-motion window ⇒ escalate as a **STALL**, not as a re-finding.
2. **Re-run I7 in both readings before reading anything.** If `binding.py:352` has been
   deleted (C376-N1 fork i), the derived column disappears and only the stored table applies;
   if §5.2's `n≤2` branch changed, **the whole of N1 is discharged** and must be recorded as
   discharged, not re-derived. **Check `default_recovery_quorum` before `remove_device`.**
3. **Do NOT re-run**: the §4.3/§5.2 three-way vector agreement (18/18, C.2 — a second pass is a
   rediscovery under frozen blobs); the 8-block exec census (C.1, all green); C388's 4-arm
   ceiling poison (guard 2, declined here as a rediscovery and still frozen); the R2/R3/R5
   rescue executions unless a locus blob moves.
4. **N2's probe is spent on this branch.** If a removal vector group has been added, run it;
   if not, do **not** re-mutate `default_recovery_quorum` — the result is determined by the
   frozen blob. Spend v59 on an **unprobed** branch, as this pass did.
5. **Path-bound every `git log -S` window probe** — `-- . ':!docs/audits'`. Any `-S` count
   published by a prior pass is off by the number of audit documents that quote the token
   (INFO-3). This applies to C388's B.2 figure and to every one in §G above.
6. **Enumerate the whole block before typing a modality** (v76, INFO-1). C388 typed
   `security-framework.md:78` as a `MAY` because it read one bullet of a `MUST`-headed block.
   When a prior INFO row types a single line, re-read its **siblings** before discharging it.
7. **Do not re-open**: C376-N1's recompute (owned, routed); the hub constellation-MFA /
   AssuranceReceipt cluster (C286-N3, C288-N2); `C80:134`'s completeness predicate; the 9-of-9
   C80 accounting; C308-N1/N2's mirror layer while frozen; the binding conformance-suite
   absence (C308 INFO-1 — the vectors *are* run, `test_binding.py:646-748`); the `suspended`
   lifecycle gap (**disclosed** at `:289`, recorded in R5, not chargeable).
8. **C348-N2 is escalated, not routed.** Do **not** route it a fourth time. If the operator
   has not answered by C468, report it as an **unanswered escalation**, which is a different
   row from an undelivered one.
9. **Re-resolve every anchor you inherit, not only every anchor you write.** This pass
   verified 21 anchors carried forward from C388's baseline and found **1 wrong under a frozen
   blob** (§F.7). A baseline is a claim, and a frozen blob makes a wrong anchor look stable
   rather than making it right. Budget one `sed -n "<n>p"` per inherited anchor before §A.

---

## Pattern (C428)

**C388 found a value that was wrong but reasonable. This pass found a value that is right and
still unusable — because a threshold's correctness and its satisfiability are different
questions, and the corpus has instruments for only the first.**

Six audits, an SDK, and eight shipped vector cases all agree that
`default_recovery_quorum(2) == 2`. They are all correct. The vectors test the function's
*range*; the tests assert its *values*; the spec's table publishes its *branches*. Not one of
them, and no reviewer in nine passes, composed that number with the rule sitting fifteen
sections away — that the device being removed cannot authorize its own removal — and noticed
that the two together make a quorum of `n` out of a pool of `n − 1`. **The defect is not in
either artifact. It is in the join, and the join is what nobody's instrument spans.**

The general shape, and it is the carry: **a constant is verified against its definition; a
threshold must be verified against its satisfying set.** `default_recovery_quorum` was checked
eight ways as a function — *does it return the documented number?* — and zero ways as a gate —
*is there a caller state in which the number it returns can be met?* Those are not the same
check, and passing the first at 100% tells you nothing about the second. The tell is visible
in the mutation result: poisoning the branch fails three tests, and **all three fail by
restating the constant**. A guard that can only say *"the number changed"* cannot say *"the
number is unreachable."*

**v79 (new): a threshold needs a reachability probe, not only a value probe — run the gate
against its own caller and ask whether any input satisfies it.** The cheapest form is a
drain: apply the operation repeatedly under the most permissive possible caller and see where
it stops. It costs eight lines, it is a *behavioural* question no vector file can encode, and
on this target it produced the finding that six point-checking passes could not — including
the closed form (`terminal = default_recovery_quorum(n₀)`) that only appears once you run the
loop past the first iteration.

**Corollary, and it repeats C388's with the sign flipped: the falsifier you need is in a
sibling lineage, and it is filed under the opposite polarity.** C376 printed this pass's
number — *"the recompute floors at 2"* — as a **mitigating bound on its own charge**. Filed as
a limitation, it was invisible to every matcher looking for a defect. A prose matcher searches
for the shape of the claim you intend to make; the prior art is often the same measurement
with the opposite verb. **Search for the number, not the verdict.**
→ [[feedback_threshold_needs_a_reachability_probe]] / [[feedback_predecessor_holds_the_falsifier]] /
[[feedback_mutate_to_a_plausible_value]] / [[feedback_enumerate_the_whole_block]] /
[[feedback_delivery_is_an_act_of_the_receiver]].
