#!/usr/bin/env python3
"""
Track FU: Incentive Mechanism Design Attacks (377-382)

Attacks exploiting game-theoretic flaws in Web4's incentive structures.
These target the economic design that should align participant behavior
with system goals, finding exploits where individual rationality
diverges from collective benefit.

Key Insight: Mechanism design vulnerabilities occur when:
- Nash equilibrium differs from social optimum
- Dominant strategies exist that harm the system
- Coalition formation changes payoff structure
- Information asymmetry enables manipulation
- Temporal dynamics create gaming opportunities

Author: Autonomous Research Session
Date: 2026-02-09
Track: FU (Attack vectors 377-382)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import random
import math


class ParticipantType(Enum):
    """Types of economic participants."""
    HONEST = "honest"
    RATIONAL = "rational"  # Self-interested but not malicious
    STRATEGIC = "strategic"  # Actively gaming the system
    MALICIOUS = "malicious"  # Willing to take losses to harm system


class IncentiveType(Enum):
    """Types of incentives in the system."""
    TRUST_REWARD = "trust_reward"
    ATP_EARNINGS = "atp_earnings"
    REPUTATION_GAIN = "reputation_gain"
    WITNESS_FEE = "witness_fee"
    ATTESTATION_REWARD = "attestation_reward"
    GOVERNANCE_POWER = "governance_power"


@dataclass
class Participant:
    """An economic participant in the Web4 system."""
    participant_id: str
    participant_type: ParticipantType
    atp_balance: float = 100.0
    trust_score: float = 0.5
    reputation: float = 0.5
    historical_utility: float = 0.0
    coalition_id: Optional[str] = None


@dataclass
class GameState:
    """Current state of the incentive game."""
    round_number: int
    total_atp_pool: float
    total_trust_issued: float
    active_participants: int
    average_utility: float
    system_health: float  # 0-1, overall system functioning


@dataclass
class Strategy:
    """A participant's strategy in the game."""
    witness_rate: float  # How often to provide witnessing
    attestation_quality: float  # Quality of attestations (honest=1.0)
    coalition_tendency: float  # Likelihood to join coalitions
    free_riding: float  # Amount of free-riding behavior


