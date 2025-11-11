# Phase 1 Security Mitigations - Implementation Guide

**Session**: 11
**Date**: 2025-11-10
**Status**: Design Complete, Implementation In Progress

---

## Overview

Phase 1 mitigations address the most critical, immediately implementable security controls
discovered in the attack vector analysis. These are "low-hanging fruit" that significantly
improve security posture with minimal complexity.

---

## Mitigation 1: LCT Minting Cost (ATP Required)

### Threat Mitigated
- A1: Sybil Attack (Multiple Fake Identities)
- F1: Multi-Stage Privilege Escalation (Stage 1)

### Design

**Principle**: Make identity creation costly enough to deter mass Sybil attacks while
remaining accessible for legitimate users.

**Implementation**:
```python
# identity_service.py modifications

ATP_MINT_BASE_COST = 100  # Base ATP cost to mint an LCT
ATP_MINT_SCALE_FACTOR = 1.5  # Cost multiplier per existing LCT from same society

async def mint_lct(req: MintLCTRequest) -> MintLCTResponse:
    """Mint new LCT with ATP cost enforcement"""

    # Calculate ATP cost based on existing LCTs from this society
    existing_count = count_lcts_from_society(req.society)
    atp_cost = ATP_MINT_BASE_COST * (ATP_MINT_SCALE_FACTOR ** existing_count)

    # Verify caller has sufficient ATP
    caller_atp = get_atp_balance(req.caller_lct_id)
    if caller_atp < atp_cost:
        return error_response("Insufficient ATP balance")

    # Deduct ATP cost
    deduct_atp(req.caller_lct_id, atp_cost)

    # Proceed with minting
    lct_id = generate_lct_id(req.entity_type, req.entity_identifier, req.society)
    # ... rest of minting logic

    return MintLCTResponse(
        lct_id=lct_id,
        atp_cost=atp_cost,
        remaining_balance=caller_atp - atp_cost
    )
```

**Parameters**:
- `ATP_MINT_BASE_COST`: 100 ATP (initial suggestion, tune based on testing)
- Scaling: Cost = BASE * (1.5 ^ existing_LCT_count)
  - 1st LCT: 100 ATP
  - 2nd LCT: 150 ATP
  - 3rd LCT: 225 ATP
  - 10th LCT: 5,766 ATP

**Trade-offs**:
- ✅ Significantly increases Sybil attack cost
- ✅ Linear growth in society size requires exponential ATP investment
- ❌ New organizations need ATP to mint first LCT (bootstrap problem)
- ❌ Legitimate multi-agent systems may be penalized

**Bootstrap Solution**:
- System grants initial ATP allocation to verified organizations
- Early adopter program for trusted entities
- Witness staking can subsidize new LCT costs

**Testing**:
- Simulate Sybil attack with N=100 fake LCTs
- Measure total ATP cost (should be prohibitive)
- Verify legitimate use cases remain affordable

---

## Mitigation 2: Witness Validation (Reputation Check)

### Threat Mitigated
- A1: Sybil Attack (Fabricated Witnesses)
- B1: Reputation Washing (Collusive Witnesses)

### Design

**Principle**: Witnesses must be established entities with reputation at stake.

