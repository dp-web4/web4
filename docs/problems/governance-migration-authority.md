# Governance migration without laundering authority drift

## The problem

Governance systems evolve. Roles, councils, delegations and approval rules may move from one representation to another while the old mechanism is still live.

A dangerous migration failure is not only data loss. It is **normalizing a defect**: the old system may already be enforcing the wrong authority, and a naive migration can faithfully copy that wrong effective state into the new design.

The question is:

> **How do we move authority without silently treating an old governance defect as the intended constitution?**

## Failure mode

A legacy system's effective state is copied as truth:

```text
intended rule: 3-of-3
one holder leaves -> legacy clamps to 2-of-2
holder returns -> legacy remains 2-of-3
migration copies "2" -> old defect becomes new constitution
```

The migration can then report success precisely because it made the two systems agree by laundering the defect.

## Web4 / Hub mechanism

Hub's council-to-role migration uses a **dual-read differential** rather than a boolean “same/different” check.

The differential names why the old and new representations disagree. In Web4 #848, one disagreement class is explicit:

- `LegacyClampedThreshold`

The new role-side representation keeps the originally requested quorum instead of inheriting the clamped legacy value. Cutover is allowed only when holder sets match exactly and the remaining threshold difference is the known legacy-clamp class.

Web4 #850 then adds the operational migration surface and safety properties around it:

- law protection is written before the mirror;
- role-side counterparts are gated before legacy changes append;
- the live differential is exposed for cutover evidence;
- the public roles/council views share one authority reading instead of presenting contradictory counts.

## Status

**Implemented, not yet authoritative** at the evidence point represented by #848/#850.

The role-tree substrate and live differential exist, but the PR record explicitly says succession/cutover is not authoritative while the legacy gate still controls the relevant authority path.

That distinction is part of the proof, not a caveat to hide.

## Public evidence

### Web4 #848 — defect-aware differential

PR **#848** drives the legacy quorum defect in a test:

1. 3 holders, threshold 3;
2. one resigns -> legacy becomes 2-of-2;
3. holder returns -> legacy remains 2-of-3;
4. new role tree remains N=3, O=3, M=3.

The migration differential distinguishes the legacy clamp from unacceptable holder-set or required-signature divergence.

Merge commit:

```text
6f3796eb75cf2836788aa37c4c179459348ec038
```

### Web4 #850 — coupled-act migration and adversarial HOLD

PR **#850** records an adversarial review finding that the mirror endpoint performed two consequential acts while initially preflighting only one. The repair gates the law amendment under the law then in force, orders law-before-mirror, and adds falsifiers/induced failures for the migration properties.

Merge commit:

```text
1bad034e3f9a8e7fedd6f51a7d348c64ee2f11ea
```

A later descendant integration merge, #851, preserved the #850 test block and reported the full Hub suites green after rebasing on later main.

## What this evidence establishes

- a concrete legacy authority defect was measured rather than assumed;
- the migration does not silently copy the defective effective threshold as intended law;
- disagreement is typed, so expected legacy defect can be distinguished from unsafe migration drift;
- the migration path contains falsifiers intended to fail if ordering/gating protections disappear;
- implementation state is explicitly separated from authority cutover state.

## What it does NOT establish

- that the role representation is already authoritative for all council decisions;
- that every possible legacy defect has a named differential class;
- that every future migration endpoint is automatically safe;
- that operator-plane law amendment is fully council-governed in all states — #850 records this as open work;
- that later refactors preserve the same properties without rerun evidence.

## Inspect it

- #848: https://github.com/dp-web4/web4/pull/848
- #850: https://github.com/dp-web4/web4/pull/850
- Hub source: [`../../hub/`](../../hub/)
- Current project status: [`../../STATUS.md`](../../STATUS.md)

## Related problems

- [Policy must bind the action, not only one interface](policy-must-bind-the-action.md)
- [Persistent identity for long-lived AI agents](persistent-agent-identity.md)
