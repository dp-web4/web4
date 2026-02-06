# Team-Society Mapping: Enterprise Terminology for Web4 Governance

**Created**: 2026-02-06
**Status**: Reference Architecture

This document maps Web4's distributed society concepts to enterprise-friendly terminology used in the Hardbound implementation.

---

## Core Terminology Mapping

| Web4 Society Concept | Enterprise (Hardbound) Term | Description |
|---------------------|---------------------------|-------------|
| **Society** | **Team** | A governed organization of entities |
| **Blockchain** | **Ledger** | Immutable record store |
| **Citizen** | **Member** | Entity participating in the team |
| **Law Oracle** | **Admin** | Hardware-bound governance authority |
| **Consensus** | **Verification** | Agreement protocol |
| **Genesis Block** | **Team Creation** | Initial ledger entry |
| **Transaction** | **Action** | Recorded change to team state |
| **Smart Contract** | **Policy** | Encoded rules for behavior |

---

## Component Architecture

### Web4 Society Structure → Hardbound Team Structure

```
Society (root LCT)              →  Team (root LCT: web4:team:XXXX)
├── Blockchain                  →  ├── Ledger (SQLite, hash-chained)
│   ├── Blocks                  →  │   ├── Heartbeats (metabolic blocks)
│   ├── Transactions            →  │   ├── audit_trail (hash-linked)
│   └── Consensus               →  │   └── Verification (signatures)
├── Law Oracle                  →  ├── Admin (TPM2/software bound)
│   ├── Key management          →  │   ├── admin_bindings
│   └── Judgment                →  │   └── Policy enforcement
├── Citizens                    →  ├── Members
│   ├── Identity (LCT)          →  │   ├── Identity (LCT)
│   ├── Reputation              →  │   ├── Trust tensor (6D)
│   └── Rights                  →  │   └── Roles
├── Laws                        →  ├── Policy
│   ├── Constitution            →  │   ├── Default rules
│   └── Bylaws                  →  │   └── PolicyStore (versioned)
└── Treasury                    →  └── ATP Economy
    ├── Token supply            →      ├── Team budget
    └── Distribution            →      └── Member allocations
```

---

## 9 Core Components Implementation Status

| # | Component | File | Status | Description |
|---|-----------|------|--------|-------------|
| 1 | Team Root LCT | `team.py:393-407` | ✅ | SHA256-based team identity |
| 2 | Ledger | `ledger.py` | ✅ | SQLite + hash-chain witnessing |
| 3 | Admin Role | `admin_binding.py` | ✅ | Role definition and enforcement |
| 4 | Hardware Binding | `admin_binding.py:150-212` | ✅ | TPM2 attestation support |
| 5 | Member LCTs | `member.py`, `team.py:656-867` | ✅ | Identity + roles + budgets |
| 6 | Policy Engine | `policy.py` | ✅ | Rules + versioning + enforcement |
| 7 | R6 Workflow | `r6.py` | ✅ | Request → Approval → Execution |
| 8 | ATP Tracking | `team.py:868-1036` | ✅ | Budget allocation + consumption |
| 9 | Audit Trail | `ledger.py:356-434` | ✅ | Hash-chain verification |

**All 9 core components are implemented in `/simulations/`**

---

## Key Architectural Concepts

### 1. Team as Entity

A team IS an entity in Web4:
- Has its own LCT (`web4:team:{hash}`)
- Can be a member of other teams (fractal structure)
- Accumulates its own trust through witnessed actions
- Dies if no members remain

### 2. Hardware-Bound Admin

The Admin role differs from regular members:
- **TPM2 binding**: Cryptographic proof of specific hardware
- **Software binding**: Development mode with trust ceiling (0.7)
- **Trust ceiling**: TPM2 = 1.0, Software = 0.7
- **Cannot be delegated**: Only transferred through multi-sig

### 3. Heartbeat-Driven Ledger

Blocks don't follow fixed intervals:
- **Metabolic states**: ACTIVE → REST → SLEEP → HIBERNATION
- **State-adaptive intervals**: 60s (active) → 7200s (torpor)
- **Trust decay multipliers**: Higher decay in dormant states
- **Activity drives blocks**: Not clock time

### 4. R6 Workflow (Enterprise Actions)

Every significant action flows through R6:

```
1. Member submits R6Request
   ├── Rules: Which policy applies
   ├── Role: Member's role in team
   ├── Request: What they want to do
   ├── Reference: Context (diff, issue, etc.)
   ├── Resource: ATP cost estimate
   └── (implicit) Result: Pending

2. Admin processes via policy
   ├── Check trust thresholds
   ├── Check ATP balance
   ├── Apply policy rules
   └── May require additional approvals

3. Admin closes R6
   ├── APPROVED: Action proceeds, ATP debited
   ├── REJECTED: Reason recorded, ATP returned
   └── R6 record written to ledger
```

### 5. 6-Dimensional Trust Tensor

Each member has a trust tensor with 6 dimensions:
- **Competence**: Can they do what they claim?
- **Reliability**: Do they follow through?
- **Alignment**: Do their goals match team goals?
- **Consistency**: Is their behavior predictable?
- **Witnesses**: How many entities attest to them?
- **Lineage**: What is their origin chain?

---

## Enterprise Deployment Patterns

### Single Team (Small Organization)

```
Team "DevOps-Alpha"
├── Admin: ops-lead (TPM2-bound)
├── Members:
│   ├── dev-1 (developer, budget: 100 ATP)
│   ├── dev-2 (developer, budget: 100 ATP)
│   └── ci-agent (deployer, budget: 500 ATP)
└── Policy: Standard development workflow
```

### Federated Teams (Enterprise)

```
Team "Engineering-Org"
├── Admin: cto-lct (TPM2-bound)
├── Sub-Teams (as members):
│   ├── Team "Frontend" (budget: 5000 ATP)
│   ├── Team "Backend" (budget: 5000 ATP)
│   └── Team "DevOps" (budget: 10000 ATP)
├── Cross-Team Policies:
│   └── Deploy requires witness from 2 teams
└── Federation Witnesses: External orgs
```

---

## Security Considerations

### Why Enterprise Terminology?

1. **Accessibility**: "Team" is understood; "Society" requires explanation
2. **Compliance**: "Ledger" maps to audit requirements
3. **Integration**: "Admin" fits RBAC mental models
4. **Legal**: "Member" has clearer contractual implications

### Trust Boundaries

| Boundary | Web4 Term | Enterprise Term | Enforcement |
|----------|-----------|-----------------|-------------|
| Identity | LCT binding | Device registration | TPM2 attestation |
| Authorization | Capability | Role permission | Policy engine |
| Audit | Witness chain | Audit trail | Hash-chain ledger |
| Economics | ATP flow | Resource allocation | Budget tracking |

---

## Implementation Notes

### File Locations

All implementation files are in `/simulations/`:

```
simulations/
├── team.py           # Team + TeamConfig
├── member.py         # Member + MemberRole
├── ledger.py         # Ledger (SQLite + hash-chain)
├── admin_binding.py  # Admin binding (TPM2/software)
├── policy.py         # Policy + PolicyStore
├── r6.py             # R6Request + R6Response + R6Status
├── heartbeat_ledger.py  # Metabolic-state-driven blocks
├── multisig.py       # Multi-signature critical actions
├── trust_decay.py    # Trust decay calculator
├── activity_quality.py  # Quality-adjusted activity
├── sybil_detection.py   # Behavioral correlation
└── attack_simulations.py  # 126 attack vectors
```

### Database Schema

```sql
-- Core tables in ledger.db
CREATE TABLE identities (lct_id, name, role, created_at, ...);
CREATE TABLE admin_bindings (lct_id, binding_type, anchor, attestation, ...);
CREATE TABLE policies (version, content_hash, policy_json, ...);
CREATE TABLE r6_requests (request_id, requester, action, status, ...);
CREATE TABLE audit_trail (seq, record_hash, previous_hash, ...);
CREATE TABLE heartbeats (block_id, timestamp, state, ...);
```

---

## Migration from Web4 to Hardbound

If you have existing Web4 society code, the mapping is straightforward:

```python
# Web4 society pattern
society = Society(chain=blockchain, oracle=law_oracle)
citizen = society.add_citizen(lct_id, capabilities)
society.propose_law(law_oracle.sign(policy))

# Hardbound team pattern
team = Team(config=TeamConfig(name="MyTeam"))
member = team.add_member(lct_id, role=MemberRole.developer)
team.policy_store.add_policy(admin.sign(policy))
```

---

## References

- **R6 Framework**: `/simulations/docs/R6_IMPLEMENTATION_GUIDE.md`
- **Attack Simulations**: `/simulations/attack_simulations.py` (126 vectors)
- **Security Analysis**: `/simulations/security_analysis.md`
- **Web4 Spec**: `/web4-standard/core-spec/`

---

*"A team is a society with enterprise vocabulary. The governance is identical; only the names have been changed to protect the innocent."*