**Implementation**:
```python
# identity_service.py modifications

MIN_WITNESS_REPUTATION = 0.4  # Minimum T3 score to be a witness
MIN_WITNESS_AGE_DAYS = 30  # Minimum days since witness LCT creation
MIN_WITNESS_ACTIONS = 50  # Minimum actions witnessed by the witness

async def validate_witness(witness_lct_id: str) -> tuple[bool, str]:
    """Validate witness eligibility"""

    # Check witness exists
    witness_data = await get_lct_info(witness_lct_id)
    if not witness_data:
        return False, "Witness LCT does not exist"

    # Check witness age
    creation_time = witness_data["birth_certificate"]["creation_time"]
    age_days = (datetime.now() - datetime.fromisoformat(creation_time)).days

    if age_days < MIN_WITNESS_AGE_DAYS:
        return False, f"Witness too new ({age_days} days, need {MIN_WITNESS_AGE_DAYS})"

    # Check witness reputation
    rep_data = await reputation_service.get_reputation(witness_lct_id, role="witness")
    if not rep_data:
        return False, "Witness has no reputation record"

    t3_score = rep_data.get("t3_score", 0.0)
    if t3_score < MIN_WITNESS_REPUTATION:
        return False, f"Witness reputation too low ({t3_score:.2f}, need {MIN_WITNESS_REPUTATION})"

    # Check witness history
    action_count = rep_data.get("action_count", 0)
    if action_count < MIN_WITNESS_ACTIONS:
        return False, f"Witness too inexperienced ({action_count} actions, need {MIN_WITNESS_ACTIONS})"

    return True, "Witness validated"


async def mint_lct(req: MintLCTRequest) -> MintLCTResponse:
    """Mint new LCT with witness validation"""

    # Validate all witnesses
    for witness in req.witnesses:
        valid, reason = await validate_witness(witness)
        if not valid:
            return error_response(f"Invalid witness {witness}: {reason}")

    # Require minimum number of witnesses (e.g., 3)
    if len(req.witnesses) < 3:
        return error_response("Minimum 3 witnesses required")

    # ... proceed with minting
```

**Parameters**:
- `MIN_WITNESS_REPUTATION`: 0.4 (40% on T3 scale)
- `MIN_WITNESS_AGE_DAYS`: 30 days
- `MIN_WITNESS_ACTIONS`: 50 witnessed events
- Minimum witnesses per LCT: 3

**Trade-offs**:
- ✅ Prevents fabricated witness attacks
- ✅ Creates economic cost to corruption (witness reputation at stake)
- ❌ Bootstrap problem: how do first witnesses get validated?
- ❌ Collusion still possible if witnesses coordinate

**Bootstrap Solution**:
- System bootstraps with trusted founding witnesses
- Gradual onboarding of new witnesses through verification process
- Witnesses must be vouched for by existing witnesses

**Testing**:
- Attempt LCT mint with fake witnesses (should fail)
- Attempt with low-reputation witnesses (should fail)
- Verify legitimate minting with proper witnesses succeeds

---

## Mitigation 3: Outcome Recording Cost (ATP Required)

### Threat Mitigated
- B1: Reputation Washing (Fake Outcomes)
- B2: Reputation Sybil (Mass Collusion)

### Design

**Principle**: Recording outcomes has ATP cost that scales with claimed quality.

**Implementation**:
```python
# reputation_service.py modifications

ATP_OUTCOME_BASE_COST = 10  # Base cost to record an outcome
ATP_OUTCOME_QUALITY_MULTIPLIER = {
    "exceptional_quality": 5.0,  # 50 ATP
    "meets_expectations": 2.0,   # 20 ATP
    "partial_completion": 1.0,   # 10 ATP
    "failed": 0.5                # 5 ATP
}

async def record_outcome(req: RecordOutcomeRequest) -> RecordOutcomeResponse:
    """Record outcome with ATP cost"""

    # Calculate ATP cost based on claimed outcome quality
    quality_multiplier = ATP_OUTCOME_QUALITY_MULTIPLIER.get(
        req.outcome,
        1.0  # Default multiplier
    )
    atp_cost = ATP_OUTCOME_BASE_COST * quality_multiplier

    # Verify entity has sufficient ATP
    entity_atp = get_atp_balance(req.entity)
    if entity_atp < atp_cost:
        return error_response("Insufficient ATP to record outcome")

    # Deduct ATP (refundable if outcome verified by oracle)
    deduct_atp(req.entity, atp_cost)

    # Validate witnesses (using Mitigation 2 logic)
    for witness in req.witnesses:
        valid, reason = await validate_witness(witness)
        if not valid:
            return error_response(f"Invalid witness {witness}: {reason}")

    # Record outcome
    t3_delta, v3_delta = compute_reputation_update(req)

    # Store outcome with ATP cost metadata
    store_outcome(
        entity=req.entity,
        outcome_data=req,
        atp_cost=atp_cost,
        refundable=True  # Can be refunded if verified
    )

    return RecordOutcomeResponse(
        t3_score=new_t3,
        v3_score=new_v3,
        atp_cost=atp_cost,
        atp_remaining=entity_atp - atp_cost
    )
```

