# ATP Economic Analysis: Attack Cost Modeling

**Date**: 2025-11-30
**Session**: Legion Autonomous Web4 Research
**Status**: Research Analysis

---

## Executive Summary

This document analyzes the economic viability of Web4's ATP-based Sybil resistance and attack deterrence mechanisms. The key question: **Are current stake amounts (75k-300k ATP) actually deterrent to attackers?**

**Short Answer**: Current stakes provide meaningful deterrence IF:
1. ATP has real economic value (market price)
2. Attack success probability is low (<30%)
3. Detection happens before significant profit extraction

**Research Gap**: No empirical data on attacker ROI, market pricing, or real-world validation.

---

## Current ATP Pricing Framework

### Base Operation Costs (Calibrated)

From `game/atp_pricing_calibrated.json`:

| Complexity | ATP Cost | Example Operations |
|-----------|----------|-------------------|
| Low | 10.8 ATP | Simple queries, cache hits |
| Medium | 34.0 ATP | Text generation, moderate inference |
| High | 56.1 ATP | Vision processing, complex reasoning |
| Critical | 200 ATP | Multi-modal coordination, high-stakes decisions |

**Multipliers**:
- Latency premium: 0.23× (low latency operations cost more)
- Quality premium: 8.15× (high quality requirements cost more)
- Complexity factor: 1.0× (baseline)

### Identity Stake Costs

From `game/engine/atp_aware_identity_stakes.py` and Session #86 THREAT_MODEL.md:

| Identity Type | Horizon | Privilege | ATP Stake |
|--------------|---------|-----------|-----------|
| LOCAL agent | LOCAL | NORMAL | 1,000 ATP |
| REGIONAL witness | REGIONAL | HIGH | 25,000 ATP |
| **GLOBAL coordinator** | **GLOBAL** | **CRITICAL** | **75,000 ATP** |

**Attack Scenarios**:
- **Single GLOBAL Sybil**: 75,000 ATP
- **Cartel (3 GLOBAL platforms)**: 225,000 ATP (3×75k)
- **Eclipse (5 GLOBAL platforms)**: 300,000 ATP (5×75k minimum)

---

## Attack Cost vs. Benefit Analysis

### Attack Scenario 1: Quality Score Inflation

**Setup**:
- Attacker creates 1 GLOBAL Sybil platform
- Provides execution services to victims
- Inflates quality scores to maximize ATP payment
- Extracts value before detection

**Costs**:
- **Stake**: 75,000 ATP
- **Operating costs**: ~1,000 ATP/day (infrastructure, actual execution)
- **Total upfront**: 76,000 ATP

**Benefits** (if undetected):
- Victim pays for "high quality" but receives "medium quality"
- Quality inflation: 20-30% markup (56 ATP vs 34 ATP)
- Volume: 100 tasks/day × 30 days = 3,000 tasks
- **Profit**: 3,000 tasks × 20 ATP markup = 60,000 ATP/month
- **ROI**: 60k profit / 76k cost = **-21% first month, +79% over 2 months**

