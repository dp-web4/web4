# R6 Implementation Guide: Hardbound in Practice

## Overview

This guide demonstrates how the R6 framework is implemented in Hardbound,
using a realistic AI agent (moltbot) scenario. It covers the full lifecycle
from team creation through request, approval, execution, and result tracking.

## Architecture

```
Team
 ├── Admin (hardware-bound identity)
 ├── Members (AI agents, humans - each with LCT)
 ├── Policy (rules governing what actions are allowed)
 ├── R6 Workflow (request lifecycle management)
 │   ├── SQLite persistence (survives restart)
 │   ├── Multi-sig delegation (critical actions)
 │   └── Heartbeat integration (metabolic tracking)
 ├── Multi-Sig Manager (collective governance)
 │   └── Federation (cross-team witnessing)
 └── Heartbeat Ledger (metabolic state + block sealing)
```

## Tier 1: Single-Agent R6 (moltbot)

### Scenario: AI Code Review Agent

moltbot is an AI agent that performs automated code reviews. It operates
within a governed team, requesting permission for each review via R6.

### Step 1: Team Setup

```python
from hardbound.team import Team, TeamConfig
from hardbound.policy import Policy, PolicyRule, ApprovalType
from hardbound.r6 import R6Workflow

# Create the team
config = TeamConfig(
    name="acme-engineering",
    description="Acme Corp engineering team",
    default_member_budget=200,  # ATP per member
)
team = Team(config=config)

# Bind admin (typically hardware-bound in production)
team.set_admin("lct:admin:alice")

# Add moltbot as a team member
team.add_member("lct:agent:moltbot", role="reviewer", atp_budget=500)

# Add human developers
team.add_member("lct:human:bob", role="developer", atp_budget=100)
team.add_member("lct:human:carol", role="developer", atp_budget=100)
```

### Step 2: Define Policy

```python
policy = Policy()

# Code review: low cost, admin approval
policy.add_rule(PolicyRule(
    action_type="code_review",
    allowed_roles=["reviewer", "admin"],
    trust_threshold=0.3,
    atp_cost=5,
    approval=ApprovalType.ADMIN,
    description="Automated code review on a pull request",
))

# Deployment: higher cost, multi-sig required
policy.add_rule(PolicyRule(
    action_type="deploy",
    allowed_roles=["deployer", "admin"],
    trust_threshold=0.7,
    atp_cost=25,
    approval=ApprovalType.MULTI_SIG,
    approval_count=2,
    description="Deploy to production environment",
))

# Secret rotation: critical action, multi-sig + external witness
policy.add_rule(PolicyRule(
    action_type="secret_rotation",
    allowed_roles=["admin"],
    trust_threshold=0.85,
    atp_cost=50,
    approval=ApprovalType.MULTI_SIG,
    approval_count=3,
    description="Rotate API keys and credentials",
))
```

### Step 3: R6 Request Lifecycle

```python
# Initialize R6 workflow
wf = R6Workflow(team, policy)

# moltbot creates a code review request
request = wf.create_request(
    requester_lct="lct:agent:moltbot",
    action_type="code_review",
    description="Review PR #142: Add user auth middleware",
    target="github.com/acme/backend/pull/142",
    parameters={
        "repo": "acme/backend",
        "pr_number": 142,
        "files_changed": 12,
    },
    reference_type="pull_request",
    reference_id="PR-142",
)

print(f"R6 ID: {request.r6_id}")
print(f"Status: {request.status.value}")  # "pending"
print(f"ATP cost: {request.atp_cost}")    # 5
```

### Step 4: Approval

```python
# Admin approves the request
response = wf.approve_request(request.r6_id, "lct:admin:alice")
print(f"Status: {response.status.value}")  # "approved"

# moltbot's trust is checked automatically during approval:
# - Role "reviewer" is allowed for "code_review" ✓
# - Trust score >= 0.3 threshold ✓
# - ATP budget >= 5 cost ✓
```

### Step 5: Execution

```python
# moltbot performs the review and reports result
result = wf.execute_request(
    request.r6_id,
    success=True,
    result_data={
        "findings": 3,
        "severity": "low",
        "approved": True,
        "comments_posted": 5,
    },
)

print(f"Status: {result.status.value}")      # "executed"
print(f"ATP consumed: {result.atp_consumed}") # 5
print(f"Trust delta: {result.trust_delta}")   # positive (success)
```

### Step 6: What Happened Behind the Scenes

1. **R6 created**: Persisted to SQLite, submitted to heartbeat ledger
2. **Policy checked**: Role, trust threshold, ATP verified
3. **Admin approved**: Trust-weighted approval recorded in audit trail
4. **ATP consumed**: 5 ATP deducted from moltbot's budget
5. **Execution recorded**: Result + heartbeat transaction + audit entry
6. **Trust updated**: moltbot's trust increases slightly (successful review)
7. **ATP reward**: Partial ATP returned (success reward = cost/2)

## Tier 2: Multi-Agent R6 with Multi-Sig

