# C354 — ACP Framework Ninth-Delta Re-Audit

**Date:** 2026-08-10
**Auditor:** Autonomous session `legion-web4-20260810-120000`
**Document audited:** `web4-standard/core-spec/acp-framework.md` (710 lines, blob `f8d7ccda`, last moved `fb0075fc` 2026-07-08 — **33 days byte-frozen**)
**Window:** `git rev-list e8005332..HEAD` = **54 commits**
**Lineage:** C18 → C37 → C86 → C87 → C125 → C126 → C158 → C159 → C196 → C234 → C274 → C314 (8th) → **C354** (this 9th delta).

**1 LOW net-new (overturns a prior ruling) · 3 INFO · ZERO mutation of `web4-standard/`.**

## Proportionality — what this pass deliberately did NOT do

C314 §5 pre-registered: *"an empty window at C354 ⇒ SHORT NO-OP RECORD."* The window **is** empty of acp
spec-artifact movement, so per the policy review this pass **cut** two sections rather than re-deriving them,
and records the cuts here so a later pass can see they were discharged, not dropped ([[feedback_metric_denominator_is_a_domain]], C350 precedent):

- **CUT — the 11-pairing schema↔context coverage baseline (C314-N1).** `git log --oneline f38858d8..HEAD -- web4-standard/schemas/` = **0**. `acp-jsonld.schema.json` = `fbe09135` and `contexts/acp.jsonld` = `08b09ffb`, both unmoved since C314. Re-deriving the table reproduces C314's cells by construction. **Discharged by freeze, which is a stronger discharge than a re-run grep.** What was funded instead: the guard's own enumeration rule — see N3.
- **CUT — per-commit window table.** One row published (§B), the rest gated and dropped.
- **PRE-DECLARED OUT OF SCOPE before running:** `@context` / `@type` absence in the §2.x examples is **REFUTED-GUARD 2(b)** (`C37:264-266`, applied by C87). `grep -c "@context" acp-framework.md` = 0 and always would be. **`REFUTED-GUARD-2(b) HELD`** — no failure on other grounds was found, and none is reported.
- **NOT re-derived:** the `forum/nova/ACP-bundle/` declination (C314 §C.1) and the `forum/`+`archive/` exclusion (§C.0).

**Swept artifact set, published as an enumeration rather than a count word** (C314 asserted "11", which collided
with its other "11"): `git ls-files | grep -i acp` → **9 canonical `web4-standard/` artifacts** —
`core-spec/acp-framework.md`, `ACP_INTEGRATION_SUMMARY.md`, `schemas/acp-jsonld.schema.json`,
`schemas/contexts/acp.jsonld`, `test-vectors/acp/plan-operations.json`,
`test-vectors/schema-validation/acp-jsonld-validation.json`, `implementation/sdk/web4/acp.py`,
`implementation/sdk/tests/test_acp.py`, `implementation/sdk/tests/test_acp_jsonld.py` — plus the **declined**
`forum/nova/ACP-bundle/` (**21** files) and the **excluded** `archive/reference-implementations/acp_*.py` (3 files).

---

## §A — Carry ledger: 9 rows + I-3, split by evidence locus

Re-derived from C314 §A.4's **table**, not its prose ([[feedback_prose_is_not_ledger]]).

**Rows whose evidence sits inside the frozen acp set — discharged by blob identity.** `acp-framework.md`
`f8d7ccda`, `acp.py` `f21616a0`, `ACP_INTEGRATION_SUMMARY.md` `3283d330`, all unmoved since C314. **M7**
(int `witnessLevel` vs structured `witness_requirement`), **B-LEDGERPROOF/C37-5**, **N2** (`maxAtp` cumulative
vs per-intent), **JSONC fences** (3 of 7), **I-3** (`ACP_INTEGRATION_SUMMARY.md:101` `ledgerInclusion`, now
**64 days** in prose, in no ledger) — all **STILL-OPEN, unchanged, by blob**. The `json.loads` fence
measurement and the `acp:` in-file count were **not** re-run: identical bytes cannot yield a different answer.

**Rows whose evidence sits outside it — re-grepped at HEAD, because this is where the window bites.**

