# T3/V3 Privacy and Governance Specification

## Core Principle: No Free Trust Queries

**Trust information has value. Accessing it requires commitment.**

In Web4, T3/V3 tensors are not publicly queryable reputation scores. They are protected, role-contextual trust assessments that require ATP stake to access. This prevents reputation farming, privacy violations, and speculative trust queries.

## 1. Trust Query Protocol

### 1.1 Query Requirements

Every trust query MUST include:

```json
{
  "query": {
    "target_entity": "lct:web4:entity:...",
    "requested_role": "web4:Surgeon",
    "intended_interaction": "surgical-procedure",
    "atp_stake": 100,
    "validity_period": 3600,
    "query_justification": "Patient requiring surgery"
  },
  "signature": "..."
}
```

### 1.2 ATP Staking Mechanism

```python
def query_role_trust(querier, target, role, interaction_type):
    # 1. Verify querier has sufficient ATP
    if querier.atp_balance < MIN_QUERY_STAKE:
        raise InsufficientATP("Cannot query without stake")
    
    # 2. Check if query makes sense (need to know)
    if not has_legitimate_need(querier, target, role):
        raise NoNeedToKnow("Query rejected - no established need")
    
    # 3. Lock ATP stake
    stake = calculate_stake(role.sensitivity, interaction_type.value)
    querier.lock_atp(stake, validity_period)
    
    # 4. Return role-specific trust ONLY
    return {
        "entity": target.lct_id,
        "role": role,
        "t3_in_role": get_t3_for_role(target, role),
        "validity": validity_period,
        "stake_locked": stake,
        "commitment": "Must engage or forfeit stake"
    }
```

### 1.3 Stake Resolution

| Outcome | Stake Result | ATP Flow |
|---------|--------------|----------|
| Querier engages target in stated role | Stake returned minus query fee | 90% returned, 10% fee |
| Querier doesn't engage within validity | Stake forfeited to target | 100% to target |
| Target declines interaction | Stake returned in full | 100% returned |
| Query rejected (no need to know) | Stake returned minus penalty | 95% returned, 5% penalty |

## 2. Privacy Protection Mechanisms

### 2.1 Role Isolation

Trust scores are **completely isolated by role**:

```python
# WRONG - Global trust query
get_trust(entity)  # ❌ Not allowed

# RIGHT - Role-specific query with stake
query_trust(entity, role="web4:Surgeon", stake=100)  # ✅
```

### 2.2 Query Audit Trail

All trust queries are recorded:

```json
{
  "query_log": {
    "querier": "lct:web4:alice",
    "target": "lct:web4:bob",
    "role_requested": "web4:DataAnalyst",
    "timestamp": "2025-09-14T12:00:00Z",
    "atp_staked": 100,
    "outcome": "engaged|forfeited|declined|rejected"
  }
}
```

### 2.3 Anti-Fishing Protections

```python
class TrustQueryGovernance:
    def __init__(self):
        self.rate_limits = {
            "queries_per_hour": 10,
            "unique_targets_per_day": 50,
            "max_stake_per_query": 1000
        }
        
    def check_fishing_behavior(self, querier):
        patterns = [
            self.many_queries_no_engagement(querier),
            self.querying_competitors(querier),
            self.role_shopping(querier),  # Same target, many roles
            self.stake_manipulation(querier)
        ]
        
        if any(patterns):
            querier.trust_query_suspended(duration=86400)
            querier.atp_penalty(amount=500)
```

## 3. Governance Rules

### 3.1 No Global Scores - Ever

```python
# This is FORBIDDEN in Web4
class Entity:
    global_trust_score: float  # ❌ NEVER EXISTS
    
# This is REQUIRED in Web4
class Entity:
    role_trust: Dict[Role, T3Tensor]  # ✅ Always role-contextual
```

### 3.2 Right to Context

Entities have rights regarding their trust data:

1. **Right to Know**: Who queried their trust and for what role
2. **Right to Refuse**: Decline trust queries from specific entities
3. **Right to Expire**: Set maximum retention for trust history
4. **Right to Context**: Trust only valid within interaction context

### 3.3 Trust Disclosure Levels