**Detection**:
- Challenge-response system (Session #84)
- Victim re-executes 10% of tasks randomly
- Detect quality mismatch after ~30 task samples
- **Detection time**: 3-10 days (probabilistic)
- **Profit before detection**: 1,000-3,000 tasks × 20 ATP = 20k-60k ATP
- **Net outcome**: -16k to +44k ATP (VARIABLE - depends on detection speed)

**Deterrence Analysis**:
- ⚠️ **PARTIAL DETERRENT**: Profitable IF detection takes >10 days
- ✅ **DETERRENT**: If detection <5 days OR challenge rate >20%

---

### Attack Scenario 2: Witness Cartel

**Setup**:
- 3 GLOBAL platforms collude
- All attest to each other's (inflated) execution quality
- Consensus validation requires 3/3 agreement
- Extract profits until detected

**Costs**:
- **Stakes**: 225,000 ATP (3 platforms × 75k)
- **Operating costs**: ~3,000 ATP/day (3 platforms)
- **Coordination overhead**: Communication, profit-sharing disputes
- **Total upfront**: 228,000 ATP

**Benefits** (if undetected):
- Cartel controls consensus for their tasks
- Each member inflates scores by 30%
- Volume: 300 tasks/day combined × 30 days = 9,000 tasks
- **Profit**: 9,000 × 20 ATP = 180,000 ATP/month
- **ROI**: 180k profit / 228k cost = **-21% first month, +79% over 2 months**

**Detection**:
- Cartel detector (Session #86): Co-witnessing correlation ≥ 0.8 flagged
- Statistical likelihood of 3 platforms ALWAYS agreeing: < 0.1% natural
- **Detection time**: 5-10 co-witness events = 5-10 days
- **Profit before detection**: 30k-90k ATP
- **Net outcome**: -198k to -138k ATP (LOSS - early detection)

**Deterrence Analysis**:
- ✅ **STRONG DETERRENT**: Cartel detection very effective
- Attack requires:
  - 3 coordinated actors (conspiracy risk)
  - High upfront cost (225k ATP)
  - Fast detection (5-10 days)
  - Reputation destruction (all 3 platforms)
- **Conclusion**: Economically unfavorable

---

### Attack Scenario 3: Eclipse Attack (5 Platforms)

**Setup**:
- 5 GLOBAL platforms created by single attacker
- Controls majority of federation witnesses
- Can fabricate consensus at will
- Extracts maximum value

**Costs**:
- **Stakes**: 375,000 ATP minimum (5 platforms × 75k)
- **Operating costs**: ~5,000 ATP/day
- **Infrastructure**: Hardware for 5 platforms
- **Total upfront**: 380,000 ATP

**Benefits** (if undetected):
- Complete consensus control
- Inflate all scores maximally (100%+ markup)
- Volume: 500 tasks/day × 30 days = 15,000 tasks
- **Profit**: 15,000 × 40 ATP markup = 600,000 ATP/month
- **ROI**: 600k profit / 380k cost = **+58% first month**

**Detection**:
- Platform diversity requirement (Session #86): ≥3 independent platforms
- If attacker controls 5/8 total platforms = 62.5% dominance
- Cross-platform validation detects same-source platforms via:
  - Network topology (same IP ranges)
  - Timing correlation (synchronized responses)
  - Hardware fingerprints (if implemented)
- **Detection time**: Variable (2 weeks to 2 months)
- **Profit before detection**: 300k-600k ATP
- **Net outcome**: -80k to +220k ATP (POTENTIALLY PROFITABLE)

**Deterrence Analysis**:
- ⚠️ **WEAK DETERRENT**: Potentially profitable despite high cost
- **Critical gap**: Requires diverse platform population (≥8 total)
- If only 5-6 platforms exist globally, attacker can dominate
- **Mitigation**: Geographic/network diversity requirements

---

## Economic Modeling: Real-World ATP Value

### What is 1 ATP Worth?

**Computation Cost Basis**:
- Medium complexity task: 34 ATP
- Actual compute cost: ~0.5-2 GPU-seconds (inference)
- Cloud GPU cost: $0.0001-0.001 per GPU-second
- **Implied ATP value**: $0.000003-0.00003 per ATP
- **Or**: 1 ATP = 33,000-330,000 operations per $1

**Alternate: Energy Basis**:
- GPU power: 300W typical
- Task duration: 1-5 seconds
- Energy: 0.3-1.5 Wh per task (34 ATP)
- Electricity cost: $0.15/kWh
- **Task energy cost**: $0.000045-0.000225
- **Implied ATP value**: $0.0000013-0.0000066 per ATP

**Market Pricing (Hypothetical)**:
If Web4 ATP were tradable:
- Comparison to cloud credits (AWS, GCP)
- Typical markup: 2-5× over cost
- **Market ATP value**: $0.000006-0.00015 per ATP (2-5× energy cost)

**Attack Cost Translation**:

| Attack | ATP Cost | USD (Energy) | USD (Market) |
|--------|----------|--------------|--------------|
| Single Sybil | 75,000 ATP | $0.10-$0.50 | $0.45-$11.25 |
| Cartel (3) | 225,000 ATP | $0.29-$1.49 | $1.35-$33.75 |
| Eclipse (5) | 375,000 ATP | $0.49-$2.48 | $2.25-$56.25 |

**Reality Check**:
- Current stakes deter trivial attacks (pennies at risk)
- But not serious adversaries (dollars of risk)
- **Conclusion**: Stakes need 100-1000× increase for real deterrence OR ATP needs real market value

---

## Empirical Validation Gaps

### Gap 1: No Real Market Data

**Problem**: ATP pricing is calibrated to compute cost, not market value

**Needed**:
- Real users buying/selling ATP
- Price discovery via market mechanisms
- Validation that 75k ATP is "expensive"

**Current State**: Theoretical pricing only

---

### Gap 2: No Attack Simulations

**Problem**: All attack cost analysis is hypothetical

**Needed**:
- Agent-based simulations of attackers
- Measure actual profit extraction before detection
- Test cartel formation dynamics
- Validate detection times

**Current State**: No empirical validation

---

### Gap 3: No Game-Theoretic Analysis

**Problem**: Unknown if honest behavior is Nash equilibrium

**Needed**:
- Formal game theory model
- Calculate expected utility for honest vs malicious
- Determine if current penalties create incentive for honesty
- Identify parameter ranges for stable equilibrium

**Current State**: Designed by intuition, not proven

---

## Recommendations

### Priority 1: Economic Simulation (High Impact)

**Goal**: Validate attack costs empirically

**Approach**:
```python
class AttackerAgent:
    """Simulated attacker agent"""
    stake: float = 75_000  # ATP
    daily_profit_target: float = 10_000  # ATP
    risk_tolerance: float = 0.3  # 30% chance of detection acceptable

    def decide_attack(self) -> bool:
        """Game-theoretic decision to attack"""
        expected_profit = self.estimate_profit()
        detection_probability = self.estimate_detection_risk()
        expected_value = expected_profit * (1 - detection_probability) - self.stake * detection_probability
        return expected_value > 0

class DefenderAgent:
    """Simulated defender (challenge system)"""
    challenge_rate: float = 0.10  # 10% of tasks
    detection_threshold: int = 3  # Quality mismatches

    def detect_attack(self, attacker: AttackerAgent) -> bool:
        """Probabilistic detection"""
        challenges = self.challenge_rate * attacker.tasks_completed
        quality_mismatches = sum(1 for _ in range(int(challenges)) if random() < 0.8)
        return quality_mismatches >= self.detection_threshold
```

**Metrics**:
- Time to detection (days)
- Profit before detection (ATP)
- Net ROI (%)
- Attack frequency (% of agents who attack)

**Expected Outcome**: Identify minimum stake amounts for deterrence

---

### Priority 2: Stake Amount Calibration (High Impact)

**Current Stakes** (from Session #86):
- GLOBAL LCT: 75,000 ATP

**Proposed Stakes** (based on attack analysis):

| Scenario | Current | Recommended | Multiplier |
|----------|---------|-------------|------------|
| Quality inflation deterrence | 75k ATP | 150k-300k ATP | 2-4× |
| Cartel deterrence | 225k ATP | 450k-900k ATP | 2-4× |
| Eclipse deterrence | 375k ATP | 1M-2M ATP | 3-5× |

**Rationale**:
- Current stakes marginally profitable for sophisticated attacks
- 2-4× increase makes attacks unprofitable unless detection >30 days
- Preserves accessibility for honest participants (still <1% of monthly compute budget)

**Implementation**:
```python
# Update atp_aware_identity_stakes.py
GLOBAL_BASE_STAKE = 150_000  # Was 75,000 (2× increase)
CRITICAL_PRIVILEGE_MULTIPLIER = 3.0  # Was 2.0
# Resulting GLOBAL CRITICAL stake: 450,000 ATP
```

---

### Priority 3: Market Mechanisms (Medium Impact)

**Goal**: Establish real ATP value through market

**Approach**:
1. **Internal market**: Allow platforms to trade ATP
2. **Price discovery**: Order book with bids/asks
3. **Stake-to-market ratio**: Require stakes = 30-90 days of trading volume
4. **Dynamic adjustment**: Stakes adjust based on market price

**Benefits**:
- ATP price reflects actual scarcity/demand
- Stakes auto-calibrate to economic conditions
- Real economic deterrence (not theoretical)

---

### Priority 4: Detection Optimization (High Impact)

**Current Detection** (Session #84, #86):
- Challenge-response: 10% of tasks re-executed
- Cartel detection: Co-witnessing correlation
- Quality validation: Consensus vs claimed quality

**Improvements**:

1. **Adaptive challenge rate**:
   ```python
   # Increase challenges for low-reputation platforms
   challenge_rate = base_rate * (1 + reputation_penalty)
   # High-rep platforms: 5% challenges
   # Low-rep platforms: 20-50% challenges
   ```

2. **Temporal correlation**:
   ```python
   # Detect platforms that always agree (cartel indicator)
   correlation = agreement_count / co_witness_count
   if correlation > 0.8 and co_witness_count > 10:
       flag_as_potential_cartel()
   ```

3. **Statistical anomaly detection**:
   ```python
   # Natural quality scores follow normal distribution
   # Inflation creates non-normal patterns
   quality_scores = platform.get_recent_scores()
   if ks_test(quality_scores, normal_distribution) > 0.05:
       trigger_audit()
   ```

**Expected Impact**:
- Reduce detection time from 10 days → 3-5 days
- Makes attacks unprofitable at current stake levels

---

## Game-Theoretic Framework (Future Work)

### Honest Strategy Payoff

**Honest Platform**:
- Upfront cost: 75,000 ATP stake
- Monthly revenue: 100 tasks/day × 34 ATP × 30 days = 102,000 ATP
- Operating costs: 1,000 ATP/day × 30 = 30,000 ATP
- **Net profit**: 72,000 ATP/month
- **ROI**: 72k / 75k = 96% per month = **breakeven in 1 month**

### Malicious Strategy Payoff

**Malicious Platform** (quality inflation):
- Upfront cost: 75,000 ATP stake
- Monthly revenue: 100 tasks/day × 56 ATP (inflated) × 30 days = 168,000 ATP
- Actual costs: 100 × 34 ATP × 30 = 102,000 ATP (medium quality delivered)
- Markup profit: 66,000 ATP
- Operating costs: 30,000 ATP
- **Expected profit**: 66k - 30k = 36k ATP/month
- Detection probability: 0.7 (70% detected in first month)
- **Expected value**: 36k × 0.3 - 75k × 0.7 = **-41,700 ATP (LOSS)**

**Nash Equilibrium**:
- Honest: +72k ATP/month (certain)
- Malicious: -41.7k ATP/month (expected value)
- **Conclusion**: Honest strategy dominates IF detection probability > 60%

**Critical Parameter**: Detection effectiveness

---

## Conclusions

### Current State Assessment

**Strengths**:
- ✅ ATP pricing framework calibrated to real compute costs
- ✅ Dynamic stakes scale with privilege and horizon
- ✅ Multi-layer defense (economic + cryptographic + social)
- ✅ Cartel detection via co-witnessing correlation

**Weaknesses**:
- ❌ No empirical validation of attack costs
- ❌ No game-theoretic proof of Nash equilibrium
- ❌ Stakes may be too low (75k ATP potentially profitable for eclipse)
- ❌ No real market for ATP (theoretical pricing only)

**Risk Level**:
- Low-sophistication attacks: **DETERRED** (not worth effort)
- Medium-sophistication attacks: **PARTIALLY DETERRED** (marginal profit)
- High-sophistication attacks: **POTENTIALLY PROFITABLE** (if detection slow)

---

### Recommended Actions

**Immediate** (Next Session):
1. Implement agent-based attack simulation (Priority 1)
2. Measure empirical detection times and profit extraction
3. Calibrate stake amounts based on simulation results

**Near-Term** (Next 2 Weeks):
4. Create game-theoretic model of honest vs malicious strategies
5. Calculate Nash equilibrium for current parameters
6. Identify parameter ranges (stake, detection rate, challenge rate) for stable honesty

**Long-Term** (Next Month):
7. Implement internal ATP market for price discovery
8. Add geographic/network diversity requirements
9. Create dynamic stake adjustment based on market conditions

---

### Key Insight: Detection is Critical

The deterrence effectiveness of ATP stakes depends heavily on detection speed:

| Detection Time | Attack ROI | Deterrence Level |
|----------------|-----------|------------------|
| < 5 days | -60% | ✅ STRONG |
| 5-10 days | -20% to +20% | ⚠️ MARGINAL |
| 10-20 days | +50% to +100% | ❌ WEAK |
| > 20 days | +200%+ | ❌ PROFITABLE |

**Conclusion**: Current 75k ATP stakes ARE deterrent IF detection is fast (<5 days). But we have no empirical data on actual detection times.

**Research Priority**: Measure real-world detection performance through adversarial testing.

---

**Status**: ⚠️ RESEARCH REQUIRED

**Next Steps**: Agent-based simulation + game-theoretic analysis

**Quote**: *"In research, deviation from expectation is data."* - We need empirical validation, not just theoretical analysis.

---

Co-Authored-By: Claude <noreply@anthropic.com>