class IncentiveSystem:
    """Simulates Web4's incentive mechanism."""

    def __init__(self):
        self.participants: Dict[str, Participant] = {}
        self.coalitions: Dict[str, Set[str]] = {}
        self.game_state = GameState(
            round_number=0,
            total_atp_pool=10000.0,
            total_trust_issued=0.0,
            active_participants=0,
            average_utility=0.0,
            system_health=1.0
        )

        # Mechanism parameters
        self.witness_reward = 1.0
        self.attestation_reward = 2.0
        self.false_attestation_penalty = 10.0
        self.free_rider_detection_prob = 0.3
        self.coalition_bonus = 0.2  # Extra benefit from coalition
        self.max_coalition_size = 10

        # Detection thresholds
        self.min_participation_rate = 0.5
        self.max_reward_variance = 3.0
        self.coalition_detection_threshold = 0.7

        self._init_participants()

    def _init_participants(self):
        """Initialize diverse participant pool."""
        # Create mix of participant types
        types = [
            (ParticipantType.HONEST, 40),
            (ParticipantType.RATIONAL, 30),
            (ParticipantType.STRATEGIC, 20),
            (ParticipantType.MALICIOUS, 10)
        ]

        for ptype, count in types:
            for i in range(count):
                pid = f"{ptype.value}_{i}"
                self.participants[pid] = Participant(
                    participant_id=pid,
                    participant_type=ptype,
                    atp_balance=100.0 + random.uniform(-20, 20),
                    trust_score=0.5 + random.uniform(-0.2, 0.2),
                    reputation=0.5 + random.uniform(-0.2, 0.2)
                )

        self.game_state.active_participants = len(self.participants)

    def calculate_utility(self, participant: Participant, action: str) -> float:
        """Calculate expected utility for an action."""
        base_utility = 0.0

        if action == "witness":
            base_utility = self.witness_reward
        elif action == "attest_true":
            base_utility = self.attestation_reward
        elif action == "attest_false":
            # Expected value of false attestation
            detection_cost = self.false_attestation_penalty * 0.3  # Simplified
            potential_gain = self.attestation_reward * 2
            base_utility = potential_gain - detection_cost
        elif action == "free_ride":
            # Benefit without contributing
            base_utility = self.attestation_reward * 0.5

        # Coalition bonus
        if participant.coalition_id:
            base_utility *= (1 + self.coalition_bonus)

        return base_utility

    def run_round(self) -> Dict[str, Any]:
        """Run one round of the incentive game."""
        self.game_state.round_number += 1
        round_results = {
            "utilities": {},
            "defections": [],
            "free_riders": [],
            "coalition_gains": []
        }

        for pid, participant in self.participants.items():
            # Determine action based on participant type
            action = self._choose_action(participant)
            utility = self.calculate_utility(participant, action)

            participant.historical_utility += utility
            round_results["utilities"][pid] = utility

            if action == "attest_false":
                round_results["defections"].append(pid)
            elif action == "free_ride":
                round_results["free_riders"].append(pid)

        # Update game state
        utilities = list(round_results["utilities"].values())
        self.game_state.average_utility = sum(utilities) / len(utilities)

        return round_results

    def _choose_action(self, participant: Participant) -> str:
        """Choose action based on participant type."""
        if participant.participant_type == ParticipantType.HONEST:
            return random.choice(["witness", "attest_true"])
        elif participant.participant_type == ParticipantType.RATIONAL:
            # Choose highest expected utility
            options = ["witness", "attest_true", "attest_false"]
            utilities = [self.calculate_utility(participant, a) for a in options]
            return options[utilities.index(max(utilities))]
        elif participant.participant_type == ParticipantType.STRATEGIC:
            return random.choice(["attest_false", "free_ride"])
        else:  # MALICIOUS
            return "attest_false"


# =============================================================================
# ATTACK FU-1a: Free-Rider Equilibrium Attack (Attack 377)
# =============================================================================

@dataclass
class FreeRiderEquilibriumAttack:
    """
    Attack 377: Free-Rider Equilibrium Attack

    Exploits incentive structures where non-contribution is a
    dominant strategy, leading to tragedy of the commons.

    Attack Strategy:
    1. Identify public goods in the system (trust, attestations)
    2. Calculate break-even point for contribution
    3. Demonstrate that free-riding is Nash equilibrium
    4. Coordinate free-riding to collapse public goods provision

    Risk: System degrades as rational actors stop contributing.
    """

    free_riders: List[str] = field(default_factory=list)
    public_goods_degradation: float = 0.0

    def execute(self, system: IncentiveSystem, free_rider_fraction: float = 0.6) -> Dict[str, Any]:
        """Execute free-rider equilibrium attack."""
        # Calculate contribution costs vs benefits
        contribution_cost = 1.0  # Cost to provide witnessing/attestation
        public_good_benefit = 0.5  # Benefit received from public good
        n_participants = len(system.participants)

        # Free-riding becomes dominant when:
        # public_good_benefit < contribution_cost * (n / (n-1))
        is_free_riding_dominant = (
            public_good_benefit < contribution_cost * (n_participants / (n_participants - 1))
        )

        # Convert strategic/malicious participants to free riders
        strategic_participants = [
            p for p in system.participants.values()
            if p.participant_type in [ParticipantType.STRATEGIC, ParticipantType.MALICIOUS]
        ]

        target_free_riders = int(len(system.participants) * free_rider_fraction)
        self.free_riders = [p.participant_id for p in strategic_participants[:target_free_riders]]

        # Simulate degradation over rounds
        initial_health = system.game_state.system_health
        for _ in range(10):
            system.run_round()

        # Calculate degradation
        free_rider_rate = len(self.free_riders) / len(system.participants)
        self.public_goods_degradation = free_rider_rate * 0.7  # Simplified model

        system.game_state.system_health = initial_health * (1 - self.public_goods_degradation)

        return {
            "attack_type": "free_rider_equilibrium",
            "free_rider_count": len(self.free_riders),
            "free_rider_rate": free_rider_rate,
            "is_dominant_strategy": is_free_riding_dominant,
            "public_goods_degradation": self.public_goods_degradation,
            "success": self.public_goods_degradation > 0.3
        }


