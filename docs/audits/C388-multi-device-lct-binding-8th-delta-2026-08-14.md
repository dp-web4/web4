# C388 — `multi-device-lct-binding.md` Eighth Delta Re-Audit (the standard's trust ceiling rises when a weaker device is enrolled — and the two arms that do it are the two no test in the SDK can see)

**Slot**: C388 (= C348 + 40) · **Date**: 2026-08-14 · **Track**: legion-web4 ·
**Protocol**: v2 · **Branch**: `worker/web4-20260814-120000`
**Target**: `web4-standard/core-spec/multi-device-lct-binding.md`
**Window** (pre-registered before reading): `afa107f5..cd39cfab`, **32 commits**;
roots `web4-standard/`, `web4-core/`, `hub/`, `docs/specs/`, `docs/designs/`, `core/`, `forum/`;
excluded `archive/`, `sessions/`, `simulations/`, `**/target/`, `docs/audits/`.
**Mutation**: **ZERO.** One new file (this one).

**Lineage / enumeration rule** (inclusive — every `docs/audits/` document whose subject is
this target, C-numbered or not, and the same rule applied to my own lineage and to every
lineage charged below): `multi-device-lct-binding-internal-consistency-2026-05-28.md`,
`C36`, `C80`, `C81` (remediation), `C120`, `C152`, `C268`, `C308`, `C348` ⇒ **9 prior
members**; the delta re-audits run C80 (1st) … C348 (7th), so **this is the 8th delta**.
(The file was skipped in one rotation cycle — recorded at C268 — which is why an 8th delta
lands in a slot where sibling files are on their 9th.)

---

## Headline

**The standard's constellation trust ceiling is non-monotone under device enrolment: a
strict superset of the active anchor set can receive a strictly higher cap.** Executed over
all 15 non-empty anchor-type subsets, the cap rises in **3 of 7** hardware compositions —
`[phone_se]` 0.75→**0.80**, `[tpm2]` 0.75→**0.80**, `[phone_se,fido2,tpm2]` 0.95→**0.98**.

The third is the sharp one, and it is **software-specific, provably**: adding a *second
TPM2* to `[phone_se,fido2,tpm2]` leaves the cap at **0.95**, while adding a **software-only**
key — the weakest anchor type the standard defines, the one §2.2.4 gives weight 0.40 —
promotes it to **0.98**. §4.2's precedence rule 2 (`:897-900`) *mandates* this, §3.4's own
docstring (`:616-618`) *explains* it, and shipped vector case 6 *pins* it. **The standard
rewards the weaker addition.**

This is not confined to a helper: run end-to-end, `compute_constellation_trust` **final
output rises in all three cases** (0.7500→0.8000, 0.7500→0.7900, 0.9500→0.9800), and in each
the ceiling lift is *counterfactually necessary* — with the old ceiling, `min()` returns the
old value.

And the guard cannot see two of the three. Per-arm mutation of the "generic
hardware-diversity fallback" block: poisoning `len(hardware_types)==1 → 0.80` — the arm that
produces both 0.75→0.80 raises — leaves the **entire SDK suite green, 2750 passed / 5
xfailed**. So does the software-only arm. **The third arm is guarded only by a *bound*:**
its lone ceiling assert is `assert ceiling > 0.7` (`test_integration.py:1597`), which passes
when the arm is poisoned to a plausible wrong `0.98` — a sentinel-value probe reports it
guarded, a plausible-value probe reports it not. **⇒ v59.**

---

## Severity legend

| | |
|---|---|
| **HIGH** | Wire-visible, executable, and reachable by a conforming implementation today |
| **MEDIUM** | Published normative conflict or a normative claim with no live enforcer |
| **LOW** | Instrument / accounting defect; no wire effect |
| **INFO** | Recorded status, not charged |

---

## §A — Freeze, measured against C348's published 10-blob baseline (blob column typed, C348 guard 3)

`git rev-parse cd39cfab:<path>` for each; **blobs only in this table** — no commit ids.

| Artifact | C348 baseline blob | HEAD `cd39cfab` blob | |
|---|---|---|---|
| `web4-standard/core-spec/multi-device-lct-binding.md` | `b979ea7d` | `b979ea7d` | frozen |
| `web4-standard/implementation/sdk/web4/binding.py` | `857f8040` | `857f8040` | frozen |
| `web4-standard/test-vectors/binding/binding-vectors.json` | `dc969641` | `dc969641` | frozen |
| `web4-core/src/ratchet.rs` | `806882b1` | `806882b1` | frozen |
| `docs/specs/attestation-envelope.md` | `c2f604aa` | `c2f604aa` | frozen |
| `web4-standard/implementation/sdk/web4/attestation.py` | `37a7c673` | `37a7c673` | frozen |
| `web4-core/python/web4_core/trust/attestation/envelope.py` | `c3046043` | `c3046043` | frozen |
| `web4-standard/test-vectors/attestation/attestation-vectors.json` | `fecbc695` | `fecbc695` | frozen |
| `web4-core/src/lct.rs` | `2e9d4586` | `2e9d4586` | frozen |
| `hub/hub-lib/src/hub.rs` | `2431521d` | **`fd45f9ce`** | **MOVED** |

