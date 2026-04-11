#!/usr/bin/env python3
"""
T3/V3 Privacy Governance Reference Implementation
Spec: web4-standard/T3V3_PRIVACY_GOVERNANCE.md

Core principle: No Free Trust Queries — trust information has value,
accessing it requires ATP commitment.

Key features:
- ATP-staked trust queries (no free lookups)
- Role-contextual isolation (never global scores)
- Stake resolution: engage→returned, forfeit→to target, declined→returned
- Trust disclosure levels: NONE/BINARY/RANGE/PRECISE
- Anti-fishing protections: rate limits, pattern detection, suspensions
- Need-to-know validation (legitimate interaction intent required)
- Query pricing: sensitivity × scarcity × trust premium × demand
- Privacy-preserving aggregates (anonymous statistics only)
- Entity rights: know, refuse, expire, context
- Attack mitigations: sybil, manipulation, surveillance
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# Section 1: Core Data Structures
# ============================================================

class TrustDisclosure(IntEnum):
    """Trust disclosure levels — higher stake = more detail."""
    NONE = 0      # No trust information
    BINARY = 1    # Qualified/Not qualified
    RANGE = 2     # Low/Medium/High
    PRECISE = 3   # Exact T3 tensor values

    @staticmethod
    def for_stake(stake: float) -> "TrustDisclosure":
        if stake < 10:
            return TrustDisclosure.NONE
        elif stake < 50:
            return TrustDisclosure.BINARY
        elif stake < 100:
            return TrustDisclosure.RANGE
        else:
            return TrustDisclosure.PRECISE


class RoleSensitivity(Enum):
    """Role sensitivity categories with ATP stake minimums."""
    PUBLIC_SERVICE = ("public_service", 10, 0.1)
    PROFESSIONAL = ("professional", 50, 0.3)
    SPECIALIST = ("specialist", 100, 0.5)
    CRITICAL = ("critical", 500, 0.8)
    GOVERNANCE = ("governance", 1000, 1.0)

    def __init__(self, label: str, min_stake: int, sensitivity_score: float):
        self.label = label
        self.min_stake = min_stake
        self.sensitivity_score = sensitivity_score


class QueryOutcome(Enum):
    """Possible outcomes for a trust query."""
    ENGAGED = "engaged"           # Querier engaged target → 90% returned
    FORFEITED = "forfeited"       # Querier didn't engage → 100% to target
    DECLINED = "declined"         # Target declined → 100% returned
    REJECTED = "rejected"         # No need to know → 95% returned


@dataclass
class T3Tensor:
    """Role-contextual trust tensor."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def to_binary(self) -> str:
        """Binary disclosure: qualified or not."""
        return "qualified" if self.composite >= 0.5 else "not_qualified"

    def to_range(self) -> str:
        """Range disclosure: Low/Medium/High."""
        c = self.composite
        if c < 0.33:
            return "low"
        elif c < 0.67:
            return "medium"
        else:
            return "high"

    def to_precise(self) -> Dict[str, float]:
        """Precise disclosure: exact values."""
        return {
            "talent": round(self.talent, 4),
            "training": round(self.training, 4),
            "temperament": round(self.temperament, 4),
            "composite": round(self.composite, 4),
        }

    def disclose(self, level: TrustDisclosure) -> Any:
        """Return trust data at the specified disclosure level."""
        if level == TrustDisclosure.NONE:
            return None
        elif level == TrustDisclosure.BINARY:
            return self.to_binary()
        elif level == TrustDisclosure.RANGE:
            return self.to_range()
        else:
            return self.to_precise()


@dataclass
class Role:
    """A Web4 role with sensitivity classification."""
    role_id: str = ""
    name: str = ""
    sensitivity: RoleSensitivity = RoleSensitivity.PUBLIC_SERVICE

    def __post_init__(self):
        if not self.role_id:
            self.role_id = f"web4:{self.name}"


@dataclass
class Entity:
    """An entity with role-contextual trust (never global scores)."""
    lct_id: str = ""
    atp_balance: float = 1000.0
    atp_locked: float = 0.0
    role_trust: Dict[str, T3Tensor] = field(default_factory=dict)
    # Privacy rights
    blocked_queriers: Set[str] = field(default_factory=set)
    trust_history_max_days: int = 365  # Right to Expire
    query_suspended_until: Optional[str] = None

    @property
    def atp_available(self) -> float:
        return self.atp_balance - self.atp_locked

    def lock_atp(self, amount: float) -> bool:
        if self.atp_available < amount:
            return False
        self.atp_locked += amount
        return True

    def unlock_atp(self, amount: float):
        self.atp_locked = max(0, self.atp_locked - amount)

    def deduct_atp(self, amount: float):
        """Permanently consume ATP (fee/forfeit)."""
        self.atp_locked = max(0, self.atp_locked - amount)
        self.atp_balance -= amount

    def receive_atp(self, amount: float):
        self.atp_balance += amount

    def is_suspended(self) -> bool:
        if not self.query_suspended_until:
            return False
        sus_time = datetime.fromisoformat(self.query_suspended_until)
        return datetime.now(timezone.utc) < sus_time

    def get_trust_in_role(self, role_id: str) -> Optional[T3Tensor]:
        return self.role_trust.get(role_id)

    def set_trust_in_role(self, role_id: str, t3: T3Tensor):
        self.role_trust[role_id] = t3

    def average_t3_in_role(self, role_id: str) -> float:
        t3 = self.role_trust.get(role_id)
        return t3.composite if t3 else 0.0


# ============================================================
# Section 2: Trust Query Protocol
# ============================================================

@dataclass
class TrustQueryRequest:
    """A request to query trust information."""
    query_id: str = ""
    querier_id: str = ""
    target_id: str = ""
    role_id: str = ""
    intended_interaction: str = ""
    atp_stake: float = 0.0
    validity_seconds: int = 3600
    justification: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.query_id:
            self.query_id = f"tq:{uuid.uuid4().hex[:12]}"


@dataclass
class TrustQueryResponse:
    """Response to a trust query."""
    query_id: str = ""
    status: str = "OK"
    reason: str = ""
    disclosure_level: TrustDisclosure = TrustDisclosure.NONE
    trust_data: Any = None
    stake_locked: float = 0.0
    stake_returned: float = 0.0
    must_engage_by: str = ""
    engagement_deadline: Optional[str] = None


@dataclass
class QueryLogEntry:
    """Audit log entry for a trust query."""
    query_id: str = ""
    querier_id: str = ""
    target_id: str = ""
    role_id: str = ""
    timestamp: str = ""
    atp_staked: float = 0.0
    outcome: str = "pending"
    disclosure_level: int = 0
    resolved_at: Optional[str] = None


@dataclass
class EngagementExpectation:
    """Tracks expected engagement after a trust query."""
    query_id: str = ""
    querier_id: str = ""
    target_id: str = ""
    role_id: str = ""
    stake: float = 0.0
    deadline: str = ""
    resolved: bool = False
    outcome: Optional[QueryOutcome] = None


# ============================================================
# Section 3: Anti-Fishing & Rate Limiting
# ============================================================

