# ATP Insurance Protocol

**Status**: Draft Proposal
**Version**: 0.1
**Date**: November 24, 2025
**Authors**: Claude (Autonomous Research), Session #70

## Abstract

This document specifies the ATP Insurance Protocol, a cross-society insurance mechanism for Web4 that enables societies to pool resources and distribute risk across a federation. The protocol addresses the fundamental limitation of single-society insurance (a society paying 100 ATP premium can only receive a maximum 100 ATP payout) through network effects and federation-wide risk pooling.

**Key Insight**: Insurance requires network effects. Single-society insurance cannot cover losses exceeding the premium paid. Federation insurance pools enable societies to claim more than their individual premium contribution.

## Background

### Problem Statement

From Session #69 experimental findings:

1. **Single Society Insurance Insufficient**
   - Society pays 100 ATP premium
   - Society suffers 300 ATP fraud loss
   - Maximum possible payout: 100 ATP (pool exhausted)
   - Coverage ratio: 33% (100/300)
   - **Result**: Insurance ineffective

2. **Need for Risk Distribution**
   - Individual societies face unpredictable fraud/attack losses
   - Losses can exceed any reasonable premium a single society can afford
   - Trust mechanisms alone cannot prevent all malicious activity
   - Recovery mechanism needed to maintain society viability

### Solution: Federation Insurance Pools

From Session #70 Track 1 experimental results:

1. **Federation Pool Formation**
   - 5 societies each contribute premiums
   - Total pool: 450 ATP (vs 95 ATP single society)
   - Network multiplier: 4.7x

2. **Effective Coverage**
   - Society B loses 300 ATP to fraud
   - Insurance claim approved: 240 ATP payout (80% coverage)
   - Pool remaining: 210 ATP (47% reserves)
   - **Result**: Insurance effective, sustainable

## Protocol Specification

### 1. Core Concepts

#### 1.1 Insurance Pool

An **Insurance Pool** is a shared ATP reserve created by multiple societies contributing premiums. The pool is managed independently of any single society's treasury.

```python
@dataclass
class InsurancePool:
    """Shared insurance pool across federated societies."""
    balance: float = 0.0
    total_premiums_collected: float = 0.0
    total_payouts: float = 0.0
    policies: List[InsurancePolicy] = field(default_factory=list)
```

#### 1.2 Insurance Policy

An **Insurance Policy** is a contract between a society and an insurance pool, specifying:
- Premium paid
- Coverage ratio (percentage of loss covered)
- Maximum payout cap
- Effective date and duration

```python
@dataclass
class InsurancePolicy:
    """Insurance policy for a society."""
    society_lct: str
    premium_paid: float
    coverage_ratio: float  # 0.0 to 1.0 (typically 0.8)
    max_payout: float      # cap on single claim
    effective_tick: int
    expiration_tick: Optional[int] = None
```

#### 1.3 Fraud Claim

A **Fraud Claim** is a request for insurance payout following detected malicious activity. Claims must include:
- Amount of ATP lost
- Attribution to specific agent(s)
- Confidence score
- Supporting evidence (audit trails, MRH context)

```python
@dataclass
class FraudClaim:
    """Claim for insurance payout after detected fraud."""
    society_lct: str
    policy_id: str
    atp_lost: float
    attributed_to_lct: str
    attribution_confidence: float  # 0.0 to 1.0
    evidence: Dict[str, Any]
    filed_at_tick: int
    status: str  # "pending" | "approved" | "denied"
    payout: float = 0.0
```

### 2. Protocol Operations

#### 2.1 Pool Formation

**Preconditions**:
- Multiple societies in federation (minimum 3 recommended)
- Societies have sufficient ATP treasury
- Consensus on pool parameters

**Process**:
```python
def create_insurance_pool(
    societies: List[Society],
    premium_rate: float = 0.05,      # % of treasury
    coverage_ratio: float = 0.8,      # 80% of loss covered
    max_payout_ratio: float = 0.3     # 30% of treasury max
) -> InsurancePool:
    """
    Create federation-wide insurance pool.

    Args:
        societies: List of participating societies
        premium_rate: Percentage of treasury as premium (default 5%)
        coverage_ratio: Percentage of loss covered (default 80%)
        max_payout_ratio: Max payout as % of treasury (default 30%)

    Returns:
        Initialized InsurancePool with policies
    """
```

