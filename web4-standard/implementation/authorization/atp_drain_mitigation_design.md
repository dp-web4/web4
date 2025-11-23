# ATP Drain Attack Mitigation Design
**Session #65**: P2 Security Enhancement
**Status**: ⚠️ VULNERABLE → 🔄 IMPLEMENTING

## Attack Vector Analysis

### Attack Pattern
```python
# Victim starts expensive action sequence
victim_sequence = create_sequence(
    actor="lct:victim:001",
    actions=[gpu_compute, dataset_analysis, model_training],
    total_atp=1000
)

# Attacker sabotages at iteration 8/10
# Methods:
# 1. Resource contention (consume GPU/memory)
# 2. Denial of service (network flooding)
# 3. Data corruption (invalid inputs)
# 4. Dependency unavailability (kill required service)

# Result: Victim loses 800 ATP, gets no useful work
# Attacker: Minimal cost, competitive advantage
```

### Impact
- **Denial of Service**: Victims can't complete work
- **Resource Exhaustion**: ATP drained without value
- **Competitive Sabotage**: Attacker gains by victim's failure
- **Economic Attack**: System loses trust if failures common

## Mitigation Strategy (4-Layer Defense)

### Layer 1: Failure Attribution

**Goal**: Identify who/what caused the failure

**Mechanism**:
```python
class FailureAttribution:
    """Track failure causes and assign responsibility"""

    def record_failure(self, sequence_id, iteration, failure_type, evidence):
        """
        Record failure with attribution evidence

        failure_type:
        - 'internal': Actor's code failed
        - 'resource_contention': External resource unavailable
        - 'dependency': Required service down
        - 'sabotage': Evidence of malicious interference
        - 'timeout': Exceeded time limit
        """

        # Analyze evidence
        attribution = self.analyze_failure_cause(evidence)

        # Record in database
        INSERT INTO failure_attributions (
            sequence_id, iteration, failure_type,
            attributed_to_lct,  -- Who is responsible?
            evidence_hash,      -- Cryptographic proof
            confidence_score    -- Attribution confidence (0-1)
        ) VALUES (...)

        # If sabotage detected, penalize attacker
        if attribution.confidence > 0.8 and attribution.sabotage_detected:
            self.penalize_attacker(attribution.attributed_to_lct)
```

**Evidence Collection**:
- Resource consumption logs (who consumed what)
- Network traffic analysis (who sent requests)
- Timing analysis (unusual patterns)
- Checkpoint state validation (corrupted state)
- Witness attestations (other agents observed sabotage)

### Layer 2: ATP Insurance

**Goal**: Protect victims from unattributable failures

**Mechanism**:
```python
class ATPInsurance:
    """Optional insurance for action sequences"""

    def purchase_insurance(self, sequence_id, coverage_ratio=0.5, premium_rate=0.05):
        """
        Purchase ATP insurance for sequence

        coverage_ratio: What % of ATP loss is covered (0-1)
        premium_rate: Cost as % of total ATP budget

        Example:
        - Budget: 1000 ATP
        - Coverage: 50% (500 ATP max payout)
        - Premium: 5% (50 ATP cost)
        """

        premium = budget * premium_rate
        max_payout = budget * coverage_ratio

        INSERT INTO atp_insurance_policies (
            sequence_id, premium_paid, max_payout,
            coverage_start, coverage_end
        ) VALUES (...)

        # Deduct premium immediately
        UPDATE action_sequences
        SET atp_consumed = atp_consumed + premium
        WHERE sequence_id = sequence_id

    def claim_insurance(self, sequence_id, atp_lost):
        """File insurance claim on failure"""

        policy = get_policy(sequence_id)
        if not policy or not policy.valid:
            return 0

        # Calculate payout
        payout = min(atp_lost * policy.coverage_ratio, policy.max_payout)

        # Record claim
        INSERT INTO insurance_claims (
            policy_id, sequence_id, atp_lost,
            payout_amount, claim_status
        ) VALUES (...)

        # Issue payout
        return payout
```

**Economic Model**:
- **Premium**: 5-10% of ATP budget
- **Coverage**: 50-80% of potential loss
- **Max Payout**: Capped at coverage limit
- **Risk Pool**: Insurance premiums fund payouts

### Layer 3: Retry Mechanisms

**Goal**: Automatic retry with ATP protection