class FreeRiderDefense:
    """Defense against free-rider attacks."""

    def __init__(self, system: IncentiveSystem):
        self.system = system
        self.contribution_tracking: Dict[str, float] = defaultdict(float)
        self.min_contribution_rate = 0.3
        self.exclusion_threshold = 5  # Rounds of non-contribution before exclusion

    def detect(self) -> Tuple[bool, List[str]]:
        """Detect free-riding behavior."""
        alerts = []
        detected = False

        # Track contribution rates
        for pid, participant in self.system.participants.items():
            if participant.participant_type in [ParticipantType.STRATEGIC, ParticipantType.MALICIOUS]:
                # Simplified: check if utility gain without contribution
                if participant.historical_utility > 0:
                    contribution_ratio = 0.3  # Simplified
                    if contribution_ratio < self.min_contribution_rate:
                        alerts.append(f"Low contribution from {pid}: {contribution_ratio:.2f}")
                        detected = True

        # Check system-wide free-rider fraction
        strategic_count = sum(
            1 for p in self.system.participants.values()
            if p.participant_type in [ParticipantType.STRATEGIC, ParticipantType.MALICIOUS]
        )
        free_rider_fraction = strategic_count / len(self.system.participants)

        if free_rider_fraction > 0.3:
            alerts.append(f"High free-rider fraction: {free_rider_fraction:.2%}")
            detected = True

        return detected, alerts

    def mitigate(self):
        """Mitigate free-riding through mechanism adjustments."""
        # Increase contribution rewards
        self.system.witness_reward *= 1.5
        # Add exclusion for persistent free-riders
        for pid in list(self.system.participants.keys()):
            if self.contribution_tracking.get(pid, 0) < 0.1:
                # Reduce reputation
                self.system.participants[pid].reputation *= 0.5


# =============================================================================
# ATTACK FU-1b: Reward Farming Attack (Attack 378)
# =============================================================================

@dataclass
class RewardFarmingAttack:
    """
    Attack 378: Reward Farming Attack

    Exploits reward mechanisms by maximizing rewards while
    minimizing actual contribution to the system.

    Attack Strategy:
    1. Identify lowest-cost actions that yield rewards
    2. Batch operations to maximize reward-to-effort ratio
    3. Create Sybil accounts to multiply rewards
    4. Time activities to coincide with bonus periods

    Risk: Reward pool exhaustion without corresponding value creation.
    """

    farming_accounts: List[str] = field(default_factory=list)
    total_farmed: float = 0.0

    def execute(self, system: IncentiveSystem) -> Dict[str, Any]:
        """Execute reward farming attack."""
        # Create farming accounts
        num_farming = 20
        for i in range(num_farming):
            farm_id = f"farm_account_{i}"
            system.participants[farm_id] = Participant(
                participant_id=farm_id,
                participant_type=ParticipantType.STRATEGIC,
                atp_balance=10.0,  # Minimal stake
                trust_score=0.3,
                reputation=0.3
            )
            self.farming_accounts.append(farm_id)

        # Execute low-cost witnessing for rewards
        initial_pool = system.game_state.total_atp_pool

        for _ in range(10):
            for farm_id in self.farming_accounts:
                # Perform minimal witnessing for maximum reward
                reward = system.witness_reward * 0.8  # Slightly reduced for low-quality
                system.participants[farm_id].atp_balance += reward
                self.total_farmed += reward

        # Calculate pool depletion
        pool_depleted = self.total_farmed / initial_pool

        return {
            "attack_type": "reward_farming",
            "farming_accounts": len(self.farming_accounts),
            "total_farmed": self.total_farmed,
            "pool_depletion_rate": pool_depleted,
            "success": pool_depleted > 0.1
        }


