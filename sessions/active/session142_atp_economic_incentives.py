#!/usr/bin/env python3
"""
Session 142: ATP Economic Incentives for Federated Consciousness

Integrates ATP (Attention Token Protocol) economic incentives with the
security/reputation system from Sessions 137-141.

Economic Layer:
- Quality thoughts earn ATP rewards
- Violations cost ATP penalties
- ATP balance affects privileges (rate limits, corpus priority)
- Creates self-sustaining economic + security ecosystem

This completes the "Economics + Security" stack:
- Sessions 137-141: Security (rate limiting, reputation, PoW, corpus, decay)
- Session 142: Economics (ATP rewards/penalties, resource allocation)

Design Philosophy:
- Align economic incentives with security goals
- Quality contributions earn resources
- Bad behavior costs resources
- Economic feedback reinforces security feedback
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, str(Path.home() / "ai-workspace/web4"))

from session137_security_hardening import (
    ReputationSystem,
    RateLimiter,
    RateLimit,
    QualityValidator
)


class ATPTransactionType(Enum):
    """Types of ATP transactions in federated consciousness."""
    THOUGHT_REWARD = "thought_reward"  # Reward for quality thought
    VIOLATION_PENALTY = "violation_penalty"  # Penalty for bad behavior
    DAILY_RECHARGE = "daily_recharge"  # System regeneration
    TRANSFER = "transfer"  # Peer-to-peer transfer
    CORPUS_PRIORITY = "corpus_priority"  # Pay to prioritize in corpus


@dataclass
class ATPConfig:
    """Configuration for ATP economic system."""
    # Rewards
    base_thought_reward: float = 1.0  # Base ATP for accepted thought
    quality_multiplier: float = 2.0  # Multiplier for high-quality (coherence > 0.8)

    # Penalties
    violation_penalty: float = 5.0  # ATP cost for violations (5× rewards)
    spam_penalty: float = 10.0  # ATP cost for spam attempts

    # Balances
    initial_balance: float = 100.0  # Starting ATP balance
    min_balance: float = 0.0  # Can go to zero
    max_balance: float = 10000.0  # Cap to prevent hoarding

    # Daily recharge
    daily_recharge_rate: float = 10.0  # ATP regenerated per day
    recharge_interval_seconds: float = 86400  # 24 hours

    # Rate limit bonuses
    atp_rate_bonus: bool = True  # ATP balance affects rate limits
    atp_bonus_threshold: float = 500.0  # ATP needed for bonus
    atp_bonus_multiplier: float = 0.2  # 20% rate limit increase per 500 ATP


@dataclass
class ATPTransaction:
    """Record of an ATP transaction."""
    transaction_type: ATPTransactionType
    node_id: str
    lct_id: str
    amount: float  # Positive = credit, negative = debit
    balance_after: float
    timestamp: float
    reason: str


class ATPEconomicSystem:
    """
    ATP-based economic system for federated consciousness.

    Features:
    - Rewards for quality contributions
    - Penalties for violations
    - Economic feedback with security system
    - Daily regeneration
    - Balance-based privileges
    """

    def __init__(self, config: ATPConfig = None):
        self.config = config or ATPConfig()
        self.balances: Dict[str, float] = {}  # lct_id -> ATP balance
        self.transactions: list[ATPTransaction] = []
        self.last_recharge: Dict[str, float] = {}  # lct_id -> timestamp

    def get_balance(self, lct_id: str) -> float:
        """Get current ATP balance for an LCT."""
        if lct_id not in self.balances:
            self.balances[lct_id] = self.config.initial_balance
            self.last_recharge[lct_id] = time.time()

        return self.balances[lct_id]

    def _record_transaction(
        self,
        transaction_type: ATPTransactionType,
        node_id: str,
        lct_id: str,
        amount: float,
        reason: str
    ):
        """Record an ATP transaction."""
        current_balance = self.get_balance(lct_id)
        new_balance = max(
            self.config.min_balance,
            min(self.config.max_balance, current_balance + amount)
        )

        self.balances[lct_id] = new_balance

        transaction = ATPTransaction(
            transaction_type=transaction_type,
            node_id=node_id,
            lct_id=lct_id,
            amount=amount,
            balance_after=new_balance,
            timestamp=time.time(),
            reason=reason
        )

        self.transactions.append(transaction)

        return new_balance

    def reward_thought(
        self,
        node_id: str,
        lct_id: str,
        coherence_score: float
    ) -> Tuple[float, str]:
        """
        Reward a quality thought contribution.

        Returns (ATP_earned, reason)
        """
        # Calculate reward based on quality
        reward = self.config.base_thought_reward

        if coherence_score >= 0.8:
            reward *= self.config.quality_multiplier
            reason = f"High-quality thought (coherence {coherence_score:.2f})"
        else:
            reason = f"Quality thought (coherence {coherence_score:.2f})"

        new_balance = self._record_transaction(
            ATPTransactionType.THOUGHT_REWARD,
            node_id,
            lct_id,
            reward,
            reason
        )

        return reward, reason

    def penalize_violation(
        self,
        node_id: str,
        lct_id: str,
        violation_type: str
    ) -> Tuple[float, str]:
        """
        Penalize a violation.

        Returns (ATP_cost, reason)
        """
        if "spam" in violation_type.lower():
            penalty = self.config.spam_penalty
        else:
            penalty = self.config.violation_penalty

        reason = f"Penalty for {violation_type}"

        new_balance = self._record_transaction(
            ATPTransactionType.VIOLATION_PENALTY,
            node_id,
            lct_id,
            -penalty,  # Negative = debit
            reason
        )

        return penalty, reason

    def apply_daily_recharge(self, lct_id: str) -> Tuple[float, bool]:
        """
        Apply daily ATP recharge if eligible.

        Returns (recharge_amount, was_recharged)
        """
        current_time = time.time()
        last_recharge = self.last_recharge.get(lct_id, 0)

        time_since_recharge = current_time - last_recharge

        if time_since_recharge < self.config.recharge_interval_seconds:
            return 0.0, False

        # Calculate recharge (could be multiple days)
        days_elapsed = time_since_recharge / self.config.recharge_interval_seconds
        recharge_amount = self.config.daily_recharge_rate * days_elapsed

        new_balance = self._record_transaction(
            ATPTransactionType.DAILY_RECHARGE,
            "system",
            lct_id,
            recharge_amount,
            f"Daily recharge ({days_elapsed:.1f} days)"
        )

        self.last_recharge[lct_id] = current_time

        return recharge_amount, True

    def get_rate_limit_bonus(self, lct_id: str) -> float:
        """
        Calculate rate limit bonus based on ATP balance.

        Higher ATP = higher rate limits (economic privilege)
        """
        if not self.config.atp_rate_bonus:
            return 0.0

        balance = self.get_balance(lct_id)

        if balance < self.config.atp_bonus_threshold:
            return 0.0

        # Linear bonus: 20% per 500 ATP threshold
        bonus_tiers = int(balance / self.config.atp_bonus_threshold)
        bonus = bonus_tiers * self.config.atp_bonus_multiplier

        return min(bonus, 1.0)  # Cap at 100% bonus

    def get_stats(self, lct_id: str) -> Dict[str, Any]:
        """Get ATP statistics for an LCT."""
        balance = self.get_balance(lct_id)
        rate_bonus = self.get_rate_limit_bonus(lct_id)

        # Calculate transaction stats
        lct_transactions = [t for t in self.transactions if t.lct_id == lct_id]

        total_earned = sum(t.amount for t in lct_transactions if t.amount > 0)
        total_spent = sum(abs(t.amount) for t in lct_transactions if t.amount < 0)

        return {
            "balance": balance,
            "rate_limit_bonus": rate_bonus,
            "total_earned": total_earned,
            "total_spent": total_spent,
            "net_flow": total_earned - total_spent,
            "transaction_count": len(lct_transactions)
        }


class EconomicCogitationNode:
    """
    Cogitation node with integrated economics + security.

    Combines:
    - Session 137: Security (rate limiting, quality, reputation)
    - Session 142: Economics (ATP rewards, penalties)
    """

    def __init__(
        self,
        node_id: str,
        lct_id: str,
        atp_system: ATPEconomicSystem,
        reputation_system: ReputationSystem,
        rate_limiter: RateLimiter,
        quality_validator: QualityValidator
    ):
        self.node_id = node_id
        self.lct_id = lct_id
        self.atp_system = atp_system
        self.reputation_system = reputation_system
        self.rate_limiter = rate_limiter
        self.quality_validator = quality_validator

    def submit_thought(
        self,
        content: str,
        coherence_score: float
    ) -> Tuple[bool, str, Optional[float]]:
        """
        Submit a thought with full economic + security validation.

        Returns (accepted, message, ATP_change)
        """
        # Apply daily recharge first
        recharge, recharged = self.atp_system.apply_daily_recharge(self.lct_id)

        # Get current trust and ATP for rate limiting
        record = self.reputation_system.get_or_create_record(self.node_id, self.lct_id)
        trust_score = record.trust_score

        # ATP bonus affects rate limits
        atp_bonus = self.atp_system.get_rate_limit_bonus(self.lct_id)
        effective_trust = min(1.0, trust_score + atp_bonus)

        # Update rate limiter with effective trust
        self.rate_limiter.set_trust_score(self.node_id, effective_trust)

        # Check rate limit
        thought_size = len(content.encode('utf-8'))
        allowed, rate_msg = self.rate_limiter.check_rate_limit(self.node_id, thought_size)

        if not allowed:
            # Rate limit exceeded = spam attempt = ATP penalty
            penalty, penalty_msg = self.atp_system.penalize_violation(
                self.node_id,
                self.lct_id,
                "Rate limit spam"
            )

            return False, f"Rate limited + {penalty} ATP penalty: {rate_msg}", -penalty

        # Check quality
        valid, quality_msg = self.quality_validator.validate_thought(content, coherence_score)

        if not valid:
            # Quality failure = violation = ATP penalty + reputation loss
            penalty, penalty_msg = self.atp_system.penalize_violation(
                self.node_id,
                self.lct_id,
                f"Quality violation: {quality_msg}"
            )

            self.reputation_system.record_violation(self.node_id, self.lct_id, quality_msg)

            return False, f"Quality failed + {penalty} ATP penalty: {quality_msg}", -penalty

        # Thought accepted!
        # Record rate limit
        self.rate_limiter.record_thought(self.node_id, thought_size)

        # Update reputation (positive)
        self.reputation_system.record_contribution(self.node_id, self.lct_id, coherence_score)

        # Award ATP
        reward, reward_msg = self.atp_system.reward_thought(self.node_id, self.lct_id, coherence_score)

        return True, f"Thought accepted + {reward} ATP reward: {reward_msg}", reward


def test_atp_economic_incentives():
    """Test ATP economic incentives integrated with security."""
    print()
    print("=" * 80)
    print("SESSION 142: ATP ECONOMIC INCENTIVES")
    print("=" * 80)
    print()
    print("Testing economic layer on top of Sessions 137-141 security.")
    print()

    # Create systems
    atp = ATPEconomicSystem()
    reputation = ReputationSystem(storage_dir=Path("economic_reputation_db"))
    rate_limiter = RateLimiter(base_limits=RateLimit(
        max_thoughts_per_minute=10,
        max_bandwidth_kb_per_minute=100.0,
        trust_multiplier=0.5
    ))
    quality_validator = QualityValidator()

    # Test 1: Quality rewards
    print("=" * 80)
    print("TEST 1: ATP Rewards for Quality Contributions")
    print("=" * 80)
    print()

    node = EconomicCogitationNode(
        "quality-node",
        "lct:web4:ai:quality001",
        atp,
        reputation,
        rate_limiter,
        quality_validator
    )

    initial_balance = atp.get_balance(node.lct_id)
    print(f"Initial ATP balance: {initial_balance}")
    print()

    # High-quality thought
    accepted, msg, atp_change = node.submit_thought(
        "High-quality distributed consciousness research",
        coherence_score=0.9
    )

    stats = atp.get_stats(node.lct_id)
    print(f"High-quality thought (0.9 coherence):")
    print(f"  Accepted: {accepted}")
    print(f"  ATP change: +{atp_change}")
    print(f"  New balance: {stats['balance']}")
    print()

    # Medium-quality thought
    accepted2, msg2, atp_change2 = node.submit_thought(
        "Medium-quality thought about federation",
        coherence_score=0.6
    )

    stats2 = atp.get_stats(node.lct_id)
    print(f"Medium-quality thought (0.6 coherence):")
    print(f"  Accepted: {accepted2}")
    print(f"  ATP change: +{atp_change2}")
    print(f"  New balance: {stats2['balance']}")
    print()

    if atp_change > atp_change2:
        print("✓ Higher quality earns more ATP")
    print()

    # Test 2: Violation penalties
    print("=" * 80)
    print("TEST 2: ATP Penalties for Violations")
    print("=" * 80)
    print()

    spammer = EconomicCogitationNode(
        "spammer",
        "lct:web4:ai:spam001",
        atp,
        reputation,
        rate_limiter,
        quality_validator
    )

    spam_balance = atp.get_balance(spammer.lct_id)
    print(f"Spammer initial balance: {spam_balance}")
    print()

    # Low-quality spam
    accepted_spam, msg_spam, atp_spam = spammer.submit_thought(
        "spam",  # Too short
        coherence_score=0.1
    )

    spam_stats = atp.get_stats(spammer.lct_id)
    print(f"Spam attempt:")
    print(f"  Accepted: {accepted_spam}")
    print(f"  ATP change: {atp_spam}")
    print(f"  New balance: {spam_stats['balance']}")
    print(f"  Message: {msg_spam}")
    print()

    if atp_spam < 0:
        print("✓ Violations cost ATP")
    print()

    # Test 3: Economic feedback with security
    print("=" * 80)
    print("TEST 3: Economic → Security Feedback Loop")
    print("=" * 80)
    print()

    rich_node = EconomicCogitationNode(
        "rich-node",
        "lct:web4:ai:rich001",
        atp,
        reputation,
        RateLimiter(base_limits=RateLimit(
            max_thoughts_per_minute=10,
            max_bandwidth_kb_per_minute=100.0,
            trust_multiplier=0.5
        )),
        quality_validator
    )

    # Give rich node lots of ATP
    for i in range(50):
        rich_node.submit_thought(f"Quality thought {i}" * 10, 0.85)

    rich_stats = atp.get_stats(rich_node.lct_id)
    rich_bonus = atp.get_rate_limit_bonus(rich_node.lct_id)

    print(f"After 50 quality contributions:")
    print(f"  ATP balance: {rich_stats['balance']:.1f}")
    print(f"  Rate limit bonus: {rich_bonus:.1%}")
    print(f"  Total earned: {rich_stats['total_earned']:.1f}")
    print()

    if rich_bonus > 0:
        print("✓ ✓ ✓ ECONOMIC FEEDBACK WORKING!")
        print("  High ATP balance → Higher rate limits")
    print()

    # Test 4: Attack economics
    print("=" * 80)
    print("TEST 4: Attack Economics (Cost-Benefit Analysis)")
    print("=" * 80)
    print()

    attacker = EconomicCogitationNode(
        "attacker",
        "lct:web4:ai:attack001",
        atp,
        reputation,
        RateLimiter(base_limits=RateLimit(
            max_thoughts_per_minute=10,
            max_bandwidth_kb_per_minute=100.0,
            trust_multiplier=0.5
        )),
        quality_validator
    )

    attack_balance_start = atp.get_balance(attacker.lct_id)

    # Attempt spam attack
    for i in range(20):
        attacker.submit_thought("spam spam spam", 0.1)

    attack_balance_end = atp.get_balance(attacker.lct_id)
    atp_lost = attack_balance_start - attack_balance_end

    print(f"Spam attack (20 attempts):")
    print(f"  Initial ATP: {attack_balance_start}")
    print(f"  Final ATP: {attack_balance_end}")
    print(f"  ATP lost: {atp_lost}")
    print()

    if atp_lost > attack_balance_start * 0.5:
        print("✓ Attack is economically costly")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    print("Economic + Security Stack:")
    print("  Layer 1 (Identity): PoW + LCT binding")
    print("  Layer 2 (Content): Quality validation + rate limiting")
    print("  Layer 3 (Behavior): Reputation + trust decay")
    print("  Layer 4 (Resources): Corpus limits")
    print("  Layer 5 (Economics): ATP rewards + penalties ← NEW")
    print()

    print("ATP Economic Mechanisms:")
    print("  ✓ Quality rewards (1-2 ATP per thought)")
    print("  ✓ Violation penalties (5-10 ATP cost)")
    print("  ✓ Balance-based privileges (rate limit bonus)")
    print("  ✓ Daily regeneration (10 ATP/day)")
    print()

    print("Attack Economics:")
    print(f"  Spam cost: {atp_lost:.1f} ATP lost")
    print(f"  Quality reward: {rich_stats['total_earned']:.1f} ATP earned")
    print(f"  Cost/benefit ratio: {atp_lost / rich_stats['total_earned']:.1f}x")
    print()

    print("Economic Feedback:")
    print(f"  Rich node bonus: {rich_bonus:.1%} rate limit increase")
    print(f"  Attacker penalty: {atp_lost:.1f} ATP lost")
    print(f"  Incentive alignment: {'✓ Working' if rich_bonus > 0 and atp_lost > 0 else '✗ Failed'}")
    print()

    all_tests_passed = (
        atp_change > atp_change2 and
        atp_spam < 0 and
        rich_bonus > 0 and
        atp_lost > 0
    )

    if all_tests_passed:
        print("╔" + "=" * 78 + "╗")
        print("║" + "  ✓ ✓ ✓ ATP ECONOMIC INCENTIVES WORKING! ✓ ✓ ✓".center(78) + "║")
        print("╚" + "=" * 78 + "╝")
        print()
        print("COMPLETE STACK (Sessions 137-142):")
        print("  ✓ Security hardening (Sessions 137-141)")
        print("  ✓ Economic incentives (Session 142)")
        print("  ✓ Attack resistance (computational + economic)")
        print("  ✓ Self-sustaining ecosystem")
    else:
        print("╔" + "=" * 78 + "╗")
        print("║" + "  ⚠ SOME TESTS NEED ATTENTION ⚠".center(78) + "║")
        print("╚" + "=" * 78 + "╝")

    print()
    return all_tests_passed


if __name__ == "__main__":
    success = test_atp_economic_incentives()
    sys.exit(0 if success else 1)
