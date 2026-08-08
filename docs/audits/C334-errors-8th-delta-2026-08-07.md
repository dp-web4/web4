# C334 — `errors.md` Eighth Delta Re-Audit (9th pass)

**Date**: 2026-08-07
**Target**: `web4-standard/core-spec/errors.md` — 154 L, blob `acda930e`, byte-frozen at `6189432d` (C67, 2026-06-17) — **51 days**
**HEAD**: `c32a83c0`
**Prior pass**: `docs/audits/C294-errors-7th-delta-2026-07-30.md` (`e464e540`)
**Snapshot anchor**: `6f3d610a` (C294's) → HEAD = **51 commits**
**Lineage (9 docs incl. this one)**: C30 → C66 → **C67 (remediation)** → C106 → C138 → C178 → C216 → C254 → C294 → **C334**

---

## Headline

**The spec that declares itself the single source of truth for protocol error codes is missing a
code that a sibling spec `MUST` abort with — and the item saying so has been addressed to this file
by name, in ten sibling audit documents, for fifty days, and named in zero of this lineage's eight
passes.**

`web4-handshake.md` §6.0.7 `:164` — *"endpoints **MUST** abort with `W4_ERR_PROTO_FORMAT` (Problem
Details)"*. `grep -cF W4_ERR_PROTO_FORMAT web4-standard/core-spec/errors.md` = **0**. The same
document's §10 is titled *"Error Handling (Problem Details, RFC 9457)"* and emits a conformant
example on a §2 code, so it is a **declared conformer** to this taxonomy; and it is **not** one of
§1's four enumerated extenders, so §1's extension grant does not reach it.

The lineage has been carrying this code since C66 — as **B-2**, *"codes `initial-registries.md` adds
that §2 does not have."* The registries lineage inverted that reading on **2026-06-18** (C70 A-2:
*"an initial lead read of 'registry-only' was **WRONG**"*) and routed the fix here by name — **"Owner:
`errors.md` (on its own delta cycle)"**. Eight passes carried the code with the direction pointing
the wrong way.