### Scenario: Production Deployment

Two agents collaborate on a deployment that requires multi-sig approval.

```python
from hardbound.multisig import MultiSigManager

msig = MultiSigManager(team)
wf = R6Workflow(team, policy, multisig=msig)

# moltbot requests a deployment (MULTI_SIG approval required)
deploy_req = wf.create_request(
    requester_lct="lct:agent:moltbot",
    action_type="deploy",
    description="Deploy v2.3.1 to production",
    parameters={
        "version": "2.3.1",
        "environment": "production",
        "rollback_plan": "v2.3.0",
    },
)

# Because policy says MULTI_SIG and action_type="deploy" doesn't map to a
# CriticalAction, approval uses count-based multi-sig (no linked proposal).
# Two approvals needed:

wf.approve_request(deploy_req.r6_id, "lct:admin:alice")  # 1st approval
wf.approve_request(deploy_req.r6_id, "lct:human:bob")    # 2nd approval → APPROVED

# Execute
wf.execute_request(deploy_req.r6_id, success=True)
```

### Multi-Sig Delegation for Critical Actions

When the action type maps to a `CriticalAction`, R6 auto-creates a linked
multi-sig Proposal with full voting, external witnessing, and voting periods:

```python
# Secret rotation maps to CriticalAction.SECRET_ROTATION
rotate_req = wf.create_request(
    requester_lct="lct:admin:alice",
    action_type="secret_rotation",
    description="Rotate GitHub PAT",
    parameters={"secret_type": "github_pat"},
)

# A multi-sig proposal was auto-created
print(f"Linked proposal: {rotate_req.linked_proposal_id}")  # "msig:..."

# Approvals now go through the multi-sig voting system
# (external witnesses required for secret rotation)
```

## Tier 3: Federated R6 with Cross-Team Witnessing

### Scenario: Governance Action with External Accountability

```python
from hardbound.federation import FederationRegistry

# Set up federation
fed = FederationRegistry()
fed.register_team(team.team_id, "Acme Engineering", creator_lct="lct:admin:alice")
fed.register_team("team:audit-corp", "Audit Corp", creator_lct="lct:admin:eve")

# Multi-sig manager with federation
msig = MultiSigManager(team, federation=fed)

# For admin transfers, the federation auto-selects witnesses:
witnesses = fed.select_witnesses(
    team.team_id,
    count=1,  # Admin transfer needs 1 external witness
    seed=None,  # Random selection (deterministic with seed)
)

# Witnesses are reputation-weighted: higher-scored teams are more
# likely to be selected, preventing witness concentration.
```

## R6 Cancellation

Requesters can cancel their own pending requests:

```python
request = wf.create_request(
    requester_lct="lct:agent:moltbot",
    action_type="code_review",
    description="Review PR #200",
)

# moltbot realizes the PR was already merged
wf.cancel_request(request.r6_id, "lct:agent:moltbot", reason="PR already merged")
# No trust penalty, no ATP consumed
```

## Persistence

R6 requests survive process restarts:

```python
# Create request in one workflow instance
wf1 = R6Workflow(team, policy)
request = wf1.create_request(...)

# Simulate restart: create new workflow instance
wf2 = R6Workflow(team, policy)
reloaded = wf2.get_request(request.r6_id)
assert reloaded is not None  # ✓ Request persisted in SQLite
```

## Defense Stack

The R6 implementation includes comprehensive defenses:

| Defense | Component | Attack Mitigated |
|---------|-----------|-----------------|
| Trust velocity caps | team.py | Rapid trust inflation |
| Diminishing witness returns | team.py | Mutual witness farming |
| Post-rejoin cooldown (72h) | team.py | Witness cycling |
| Sybil detection (4 signals) | sybil_detection.py | Fake member creation |
| Cross-team Sybil detection | sybil_detection.py | Multi-team Sybil rings |
| External witness requirement | multisig.py | Single-team governance capture |
| Witness diversity | multisig.py | Colluding team witnesses |
| Federation collusion detection | federation.py | Witness reciprocity |
| Creator lineage tracking | federation.py | Shell team creation |
| Member overlap analysis | federation.py | Shared LCT detection |
| Pattern signing (HMAC-SHA256) | federation.py | Report tampering |
| Federation health dashboard | federation.py | Aggregate risk assessment |
| Reputation-weighted selection | federation.py | Witness concentration |
| Activity quality scoring | activity_quality.py | Micro-ping gaming |
| ATP exhaustion guards | team.py | Resource drain |

## Test Coverage

93 tests validate the full R6 lifecycle including:
- Request creation, approval, rejection, execution, cancellation
- SQLite persistence across workflow instances
- Multi-sig delegation with linked proposals
- Heartbeat ledger integration
- ATP economics (consumption, rewards, exhaustion)
- 10 attack simulations (9 defended)

---

*"In Hardbound, every action has a story: who wanted it, what policy allowed it,
who approved it, what it cost, and what it achieved. R6 is that story."*
