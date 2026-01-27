# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Activity Quality Scoring
# https://github.com/dp-web4/web4

"""
Activity Quality: Distinguishing meaningful work from trivial pings.

Problem: Trust decay evasion via daily micro-pings. An entity that sends
one trivial heartbeat per day preserves ~4.1% more trust than an entity
doing genuine work. Activity quality scoring closes this gap by weighting
actions based on their actual significance.

Design principles:
- Actions that change state are more meaningful than read-only
- Actions requiring approval are more meaningful than unilateral
- Actions with ATP cost are more meaningful than free ones
- Diversity of action types indicates genuine engagement
- Repetitive identical actions suggest automation/gaming
- Context matters: metabolic state affects quality interpretation

Quality score range: 0.0 (trivial ping) to 1.0 (high-value action)
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ActivityTier(Enum):
    """Classification of activity significance."""
    TRIVIAL = "trivial"         # Heartbeat-only, no real content
    LOW = "low"                 # Minor read/status actions
    MODERATE = "moderate"       # Standard work (commits, reviews)
    HIGH = "high"               # Approved actions, deployments
    CRITICAL = "critical"       # Multi-sig proposals, policy changes


# Quality weights by transaction type
TX_TYPE_QUALITY: Dict[str, float] = {
    # Critical actions (0.8-1.0)
    "multisig_proposal_created": 0.90,
    "multisig_executed": 0.95,
    "multisig_vetoed": 0.85,
    "policy_changed": 0.90,
    "admin_bound_tpm2": 1.00,
    "admin_bound_software": 0.80,

    # High-value actions (0.6-0.8)
    "r6_completed": 0.75,
    "r6_approved": 0.70,
    "r6_created": 0.65,
    "r6_rejected": 0.60,      # Rejection still shows engagement
    "member_added": 0.70,
    "member_removed": 0.65,

    # Moderate actions (0.3-0.6)
    "trust_update": 0.45,
    "multisig_vote": 0.50,
    "metabolic_transition": 0.40,
    "atp_transfer": 0.50,
    "audit_record": 0.35,

    # Low actions (0.1-0.3)
    "heartbeat": 0.15,
    "status_check": 0.10,
    "presence_ping": 0.10,

    # Trivial (0.0-0.1)
    "noop": 0.0,
    "keepalive": 0.05,
}

# Default quality for unknown transaction types
DEFAULT_TX_QUALITY = 0.30


@dataclass
class ActivityWindow:
    """Sliding window of activity for quality analysis."""
    entity_id: str
    window_seconds: float = 86400.0  # 24 hours
    actions: List[Dict] = field(default_factory=list)
    _type_counts: Dict[str, int] = field(default_factory=dict)

    def record(self, tx_type: str, timestamp: str, metadata: Optional[Dict] = None,
               atp_cost: float = 0.0):
        """Record an action in the window."""
        entry = {
            "tx_type": tx_type,
            "timestamp": timestamp,
            "metadata": metadata or {},
            "atp_cost": atp_cost,
            "quality": self._score_single(tx_type, metadata or {}, atp_cost),
        }
        self.actions.append(entry)
        self._type_counts[tx_type] = self._type_counts.get(tx_type, 0) + 1
        self._prune()

    def _prune(self):
        """Remove actions outside the window."""
        if not self.actions:
            return
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window_seconds)
        cutoff_str = cutoff.isoformat()

        pruned = [a for a in self.actions if a["timestamp"] >= cutoff_str]
        if len(pruned) < len(self.actions):
            # Recount types
            self._type_counts = {}
            for a in pruned:
                t = a["tx_type"]
                self._type_counts[t] = self._type_counts.get(t, 0) + 1
            self.actions = pruned

    def _score_single(self, tx_type: str, metadata: Dict, atp_cost: float) -> float:
        """Score a single action's quality."""
        base = TX_TYPE_QUALITY.get(tx_type, DEFAULT_TX_QUALITY)

        # ATP cost bonus: spending resources signals commitment
        if atp_cost > 0:
            atp_bonus = min(0.15, atp_cost / 100.0)
            base = min(1.0, base + atp_bonus)

        # Metadata richness bonus: actions with meaningful data score higher
        if metadata:
            data_keys = len(metadata)
            if data_keys >= 5:
                base = min(1.0, base + 0.10)
            elif data_keys >= 3:
                base = min(1.0, base + 0.05)

        return base

    @property
    def quality_score(self) -> float:
        """
        Aggregate quality score for the activity window.

        Factors:
        1. Individual action qualities (weighted)
        2. Type diversity (more diverse = higher quality)
        3. Repetition penalty (same action repeated = gaming)
        4. Volume reasonableness (too many or too few is suspect)
        """
        if not self.actions:
            return 0.0

        # 1. Weighted action quality (most recent actions count more)
        n = len(self.actions)
        total_quality = 0.0
        total_weight = 0.0
        for i, action in enumerate(self.actions):
            # Recency weight: latest = 1.0, oldest = 0.5
            recency = 0.5 + 0.5 * (i / max(n - 1, 1))
            total_quality += action["quality"] * recency
            total_weight += recency

        avg_quality = total_quality / total_weight if total_weight > 0 else 0.0

        # 2. Type diversity bonus
        diversity = self._diversity_score()

        # 3. Repetition penalty
        repetition = self._repetition_penalty()

        # 4. Volume reasonableness
        volume = self._volume_factor()

        # Composite: quality weighted by diversity, penalized for repetition
        composite = avg_quality * 0.50 + diversity * 0.25 + volume * 0.25
        composite *= (1.0 - repetition)

        return max(0.0, min(1.0, composite))

    def _diversity_score(self) -> float:
        """Score based on variety of action types (Shannon entropy normalized)."""
        if not self._type_counts:
            return 0.0

        total = sum(self._type_counts.values())
        if total == 0:
            return 0.0

        # Shannon entropy
        entropy = 0.0
        for count in self._type_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        # Normalize by log2 of max possible types (capped at 10 for scaling)
        max_entropy = math.log2(min(len(self._type_counts), 10))
        if max_entropy == 0:
            return 0.0

        return min(1.0, entropy / max_entropy)

    def _repetition_penalty(self) -> float:
        """Penalty for repetitive identical actions (gaming signal)."""
        if len(self.actions) < 3:
            return 0.0

        total = sum(self._type_counts.values())
        max_count = max(self._type_counts.values())
        dominance = max_count / total

        # If one type is >80% of all actions, that's suspicious
        if dominance > 0.8:
            return 0.4  # Heavy penalty
        elif dominance > 0.6:
            return 0.2  # Moderate penalty
        return 0.0

    def _volume_factor(self) -> float:
        """
        Score based on action volume reasonableness.

        Too few actions = not really working.
        Reasonable volume = good.
        Too many actions = likely automation.
        """
        n = len(self.actions)
        hours = self.window_seconds / 3600.0

        rate = n / max(hours, 1.0)  # actions per hour

        if rate < 0.5:
            # Less than 1 action per 2 hours - minimal engagement
            return 0.2
        elif rate <= 10:
            # 0.5-10 per hour - reasonable human pace
            return 0.8 + 0.2 * min(1.0, rate / 10.0)
        elif rate <= 30:
            # 10-30 per hour - high but possible during active work
            return 0.8
        else:
            # >30 per hour - likely automated
            return max(0.2, 0.8 - (rate - 30) / 100.0)

    @property
    def tier(self) -> ActivityTier:
        """Classify activity into a tier."""
        score = self.quality_score
        if score >= 0.7:
            return ActivityTier.CRITICAL
        elif score >= 0.5:
            return ActivityTier.HIGH
        elif score >= 0.3:
            return ActivityTier.MODERATE
        elif score >= 0.1:
            return ActivityTier.LOW
        return ActivityTier.TRIVIAL

    @property
    def weighted_action_count(self) -> float:
        """
        Quality-weighted action count for trust decay calculations.

        Replaces raw `actions_since_update` with quality-aware count.
        A single high-quality action counts more than many trivial ones.
        """
        if not self.actions:
            return 0.0

        return sum(a["quality"] for a in self.actions)

    def to_dict(self) -> Dict:
        """Serialize window state."""
        return {
            "entity_id": self.entity_id,
            "window_seconds": self.window_seconds,
            "action_count": len(self.actions),
            "quality_score": round(self.quality_score, 4),
            "tier": self.tier.value,
            "weighted_count": round(self.weighted_action_count, 2),
            "type_distribution": dict(self._type_counts),
            "diversity": round(self._diversity_score(), 4),
            "repetition_penalty": round(self._repetition_penalty(), 4),
        }


