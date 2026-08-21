# Hestia / Web4 / Hub sweep — 2026-08-21

Context: cold-ish cross-model review focused on repository hygiene, open work, PRD truth, and readiness for the AI Collective Portland proposal (“How does Portland split without fragmenting?”).

## Executive assessment

The system is further along than the public presentation currently makes obvious.

- **Web4 / Hub:** repository state is relatively clean. The governance substrate, semantic member discovery, consent-based introductions, sealed channels, admission/law/ledger machinery, and deployment path are real. The largest AIC gap is **product surface + the R4/R5 backend spine**, not greenfield governance.
- **Hestia:** functionally active and increasingly coherent, but repository/process sediment is substantial. Branch clutter and rescued/stranded work make actual status harder to see than it should be.
- **4-hub:** clean by design: one branch, no PRs/issues, read-only mirror. It should remain a publication artifact, not a development locus.
- **AIC framing:** do not present this as a conceptual governance system that still needs to be invented. Present it as a working governance/discovery substrate that needs a bounded chapter-delivery layer and subgroup/federation spine for the Portland pilot.

## Repository hygiene snapshot

### Hestia

At review time:

- ~75 branches total.
- 5 open PRs.
- 71 open issues.
- Therefore roughly 69 non-main branches do not correspond to current open PR heads.

Issue #494 already identified the historical-ref problem; branch count has improved from its audit point but remains far above a healthy operational baseline.

Open PR triage:

1. **#562 — unreadable mailbox => UNKNOWN, not evidence of silence**
   - Mergeable on current main.
   - Corrects a meaningful evidence-semantics bug.
   - Recommended: land after normal review/checks.

2. **#561 — window mailbox reader by escalation TTL**
   - Not mergeable as reviewed.
   - Fixes stale mailbox reads being treated as evidence that a peer saw and declined an ask.
   - Recommended: rebase/reconcile on #562 rather than treat as independent semantics.

3. **#517 — claude-code seat cuts over to shared law core**
   - Mergeable.
   - Important because the author/adjudicator seat was measured outside the same common decision path used for other seats.
   - Repo merge is not equivalent to live seat installation/verification; deployment evidence remains separate.

4. **#498 — invite peers on single_approver**
   - Not mergeable / rescue branch.
   - Original blocker is gone, but current liveness/escalation semantics have moved.
   - Recommended: rederive against current main rather than blindly rescue.

5. **#479 draft — act row names admitting authorization**
   - Large, old, heavily drifted branch.
   - Underlying invariant remains valuable: a consequential act record should cryptographically identify the authorization basis that admitted it.
   - Recommended: replace with a small current-main implementation, not wholesale branch rescue.

### Web4

At review time:

- 5 branches total.
- 3 open PRs.
- 9 open issues.

Open PRs:

- **#739 — chapter delivery PRD**: the most directly useful AIC planning artifact; mergeable.
- **#744 — key-at-mint**: fixes member bootstrap correctness; mergeable and important for real onboarding.
- **#732 — role-scope normative-home cleanup**: mergeable; Hestia twin already landed.

`hub/deploy-managed-host` appears to be a leftover from merged #728; prune after confirming no unique commits.

Open issue bookkeeping includes #700/#701/#702 still open despite implementation PRs landing. They should be reconciled against the actual landed/remaining scope instead of being left as ambiguous zombie trackers.

### 4-hub mirror

- 1 branch: `main`.
- 0 open PRs.
- 0 open issues.
- Correctly declares itself read-only.
- Publication script hard-pins and refreshes `origin/main`, uses a fresh clone/filter, and force-publishes the mirror.