**9 of 10 frozen. Target byte-frozen at `b979ea7d` since C81 `a6cbde92` — 54 days, 8 passes.**

The one mover: `hub/hub-lib/src/hub.rs`, **+11 lines**, sole commit `5513af97` ("hub F0.3
(R7c): deploy ratification"). Read: the added lines are a `ratified` block wiring
`hub-lib/ratified.rs` into the operator overview. **`grep -n trust_ceiling` over the diff = 0**
— the mover does not touch the C308-N2 locus, which is why that carry's status below is
"held by freeze of the relevant lines" and not "held by blob identity". Publishing the
distinction is the point: C348 guard 3's typed column would have let a blob-level "MOVED"
read as a carry disturbance when it is not one.

**Commits in window by root** (each cell carries its command —
`git log --oneline afa107f5..cd39cfab -- <root>`): `web4-standard/` **1** (`afd04623`);
`web4-core/` **1** (`91c1c333`); `hub/hub-lib/src/hub.rs` **1** (`5513af97`).

---

## §B — The inbound sweep as a set difference, run before §A's reading (v36/v37, C348 guard 2)

Verb/term set **pre-registered** before running: domain word = `constellation` (the domain's
own word — the target never writes its own filename, so a filename sweep is a citation-graph
query and structurally cannot return an orphan).

| | command | count |
|---|---|---|
| filename sweep (citation query) | `git grep -li "multi-device-lct-binding" -- .` minus `docs/audits/` | **21** |
| domain-word sweep, tree-bounded | `git grep -li -E "constellation" -- web4-standard/ web4-core/ hub/ docs/specs/ docs/designs/ core/ forum/`, minus `archive/ sessions/ simulations/ **/target/ docs/audits/` | **48** |
| **residue** = domain ∖ filename (`comm -23`) | | **41** |
| residue rows with ≥1 commit in window | `git log -1 --format=%ci afa107f5..HEAD -- <f>` per row | **8** |

The 8 postdating rows, classified:

| row | classification |
|---|---|
| `hub/hub-daemon/src/rest.rs` (57 hits), `hub/hub-lib/src/law.rs` (61), `hub/hub-lib/src/state.rs` (10), `events.rs` (3), `lib.rs` (1), `hub-daemon/src/main.rs` (2), `hub/docs/SPRINTS.md` (1) | **The hub constellation-MFA / AssuranceReceipt cluster.** C308 already ruled this **reach-escalation, routed twice by siblings (C286-N3, C288-N2)**. **NOT re-charged** — re-filing it would inflate this pass with two other ledgers' work. |
| `web4-standard/core-spec/security-framework.md` | **In-standard, in-window, net-new text about this target's subject matter** — see INFO-1. |

**Recorded negative, and it is the informative half:** the residue is 41 rows and *none* of
the 33 that did not move in the window carries a claim about the ceiling. The v36 difference
was the entire yield of C344, C346 and C348; **on this target, in this window, it yields one
INFO and nothing chargeable.** Saying so is what makes the other fires' positives readable.
This pass's yield came from §C's machine checks instead.

### B.2 — Third direction (v28) / outward trees (v29)

`forum/` in the domain sweep: 0 rows in the residue that postdate the window. `git log -S
"constellation_trust_ceiling"` over the whole window: **0 commits.** The function at issue
has not been touched by anyone, anywhere, in 32 commits.

---

## §C — Findings

### N1 (MEDIUM → standard editor + SDK owner) — the constellation trust ceiling is non-monotone under enrolment: a strict superset of the anchor set can receive a strictly higher cap, and the standard mandates the sharpest case

**Locus.** `constellation_trust_ceiling` is published **twice, in agreement**: spec §3.4
pseudocode `web4-standard/core-spec/multi-device-lct-binding.md:611-659`, and the canonical
SDK `web4-standard/implementation/sdk/web4/binding.py:395-442`. The governing normative text
is §4.2 `:871-900`: a 7-row table, a MUST at `:884-887` (*"Implementations MUST use the
anchor-composition-derived ceiling (not a universal `1.0` cap) when clamping"*), and **two
precedence rules declared normative** at `:889-900`.

**Executed** (denominator: all **15** non-empty subsets of the 4-member `AnchorType` enum,
one `DeviceRecord` per type; and separately the **7** non-empty subsets of the 3-member
*hardware* enum, which is the denominator for "3 of 7"):

```
[phone_secure_element]              0.75   →  + software  0.80   RAISE
[fido2]                             0.80   →  + software  0.80
[tpm2]                              0.75   →  + software  0.80   RAISE
[phone_se, fido2]                   0.90   →  + software  0.90
[phone_se, tpm2]                    0.90   →  + software  0.90
[fido2, tpm2]                       0.90   →  + software  0.90
[phone_se, fido2, tpm2]             0.95   →  + software  0.98   RAISE
```

**The mechanism differs across the three, and conflating them would ship a false headline.**
Controls run:

| control | result | reading |
|---|---|---|
| `[phone_se, phone_se]` (2nd *identical* device) | **0.80** | raises 1–2 are a **device-count** effect: the set leaves the `n_active == 1` branch and lands in the `len(hardware_types)==1 → 0.80` fallback. Software is the cheapest witness of it, **not the cause**. |
| `[tpm2, tpm2]` | **0.80** | same |
| **`[phone_se, fido2, tpm2, tpm2]`** (4th device, *strong* type) | **0.95** | raise 3 is **genuinely software-specific**: a duplicate hardware anchor does **not** promote; only a *new type* does, and `software` is a new type. |
| `[phone_se, fido2, tpm2, software]` | **0.98** | the spec's own worked example, `:617-618` |

So the defensible predicate is **non-monotonicity under enrolment** (strict superset ⇒
strictly higher cap), of which the software case is the extremal instance: **the weakest
anchor type the standard defines promotes the constellation; the strongest one does not.**

**It is not an intermediate — it reaches the wire.** End-to-end `compute_constellation_trust`
(full cross-witness mesh, `days_since_witness = 0` throughout):

| composition | ceiling | raw | **final** | ceiling binding? |
|---|---|---|---|---|
| `[phone_se]` | 0.7500 | 0.9500 | **0.7500** | yes |
| `[phone_se, software]` | 0.8000 | 0.8019 | **0.8000** | yes |
| `[tpm2]` | 0.7500 | 0.9300 | **0.7500** | yes |
| `[tpm2, software]` | 0.8000 | 0.7900 | **0.7900** | no — raw binds |
| `[phone_se, fido2, tpm2]` | 0.9500 | 1.2060 | **0.9500** | yes |
| `[phone_se, fido2, tpm2, software]` | 0.9800 | 1.0758 | **0.9800** | yes |

Final constellation trust rises in **all three** pairs, and the ceiling lift is
*counterfactually necessary* in each (hold the old ceiling and `min()` returns the old
value). Even the one row where the ceiling is not binding still rises, 0.7500→0.7900,
because the raw term rose too.

**Direction, tested** (`git log -S`, per standing rule): precedence rules 1+2 and the §3.4
pseudocode fallbacks both arrived in **`d4f926ad` (#281, 2026-06-07)**, which is this
lineage's *own* remediation of C36. The SDK fallback **predates** them (`441b12f0`, #30).
**This kills the attractive framing** — "a newly-canonized principle retroactively re-scoped
a byte-frozen file", the C268 mechanism — because the rules predate C80's refutation by 14
days. **Recorded as a negative;** the finding stands on execution, not on chronology.

#### The prior decline, and why this is outside its range (v41)

**`C80:134` refuted** — verbatim: *"§4.2 ceiling table is non-exhaustive vs the §3.4 code
branches (2-hw=0.90, 1-hw=0.80, multi-software=0.40) | refuted | §4.2 L884-888 + L890-900
**explicitly** declare the `constellation_trust_ceiling` function (not the table)
authoritative and state the precedence rules. The table is intentionally illustrative. No
defect."*

That decline licenses **its own predicate: completeness** — *does the table enumerate every
branch?* This pass charges **direction** — *does the function's output move the right way?*
The two are not the same question, and **C80's rationale is a premise of this finding, not a
defeater of it**: if the table were authoritative, an unpublished `0.80` would be a
documentation gap and C80's disposal would be right. Because C80 ruled the **function**
authoritative, that same `0.80` is a **normative claim about trust**, and its direction
becomes chargeable. Charging completeness again would be a re-filing; this is not one.

**And the falsifier was in my predecessor's hands (v52).** `C80:50` — finding N3, verdict
**HELD** — reads: *"hand-reproduces all 6 `trust_ceiling_by_config` vector cases
(software→0.40, phone→0.75, fido2→0.80, phone+fido2→0.90, **3-named→0.95,
3-named+software→0.98**)."* C80 **enumerated the falsifying pair inside a single
parenthesis and certified the function HELD.** It was checking spec-vs-vector concordance and
never asked about direction, so it is not a refutation — but it is the strongest
"someone already looked here" artifact in the lineage, and it must travel beside `C80:134`.
My own novelty matcher did not surface it; the policy reviewer's did. Disclosed here per v41.

#### Rescue readings, anticipated and killed (v58)

| # | rescue | verdict |
|---|---|---|
| **R1** | *"More devices = more recovery redundancy; the premium is intentional."* | **Survives partially, and it is why the headline says "enrolment", not "software".** It explains raises 1–2 exactly — and is *falsified for raise 3* by the `[p,f,t,tpm2] → 0.95` control: a second hardware device adds the same redundancy and gets **no** premium. R1 cannot explain a rule that pays for the weak addition and not the strong one. |
| **R2** | *"The ceiling never binds — a software key drags `raw_trust` down, so final trust never rises."* | **FALSIFIED by execution.** The table above: final rises in all three pairs; the ceiling is the binding term in 5 of 6 rows. This was the strongest available rescue. |
| **R3** | *"`0.80`/`0.90` **are** table rows, so nothing unpublished is happening."* | **Fails.** `0.80` is the *Single FIDO2* row and `0.90` the *Phone + FIDO2* row; the fallbacks reuse the **numbers**, not the row semantics — the function asserts the Single-FIDO2 ceiling applies to a phone-SE-plus-software constellation. And C80 already made publication moot by ruling the function authoritative. |
| **R4** | *"Configurations are not ordered, so 'monotone' is undefined — a category error."* | **Does not survive.** §4.2 precedence rule 2 **itself** names two configurations standing in a strict subset relation (`[p,f,t]` ⊂ `[p,f,t,software]`) and assigns the superset a strictly higher cap. A subset relation is an order; monotonicity is well-defined on exactly the pairs the spec names. |
| **R5** | *"§4.1 `:863` allows 0.60–0.80 for mixed hardware/software, so 0.80 is in-band."* | **Correct, and it narrows the charge — recorded rather than dismissed.** `hardware_binding_strength` is a different quantity from the ceiling, and 0.80 sits at the top of its band. §4.1 does **not** forbid the *level*. **The defect is the direction (0.75 → 0.80), not the level.** Stating this is what keeps the finding MEDIUM and honest. |

#### Severity

**MEDIUM, not HIGH.** Reachable and wire-visible (the end-to-end table), but the two
unguarded raises are worth **+0.05** on a 0–1 scale, and the standard has no ratified
consumer that turns a constellation ceiling into an admission decision — consistent with
C308-N1's R3 bound (*"nothing executes both"* adopted as the severity bound, not as a
refutation). It is not a reason for the standard to reward enrolling the weakest device.

#### Routing, and the fork the author must resolve

**Not auditor-applicable — the remedy forks across two owners** and the fork is a design
question, not an editorial one:

- **(a) Rule-2 side** — strike the promotion: make the named `phone_se+fido2+tpm2` row match
  on the *hardware* subset (so a 4th software type does not promote), which requires editing
  §4.2 `:897-900`, §3.4 `:616-618`, `binding.py:419-426`, **and vector case 6** (`0.98` →
  `0.95`), i.e. changing a shipped conformance expectation.
- **(b) Fallback side** — make `len(hardware_types)==1` return the *single-device* row for
  that anchor type (0.75 for phone_se and tpm2), so device count alone cannot lift a cap.
  Touches `binding.py:437-440` and §3.4 `:653-657`.

(a) and (b) are independent; a one-sided fix leaves the other two raises standing, which is
**C346-N1's exact shape**. Adjudicate **jointly with C308-N1** (the envelope's `tpm2` = 1.0
against §4.2's `Single TPM2` = 0.75), because both are edits to the same seven rows.

---

### N2 (LOW → SDK owner + this ledger, instrument) — the two arms that produce the raises are unguarded by the entire 2755-test suite, and the one arm that is "guarded" is guarded only by a bound

**Guard inventory, denominator published.** Dedicated `constellation_trust_ceiling`
assertion sites: **7** — `test_binding.py:464, 478, 481, 491, 494, 507` plus the
vector-driven loop at `:705`. Shipped conformance vectors: **6 groups** in
`binding-vectors.json`, of which `trust_ceiling_by_config` carries **6 cases**. Full SDK
suite: **2755** (2750 passed + 5 xfailed).

**Per-arm mutation probe** of the "generic hardware-diversity fallback" block
(`binding.py:436-442`) — file copied to `/tmp` first, restored after every arm; `git diff`
verified empty and `md5sum` verified equal to `git show HEAD:…` at the end:

| arm | poisoned to sentinel `-99.0` | poisoned to a **plausible** wrong value | verdict |
|---|---|---|---|
| `len(hardware_types) >= 3 → 0.98` — **backed control** | **2 failed** (`test_ceiling_three_plus_diverse`, `test_trust_ceiling_by_config`) | — | **GUARDED by value.** The control fires, so the denominator is live. |
| `len(hardware_types) >= 2 → 0.90` | 2 failed (`test_integration.py`, `test_binding_attestation.py`) | **`0.98` → 1 failed** | **guarded only downstream.** Its lone *ceiling* assert is `test_integration.py:1597` `assert ceiling > 0.7` — a **bound**, which passes at `0.98`. |
| `len(hardware_types) == 1 → 0.80` ← **raises 1–2** | **2750 passed, 5 xfailed** | — | **UNGUARDED** |
| software-only-multi-device `→ 0.40` | **2750 passed, 5 xfailed** | — | **UNGUARDED** |

**0 of the 7 dedicated assertion sites reach either unguarded arm.** The arm carrying raise 3
*is* pinned (vector case 6) — so guard-blindness covers **2 of the 3 raises, not 3 of 3**.
Stating the split is the finding's honest form; "the fallback block is unguarded" would be
**false**.

**⇒ v59, and this is the transferable part.** A mutation probe that substitutes an *absurd
sentinel* measures **reachability**. A probe that substitutes a *plausible wrong value*
measures **the assertion**. The `>= 2` arm is the demonstration: sentinel says guarded,
`0.98` says the only ceiling assert is a floor test that admits any value above 0.7. Every
prior pass in this lineage that used a sentinel would have over-reported guard strength here.

**The coverage gap is an Nth member of the named `remediation-incompleteness` family**
(C384, C386) — **not net-new as a class.** `multi-device-lct-binding-internal-consistency-2026-05-28.md:228`
recorded *"(a) Missing 'Single TPM2' row. The table covers single-phone-SE, single-FIDO2,
single-software — but skips single-TPM2"*, restated at `:528` as D4. The remediation **added
the §4.2 row and never added the vector or the unit assert**: `trust_ceiling_by_config` has
6 cases pinning 6 of the 7 table rows, and `["tpm2"] → 0.75` is the one with neither a vector
case nor a `TestTrustCeiling` assert (`grep -n tpm2 test_binding.py` returns fixtures and
diversity tests only). It is also **the same row C308-N1 charged** against the
AttestationEnvelope's `tpm2` = 1.0 — the standard's least-tested ceiling row is its most
contested one.

---

### INFO-1 (recorded, not charged) — new in-standard text about this target's subject matter landed in the window

`web4-standard/core-spec/security-framework.md:78` — *"Root-LCT public state, constellation
membership, enrollment/revocation state, recovery policy, and public Device-LCT material MAY
be replicated across authorized devices."* — was **added in-window** by `afd04623` (#678, the
hackathon fold), confirmed by `git log -S "constellation membership, enrollment/revocation
state" -- web4-standard/core-spec/security-framework.md` returning exactly that commit.

It is the **only** in-standard residue row and it lands in the file holding this lineage's
**B-10** arm. It is a `MAY` about replication and does not conflict with the target's
`:257`/`:270`, so it is **not charged**. Recorded because it is a live change to the
security ledger's text about *our* subject matter, and because the next pass should check
whether it acquired normative force. **Do not re-charge unless it changes modality.**

### INFO-2 (recorded) — the canonical SDK docstring is silent on the behaviour §4.2 makes normative

`binding.py:396` is one line: *"Max trust achievable given current anchor type mix."* The
spec's mirror carries the full rationale at `:616-618` (*"...is why a [phone_se, fido2, tpm2,
software] constellation resolves to 0.98 ... rather than the 3-type named 0.95 row"*). The
canonical implementation of a normative rule carries none of the rule's disclosure. Not a
separate finding — it folds into N1's remedy, whichever fork is taken.

