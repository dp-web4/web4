# C274 — ACP Framework Seventh-Delta Re-Audit

**Date:** 2026-07-28
**Auditor:** Autonomous session `legion-web4-20260728-060011`
**Document audited:** `web4-standard/core-spec/acp-framework.md` (710 lines, blob `f8d7ccda`, last moved `fb0075fc` 2026-07-08)
**Method:** §A hand-verification at live HEAD (C159's three edits + C234's checklist + all 9 carry-ledger rows, every anchor re-grepped rather than inherited). §B refute-by-default finder pass over the corpus-delta since C234 — a window of **five operator-authored documents**, each gated before it was allowed to yield; plus a genuine-mirror gate re-derived at live HEAD including the crates that did not exist at C234.
**Lineage:** C18 (#244) → C37 (#283) → C86 → C87 (#378) → C125 → C126 (#437) → C158 (#485) → C159 (remediation, #487 `fb0075fc`) → C196 (5th, 0 net-new) → C234 (6th, 0 net-new, #556) → **C274** (this 7th delta).

---

## Instrument note — the window, not the target

The full acp authority stack is **byte-frozen for 20 days**: `git log fb0075fc..HEAD` over the spec, SDK `acp.py`, `acp-jsonld.schema.json` and `test-vectors/` is **empty**. As at C268/C270/C272, the frozen target is the least informative artifact in its own audit; the yield surface is the window.

This window is the richest any C-fire has drawn. Five operator-authored documents landed in 48 hours, four of which speak directly to *authorization evidence for agent actions* — which is acp's entire subject matter:

| Commit | Artifact | Prima-facie acp relevance |
|---|---|---|
| `752eadde` | `docs/PRD_ACTION_EVIDENCE.md` — the **Agent Action Evidence Profile (AAEP)** | **Highest.** Scopes "the evidence an external party needs to decide whether an agent action was authorized" |
| `780af6ef` | `docs/strategy/hub-position-review-and-plan-2026-07-28.md` | **Highest.** States the gap in prose: *"nothing binds an Action Request → Policy Decision → Result Evidence triple into signed, separately-attributable objects"* |
| `954ee391` | #580 `resilience-to-incomplete-information.md` — "absence NEVER grants" | High — acp is the corpus's absence-handling agentic spec |
| `4665a430` | #579 `dictionary-as-context-mandatory-role.md` | Low — acp carries 0 dictionary references |
| `5df662a5` | README worked example — why the **relying party** must compute trust | Low — rides the ratified #531 principle |

`780af6ef` was **not** in this session's proposed scope; the policy reviewer caught the omission and made adjudicating it binding condition 1. It turned out to be the artifact that decided the pass.

**Pre-declared question, recorded before the finder ran:** AAEP §1 asserts the corpus lacks a compact package answering *who acted / under whose delegation / against which policy / with what witnessed result*. acp §2.2 Intent + §2.3 Decision + §2.4 ExecutionRecord + §4.2 proofOfAgency is the corpus's existing candidate for exactly that. Either **(a)** the PRD's precedent survey is incomplete, **(b)** acp genuinely fails the PRD's load-bearing property ("each party signs only its own statement"), or **(c)** the two are disjoint by layer.

Binding condition 3 required that **(b) be tested first and honestly**, because (b) is the self-implicating branch: audit cycle C37-B2-8 (applied at C87, #283) **removed** the only signature field acp ever had — a top-level `signatures` on §2.1 AgentPlan — on the stated ground that *"the ACP SDK has no signature concept"*. An audit lineage that deleted spec surface to match an implementation, where the operator now requires that surface back, is the expensive answer, and therefore the one at risk of being skipped.

**It was tested first. It was refuted — on corpus evidence, not on convenience.** See §B.0.

## Authority Hierarchy

Unchanged from C125/C158/C196/C234: vectors → schema → SDK → spec prose; canonical neighbor owns its primitive.

---

## §A — Delta Re-Verification

### §A.1 — C159's three applied edits (present + regression-clean at live HEAD)

Spec blob unchanged since C196, but every locus was re-grepped at live HEAD per [[feedback_prior_finding_path_provenance]] rather than inherited from C234's transcript:

| Edit | Locus | Live state | Anchor re-verified at HEAD |
|---|---|---|---|
| **C156-5** softened trust-gaming cell | `:418` | `Audit adjustments (reputation staking is a future mechanism — see reputation-computation.md §10)` | reputation `## 10. Future Evolution` **L835** + `### Reputation Staking` **L845**. Section-cite, line-shift-immune. **HELD** |
| **N1** WitnessDeficit re-cite | `:568` | `runtime-count deficit (approval-gate phase, §3.2/§5.2): too few…` | acp §3.2/§5.2 live (frozen). **HELD** |
| **N3** grant-path correction | `:254` | `exceeds_caps(intent, grant.scope.r6Caps.resourceCaps)` | entity-types still carries `"r6Caps"` **L377** / `"resourceCaps": {"max_atp": 25}` **L379** — byte-identical to the L377-379 C234 recorded. Effector still at §4.8, *after* §4.7. **HELD** |

**[[feedback_remediation_introduced_regression]] check: CLEAN.** Spec byte-frozen; nothing to introduce. **No recorded-path drift this pass** (contrast C272, where three recorded paths had drifted).

### §A.2 — C87's 8 fixes / 13-transition count

Byte-frozen since verified HELD at C158; SDK `VALID_TRANSITIONS` frozen. Spot-checked (`:234` wildcard-expansion note intact). Not re-litigated.

### §A.3 — Carry ledger: **9 rows** (13 named carries), all re-verified STILL-OPEN

Re-derived from C234 §A.3's table, not from this session's scope prose — the scope proposal said "12 carries" and was wrong; C234 §A.3 has **9 rows**. Recorded per binding condition 5 and [[feedback_prose_is_not_ledger]].

| Carry | C234 state | C274 state | Live evidence at HEAD |
|---|---|---|---|
| **M6 / B-M6** — 11 `acp:` predicates in no TTL | STILL-OPEN | **STILL-OPEN** | `grep -c "acp:" ontology/*.ttl` = **0**. CROSS-TRACK (ontology) |
| **M7** — integer `witnessLevel` vs structured `witness_requirement` | STILL-OPEN | **STILL-OPEN** | Split live: int at `:81`/`:316`/`:605`, structured object at `:329`. SDK integer-only. SDK bridge |
| **B-AGENCY / L1** — `web4_context` proofOfAgency casing/field-set | STILL-OPEN | **STILL-OPEN** | mcp-owned envelope; mcp byte-frozen since C226. MEDIUM CROSS-TRACK |
| **B-LEDGERPROOF / C37-5** — §4.2 `ledgerProof` | STILL-OPEN | **STILL-OPEN** | Sole in-doc ledger object (`:281-285`); SDK `ProofOfAgency` has no ledger proof; schema `additionalProperties:false`. DESIGN-Q — **and see N1 below, which is the first window evidence bearing on it** |
| **B8** — ACP discharge not routed through R6 | STILL-OPEN | **STILL-OPEN** | atp-adp §7.1 #5 `Discharging MUST occur through R6 transactions` live; acp §9.1 MUST list (5 items, `:9.1`) has no R6-discharge item. CROSS-TRACK |
| **N2** — `maxAtp` "budget"/cumulative vs SDK per-intent-only | STILL-OPEN | **STILL-OPEN (unchanged)** | acp `:174` "against the plan's `resourceCaps.maxAtp` budget"; SDK `check_atp` **acp.py L213-217** still `return atp_amount <= self.max_atp` (per-intent); `check_executions` **L219** still defined. SDK frozen ⇒ divergence unchanged |
| **N4** — hub MCP write tools carry no ACP proof-of-agency | INFO (UNTRIPPED) | **STILL INFO (UNTRIPPED)** | The hub moved a lot this interval (`9034ade0`…`5c2dd39f`: pubkey-by-uuid, pair sidecar, enrollment registry, encrypted-state fix, H-007/H-008 hardening, notice-drop alarm) but **no mover admitted a non-operator agentic caller to a write tool**. Not an acp defect regardless |
| **B11 / B12 / B13 / B14 / B15** | STILL-OPEN | **STILL-OPEN** | No mover touched errors §10.1 envelope, SAL witness vocab, or the D0 cluster |
| **JSONC fences** | INFO-corpus | **INFO-corpus** | Re-derived: **3 of 7** `json` fences fail strict parse — matches C126/C158/C234 exactly. Corpus-wide style DESIGN-Q, operator-gated |

### §A.4 — Genuine-mirror gate: **NEGATIVE**, re-derived at live HEAD

Per the standing method guard ("the SDK mirror is not a fixed set"), the checker was re-baselined on the **current** crate set rather than C234's. Two crates now exist that did not at C234's baseline: `web4-policy/` and **`web4-trust-core/`**.

- `grep -rln "ProofOfAgency|ExecutionRecord|AgentPlan|ACPState|acp" --include=*.rs` over `web4-core/ web4-policy/ hub/` → **one file**: `web4-core/src/r6.rs` (the `ProofOfAgency` already routed at C156-3, inside the excluded B-AGENCY carry).
- **`web4-trust-core/` → zero acp tokens.** The new crate is not an acp mirror.
- No `Plan` / `Intent` / `Decision` / `ExecutionRecord` / `ACPState` structs anywhere in Rust.

This reproduces the C158/C196/C234 negative for the **fourth** consecutive delta and matches the C182/C220 NEGATIVE-gate pattern: acp's only implementation is the frozen Python SDK. **No layer-split, no wire-shape divergence to route.**

---

## §B — Findings

**Result: 1 MEDIUM routed to the author, 2 INFO, ZERO mutation — and one flagship candidate refuted on corpus evidence.** This is a **subtractive** pass: the finding the window most invited is the one that died.

### §B.0 — Flagship candidate: **REFUTED** (branches (b) and (c) both fail)

**The candidate.** acp's §2.3 Decision (`:135`) and §2.4 ExecutionRecord (`:165`) carry `witnesses` as a **bare list of LCT strings**. The corpus elsewhere declares a *canonical* witness shape — `r7-framework.md` §1.7 `{lct, signature, timestamp}` — which `mcp-protocol.md` `:417` makes normative for high-consequence actions: *"Each `witnesses` entry is a `{lct, signature, timestamp}` object, matching the canonical Reputation witness shape in `r7-framework.md` §1.7"*, alongside `:413`'s *"`responding_society_signature` MUST be signed by the responding society's Policy-Entity."* That pattern is **precisely** AAEP's "Policy Decision signed by the policy entity" + "Result Evidence observed by these parties **separately**". acp's schema (`acp-jsonld.schema.json` L189-192, L229-232, `additionalProperties:false`, `items:{type:"string"}`) would **schema-reject** the canonical object. acp also carries **no signature concept at all** — `grep -i "signat|sign("` over the spec, the schema and `acp.py` returns **zero hits in all three**. Read against the PRD, that is the format it calls *"testimony transcribed by an interested party."*

**Refutation 1 — corpus-idiom baseline. HOLDS, and is decisive.** Per [[feedback_refute_your_best_finding]], the "novel deviation" was tested against corpus ground truth rather than asserted. Every core-spec file carrying a `witnesses` field, classified by shape:

| Bare/unsigned `witnesses` | Signed `{lct,signature,timestamp}` |
|---|---|
| SOCIETY_SPECIFICATION (7), entity-types (3), atp-adp (2), **acp (2)**, web4-society-authority-law (2), dictionary-entities (1), r6-framework (1) | r7-framework (3 of 4), mcp-protocol (1 of 1), reputation-computation (1 of 1) |

**7 of 10 files use the bare form; 19 of 24 occurrences.** Unsigned `witnesses` is the corpus *majority idiom*, not an acp deviation — including `entity-types.md` §4.7's **Agency Grant**, the ratified root of acp's own authority chain, which carries `"witnesses": ["lct:web4:witness:A"]`. This is the exact deflation shape as C158's JSONC adjudication (*a property shared by most of the corpus is corpus style, not a defect in the file the rotation happens to be pointing at*) and the exact error C234's flagship died of. **Charging acp specifically would be an overcall.**

**The verifier behind that table was itself baselined**, per [[feedback_enumeration_and_grep_hypotheses]] — a decisive refutation resting on one grep is a silent-failing hypothesis. Three independent classifications were run and they **disagreed**: a 2-line proximity window (bare 17 / signed 7), a 6-line window (bare 15 / signed 7), and a parser that classifies by the **array item shape** (bare 19 / signed 5). The disagreement was resolved by reading the disputed sites rather than by picking a number: both extra "signed" hits in the wider windows are **false positives** — `entity-types.md:394-395` is a bare `"witnesses": ["lct:web4:witness:A"]` followed by a *sibling* `"signatures": [...]` key (not a signed witness item), and the `SOCIETY_SPECIFICATION.md` hit was prose at `:299` about co-signatures caught in a neighbouring occurrence's window. The item-shape parser is the correct instrument for the question asked, and it reproduces the table above.

**Refutation 2 — no binding, so mcp's MUST does not reach acp. HOLDS.** `grep -i "r7|r6-framework"` over acp = **0** (the sole reputation cite is §7.2's staking note); `grep -i "acp"` over `r7-framework.md` = **0**. The cross-reference count is zero **in both directions**. mcp `:417`'s MUST self-scopes to the *R7-over-MCP reputation envelope*; acp's ExecutionRecord is a different object in a spec that neither cites nor is cited by it. Branch **(c) disjoint-by-layer holds** for the MUST, exactly as C158's self-scoping precedent ("Every MCP call **from ACP**") predicted.

**Therefore branch (b) is REFUTED**, and with it the self-implicating reading of C37-B2-8. That remediation removed a field that had no home in the schema or SDK; it is correct at its own layer and did **not** introduce this gap. **No finding is recorded against the audit lineage.** Binding condition 3 is discharged on the evidence, not by avoidance.

### §B.1 — N1 (MEDIUM) — the AAEP gap is real but mis-stated: it is a **non-join**, not an absence — and that mis-statement mis-scopes a P1 work item

**Route: author (dp). Do NOT self-apply.** Both charged artifacts are operator-authored; per the C272 corollary their authority is **prospective**, so this is a completeness claim against a precedent survey, not a defect verdict against a ratified spec. Per binding condition 2 it is stated as a factual omission with citations, and carries **no** judgment on the PRD's scoping, direction or priority.

**The claim.** `PRD_ACTION_EVIDENCE.md` §1 states an external implementer *"still lacks one compact, normative package"* answering who acted / under whose delegation / against which policy / with what witnessed result; `780af6ef` §4 states *"nothing binds an Action Request → Policy Decision → Result Evidence triple into signed, separately-attributable objects."* Verified at HEAD, both halves already exist in the ratified corpus, in two specs that do not cite each other:

| AAEP object | Existing ratified corpus artifact | Gap |
|---|---|---|
| **Action Request** | `acp-framework.md` §2.2 Intent + §4.2 `proofOfAgency` (`{grantId, planId, intentId, nonce, audience, expiresAt}`, + `ledgerProof`) | unsigned |
| **Policy Decision** | §2.3 Decision (`{decision, by, rationale, witnesses, timestamp}`) — `by` is an LCT, i.e. attribution *is* modelled | unsigned |
| **Result Evidence** | §2.4 ExecutionRecord (`{mcpCall, result, t3v3Delta, witnesses, canonicalHash}`) | unsigned |
| **the signing/attribution pattern the triple needs** | `r7-framework.md` §1.7 + `mcp-protocol.md` `:413`/`:417` — Policy-Entity signature + `{lct,signature,timestamp}` witnesses | exists, but in specs with **zero** cross-reference to acp |

So the triple is not missing: it is **ratified, schema'd, test-vectored and implemented in the SDK**, and it already carries `canonicalHash` (§2.4) and `t3v3Delta` — i.e. it is already on the reputation path. What is missing is the **join** between it and the corpus's own signed-attribution pattern. The concrete, checkable blockers are two, and both are small:

1. acp's schema constrains `witnesses` to `items:{type:"string"}` under `additionalProperties:false` (L189-192, L229-232) — the canonical `{lct,signature,timestamp}` object is **schema-rejected today**.
2. acp has no signature affordance at all (0 hits across spec/schema/SDK), and `additionalProperties:false` means one cannot be added by an implementer.

**Why this matters practically, and why it is MEDIUM rather than INFO.** `780af6ef` §5 sequences **P1-6: "AAEP gap-map of the join path… costs a day, not a sprint"** — scoped to *the hub's join path*. On this evidence that is scoped to the more expensive artifact. The hub would have to be reverse-engineered into the triple; **acp already is the triple**, with a schema and vectors to diff against. The cheapest gap-map — and the one that would tell the PRD what its FR-2 field set should actually be — is **acp §2.2/§2.3/§2.4 ↔ r7 §1.7**, and its output is two named edits rather than a discovery exercise. Stated as an absence, the gap reads as greenfield specification work; stated as a non-join, it is a schema constraint plus a cross-reference.

**Note for B-LEDGERPROOF/C37-5.** This is the **first window evidence** bearing on that DESIGN-Q, open since C37. AAEP FR-4 ("evidence atomicity… heads anchored beyond the issuing party") is an independent argument *for* the admit arm of the admit-vs-strip question. Recorded as evidence for the operator's decision; **not** self-adjudicated — the carry stays open.

**Refutations run and survived:** (i) *"the PRD self-scopes to a portable external profile, so internal corpus specs are out of scope"* — fails: §1's claim is explicitly about what the **corpus** provides ("The corpus describes identity, trust, law, action grammar and witnessing"), and §4's integration table surveys SPIFFE/SPIRE, MCP, policy engines, sandboxes and provenance frameworks — external ecosystems — while naming no internal corpus spec at all. (ii) *"'action grammar' in §1 already gestures at acp"* — fails: the corpus's action grammar is R6/R7 (`r6-framework.md`/`r7-framework.md`), and the sentence lists it among things the corpus *has* while the following sentence says the package is *lacking*; acp is named nowhere in either document. (iii) *"this is just B-AGENCY/L1 again"* — fails: B-AGENCY is about `web4_context` proofOfAgency **casing and field-set** within the mcp envelope; this is about whether acp's three objects are separately attributable at all.

### §B.2 — I-1 (INFO) — acp is uncited prior art **for** #580; corroborates C272-N1 rather than being net-new

**#580 asked whether absence may grant. acp answers no, everywhere, and #580 does not cite it.** Every absence surface in acp fails closed, verified at HEAD: `:86` `"fallback": "deny"` (human-approval timeout), `:337` `"fallback": "abort"` (witness quorum not reached), `:232` `Any active state | Error / Timeout / Deny / Law-check fail → Failed`, and five deny-on-absence raise sites (`:247` NoValidGrant, `:251`/`:309` ScopeViolation, `:255`/`:313` ResourceCapExceeded, `:318` WitnessDeficit). `grep -i "acp"` over `resilience-to-incomplete-information.md` = **0**.

This is the **same charge class as C272-N1** (#580's precedent survey is incomplete), now with a second witness — and a notably sharper one, because the polarity is inverted: at C272 the window artifact *indicted* reputation §4's fail-open delegation; here the same artifact is *exonerated and anticipated* by acp, which has shipped its rule since C18. Per [[feedback_prose_is_not_ledger]], the "is it NEW?" question is asked before "is it TRUE?": **this is not net-new** — it is corroboration folded into the already-routed C272-N1, and it should travel with it to the author rather than be counted a second time.

### §B.3 — I-2 (INFO) — #579 and `5df662a5` adjudicated **DISJOINT** for acp

- **#579 (dictionary context-mandatory)** — acp carries **0** dictionary references. #579's normative sketch self-scopes to *"any society that accepts requests from outside itself"* and to R6 Request formation by an **outside actor**; acp's plan→intent path is intra-society and grant-scoped. Additionally, #579's null-answer rule (*"an empty answer must not be readable as 'nothing is accepted'"*) is **satisfied** by acp for the same reason as §B.2 — `within_scope` failure raises rather than permits. Adjudicated disjoint; no carry created.
- **`5df662a5` (relying-party worked example)** — rides the already-ratified #531 "Inspectable Evidence, Not Prescribed Trust" principle. acp §6.1's `riskAssessment`/auto-approve surfaces are *the plan author's own* thresholds, not a prescribed trust verdict imposed on a relying party. No acp referent; no carry created.

### Summary by severity

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH+ | 0 | — |
| MEDIUM | 1 | **N1** — AAEP gap mis-stated as absence; mis-scopes strategy-doc P1-6 → **author (dp)** |
| INFO | 2 | **I-1** corroborates C272-N1 (not net-new) · **I-2** #579 + README disjoint |
| REFUTED | 1 | flagship: "acp deviates from the canonical witness shape" — killed by corpus-idiom baseline (7 of 10 files) + zero acp↔r7 binding |

### Direction of every finding

- **N1 → author (dp), MEDIUM.** A completeness claim against two operator-authored documents whose authority is prospective. **Not** a defect in `acp-framework.md`; **nothing to self-apply**.
- **I-1 → travels with C272-N1** to the same author. Not counted as net-new.
- **I-2 → closed in place.** No carry.
- **All 9 carry-ledger rows → unchanged**, re-verified STILL-OPEN with live evidence (§A.3).

---

## §C — Carry ledger for the next acp delta (~C312)

**Do NOT re-open any of the following as net-new.**

- **Freeze state:** `acp-framework.md` blob `f8d7ccda`, last moved `fb0075fc` (2026-07-08). SDK `acp.py`, `acp-jsonld.schema.json`, `test-vectors/acp/` all **0 commits** since. If any has moved at the next fire, the mirror gate must be re-derived from scratch.
- **Genuine-mirror gate NEGATIVE for the 4th consecutive delta**, now including `web4-policy/` and `web4-trust-core/` (both zero acp tokens). The only Rust `ProofOfAgency` is `web4-core/src/r6.rs`, already routed at C156-3 inside the excluded B-AGENCY carry — **do not re-count it as an acp mirror.**
- **9 open carry rows, all STILL-OPEN:** M6/B-M6 (ontology), M7 (SDK bridge), B-AGENCY/L1 (mcp-owned), B-LEDGERPROOF/C37-5 (DESIGN-Q — **now has first supporting window evidence via AAEP FR-4; still operator's call**), B8 (atp-adp §7.1 #5), N2 (`maxAtp` budget-vs-per-intent), N4 (INFO, trigger still UNTRIPPED), B11-B15, JSONC fences (3 of 7, corpus-wide).
- **C274-N1 is routed, not applied.** If the author acts on it, the next acp delta's regression check is: did `acp-jsonld.schema.json` `witnesses` widen from `items:{type:"string"}`, and did acp gain a cross-reference to `r7-framework.md` §1.7? Both are one-grep checks.
- **REFUTED, do not resurrect without new evidence:** "acp's bare-string `witnesses` deviates from the canonical shape." It is the corpus majority idiom (7 of 10 files, including entity-types §4.7's Agency Grant) and acp↔r7 cross-reference count is 0 in both directions. Any future attempt must first re-run the corpus-idiom baseline and show it has changed.
- **N4 trigger to watch (unchanged):** if the hub later admits non-operator agentic callers to write tools, N4 converts from INFO to a real spec-lag gap. The hub moved substantially this interval without tripping it.

---

## Method notes

**The method carry fired a 4th consecutive time — and this time it was a finding-killer.** C268, C270 and C272 each established that the window, not the frozen target, carries the yield, and that one should ask *what landed that claims authority over this file's subject matter*. Here five such artifacts landed at once, and the discipline that mattered was the **second** half of the guard: [[feedback_read_the_specs_meta_structure]] and [[feedback_refute_your_best_finding]] run in both directions. The corpus-idiom baseline — the cheap grep that classified every `witnesses` field in the corpus — killed the pass's most attractive finding, exactly as the same instrument killed C158's JSONC charge and C234's "Scope" flagship. Had it not been run, this audit would have shipped a confident, well-cited, **wrong** MEDIUM against a byte-frozen ratified spec, on the authority of a draft PRD.

**And the killer grep itself had to be baselined before it could be trusted.** Three classifications of the same corpus disagreed (§B.0); the first one run would have overstated the signed-shape population by 40%. The lesson is one level up from [[feedback_enumeration_and_grep_hypotheses]] as previously written: when a *refutation* is the load-bearing result, the refutation's instrument needs the same adversarial treatment as the finding it kills — otherwise a bad grep silently rescues a bad finding, or buries a good one. Resolution came from reading the disputed sites, not from preferring a number.

**What survived is better-directed than what died.** The refutation did not empty the pass; it *relocated* the finding — from "the spec is defective" to "the gap statement about the spec is imprecise, and the imprecision has already mis-scoped a sequenced work item." That is the C272 tier-check pattern repeating (there, the governance-tier check *relocated* a finding rather than killing it), and it is the second consecutive fire where the honest answer was a charge against a **precedent survey** rather than against a spec.

**The policy reviewer changed the outcome.** `780af6ef` was missing from the proposed scope; the reviewer found it, made it binding, and it turned out to hold the operator's own prose statement of the exact seam under audit — the artifact that let N1 be stated as a scoping correction to a real P1 item rather than as an abstract observation. Binding condition 3 (test the self-implicating branch first) is the reason §B.0 leads with branch (b) rather than burying it. The review was not a formality on this pass.

---

*Audit produced under v2 Autonomous Session Protocol. Zero mutation of `acp-framework.md`, `acp.py`, the schema, the test vectors, or any of the five operator-authored window documents. Every cited line re-grepped at live HEAD during execution; the corpus-idiom baseline is reproducible from the command recorded in §B.0.*
