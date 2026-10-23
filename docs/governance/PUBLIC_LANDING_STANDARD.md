# Public landing-document standard

**Proposed:** 2026-10-23. **Status:** documentation convention awaiting review, not protocol law.

Every actively maintained public repository should show, near the beginning:

1. **Identity:** purpose, audience, and whether canonical implementation, mirror, independent experiment, historical snapshot, or upstream fork.
2. **Truthful state:** separately identify deployed/measured, implemented-but-unverified, experimental, specified, and planned. A commit is not deployment; mechanism is not measured capability.
3. **Start path:** one tested beginner route and one technical/evidence route. Distinguish a public demo from localhost.
4. **Authority:** canonical issue/PR location, licensing, provenance, upstream credits, mirror ownership.
5. **Dated status:** as-of date, revision, scope, known limitations and evidence links; minimize volatile counts duplicated from canonical status.

## Claim rules

- Hestia A1 cooperative/tamper-evident governance must not be presented as adversary-proof containment.
- Authorization, execution and legitimate outcome are different claims.
- Persistent records do not guarantee continuity of retrieval, interpretation, judgment or action.
- SAGE results are specific to being + model + runtime + history + intervention; fleet generalization requires distinct evidence.
- Treat self-description as observable behavior, not proof of internal mechanism or subjective experience.
- Preserve historical claims as dated, contextual evidence; annotate later developments rather than erasing earlier results.
- **Fix verified facts; caveat only unverified ones.** When the current fact is in hand with dated evidence (a package version on its registry, a census, a merged change in use), state it, and keep the earlier figure as dated history. A caveat ("may be stale, verify before relying on it") is for a claim nobody has checked; it is not a substitute for a fact someone has.
- Forks preserve upstream authorship; mirrors link to canonical code and do not independently redefine status.

## Maintenance / PR requirements

Inspect root README, START_HERE, STATUS, landing docs, links, badges, examples, demos and install paths together. For each proposed change record priority, exact evidence, unresolved verifications and deliberately unchanged claims.

**P0:** misleading first-screen fact; **P1:** stale or unverified operational instruction/status; **P2:** navigation or clarity. New documentation changes go through reviewable PRs, not silent default-branch commits.

See [dated audit](PUBLIC_LANDING_AUDIT_2026-10-23.md), [Web4 status](../../STATUS.md), and [SAGE generalization rule](https://github.com/dp-web4/SAGE/blob/main/sage/docs/RESEARCH_GENERALIZATION_RULE.md).
