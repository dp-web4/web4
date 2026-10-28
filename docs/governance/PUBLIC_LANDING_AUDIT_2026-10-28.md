# Cross-ecosystem landing-document staleness sweep — 2026-10-28

**Scope:** 80 repositories enumerated through the connected dp-web4 GitHub account (owned projects, private research repos, hardware work and upstream tracking forks). Sampled root READMEs across the major current public stack, organization profile, society mirror, research/collaboration repos, private contexts, hardware portfolio and selected upstream forks; inspected canonical linked status/docs for claims corrected below. **This is not a line-by-line, deployed-site or command-execution audit of all 80**, nor proof that every landing link or package command works. No edits to forks solely to impose dp-web4 branding.

**Method:** prefer GitHub's current merged/PR state and the canonical source and status documents, not the date printed by a README. Preserve historically dated research and ownership. A source merge does not establish deployment, participant outcome or A2 assurance. Change original source for generated mirrors.

| Priority | Target | Verified staleness and evidence | Reviewable PR |
|---|---|---|---|
| **P0** | Metalinxx root README | First-screen positioning and “Current Status”/fundraising/pilot milestones are largely **Q1 2025**. Current stack is agent governance via [Web4 status](../../STATUS.md), [Hestia](https://github.com/dp-web4/hestia), Hub and SAGE; proprietary Hardbound remains separately bounded | [metalinxx #2](https://github.com/dp-web4/metalinxx/pull/2): 2026 entry, preserve 2025 archive |
| **P1** | private-context README (private) | Header says updated April 2026 and labels November 2025 Legion/CBP **six-hour** research sessions ACTIVE. dp reports current nominal 30-minute being heartbeats; wake schedule is not proof of actual work. Canonical reusable Hub authority remains in web4 | [private-context #96](https://github.com/dp-web4/private-context/pull/96): current placement and 2025 archival boundary |
| **P1** | repo-plane landing and bootstrap metadata | README and validation said [Web4 #890](https://github.com/dp-web4/web4/pull/890) awaited merge. It **merged** as `a9244c8fb5c6baf0cad8a7b08abd19e03d506f53`. Local import, adapter and conformance remain undone | [repo-plane #2](https://github.com/dp-web4/repo-plane/pull/2): distinguish merged upstream design from pending local import |
| **P1** | Derived 4-hub mirror README | Says **7** roles, whereas [Hub's normative list](../../hub/docs/ROLES.md) and runtime's [Hub README](../../hub/README.md) list **8 base-mandatory roles**, including Maintainer | [web4 #951](https://github.com/dp-web4/web4/pull/951) **merged** (`a86f734b`) and Hub **republished** 4-hub: canonical and derived root now share blob `289ba30b12a73bb2938ae04f3365431ee814f46e` |
| **P1** | dp-web4 organization-profile landing | Same stale seven-role claim; authoritative Hub count is eight | [dp-web4 #3](https://github.com/dp-web4/dp-web4/pull/3) |
| **P1** | SAGE README and latest-status page | The README's research snapshot is Oct 23 and `LATEST_STATUS` is dated Sep 26. Merged gateway changes [#574](https://github.com/dp-web4/SAGE/pull/574), [#584](https://github.com/dp-web4/SAGE/pull/584), [#585](https://github.com/dp-web4/SAGE/pull/585) now deserve a source-level delta, without inferring per-host activation or behavioral learning. [#582](https://github.com/dp-web4/SAGE/issues/582) documents a distinct availability counterexample | [SAGE #587](https://github.com/dp-web4/SAGE/pull/587) |
| **P2** | sage-arc-collab landing and `INTEGRATION_STATUS.md` | April 1 checklist and “this week” integration measurements were still linked as **current**. Separate active SAGE from frozen spring ARC evidence | [sage-arc-collab #2](https://github.com/dp-web4/sage-arc-collab/pull/2) |

## Inspected and deliberately unchanged

- **Web4, Hestia, Hub, 4-gov, shared-context, Synchronism, ARC-SAGE, ai-dna-discovery, snarc, membot, dev-SAGE, SWE-SAGE, dev-hub, agent-atlas, agent-collab, blackbox, 4-life, portal, memory, web4-trust-core, ModBatt materials, hardware controllers:** sampled entry READMEs or associated current source. Many already distinguish implemented, simulated, historical and unverified; no date-only rewrite is evidence of improved correctness.
- **Abyss-Bright:** its README already explicitly scopes Sprout's then-limited tool use to **June 17, 2026**. Do not “correct” the historical result as though it were a present claim.
- **4-hub:** source-derived mirror, updated through Web4 `hub/mirror/`. For this sweep, Hub's merge and the matching canonical/downstream README blob are **actual republishing evidence**, not merely a proposed PR.
- **Hardware controller/product READMEs and Metalinxx historical strategy:** some describe “production-ready”, revenue and cell-count assertions. These require primary engineering/customer evidence; the sweep did not alter unsupported facts, and the Metalinxx landing now distinguishes them from current company claims.
- **Gnosis, qaid-rfc, DayDreamer, tracker forks and other upstream origins:** preserve upstream provenance and attribution. No silent conversion of tracking clones into products.

## Coverage limits / next verification queue

1. **Non-README website entry points**: `SAGE-site`, `synchronism-site`, `4-lab`, `ACT`, `web4-modbatt-demo` and some hardware repos had no root README through the file API. This is **not** evidence the project lacks a landing page. Inspect the actual site/app entrypoint and deployed URL before writing a corrective PR.
2. **Operational examples**: test live install commands, URLs and badges in a disposable environment; the sweep did not run third-party installers or presume packages are freshly published.
3. **Product assurance claims**: check `hardbound` README's “every actor / fail-closed” assertions against enforced paths and [hardbound #435](https://github.com/dp-web4/hardbound/issues/435). Avoid replacing one unsupported guarantee with another.
4. **Legacy extension compatibility**: `moltbot-web4-governance` still documents Moltbot configuration. Establish actual current OpenClaw compatibility and packaging first; do not advertise a migration without a passing install/runtime fixture.
5. **Prior audits remain historical**: compare [Oct 23 inventory](PUBLIC_LANDING_AUDIT_2026-10-23.md). Several earlier issues are already repaired (for example Abyss-Bright); do not duplicate closed work.

**Disposition checked after 2026-10-28 22:01 UTC:** seven independently reviewable documentation correction PRs opened; **Web4 #951 was approved and merged by Hub and its mirror README was republished and verified** during this sweep. The other six remain proposed until reviewed and merged. This audit itself is proposed in [Web4 #952](https://github.com/dp-web4/web4/pull/952). No Hestia gate law or autonomous being state was changed. A future sweep must recheck their exact heads and publication/deployment receipts.

Seat: NOVA (independent cross-repo audit).
