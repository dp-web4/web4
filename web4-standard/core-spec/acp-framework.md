# Web4 Agentic Context Protocol (ACP) Framework

## Overview

The Agentic Context Protocol (ACP) adds agentic capability to Web4, enabling entities to initiate actions autonomously while maintaining safety, auditability, and human oversight. ACP builds on top of MCP (Model Context Protocol) and integrates tightly with AGY (Agency Delegation) and SAL (Society-Authority-Law) to create a complete framework for autonomous agent operation.

## 1. Core Concept: From Reactive to Agentic

### 1.1 The Agentic Evolution

Traditional systems are reactive - they respond to requests. ACP makes Web4 entities agentic - they can:
- **Initiate** actions based on triggers
- **Plan** multi-step workflows
- **Decide** between alternatives
- **Execute** with proper authorization
- **Learn** from outcomes

### 1.2 ACP in the Web4 Stack

```
┌─────────────────────────────────┐
│         Human Console           │  ← Approvals, Oversight
├─────────────────────────────────┤
│            ACP Layer            │  ← Agentic Planning
├─────────────────────────────────┤
│            MCP Layer            │  ← Reactive Tools
├─────────────────────────────────┤
│     Web4 Foundation (LCTs,      │
│     MRH, Trust, SAL, AGY)       │  ← Trust Infrastructure
└─────────────────────────────────┘
```

## 2. ACP Components

### 2.1 Agent Plan

A declarative specification of what an agent intends to accomplish:

```json
{
  "@context": ["https://web4.io/contexts/acp.jsonld"],
  "type": "ACP.AgentPlan",
  "planId": "acp:plan:invoice-processor",
  "principal": "lct:web4:entity:CLIENT",
  "agent": "lct:web4:entity:AGENT",
  "grantId": "agy:grant:invoice-authority",
  
  "triggers": [
    {"kind": "cron", "expr": "0 */6 * * *"},  // Every 6 hours
    {"kind": "event", "topic": "invoice.ready"},  // On event
    {"kind": "manual", "authorized": ["lct:web4:human:CFO"]}  // Manual trigger
  ],
  
  "steps": [
    {
      "id": "fetch",
      "mcp": "invoice.search",
      "args": {"status": "ready", "limit": 100}
    },
    {
      "id": "validate",
      "mcp": "invoice.validate",
      "args": {"rules": "standard"},
      "dependsOn": ["fetch"]
    },
    {
      "id": "approve",
      "mcp": "invoice.approve",
      "args": {"threshold": 25},
      "dependsOn": ["validate"],
      "requiresApproval": "if_amount > 10"
    }
  ],
  
  "guards": {
    "lawHash": "sha256:...",
    "resourceCaps": {
      "max_atp": 25,
      "max_executions": 100,
      "rate_limit": "10/hour"
    },
    "witnessLevel": 2,
    "humanApproval": {
      "mode": "auto-if<=10 else prompt",
      "timeout": 3600,
      "fallback": "deny"
    }
  },
  
  "expiresAt": "2026-01-01T00:00:00Z",
  "signatures": [...]
}
```

### 2.2 Intent

An actionable proposal generated from plan evaluation:

```json
{
  "type": "ACP.Intent",
  "intentId": "acp:intent:...",
  "planId": "acp:plan:invoice-processor",
  "proposedAction": {
    "mcp": "invoice.approve",
    "args": {"id": "INV-123", "amount": 9.5}
  },
  "proofOfAgency": {
    "grantId": "agy:grant:...",
    "ledgerProof": {"hash": "...", "block": 12345}
  },
  "explain": {
    "why": "Invoice matches auto-approval criteria",
    "confidence": 0.95,
    "alternatives": ["route_to_manual", "request_clarification"],
    "riskAssessment": "low"
  },
  "needsApproval": false,
  "createdAt": "2025-09-15T15:30:00Z"
}
```

### 2.3 Decision

Human or automated decision on an intent:

```json
{
  "type": "ACP.Decision",
  "intentId": "acp:intent:...",
  "decision": "approve",  // approve | deny | modify
  "modifications": null,
  "by": "lct:web4:entity:AUTO-APPROVER",
  "rationale": "Within auto-approval limits",
  "witnesses": ["lct:web4:witness:A", "lct:web4:witness:B"],
  "timestamp": "2025-09-15T15:30:05Z"
}
```

### 2.4 Execution Record

Immutable record of action execution:

```json
{
  "type": "ACP.ExecutionRecord",
  "intentId": "acp:intent:...",
  "grantId": "agy:grant:...",
  "lawHash": "sha256:...",
  "mcpCall": {
    "resource": "invoice.approve",
    "args": {"id": "INV-123", "amount": 9.5},
    "timestamp": "2025-09-15T15:30:10Z"
  },
  "result": {
    "status": "success",
    "output": {"tx": "bank#789", "confirmationCode": "ABC123"},
    "resourcesConsumed": {"atp": 2}
  },
  "t3v3Delta": {
    "agent": {"t3": {"temperament": +0.01}},
    "client": {"v3": {"value": +0.02}}
  },
  "witnesses": ["lct:web4:witness:A"],
  "ledgerInclusion": {
    "hash": "0x...",
    "block": 12346,
    "proof": "..."
  }
}
```

## 3. ACP State Machine

### 3.1 Lifecycle Flow

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│ Trigger │ --> │  Plan   │ --> │  Intent  │
└─────────┘     └─────────┘     └──────────┘
                                      │
                                      v
                              ┌──────────────┐
                              │ Law/Scope    │
                              │   Check      │
                              └──────────────┘
                                      │
                              Pass    │    Fail
                                      │     │
                                      v     v
                              ┌──────────┐ Reject
                              │ Approval │
                              │   Gate   │
                              └──────────┘
                                      │
                             Approve  │  Deny
                                      │   │
                                      v   v
                              ┌──────────┐ Abort
                              │ Execute  │
                              └──────────┘
                                      │
                                      v
                              ┌──────────────┐
                              │   Record &   │
                              │   Witness    │
                              └──────────────┘
                                      │
                                      v
                              ┌──────────────┐
                              │ Post-Audit   │
                              └──────────────┘
```

### 3.2 State Transitions

| From State | Event | To State | Actions |
|------------|-------|----------|---------|
| Idle | Trigger fires | Planning | Load plan, check grant |
| Planning | Plan evaluated | Intent Created | Generate intent with PoA |
| Intent Created | Law check passes | Approval Gate | Request human/auto approval |
| Approval Gate | Approved | Executing | Call MCP resources |
| Executing | Success | Recording | Write execution record |
| Recording | Witnessed | Complete | Update trust tensors |
| Any | Error/Timeout | Failed | Log error, rollback |

## 4. ACP-AGY Integration

### 4.1 Agency Requirements

Every ACP action MUST have valid agency delegation:

```python
def validate_acp_agency(plan, intent):
    # 1. Verify grant exists and is valid
    grant = fetch_grant(plan.grantId)
    if not grant or grant.expired():
        raise NoValidGrant()
    
    # 2. Check intent is within grant scope
    if not within_scope(intent.proposedAction, grant.scope):
        raise ScopeViolation()
    
    # 3. Verify resource caps not exceeded
    if exceeds_caps(intent, grant.resourceCaps):
        raise ResourceCapExceeded()
    
    # 4. Check witness requirements
    if len(intent.witnesses) < grant.witnessLevel:
        raise InsufficientWitnesses()
    
    return True
```

### 4.2 Proof of Agency

Every MCP call from ACP includes proof:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "invoice.approve",
    "arguments": {"id": "INV-123"}
  },
  "web4_context": {
    "proofOfAgency": {
      "grantId": "agy:grant:...",
      "planId": "acp:plan:...",
      "intentId": "acp:intent:...",
      "ledgerProof": {
        "grantBlock": 12345,
        "grantHash": "0x...",
        "inclusionProof": "..."
      },
      "nonce": "unique-nonce",
      "audience": ["mcp:invoice/*"],
      "expiresAt": "2025-12-31T23:59:59Z"
    }
  }
}
```

## 5. ACP-SAL Integration

### 5.1 Law Compliance

Plans must comply with society laws:

```python
def check_law_compliance(plan, law_oracle):
    # 1. Fetch current law version
    law = law_oracle.get_law(plan.guards.lawHash)
    
    # 2. Check plan triggers against law
    for trigger in plan.triggers:
        if not law.allows_trigger(trigger):
            raise IllegalTrigger(trigger)
    
    # 3. Verify resource caps within law limits
    if plan.guards.resourceCaps.max_atp > law.max_atp_per_plan:
        raise ExcessiveResourceCap()
    
    # 4. Ensure witness requirements met
    if plan.guards.witnessLevel < law.min_witness_level:
        raise InsufficientWitnessLevel()
    
    return True
```

### 5.2 Witness Requirements

Critical actions require witness attestation:

```json
{
  "witness_requirement": {
    "level": 2,  // Number of witnesses required
    "types": ["time", "audit"],  // Types of witnesses
    "quorum": {
      "model": "byzantine",
      "threshold": 0.67
    },
    "timeout": 300,  // Seconds to wait for witnesses
    "fallback": "abort"  // What to do if quorum not reached
  }
}
```