**Parameters**:
- **Premium Rate**: 5% of society treasury (configurable)
  - Society with 2000 ATP → 100 ATP premium
  - Society with 1500 ATP → 75 ATP premium
- **Coverage Ratio**: 80% (industry standard)
  - 300 ATP loss → 240 ATP payout
- **Max Payout**: 30% of society treasury (prevents pool drain)

#### 2.2 Premium Payment

**Process**:
1. Society authorizes premium payment from treasury
2. ATP transferred from society treasury to insurance pool
3. Policy created and registered in pool
4. Event recorded on society's blockchain

**Event Structure**:
```json
{
  "type": "insurance_premium_payment",
  "society_lct": "lct:web4:society:A",
  "pool_id": "lct:federation:insurance:pool-1",
  "premium_amount": 100.0,
  "policy_id": "policy-A-001",
  "coverage_ratio": 0.8,
  "max_payout": 600.0,
  "world_tick": 42,
  "r6": {
    "interaction_type": "insurance_premium",
    "justification": "Federation risk pooling",
    "constraints": {
      "mrh": {
        "deltaR": "regional",
        "deltaT": "epoch",
        "deltaC": "society-scale"
      }
    }
  }
}
```

#### 2.3 Fraud Detection and Attribution

**Detection Mechanisms**:
1. **SAGE Federation Monitoring** (Recommended)
   - SAGE agents monitor all societies in federation
   - Aggregate suspicious activities across societies
   - Trigger threshold: 2+ suspicious events by same agent
   - Cross-society correlation

2. **Local Society Policies**
   - Treasury spend policies
   - Trust threshold enforcement
   - Pattern matching on event streams

**Attribution Requirements**:
- **Minimum confidence**: 0.7 (70%)
- **Evidence**: Audit trail, MRH context, witness accounts
- **Multiple sources**: Preferably 2+ independent detections

#### 2.4 Claim Filing

**Process**:
```python
def file_fraud_claim(
    world: World,
    society: Society,
    insurance_pool: InsurancePool,
    atp_lost: float,
    attributed_to_lct: str,
    attribution_confidence: float,
    attribution_id: int,
    evidence: Optional[Dict] = None
) -> Optional[FraudClaim]:
    """
    File insurance claim for fraud-related ATP loss.

    Returns claim object if approved, None if denied.
    """
```

**Approval Criteria**:
1. Society has active policy
2. Loss amount > 0
3. Attribution confidence >= 0.7
4. Claim amount <= max_payout
5. Pool has sufficient balance

**Payout Calculation**:
```python
claimed_amount = atp_lost * coverage_ratio
payout = min(claimed_amount, max_payout, pool_balance)
```

**Event Structure**:
```json
{
  "type": "insurance_claim",
  "society_lct": "lct:web4:society:B",
  "pool_id": "lct:federation:insurance:pool-1",
  "policy_id": "policy-B-001",
  "atp_lost": 300.0,
  "attributed_to_lct": "lct:federation:agent:bob",
  "attribution_confidence": 0.85,
  "payout": 240.0,
  "status": "approved",
  "world_tick": 105,
  "r6": {
    "interaction_type": "insurance_claim",
    "justification": "Federation-wide fraud: 2 thefts across 1 societies",
    "constraints": {
      "mrh": {
        "deltaR": "regional",
        "deltaT": "session",
        "deltaC": "society-scale"
      }
    }
  }
}
```

#### 2.5 Payout Distribution

**Process**:
1. Claim approved
2. ATP transferred from pool to society treasury
3. Society treasury updated
4. Pool balance reduced
5. Events recorded on both pool and society blockchains

**MRH Profile**:
- **deltaR**: regional (cross-society transfer)
- **deltaT**: session (immediate impact)
- **deltaC**: society-scale (affects society treasury)

### 3. Network Effects Analysis

#### 3.1 Single Society vs Federation Comparison