**Mechanism**:
```python
class RetryManager:
    """Manage retries with ATP protection"""

    def create_retry_policy(self, sequence_id, max_retries=3, backoff='exponential'):
        """
        Create retry policy for sequence

        max_retries: How many times to retry on failure
        backoff: 'exponential', 'linear', 'constant'
        """

        INSERT INTO retry_policies (
            sequence_id, max_retries, retry_count,
            backoff_strategy, atp_reserved_for_retry
        ) VALUES (...)

    def execute_with_retry(self, sequence_id):
        """Execute sequence with automatic retry on failure"""

        policy = get_retry_policy(sequence_id)
        retry_count = 0

        while retry_count <= policy.max_retries:
            try:
                result = execute_sequence(sequence_id)
                if result.success:
                    return result

                # Failure - check if retryable
                if not is_retryable_failure(result.failure_type):
                    break

                retry_count += 1
                backoff_time = calculate_backoff(policy, retry_count)
                sleep(backoff_time)

                # Create new sequence with same params
                retry_sequence_id = clone_sequence(sequence_id)

                # Mark original as retried
                UPDATE action_sequences
                SET status = 'retried',
                    retry_sequence_id = retry_sequence_id
                WHERE sequence_id = sequence_id

                # Continue with retry
                sequence_id = retry_sequence_id

            except Exception as e:
                log_failure(sequence_id, e)
                break

        # All retries exhausted
        return FailureResult(reason='max_retries_exceeded')
```

**Retry Policies**:
- **Transient Failures**: Retry immediately (network glitch)
- **Resource Contention**: Exponential backoff (wait for resources)
- **Sabotage**: Don't retry (failure attribution needed first)
- **Internal Errors**: Don't retry (fix code first)

### Layer 4: Reputation Requirements

**Goal**: Require high reputation for expensive operations

**Mechanism**:
```python
class ReputationGating:
    """Gate expensive operations by reputation"""

    REPUTATION_THRESHOLDS = {
        'low_cost': 0.3,      # < 100 ATP
        'medium_cost': 0.5,   # 100-500 ATP
        'high_cost': 0.7,     # 500-2000 ATP
        'critical_cost': 0.9  # > 2000 ATP
    }

    def check_reputation_requirement(self, lct_id, org_id, atp_budget):
        """Check if actor has sufficient reputation for ATP budget"""

        reputation = get_t3_score(lct_id, org_id)

        required = self.get_required_reputation(atp_budget)

        if reputation < required:
            raise InsufficientReputationError(
                f"Reputation {reputation:.2f} < required {required:.2f} "
                f"for {atp_budget} ATP budget"
            )

        return True

    def get_required_reputation(self, atp_budget):
        """Calculate required reputation for ATP budget"""

        if atp_budget < 100:
            return self.REPUTATION_THRESHOLDS['low_cost']
        elif atp_budget < 500:
            return self.REPUTATION_THRESHOLDS['medium_cost']
        elif atp_budget < 2000:
            return self.REPUTATION_THRESHOLDS['high_cost']
        else:
            return self.REPUTATION_THRESHOLDS['critical_cost']
```

**Gating Logic**:
- New identities: Limited to 100 ATP budgets (T3 < 0.3)
- Established identities: 500 ATP budgets (T3 ≥ 0.5)
- Trusted identities: 2000 ATP budgets (T3 ≥ 0.7)
- Highly trusted: Unlimited (T3 ≥ 0.9)

## Database Schema

```sql
-- Failure Attribution Table
CREATE TABLE failure_attributions (
    attribution_id BIGSERIAL PRIMARY KEY,
    sequence_id VARCHAR(255) REFERENCES action_sequences(sequence_id),
    iteration_number INTEGER,
    failure_type VARCHAR(100),  -- internal, resource_contention, dependency, sabotage, timeout
    attributed_to_lct VARCHAR(255) REFERENCES lct_identities(lct_id),
    evidence_hash VARCHAR(66),  -- SHA256 of evidence
    confidence_score NUMERIC(3, 2),  -- 0.00-1.00
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    investigation_status VARCHAR(50) DEFAULT 'pending',  -- pending, confirmed, dismissed
    penalty_applied BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_failure_attrib_lct ON failure_attributions(attributed_to_lct);
CREATE INDEX idx_failure_attrib_confidence ON failure_attributions(confidence_score DESC);

-- ATP Insurance Policies Table
CREATE TABLE atp_insurance_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    sequence_id VARCHAR(255) REFERENCES action_sequences(sequence_id),
    policyholder_lct VARCHAR(255) REFERENCES lct_identities(lct_id),
    premium_paid INTEGER,
    max_payout INTEGER,
    coverage_ratio NUMERIC(3, 2),  -- 0.00-1.00
    coverage_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    coverage_end TIMESTAMP WITH TIME ZONE,
    policy_status VARCHAR(50) DEFAULT 'active'  -- active, claimed, expired
);

-- Insurance Claims Table
CREATE TABLE insurance_claims (
    claim_id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT REFERENCES atp_insurance_policies(policy_id),
    sequence_id VARCHAR(255) REFERENCES action_sequences(sequence_id),
    atp_lost INTEGER,
    payout_amount INTEGER,
    claim_filed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    claim_status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, denied, paid
    denial_reason TEXT
);

-- Retry Policies Table
CREATE TABLE retry_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    sequence_id VARCHAR(255) REFERENCES action_sequences(sequence_id),
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    backoff_strategy VARCHAR(50) DEFAULT 'exponential',  -- exponential, linear, constant
    atp_reserved_for_retry INTEGER,
    last_retry_at TIMESTAMP WITH TIME ZONE
);

-- Reputation Requirements Table (configuration)
CREATE TABLE reputation_requirements (
    requirement_id SERIAL PRIMARY KEY,
    operation_type VARCHAR(100),  -- action_sequence, delegation, resource_access
    atp_budget_min INTEGER,
    atp_budget_max INTEGER,
    min_t3_score NUMERIC(3, 2),
    min_v3_score NUMERIC(3, 2),
    min_total_actions INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Default reputation requirements
INSERT INTO reputation_requirements (operation_type, atp_budget_min, atp_budget_max, min_t3_score) VALUES
    ('action_sequence', 0, 100, 0.30),      -- Low cost
    ('action_sequence', 100, 500, 0.50),    -- Medium cost
    ('action_sequence', 500, 2000, 0.70),   -- High cost
    ('action_sequence', 2000, 999999, 0.90) -- Critical cost
;
```