@dataclass
class FishingDetector:
    """Detects trust query fishing patterns."""
    queries_per_hour_limit: int = 10
    unique_targets_per_day_limit: int = 50
    max_stake_per_query: float = 1000.0
    suspension_duration_hours: int = 24
    fishing_penalty_atp: float = 500.0

    # Tracking
    hourly_counts: Dict[str, List[str]] = field(default_factory=dict)  # entity → [timestamps]
    daily_targets: Dict[str, Set[str]] = field(default_factory=dict)   # entity → {targets}
    engagement_history: Dict[str, List[bool]] = field(default_factory=dict)  # entity → [engaged?]
    role_query_history: Dict[str, Dict[str, Set[str]]] = field(default_factory=dict)  # entity → {target → {roles}}

    def record_query(self, querier_id: str, target_id: str, role_id: str):
        now = datetime.now(timezone.utc).isoformat()
        # Hourly tracking
        if querier_id not in self.hourly_counts:
            self.hourly_counts[querier_id] = []
        self.hourly_counts[querier_id].append(now)
        # Daily targets
        if querier_id not in self.daily_targets:
            self.daily_targets[querier_id] = set()
        self.daily_targets[querier_id].add(target_id)
        # Role shopping tracking
        if querier_id not in self.role_query_history:
            self.role_query_history[querier_id] = {}
        if target_id not in self.role_query_history[querier_id]:
            self.role_query_history[querier_id][target_id] = set()
        self.role_query_history[querier_id][target_id].add(role_id)

    def record_engagement(self, querier_id: str, engaged: bool):
        if querier_id not in self.engagement_history:
            self.engagement_history[querier_id] = []
        self.engagement_history[querier_id].append(engaged)

    def check_rate_limit(self, querier_id: str) -> Tuple[bool, str]:
        """Check if querier exceeds rate limit."""
        counts = self.hourly_counts.get(querier_id, [])
        # Count queries in last hour
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        recent = [t for t in counts if t > cutoff]
        if len(recent) >= self.queries_per_hour_limit:
            return False, f"Rate limit: {len(recent)}/{self.queries_per_hour_limit} queries/hour"
        return True, ""

    def check_target_limit(self, querier_id: str) -> Tuple[bool, str]:
        """Check unique targets per day limit."""
        targets = self.daily_targets.get(querier_id, set())
        if len(targets) >= self.unique_targets_per_day_limit:
            return False, f"Target limit: {len(targets)}/{self.unique_targets_per_day_limit} unique targets/day"
        return True, ""

    def many_queries_no_engagement(self, querier_id: str) -> bool:
        """Pattern: querying trust but never engaging."""
        history = self.engagement_history.get(querier_id, [])
        if len(history) < 5:
            return False
        recent = history[-10:]  # Last 10 queries
        engagement_rate = sum(1 for e in recent if e) / len(recent)
        return engagement_rate < 0.2  # < 20% engagement is suspicious

    def role_shopping(self, querier_id: str) -> bool:
        """Pattern: querying same target for many different roles."""
        targets = self.role_query_history.get(querier_id, {})
        for target, roles in targets.items():
            if len(roles) >= 5:  # 5+ different roles for same target
                return True
        return False

    def detect_fishing(self, querier_id: str) -> Tuple[bool, List[str]]:
        """Run all fishing detection patterns."""
        patterns = []
        if self.many_queries_no_engagement(querier_id):
            patterns.append("many_queries_no_engagement")
        if self.role_shopping(querier_id):
            patterns.append("role_shopping")
        return len(patterns) > 0, patterns


# ============================================================
# Section 4: Query Pricing & Economics
# ============================================================

@dataclass
class MarketDemand:
    """Market demand tracking for roles."""
    role_demand: Dict[str, float] = field(default_factory=dict)
    role_entity_counts: Dict[str, int] = field(default_factory=dict)

    def get_demand(self, role_id: str) -> float:
        return self.role_demand.get(role_id, 1.0)

    def get_entity_count(self, role_id: str) -> int:
        return max(1, self.role_entity_counts.get(role_id, 1))


def calculate_query_price(
    role: Role,
    target: Entity,
    market: MarketDemand,
) -> float:
    """Calculate ATP price for a trust query.

    Price = base × scarcity × trust_premium × demand
    """
    base_price = role.sensitivity.sensitivity_score * 10

    # Scarce expertise costs more
    entity_count = market.get_entity_count(role.role_id)
    scarcity_multiplier = 1.0 / entity_count

    # High-trust entities charge more
    trust_premium = max(0.1, target.average_t3_in_role(role.role_id))

    # Market demand dynamics
    demand_factor = market.get_demand(role.role_id)

    return base_price * scarcity_multiplier * trust_premium * demand_factor


# ============================================================
# Section 5: Need-to-Know Validation
# ============================================================

@dataclass
class NeedToKnowValidator:
    """Validates legitimate need for trust information."""
    # Established relationships
    established_needs: Dict[str, Set[str]] = field(default_factory=dict)  # querier → {targets}
    # Role-interaction mappings (which interactions justify which role queries)
    valid_interactions: Dict[str, Set[str]] = field(default_factory=dict)  # role → {interaction_types}

    def register_need(self, querier_id: str, target_id: str):
        if querier_id not in self.established_needs:
            self.established_needs[querier_id] = set()
        self.established_needs[querier_id].add(target_id)

    def register_valid_interaction(self, role_id: str, interaction: str):
        if role_id not in self.valid_interactions:
            self.valid_interactions[role_id] = set()
        self.valid_interactions[role_id].add(interaction)

    def validate(
        self, querier_id: str, target_id: str, role_id: str, interaction: str
    ) -> Tuple[bool, str]:
        """Check if querier has legitimate need to query target's trust."""
        # Check established need
        needs = self.established_needs.get(querier_id, set())
        if target_id not in needs:
            return False, "No established need for this target"
        # Check interaction validity
        valid = self.valid_interactions.get(role_id, set())
        if valid and interaction not in valid:
            return False, f"Interaction '{interaction}' not valid for role '{role_id}'"
        return True, "Need validated"


# ============================================================
# Section 6: Entity Rights
# ============================================================

@dataclass
class EntityRights:
    """Entity privacy rights management."""

    def right_to_know(self, entity: Entity, query_log: List[QueryLogEntry]) -> List[QueryLogEntry]:
        """Right to Know: who queried entity's trust and for what role."""
        return [e for e in query_log if e.target_id == entity.lct_id]

    def right_to_refuse(self, entity: Entity, querier_id: str):
        """Right to Refuse: block specific queriers."""
        entity.blocked_queriers.add(querier_id)

    def is_blocked(self, entity: Entity, querier_id: str) -> bool:
        return querier_id in entity.blocked_queriers

    def right_to_expire(self, entity: Entity, max_days: int):
        """Right to Expire: set max retention for trust history."""
        entity.trust_history_max_days = max_days

    def expire_old_entries(
        self, entity: Entity, query_log: List[QueryLogEntry]
    ) -> List[QueryLogEntry]:
        """Remove query log entries older than entity's retention limit."""
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=entity.trust_history_max_days)
        ).isoformat()
        return [e for e in query_log if e.timestamp > cutoff or e.target_id != entity.lct_id]