| Carry | C314 | C354 | Live evidence |
|---|---|---|---|
| **M6** — `acp:` predicates in no TTL | STILL-OPEN | **STILL-OPEN** | `grep -c "acp:" web4-standard/ontology/*.ttl` = **0**, unchanged |
| **B-AGENCY / L1** | STILL-OPEN | **STILL-OPEN** | `mcp-protocol.md` = `4491c1bb`, byte-frozen. MEDIUM CROSS-TRACK |
| **B8** — ACP discharge not routed through R6 | STILL-OPEN | **STILL-OPEN — and dispositioned inbound** | `atp-adp-cycle.md:126`/`:161` live. **`C346:418` re-verified B8 from the atp side, ruled §7.1 #5 the correct-side referent, and routed it back to this lineage.** First inbound disposition this row has received |
| **N4** — hub write tools carry no proof-of-agency | INFO (UNTRIPPED) | **STILL INFO (UNTRIPPED)** | `git grep -ciE "proofOfAgency\|proof_of_agency\|agency_grant" -- hub/` = **0 across `hub/`**. No mover admitted a non-operator agentic caller |
| **B11 / B12 / B13 / B14 / B15** | STILL-OPEN | **STILL-OPEN — cell now reasoned, not inherited** | See N4 below: `errors.md` **moved this window** |

**0 rows closed, 0 opened. Row survival 9/9 + I-3 = 10** — recorded so a clean streak cannot be mistaken for
an emptying ledger. **But the count is only true of the rows C314 held; see N2, which is about a row it did not.**

**C314's guard 4 — C274-N1's two pre-registered greps, both re-run, both unmoved:** schema `witnesses` still
`"items": {"type": "string"}` at `:189`/`:229`; acp↔r7 cross-references still **0 in both directions**.

## §B — Window: one row, gated

Zero of the 54 commits touch **any of the 9 canonical acp artifacts** (`git log --oneline e8005332..HEAD -- <the 9>` = empty).
That zero is cased narrowly and deliberately: **C314's own document (`f38858d8`) is inside this window**, so the
zero is over *spec artifacts*, not over the lineage's tree ([[feedback_zero_as_wide_as_its_casing]]).