**Parameters**:
- `ATP_OUTCOME_BASE_COST`: 10 ATP
- Quality multipliers:
  - Exceptional: 5x (50 ATP)
  - Meets expectations: 2x (20 ATP)
  - Partial: 1x (10 ATP)
  - Failed: 0.5x (5 ATP)

**Refund Mechanism**:
- Outcomes verified by external oracle get ATP refunded
- Unverified outcomes: ATP retained as deposit
- False claims: ATP slashed, reputation penalty

**Trade-offs**:
- ✅ Economic cost deters fake outcome spam
- ✅ Self-regulation: high claims require high stakes
- ❌ Legitimate outcomes need ATP (friction)
- ❌ Requires oracle system for verification (future work)

**Testing**:
- Simulate reputation washing with 100 fake outcomes
- Measure total ATP cost (should be prohibitive)
- Verify legitimate outcome recording remains affordable

---

## Mitigation 4: Usage Monitoring (Actual vs Reported)

### Threat Mitigated
- C1: ATP Draining Attack
- C2: Resource Hoarding

### Design

**Principle**: External monitoring validates self-reported resource usage.

**Implementation**:
```python
# resources_service.py modifications

class ResourceMonitor:
    """External monitor for actual resource usage"""

    def __init__(self):
        self.allocations = {}  # allocation_id -> usage_data

    async def track_allocation(self, allocation_id: str, entity_id: str,
                                resource_type: str, amount: float):
        """Start tracking an allocation"""
        self.allocations[allocation_id] = {
            "entity_id": entity_id,
            "resource_type": resource_type,
            "allocated": amount,
            "start_time": time.time(),
            "measured_usage": []  # Periodic measurements
        }

        # Start background monitoring task
        asyncio.create_task(self._monitor_usage(allocation_id))

    async def _monitor_usage(self, allocation_id: str):
        """Periodically measure actual resource usage"""
        while allocation_id in self.allocations:
            # Measure actual usage (implementation depends on resource type)
            actual_usage = await self._measure_usage(allocation_id)

            self.allocations[allocation_id]["measured_usage"].append({
                "timestamp": time.time(),
                "usage": actual_usage
            })

            await asyncio.sleep(60)  # Check every minute

    async def verify_reported_usage(self, allocation_id: str,
                                     reported_usage: float) -> tuple[bool, float]:
        """Verify reported usage against measurements"""

        if allocation_id not in self.allocations:
            return False, 0.0

        # Calculate average measured usage
        measurements = self.allocations[allocation_id]["measured_usage"]
        if not measurements:
            return False, 0.0

        avg_measured = sum(m["usage"] for m in measurements) / len(measurements)

        # Allow 10% variance (measurement error tolerance)
        discrepancy = abs(reported_usage - avg_measured) / avg_measured

        if discrepancy > 0.10:  # More than 10% difference
            return False, avg_measured  # Report flagged, return actual usage

        return True, reported_usage  # Report verified


monitor = ResourceMonitor()

async def allocate_resources(req: AllocateResourcesRequest) -> AllocateResponse:
    """Allocate resources with monitoring"""

    # ... existing allocation logic

    # Start monitoring
    await monitor.track_allocation(
        allocation_id=allocation_id,
        entity_id=req.entity_id,
        resource_type=req.resource_type,
        amount=allocated_amount
    )

    return AllocateResponse(...)


async def report_usage(req: ReportUsageRequest) -> ReportUsageResponse:
    """Report usage with verification"""

    # Verify reported usage
    verified, actual_usage = await monitor.verify_reported_usage(
        allocation_id=req.allocation_id,
        reported_usage=req.actual_usage
    )

    if not verified:
        # Flag for investigation
        flag_entity_for_misreporting(req.entity_id)

        # Use measured usage instead
        usage_for_refund = actual_usage

        # Penalize repeated offenders
        penalty = calculate_misreporting_penalty(req.entity_id)
        apply_atp_penalty(req.entity_id, penalty)

        return ReportUsageResponse(
            verified=False,
            actual_usage=actual_usage,
            reported_usage=req.actual_usage,
            penalty=penalty,
            note="Discrepancy detected, using measured usage"
        )

    # Calculate refund for unused resources
    refund = calculate_refund(allocated_amount, usage_for_refund)

    return ReportUsageResponse(
        verified=True,
        refund=refund
    )
```

