# Web4 Community Hub — Hub Law

Two distinct documents govern a chapter, and it's worth keeping them straight:

- The **charter** (`<chapter-dir>/charter.json`) is the constitutional preamble
  the Sovereign signs at founding. It's plain-text-with-structure (JSON) and its
  sha256 is pinned in `society.json`'s `charter_hash` field — tamper-evident, but
  prose. It says *who the chapter is*.
- **Hub law** is a separate, signed **YAML** document with a typed schema. It
  says *what the hub will and won't do*. Unlike the charter, hub law is
  **machine-readable and enforced**: the PolicyEntity gate evaluates every act and
  every gated read against it before anything commits.

This doc is about hub law — the enforced half.

## The law document

Hub law is a single YAML file matching `web4-standard/core-spec/hub-law-schema.md`,
parsed into the typed `Law` struct in `hub-lib/src/law.rs`. Top-level sections:

| Section | Shape | Purpose |
|---|---|---|
| `version` | semver string (required) | e.g. `"1.0.0"`. |
| `norms` | list | The atomic rules. Each is `selector`/`operator`/`value` → `decision`. |
| `procedures` | list | `requires_witnesses` / `requires_quorum` / `applies_to`. |
| `delegation` | object | `max_depth` (≥ 0), `requires_approval`, `allowed_roles`. |
| `escalation` | list | `condition` (an R6 expression) + `escalate_to` (a role). |
| `admission` | object | `open`, `requires_sponsor`, `sponsor_role`, `min_trust_score` (0–1). |
| `atp_issuance` | object | `mint_authority` (a role), `max_mint_per_cycle` (≥ 0), `distribution`. |
| `custom_predicates` | list | Community-defined predicates (reserved; not yet evaluated). |

### Norms

A norm is the atomic unit of law:

```yaml
norms:
  - id: ATP-LIMIT                 # unique within the file
    selector: r6.resource.atp     # what to look at on the request
    operator: ">"                 # how to compare
    value: 100                    # what to compare against
    decision: deny                # allow | warn | deny | escalate
    priority: 10                  # higher wins on conflict (default 0)
    description: "No single action may spend more than 100 ATP"
```

**Selectors** address the R6 request being evaluated:
`r6.role`, `r6.request.action`, `r6.request.payload.<field>` (dot-path into the
event payload), and `r6.resource.<key>` (quantifiable costs like `atp`,
`witness_count`). A selector that doesn't resolve means the norm simply doesn't
fire.

> **A norm that never fires is not an error — it is an allow.** Nothing in the
> stack distinguishes a norm that names something the gate never produces from a
> norm nobody wrote. Both leave the act on whatever the default is. This is why
> `r6.request.action` values must come from the table below rather than from
> intuition — and why `hub set-law` now **refuses** a law whose norms name an
> action the gate cannot emit (the daemon's load path warns instead, so an
> existing hub is never bricked by a law that predates the check).

### What `r6.request.action` can be

The action is the **HubEvent kind** — the past-tense name of the act that was
performed, not the imperative of the command that performed it. `role_assigned`,
not `assign_role`. `member_removed`, not `remove_member`. The CLI verb and the
event kind are different vocabularies and only the second one reaches law.

Canonical list: `HubEvent::ALL_EVENT_KINDS` (`hub-lib/src/events.rs`), kept in
lockstep with `HubEvent::kind()` by a test that reads the function's own source.

| group | actions |
|---|---|
| founding | `genesis`, `charter_amended`, `law_amended` |
| membership | `member_added`, `member_removed`, `member_admission_reset`, `member_key_pinned`, `member_profile_updated`, `member_skill_declared` |
| admission queue | `member_join_requested`, `member_join_resolved`, `member_join_review_requested`, `member_join_review_resolved` |
| roles | `role_assigned` |
| council | `council_member_added`, `council_member_removed`, `council_threshold_changed` |
| discussion | `topic_created`, `post_added` |
| pairing + channels | `pairing_requested`, `pairing_confirmed`, `pairing_revoked`, `pair_message_posted`, `intro_requested`, `intro_responded` |
| devices | `device_enrolled`, `device_revoked` |
| obligations + trust | `obligation_opened`, `obligation_resolved`, `reputation_recorded` |
| degraded-window audit | `degraded_reconciled` (F0.1: the witnessed summary of infrastructure-failure windows — recorded by the hub at ignition, never member conduct) |
| vault unlock (audit) | `vault_unlock_requested`, `vault_unlock_attested`, `vault_unlock_resolved` |
| records | `event_recorded`, `lct_published`, `referenced_act` |

**Two action families that are not event kinds**, and both are load-bearing:

- **`member_join_request`** — the join gate prices a request *before* any event
  exists, so it synthesises this action. Note it is **not** `member_join_requested`
  (which is the event written *after* the decision). The starter law's
  `ESCALATE-MEMBER-JOIN` norm uses this one.
- **`read:<tool>`** — read gating is namespaced so read norms cannot collide with
  act norms: `read:list_members`, `read:find_skill`, and so on.

