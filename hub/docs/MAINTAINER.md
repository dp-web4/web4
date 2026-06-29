# Hub Track Maintainer

**Effective**: 2026-06-09
**Maintainer**: HUB (the fleet machine hosting the live Web4 Community Hub deployment)
**Scope**: everything under `web4/hub/`, `web4/hub-lib/`, `web4/hub-daemon/`, and the live hub deployment

---

## Why HUB

HUB is the machine that physically runs the Web4 Community Hub daemon for the "Web4 Fleet" society. Consolidating review/merge/rebuild/redeploy on the same machine that owns the deployment collapses the round-trip — there's no hand-off between "the machine that reviewed the PR" and "the machine that has to redeploy the result." Authority binds to the role; the hub-maintainer role binds to the machine that operates the hub.

This is the first explicit per-track maintainer assignment in the fleet. Previous tracks (e.g. the 4-life maintainer cycle, the web4-reviewer cycle on Legion) emerged through cron schedules and convention. The hub track is being declared explicitly because the live deployment makes ownership operationally consequential — a wrong merge means a redeploy of the wrong code on the live society host.

## Contributor workflow

If you are any fleet machine *other than HUB* and want to land hub-track code:

1. **Branch + commit** locally as usual
2. **Open a PR** against `dp-web4/web4` (the public repo). Paths under `web4/hub*`, `web4/hub-lib*`, `web4/hub-daemon*` route to the hub maintainer.
3. **Reference relevant sprints** (`web4/hub/docs/SPRINTS.md`, `PAIRED-CHANNELS.md`, etc.) in the PR description.
4. **Run the standard test surface** locally before opening:
   ```bash
   cd web4/hub
   cargo build --release
   cargo test -p hub-lib -p hub-daemon
   ```
5. **Address HUB's review feedback** as you would any reviewer.

## Maintainer workflow (HUB)

When HUB's supervisor track runs:

1. **Watch** `dp-web4/web4` for new PRs touching `web4/hub*` paths
2. **Review** against:
   - Hub PRD (`web4/hub/docs/PRD.md`)
   - Active sprint plan (`web4/hub/docs/SPRINTS.md`, `PAIRED-CHANNELS.md`)
   - Hub law for the "Web4 Fleet" society (the hub's own laws govern its evolution)
   - Standard code quality + test coverage
3. **Merge** via squash unless the contributor requests preserve-history with reason
4. **Rebuild** the hub daemon binary
5. **Redeploy** the live hub instance (with appropriate rollback safeguard — see `docs/DEPLOYMENT.md` when it exists)
6. **Log** the reviewer session to `private-context/autonomous-sessions/`
7. **Post a forum notice** if the change has fleet-wide implications (vocabulary changes, breaking API changes, security-relevant updates)

## What stays distributed

- **Specification and architecture decisions** are fleet-wide (PRDs, ROLES.md, V2-V3-ARCHITECTURE.md). Any machine can propose changes via PR.
- **Sprint planning** is collaborative. Sprints can be claimed by any contributor; the maintainer-track exists to land the work, not to monopolize it.
- **Code authorship** remains diverse. The maintainer track is about ownership of the merge/deploy loop, not about being the sole author.

## What's centralized

- **Merge authority** for hub-track changes
- **Rebuild + redeploy** of the live hub daemon
- **Final say on operational changes** that affect the live society's law, members, or trust state
- **Coordination with Sovereign actions** (chapter-amendment, identity-recovery, extraordinary inter-society decisions)

## Sovereign relationship

HUB is the hub *maintainer* — operating the codebase. The Sovereign of the "Web4 Fleet" society is dp's LCT (see hub charter). The hub maintainer does not act as Sovereign and does not amend hub law without explicit Sovereign signature. Day-to-day operations (merging PRs, redeploying, etc.) do not require Sovereign action; structural changes do.

## Escalation

If a PR is stalled, contentious, or raises questions HUB can't resolve:

1. **Forum post** in `shared-context/forum/` flagging the issue (HUB-maintainer voice)
2. **Tag the relevant contributor** in the PR for direct discussion
3. **Defer to dp** for decisions that require Sovereign judgment (hub law, security policy, vocabulary canon)

## Effective date

This ownership transfer is effective 2026-06-09 (announcement: `shared-context/forum/cbp-hub-track-ownership-transfer-2026-06-09.md`). The supervisor track on HUB comes up at the office today; until then, PRs queue and HUB merges them when its track goes live.
