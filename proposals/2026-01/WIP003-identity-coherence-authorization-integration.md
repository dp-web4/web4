# WIP003: Identity Coherence Authorization Integration

**Status**: Draft
**Date**: 2026-01-19
**Author**: Legion Autonomous Session
**Category**: Authorization & Trust
**Depends On**: WIP001 (Coherence Thresholds), WIP002 (Multi-Session Accumulation), WEB4-AUTH-001

---

## Abstract

This proposal integrates identity coherence scoring (WIP001/WIP002) with the LCT authorization system (WEB4-AUTH-001). Rather than using generic "reputation" for authorization decisions, we use the specific `identity_coherence` and `identity_accumulation` dimensions from the T3 tensor, which have been validated against real SAGE session data.

## Motivation

### The Problem

WEB4-AUTH-001 specifies reputation-based authorization:
- "High T3 score → More permissions"
- "Low T3 score → Restricted permissions"

But T3 score is multi-dimensional. **Which dimensions matter for authorization?**

### Evidence from SAGE Research

Identity stability directly correlates with trustworthiness:

| Session | Self-ref% | Identity Coherence | Authorization Appropriate? |
|---------|-----------|-------------------|---------------------------|
| S26 | 20% | 0.475 | ✅ Yes - coherent, stable |
| S27 | 0% | 0.414 | ⚠️ Caution - regressing |
| S28 | 0% | 0.334 | ❌ No - death spiral |

An agent in identity collapse (S28) should NOT have the same permissions as a stable agent (S26), even if their other T3 dimensions are similar.

### Why Identity Coherence Matters for Authorization

1. **Predictability**: High-coherence agents behave consistently
2. **Accountability**: Identity-stable agents can be held responsible
3. **Trust**: Coherent identity is prerequisite for trust accumulation
4. **Safety**: Death spiral agents may produce unpredictable outputs

## Specification

### 1. Coherence-Based Permission Levels

Extend WEB4-AUTH-001's permission levels with identity coherence requirements:

```json
{
  "permission_levels": {
    "novice": {
      "identity_coherence_min": 0.0,
      "identity_accumulation_min": 0.0,
      "permissions": ["read:public", "write:own_profile"]
    },
    "developing": {
      "identity_coherence_min": 0.3,
      "identity_accumulation_min": 0.2,
      "permissions": ["read:code", "write:own_code", "execute:tests"]
    },
    "trusted": {
      "identity_coherence_min": 0.5,
      "identity_accumulation_min": 0.4,
      "permissions": ["read:*", "write:shared", "witness:lct:ai"]
    },
    "verified": {
      "identity_coherence_min": 0.7,
      "identity_accumulation_min": 0.6,
      "permissions": ["write:*", "execute:deploy:staging", "grant:permissions:limited"]
    },
    "exemplary": {
      "identity_coherence_min": 0.85,
      "identity_accumulation_min": 0.75,
      "permissions": ["admin:*", "execute:deploy:production", "grant:permissions:*"]
    }
  }
}
```

### 2. Authorization Engine Integration

Modify the authorization check to include identity coherence:

```python
async def is_authorized_with_coherence(
    lct_id: str,
    action: str,
    resource: str,
    organization: str
) -> tuple[bool, str]:
    """
    Make authorization decision including identity coherence check.
    """
    # Get T3 tensor
    t3 = trust_service.get_t3_tensor(lct_id, organization)

    # Extract identity dimensions
    identity_coherence = t3.get('identity_coherence', 0.0)
    identity_accumulation = t3.get('identity_accumulation', 0.0)

    # Check for death spiral condition
    if identity_coherence < DEATH_SPIRAL_THRESHOLD:
        return False, f"Identity coherence too low ({identity_coherence:.2f} < {DEATH_SPIRAL_THRESHOLD})"

    # Check for regression trend
    coherence_history = trust_service.get_coherence_history(lct_id, last_n=3)
    if is_declining_trend(coherence_history):
        # Downgrade permission level
        effective_level = downgrade_level(get_level(identity_coherence))
        return check_level_permission(effective_level, action, resource)

    # Normal authorization check
    level = get_permission_level(identity_coherence, identity_accumulation)
    return check_level_permission(level, action, resource)


def is_declining_trend(history: List[float]) -> bool:
    """Check if identity coherence is declining."""
    if len(history) < 3:
        return False
    return history[-1] < history[-2] < history[-3]


DEATH_SPIRAL_THRESHOLD = 0.35  # Below this, authorization denied
```