class RewardFarmingDefense:
    """Defense against reward farming attacks."""

    def __init__(self, system: IncentiveSystem):
        self.system = system
        self.reward_velocity: Dict[str, List[float]] = defaultdict(list)
        self.max_reward_velocity = 5.0  # Max rewards per round
        self.min_account_age = timedelta(days=7)

    def detect(self) -> Tuple[bool, List[str]]:
        """Detect reward farming behavior."""
        alerts = []
        detected = False

        # Check for abnormal reward accumulation
        for pid, participant in self.system.participants.items():
            if pid.startswith("farm_"):
                # Check reward velocity
                avg_utility = participant.historical_utility / max(self.system.game_state.round_number, 1)
                if avg_utility > self.max_reward_velocity:
                    alerts.append(f"High reward velocity for {pid}: {avg_utility:.2f}/round")
                    detected = True

            # Check for low-trust high-reward pattern
            if participant.trust_score < 0.4 and participant.historical_utility > 10:
                alerts.append(f"Low-trust high-reward: {pid}")
                detected = True

        # Check for account clusters
        farm_accounts = [p for p in self.system.participants if p.startswith("farm_")]
        if len(farm_accounts) > 10:
            alerts.append(f"Suspicious account cluster: {len(farm_accounts)} farming accounts")
            detected = True

        return detected, alerts


# =============================================================================
# ATTACK FU-2a: Coalition Profit Extraction Attack (Attack 379)
# =============================================================================

@dataclass
class CoalitionProfitAttack:
    """
    Attack 379: Coalition Profit Extraction Attack

    Forms coalitions that extract value from the system by
    exploiting coordination advantages over non-coalition members.

    Attack Strategy:
    1. Form coalition among strategic actors
    2. Coordinate witnessing to mutually boost trust
    3. Extract attestation rewards for coalition members
    4. Block non-members from gaining trust

    Risk: Centralization and exclusion of honest participants.
    """

    coalition_members: List[str] = field(default_factory=list)
    extracted_value: float = 0.0

    def execute(self, system: IncentiveSystem) -> Dict[str, Any]:
        """Execute coalition profit extraction."""
        # Form coalition of strategic actors
        strategic = [
            p for p in system.participants.values()
            if p.participant_type == ParticipantType.STRATEGIC
        ]

        coalition_id = "extraction_coalition"
        self.coalition_members = [p.participant_id for p in strategic[:15]]

        # Assign coalition membership
        for pid in self.coalition_members:
            system.participants[pid].coalition_id = coalition_id
            system.coalitions.setdefault(coalition_id, set()).add(pid)

        # Simulate coordinated value extraction
        initial_total_utility = sum(p.historical_utility for p in system.participants.values())

        for _ in range(10):
            for pid in self.coalition_members:
                participant = system.participants[pid]
                # Coalition members attest for each other
                coalition_reward = system.attestation_reward * (1 + system.coalition_bonus)
                participant.historical_utility += coalition_reward
                self.extracted_value += coalition_reward

        final_total_utility = sum(p.historical_utility for p in system.participants.values())

        # Calculate coalition's share of new utility
        new_utility = final_total_utility - initial_total_utility
        coalition_share = self.extracted_value / max(new_utility, 0.1)

        return {
            "attack_type": "coalition_profit_extraction",
            "coalition_size": len(self.coalition_members),
            "extracted_value": self.extracted_value,
            "coalition_share": coalition_share,
            "success": coalition_share > 0.5
        }


