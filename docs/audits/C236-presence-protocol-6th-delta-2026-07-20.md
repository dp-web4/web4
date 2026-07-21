# C236 — presence-protocol.md Sixth Delta Re-Audit

**Date**: 2026-07-20
**Auditor**: autonomous web4 session (legion, C-series **C236**, slot web4-20260720-180036)
**Subject**: `web4-standard/core-spec/presence-protocol.md` (722 lines, 9 sections), v1 Draft — blob `6414a7fe` at HEAD
**Baseline**: `docs/audits/C198-presence-protocol-5th-delta-2026-07-16.md` (5th delta). C198 found **zero net-new autonomous** findings; its only additions were one forward-compat INFO (B.2 — the hub-law `escalate` → presence `{decision, status}` mapping owed *when* a v1.x LLM-backed engine lands) and a standing cross-track carry (C127-1 facet).
**Lineage**: C5 (`presence-protocol-internal-consistency-2026-05-17.md`, 13 findings) → C38 (#284/#285) → C88 (#379) → C89 (#380) → C127 (audit) → C128 (#439 `cf0d6cc5`, remediation) → C160 (4th, audit) → C198 (5th, audit) → **C236** (this, 6th, audit).
**Companion artifacts cross-checked**: `presence-protocol-CHANGELOG.md`; all **12** JSON Schemas under `web4-standard/schemas/presence-protocol/{v0/common,v0/tools,v1/tools}` + the schema-dir `README.md`; `web4-standard/testing/conformance/presence-protocol-conformance.json` (**14** scenarios, P0-001..P0-010 + P1-001..P1-004); filesystem ground-truth at live HEAD.
**Scope**: Internal-consistency + **inbound-carry** 6th-delta re-audit. The presence artifact set is **byte-frozen since C128 (`cf0d6cc5`)** — `git diff cf0d6cc5 HEAD` over `{presence-protocol.md, CHANGELOG, all 12 schemas, README, conformance.json}` is **empty**. So §A = verify the frozen state and re-confirm C198/C160/C89/C5/C38/C88-5/C128 findings hold by construction. **The genuinely new surface this delta is external**: the sibling churn merged into the corpus *after* C198 (2026-07-16). C198 already adjudicated the largest inbound (the W4IP 4-verb governance vocabulary) as clean-by-layer; this delta adjudicates the **next tranche** — the **durable-messaging hub implementation** (`send_secret` `38ec3b58`, pair-message sidecar #553 `a101d216`, member-pubkey route `9034ade0`), the **authority_ratchet LCT** construct (#544 `2ec6ea09`), and the **oracle-scope** role extension (`4f76f110`, the already-refuted C234/acp flagship). The flagship question this delta uniquely answers: **does the now-*implemented* (not just spec'd) inter-entity durable mailbox obligate a change to presence's intra-query `status`/`nextPollMs` wait protocol?** **Does NOT patch anything** — remediation, if any, is the next alternation turn.
**Instrument**: Lead-context mechanical verification (empty-diff freeze proof, schema/vector counts at live HEAD, decision-enum extraction from spec + both query_policy schemas) + **re-derivation of the SDK/consumer set at live HEAD** (per the policy-review method guard: the durable-messaging churn is exactly the untracked-consumer surface where net-new hides) + refute-by-default adjudication of the post-C198 inbound. Per [[feedback_refute_your_best_finding]], [[feedback_cross_doc_carry_inbound]], [[feedback_prose_is_not_ledger]], [[feedback_enumeration_and_grep_hypotheses]].

---

## Frozen-state ground truth

`git diff cf0d6cc5 HEAD` over the full presence artifact set is **empty**. The spec (722 lines), CHANGELOG, all 12 schema files, the schema-dir README, and the 14 conformance scenarios are byte-stable **~18 days** since C128 (`cf0d6cc5`, 2026-07-02) and ~27 days since the last *spec* edit (C89 `0beb1b93`, 2026-06-23). Ground-truth re-confirmed at HEAD:

- **12** `*.schema.json` files (`v0/common`×3 + `v0/tools`×8 + `v1/tools`×1) — matches C160/C198's corrected count.
- **14** conformance scenarios, ids `P0-001..P0-010` + `P1-001..P1-004` — unchanged.
- `decision` enum = `["allow", "deny", "warn"]` in **both** the v0 and v1 `hestia_query_policy` schemas (`:27`) and in spec §3.4 (L278) + §5.4 (L531). Three values. **No `escalate`** (as C198 established, correct-by-layer).
- `status` enum (v1 query_policy schema `:53`) = `["decided", "evaluating"]`.

Because the target is byte-identical to its C198/C160-audited state, every C198/C160/C89/C5/C38/C88-5/C128 verdict **HOLDS by construction** — there is no edit site that could regress one. §A below records the verification; the audit's *value* this delta is entirely in §B's inbound-carry adjudication of the post-C198 sibling churn.

---

## Headline

**Zero net-new autonomous findings (sixth consecutive substantive-CLEAN presence delta).** The post-C198 sibling churn creates **no** inbound consistency obligation on presence:

- **Durable-messaging hub implementation (`send_secret`, pair sidecar #553, member-pubkey route) — REFUTED, no carry.** C198 B.3 already ruled the mcp §7.8 *spec* landing (accept-and-defer async mailbox) a **distinct async surface** from presence's wait protocol. This delta confirms the refutation survives the surface being *implemented*: `send_secret` (`38ec3b58`) is a **content-blind member→member sealed relay** and the pair sidecar (#553) is a **store-backend gap fix** for the `/pairs/:pair_id/messages` durable queue — both are **inter-entity durable message transport** in the hub daemon. Presence's `status ∈ {decided, evaluating}` + `nextPollMs` (§3.4.1) is **intra-query polling on a single synchronous policy evaluation still computing** on one host's MCP surface. Different layer (inter-entity transport vs intra-query verdict-finality), different repo (hub daemon vs Hestia inward-MCP gate), zero lexical overlap: grep across `hub/` for `query_policy | nextPollMs | hestia_query | status.*evaluating | presence-protocol` = **empty**. They coexist without conflict; **no carry**.
- **authority_ratchet LCT (#544 `2ec6ea09`) — REFUTED, no referent.** The society-ratchet-level-provable-on-LCT construct is a **society-governance** primitive (like the W4IP `escalate` verb C198 refuted). Presence's `hestia_query_policy` is a host-local tool-gate with **no society, no sovereign, no ratchet** in scope; the ratchet has no presence referent. Grep for `ratchet` in the presence spec = **empty**.
- **oracle-scope role extension (`4f76f110`) — REFUTED, lexical collision (inherited from C234).** `RoleExtension::Scope` (`role_extension.rs`, gained oracle-consult/write-set) is a *society role-scope* type; presence has no role-scope surface. This is the same lexical "Scope" collision C234 refuted for acp; presence never references it.

**SDK/Rust-mirror gate = NEGATIVE (re-derived at live HEAD).** Per the standing method guard — re-derive implementers/consumers at HEAD before declaring §B clean, because the untracked consumer is where net-new lives — this delta explicitly re-ran the consumer sweep against the **new** durable-messaging code. Result unchanged from C198: there is **no** presence-protocol twin in `web4-core/src/*.rs` or the Python SDK. `grep -rlE 'query_policy|hestia_connect|hestia_begin_action|nextPollMs|PolicyResult|hestia_record_outcome' web4-core/src` = **empty**; the `presence` token in web4-core (`lib.rs`, `lct.rs`) is **LCT witnessed-presence tokens** (a different concept), and `record_outcome` in `act.rs` is the **T3/V3 trust act**, not the presence `hestia_record_outcome` MCP tool. The presence protocol is Hestia's inward MCP surface, implemented in the hestia daemon (private repo), which this audit does not cross-compare. The SDK-mirror lens that yields net-new for reputation/t3-v3/mcp **does not apply to presence** — there is nothing in the tracked mirror to diverge.

**§A: frozen (empty diff since C128) ⇒ C128 ledger COMPLETE + 6/6 claims TRUE · C89 4/4 HELD across 6 mirrors · 13/13 C5 + 5/5 C38 HELD · C88-5 R6Action still INFO · C127-1 cross-track facet STANDS as a routed carry · C198 B.2 escalate-mapping INFO STANDS (unchanged — no v1.x engine has landed). All by construction (byte-identical).**
**§B: post-C198 sibling churn (durable-messaging impl · authority_ratchet · oracle-scope) = ALL distinct-layer / no-referent, refuted independently · SDK-mirror gate NEGATIVE re-derived at HEAD · 0 net-new autonomous findings · 0 new INFO (the durable-messaging surface was already covered by C198 B.3; its *implementation* changes nothing for presence).**

---

## §A — Delta Verification (frozen target)

The presence artifact set is byte-identical to its C198/C160-audited state (`git diff cf0d6cc5 HEAD` empty). Therefore:

- **A.1 — C128 remediation (README known-gap ledger).** File unchanged since C128. The complete schema-less set `{Session, R6Action, VaultEntry, society/state}` and the README's four matches (with the two traps correctly omitted: Outcome §5.3 bound by `record_outcome` **input** `$defs`; PolicyResult §5.4 bound by v1 `query_policy` **output**) are byte-stable ⇒ **still COMPLETE, all 6 factual claims still TRUE**. No regression.
- **A.2 — C89 four (C88) findings + six-mirror `vault_denied`.** File byte-identical ⇒ `vault_denied`/interactive-approval still uniformly "reserved for v2+" across all six sites (§3.5 L337-339, L344-345; §3.6 L351-352; §6.1 L626, L634-642; §8 L692); the §6.1 `(v1+)` footer still names exactly `policy_denied` + `invalid_role`. **4/4 HELD.**
- **A.3 — C5 / C38 / C88-5.** No edit site ⇒ **13/13 C5 + 5/5 C38 HELD**; C88-5 R6Action §5.2 still **INFO** (documentary struct, `toolName` absent from `begin_action` output, no wire-carrier claim).
- **A.4 — C127-1 cross-track facet (standing carry).** Unchanged — C128 applied only the autonomous README facet; the cross-track facet (author `Session`/`VaultEntry` JSON Schemas under `v0/common/` + 2 `resources/read` vectors for `session/own`, `vault/{name}`) **STANDS** as an open cross-track judgment call. Do NOT self-apply.
- **A.5 — C198 B.2 escalate-mapping INFO (standing forward-compat carry).** Unchanged. No v1.x LLM-backed / PolicyEntity presence engine has landed since C198 (grep of CHANGELOG "Upcoming" + spec §3.4.1 confirms `evaluating` is still "reserved for future v1.x engines"). The obligation — decide the hub-law `escalate` → presence `{decision, status}` mapping *when* such an engine wraps a law oracle — **STANDS** as a routed forward-compat carry. Not yet a defect; do NOT self-apply.

**Inbound-carry surface (§B territory, checked for §A regressions):** the sibling files that churned since C198 (`send_secret` `38ec3b58`, pair sidecar `a101d216`, member-pubkey `9034ade0`, authority_ratchet `2ec6ea09`, oracle-scope `4f76f110`, entity-types C214 `2bc3bafb`, operational-key vouching `357173c4`, citizenship `0e997079`) are all hub-daemon / LCT / entity-types / society-role landings. **None edits presence; none routes a carry *back* into presence's ledger.** Whether any creates a *new* consistency obligation for presence is the §B flagship.

---

## §B — Fresh Findings

**None (0 net-new autonomous). 0 new INFO. All three post-C198 inbound candidates refuted independently.**

### B.1 — FLAGSHIP: durable-messaging hub implementation → presence wait protocol (REFUTED — distinct layer, no carry)

**Candidate (strongest):** Between C198 and this delta the corpus went from *spec'ing* an async mailbox (mcp §7.8, which C198 B.3 already handled) to **implementing and extending** it: `send_secret` (`38ec3b58`, a content-blind member→member sealed relay adding the *send* half of the sealed channel), the pair-message sidecar (#553 `a101d216`, making `append_pair_message`/`list_pair_messages` work on the sqlite/dynamodb backends behind `/v1/hubs/:hub_id/pairs/:pair_id/messages`), and a member-pubkey route (`9034ade0`). *Charge:* a live durable inter-entity queue with accept-and-defer semantics obligates presence to reconcile its `status: "evaluating"` / `nextPollMs` deferral surface with it — perhaps presence's "wait" should route through the mailbox, or its `evaluating` verdict should be persisted to a per-LCT queue.

**Refutation (independent layer-split test):**

1. **Two different async axes.** The mailbox is **inter-entity durable message transport**: member A seals a body to member B's operational key, the hub queues it (TTL/cap/durable write-through via `enqueue_notice`), B drains it later (`hestia_inbox`, §7.8.2-gated). Presence's wait protocol is **intra-query verdict-finality polling**: a *single* `hestia_query_policy` call on *one* host whose engine "is **here** but still working on a verdict" (§3.4.1), re-queried with the *same* `action_id`. One is A→hub→B message delivery; the other is a caller re-asking one local engine for the same still-computing answer. No shared state, no shared endpoint.
2. **No lexical or structural overlap.** Grep across `hub/` for `query_policy | nextPollMs | hestia_query | status.*evaluating | presence-protocol` = **empty**; grep across the presence spec for `inbox | mailbox | deferred inbox | send_secret | async | ratchet` = only the *unrelated* v2+ vault-approval "deferred" uses (§3.5/§3.6/§6.1/§8) — never a message queue. Neither surface names the other. The `sealed_by`/`from`/`enqueue_notice` vocabulary of the mailbox has no presence counterpart; the `nextPollMs`/`action_id`/`evaluating` vocabulary of the wait protocol has no mailbox counterpart.
3. **The implementation is strictly more of what C198 already refuted.** C198 B.3 ruled the mcp §7.8 mailbox *spec* a distinct surface with no inbound carry. #553/`38ec3b58` **implement** that same spec on more backends and add its send half — they change the *fidelity of the mailbox*, not its *relationship to presence*. A refutation that held against the spec holds a fortiori against the spec's implementation, since the implementation introduces no new presence-facing construct (verified: the diffs are entirely within `hub/` store/relay code).

**Verdict: REFUTED — distinct layer, no carry.** Presence's wait protocol needs no reconciliation with the durable mailbox. Do **not** flag.

### B.2 — authority_ratchet LCT (#544) → presence policy engine (REFUTED — no referent)

**Candidate:** #544 (`2ec6ea09`) makes the **society ratchet level provable on the LCT** (`authority_ratchet`). Presence's policy `decision` enum includes `warn` — the same token as the W4IP rung-enforcement `warn` (the gate-`warn` collision ruled real in #522). *Charge:* presence's tool-gate should consult / reflect the LCT-borne ratchet level when deciding.

**Refutation:** The `authority_ratchet` is a **society-governance** construct — a ratchet level within a society's law hierarchy, provable on a member's LCT. Presence's `hestia_query_policy` is a **host-local inward-MCP tool-gate** driven by "4 built-in presets" (§3.4) on one daemon's MCP surface: there is **no society, no sovereign, no ratchet** in that layer to consult (the same "no referent where there is no sovereign" reasoning C198 used to refute the `escalate` verb). Presence's `warn` = *"allow-but-flag this tool call for the orchestrator to log"* (§3.4), a per-tool-call audit signal; the W4IP `warn` = a society rung. Lexical collision, not semantic drift — and presence makes **no** claim to mirror the society ratchet. Grep for `ratchet` in the presence spec = **empty**. **REFUTED — no referent; no carry.**

### B.3 — oracle-scope role extension (`4f76f110`) → presence (REFUTED — lexical collision, inherited from C234)

`RoleExtension::Scope` gaining `oracle_consult`/`write_set` (`role_extension.rs`, Piece B for oracle-scope gating) is a **society role-scope** type — the exact construct C234 refuted as a lexical "Scope" collision for acp (`grant.scope.r6Caps.resourceCaps` ≠ Rust `RoleExtension::Scope`). Presence has **no role-scope surface at all** (its `scope` fields are vault credential scopes — `hestia_vault_get.scope`, §3.5 — an allow-list match, not a role capability). No presence referent. **REFUTED — no carry.**

### B.4 — Internal-consistency contradiction lens (frozen ⇒ inherits C198/C160)

Because the artifact set is byte-identical to C198/C160's audited state, the candidate contradictions those deltas raised and refuted (the strongest being `enforced=true` on default-allow P1-002 vs §5.4 "default pass-through", demoted to under-specification) are **unchanged and still refuted**. Version tags (`policy_denied`/`invalid_role`=v1+, `vault_denied`=v2+), enums, counts (8 tools / 6 resources / 10 error codes / 14 vectors / 12 schemas), and all `$ref` resolutions remain internally consistent. No new internal contradiction can arise from a file that did not change.

---

## Remediation Grouping (for the next presence turn)

| Cluster | Findings | Shape |
|---------|----------|-------|
| (none — autonomous) | — | **Zero net-new autonomous findings.** The next presence remediation turn is a genuine **no-op** unless the operator greenlights a routed carry below. |
| **(cross-track, STANDING) resource-body wire coverage** | C127-1 facet | Author `Session`/`VaultEntry` schemas under `v0/common/` + 2 `resources/read` vectors for `session/own`, `vault/{name}`. Operator/cross-track judgment call — route, do NOT self-apply. |
| **(operator/cross-track, STANDING from C198) `escalate` mapping at v1.x** | C198 B.2 INFO | Decide the hub-law `escalate` → presence `{decision, status}` mapping *when* a v1.x LLM-backed / PolicyEntity engine lands. Forward-compat design question; nothing to apply against the current v1 spec. **Unchanged this delta — no such engine has landed.** |

No operator **DESIGN-Q** blocks the current spec.

---

## Cross-Cutting Observation

**This delta's value was proving that a governance-vocabulary inbound refuted at the *spec* level stays refuted when the corpus *implements* it.** C198 refuted the W4IP 4-verb enum and the mcp §7.8 mailbox spec as clean-by-layer. In the four days since, the corpus did not add new presence-facing vocabulary — it *built out* the mailbox (send half + more backends), *reified* the society ratchet onto the LCT, and *extended* role-scope gating. The refutation instinct here was to re-test each against presence's own text rather than assume "C198 covered it": the sharper finding is that **an implementation of an already-distinct surface introduces no new presence-facing construct**, so the layer-split verdict inherits by construction — but only *after* confirming (grep-verified at HEAD) that the implementation stayed within `hub/`store/relay code and never reached for a presence vocabulary token.

The one carry the W4IP landing created (C198 B.2, the `escalate` mapping owed at v1.x) is **still owed and still not yet a defect** — no v1.x LLM-backed presence engine has landed, so the mapping remains a forward-compat design note rather than a present-tense ambiguity. Promoting it to a ledger home at C198 (per [[feedback_prose_is_not_ledger]]) is why this delta could confirm it STANDS with a one-line grep rather than re-discovering it.

For the **sixth** presence delta running, frozen ≈ clean — and, as the rotation method predicts for a long-stable target, the only place net-new could have lived was the inbound-carry lens (the newly-*implemented* durable mailbox), which the SDK/consumer re-derivation at live HEAD confirmed carries nothing back into presence.