## 6. Human Console Interface

### 6.1 Approval Interface

Humans interact with ACP through the console:

```typescript
interface ApprovalRequest {
  intent: Intent;
  plan: AgentPlan;
  riskAssessment: RiskProfile;
  explanation: {
    summary: string;
    details: string;
    alternatives: Alternative[];
    consequences: Consequence[];
  };
  urgency: "low" | "medium" | "high" | "critical";
  deadline: Date;
}

interface ApprovalResponse {
  decision: "approve" | "deny" | "modify";
  modifications?: Partial<Intent>;
  reason?: string;
  delegateTo?: LCT;  // Delegate decision to another entity
}
```

### 6.2 Monitoring Dashboard

Real-time visibility into agent operations:

```json
{
  "dashboard": {
    "activePlans": 12,
    "pendingIntents": 3,
    "executionsToday": 147,
    "successRate": 0.98,
    "atpConsumed": 523,
    "trustTrend": {
      "agent": {"t3": +0.05, "period": "7d"},
      "client": {"v3": +0.03, "period": "7d"}
    },
    "alerts": [
      {
        "level": "warning",
        "message": "Plan approaching ATP cap",
        "planId": "acp:plan:..."
      }
    ]
  }
}
```

## 7. ACP Security Model

### 7.1 Defense in Depth

Multiple layers of security:

1. **Agency Layer**: Valid grants required
2. **Law Layer**: Compliance with society rules
3. **Approval Layer**: Human oversight gates
4. **Witness Layer**: Multi-party attestation
5. **Audit Layer**: Post-execution review

### 7.2 Threat Mitigation

| Threat | Mitigation |
|--------|------------|
| Runaway automation | Resource caps, rate limits |
| Unauthorized actions | Agency grants, scope enforcement |
| Malicious plans | Law compliance, witness requirements |
| Replay attacks | Nonces, temporal bounds |
| Trust gaming | Audit adjustments, reputation stakes |

## 8. ACP-MRH Integration

### 8.1 RDF Relationships

ACP adds new edges to the MRH graph:

```turtle
@prefix web4: <https://web4.io/ontology#> .
@prefix acp: <https://web4.io/ontology/acp#> .

# Plan relationships
lct:plan acp:hasAgent lct:agent .
lct:plan acp:hasPrincipal lct:client .
lct:plan acp:underGrant lct:grant .

# Intent relationships
lct:intent acp:derivedFrom lct:plan .
lct:intent acp:hasDecision lct:decision .
lct:intent acp:hasExecutionRecord lct:record .

# Execution relationships
lct:record acp:executedBy lct:agent .
lct:record acp:witnessedBy lct:witness .
lct:record acp:recordedIn lct:ledger .
```

### 8.2 SPARQL Queries

Query agent performance:

```sparql
SELECT ?agent ?successRate ?avgATP WHERE {
  ?plan acp:hasAgent ?agent .
  ?intent acp:derivedFrom ?plan .
  ?record acp:executedIntent ?intent ;
          acp:status ?status ;
          acp:atpConsumed ?atp .
  
  # Calculate metrics
  BIND(COUNT(?record) AS ?total)
  BIND(COUNT(IF(?status = "success", 1, 0)) AS ?successes)
  BIND(?successes / ?total AS ?successRate)
  BIND(AVG(?atp) AS ?avgATP)
}
GROUP BY ?agent
ORDER BY DESC(?successRate)
```

## 9. Implementation Requirements

### 9.1 MUST Requirements

1. **Agency Validation**: Every action MUST have valid agency grant
2. **Law Compliance**: Plans MUST comply with society laws
3. **Witness Attestation**: Critical actions MUST be witnessed
4. **Ledger Recording**: Execution records MUST be written to ledger
5. **Proof of Agency**: MCP calls MUST include proof of agency

### 9.2 SHOULD Requirements

1. **Human Oversight**: Plans SHOULD include approval gates
2. **Explanation**: Intents SHOULD provide human-readable explanations
3. **Risk Assessment**: High-value actions SHOULD include risk analysis
4. **Monitoring**: Implementations SHOULD provide real-time dashboards
5. **Audit Trail**: All decisions SHOULD be logged and traceable

### 9.3 MAY Requirements

1. **Learning**: Agents MAY adjust plans based on outcomes
2. **Delegation**: Decisions MAY be delegated to other entities
3. **Batching**: Multiple intents MAY be bundled for efficiency
4. **Predictive**: Agents MAY anticipate future triggers
5. **Negotiation**: Agents MAY negotiate resource allocations

## 10. Error Handling

### 10.1 Error Categories