def compute_quality_adjusted_decay(
    raw_action_count: int,
    activity_window: Optional[ActivityWindow] = None,
    metabolic_state: str = "active",
) -> float:
    """
    Convert raw action count to quality-adjusted count for trust decay.

    If an ActivityWindow is available, uses quality-weighted counting.
    Otherwise falls back to raw count with metabolic state adjustment.

    Returns: Adjusted action count (float) for use with TrustDecayCalculator.
    """
    if activity_window is not None:
        weighted = activity_window.weighted_action_count
        quality = activity_window.quality_score

        # Minimum quality threshold: actions below this don't count
        QUALITY_THRESHOLD = 0.15
        if quality < QUALITY_THRESHOLD:
            # Trivial activity gets minimal credit
            return weighted * 0.1

        return weighted

    # Fallback: apply metabolic state multiplier to raw count
    METABOLIC_QUALITY_MULTIPLIERS = {
        "active": 1.0,
        "rest": 0.8,
        "sleep": 0.3,
        "hibernation": 0.1,
        "torpor": 0.05,
        "estivation": 0.2,
        "dreaming": 0.5,  # Recalibration has value
        "molting": 0.7,
    }
    multiplier = METABOLIC_QUALITY_MULTIPLIERS.get(metabolic_state, 1.0)
    return raw_action_count * multiplier


