"""
T3 (Trust Tensor) Tracker - Agent Reputation System

Implements the T3 tensor for agent reputation tracking in Web4 authorization system.

T3 Dimensions:
- **Talent**: Inherent capability (success rate, quality of outcomes)
- **Training**: Experience over time (transaction count, domain expertise)
- **Temperament**: Reliability and consistency (behavioral variance, adherence to constraints)

Key Features:
- Per-agent T3 score tracking (0.0-1.0 for each dimension)
- Dynamic updates based on transaction outcomes
- Historical performance tracking
- Integration with authorization decisions
- Persistent storage (JSON)

Closes Critical Gap:
- Whitepaper describes T3 tensors as fundamental trust mechanism
- Previously 0% implemented
- This provides foundation for reputation-based authorization

Usage:
    tracker = T3Tracker(storage_path="t3_scores.json")

    # Initialize agent with baseline scores
    tracker.create_profile("agent-001", initial_talent=0.7, initial_training=0.5, initial_temperament=0.8)

    # Record successful transaction
    tracker.record_transaction(
        agent_id="agent-001",
        transaction_type="purchase",
        success=True,
        amount=50.00,
        within_constraints=True,
        quality_score=0.9
    )

    # Get current T3 scores
    scores = tracker.get_t3_scores("agent-001")
    # Returns: {"talent": 0.72, "training": 0.52, "temperament": 0.81}

    # Get composite trust score (weighted average)
    trust_score = tracker.get_composite_trust("agent-001")
    # Returns: 0.68 (weighted: talent=30%, training=50%, temperament=20%)

Integration with Authorization:
    # Before authorizing purchase
    trust_score = t3_tracker.get_composite_trust(agent_id)
    if trust_score < required_trust_threshold:
        # Require additional approval or deny
        pass

Author: Claude (Anthropic AI), autonomous Web4 development
Date: November 12, 2025
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import statistics


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TransactionRecord:
    """Record of a single transaction for reputation calculation."""
    timestamp: str
    transaction_type: str  # "purchase", "refund", "approval_response", etc.
    success: bool
    amount: float
    within_constraints: bool  # Did agent respect spending limits?
    quality_score: Optional[float] = None  # 0.0-1.0, if applicable
    notes: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


@dataclass
class T3Profile:
    """T3 tensor profile for an agent."""
    agent_id: str

    # T3 Scores (0.0 - 1.0)
    talent: float = 0.5  # Capability - success rate, quality
    training: float = 0.5  # Experience - grows with transactions
    temperament: float = 0.5  # Reliability - consistency, constraint adherence

    # Historical data
    transaction_history: List[Dict] = field(default_factory=list)
    created_at: str = ""
    last_updated: str = ""

    # Statistics
    total_transactions: int = 0
    successful_transactions: int = 0
    constraint_violations: int = 0
    total_value_handled: float = 0.0

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        if not self.created_at:
            self.created_at = now
        if not self.last_updated:
            self.last_updated = now

    def get_success_rate(self) -> float:
        """Calculate success rate for talent assessment."""
        if self.total_transactions == 0:
            return 0.5  # Neutral starting point
        return self.successful_transactions / self.total_transactions

    def get_constraint_adherence_rate(self) -> float:
        """Calculate constraint adherence for temperament assessment."""
        if self.total_transactions == 0:
            return 0.5  # Neutral starting point
        violations_rate = self.constraint_violations / self.total_transactions
        return 1.0 - violations_rate  # Higher is better

    def get_experience_level(self) -> float:
        """Calculate experience level for training assessment."""
        # Experience grows logarithmically - early transactions matter more
        # Cap at 1.0 after ~100 transactions
        if self.total_transactions == 0:
            return 0.0

        # Logarithmic scale: log(1 + n) / log(101)
        # 0 trans → 0.0, 10 trans → ~0.5, 100 trans → ~1.0
        import math
        experience = math.log(1 + self.total_transactions) / math.log(101)
        return min(1.0, experience)

    def get_behavioral_consistency(self) -> float:
        """Calculate behavioral consistency for temperament assessment."""
        if len(self.transaction_history) < 3:
            return 0.5  # Need history for variance calculation

        # Calculate variance in decision quality
        recent_quality_scores = [
            t.get('quality_score', 0.5)
            for t in self.transaction_history[-20:]  # Last 20 transactions
            if t.get('quality_score') is not None
        ]

        if len(recent_quality_scores) < 2:
            return 0.5

        # Low variance = high consistency
        variance = statistics.variance(recent_quality_scores)

        # Convert variance (0.0-0.25) to consistency score (1.0-0.0)
        # Lower variance → higher consistency
        consistency = max(0.0, 1.0 - (variance * 4))  # Scale variance to 0-1
        return consistency


class T3Tracker:
    """
    T3 Tensor Tracker for agent reputation management.

    Tracks three dimensions of agent trustworthiness:
    - Talent: Capability and success rate
    - Training: Experience and domain expertise
    - Temperament: Reliability and behavioral consistency
    """

    # Default weights for composite trust score
    DEFAULT_WEIGHTS = {
        "talent": 0.30,     # 30% - inherent capability
        "training": 0.50,   # 50% - experience matters most
        "temperament": 0.20  # 20% - consistency/reliability
    }

    def __init__(self, storage_path: str = "t3_profiles.json"):
        """
        Initialize T3 tracker.

        Args:
            storage_path: Path to JSON file for persistent storage
        """
        self.storage_path = Path(storage_path)
        self.profiles: Dict[str, T3Profile] = {}
        self._load_profiles()

    def _load_profiles(self):
        """Load T3 profiles from storage."""
        if not self.storage_path.exists():
            logger.info(f"No existing T3 profiles found at {self.storage_path}")
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for agent_id, profile_dict in data.items():
                    # Convert dict back to T3Profile
                    self.profiles[agent_id] = T3Profile(
                        agent_id=agent_id,
                        talent=profile_dict.get('talent', 0.5),
                        training=profile_dict.get('training', 0.5),
                        temperament=profile_dict.get('temperament', 0.5),
                        transaction_history=profile_dict.get('transaction_history', []),
                        created_at=profile_dict.get('created_at', ''),
                        last_updated=profile_dict.get('last_updated', ''),
                        total_transactions=profile_dict.get('total_transactions', 0),
                        successful_transactions=profile_dict.get('successful_transactions', 0),
                        constraint_violations=profile_dict.get('constraint_violations', 0),
                        total_value_handled=profile_dict.get('total_value_handled', 0.0)
                    )
            logger.info(f"Loaded {len(self.profiles)} T3 profiles from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load T3 profiles: {e}")
            self.profiles = {}

    def _save_profiles(self):
        """Save T3 profiles to storage."""
        try:
            # Convert profiles to dict
            data = {
                agent_id: asdict(profile)
                for agent_id, profile in self.profiles.items()
            }

            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.profiles)} T3 profiles to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save T3 profiles: {e}")

    def create_profile(
        self,
        agent_id: str,
        initial_talent: float = 0.5,
        initial_training: float = 0.5,
        initial_temperament: float = 0.5
    ) -> T3Profile:
        """
        Create new T3 profile for an agent.

        Args:
            agent_id: Unique agent identifier
            initial_talent: Starting talent score (0.0-1.0)
            initial_training: Starting training score (0.0-1.0)
            initial_temperament: Starting temperament score (0.0-1.0)

        Returns:
            Created T3Profile
        """
        # Validate scores
        for score in [initial_talent, initial_training, initial_temperament]:
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"T3 scores must be between 0.0 and 1.0, got {score}")

        if agent_id in self.profiles:
            logger.warning(f"Profile already exists for {agent_id}, returning existing")
            return self.profiles[agent_id]

        profile = T3Profile(
            agent_id=agent_id,
            talent=initial_talent,
            training=initial_training,
            temperament=initial_temperament
        )

        self.profiles[agent_id] = profile
        self._save_profiles()

        logger.info(f"Created T3 profile for {agent_id}: T={initial_talent:.2f}, "
                   f"T={initial_training:.2f}, T={initial_temperament:.2f}")

        return profile

    def get_profile(self, agent_id: str) -> Optional[T3Profile]:
        """
        Get T3 profile for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            T3Profile if exists, None otherwise
        """
        return self.profiles.get(agent_id)

    def record_transaction(
        self,
        agent_id: str,
        transaction_type: str,
        success: bool,
        amount: float = 0.0,
        within_constraints: bool = True,
        quality_score: Optional[float] = None,
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Record a transaction and update T3 scores.

        Args:
            agent_id: Agent identifier
            transaction_type: Type of transaction ("purchase", "refund", etc.)
            success: Whether transaction was successful
            amount: Transaction amount (for value tracking)
            within_constraints: Whether agent respected spending limits
            quality_score: Optional quality assessment (0.0-1.0)
            notes: Optional notes about transaction

        Returns:
            Tuple of (success, message)
        """
        # Get or create profile
        profile = self.profiles.get(agent_id)
        if not profile:
            logger.info(f"Creating new T3 profile for {agent_id} (first transaction)")
            profile = self.create_profile(agent_id)

        # Create transaction record
        record = TransactionRecord(
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            transaction_type=transaction_type,
            success=success,
            amount=amount,
            within_constraints=within_constraints,
            quality_score=quality_score,
            notes=notes
        )

        # Update statistics
        profile.total_transactions += 1
        if success:
            profile.successful_transactions += 1
        if not within_constraints:
            profile.constraint_violations += 1
        profile.total_value_handled += amount

        # Add to history (keep last 100 transactions)
        profile.transaction_history.append(asdict(record))
        if len(profile.transaction_history) > 100:
            profile.transaction_history = profile.transaction_history[-100:]

        # Update T3 scores
        profile.talent = self._calculate_talent(profile)
        profile.training = self._calculate_training(profile)
        profile.temperament = self._calculate_temperament(profile)

        # Update timestamp
        profile.last_updated = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        # Save
        self._save_profiles()

        logger.info(f"Recorded transaction for {agent_id}: {transaction_type} "
                   f"(success={success}, T3=[{profile.talent:.3f}, {profile.training:.3f}, {profile.temperament:.3f}])")

        return True, f"Transaction recorded, T3 updated"

    def _calculate_talent(self, profile: T3Profile) -> float:
        """
        Calculate talent score based on success rate and quality.

        Talent = 0.7 * success_rate + 0.3 * avg_quality
        """
        success_rate = profile.get_success_rate()

        # Calculate average quality from recent transactions
        recent_quality_scores = [
            t.get('quality_score')
            for t in profile.transaction_history[-20:]
            if t.get('quality_score') is not None
        ]

        if recent_quality_scores:
            avg_quality = statistics.mean(recent_quality_scores)
        else:
            avg_quality = 0.5  # Neutral default

        # Weighted combination
        talent = 0.7 * success_rate + 0.3 * avg_quality

        return max(0.0, min(1.0, talent))  # Clamp to [0,1]

    def _calculate_training(self, profile: T3Profile) -> float:
        """
        Calculate training score based on experience and domain expertise.

        Training grows with transaction count (logarithmically).
        """
        return profile.get_experience_level()

    def _calculate_temperament(self, profile: T3Profile) -> float:
        """
        Calculate temperament score based on reliability and consistency.

        Temperament = 0.6 * constraint_adherence + 0.4 * behavioral_consistency
        """
        constraint_adherence = profile.get_constraint_adherence_rate()
        behavioral_consistency = profile.get_behavioral_consistency()

        # Weighted combination
        temperament = 0.6 * constraint_adherence + 0.4 * behavioral_consistency

        return max(0.0, min(1.0, temperament))  # Clamp to [0,1]

    def get_t3_scores(self, agent_id: str) -> Optional[Dict[str, float]]:
        """
        Get current T3 scores for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Dict with talent, training, temperament scores, or None if no profile
        """
        profile = self.profiles.get(agent_id)
        if not profile:
            return None

        return {
            "talent": profile.talent,
            "training": profile.training,
            "temperament": profile.temperament
        }

    def get_composite_trust(
        self,
        agent_id: str,
        weights: Optional[Dict[str, float]] = None
    ) -> Optional[float]:
        """
        Calculate composite trust score as weighted average of T3 dimensions.

        Args:
            agent_id: Agent identifier
            weights: Optional custom weights (default: talent=30%, training=50%, temperament=20%)

        Returns:
            Composite trust score (0.0-1.0), or None if no profile
        """
        profile = self.profiles.get(agent_id)
        if not profile:
            return None

        if weights is None:
            weights = self.DEFAULT_WEIGHTS

        # Validate weights sum to 1.0
        weight_sum = sum(weights.values())
        if not (0.99 <= weight_sum <= 1.01):  # Allow small floating point error
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

        composite = (
            weights.get("talent", 0.3) * profile.talent +
            weights.get("training", 0.5) * profile.training +
            weights.get("temperament", 0.2) * profile.temperament
        )

        return max(0.0, min(1.0, composite))

    def get_stats(self, agent_id: str) -> Optional[Dict]:
        """
        Get comprehensive statistics for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Dict with all statistics, or None if no profile
        """
        profile = self.profiles.get(agent_id)
        if not profile:
            return None

        return {
            "agent_id": agent_id,
            "t3_scores": {
                "talent": profile.talent,
                "training": profile.training,
                "temperament": profile.temperament,
                "composite": self.get_composite_trust(agent_id)
            },
            "statistics": {
                "total_transactions": profile.total_transactions,
                "successful_transactions": profile.successful_transactions,
                "success_rate": profile.get_success_rate(),
                "constraint_violations": profile.constraint_violations,
                "constraint_adherence_rate": profile.get_constraint_adherence_rate(),
                "total_value_handled": profile.total_value_handled,
                "experience_level": profile.get_experience_level()
            },
            "timestamps": {
                "created_at": profile.created_at,
                "last_updated": profile.last_updated
            }
        }

    def list_profiles(self) -> List[str]:
        """Get list of all agent IDs with T3 profiles."""
        return list(self.profiles.keys())

    def get_all_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all agents.

        Returns:
            Dict mapping agent_id to stats
        """
        return {
            agent_id: self.get_stats(agent_id)
            for agent_id in self.profiles.keys()
        }


# Example usage
if __name__ == "__main__":
    # Create tracker
    tracker = T3Tracker(storage_path="demo_t3_profiles.json")

    # Create profile for agent
    tracker.create_profile("agent-claude-001", initial_talent=0.7, initial_training=0.5, initial_temperament=0.8)

    # Simulate transactions
    print("\\nSimulating transactions...")
    tracker.record_transaction("agent-claude-001", "purchase", True, 45.00, True, 0.9)
    tracker.record_transaction("agent-claude-001", "purchase", True, 25.00, True, 0.85)
    tracker.record_transaction("agent-claude-001", "purchase", True, 75.00, True, 0.95)
    tracker.record_transaction("agent-claude-001", "purchase", False, 150.00, False, 0.3)  # Failed, exceeded limit
    tracker.record_transaction("agent-claude-001", "purchase", True, 30.00, True, 0.9)

    # Get stats
    stats = tracker.get_stats("agent-claude-001")
    print(f"\\nAgent Statistics:")
    print(f"  T3 Scores: Talent={stats['t3_scores']['talent']:.3f}, "
          f"Training={stats['t3_scores']['training']:.3f}, "
          f"Temperament={stats['t3_scores']['temperament']:.3f}")
    print(f"  Composite Trust: {stats['t3_scores']['composite']:.3f}")
    print(f"  Transactions: {stats['statistics']['total_transactions']} "
          f"({stats['statistics']['successful_transactions']} successful)")
    print(f"  Success Rate: {stats['statistics']['success_rate']:.1%}")
    print(f"  Constraint Adherence: {stats['statistics']['constraint_adherence_rate']:.1%}")