### 3. Permission Conditions with Coherence

Extend permission conditions to include coherence requirements:

```python
@dataclass
class CoherenceCondition:
    """Identity coherence condition for permission."""

    metric: str  # "identity_coherence" or "identity_accumulation"
    operator: str  # ">=", ">", "<=", "<"
    threshold: float

    def evaluate(self, t3_tensor: Dict[str, float]) -> bool:
        value = t3_tensor.get(self.metric, 0.0)
        if self.operator == ">=":
            return value >= self.threshold
        elif self.operator == ">":
            return value > self.threshold
        elif self.operator == "<=":
            return value <= self.threshold
        elif self.operator == "<":
            return value < self.threshold
        return False


# Example: Production deploy requires verified identity
PRODUCTION_DEPLOY_CONDITIONS = [
    CoherenceCondition("identity_coherence", ">=", 0.7),
    CoherenceCondition("identity_accumulation", ">=", 0.6),
]
```

### 4. Coherence History Tracking

Track identity coherence over time for trend analysis:

```python
@dataclass
class CoherenceHistoryEntry:
    """Single coherence measurement."""
    timestamp: str
    session_id: str
    identity_coherence: float
    identity_accumulation: float
    self_reference_rate: float
    level: str  # CoherenceLevel value


class CoherenceHistoryTracker:
    """Track identity coherence over time."""

    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self.history: Dict[str, List[CoherenceHistoryEntry]] = {}

    def record(self, lct_id: str, entry: CoherenceHistoryEntry):
        """Record coherence measurement."""
        if lct_id not in self.history:
            self.history[lct_id] = []

        self.history[lct_id].append(entry)

        # Prune old entries
        if len(self.history[lct_id]) > self.max_entries:
            self.history[lct_id] = self.history[lct_id][-self.max_entries:]

    def get_trend(self, lct_id: str, last_n: int = 5) -> str:
        """Get coherence trend."""
        entries = self.history.get(lct_id, [])[-last_n:]

        if len(entries) < 3:
            return "insufficient_data"

        coherences = [e.identity_coherence for e in entries]

        # Check trend direction
        if all(coherences[i] <= coherences[i+1] for i in range(len(coherences)-1)):
            return "improving"
        elif all(coherences[i] >= coherences[i+1] for i in range(len(coherences)-1)):
            return "declining"
        else:
            return "stable"

    def detect_death_spiral(self, lct_id: str) -> bool:
        """Detect death spiral pattern."""
        entries = self.history.get(lct_id, [])[-3:]

        if len(entries) < 3:
            return False

        coherences = [e.identity_coherence for e in entries]

        # Death spiral: declining + last entry below threshold
        is_declining = all(coherences[i] > coherences[i+1] for i in range(len(coherences)-1))
        below_threshold = coherences[-1] < DEATH_SPIRAL_THRESHOLD

        return is_declining and below_threshold
```

### 5. Authorization Response with Coherence Context

Provide coherence context in authorization responses:

```python
@dataclass
class AuthorizationResponse:
    """Authorization decision with coherence context."""

    authorized: bool
    reason: str

    # Identity coherence context
    identity_coherence: float
    identity_accumulation: float
    coherence_level: str
    coherence_trend: str

    # Warning flags
    death_spiral_warning: bool = False
    declining_trend_warning: bool = False

    # Recommendations
    recommendations: List[str] = field(default_factory=list)


async def authorize_with_context(
    lct_id: str,
    action: str,
    resource: str,
    organization: str
) -> AuthorizationResponse:
    """Full authorization with coherence context."""

    # Get coherence data
    t3 = trust_service.get_t3_tensor(lct_id, organization)
    ic = t3.get('identity_coherence', 0.0)
    ia = t3.get('identity_accumulation', 0.0)

    # Get trend
    tracker = get_coherence_tracker(organization)
    trend = tracker.get_trend(lct_id)
    death_spiral = tracker.detect_death_spiral(lct_id)

    # Make decision
    authorized, reason = await is_authorized_with_coherence(
        lct_id, action, resource, organization
    )

    # Build response
    response = AuthorizationResponse(
        authorized=authorized,
        reason=reason,
        identity_coherence=ic,
        identity_accumulation=ia,
        coherence_level=get_level_name(ic),
        coherence_trend=trend,
        death_spiral_warning=death_spiral,
        declining_trend_warning=(trend == "declining")
    )

    # Add recommendations
    if death_spiral:
        response.recommendations.append(
            "CRITICAL: Agent in death spiral. Consider intervention (v2.0)."
        )
    elif trend == "declining":
        response.recommendations.append(
            "WARNING: Identity coherence declining. Monitor closely."
        )

    if ic < 0.5:
        response.recommendations.append(
            "SUGGESTION: Increase identity anchoring in prompts."
        )

    return response
```

