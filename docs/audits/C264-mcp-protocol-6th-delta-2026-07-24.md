# C264 — `mcp-protocol.md` Sixth Delta Re-Audit (re-frozen since C226; mailbox mirror moved, surface unchanged)

**Date**: 2026-07-24
**Auditor**: autonomous web4 session (legion, slot `060036`, C-series)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` (1020 lines, 16 sections; blob `4491c1bb`)
**Instrument**: byte-freeze confirmation (spec) + §A live-HEAD anchor re-verification of the C188/C226 finding set + **SDK-mirror re-derivation at live HEAD** (the growth edge — the hub mailbox mirror `store.rs`/`rest.rs` MOVED since C226) + genuine-mirror gate + corpus-delta disjointness. Not a fan-out — the spec is frozen; the real work is adjudicating the moved mirror.
**Scope**: §A delta re-verification of **C226** (5th delta) + its lineage (C188 findings, C154-N1 anchor); §B — corpus-delta since C226 (2026-07-19), SDK-mirror re-derivation, disposition of standing carries C226-N1 (MEDIUM) and C188-N1.
**This audit RECOMMENDS ONLY — no spec/SDK mutation this turn.** Two new files (this doc + session log).

**Lineage**: C35 (2026-06-06, #279) → C76 (#365) → C77 (`f3d2613d`, remediated 8) → C116 (#406) → C117 (`afab0c43`, applied N1) → C148 (CLEAN) → C188 (`91225131`, applied C154-N1, SDK PARTIAL) → C226 (`d1cd70e1`, §7.8 net-new, N1 MEDIUM routed) → **C264** (this audit).

---

## Headline

1. **mcp-protocol.md is RE-FROZEN — byte-identical to the C226 baseline.** Blob `4491c1bb7f603808abfbaa01613e12b36f9c3192` is identical at the C226 baseline commit `3e765345` and at live HEAD; **0 commits touched the file since C226.** The §7.8 Asynchronous Mailbox surface added at C226 is unchanged. Every C188 + C226 finding holds **by construction** (byte-identical spec) — §A is a formality this turn, and the audit's weight moves entirely to §B.

2. **§B — the delta is the moved SDK mirror, and it re-confirms the C226 characterization.** The hub mailbox mirror (`hub/hub-lib/src/store.rs` + `hub/hub-daemon/src/rest.rs`) genuinely MOVED since C226's `f62c9e6` (public-release hardening wave `9e9f349a`/`95683868`, pair-message sidecar #553 `a101d216`, `send_secret` relay `38ec3b58`, H-007/H-008 hardening `1fc873d1`). **But the mailbox *core* (`mailbox_put`/`mailbox_delete`/`mailbox_load_all`/`mailbox_is_durable`) is semantically unchanged, and every mover narrows *away* from — or is disjoint to — N1's deferred-action double-completion surface.** The genuine-mirror gate holds at "genuine, but narrowed to notices/message transport."

3. **C226-N1 (MEDIUM) STANDS unchanged → operator/author.** §7.8.2 still mandates at-least-once + consume-once with **no consumer idempotency/dedup clause**; the mcp spec still never mentions `action_id` (grep=0), the corpus dedup key (`r7-framework.md` §1.7). The moved impl still does not exercise the double-execution surface (it carries content-blind notices/messages, not deferred R7 *actions*), so it neither closes N1 nor supplies counter-evidence. **N1 is the operator's to ratify** (a new normative obligation, not a zero-stretch citation fix) — the spec's continued silence on `action_id` is the *evidence N1 stands*, not license for the auditor to author the clause.

4. **C188-N1 (SDK ReputationEnvelope divergence) STANDS unchanged.** `mcp.py` is byte-frozen (last touch `b6c243c2`, 2026-05-19, pre-C188) → SDK-track carry B2+B6, unchanged.

5. **§A CLEAN — 8/8 C188 findings + all C226 findings HELD by construction; C154-N1 anchor stable; 0 regression.** The C154-N1 anchor (`reputation-computation.md` §4) is stable — repcomp untouched since `2bc3bafb` (2026-07-18, pre-C226); the C232 reputation audit (2026-07-19, after C226) left it substantive-clean.

6. **0 net-new. C265 = declared NO-OP** (mcp CLEAN internally; N1 is operator-owned; do NOT self-fix). Rotation advances +2 → `atp-adp` cluster = **C266**.

---

## Severity legend

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR a normative value/structure is rejected by the canonical taxonomy/SSOT. |
| **MEDIUM** | Normative guidance self-contradicts / under-specifies enough that two good-faith implementations diverge. |
| **LOW** | Maintainability / precision / SDK-lag hazard; recoverable by a careful reader; not a blocking contradiction. |
| **INFO** | Observation; recorded for completeness or to confirm a seam was inspected and found bounded. |

---

## §A — Delta re-verification of C226 (+ lineage)

**Spec byte-freeze established first (path-provenance discipline).** `git rev-parse HEAD:…/mcp-protocol.md` = `4491c1bb…` = `git rev-parse 3e765345:…/mcp-protocol.md`. `git log 3e765345..HEAD -- mcp-protocol.md` returns empty. The file has not moved one byte since C226. Consequently:

| Finding (source) | C226 status | C264 status | Basis |
|---|---|---|---|
| **8/8 C188 findings** (N5/N9/N13, N12, N15, F5/C62-B1, F9-inverted, B1-family) | HELD | **HELD** | byte-identical spec; loci unshifted (no intervening edit) |
| **C117 N1** (applied `afab0c43`) | intact | **intact** | byte-identical spec |
| **C154-N1** (mcp citation → `reputation-computation.md` §4) | applied & anchor-stable | **HELD; anchor STABLE** | mcp text frozen; repcomp §4 header stable, repcomp untouched since `2bc3bafb` 2026-07-18 (pre-C226; C232 left §4 substantive-clean) |
| **C226-N1** (MEDIUM, §7.8.2 idempotency gap) | routed operator/author | **STANDS** (see §B) | §7.8 text frozen; remedy key `action_id` still grep=0 in mcp |
| **C226-N2** (INFO, "gated on receipt (§7.2)" wording) | REFUTED-as-defect, INFO | **INFO, unchanged** | frozen text; defensible reading holds |

**§A verdict: CLEAN. 0 regression.** With the spec byte-identical, §A is confirmatory; the live-HEAD re-grep of the one *external* anchor (C154-N1 → repcomp §4) is the only part that could have moved, and it did not.

---

## §B — Corpus-delta + SDK-mirror re-derivation since C226

The spec is frozen, so all net-new potential lives in the mirror/consumer layer. Per the standing method ("re-derive implementers/CONSUMERS at live HEAD; an untracked mirror is where net-new hides"), the SDK surface was re-derived from scratch at HEAD.

### B.1 — Python SDK: `mcp.py` byte-frozen → C188-N1 STANDS

`web4-standard/implementation/sdk/web4/mcp.py` last touched `b6c243c2` (2026-05-19, pre-C188). No motion. The C188-N1 ReputationEnvelope-shape divergence is unchanged → SDK-track carry **B2+B6**, route not self-apply.

### B.2 — Hub mailbox mirror MOVED; core semantics UNCHANGED

`store.rs`/`rest.rs` moved since C226's `f62c9e6`. Commits since:

| Commit | Surface | Relation to §7.8 / N1 |
|---|---|---|
| `a101d216` (#553) | **pair-message sidecar** (`pair_message.rs`, sqlite+dynamodb) | Per-pair message log **explicitly outside the ledger** ("keep the chain [clean]") = reaffirms §7.8.2 *queue≠ledger*. Message transport, not a deferred R7 action. |
| `38ec3b58` | **`send_secret`** content-blind member→member sealed relay | Hub "relays the ciphertext into the recipient's mailbox WITHOUT" inspecting the sealed body = reaffirms §7.8.2 *stored still-sealed / plaintext never rests*. Notice transport, not action execution. |
| `9e9f349a`, `95683868` | public-release hardening wave | Token/freshness + review fixes on the delivery/relay path; mailbox trait unchanged. |
| `9034ade0`, `4380776a`, `9aedd2b7`, `1fc873d1` | pubkey-by-uuid, constellation enrollment registry, `/state` 500 fix, **H-007/H-008 auth-freshness** | Auth/enrollment/read-path; the H-007 comment even flags "idempotent READ tools exempt from freshness" — that is **auth idempotency, disjoint** from §7.8 *delivery/action* idempotency. |

The mailbox trait itself — `mailbox_put` (INSERT), `mailbox_delete` (idempotent DELETE-on-drain: "harmless no-op" re-delete, but **not** action-level dedup), `mailbox_load_all` (restart re-hydrate), `mailbox_is_durable` (durability flag + loud non-durable startup warn) — is semantically identical to C226. The `mailbox_delete` idempotency is *queue-cleanup* idempotency (re-deleting an empty queue is safe), which is **not** the *consumer action dedup* N1 requires (suppressing a re-delivered completed action).

### B.3 — Genuine-mirror gate: GENUINE, narrowed to notices/messages (unchanged from C226)

The gate outcome is unchanged: the hub mailbox is a **genuine** mirror of §7.8.2's queue MUSTs (per-recipient-LCT keying, encrypted-at-rest, durability flag, queue≠ledger, park-before-ACK), but it is **narrowed to hub→citizen notices and member↔member sealed messages** — delivery items, not inbound *R6/R7 actions* whose completion is a witnessed reputation/ATP event. The two new sibling surfaces (#553 sidecar, `send_secret`) **extend** this narrowing (both are content-blind transport) rather than reaching into the deferred-action execution path. **Therefore the impl still does not exercise N1's double-completion surface** — it neither closes N1 nor refutes it.

### B.4 — C226-N1 disposition: STANDS, route operator/author

The remedy key `action_id` (`r7-framework.md` §1.7) is still **absent from mcp-protocol.md** (grep=0, re-confirmed at HEAD). §7.8.2 still pairs at-least-once + consume-once with no consumer idempotency clause. A crash in the window *after a deferred action completes (witnessed) but before its drain-removal is durable* still permits redelivery → double-completion (double witness / double ATP discharge). This is a **new normative obligation**, not a zero-stretch citation fix → **not auditor-applicable.** Per the policy-review guardrail: the spec's continued silence on `action_id` is the *evidence N1 stands*, not a license to write the clause. Standing carry **B2+B6** to author/operator.

### B.5 — Corpus-delta disjointness

The audits and hub commits landed since C226 (C228 atp-adp … C262 web4-lct; constellation/pubkey/state hub work) do not add any mcp citation or any §7.8-mailbox-affecting normative surface. Effector (#523) and Inspectable-Evidence (#531) remain grep-empty in mcp (DISJOINT, consumed at C226). No new file cites mcp §7.8.

**§B verdict: 0 net-new.** The one moving surface (hub mailbox mirror) re-confirms the C226 genuine-narrowed-to-notices characterization; both standing carries (C226-N1, C188-N1) STAND unchanged and route to operator/author. This is a clean empty-corpus-delta PASS — no face manufactured to justify the turn.

---

## §C — Disposition & rotation

- **C226-N1 (MEDIUM)** — STANDS. §7.8.2 idempotency-on-redelivery gap; remedy = one clause keyed on `action_id`. **Author/operator (B2+B6). NOT auditor-applicable.**
- **C188-N1 (LOW/SDK)** — STANDS. `mcp.py` ReputationEnvelope shape. **SDK-track B2+B6.**
- **C226-N2 (INFO)** — REFUTED-as-defect; do NOT re-raise.
- **C148/C188 standing carries** (B5+B12, N5/N9/N13, N12, N15, F5/C62-B1, F9-inverted, B1-family) — HELD by byte-freeze construction.
- **C265 = declared NO-OP.** mcp CLEAN internally; N1 is operator-owned; do NOT self-fix mcp-protocol.md. Next mcp delta ~C302.
- **Rotation** advances +2 → `atp-adp` cluster = **C266** (atp-adp last audited C228, PR #551).

**Baseline for next mcp delta (C302):** spec `3e765345` (blob `4491c1bb`, 1020L, §7.8 L708-763, §8 L764); `mcp.py` `b6c243c2`; hub mailbox mirror re-derive at live HEAD (moved this turn — re-baseline from HEAD `store.rs`/`rest.rs` and re-run the narrowed-to-notices gate). **Guard:** check whether §7.8.2 gained an idempotency/dedup clause (keyed `action_id`) — if not, C226-N1 STILL STANDS; do NOT re-open the sibling relay surfaces (pair-sidecar, send_secret) as net-new (they are content-blind transport, DISJOINT from N1's deferred-action surface).

---

## Pattern (C264)

When a rotation's *spec* re-freezes but its *named reference implementation* keeps moving, the audit's center of gravity shifts entirely to the SDK-mirror re-derivation — and the disciplined question is **"does the mover close the standing gap, refute it, or merely extend the narrowing?"** Here three movers (pair-message sidecar, content-blind `send_secret`, auth-freshness hardening) all extended the "narrowed to notices/messages" characterization or were disjoint (auth idempotency ≠ delivery idempotency) — so C226-N1 neither closed nor gained counter-evidence, and STANDS as the operator's to ratify. A frozen spec's continued silence on the remedy key (`action_id`) is itself the standing-carry's live evidence, not an invitation to author the clause. → [[feedback_prose_is_not_ledger]] / [[feedback_prior_finding_path_provenance]] / [[feedback_refute_your_best_finding]].
