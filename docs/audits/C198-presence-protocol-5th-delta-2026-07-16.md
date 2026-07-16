# C198 — presence-protocol.md Fifth Delta Re-Audit

**Date**: 2026-07-16
**Auditor**: autonomous web4 session (legion, C-series **C198**, slot web4-20260716-000036)
**Subject**: `web4-standard/core-spec/presence-protocol.md` (722 lines, 9 sections), v1 Draft
**Baseline**: `docs/audits/C160-presence-protocol-4th-delta-2026-07-08.md` (4th delta). C160 found **zero net-new** findings; its only note was a documentation-hygiene correction (schema count 12, not the "13" the C127 doc miscounted).
**Lineage**: C5 (`presence-protocol-internal-consistency-2026-05-17.md`, 13 findings) → C38 (#284/#285) → C88 (#379) → C89 (#380) → C127 (audit) → C128 (#439 `cf0d6cc5`, remediation) → C160 (4th, audit) → **C198** (this, 5th, audit).
**Companion artifacts cross-checked**: `presence-protocol-CHANGELOG.md`; all **12** JSON Schemas under `web4-standard/schemas/presence-protocol/{v0/common,v0/tools,v1/tools}` + the schema-dir `README.md`; `web4-standard/testing/conformance/presence-protocol-conformance.json` (**14** scenarios, P0-001..P0-010 + P1-001..P1-004); filesystem ground-truth at live HEAD.
**Scope**: Internal-consistency + **inbound-carry** 5th-delta re-audit. The presence artifact set is **byte-frozen since C128 (`cf0d6cc5`)** — `git diff cf0d6cc5 HEAD` over `{presence-protocol.md, CHANGELOG, all 12 schemas, README, conformance.json}` is **empty**. So §A = verify the frozen state and re-confirm C160/C89/C5/C38/C88-5/C128 findings hold by construction. **The genuinely new surface this delta is external**: the **W4IP governance-vocabulary landings** (#521 `767eb564`, #522 `87377c38`, #523 `1354e4c2`, #525 `cb788768`) merged into sibling core-spec files *after* C160. The flagship question this delta uniquely answers: **does presence's policy `decision` enum drift against the now-ratified 4-verb law-engine vocabulary?** **Does NOT patch anything** — remediation, if any, is the next alternation turn (C199).
**Instrument**: Lead-context mechanical verification (empty-diff freeze proof, schema/vector counts at live HEAD, decision-enum extraction from spec + both query_policy schemas, cross-repo grep for a presence twin) + refute-by-default adjudication of the W4IP inbound, run as an **independent** layer-split test (NOT imported from the C196/acp verdict, per the policy-review method guard). Per [[feedback_refute_your_best_finding]], [[feedback_cross_doc_carry_inbound]], [[feedback_prose_is_not_ledger]], [[feedback_enumeration_and_grep_hypotheses]].

---

## Frozen-state ground truth

`git diff cf0d6cc5 HEAD` over the full presence artifact set is **empty**. The spec (722 lines), CHANGELOG, all 12 schema files, the schema-dir README, and the 14 conformance scenarios are byte-stable **~14 days** since C128 (`cf0d6cc5`, 2026-07-02) and ~18 days since the last *spec* edit (C89 `0beb1b93`). Ground-truth re-confirmed at HEAD:

- **12** `*.schema.json` files (`v0/common`×3 + `v0/tools`×8 + `v1/tools`×1) — matches C160's corrected count.
- **14** conformance scenarios, ids `P0-001..P0-010` + `P1-001..P1-004` — unchanged.
- `decision` enum = `["allow", "deny", "warn"]` in **both** the v0 and v1 `hestia_query_policy` schemas (`:27`) and in spec §3.4 (L278) + §5.4 (L531). Three values. **No `escalate`.**
- `status` enum (v1 query_policy schema `:53`) = `["decided", "evaluating"]`.

Because the target is byte-identical to its C160-audited state, every C160/C89/C5/C38/C88-5/C128 verdict **HOLDS by construction** — there is no edit site that could regress one. §A below records the verification; the audit's *value* this delta is entirely in §B's inbound-carry adjudication.

---

## Headline

**Zero net-new autonomous findings. The presence policy `decision` enum's 3-value vocabulary `{allow, deny, warn}` does NOT drift against the W4IP-ratified 4-verb law engine `{allow, warn, deny, escalate}` — it is CLEAN-BY-LAYER, adjudicated independently of the acp/C196 precedent.** The two engines are deliberately partitioned:

- **hub-law engine** (`web4-policy/src/lib.rs::Decision`, transcribed into `hub-law-schema.md §2` by #521) is the **society-governance** law oracle. Its `escalate` verb means *"block pending a **higher authority's** decision (default `escalate_to: sovereign`)"* — a construct that **presupposes a society with a Sovereign role** to escalate to.
- **presence `hestia_query_policy`** is Hestia's **inward-MCP tool-gate**: a host-local, per-tool-call pre-action check on a single daemon's MCP surface, driven by "4 built-in presets" (§3.4). In that context **there is no sovereign in scope** to escalate to, so the hub-law `escalate` verb has no referent.

Presence does model deferral — but as an **orthogonal axis**, not a decision verb: the `status ∈ {decided, evaluating}` "wait protocol" (§3.4.1) with `nextPollMs`, explicitly *"reserved for future v1.x engines that consult an LLM-backed policy entity or external attestation service."* hub-law folds *defer* into the decision enum (`escalate`); presence factors it out into `status`. Both are legitimate; neither claims to mirror the other. **Presence nowhere asserts its `decision` enum equals the `web4-policy` `Decision` enum**, and the #521 "Decision semantics" note explicitly scopes itself as a *sync surface for `web4-policy/src/lib.rs`* — a claim about the society law engine, not about the Hestia MCP gate. The refutation survives: to be a drift, presence would have to *claim* the mirror; it does not. This is the same **layer-split** outcome as C196/acp, reached by presence's own construction rather than by importing acp's verdict.

**SDK/Rust-mirror gate = NEGATIVE.** There is **no** presence-protocol twin in `web4-core/src/*.rs` or the Python SDK: the `presence` token in web4-core (`lib.rs`, `lct.rs`) is **LCT witnessed-presence** (non-transferable presence *tokens*) — a different concept — and `record_outcome` in `act.rs` is the **T3/V3 trust act**, not the presence `hestia_record_outcome` MCP tool. Grep for `query_policy` / `hestia_connect` / `PolicyResult` / `nextPollMs` across web4-core = **empty**. The presence protocol is Hestia's inward MCP surface, implemented in the hestia daemon (other/private repo), which this audit does not cross-compare. The SDK-mirror lens that yielded net-new findings for reputation (C194-N1), t3-v3 (C192), and mcp (C188) **does not apply to presence** — there is nothing in the tracked mirror to diverge.

**One INFO (forward-compat, not a current defect):** when a v1.x presence engine actually consults a PolicyEntity/PolicyGate that wraps the `web4-policy` law engine (the future §3.4.1 anticipates), that engine *can* emit `escalate`. Presence will then need a documented **mapping** (hub-law `escalate` → presence `{decision, status}`). This is a v1.x design question, not a v1 artifact defect, and is recorded for the operator/cross-track — **do NOT self-apply**.

**§A: frozen (empty diff since C128) ⇒ C128 ledger COMPLETE + 6/6 claims TRUE · C89 4/4 HELD across 6 mirrors · 13/13 C5 + 5/5 C38 HELD · C88-5 R6Action still INFO · C127-1 cross-track facet STANDS as a routed carry. All by construction (byte-identical).**
**§B: W4IP decision-vocab inbound = CLEAN-BY-LAYER (independently adjudicated) · mcp §7.8 mailbox = distinct async surface, no carry · SDK-mirror gate NEGATIVE · 0 net-new autonomous findings · 1 forward-compat INFO routed.**

---

## §A — Delta Verification (frozen target)

The presence artifact set is byte-identical to its C160-audited state (`git diff cf0d6cc5 HEAD` empty). Therefore:

- **A.1 — C128 remediation (README known-gap ledger).** File unchanged since C128. C160 re-derived the complete schema-less set `{Session, R6Action, VaultEntry, society/state}` from ground truth and confirmed the README's four match exactly, with the two traps (Outcome §5.3 bound by `record_outcome` **input** `$defs`; PolicyResult §5.4 bound by v1 `query_policy` **output**) correctly omitted. No byte moved ⇒ **still COMPLETE, all 6 factual claims still TRUE**. No regression.
- **A.2 — C89 four (C88) findings + six-mirror `vault_denied`.** File byte-identical ⇒ `vault_denied`/interactive-approval still uniformly "reserved for v2+" across all six sites (§3.5 L337-339, L344-345; §3.6 L351-352; §6.1 L626, L634-642; §8 L692); the §6.1 `(v1+)` footer still names exactly `policy_denied` + `invalid_role`. **4/4 HELD.**
- **A.3 — C5 / C38 / C88-5.** No edit site ⇒ **13/13 C5 + 5/5 C38 HELD**; C88-5 R6Action §5.2 still **INFO** (documentary struct, `toolName` absent from `begin_action` output, no wire-carrier claim).
- **A.4 — C127-1 cross-track facet (standing carry).** Unchanged — C128 applied only the autonomous README facet; the cross-track facet (author `Session`/`VaultEntry` JSON Schemas under `v0/common/` + 2 `resources/read` vectors for `session/own`, `vault/{name}`) **STANDS** as an open cross-track judgment call. Do NOT self-apply.

**Inbound-carry surface (§B territory, but checked for §A regressions):** the sibling core-spec files that churned since C128 are all W4IP-vocabulary / hub-law / reputation / mcp landings (#521-#525, #526, `3e765345`, `d1759397`, `6b66c949`). None edits presence; none routes a carry *back* into presence's ledger. Whether any of them creates a *new* consistency obligation for presence is the §B flagship.

---

## §B — Fresh Findings

**None (0 net-new autonomous). One forward-compat INFO. Flagship refuted clean-by-layer.**

### B.1 — FLAGSHIP: W4IP decision-vocabulary inbound → presence `decision` enum (REFUTED — clean-by-layer)

**Candidate (strongest):** W4IP Phase 0 (#521 `767eb564`) ratified the live law engine's decision vocabulary as **`allow | warn | deny | escalate`** (4 verbs) and synced four doc surfaces to it (`hub-law-schema.md §2`, `hub-law.ttl`, `starter-law.yaml`, `HUB-LAW.md`). Presence's policy `decision` enum is **`allow | deny | warn`** (3 verbs) at every site (§3.4 L278, §5.4 L531, both query_policy schemas `:27`). *Charge:* presence's enum is stale/incomplete vs the now-canonical 4-verb vocabulary — it is missing `escalate`.

**Refutation (independent layer-split test — not imported from C196):**

1. **Different engines, different scope.** The 4-verb enum is the **`web4-policy` society-governance law engine** (`lib.rs::Decision`). The #521 "Decision semantics" note self-scopes: *"transcribe the live engine (`web4-policy/src/lib.rs`) … a sync surface, not a design surface."* Presence's `hestia_query_policy` is a **host-local inward-MCP tool-gate** with "4 built-in presets" (§3.4) — a per-tool-call check on one daemon's MCP surface. Neither the spec nor the schema claims presence's engine **is** the society law engine.
2. **`escalate` has no referent in presence's layer.** hub-law `escalate` = *"block pending a **higher authority's** decision (default `escalate_to: sovereign`)."* A **sovereign** is a society role (SAL §2.1). Presence's tool-gate operates on a single host's MCP surface with a connected orchestrator (`claude-code`, `openclaw`) — **no society, no sovereign** in that context to escalate *to*. Importing `escalate` would introduce a verb with no defined semantics at this layer.
3. **Presence already models deferral — orthogonally.** The §3.4.1 "wait protocol" (`status ∈ {decided, evaluating}` + `nextPollMs`) is presence's deferral mechanism: *"the engine is still working (e.g. it has invoked an LLM-backed reviewer or is awaiting an external attestation)."* Presence factors *verdict* (`decision`) apart from *finality* (`status`); hub-law folds deferral into the verb (`escalate`). Two legitimate factorings of the same underlying need.
4. **No normative equivalence claim exists.** Grep confirms presence never states its `decision` enum MUST equal the hub-law `Decision` enum, and #521 never states the hub-law enum governs the Hestia MCP gate. Absent a claimed mirror, divergent enums are **two layers**, not a contradiction. (Same class as C158's self-scoping precedent, C196's acp verdict — but re-derived here from presence's own text.)

**Verdict: REFUTED — clean-by-layer.** Presence's 3-verb enum is correct for its layer. Do **not** flag; do **not** add `escalate` to presence.

### B.2 — INFO (forward-compat, routed): presence↔PolicyEntity `escalate` mapping when v1.x lands

§3.4.1 reserves `status: "evaluating"` for *"future v1.x engines that consult an LLM-backed policy entity."* When such an engine wraps the `web4-policy` law oracle (per CLAUDE.md's PolicyEntity→PolicyGate repositioning), that oracle **can** emit `escalate`. At that point presence needs a documented mapping — most naturally **hub-law `escalate` → presence `{status: "evaluating"}`** (defer/poll) or a new terminal `{decision: "deny", reason: "escalated to <authority>"}`, depending on whether the higher authority is reachable in-band. This is a **v1.x design decision**, not a v1 defect — the current spec is internally consistent and correct for a host-local engine with no sovereign. **Routed to the operator/cross-track bundle; NOT self-applied.** (Genuinely new: it did not exist before the W4IP `escalate` verb was ratified, so it is absent from C160 and prior — [[feedback_prose_is_not_ledger]] check passed: this is new, not a re-discovery.)

### B.3 — mcp §7.8 async mailbox vs presence wait protocol (no carry)

The mcp §7.8 landing (`3e765345`) specs an **accept-and-defer async mailbox** (202 = delivery-not-completion, durable per-LCT queue, witness-on-completion). Candidate: does it obligate a change to presence's `status`/`nextPollMs` wait protocol? **No.** They are distinct async surfaces at distinct layers: the mailbox is an **inter-entity durable message queue** (hub per-member mailbox / hestia deferred inbox); presence's wait protocol is **intra-query polling** on a single synchronous policy evaluation that is still computing. The mcp §7.8 diff never mentions `presence`, `nextPollMs`, `evaluating`, or `status` (grep-verified). They coexist without conflict; no inbound carry.

### B.4 — Internal-consistency contradiction lens (frozen ⇒ inherits C160)

Because the artifact set is byte-identical to C160's audited state, the ~17 candidate contradictions C160 raised and refuted (the strongest being `enforced=true` on default-allow P1-002 vs §5.4 "default pass-through", demoted to under-specification) are **unchanged and still refuted**. Re-running them would re-derive the same verdicts against identical bytes. Version tags (`policy_denied`/`invalid_role`=v1+, `vault_denied`=v2+), enums, counts (8 tools / 6 resources / 10 error codes / 14 vectors / 12 schemas), and all `$ref` resolutions remain internally consistent. No new internal contradiction can arise from a file that did not change.

---

## Remediation Grouping (for C199)

| Cluster | Findings | Shape |
|---------|----------|-------|
| (none — autonomous) | — | **Zero net-new autonomous findings.** C199 (presence remediation turn) is a genuine **no-op** unless the operator greenlights a routed carry below. |
| **(cross-track, STANDING) resource-body wire coverage** | C127-1 facet | Author `Session`/`VaultEntry` schemas under `v0/common/` + 2 `resources/read` vectors for `session/own`, `vault/{name}`. Operator/cross-track judgment call — route, do NOT self-apply. |
| **(operator/cross-track, NEW this delta) `escalate` mapping at v1.x** | B.2 INFO | Decide the hub-law `escalate` → presence `{decision, status}` mapping *when* a v1.x LLM-backed/PolicyEntity engine lands. Forward-compat design question; nothing to apply against the current v1 spec. |

No operator **DESIGN-Q** blocks the current spec — B.2 is a forward-looking note, not a present-tense ambiguity.

---

## Cross-Cutting Observation

**This delta's value was proving that the largest inbound governance-vocabulary change in the corpus (W4IP's 4-verb ratification) produces NO drift in a byte-frozen consumer — and proving it by presence's own construction, not by citing the sibling that already survived the same inbound (acp/C196).** The policy-review method guard was explicit: run the layer-split as a *tested* refutation, not an assumed one. Doing so surfaced the sharper reason presence is clean — not merely "different repo" but **"`escalate` has no referent where there is no sovereign to escalate to,"** and **"presence factors deferral into an orthogonal `status` axis rather than into the decision verb."** That is a stronger, presence-specific refutation than "acp was clean, so presence is too."

The one thing the W4IP landing *did* create is a **forward-compat obligation** (B.2): the moment presence's anticipated v1.x LLM-backed engine wraps a law oracle that can emit `escalate`, a mapping must be decided. Recording it now — while it is a design note and not yet a defect — is the [[feedback_prose_is_not_ledger]] discipline applied prospectively: promote the item to a ledger home *before* it can vanish, so the delta that finally reaches a v1.x presence engine inherits it as an open question rather than re-discovering it.

Frozen ≠ clean in general; here, for the **fifth** presence delta running, frozen ≈ clean — and the inbound-carry lens (not the internal-consistency lens) was where the only genuinely-new content lived, exactly as the rotation method predicts for a long-stable target.
