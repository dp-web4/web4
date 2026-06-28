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

For single-signer acts, the daemon commits ledger entries under the founding
Sovereign's executor signature regardless of which role "did" the action (the
event's `assigned_by`/`recorded_by` field captures the actor at the data layer).
That's *not* the whole story, though: on the **council path**, co-Sovereign
holders hold their **own** keypairs and counter-sign acts via
`SignedEnvelope`s. Each vote is a full, independently verifiable envelope, and
`CouncilProposal::unique_signers()` counts distinct holder signatures toward the
M-of-N threshold (see `hub-lib/src/proposal.rs`). So role-fillers holding their
own keys and signing directly is already real for the Sovereign Council — see
below.

## Sovereign Council — multi-Sovereign M-of-N

A chapter need not have a single founder holding the Sovereign key forever. The
**Sovereign Council** is a set of co-Sovereigns who jointly authorize chapter
acts under an M-of-N threshold.

State (`hub-lib/src/state.rs`):

- `council_holders` — the co-Sovereign LCT ids beyond the founding Sovereign.
- `council_pubkeys` — each holder's pinned public key, so their envelopes verify
  without an external registry.
- `council_threshold` — `(m, n)` where **N is derived as `holders + 1`** (the
  founding Sovereign always counts as one holder). Removing a holder re-derives
  N and clamps M down if needed.

Events (ledger-audited): `CouncilMemberAdded`, `CouncilMemberRemoved`,
`CouncilThresholdChanged`.

CLI:

```bash
hub council add <chapter-dir> <member-lct-id> --pubkey <hex> [--name ...]
hub council remove <chapter-dir> <member-lct-id> [--kind resigned|ejected|elected] [--reason ...]
hub council set-threshold <chapter-dir> <m>      # N derived from holders + 1
hub council show <chapter-dir>
```

### The propose / sign flow

When the threshold is **1-of-N** (or no threshold is set), single-signer commits
still work — the act commits on first signature, with a council audit trail.

When the threshold is **M ≥ 2**, single-signer commits are **blocked**: the
`/events` and pair endpoints return `HTTP 409` and redirect callers to the
council flow. Acts then aggregate counter-signatures:

| Endpoint | Purpose |
|---|---|
| `POST /v1/hubs/:id/council/propose` | A holder proposes an act (their envelope is the first vote). |
| `POST /v1/hubs/:id/council/sign` | Another holder counter-signs an open proposal by id. |
| `GET /v1/hubs/:id/council/proposals` | List proposals. |
| `GET /v1/hubs/:id/council/proposals/:id` | Inspect one proposal. |

Each signature is a `SignedEnvelope` stored in the proposal (not a bare
signature), so every vote stays independently re-verifiable after the fact. Only
council holders (including the founding Sovereign) may propose or sign; members
cannot. When unique holder signatures reach M, the hub appends the proposed event
to the ledger and marks the proposal `Committed` with the resulting
`entry_index`. Proposals expire after a TTL (default 24h) if the threshold isn't
met.