---

## §D — C348's guards and carries, re-adjudicated at HEAD `cd39cfab`

| # | C348 guard | verdict at HEAD |
|---|---|---|
| 1 | *Check whether B-10 was re-typed with its per-locus split, in the security ledger **and** here* | **NOT DONE on either side.** `security-framework.md` moved once in-window (`afd04623`) and the change is INFO-1, not a B-10 re-typing; this ledger has no split either. **Still open, still symmetric** — which is the correct state, since a split recorded on one side only is C346-N1's shape. **Re-check at C428.** |
| 2 | *Run the inbound set difference BEFORE §A; pre-register the verb set; search by subject matter as well as by label* | **DONE — §B.** Result is a **recorded negative**: 41 residue rows, 8 postdating, 7 of them a cluster two sibling ledgers already own, 1 INFO. First time in four passes this instrument yielded nothing chargeable on this target. |
| 3 | *Type every identifier before comparing two of them* | **DONE — §A is a blob-only column.** It earned its keep immediately: `hub.rs` reads MOVED at blob level while the C308-N2 lines inside it are untouched, and an untyped table would have mixed those. |
| 4 | *Build §E by capture; root every basename; never publish a `git log -- <path>` green without confirming the pathspec matches a tracked file* | **DONE — §E, built last and by capture.** |
| 5 | *Check whether C330's instrument was re-typed (N2), and whether C80's accounting is cited when it is* | **NOT re-typed — and the way it failed is worse than "not read".** `docs/audits/C370-inter-society-protocol-9th-delta-2026-08-12.md` cites **C330 fourteen times**, discharges C330's entire six-item deferral row, and rules explicitly on the finding-id census (item 6, **DECLINED** as underpowered on C330's own numbers, Fisher p=0.749). So the receiver was working C330's ledger *in that very pass*. Yet `grep -c "C348"` over C370 = **0**, and `grep -ci "orphan"` = **0** — the orphaned-by-id correction C348 sent (`C330:262`: *"Orphaned-by-id ≠ unconsumed … routed as a forward guard, not a finding"*) is **absent**. **The row was not skipped for lack of attention; it was invisible while its receiver had the ledger open**, which is precisely what C348 diagnosed and precisely why filing under the sender's id fails. **Second miss on this row.** Re-route below. |
| 6 | *Do not re-open: the 9-of-9 C80 accounting; C308-N1/N2's mirror layer while its ten blobs are frozen; the `binding` conformance-suite absence (C308 INFO-1, C276 precedent)* | **HONOURED.** None re-opened. Note the conformance-suite row has **shifted in fact but not in disposition**: `testing/conformance/` still has no binding suite, but `test_binding.py:646-748` **does** load and run all 6 vectors, so the vectors are not orphaned. Recorded, not charged — C276 precedent stands. |

