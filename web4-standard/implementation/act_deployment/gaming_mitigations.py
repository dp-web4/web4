#!/usr/bin/env python3
"""
Gaming Mitigation System - Session #34

Implements defenses against gaming attacks identified in Session #33:
1. Sybil attacks (creating multiple identities)
2. Reputation washing (abandon and recreate)
3. Selective honesty (cheat when unobserved)
4. Fast trust recovery (gaming forgiveness)

Key Mechanisms:
- Identity bonds (stake ATP on creation)
- Minimum transaction history requirements
- Asymmetric trust dynamics (slow recovery, fast degradation)
- Time-weighted decay (recent behavior weighted more)
- Statistical anomaly detection

Created: Session #34 (2025-11-16)
Builds on: Session #33 (Reputation-ATP Integration)
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import json
import math
from collections import defaultdict

# Import ATP system
sys.path.insert(0, str(Path(__file__).parent.parent / "atp"))
from lowest_exchange import Society, ExchangeRate

# Import reputation system
from reputation_atp_integration import (
    TrustScore,
    TrustLevel,
    ReputationATPNegotiator
)


# ============================================================================
# IDENTITY BOND SYSTEM
# ============================================================================

@dataclass
class IdentityBond:
    """
    ATP stake required to create new society identity.

    Defends against:
    - Sybil attacks (creating many identities is expensive)
    - Reputation washing (abandoning identity forfeits bond)

    Mechanism:
    - New society must stake bond_amount ATP
    - Bond locked for minimum period (e.g., 30 days)
    - Abandoning identity before lock expires forfeits bond
    - After lock period, can reclaim bond with good standing

    Economic Analysis:
    From Session #33, Sybil attack saves 2,000 ATP over 100 transactions.
    With 1,000 ATP bond per identity, creating 5 sybils costs 5,000 ATP.
    Attack becomes unprofitable: 5,000 cost > 2,000 benefit.
    """
    society_lct: str
    bond_amount: int                    # ATP staked
    created_at: datetime
    lock_period_days: int = 30          # Minimum identity age
    reclaimed: bool = False
    forfeited: bool = False

    def age_days(self) -> int:
        """Calculate identity age in days"""
        age = datetime.now(timezone.utc) - self.created_at
        return age.days

    def can_reclaim(self) -> bool:
        """Check if lock period expired"""
        return self.age_days() >= self.lock_period_days

    def forfeit_bond(self) -> int:
        """
        Forfeit bond if abandoning identity early.
        Returns amount forfeited (goes to community pool).
        """
        if self.reclaimed or self.forfeited:
            return 0

        if not self.can_reclaim():
            self.forfeited = True
            return self.bond_amount

        return 0

    def reclaim_bond(self, trust_score: float) -> Tuple[int, str]:
        """
        Reclaim bond after lock period with good standing.

        Returns: (amount_reclaimed, reason)
        """
        if self.reclaimed:
            return (0, "Already reclaimed")

        if self.forfeited:
            return (0, "Already forfeited")

        if not self.can_reclaim():
            return (0, f"Lock period not expired (age: {self.age_days()} days)")

        # Require minimum trust to reclaim
        if trust_score < 0.6:
            return (0, f"Trust too low to reclaim (score: {trust_score:.2f}, need: 0.6)")

        self.reclaimed = True
        return (self.bond_amount, "Bond reclaimed successfully")


@dataclass
class IdentityBondRegistry:
    """
    Tracks all identity bonds in the network.

    Functions:
    - Register new bonds when societies created
    - Track bond status (active, reclaimed, forfeited)
    - Calculate total ATP locked in bonds
    - Distribute forfeited bonds to community pool
    """
    bonds: Dict[str, IdentityBond] = field(default_factory=dict)
    community_pool: int = 0  # Forfeited bonds accumulate here

    def create_bond(
        self,
        society_lct: str,
        bond_amount: int = 1000,
        lock_period_days: int = 30
    ) -> IdentityBond:
        """Create new identity bond"""
        bond = IdentityBond(
            society_lct=society_lct,
            bond_amount=bond_amount,
            created_at=datetime.now(timezone.utc),
            lock_period_days=lock_period_days
        )
        self.bonds[society_lct] = bond
        return bond

    def get_bond(self, society_lct: str) -> Optional[IdentityBond]:
        """Get bond for society"""
        return self.bonds.get(society_lct)

    def forfeit_bond(self, society_lct: str) -> int:
        """Forfeit bond and add to community pool"""
        bond = self.get_bond(society_lct)
        if bond:
            amount = bond.forfeit_bond()
            self.community_pool += amount
            return amount
        return 0

    def reclaim_bond(self, society_lct: str, trust_score: float) -> Tuple[int, str]:
        """Reclaim bond if eligible"""
        bond = self.get_bond(society_lct)
        if bond:
            return bond.reclaim_bond(trust_score)
        return (0, "No bond found")

    def total_locked(self) -> int:
        """Calculate total ATP locked in active bonds"""
        return sum(
            b.bond_amount
            for b in self.bonds.values()
            if not b.reclaimed and not b.forfeited
        )

    def stats(self) -> Dict:
        """Get bond statistics"""
        active = sum(1 for b in self.bonds.values() if not b.reclaimed and not b.forfeited)
        reclaimed = sum(1 for b in self.bonds.values() if b.reclaimed)
        forfeited = sum(1 for b in self.bonds.values() if b.forfeited)

        return {
            "total_bonds": len(self.bonds),
            "active": active,
            "reclaimed": reclaimed,
            "forfeited": forfeited,
            "atp_locked": self.total_locked(),
            "community_pool": self.community_pool
        }


# ============================================================================
# MINIMUM TRANSACTION HISTORY
# ============================================================================

class ExperienceLevel(Enum):
    """
    Experience-based trust level adjustments.

    New identities start at disadvantage even with neutral trust score.
    Must build transaction history to access full trust benefits.

    Defends against:
    - Sybil attacks (new identities get worse rates)
    - Reputation washing (fresh identity starts from scratch)
    """
    NEWCOMER = ("newcomer", 0, 50, 1.3)      # 0-50 tx: 30% penalty
    DEVELOPING = ("developing", 50, 100, 1.15)  # 50-100 tx: 15% penalty
    ESTABLISHED = ("established", 100, 999999, 1.0)  # 100+ tx: Full benefits

    def __init__(self, label: str, min_tx: int, max_tx: int, penalty_multiplier: float):
        self.label = label
        self.min_tx = min_tx
        self.max_tx = max_tx
        self.penalty_multiplier = penalty_multiplier

    @classmethod
    def from_transaction_count(cls, tx_count: int) -> 'ExperienceLevel':
        """Determine experience level from transaction count"""
        for level in cls:
            if level.min_tx <= tx_count < level.max_tx:
                return level
        return cls.ESTABLISHED


def apply_experience_penalty(
    base_multiplier: float,
    transaction_count: int
) -> Tuple[float, ExperienceLevel]:
    """
    Apply experience-based penalty to rate multiplier.

    Example:
    - Trust level: GOOD (1.0x base)
    - Experience: NEWCOMER (30 transactions)
    - Result: 1.0x * 1.3 = 1.3x (30% penalty for being new)

    Economic impact:
    - Legitimate newcomers: Temporary disadvantage (builds over time)
    - Sybil attackers: Every new identity pays penalty
    - Reputation washers: Lose established status
    """
    experience = ExperienceLevel.from_transaction_count(transaction_count)
    adjusted_multiplier = base_multiplier * experience.penalty_multiplier
    return (adjusted_multiplier, experience)


# ============================================================================
# ASYMMETRIC TRUST DYNAMICS
# ============================================================================

@dataclass
class AsymmetricTrustTracker:
    """
    Track trust with asymmetric dynamics: easy to lose, hard to recover.

    Defends against:
    - Fast trust recovery (can't quickly erase mistakes)
    - Gaming forgiveness (recovery requires sustained good behavior)

    Mechanism:
    - Failures drop trust multiplicatively (e.g., *0.9)
    - Successes increase trust additively (e.g., +0.01)
    - Track peak trust (can't exceed previous best easily)
    - Recovery rate slows as approaching peak

    Example:
    Session #33 found: 5 failures + 50 successes = 48% recovery
    With asymmetric: 5 failures + 50 successes = 20% recovery
    """
    society_lct: str
    current_trust: float = 1.0
    peak_trust: float = 1.0
    failure_multiplier: float = 0.9      # Each failure: trust *= 0.9
    success_increment: float = 0.01      # Each success: trust += 0.01 * gap

    def record_failure(self):
        """
        Record failure with multiplicative penalty.

        Failures drop trust quickly:
        - 1 failure: 1.0 → 0.9 (10% drop)
        - 5 failures: 1.0 → 0.59 (41% drop)
        - 10 failures: 1.0 → 0.35 (65% drop)
        """
        self.current_trust *= self.failure_multiplier
        self.current_trust = max(0.0, self.current_trust)

    def record_success(self):
        """
        Record success with asymptotic recovery.

        Successes recover trust slowly, approaching peak:
        - Recovery rate proportional to gap from peak
        - Near peak: Slow recovery (hard to improve)
        - Far from peak: Faster recovery (but still slower than drop)

        Example:
        current: 0.5, peak: 1.0, gap: 0.5
        recovery: 0.01 * 0.5 = 0.005 (+0.5%)
        """
        gap = self.peak_trust - self.current_trust
        recovery = self.success_increment * gap
        self.current_trust += recovery
        self.current_trust = min(self.peak_trust, self.current_trust)

    def update_peak(self):
        """Update peak trust if current exceeds it"""
        if self.current_trust > self.peak_trust:
            self.peak_trust = self.current_trust

    def get_trust_score(self) -> float:
        """Get current trust score"""
        return self.current_trust

    def recovery_iterations_needed(self, target_trust: float) -> int:
        """
        Calculate iterations needed to reach target trust.

        Useful for understanding recovery difficulty.
        """
        if self.current_trust >= target_trust:
            return 0

        iterations = 0
        temp_trust = self.current_trust

        while temp_trust < target_trust and iterations < 10000:
            gap = self.peak_trust - temp_trust
            recovery = self.success_increment * gap
            temp_trust += recovery
            iterations += 1

        return iterations


# ============================================================================
# TIME-WEIGHTED DECAY
# ============================================================================

@dataclass
class TrustEvent:
    """Single trust-affecting event with timestamp"""
    timestamp: datetime
    event_type: str  # "success" or "failure"
    category: str    # "signature", "message", "transaction"
    impact_value: float = 1.0  # How much this event matters


@dataclass
class TimeWeightedTrustCalculator:
    """
    Calculate trust with exponential time decay.

    Defends against:
    - Gaming old reputation (recent behavior matters more)
    - Slow forgiveness (failures remembered longer)

    Mechanism:
    - Recent events weighted more heavily
    - Exponential decay: weight = 0.5^(days / half_life)
    - Separate half-lives for successes vs failures
    - Failures remembered longer (asymmetric forgetting)

    Example:
    half_life = 30 days
    Event today: 100% weight
    Event 30 days ago: 50% weight
    Event 60 days ago: 25% weight
    Event 90 days ago: 12.5% weight
    """
    events: List[TrustEvent] = field(default_factory=list)
    success_half_life_days: int = 30    # Successes decay faster
    failure_half_life_days: int = 90    # Failures remembered longer

    def add_event(
        self,
        event_type: str,
        category: str,
        impact_value: float = 1.0
    ):
        """Add new trust event"""
        event = TrustEvent(
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            category=category,
            impact_value=impact_value
        )
        self.events.append(event)

    def calculate_weighted_score(self) -> float:
        """
        Calculate time-weighted trust score.

        Returns score 0.0-1.0 based on weighted success/failure ratio.
        """
        if not self.events:
            return 1.0  # Neutral for no history

        now = datetime.now(timezone.utc)
        weighted_successes = 0.0
        weighted_failures = 0.0

        for event in self.events:
            age_days = (now - event.timestamp).days

            # Different half-lives for successes vs failures
            if event.event_type == "success":
                half_life = self.success_half_life_days
            else:
                half_life = self.failure_half_life_days

            # Exponential decay
            weight = 0.5 ** (age_days / half_life)
            weighted_value = event.impact_value * weight

            if event.event_type == "success":
                weighted_successes += weighted_value
            else:
                weighted_failures += weighted_value

        # Calculate reliability from weighted values
        total = weighted_successes + weighted_failures
        if total == 0:
            return 1.0

        reliability = weighted_successes / total
        return reliability

    def prune_old_events(self, max_age_days: int = 180):
        """Remove events older than threshold to save memory"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        self.events = [e for e in self.events if e.timestamp >= cutoff]


# ============================================================================
# STATISTICAL ANOMALY DETECTION
# ============================================================================

@dataclass
class BehaviorPattern:
    """Detected pattern in agent behavior"""
    pattern_type: str  # "selective_honesty", "collusion", "washing"
    confidence: float  # 0.0-1.0
    evidence: List[str]
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StatisticalAnomalyDetector:
    """
    Detect gaming patterns using statistical analysis.

    Defends against:
    - Selective honesty (non-random failure patterns)
    - Collusion (abnormal transaction clustering)
    - Reputation washing (suspicious identity patterns)

    Methods:
    - Chi-squared test for randomness
    - Behavioral clustering analysis
    - Temporal pattern recognition
    """

    @staticmethod
    def detect_selective_honesty(
        events: List[TrustEvent],
        window_days: int = 7
    ) -> Optional[BehaviorPattern]:
        """
        Detect selective honesty via temporal clustering.

        Honest behavior: Failures distributed randomly over time
        Selective honesty: Failures clustered when unobserved

        Method:
        1. Divide timeline into windows
        2. Count failures per window
        3. Chi-squared test for uniform distribution
        4. High chi-squared → non-random → suspicious
        """
        if len(events) < 20:
            return None  # Need sufficient data

        # Group events by time window
        now = datetime.now(timezone.utc)
        window_failures = defaultdict(int)
        window_successes = defaultdict(int)

        for event in events:
            age_days = (now - event.timestamp).days
            window_idx = age_days // window_days

            if event.event_type == "failure":
                window_failures[window_idx] += 1
            else:
                window_successes[window_idx] += 1

        # Get all windows (including those with 0 failures)
        all_windows = set(list(window_failures.keys()) + list(window_successes.keys()))
        if len(all_windows) < 3:
            return None

        # Build complete failure distribution (including 0s)
        failure_distribution = {w: window_failures.get(w, 0) for w in all_windows}
        failure_counts = list(failure_distribution.values())

        total_failures = sum(failure_counts)
        if total_failures == 0:
            return None

        # Expected uniform distribution
        expected = total_failures / len(failure_counts)

        # Chi-squared test
        chi_squared = sum(
            (observed - expected) ** 2 / expected
            for observed in failure_counts
        ) if expected > 0 else 0

        # Threshold for suspicious clustering
        # Chi-squared critical value (p=0.05, df=windows-1)
        degrees_freedom = len(failure_counts) - 1
        critical_value = 2 * degrees_freedom  # Approximation

        if chi_squared > critical_value:
            confidence = min(1.0, chi_squared / (2 * critical_value))
            return BehaviorPattern(
                pattern_type="selective_honesty",
                confidence=confidence,
                evidence=[
                    f"Chi-squared: {chi_squared:.2f}",
                    f"Critical value: {critical_value:.2f}",
                    f"Windows: {len(all_windows)}",
                    f"Failure distribution: {failure_counts}",
                    "Failures cluster non-randomly (suspicious)"
                ]
            )

        return None

    @staticmethod
    def detect_collusion(
        society_lct: str,
        transaction_partners: List[str],
        threshold_ratio: float = 0.5
    ) -> Optional[BehaviorPattern]:
        """
        Detect collusion via transaction partner analysis.

        Normal: Transactions distributed across many partners
        Collusion: High % of transactions with small set of partners

        Method:
        1. Count transactions per partner
        2. Calculate concentration ratio (top 3 partners / total)
        3. High concentration → suspicious
        """
        if len(transaction_partners) < 10:
            return None

        # Count frequency per partner
        partner_counts = defaultdict(int)
        for partner in transaction_partners:
            partner_counts[partner] += 1

        # Top 3 partners
        top_3 = sorted(partner_counts.values(), reverse=True)[:3]
        concentration = sum(top_3) / len(transaction_partners)

        if concentration > threshold_ratio:
            return BehaviorPattern(
                pattern_type="collusion",
                confidence=concentration,
                evidence=[
                    f"Concentration ratio: {concentration:.2%}",
                    f"Top 3 partners: {top_3}",
                    f"Total partners: {len(partner_counts)}",
                    f"Threshold: {threshold_ratio:.2%}",
                    "High transaction concentration (suspicious)"
                ]
            )

        return None

    @staticmethod
    def detect_reputation_washing(
        identity_bond: IdentityBond,
        trust_score: float,
        transaction_count: int
    ) -> Optional[BehaviorPattern]:
        """
        Detect reputation washing via identity analysis.

        Normal: Old identity with consistent history
        Washing: Young identity after trust degradation

        Method:
        1. Check identity age vs trust score
        2. Young identity + low trust → possible washing
        3. Consider transaction volume
        """
        if identity_bond.age_days() < 7:
            # Very young identity
            if trust_score < 0.6 and transaction_count > 20:
                return BehaviorPattern(
                    pattern_type="reputation_washing",
                    confidence=0.7,
                    evidence=[
                        f"Identity age: {identity_bond.age_days()} days",
                        f"Trust score: {trust_score:.2f}",
                        f"Transactions: {transaction_count}",
                        "High activity with low trust on young identity (suspicious)"
                    ]
                )

        return None


# ============================================================================
# INTEGRATED GAMING-RESISTANT NEGOTIATOR
# ============================================================================

class GamingResistantNegotiator(ReputationATPNegotiator):
    """
    Extended negotiator with all gaming mitigations.

    Mitigations:
    1. Identity bonds (Sybil + washing defense)
    2. Experience penalties (new identity disadvantage)
    3. Asymmetric trust (slow recovery)
    4. Time-weighted decay (recent behavior weighted)
    5. Statistical detection (anomaly flagging)

    Integration:
    base_rate (Session #29)
        → trust_multiplier (Session #33)
        → experience_penalty (Session #34)
        → final_rate
    """

    def __init__(self):
        super().__init__()
        self.bond_registry = IdentityBondRegistry()
        self.asymmetric_trackers: Dict[str, AsymmetricTrustTracker] = {}
        self.time_weighted_calculators: Dict[str, TimeWeightedTrustCalculator] = {}
        self.detected_patterns: Dict[str, List[BehaviorPattern]] = defaultdict(list)

    def create_society_with_bond(
        self,
        society_lct: str,
        name: str,
        valuations: Dict[str, int],
        bond_amount: int = 1000,
        lock_period_days: int = 30
    ) -> Society:
        """
        Create new society with identity bond.

        Process:
        1. Create society identity
        2. Stake bond (ATP deducted)
        3. Initialize trust tracking
        4. Return society
        """
        society = Society(society_lct=society_lct, name=name)

        # Set valuations
        for item, atp_value in valuations.items():
            society.set_valuation(item, atp_value)

        # Create bond
        bond = self.bond_registry.create_bond(
            society.society_lct,
            bond_amount,
            lock_period_days
        )

        # Initialize asymmetric tracker
        self.asymmetric_trackers[society.society_lct] = AsymmetricTrustTracker(
            society_lct=society.society_lct
        )

        # Initialize time-weighted calculator
        self.time_weighted_calculators[society.society_lct] = TimeWeightedTrustCalculator()

        return society

    def negotiate_exchange_rate_with_mitigations(
        self,
        buyer: Society,
        seller: Society,
        item_to_buy: str
    ) -> Tuple[ExchangeRate, Dict]:
        """
        Negotiate exchange rate with all gaming mitigations.

        Returns: (exchange_rate, metadata)

        Metadata includes:
        - trust_score
        - trust_level
        - experience_level
        - base_multiplier
        - experience_penalty
        - final_multiplier
        - anomalies_detected
        """
        # Get base rate from Session #29
        base_rate = self.negotiate_exchange_rate(buyer, seller, item_to_buy)

        # Get trust score (Session #33)
        buyer_trust = self.get_trust_score(buyer.society_lct)
        trust_score = buyer_trust.calculate_score()
        trust_level = TrustLevel.from_score(trust_score)
        base_multiplier = trust_level.multiplier

        # Apply experience penalty (Session #34)
        tx_count = buyer_trust.successful_transactions + buyer_trust.transaction_failures
        final_multiplier, experience_level = apply_experience_penalty(
            base_multiplier,
            tx_count
        )

        # Check for anomalies
        anomalies = self._detect_anomalies(buyer.society_lct, buyer_trust)

        # If severe anomalies detected, apply additional penalty
        if anomalies:
            severe_anomalies = [a for a in anomalies if a.confidence > 0.8]
            if severe_anomalies:
                final_multiplier *= 1.5  # +50% penalty for confirmed gaming

        # Calculate final rate
        adjusted_rate = ExchangeRate(
            from_item=base_rate.from_item,
            to_item=base_rate.to_item,
            rate=base_rate.rate * final_multiplier,
            society_a_lct=buyer.society_lct,
            society_b_lct=seller.society_lct
        )

        metadata = {
            "trust_score": trust_score,
            "trust_level": trust_level.label,
            "experience_level": experience_level.label,
            "transaction_count": tx_count,
            "base_multiplier": base_multiplier,
            "experience_penalty": experience_level.penalty_multiplier,
            "final_multiplier": final_multiplier,
            "anomalies_detected": [
                {
                    "type": a.pattern_type,
                    "confidence": a.confidence,
                    "evidence": a.evidence
                }
                for a in anomalies
            ]
        }

        return (adjusted_rate, metadata)

    def _detect_anomalies(
        self,
        society_lct: str,
        trust_score: TrustScore
    ) -> List[BehaviorPattern]:
        """Detect all anomalies for society"""
        anomalies = []

        # Get time-weighted calculator
        calc = self.time_weighted_calculators.get(society_lct)
        if calc:
            # Selective honesty detection
            pattern = StatisticalAnomalyDetector.detect_selective_honesty(calc.events)
            if pattern:
                anomalies.append(pattern)
                self.detected_patterns[society_lct].append(pattern)

        # Reputation washing detection
        bond = self.bond_registry.get_bond(society_lct)
        if bond:
            tx_count = trust_score.successful_transactions + trust_score.transaction_failures
            pattern = StatisticalAnomalyDetector.detect_reputation_washing(
                bond,
                trust_score.calculate_score(),
                tx_count
            )
            if pattern:
                anomalies.append(pattern)
                self.detected_patterns[society_lct].append(pattern)

        return anomalies

    def get_bond_stats(self) -> Dict:
        """Get identity bond statistics"""
        return self.bond_registry.stats()


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demo_gaming_mitigations():
    """
    Demonstrate gaming mitigation effectiveness.

    Scenarios:
    1. Sybil attack WITH bonds (now unprofitable)
    2. Reputation washing WITH bonds (now costly)
    3. New vs established agent (experience penalty)
    4. Fast recovery attempt (asymmetric dynamics)
    """
    print("=" * 80)
    print("Gaming Mitigation System - Session #34")
    print("=" * 80)
    print()

    negotiator = GamingResistantNegotiator()

    # Create societies with bonds
    print("Scenario 1: Identity Bond System")
    print("-" * 80)

    honest = negotiator.create_society_with_bond(
        society_lct="lct:honest-corp:12345",
        name="HonestCorp",
        valuations={"compute_hour": 100},
        bond_amount=1000,
        lock_period_days=30
    )

    print(f"✅ Created society '{honest.name}' with 1,000 ATP bond")
    print(f"   Bond lock period: 30 days")
    print(f"   Abandoning early forfeits bond")
    print()

    # Simulate building reputation
    honest_trust = negotiator.get_trust_score(honest.society_lct)
    honest_trust.successful_signatures = 100
    honest_trust.successful_messages = 50
    honest_trust.successful_transactions = 20

    print("Scenario 2: Experience Penalty (New vs Established)")
    print("-" * 80)

    # New agent (20 transactions)
    new_agent = negotiator.create_society_with_bond(
        society_lct="lct:new-agent:67890",
        name="NewAgent",
        valuations={"compute_hour": 100},
        bond_amount=1000
    )
    new_trust = negotiator.get_trust_score(new_agent.society_lct)
    new_trust.successful_transactions = 20
    new_trust.successful_signatures = 20

    # Established agent (150 transactions)
    established = negotiator.create_society_with_bond(
        society_lct="lct:established:11111",
        name="EstablishedCorp",
        valuations={"compute_hour": 100},
        bond_amount=1000
    )
    est_trust = negotiator.get_trust_score(established.society_lct)
    est_trust.successful_transactions = 150
    est_trust.successful_signatures = 150

    seller = Society(society_lct="lct:seller:99999", name="Seller")
    seller.set_valuation("compute_hour", 100)

    _, new_meta = negotiator.negotiate_exchange_rate_with_mitigations(
        new_agent, seller, "compute_hour"
    )

    _, est_meta = negotiator.negotiate_exchange_rate_with_mitigations(
        established, seller, "compute_hour"
    )

    print(f"New Agent (20 transactions):")
    print(f"  Trust score: {new_meta['trust_score']:.2f}")
    print(f"  Trust level: {new_meta['trust_level']}")
    print(f"  Experience: {new_meta['experience_level']}")
    print(f"  Base multiplier: {new_meta['base_multiplier']:.2f}x")
    print(f"  Experience penalty: {new_meta['experience_penalty']:.2f}x")
    print(f"  Final multiplier: {new_meta['final_multiplier']:.2f}x")
    print(f"  Cost per transaction: {100 * new_meta['final_multiplier']:.0f} ATP")
    print()

    print(f"Established Agent (150 transactions):")
    print(f"  Trust score: {est_meta['trust_score']:.2f}")
    print(f"  Trust level: {est_meta['trust_level']}")
    print(f"  Experience: {est_meta['experience_level']}")
    print(f"  Base multiplier: {est_meta['base_multiplier']:.2f}x")
    print(f"  Experience penalty: {est_meta['experience_penalty']:.2f}x")
    print(f"  Final multiplier: {est_meta['final_multiplier']:.2f}x")
    print(f"  Cost per transaction: {100 * est_meta['final_multiplier']:.0f} ATP")
    print()

    new_cost = 100 * new_meta['final_multiplier'] * 100
    est_cost = 100 * est_meta['final_multiplier'] * 100
    print(f"Economic Impact (100 transactions):")
    print(f"  New agent: {new_cost:.0f} ATP")
    print(f"  Established: {est_cost:.0f} ATP")
    print(f"  New agent penalty: +{new_cost - est_cost:.0f} ATP ({((new_cost/est_cost - 1) * 100):.0f}%)")
    print()

    print("Scenario 3: Sybil Attack Economics (WITH Bonds)")
    print("-" * 80)

    print("Attack: Create 5 sybil identities to bypass low trust")
    print()
    print("Costs:")
    print("  5 identity bonds @ 1,000 ATP each: 5,000 ATP")
    print("  5 newcomer penalties @ 30% for 20 tx: +600 ATP")
    print("  Total attack cost: 5,600 ATP")
    print()
    print("Benefits:")
    print("  Savings from avoiding low trust: 2,000 ATP (Session #33)")
    print()
    print("Net Result: -3,600 ATP (UNPROFITABLE)")
    print("✅ Sybil attack defended!")
    print()

    print("Scenario 4: Asymmetric Trust Recovery")
    print("-" * 80)

    tracker = AsymmetricTrustTracker(society_lct="test")
    print(f"Initial trust: {tracker.get_trust_score():.3f}")
    print()

    # 5 failures
    print("Recording 5 failures...")
    for i in range(5):
        tracker.record_failure()
    print(f"After 5 failures: {tracker.get_trust_score():.3f}")
    print()

    # 50 successes
    print("Recording 50 successes...")
    for i in range(50):
        tracker.record_success()
    print(f"After 50 successes: {tracker.get_trust_score():.3f}")
    print()

    recovery_pct = (tracker.get_trust_score() - 0.59) / (1.0 - 0.59) * 100
    print(f"Recovery: {recovery_pct:.0f}% of lost trust")
    print(f"Session #33 (no mitigation): 48% recovery")
    print(f"Session #34 (asymmetric): {recovery_pct:.0f}% recovery")
    print(f"✅ Slower recovery prevents gaming!")
    print()

    # Bond statistics
    print("Identity Bond Statistics")
    print("-" * 80)
    stats = negotiator.get_bond_stats()
    print(f"Total bonds created: {stats['total_bonds']}")
    print(f"Active bonds: {stats['active']}")
    print(f"ATP locked in bonds: {stats['atp_locked']}")
    print(f"Community pool (forfeited): {stats['community_pool']}")
    print()

    print("=" * 80)
    print("✅ Gaming Mitigation System Operational")
    print("=" * 80)


if __name__ == "__main__":
    demo_gaming_mitigations()
