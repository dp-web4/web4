# Web4 Community Hub — Society Roles

The Web4 standard defines **7 base-mandatory roles** every society must fill, plus 2 context-mandatory roles, plus an open Custom role slot. The hub uses these directly (from `web4_core::role::SocietyRole`); the chapter doesn't invent its own role taxonomy.

## The 7 base-mandatory roles

| Role | Job |
|---|---|
| **Sovereign** | Final authority for charter amendment, identity recovery, extraordinary inter-society decisions. The chapter's last line of accountability. |
| **Law Oracle** | Publishes machine-readable laws, signs interpretations, answers compliance queries. *Not* a decision-maker — an oracle the Policy Entity consults. |
| **Policy Entity** | Takes R6/R7 action requests, evaluates against Law Oracle's laws, returns approve/deny/escalate with reasoning. The enforcement arm. |
| **Treasurer** | Operates the treasury: mints ATP, allocates per law, accounts for ATP/ADP flows. Conservation invariant: sum(ATP) + sum(ADP) = const. |
| **Administrator** | Operational execution: citizen lifecycle, R6/R7 dispatch routing, infrastructure liveness. Day-to-day chapter ops. |
| **Archivist** | Maintains ledger writes, chain integrity, retention policy, historical queries. The chapter's memory. |
| **Citizen** | Base membership role. Every entity holds Citizen first; other roles layer on top. Genesis role — immutable once granted. |

## Context-mandatory roles

| Role | When required |
|---|---|
| **Witness** | Mandatory when outward-facing roles exist (i.e. when your chapter interacts with other societies). Provides independent attestation. |
| **Auditor** | Mandatory when the chapter issues trust attestations (T3/V3) that other societies consume. |

## Optional / custom

`SocietyRole::Custom(String)` — your chapter can define additional roles with arbitrary names + authority scopes (e.g. `Custom("DemoNightLead")`, `Custom("MentorshipCoordinator")`).

## Fractal composability — multiple hats per person

> Per the Web4 spec: a role can be filled by a single entity, a sub-society, or a federation of societies.

In practice for an MVP chapter:

- **Solo founder pattern**: one person initially holds all 7 roles. `hub init` does this automatically — the Sovereign LCT fills every role at genesis. This is the default and is the right shape for a chapter just starting.
- **Small chapter pattern (3-5 active members)**: split into 2-3 role buckets. Sovereign + Law Oracle on one person; Treasurer + Administrator on another; Archivist + Policy Entity on a third. Citizen is everyone.
- **Mature chapter pattern (10+ active members)**: each base role has a dedicated filler. Custom roles emerge for chapter-specific functions.

## Assigning a role to someone else

```bash
hub assign-role <chapter-dir> <role-name> <role-lct-id> <member-lct-id>
```

Example: delegating Treasurer to Alice (assuming you ran `hub init` earlier and saved the role LCT ids):

```bash
hub assign-role ./my-chapter treasurer 5ce1c40d-ac65-413b-8f18-2ecb165a1797 $ALICE_ID
```

The role LCT id stays stable — when you rotate the Treasurer to Bob later, the role's LCT (and its accrued T3) follows. The *filling entity* changes; the *role identity* doesn't. This is what "authority binds to the role, not the entity" means structurally.

## When to delegate

A few heuristics:

- **Delegate Treasurer first** if your chapter is taking in any sponsorship money. Single-person treasury is operationally fine but socially risky.
- **Delegate Archivist** if your event cadence is high enough that someone other than you should own the witnessed record (e.g. recording event attendance after each meetup).
- **Delegate Witness** the moment your chapter starts interacting with other chapters (federation requests, joint events, etc.). Independent attestation matters more once trust flows cross-chapter.
- **Sovereign stays solo for a while** unless you specifically want a multi-key constitutional signing setup.

## What the role LCTs are good for

Each role's LCT can independently:
- Sign role-scoped actions
- Accrue T3 (Talent / Training / Temperament) for performance of that role
- Be rotated to a new filling entity without breaking the chapter's accountability chain
- Be inspected via `hub query chapter <chapter-dir>` (which shows role-id ↔ filler-id pairs)

In MVP, the daemon signs all ledger entries with the Sovereign keypair regardless of which role "did" the action (the event's `assigned_by`/`recorded_by` field captures the actor at the data layer). V2 will let each role-filler hold their own keypair and sign role-scoped events directly.