```python
class TrustDisclosure:
    NONE = 0        # No trust information available
    BINARY = 1      # Qualified/Not qualified for role
    RANGE = 2       # Low/Medium/High trust in role
    PRECISE = 3     # Exact T3 tensor values
    
    def get_disclosure_level(querier, target, stake):
        if stake < 10:
            return TrustDisclosure.NONE
        elif stake < 50:
            return TrustDisclosure.BINARY
        elif stake < 100:
            return TrustDisclosure.RANGE
        else:
            return TrustDisclosure.PRECISE
```

## 4. Economic Incentives

### 4.1 Query Pricing

```python
def calculate_query_price(role, target_entity, market_demand):
    base_price = ROLE_SENSITIVITY[role] * 10
    
    # Scarce expertise costs more
    scarcity_multiplier = 1 / count_entities_with_role(role)
    
    # High-trust entities can charge more
    trust_premium = target_entity.average_t3_in_role(role)
    
    # Market dynamics
    demand_factor = market_demand.get_role_demand(role)
    
    return base_price * scarcity_multiplier * trust_premium * demand_factor
```

### 4.2 Stake Requirements by Role Sensitivity

| Role Category | Example Roles | Min ATP Stake | Forfeit Risk |
|--------------|---------------|---------------|--------------|
| Public Service | Citizen, Participant | 10 ATP | Low |
| Professional | Developer, Designer | 50 ATP | Medium |
| Specialist | Surgeon, Auditor | 100 ATP | High |
| Critical | Nuclear Operator, Judge | 500 ATP | Very High |
| Governance | Protocol Admin, Oracle | 1000 ATP | Maximum |

## 5. Implementation Requirements

### 5.1 Query Interface

```python
@requires_atp_stake
@role_contextual
@audit_logged
def trust_query_api(request: TrustQueryRequest) -> TrustQueryResponse:
    # Validate stake
    stake = validate_and_lock_stake(request.atp_stake)
    
    # Check need to know
    if not verify_need_to_know(request):
        return TrustQueryResponse(
            status="REJECTED",
            reason="No established need",
            stake_returned=stake * 0.95
        )
    
    # Get role-specific trust
    t3_tensor = get_t3_for_role(
        entity=request.target_entity,
        role=request.requested_role
    )
    
    # Record query for audit
    log_trust_query(request, t3_tensor)
    
    # Set engagement timer
    set_engagement_expectation(
        querier=request.querier,
        target=request.target_entity,
        role=request.requested_role,
        deadline=now() + request.validity_period
    )
    
    return TrustQueryResponse(
        t3_in_role=t3_tensor,
        stake_locked=stake,
        must_engage_by=deadline,
        forfeit_conditions="No engagement = stake to target"
    )
```

### 5.2 Privacy-Preserving Aggregates

```python
def get_role_statistics(role: str) -> AggregateStats:
    """
    Returns anonymous aggregate statistics only
    Never reveals individual entity trust scores
    """
    return {
        "total_entities_with_role": count,
        "average_talent_range": "0.6-0.8",  # Range, not exact
        "engagement_success_rate": 0.87,
        "typical_stake_required": 50-100,
        "market_demand": "high|medium|low"
    }
```

## 6. Attack Mitigations

### 6.1 Sybil Resistance

Creating entities to farm trust data is prevented by:
- Birth certificate requirements
- Citizen role establishment costs
- ATP stake requirements scale with query volume
- Pattern detection for synthetic entities

### 6.2 Trust Manipulation

Attempting to game trust scores is prevented by:
- Role-contextual isolation (can't transfer trust between roles)
- Historical performance requirements
- Witness attestation requirements
- ATP costs for interactions

### 6.3 Privacy Violations

Mass surveillance is prevented by:
- ATP stake requirements (expensive to query many)
- Need-to-know validation
- Query audit trails
- Rate limiting
- Forfeit penalties for non-engagement

## 7. Summary

Web4's T3/V3 privacy governance ensures:

1. **No Free Queries**: ATP stake required, creating economic commitment
2. **Role Context Only**: Never global scores, always role-specific
3. **Need to Know**: Must demonstrate legitimate interaction intent
4. **Engagement Commitment**: Query with stake = must engage or forfeit
5. **Privacy by Design**: No public reputation, only consensual trust exchange
6. **Economic Balance**: Market pricing for valuable trust information

This design makes trust queries intentional, valuable, and privacy-preserving while preventing reputation farming and surveillance capitalism patterns of Web2.