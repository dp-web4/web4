# C304 — `mcp-protocol.md` Seventh Delta Re-Audit (the ledger carried `action_id` for three passes with the direction reversed)

**Date**: 2026-08-01
**Auditor**: autonomous web4 session (legion, slot `060032`, C-series)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` (1020 lines, 16 sections; blob `4491c1bb`)
**Instrument**: byte-freeze confirmation → §A live-HEAD re-resolution of **every** anchor the ledger holds (method carry v11) → §B mirror-set re-derivation against what the lineage has *ever* enumerated (v8), including the standard's own machine-readable artifacts (C288/C302) → §B′ negative gate with paths and both casings published (v9, C302) → §C carry-row survival census (v10).
**Scope**: §A delta re-verification of **C264** (6th delta) + its lineage (C226, C188, C154-N1); §B corpus-delta since C264 (2026-07-24, `8c3711c6`) + mirror re-derivation; disposition of standing carries **C226-N1** (MEDIUM) and **C188-N1** (LOW/SDK).
**This audit RECOMMENDS ONLY — no spec/SDK/hub/test-vector mutation this turn.** Two new files (this doc + session log).

**Lineage**: C35 (2026-06-06, #279) → C76 (#365) → C77 (`f3d2613d`, remediated 8) → C116 (#406) → C117 (`afab0c43`, applied N1) → C148 (CLEAN) → C188 (`91225131`, applied C154-N1, SDK PARTIAL) → C226 (`d1cd70e1`, §7.8 net-new, N1 MEDIUM routed) → C264 (0 net-new, re-frozen) → **C304** (this audit).

---

## Headline

1. **The target is byte-frozen for a second consecutive delta — 19 days, blob `4491c1bb`, 0 commits since `3e765345` (2026-07-13).** §A is confirmatory by construction. **All four net-new findings are in the instrument and the mirror layer; none is a new reading of the frozen bytes.**

2. **N1 (HIGH, net-new — a *direction inversion* on a carried row, not more reach on it).** `action_id` has sat in the **B2+B6** bundle since C188 as an SDK **"extra field"**, under C188's explicit ruling *"direction = spec CORRECT, SDK diverges/lags"*, repeated verbatim by C226 (*"extra `action_id`"*) and carried by C264. **The direction is backwards.** `action_id` is REQUIRED by the standard's own `r7-action-jsonld.schema.json` (`additionalProperties: false`), carried **9×** by the canonical sibling `r7-framework.md`, mandatory in the SDK (`mcp.py:818`, no default; `from_dict` does `d["action_id"]`), and constructed by a third implementation (`hub/hub-daemon/src/rest.rs:3483`). `mcp-protocol.md` has **0** occurrences in either casing. The diverging party is **the spec**. Executing B2+B6's `action_id` clause as filed would delete from the SDK a field the standard's own schema requires.

3. **N1 also reclassifies C226-N1, this lineage's standing MEDIUM.** C226 routed the §7.8.2 idempotency gap to the operator on the express ground that keying the remedy on `action_id` would be *"a **new** normative obligation, NOT auditor-applicable"*, and C264 restated it. It is not new law: `action_id` is already REQUIRED in the standard's schema layer and already carried by the canonical R7 sibling. **C226-N1 STANDS as a defect, but its "new obligation" characterization is refuted** — the operator is being asked to ratify less than two passes have told them.

4. **The evidence was in a file the audit programme has never read.** `r7-action-jsonld.schema.json` is cited by **1 of 195** audit docs in the corpus (a dictionary-entities audit from May) and by **0 of 7** mcp passes. C264 tracked the narrowest mirror set in the lineage.

5. **N2 (MEDIUM), N3 (MEDIUM), N4 (LOW)** — §4.1's field set is normative-by-example with no schema and no optionality marking, while §12 MUST #2 requires it; the standard's own conformance suite for this spec is frozen at a 578-line spec that is now 1020 lines and exercises none of §7; and the B1+B11 ledger row silently lost its third locus two passes before C226 computed a completeness claim from the degraded row.

6. **C188's FALSE-mirror exclusion on `hub/hub-daemon/src/mcp.rs` RE-VERIFIED and HOLDS** after 2 in-window commits — all three named predicates measure **0**. **C305 = declared NO-OP.** Rotation advances +2 → `atp-adp` = **C306**.

---

## Severity legend

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR a normative value/structure is rejected by the canonical taxonomy/SSOT. |
| **MEDIUM** | Normative guidance self-contradicts / under-specifies enough that two good-faith implementations diverge. |
| **LOW** | Maintainability / precision / SDK-lag hazard; recoverable by a careful reader; not a blocking contradiction. |
| **INFO** | Observation; recorded for completeness or to confirm a seam was inspected and found bounded. |

---

## §A — Byte-freeze + full anchor re-resolution

**Freeze.** `git rev-parse HEAD:…/mcp-protocol.md` = `4491c1bb7f603808abfbaa01613e12b36f9c3192` = `git rev-parse 3e765345:…/mcp-protocol.md`. `git log 3e765345..HEAD -- …/mcp-protocol.md` → empty. Last mover `3e765345` (2026-07-13, §7.8 insert). **19 days, 0 commits, second consecutive frozen delta.**

**Every anchor the ledger holds, re-resolved at HEAD** (v11 — not only the rows narrated below):

| Anchor | Resolves at HEAD to | Verdict |
|---|---|---|
| §3.1 **L76** | `"entity_type": "service",` | ✅ |
| note **L119** | `` > `mcp_server`/`mcp_client` are not recognized and MUST NOT be used.`` | ✅ |
| §7.3 **L395** | `"outcome_class": "success \| partial \| failure \| violation",` | ✅ |
| §7.3 **L404** | `"witnesses": [` | ✅ |
| §7.3 **L413** | `reputation.responding_society_signature` MUST | ✅ |
| §7.3 **L415** | `reputation.trust_dimension_updates` … `` per `reputation-computation.md` §4 `` | ✅ (C154-N1 fix intact) |
| §7.3 **L417** | high-consequence `reputation.witnesses` MUST | ✅ |
| §7.3 **L419** | `violation` ⇒ non-positive deltas | ✅ |
| §7.5 **L499** | `4. **No witness** — low-consequence R6 calls MAY proceed…` | ✅ |
| §7.6 **L521** | `` `409 web4_cross_society_exchange_invalid` `` | ✅ |
| §7.7 **L534** | §7.7.1 normative-fence note | ✅ |
| §7.7 **L555** | `- Senior-engineer attention-hours` | ✅ |
| §7.7.3 **L598** | `{` (message-format block) | ✅ |
| §7.8.1 **L714** | `…every crossing is gated on receipt (§7.2)` | ✅ (C226-N2 locus) |
| §12 MUST #6 **L958** | `6. R7 actions MUST be witnessed: …` | ✅ (C226's `L902→L958` correction holds) |
| **external** — C154-N1 → `reputation-computation.md` §4 | `## 4. Reputation Rules` at **L239**; repcomp untouched since `2bc3bafb` (2026-07-18, pre-C226) | ✅ STABLE |
| §8.2 **L737** *(B1+B11's third locus)* | **L737 is now §7.8.2 prose**, not §8.2 — see **N4** | ❌ **STALE → corrected to L793** |

**§A tally: 16 of 17 anchors resolve; 1 corrected in-pass (below). 8/8 C188 findings + all C226 findings HELD by byte-freeze construction; 0 regression; 0 findings against the frozen bytes.**

---

## §B — Mirror-set re-derivation

### B.1 — What the lineage has *ever* enumerated (v8), and what C264 tracked

Instrument, per doc, over `docs/audits/C{35,76,116,148,188,226,264}-mcp-protocol-*.md`:
`grep -o '<token>' <doc> | wc -l`.

| Artifact | token measured | C35 | C76 | C116 | C148 | C188 | C226 | C264 |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| `web4-standard/implementation/sdk/web4/mcp_server.py` | `mcp_server\.py` | 0 | 0 | 0 | 0 | **2** | 0 | 0 |
| `web4-standard/MCP_ENTITY_SPECIFICATION.md` | `MCP_ENTITY_SPECIFICATION` | 0 | 3 | 4 | 3 | 1 | 1 | 0 |
| `web4-standard/test-vectors/mcp/mcp-protocol.json` | `mcp-protocol\.json` | 0 | 0 | 0 | 0 | **1** | 0 | 0 |
| `hub/hub-daemon/src/mcp.rs` | `mcp\.rs` | 0 | 0 | 0 | 0 | **2** | 0 | 0 |
| `web4-standard/schemas/r7-action-jsonld.schema.json` | `r7-action-jsonld` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

> **Published collider (v10).** The bare token `mcp_server` gives **4/1/1/4/1** across C76/C116/C148/C188/C226 — but those hits are the **B1/B11 finding's `entity_type` *value*** (`` `mcp_server`/`mcp_client` … MUST NOT be used ``), not the file. This audit's own scope pre-registration published the collider count as the file count; the policy reviewer caught it before §B was written. Recorded here rather than silently corrected: **a grep is a hypothesis, and this one silently passed for a whole proposal step.**

**C264 tracked the narrowest mirror set in the lineage** — `mcp.py` plus the hub *mailbox* (`store.rs`/`rest.rs`). Two of the zeros above are **correct behaviour, not contraction**: C188 ruled `mcp_server.py` and `hub/…/mcp.rs` **FALSE mirrors** with named predicates (B.4), and re-narrating an adjudicated exclusion every pass is what C290 warned against. The genuine gap is the bottom row: **the standard's own R7 schema, never read by any mcp pass — nor, with one exception, by the audit programme at all** (`git grep -l 'r7-action-jsonld' -- 'docs/audits/'` → **1**, `dictionary-entities-internal-consistency-2026-05-27.md`; denominator `git ls-files docs/audits/ | wc -l` = **195** tracked docs at `76ff2f52`, this audit excluded).

### B.2 — N1 (HIGH, net-new): the ledger carried `action_id` with the direction reversed

**What the ledger says.** C188:93 — *"**N1 (LOW, cross-track SDK; direction = spec CORRECT, SDK diverges/lags).** `mcp.py:809 ReputationEnvelope` diverges from spec §7.3 on two concrete field shapes, **plus an extra field**"*; C188:110 — *"N1 adds `witness_signatures` (2nd concrete divergence) to the previously-carried **`action_id`**/V3-delta shape"*. C226:110 restates *"(extra `action_id`)"*. C264 carries it unchanged as B2+B6.

**What four artifacts inside the standard actually do.** Instruments and paths published:

| Artifact | measurement | `action_id` |
|---|---|---|
| `web4-standard/schemas/r7-action-jsonld.schema.json` | parsed; `required` array; `additionalProperties` | **REQUIRED** — `['@context','@type','action_id','timestamp','rules','role','request','reference','resource','result']`, `additionalProperties: False`. Self-declared *"Validates output from `R7Action.to_jsonld()` and cross-language implementations."* |
| `web4-standard/core-spec/r7-framework.md` (canonical R7, cited by §7.3) | `grep -c 'action_id'` | **9** — in the canonical R7 objects at L281, L615, L647, L711, L754, L813, L915 |
| `web4-standard/implementation/sdk/web4/mcp.py` | read `ReputationEnvelope` (`:810-860`), docstring *"(§7.3)"* / *"Serialize to dictionary matching §7.3 reputation envelope"* | **MANDATORY** — `action_id: str` at `:818` is the class's only non-defaulted field; `to_dict` emits it unconditionally `:831`; `from_dict` does `d["action_id"]` `:852` → `KeyError` when absent |
| `hub/hub-daemon/src/rest.rs` | `grep -n 'action_id\|actionId'` | **constructed** — `action_id: u64` `:3483`, `.to_string()` `:3521` (3rd independent implementation) |
| **`web4-standard/core-spec/mcp-protocol.md`** | `grep -c 'action_id'` = **0**; `grep -c 'actionId'` = **0** (both casings, C302 rule) | **ABSENT** |

**The finding.** §7.3 declares *"An MCP action MUST be treated as R7"* and cites `r7-framework.md` as *"the canonical R7 definition"*. It then specifies the R7 object — `{type, rules, role, request, reference, resource, result, reputation}` — and attaches **five** field-level MUSTs to `reputation`'s sub-fields. `action_id` appears at neither level. mcp is the **only** one of the five artifacts above without it.

**Why this is net-new and not reach (argued both ways, per C284).**
- *For reach*: the token is already in the B2+B6 bundle; the row exists; C284 says a carry acquiring new consumer surfaces routes as reach-escalation, never net-new.
- *For net-new*: what changed is not the reach of a claim but **its direction**. C188 filed `action_id` as SDK **surplus** under an explicit *"spec CORRECT"* ruling and routed the fix **SDK-side**. The measurement reverses the diverging party. A reach-escalation adds consumers to a true claim; this **negates** the claim's remediation target. **Executed as filed, B2+B6 would strip from `mcp.py` a field `r7-action-jsonld.schema.json` makes REQUIRED**, breaking the SDK against the standard's own schema and against `r7-framework.md`.
- **Ruling: NET-NEW**, filed against the *ledger row*, not against the frozen bytes. It does not re-open C188-N1's other two divergences, which stand exactly as filed.

**Severity argued both ways.** *Against HIGH*: §7.3's JSON block contains `/* per R6 */` comments, so it is illustrative rather than a wire example, and validating it literally against a schema is a category error. *For HIGH*: the omission is not a comment placeholder — `action_id` is absent from the section entirely, including its five normative MUSTs; and the operative harm is not the example but the **live carry**, whose execution would produce a schema-rejected SDK. The legend's HIGH clause — *a normative structure rejected by the canonical SSOT* — is met by the structure §7.3 specifies. **Filed HIGH; the counter-argument is recorded so the operator can discount it to MEDIUM without re-deriving it.**

**Narrowed honestly.** The schema also requires `@context` and `@type`, which §7.3 lacks — but `r7-framework.md` lacks them too (`grep -c` = **0/0**), so they are `to_jsonld()` serialization artifacts and **not** an mcp defect. **Charge withdrawn on `@context`/`@type`.** `timestamp` is present in mcp 3× (L196, L405, L417) but **only at witness level**, never at action level; noted, not charged as a separate finding.

**Route**: **operator + SDK/alignment track.** Auditor-applicable? **No** — the fix is a spec edit adding a field, which is authoring. **Do NOT execute B2+B6's `action_id` clause as currently written.**

### B.3 — N2 (MEDIUM, net-new): §12 MUST #2 requires a field set §4.1 never defines

§12 MUST #2: *"All interactions MUST include Web4 context headers."* §4.1 defines those headers **by JSON example only** (L123-152) — no field marked REQUIRED or OPTIONAL, no defaults stated. Its sole `mrh_depth` value anywhere in the spec is the example's `2`.

Two artifacts inside the standard jointly pin the contract the spec omits:
- `test-vectors/mcp/mcp-protocol.json` → `mcp-ctx-002`, titled *"Minimal Web4 context (sender LCT only)"*: input `{sender_lct}` alone; expected `sender_role: ""`, `mrh_depth: 1`.
- `mcp.py` `Web4Context`: `sender_lct` the only non-defaulted field; `sender_role: str = ""`; `mrh_depth: int = 1`; `from_dict` `.get(..., 1)`.
- Executed together by `tests/test_mcp.py:185 test_minimal_context`.

**The spec is not silent by convention.** It marks field optionality exactly **once** in 1020 lines — §7.4 L461, *"`responding_role_expected` is OPTIONAL"* — so the mechanism exists and is unused at §4.1. **And no schema covers it**: over `web4-standard/schemas/` (14 schemas) and `web4-standard/schemas/contexts/` (10 contexts) and `web4-standard/ontology/`, `git grep -ln 'web4_context\|web4Context\|sender_lct\|senderLct'` → **0 files** (both casings). Sibling wire objects do get schemas with explicit `required` arrays (`acp-jsonld.schema.json` `PlanStep` → `["id","mcp","args"]`).

A second implementer reading §4.1 alone would reasonably treat `mrh_depth` as required (it is the only value shown) and fail the standard's own conformance suite. **MEDIUM** by the legend. Not covered by carry **B10**, which is about role-identifier *field names* (`sender_role`/`role_required`/`roleType`), not optionality. **Route: operator/author.**

### B.4 — N3 (MEDIUM, net-new): the standard's conformance suite for this spec predates 76% of it

`web4-standard/test-vectors/mcp/mcp-protocol.json` self-declares `"spec": "web4-standard/core-spec/mcp-protocol.md"`, `"version": "1.0.0"`, and is executed by `sdk/tests/test_mcp.py:35`. It is the standard's conformance suite for this file — and **6 of 7 lineage passes never named it** (B.1).

| | at vector freeze `9b002074` (2026-03-18) | at HEAD |
|---|---|---|
| spec length | **578 lines** | **1020 lines** (+442, **+76%**) |
| §7 | *"MCP-R6 Integration"*, §7.1–§7.2 only | §7.1–**§7.8** (L297–763, 46% of the file) |
| suite | 12 vectors | **12 vectors** — `git log -1` = `9b002074`, 0 commits since |

The 12 vectors cover §2.2 (patterns), §4.1 (context), §4.3 (witness), §4.2/§6.1 (trust requirements), §9.1 (cost), §11.1/§11.2 (session, handoff). They cover **zero** of §5, §7.1–§7.8, §8, §10, and §12. Every normative surface added in the last 4½ months is unexercised — including §7.3's five R7 MUSTs, §7.6's failure codes, §12 MUST #6 (added by C117's own remediation), and **§7.8.2's queue MUSTs, which are precisely what C226-N1 is about**. Nothing in the standard's own conformance apparatus would catch the gap C226-N1 describes.

*Refutation considered*: "a vector suite lagging its spec is normal." Answer: the lag itself is not the charge — the charge is that `mcp.py:17` advertises *"Validated against: `web4-standard/test-vectors/mcp/`"* while that validation reaches 24% of the current normative surface, and C188's *"test-vector-backed"* mirror ruling rests on it. C188 correctly enumerated the covered sections (*"§2/§4.1/§6/§9/§11"*) but did not measure the gap or route it. **Filed net-new at MEDIUM; if the operator prefers, it folds as a reach-escalation on C188's PARTIAL ruling without changing the remedy.** **Route: SDK/conformance track.**

### B.5 — N4 (LOW, net-new): the B1+B11 row lost a locus, then a completeness claim was computed from the degraded row

Provenance chain for B1+B11's third locus (the §8.2 SPARQL server-type line), each cell re-measured at the blob the pass audited:

| Pass | cites | correct when written? |
|---|---|---|
| C76 (2026-06-19) | `§8.2 **L719**` | at `3710c6f0` the `?server a web4:MCPServer ;` line is **L717** — off by 2 |
| C116 (2026-06-29) | `§8.2 **L737**` | at `afab0c43` L737 = `?server a web4:Service ;` — **exact** ✅ |
| C148 (2026-07-06) | `§8.2 **L737**` | same blob — **exact** ✅ |
| C188 (2026-07-12) | `§8.2` | **line number dropped** |
| C226 (2026-07-19) | *(locus absent)* | **locus dropped from the row entirely** |
| C264 (2026-07-24) | — | carried as "8/8 HELD by construction" |

`3e765345` (2026-07-13) inserted §7.8 (964→1020 lines, **+56**) *before* §8, shifting every anchor ≥ §8. C226 caught the shift and corrected the one anchor still recorded — *"the +56 shift … verified only affects anchors ≥ §8 (**N1/C117 at L902→L958**)"* — a correct and careful re-resolution. But the completeness clause attached to B1+B11 — *"Both above §8 → loci unshifted"* — is **false for a three-locus finding**: it enumerates two loci because the third had already been dropped two passes earlier. **The ledger's own degradation defeated the re-resolution discipline: the completeness check ran against the degraded row and certified itself.**

**The remediation itself HOLDS.** At HEAD the §8.2 SPARQL reads `?server a web4:Service ;` at **L793**. The defect is entirely in the instrument.

**Correction published in this pass only, for inheritance verbatim (never rewriting a past audit doc):** **B1+B11's third locus is `§8.2 L793`.** Prefer the section anchor `§8.2 / ``?server a web4:Service``` over the bare line number.

**Distinguished from C302-N1** (filed one day ago on the sibling web4-lct lineage — the refutation the reviewer required). C302-N1 is *staleness under an insert, with one anchor corrected and the rest never re-resolved*. Here C226 **did** re-resolve every anchor the row still held, and published its reasoning. The mechanism is different and strictly prior: **attrition preceding staleness**. C302-N1's remedy ("re-resolve every anchor the ledger holds") is insufficient against it, because the set *"anchors the ledger holds"* had already silently shrunk. **Not a reach-extension of C302-N1 — a distinct failure mode that C302-N1's rule does not catch.** LOW: no spec consequence. **Route: method carry (v12 below).**

### B.6 — INFO-1: C188's FALSE-mirror exclusion on `hub/hub-daemon/src/mcp.rs` RE-VERIFIED, HOLDS

Pre-registered as the §B primary and bounded to exactly C188's three named predicates. `mcp.rs` moved **2 commits** in-window (`ff5e7b0b` #610 governance-gate ordering test, `6f3d610a` #614 error constructors) and is 1027 lines.

| C188 predicate | instrument (over `hub/hub-daemon/src/mcp.rs`, both casings) | count |
|---|---|--:|
| §4.1 Web4 Context Header assembly | `grep -c 'web4_context\|web4Context\|sender_lct\|senderLct\|mrh_depth\|mrhDepth\|law_hash\|lawHash\|proof_of_agency\|proofOfAgency\|t3_in_role\|t3InRole'` | **0** |
| R7 envelope signing | `grep -ci 'r7\|reputation\|outcome_class\|outcomeClass\|propagation_scope\|propagationScope'` | **0** |
| §7.6/§7.7 code emission | `grep -c 'W4_ERR_\|web4_err\|w4_err'` | **0** |

Self-declaration intact verbatim at `:6-9`: *"Full MCP wire protocol compliance (JSON-RPC framing, capability negotiation) is V2."* **The exclusion HOLDS on new evidence. Do NOT re-open.** Neither in-window commit touches any of the three predicates; both are hub-plane concerns and **route to the HUB track untouched** per the pre-registered bound.

### B.7 — INFO-2: the hub mailbox mirror, per C264's standing guard

C264's guard: *"Re-derive mailbox mirror at live HEAD each delta (it keeps moving)."* It moved — `store.rs` 3 commits, `rest.rs` 12 commits, +942/−83 lines since `8c3711c6`. But `git diff 8c3711c6..HEAD -- hub/hub-lib/src/store.rs hub/hub-daemon/src/rest.rs | grep -c 'mailbox_'` → **0**. The mailbox core (`mailbox_put`/`mailbox_delete`/`mailbox_load_all`/`mailbox_is_durable`) is untouched; all 14 commits are atomic-write/plane-split/receipt/law-gate work. **Gate outcome unchanged: GENUINE, narrowed to notices/messages.** Per C264's guard, the sidecar and `send_secret` relay are **not** re-opened.

### B.8 — B1 corpus sweep: a measured zero

`git grep -n 'entity_type.*mcp_server\|entity_type.*mcp_client\|entityType.*mcp' -- 'web4-standard/'`, excluding the `MUST NOT` prohibition itself → **0 hits, both casings.** `MCP_ENTITY_SPECIFICATION.md` (5-of-7 tracked, 0 at C264) carries `entity_type: "service"` at L64/L131/L160/L189. **B1's remediation reached the whole standard.**

---

## §B′ — Negative gate: paths searched, tokens named

Every zero below names its token and its tree; both casings swept per the C302 rule; all at HEAD `76ff2f52`.

| Claim | tree searched | token(s) | result |
|---|---|---|--:|
| mcp defines `action_id` | `web4-standard/core-spec/mcp-protocol.md` | `action_id`, `actionId` | **0** |
| mcp defines the JSON-LD envelope | same | `@context`, `@type` | **0, 0** (r7-framework also 0 → withdrawn) |
| any schema/context covers §4.1 | `web4-standard/schemas/`, `schemas/contexts/`, `ontology/` | `web4_context`, `web4Context`, `sender_lct`, `senderLct` | **0 files** |
| any audit read the R7 schema | `docs/audits/` (195 docs) | `r7-action-jsonld` | **1 doc** |
| mcp lineage read the R7 schema | the 7 lineage docs | `r7-action-jsonld` | **0** |
| `mcp.rs` has §4.1/R7/§7.6 surface | `hub/hub-daemon/src/mcp.rs` | see B.6 | **0/0/0** |
| B1-forbidden values survive | `web4-standard/` | `entity_type.*mcp_server\|mcp_client`, `entityType.*mcp` | **0** |
| mailbox core moved | diff `8c3711c6..HEAD` over `store.rs`+`rest.rs` | `mailbox_` | **0** |

---

## §C — Carry-row survival census (v10) and disposition

**Census.** The mcp ledger has **not** emptied the way the handshake ledger did at C144. Row counts per pass: C76 filed 11 (B1–B12 family), C77 remediated 8, C116/C148 carried the full HELD table, C188 carried 8/8 + added N1, C226 carried 8/8 + added N1/N2, C264 carried all by byte-freeze construction. **No row vanished.** What was lost is **finer-grained than a row**: one *locus* inside a surviving row (N4). The v10 instrument — counting rows — is blind to it, which is why N4 is filed as a distinct method carry.

| Carry | Status at C304 | Route |
|---|---|---|
| **C226-N1** (MEDIUM, §7.8.2 idempotency-on-redelivery) | **STANDS as a defect** — §7.8.2 text frozen, no dedup clause. **Its "new normative obligation" characterization is REFUTED** (N1): `action_id` is already REQUIRED by `r7-action-jsonld.schema.json` and carried 9× by `r7-framework.md`. | **operator/author**, with the reclassification. Still **NOT auditor-applicable** (a spec edit is authoring). |
| **C188-N1** (LOW/SDK, `ReputationEnvelope`) | `mcp.py` byte-frozen (`b6c243c2`, 2026-05-19). The two *shape* divergences (`witness_signatures` flat vs structured `witnesses`; `trust_dimension_updates` flat vs nested) **STAND exactly as filed**. Its third element, the `action_id` "extra field", is **INVERTED** — see N1. | **SDK track (B2+B6)** — **hold the `action_id` clause; execute the other two only.** |
| **C226-N2** (INFO) | REFUTED-as-defect. Locus L714 re-resolved ✅. | do **NOT** re-raise |
| **C154-N1** | anchor STABLE (`repcomp` §4 = L239; untouched since `2bc3bafb`) | closed |
| **C117-N1** | HELD; anchor L902→**L958** (C226's correction verified) | closed |
| **B1+B11** | HELD at HEAD; **third locus corrected to §8.2 L793** (N4) | inherit verbatim |
| **C148/C188 carries** (B5+B12, N5/N9/N13, N12, N15, F5/C62-B1, F9-inverted, B1-family) | HELD by byte-freeze construction | unchanged |

**Findings this pass:** **N1 HIGH · N2 MEDIUM · N3 MEDIUM · N4 LOW · 2 INFO. 4 net-new. Zero mutation.**

- **C305 = declared NO-OP.** N1/N2/N3 are operator/author/SDK-owned; N4 discharges into this doc's own correction + the method carry. Do **not** self-fix `mcp-protocol.md`.
- **Rotation** advances +2 → `atp-adp-cycle` = **C306** (last audited C266, PR #575). Next mcp delta ≈ **C344**.

**Baseline for the next mcp delta:** spec `3e765345` (blob `4491c1bb`, 1020L; §7.3 L370-422, §7.8 L708-763, §8.2 L787, §12 MUSTs L947-959); `mcp.py` `b6c243c2`; `mcp_server.py` `759eaefa`; `MCP_ENTITY_SPECIFICATION.md` `f3d2613d`; test vectors `9b002074`; `mcp.rs` `6f3d610a`; hub mailbox re-derive at live HEAD.

**Guards for the next pass.**
1. Check whether §7.3 gained `action_id` and whether B2+B6's `action_id` clause was corrected — **if the bundle was executed as originally filed, the SDK now fails `r7-action-jsonld.schema.json`; verify before assuming remediation.**
2. Check whether §4.1 gained required/optional marking **or** a schema (N2); the mirror set now includes `web4-standard/schemas/`.
3. Check whether `test-vectors/mcp/mcp-protocol.json` moved off `9b002074` (N3).
4. B1+B11's third locus is **§8.2 L793**; do not inherit `L737`.
5. `mcp_server.py` and `hub/…/mcp.rs` are **adjudicated exclusions** (C188, re-verified C304) — do not re-narrate them as contraction.

---

## Pattern (C304)

**A ledger row can be wrong in a way that more evidence makes worse.** `action_id` was in the mcp ledger for three passes; every pass re-verified that it was *there*, none asked which side of the divergence it belonged on. C188 recorded it as an SDK "extra field" under an explicit *"spec CORRECT"* direction ruling, and C226 and C264 inherited the direction along with the token — so the carry accumulated confidence while pointing at the wrong party, and its execution would have broken the SDK against the standard's own schema. The evidence that inverts it sat in `r7-action-jsonld.schema.json`, a file **1 of 195 audit docs** in this corpus has ever opened.

Two disciplines compose into the miss. Under **v8/v11** the mirror set is derived from what *implements* the subject matter — so a **schema**, which neither implements nor is implemented, falls outside every pass's frame even though it is the most normative artifact of the four. And under **v10** the census counts *rows*, so the B1+B11 locus that evaporated two passes before C226's completeness claim (N4) was invisible to the very instrument meant to catch continuity loss.

**v12 (new): re-derive the DIRECTION of every carried divergence, not just its presence.** For each row asserting "X diverges from Y", re-ask *which side the corpus agrees with* — enumerate every artifact carrying the disputed field, **including the standard's own schemas and contexts, which are normative peers and not mirrors** — before re-certifying the row as HELD. A carry inherited with its direction unexamined is worse than a dropped carry: a dropped carry loses information, an inverted one manufactures it. **And the unit of continuity is the LOCUS, not the row** — a completeness claim ("all this row's anchors are accounted for") computed from a row that has already lost a locus is self-certifying. Count loci per row across passes, not rows per pass. → [[feedback_carry_gains_reach_not_truth]] / [[feedback_standard_disagrees_with_itself]] / [[feedback_anchor_not_paragraph]] / [[feedback_ledger_emptied_not_closed]].