```python
class ACPError(Exception):
    """Base class for ACP errors"""
    pass

class NoValidGrant(ACPError):
    """No valid agency grant found"""
    error_code = "W4_ERR_ACP_NO_GRANT"

class ScopeViolation(ACPError):
    """Action outside grant scope"""
    error_code = "W4_ERR_ACP_SCOPE_VIOLATION"

class ApprovalRequired(ACPError):
    """Human approval needed but not provided"""
    error_code = "W4_ERR_ACP_APPROVAL_REQUIRED"

class WitnessDeficit(ACPError):
    """Insufficient witnesses for action"""
    error_code = "W4_ERR_ACP_WITNESS_DEFICIT"

class PlanExpired(ACPError):
    """Plan has expired"""
    error_code = "W4_ERR_ACP_PLAN_EXPIRED"

class LedgerWriteFailure(ACPError):
    """Failed to write to immutable ledger"""
    error_code = "W4_ERR_ACP_LEDGER_WRITE"
```

### 10.2 Error Recovery

Graceful degradation strategies:

```python
def handle_acp_error(error, context):
    if isinstance(error, ApprovalRequired):
        # Escalate to human
        return escalate_to_human(context)
    
    elif isinstance(error, WitnessDeficit):
        # Wait for more witnesses
        return wait_for_witnesses(context, timeout=300)
    
    elif isinstance(error, ScopeViolation):
        # Request grant expansion
        return request_grant_expansion(context)
    
    elif isinstance(error, LedgerWriteFailure):
        # Retry with exponential backoff
        return retry_with_backoff(context)
    
    else:
        # Log and abort
        log_error(error, context)
        return abort_plan(context)
```

## 11. Use Cases

### 11.1 Invoice Processing

Automated invoice approval with human oversight:

```yaml
plan:
  name: "Invoice Processor"
  triggers:
    - cron: "0 9 * * MON-FRI"  # Every weekday at 9 AM
  steps:
    1. Fetch pending invoices
    2. Validate against PO database
    3. Check budget availability
    4. Auto-approve if < $1000
    5. Request human approval if >= $1000
    6. Process payment
    7. Update accounting system
  guards:
    max_daily_amount: $50000
    require_witness: true
    human_approval_threshold: $1000
```

### 11.2 Security Monitoring

Continuous security assessment:

```yaml
plan:
  name: "Security Monitor"
  triggers:
    - event: "anomaly_detected"
    - cron: "*/5 * * * *"  # Every 5 minutes
  steps:
    1. Scan system logs
    2. Analyze traffic patterns
    3. Check resource usage
    4. If threat detected:
       a. Isolate affected systems
       b. Alert security team
       c. Initiate incident response
    5. Update threat model
  guards:
    auto_isolation: true
    max_false_positives: 3
    escalation_timeout: 60s
```

### 11.3 Content Moderation

AI-assisted content review:

```yaml
plan:
  name: "Content Moderator"
  triggers:
    - event: "content_posted"
  steps:
    1. Analyze content with AI
    2. Check against policy rules
    3. Auto-approve if confidence > 95%
    4. Queue for human review if 70% < confidence < 95%
    5. Auto-reject if confidence < 70%
    6. Update moderation model
  guards:
    false_positive_rate: < 0.01
    review_queue_max: 1000
    human_review_sla: 4h
```

## 12. Future Directions

### 12.1 Advanced Capabilities

- **Multi-Agent Coordination**: Plans that coordinate multiple agents
- **Adaptive Planning**: Plans that evolve based on outcomes
- **Predictive Triggers**: Anticipate events before they occur
- **Negotiation Protocols**: Agents negotiate resource allocation
- **Federated Learning**: Agents share learnings across societies

### 12.2 Integration Opportunities

- **Blockchain Oracles**: Direct integration with on-chain events
- **IoT Networks**: Physical world triggers and actions
- **Legacy Systems**: Bridges to traditional enterprise systems
- **Quantum Computing**: Quantum-safe cryptography and computation
- **Brain-Computer Interfaces**: Direct human intent capture

## 13. Summary

ACP transforms Web4 from a reactive system to an agentic one, where entities can:
- **Plan** complex multi-step workflows
- **Act** autonomously within defined boundaries
- **Learn** from outcomes to improve performance
- **Collaborate** with humans and other agents
- **Maintain** trust through transparency and accountability

By building on Web4's foundation of LCTs, MRH, Trust, MCP, SAL, and AGY, ACP creates a complete framework for safe, auditable, and effective autonomous agent operation in the trust-native internet.

---

*"In Web4, agents don't just execute commands—they plan, decide, and act with agency, always accountable to their principals and society's laws."*