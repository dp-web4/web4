# Policy must bind the action, not only one interface

## The problem

An AI or human actor can often reach the same consequential operation through more than one path: a normal API, a multi-signer workflow, an admin surface, a plugin host, a delegated route, or a later migration path.

A policy system can look correct while still being bypassable if only the most common interface evaluates the actual rules.

The question is:

> **If two paths can perform the same act, does the law bind the act on both paths?**

## Failure mode

Path-dependent governance:

```text
normal path -> law says DENY -> refused
alternate path -> checks identity/quorum only -> commits same act
```

That is not a policy exception. It is a policy bypass caused by the enforcement boundary being attached to an interface rather than the consequential act.

## Web4 / Hub mechanism

Hub law is intended to govern consequential acts before they commit, regardless of which authority path submits them.

The council path therefore evaluates the same law norms used by the single-signer path:

- when a proposal is opened; and
- again when it commits, because law may change while signatures accumulate.

The shared mechanism is more important than the specific API: alternate paths should not carry independent interpretations of the same law.

## Status

**Implemented in Hub and merged.**

This page does **not** claim every possible alternate path in Web4/Hestia/SAGE has been proven equivalent, nor that the merged repair was immediately live on every fleet deployment.

## Public evidence

Web4 PR **#849** — `hub: hub law binds the council path — a proposal could commit what the law denies`

Merge commit:

```text
82dfa9899ca39c75e80a9ed00e5b446398f62f2f
```

The PR records the defect **red first**:

1. the single-signer gate refused an act with HTTP 403;
2. the same act, routed through a council-holder proposal, committed on unpatched main.

The repair moved norm evaluation into shared logic and applied it at proposal-open and commit time.

The PR also names induced failures:

- remove proposal-time law evaluation -> test fails;
- remove commit-time current-law evaluation -> test fails;
- change the chosen escalation semantics -> explicit test fails.

A later descendant Hub integration merge, Web4 **#851**, preserved the #849/#850 test blocks and reported the full Hub suites green after rebasing on later main.

## What this evidence establishes

- a real alternate-path governance bypass existed in the tested Hub implementation;
- the bypass was demonstrated before repair rather than inferred only from code review;
- the repaired council path evaluates the same law family as the single-signer path;
- proposal-time and commit-time enforcement have discriminating tests;
- the public record preserves that the earlier broad documentation claim was false for this path.

## What it does NOT establish

- every action route in the full Web4 stack has equivalent enforcement;
- all future plugin/admin/delegation paths automatically inherit this property;
- current live deployment state on every machine;
- A2+ containment against an adversarial same-UID process;
- that Hestia's A1 gate cannot be routed around outside its governed action paths.

## Inspect it

- PR: https://github.com/dp-web4/web4/pull/849
- Hub source: [`../../hub/`](../../hub/)
- Current project status: [`../../STATUS.md`](../../STATUS.md)

## Related problems

- [Governance migration without laundering authority drift](governance-migration-authority.md)
- [Persistent identity for long-lived AI agents](persistent-agent-identity.md)
