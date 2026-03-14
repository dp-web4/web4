"""
SAGE-Web4 Trust Bridge
======================

Bridge between SAGE SNARC compression and Web4 T3/V3 trust framework.

Conceptual Mapping:
- SAGE uses 5-dimensional SNARC compression for attention allocation
- Web4 uses T3/V3 trust tensors for authorization decisions
- Both implement compression-action-threshold pattern

This module enables:
1. SNARC metrics → T3 trust scores (capability assessment)
2. SNARC metrics → V3 trust scores (transaction quality)
3. Bidirectional trust flow between SAGE and Web4 societies

Pattern Convergence:
┌─────────────────────────────────────────────────────────────┐
│ Synchronism: Intent field → tanh(γρ/ρ_crit) → quantum/class│
│ Web4: Multi-D reputation → trust score → authorize/deny    │
│ SAGE: 5D sensors → SNARC compression → attend/ignore       │
└─────────────────────────────────────────────────────────────┘

All three substrates use compression-action-threshold pattern.

Author: Legion Autonomous Session (2025-12-05)
Session: Track 10 - SAGE-Web4 Integration
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import math


# ============================================================================
# SNARC to T3 Mapping (Capability)
# ============================================================================

@dataclass
class SNARCDimensions:
    """SNARC dimensions (imported concept from SAGE)"""
    surprise: float = 0.0    # 0-1: prediction error
    novelty: float = 0.0     # 0-1: memory mismatch
    arousal: float = 0.0     # 0-1: computational activation
    reward: float = 0.0      # 0-1: goal achievement
    conflict: float = 0.0    # 0-1: hypothesis uncertainty


@dataclass
class T3Trust:
    """T3 Trust Tensor (Talent, Training, Temperament)"""
    talent: float      # 0-1: Innate capability
    training: float    # 0-1: Learned skill
    temperament: float # 0-1: Behavioral consistency

    def composite_score(self) -> float:
        """Geometric mean of T3 components"""
        return (self.talent * self.training * self.temperament) ** (1/3)


@dataclass
class V3Trust:
    """V3 Trust Tensor (Veracity, Validity, Valuation)"""
    veracity: float    # 0-1: Truthfulness
    validity: float    # 0-1: Claim correctness
    valuation: float   # 0-1: Value delivered

    def composite_score(self) -> float:
        """Geometric mean of V3 components"""
        return (self.veracity * self.validity * self.valuation) ** (1/3)


class SNARCToT3Mapper:
    """
    Map SNARC dimensions to T3 trust scores.

    Conceptual mapping:
    - Talent: How well agent handles novelty and surprise
    - Training: Consistent performance (low conflict, high reward)
    - Temperament: Stability (low arousal, predictable behavior)
    """

    def __init__(self):
        """Initialize mapper with default calibration"""
        # Calibration: SNARC values that indicate HIGH trust
        # (These would be learned from observed behavior)
        self.high_trust_snarc = {
            'surprise': 0.3,     # Moderate surprise OK (agent explores)
            'novelty': 0.4,      # Handles some novelty well
            'arousal': 0.2,      # Low arousal = stable
            'reward': 0.7,       # High reward = good outcomes
            'conflict': 0.1      # Low conflict = decisive
        }

    def compute_talent(self, snarc: SNARCDimensions) -> float:
        """
        Talent: Innate capability to handle novel, surprising situations.

        High talent agents:
        - Handle novelty without excessive arousal
        - Recover from surprise effectively (reward after surprise)
        - Don't get stuck in conflict when facing new situations

        Mapping:
        - Positive: Moderate novelty, moderate surprise (agent explores)
        - Negative: High conflict with novelty (gets confused)
        - Negative: High arousal with novelty (overwhelmed)
        """
        # Handle novelty (positive up to a point)
        novelty_handling = min(snarc.novelty / 0.5, 1.0) * 0.4

        # Handle surprise (moderate is good, extreme is bad)
        surprise_optimal = 0.3
        surprise_penalty = abs(snarc.surprise - surprise_optimal)
        surprise_score = max(0.0, 1.0 - surprise_penalty) * 0.3

        # Low conflict when novel (stays decisive)
        conflict_penalty = snarc.conflict if snarc.novelty > 0.3 else 0.0
        decisiveness = (1.0 - conflict_penalty) * 0.3

        talent = novelty_handling + surprise_score + decisiveness
        return min(1.0, max(0.0, talent))

    def compute_training(self, snarc: SNARCDimensions, history: List[SNARCDimensions]) -> float:
        """
        Training: Learned skill through consistent performance.

        High training agents:
        - Achieve rewards consistently
        - Low conflict (have learned the task)
        - Predictable behavior (low surprise to observers)

        Mapping:
        - Positive: High reward
        - Positive: Low conflict (knows what to do)
        - Positive: Consistency over time
        """
        # Reward achievement
        reward_score = snarc.reward * 0.4

        # Decisiveness (low conflict)
        decisiveness = (1.0 - snarc.conflict) * 0.3

        # Consistency (if history available)
        if len(history) >= 3:
            # Variance in reward (low variance = consistent training)
            rewards = [s.reward for s in history[-10:]]
            reward_variance = sum((r - sum(rewards)/len(rewards))**2 for r in rewards) / len(rewards)
            consistency = max(0.0, 1.0 - 2*reward_variance) * 0.3
        else:
            consistency = 0.15  # Neutral if no history

        training = reward_score + decisiveness + consistency
        return min(1.0, max(0.0, training))

    def compute_temperament(self, snarc: SNARCDimensions, history: List[SNARCDimensions]) -> float:
        """
        Temperament: Behavioral consistency and stability.

        Good temperament agents:
        - Low arousal (stable under load)
        - Consistent behavior over time
        - Predictable (low surprise to others)

        Mapping:
        - Positive: Low arousal
        - Positive: Low variance in arousal/conflict over time
        - Positive: Predictable reward patterns
        """
        # Stability (low arousal)
        stability = (1.0 - snarc.arousal) * 0.4

        # Predictability (low conflict)
        predictability = (1.0 - snarc.conflict) * 0.3

        # Consistency over time
        if len(history) >= 3:
            # Variance in arousal (low = stable temperament)
            arousals = [s.arousal for s in history[-10:]]
            arousal_variance = sum((a - sum(arousals)/len(arousals))**2 for a in arousals) / len(arousals)
            consistency = max(0.0, 1.0 - 3*arousal_variance) * 0.3
        else:
            consistency = 0.15  # Neutral if no history

        temperament = stability + predictability + consistency
        return min(1.0, max(0.0, temperament))

    def snarc_to_t3(
        self,
        current: SNARCDimensions,
        history: Optional[List[SNARCDimensions]] = None
    ) -> T3Trust:
        """
        Convert SNARC dimensions to T3 trust score.

        Args:
            current: Current SNARC dimensions
            history: Historical SNARC observations (for consistency metrics)

        Returns:
            T3Trust with computed talent, training, temperament
        """
        if history is None:
            history = []

        talent = self.compute_talent(current)
        training = self.compute_training(current, history)
        temperament = self.compute_temperament(current, history)

        return T3Trust(
            talent=talent,
            training=training,
            temperament=temperament
        )


class SNARCToV3Mapper:
    """
    Map SNARC dimensions to V3 trust scores (transaction quality).

    Conceptual mapping:
    - Veracity: Claims match reality (low surprise after action)
    - Validity: Actions produce intended effects (high reward)
    - Valuation: Value delivered vs promised (reward vs expectation)
    """

    def compute_veracity(self, snarc: SNARCDimensions, claimed_outcome: float) -> float:
        """
        Veracity: Truthfulness of claims.

        High veracity:
        - Low surprise (claims matched reality)
        - Actual reward matches claimed outcome

        Args:
            snarc: Observed SNARC after action
            claimed_outcome: What agent claimed would happen (0-1)

        Returns:
            Veracity score 0-1
        """
        # Low surprise = claims matched reality
        claim_match = (1.0 - snarc.surprise) * 0.6

        # Reward matched claimed outcome
        if claimed_outcome > 0:
            outcome_match = 1.0 - abs(snarc.reward - claimed_outcome)
            outcome_match = max(0.0, outcome_match) * 0.4
        else:
            outcome_match = 0.2  # Neutral if no claim

        veracity = claim_match + outcome_match
        return min(1.0, max(0.0, veracity))

    def compute_validity(self, snarc: SNARCDimensions) -> float:
        """
        Validity: Correctness of actions.

        High validity:
        - High reward (action worked)
        - Low conflict (action was appropriate)
        - Low arousal (action didn't cause problems)

        Returns:
            Validity score 0-1
        """
        # Action produced reward
        effectiveness = snarc.reward * 0.5

        # Action was appropriate (low conflict)
        appropriateness = (1.0 - snarc.conflict) * 0.3

        # Action didn't cause problems (low arousal)
        safety = (1.0 - snarc.arousal) * 0.2

        validity = effectiveness + appropriateness + safety
        return min(1.0, max(0.0, validity))

    def compute_valuation(
        self,
        snarc: SNARCDimensions,
        expected_reward: float,
        cost: float = 0.0
    ) -> float:
        """
        Valuation: Value delivered relative to expectation and cost.

        High valuation:
        - Actual reward ≥ expected reward
        - Reward >> cost (good ROI)
        - Low conflict (no hidden costs)

        Args:
            snarc: Observed SNARC after action
            expected_reward: What was expected (0-1)
            cost: Cost of action (0-1, e.g., ATP spent)

        Returns:
            Valuation score 0-1
        """
        # Exceeded expectations
        if expected_reward > 0:
            expectation_ratio = snarc.reward / expected_reward
            exceeded = min(1.0, expectation_ratio) * 0.5
        else:
            exceeded = snarc.reward * 0.5  # Any reward is good if none expected

        # ROI (reward vs cost)
        if cost > 0:
            roi = (snarc.reward - cost) / cost
            roi_score = min(1.0, max(0.0, roi)) * 0.3
        else:
            roi_score = 0.15  # Neutral if no cost

        # No hidden costs (low conflict/arousal)
        transparency = (1.0 - (snarc.conflict + snarc.arousal) / 2) * 0.2

        valuation = exceeded + roi_score + transparency
        return min(1.0, max(0.0, valuation))

    def snarc_to_v3(
        self,
        current: SNARCDimensions,
        claimed_outcome: float = 0.5,
        expected_reward: float = 0.5,
        cost: float = 0.0
    ) -> V3Trust:
        """
        Convert SNARC dimensions to V3 trust score.

        Args:
            current: Observed SNARC dimensions after transaction
            claimed_outcome: What agent claimed would happen
            expected_reward: What was expected
            cost: Cost of transaction (ATP, compute, etc.)

        Returns:
            V3Trust with computed veracity, validity, valuation
        """
        veracity = self.compute_veracity(current, claimed_outcome)
        validity = self.compute_validity(current)
        valuation = self.compute_valuation(current, expected_reward, cost)

        return V3Trust(
            veracity=veracity,
            validity=validity,
            valuation=valuation
        )


# ============================================================================
# Bidirectional Trust Flow
# ============================================================================

class SAGEWeb4TrustBridge:
    """
    Bidirectional trust flow between SAGE and Web4.

    SAGE → Web4:
    - SAGE agent's SNARC history → Web4 T3/V3 scores
    - Enable SAGE agents to participate in Web4 societies

    Web4 → SAGE:
    - Web4 trust scores → SAGE attention weighting
    - Enable Web4 reputation to influence SAGE attention
    """

    def __init__(self):
        """Initialize bridge with mappers"""
        self.t3_mapper = SNARCToT3Mapper()
        self.v3_mapper = SNARCToV3Mapper()

    def sage_to_web4_trust(
        self,
        agent_lct: str,
        snarc_history: List[SNARCDimensions],
        transaction_context: Optional[Dict] = None
    ) -> Tuple[T3Trust, Optional[V3Trust]]:
        """
        Convert SAGE agent's SNARC history to Web4 trust scores.

        Args:
            agent_lct: LCT identity of SAGE agent
            snarc_history: Historical SNARC observations
            transaction_context: Optional transaction details for V3

        Returns:
            (T3Trust, Optional[V3Trust]) tuple
        """
        if len(snarc_history) == 0:
            # No history - return default neutral scores
            t3 = T3Trust(talent=0.5, training=0.5, temperament=0.5)
            return t3, None

        # Compute T3 from history
        current = snarc_history[-1]
        t3 = self.t3_mapper.snarc_to_t3(current, snarc_history[:-1])

        # Compute V3 if transaction context provided
        v3 = None
        if transaction_context:
            v3 = self.v3_mapper.snarc_to_v3(
                current=current,
                claimed_outcome=transaction_context.get('claimed_outcome', 0.5),
                expected_reward=transaction_context.get('expected_reward', 0.5),
                cost=transaction_context.get('cost', 0.0)
            )

        return t3, v3

    def web4_to_sage_weight(
        self,
        t3_score: float,
        v3_score: Optional[float] = None
    ) -> float:
        """
        Convert Web4 trust scores to SAGE attention weight.

        High-trust entities get more attention weight in SAGE.

        Args:
            t3_score: T3 composite score (0-1)
            v3_score: Optional V3 composite score (0-1)

        Returns:
            Attention weight multiplier (0.1 - 2.0)
        """
        # T3 provides base weight (60%)
        base_weight = t3_score

        # V3 modulates if available (40%)
        if v3_score is not None:
            composite = 0.6 * t3_score + 0.4 * v3_score
        else:
            composite = t3_score

        # Map to attention weight range [0.1, 2.0]
        # 0.0 trust → 0.1x weight (minimal attention)
        # 0.5 trust → 1.0x weight (normal attention)
        # 1.0 trust → 2.0x weight (prioritized attention)
        weight = 0.1 + 1.9 * composite

        return weight


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    """Demonstrate SAGE-Web4 trust bridge"""

    # Example 1: SAGE agent with good performance
    print("=" * 60)
    print("Example 1: High-performing SAGE agent → Web4 trust")
    print("=" * 60)

    # SAGE agent history (good performance)
    good_agent_history = [
        SNARCDimensions(surprise=0.2, novelty=0.3, arousal=0.1, reward=0.8, conflict=0.1),
        SNARCDimensions(surprise=0.1, novelty=0.2, arousal=0.1, reward=0.9, conflict=0.05),
        SNARCDimensions(surprise=0.15, novelty=0.25, arousal=0.05, reward=0.85, conflict=0.1),
    ]

    bridge = SAGEWeb4TrustBridge()
    t3, v3 = bridge.sage_to_web4_trust(
        agent_lct="lct:sage:ai:good_agent:001",
        snarc_history=good_agent_history,
        transaction_context={
            'claimed_outcome': 0.8,
            'expected_reward': 0.7,
            'cost': 0.2
        }
    )

    print(f"T3 Trust:")
    print(f"  Talent: {t3.talent:.3f} (handles novelty well)")
    print(f"  Training: {t3.training:.3f} (consistent high reward)")
    print(f"  Temperament: {t3.temperament:.3f} (stable, low arousal)")
    print(f"  Composite: {t3.composite_score():.3f}")

    if v3:
        print(f"\nV3 Trust:")
        print(f"  Veracity: {v3.veracity:.3f} (claims matched reality)")
        print(f"  Validity: {v3.validity:.3f} (action worked)")
        print(f"  Valuation: {v3.valuation:.3f} (good ROI)")
        print(f"  Composite: {v3.composite_score():.3f}")

    # Example 2: Poor-performing agent
    print("\n" + "=" * 60)
    print("Example 2: Poor-performing SAGE agent → Web4 trust")
    print("=" * 60)

    poor_agent_history = [
        SNARCDimensions(surprise=0.7, novelty=0.6, arousal=0.8, reward=0.2, conflict=0.7),
        SNARCDimensions(surprise=0.8, novelty=0.5, arousal=0.9, reward=0.1, conflict=0.8),
    ]

    t3_poor, v3_poor = bridge.sage_to_web4_trust(
        agent_lct="lct:sage:ai:poor_agent:001",
        snarc_history=poor_agent_history,
        transaction_context={
            'claimed_outcome': 0.8,
            'expected_reward': 0.7,
            'cost': 0.3
        }
    )

    print(f"T3 Trust:")
    print(f"  Talent: {t3_poor.talent:.3f} (struggles with novelty)")
    print(f"  Training: {t3_poor.training:.3f} (poor reward consistency)")
    print(f"  Temperament: {t3_poor.temperament:.3f} (high arousal, unstable)")
    print(f"  Composite: {t3_poor.composite_score():.3f}")

    if v3_poor:
        print(f"\nV3 Trust:")
        print(f"  Veracity: {v3_poor.veracity:.3f} (claims didn't match)")
        print(f"  Validity: {v3_poor.validity:.3f} (action failed)")
        print(f"  Valuation: {v3_poor.valuation:.3f} (poor ROI)")
        print(f"  Composite: {v3_poor.composite_score():.3f}")

    # Example 3: Web4 trust → SAGE attention weight
    print("\n" + "=" * 60)
    print("Example 3: Web4 trust → SAGE attention weight")
    print("=" * 60)

    high_trust_weight = bridge.web4_to_sage_weight(
        t3_score=t3.composite_score(),
        v3_score=v3.composite_score() if v3 else None
    )

    low_trust_weight = bridge.web4_to_sage_weight(
        t3_score=t3_poor.composite_score(),
        v3_score=v3_poor.composite_score() if v3_poor else None
    )

    print(f"High-trust agent attention weight: {high_trust_weight:.2f}x")
    print(f"Low-trust agent attention weight: {low_trust_weight:.2f}x")
    print(f"\nHigh-trust agent gets {high_trust_weight/low_trust_weight:.1f}x more attention")

    print("\n" + "=" * 60)
    print("SAGE-Web4 Trust Bridge Demonstration Complete")
    print("=" * 60)