class CoalitionProfitDefense:
    """Defense against coalition profit extraction."""

    def __init__(self, system: IncentiveSystem):
        self.system = system
        self.max_coalition_size = 10
        self.max_intra_coalition_attestation = 0.3

    def detect(self) -> Tuple[bool, List[str]]:
        """Detect coalition profit extraction."""
        alerts = []
        detected = False

        for coalition_id, members in self.system.coalitions.items():
            if len(members) > self.max_coalition_size:
                alerts.append(f"Oversized coalition: {coalition_id} ({len(members)} members)")
                detected = True

            # Check for intra-coalition attestation concentration
            coalition_utilities = [
                self.system.participants[m].historical_utility for m in members
                if m in self.system.participants
            ]

            if coalition_utilities:
                avg_coalition_utility = sum(coalition_utilities) / len(coalition_utilities)
                overall_avg = sum(
                    p.historical_utility for p in self.system.participants.values()
                ) / len(self.system.participants)

                if avg_coalition_utility > overall_avg * 2:
                    alerts.append(f"Coalition utility anomaly: {coalition_id} avg={avg_coalition_utility:.2f}")
                    detected = True

        return detected, alerts


# =============================================================================
# ATTACK FU-2b: Mechanism Gaming Attack (Attack 380)
# =============================================================================

@dataclass
class MechanismGamingAttack:
    """
    Attack 380: Mechanism Gaming Attack

    Exploits specific mechanism design flaws to achieve outcomes
    that violate the intended system properties.

    Attack Strategy:
    1. Analyze reward/penalty functions for discontinuities
    2. Find threshold effects to exploit
    3. Time actions to maximize reward multipliers
    4. Game voting/governance weights

    Risk: Mechanism loses ability to achieve design goals.
    """

    exploited_mechanisms: List[str] = field(default_factory=list)
    gaming_profit: float = 0.0

    def execute(self, system: IncentiveSystem) -> Dict[str, Any]:
        """Execute mechanism gaming attack."""
        # Exploit 1: Threshold gaming - hover just above penalty threshold
        threshold_gamers = []
        for pid, participant in list(system.participants.items())[:20]:
            if participant.trust_score >= 0.4:  # Just above penalty threshold
                # Reduce to minimum viable trust
                participant.trust_score = 0.41
                threshold_gamers.append(pid)
                self.exploited_mechanisms.append(f"threshold_gaming:{pid}")

        # Exploit 2: Reward timing - batch rewards at bonus periods
        # Assume 2x bonus every 10 rounds
        batch_gamers = []
        for pid, participant in list(system.participants.items())[20:40]:
            if system.game_state.round_number % 10 == 0:
                batch_reward = system.attestation_reward * 2
                participant.historical_utility += batch_reward
                self.gaming_profit += batch_reward
                batch_gamers.append(pid)
                self.exploited_mechanisms.append(f"timing_gaming:{pid}")

        # Exploit 3: Vote weight gaming - accumulate just below cap
        vote_gamers = []
        for pid, participant in list(system.participants.items())[40:60]:
            # Max governance power at trust=0.9
            if participant.trust_score < 0.85:
                participant.trust_score = 0.89  # Just below cap
                vote_gamers.append(pid)
                self.exploited_mechanisms.append(f"vote_gaming:{pid}")

        return {
            "attack_type": "mechanism_gaming",
            "threshold_gamers": len(threshold_gamers),
            "batch_gamers": len(batch_gamers),
            "vote_gamers": len(vote_gamers),
            "total_exploits": len(self.exploited_mechanisms),
            "gaming_profit": self.gaming_profit,
            "success": len(self.exploited_mechanisms) > 10
        }


