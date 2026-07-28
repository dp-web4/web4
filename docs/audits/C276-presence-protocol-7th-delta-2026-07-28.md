# C276 — presence-protocol.md Seventh Delta Re-Audit

**Date**: 2026-07-28
**Auditor**: autonomous web4 session (legion, C-series **C276**, slot `web4-20260728-120011`)
**Subject**: `web4-standard/core-spec/presence-protocol.md` (722 lines, 9 sections), v1 Draft — blob `6414a7fe` at HEAD
**Baseline**: `docs/audits/C236-presence-protocol-6th-delta-2026-07-20.md` (6th delta, zero net-new)
**Lineage**: C5 (`presence-protocol-internal-consistency-2026-05-17.md`, 13 findings) → C38 (#284/#285) → C88 (#379) → C89 (#380, `0beb1b93`) → C127 → C128 (#439 `cf0d6cc5`, remediation) → C160 (4th) → C198 (5th) → C236 (6th, #557) → **C276** (this, 7th).
**Companion artifacts cross-checked**: `presence-protocol-CHANGELOG.md`; all **12** JSON Schemas under `web4-standard/schemas/presence-protocol/{v0/common,v0/tools,v1/tools}` + the schema-dir `README.md`; `web4-standard/testing/conformance/presence-protocol-conformance.json` (**14** scenarios, P0-001..P0-010 + P1-001..P1-004); filesystem ground truth at live HEAD.
**Scope**: Internal-consistency + **inbound-carry** 7th-delta re-audit. **Zero mutation** — no edit to the spec, its schemas, its CHANGELOG, or its vectors.
**Instrument**: Empty-diff freeze proof + live-HEAD re-derivation of the SDK/consumer set (including crates absent from C236's gate list) + refute-by-default adjudication of the 2026-07-20 → 2026-07-28 window, one lens per candidate, **with an independent adversarial pass pointed at this delta's own flagship**. Per [[feedback_refute_your_best_finding]], [[feedback_canonized_principle_rescopes_frozen_file]], [[feedback_read_the_specs_meta_structure]], [[feedback_prose_is_not_ledger]], [[feedback_snapshot_presence_guard]], [[feedback_enumeration_and_grep_hypotheses]], [[feedback_prior_finding_path_provenance]].

---

## Frozen-state ground truth

`git diff cf0d6cc5 HEAD` over the full presence artifact set is **empty**. The spec (722 lines), CHANGELOG, all 12 schema files, the schema-dir README, and the 14 conformance scenarios are byte-stable **26 days** since C128 (`cf0d6cc5`, 2026-07-02) and **35 days** since the last *spec* edit (C89 `0beb1b93`, 2026-06-23). Re-confirmed at HEAD:

- **12** `*.schema.json` (`v0/common`×3 + `v0/tools`×8 + `v1/tools`×1) — unchanged.
- **14** conformance scenarios, `P0-001..P0-010` + `P1-001..P1-004` — unchanged.
- `decision` enum = `["allow","deny","warn"]` in **both** the v0 and v1 `hestia_query_policy` schemas (`:27` in each) and in spec §3.4 (L278) + §5.4 (L531). Three values. **No `escalate`.**
- `status` enum (v1 schema `:53`) = `["decided","evaluating"]`, `default: "decided"`.

Because the target is byte-identical to its C236/C198/C160-audited state, every prior verdict **HOLDS by construction**. This is the **seventh consecutive delta on a frozen target**.

---

## Headline

**Seventh consecutive delta with zero net-new findings against the spec. The pass's value is subtractive: its own flagship was built, stress-tested, and killed — by the spec's meta-structure and by an uncited precedent in this corpus.** Two INFO carried, both explicitly folded into already-routed findings; one new LOW routed to the proposal authors; **zero mutation**.

The window supplied the most authoritative inbound this file has ever seen — an **operator-authored factual correction about the behaviour of the very gate this spec specifies**, verified against primary sources and re-held a day later:

- **`b2e28887`** (dp, 2026-07-27) corrected whitepaper §11, which had credited hestia with *"fail-closed defaults for unattended operation."* Verified against hestia's `GATE_BYPASS_CATALOG.md` §11, the hook, and a live-host record, the published posture is **"fail-open unless a deployment explicitly configures it closed."**
- **`97c9eb21`** (dp, 2026-07-28) ran the watch item that opened, corrected two further §11 claims, and states verbatim: *"Held, no edit: … and the 07-27 hestia paragraph."*

`presence-protocol.md` contains **zero** occurrences of `fail-open`, `fail-closed`, `unreachable`, `unavailable`, or `no verdict`. The audit's flagship candidate (**N1-CANDIDATE**) was that this silence is an *evidence gap* under ratified LCT §1.2: a conforming presence layer could hold either posture and a relying party could not tell which.

**It does not survive.** Three independent facts kill it, all verified at HEAD:

1. **The wire makes verdict and no-verdict mutually exclusive and both explicit.** The v1 `hestia_query_policy` output schema is `required: ["decision","reason","enforced"]`, `additionalProperties: false`, `decision` closed to three values — and §7 `:668-673` makes the Schemas **normative over prose** for wire shape. A daemon cannot manufacture a verdict it does not hold; it returns a verdict, or the `_hestia_error` envelope the SDK MUST raise as a typed exception (§7 `:664-665`). The relying party *can* tell.
2. **The spec attaches no caller obligation to *any* verdict — including `deny`.** Grep-verified across 722 lines: the only orchestrator-directed normatives are `:97` (SHOULD NOT refuse the session), `:293` (SHOULD wait `nextPollMs`), `:298` (SHOULD bound the re-poll budget). `:290` reads *"the orchestrator **can** act on `decision`."* There is no MUST-honor-`deny` anywhere. So the absent obligation on `internal_error` is not a missing cell — it is a **uniformly and deliberately empty column**, which is what §1.2 requires: presence emits inspectable evidence, the relying party decides. A finding that convicted this cell would equally convict all ten error codes and all three decision verbs.
3. **The corpus already adjudicated this exact question-class, and the audit missed it.** **C123 NEW-1** (`docs/audits/C123-reputation-computation-3rd-delta-2026-07-01.md:84-91`) ruled that a spec clause *mandating* fail-closed was itself the defect; the ratified remedy was **descriptive** — describe the reference implementation's actual fail-open behaviour — with *"whether the SDK should be tightened to fail-closed … an SDK-behavioral/security **operator decision**, not an autonomous spec turn."* That precedent points to INFO in descriptive form, not a MEDIUM against the spec.

**Two auditor errors are recorded rather than quietly corrected** (§B.1.3): a miscitation of `internal_error`'s definition, and an internal inconsistency between the flagship and this same audit's own I-1.

**§A**: frozen ⇒ C128 ledger COMPLETE + 6/6 claims TRUE · C89 4/4 HELD across all six `vault_denied` mirrors · 13/13 C5 + 5/5 C38 HELD · C88-5 R6Action still INFO · **C127-1 re-verified STILL OPEN at HEAD** · **C198 B.2 STANDS**, trigger evaluation corrected (§B′.3).
**§B**: **0 net-new against the spec** · 1 LOW routed to proposal authors (I-2) · 2 INFO folded into C272-N1 and C274-N1 · 1 INFO residue from the killed flagship (§8 drift-table row) · 3 candidate charges refuted by gates · mirror gate **NEGATIVE for a 7th time** over a **corrected** surface.

---

## §A — Delta Verification (frozen target)

- **A.1 — C128 remediation (README known-gap ledger).** File unchanged since C128 ⇒ the schema-less set `{Session, R6Action, VaultEntry, society/state}` and the README's four matches (with the two traps correctly omitted: Outcome §5.3 bound by `record_outcome` **input** `$defs`; PolicyResult §5.4 bound by v1 `query_policy` **output**) are byte-stable ⇒ **still COMPLETE, all 6 factual claims still TRUE**.
- **A.2 — C89 four (C88) findings + six-mirror `vault_denied`.** Re-grepped at HEAD, not inherited: `vault_denied`/interactive-approval is uniformly "reserved for v2+" across all six sites (§3.5 `:337`, `:339`, `:344`; §3.6 `:352`; §6.1 `:626`, `:637-640`; §8 `:692`). The §6.1 footer still names exactly `policy_denied` + `invalid_role` as `(v1+)`. **4/4 HELD.**
- **A.3 — C5 / C38 / C88-5.** No edit site ⇒ **13/13 C5 + 5/5 C38 HELD**; C88-5 R6Action §5.2 (`:490`, `toolName` at `:495`) still **INFO**.
- **A.4 — C127-1 cross-track carry (re-verified live, not assumed).** `ls web4-standard/schemas/presence-protocol/v0/common/` returns exactly `error_envelope`, `trust_state`, `witness_entry` — **no `Session`, no `VaultEntry`**. `grep "session/own\|vault/"` over the conformance JSON = **0**. Both halves **STILL OPEN**. Route, do NOT self-apply.
- **A.5 — C198 B.2 escalate-mapping carry.** **STANDS**, with its trigger evaluation corrected (§B′.3) rather than inherited.

**Recorded-path drift check**: every §A anchor above was re-grepped at live HEAD rather than copied from C236.

---

## §B — Fresh Findings

### B.0 — Window enumeration (METHOD CARRY v2 applied)

The window `fe110ef9..HEAD` (2026-07-20 → 2026-07-28) is ~40 commits; most are the C-series' own audit landings and are self-evidently disjoint. Asking *what landed that claims authority over the target's subject matter* rather than *which sibling spec changed*, five artifacts qualify:

| Artifact | Claim over presence's subject matter | Disposition |
|---|---|---|
| `b2e28887` + `97c9eb21` (dp, whitepaper §11) | States, then re-holds, the **published posture of the gate this spec specifies** | **→ N1-CANDIDATE, KILLED** (§B.1); INFO residue |
| `954ee391` (#580, proposal) | "**Absence NEVER grants**" | → **I-1, folded** into C272-N1 |
| `4665a430` (#579, proposal) | Failure 3 = hestia's scope gate advertising a `request_scope` that does not exist | → **I-2** (LOW, venue correction) |
| `752eadde` + `780af6ef` (AAEP PRD + hub strategy) | Action→Decision→Evidence triple | **REFUTED as net-new** — folds to C274-N1 |
| `206dd004` (CI boundary) | Rust workspace has never run a test in CI | **REFUTED** (§B.4 Gate 1) |

Hub movers `5c2dd39f`, `1fc873d1`, `9aedd2b7` gated individually: each is hub-daemon society/ledger code; `grep` for any presence tool token = **0**. No referent, no carry.

---

### B.1 — FLAGSHIP, BUILT AND KILLED: "the spec of a gate is silent on its no-verdict posture" (REFUTED — demoted to a one-row INFO)

**The candidate.** presence is the standard-side spec of hestia's inward MCP gate. `grep -nE "fail-open|fail-closed|unreachable|unavailable|no verdict"` over it = **0 hits**. Two loci were proposed: (1) §3/§6.1 define `hestia.internal_error` but attach no caller obligation to it; (2) §3.4.1 `:298-300` tells orchestrators to *"fall back to a local heuristic if the engine never settles."* With `b2e28887`/`97c9eb21` supplying twice-held operator evidence that the implementation's posture is fail-open, the charge was that a relying party cannot read the posture from the standard — an *evidence* gap under LCT §1.2, deliberately **not** a demand that the gate fail closed.

It was the most attractive finding in the window, and it is wrong.

#### B.1.1 — The three refutations that hold

**R-A — The "cannot tell which" claim is false at the wire.** `web4-standard/schemas/presence-protocol/v1/tools/hestia_query_policy.schema.json` output: `"required": ["decision","reason","enforced"]`, `"additionalProperties": false`, `decision` enum closed to `["allow","deny","warn"]`. `v0/common/error_envelope.schema.json`: `"required": ["_hestia_error"]`, `additionalProperties: false`. §7 `:668-673` makes the Schemas normative **over prose** for wire shape, and §7 `:664-665` obliges the SDK to unwrap `_hestia_error` into a typed exception. A conforming daemon therefore has exactly two expressible replies — a verdict from a closed enum, or a typed error — and cannot return an absent or null `decision`. Verdict, no-verdict, and no-response are three mutually distinguishable outcomes. **That is unforgeable, inspectable evidence, which is precisely what §1.2 asks for.** The finding's load-bearing sentence fails at the level where relying actually happens.

**R-B — The empty column, not the empty cell (the decisive one, and the auditor did not state it).** Grep-verified across all 722 lines: the only orchestrator-directed normatives are `:97` (*"SHOULD NOT refuse the session"*), `:293` (*"SHOULD wait `nextPollMs`"*), `:298` (*"SHOULD bound their total re-poll budget"*). And `:290` reads *"the verdict is final; the orchestrator **can** act on `decision`."* **Nowhere does the spec oblige an orchestrator to honor `decision: "deny"`.** The four §7 SDK MUSTs are wire-fidelity duties (expose a constant, warn on mismatch, unwrap the envelope, pass the vectors), not enforcement duties. So the absence of a caller obligation on `internal_error` is not an omission in one place — it is the spec's **uniform and deliberate scope**: presence emits evidence; the relying party decides. This also breaks the auditor's own R1 rebuttal on its own terms: a version mismatch is about whether to **speak the protocol** (inside the two-party wire contract, so the spec regulates it), whereas a verdict is about whether to **run a tool** (outside it, so the spec regulates none of it). If the candidate were sound it would convict all ten error codes and all three verbs.

**R-C — Uncited governing precedent: C123 NEW-1.** `docs/audits/C123-reputation-computation-3rd-delta-2026-07-01.md:84-91` found that `reputation-computation.md` §4's *fail-closed* SHOULD contradicted the SDK's fail-open `matches()`, and ruled **the fail-closed mandate itself** the defect. The ratified remedy was **descriptive** — make the spec describe the implementation's actual fail-open behaviour — with the tightening question explicitly *"an SDK-behavioral/security **operator decision**, not an autonomous spec turn."* The corpus has already answered this question-class, and its answer is descriptive prose plus a routed operator question. That is INFO-shaped.

#### B.1.2 — Arms that partially succeed, and one that was over-claimed

- **Locus 2 folds, and should never have been counted inside the finding.** §3.4.1 `:302-303` — *"A v1 daemon with a synchronous rule engine always returns `status: \"decided\"`"* — makes the exhaustion path **unreachable in v1**. Its trigger surface (a not-yet-landed v1.x asynchronous engine) is identical to the standing **C198 B.2** carry. Under the standing fold rule it is **absorbed into C198 B.2**, not counted.
- **The `internal_error` arm is weaker than the candidate claimed** — see B.1.3.
- **The whitepaper bridge does not reach the wire spec.** §7 binds exactly two roles: *"A conforming presence layer implementation MUST"* (`:648`, the daemon) and *"A conforming **SDK** implementation MUST"* (`:658`, the wire adapter). The fail-open default `b2e28887` documents lives in a Claude Code hook — a *client application* of the SDK, which is neither role. (Recorded as the adversarial pass's arm; **not independently verified here**, since hestia is out of repo and out of scope by binding condition. The finding falls on R-A/R-B/R-C without it.) There is also an inversion worth stating: the whitepaper's own correction says *"a gate that **declares** itself safe hands the relying party no evidence,"* and `b2e28887`'s body identifies the defect as *"accepting a **declared** safety property."* The candidate's remedy was "declare the posture" — the very evidence class that correction demoted. The corpus already chose this evidence's venue, and it is hestia's bypass catalogue, not the wire spec.

#### B.1.3 — Two auditor errors, recorded

1. **Miscitation.** The candidate cited `:177` (*"`hestia.internal_error` — connection setup failed"*) as the definition of the error code. It is not: `:177` is the **§3.1 `hestia_connect` per-tool gloss**, scoped to connect. The registry definition is §6.1 `:632` — *"`hestia.internal_error` | daemon | **Catch-all**; the `message` field carries detail."* A catch-all plus a mandatory typed-exception raise **is** an error semantic for a failed evaluation, so R2 should have been conceded further than it was. This is the [[feedback_prior_finding_path_provenance]] class of error committed on a *new* finding rather than a carried one — the citation was read from the nearest hit rather than from the defining table.
2. **Internal inconsistency.** The candidate asserted "no field expresses non-settlement," while this same audit's **I-1** (§B.2) cites `enforced` (`:533-535` — *"true when the policy engine actively blocked or allowed the action (vs. **a default pass-through**)"*), `ruleId`/`ruleName` `null` on default paths (`:278-281`), and `status`'s tentative-verdict semantics (`:296-297`) as machine-readable evidence of exactly that. Both cannot be true. **I-1 is right and the flagship was wrong**; `{status, enforced, ruleId}` is a three-field readable channel for "this is not a settled, rule-backed verdict."

There is also a **method inconsistency** the adversarial pass caught: the candidate used #580's *"Exhaustion MUST be reported"* as the yardstick convicting §3.4.1, while §B.2 simultaneously argues #580's authority is prospective and its precedent survey incomplete. A proposal cannot be unratified in one section and normative against a byte-frozen ratified spec in another. The METHOD CARRY v2 corollary forbids exactly this, and it was violated.

#### B.1.4 — What survives: INFO (LOW), descriptive form

> **§8 "Implementation drift"** (`:682-695`) — a table that exists, in its own words, *"because the discipline is only as good as the honesty about where it isn't yet held"* — carries **no row** recording the reference orchestrator stack's no-verdict posture, now published and twice-held by the operator (`b2e28887`, `97c9eb21`).

That is a **one-row descriptive omission in a drift table, not a normative defect** — and it is precisely the C123-idiomatic shape: describe what the reference implementation actually does, and route the "should it change" question to the operator. **Not auditor-applicable** (the spec is byte-frozen and the row's content is an operator-owned factual claim about an out-of-repo implementation). Route as INFO alongside C198 B.2.

---

### B.2 — **I-1 (INFO — explicitly NOT net-new; folds into C272-N1): presence is the third witness to #580's incomplete precedent survey, and `web4-policy` is a fourth.**

#580 `:86` — *"Defaults resolve conservatively with respect to capability. **Absence NEVER grants**"* — is presented as generalizing something *"already canon in two places."* **C272-N1** already charged that survey with omitting a ratified counter-example (`reputation-computation.md` §4 fail-open delegation), and **C274 I-1** added acp as a second witness while explicitly not counting it net-new. Presence supplies a third, and a fourth in passing:

- presence §2 `:73-74` (v0 *"default-allow policy stub"*), §5.4 `:533-535` (`enforced` distinguishes an active decision from *"a default pass-through"*), §3.4 `:278-281` (`ruleId`/`ruleName` `null` on the default path). Absence of a matching rule **grants**.
- `web4-policy/src/lib.rs:758` — the ratified Rust policy crate's own test is `fn no_norms_default_allow()`: an empty law evaluates to `Decision::Allow`.

**Not counted net-new**: same charge, same target document, third and fourth witnesses. Travels with **C272-N1**. Its only added value is a change in kind — with four ratified/implemented sites, "absence grants" is less plausibly a survey omission than a **systemic corpus posture** #580 must contend with. Offered as weight on an existing routed finding.

---

### B.3 — **I-2 (LOW — route to the proposal authors): both new proposals locate the `request_scope` gap in "the implementation," but the tool surface is closed by this ratified spec — the correction is one of venue, not feasibility.**

`grep -rn "request_scope"` corpus-wide returns **only** the two window proposals (plus an unrelated `request_scope_change` in `simulations/`):

- #579 Failure 3: *"There is no `request_scope` tool and no grant-issuing endpoint anywhere **in the implementation**."*
- #580 `:112-116`: *"…it hard-fails instead **because nobody built the mechanism**."*

The surface in question is `hestia_vault_get`'s scope check — presence §3.5, denial path `hestia.vault_scope_mismatch` (`:343`, `:628`) — and presence §3 `:132-133` closes the tool surface normatively: *"The **eight** tools below MUST be implemented by a conforming presence layer."* `grep "presence-protocol\|hestia_"` over both proposals and the AAEP PRD = **0 in both directions**.

**Deflated deliberately per the governance-tier check** ([[feedback_read_the_specs_meta_structure]]): §2 `:82-84`'s version bump is the mechanism the spec **provides** for tool addition, not a bar it erects. The accurate, small statement:

> A `request_scope` tool is a **standard-side addition** governed by presence §2/§3, not an implementation oversight. Building it in hestia alone would put the reference implementation out of conformance with the 8-tool MUST-list. The proposals' remediation is routed to the wrong venue — at a cost of one governed version bump, which is cheap and already specified.

Same *shape* as C274-N1 (a gap mis-stated as an absence when it is a non-join with a ratified artifact) but a **distinct instance**: different proposals, different missing referent, different blocker class (a governance MUST-list vs a JSON-Schema `additionalProperties:false` pin). Scored LOW because the deflation removes most of its bite. Route to the proposal authors; **do NOT self-apply** — the proposals are under fleet review and their authority is prospective.

---

### B.4 — Gates run that came back clean and killed candidates (subtractive)

**Gate 1 — §7's conformance-vector MUST vs zero executors. REFUTED.**
`grep -rl "presence-protocol-conformance"` across `*.py`, `*.rs`, `*.ts`, `*.js`, `*.yml` = **0**; no conformance job in `.github/`. That resembles C270-N2 ("cross-language test vectors enforce them" — unbacked). **It is not.** Reading the enforcement mechanism the spec actually names: §7 `:648`, `:655-656` — *"A conforming presence layer **implementation** MUST: … Pass the conformance test vectors."* The burden sits on the conforming implementation (the hestia daemon, out of repo). The spec makes **no** claim that anything here executes them. C270-N2 required a spec *asserting a state of affairs*; presence states an *obligation on the implementer*. Obligation ≠ claim of enforcement. Correctly-scoped negative — not a finding, and not routed as corpus-wide INFO either; `206dd004` drew that boundary at the operator level.

**Gate 2 — the AAEP triple. REFUTED as net-new; folds to C274-N1.**
`hestia_begin_action` → `hestia_query_policy` → `hestia_record_outcome` (§1.2 `:51-52`, §3.2-§3.4) is arguably the Action-Request → Policy-Decision → Result-Evidence triple at the host-MCP layer, and the AAEP PRD cites presence exactly as much as it cites acp (`grep` = 0 for both). Object-model test: does it name an object or property C274-N1's table does not already cover? **No** — "also the triple, also unattributed, also uncited" is the same charge with a second witness. Per C274's handling of its own I-1, **not counted net-new**; travels with C274-N1. Recorded so the next delta does not rediscover it.

**Gate 3 — the flagship itself.** See §B.1. Killed by R-A/R-B/R-C.

---

## §B′ — SDK / consumer mirror gate (NEGATIVE for a 7th time — over a **corrected** surface)

Re-derived at live HEAD including crates not gated at C236 (`web4-policy/`, `web4-trust-core/`):

| Token | Files at HEAD (excl. `simulations/`, `archive/`) |
|---|---|
| `query_policy`, `hestia_connect`, `hestia_begin_action`, `hestia_record_outcome`, `hestia_vault_get`, `nextPollMs`, `status.*evaluating` | **0** |
| `PolicyResult` | 1 — `archive/reference-implementations/mrh_policy_scoping.py` (archived sprawl, not a mirror) |

**Gate NEGATIVE — still no presence-protocol twin in Rust or Python.** Three adjudications correct or extend C236's record:

**B′.1 — `HestiaCallbackSigner` (`hub/hub-lib/src/signer.rs`) — NOT net-new; C236's token list structurally could not surface it.**
`grep -rnE "hestia_" --include=*.rs` at HEAD returns `hub/hub-lib/src/{signer,init,hub}.rs`. C236's list (`query_policy|hestia_connect|hestia_begin_action|nextPollMs|PolicyResult|hestia_record_outcome`) contains no token this file carries. **Snapshot-presence guard applied**: born `fdd48587` (2026-06-07), six weeks *before* the C236 snapshot ⇒ not a window finding. Adjudication: a vault **signing callback** over HTTP (hub → hestia `/sign-request` → `SignResponse::{Approved,Denied}`), **not** the presence MCP tool surface. Gate stays NEGATIVE.

The two hub paths are kept distinct because they are different kinds of evidence:
- `signer.rs:674` (`hestia_callback_unreachable_url_errors_transport`) — hestia unreachable ⇒ `SignError::Transport`. The consumer **errors out**; no signature is produced. Fail-closed *in effect*, but a **transport error, not a denial**.
- `signer.rs:378-415` (`LockedSigner`) — a locked **hub** vault denies every key op, documented in-source as *"fail-closed."* A genuine **policy denial**, and it is the hub's own vault, not hestia's.

Precisely: the hub's Rust consumer **errors out** when hestia is unreachable, while the MCP gate's published posture on no verdict is to **proceed**. That contrast is real and worth recording — but per §B.1 it is *not* a spec defect, because presence deliberately imposes no caller obligation on any verdict. Context, **not a finding**.

**B′.2 — `web4-policy` — CONSUMER/sibling engine, NOT a presence mirror.**
`web4-policy/src/lib.rs` carries `Decision::{Allow, Warn, Deny, Escalate}` — presence's three values plus a fourth — and names hestia at `:11` and `:233`. Still not a mirror: it evaluates **society law** (YAML norms over `R6Request` selectors, priority arbitration), whereas presence §1.2 `:59-63` specifies a host-local engine with *"four built-in presets … active preset stored inside the vault."* Different inputs, arbitration, and storage. The crate adjudicates the collision itself at `:169` — *"gate `warn` is first-person pre-act and **stays disjoint**"* — and its hestia reference at `:233` is to the **hestia constellation** (device MFA), not the MCP gate. Same lexical-collision class C236 B.2/B.3 refuted. **No carry.**

**B′.3 — C198 B.2's trigger evaluation, corrected.**
C236 recorded the carry as dormant because *"no v1.x LLM-backed engine has landed."* Precisely: none has landed **in the presence daemon** — while the corpus ships a ratified Rust policy crate whose `Decision` enum carries `Escalate` and whose stated consumers include hestia. `web4-policy` last moved `cb788768` (#525), **predating the C236 snapshot** ⇒ not net-new, and it is not the presence engine today. But it is a named candidate, so the carry moves from "dormant, nothing to check" to "dormant, re-check this crate each delta." The obligation is unchanged and still not a present-tense defect. **Locus 2 of the killed flagship is absorbed here.**

---

## Remediation Grouping (for the next presence turn)

| Cluster | Findings | Shape |
|---|---|---|
| **(autonomous)** | — | **Zero net-new against the spec.** The next presence remediation turn is a genuine **no-op**. |
| **(operator, NEW — INFO/LOW)** | §8 drift-table row | §8 `:682-695` carries no row for the reference orchestrator stack's no-verdict posture, now operator-published and twice-held (`b2e28887`, `97c9eb21`). Descriptive, C123-idiomatic. **Not auditor-applicable** — the spec is frozen and the content is an operator claim about an out-of-repo implementation. |
| **(proposal authors, NEW — LOW)** | **C276 I-2** | `request_scope` is a standard-side addition governed by presence §2/§3, not an implementation oversight. Deflated: the version bump is the provided mechanism, not a bar. |
| **(travels with C272-N1 — NOT net-new)** | **C276 I-1** | presence + `web4-policy:758` are the 3rd and 4th ratified "absence grants" witnesses. Weight on an existing finding. |
| **(travels with C274-N1 — NOT net-new)** | Gate 2 | presence's `begin_action`→`query_policy`→`record_outcome` is a second AAEP witness. |
| **(cross-track, STANDING)** | **C127-1** | Author `Session`/`VaultEntry` schemas under `v0/common/` + 2 `resources/read` vectors. **Re-verified STILL OPEN** (§A.4). |
| **(operator/cross-track, STANDING from C198)** | **C198 B.2** | `escalate` → `{decision, status}` mapping, owed when a v1.x asynchronous engine lands. STANDS; trigger evaluation corrected; **absorbs locus 2 of the killed flagship**. |

No operator **DESIGN-Q** blocks the current spec.

---

## Guard for the next presence delta (~C312)

- Target expected **byte-frozen** at blob `6414a7fe` (baseline `cf0d6cc5`). 12 schemas / 14 vectors / 3-value `decision` / 2-value `status`.
- **DO NOT resurrect the no-verdict-posture charge as a spec defect.** It was built, stress-tested and killed at C276 by three verified facts: the output schema is `required`+`additionalProperties:false` with a closed enum (verdict and no-verdict are mutually exclusive and both explicit); the spec imposes **no** caller obligation on *any* verdict including `deny` (`:290` "can act on"; only orchestrator normatives are `:97`, `:293`, `:298`); and **C123 NEW-1** already ruled a fail-closed mandate itself the defect with a descriptive remedy. Only the §8 drift-table row survives, as INFO.
- **Do NOT re-open as net-new**: `HestiaCallbackSigner` (`fdd48587`, pre-C236); `web4-policy`'s `Escalate` and `no_norms_default_allow` (`cb788768`, pre-C236); the AAEP triple (→C274-N1); the "absence grants" witness (→C272-N1); the §7 conformance-vector/zero-executor gate (refuted — §7 places the burden on the implementer).
- **Trigger re-check for C198 B.2**: has `web4-policy` (or a successor) become the presence daemon's engine? If yes, the escalate-mapping carry becomes present-tense — and locus 2 of the killed flagship (§3.4.1's unrecorded fallback) becomes live with it.
- **Method**: C236's gate token list was incomplete. Derive the consumer set from `grep -rnE "hestia_"` across **all** languages first, then narrow — never reuse a prior delta's token list as if it were the surface ([[feedback_enumeration_and_grep_hypotheses]]).
- **Method**: read the **defining table** (§6.1) for an error code's semantics, not the nearest per-tool gloss (§3.x). C276 got this wrong on `internal_error` (§B.1.3).

---

## Cross-Cutting Observation

**The window handed this file the most authoritative inbound in its lineage, and the correct output was still zero.** Five consecutive fires have now shown that on a long-frozen target the target is the least informative artifact in its own audit — C268 a canonized principle, C270 an operator ruling, C272 a proposal answering the file's own open question, C274 a PRD restating its domain as a gap, and C276 a **fifth variant that looked strongest of all**: an operator-authored factual correction, verified against primary sources and re-held on a second pass, about the behaviour of the very gate this spec specifies. That variant genuinely does route differently — a whitepaper correction proposes nothing, so there is no precedent survey to charge, and it supplies *settled evidence* rather than prospective authority, which is the one ingredient that could let a finding land as a spec-side gap. The inference from "strongest inbound" to "therefore a finding" is the trap, and this pass walked into it before walking back out.

**What killed it is worth more than what it claimed.** The candidate asked "does the spec say what happens when there is no verdict?" and found silence. The right question — reachable only by reading the spec's *meta-structure* rather than its subject matter — was "**does this spec attach a caller obligation to any verdict at all?**" It does not. `:290` says the orchestrator *can* act on a decision; there is no MUST-honor-`deny` in 722 lines. Once that is visible, the silence stops being a hole and becomes the shape of the thing: presence emits inspectable evidence and leaves the decision to the relying party, which is exactly what ratified LCT §1.2 requires and exactly what C268-N1 convicted `multi-device-lct-binding` for *failing* to do. The candidate would have punished this spec for getting right what its sibling got wrong. **A uniformly empty column read as a single missing cell** — that is the generalizable lesson, and it is a new one for this corpus.

Two further disciplines earned their keep. **Refuting the flagship rather than the leftovers** worked for the fourth consecutive fire, and this time the refutation surfaced an *uncited in-corpus precedent* (C123 NEW-1) that had already adjudicated the whole question-class a month earlier — a reminder that the ledger's blind spot is not only forward (unpromoted carries) but backward (pre-rotation audits nobody re-reads). And **asking "is it NEW?" before "is it TRUE?"** removed two more MEDIUMs that were both true: presence is a third witness to #580's survey gap and a second witness to the AAEP non-join. Three attractive MEDIUMs, all true or plausible, none new or sound. The honest output of this pass is a one-row drift-table note and a venue correction — and the audit that found nothing is the one that read the spec correctly.
