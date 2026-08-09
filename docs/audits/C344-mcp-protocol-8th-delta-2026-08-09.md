# C344 — `mcp-protocol.md` Eighth Delta Re-Audit (the standard ran a `roleType` → `roleLCT` migration and this is the spec it missed — then documented the miss as a design choice)

**Date**: 2026-08-09
**Target**: `web4-standard/core-spec/mcp-protocol.md`
**Prior pass**: C304 (7th delta, 2026-08-01, PR #628)
**Base**: C304's HEAD `76ff2f52` → this pass's HEAD `79957170`
**Mutation**: **ZERO.** No spec, schema, SDK, vector or sibling file is edited by this pass.

---

## Headline

The target is byte-frozen for 27 days and its window is 2 standard-side commits. Every guard C304
published discharges NEGATIVE. **The pass is not clean.**

`mcp-protocol.md` §7.1 opens *"Every MCP interaction maps to R6:"* and prints an R6 object carrying
all six canonical components in canonical order — `rules`, `role`, `request`, `reference`,
`resource`, `result`. Five of the six use canonical key names. The sixth, `role`, uses **neither** of
the two keys the standard's own R6/R7 grammar requires:

```json
"role": {
  "entity": "lct:web4:client:...",
  "roleType": "web4:Developer"
}
```

Canonical is `{"actor": …, "roleLCT": …}` — and `schemas/r7-action-jsonld.schema.json:87` makes it
`"required": ["actor", "roleLCT"]` under `"additionalProperties": false`, so the target's block is
invalid on **four** counts at once (two missing required keys, two forbidden extra keys).

This is not a novel defect class. It is *the* defect class the standard already prosecuted:
`r7-framework.md` was charged **HIGH** for exactly it (C14 H1, *"four of the five transaction
examples encode the role as a bare type string"*) and remediated in `6d40cc4b` (#234, 2026-05-25);
`dictionary-entities.md` was charged (C17 H2) and remediated in `991a0092` (#242, 2026-05-28).
**`mcp-protocol.md` is the one spec the migration did not reach** — and the C77 remediation later
added a note (`:340-347`) that ratifies `roleType` as *"intentionally distinct"* while saying nothing
about `entity`. r7-framework's examples were merely stale. This spec's are stale **and defended**.

The carry that should have delivered this — `C17-INFO3`, filed 2026-05-27 and routed to "an MCP-side
pass" by **six** dictionary-lineage documents over **74 days** — reached **0 of 9** MCP-side passes.
Reception happens here. And the carry as filed understates the defect: it calls the site *"an
identical stale `roleType` site"*, but the dictionary site had `actor` and only its role-*value* key
was wrong. **The `entity` key has never been named by any audit document in either tree.**

---

## Severity legend

| level | meaning |
|---|---|
| HIGH | a conformant implementation reading the spec is led into a wire-incompatible or unsafe result |
| MEDIUM | a normative statement is unsatisfiable, self-contradictory, or contradicted by the standard's own machine-readable artifacts, with no executable path today |
| LOW | a defect in an in-standard artifact that does not change what a conformant implementation emits |
| INFO | a re-verification, an exclusion re-held, or an instrument note |

---

## §A — Byte-freeze (collapsed: blob identity is stronger than an anchor table)

The policy review struck this pass's proposed 17-row anchor table on the ground that blob identity is
a strictly stronger proof. It is right, and the identity holds three ways:

```
git rev-parse 3e765345:web4-standard/core-spec/mcp-protocol.md  -> 4491c1bb7f603808abfbaa01613e12b36f9c3192
git rev-parse 76ff2f52:web4-standard/core-spec/mcp-protocol.md  -> 4491c1bb7f603808abfbaa01613e12b36f9c3192
git rev-parse HEAD:web4-standard/core-spec/mcp-protocol.md      -> 4491c1bb7f603808abfbaa01613e12b36f9c3192
```

The object C304 resolved its anchors against **is** the object at HEAD. 1020 L, last mover
`3e765345` (2026-07-13, §7.8 insert) ⇒ **27 days frozen, 3rd consecutive frozen delta.**

**A.2 — mechanical extractor, publishing the diff and not the table.** Every distinct `L<num>`
token in C304 (**41**, a superset of the 17 ledger anchors — it includes narrative line references)
was re-resolved against the target by script. **Diff vs C304: empty.** `L787` = `### 8.2 Discovery
via MRH`; `L793` = `  ?server a web4:Service ;`. The reviewer's pre-emption is confirmed: the
baseline's `§8.2 L787` and C304-N4's corrected `L793` are the **heading** and the **triple** — two
consistent anchors, not a contradiction. Do not spend a future pass on it.

**A.3 — the one anchor that can move, because it is external.** C154-N1 points at
`reputation-computation.md` §4. Re-resolved by content: `## 4. Reputation Rules` = **L239**; file
unmoved since `2bc3bafb` (2026-07-18). **STABLE.**

---

## §B — Mirror set re-derived, and the third direction swept

### B.1 — The one tracked mirror that moved, re-verified hardest (v30)

`hub/hub-daemon/src/mcp.rs` is C188's **adjudicated FALSE-mirror exclusion**, re-verified 0/0/0 at
C304. It moved in-window: commit `6f3d610a` → **`b05845bc`** (#630, 2026-08-01), 1027 → **1094 L**
(blob `7974528a`). Under v30 a freeze-check on a file that moved is the one that must be re-run, so
C188's three named predicates were re-run **verbatim**, not inherited:

| C188 predicate | instrument (over `hub/hub-daemon/src/mcp.rs`, both casings) | C304 | C344 |
|---|---|--:|--:|
| §4.1 Web4 Context Header assembly | `grep -c 'web4_context\|web4Context\|sender_lct\|senderLct\|mrh_depth\|mrhDepth\|law_hash\|lawHash\|proof_of_agency\|proofOfAgency\|t3_in_role\|t3InRole'` | 0 | **0** |
| R7 envelope signing | `grep -ci 'r7\|reputation\|outcome_class\|outcomeClass\|propagation_scope\|propagationScope'` | 0 | **0** |
| §7.6/§7.7 code emission | `grep -c 'W4_ERR_\|web4_err\|w4_err'` | 0 | **0** |

Self-declaration intact verbatim at `:6-9` (*"Full MCP wire protocol compliance … is V2"*). The
in-window commit is a build-provenance change. **Exclusion HOLDS on new evidence. Do NOT re-open,
and do NOT re-narrate as contraction** (C304 guard 5).

**C264's standing mailbox guard**, re-run at live HEAD:
`git diff 8c3711c6..HEAD -- hub/hub-lib/src/store.rs hub/hub-daemon/src/rest.rs | grep -c 'mailbox_'`
→ **0**, across 25 in-window `hub/` commits. Core untouched; gate outcome unchanged.

### B.2 — Third direction (v28): what *cites* the target, and what the lineage has ever read

`git grep -l "mcp-protocol" -- . ':!docs/audits' ':!web4-standard/docs/audits'` → **40 files.**
Cross-referencing each basename against the 9 lineage documents:

| | count |
|---|--:|
| tracked files citing `mcp-protocol` (outside both audit trees) | **40** |
| ever named by any of the 9 mcp lineage documents | **7** |
| **never named by any mcp lineage document** | **33** |

The 7 read: `atp-adp-cycle.md`, `errors.md`, `inter-society-protocol.md`, `society-roles.md`,
`mcp.py`, `test_mcp.py`, `test-vectors/mcp/mcp-protocol.json`.

Among the 33 unread are two **`core-spec/` siblings** (`presence-protocol.md`,
`SOCIETY_SPECIFICATION.md`), an in-standard SDK suite explicitly scoped to the target
(`test_mcp_cross_society.py`, whose docstring `:4` reads *"Covers the 6 types added to web4.mcp
implementing mcp-protocol.md §7.3–7.6"*), two `rfcs/`, one `proposals/`, the whitepaper's entire
MCP section, and three archived reference implementations. **Two of the 33 are load-bearing for N1
and one is N3.** This is not a call to read all 33 — it is the measured statement that the lineage's
frame has been the four artifacts that *implement* the target, and the artifacts that *consume* it
were outside it.

---

## §C — Findings

### N1 (MEDIUM, net-new) — §7.1's R6 `role` object is the standard's only role block using neither canonical key

**Locus:** `web4-standard/core-spec/mcp-protocol.md:313-314` (block `:305-337`, §7.1 *MCP Actions as
R6 Transactions*).

**The claim the block makes.** `:301` — *"Every MCP interaction maps to R6:"*. The object that
follows carries all six R6 components, canonically named and in the order of `r6-framework.md`
§1.1–1.6: `rules`, `role`, `request`, `reference`, `resource`, `result`. It is a mapping statement,
not a sketch.

**What the corpus says a `role` block is.** Census of every `"role": {…}` block in the repository
carrying at least one of `actor|entity|roleType|roleLCT`, by **block** (Python parse over 193 files
containing `"role"`; no filetype filter; `*/target/` and `node_modules` excluded). **Measured against
the corpus as it stood before this file was written** — see §F.4, which publishes what the same run
returns afterwards and why:

| key set | blocks | where |
|---|--:|---|
| `actor` + `roleLCT` | **26** | `r6-framework.md:59`, `r7-framework.md:69`/`:672`, `dictionary-entities.md:417`, `schemas/r7-action-jsonld.schema.json:87`, `schema_registry.json:2604`, and **20** vectors in `test-vectors/schema-validation/r7-action-jsonld-validation.json` |
| `roleLCT` alone (inline one-liners) | 15 | `r6-framework.md` ×5, `r7-framework.md` ×4, audit quotes ×6 |
| `roleType` alone | 4 | all four are `docs/audits/r7-framework-internal-consistency-2026-05-24.md` quoting the **pre-remediation** r7-framework |
| `actor` + `roleType` | 2 | `submission/draft-palatov-web4-core-00.txt:567`, `:868` — outward draft, half-migrated |
| **`entity` + `roleType`** | **3** | **`mcp-protocol.md:312`** + `archive/reference-implementations/mcp_trust_binding.py:395` + `mcp_web4_protocol.py:1038` |
| `actor` + `entity` | 1 | `docs/audits/C52-…:107`, an audit quote |

**Within `web4-standard/`, the target is the sole `entity`+`roleType` site.** The other two are
archived implementations **of this very example** — `mcp_trust_binding.py:395` reads
`"role": {"entity": web4_ctx.sender_lct, "roleType": web4_ctx.sender_role}`, a faithful transcription
of §7.1. They are non-normative (archived `65cd5488`, #151, the 2026-04-11 drift cleanup) and are
recorded here as **evidence, not as a defect** — the same disposition C284 gave `ledgers/`. What they
evidence is that this example gets copied.

**The schema settles direction (v12).** `schemas/r7-action-jsonld.schema.json`:

```
role.required            = ["actor", "roleLCT"]
role.additionalProperties = false
role.properties keys      = actor, roleLCT, pairedAt, t3InRole, v3InRole
```

The target's block therefore fails on four counts: `actor` missing, `roleLCT` missing, `entity`
forbidden, `roleType` forbidden. The SDK agrees and is stricter than the schema: `r6.py`
`Role.from_dict` (`:253-259`) does `d["actor"]` and `d["roleLCT"]` as **mandatory** reads —
§7.1's object raises `KeyError: 'actor'`. This is C304-N1's mechanism exactly (*the schema is the
authority and the ledger had the direction reversed*), on a second field of the same section, found
because C304 admitted `schemas/` into the mirror set and this pass re-derived rather than inherited.

**Remediation history proves the direction, so it is not inferred.** The standard ran a
`roleType` → `roleLCT` migration in May 2026:

| spec | charge | severity | remediated |
|---|---|---|---|
| `r7-framework.md` | C14 H1 — *"four of the five transaction examples encode the role as a bare type string"* | **HIGH** | `6d40cc4b` (#234, 2026-05-25) |
| `dictionary-entities.md` | C17 H2 — *"§7.1 R6 example uses stale `roleType` field name … and a non-canonical role value"* | HIGH | `991a0092` (#242, 2026-05-28) |
| **`mcp-protocol.md`** | **C17-INFO3, 2026-05-27** | INFO (as filed) | **never — 74 days** |

**Four refutations attempted; all fail, and one narrows the charge.**

1. *"§7.1 is R6; the schema is R7 — different grammars."* — **Fails.** `r6-framework.md:57-63`'s
   canonical R6 role block is `actor`+`roleLCT`+`pairedAt`+`t3InRole`+`v3InRole`, the **identical**
   key set to the R7 schema's role object. R7 extends R6 with Reputation only — which the target
   itself states at `:372`. The R6/R7 distinction does not reach the role block.
2. *"The C77 note ratifies it."* — **Partially, and not where it matters.** The note (`:340-347`)
   defends `roleType` as *"intentionally distinct"* and is **silent on `entity`**, the key no audit
   has ever named. Its stated rationale — *"the R6 `role` block here uses the abstract role name
   form"* — has no counterpart in `r6-framework.md`, whose R6 role block has no name form at all;
   and its escape clause (*"where an implementation binds to a concrete role LCT it uses
   `roleLCT` instead"*) makes optional a key the schema marks `required`.
3. *"It is an example with elisions."* — **Fails.** The `...` elisions are in **values**
   (`lct:web4:client:...`); the key set is fully specified, and the other five components are
   canonical.
4. *"`web4:Developer` is a placeholder, so the value is not a defect."* — **Granted, and the charge
   is narrowed accordingly.** This finding is about the **key set**, not the value. The
   role-value-canonicity question is C17 H2's DESIGN-Q half, operator-gated since 2026-05-27, and is
   **not** re-argued here.

**Severity: MEDIUM, with the operator's attention drawn to the HIGH precedent.** Bounded down from
C14 H1's HIGH because §7.1 is an integration mapping rather than the canonical Role definition, and
because no harness dereferences the fenced block (C304-N3: the mcp vector suite covers 0 of
§7.1–7.8). Bounded **up** from LOW because the block claims to be *the* R6 mapping, it fails the
standard's own schema and crashes the standard's own SDK loader, and the C77 note actively tells a
reader the divergence is intentional. **Route: operator/author.** Not auditor-applicable — a spec
edit is authoring, and the fix must decide whether to correct the example, withdraw the note, or
ratify `roleType` *in the schema* (only one of the three is cheap).

### N2 (MEDIUM, net-new, process) — 74 days, 9 MCP-side passes, 0 receptions

`C17-INFO3` was filed 2026-05-27 in `dictionary-entities-internal-consistency-2026-05-27.md:478`,
naming `mcp-protocol.md:306` and stating *"warrants a future MCP-spec audit."* It has been re-routed
to this lineage by **six** documents:

| document | date | routing language |
|---|---|---|
| `dictionary-entities-internal-consistency:478` | 2026-05-27 | *"warrants a future MCP-spec audit"* |
| `C52-…:221` | 2026-06-12 | *"Remains carried for an MCP-side pass"* |
| `C94-…:105` | 2026-06-24 | *"For an MCP-side pass"* |
| `C132-…:80` | 2026-07-03 | *"For an MCP-side pass"* |
| `C166-…:183` | 2026-07-09 | *"cross-doc → MCP pass"* |
| `C322-…:269` | 2026-08-06 | *"owned by the mcp lineage"* |

**Reception, measured.** `grep -c 'C17-INFO3'` over all **11** MCP-side audit documents that predate
this pass (the 9 C-series lineage docs plus the two 2026-05-15 pre-C-series docs) → **0, every one**
— re-confirmed post-write, each still 0. The nine passes
that ran *after* the first routing — C35, C76, C116, C117, C148, C188, C226, C264, C304 — collectively
mention `roleType` five times, and all five are carry **B10** (role-identifier *field names*, a
different item that C304 `:128` explicitly distinguishes).

This is the second lineage-pair instance of **C342-N1** (v32: *routing by slot number is not
delivery*), and the first where this track is the **addressee** rather than the reporter. It is also
sharper than C342's: there the carry named its addressee by slot number; here six documents named the
addressee **by lineage, in prose, over 74 days**, and prose addressing is no better. C342-N1 declined
to charge C328 because v28 postdated it; the same test applied here **does** charge this lineage —
every one of the nine passes postdates the first routing.

**No dictionary-lineage pass is culpable.** They filed it, they kept it alive, and C322 restored it
after C282 dropped it. The failure is entirely on the receiving side, and the corrective is
structural, not exhortative: **the delta template needs an inbound step that greps both audit trees
for the target's filename before §A**, because that grep — run for the first time in this lineage's
history, this pass — is what produced N1.

**Route: operator + rotation-wide.** Recorded here as **RECEIVED**; N1 is its discharge.

### N3 (LOW, net-new, SDK) — the standard's own §7.3–7.6 suite is the sole corpus counterexample to §7.1's stated value form

`mcp-protocol.md:344` states *"All three carry the same value form, `web4:<RoleName>`"*, and `:461`
repeats it for `responding_role_expected` (*"in the `web4:<RoleName>` form, per §4.1
`sender_role`"*). Every `sender_role` value in the standard:

| value | site |
|---|---|
| `web4:DataAnalyst` | `mcp-protocol.md:137`, `test-vectors/mcp/mcp-protocol.json:12`, `:27`, `test_integration.py:1394` |
| `web4:Developer` | `submission/draft-palatov-web4-core-00.txt:350`, `test_mcp.py:196` |
| `web4:...` (elided) | `mcp-protocol.md:432` |
| `""` (empty, permitted) | `mcp-protocol.json:41`, `test_mcp_cross_society.py:97` |
| **`Trader`** | **`test_mcp_cross_society.py:114`** |
| **`Diplomat`** | **`test_mcp_cross_society.py:166`** |

`Trader` and `Diplomat` are the **only** non-empty `sender_role` values anywhere in the standard that
omit the `web4:` prefix, and both are in `test_mcp_cross_society.py` — the suite whose own docstring
scopes it to *"mcp-protocol.md §7.3–7.6."*
Nothing catches it: `mcp.py:275`/`:727` type `sender_role` as a bare `str` with no pattern, and the
form is stated in a note and a parenthetical, not as a MUST. **LOW** — no conformant implementation
emits anything different because of it. **Route: SDK track.** The file is one of the 33 never-named
citing artifacts (§B.2).

### N4 (LOW, net-new, instrument → dictionary lineage) — the restoration re-published the pre-correction locus

`C322:269` restores `C17-INFO3` citing **`mcp-protocol.md:306`**. That was correct when C52 wrote it
and stopped being correct on 2026-06-20: **`C94:85` (2026-06-24) explicitly recorded the shift,
*"line shifted 306→314 by the C77 remediation"***, and `C132:44`, `C132:61`, `C132:80` and `C166:183`
all carry `:314`. Live HEAD is **`:314`**.

The restoration reverted its own lineage's correction, silently, two months and three passes after it
was made. The likely mis-resolution is not a miss but a false hit: `:306` at HEAD is
`  "type": "mcp_invocation",` — a real line, inside the same JSON block, eight lines above the
defect. A reader resolving the restored pointer lands on plausible content and finds no `roleType`.

This is v19's shape at the anchor scale: *the pass most likely to degrade a row is the one restoring
it.* C322 did the harder and more valuable thing — it recovered nine rows C282 had dropped — and the
attention that took is what let the anchor regress. **The corrective is narrow: when restoring a
dropped row, restore the ledger's *latest* anchor, not the row's *original* one.** **Route:
dictionary lineage (~C362).** Verdict of C322's restoration is unaffected; the row is correctly
OPEN and correctly owned here.

---

## §D — C304's five guards, and the carry ledger with loci counted

Every cell is a measurement taken this pass. The **loci** column answers C304-N4's carry (count loci
per row, not rows per pass).

| # | C304 guard | measured at HEAD `79957170` | verdict |
|--:|---|---|---|
| 1 | did §7.3 gain `action_id`; was B2+B6's inverted clause executed? | target `action_id\|actionId` = **0**; `mcp.py` unmoved at commit `b6c243c2`, `action_id` intact at `:818`/`:831`/`:852` with `d["action_id"]` a mandatory read | **NOT EXECUTED** — the SDK does **not** fail `r7-action-jsonld.schema.json`. C304-N1's hold worked. |
| 2 | did §4.1 gain required/optional marking or a schema? | `web4-standard/schemas/` = **0 commits** in window; `web4_context\|web4Context\|sender_lct\|senderLct` over `schemas/` + `ontology/` = **0 files** | **UNCHANGED** — C304-N2 stands, zero-yield by construction |
| 3 | did `test-vectors/mcp/mcp-protocol.json` move off `9b002074`? | last commit **`9b002074`** (2026-03-18), 12 vectors | **UNMOVED** — C304-N3 stands |
| 4 | B1+B11's third locus is §8.2 L793, not L737 | `:787` = `### 8.2 Discovery via MRH`; `:793` = `?server a web4:Service ;` | **CORRECT, and consistent with the `L787` baseline** (§A.2) |
| 5 | `mcp_server.py` and `hub/…/mcp.rs` are adjudicated exclusions | `mcp_server.py` unmoved at `759eaefa`; `mcp.rs` moved and re-verified 0/0/0 (§B.1) | **HELD on new evidence** |

| Carry | loci at C226 | loci at C304 | loci at C344 | Status | Route |
|---|--:|--:|--:|---|---|
| **C226-N1** §7.8.2 idempotency-on-redelivery | 1 | 1 | **1** (`§7.8.2`, text frozen) | **STANDS as a defect**; its "new normative obligation" framing remains REFUTED per C304-N1 | operator/author |
| **C188-N1** `ReputationEnvelope` shape | 3 | 3 | **2 + 1 held** (`witness_signatures`, `trust_dimension_updates` stand; `action_id` clause **held**) | unchanged — `mcp.py` byte-frozen | SDK track (B2+B6) |
| **C304-N1** `action_id` direction inversion | — | 1 | **1** | HELD; guard 1 confirms the hold was honoured | operator + SDK |
| **C304-N2** §12 MUST #2 vs §4.1 | — | 3 | **3** (0 schemas / 0 contexts / vector `mcp-ctx-002`) | HELD, unchanged | operator/author |
| **C304-N3** vector suite predates 76% of the spec | — | 1 | **1**, and see §E | HELD, **reach unchanged by the new gate** | operator/author |
| **B1+B11** | 3 | 3 (third corrected to `§8.2 L793`) | **3** | HELD | inherit verbatim |
| **B10** role-identifier field names | 3 | 3 | **3** | HELD — and **N1 is not B10**: B10 is about three *names in three contexts*, N1 is about one block failing the schema's key set. Do not merge them. | operator/author |
| **C154-N1** | 1 | 1 | **1** (`repcomp` §4 = `:239`) | anchor STABLE | closed |
| **C117-N1** | 1 | 1 | **1** (`:958`) | HELD | closed |
| **C148/C188 carries** (B5+B12, N5/N9/N13, N12, N15, F5/C62-B1, F9-inverted, B1-family) | — | — | — | HELD by byte-freeze construction | unchanged |
| **C17-INFO3** | — | — | **1** (`:314`, corrected from the restored `:306`) | **RECEIVED** this pass; discharged by N1 | this ledger |

**No row lost a locus this pass.** One row **gained** the ledger (`C17-INFO3`, 74 days late), and one
locus was **corrected** (`:306` → `:314`, N4).

---

## §E — The highest-information in-window event: a new conformance gate that cannot reach this suite

Of the two in-window `web4-standard/` commits, `8d3808db` (#637, 2026-08-04) is the substantive one:
it adds `web4-standard/test-vectors/validate_context_refs.py` (152 L) plus a CI workflow — a **new
conformance gate over the whole test-vector tree**, born from C310-N3. It is the first new gate over
that tree since C304 filed **N3** (*the mcp suite is frozen at a spec 76% shorter than today's*), so
the question it raises for this target is exact: **does the new gate reach `test-vectors/mcp/`?**

Run at HEAD:

```
$ python3 web4-standard/test-vectors/validate_context_refs.py
  lct.jsonld         OK     (32 refs, 2 files)
  r7-action.jsonld   OK     (20 refs, 1 files)
  t3v3.jsonld        KNOWN  (36 refs, 1 files) — carried: C310-N3
  ALL REFERENCED CONTEXTS BACKED (except 1 carried: t3v3.jsonld)
```

`grep -c '@context' web4-standard/test-vectors/mcp/mcp-protocol.json` → **0.** The gate walks the mcp
suite and finds nothing to check: a **vacuous pass**, not a pass. Independently,
`grep -n 'mcp' web4-standard/test-vectors/schema-validation/validate_schema_vectors.py` → **0** — the
schema-validation runner does not reference the mcp suite either.

**C304-N3's reach is therefore unchanged and slightly worse-evidenced than when filed.** Two
independent gates now run over `test-vectors/`; the mcp suite passes both without either one asserting
anything about it. The gate's own docstring makes the general form of this point — *"the
schema-validation runner cannot see this class of error … a vector can pass schema validation forever
while citing a context that does not exist"* — and the mcp suite sits one level further out: it
carries no JSON-LD envelope for a context gate to check and is not enumerated by the schema gate.
This is an **INFO** re-verification of a standing MEDIUM, not a net-new finding.

*(Recorded because a future pass will otherwise read "a new test-vector gate landed in-window and went
green" as coverage. It is not coverage; the green is silence.)*

---

## §F — Own errors

Published because a pass that reports only its findings is reporting half its instrument.

1. **A bare-filename baseline resolved to the wrong directory.** This track's guard file baselines
   `MCP_ENTITY_SPECIFICATION.md` with **no path**. The first freeze check looked under
   `core-spec/` and returned empty — the file is at `web4-standard/MCP_ENTITY_SPECIFICATION.md`
   (unmoved, commit `f3d2613d`, blob `3917ae17`). No finding was affected; the *instrument* was
   wrong for one step. **A locus written as a bare filename is not a locus.**
2. **Blob read against a commit column.** `git rev-parse HEAD:…/mcp.py` returns **`9fe9fea1`**; the
   baseline says `b6c243c2`. These disagree because the baseline column is **commits**, not blobs —
   `mcp.py`'s last commit *is* `b6c243c2` and the file is unmoved. Caught before publication. Same
   class as the 2026-08-09 00:00 fire's §A.1: **name the object type in the column header, and fix
   values to the declared instrument rather than relabelling the instrument to fit the values.**
3. **The role-block census changed under a cross-tool re-run, and the change was load-bearing
   (v34, third firing in this track).** The first instrument was
   `grep -rn -A3 '"role": {' --include=*.md --include=*.json --include=*.txt --include=*.xml --include=*.jsonld web4-standard/`
   and it returned `entity`+`roleType` = **1**. The re-run — a Python block parse, **no filetype
   filter**, whole repository, counting *blocks* rather than *matching lines* — returned **3**. The
   two new sites are the archived implementations of §7.1, which are precisely the evidence that the
   example gets copied. The first instrument was not merely narrower; it excluded `.py`, which is
   where the corroboration lived. **A filetype filter on a search for "who implements this" excludes
   implementations** (v29, rider 2).
   *Note the two counts are also in different units: the grep line-count over `web4-standard/` is
   **52**, the Python block-count over the repository is **51**. They are not comparable and are not
   presented as agreeing — the block census is the instrument of record.*
4. **The census would not hold still, because writing it changed it (v33, third firing in this
   track).** The post-write re-run of §C N1's table — same tool, same query, run *after* this file
   existed — returns **5** `entity`+`roleType` blocks and **53** total, not 3 and 51. The two new
   sites are **this document**, which quotes the offending block twice (Headline and §C N1). The
   published table is therefore stated **as of the pre-write corpus**, and every count that could be
   contaminated is scoped in words rather than left to the reader: §C N1's census excludes this file,
   and §C N2's *"0 of 11"* means the eleven MCP-side documents that **predate** this pass
   (`C17-INFO3` occurs **7** times in this one). Two counts were re-run post-write and did **not**
   move: the citing-file sweep (**40** — it excludes both audit trees by construction) and the
   `sender_role` census (scoped to `web4-standard/`).
   *An audit that greps the tree it is being written into is part of its own corpus. Publish the
   measurement instant, not only the number.*

---

## §G — Disposition

**Findings: N1 MEDIUM · N2 MEDIUM · N3 LOW · N4 LOW · 1 INFO (§E). 4 net-new. ZERO mutation.**

- **C345 = declared NO-OP.** N1 is operator/author-owned (a spec edit is authoring); N2 is
  operator + rotation-wide; N3 routes to the SDK track; N4 routes to the dictionary lineage.
  Do **not** self-fix `mcp-protocol.md`, `test_mcp_cross_society.py`, or any C322 text.
- **Adjudicate N1 with C17 H2's deferred DESIGN-Q half** (role-value canonicity, operator-gated since
  2026-05-27) — they are the two halves of one question and answering the key set without the value
  form will leave `web4:Developer` unresolved a third time.
- **Rotation** advances +2 → `atp-adp-cycle` = **C346** (last audited C306, PR #629).
  Next mcp delta ≈ **C384**.

**Baseline for the next mcp delta** (all values are **commits** except where marked *blob*):
target `3e765345` (*blob* `4491c1bb`, 1020 L; §7.1 `:305-337` with the role block at `:313-314`,
§7.3 `:370-422`, §7.8 `:708-763`, §8.2 `:787`/`:793`, §12 MUSTs `:947-959`);
`mcp.py` `b6c243c2`; `mcp_server.py` `759eaefa`;
`web4-standard/MCP_ENTITY_SPECIFICATION.md` `f3d2613d` (**path corrected — not `core-spec/`**);
test vectors `9b002074`; `hub/hub-daemon/src/mcp.rs` **`b05845bc`** (*blob* `7974528a`, 1094 L);
`schemas/r7-action-jsonld.schema.json` `766611ef`; `reputation-computation.md` `2bc3bafb`.

**Guards for C384.**
1. **Run the inbound grep FIRST**: `grep -rn "mcp-protocol" docs/audits/ web4-standard/docs/audits/`,
   and read every row addressed to this lineage in prose as well as by slot. This pass's entire yield
   came from that one command, run for the first time in nine passes.
2. Check whether N1 landed — and **if `role` was fixed, check whether the C77 note at `:340-347` was
   withdrawn with it.** A patched example under a note that still ratifies `roleType` is worse than
   either alone.
3. Check whether the outward draft's two half-migrated sites moved
   (`submission/draft-palatov-web4-core-00.txt:567`, `:868`). They are **not** this lineage's — the
   XML/draft artifacts are C340-N1's subject and the handshake lineage's — but a `roleType` fix that
   reaches `core-spec/` and not `submission/` is C336-N1's mechanism a third time.
4. Do **not** re-open: the adjudicated exclusions (`mcp_server.py`, `hub/…/mcp.rs`); C226-N2; the B1
   remediation; the `§8.2 L787`-vs-`L793` pair (§A.2 settles it); C17 H2's role-value DESIGN-Q
   (operator-gated, do not re-argue); the archived implementations as a defect (evidence only).
5. The mirror set for this file **must** include `web4-standard/schemas/` (C304) **and** the
   citation direction (§B.2). Re-derive both; do not inherit either table.

---

## Pattern (C344)

**A standard can complete a migration everywhere except the one place that later documents the
omission as a decision.** The `roleType` → `roleLCT` correction was charged HIGH in `r7-framework.md`,
executed there and in `dictionary-entities.md`, and encoded into
`schemas/r7-action-jsonld.schema.json` as `required` under `additionalProperties: false`. It reached
every artifact that gets validated. It did not reach `mcp-protocol.md` §7.1 — and eight weeks later a
remediation pass, working on a different finding in the same file, added a note explaining that
`roleType` is *"intentionally distinct."* Nothing was concealed and no one was careless; the note is a
reasonable thing to write if you are looking at the three field *names* and not at the schema. But its
effect is that the corpus now contains a prose defence of its own outlier, and the next reader has to
disprove a documented intention rather than notice a stale example.

The delivery failure is the same shape one level up. Six documents across two and a half months
routed this to "an MCP-side pass," and nine MCP-side passes ran without receiving it — not because
any of them was lax, but because none of them ever asked *who is talking to me*. Every instrument
this rotation owns operates on rows already in the ledger: re-resolve the anchor, re-derive the
direction, re-run the grep, count the zeros. All of them presuppose the row arrived.

**v36 (new): before §A, grep both audit trees for the target's own filename and read every row
addressed to this lineage — by slot number, by lineage name, or in prose.** v32 established that
routing by slot number is not delivery. This pass establishes the stronger and less comfortable form:
**routing by any means is not delivery, because delivery is an act of the receiver.** The sender can
only make the row findable. Six senders did, correctly, for 74 days. The one command that would have
found it costs a second and had never been run. → [[feedback_routing_by_slot_is_not_delivery]] /
[[feedback_class_not_cell]] / [[feedback_cross_doc_carry_inbound]] / [[feedback_admission_row_is_not_examination]].