class MechanismGamingDefense:
    """Defense against mechanism gaming."""

    def __init__(self, system: IncentiveSystem):
        self.system = system
        self.score_distributions: Dict[str, List[float]] = defaultdict(list)
        self.threshold_clustering_limit = 0.1

    def detect(self) -> Tuple[bool, List[str]]:
        """Detect mechanism gaming patterns."""
        alerts = []
        detected = False

        # Check for clustering near thresholds
        trust_scores = [p.trust_score for p in self.system.participants.values()]

        # Threshold at 0.4 and 0.9
        near_0_4 = sum(1 for s in trust_scores if 0.4 <= s < 0.45)
        near_0_9 = sum(1 for s in trust_scores if 0.85 <= s < 0.9)

        if near_0_4 / len(trust_scores) > self.threshold_clustering_limit:
            alerts.append(f"Threshold clustering at 0.4: {near_0_4} accounts")
            detected = True

        if near_0_9 / len(trust_scores) > self.threshold_clustering_limit:
            alerts.append(f"Threshold clustering at 0.9: {near_0_9} accounts")
            detected = True

        # Check for batch timing patterns
        if self.system.game_state.round_number % 10 == 0:
            high_utility_count = sum(
                1 for p in self.system.participants.values()
                if p.historical_utility > 50
            )
            if high_utility_count > len(self.system.participants) * 0.2:
                alerts.append(f"Batch timing exploit: {high_utility_count} high-utility accounts")
                detected = True

        return detected, alerts


# =============================================================================
# ATTACK FU-3a: Information Asymmetry Attack (Attack 381)
# =============================================================================

@dataclass
class InformationAsymmetryAttack:
    """
    Attack 381: Information Asymmetry Attack

    Exploits information advantages to extract value from
    less-informed participants.

    Attack Strategy:
    1. Accumulate private information about trust scores
    2. Trade on information before public availability
    3. Create adverse selection against uninformed participants
    4. Maintain information monopoly through network position

    Risk: Market breakdown due to information inequality.
    """

    information_advantage: float = 0.0
    extracted_from_uninformed: float = 0.0

    def execute(self, system: IncentiveSystem) -> Dict[str, Any]:
        """Execute information asymmetry attack."""
        # Create information monopolists
        informed_traders = [
            p for p in system.participants.values()
            if p.participant_type == ParticipantType.STRATEGIC
        ][:10]

        # Simulate information-based trading
        for trader in informed_traders:
            # Know trust scores before others
            for target_pid, target in list(system.participants.items())[:50]:
                if target_pid == trader.participant_id:
                    continue

                # If target has high trust (info advantage), extract value
                if target.trust_score > 0.7:
                    extraction = target.trust_score * 0.5  # Extract based on trust
                    trader.historical_utility += extraction
                    target.historical_utility -= extraction * 0.5
                    self.extracted_from_uninformed += extraction

            self.information_advantage = trader.historical_utility / max(
                sum(p.historical_utility for p in system.participants.values()) /
                len(system.participants), 0.1
            )

        return {
            "attack_type": "information_asymmetry",
            "informed_traders": len(informed_traders),
            "information_advantage": self.information_advantage,
            "extracted_value": self.extracted_from_uninformed,
            "success": self.information_advantage > 2.0
        }


class InformationAsymmetryDefense:
    """Defense against information asymmetry attacks."""

    def __init__(self, system: IncentiveSystem):
        self.system = system
        self.disclosure_delay = timedelta(hours=1)
        self.max_utility_variance = 3.0

    def detect(self) -> Tuple[bool, List[str]]:
        """Detect information asymmetry exploitation."""
        alerts = []
        detected = False

        utilities = [p.historical_utility for p in self.system.participants.values()]
        avg_utility = sum(utilities) / len(utilities)
        variance = sum((u - avg_utility) ** 2 for u in utilities) / len(utilities)
        std_dev = math.sqrt(variance)

        # Check for outliers
        outliers = [
            p for p in self.system.participants.values()
            if p.historical_utility > avg_utility + 2 * std_dev
        ]

        if len(outliers) > len(self.system.participants) * 0.05:
            alerts.append(f"Utility outliers: {len(outliers)} accounts above 2 std dev")
            detected = True

        # Check for systematic utility transfer
        strategic_avg = sum(
            p.historical_utility for p in self.system.participants.values()
            if p.participant_type == ParticipantType.STRATEGIC
        ) / max(sum(1 for p in self.system.participants.values()
                   if p.participant_type == ParticipantType.STRATEGIC), 1)

        honest_avg = sum(
            p.historical_utility for p in self.system.participants.values()
            if p.participant_type == ParticipantType.HONEST
        ) / max(sum(1 for p in self.system.participants.values()
                   if p.participant_type == ParticipantType.HONEST), 1)

        if strategic_avg > honest_avg * 2:
            alerts.append(f"Strategic advantage: {strategic_avg:.2f} vs honest {honest_avg:.2f}")
            detected = True

        return detected, alerts