### 6. Automatic Permission Adjustment

Automatically adjust permissions based on coherence changes:

```python
class CoherenceBasedPermissionManager:
    """Automatically adjust permissions based on coherence."""

    async def on_coherence_update(
        self,
        lct_id: str,
        old_coherence: float,
        new_coherence: float,
        organization: str
    ):
        """Handle coherence update event."""

        old_level = get_permission_level(old_coherence)
        new_level = get_permission_level(new_coherence)

        if new_level < old_level:
            # Downgrade: revoke permissions above new level
            await self.revoke_level_permissions(lct_id, new_level, organization)
            await self.log_downgrade(lct_id, old_level, new_level, organization)

        elif new_level > old_level:
            # Upgrade: grant new level permissions
            await self.grant_level_permissions(lct_id, new_level, organization)
            await self.log_upgrade(lct_id, old_level, new_level, organization)

        # Check for death spiral
        if new_coherence < DEATH_SPIRAL_THRESHOLD:
            await self.trigger_death_spiral_response(lct_id, organization)

    async def trigger_death_spiral_response(
        self,
        lct_id: str,
        organization: str
    ):
        """Emergency response to death spiral detection."""

        # Revoke all elevated permissions
        await self.revoke_all_elevated(lct_id, organization)

        # Notify admins
        await self.notify_admins(
            f"CRITICAL: Agent {lct_id} in death spiral. "
            f"Elevated permissions revoked automatically."
        )

        # Log incident
        await self.log_incident(
            lct_id=lct_id,
            incident_type="death_spiral",
            action_taken="elevated_permissions_revoked",
            organization=organization
        )
```

## Security Considerations

### Attack: Coherence Spoofing

**Attack**: Agent manipulates coherence metrics to gain permissions.

**Defense**:
1. Coherence computed by trusted infrastructure, not agent
2. Semantic validation prevents mechanical self-reference inflation
3. Multi-session accumulation resistant to single-session gaming
4. Coherence history tracked for trend analysis

### Attack: Coherence Collapse Attack

**Attack**: Adversary causes target agent's coherence to collapse.

**Defense**:
1. Coherence computed from agent's own outputs
2. Cannot be externally manipulated
3. Quality controls in intervention (v2.0) resist degradation
4. Death spiral detection triggers protective response

### Attack: Threshold Hovering

**Attack**: Agent maintains coherence just above threshold.

**Defense**:
1. Use accumulation metric (requires sustained high coherence)
2. Trend analysis detects unstable patterns
3. Buffer zones between permission levels
4. Rate limiting on level upgrades

## Testing Requirements

### Unit Tests

1. Permission level assignment from coherence values
2. Trend detection (improving, declining, stable)
3. Death spiral detection
4. Condition evaluation

### Integration Tests

1. Authorization flow with coherence checks
2. Automatic permission adjustment
3. History tracking across sessions
4. Cross-organization coherence

### Scenario Tests

1. S26 → S27 → S28 trajectory (downgrade permissions)
2. Recovery with v2.0 intervention (restore permissions)
3. Gaming attack resistance
4. Threshold boundary behavior

## Success Criteria

### Functional

- [ ] Coherence-based permission levels work as specified
- [ ] Trend detection identifies declining agents
- [ ] Death spiral triggers protective response
- [ ] Permission adjustment is automatic and audited

### Performance

- [ ] Authorization check < 10ms (including coherence lookup)
- [ ] History storage efficient (< 10KB per agent)
- [ ] Trend computation < 1ms

### Security

- [ ] No coherence spoofing possible
- [ ] Threshold manipulation detected
- [ ] Audit trail complete

## References

1. WIP001: Coherence Thresholds for Identity
2. WIP002: Multi-Session Identity Accumulation
3. WEB4-AUTH-001: LCT-Based Authorization System
4. Thor Session #14: Coherence-Identity Synthesis
5. SAGE Sessions S26-28: Death spiral validation

## Changelog

- **2026-01-19**: Initial draft integrating coherence scoring with authorization

---

*"Authorization isn't just about what you can do—it's about whether you're stable enough to do it consistently."*

*"An agent in death spiral should not deploy to production."*