The mirror is not materially stale with respect to **merged Hub implementation** at the review point: later Hub-relevant work (#732/#739/#744) is still open and therefore should not yet appear there. Republish intentionally after those changes land.

## PRD truth / remaining gaps

### Federated Hub north star

`hub/docs/PRD_HUB_V2_FEDERATED.md` remains the useful source of truth.

- **R1 peer federation:** specified, unbuilt.
- **R2 greater hubs chartered for a narrow role:** specified, unbuilt.
- **R3 fractally joinable ledgers:** local ledger exists; peer hash witnessing/checkpoints unbuilt.
- **R4 runtime roles as entities:** unbuilt.
- **R5 role promoted to child sovereign sub-hub:** unbuilt.
- **R6 edge-scoped law compatibility:** unbuilt.
- **R7a degraded-vs-conduct semantics:** landed.
- **R7b asserted-asker sponsor evidence:** core landed; witnessed sponsor-vouch completion remains (#707).
- **R7c deploy ratification:** partially landed; deploy-closure write protection remains (#709). Phase 0 must not be described as fully complete while this is open.
- **R7d availability parity:** not started.
- **R8 AIC Portland use case:** defined.
- **R9 semantic member discovery:** engine already built.
- **R10 consent-based introductions:** engine already built.

### AIC-specific architectural conclusion

AIC’s immediate problem does **not** require full arbitrary peer federation first. The correct implementation path is the restricted **parent-child subset of the canonical R1 edge**, so the pilot does not create a temporary subgroup mechanism that later needs replacement.

The core “split without fragmenting” demonstration requires:

1. **R4** — group/role as a runtime governed entity.
2. **R5** — that entity can become a child society while retaining a deliberate federation edge to Portland.
3. Presentation showing that division and connection simultaneously.

R2/R3/R6 can follow after the first local parent-child proof.

## What already exists for the AIC proposal

The proposal should be described from actual capability, not future architecture.

Already present:

- signed hub law and governed consequential acts;
- append-only witnessed ledger;
- member admission machinery;
- sealed member↔hub and member↔member paths;
- durable member messaging;
- `find_members` semantic discovery via membot sidecar;
- consent-based introductions (`request_intro`, `list_intros`, `respond_intro`);
- member registry enrichment without putting PII into the semantic index;
- Hestia profile links with visibility tiers and verification state;
- local-first chapter-owned data model;
- operator/admin surfaces;
- managed/self-host deployment work.

So the AIC product gap is mainly: **make the member/public experience visible and usable, then add the minimal R4/R5 subgroup spine.**

## Chapter-delivery surface priority

PR #739’s B1-B12 breakdown is directionally right.

Highest persuasive-value sequence for AIC:

1. **B9 public redacted decision record.** This most directly proves transparent governance instead of looking like another community directory.
2. **B1 chapter profile + API.** Public identity / legitimacy surface.
3. **B5 My Chapter.** Highest-value authenticated member page: roles, groups, obligations.
4. **B4 member directory.** Tier-correct, verified references.
5. **B11 discovery + introductions UI.** Engine already exists; expose it.
6. **B7 join status.** Makes governance legible to applicants and reduces organizer support load.
7. **B2/B6/B8 group/event/formation surfaces** once R4/R5 exists.
8. **B12 export** is a standing requirement because the proposal promises portability/exit.

Theming is useful but should follow working product planes. Current Hub HTML is hard-coded Rust `format!` output with inline styling; theming is an architectural extraction task, not a palette tweak.

## Hestia profile / channel gaps relevant to AIC

The current Hestia substrate is useful but insufficient for real chapter/community presentation:

- **H1:** no structured community-channel variants for Slack, Discord, Matrix, Telegram, Meetup, Luma, Eventbrite, Zoom.
- **H2:** references are member-owned; no group/community-owned channel/profile references.
- **H3:** no external public endpoint that serves tier-filtered links.
- **H4:** `hub_fields()` flattens platform→URL and loses label, verification, multiplicity, and public-vs-member distinction.
- **H5:** `SelfVerified` is an enum state without a proof mechanism.
- **H6:** references have no revocation/expiry semantics.

These were present in the chapter-delivery PRD but did not have dedicated Hestia tracker coverage at review time. They should become issues so they stop living only in prose.

## Operational blockers / risks

### Sponsor vouch (#707)

A resolvable sponsor with no witnessed vouch remains undecidable. With `requires_sponsor: true`, every applicant can still fall back to operator review. For a 4,500-member volunteer community this directly conflicts with the “reduce admin burden” goal.

Before optimizing, measure AIC’s actual baseline administrative burden (join handling, group formation, conflict routing, event approvals, directory/discovery support). Then use the pilot to demonstrate a reduction.

### Managed-host semantic search

Semantic member discovery depends on the loopback membot sidecar (`WEB4_MEMBOX_URL`). The managed-host path provisions the Hub container but not, as reviewed, the sidecar. Without correcting or explicitly degrading this, a hosted AIC pilot can advertise discovery while the deployed product silently lacks the engine.

This is an AIC pilot-readiness issue, not merely deployment polish.

### Deploy closure (#709)

Artifact ratification/self-reporting exists, but the closure that determines **what executes** is not yet protected against unauthorized writes. Unit/ExecStart, deploy scripts, staged artifact, and ratification manifest must join the governed closure. Until then R7c/Phase 0 is partial.

### Production key custody (#729/#730)

Production key custody / hardware evidence semantics remain separate hardening work. They matter for production claims but should not be conflated with what is needed to run a supervised AIC pilot.

## Documentation drift

### Hestia

Public README status was still anchored to an Aug 8 audit and said the shared gate decision core was not wired, while the gate-consolidation PRD records Sprints A-G as implemented/deployed and served since Aug 14. The README needs a current statement that preserves the remaining seat-specific cutover/install evidence (notably #517) without describing the entire consolidation as unbuilt.

### Hub

README / sprint language currently overstates F0/R7c completion. #708 deliberately landed only ratified-artifact visibility; #709 explicitly says deploy-closure protection still gates completion. Public status should say **R7c partial** and **Phase 0 not yet complete**.

## Proposed execution order

### Immediate / low-risk coordination

1. Land/ratify Web4 PRs **#739, #744, #732** after ordinary review/checks.
2. Convert chapter-delivery H1-H6 / B1-B12 into tracked work; avoid one giant implementation ticket.
3. Reconcile stale F0 tracker issues (#700/#701/#702) with actual landed scope.
4. Correct public status docs so they stop claiming completed work is unbuilt or incomplete work is complete.
5. Republish 4-hub only after Hub-path merges.

### AIC pilot path

6. Make managed-host membot explicit: provision sidecar or visibly degrade discovery.
7. Build minimal **R4 design then implementation**.
8. Build **R5 as restricted canonical parent-child R1 edge**, not a parallel subgroup mechanism.
9. Deliver B9/B1/B5/B4/B11/B7 in that order unless pilot feedback changes priority.
10. Measure baseline organizer burden before automation; then close #707 in a way that reduces actual manual handling without inventing false sponsor evidence.

### Hardening / production separation

11. Close #709 deploy closure.
12. Implement R7d availability parity.
13. Resolve #729/#730 production key custody/hardware evidence semantics.

### Hestia cleanup

14. Land #562; reconcile #561 on top.
15. Land #517 with separate live-install verification.
16. Re-derive #498 and #479 against current main rather than preserving historical branch shape.
17. Execute #494 branch/ref cleanup after rescuable work is accounted for.

## Review posture for the AIC conversation

A precise claim set is stronger than either overselling or apologizing:

- **Live today:** governance law/ledger, admission, member identity/channels, semantic discovery, consented introductions, local ownership, deployable daemon.
- **Pilot work:** member/public presentation, managed-host sidecar, subgroup runtime entities and child-society promotion.
- **Later federation:** arbitrary peer federation, greater-hub governance, peer-ledger witnessing, edge law compatibility.
- **Humans remain in the loop:** conflict resolution is governed/routed/witnessed by software; software does not pretend to replace judgment where law calls for escalation.

That answer directly addresses AIC’s questions about “is it live?”, scale, hosting/data ownership, governance vs discovery, and what software does in a real conflict.

## Lane assignment

Nova/GPT lane from this sweep:

- durable audit note (this file);
- status/documentation truth corrections;
- issue routing for PRD-only gaps;
- branch/PR triage and explicit handoffs;
- no destructive branch deletion without a final explicit branch list / confirmation;
- no blind merging of implementation PRs solely because they are mergeable; normal review and seat ownership still apply.
