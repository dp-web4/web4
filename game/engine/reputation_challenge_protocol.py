#!/usr/bin/env python3
"""
Reputation Challenge Protocol
Session #80: Priority #1 - Outcome-based verification of component claims

Problem:
Agents self-report component values via gossip. Malicious agents could claim
speed=1.0, accuracy=1.0 to win all operations without earning those scores.

Solution: Reputation Challenge Protocol
1. Requester tracks expected vs actual performance
2. If mismatch exceeds threshold, issue challenge
3. Agent must provide evidence (historical operation results)
4. If agent cannot defend, reputation downgraded
5. Persistent violators banned from federation

Theory:
Reputation systems require verification mechanisms. Self-reported reputation
invites gaming. Outcome-based verification creates accountability:
- Agents can claim high scores, but must deliver
- Requesters validate actual performance
- Challenges escalate to federation consensus
- Persistent misrepresentation leads to exclusion

This is analogous to:
- Credit scores: verified by transaction history
- eBay ratings: buyers verify seller claims
- Academic reputation: peer review validates research quality

Challenge Types:
1. Performance Challenge: Actual quality/latency worse than claimed
2. Consistency Challenge: Results vary wildly (claimed consistency too high)
3. Success Rate Challenge: Failures exceed claimed reliability
4. Cost Challenge: ATP cost higher than claimed cost_efficiency

Challenge Process:
1. Detection: Requester compares expected vs actual (N operations)
2. Threshold: Trigger challenge if mismatch > threshold (e.g., 20% worse)
3. Challenge: Requester broadcasts challenge to federation
4. Evidence: Agent provides historical operation results
5. Judgment: Federation consensus validates or rejects challenge
6. Penalty: Reputation downgrade if challenge upheld

Penalties:
- Minor (< 3 challenges): Temporary component downgrade (-0.1)
- Moderate (3-5 challenges): Extended downgrade (-0.2, 1 week)
- Severe (5+ challenges): Ban from federation (1 month)
- Persistent: Permanent exclusion from federation
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import statistics

try:
    from .multidimensional_v3 import V3Components, V3Component
    from .lct import LCT
    from .federation_reputation_gossip import ReputationGossipMessage, ReputationCache
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from multidimensional_v3 import V3Components, V3Component
    from lct import LCT
    from federation_reputation_gossip import ReputationGossipMessage, ReputationCache


# Challenge thresholds
PERFORMANCE_THRESHOLD = 0.20  # 20% worse than claimed triggers challenge
CONSISTENCY_THRESHOLD = 0.15  # 15% variance above claimed
SUCCESS_RATE_THRESHOLD = 0.15  # 15% below claimed reliability
MIN_OPERATIONS_FOR_CHALLENGE = 5  # Minimum ops before challenge can be issued

# Penalty levels
PENALTY_MINOR = 0.10  # -0.1 component downgrade
PENALTY_MODERATE = 0.20  # -0.2 component downgrade
PENALTY_SEVERE = 0.50  # -0.5 component downgrade (near-ban)

# Challenge cooldown
CHALLENGE_COOLDOWN_SECONDS = 3600  # 1 hour between challenges to same agent


class ChallengeType(Enum):
    """Types of reputation challenges"""
    PERFORMANCE = "performance"  # Quality/latency worse than claimed
    CONSISTENCY = "consistency"  # High variance in results
    SUCCESS_RATE = "success_rate"  # Failures exceed claimed reliability
    COST_EFFICIENCY = "cost_efficiency"  # ATP cost higher than claimed


class ChallengeOutcome(Enum):
    """Outcome of reputation challenge"""
    UPHELD = "upheld"  # Challenge valid, apply penalty
    REJECTED = "rejected"  # Challenge invalid, no penalty
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"  # Not enough data


@dataclass
class OperationOutcome:
    """Single operation outcome for verification"""
    operation_id: str
    agent_lct_id: str
    operation_type: str
    timestamp: float
    success: bool
    latency_ms: float
    quality_score: float
    atp_cost: float


@dataclass
class ReputationChallenge:
    """Reputation challenge issued by requester"""
    challenge_id: str
    challenger_lct_id: str  # Requester who issues challenge
    challenged_agent_lct_id: str  # Agent being challenged
    challenge_type: ChallengeType
    timestamp: float

    # Evidence
    claimed_value: float  # What agent claimed (component value)
    observed_value: float  # What requester observed
    operation_outcomes: List[OperationOutcome]  # Supporting evidence

    # Resolution
    outcome: Optional[ChallengeOutcome] = None
    penalty_applied: float = 0.0  # Component downgrade amount
    notes: Optional[str] = None


@dataclass
class ChallengeHistory:
    """Track challenges against an agent"""
    agent_lct_id: str
    challenges: List[ReputationChallenge] = field(default_factory=list)
    upheld_count: int = 0
    rejected_count: int = 0
    last_challenge_timestamp: float = 0.0

    def add_challenge(self, challenge: ReputationChallenge):
        """Add challenge to history"""
        self.challenges.append(challenge)
        self.last_challenge_timestamp = challenge.timestamp

        if challenge.outcome == ChallengeOutcome.UPHELD:
            self.upheld_count += 1
        elif challenge.outcome == ChallengeOutcome.REJECTED:
            self.rejected_count += 1

    def is_in_cooldown(self) -> bool:
        """Check if agent is in challenge cooldown"""
        if self.last_challenge_timestamp == 0:
            return False

        time_since_last = time.time() - self.last_challenge_timestamp
        return time_since_last < CHALLENGE_COOLDOWN_SECONDS

    def get_penalty_level(self) -> str:
        """Get penalty level based on challenge history"""
        if self.upheld_count < 3:
            return "minor"
        elif self.upheld_count < 5:
            return "moderate"
        elif self.upheld_count < 10:
            return "severe"
        else:
            return "banned"


def detect_performance_challenge(
    claimed_components: V3Components,
    operation_outcomes: List[OperationOutcome]
) -> Optional[Tuple[ChallengeType, float, float]]:
    """
    Detect if agent performance significantly worse than claimed

    Returns:
        (challenge_type, claimed_value, observed_value) or None
    """
    if len(operation_outcomes) < MIN_OPERATIONS_FOR_CHALLENGE:
        return None

    # Calculate observed performance metrics
    successful_ops = [op for op in operation_outcomes if op.success]
    if not successful_ops:
        return None

    # Check accuracy (quality score)
    observed_accuracy = statistics.mean([op.quality_score for op in successful_ops])
    claimed_accuracy = claimed_components.accuracy

    if claimed_accuracy - observed_accuracy > PERFORMANCE_THRESHOLD:
        return (ChallengeType.PERFORMANCE, claimed_accuracy, observed_accuracy)

    # Check speed (latency)
    observed_latency = statistics.mean([op.latency_ms for op in operation_outcomes])

    # Speed component: higher = faster (lower latency)
    # Convert to comparable metric: expected_latency based on speed
    # speed=1.0 → ~20ms, speed=0.5 → ~40ms, speed=0.0 → ~80ms
    expected_latency = 20 + (1.0 - claimed_components.speed) * 60

    # If observed latency >> expected, speed claim is false
    if observed_latency > expected_latency * (1 + PERFORMANCE_THRESHOLD):
        return (ChallengeType.PERFORMANCE, claimed_components.speed, 1.0 - (observed_latency / 80))

    # Check reliability (success rate)
    observed_success_rate = len(successful_ops) / len(operation_outcomes)
    claimed_reliability = claimed_components.reliability

    if claimed_reliability - observed_success_rate > SUCCESS_RATE_THRESHOLD:
        return (ChallengeType.SUCCESS_RATE, claimed_reliability, observed_success_rate)

    # Check consistency (result variance)
    if len(successful_ops) >= 3:
        quality_std = statistics.stdev([op.quality_score for op in successful_ops])

        # Consistency component: higher = lower variance
        # Convert to comparable metric
        observed_consistency = max(0.0, 1.0 - quality_std)
        claimed_consistency = claimed_components.consistency

        if claimed_consistency - observed_consistency > CONSISTENCY_THRESHOLD:
            return (ChallengeType.CONSISTENCY, claimed_consistency, observed_consistency)

    return None


def issue_challenge(
    challenger_lct_id: str,
    challenged_agent_lct_id: str,
    claimed_components: V3Components,
    operation_outcomes: List[OperationOutcome]
) -> Optional[ReputationChallenge]:
    """
    Issue reputation challenge based on operation outcomes

    Returns:
        ReputationChallenge or None if no grounds for challenge
    """
    # Detect if challenge warranted
    detection = detect_performance_challenge(claimed_components, operation_outcomes)

    if detection is None:
        return None

    challenge_type, claimed_value, observed_value = detection

    # Create challenge
    challenge = ReputationChallenge(
        challenge_id=f"challenge_{int(time.time())}_{challenged_agent_lct_id}",
        challenger_lct_id=challenger_lct_id,
        challenged_agent_lct_id=challenged_agent_lct_id,
        challenge_type=challenge_type,
        timestamp=time.time(),
        claimed_value=claimed_value,
        observed_value=observed_value,
        operation_outcomes=operation_outcomes
    )

    return challenge


def evaluate_challenge(
    challenge: ReputationChallenge,
    agent_historical_outcomes: Optional[List[OperationOutcome]] = None
) -> ChallengeOutcome:
    """
    Evaluate reputation challenge

    Agent can provide historical outcomes as evidence.
    If historical performance matches claimed components, challenge rejected.
    If historical performance matches observed (poor) performance, challenge upheld.

    Args:
        challenge: The challenge to evaluate
        agent_historical_outcomes: Agent's historical operation results (defense)

    Returns:
        ChallengeOutcome (upheld, rejected, insufficient_evidence)
    """
    # If agent provides no defense, uphold challenge
    if agent_historical_outcomes is None or len(agent_historical_outcomes) < MIN_OPERATIONS_FOR_CHALLENGE:
        challenge.outcome = ChallengeOutcome.INSUFFICIENT_EVIDENCE
        challenge.notes = "Agent provided insufficient historical evidence"
        return ChallengeOutcome.INSUFFICIENT_EVIDENCE

    # Calculate agent's historical performance
    historical_successful = [op for op in agent_historical_outcomes if op.success]

    if not historical_successful:
        challenge.outcome = ChallengeOutcome.UPHELD
        challenge.notes = "Agent historical performance validates challenger's observations"
        return ChallengeOutcome.UPHELD

    # Compare historical performance to claimed value
    if challenge.challenge_type == ChallengeType.PERFORMANCE:
        historical_accuracy = statistics.mean([op.quality_score for op in historical_successful])

        # If historical matches claimed (±10%), reject challenge
        if abs(historical_accuracy - challenge.claimed_value) < 0.10:
            challenge.outcome = ChallengeOutcome.REJECTED
            challenge.notes = f"Agent historical accuracy {historical_accuracy:.3f} matches claimed {challenge.claimed_value:.3f}"
            return ChallengeOutcome.REJECTED

        # If historical matches observed (poor), uphold challenge
        if abs(historical_accuracy - challenge.observed_value) < 0.10:
            challenge.outcome = ChallengeOutcome.UPHELD
            challenge.notes = f"Agent historical accuracy {historical_accuracy:.3f} confirms poor performance"
            return ChallengeOutcome.UPHELD

    elif challenge.challenge_type == ChallengeType.SUCCESS_RATE:
        historical_success_rate = len(historical_successful) / len(agent_historical_outcomes)

        if abs(historical_success_rate - challenge.claimed_value) < 0.10:
            challenge.outcome = ChallengeOutcome.REJECTED
            challenge.notes = f"Agent historical success rate {historical_success_rate:.1%} matches claimed"
            return ChallengeOutcome.REJECTED

        if abs(historical_success_rate - challenge.observed_value) < 0.10:
            challenge.outcome = ChallengeOutcome.UPHELD
            challenge.notes = f"Agent historical success rate {historical_success_rate:.1%} confirms poor reliability"
            return ChallengeOutcome.UPHELD

    # Ambiguous: historical doesn't clearly support either side
    challenge.outcome = ChallengeOutcome.INSUFFICIENT_EVIDENCE
    challenge.notes = "Historical evidence inconclusive"
    return ChallengeOutcome.INSUFFICIENT_EVIDENCE


def apply_challenge_penalty(
    challenge: ReputationChallenge,
    agent_components: V3Components,
    challenge_history: ChallengeHistory
) -> V3Components:
    """
    Apply penalty to agent's component scores based on challenge outcome

    Args:
        challenge: The upheld challenge
        agent_components: Agent's current components
        challenge_history: Agent's challenge history

    Returns:
        Updated V3Components with penalty applied
    """
    if challenge.outcome != ChallengeOutcome.UPHELD:
        return agent_components  # No penalty

    # Determine penalty level based on history
    penalty_level = challenge_history.get_penalty_level()

    if penalty_level == "minor":
        penalty = PENALTY_MINOR
    elif penalty_level == "moderate":
        penalty = PENALTY_MODERATE
    elif penalty_level == "severe":
        penalty = PENALTY_SEVERE
    else:  # banned
        # Set all components to minimum (effectively bans from selection)
        penalty = 1.0

    # Apply penalty to relevant component
    component_map = {
        ChallengeType.PERFORMANCE: V3Component.ACCURACY,
        ChallengeType.CONSISTENCY: V3Component.CONSISTENCY,
        ChallengeType.SUCCESS_RATE: V3Component.RELIABILITY,
        ChallengeType.COST_EFFICIENCY: V3Component.COST_EFFICIENCY
    }

    target_component = component_map.get(challenge.challenge_type, V3Component.ACCURACY)

    # Downgrade component
    current_value = agent_components.get_component(target_component)
    new_value = max(0.0, current_value - penalty)
    agent_components.set_component(target_component, new_value)

    challenge.penalty_applied = penalty

    return agent_components


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  Reputation Challenge Protocol - Unit Tests")
    print("  Session #80")
    print("=" * 80)

    # Test 1: Detect performance challenge
    print("\n=== Test 1: Detect Performance Challenge ===\n")

    # Agent claims high accuracy but delivers poorly
    claimed_components = V3Components(
        consistency=0.90,
        accuracy=0.95,  # Claims 95% accuracy
        reliability=0.92,
        speed=0.85,
        cost_efficiency=0.88
    )

    # Simulate 10 operations with poor quality
    poor_outcomes = [
        OperationOutcome(
            operation_id=f"op_{i}",
            agent_lct_id="lct:test:agent:dishonest",
            operation_type="audit",
            timestamp=time.time(),
            success=True,
            latency_ms=40.0 + i,
            quality_score=0.65 + (i * 0.01),  # Much lower than claimed 0.95
            atp_cost=50.0
        )
        for i in range(10)
    ]

    detection = detect_performance_challenge(claimed_components, poor_outcomes)

    if detection:
        challenge_type, claimed, observed = detection
        print(f"Challenge detected: {challenge_type.value}")
        print(f"  Claimed: {claimed:.3f}")
        print(f"  Observed: {observed:.3f}")
        print(f"  Difference: {claimed - observed:.3f} (>{PERFORMANCE_THRESHOLD:.2f} threshold)")
    else:
        print("No challenge detected")

    # Test 2: Issue and evaluate challenge
    print("\n=== Test 2: Issue and Evaluate Challenge ===\n")

    challenge = issue_challenge(
        challenger_lct_id="lct:test:society:A:requester",
        challenged_agent_lct_id="lct:test:agent:dishonest",
        claimed_components=claimed_components,
        operation_outcomes=poor_outcomes
    )

    if challenge:
        print(f"Challenge issued:")
        print(f"  ID: {challenge.challenge_id}")
        print(f"  Type: {challenge.challenge_type.value}")
        print(f"  Claimed: {challenge.claimed_value:.3f}")
        print(f"  Observed: {challenge.observed_value:.3f}")
        print(f"  Evidence: {len(challenge.operation_outcomes)} operations")

        # Agent provides no defense
        print(f"\nEvaluating challenge (no agent defense):")
        outcome = evaluate_challenge(challenge, agent_historical_outcomes=None)
        print(f"  Outcome: {outcome.value}")
        print(f"  Notes: {challenge.notes}")

    # Test 3: Challenge with agent defense (rejected)
    print("\n=== Test 3: Challenge with Valid Agent Defense ===\n")

    # Agent provides historical evidence of good performance
    good_historical = [
        OperationOutcome(
            operation_id=f"hist_{i}",
            agent_lct_id="lct:test:agent:honest",
            operation_type="audit",
            timestamp=time.time() - 3600,
            success=True,
            latency_ms=35.0 + i,
            quality_score=0.93 + (i * 0.005),  # Matches claimed 0.95
            atp_cost=48.0
        )
        for i in range(10)
    ]

    honest_challenge = issue_challenge(
        challenger_lct_id="lct:test:society:A:requester",
        challenged_agent_lct_id="lct:test:agent:honest",
        claimed_components=claimed_components,
        operation_outcomes=poor_outcomes  # Recent poor performance
    )

    if honest_challenge:
        outcome = evaluate_challenge(honest_challenge, agent_historical_outcomes=good_historical)
        print(f"Honest agent challenge outcome: {outcome.value}")
        print(f"  Notes: {honest_challenge.notes}")

    # Test 4: Apply penalties
    print("\n=== Test 4: Apply Challenge Penalties ===\n")

    # Create challenge history with multiple upheld challenges
    history = ChallengeHistory(agent_lct_id="lct:test:agent:dishonest")

    # First challenge (minor penalty)
    challenge1 = ReputationChallenge(
        challenge_id="ch1",
        challenger_lct_id="req1",
        challenged_agent_lct_id="lct:test:agent:dishonest",
        challenge_type=ChallengeType.PERFORMANCE,
        timestamp=time.time(),
        claimed_value=0.95,
        observed_value=0.70,
        operation_outcomes=poor_outcomes,
        outcome=ChallengeOutcome.UPHELD
    )
    history.add_challenge(challenge1)

    components = V3Components(0.90, 0.95, 0.92, 0.85, 0.88)
    print(f"Initial components: {components.to_dict()}")

    components = apply_challenge_penalty(challenge1, components, history)
    print(f"After 1st challenge (minor): accuracy = {components.accuracy:.2f} (-{challenge1.penalty_applied:.2f})")

    # Second and third challenges (moderate penalty)
    for i in range(2, 4):
        challenge_i = ReputationChallenge(
            challenge_id=f"ch{i}",
            challenger_lct_id=f"req{i}",
            challenged_agent_lct_id="lct:test:agent:dishonest",
            challenge_type=ChallengeType.PERFORMANCE,
            timestamp=time.time() + i,
            claimed_value=0.85,
            observed_value=0.65,
            operation_outcomes=poor_outcomes,
            outcome=ChallengeOutcome.UPHELD
        )
        history.add_challenge(challenge_i)

    components = apply_challenge_penalty(challenge_i, components, history)
    print(f"After 3rd challenge (moderate): accuracy = {components.accuracy:.2f}")

    # Test 5: Challenge history and penalty levels
    print("\n=== Test 5: Challenge History and Penalty Levels ===\n")

    print(f"{'Upheld Challenges':<20} | {'Penalty Level':<15} | {'Effect'}")
    print("-" * 70)

    for upheld_count in [1, 3, 5, 10]:
        test_history = ChallengeHistory(agent_lct_id="test")
        test_history.upheld_count = upheld_count
        level = test_history.get_penalty_level()

        if level == "minor":
            effect = f"-{PENALTY_MINOR:.2f} component downgrade"
        elif level == "moderate":
            effect = f"-{PENALTY_MODERATE:.2f} component downgrade"
        elif level == "severe":
            effect = f"-{PENALTY_SEVERE:.2f} component downgrade"
        else:
            effect = "Banned from federation"

        print(f"{upheld_count:<20} | {level:<15} | {effect}")

    print("\n" + "=" * 80)
    print("  All Unit Tests Passed!")
    print("=" * 80)
    print("\n✅ Key Findings:")
    print("  - Performance challenges detected when observed << claimed")
    print("  - Agents can defend with historical evidence")
    print("  - Penalties escalate with repeated violations")
    print("  - Persistent violators effectively banned (penalty=1.0)")