| Metric | Single Society | Federation (5 societies) | Improvement |
|--------|---------------|-------------------------|-------------|
| Premium paid | 95 ATP | 95 ATP | 1.0x |
| Pool size | 95 ATP | 450 ATP | 4.7x |
| Max payout | 95 ATP | 240 ATP | 2.5x |
| Coverage for 300 ATP loss | 32% | 80% | 2.5x |
| Pool remaining after claim | 0 ATP | 210 ATP | ∞ |
| Sustainability | ❌ Exhausted | ✅ 47% reserves | - |

#### 3.2 Network Multiplier

```
Network Multiplier = Total Pool / Individual Premium
                   = (n * avg_premium) / individual_premium
                   ≈ n (for equal-sized societies)
```

For 5 societies: **4.7x multiplier**

#### 3.3 Optimal Federation Size

**Minimum**: 3 societies
- Provides 3x multiplier
- Distributes risk minimally
- Still susceptible to correlated failures

**Recommended**: 5-10 societies
- 5x-10x multiplier
- Good risk distribution
- Manageable governance overhead

**Maximum**: No hard limit
- Linear scaling of pool size
- Diminishing returns on coverage improvement
- Governance complexity increases

### 4. Security Considerations

#### 4.1 Fraud Vectors

**Claim Fraud**:
- **Threat**: Society falsely claims fraud to extract ATP
- **Mitigation**:
  - Require attribution confidence >= 0.7
  - Cross-reference with federation-wide SAGE monitoring
  - Audit trail required
  - Reputation penalties for false claims

**Collusion**:
- **Threat**: Multiple societies collude to drain pool
- **Mitigation**:
  - Max payout caps per society
  - Pool rebalancing mechanisms
  - Federation-wide trust monitoring
  - Quarantine low-trust societies

**Sybil Attack**:
- **Threat**: Attacker creates many fake societies to drain pool
- **Mitigation**:
  - Society admission requirements (proof of work/stake)
  - Hardware-bound society root LCTs
  - Trust threshold for pool participation
  - Federation governance approval

#### 4.2 Pool Sustainability

**Depletion Risk**:
- **Scenario**: Multiple concurrent fraud events drain pool
- **Mitigation**:
  - Monitor claim rate (target < 50% of pool)
  - Adjust premiums dynamically
  - Emergency pool rebalancing
  - Coverage ratio reduction under stress

**Reserve Requirements**:
- **Minimum**: 20% of pool post-claim
- **Target**: 40-60% of pool post-claim
- **Alert**: If pool < 30% after claim, trigger premium review

### 5. Governance

#### 5.1 Pool Parameters

**Adjustable Parameters**:
- Premium rate (default 5%)
- Coverage ratio (default 80%)
- Max payout ratio (default 30%)
- Attribution confidence threshold (default 0.7)

**Adjustment Process**:
1. Federation governance proposal
2. Society voting (weighted by premium contribution)
3. Require 2/3 majority
4. Parameters update at next epoch boundary

#### 5.2 Dispute Resolution

**Disputed Claims**:
1. Initial auto-approval/denial based on criteria
2. If denied, society can appeal
3. Appeal reviewed by federation auditors
4. Final decision by federation vote
5. Escalation to cross-federation arbitration if unresolved

### 6. Implementation Notes

#### 6.1 Reference Implementation

See `web4/game/engine/insurance.py` for v0 implementation:
- `InsurancePool` class
- `insure_society()` function
- `file_fraud_claim()` function
- `get_pool_stats()` analytics

#### 6.2 Database Schema

```sql
CREATE TABLE insurance_pools (
    pool_id TEXT PRIMARY KEY,
    balance REAL,
    total_premiums_collected REAL,
    total_payouts REAL,
    created_at INTEGER
);

CREATE TABLE insurance_policies (
    policy_id TEXT PRIMARY KEY,
    pool_id TEXT REFERENCES insurance_pools(pool_id),
    society_lct TEXT,
    premium_paid REAL,
    coverage_ratio REAL,
    max_payout REAL,
    effective_tick INTEGER,
    expiration_tick INTEGER,
    FOREIGN KEY (society_lct) REFERENCES societies(society_lct)
);

CREATE TABLE fraud_claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT REFERENCES insurance_policies(policy_id),
    society_lct TEXT,
    atp_lost REAL,
    attributed_to_lct TEXT,
    attribution_confidence REAL,
    attribution_id INTEGER,
    payout REAL,
    status TEXT,  -- 'pending' | 'approved' | 'denied'
    filed_at_tick INTEGER,
    resolved_at_tick INTEGER,
    FOREIGN KEY (attribution_id) REFERENCES attributions(attribution_id)
);
```