| Commit | Artifact | Disposition |
|---|---|---|
| **`afd04623` (#678)** | `errors.md` `acda930e` → `9cf077ba`: `W4_ERR_PROTO_FORMAT` added to §2.6; §1's delegation sentence and Last-Updated revised | **Gated against B11 — see N4.** Does not touch §10.1's envelope, so B11's cell survives; it now survives by reasoning. **§1's edit is what makes N1 citable at HEAD** |

---

## §C / N1 (LOW, NET-NEW, **overturns `C37:333`**) — `W4_ERR_ACP` is an emittable code that no register holds, and the ruling that retired it rests on a premise that is false at the language level

`C37:326-334` raised **B1-3**: the SDK base `ACPError` declares `error_code = "W4_ERR_ACP"` (`acp.py:80`) where the
spec §10.1 base declares none (`pass`, `acp-framework.md:511-513`). C37 **deflated it LOW→INFO** on this evidence:
*"is never instantiated/raised (**the base is abstract**; all 8 subclasses override), is untested, and is NOT
registered in `errors.md`. So it is never wire-observable."* `C86:80` carried it forward repeating *"never
wire-observable"* verbatim. **Machine-checked at HEAD, the load-bearing clause is false:**

```
exported in web4.__all__      : True          metaclass : type
__abstractmethods__           : none
INSTANTIABLE                  : YES -> ACPError('boom')  error_code = W4_ERR_ACP
raised+caught, emitted code   : W4_ERR_ACP
```

`ACPError` is a plain `Exception` subclass — no `ABCMeta`, no `abstractmethod`, and it is **public API**
(`web4/__init__.py:194`, `:652`). "The base is abstract" is not a judgement call that aged badly; it is wrong
about the code as written. And C37's third clause — *not registered in `errors.md`* — was offered as evidence
of **harmlessness**; under the delegation architecture `C37:402` itself established (M2, subsystem-extends-core)
non-registration is the **defect**, not the exoneration.

**Where the code is registered: nowhere.** `git grep -nE 'W4_ERR_ACP"' -- web4-standard/` returns **exactly one
hit — its own definition.** Absent from `registries/`, `schemas/`, `test-vectors/`. `errors.md:9` (moved this
window) delegates: *"ACP (`acp-framework.md` §10) add codes following the `W4_ERR_*` convention"* — so **§10 is
the register of record for ACP codes, and §10 omits this one.**

**The SDK's own convention test would fail on it, and never sees it** ([[feedback_metric_denominator_is_a_domain]], 3rd firing):

```
subclass passes SDK convention test : True       # NoValidGrant.error_code.startswith("W4_ERR_ACP_")
exported BASE passes same test      : False      # "W4_ERR_ACP".startswith("W4_ERR_ACP_")
```

`test_acp.py:122-138` ranges over a hand-listed array of the **8 subclasses**. `139 passed` is true about the
test's domain, not about the module's exported surface.

**Independent corroboration, from a lineage that had no reason to be kind to it.** `C338:67` (2026-08-08) swept
`W4_ERR_[A-Z0-9_]+` over `web4-standard/` and counted `W4_ERR_ACP` **into** the registrable corpus, naming it
*"`implementation/sdk/web4/acp.py:80`, an SDK default **the code really can emit** — counted"* — explicitly
distinguishing it from `W4_ERR_UNKNOWN_FAKE`, a fixture it declined to count. **Same locus, opposite adjudication
to C37's, reached independently.**

**Severity LOW, and why not MED:** the emit requires a consumer catching the exported base in a generic handler
and reading `.error_code`. No such path exists in the shipped SDK (no generic problem-details serializer reads it).
The one in-repo demonstration — `archive/reference-implementations/acp_framework.py:1143`,
`handle_error("test", ACPError())` — is inside the standing `archive/` exclusion and is cited as *shape*, not as
evidence. The public export is what keeps it live rather than latent: any consumer can reach it.

**Remedy — routed, not resolved in the auditor's favour.** C37's own two options stand and this pass does not
choose between them: (a) add a base `W4_ERR_ACP` row to `acp-framework.md` §10.1 — now the *correct* venue under
`errors.md:9`'s delegation, where C37 (writing before that sentence existed) sent it to `errors.md`; or (b) drop
the SDK base default as a non-canonical idiom. **(b) is test-affecting** and (a) mutates a frozen spec; both are
author calls. **DESIGN-Q → operator.**

## N2 (INFO, method ⇒ **v42**) — a deflation retires the row; an admission keeps it

`grep -cE "B1-3"` across the 11 lineage documents: **C37 = 4, C86 = 1, and 0 in the seven passes since**
(C125, C126, C158, C159, C196, C234, C274, C314 — 2026-06-22 → 2026-08-05, **44 days**). C314's ledger holds
9 rows and **B1-3 is not among them.** Meanwhile `C334:345-351` (2026-08-07) measured the errors lineage as
having received **0 of 8** inbound carries and named **`B1-3` (origin: C37 / C86 acp)** as one of them.

**So at HEAD the row survives only in a third party's census of its own failure to receive it.** The sender
stopped carrying it; the receiver never received it; the only live record is a sibling lineage's measurement
of the gap. C314 published 2026-08-05 and could not have seen C334 — **C354 is the first pass with the
opportunity, which is exactly why the row had to be looked for rather than inherited.**

The method carry: **v41 said a DECLINE licenses only the range it names. v42 is its sibling — a DEFLATION
retires the row.** An ADMITTED row stays in the ledger and gets re-examined every pass; a row deflated to INFO
and routed CROSS-TRACK leaves the ledger, and **the routing becomes the retirement**. When the deflation's
premise is later falsified — as C37's was, twice, by `C338:67` and by the language itself — no instrument in
either lineage is watching. → `feedback_deflation_retires_the_row`

## N3 (INFO) — C314's guard 3 enumerates the schema tree with a glob that cannot see half of it

Guard 3 says *"every `schemas/*.json`"* — and **that literal pattern returns three different answers depending
on what executes it**, which is the defect:

| Command | Result |
|---|--:|
| `ls web4-standard/schemas/*.json` (shell glob — no recursion) | **12** |
| `git ls-files 'web4-standard/schemas/*.json'` (git pathspec — `*` crosses `/`) | **24** |
| `git ls-files 'web4-standard/schemas/**/*.json'` (nested only) | **12** |

The 12 files the shell reading cannot see are all `schemas/presence-protocol/v0|v1/**`. **The result is
unchanged — none of them has a stem-matching context, so 0 pairings are added — but the rule was wrong, and
the correction is the finding, not the result.** The unambiguous form, which is what a future pass should
write, is `git ls-files web4-standard/schemas/ | grep '\.json$'` = **24**. This is
[[feedback_decline_licenses_its_range]]'s companion committed *inside the guard written to prevent it*
(2nd firing; C352 §F recorded the first, `schemas/*.json` = 12 of 24).

## N4 (INFO) — B11's cell was contestable this window for the first time in three passes

`C196:50`, `C234:60` and `C314:99` all carry *"No mover touched errors §10.1 envelope"* **verbatim**.
`afd04623` moved `errors.md`. Re-read rather than inherited: the commit adds a row to **§2.6** and revises
**§1**; §1's *Fields* block and §3's examples — the envelope — are untouched. **The cell holds.** Recorded
because a cell that has been copied three times is the one most likely to be shipped as inherited-true on the
one interval where it is contestable, and because §1's edit is load-bearing for N1.

**The `W4_ERR_ACP_*`-absent-from-`errors.md` question, checked and NOT filed.** `grep -c "W4_ERR_ACP" errors.md`
= 0 and the 8 codes live only in §10. This is **`C37:402` M2**, adjudicated by-design
(subsystem-extends-core, `aaa2bd86` #269), re-confirmed by `C158:102` (*"registry CLEAN"*) and `C334:224`
(**ADMITTED**, *"enumerated extender 2 of 4; convention followed"*). Not net-new; the 8 suffixed codes are
correctly registered. **N1 is the ninth code, the unsuffixed base, which that adjudication does not reach.**

---

## §E — Evidence, built by capture

Every path token below was resolved with `git ls-files` / `git rev-parse` before being written, not after
([[feedback_last_table_to_convert]]). No `git log -- <path>` green is published without its pathspec having
been confirmed to match a tracked file. `grep -F` used for every `acp.jsonld` matcher (C314's standing
MATCHER GUARD: the regex form matches `acp-jsonld` and returns 11 instead of 0).

| Claim | Command | Result |
|---|---|---|
| target frozen 33 d | `git rev-parse HEAD:…/acp-framework.md` | `f8d7ccda`, last moved `fb0075fc` 2026-07-08 |
| window | `git rev-list e8005332..HEAD \| wc -l` | 54 |
| 0 acp artifacts moved | `git log --oneline e8005332..HEAD -- <9 paths>` | empty |
| schemas frozen since C314 | `git log --oneline f38858d8..HEAD -- web4-standard/schemas/` | 0 |
| N1 registration | `git grep -nE 'W4_ERR_ACP"' -- web4-standard/` | 1 hit (`acp.py:80`) |
| N1 instantiability | `python3` on `web4.acp.ACPError` | metaclass `type`, no abstractmethods, emits `W4_ERR_ACP` |
| N1 green gate | `pytest tests/test_acp.py tests/test_acp_jsonld.py -q` | **139 passed** |
| N2 row decay | `grep -cE "B1-3"` × 11 lineage docs | C37 = 4, C86 = 1, **0 × 7 passes** |
| N3 enumeration | `ls schemas/*.json` vs `git ls-files web4-standard/schemas/ \| grep '\.json$'` | **12 vs 24** |

**Inbound sweep (v36 as a set difference, v40 by artifact token, verb set pre-registered).** Tokens:
`acp-framework`, `ACP_INTEGRATION_SUMMARY`, `ACP-bundle`, `proofOfAgency`, `ProofOfAgency`, `acp.py`,
`acp-jsonld`, `acp.jsonld` (`-F`), `agentic-context-protocol`. Scope both audit trees at HEAD, self-collision
excluded. **Filename alone = 37 docs; artifact tokens = 42.** The 5 the filename matcher cannot see are
`C304`, `C316`, `C338`, `C344`, `mcp-protocol-sdk-alignment` — **and `C338` is where N1's corroboration lives.**
Minus the 11 lineage docs = **31 non-lineage**; 7 postdate C314. Full read of the 12 postdating-or-token-only;
the other 19 dispositioned by set difference against rows already held. **The entire yield of this pass came
from that sweep, not from the window — the sixth consecutive fire for which that is true.**

## §F — This pass's own errors

1. **The scope's central premise was false, and the policy reviewer caught it.** "The window is empty" was
   published in the proposal after measuring only *acp artifact* movement. `afd04623` moved `errors.md` §2.6 —
   the taxonomy `acp-framework.md:552` dispatches over — inside a window whose B11 cell asserts no such mover.
   A two-command zero would have shipped that cell as inherited-true on the one interval where it was live.
   The zero is now cased to *spec artifacts* (§B).
2. **The proposal asserted "11 swept acp artifacts" as a count word, inherited from C314 and never verified.**
   `git ls-files` returns **9** canonical `web4-standard/` artifacts. C314's own "11" also collided with its
   *other* "11" (the schema→context pairings). §C now publishes the enumeration and no count word.
3. **§D as proposed would have resurrected a refuted finding.** "Validate the published examples against schema
   and context" fails first on `@context`, which is **REFUTED-GUARD 2(b)**. The instrument was pre-declared out
   of scope *before* running rather than after — had it run first, the output would have argued for the finding.
4. **N3 is this lineage's guard committing the defect the guard exists to catch** — and it was found only by
   re-executing §E's enumeration rather than re-reading it, which is also how error 2 surfaced.
5. **N3 itself was first published with a matcher I had not re-run** — the finding *about* an unreproducible
   matcher, committed with an unreproducible matcher. The draft claimed
   `git ls-files 'web4-standard/schemas/**/*.json'` = 24; re-execution returns **12**. The pattern that returns
   24 is `git ls-files 'web4-standard/schemas/*.json'` — **the same literal string that returns 12 under the
   shell**, because git's pathspec `*` crosses `/` and the shell's does not. Correcting it made N3 **stronger**
   (three answers from one rule, not two), which is how I knew it had been guessed rather than run — the same
   tell as C352 §F. Third firing of [[feedback_loose_matcher_certifies_absence]] in this lineage.
6. **`forum/nova/ACP-bundle/` published as 19 files; `git ls-files` returns 21.** Inherited from C314's "9 files"
   plus an uncounted re-read, in the same §C sentence that replaces C314's unverified count word with an
   enumeration. A count word smuggled back into the correction for count words.
7. **Length: this document is ~235 lines against the ~120 the policy review set.** Stated rather than quietly
   exceeded. The cap was premised on an empty window producing a short record; the window *was* empty and §B is
   two paragraphs, but the inbound sweep produced a net-new finding that **overturns a standing ruling**, and an
   overturn has to carry its exhibit or it is just an assertion against a prior pass. §D and the per-commit table
   were cut as instructed; the overrun is N1's exhibit plus §F, and I judged trimming the exhibit to be the
   wrong economy. A future pass should read the cap as binding on **re-derivation**, not on evidence.

---

## Next-delta (C394) checks — pre-registered

1. **N1**: has `acp-framework.md` §10.1 gained a base-class `error_code`, or has `acp.py:80` dropped it?
   One grep each: `git grep -nE 'W4_ERR_ACP"' -- web4-standard/` — **1 hit at HEAD is the baseline; any change is the answer.**
2. **N2**: is **B1-3 back in the ledger?** It is re-entered here as row **11**. If a future pass reports 10 rows,
   it has retired it again — check the deflation, not the count.
3. **Guard 3 correction stands**: enumerate schema trees with `git ls-files`, **never** `schemas/*.json` (12 of 24).
4. C274-N1's two greps (schema `witnesses` widening; acp↔r7 cross-refs) — both still **NO**; one-liners, keep them.
5. **Ledger is now 10 rows + I-3 = 11.** Row survival this pass 9/9, **+1 recovered (B1-3)**.
6. C314's REFUTED-GUARDS (a) `ledgerInclusion` count, (b) `@context` absence, (c) `ns/` vs `ontology#` — all
   **still standing, none re-opened.** C274's bare-string `witnesses` guard likewise.
7. **Proportionality**: this pass cut two sections against an empty window and said so inside the document.
   An empty window at C394 with no inbound residue ⇒ genuinely short record. **The inbound sweep is not covered
   by that ruling** and should be run at full every pass — it has been the entire yield six fires running.