# --- Self-test ---

def _self_test():
    """Verify activity quality scoring behavior."""
    print("=" * 60)
    print("Activity Quality Scoring - Self Test")
    print("=" * 60)
    now = datetime.now(timezone.utc)

    # Test 1: Empty window
    window = ActivityWindow(entity_id="test:empty")
    assert window.quality_score == 0.0
    assert window.tier == ActivityTier.TRIVIAL
    print("  [1] Empty window: score=0.0, tier=trivial ✓")

    # Test 2: Trivial ping-only activity
    ping_window = ActivityWindow(entity_id="test:pinger")
    for i in range(5):
        ts = (now - timedelta(hours=4-i)).isoformat()
        ping_window.record("heartbeat", ts)
    score_ping = ping_window.quality_score
    print(f"  [2] Ping-only (5 heartbeats): score={score_ping:.3f}, tier={ping_window.tier.value}")
    assert score_ping < 0.3, f"Ping-only should be low quality, got {score_ping}"

    # Test 3: Diverse meaningful activity
    work_window = ActivityWindow(entity_id="test:worker")
    actions = [
        ("r6_created", 2.0),
        ("r6_approved", 0.0),
        ("r6_completed", 5.0),
        ("trust_update", 0.0),
        ("multisig_vote", 0.0),
        ("heartbeat", 0.0),
        ("audit_record", 0.0),
    ]
    for i, (tx_type, atp) in enumerate(actions):
        ts = (now - timedelta(hours=6-i)).isoformat()
        work_window.record(tx_type, ts, atp_cost=atp)
    score_work = work_window.quality_score
    print(f"  [3] Diverse work (7 mixed actions): score={score_work:.3f}, tier={work_window.tier.value}")
    assert score_work > score_ping, "Diverse work should score higher than pings"

    # Test 4: Repetitive gaming pattern
    game_window = ActivityWindow(entity_id="test:gamer")
    for i in range(20):
        ts = (now - timedelta(minutes=60-i*3)).isoformat()
        game_window.record("heartbeat", ts)
    score_game = game_window.quality_score
    print(f"  [4] Repetitive (20 heartbeats): score={score_game:.3f}, tier={game_window.tier.value}")
    assert score_game < 0.2, f"Repetitive gaming should be very low, got {score_game}"

    # Test 5: High-value critical actions
    crit_window = ActivityWindow(entity_id="test:admin")
    crit_actions = [
        ("multisig_proposal_created", 10.0),
        ("policy_changed", 5.0),
        ("admin_bound_software", 0.0),
        ("r6_completed", 8.0),
        ("multisig_executed", 15.0),
    ]
    for i, (tx_type, atp) in enumerate(crit_actions):
        ts = (now - timedelta(hours=4-i)).isoformat()
        crit_window.record(tx_type, ts, atp_cost=atp)
    score_crit = crit_window.quality_score
    print(f"  [5] Critical actions (5 high-value): score={score_crit:.3f}, tier={crit_window.tier.value}")
    assert score_crit > score_work, "Critical actions should score highest"

    # Test 6: Quality-adjusted decay
    adjusted_ping = compute_quality_adjusted_decay(5, ping_window)
    adjusted_work = compute_quality_adjusted_decay(7, work_window)
    adjusted_crit = compute_quality_adjusted_decay(5, crit_window)
    print(f"  [6] Decay adjustments: ping={adjusted_ping:.2f}, work={adjusted_work:.2f}, crit={adjusted_crit:.2f}")
    assert adjusted_work > adjusted_ping, "Work should get more decay credit than pings"
    assert adjusted_crit > adjusted_work, "Critical should get most decay credit"

    # Test 7: Metabolic fallback
    active = compute_quality_adjusted_decay(10, metabolic_state="active")
    hibernating = compute_quality_adjusted_decay(10, metabolic_state="hibernation")
    print(f"  [7] Metabolic fallback: active={active:.1f}, hibernation={hibernating:.1f}")
    assert active > hibernating, "Active state should get more credit"

    # Test 8: Micro-ping detection (the attack vector)
    micro_window = ActivityWindow(entity_id="test:micropinger", window_seconds=86400*7)
    # One ping per day for a week
    for day in range(7):
        ts = (now - timedelta(days=6-day)).isoformat()
        micro_window.record("presence_ping", ts)
    score_micro = micro_window.quality_score
    adjusted_micro = compute_quality_adjusted_decay(7, micro_window)
    print(f"  [8] Micro-ping (1/day, 7 days): score={score_micro:.3f}, adjusted={adjusted_micro:.2f}")
    # This is the key test: micro-pings should barely count
    assert adjusted_micro < 2.0, f"Micro-pings should get minimal credit, got {adjusted_micro}"

    print("\n" + "=" * 60)
    print("All activity quality tests passed!")
    print("=" * 60)

    # Summary comparison
    print("\n  Quality Score Comparison:")
    print(f"    Micro-ping (1/day):     {score_micro:.3f} ({ping_window.tier.value})")
    print(f"    Rapid heartbeats (20x): {score_game:.3f} ({game_window.tier.value})")
    print(f"    Normal heartbeats (5x): {score_ping:.3f} ({ping_window.tier.value})")
    print(f"    Diverse work (7x):      {score_work:.3f} ({work_window.tier.value})")
    print(f"    Critical actions (5x):  {score_crit:.3f} ({crit_window.tier.value})")


if __name__ == "__main__":
    _self_test()
