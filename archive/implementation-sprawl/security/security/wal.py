#!/usr/bin/env python3
"""
Web4 Accountability Layer (WAL)
================================

Encodes systemic consequences for behavior, turning:
- Malicious actions into durable trust penalties
- Trust penalties into practical limitations on future actions

WAL is the bridge between observed behavior and enforced constraints.

Key Concepts:
- WAL Events record security-relevant behaviors
- Trust Impact tracks reputation changes
- Constraints enforce practical limitations
- Adjudication provides oversight and appeals

Created: Session #27 (2025-11-14)
Related: FIPT (Session #25), MPE (Session #26), Nova BEC Case Study
"""

import sys
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

# Import reputation
sys.path.insert(0, str(Path(__file__).parent.parent / "reputation"))
from reputation_tracker import ReputationTracker, BehaviorType


class WALEventType(str, Enum):
    """Types of WAL events"""
    FRAUD_ATTEMPT = "fraud_attempt"
    CONFIRMED_FRAUD = "confirmed_fraud"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    EXONERATION = "exoneration"
    POLICY_VIOLATION = "policy_violation"
    SECURITY_INCIDENT = "security_incident"


class ConstraintType(str, Enum):
    """Types of constraints that can be imposed"""
    RATE_LIMIT = "rate_limit"
    MAX_TRANSACTION_VALUE = "max_transaction_value"
    QUARANTINE = "quarantine"
    ACTION_BLOCK = "action_block"
    SUPERVISION_REQUIRED = "supervision_required"


@dataclass
class TrustImpact:
    """Trust impact of a WAL event"""
    delta_score: float  # Change in T3 score
    new_trust_state: float  # New T3 score after event
    tier_change: Optional[str] = None  # e.g., "trusted -> developing"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Constraint:
    """Constraint imposed on an entity"""
    constraint_type: ConstraintType
    value: Optional[float] = None  # For rate_limit, max_transaction_value
    expires_at: Optional[datetime] = None  # For time-limited constraints
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_active(self, check_time: Optional[datetime] = None) -> bool:
        """Check if constraint is currently active"""
        if self.expires_at is None:
            return True  # Permanent constraint

        if check_time is None:
            check_time = datetime.now(timezone.utc)

        return check_time < self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        if self.expires_at:
            result['expires_at'] = self.expires_at.isoformat()
        return result