**Parameters**:
- Measurement interval: 60 seconds
- Verification tolerance: 10% variance
- Penalty escalation:
  - 1st offense: Warning
  - 2nd offense: 50 ATP penalty
  - 3rd offense: 200 ATP penalty
  - 4th+ offense: Allocation privileges suspended

**Trade-offs**:
- ✅ Prevents false usage reporting
- ✅ Automated detection, no manual review needed
- ❌ Requires actual monitoring infrastructure
- ❌ May have measurement errors

**Testing**:
- Simulate ATP draining with false usage reports
- Verify detection triggers correctly
- Measure false positive rate on legitimate workloads

---

## Mitigation 5: Triple Authentication (Signature Required)

### Threat Mitigated
- E1: Graph Poisoning
- F1: Multi-Stage Privilege Escalation (Knowledge layer)

### Design

**Principle**: RDF triples must be signed by the subject entity.

**Implementation**:
```python
# knowledge_service.py modifications

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
import base64

async def add_triple(req: AddTripleRequest, auth: AuthContext) -> AddTripleResponse:
    """Add RDF triple with authentication"""

    # Extract subject LCT from triple
    subject_lct = req.subject

    # Verify caller is the subject (or has delegation)
    if auth.lct_id != subject_lct:
        # Check if caller has delegation from subject
        has_delegation = await check_delegation(
            delegator=subject_lct,
            delegatee=auth.lct_id,
            action="add_triple"
        )

        if not has_delegation:
            return error_response("Not authorized to make claims about this subject")

    # Verify signature on triple content
    triple_content = f"{req.subject}|{req.predicate}|{req.object}"
    signature_valid = verify_signature(
        message=triple_content,
        signature=auth.signature,
        public_key=auth.public_key
    )

    if not signature_valid:
        return error_response("Invalid signature on triple")

    # For high-stakes predicates, require witnesses
    high_stakes_predicates = ["trusts", "certified_expert", "authorized_for"]

    if req.predicate in high_stakes_predicates:
        if not req.metadata.get("witnesses") or len(req.metadata["witnesses"]) < 2:
            return error_response(f"Predicate '{req.predicate}' requires 2+ witnesses")

        # Validate witnesses
        for witness in req.metadata["witnesses"]:
            valid, reason = await validate_witness(witness)
            if not valid:
                return error_response(f"Invalid witness: {reason}")

    # Calculate ATP cost (higher for trust claims)
    atp_cost = calculate_triple_atp_cost(req.predicate, req.metadata)

    # Verify ATP balance
    entity_atp = get_atp_balance(auth.lct_id)
    if entity_atp < atp_cost:
        return error_response("Insufficient ATP")

    # Deduct ATP
    deduct_atp(auth.lct_id, atp_cost)

    # Add triple with provenance
    triple_id = add_to_graph(
        subject=req.subject,
        predicate=req.predicate,
        object=req.object,
        metadata={
            **req.metadata,
            "author": auth.lct_id,
            "signature": auth.signature,
            "timestamp": datetime.now().isoformat(),
            "atp_cost": atp_cost
        }
    )

    return AddTripleResponse(
        triple_id=triple_id,
        atp_cost=atp_cost
    )


def calculate_triple_atp_cost(predicate: str, metadata: Dict) -> int:
    """Calculate ATP cost based on triple significance"""

    base_costs = {
        "trusts": 50,  # Trust claims are expensive
        "certified_expert": 100,  # Certifications very expensive
        "authorized_for": 75,  # Authorization claims expensive
        "has_role": 20,  # Role claims moderate
        "member_of": 10,  # Membership claims cheap
        "default": 5  # Generic relations cheap
    }

    return base_costs.get(predicate, base_costs["default"])
```