**C308 carries, status only** (all held by the freeze of §A's nine blobs): C308-N1 (envelope
vs §4.2 ceiling table) **unconsumed** — and **N1 above is its neighbour**, same seven rows,
so they must be adjudicated together. C308-N2 (`HardwareBinding::default()` `trust_ceiling:
0.85` vs the spec's 0.4 software cap) **unconsumed**, `web4-core/src/lct.rs` blob-identical.
C268-N1 (all-software constellation permanently barred from recovery, contra LCT §1.2)
**unconsumed**, `:155`/`:795-801` byte-frozen. **Not re-litigated.**

---

## §E — Instrument index (built last, by capture — C348 guard 4)

Uniqueness run over **all 12** baseline basenames
(`git ls-tree -r --name-only cd39cfab | grep -c "/<basename>$"`), because
`forum/nova/web4-sal-bundle/` shadows 8 `core-spec/` basenames at differing blobs and is the
standing trap on this target. **11 of 12 return 1. `test_integration.py` returns 2** —
`simulations/test_integration.py` and `web4-standard/implementation/sdk/tests/test_integration.py`.
Every reference to it in this document is rooted to the second; the bare basename would have
been a fork. (This is the one instrument cell in this pass that failed its own check on first
run — see §F.6.)

| # | instrument | scope / denominator | command |
|---|---|---|---|
| I1 | freeze | 10 baseline artifacts, blob column | `git rev-parse cd39cfab:<path>` ×10 |
| I2 | window | 32 commits, `afa107f5..cd39cfab` | `git rev-list --count afa107f5..HEAD` |
| I3 | filename sweep | 21 files, `docs/audits/` excluded | `git grep -li "multi-device-lct-binding" -- .` |
| I4 | domain sweep | 48 files, 7 roots, 5 exclusions | `git grep -li -E "constellation" -- <7 roots>` |
| I5 | residue | 41 = I4 ∖ I3 | `comm -23` |
| I6 | ceiling execution | **15** non-empty subsets of the 4-member `AnchorType`; **7** non-empty subsets of the 3-member *hardware* enum (the "3 of 7" denominator) | `itertools.combinations` over `AnchorType`, one `DeviceRecord` per type |
| I7 | end-to-end | 6 compositions + 3 controls, full mesh, `days_since_witness=0` | `compute_constellation_trust(c, days_since_witness=…)` |
| I8 | mutation probe | 4 arms × {sentinel, plausible}; suite = **2755** (2750 + 5 xfailed) | `cp` → edit → `python3 -m pytest tests/ -q` → restore → `git diff` + `md5sum` |
| I9 | guard inventory | **7** dedicated assertion sites | `git grep -n "constellation_trust_ceiling" -- web4-standard/implementation/sdk/tests/` |
| I10 | direction | 4 `-S` probes | `git log --oneline -S "<literal>" -- <rooted path>` |
| I11 | novelty | 7 matchers + 6 reviewer matchers, over `docs/audits/` + `web4-standard/docs/audits/` | `grep -rliE` |

**Restoration verified explicitly** after I8: `git diff --stat -- …/binding.py` empty, and
`md5sum web4/binding.py` = `f1a085d108e87c35d573d61ddc35fb39` = `git show
HEAD:web4-standard/implementation/sdk/web4/binding.py | md5sum`. Byte-identical to HEAD.
Nothing was left behind, in this worktree or the shared main.

**Novelty, matcher published** (N1's class): `monoton`, `raise the ceiling`, `raises the`,
`weaker anchor`, `enrolling a software`, `software.*rais`, `adding a software`, `lower the
ceiling`; plus, from the policy reviewer, `non-monoton`, `perverse`, `counterintuitive`,
`inversion.*ceiling`, `ceiling.*(increase|higher)`, `0\.75.{0,12}0\.80`, `0\.95.{0,12}0\.98`,
`len\(hardware_types\)`. `grep -rlow "monotone" docs/audits/` returns **8 files, 7 excluding
this one** — C206, C222, C244, C246, C252, C260 (all the `web4-core/ratchet.rs`
governance-ratchet naming thread) and C308; the case-insensitive stem `monoton` adds C27
(section renumbering). **`C308:150` R5 uses "monotone" as a *refuted rescue label* on a
different predicate** (constellation cap vs AttestationEnvelope device cap) — the word is in
this lineage, the question is not. Five audits reference
`constellation_trust_ceiling` (internal-consistency, C36, C80, C120, C308); **none asks
direction-of-change under enrolment.** Novel.

---

## §F — Own errors

1. **My first headline was FALSE in its causal attribution, and my own output held the
   falsifier.** I framed all three raises as *"enrolling a software-only device raises the
   ceiling"*. The duplicate-device control — `2 x phone_secure_element -> 0.8` — was **printed
   in my own first execution block**, three lines below the software table, and I wrote the
   software framing anyway. Raises 1–2 are a device-count effect. The policy reviewer ran the
   control I had already run and read it correctly. **This is v52 turned on myself: the
   falsifier was not in a predecessor's document, it was in my own terminal.** Corrected
   above; the surviving predicate (non-monotonicity under enrolment, with raise 3
   software-specific and *proved* so by the `[p,f,t,tpm2] → 0.95` control) is narrower and
   stronger than what I proposed.
2. **I generalized a two-arm measurement to a three-arm block.** I measured "2 failed" for
   the `>= 2` arm and then wrote "the fallback block is unguarded". It is not; 2 of 3 arms
   are. The correction led directly to the sharpest result in the pass (the bound-vs-value
   probe, v59), which I would not have run had I not been forced back to the arm I had
   mis-summarized.
3. **My novelty matcher missed `C80:50`** — the strongest materiality artifact in my own
   lineage, which enumerates my falsifying pair in a parenthesis. My matchers searched the
   *finding's* vocabulary; `C80:50` is written in the *vector's* vocabulary (`3-named+software→0.98`).
   v44 says search the domain expert's words; a **vector case name is a domain word** and my
   matcher set had none. Added to the guards below.
4. **The attractive framing was killed by my own direction test.** I expected the C268
   mechanism (a newly-canonized rule retroactively re-scoping a frozen file) and `git log -S`
   dated the rules 14 days *before* C80's refutation. Recorded as a negative rather than
   quietly dropped, because the next pass should not re-derive it.
5. **I claimed a uniqueness check I had not finished, in the section that certifies the
   others — C348's guard 4, missed on the same guard's own terms (v39, second firing on this
   lineage).** §E's first draft asserted all baseline basenames returned **1**. Run properly,
   `test_integration.py` returns **2** (`simulations/` + the SDK tree). No value in the
   document was wrong — every reference was already to the SDK path — but the warranty was
   false while the numbers were true, which is v39 verbatim, one pass after C348 wrote it
   down. **The correction that catches this is mechanical and should be automated:** run the
   uniqueness loop over the basename list *before* writing §E, not as a claim inside it.
6. **Two of my §D verdicts were right for the wrong evidence.** I wrote that C370 "does not
   cite `C330:262`'s instrument"; it cites C330 **fourteen** times and discharges its whole
   deferral row. The verdict survives — `C348` and `orphan` are both **0** in C370 — but the
   corrected evidence makes the finding *stronger*, not weaker (the receiver had the ledger
   open and still could not see the row). Per v41: **when correcting your own cite
   strengthens your argument, the original was guessed.** It was.
7. **Policy review falsified this pass's headline — the 10th consecutive fire in which it
   has struck a central premise or headline** (C354, C356, C364, C366, C372, C378, C382,
   C384, C386, C388). Corrections issued: **6**; verified independently and **accepted: 6**;
   **rejected: 0** (second consecutive zero-rejection). Every reviewer-supplied anchor
   resolved as written on this pass — `C80:50`, `C80:134`, `internal-consistency:228`/`:528`,
   `§4.1:863`, `test_integration.py:1597`, `binding.py:396` — **6 of 6 exact**, the first
   pass in four with no off-by-one. Per v56, the reviewer's anchors are still **my** cells,
   and I re-ran all of them.

---

## §G — Disposition

**Findings: N1 MEDIUM · N2 LOW · 2 INFO. 2 net-new. ZERO mutation. 1 new file.**

- **C389 = declared NO-OP.** N1's remedy **forks across two owners** and changes a shipped
  conformance expectation under fork (a); that is an author ruling, not an auditor's edit.
  N2 is this ledger's own instrument plus an SDK coverage gap whose fix must follow N1's
  fork (adding the missing vector before the ceiling values are settled would pin the wrong
  number). Do **not** self-fix the target, `binding.py`, `binding-vectors.json`,
  `attestation-envelope.md`, or any C80/C268/C308/C348 text.
- **Delivered outward this fire, not merely routed** (v36 applied to this pass's own output):
  **C348-N2 is re-routed**, because its C370 re-check found it undelivered. It is recorded
  here under **both** `C330:262`'s id **and** its subject matter (*"an orphaned-by-id
  instrument reads a remediated lineage as a dropped one"*), so a sweep from either side
  joins them. Next ISP slot ≈ **C410**. **If it is still open at C410 that is three misses on
  one row across three passes, and the instrument — not the row — is the finding.**
- **N1 routes to the standard editor and the SDK owner jointly, adjudicated with C308-N1**
  (same seven rows). **N2's coverage half routes to the SDK owner, after N1's fork resolves.**
- **Rotation**: next multi-device delta ≈ **C428**.

**Baseline for C428** (blob column; each basename verified unique in the tree at
`cd39cfab`): target `web4-standard/core-spec/multi-device-lct-binding.md` `b979ea7d`
(*commit* `a6cbde92`, 1126 L; N1 loci §4.2 `:871-900`, §3.4 `:611-659`, fallbacks `:653-657`;
C268-N1 sites `:155`, `:795-801`; B-10 `:257`/`:270`);
`web4-standard/implementation/sdk/web4/binding.py` `857f8040` (N1 `:395-442`, fallbacks
`:436-442`, docstring `:396`); `web4-standard/test-vectors/binding/binding-vectors.json`
`dc969641` (6 groups; `trust_ceiling_by_config` 6 cases; **case 6 = `0.98`, the pinned raise**);
`web4-standard/implementation/sdk/tests/test_binding.py` **NEW to the baseline** `ad7fd3dd`
(748 L; guard sites `:464,478,481,491,494,507,705`);
`web4-standard/implementation/sdk/tests/test_integration.py` **NEW to the baseline**
`e3c23c00` (`:1596-1597`, the bound assert — **root this path; the basename is not unique**);
`web4-core/src/ratchet.rs`
`806882b1`; `docs/specs/attestation-envelope.md` `c2f604aa`;
`web4-standard/implementation/sdk/web4/attestation.py` `37a7c673`;
`web4-core/python/web4_core/trust/attestation/envelope.py` `c3046043`;
`web4-standard/test-vectors/attestation/attestation-vectors.json` `fecbc695`;
`web4-core/src/lct.rs` `2e9d4586`; `hub/hub-lib/src/hub.rs` **`fd45f9ce`** (moved this window;
C308-N2 lines untouched).

**Guards for C428.**
1. **Re-run I6 and I7 FIRST and identify WHICH fork landed** (a: rule-2 side, b: fallback
   side, or neither). A one-sided fix leaves the other raises standing and is the C346-N1
   shape. If vector case 6 still reads `0.98`, fork (a) did **not** land regardless of what
   the spec text says.
2. **Mutate to a plausible wrong value, not a sentinel** (v59). Re-run the 4-arm probe in
   *both* modes and publish both columns. A guard that fires on `-99.0` but not on `0.98` is
   guarding reachability, not the value. Check specifically whether
   `test_integration.py:1597`'s `assert ceiling > 0.7` is still a bound.
3. **Add vector-case vocabulary to the novelty matcher** (§F.3). Before claiming net-new,
   grep the lineage for the *vector case names* and their expected values
   (`3-named→0.95`, `trust_ceiling_by_config`, `constellation_trust_multi_device`), not only
   the finding's prose. `C80:50` was invisible to eight prose matchers.
4. **Check C348-N2 at the ISP ledger (≈C410) before re-routing it a third time**, and if it
   is still open report the *instrument*, not the row.
5. **Re-run the §B set difference** — it produced a recorded negative this pass, and a
   negative followed by a negative is a fact about the target; a negative followed by a
   positive dates the change. Same pre-registered domain word (`constellation`), same 7
   roots, same 5 exclusions, so the counts are comparable: **21 / 48 / 41 / 8**.
6. **Check whether `security-framework.md:78` acquired normative force** (INFO-1). It is a
   `MAY` today. Do not charge it otherwise.
7. Do **not** re-open: `C80:134`'s completeness predicate; the 9-of-9 C80 accounting;
   C308-N1/N2's mirror layer while its blobs are frozen; the hub constellation-MFA /
   AssuranceReceipt cluster (C286-N3, C288-N2 own it); the binding conformance-suite absence
   (C308 INFO-1 — and note the vectors themselves *are* run, by `test_binding.py:646-748`).

---

## Pattern (C388)

**C386 found a claim no instrument consumes. This pass found its inverse: a claim two
instruments consume, agree on, and are both wrong about — because they were both asked
whether the number was *right*, and never whether it moved the *right way*.**

Six audits over 78 days checked `constellation_trust_ceiling` against its table, its vectors,
its mirror, and a rival table in another document. Every one of those is a **point** check:
*for this composition, is the value correct?* The function passes all of them. Nobody ran a
**pair** check: *for these two compositions, one a subset of the other, does the value move
the right way?* The spec's own precedence rule 2 names such a pair explicitly, in one
sentence, and assigns the superset a higher cap — and C80 quoted both halves of that pair in
a single parenthesis while certifying the function HELD. **The falsifier was never hidden; it
was never the question.**

**v59 (new): mutate to a plausible wrong value, not a sentinel — a sentinel measures
reachability, a plausible value measures the assertion.** Poisoning the `>= 2` fallback arm
to `-99.0` produces two failures and reads as *guarded*. Poisoning it to `0.98` produces one,
and reveals that its only ceiling assert is `assert ceiling > 0.7` — a floor that admits every
value the arm could plausibly return wrong. A green suite proves the vectors it ran; a red
suite under a sentinel proves only that *something downstream is arithmetic*. Between them
sits the class of defect this lineage keeps finding: **a value that is wrong but reasonable.**
Sentinel probes are blind to exactly that class, and every prior pass in this lineage used a
sentinel.

**Corollary, and it is the one with teeth for the next pass: the control you need is often
already in your own output.** The duplicate-device row that falsified this pass's first
headline was printed by this pass's first command, three lines below the table it
contradicted. v52 says your predecessor holds the falsifier. The sharper version is that
**you** hold it, and the reason you cannot see it is that you already know what you are
looking for. → [[feedback_mutate_to_a_plausible_value]] / [[feedback_predecessor_holds_the_falsifier]] /
[[feedback_unconsumed_claim_is_a_fork]] / [[feedback_decline_licenses_its_range]] /
[[feedback_unit_green_is_not_system_green]].