**Zero mutation this fire** (7th consecutive delta with no proposed change to the target's bytes;
N1's remediation is routed to the next remediation turn, not applied here).

| | |
|---|---|
| Net-new | **2** — N1 (MED, direction inversion), N2 (MED, process/rotation) |
| Reach-escalation on standing carries | **2** — N3 on B-4/B-5, N4 on C294-N1 |
| Carried rows re-verified | **17 of 17 present; 0 dropped; 0 resolved into a defect; 0 regressed** |
| Inbound item retired by refutation | **1** — `C16-H1-remainder`, routed to this slot by C326 |
| Target bytes changed | **0** |

---

## Scope & Methodology

Standing C-series protocol: §A prior-finding verification, §B corpus delta, §B′ mirror-set
re-derivation, §C fresh internal-consistency (refute-by-default). Both audit trees searched
(`docs/audits/` = 211 docs; `web4-standard/docs/audits/` = 2 docs, **neither an errors doc** — the
zero is published, per v17).

### Pre-registered window and matchers (written before the sweep, per v26)

| Parameter | Fixed value |
|---|---|
| Corpus window | `6f3d610a..HEAD` (C294's snapshot anchor → `c32a83c0`) |
| Recursion root | repo root; all `git grep` run from it, `-F` for any token containing `.` or `-` |
| Trees searched | `docs/audits/` **and** `web4-standard/docs/audits/` |
| Target span | whole file, 154 L |
| Mirror-set criterion | C294's, verbatim: *any `web4-standard/` document that defines a failure-code registry, or assigns a failure result by MUST* |
| Net-new vs reach rule | v16 — **CLASS change = reach-escalation; DIRECTION inversion = net-new**. Fixed before any candidate was scored. |

**A date filter is not a snapshot anchor.** The first count taken this fire was
`git log --since=2026-07-29 | wc -l` = **75**. The anchored count is **51**
(`--since=2026-07-30` = 54; `e464e540..HEAD` = 46). The reviewer caught it; both were re-run before
the correction was accepted. **51** is used throughout.

---

## §A — Prior-Finding Verification

### A.1 — Freeze: **HELD, exact**

| Cell | C294 recorded | This fire | |
|---|---|---|---|
| last-touch commit | `6189432d` | `6189432d` | ✔ |
| blob | `acda930e` | `acda930ec906ab4a9b9c1a021633e722c123de6c` | ✔ |
| lines | 154 | 154 | ✔ |

The 3 AUTONOMOUS C67 fixes (**B-3**, **B-6**, **B-7**) are covered by the freeze and re-read in the
live file: §1 L9 carries the four-home split with mcp named separately as lowercase `web4_*`; §5 is
titled "Status Code Semantics" with the transport-agnostic lead; §5 L146/L147 mirror §2.4's split.
**All HELD.**

### A.2 — The certification chain has a gap, and it is a NEGATIVE

Every pass from C106 onward verifies *"the 3 AUTONOMOUS **C67** fixes, HELD by byte-freeze."* The
**C30/C31** remediation set — **A-M1, A-M2, A-M3, A-L1, I1** — has no row in any pass from C106 on:

| ID | C30 | C66 | C106 | C138 | C178 | C216 | C254 | C294 |
|---|---|---|---|---|---|---|---|---|
| A-M1 / A-M2 / A-M3 / A-L1 | 4 | 1–7 | **0** | **0** | **0** | **0** | **0** | **0** |
| I1 | 3 | 4 | **0** | **0** | **0** | **0** | 1 | **0** |

The blanket disposition ("byte-frozen since C67") is anchored at **the commit that edited §1 and §5**
— the sections A-M2 / A-M3 / A-L1 live in. A freeze anchored at an edit cannot certify what preceded
the edit. **Discharged by reading `git show 6189432d`:** the diff is +7/−5 and touches exactly three
spans — the `Last-Updated` line, the §1 L9 *intro* paragraph, and §5's title + two bullets. The §1
**Fields** block (L28–L35), where A-M2/A-M3/A-L1 landed, and §3's examples (A-M1) are **untouched**.
All five re-read HELD in the live file. **NEGATIVE — published because the gap in the argument was
real even though the answer is clean.**

### A.3 — Ledger row set: **17 of 17 present** (v19 / v24)

Reconstructed from the lineage's oldest full ledger (C30's Classification Summary, 11 rows) plus
C66's (9 rows) and traced by `grep -coF` per id per doc. Membership, not just row count:

| ID | C30 | C66 | C106 | C138 | C178 | C216 | C254 | C294 |
|---|---|---|---|---|---|---|---|---|
| B-1 | 0 | 5 | 13 | 13 | 3 | 5 | 3 | 3 |
| B-2 | 0 | 5 | 7 | 7 | 2 | 3 | 3 | 5 |
| B-3 | 0 | 5 | 4 | 5 | 2 | 2 | 2 | 1 |
| B-4 | 0 | 5 | 4 | 3 | 8 | 6 | 6 | 2 |
| B-5 | 0 | 8 | 4 | 6 | 14 | 9 | 9 | 11 |
| B-6 | 0 | 6 | 2 | 2 | 2 | 2 | 2 | 1 |
| B-7 | 0 | 5 | 2 | 2 | 2 | 2 | 2 | 1 |
| B-8 | 0 | 5 | 6 | 8 | 4 | 3 | 2 | 10 |
| B-9 | 0 | 5 | 3 | 3 | 2 | 2 | 2 | 6 |
| B-H1 | 7 | 4 | 11 | 4 | 2 | 2 | 2 | 6 |
| B-M1 | 9 | 9 | 3 | 3 | 2 | 2 | 2 | 3 |
| B-M2 | 6 | 2 | 3 | 3 | 2 | 2 | 2 | 3 |
| B-M3 | 9 | 2 | 3 | 4 | 2 | 2 | 2 | 3 |
| I2 | 4 | 2 | 3 | 3 | 2 | 2 | 2 | 3 |
| I3 | 2 | 2 | 3 | 3 | 2 | 2 | 2 | 2 |
| C16-H1 | 0 | 0 | 2 | 3 | 2 | 3 | 2 | 2 |
| B-D1 | 0 | 0 | 5 | 4 | 2 | 2 | 2 | 9 |

**No row lost its id. No disposition lost its members.** The C326 disease (a row keeping its count
and its disposition while shedding every id it covered) is **absent from this lineage.** Published as
a NEGATIVE because v19/v24 are satisfied by any disposition and any unchanged count — the check is
membership, and membership was measured individually with `grep -coF`.

### A.4 — The four named re-measurements: all reproduce **exactly**

Re-derived by parsing the live artifacts, not transcribed. Instrument:
`/tmp/c334/xvalidate.py` (not committed — a throwaway measurement script, per the no-new-tooling
constraint); every number below is reproducible from the greps named in each row.

| Carry | C294's value | This fire | |
|---|---|---|---|
| **B-H1** numeric registry orphan | 0 shared identifiers; 11 numeric rows vs 24 §2 codes | **0 shared; 11 vs 24** | ✔ exact |
| **B-2** `initial-registries.md` divergence | 7 codes absent from §2 | **7**, same 7 names | ✔ exact |
| **B-9** vector coverage | 5 of 24; 0 cross-society | **5 of 24 (21%); 0 cross-society** | ✔ exact |
| **B-5** SDK ↔ mcp §7.6 statuses | 3 of 6 diverge | **3 of 6 diverge**, 3 agree | ✔ exact |
| vectors, machine-validated | 0 mismatches | **0 mismatches** across 5 vectors × 2 sources (§2 and SDK) | ✔ re-run, not re-derived |

B-5 in full, re-executed rather than read:

| §7.6 failure mode | mcp §7.6 | SDK `errors.py` | |
|---|---|---|---|
| `exchange_invalid` | 409 | **400** | DIVERGE |
| `law_conflict` | 409 | 409 | agree |
| `unrecognized_lct` | 403 | **404** | DIVERGE |
| `witness_required` | **412** | **403** | DIVERGE |
| `propagation_scope_unsupported` | 400 | 400 | agree |
| `r7_reputation_invalid` | 400 | 400 | agree |

Identifier form: mcp uses lowercase `web4_*` on all 13 of its rows; the SDK uses `W4_ERR_*` on all
6 → **6 of 6 identifier-form divergences**, as C66 recorded.

### A.5 — Carry status at live HEAD

**B-1, B-2, B-4, B-5, B-8, B-9, B-H1, B-M1, B-M2, B-M3, I2, I3, C16-H1, B-D1, C178-N1, C294-N1,
C294-N2 — all STAND.** No host file in the carry set moved in the window (§B). **B-3, B-6, B-7 —
remediated at C67, HELD.** **0 carries resolved into a defect; 0 regressed.**

---

## §B — Corpus Delta (`6f3d610a..HEAD`, 51 commits)

### B.1 — The governing risk condition, stated first

```
git log --oneline 6f3d610a..HEAD -- \
  web4-standard/core-spec/errors.md web4-standard/core-spec/mcp-protocol.md \
  web4-standard/core-spec/presence-protocol.md web4-standard/core-spec/did-web4-method.md \
  web4-standard/core-spec/web4-society-authority-law.md web4-standard/core-spec/acp-framework.md \
  web4-standard/protocols/web4-metering.md web4-standard/protocols/web4-handshake.md \
  web4-standard/registries/ web4-standard/test-vectors/errors/ \
  web4-standard/implementation/sdk/web4/errors.py web4-standard/schemas/presence-protocol/
→ 0 commits
```

**Frozen target, frozen mirrors, zero movement.** This is the exact v13 condition under which a
false clean is most likely, and it is why this pass spends its budget on §B′ rather than on §B. It
is reported as a risk condition, not as a clean bill.

### B.2 — What did move

| Tree | Files touched | Bearing on errors |
|---|---|---|
| `hub/` | 89 | dominant mover, 2nd consecutive errors delta — gated at §B′.1 |
| `docs/` | 31 | audit docs + design decisions — mined at §B′.4 (this is where the yield was) |
| `whitepaper/` | 10 | none |
| `web4-standard/` | 4 files: `docs/FRACTAL_ROLE_IDENTITY.md`, `rfcs/RFC-COMPOSITE-ENTITY-IDENTITY.md`, `rfcs/RFC-SHARED-POLICY-SUBSTRATE.md`, `test-vectors/validate_context_refs.py` | the last is the only *executable* one — gated at §B′.3 |
| `web4-trust-core/` 2, `web4-core/` 1, `.github/` 1, `forum/` 1 | | `web4-core` unchanged w.r.t. `error.rs` |

---

## §B′ — Mirror-Set Re-Derivation

C294 left a behaviour-phrased criterion and an instruction: **"Re-derive it, do not transcribe it."**
Re-derived here from the criterion, in **both** citation directions (v14/v20), then every member of
C294's ten-member enumeration given a published disposition — **NEGATIVEs included**, so no member is
shed silently (v8).

### B′.0 — The derivation, both directions

**Inbound** (`git grep -lF "core-spec/errors.md"`, 25 files; 18 are audit docs):
`web4-standard/README.md`, `registries/error-codes.md`, `test-vectors/errors/error-taxonomy.json`,
`implementation/sdk/web4/errors.py`, `docs/how/manus_instructions_v2_post_review.md`,
`archive/reference-implementations/web4_error_handler.py`.
Bare `errors.md` adds `core-spec/r7-framework.md`, `INTEGRATION_STATUS.md`, `whitepaper/PUBLISHER_CONTEXT.md`, `docs/history/STATUS-2026-02.md`, two `forum/nova/` reviews.

**Outbound / by criterion** — `git grep -lF "W4_ERR_"` over `web4-standard` (15 files) plus a
heading sweep `^#+.*(error code|error registry|failure mode|errors?)` over `web4-standard/**/*.md`
(14 files) plus the lowercase `web4_*` family (1 file).

### B′.1 — Member-by-member disposition

| # | Member | In C294's set? | M1 | M2 | M3 | Disposition this fire |
|---|---|---|---|---|---|---|
| 1 | `core-spec/errors.md` §2 | ✔ | — | — | — | **the target** |
| 2 | `core-spec/web4-society-authority-law.md` §9 | ✔ | PASS | GENUINE | ADMITTED | 8 codes, 3 novel; **enumerated extender 1 of 4** → see N4 |
| 3 | `core-spec/acp-framework.md` §10 | ✔ | PASS | GENUINE | ADMITTED | 8 codes, all `W4_ERR_ACP_*`-prefixed; **enumerated extender 2 of 4**; convention followed |
| 4 | `protocols/web4-metering.md` §6 | ✔ | PASS | GENUINE | ADMITTED | 6 codes, 6 novel; **enumerated extender 3 of 4**; §1's SHOULD violated — see N1(b) |
| 5 | `core-spec/mcp-protocol.md` §7.6 + §7.7.7 | ✔ | PASS | GENUINE | ADMITTED | 13 lowercase rows; **enumerated extender 4 of 4**; B-5 STANDS |
| 6 | `core-spec/presence-protocol.md` §6.1 | ✔ | PASS | GENUINE | ADMITTED | 10 `hestia.*` codes; **not** enumerated → C294-N1, reach-escalated at N4′ |
| 7 | `core-spec/did-web4-method.md` §5.1 | ✔ | PASS | GENUINE | ADMITTED | `notFound` by MUST; **not** enumerated → C294-N1, unchanged |
| 8 | `registries/error-codes.md` | ✔ | PASS | — | ADMITTED | B-H1 re-measured: **0 shared identifiers**, orphan total |
| 9 | `registries/initial-registries.md` | ✔ | PASS | — | ADMITTED | B-2 re-measured: **7** §2-absent; direction re-derived → **N1** |
| 10 | `test-vectors/errors/error-taxonomy.json` | ✔ | PASS | — | ADMITTED | re-validated, **0 mismatches**, 5 of 24 |
| **11** | **`protocols/web4-handshake.md` §6.0.7 + §10** | **ABSENT** | **PASS** | **GENUINE** | **ADMITTED** | **ADDITION → the flagship, N1** |
| **12** | **`implementation/sdk/tests/test_errors.py`** | **ABSENT** | **PASS** | — | **ADMITTED** | **ADDITION → N3** (the gate is a mirror: it *asserts* the taxonomy) |
| **13** | **`schemas/presence-protocol/v0/common/error_envelope.schema.json`** | **ABSENT** | **PASS** | GENUINE | ADMITTED | **ADDITION → N4′** (the machine encoding of member 6) |
| **14** | **`core-spec/r7-framework.md` §7** | **ABSENT** | **PASS** | GENUINE | ADMITTED | **ADDITION**; charge already owned by `C48-DQ-errors` → folded into **N2** |
| 15 | `implementation/sdk/web4/errors.py` | (in C294's §A table) | PASS | GENUINE | ADMITTED | X1: **24 of 24 core codes match §2 exactly** — title, status and description, 0 mismatches |
| 16 | `implementation/sdk/web4/acp.py` | ABSENT | PASS | GENUINE | ADMITTED | ADDITION; 9 codes; supplies N3's convention baseline |
| 17 | `web4-core/src/error.rs` | (C178-N1) | PASS | **FALSE** | — | NEGATIVE re-confirmed: 13 internal variants, `git grep -c W4_ERR web4-core/` = **0** |

**The set grew from 10 to 17. It did not contract.** Six additions, each argued above.

### B′.2 — `hub/`: the M3 re-open trigger, discharged **NEGATIVE**

C294's trigger is phrased as a behaviour: *"a hub artifact starts claiming errors.md/RFC-9457
conformance, OR errors.md gains language binding society-server implementations."* Measured over
`hub/` excluding `hub/target/`, at `c32a83c0`:

| Token (`git grep -lF`) | Files |
|---|---|
| `errors.md` | **0** |
| `RFC 9457` | **0** |
| `rfc9457` | **0** |
| `problem+json` | **0** |
| `W4_ERR` | **0** |

Second limb: `errors.md` is byte-frozen, so it gained no language at all. **Trigger un-fired on both
limbs. `hub/` stays M3-DECLINED, admitted as evidence only.** Not re-litigated — and worth stating
that the interval's 89 hub file-touches include a new `LawError` module (#661/#662) that would have
been the natural place for such a claim to appear, and it does not.

### B′.3 — `validate_context_refs.py`: NEGATIVE with its scope published

The only executable `web4-standard/` file to move in the window. It walks
`test-vectors/**/*.json` and checks that every `@context` URI of the form
`https://web4.io/contexts/<name>.jsonld` has a backing file. `error-taxonomy.json` carries **no
`@context`**, so the gate is a structural no-op over the errors vectors. **No coverage gained, none
lost.** Recorded so the next pass does not mistake a moving validator for a moving gate.

### B′.4 — The inbound-carry sweep (the pass's yield)

Neither citation direction finds work *addressed to* this file. That is a third direction, and it
had never been run in this lineage. Instrument: `git grep -nE "errors\.md"` over **both** audit
trees, minus the errors lineage's own eight docs, filtered to lines carrying an ownership word
(`owner|route|routed|cross-track|add .* to .* errors`). Results are the **reception matrix** in §C.

---

## §C — Findings

### C334-N1 (MED, **NET-NEW** by direction inversion) — the SSOT does not contain a code a sibling spec `MUST` abort with, and the item saying so was addressed here by name and never received

**(a) The defect, at live HEAD.**

| Cell | Measurement |
|---|---|
| `web4-handshake.md` §6.0.7 `:164` | *"If the received signature profile doesn't match the negotiated `media`/`ext`, endpoints **MUST** abort with `W4_ERR_PROTO_FORMAT` (Problem Details)."* |
| `grep -cF W4_ERR_PROTO_FORMAT web4-standard/core-spec/errors.md` | **0** |
| `errors.md` §1 L33 | `code` **(REQUIRED in Web4)** … "carrying the error code **from the §2 taxonomy**" |
| `errors.md` §2.6 contents | `PROTO_VERSION`, `PROTO_SEQUENCE`, `PROTO_REPLAY`, `PROTO_DOWNGRADE` — no format-mismatch code |
| Is handshake an enumerated extender? | **No.** §1 enumerates SAL §9, ACP §10, metering §6, mcp §7.6. `grep -ciE handshake errors.md` = **1**, and that one hit is the words "Pairing handshake timed out" inside a §2.2 description cell. |
| Is handshake a declared conformer? | **Yes.** §10 is titled *"Error Handling (Problem Details, RFC 9457)"* and emits a conformant example on `W4_ERR_AUTHZ_DENIED`. |

A document that declares conformance to this taxonomy, is not granted extension rights by it, and
`MUST`-emits a code it does not define. The MUST is unsatisfiable in conformant form.

**(b) The refutation that narrowed it.** The inbound carry (C70 B-C1) bundles **two** codes:
`W4_ERR_PROTO_FORMAT` and `W4_ERR_WITNESS_REQUIRED`. Measured against §1's extension grant, they do
not behave alike. `W4_ERR_WITNESS_REQUIRED` is emitted only by `web4-metering.md:109` — and metering
§6 **is** enumerated extender 3 of 4, so §1 *authorizes* it to mint domain-specific codes. **That
half is not an SSOT gap and this pass withdraws it as one.** What survives against metering is the
weaker, separate charge that §1's *"SHOULD reuse the codes defined here … rather than introducing
parallel names"* is violated — and `initial-registries.md:56` documents the violation in its own
description column: `W4_ERR_RATE_LIMIT - Rate limit exceeded (same as W4_ERR_AUTHZ_RATE)`. That is
C70's **B-C2**, also never received. **N1 is `W4_ERR_PROTO_FORMAT`, alone.** The bundle was wrong
and the correction belongs to this seat, since errors.md is the named owner.

**(c) The direction inversion — why this is net-new and not B-2 restated.** The errors lineage has
held these codes since C66 under **B-2**, framed as *codes `initial-registries.md` **adds** that §2
does not have* — i.e. the registry over-defines. C294 re-measured B-2 that same way ("7 codes in
`initial-registries.md` absent from errors.md"). C70 §A-2, **2026-06-18**, corrected the reading in
terms:

> *"**CORRECTION / escalation** … an initial lead read of 'registry-only' was **WRONG**: these two
> codes are **not registry-only**. They are emitted by **live sibling specs** … So the file that
> claims to be 'the single source of truth for core protocol error codes' is **missing** two codes
> its own subsystem specs MUST/do emit. This is a genuine SSOT-completeness gap, not a mere mirror
> over-definition."*

Under the pre-registered rule (v16), a **class** change routes as reach-escalation and a **direction**
inversion routes as net-new. The arrow reverses — the defendant changes from `initial-registries.md`
to `errors.md`. **Net-new.**

**(d) Reception.** `grep -coF` per id, per doc, both trees:

| Inbound id | Origin | Sibling docs carrying it | Errors-lineage passes naming it |
|---|---|---|---|
| **B-C1** (add the codes to §2.3/§2.6) | C70, 2026-06-18 | **10** — C70, C72, C110, C112, C142, C182, C220, C258, C298, C300 | **0 of 8** |
| **B-C2** (`RATE_LIMIT` → `AUTHZ_RATE`) | C70 | 7 | **0 of 8** |
| **B-C3** (three competing "format" names) | C70 | 7 | **0 of 8** |
| `C16-H1-remainder` | C16/C58 | 6 | **6 of 8** (C106, C138, C178, C216, C254, C294) |

Ten sibling documents, every one naming `errors.md` as owner, six of them re-confirming B-C1 STILL
OPEN on consecutive registries deltas — the most recent **seven days ago** (C298). C70 wrote the
routing explicitly: *"Owner: `errors.md` (on its own delta cycle, C66/C67)."*

**Routing**: **AUTONOMOUS-ready** for the next errors remediation turn — one row in §2.6. Status:
C70 suggested `400`, which is §5-compatible and consistent with the other three §2.6 codes.
(C70's companion suggestion of **428** for `WITNESS_REQUIRED` is now moot under (b); noting for the
record that **428 is not among §5's eight classes**, so it would have required a §5 row too.)
This pass proposes no edit and applies none.

### C334-N2 (MED, **NET-NEW**, process → the rotation, not to `errors.md`) — the lineage's inbound reception is selective, and the selection is legible

The lineage is not blind to inbound carries: it received `C16-H1-remainder` on **6 of 8** passes. It
received **0 of 8** for every item originating in the registries, handshake, r6 and acp lineages:

| Unreceived | Origin | Content |
|---|---|---|
| B-C1 / B-C2 / B-C3 | C70 registries | above |
| `C48-DQ-errors` | C48 r6-framework | §7's `R6Error` Python-class model has no link to the `W4_ERR_*` / RFC-9457 taxonomy |
| `B1-3` | C37 / C86 acp | SDK base `ACPError` `error_code="W4_ERR_ACP"` — unregistered, absent from errors.md |

The mechanism is measurable. **C106 names `C71` — the registries *remediation commit* — thirteen
times, and names `C70`, the registries *audit document*, zero times.** C138 does the same (C71 ×4,
C70 ×0). The lineage watched the sibling's **commits** and never read the sibling's **audit doc**,
which is where routing lives. A carry routed to you lands in *someone else's* document; nothing in
either citation direction, and nothing in a corpus-delta commit sweep, will surface it.

This also disposes of a candidate this pass raised independently and then found already owned:
`r7-framework.md` §7 defines an error-result JSON shape whose `type` member holds a Python class name
(`"ResourceInsufficient"`) where errors.md §1 defines `type` as a URI defaulting to `about:blank`.
That is `C48-DQ-errors` at a sibling section — **an unreceived inbound, not a discovery.**

**Routing**: to the rotation method, not to a spec. Concretely: *add an inbound-carry sweep to the
standing per-delta method* — grep both audit trees for lines naming the target file alongside an
ownership word, minus the target's own lineage, before §A. Severity MED because the loss compounds:
B-C1 is fifty days old and has been re-confirmed six times by a lineage that cannot fix it.

### C334-N3 (LOW, **reach-escalation on B-4 + B-5**, class change — *not* net-new) — the SDK's own gate asserts the divergent value, so the standing remediation is test-breaking

`python3 -m pytest tests/test_errors.py -q` → **50 passed**. Inside that green suite:

| Test | Asserts | Against |
|---|---|---|
| `test_cross_society_unrecognized_lct` | `meta.status == 404` | mcp §7.6 says **403** (B-5) |
| `test_exactly_30_codes` | `len(ErrorCode) == 30` | §2 defines **24** (B-4) |
| `test_exactly_7_categories` | `len(ErrorCategory) == 7` | §2 defines **6** (B-4) |
| `test_codes_per_category` | `CROSS_SOCIETY: 6` | §2 defines the category **not at all** |
| `test_all_codes_have_valid_status` | `100 <= status <= 599` | §1's *range*, never §5's **8 semantic classes** — which is why 404 and 412 pass |

`grep -rn "core-spec"` over `implementation/sdk/tests/` → **2 files**, neither of them
`test_errors.py`. **No test in the suite dereferences `errors.md` or `mcp-protocol.md`.** The
module docstring claims *"Canonical implementation per web4-standard/core-spec/errors.md"*; the
canonicity claim has never been testable, and the gate that is green instead **pins** the three
divergent facts. Aligning the SDK to mcp §7.6 breaks three assertions. Seven passes have routed B-5
as *"align statuses per code (single-owner decision)"* without stating that cost.

**A concrete remediation target, which is what the class change buys.** The SDK already has a
convention and follows it once: `web4/acp.py` holds ACP §10's 8 codes plus its base. Per-module
`W4_ERR_` counts across `web4/*.py`: **`acp.py` 9, `errors.py` 30, everything else 0** — and
`web4/mcp.py` **exists** and holds none. `errors.py` is the single place where an extender's codes
were absorbed into the core-taxonomy module, up-cased out of their source's namespace, and
mis-transcribed on 3 of 6 statuses. Moving the six `CROSS_SOCIETY` codes to `mcp.py`, on the
`acp.py` precedent, discharges **B-4** (docstring 30/7 → 24/6), **B-5** (the codes leave the module
that mis-transcribed them) and **B-9** (cross-society vectors stop being owed by the *errors* vector
file) in one change.

**Routing**: CROSS-TRACK (SDK), folded onto B-4/B-5. **Explicitly recorded as reach-escalation, not
net-new**, under the pre-registered v16 rule: the locus (`errors.py` ↔ mcp §7.6) is B-5's, and what
changed is the *class* of claim about it — the gate is protective rather than merely absent. This
was the pass's most quotable cell and the rule demotes it; the rule was fixed first.

### C334-N4 (INFO→answer) — `C16-H1-remainder`, routed to this slot by C326, is **REFUTED as a defect against `errors.md`**

C326 (2026-08-06) routed this here by name — *"`C16-H1-remainder` routes to the `errors.md` slot
(C334) with no severity assigned here"* — flagging it as a still-true **HIGH** tracked by nothing.
Verified at live HEAD first:

| Code | `errors.md` | `errors.py` | SAL §9 | `initial-registries.md` |
|---|---|---|---|---|
| `W4_ERR_LEDGER_WRITE` | 0 | 0 | 1 (`:331`) | 0 |
| `W4_ERR_AUDIT_EVIDENCE` | 0 | 0 | 1 (`:332`) | 0 |
| `W4_ERR_LAW_CONFLICT` | 0 | 0 | 1 (`:333`) | 0 |

The measurements are all true. **The charge is not.** §1 grants subsystem specifications the right
to *"extend this taxonomy with additional domain-specific codes"* and names **SAL §9 as extender 1
of 4**. Three SAL-domain codes living in SAL §9 and not in §2 is the mechanism working, not failing.
Absence from `errors.md` is **authorized**, and the same reasoning that withdraws the
`WITNESS_REQUIRED` half of N1(b) withdraws this. It is exactly the distinction
[[feedback_absence_is_not_prohibition]] exists for: §1 **omits** these codes; it does not **require**
them.

**What survives, and it is smaller:** the codes are absent from **`errors.py`**, which absorbed
extender 4's six codes (mcp §7.6) while absorbing **0 of SAL's 3** and **0 of ACP's 8** — measured in
N3. That is an SDK inconsistency against the SDK's own `acp.py` convention, not an `errors.md`
defect. **Severity from this seat: LOW, CROSS-TRACK (SDK), folded into N3.** A HIGH that nothing was
tracking is retired, on the merits, at the slot it was routed to.

### C334-N4′ (reach-escalation on **C294-N1**) — the presence envelope makes RFC-9457 conformance schema-*invalid*, not merely absent

C294 folded `presence-protocol.md` §6.1 into N1 on the ground that it *"assigns no statuses at all."*
Its machine encoding — `schemas/presence-protocol/v0/common/error_envelope.schema.json`, read by
**5 presence-lineage passes and 0 errors passes** — is stronger than that:

```
required: ["code", "message"]        additionalProperties: false
code pattern: ^hestia\.[a-z_]+$      title: ABSENT   status: ABSENT
```

`additionalProperties: false` means a `_hestia_error` object carrying errors.md §1's REQUIRED `title`
and `status` **fails schema validation**. The incompatibility is machine-enforced, not editorial. All
10 §6.1 codes match the schema's own pattern (0 violations) — the schema and its spec agree with each
other perfectly; both disagree with errors.md §1's *"all protocol errors"* MUST. And §6.1 carries
`hestia.vault_not_found`, `hestia.action_not_found` and `hestia.internal_error` — **precisely the two
classes C294-N1 says §2 cannot express**, in a core-spec document, in machine-checkable form.

No new severity. **C294-N1's basis strengthens from "said five incompatible ways" to "one of those
ways is enforced by a published schema that forbids the conformant form."** Routes with N1 to the
operator; do **not** re-raise separately.

### Considered and dismissed (anti-padding transparency)

- **"§1's three remaining extender claims are false."** The C67 remediation asserted that SAL §9,
  ACP §10 and metering §6 *"add codes following the `W4_ERR_*` convention"* while only *verifying*
  the mcp clause it was fixing — the classic remediation-born-false shape (v15). **Measured: all
  three true.** SAL §9 = 8 `W4_ERR_*`, ACP §10 = 8 `W4_ERR_ACP_*`, metering §6 = 6 `W4_ERR_*`.
  Dropped.
- **"`errors.md` §5 omits a status used in §2."** §2 uses exactly {400,401,403,408,409,410,429,503};
  §5 lists exactly those 8. Re-confirmed (C66 refuted the same candidate; re-run, not transcribed).
- **"`initial-registries.md` is the union of §2 and metering §6."** Suggestive — 5 of its 7
  §2-absent codes are metering §6's verbatim, a 6th is metering's `W4_ERR_FORMAT` renamed to
  `W4_ERR_PROTO_FORMAT`, and it carries a literal `### Metering Errors` subsection while absorbing
  **0 of SAL's 3** and **0 of ACP's 8**. Dropped as a *causal* claim: both files were born in the
  same commit (`18209449`, 2025-09-11), so there is no promotion to observe. The set structure is
  reported under N1 as context, not charged.
- **`W4_ERR_BAD_TIMESTAMP`** — the one §2-absent registry code belonging to none of the three
  enumerated extenders. Emitted by nothing in `web4-standard/`. Registry-only; no MUST behind it;
  correctly inside B-2 and not escalated.
- **The Rust `error.rs` false-mirror boundary** — re-applied, unchanged, `web4-core/` had 1
  file-touch in the window and not to `error.rs`.

---

## Own errors caught before shipping

1. **A `\w+` regex reported 30 unique `W4_ERR_` tokens in `errors.md`; the true count is 24.** Six
   were §2.x heading prefixes (`W4_ERR_BINDING_` from `### 2.1 Binding Errors (W4_ERR_BINDING_*)`) —
   `\w` stops at `*`. The set arithmetic that used it is unaffected (the six prefixes appear in no
   other artifact), but the published cell was wrong and is corrected here rather than quietly
   dropped.
2. **The window was first measured with a date filter, not the snapshot anchor** — 75 vs the correct
   51. Caught at policy review; both re-run before the correction was accepted (§Scope).
3. **`web4-handshake.md:160` is the anchor every inbound doc cites; the MUST is at `:164`** at live
   HEAD. Content identical. Re-resolved by content, not by line (v11/v22); N1 cites `:164` and
   records that ten sibling docs carry the stale anchor. (C142, 2026-07-05, had already re-resolved
   it to `:164` — the later registries passes reverted to the C70 anchor.)
4. **An instrument cell in the table below was published at the wrong scope and corrected after the
   post-write re-run**: `git grep -nF W4_ERR_PROTO_FORMAT` returns **5** lines when `docs/audits/`
   is excluded and **29** repo-wide. The finding is unaffected — `errors.md` is 0 at every scope —
   but "5 sites" without its exclusion was a measurement, not a fact.

## Instruments, re-run after writing at a different scope (v17)

| Claim | Instrument | Re-run |
|---|---|---|
| `W4_ERR_PROTO_FORMAT` absent from the SSOT | `grep -cF` on the file | **0** ✔ ; `git grep -nF` excluding `docs/audits/` = **5 lines in 3 files** (`web4-handshake.md:164`, `initial-registries.md:52`, and 3 lines in one archived reference impl), none in `errors.md` ✔ — **repo-wide the same grep returns 29 lines**, the other 24 being audit-doc prose, which is exactly why the scope is published with the number |
| B-C1 named in 0 errors passes | `grep -coF B-C1` × 8 | **0 × 8** ✔ ; widened to `B-C[123]` = **0 × 8** ✔ |
| hub M3 trigger un-fired | 5 × `git grep -lF` over `hub` minus `hub/target/` | **0 × 5** ✔ ; re-run over whole repo minus `docs/audits` — `problem+json` = 0 files ✔ |
| SDK gate green | `pytest tests/test_errors.py -q` | **50 passed** ✔ |
| the 3 SAL codes absent from `errors.py` | `grep -coF` × 3 | **0 × 3** ✔ ; re-run `grep -rl` over the whole `sdk/` tree = no files ✔ |
| ledger row set intact | `grep -coF` × 17 ids × 8 docs | 136 cells, **0 zeros in the C294 column** ✔ |

Row count published, per v23: **§C carries 5 numbered items** (N1, N2, N3, N4, N4′) and **5**
considered-and-dismissed entries. The disposition table in §B′.1 carries **17 rows**, one per mirror
member, and the output that produced it had 17 lines.

---

## Classification Summary

| ID | Sev | Class | Finding | Routing |
|---|---|---|---|---|
| **C334-N1** | MED | **NET-NEW** (direction inversion) | `W4_ERR_PROTO_FORMAT` is a `MUST`-abort in `web4-handshake.md` §6.0.7 and absent from the §2 taxonomy `code` is REQUIRED to come from; handshake is a declared Problem-Details conformer and not an enumerated extender | **AUTONOMOUS-ready** — one row in §2.6 at the next remediation turn (status `400`) |
| **C334-N2** | MED | **NET-NEW** (process) | inbound carries addressed to `errors.md` by name are received 0 of 8 times from four sibling lineages, while received 6 of 8 from a fifth; the lineage tracked sibling *commits*, never sibling *audit docs* | **method** → add an inbound-carry sweep to the standing per-delta protocol |
| **C334-N3** | LOW | reach-escalation on **B-4 + B-5** | the SDK's own 50-test green gate *asserts* status 404 and the 30/7 counts, so B-4/B-5 remediation is test-breaking; concrete target: move the 6 cross-society codes to the empty `web4/mcp.py` on the `acp.py` precedent | CROSS-TRACK (SDK) |
| **C334-N4** | LOW | **refutation** of an inbound HIGH | `C16-H1-remainder` is **not** an `errors.md` defect — SAL §9 is enumerated extender 1 of 4 and §1 authorizes it; survives only as an `errors.py` inconsistency | answers C326's routing; folds into N3 |
| **C334-N4′** | — | reach-escalation on **C294-N1** | `error_envelope.schema.json` `additionalProperties: false` makes the RFC-9457 conformant form **schema-invalid**, not merely absent | rides C294-N1 to the operator |

**Totals**: 0 HIGH, 2 MED (both net-new), 2 LOW, 1 basis-strengthening. **1 inbound HIGH retired by
refutation.** **0 bytes of the target changed or proposed changed this fire.**

---

## Key Adjudication

1. **A third citation direction exists, and it had never been run.** Method carries v14 and v20
   fixed the outbound and inbound *citation* directions — what the spec points at, and who points at
   the spec. Neither finds work **addressed to** the spec, because a carry routed to you lives in
   someone else's ledger and cites you in prose, not in a path. Ten sibling documents named
   `errors.md` as the owner of B-C1; a `git grep -lF "core-spec/errors.md"` returns **six**
   non-audit files and not one of those ten. The whole yield of this pass came from a sweep no
   guard required.

2. **The refutation pass removed more than it kept, and that is the result.** Four of the five
   candidate "SSOT is missing a code" charges died on §1's own extension grant — three SAL codes
   (retiring an inbound HIGH) and one metering code (halving the inbound carry this pass was
   receiving). What survived is the single case where the emitting document has no extension right:
   a `MUST`, in a document whose error section is titled for RFC 9457. **A carry can be right about
   its facts and wrong about its defendant**, and a receiving seat that only forwards never finds
   that out.

3. **The gate is a mirror.** `test_errors.py` was in neither citation direction and in no prior
   mirror set, yet it is the artifact that decides what the SDK is allowed to say. It asserts 404
   where the cited source says 403. C332 established that a green suite proves only what it
   compares; this pass adds the sharper case — **a green suite can assert the divergence itself**,
   converting a "single-owner decision" into a test-breaking change without anyone recording the
   cost.

---

## Next-Turn Carry — fresh ledger for **C374**

**Deferral row (v25) — discharge each of these with a row, including the NEGATIVEs:**

| # | Item | What C374 must do |
|---|---|---|
| 1 | **Re-run the inbound-carry sweep** (§B′.4) | It found this pass's entire yield. Re-run it *first*; B-C1's reception should now be 1 of 9. If N1 was remediated, confirm `W4_ERR_PROTO_FORMAT` is in §2.6 **and** that `initial-registries.md`, `errors.py`, `test_errors.py` and the vector file agree with the row that was added. |
| 2 | **B-C2 and B-C3 are still 0-of-9 received** | This pass named them and did not charge them (N1 was narrowed to one code deliberately). Discharge each with a row: B-C2 = `W4_ERR_RATE_LIMIT` vs `W4_ERR_AUTHZ_RATE`, self-annotated at `initial-registries.md:56`; B-C3 = `W4_ERR_FORMAT` / `W4_ERR_PROTO_FORMAT` / `W4_ERR_CRYPTO_*`. **This is the one left behind on purpose.** |
| 3 | **The `mcp.py` relocation (N3)** | If the SDK moved the 6 cross-society codes, B-4/B-5/B-9 all change state together — verify as one set, and re-run `pytest tests/test_errors.py`. If it did not move, report the negative with the per-module `W4_ERR_` counts re-measured. |
| 4 | **`C16-H1-remainder` is REFUTED against `errors.md`** | Do **not** re-raise it as an errors.md defect. If a future SAL delta re-routes it here, answer with N4 rather than re-deriving. Its surviving `errors.py` half rides N3. |
| 5 | **hub M3 trigger** | Re-run the 5-token NEGATIVE. It has now been un-fired twice. The trigger is a behaviour, not a path — re-read it before measuring. |

**Standing carries, all STAND at `c32a83c0`:** B-1, B-2, B-4, B-5, B-8, B-9, B-H1, B-M1, B-M2, B-M3,
I2, I3, C16-H1, B-D1, C178-N1, C294-N1 (+N4′), C294-N2. **B-3/B-6/B-7 remediated at C67, HELD.**
**Inbound and unreceived:** B-C1 (now received, → N1), B-C2, B-C3, C48-DQ-errors, B1-3.

**Operator bundle (unchanged, do not self-apply):** B-1 (`AUTHZ_DENIED` 401→403 across 5 mirrors),
B-H1/B-D1 (numeric registry canonicity / SSOT inversion), B-M1 (centralised vs distributed error
ownership), B-M3 (W4IDp form), C294-N1 (+N4′: no *not-found* / *internal-failure* class, now with a
schema that forbids the conformant form), C294-N2 (no non-terminal class for proposal #580).

**C335 = NO-OP on the spec side** — this pass proposes no `errors.md` edit. N1 is AUTONOMOUS-ready
and should be applied at the next remediation turn that opens for this file, not manufactured into
one.

**Freeze to re-verify first at C374:** `6189432d` / blob `acda930e` / 154 L — *unless* N1 lands, in
which case re-anchor to the remediation commit and re-verify the C67 **and** C30/C31 fix sets against
it (§A.2's gap, which this pass discharged by reading the diff rather than trusting the anchor).