# ============================================================
# Section 7: Privacy-Preserving Aggregates
# ============================================================

@dataclass
class RoleStatistics:
    """Anonymous aggregate statistics — never reveals individual scores."""
    total_entities: int = 0
    average_talent_range: str = ""
    engagement_success_rate: float = 0.0
    typical_stake_min: float = 0.0
    typical_stake_max: float = 0.0
    market_demand: str = "medium"


def compute_role_statistics(
    entities: List[Entity], role_id: str, engagement_logs: List[QueryLogEntry]
) -> RoleStatistics:
    """Compute anonymous aggregate statistics for a role."""
    role_entities = [e for e in entities if role_id in e.role_trust]
    if not role_entities:
        return RoleStatistics()

    # Average talent as range (never exact)
    talents = [e.role_trust[role_id].talent for e in role_entities]
    avg = sum(talents) / len(talents)
    # Round to 0.1 range
    low = round(max(0, avg - 0.1), 1)
    high = round(min(1.0, avg + 0.1), 1)

    # Engagement success rate
    role_logs = [l for l in engagement_logs if l.role_id == role_id and l.outcome != "pending"]
    if role_logs:
        engaged = sum(1 for l in role_logs if l.outcome == QueryOutcome.ENGAGED.value)
        success_rate = engaged / len(role_logs)
    else:
        success_rate = 0.0

    # Demand classification
    if len(role_entities) < 5:
        demand = "high"
    elif len(role_entities) < 20:
        demand = "medium"
    else:
        demand = "low"

    return RoleStatistics(
        total_entities=len(role_entities),
        average_talent_range=f"{low}-{high}",
        engagement_success_rate=round(success_rate, 2),
        typical_stake_min=10.0,
        typical_stake_max=100.0,
        market_demand=demand,
    )


# ============================================================
# Section 8: Trust Query Engine (Orchestrator)
# ============================================================

class TrustQueryEngine:
    """Main orchestrator for trust queries — implements full spec."""

    QUERY_FEE_RATE = 0.10       # 10% query fee on engagement
    FORFEIT_TO_TARGET = 1.00    # 100% to target on forfeit
    DECLINED_RETURN = 1.00      # 100% returned on decline
    REJECTED_PENALTY = 0.05     # 5% penalty on rejection

    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.roles: Dict[str, Role] = {}
        self.query_log: List[QueryLogEntry] = []
        self.expectations: Dict[str, EngagementExpectation] = {}
        self.fishing_detector = FishingDetector()
        self.need_validator = NeedToKnowValidator()
        self.entity_rights = EntityRights()
        self.market = MarketDemand()

    def register_entity(self, entity: Entity):
        self.entities[entity.lct_id] = entity

    def register_role(self, role: Role):
        self.roles[role.role_id] = role

    def query_trust(self, request: TrustQueryRequest) -> TrustQueryResponse:
        """Execute a trust query with full governance checks."""
        querier = self.entities.get(request.querier_id)
        target = self.entities.get(request.target_id)
        role = self.roles.get(request.role_id)

        # Basic validation
        if not querier:
            return TrustQueryResponse(
                query_id=request.query_id, status="ERROR", reason="Querier not found"
            )
        if not target:
            return TrustQueryResponse(
                query_id=request.query_id, status="ERROR", reason="Target not found"
            )
        if not role:
            return TrustQueryResponse(
                query_id=request.query_id, status="ERROR", reason="Role not found"
            )

        # Check suspension
        if querier.is_suspended():
            return TrustQueryResponse(
                query_id=request.query_id, status="SUSPENDED",
                reason="Querier suspended from trust queries"
            )

        # Check entity right to refuse
        if self.entity_rights.is_blocked(target, request.querier_id):
            return TrustQueryResponse(
                query_id=request.query_id, status="BLOCKED",
                reason="Target has blocked this querier"
            )

        # Check minimum stake
        if request.atp_stake < role.sensitivity.min_stake:
            return TrustQueryResponse(
                query_id=request.query_id, status="INSUFFICIENT_STAKE",
                reason=f"Min stake for {role.sensitivity.label}: {role.sensitivity.min_stake} ATP"
            )

        # Check max stake
        if request.atp_stake > self.fishing_detector.max_stake_per_query:
            return TrustQueryResponse(
                query_id=request.query_id, status="EXCESSIVE_STAKE",
                reason=f"Max stake: {self.fishing_detector.max_stake_per_query} ATP"
            )

        # Rate limiting
        ok, msg = self.fishing_detector.check_rate_limit(request.querier_id)
        if not ok:
            return TrustQueryResponse(
                query_id=request.query_id, status="RATE_LIMITED", reason=msg
            )

        # Target limit
        ok, msg = self.fishing_detector.check_target_limit(request.querier_id)
        if not ok:
            return TrustQueryResponse(
                query_id=request.query_id, status="TARGET_LIMITED", reason=msg
            )

        # Need-to-know validation
        ok, msg = self.need_validator.validate(
            request.querier_id, request.target_id, request.role_id,
            request.intended_interaction,
        )
        if not ok:
            # Rejected: 95% returned
            penalty = request.atp_stake * self.REJECTED_PENALTY
            return_amount = request.atp_stake - penalty
            querier.deduct_atp(penalty)
            self._log_query(request, QueryOutcome.REJECTED)
            return TrustQueryResponse(
                query_id=request.query_id, status="REJECTED",
                reason=msg, stake_returned=return_amount,
            )

        # Check querier has sufficient ATP
        if not querier.lock_atp(request.atp_stake):
            return TrustQueryResponse(
                query_id=request.query_id, status="INSUFFICIENT_ATP",
                reason=f"Need {request.atp_stake} ATP, available {querier.atp_available}"
            )

        # Determine disclosure level
        disclosure = TrustDisclosure.for_stake(request.atp_stake)

        # Get role-specific trust
        t3 = target.get_trust_in_role(request.role_id)
        if not t3:
            t3 = T3Tensor()  # Default if no trust history

        trust_data = t3.disclose(disclosure)

        # Record query
        self.fishing_detector.record_query(
            request.querier_id, request.target_id, request.role_id
        )
        self._log_query(request, outcome="pending", disclosure_level=disclosure)

        # Set engagement expectation
        deadline = datetime.now(timezone.utc) + timedelta(seconds=request.validity_seconds)
        expectation = EngagementExpectation(
            query_id=request.query_id,
            querier_id=request.querier_id,
            target_id=request.target_id,
            role_id=request.role_id,
            stake=request.atp_stake,
            deadline=deadline.isoformat(),
        )
        self.expectations[request.query_id] = expectation

        return TrustQueryResponse(
            query_id=request.query_id,
            status="OK",
            disclosure_level=disclosure,
            trust_data=trust_data,
            stake_locked=request.atp_stake,
            engagement_deadline=deadline.isoformat(),
        )

    def resolve_engagement(self, query_id: str, outcome: QueryOutcome) -> Tuple[bool, str]:
        """Resolve a trust query engagement."""
        exp = self.expectations.get(query_id)
        if not exp:
            return False, "No engagement expectation found"
        if exp.resolved:
            return False, "Already resolved"

        querier = self.entities.get(exp.querier_id)
        target = self.entities.get(exp.target_id)
        if not querier or not target:
            return False, "Entity not found"

        exp.resolved = True
        exp.outcome = outcome

        # Record engagement for fishing detection
        self.fishing_detector.record_engagement(
            exp.querier_id, outcome == QueryOutcome.ENGAGED
        )

        if outcome == QueryOutcome.ENGAGED:
            # 90% returned, 10% fee (fee goes to system)
            fee = exp.stake * self.QUERY_FEE_RATE
            returned = exp.stake - fee
            querier.unlock_atp(exp.stake)
            querier.deduct_atp(fee)
            self._update_log(query_id, QueryOutcome.ENGAGED)
            return True, f"Engaged: {returned:.2f} ATP returned, {fee:.2f} fee"

        elif outcome == QueryOutcome.FORFEITED:
            # 100% to target
            querier.unlock_atp(exp.stake)
            querier.deduct_atp(exp.stake)
            target.receive_atp(exp.stake)
            self._update_log(query_id, QueryOutcome.FORFEITED)
            return True, f"Forfeited: {exp.stake:.2f} ATP to target"

        elif outcome == QueryOutcome.DECLINED:
            # 100% returned
            querier.unlock_atp(exp.stake)
            self._update_log(query_id, QueryOutcome.DECLINED)
            return True, f"Declined: {exp.stake:.2f} ATP returned"

        return False, f"Unknown outcome: {outcome}"

    def check_expired_expectations(self) -> List[str]:
        """Auto-forfeit expired unresolved expectations."""
        now = datetime.now(timezone.utc).isoformat()
        forfeited = []
        for qid, exp in self.expectations.items():
            if not exp.resolved and exp.deadline < now:
                self.resolve_engagement(qid, QueryOutcome.FORFEITED)
                forfeited.append(qid)
        return forfeited

    def detect_and_suspend_fishing(self, querier_id: str) -> Tuple[bool, List[str]]:
        """Check for fishing behavior and suspend if detected."""
        is_fishing, patterns = self.fishing_detector.detect_fishing(querier_id)
        if is_fishing:
            querier = self.entities.get(querier_id)
            if querier:
                sus_until = (
                    datetime.now(timezone.utc)
                    + timedelta(hours=self.fishing_detector.suspension_duration_hours)
                )
                querier.query_suspended_until = sus_until.isoformat()
                querier.deduct_atp(self.fishing_detector.fishing_penalty_atp)
        return is_fishing, patterns

    def get_role_statistics(self, role_id: str) -> RoleStatistics:
        """Get anonymous aggregate statistics for a role."""
        entities = list(self.entities.values())
        return compute_role_statistics(entities, role_id, self.query_log)

    def get_queries_about(self, entity_id: str) -> List[QueryLogEntry]:
        """Entity's Right to Know: who queried their trust."""
        return self.entity_rights.right_to_know(
            self.entities.get(entity_id, Entity()), self.query_log
        )

    def _log_query(
        self, request: TrustQueryRequest, outcome: Any = "pending",
        disclosure_level: TrustDisclosure = TrustDisclosure.NONE,
    ):
        outcome_str = outcome.value if isinstance(outcome, QueryOutcome) else str(outcome)
        entry = QueryLogEntry(
            query_id=request.query_id,
            querier_id=request.querier_id,
            target_id=request.target_id,
            role_id=request.role_id,
            timestamp=request.timestamp,
            atp_staked=request.atp_stake,
            outcome=outcome_str,
            disclosure_level=int(disclosure_level),
        )
        self.query_log.append(entry)

    def _update_log(self, query_id: str, outcome: QueryOutcome):
        for entry in self.query_log:
            if entry.query_id == query_id:
                entry.outcome = outcome.value
                entry.resolved_at = datetime.now(timezone.utc).isoformat()
                break