**The nine operators** (schema §2): `<=`, `>=`, `==`, `!=`, `<`, `>`, `in`,
`not_in`, `matches`. The four comparison operators require both sides numeric.
`==`/`!=` use deep value equality. `in`/`not_in` expect a list. (`matches` —
regex — is reserved and currently a no-op.)

**Decisions**: `allow`, `warn`, `deny`, `escalate`. `allow` and `warn` are
non-blocking (the action proceeds; `warn` flags it as noteworthy — a
flagged-allow whose advisory text rides the winning norm's `description`);
`deny` and `escalate` block.

### Evaluation semantics

`Law::evaluate_outcome()` (the function the gate calls) works like this:

1. Every norm whose selector resolves and whose operator matches **fires**.
2. Among firing norms, the **highest `priority` wins** (ties broken by
   first-defined).
3. **`Deny` is terminal** — a winning Deny short-circuits; no escalation can
   override it. (A winning `Warn` is NOT terminal — it proceeds, like `Allow`.)
4. Otherwise, any matching `escalation` trigger produces `Escalate` (with its
   `escalate_to` role). A norm that resolves to `Escalate` but has no explicit
   target defaults to `sovereign`.
5. **Silence is consent**: if no norm and no trigger fires, the default is
   `Allow`. An empty law (just a `version`) allows everything — open by default.

## The CLI

There is a full law CLI (in `hub-daemon/src/main.rs`). It is *not* a hand-edit
workflow:

```bash
# 1. Write the starter template (embedded in the binary; validated on write)
hub init-law ./hub-law.yaml

# 2. Edit it, then apply it to a chapter. set-law parses + validates,
#    writes the signed YAML to chapter storage, and appends a witnessed
#    LawAmended event to the ledger.
hub set-law ./my-chapter ./hub-law.yaml --diff-summary "raise ATP ceiling"

# 3. Read back the law currently in force
hub get-law ./my-chapter

# If `hub serve` is running, reload the live law slot without a restart:
curl -X POST http://<host>/v1/admin/reload-law
# -> {"reloaded":true,"version":"1.0.0","law_integrity":"ok"}
```

**Check `law_integrity` in that reply, not just `reloaded`.** `reloaded: true`
only says the file parsed. `law_integrity` is the HUB-001 verdict — `ok`,
`mismatch`, or `unverifiable` — and `mismatch` means the hub is refusing every
governed write with a 409 because the law it serves diverges from the last
witnessed `LawAmended`. Without that field the first symptom is your *next* act
failing for reasons the response never mentioned.

> **`set-law` overwrites `<chapter-dir>/hub-law.yaml`.** The applied law is
> written into the chapter directory, so the copy that was there before is gone.
> Keep amendment files (and your pristine starter law) **outside** the chapter
> directory, or `hub init-law` a fresh template when you need the baseline back.

`hub init-law` ships a starter template (from `examples/starter-law.yaml`),
sanity-validated against the schema before it's written. `hub set-law` rejects
the file loudly on the first validation error — operators get one clear message
per fix (bad semver, duplicate norm id, unknown role, out-of-range trust score,
etc.), so malformed law never reaches the ledger.

## The PolicyEntity gate is live

The Law Oracle publishes the law; the **PolicyEntity** enforces it. This is not a
V2 aspiration — the gate runs today.

### On writes (every act)

Every act, before it commits, is turned into an `R6Request` and run through
`Law::evaluate_outcome()`. This happens in both transports:

- REST: `hub-daemon/src/rest.rs` (~L1697), and on the pair endpoints too.
- MCP: `hub-daemon/src/mcp.rs` (~L384).

The decision maps directly to HTTP status:

| Decision | Result |
|---|---|
| **Allow** | The act proceeds and commits to the ledger. |
| **Deny** | `HTTP 403` — the act is rejected (response names the winning norm). |
| **Escalate** | `HTTP 202` — held for review by the `escalate_to` role; not committed. |

If no law is loaded, acts proceed (open-by-default) — the same behavior as before
a chapter sets law.

### On reads (gated queries)

The PolicyEntity gates queries the same way it gates writes (schema §8). Channel
read tools run through `gate_read()` (rest.rs), which evaluates a request with
`action = "read:<tool>"` — e.g. `read:find_members`. Read actions are namespaced
with the `read:` prefix so a read norm can never collide with an act (event-kind)
norm. Same Allow/Deny/Escalate → proceed/403/202 mapping. This is how a chapter
restricts *who can run member discovery*, scoped per tier.

### Admission via law

Joining is admission-by-law. A join request (the encrypted
`request_citizenship` path, and the plaintext `/members/join`) is evaluated with
`action = member_join_request`, `role = applicant`:

- **Allow** → the applicant is auto-admitted (the Sovereign signs a `MemberAdded`
  pinning their pubkey; they're added to the resolver so their next channel is as
  a citizen).
- **Deny** → `HTTP 403`, rejected.
- **Escalate** → a `MemberJoinRequested` event is **witnessed** with status
  `pending_review`, and the applicant gets a `request_id` to poll. That witnessed
  pending event *is* the admission queue the operator actions — nothing is
  silently dropped.

The `admission` section of the law (`open`, `requires_sponsor`, `sponsor_role`,
`min_trust_score`) is the natural place to express this, but any norm matching
`r6.request.action == "member_join_request"` participates.

## Audit trail

Law is always signed and auditable — the hub binary contains no hardcoded policy;
it's a law interpreter. Every `hub set-law` appends a `LawAmended` ledger event
carrying `new_law_sha256` (the canonical sha256 of the YAML), `version`,
`amended_by`, and an optional `diff_summary`. Because every amendment is on the
chain with its hash, any party can walk the ledger, follow the `LawAmended`
events, and reconstruct exactly which law was in force at any historical point.

## What hub law should cover (suggested topics)

The schema gives you the mechanism; the policy is yours. A practical starter set
of topics to encode:

### Member admission

- Who can become a Citizen? (`admission.open`, `requires_sponsor`.)
- What's the gate? Auto-admit, sponsor-required, or queue-for-review (Escalate)?
- What minimum trust, if any? (`admission.min_trust_score`.)

### Member departure + removal

- Involuntary removal: under what conditions, and who decides? Encode as a norm
  on `r6.request.action == "member_removed"` — Deny outright, or Escalate to
  Sovereign.

### Role rotation

- Who can assign roles? A common pattern: `r6.request.action == "role_assigned"` →
  `escalate` to Sovereign or Administrator. Past tense — see the action table
  above; `assign_role` is the CLI verb and matches nothing. (The assignee LCT
  still signs acceptance — enforced by `hub assign-role` independent of law.)

### Treasury policy

- Who mints ATP and how much per cycle? (`atp_issuance.mint_authority`,
  `max_mint_per_cycle`.)
- Cap single-action spend with a norm on `r6.resource.atp`.

### Events + consequential actions

- Require independent witnesses or a quorum for weighty acts
  (`procedures.requires_witnesses` / `requires_quorum`, scoped by `applies_to`).

### Discussion

The hub carries a governed discussion surface (`/discuss`, `/v1/hubs/:id/topics`).
Opening a topic and posting to one are ordinary law-gated acts — `topic_created`
and `post_added`.

**The starter law names neither**, so today both fall to `DEFAULT-ALLOW`: anyone
who can sign an envelope can open a topic. That is a default nobody chose, and
the starter law's own comment asks the next author to extend the list as new
consequential kinds land. Worth deciding explicitly, e.g.:

```yaml
  - id: ALLOW-POSTING
    selector: r6.request.action
    operator: "=="
    value: post_added
    decision: allow
    priority: 60
    description: "Speaking in an existing topic is a right of membership."

  - id: ESCALATE-TOPIC-OPEN
    selector: r6.request.action
    operator: "=="
    value: topic_created
    decision: escalate
    priority: 60
    description: "Opening a topic sets the agenda — Sovereign review."
```

Posts are ledger entries, so a law change here is visible in the record: the
refusal names the norm that produced it.

### Escalation + delegation

- Which conditions always go to a human? (`escalation` triggers, e.g.
  `"r6.resource.atp > 50" → escalate_to: sovereign`.)
- How deep may authority be delegated, and to which roles?
  (`delegation.max_depth`, `allowed_roles`.)

### Federation

- Posture toward other chapters, and how imported reputation is weighted. The
  schema's `custom_predicates` slot is reserved for chapter-specific predicates
  the cross-chapter exchange will exercise.

## What hub law is NOT

- Not a binding legal document outside the chapter's own membership.
- Not a substitute for actual law (employment, finance, etc.) where applicable.
- Not the charter. The charter is signed prose; hub law is the enforced,
  machine-readable rules. They reference each other but are distinct documents.

## Template

`hub init-law` writes a validated starter. A community chapter's law might look
like:

```yaml
version: "1.0.0"

norms:
  - id: ATP-CEILING
    selector: r6.resource.atp
    operator: ">"
    value: 100
    decision: deny
    priority: 10
    description: "No single action may spend more than 100 ATP"

  - id: ROLE-ASSIGNMENT-REVIEW
    selector: r6.request.action
    operator: "=="
    value: role_assigned
    decision: escalate
    priority: 20
    description: "Role assignment is reviewed by the Sovereign"

procedures:
  - id: WITNESS-3
    requires_witnesses: 3
    applies_to: "consequential_actions"

escalation:
  - condition: "r6.resource.atp > 50"
    escalate_to: sovereign
    description: "High-ATP actions escalate to Sovereign"
  - condition: "r6.request.action == 'amend_charter'"
    escalate_to: sovereign

admission:
  open: false
  requires_sponsor: true
  sponsor_role: citizen
  min_trust_score: 0.3
  description: "Closed admission — an existing citizen must sponsor"

atp_issuance:
  mint_authority: treasurer
  max_mint_per_cycle: 1000
  distribution: proportional_to_contribution
```

Adapt it to your chapter, then `hub set-law` it. The hub witnesses the amendment
and enforces the result; the deciding is yours.