## Implementation Plan

### Phase 1: Failure Attribution (Foundation)
1. Create `failure_attributions` table
2. Implement evidence collection
3. Create basic attribution logic
4. Test with simulated sabotage

### Phase 2: ATP Insurance (Protection)
1. Create insurance tables
2. Implement premium calculation
3. Implement claims processing
4. Test insurance lifecycle

### Phase 3: Retry Mechanisms (Resilience)
1. Create retry_policies table
2. Implement retry logic
3. Add backoff strategies
4. Test transient failure recovery

### Phase 4: Reputation Gating (Prevention)
1. Create reputation_requirements table
2. Implement reputation checks
3. Add to sequence creation
4. Test reputation enforcement

## Testing Strategy

### Test Suite: `test_atp_drain_mitigation.py`

**Test 1**: Failure attribution with sabotage evidence
- Simulate external resource contention
- Collect timing evidence
- Verify attacker identified
- Confirm penalty applied

**Test 2**: ATP insurance claim processing
- Purchase insurance (50 ATP premium)
- Execute sequence (failure at iteration 8)
- File claim (600 ATP lost)
- Verify payout (300 ATP, 50% coverage)

**Test 3**: Retry with exponential backoff
- First attempt fails (transient error)
- Retry after 1s
- Second attempt fails
- Retry after 2s
- Third attempt succeeds

**Test 4**: Reputation gating enforcement
- New identity (T3 = 0.2) attempts 500 ATP sequence
- Rejection (requires T3 ≥ 0.5)
- Build reputation to 0.6
- Retry succeeds

**Test 5**: Combined mitigation scenario
- Victim with insurance
- Sabotage detected mid-sequence
- Failure attributed to attacker
- Insurance claim approved
- Retry succeeds
- Attacker penalized

## Economic Model

### Insurance Risk Pool

**Revenue** (Premiums):
- 100 sequences/day
- Average budget: 500 ATP
- Premium rate: 5%
- Daily premium revenue: 100 × 500 × 0.05 = 2,500 ATP

**Costs** (Payouts):
- Failure rate: 10%
- Average loss: 250 ATP (50% of budget)
- Coverage: 50%
- Daily payouts: 100 × 0.1 × 250 × 0.5 = 1,250 ATP

**Profit**: 2,500 - 1,250 = 1,250 ATP/day (50% margin)

### Reputation Economics

**Reputation Building Cost**:
- 100 successful sequences → T3 = 0.5 (100 ATP budget access)
- 200 more sequences → T3 = 0.7 (2000 ATP budget access)
- 300 total sequences → T3 = 0.9 (unlimited access)

**Value**:
- Prevents Sybil attacks (new identities limited)
- Creates incentive for good behavior
- Economic moat (attackers must build reputation first)

## Security Properties

1. **Sabotage Detection**: High-confidence attribution (>0.8) for malicious failures
2. **Economic Protection**: Insurance covers 50-80% of unattributable losses
3. **Resilience**: Automatic retry for transient failures
4. **Prevention**: Reputation gating prevents low-trust entities from expensive operations
5. **Accountability**: Failed attributions penalize attackers via reputation loss
6. **Deterrence**: Cost of sabotage > benefit due to penalties

## Comparison with Other Systems

| System | Failure Handling | Economic Protection | Reputation Gating |
|--------|------------------|---------------------|-------------------|
| **Ethereum** | Gas consumed on failure | No refunds | None |
| **Cosmos** | Gas refunded if out-of-gas | Partial refunds | None |
| **Web4** | Attribution + insurance + retry | Insurance + refunds | T3-based |

**Web4 Advantage**:
- Only system with failure attribution
- Only system with ATP insurance
- Only system with reputation-based gating
- Comprehensive 4-layer defense

## Next Steps

1. Implement Phase 1 (Failure Attribution)
2. Create test suite
3. Validate with SAGE execution
4. Document findings in ATTACK_VECTORS.md
5. Update status: ⚠️ VULNERABLE → ✅ MITIGATED