**Parameters**:
- ATP costs:
  - Trust claims: 50 ATP
  - Certifications: 100 ATP
  - Authorizations: 75 ATP
  - Roles: 20 ATP
  - Membership: 10 ATP
  - Default: 5 ATP

**Trade-offs**:
- ✅ Prevents unauthorized claims about entities
- ✅ Economic cost deters graph spam
- ✅ Provenance tracking enables auditing
- ❌ Friction for legitimate graph building
- ❌ Requires signature infrastructure

**Testing**:
- Attempt to add triples about other entities (should fail)
- Verify signature validation works correctly
- Test witness validation for high-stakes predicates

---

## Implementation Checklist

### Identity Service
- [ ] Add ATP minting cost logic
- [ ] Implement witness validation function
- [ ] Scale costs with society LCT count
- [ ] Add bootstrap mechanism for founding witnesses
- [ ] Test Sybil attack mitigation

### Reputation Service
- [ ] Add ATP outcome recording cost
- [ ] Implement outcome quality multipliers
- [ ] Add witness validation to outcome recording
- [ ] Implement refund mechanism (oracle integration TBD)
- [ ] Test reputation washing mitigation

### Resources Service
- [ ] Implement ResourceMonitor class
- [ ] Add actual usage measurement (per resource type)
- [ ] Implement usage verification logic
- [ ] Add penalty escalation for misreporting
- [ ] Test ATP draining mitigation

### Knowledge Service
- [ ] Add triple signature verification
- [ ] Implement high-stakes predicate witness requirements
- [ ] Add ATP cost calculation for triples
- [ ] Implement delegation checking
- [ ] Test graph poisoning mitigation

### Cross-Service
- [ ] Implement ATP balance tracking
- [ ] Create deduct_atp() and get_atp_balance() functions
- [ ] Add monitoring dashboard for security events
- [ ] Create attack detection alerts
- [ ] Integration testing with attack simulator

---

## Testing Strategy

### Unit Tests
- Each mitigation function tested independently
- Edge cases covered (zero ATP, invalid witnesses, etc.)
- Performance benchmarks

### Integration Tests
- Test with attack_simulator.py
- Verify mitigations prevent attacks
- Measure attack cost increase

### Performance Tests
- Measure overhead of mitigations
- Verify latency remains acceptable
- Load testing with mitigations enabled

### Economic Tests
- Simulate ATP economy with mitigations
- Verify bootstrap scenarios work
- Test legitimate use cases remain affordable

---

## Deployment Strategy

### Phase 1A: Monitoring (Non-blocking)
- Deploy mitigations in monitoring mode
- Collect metrics on violations
- Tune parameters based on data

### Phase 1B: Warnings (Soft enforcement)
- Log violations, return warnings
- Don't block requests yet
- Observe impact on legitimate users

### Phase 1C: Enforcement (Hard enforcement)
- Enable blocking for violations
- Monitor for false positives
- Provide appeal mechanism

---

## Success Metrics

### Security Metrics
- Sybil attack cost increased by 100x
- Reputation washing cost increased by 50x
- Resource draining detected within 5 minutes
- Graph poisoning success rate < 1%

### Usability Metrics
- Legitimate LCT minting success rate > 99%
- Legitimate outcome recording success rate > 95%
- False positive rate for usage monitoring < 2%
- Average latency increase < 10ms

---

## Next Steps

1. Implement mitigations in services
2. Run attack_simulator.py against hardened services
3. Tune parameters based on results
4. Document findings in Session 11 summary
5. Commit to repository
6. Plan Phase 2 mitigations (network analysis)

---

**Status**: Design complete, implementation ready to begin
**Priority**: CRITICAL - Foundational security
**Estimated Effort**: 4-6 hours implementation + 2-3 hours testing