# ============================================================
# Section 9: Tests
# ============================================================

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name, condition):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}")

    # ── T1: Trust Disclosure Levels ──
    print("\n── T1: Trust Disclosure Levels ──")

    check("T1.1 Stake <10 → NONE", TrustDisclosure.for_stake(5) == TrustDisclosure.NONE)
    check("T1.2 Stake 10-49 → BINARY", TrustDisclosure.for_stake(25) == TrustDisclosure.BINARY)
    check("T1.3 Stake 50-99 → RANGE", TrustDisclosure.for_stake(75) == TrustDisclosure.RANGE)
    check("T1.4 Stake ≥100 → PRECISE", TrustDisclosure.for_stake(100) == TrustDisclosure.PRECISE)
    check("T1.5 Stake 500 → PRECISE", TrustDisclosure.for_stake(500) == TrustDisclosure.PRECISE)

    # ── T2: T3 Tensor Disclosure ──
    print("\n── T2: T3 Tensor Disclosure ──")

    t3 = T3Tensor(talent=0.8, training=0.7, temperament=0.9)
    check("T2.1 Composite", abs(t3.composite - 0.8) < 0.001)
    check("T2.2 Binary = qualified", t3.to_binary() == "qualified")
    check("T2.3 Range = high", t3.to_range() == "high")
    precise = t3.to_precise()
    check("T2.4 Precise has talent", precise["talent"] == 0.8)
    check("T2.5 Precise has composite", abs(precise["composite"] - 0.8) < 0.001)

    t3_low = T3Tensor(talent=0.2, training=0.1, temperament=0.3)
    check("T2.6 Low binary = not_qualified", t3_low.to_binary() == "not_qualified")
    check("T2.7 Low range = low", t3_low.to_range() == "low")

    t3_mid = T3Tensor(talent=0.5, training=0.5, temperament=0.5)
    check("T2.8 Mid range = medium", t3_mid.to_range() == "medium")

    # Disclosure at levels
    check("T2.9 NONE disclosure = None", t3.disclose(TrustDisclosure.NONE) is None)
    check("T2.10 BINARY disclosure", t3.disclose(TrustDisclosure.BINARY) == "qualified")
    check("T2.11 RANGE disclosure", t3.disclose(TrustDisclosure.RANGE) == "high")
    check("T2.12 PRECISE disclosure", isinstance(t3.disclose(TrustDisclosure.PRECISE), dict))

    # ── T3: Role Sensitivity ──
    print("\n── T3: Role Sensitivity ──")

    check("T3.1 Public min stake = 10", RoleSensitivity.PUBLIC_SERVICE.min_stake == 10)
    check("T3.2 Professional min = 50", RoleSensitivity.PROFESSIONAL.min_stake == 50)
    check("T3.3 Specialist min = 100", RoleSensitivity.SPECIALIST.min_stake == 100)
    check("T3.4 Critical min = 500", RoleSensitivity.CRITICAL.min_stake == 500)
    check("T3.5 Governance min = 1000", RoleSensitivity.GOVERNANCE.min_stake == 1000)

    # ── T4: Entity ATP Management ──
    print("\n── T4: Entity ATP Management ──")

    alice = Entity(lct_id="lct://alice", atp_balance=1000)
    check("T4.1 Initial balance", alice.atp_balance == 1000)
    check("T4.2 Available = balance", alice.atp_available == 1000)

    check("T4.3 Lock 100", alice.lock_atp(100))
    check("T4.4 Locked = 100", alice.atp_locked == 100)
    check("T4.5 Available = 900", alice.atp_available == 900)

    check("T4.6 Can't lock > available", not alice.lock_atp(950))
    alice.unlock_atp(100)
    check("T4.7 Unlock restores available", alice.atp_available == 1000)

    alice.deduct_atp(50)
    check("T4.8 Deduct reduces balance", alice.atp_balance == 950)

    alice.receive_atp(50)
    check("T4.9 Receive increases balance", alice.atp_balance == 1000)

    # ── T5: Role-Contextual Trust (Never Global) ──
    print("\n── T5: Role-Contextual Trust (Never Global) ──")

    bob = Entity(lct_id="lct://bob", atp_balance=500)
    bob.set_trust_in_role("web4:Surgeon", T3Tensor(0.9, 0.8, 0.7))
    bob.set_trust_in_role("web4:Developer", T3Tensor(0.3, 0.4, 0.5))

    surgeon_t3 = bob.get_trust_in_role("web4:Surgeon")
    dev_t3 = bob.get_trust_in_role("web4:Developer")

    check("T5.1 Surgeon talent = 0.9", surgeon_t3.talent == 0.9)
    check("T5.2 Developer talent = 0.3", dev_t3.talent == 0.3)
    check("T5.3 Different roles, different trust", surgeon_t3.composite > dev_t3.composite)
    check("T5.4 No global score exists", not hasattr(bob, "global_trust_score"))
    check("T5.5 Unknown role = None", bob.get_trust_in_role("web4:Pilot") is None)
    check("T5.6 Average in role", abs(bob.average_t3_in_role("web4:Surgeon") - 0.8) < 0.001)

    # ── T6: Trust Query Engine — Basic Flow ──
    print("\n── T6: Trust Query Engine — Basic Flow ──")

    engine = TrustQueryEngine()

    # Setup entities
    querier = Entity(lct_id="lct://patient", atp_balance=2000)
    target = Entity(lct_id="lct://dr_smith", atp_balance=500)
    target.set_trust_in_role("web4:Surgeon", T3Tensor(0.9, 0.85, 0.95))
    engine.register_entity(querier)
    engine.register_entity(target)

    surgeon_role = Role(name="Surgeon", sensitivity=RoleSensitivity.SPECIALIST)
    engine.register_role(surgeon_role)

    # Establish need
    engine.need_validator.register_need("lct://patient", "lct://dr_smith")
    engine.need_validator.register_valid_interaction("web4:Surgeon", "surgical-procedure")

    # Execute query
    req = TrustQueryRequest(
        querier_id="lct://patient",
        target_id="lct://dr_smith",
        role_id="web4:Surgeon",
        intended_interaction="surgical-procedure",
        atp_stake=150,
        validity_seconds=3600,
    )
    resp = engine.query_trust(req)
    check("T6.1 Query OK", resp.status == "OK")
    check("T6.2 Disclosure = PRECISE", resp.disclosure_level == TrustDisclosure.PRECISE)
    check("T6.3 Trust data is dict", isinstance(resp.trust_data, dict))
    check("T6.4 Talent in data", resp.trust_data["talent"] == 0.9)
    check("T6.5 Stake locked", resp.stake_locked == 150)
    check("T6.6 Deadline set", resp.engagement_deadline is not None)
    check("T6.7 ATP locked on querier", querier.atp_locked == 150)

    # ── T7: Stake Resolution — Engagement ──
    print("\n── T7: Stake Resolution — Engagement ──")

    balance_before = querier.atp_balance
    ok, msg = engine.resolve_engagement(req.query_id, QueryOutcome.ENGAGED)
    check("T7.1 Engagement resolved", ok)
    check("T7.2 Lock released", querier.atp_locked == 0)
    fee = 150 * 0.10  # 10% fee
    check("T7.3 Fee deducted", abs(querier.atp_balance - (balance_before - fee)) < 0.01)
    check("T7.4 Already resolved", not engine.resolve_engagement(req.query_id, QueryOutcome.ENGAGED)[0])

    # ── T8: Stake Resolution — Forfeiture ──
    print("\n── T8: Stake Resolution — Forfeiture ──")

    engine2 = TrustQueryEngine()
    q2 = Entity(lct_id="lct://q2", atp_balance=2000)
    t2 = Entity(lct_id="lct://t2", atp_balance=500)
    t2.set_trust_in_role("web4:Dev", T3Tensor(0.7, 0.7, 0.7))
    engine2.register_entity(q2)
    engine2.register_entity(t2)
    dev_role = Role(name="Dev", sensitivity=RoleSensitivity.PROFESSIONAL)
    engine2.register_role(dev_role)
    engine2.need_validator.register_need("lct://q2", "lct://t2")

    req2 = TrustQueryRequest(
        querier_id="lct://q2", target_id="lct://t2",
        role_id="web4:Dev", intended_interaction="coding",
        atp_stake=100,
    )
    engine2.query_trust(req2)
    t2_balance_before = t2.atp_balance
    q2_balance_before = q2.atp_balance

    ok, msg = engine2.resolve_engagement(req2.query_id, QueryOutcome.FORFEITED)
    check("T8.1 Forfeiture resolved", ok)
    check("T8.2 Target received stake", t2.atp_balance == t2_balance_before + 100)
    check("T8.3 Querier lost stake", q2.atp_balance == q2_balance_before - 100)

    # ── T9: Stake Resolution — Declined ──
    print("\n── T9: Stake Resolution — Declined ──")

    engine3 = TrustQueryEngine()
    q3 = Entity(lct_id="lct://q3", atp_balance=2000)
    t3_entity = Entity(lct_id="lct://t3", atp_balance=500)
    t3_entity.set_trust_in_role("web4:Citizen", T3Tensor(0.5, 0.5, 0.5))
    engine3.register_entity(q3)
    engine3.register_entity(t3_entity)
    citizen_role = Role(name="Citizen", sensitivity=RoleSensitivity.PUBLIC_SERVICE)
    engine3.register_role(citizen_role)
    engine3.need_validator.register_need("lct://q3", "lct://t3")

    req3 = TrustQueryRequest(
        querier_id="lct://q3", target_id="lct://t3",
        role_id="web4:Citizen", intended_interaction="collaboration",
        atp_stake=50,
    )
    engine3.query_trust(req3)
    q3_balance_before = q3.atp_balance

    ok, msg = engine3.resolve_engagement(req3.query_id, QueryOutcome.DECLINED)
    check("T9.1 Decline resolved", ok)
    check("T9.2 Full stake returned", q3.atp_balance == q3_balance_before)
    check("T9.3 Lock released", q3.atp_locked == 0)

    # ── T10: Rejection (No Need-to-Know) ──
    print("\n── T10: Rejection (No Need-to-Know) ──")

    engine4 = TrustQueryEngine()
    q4 = Entity(lct_id="lct://stranger", atp_balance=2000)
    t4 = Entity(lct_id="lct://private", atp_balance=500)
    t4.set_trust_in_role("web4:Auditor", T3Tensor(0.8, 0.8, 0.8))
    engine4.register_entity(q4)
    engine4.register_entity(t4)
    auditor_role = Role(name="Auditor", sensitivity=RoleSensitivity.SPECIALIST)
    engine4.register_role(auditor_role)
    # NOTE: No need registered — should be rejected

    req4 = TrustQueryRequest(
        querier_id="lct://stranger", target_id="lct://private",
        role_id="web4:Auditor", intended_interaction="audit",
        atp_stake=200,
    )
    resp4 = engine4.query_trust(req4)
    check("T10.1 Rejected", resp4.status == "REJECTED")
    penalty = 200 * 0.05
    check("T10.2 95% returned", abs(resp4.stake_returned - (200 - penalty)) < 0.01)
    check("T10.3 5% penalty", abs(q4.atp_balance - (2000 - penalty)) < 0.01)

    # ── T11: Minimum Stake Enforcement ──
    print("\n── T11: Minimum Stake Enforcement ──")

    engine5 = TrustQueryEngine()
    q5 = Entity(lct_id="lct://cheap", atp_balance=2000)
    t5 = Entity(lct_id="lct://expert", atp_balance=500)
    engine5.register_entity(q5)
    engine5.register_entity(t5)
    crit_role = Role(name="NuclearOp", sensitivity=RoleSensitivity.CRITICAL)
    engine5.register_role(crit_role)
    engine5.need_validator.register_need("lct://cheap", "lct://expert")

    # Try with insufficient stake
    req5 = TrustQueryRequest(
        querier_id="lct://cheap", target_id="lct://expert",
        role_id="web4:NuclearOp", intended_interaction="operation",
        atp_stake=100,  # Critical requires 500
    )
    resp5 = engine5.query_trust(req5)
    check("T11.1 Insufficient stake rejected", resp5.status == "INSUFFICIENT_STAKE")
    check("T11.2 Reason mentions min stake", "500" in resp5.reason)

    # Try with sufficient stake
    req5b = TrustQueryRequest(
        querier_id="lct://cheap", target_id="lct://expert",
        role_id="web4:NuclearOp", intended_interaction="operation",
        atp_stake=500,
    )
    resp5b = engine5.query_trust(req5b)
    check("T11.3 Sufficient stake accepted", resp5b.status == "OK")

    # ── T12: Entity Right to Refuse ──
    print("\n── T12: Entity Right to Refuse ──")

    engine6 = TrustQueryEngine()
    q6 = Entity(lct_id="lct://stalker", atp_balance=2000)
    t6 = Entity(lct_id="lct://victim", atp_balance=500)
    t6.set_trust_in_role("web4:Citizen", T3Tensor(0.5, 0.5, 0.5))
    engine6.register_entity(q6)
    engine6.register_entity(t6)
    engine6.register_role(citizen_role)
    engine6.need_validator.register_need("lct://stalker", "lct://victim")

    # Block the stalker
    engine6.entity_rights.right_to_refuse(t6, "lct://stalker")
    check("T12.1 Stalker blocked", engine6.entity_rights.is_blocked(t6, "lct://stalker"))

    req6 = TrustQueryRequest(
        querier_id="lct://stalker", target_id="lct://victim",
        role_id="web4:Citizen", intended_interaction="collaboration",
        atp_stake=50,
    )
    resp6 = engine6.query_trust(req6)
    check("T12.2 Blocked query rejected", resp6.status == "BLOCKED")
    check("T12.3 Reason mentions blocked", "blocked" in resp6.reason.lower())

    # ── T13: Right to Know ──
    print("\n── T13: Right to Know ──")

    # Use engine from T6 which has query log
    about_dr = engine.get_queries_about("lct://dr_smith")
    check("T13.1 Query logged about dr_smith", len(about_dr) > 0)
    check("T13.2 Log has querier", about_dr[0].querier_id == "lct://patient")
    check("T13.3 Log has role", about_dr[0].role_id == "web4:Surgeon")

    # ── T14: Right to Expire ──
    print("\n── T14: Right to Expire ──")

    rights = EntityRights()
    test_entity = Entity(lct_id="lct://test", trust_history_max_days=30)
    old_entry = QueryLogEntry(
        query_id="old", target_id="lct://test",
        timestamp="2020-01-01T00:00:00+00:00",
    )
    new_entry = QueryLogEntry(
        query_id="new", target_id="lct://test",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    other_entry = QueryLogEntry(
        query_id="other", target_id="lct://other",
        timestamp="2020-01-01T00:00:00+00:00",
    )
    filtered = rights.expire_old_entries(test_entity, [old_entry, new_entry, other_entry])
    check("T14.1 Old entry expired", len(filtered) == 2)
    check("T14.2 New entry kept", any(e.query_id == "new" for e in filtered))
    check("T14.3 Other entity kept", any(e.query_id == "other" for e in filtered))

    # ── T15: Anti-Fishing — Rate Limit ──
    print("\n── T15: Anti-Fishing — Rate Limit ──")

    detector = FishingDetector(queries_per_hour_limit=3)
    for i in range(3):
        detector.record_query("fisher", f"target_{i}", "web4:Dev")

    ok, msg = detector.check_rate_limit("fisher")
    check("T15.1 Rate limited after 3", not ok)
    check("T15.2 Message mentions limit", "3" in msg)

    ok2, _ = detector.check_rate_limit("innocent")
    check("T15.3 Innocent not limited", ok2)

    # ── T16: Anti-Fishing — Target Limit ──
    print("\n── T16: Anti-Fishing — Target Limit ──")

    detector2 = FishingDetector(unique_targets_per_day_limit=3)
    for i in range(3):
        detector2.record_query("scanner", f"target_{i}", "web4:Citizen")

    ok, msg = detector2.check_target_limit("scanner")
    check("T16.1 Target limited", not ok)
    check("T16.2 Message mentions limit", "3" in msg)

    # ── T17: Anti-Fishing — No Engagement Pattern ──
    print("\n── T17: Anti-Fishing — No Engagement Pattern ──")

    detector3 = FishingDetector()
    # 10 queries, only 1 engagement (10% rate)
    for i in range(10):
        detector3.record_engagement("lurker", i == 0)

    check("T17.1 Low engagement detected", detector3.many_queries_no_engagement("lurker"))

    # Good actor
    for _ in range(10):
        detector3.record_engagement("good", True)
    check("T17.2 Good actor not flagged", not detector3.many_queries_no_engagement("good"))

    # Not enough history
    check("T17.3 New user not flagged", not detector3.many_queries_no_engagement("new_user"))

    # ── T18: Anti-Fishing — Role Shopping ──
    print("\n── T18: Anti-Fishing — Role Shopping ──")

    detector4 = FishingDetector()
    for i in range(5):
        detector4.record_query("shopper", "same_target", f"role_{i}")

    check("T18.1 Role shopping detected", detector4.role_shopping("shopper"))

    detector4.record_query("normal", "target1", "role1")
    check("T18.2 Normal not flagged", not detector4.role_shopping("normal"))

    # ── T19: Fishing Detection Composite ──
    print("\n── T19: Fishing Detection Composite ──")

    detector5 = FishingDetector()
    # Build fishing profile
    for i in range(5):
        detector5.record_query("fisher5", "same_target", f"role_{i}")
    for _ in range(10):
        detector5.record_engagement("fisher5", False)

    is_fishing, patterns = detector5.detect_fishing("fisher5")
    check("T19.1 Fishing detected", is_fishing)
    check("T19.2 Multiple patterns", len(patterns) == 2)
    check("T19.3 Role shopping in patterns", "role_shopping" in patterns)
    check("T19.4 No engagement in patterns", "many_queries_no_engagement" in patterns)

    # Clean user
    is_clean, _ = detector5.detect_fishing("clean_user")
    check("T19.5 Clean user OK", not is_clean)

    # ── T20: Query Pricing ──
    print("\n── T20: Query Pricing ──")

    market = MarketDemand(
        role_demand={"web4:Surgeon": 2.0, "web4:Citizen": 0.5},
        role_entity_counts={"web4:Surgeon": 5, "web4:Citizen": 100},
    )
    surgeon = Role(name="Surgeon", sensitivity=RoleSensitivity.SPECIALIST)
    citizen = Role(name="Citizen", sensitivity=RoleSensitivity.PUBLIC_SERVICE)

    surgeon_target = Entity(lct_id="lct://surgeon1")
    surgeon_target.set_trust_in_role("web4:Surgeon", T3Tensor(0.9, 0.9, 0.9))
    citizen_target = Entity(lct_id="lct://citizen1")
    citizen_target.set_trust_in_role("web4:Citizen", T3Tensor(0.5, 0.5, 0.5))

    surgeon_price = calculate_query_price(surgeon, surgeon_target, market)
    citizen_price = calculate_query_price(citizen, citizen_target, market)

    check("T20.1 Surgeon more expensive", surgeon_price > citizen_price)
    check("T20.2 Surgeon price > 0", surgeon_price > 0)
    check("T20.3 Citizen price > 0", citizen_price > 0)

    # Scarcity effect
    market2 = MarketDemand(
        role_demand={"web4:Rare": 1.0},
        role_entity_counts={"web4:Rare": 1},
    )
    market3 = MarketDemand(
        role_demand={"web4:Rare": 1.0},
        role_entity_counts={"web4:Rare": 100},
    )
    rare_role = Role(name="Rare", sensitivity=RoleSensitivity.PROFESSIONAL)
    rare_entity = Entity(lct_id="lct://rare")
    rare_entity.set_trust_in_role("web4:Rare", T3Tensor(0.8, 0.8, 0.8))

    scarce_price = calculate_query_price(rare_role, rare_entity, market2)
    common_price = calculate_query_price(rare_role, rare_entity, market3)
    check("T20.4 Scarce costs more", scarce_price > common_price)

    # ── T21: Privacy-Preserving Aggregates ──
    print("\n── T21: Privacy-Preserving Aggregates ──")

    entities = []
    for i in range(10):
        e = Entity(lct_id=f"lct://e{i}")
        e.set_trust_in_role("web4:Dev", T3Tensor(0.6 + i * 0.02, 0.7, 0.6))
        entities.append(e)

    logs = [
        QueryLogEntry(query_id=f"q{i}", role_id="web4:Dev",
                       outcome=QueryOutcome.ENGAGED.value if i < 8 else QueryOutcome.FORFEITED.value)
        for i in range(10)
    ]
    stats = compute_role_statistics(entities, "web4:Dev", logs)
    check("T21.1 Total entities = 10", stats.total_entities == 10)
    check("T21.2 Talent range is range format", "-" in stats.average_talent_range)
    check("T21.3 Success rate = 0.8", abs(stats.engagement_success_rate - 0.8) < 0.01)
    check("T21.4 Demand = medium", stats.market_demand == "medium")

    # Few entities = high demand
    stats2 = compute_role_statistics(entities[:3], "web4:Dev", [])
    check("T21.5 Few entities = high demand", stats2.market_demand == "high")

    # ── T22: Suspension & Penalty ──
    print("\n── T22: Suspension & Penalty ──")

    engine7 = TrustQueryEngine()
    fisher = Entity(lct_id="lct://fisher", atp_balance=2000)
    engine7.register_entity(fisher)

    # Build fishing profile
    for i in range(5):
        engine7.fishing_detector.record_query("lct://fisher", "same_target", f"role_{i}")
    for _ in range(10):
        engine7.fishing_detector.record_engagement("lct://fisher", False)

    is_fishing, patterns = engine7.detect_and_suspend_fishing("lct://fisher")
    check("T22.1 Fisher detected", is_fishing)
    check("T22.2 Fisher suspended", fisher.is_suspended())
    check("T22.3 ATP penalty applied", fisher.atp_balance < 2000)
    check("T22.4 Penalty = 500", abs(fisher.atp_balance - 1500) < 0.01)

    # Suspended entity can't query
    engine7.register_entity(Entity(lct_id="lct://innocent_target"))
    engine7.register_role(citizen_role)
    sus_req = TrustQueryRequest(
        querier_id="lct://fisher", target_id="lct://innocent_target",
        role_id="web4:Citizen", atp_stake=50,
    )
    sus_resp = engine7.query_trust(sus_req)
    check("T22.5 Suspended query blocked", sus_resp.status == "SUSPENDED")

    # ── T23: Insufficient ATP ──
    print("\n── T23: Insufficient ATP ──")

    engine8 = TrustQueryEngine()
    poor = Entity(lct_id="lct://poor", atp_balance=5)
    rich_target = Entity(lct_id="lct://rich_target", atp_balance=500)
    rich_target.set_trust_in_role("web4:Citizen", T3Tensor(0.5, 0.5, 0.5))
    engine8.register_entity(poor)
    engine8.register_entity(rich_target)
    engine8.register_role(citizen_role)
    engine8.need_validator.register_need("lct://poor", "lct://rich_target")

    poor_req = TrustQueryRequest(
        querier_id="lct://poor", target_id="lct://rich_target",
        role_id="web4:Citizen", atp_stake=50,
    )
    poor_resp = engine8.query_trust(poor_req)
    check("T23.1 Insufficient ATP rejected", poor_resp.status == "INSUFFICIENT_ATP")

    # ── T24: Excessive Stake ──
    print("\n── T24: Excessive Stake ──")

    engine9 = TrustQueryEngine()
    whale = Entity(lct_id="lct://whale", atp_balance=100000)
    target9 = Entity(lct_id="lct://target9", atp_balance=500)
    engine9.register_entity(whale)
    engine9.register_entity(target9)
    engine9.register_role(citizen_role)
    engine9.need_validator.register_need("lct://whale", "lct://target9")

    whale_req = TrustQueryRequest(
        querier_id="lct://whale", target_id="lct://target9",
        role_id="web4:Citizen", atp_stake=5000,  # Max = 1000
    )
    whale_resp = engine9.query_trust(whale_req)
    check("T24.1 Excessive stake rejected", whale_resp.status == "EXCESSIVE_STAKE")
    check("T24.2 Reason mentions max", "1000" in whale_resp.reason)

    # ── T25: Nonexistent Entity/Role ──
    print("\n── T25: Nonexistent Entity/Role ──")

    engine10 = TrustQueryEngine()
    engine10.register_entity(Entity(lct_id="lct://exists"))

    bad_req1 = TrustQueryRequest(
        querier_id="lct://ghost", target_id="lct://exists",
        role_id="web4:Any", atp_stake=50,
    )
    check("T25.1 Unknown querier", engine10.query_trust(bad_req1).status == "ERROR")

    bad_req2 = TrustQueryRequest(
        querier_id="lct://exists", target_id="lct://ghost",
        role_id="web4:Any", atp_stake=50,
    )
    check("T25.2 Unknown target", engine10.query_trust(bad_req2).status == "ERROR")

    bad_req3 = TrustQueryRequest(
        querier_id="lct://exists", target_id="lct://exists",
        role_id="web4:Unknown", atp_stake=50,
    )
    check("T25.3 Unknown role", engine10.query_trust(bad_req3).status == "ERROR")

    # ── T26: Need-to-Know Validation ──
    print("\n── T26: Need-to-Know Validation ──")

    validator = NeedToKnowValidator()
    validator.register_need("alice", "bob")
    validator.register_valid_interaction("web4:Surgeon", "surgical-procedure")

    ok, msg = validator.validate("alice", "bob", "web4:Surgeon", "surgical-procedure")
    check("T26.1 Valid need", ok)

    ok, msg = validator.validate("alice", "charlie", "web4:Surgeon", "surgical-procedure")
    check("T26.2 No established need", not ok)
    check("T26.3 Reason mentions need", "need" in msg.lower())

    ok, msg = validator.validate("alice", "bob", "web4:Surgeon", "coffee-chat")
    check("T26.4 Invalid interaction", not ok)
    check("T26.5 Reason mentions interaction", "interaction" in msg.lower())

    # Unregistered role → any interaction OK
    ok, msg = validator.validate("alice", "bob", "web4:Citizen", "anything")
    check("T26.6 Unregistered role allows any interaction", ok)

    # ── T27: Full Trust Query Lifecycle ──
    print("\n── T27: Full Trust Query Lifecycle ──")

    engine11 = TrustQueryEngine()
    patient = Entity(lct_id="lct://patient2", atp_balance=5000)
    doctor = Entity(lct_id="lct://doctor2", atp_balance=1000)
    doctor.set_trust_in_role("web4:Surgeon", T3Tensor(0.95, 0.9, 0.85))
    engine11.register_entity(patient)
    engine11.register_entity(doctor)
    engine11.register_role(surgeon_role)
    engine11.need_validator.register_need("lct://patient2", "lct://doctor2")
    engine11.need_validator.register_valid_interaction("web4:Surgeon", "surgical-procedure")

    # 1. Query with low stake → BINARY disclosure
    low_req = TrustQueryRequest(
        querier_id="lct://patient2", target_id="lct://doctor2",
        role_id="web4:Surgeon", intended_interaction="surgical-procedure",
        atp_stake=110,  # ≥100 → PRECISE (min for specialist is 100)
    )
    low_resp = engine11.query_trust(low_req)
    check("T27.1 Low-stake query OK", low_resp.status == "OK")
    check("T27.2 Disclosure level = PRECISE", low_resp.disclosure_level == TrustDisclosure.PRECISE)

    # Engage
    ok, msg = engine11.resolve_engagement(low_req.query_id, QueryOutcome.ENGAGED)
    check("T27.3 Engagement OK", ok)

    # 2. Query with high stake → PRECISE
    high_req = TrustQueryRequest(
        querier_id="lct://patient2", target_id="lct://doctor2",
        role_id="web4:Surgeon", intended_interaction="surgical-procedure",
        atp_stake=500,
    )
    high_resp = engine11.query_trust(high_req)
    check("T27.4 High-stake PRECISE", high_resp.disclosure_level == TrustDisclosure.PRECISE)
    check("T27.5 Has exact talent", high_resp.trust_data["talent"] == 0.95)

    # Forfeit
    pat_before = patient.atp_balance
    doc_before = doctor.atp_balance
    ok, msg = engine11.resolve_engagement(high_req.query_id, QueryOutcome.FORFEITED)
    check("T27.6 Forfeit OK", ok)
    check("T27.7 Doctor received 500", doctor.atp_balance == doc_before + 500)
    check("T27.8 Patient lost 500", patient.atp_balance == pat_before - 500)

    # 3. Audit trail
    about_doctor = engine11.get_queries_about("lct://doctor2")
    check("T27.9 Two queries logged", len(about_doctor) == 2)

    # ── T28: Role Statistics ──
    print("\n── T28: Role Statistics ──")

    stats = engine11.get_role_statistics("web4:Surgeon")
    check("T28.1 Stats computed", stats.total_entities >= 1)
    check("T28.2 Has talent range", len(stats.average_talent_range) > 0)

    empty_stats = engine11.get_role_statistics("web4:Nonexistent")
    check("T28.3 Empty role = 0 entities", empty_stats.total_entities == 0)

    # ── T29: Engagement Expectation ──
    print("\n── T29: Engagement Expectation ──")

    exp = EngagementExpectation(
        query_id="exp1", querier_id="alice", target_id="bob",
        role_id="web4:Dev", stake=100,
        deadline=datetime.now(timezone.utc).isoformat(),
    )
    check("T29.1 Expectation created", exp.query_id == "exp1")
    check("T29.2 Not resolved initially", not exp.resolved)
    check("T29.3 No outcome", exp.outcome is None)
    exp.resolved = True
    exp.outcome = QueryOutcome.ENGAGED
    check("T29.4 Can be resolved", exp.resolved)
    check("T29.5 Outcome set", exp.outcome == QueryOutcome.ENGAGED)

    # ── T30: Query Outcomes ATP Math ──
    print("\n── T30: Query Outcomes ATP Math ──")

    # Verify the exact math for each outcome type
    # ENGAGED: 90% returned, 10% fee
    check("T30.1 Engage fee = 10%", TrustQueryEngine.QUERY_FEE_RATE == 0.10)
    check("T30.2 Forfeit = 100% to target", TrustQueryEngine.FORFEIT_TO_TARGET == 1.00)
    check("T30.3 Declined = 100% returned", TrustQueryEngine.DECLINED_RETURN == 1.00)
    check("T30.4 Rejected penalty = 5%", TrustQueryEngine.REJECTED_PENALTY == 0.05)

    # Engagement: 1000 ATP stake → 900 back, 100 fee
    stake = 1000
    fee = stake * TrustQueryEngine.QUERY_FEE_RATE
    returned = stake - fee
    check("T30.5 1000 stake → 100 fee", fee == 100)
    check("T30.6 1000 stake → 900 returned", returned == 900)

    # Rejection: 1000 ATP → 950 back, 50 penalty
    penalty = stake * TrustQueryEngine.REJECTED_PENALTY
    rej_returned = stake - penalty
    check("T30.7 1000 rejection → 50 penalty", penalty == 50)
    check("T30.8 1000 rejection → 950 returned", rej_returned == 950)

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"T3/V3 Privacy Governance: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    print(f"{'='*60}")
    return passed, total


if __name__ == "__main__":
    run_tests()
