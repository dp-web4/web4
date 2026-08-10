# C348 — `multi-device-lct-binding.md` Seventh Delta Re-Audit (a carry this lineage *sent* came back, by rediscovery rather than delivery — and a guard routed to this slot by number discharges NEGATIVE with a complete accounting)

**Date**: 2026-08-09
**Target**: `web4-standard/core-spec/multi-device-lct-binding.md` (1126 L, blob `b979ea7d`)
**Prior pass**: C308 (6th delta, 2026-08-01, PR #629-adjacent), base `69a5f471`
**This pass's HEAD**: `afa107f5`
**Lineage** (**8** docs at base; this pass is the 9th). **Membership rule, stated per the C346 rev1
correction**: every `docs/audits/*multi-device*` document, C-numbered or not — the same inclusive rule
this track applies to the ISP and atp-adp lineages, each of which likewise has a non-C-numbered
`…-internal-consistency-…` member.
`multi-device-lct-binding-internal-consistency-2026-05-28` → C36 → C80 → C81 → C120 → C152 → C268 →
C308 → **C348**. (C19 is the first-pass audit under its own filename and is chained by C308's header.)
**Mutation**: **ZERO.** No spec, schema, SDK, vector, config or sibling file is edited by this pass.
**Rev1**: 2026-08-10 — clears the standing block on PR #682. **No finding, severity, verdict or
measured value changes.** The block was against **§E**, the pass's own warranty surface, on two
classes this document had cleared on `#681` four hours earlier: a denominator narrower than its own
instrument's reach, and unrooted path tokens. Both were swept **by class over the whole document**
(v35) rather than by the cells named, which returned **three further members the block did not name**.
Full account and the resulting method carry (**v39**) in **§F.5**.

---

## Headline

Target byte-frozen **49 days** (`a6cbde92`, 2026-06-21) — the fifth consecutive frozen delta, and the
first **ten-fold** frozen one once the C308-N1 mirror layer is included (C308's quadruple **+ 6**
mirror files = **10**; §A publishes all ten. *Rev1: this sentence read "sextuple", which named the size
of the addition and not the size of the set the table certifies — §F.5 item 3.*). Window = **56** commits,
`web4-standard/core-spec/` **0 changed files**. Every C308 carry probe reproduces. On the numbers this
should be empty.

It is not, and both reasons arrived **after C308 closed** — which is why the instrument that found
them is the **v36 set difference over the inbound corpus**, run before §A, and not any re-reading of
the target.

1. **A carry this lineage *sent* was received — by rediscovery, 32 days late, and the receiver's own
   pass records it as having been *lost*.** C152 (2026-07-07) proved that carry **B-10**'s prescription
   (`cose:ES256` → `cose:EdDSA`) is wrong for this hardware-P-256 spec. C268 and C308 both re-recorded
   it *unconsumed*. On **2026-08-08 — one day before this pass** — `C336-N2` charged exactly that
   result as a MEDIUM net-new *direction inversion*, crediting `C152:22` by name; and `C336-N3`
   separately records `C152-1` as one of two inbound routes that were **lost**, lost because it was
   written under *this* lineage's id rather than the security ledger's. **C308's row is false at
   HEAD.** → **N1.**
2. **A guard routed to this slot BY NUMBER discharges NEGATIVE, with a complete 9-of-9 accounting —
   and the mechanism is the interesting part.** `C330:262` (2026-08-07) routed *"the C348 multi-device
   delta should check whether C80's seven findings were consumed through some other channel or
   genuinely dropped."* They were consumed, by the strongest channel available: a **remediation commit
   that edited the target itself**, one day after C80. → **N2** (and see the discharge in §C.2).
3. A third, smaller item: C308's freeze table certifies *"all four byte-identical"* over a column that
   holds three blobs and **one commit**. → **N3.**

---

## Severity legend

| level | meaning |
|---|---|
| HIGH | a conformant implementation reading the spec is led into a wire-incompatible or unsafe result |
| MEDIUM | a normative statement is unsatisfiable, self-contradictory, or contradicted by the standard's own machine-readable artifacts; **or** a ledger row's live status is false at HEAD, or rests on evidence that cannot reach it |
| LOW | a defect in an in-standard or in-ledger artifact that does not change what a conformant implementation emits |
| INFO | a re-verification, an exclusion re-held, a routed guard discharged, or an instrument note |

---

## §A — Freeze, by blob identity, with the column typed

**The type of every cell is declared, because typing it is N3.** `blob` = `git rev-parse HEAD:<path>`;
`commit` = `git log -1`. A freeze claim of the form *"byte-identical to the prior pass's state"* is
only available where the prior pass published a **blob**.

| artifact (repo-relative) | blob at HEAD | window commits |
|---|---|--:|
| `web4-standard/core-spec/multi-device-lct-binding.md` | `b979ea7d` | **0** |
| `web4-standard/implementation/sdk/web4/binding.py` | `857f8040` | **0** |
| `web4-standard/test-vectors/binding/binding-vectors.json` | `dc969641` | **0** |
| `web4-core/src/ratchet.rs` | `806882b1` *(C308 published `7b048a78`, which is a **commit** — N3)* | **0** |
| `docs/specs/attestation-envelope.md` | `c2f604aa` | **0** |
| `web4-standard/implementation/sdk/web4/attestation.py` | `37a7c673` | **0** |
| `web4-core/python/web4_core/trust/attestation/envelope.py` | `c3046043` | **0** |
| `web4-standard/test-vectors/attestation/attestation-vectors.json` | `fecbc695` | **0** |
| `web4-core/src/lct.rs` | `2e9d4586` | **0** |
| `hub/hub-lib/src/hub.rs` | `2431521d` | **0** |

**All ten frozen**, including the entire C308-N1/N2 mirror layer — so both C308 findings stand
unremediated by construction, and no per-anchor re-resolution is published, because on unchanged blobs
it cannot return a finding.

**Window.** `git rev-list --count 69a5f471..afa107f5` = **56** commits.
`git diff --name-only 69a5f471..afa107f5 -- web4-standard/core-spec/` = **0 files**. C308's executive
point 7 predicted this and it holds.

---

## §B — The inbound sweep, run FIRST (v36 as a set difference, v37)

C346 established that on a heavily-cited target the raw inbound grep is a token sink and the usable
instrument is a **set difference**: rows in non-lineage documents naming the target *as an addressee*,
minus the rows this ledger holds. Here the corpus is small enough to run exhaustively.

```
git grep -l "multi-device-lct-binding" afa107f5 -- docs/audits web4-standard/docs/audits   →  31
  minus the 8 lineage documents (inclusive rule)                                        →  23 non-lineage
```

**Verb set PRE-REGISTERED before the run** (v26, and the C346 rev1 lesson that an unregistered filter
is an unfalsifiable one): `owner|route|routed|carry|carried|owed|addressee|cross-track`, applied to
lines already matching `multi-device`.

**12 of the 23 carry addressee language.** Eight are the security-framework lineage re-recording the
**B-10** arm (C68, C108, C140, C180, C218, C256, C296, C336) and two are the t3-v3 lineage on the
`t3_tensor` DESIGN-Q (C42, C82) — both already held in this ledger. **The residue is two rows this
ledger does not hold, and both postdate C308:**

| row | source | date | held at C308? |
|---|---|---|---|
| B-10's prescription **adjudicated and re-typed with a per-locus split** | `C336-N2` | **2026-08-08** | **no** — C308 records it *unconsumed* |
| *"the C348 multi-device delta should check whether C80's seven findings were consumed"* | `C330:262` | **2026-08-07** | **no** — routed after C308 closed |

**Both are receptions, not defects in the target. The entire yield of this pass came from the inbound
sweep, for the third consecutive fire on this track.**

### B.2 — Third direction (v28) and the outward trees (v29)

`git grep -c "cose:ES256" afa107f5 -- 'web4-standard/**/*.md'` = **9 occurrences / 4 files**, reproducing
C296 and C336 to the digit; this target holds **2** of them (`:257`, `:270`).
`grep -rn "cose:EdDSA" web4-standard/` = **0**; `grep -rn "cose:EdDSA" . | grep -v docs/audits` = **0** — the token this lineage has been asked
to adopt exists **only inside audit prose**, which is itself the substance of C336-N2.

---

## §C — Findings

### N1 (MEDIUM, net-new by reception) — this ledger's B-10 row is false at HEAD: the sharpening it sent was adjudicated one day ago, and the receiver's own pass records the delivery as having failed

**What this ledger says.** C308 §A.2: *"**B-10 arm** … **STILL-OPEN — STATUS-CHECK ONLY**. Owner
ledger unmoved ⇒ no adjudication has occurred. C152's sharpening (the prescription overreaches on this
hardware-P-256 spec) **stands unconsumed.** Not re-litigated."* C268 `:56` says the same thing.

**What is true at HEAD.** `C336-N2` (2026-08-08, **MEDIUM, net-new by direction inversion**):

> *carry **B-10**'s prescription is **wrong for 2 of its 8 loci**, was proved so by a sibling lineage
> on 2026-07-07, was re-recorded *unconsumed* by two later sibling passes, and has never been named in
> a single security-lineage document. The refutation is available **inside the target itself**.*

and its disposition: ***"B-10 must be re-typed with its per-locus split"***, now standing in the
security lineage's operator bundle as *"a separate ask, and the more urgent one."* The two loci are
`multi-device-lct-binding.md:257` and `:270` — **this file's**.

**Measurement — the reception happened at C336 and nowhere earlier.**

```
git grep -c "C152" afa107f5 -- 'docs/audits/*security-framework*'
  →  C336-security-framework-8th-delta-2026-08-08.md:10        (one file, ten hits)

git ls-tree -r --name-only afa107f5 docs/audits/ | grep security-framework | wc -l   →  10
```

**Ten security-lineage documents; exactly one cites `C152`, and it is the one published yesterday.**
So the row did not travel — it was **rediscovered**, from the target's own text
(`web4-standard/core-spec/security-framework.md:35-36`, `:44`), 32 days after C152 proved it.

> **Rev1 — the denominator was published as nine and the instrument addressed ten.** The tenth member
> is `docs/audits/C109-security-framework-remediation-2026-06-28.md`, a **remediation**, excluded by an
> exclusive reading of the membership rule while this document's *own* lineage was enumerated by the
> **inclusive** rule stated in the header — which admits `C81`, a remediation, as member 7 of 8. That
> is `C346 rev1` §F.7's defect with the sign flipped, and it is the block on this PR. C109 holds **0**
> occurrences of `C152` and **0** of `multi-device`, so the corrected reading does not disturb the
> result — it **strengthens** it: **1 of 10**, not 1 of 9. Recorded in §F.5.

**And the receiver says so itself.** `C336-N3` (LOW) records inbound non-reception as *selective*:
three routes, **1 received / 2 not** — and `C152-1` is one of the two lost, lost because *"it named
the **sibling's** ids"* rather than the security ledger's. `C336:343`: *"An inbound item is received
when the sibling writes it under an id this ledger already types, and lost when it is written under
the sibling's own id — regardless of how explicitly the owner is named. C152 named the owner **twice**,
in the flagship and in a dedicated adjudication paragraph, and it still did not arrive."*

**Why this is a MEDIUM against this ledger and not a note.** C308's row is not stale in the ordinary
sense of *not yet re-checked* — it makes an affirmative claim about the owner's ledger (*"owner ledger
unmoved ⇒ no adjudication has occurred"*) whose probe was `git log` over
`web4-standard/core-spec/security-framework.md` and `web4-standard/protocols/` (C308's cell names both
unrooted; both resolve uniquely under `web4-standard/` — *except* that
`forum/nova/web4-sal-bundle/security-framework.md` also exists at a different blob, §F.5 item 2).
**A spec-freeze probe cannot see an adjudication that lives in an audit document.** That is `C346-N1`'s `C290:75` failure exactly, in this lineage, in the opposite
direction: there a *sender* certified a row against a spec blob; here a *receiver* certified
non-reception against one. **v31 fires: an OPEN row licenses only the predicate its evidence
answered.**

**Three refutations attempted.**

1. *"C308 was right on 2026-08-01; C336 is 2026-08-08 — no defect."* — **Fails on what the row
   claims.** *"Owner ledger unmoved"* was measured over spec files, not the owner's audit ledger, and
   would have returned the same answer on 2026-08-09. The probe cannot date-bound its way to
   correctness; it was never able to see the channel adjudication occurs in.
2. *"C336-N2 is the security lineage's finding, so it is theirs to record."* — **Fails on v37, in the
   direction C346 established.** A disposition must be written into the ledger of the row being
   disposed of. `B-10`'s **arm** is carried here. C336 disposed of it. This pass is the one that has
   read both ledgers, so it is the one that can close the row — and doing so is what §D does.
3. *"Nothing changed for the spec."* — **Granted, and that is why it is MEDIUM and not HIGH.** No byte
   of the target moves and no implementation emits anything different. What changes is that an
   operator reading this ledger would be told a question is unanswered that was answered yesterday,
   and re-typed with a split this file's two loci depend on.

**Severity: MEDIUM. Route: this ledger (discharged in §D — the row is re-typed here) + operator, where
it now bundles with `C336-N2` rather than standing alone.** The corrective is structural and is the
mirror of C346's v37: **v37 has a receiving half — when your carry is adjudicated elsewhere, the
adjudication does not arrive; you must go and get it, and only a pass that reads both ledgers can.**

### N2 (LOW, net-new, instrument → the C330/ISP lineage) — the orphaned-by-id instrument reads a *remediated* lineage as a dropped one, and this file is the proof case

`C330:262` routed a forward guard to this slot by number. **It is discharged here, NEGATIVE, with a
complete accounting** (§C.2 below). The net-new content is not the discharge — C330 explicitly declined
to claim the findings were dropped, and hedged correctly (*"Orphaned-by-id ≠ unconsumed"*). It is the
**mechanism**, which C330 could not see and this pass can:

**C80's items were consumed by a commit, not by a citation.** `C81` (2026-06-21, PR #372, `a6cbde92`)
applied seven of them to the spec — and **that commit is the byte-freeze** every subsequent pass
certifies. So the 49-day freeze that an activity-based instrument reads as *nothing happened* is
precisely the **evidence of consumption**. An id-citation sweep over later audit documents is
structurally blind to it: the findings left the audit-document channel entirely and entered the
standard.

**Severity: LOW** — it changes nothing a conformant implementation emits, and it charges an
instrument's reach, not a conclusion. It is recorded rather than dropped because C330's *family-level*
claim (clustering exists, Poisson `P(≥2) = 0.0147`) uses a null model in which a remediated lineage and
an abandoned one are indistinguishable, and this lineage is a measured counterexample.
**Route: C330 / ISP lineage + operator.** Not auditor-applicable: whether to re-type the instrument or
to re-run it with remediation commits as a second channel is the owning lineage's call.

### §C.2 — The discharge itself (the accounting C330 asked for)

`C80` published **8 numbered findings + 1 §A flagship = 9 items.**

| disposition | items | evidence |
|---|--:|---|
| **Applied to the spec by C81** (`a6cbde92`, #372) | **7** | flagship (`cross_witness` arity, §3.2 `:490`), N3, N4, N5, N6, N7, N8 — each with its site and change in C81's *"Findings applied (7)"* table; 95 binding tests green; SDK + vectors deliberately unchanged, the spec aligned to them |
| **Held as live carries, still open at HEAD** | **2** | N1 (flat 8-dim `t3_tensor`) and N2 (no entity-role binding) — both in C81's *"Not applied"* table as cross-spec DESIGN-Q, both re-adjudicated STILL-OPEN at C120, C152, C268, C308 and again here (§D) |
| **dropped** | **0** | — |

**9 of 9 accounted for. Zero dropped.** C330's guard is answered.

### N3 (LOW, net-new, instrument → this ledger) — the freeze table certifies byte-identity over a column with one commit in it

C308 §A.1 is headed **"Blob / last commit"** and closes: *"All four **byte-identical** to their C268
state ⇒ … Third consecutive frozen wrap; first **quadruple**-frozen one."*

Three of the four cells are blobs (`b979ea7d`, `857f8040`, `dc969641` — all re-derived here and
correct). The fourth, `7b048a78`, is **a commit**:

```
git cat-file -t 7b048a78                        →  commit
git rev-parse --short 69a5f471:web4-core/src/ratchet.rs   →  806882b1   (the blob, at C308's own HEAD)
```

**And there is no C268-side blob for it to be identical to.** C268 introduced `7b048a78` correctly, as
a *PR reference* (`web4-core/src/ratchet.rs (#529, 7b048a78)`) for a consumer that was **new** at that
pass. C308 transplanted that token into a byte-identity column. So for 1 of the 4 rows, the stated
basis — *byte-identical to their C268 state* — has **no referent on the C268 side**.

**The verdict is correct and is not disturbed**: `ratchet.rs` has 0 commits in the window, which
establishes freeze on its own. What fails is the **type** of the evidence, in the row that carries the
"quadruple" claim.

**Severity: LOW.** This is the **third firing of v34** on this track (`#675`'s §A.1 published `git log`
commits under a `git rev-parse` blob column; `C346 rev1`'s member 5 published baseline paths that
resolved from no root; this). The lesson is not doc-specific: **a table that mixes two object types
under a permissive header lets a strong claim rest on a weak cell, and a header that permits both types
types neither.** **Route: this ledger** (fixed prospectively — §A above declares the type of every
cell, and the C388 guard requires it).

---

## §D — C308's carries, re-adjudicated at HEAD `afa107f5`

Every probe re-run this pass. **12 rows; 11 HELD unchanged, 1 RE-TYPED by N1, 0 closed.**

**Rev1 — every path in this table is now repo-relative, and every `git log … -- <path>` was re-run
against the rooted path.** As originally written, seven cells named bare basenames or no path at all.
Four of those basenames are **shadowed** by `forum/nova/web4-sal-bundle/`, and — the reason this is a
correction and not a tidy-up — **`git log <range> -- <path-that-matches-nothing>` exits 0 and prints
nothing**, which is byte-identical to the true answer *"0 commits touched it."* Every `→ 0` below was
therefore an output a typo would also have produced. All values survive re-rooting unchanged; see
§F.5 item 2.

| Carry | probe re-run at HEAD (paths repo-relative) | adjudication |
|---|---|---|
| **N1** (flat 8-dim `t3_tensor`) | `git log --oneline 69a5f471..afa107f5 -- web4-standard/core-spec/t3-v3-tensors.md` → **0**; `sed -n '137p'` on that path, verbatim (*"root nodes in an open-ended RDF sub-graph"*) | **STILL-OPEN**, anchor stable a 3rd pass. DESIGN-Q — idle, no self-decision |
| **N2** (no entity-role binding) | same file (`web4-standard/core-spec/t3-v3-tensors.md`), **0** commits | **STILL-OPEN** |
| **C36-N9** (Society MUSTs / birth-cert owner) | `git log --oneline 69a5f471..afa107f5 -- web4-standard/core-spec/SOCIETY_SPECIFICATION.md web4-standard/core-spec/web4-society-authority-law.md` → **0** (C308's cell named both unrooted; `web4-society-authority-law.md` is shadowed by the SAL bundle mirror at blob `040d8e75` vs `0849ebbe`) | **STILL-OPEN** by byte-identity |
| **C36-N11** (entity-segmented LCT IDs) | `git log --oneline 69a5f471..afa107f5 -- web4-standard/core-spec/LCT-linked-context-token.md` → **0** | **STILL-OPEN** |
| **C19-M3** (3 exception classes vs `errors.md`) | `grep -cE "InsufficientRecoveryQuorum\|NoHardwareAnchorError\|DeviceLimitExceeded\|insufficient_recovery_quorum\|no_hardware_anchor\|device_limit_exceeded"` on `web4-standard/core-spec/errors.md` → **0** (both casings, v11's rider); window over that path → **0**. *The mirror `forum/nova/web4-sal-bundle/errors.md` (blob `84e1e834`, 144 L vs 154 L) also returns 0, so the verdict is root-invariant here — but the instrument was not.* | **STILL-OPEN**; adjudicate jointly with C268-N1 |
| **C19-M4** (LCT-core doesn't acknowledge §7.1) | `grep -cie "multi-device" -e "multi_device"` on `web4-standard/core-spec/LCT-linked-context-token.md` → **1** (`:41`, *"(e.g. a multi-device, biometric, richly-witnessed constellation)"*) | **STILL-OPEN, UNCHANGED** |
| **C19-M5** (8 sub-dims absent from ontology) | `grep -cE "hardware_binding_strength\|constellation_coherence\|hardwareBindingStrength\|constellationCoherence"` on `web4-standard/ontology/t3v3-ontology.ttl` → **0**; window over that path → **0** | **STILL-OPEN.** C308 moved this from byte-identity to a live measurement; the live measurement is re-run here rather than inherited |
| **C19-M7** (§7.3 ATP costs free-floating) | `git log --oneline 69a5f471..afa107f5 -- web4-standard/core-spec/atp-adp-cycle.md` → **0**; independently re-confirmed by **C346** two fires ago | **STILL-OPEN, HELD** |
| **B-10 arm** (`cose:ES256` `:257`/`:270`) | both anchors verbatim; **`C336-N2` adjudicated the arm 2026-08-08** | **RE-TYPED — see N1.** No longer *"unconsumed"*: **RECEIVED (by rediscovery), per-locus split now carried by the security ledger.** This file holds 2 of B-10's 8 loci and they are the 2 the prescription is wrong for |
| **C152-1** (B-10 overreach + §2.4 genesis-signer gap) | — | **B-10 half CONSUMED at C336-N2. Genesis-signer half remains unconsumed.** `C336-N3` records this route as having been **lost**; the reception was rediscovery, not delivery |
| **C152-2** (`hub/docs/PAIRED-CHANNELS.md` §8 item 6) | `grep -n "multi-device is later"` on `hub/docs/PAIRED-CHANNELS.md` → **`:425`** verbatim (basename unique in the tree) | **STILL-OPEN**, hub track. Status-check only |
| **C268-N1** (§2.2.4 `:155` + §3.6 exclusion verdict) | target frozen ⇒ byte-identical | **STILL-OPEN, unconsumed.** Adjudicate jointly with C19-M3 |
| **C308-N1 / C308-N2** (two ceiling authorities; `web4-core/src/lct.rs` 0.85 software default) | all 6 mirror-layer blobs frozen (§A) | **STILL-OPEN, unremediated by construction** |

**No row lost a locus. One row (B-10 arm) gained a disposition it had been denied for 32 days.**

---

## §E — Instrument index

**Built by capture, not transcription** — this is `C346 rev1`'s guard 6, written yesterday and applied
here for the first time. Every figure below is pasted from the output of the commands as written.

> **Rev1 — this section was the block on PR #682, and both halves of its warranty were false.** The
> original text warranted that *"scopes, denominators and instrument names were re-derived as their own
> class, and every path token was verified to resolve as written,"* closing **"Not mechanically
> reproducible: none."** In fact one scope cell was a denominator narrower than its own instrument's
> reach, and **eight** cells carried a path that either resolves to two tracked files or names no root
> at all. The method upgrade reached §A and did not reach §E. The whole section has been re-derived
> **by class** — every scope cell against what its instrument actually addresses, and every path token
> against `git ls-tree` — and the class sweep returned three members the block did not name. §F.5.

**Path roots — declared, not assumed.** All paths below are **repo-relative from the repository root**
and each was checked for basename uniqueness with
`git ls-tree -r --name-only afa107f5 | grep "/<basename>$"`. The hazard is specific and it is
enumerated rather than described: **`forum/nova/web4-sal-bundle/` is a tracked mirror that shadows
eight `web4-standard/core-spec/` basenames — `core-protocol.md`, `data-formats.md`, `entity-types.md`,
`errors.md`, `mrh-tensors.md`, `security-framework.md`, `t3-v3-tensors.md`,
`web4-society-authority-law.md` — and every one of the eight is at a *different blob* from its
core-spec sibling.** Four of the eight are named by cells in this document. A bare basename against
that tree is not an imprecision, it is a fork: `sed -n '137p' t3-v3-tensors.md` returns *"root nodes in
an open-ended RDF sub-graph"* under `web4-standard/core-spec/` and `"v3_tensor": {` under the mirror.

| claim | instrument (paths repo-relative) | scope | result |
|---|---|---|---|
| target frozen 49 d | `git log -1 --format=%h -- web4-standard/core-spec/multi-device-lct-binding.md` | 1 file | `a6cbde92`, 2026-06-21 |
| freeze set | `git rev-parse afa107f5:<path>` × **10** (blobs, typed — N3) | 10 files, each rooted in §A | table §A |
| window | `git rev-list --count 69a5f471..afa107f5` | repo | **56** commits |
| core-spec motion | `git diff --name-only 69a5f471..afa107f5 -- web4-standard/core-spec/` | tree | **0** files |
| inbound corpus | `git grep -l "multi-device-lct-binding" afa107f5 -- docs/audits web4-standard/docs/audits` | both audit trees (`web4-standard/docs/audits` exists at base: **2** files) | **31** |
| lineage (inclusive rule) | `git ls-tree -r --name-only afa107f5 -- docs/audits web4-standard/docs/audits \| grep -ci multi-device` — **pinned to the base commit, because the working tree now contains this document** (§F.4) | both trees @ `afa107f5` | **8** ⇒ **23** non-lineage |
| addressee residue | pre-registered verb set `owner\|route\|routed\|carry\|carried\|owed\|addressee\|cross-track` ∩ `multi-device` lines | 23 docs (= 31 − 8) | **12** carry addressee language; **2 rows not held** |
| **C152 reception** | `git grep -c "C152" afa107f5 -- 'docs/audits/*security-framework*'` | **10** docs — the count its own glob addresses, by the header's **inclusive** rule (`git ls-tree -r --name-only afa107f5 docs/audits/ \| grep -c security-framework` → **10**) ***(rev1: published as 9; C109, a remediation, was excluded — the tenth member)*** | **1** file (`C336`, 10 hits). C109 holds **0** `C152` / **0** `multi-device` ⇒ **1 of 10** |
| B-10 reach | `git grep -c "cose:ES256" afa107f5 -- 'web4-standard/**/*.md'` | `web4-standard/**/*.md` | **9** occ / **4** files (`web4-standard/core-spec/LCT-linked-context-token.md` 1, `web4-standard/core-spec/lct-capability-levels.md` 5, `web4-standard/core-spec/multi-device-lct-binding.md` 2, `web4-standard/protocols/web4-lct.md` 1); target holds **2** (`:257`, `:270`) |
| B-10 target token | `grep -rn "cose:EdDSA" web4-standard/` → **0**; `grep -rn "cose:EdDSA" . \| grep -v docs/audits` → **0** ***(rev1: printed without a path argument, so it addressed `.`, not either declared scope; both scopes now carry their own command)*** | `web4-standard/`; repo minus audit trees | **0**; **0** |
| C80 item count | `grep -c "^### N[0-9]"` + the §A flagship | `docs/audits/C80-multi-device-lct-binding-delta-audit-2026-06-21.md` ***(rev1: elided to `C80-…-2026-06-21.md`, a glob matching **3** tracked files — C80, C81, C82)*** | **8 + 1 = 9** |
| C80 disposition | C81 *"Findings applied"* / *"Not applied"* tables, cross-checked against §D | `docs/audits/C81-multi-device-lct-binding-remediation-2026-06-21.md`, 2 tables | **7** applied, **2** live carries, **0** dropped |
| ratchet object type | `git cat-file -t 7b048a78` | 1 object | **commit** (not a blob) |
| ratchet blob at C308's HEAD | `git rev-parse --short 69a5f471:web4-core/src/ratchet.rs` | 1 file | **`806882b1`** |
| C19-M3 | `grep -cE "InsufficientRecoveryQuorum\|NoHardwareAnchorError\|DeviceLimitExceeded\|insufficient_recovery_quorum\|no_hardware_anchor\|device_limit_exceeded"` ***(rev1: printed as the placeholder `"<6 spellings, both casings>"`, which is not a command)*** | `web4-standard/core-spec/errors.md` ***(rev1: bare; shadowed, blob `acda930e` vs mirror `84e1e834`)*** | **0** (mirror also **0** — root-invariant verdict, non-invariant instrument) |
| C19-M5 | `grep -cE "hardware_binding_strength\|constellation_coherence\|hardwareBindingStrength\|constellationCoherence"` | `web4-standard/ontology/t3v3-ontology.ttl` ***(rev1: bare; basename unique but unrooted)*** | **0** |
| C19-M4 | `grep -cie "multi-device" -e "multi_device"` | `web4-standard/core-spec/LCT-linked-context-token.md` ***(rev1: bare; basename unique but unrooted)*** | **1** (`:41`) |
| C152-2 | `grep -n "multi-device is later"` | `hub/docs/PAIRED-CHANNELS.md` (basename unique) | **`:425`** verbatim |
| N1 anchor | `sed -n '137p'` | `web4-standard/core-spec/t3-v3-tensors.md` ***(rev1: bare; shadowed, and the two files return **different lines** — this is the cell that falsified the "none" below)*** | *"root nodes in an open-ended RDF sub-graph"* |
| N1 rediscovery locus | `sed -n '35,36p;44p'` | `web4-standard/core-spec/security-framework.md` ***(rev1: cited bare in §C; shadowed, and both loci differ in the mirror — `:35` "ECDH-P256 (ECDH with P-256…)" vs "ECDH with P-256", `:44` "is SHOULD" vs "is OPTIONAL/SHOULD")*** | the ES256/EdDSA MTI text C336 rediscovered from |

**Not mechanically reproducible: none — *now*.** Every row above is a command, a rooted scope, and its
output. The one row that requires judgement (`addressee residue`) has its verb set pre-registered, so
it is re-runnable. **As published on 2026-08-09 this claim was false**, and the cell that falsified it
was the `N1 anchor`: an instrument whose answer depends on which of two tracked files a bare basename
lands on is reproducible by its author and by nobody else.

---

## §F — Own errors

1. **The freeze set was first derived at 4 artifacts and was wrong by 6.** §A was initially the C308
   quadruple (target, `binding.py`, `binding-vectors.json`, `ratchet.rs`). C308's own findings live in
   a **mirror layer of six further files** (`attestation-envelope.md`, `attestation.py`, `envelope.py`,
   `attestation-vectors.json`, `lct.rs`, `hub.rs` — all ten rooted in §A), and without measuring those, *"C308-N1 stands"*
   would have been an inherited status rather than a measured one — the exact failure C308's own §A.2
   corrected for C19-M5. All ten are published. **v13's corollary: a frozen target obliges you to
   widen the surface, and the first place to widen it is the prior pass's own findings.**
2. **N3 was nearly published as a freeze *discrepancy* rather than a typing defect.** The first read of
   `ratchet.rs` showed blob `806882b1` at HEAD against C308's published `7b048a78` with **0** commits
   in the window — which reads as a contradiction, and briefly looked like a MEDIUM. It is not: the
   published token is a commit. **A mismatch between two identifiers is not evidence until both have
   been typed** — which is v34, and is why the finding is the typing rather than the mismatch. Caught
   by `git cat-file -t`, one command, before any of it was written up.
3. **The lineage enumeration and the chain are not the same set.** The inclusive rule returns 8, and
   the non-C-numbered `…-internal-consistency-2026-05-28.md` is a genuine member — but the header's
   chain is C308's, and **C19 sits under a filename the glob does not match**, so the count and the
   chain disagree by one in each direction. Stated in the header rather than smoothed over.
4. **The lineage count would not hold still, and the post-write re-run is the only reason it is right
   (v33, and this is its fourth firing on this track).** Written as **8** from a working-tree `ls`,
   it returned **9** when every figure was re-run after the document was saved — because the document
   had entered its own scope. Both readings are true of different instants. **The instrument is now
   pinned to `afa107f5`** rather than the value being quietly restored, so the cell states *when* as
   well as *what*. The same hazard does not touch the `31` (measured with `git grep` at the base
   commit from the start) — which is precisely why one cell moved and the other did not: **the row
   that broke was the one whose instrument read the working tree.**
5. **Rev1 (2026-08-10) — §E's warranty was false in both halves, and the two defects are the two
   classes this document cleared on `#681` four hours earlier, recurring inside the document that
   names them.** `#681` carried a standing block against this PR; the findings §A–§D were re-derived
   by the reviewer and stand unchanged. What follows is the class sweep, run per **v35** — *clear the
   class over the whole artifact, not the cell you were shown.* **The sweep returned three members the
   block did not name** (marked ✚).
   1. **Membership rule, applied inclusively to my own lineage and exclusively to the one I charged.**
      The header states the rule and credits `C346 rev1` for it — *every `docs/audits/*multi-device*`
      document, C-numbered or not* — and applies it to this lineage, returning **8** including `C81`,
      a **remediation**. §E's `C152 reception` row then published `scope = 9 docs` while the instrument
      printed beside it addresses **10**, because
      `C109-security-framework-remediation-2026-06-28.md` — a remediation, the same kind of member the
      rule admits as `C81` — was silently dropped. This is `C346 rev1` §F.7 verbatim with the sign
      flipped. **Direction: under-claiming.** C109 holds 0 `C152` and 0 `multi-device`, so the finding
      survives and **strengthens** (1 of 10 > 1 of 9). Corrected in §C-N1, §E, and the Pattern section
      (three occurrences of *nine*).
   2. **Path roots — the warranty's load-bearing half.** §E declared *"Roots: all paths repo-relative"*
      and warranted every token resolves as written; **eight cells named a bare basename or no path at
      all**, across §C, §D and §E. `forum/nova/web4-sal-bundle/` shadows **8** `core-spec/` basenames,
      all at different blobs; this document's cells touch **4** of them
      (`errors.md`, `t3-v3-tensors.md`, `security-framework.md`, ✚ `web4-society-authority-law.md`).
      Two consequences, and the second is why this is a block rather than a note:
      - `sed -n '137p' t3-v3-tensors.md` returns **different lines** under the two roots, so the
        strongest claim in the file (*"Not mechanically reproducible: none"*) was false as written.
      - ✚ **`security-framework.md:35-36`, `:44` is a bare *line cite inside a finding*, not a scope
        cell** — and both loci **differ in text** between the two files (`:44` reads *"is SHOULD for
        bridge scenarios"* in `core-spec/` and *"is OPTIONAL/SHOULD"* in the mirror). The block listed
        four §E scope cells; this one is in N1's body, where the ambiguity touches the evidence for a
        MEDIUM rather than an index row.
   3. ✚ **A denominator in the Headline that names the addition instead of the set.** *"the first
      **sextuple**-frozen one once the C308-N1 mirror layer is included"* — the mirror layer adds
      **6** to C308's **4**, and §A certifies **10**. Same class as item 1 (a published denominator
      narrower than the thing it describes), found only because item 1 sent me through every count
      word in the file. Corrected to **ten-fold**.
   4. ✚ **The `git log -- <bare path>` cells were vacuous, not merely unrooted.** A pathspec that
      matches nothing exits 0 and prints nothing — **identical output to the true answer**. Seven §D
      cells reported `→ 0` through an instrument that would have printed `0` for a misspelling, a
      moved file, or a deleted one. All seven were re-run rooted and **all seven values hold**; the
      defect is that until this rev, nothing in the document could have distinguished the two cases.
      This is `v27`'s shape one layer down: **a green that a broken instrument also emits is not a
      measurement.**
   5. Also corrected, same class, not separately findings: the `C80 item count` scope was elided to
      `C80-…-2026-06-21.md`, a glob matching **3** tracked files (C80, C81, **C82**); `C19-M3`'s
      instrument was printed as the placeholder `"<6 spellings, both casings>"` rather than the six
      spellings (`C346 rev1`'s "named matcher, not reproducible" defect, one rev after adopting the
      guard against it); and `B-10 target token` printed `grep -rn "cose:EdDSA"` with **no path
      argument** beside a scope cell naming two different scopes.

   **What this costs and what it is worth.** No finding moves, no severity moves, no verdict moves —
   every re-rooted and re-derived value came back identical, and the one denominator that moved moved
   in the direction that strengthens the finding. That is the honest report, and it is also the
   uncomfortable one: **a warranty surface can be entirely false while every number under it is
   entirely true.** The failure mode is precise — the method upgrade (`C346 rev1` guard 6) was applied
   where the *findings* live and not where the *warranty* lives, so §A got rooted paths and typed
   columns and §E, written last, inherited the habits of the passes before it. **A pass converts to a
   new method table-by-table, and the last table to convert is the one that certifies the others.**
   → **v39.**

---

## §G — Disposition

**Findings: N1 MEDIUM · N2 LOW · N3 LOW. 3 net-new. 1 routed guard discharged NEGATIVE. ZERO mutation.**

- **C349 = declared NO-OP.** N1's ledger half is discharged **in this document** (§D re-types the B-10
  arm); its operator half now bundles with `C336-N2` and is not an auditor's edit. N2 is the C330
  lineage's instrument. N3 is fixed prospectively by §A's typed column. Do **not** self-fix
  `web4-standard/core-spec/multi-device-lct-binding.md`, `web4-standard/core-spec/security-framework.md`,
  any C308/C330/C336 text, or any carry
  another ledger owns.
- **Delivered outward this fire, not merely routed** (v36 applied to this pass's own output): N2 is
  addressed to the C330/ISP lineage, whose next rotation slot is **ISP ≈ C370**. It is recorded here
  under `C330:262`'s own id so that a sweep from either side joins them — the precise failure
  `C336-N3` diagnoses (*an item is lost when written under the sender's id*). **Re-check at C370.**
- **Rotation** advances +2 → `t3-v3-tensors.md` = **C350**. Next multi-device delta ≈ **C388**.

**Baseline for C388** (blobs unless marked *commit*; all paths repo-relative, and **each basename below
verified unique in the tree** at rev1 —
`git ls-tree -r --name-only afa107f5 | grep -c "/<basename>$"` = **1** for all ten, so none is exposed
to the `forum/nova/web4-sal-bundle/` shadowing described in §E):
target `web4-standard/core-spec/multi-device-lct-binding.md` `b979ea7d` (*commit* `a6cbde92`, 1126 L;
B-10 loci `:257`/`:270`; C268-N1 sites `:155`, `:795-801`; §4.2 ceiling table `:871-887`, closing MUST
`:886-887`); `web4-standard/implementation/sdk/web4/binding.py` `857f8040`;
`web4-standard/test-vectors/binding/binding-vectors.json` `dc969641`; `web4-core/src/ratchet.rs`
`806882b1`; `docs/specs/attestation-envelope.md` `c2f604aa`;
`web4-standard/implementation/sdk/web4/attestation.py` `37a7c673`;
`web4-core/python/web4_core/trust/attestation/envelope.py` `c3046043`;
`web4-standard/test-vectors/attestation/attestation-vectors.json` `fecbc695`; `web4-core/src/lct.rs`
`2e9d4586`; `hub/hub-lib/src/hub.rs` `2431521d`.

**Guards for C388.**
1. **Check whether B-10 was re-typed with its per-locus split** (N1) — in the **security** ledger *and*
   here. A split recorded on one side only reproduces the divergence in the other direction, which is
   C346-N1's exact shape.
2. **Run the inbound set difference BEFORE §A.** It was the entire yield of this pass, of C346 and of
   C344. Pre-register the verb set. Search a routed row by **subject matter as well as by label** — and
   note that `C330:262` routed to this slot **by number**, which is v32's shape: it arrived only
   because this pass grepped for it.
3. **Type every identifier before comparing two of them** (N3, v34, third firing). Publish blobs in a
   blob column and commits in a commit column; never a header that permits both.
4. **Build §E by capture** (C346 rev1 guard 6) — re-derive every scope, denominator, instrument name
   and path root as its own class, and verify every path resolves as written. **And do §E LAST-but-not-
   least: this pass applied the guard to §A and left §E on the old habits, which is what `#682`'s block
   convicted (§F.5, v39).** Concretely, before publishing §E: (a) for every basename in the document,
   run `git ls-tree -r --name-only <base> | grep "/<basename>$"` and root anything with more than one
   hit — `forum/nova/web4-sal-bundle/` shadows **8** `core-spec/` basenames at differing blobs and is
   the standing trap on this target; (b) never publish a `git log … -- <path>` green without confirming
   the pathspec matches a tracked file, because a non-matching pathspec prints the same nothing; (c)
   apply **one** membership rule to your lineage and the lineage you charge, and state it; (d) check
   every count word against the set it names, not the delta that produced it.
5. Check whether C330's instrument was re-typed (N2), and whether C80's accounting is cited when it is.
6. Do **not** re-open: the 9-of-9 C80 accounting (discharged NEGATIVE here); C308-N1/N2's mirror layer
   while its ten blobs are frozen; the `binding` conformance-suite absence (C308 INFO-1, C276
   precedent).

---

## Pattern (C348)

**C346 found a carry that failed by being *received*. This pass found its complement: a carry that
succeeded, and could not tell anyone.**

C152 proved a prescription wrong. The security lineage never cited it — **ten** documents, zero mentions
until yesterday — and then arrived at the same result independently, from the target's own text, 32
days later, and charged it as net-new. Both ledgers were behaving correctly the whole time: this one
re-recorded *unconsumed* against a probe that watches spec files, and that one could not find an item
filed under someone else's id. **The row was not ignored; it was invisible to both instruments at
once.**

And the discharge in §C.2 is the same shape from the other end. C330's instrument asked *whether
anyone cited C80's findings*, and the answer is no — because they stopped being findings and became
**bytes in the standard**, one day after they were written. The 49-day freeze that reads as silence is
the record of the loudest possible reception.

**v38 (new): v37 has a receiving half — an adjudication of your carry does not arrive, and a
freeze-probe on the owner's *spec* cannot detect one that happened in the owner's *ledger*.** When a
row is routed out, its status probe must watch the channel disposition actually travels in: the
receiver's audit documents, not the receiver's files. And when an instrument reports a lineage as
unconsumed, check the **remediation commits** before the citations — consumption that reached the
standard leaves no citation at all.

**v39 (rev1, from this document's own block): a pass converts to a new method table-by-table, and the
last table to convert is the one that certifies the others.** Guard 6 reached §A — typed columns,
rooted paths, ten artifacts measured — and did not reach §E, so the warranty section went out claiming
a discipline the document had genuinely acquired everywhere except in the section making the claim.
Two corollaries with teeth: **a bare basename is a fork, not an imprecision**, wherever a mirror tree
shadows the name (here `forum/nova/web4-sal-bundle/`, 8 shadowed `core-spec/` basenames, all at
different blobs); and **`git log <range> -- <pathspec-that-matches-nothing>` prints exactly what
"0 commits touched it" prints**, so an unrooted freeze green is a green a broken instrument also emits.
Every value in this document survived the re-derivation unchanged — which is the point: the warranty
was false while the numbers were true. → [[feedback_last_table_to_convert]] /
[[feedback_subsumption_is_a_disposition]] /
[[feedback_delivery_is_an_act_of_the_receiver]] / [[feedback_admission_row_is_not_examination]] /
[[feedback_routing_by_slot_is_not_delivery]].