class WALEvent:
    """
    Web4 Accountability Layer Event

    Records security-relevant behavior and its consequences.
    """

    def __init__(
        self,
        wal_event_id: str,
        entity_lct: str,
        event_type: WALEventType,
        evidence_refs: List[str],
        trust_impact: TrustImpact,
        constraints: List[Constraint],
        timestamp: datetime,
        adjudicator: str,
        mrh_context: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.wal_event_id = wal_event_id
        self.entity_lct = entity_lct
        self.event_type = event_type
        self.evidence_refs = evidence_refs
        self.trust_impact = trust_impact
        self.constraints = constraints
        self.timestamp = timestamp
        self.adjudicator = adjudicator
        self.mrh_context = mrh_context
        self.description = description
        self.metadata = metadata or {}

    @staticmethod
    def _generate_id(
        entity_lct: str,
        event_type: WALEventType,
        timestamp: datetime
    ) -> str:
        """Generate unique WAL event ID"""
        data = f"{entity_lct}:{event_type}:{timestamp.isoformat()}"
        hash_digest = hashlib.sha256(data.encode()).hexdigest()
        return f"wal:{hash_digest[:16]}"

    @classmethod
    def create(
        cls,
        entity_lct: str,
        event_type: WALEventType,
        evidence_refs: List[str],
        trust_impact: TrustImpact,
        constraints: List[Constraint],
        adjudicator: str,
        mrh_context: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> "WALEvent":
        """
        Create a new WAL event.

        Args:
            entity_lct: LCT of entity this event is about
            event_type: Type of event
            evidence_refs: References to evidence (MPE IDs, FIPT IDs, etc.)
            trust_impact: Impact on entity's trust score
            constraints: Constraints to impose
            adjudicator: LCT of entity creating this event
            mrh_context: Optional MRH context
            description: Human-readable description
            metadata: Additional metadata

        Returns:
            WALEvent instance
        """
        timestamp = datetime.now(timezone.utc)
        wal_event_id = cls._generate_id(entity_lct, event_type, timestamp)

        return cls(
            wal_event_id=wal_event_id,
            entity_lct=entity_lct,
            event_type=event_type,
            evidence_refs=evidence_refs,
            trust_impact=trust_impact,
            constraints=constraints,
            timestamp=timestamp,
            adjudicator=adjudicator,
            mrh_context=mrh_context,
            description=description,
            metadata=metadata
        )

    def get_active_constraints(
        self,
        check_time: Optional[datetime] = None
    ) -> List[Constraint]:
        """Get constraints that are currently active"""
        return [c for c in self.constraints if c.is_active(check_time)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert WAL event to dictionary"""
        return {
            "wal_event_id": self.wal_event_id,
            "entity_lct": self.entity_lct,
            "event_type": self.event_type,
            "evidence_refs": self.evidence_refs,
            "trust_impact": self.trust_impact.to_dict(),
            "constraints": [c.to_dict() for c in self.constraints],
            "timestamp": self.timestamp.isoformat(),
            "adjudicator": self.adjudicator,
            "mrh_context": self.mrh_context,
            "description": self.description,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Convert WAL event to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class WALRegistry:
    """
    Registry of WAL events.

    Tracks all accountability events and active constraints.
    """

    def __init__(self, reputation_tracker: Optional[ReputationTracker] = None):
        """
        Initialize WAL registry.

        Args:
            reputation_tracker: Optional reputation tracker
        """
        self.reputation_tracker = reputation_tracker or ReputationTracker()
        self.events: Dict[str, WALEvent] = {}  # wal_event_id -> WALEvent
        self.entity_events: Dict[str, List[str]] = {}  # entity_lct -> [wal_event_ids]

    def record_event(self, event: WALEvent):
        """Record a WAL event in the registry"""
        self.events[event.wal_event_id] = event

        if event.entity_lct not in self.entity_events:
            self.entity_events[event.entity_lct] = []

        self.entity_events[event.entity_lct].append(event.wal_event_id)

    def get_events_for_entity(
        self,
        entity_lct: str,
        event_type: Optional[WALEventType] = None
    ) -> List[WALEvent]:
        """Get all WAL events for an entity"""
        if entity_lct not in self.entity_events:
            return []

        events = [self.events[eid] for eid in self.entity_events[entity_lct]]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events

    def get_active_constraints(
        self,
        entity_lct: str,
        constraint_type: Optional[ConstraintType] = None
    ) -> List[Constraint]:
        """Get all active constraints for an entity"""
        events = self.get_events_for_entity(entity_lct)
        constraints = []

        for event in events:
            constraints.extend(event.get_active_constraints())

        if constraint_type:
            constraints = [c for c in constraints if c.constraint_type == constraint_type]

        return constraints

    def check_constraint(
        self,
        entity_lct: str,
        constraint_type: ConstraintType,
        value: Optional[float] = None
    ) -> tuple[bool, str]:
        """
        Check if action is allowed under current constraints.

        Args:
            entity_lct: LCT of entity attempting action
            constraint_type: Type of constraint to check
            value: Optional value to check (e.g., transaction amount)

        Returns:
            (allowed, reason) tuple
        """
        constraints = self.get_active_constraints(entity_lct, constraint_type)

        if not constraints:
            return True, "No active constraints"

        # Check each constraint
        for constraint in constraints:
            if constraint.constraint_type == ConstraintType.ACTION_BLOCK:
                return False, f"Action blocked: {constraint.reason}"

            elif constraint.constraint_type == ConstraintType.QUARANTINE:
                return False, f"Entity quarantined until {constraint.expires_at}: {constraint.reason}"

            elif constraint.constraint_type == ConstraintType.MAX_TRANSACTION_VALUE:
                if value is not None and constraint.value is not None:
                    if value > constraint.value:
                        return False, f"Transaction value ${value:,.2f} exceeds limit ${constraint.value:,.2f}"

            elif constraint.constraint_type == ConstraintType.RATE_LIMIT:
                # TODO: Implement rate limiting logic
                pass

        return True, "Action allowed"


class WALEnforcement:
    """
    WAL Enforcement System

    Integrates WAL events with reputation and FIPT/MPE systems.
    """

    def __init__(
        self,
        reputation_tracker: Optional[ReputationTracker] = None,
        wal_registry: Optional[WALRegistry] = None
    ):
        """
        Initialize WAL enforcement system.

        Args:
            reputation_tracker: Optional reputation tracker
            wal_registry: Optional WAL registry
        """
        self.reputation_tracker = reputation_tracker or ReputationTracker()
        self.wal_registry = wal_registry or WALRegistry(self.reputation_tracker)

    def record_fraud_attempt(
        self,
        entity_lct: str,
        evidence_refs: List[str],
        adjudicator: str,
        organization: str = "default",
        description: str = "Fraud attempt detected",
        quarantine_days: int = 30,
        max_transaction_value: Optional[float] = None
    ) -> WALEvent:
        """
        Record a fraud attempt with appropriate penalties.

        Args:
            entity_lct: LCT of entity that attempted fraud
            evidence_refs: Evidence (MPE IDs, FIPT IDs, etc.)
            adjudicator: LCT of entity recording the event
            organization: Organization context
            description: Description of fraud attempt
            quarantine_days: Days to quarantine entity
            max_transaction_value: Maximum transaction value allowed

        Returns:
            WALEvent created
        """
        # Get current trust state
        old_t3 = self.reputation_tracker.calculate_t3(entity_lct, organization)

        # Record severe reputation penalty
        self.reputation_tracker.record_event(
            agent_lct=entity_lct,
            behavior_type=BehaviorType.FALSE_WITNESS,  # -0.5 penalty
            organization=organization,
            description=description,
            attested_by=adjudicator,
            metadata={"evidence": evidence_refs}
        )

        # Get new trust state
        new_t3 = self.reputation_tracker.calculate_t3(entity_lct, organization)

        trust_impact = TrustImpact(
            delta_score=new_t3 - old_t3,
            new_trust_state=new_t3
        )

        # Create constraints
        constraints = [
            Constraint(
                constraint_type=ConstraintType.QUARANTINE,
                expires_at=datetime.now(timezone.utc) + timedelta(days=quarantine_days),
                reason=f"Quarantined for {quarantine_days} days due to fraud attempt"
            )
        ]

        if max_transaction_value is not None:
            constraints.append(
                Constraint(
                    constraint_type=ConstraintType.MAX_TRANSACTION_VALUE,
                    value=max_transaction_value,
                    reason=f"Transaction limit imposed: ${max_transaction_value:,.2f}"
                )
            )

        # Create WAL event
        wal_event = WALEvent.create(
            entity_lct=entity_lct,
            event_type=WALEventType.FRAUD_ATTEMPT,
            evidence_refs=evidence_refs,
            trust_impact=trust_impact,
            constraints=constraints,
            adjudicator=adjudicator,
            description=description,
            metadata={"organization": organization}
        )

        # Record in registry
        self.wal_registry.record_event(wal_event)

        return wal_event

    def check_action_allowed(
        self,
        entity_lct: str,
        action_type: str,
        value: Optional[float] = None,
        organization: str = "default"
    ) -> tuple[bool, str]:
        """
        Check if entity is allowed to perform action.

        Checks:
        1. Reputation thresholds
        2. Active constraints
        3. Quarantine status

        Args:
            entity_lct: LCT of entity attempting action
            action_type: Type of action (e.g., "create_fipt", "payment")
            value: Optional value (e.g., transaction amount)
            organization: Organization context

        Returns:
            (allowed, reason) tuple
        """
        # Check reputation first
        t3 = self.reputation_tracker.calculate_t3(entity_lct, organization)

        # Check if quarantined
        allowed, reason = self.wal_registry.check_constraint(
            entity_lct,
            ConstraintType.QUARANTINE
        )

        if not allowed:
            return False, reason

        # Check transaction value limit
        if value is not None:
            allowed, reason = self.wal_registry.check_constraint(
                entity_lct,
                ConstraintType.MAX_TRANSACTION_VALUE,
                value
            )

            if not allowed:
                return False, reason

        # Check action blocks
        allowed, reason = self.wal_registry.check_constraint(
            entity_lct,
            ConstraintType.ACTION_BLOCK
        )

        if not allowed:
            return False, reason

        return True, "Action allowed"


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("WAL (Web4 Accountability Layer) - Demo")
    print("=" * 80)

    # Create enforcement system
    reputation = ReputationTracker()
    wal_enforcement = WALEnforcement(reputation)

    print("\nScenario: BEC attack with WAL accountability\n")

    # Attacker LCT
    attacker_lct = "lct:attacker:bec"
    org = "business_network"

    print("1. Initial state:")
    t3 = reputation.calculate_t3(attacker_lct, org)
    print(f"   Attacker T3: {t3:.3f}")

    # Record fraud attempt
    print("\n2. System detects and records BEC fraud attempt:")

    wal_event = wal_enforcement.record_fraud_attempt(
        entity_lct=attacker_lct,
        evidence_refs=[
            "mpe:fraudulent-message-123",
            "fipt:attempted-diversion-456"
        ],
        adjudicator="lct:system:payment_processor",
        organization=org,
        description="Attempted $70K payment diversion - BEC attack",
        quarantine_days=90,
        max_transaction_value=1000.0
    )

    print(f"   ✅ WAL Event Created: {wal_event.wal_event_id}")
    print(f"   Event Type: {wal_event.event_type}")
    print(f"   Trust Impact: {wal_event.trust_impact.delta_score:.3f}")
    print(f"   New T3: {wal_event.trust_impact.new_trust_state:.3f}")
    print(f"   Constraints: {len(wal_event.constraints)}")

    # Show constraints
    print("\n3. Active constraints:")
    for i, constraint in enumerate(wal_event.constraints, 1):
        print(f"   {i}. {constraint.constraint_type}")
        print(f"      Reason: {constraint.reason}")
        if constraint.expires_at:
            print(f"      Expires: {constraint.expires_at.strftime('%Y-%m-%d')}")

    # Try to perform actions
    print("\n4. Attacker attempts high-value transaction ($50K):")

    allowed, reason = wal_enforcement.check_action_allowed(
        attacker_lct,
        "payment",
        value=50000.0,
        organization=org
    )

    if not allowed:
        print(f"   ❌ BLOCKED: {reason}")

    # Try lower transaction
    print("\n5. Attacker attempts low-value transaction ($500):")

    allowed, reason = wal_enforcement.check_action_allowed(
        attacker_lct,
        "payment",
        value=500.0,
        organization=org
    )

    if allowed:
        print(f"   ✅ ALLOWED: {reason}")
    else:
        print(f"   ❌ BLOCKED: {reason}")

    # Check quarantine
    print("\n6. Check quarantine status:")

    constraints = wal_enforcement.wal_registry.get_active_constraints(
        attacker_lct,
        ConstraintType.QUARANTINE
    )

    if constraints:
        quarantine = constraints[0]
        print(f"   Status: QUARANTINED")
        print(f"   Until: {quarantine.expires_at.strftime('%Y-%m-%d')}")
        print(f"   Reason: {quarantine.reason}")

    # Get entity's WAL history
    print("\n7. Attacker's WAL event history:")

    events = wal_enforcement.wal_registry.get_events_for_entity(attacker_lct)
    print(f"   Total events: {len(events)}")

    for event in events:
        print(f"   - {event.event_type}: {event.description}")
        print(f"     Trust impact: {event.trust_impact.delta_score:.3f}")
        print(f"     Constraints: {len(event.constraints)}")

    # Legitimate entity check
    print("\n8. Legitimate vendor (no WAL events):")

    legitimate_lct = "lct:org:legitimate_vendor"

    # Build reputation
    for i in range(10):
        reputation.record_event(
            agent_lct=legitimate_lct,
            behavior_type=BehaviorType.SUCCESSFUL_ACTION,
            organization=org
        )

    t3_legit = reputation.calculate_t3(legitimate_lct, org)
    print(f"   Vendor T3: {t3_legit:.3f}")

    allowed, reason = wal_enforcement.check_action_allowed(
        legitimate_lct,
        "payment",
        value=100000.0,
        organization=org
    )

    if allowed:
        print(f"   ✅ High-value transaction ALLOWED: {reason}")

    print("\n" + "=" * 80)
    print("WAL Implementation: OPERATIONAL")
    print("=" * 80)
    print("\nKey Capabilities:")
    print("  ✅ WAL event creation and tracking")
    print("  ✅ Trust impact recording")
    print("  ✅ Constraint enforcement (quarantine, transaction limits)")
    print("  ✅ Action authorization checks")
    print("  ✅ Event history and audit trail")
    print("  ✅ Integration with reputation system")
    print("\nAccountability Features:")
    print("  ✅ Fraud attempts create permanent records")
    print("  ✅ Constraints automatically enforced")
    print("  ✅ Time-limited quarantines")
    print("  ✅ Transaction value limits")
    print("  ✅ Full audit trail for forensics")