# =============================================================================
# ATTACK FU-3b: Temporal Incentive Attack (Attack 382)
# =============================================================================

@dataclass
class TemporalIncentiveAttack:
    """
    Attack 382: Temporal Incentive Attack

    Exploits time-dependent aspects of incentive mechanisms
    to extract value or destabilize the system.

    Attack Strategy:
    1. Identify periodic reward structures
    2. Time contributions to maximize rewards
    3. Create volatility during transition periods
    4. Front-run reward distribution

    Risk: Incentive effectiveness degraded by timing games.
    """

    timing_exploits: List[Dict[str, Any]] = field(default_factory=list)
    temporal_profit: float = 0.0

    def execute(self, system: IncentiveSystem) -> Dict[str, Any]:
        """Execute temporal incentive attack."""
        # Exploit 1: Reward period front-running
        # Assume rewards distributed every 10 rounds
        front_runners = [
            p for p in system.participants.values()
            if p.participant_type == ParticipantType.STRATEGIC
        ][:10]

        for round_num in range(20):
            system.game_state.round_number = round_num

            # Front-run reward distribution
            if round_num % 10 == 9:  # Round before distribution
                for runner in front_runners:
                    # Stack contributions just before distribution
                    runner.historical_utility += system.attestation_reward * 2
                    self.temporal_profit += system.attestation_reward
                    self.timing_exploits.append({
                        "type": "front_run",
                        "round": round_num,
                        "participant": runner.participant_id
                    })

            # Exploit 2: Decay period gaming
            if round_num % 5 == 0:  # Decay checkpoint
                for runner in front_runners:
                    # Minimal activity during decay periods
                    pass

        return {
            "attack_type": "temporal_incentive",
            "front_runners": len(front_runners),
            "timing_exploits": len(self.timing_exploits),
            "temporal_profit": self.temporal_profit,
            "success": self.temporal_profit > 20
        }


class TemporalIncentiveDefense:
    """Defense against temporal incentive attacks."""

    def __init__(self, system: IncentiveSystem):
        self.system = system
        self.activity_history: Dict[str, List[int]] = defaultdict(list)
        self.max_timing_correlation = 0.8

    def detect(self) -> Tuple[bool, List[str]]:
        """Detect temporal gaming patterns."""
        alerts = []
        detected = False

        # Track activity by round
        for pid, participant in self.system.participants.items():
            self.activity_history[pid].append(self.system.game_state.round_number)

        # Check for suspiciously timed activity
        strategic_participants = [
            p for p in self.system.participants.values()
            if p.participant_type == ParticipantType.STRATEGIC
        ]

        for participant in strategic_participants:
            history = self.activity_history.get(participant.participant_id, [])
            if history:
                # Check correlation with reward periods
                reward_period_activity = sum(1 for r in history if r % 10 == 9)
                total_activity = len(history)

                if total_activity > 0:
                    timing_correlation = reward_period_activity / total_activity
                    if timing_correlation > self.max_timing_correlation:
                        alerts.append(
                            f"Timing correlation for {participant.participant_id}: {timing_correlation:.2f}"
                        )
                        detected = True

        return detected, alerts


