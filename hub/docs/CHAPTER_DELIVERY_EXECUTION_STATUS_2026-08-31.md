# Chapter delivery - execution status, 2026-08-31

This note currentizes `PRD_CHAPTER_DELIVERY.md` without rewriting its design history. It is an execution/status overlay, not a second PRD.

## Current finding

The chapter-delivery gap is now narrower than the PRD's original snapshot suggests.

The backend plumbing is substantial. The highest-value remaining work is to expose it coherently to humans and complete the structural governance path that the proving use case needs.

## Source state that moved since the PRD snapshot

### B9a public decision record

**Source-built and merged:** #793 / `7808f3d6dba3e4d76a52683f539f8bf50d33a854` in the public mirror.

The projection:

- constructs disclosed records from an explicit allowlist;
- withholds unknown/new event kinds by default;
- does not disclose member identity as a side effect of publishing governance acts;
- preserves withheld ledger positions;
- carries both `entry_hash` and `prev_hash`, so continuity can be verified across withheld entries.

**Evidence rung:** merged and source-tested. The merge record states it had not yet been exercised against a running current Hub because the seat's daemon was stale/locked. Do not relabel this LIVE until a deployed build is restarted and the endpoint is probed against a real hub.

### B11 discovery + introductions

Still **backend-built, presentation-missing**:

- `find_members` semantic search exists through the membot sidecar;
- `request_intro`, `list_intros`, `respond_intro` exist over the sealed member channel;
- the managed-host path still requires an explicit sidecar deployment/health posture.

The implementation task is UI + deployment truth, not a replacement discovery engine.

## Post-common-gate execution order

The active Hestia one-gate consolidation remains a prerequisite for the proving demo's "law is actually enforced" claim. Once one executable authority is certified and current on the demo seat, chapter delivery is the next top-priority product sprint.

Recommended lanes:

1. **Live truth:** deploy/restart current Hub, live-probe B9a, preserve exact build/probe evidence.
2. **Presentation:** establish the data-first reference-UI pattern on B1, B5, B11, and only the B4 projections they need.
3. **Governance spine:** role/office lifecycle, one governed decision, one contest/ruling path, role rotation.
4. **Split:** implement/finish R5 as a restricted parent-child use of canonical R1, never a temporary subgroup mechanism.
5. **Deployment:** run/provision and health-check the membot sidecar; keep discovery visibly degraded if unavailable.

The intended demonstration spine is:

`delegate -> decide -> contest -> rotate -> split`

Every step should link to the witnessed act/evidence it produced.

## Deliberate first-sprint non-goals

Do not gate the first vertical on:

- full migration of legacy operator HTML;
- complete theming;
- social-channel integration;
- agent-managed channels;
- full peer/national federation;
- discussion/feed surfaces;
- polished export UI.

Exportability remains a standing data requirement. The point is to avoid holding the proving journey behind adjacent work that does not make the journey more truthful.

## Evidence discipline

For every chapter-delivery capability, keep the rungs explicit:

`source -> merged -> installed -> restarted -> live -> observed`

A public/member page on top of a dark backend is not a shipped feature. A compiled endpoint that has never run is not live. The proving case should inherit the same deployment-truth discipline as the Hestia gate work.