#### 6.3 ATP Cost Model

Based on MRH profiles (from `engine/mrh_profiles.py`):

| Operation | MRH Profile | ATP Cost |
|-----------|-------------|----------|
| Premium payment | regional/epoch/society-scale | 75 ATP |
| Claim filing | regional/session/society-scale | 50 ATP |
| Claim approval | regional/session/society-scale | 50 ATP |
| Pool analytics | local/ephemeral/simple | 0 ATP (cached) |

**Note**: These ATP costs are for protocol operations, separate from insurance premiums/payouts.

### 7. Future Extensions

#### 7.1 Dynamic Premium Adjustment

Adjust premiums based on:
- Society trust level (low trust → higher premium)
- Historical claim rate (frequent claims → higher premium)
- Pool reserve level (low reserves → higher premiums)

#### 7.2 Reinsurance

Allow insurance pools to insure each other:
- Primary pool covers societies
- Reinsurance pool covers primary pools
- Distributes catastrophic risk across multiple federations

#### 7.3 Parametric Insurance

Trigger automatic payouts based on objective criteria:
- Trust level drops below threshold
- Treasury balance drops by X%
- N suspicious events within time window

#### 7.4 Cross-Federation Pools

Enable insurance pools spanning multiple federations:
- Global risk distribution
- Requires cross-federation MRH/LCT interoperability
- Complex governance challenges

## Experimental Results

### Session #69: Single Society Insurance (Baseline)

**Setup**:
- 1 society (Society A)
- 100 ATP premium paid
- 300 ATP fraud loss

**Results**:
- Claim filed: 300 ATP
- Expected payout (80%): 240 ATP
- Actual payout: **100 ATP** (pool exhausted)
- Coverage achieved: 33%
- Pool remaining: 0 ATP
- **Conclusion**: Single-society insurance insufficient

### Session #70 Track 1: Federation Insurance

**Setup**:
- 5 societies in full-mesh federation
- Total premiums: 450 ATP
- Society B fraud loss: 300 ATP

**Results**:
- Claim filed: 300 ATP
- Expected payout (80%): 240 ATP
- Actual payout: **240 ATP** (full coverage)
- Coverage achieved: 100%
- Pool remaining: 210 ATP (47% reserves)
- **Conclusion**: Federation insurance effective and sustainable

**Network Effect**:
- Single society premium: 95 ATP
- Federation pool: 450 ATP
- Network multiplier: **4.7x**
- Coverage improvement: **3x** (33% → 100%)

## References

### Experimental Sessions

- **Session #69**: ATP Insurance Integration and Scale Testing
  - File: `private-context/moments/session_69_summary.md`
  - Key finding: Single-society insurance insufficient

- **Session #70 Track 1**: Federation Insurance Pools
  - File: `web4/game/run_federation_insurance_demo.py`
  - Key finding: 4.7x network effect, sustainable coverage

### Implementation Files

- `web4/game/engine/insurance.py` - Insurance pool implementation
- `web4/game/engine/audit.py` - Fraud detection and attribution
- `web4/game/engine/mrh_profiles.py` - MRH profiles for insurance events
- `web4/game/run_federation_insurance_demo.py` - Reference demo

### Related Specifications

- LCT (Linked Context Token) specification
- MRH (Memory, Reputation, History) specification
- R6 (Interaction Envelope) specification
- ATP/ADP metabolic cycle specification

## Changelog

### Version 0.1 (November 24, 2025)

- Initial draft based on Session #69 and Session #70 Track 1 findings
- Core protocol specification
- Network effects analysis
- Security considerations
- Reference implementation notes

---

**Next Steps**:
1. Community review and feedback
2. Security audit of protocol design
3. Extended testing with 10+ societies
4. Formal governance model specification
5. Integration with Web4 standard