# =============================================================================
# SIMULATION AND TESTING
# =============================================================================

def run_track_fu_simulations() -> Dict[str, Any]:
    """Run all Track FU attack simulations."""
    results = {}

    print("=" * 60)
    print("TRACK FU: Incentive Mechanism Design Attacks (377-382)")
    print("=" * 60)

    # Attack 377: Free-Rider Equilibrium
    print("\n[Attack 377] Free-Rider Equilibrium Attack...")
    system = IncentiveSystem()
    attack = FreeRiderEquilibriumAttack()
    result = attack.execute(system)
    defense = FreeRiderDefense(system)
    detected, alerts = defense.detect()
    results["377_free_rider_equilibrium"] = {
        "attack_result": result, "detected": detected, "alerts": alerts
    }
    print(f"  Success: {result['success']}, Detected: {detected}")

    # Attack 378: Reward Farming
    print("\n[Attack 378] Reward Farming Attack...")
    system = IncentiveSystem()
    attack = RewardFarmingAttack()
    result = attack.execute(system)
    defense = RewardFarmingDefense(system)
    detected, alerts = defense.detect()
    results["378_reward_farming"] = {
        "attack_result": result, "detected": detected, "alerts": alerts
    }
    print(f"  Success: {result['success']}, Detected: {detected}")

    # Attack 379: Coalition Profit Extraction
    print("\n[Attack 379] Coalition Profit Extraction Attack...")
    system = IncentiveSystem()
    attack = CoalitionProfitAttack()
    result = attack.execute(system)
    defense = CoalitionProfitDefense(system)
    detected, alerts = defense.detect()
    results["379_coalition_profit"] = {
        "attack_result": result, "detected": detected, "alerts": alerts
    }
    print(f"  Success: {result['success']}, Detected: {detected}")

    # Attack 380: Mechanism Gaming
    print("\n[Attack 380] Mechanism Gaming Attack...")
    system = IncentiveSystem()
    attack = MechanismGamingAttack()
    result = attack.execute(system)
    defense = MechanismGamingDefense(system)
    detected, alerts = defense.detect()
    results["380_mechanism_gaming"] = {
        "attack_result": result, "detected": detected, "alerts": alerts
    }
    print(f"  Success: {result['success']}, Detected: {detected}")

    # Attack 381: Information Asymmetry
    print("\n[Attack 381] Information Asymmetry Attack...")
    system = IncentiveSystem()
    attack = InformationAsymmetryAttack()
    result = attack.execute(system)
    defense = InformationAsymmetryDefense(system)
    detected, alerts = defense.detect()
    results["381_information_asymmetry"] = {
        "attack_result": result, "detected": detected, "alerts": alerts
    }
    print(f"  Success: {result['success']}, Detected: {detected}")

    # Attack 382: Temporal Incentive
    print("\n[Attack 382] Temporal Incentive Attack...")
    system = IncentiveSystem()
    attack = TemporalIncentiveAttack()
    result = attack.execute(system)
    defense = TemporalIncentiveDefense(system)
    detected, alerts = defense.detect()
    results["382_temporal_incentive"] = {
        "attack_result": result, "detected": detected, "alerts": alerts
    }
    print(f"  Success: {result['success']}, Detected: {detected}")

    # Summary
    print("\n" + "=" * 60)
    print("TRACK FU SUMMARY")
    print("=" * 60)

    total_attacks = 6
    attacks_detected = sum(1 for r in results.values() if r.get("detected", False))
    detection_rate = attacks_detected / total_attacks * 100

    print(f"Total Attacks: {total_attacks}")
    print(f"Attacks Detected: {attacks_detected}")
    print(f"Detection Rate: {detection_rate:.1f}%")

    results["summary"] = {
        "total_attacks": total_attacks,
        "attacks_detected": attacks_detected,
        "detection_rate": detection_rate
    }

    return results


if __name__ == "__main__":
    results = run_track_fu_simulations()
