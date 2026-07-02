# C126 — ACP Framework Remediation (apply C125 M3)

**Date:** 2026-07-02
**Author:** Autonomous session `legion-web4-20260702-000036`
**Document remediated:** `web4-standard/core-spec/acp-framework.md`
**Turn type:** REMEDIATION (alternation partner of the C125 AUDIT turn)
**Lineage:** C18 (`acp-framework-internal-consistency-2026-05-28.md`, PR #244) → C37 (PR #283) → C86 (2nd-delta) → C87 (remediation PR #378 `31cea0b0`) → **C125** (3rd-delta AUDIT, PR #434 `53c0a935`) → **C126** (this remediation).

---

## Scope

C125 was the first clean ACP delta (0 net-new confirmed findings). It routed **exactly one** autonomous item forward — finding **M3** — and deferred everything else to operator DESIGN-Q / cross-track queues. C126 applies M3 and nothing else.

**M3** (C18-era carry, sharpened by C87-B6 into an intra-document self-contradiction): the `resourceCaps` guard keys appear in snake_case in the §2.1 plan example and in one §5.1 code fragment, while three independent authorities define the canonical form as camelCase:

1. JSON-LD schema `web4-standard/schemas/acp-jsonld.schema.json` → `$defs.ResourceCaps` (L56-58): `maxAtp` / `maxExecutions` / `rateLimit`.
2. SDK `to_jsonld` serializer emits camelCase.
3. The document's **own** §11 illustrative-vs-normative note (L604, added by the C87-B6 remediation) explicitly asserts the canonical guard model is `{lawHash, resourceCaps{maxAtp,maxExecutions,rateLimit}, witnessLevel, humanApproval, expiresAt}`.

Because (3) is in-file, M3 is not merely spec-vs-schema drift — it is an **intra-document self-contradiction** between the §11 note and the §2.1/§5.1 examples. That makes it cleanly spec-local and autonomous (no operator decision, no cross-track dependency; the correct direction is pinned three ways).

---

## Edits applied

| Locus | Before | After |
|---|---|---|
| §2.1 plan example, L77 | `"max_atp": 25` | `"maxAtp": 25` |
| §2.1 plan example, L78 | `"max_executions": 100` | `"maxExecutions": 100` |
| §2.1 plan example, L79 | `"rate_limit": "10/hour"` | `"rateLimit": "10/hour"` |
| §5.1 `check_law_compliance`, L312 | `plan.guards.resourceCaps.max_atp` | `plan.guards.resourceCaps.maxAtp` |

`git diff --stat`: 1 file changed, 4 insertions(+), 4 deletions(-).

**Deliberately NOT touched:**

- **`law.max_atp_per_plan`** (same L312, RHS of the comparison) — this is a *law* attribute, not a plan guard key. It is out of M3's scope and is left snake_case. (C125 §A.3 and the C126 policy reviewer both independently verified it is a distinct symbol.)
- **§2.4 L174** `resourceCaps.maxAtp` (the C87-B7 ATP-accounting note) — already camelCase, correct.
- **§11 note L604** — already camelCase, is the in-file authority for the fix, must stay as-is.

A full-document scan (`grep max_atp|max_executions|rate_limit|maxAtp|maxExecutions|rateLimit`) confirmed these four loci were the only guard-key references; no other in-body example (e.g. §11 domain sketches) uses the three keys. The fix is complete, not partial.

---

## Verification

- **Residual snake_case guard keys:** none. The only remaining `max_atp` token is `law.max_atp_per_plan` (correctly out of scope).
- **JSON fence integrity (regression check):** the §2.1 plan example fence — the one edited — parses as valid JSON before and after. Three other `json` fences (approx L39, L128, L327) fail strict `json.loads` **both before and after this edit** (3 bad / 7 total on `HEAD` and on the working tree) because they carry JSONC-style `//` inline annotations in illustrative wire-shape examples. This is pre-existing and unchanged by C126. → routed as an observation for the next ACP audit (see below); NOT in M3's scope.
- **Authority alignment:** post-edit, §2.1/§5.1 now match schema `$defs.ResourceCaps`, the SDK serializer, and the §11 note. The intra-document self-contradiction is closed.
- **No schema / SDK / test-vector / .ttl mutation** — those were already the correct authority; only the spec examples drifted.

---

## Carries remaining (unchanged — routed to operator / cross-track, NOT self-applied)

Per C125 routing, all of the following remain open and are *not* touched by this remediation turn:

- **DESIGN-Q (operator):** B-LEDGERPROOF / C37-5 (§4.2 `ledgerProof` admit-vs-strip); B11 (subsystem `W4_ERR_*` → RFC 9457 envelope); B14 (define "ACP-critical actions").
- **CROSS-TRACK (needs another spec/SDK to move first):** B-AGENCY / L1 (mcp `web4_context` proofOfAgency casing + field-set + `agency_chain` — unchanged after mcp C117); B8 (ACP discharge ↔ atp-adp §7.1 #5 R6 linkage — unchanged after atp-adp C119); B12/B13 (ACP witness vocab ↔ SAL quorum); B-M6 / M6 (11 `acp:` predicates need an `acp-ontology.ttl`); B15 (errors.md metering ref rides the C75 D0 cluster).
- **M7** — integer `witnessLevel` vs structured `witness_requirement`; no bridge (SDK implements integer only).

## New observation for the next ACP audit (routed, NOT acted on this turn)

- **JSONC `//` comments in three `json`-fenced examples** (approx L39 triggers, L128 decision, L327 witness-requirement) prevent strict JSON parsing of those fences. C87-B1's remediation note claimed "all 7 json fences parse"; under a strict parser 3 do not (they never did — this is illustrative annotation, not new drift). A future audit turn should decide whether to (a) relabel these fences `jsonc` / `text`, (b) strip the `//` annotations to prose, or (c) accept them as illustrative. Spec-local but a *style/format DESIGN-Q*, not covered by M3 — deferred, not self-decided.

---

## Result

M3 closed. ACP-framework's `resourceCaps` examples are now internally consistent with the doc's own §11 note, the JSON-LD schema, and the SDK. ACP now carries **zero autonomous spec-local debt** (matching the reputation-computation state after C124). All remaining ACP carries are operator-DESIGN-Q or cross-track.

**Next fire:** alternation → AUDIT turn. Audit-side rotation advances **acp → presence-protocol** (presence last: C88 2nd-delta → C89 remediation #380 → next is a 3rd-delta; check `docs/audits/*presence*`). Corpus-wide remaining remediation debt: C114-N1 (web4-lct, MED, BLOCKED on operator D0).

---

*C126 complete. Single-item remediation (M3), 4-key edit, 1 file. ACP lineage C18 → C37 → C86 → C87 → C125 → C126.*
