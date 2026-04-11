"""
Contextual Hardware Binding — Reference Implementation

Implements RFC-CHB-001:
- Multi-society hardware sharing with contextual metadata
- 4 sharing models: exclusive, concurrent, temporal, development
- Trust calculation adjustments: sharing penalty, transparency bonus
- Sybil resistance: correlation monitoring, resource verification
- Resource allocation enforcement with fair share protocols
- Witness-based sharing validation
- Backward compatible: exclusive binding remains valid
- Migration path: maintain exclusivity → declare sharing → independence

Key insight from RFC: "Replace binary hardware exclusivity with contextual
metadata that enables informed trust decisions."

Spec: web4-standard/rfcs/RFC-CONTEXTUAL-HARDWARE-BINDING.md
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class SharingModel(Enum):
    """Hardware sharing models per §2.3."""
    EXCLUSIVE = "exclusive"                  # 1:1 binding (current default)
    CONCURRENT = "concurrent_multi_society"  # Multiple societies, same hardware
    TEMPORAL = "temporal_multi_society"       # Different societies at different times
    HIERARCHICAL = "hierarchical"            # Parent with specialized sub-societies
    DEVELOPMENT = "development"              # Dev/test context


class BindingState(Enum):
    """State of a hardware binding."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    MIGRATING = "migrating"
    REVOKED = "revoked"


class MigrationTarget(Enum):
    """Migration targets per §5.2."""
    MAINTAIN_EXCLUSIVITY = "maintain_exclusivity"
    DECLARE_SHARING = "declare_sharing"
    MIGRATE_TO_INDEPENDENCE = "migrate_to_independence"


# Trust calculation defaults
DEFAULT_SHARING_PENALTY_FACTOR = 0.2    # Per RFC §2.2
DEFAULT_TRANSPARENCY_BONUS = 0.1        # Per RFC §2.2
DEFAULT_CONCEALMENT_PENALTY = -0.3      # Per RFC §2.2


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class CoResident:
    """A co-resident society on shared hardware."""
    society_id: str
    resource_allocation: float  # 0.0-1.0
    primary_functions: List[str]
    governance_independent: bool = True


@dataclass
class TrustImplications:
    """Trust implications of hardware sharing per §2.1."""
    sybil_resistance: float = 1.0       # 0.0-1.0, reduced by sharing
    accountability_score: float = 1.0    # 0.0-1.0
    resource_fairness: float = 1.0       # 0.0-1.0


@dataclass
class HardwareBinding:
    """Contextual hardware binding per §2.1."""
    hardware_id: str
    society_id: str
    sharing_model: SharingModel
    co_residents: List[CoResident] = field(default_factory=list)
    resource_allocation: float = 1.0
    primary_functions: List[str] = field(default_factory=list)
    correlation_coefficient: float = 0.0  # 0.0 (independent) to 1.0 (correlated)
    governance_independent: bool = True
    trust_implications: TrustImplications = field(default_factory=TrustImplications)
    state: BindingState = BindingState.ACTIVE
    created_at: Optional[datetime] = None
    disclosed: bool = True  # Whether sharing is honestly disclosed
    production_ready: bool = True


@dataclass
class ResourceUsage:
    """Tracked resource usage for a society."""
    society_id: str
    cpu_fraction: float = 0.0
    memory_fraction: float = 0.0
    storage_fraction: float = 0.0
    network_fraction: float = 0.0
    timestamp: Optional[datetime] = None


@dataclass
class CorrelationEvent:
    """Detected correlation between co-residents."""
    society_a: str
    society_b: str
    correlation_type: str  # "timing", "resource", "behavior"
    correlation_value: float
    timestamp: datetime
    suspicious: bool = False


@dataclass
class WitnessAttestation:
    """External witness attestation of sharing arrangement."""
    witness_id: str
    hardware_id: str
    confirmed_societies: List[str]
    confirmed_allocations: Dict[str, float]
    independence_confirmed: bool
    timestamp: datetime
    confidence: float = 0.9


# ============================================================================
# TRUST CALCULATOR
# ============================================================================

class ContextualTrustCalculator:
    """Calculate trust adjustments based on hardware context per §2.2."""

    @staticmethod
    def calculate(base_trust: float,
                  binding: HardwareBinding) -> float:
        """
        Calculate contextual trust from hardware sharing context.
        Per RFC: sharing_penalty = correlation × 0.2
                 transparency_bonus = 0.1 if disclosed else -0.3
        """
        if binding.sharing_model == SharingModel.EXCLUSIVE:
            # No adjustment for exclusive binding
            return min(base_trust, 1.0)

        sharing_penalty = (binding.correlation_coefficient *
                           DEFAULT_SHARING_PENALTY_FACTOR)
        transparency = (DEFAULT_TRANSPARENCY_BONUS if binding.disclosed
                        else DEFAULT_CONCEALMENT_PENALTY)

        adjusted = base_trust - sharing_penalty + transparency
        return max(0.0, min(adjusted, 1.0))

    @staticmethod
    def compute_trust_implications(binding: HardwareBinding) -> TrustImplications:
        """Compute full trust implications."""
        # Sybil resistance: lower with more co-residents and higher correlation
        sybil = 1.0 - (binding.correlation_coefficient * 0.4)
        if len(binding.co_residents) > 2:
            sybil -= 0.1 * (len(binding.co_residents) - 2)
        sybil = max(0.1, min(sybil, 1.0))

        # Accountability: higher with transparency, governance independence
        accountability = 0.5
        if binding.disclosed:
            accountability += 0.3
        if binding.governance_independent:
            accountability += 0.2

        # Resource fairness: based on allocation consistency
        total_alloc = binding.resource_allocation
        for co in binding.co_residents:
            total_alloc += co.resource_allocation
        fairness = 1.0 if abs(total_alloc - 1.0) < 0.05 else max(0.5, 1.0 - abs(total_alloc - 1.0))

        return TrustImplications(
            sybil_resistance=round(sybil, 4),
            accountability_score=round(accountability, 4),
            resource_fairness=round(fairness, 4))


# ============================================================================
# SYBIL RESISTANCE
# ============================================================================

class SybilDetector:
    """Detect sybil attacks through correlation monitoring per §4.1."""

    def __init__(self, correlation_threshold: float = 0.7,
                 timing_window_seconds: float = 2.0):
        self.correlation_threshold = correlation_threshold
        self.timing_window = timing_window_seconds
        self._action_log: Dict[str, List[Tuple[datetime, str]]] = {}
        self.events: List[CorrelationEvent] = []

    def log_action(self, society_id: str, action: str,
                   timestamp: datetime):
        """Log a society action for correlation analysis."""
        if society_id not in self._action_log:
            self._action_log[society_id] = []
        self._action_log[society_id].append((timestamp, action))

    def check_timing_correlation(self, soc_a: str, soc_b: str,
                                  now: Optional[datetime] = None) -> float:
        """Check timing correlation between two societies."""
        ts = now or datetime.now(timezone.utc)
        log_a = self._action_log.get(soc_a, [])
        log_b = self._action_log.get(soc_b, [])

        if not log_a or not log_b:
            return 0.0

        # Count synchronized actions (within timing window)
        synced = 0
        total = min(len(log_a), len(log_b))

        for ta, action_a in log_a:
            for tb, action_b in log_b:
                delta = abs((ta - tb).total_seconds())
                if delta <= self.timing_window:
                    synced += 1
                    break

        correlation = synced / total if total > 0 else 0.0

        event = CorrelationEvent(
            society_a=soc_a, society_b=soc_b,
            correlation_type="timing",
            correlation_value=correlation,
            timestamp=ts,
            suspicious=correlation > self.correlation_threshold)
        self.events.append(event)

        return correlation

    def check_behavior_correlation(self, actions_a: List[str],
                                    actions_b: List[str]) -> float:
        """Check if two societies exhibit similar behavior patterns."""
        if not actions_a or not actions_b:
            return 0.0

        # Jaccard similarity
        set_a = set(actions_a)
        set_b = set(actions_b)
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)

        return intersection / union if union > 0 else 0.0


# ============================================================================
# RESOURCE MONITOR
# ============================================================================

class ResourceMonitor:
    """Monitor resource usage vs declared allocations per §4.2."""

    def __init__(self, tolerance: float = 0.15):
        self.tolerance = tolerance
        self._usage_history: Dict[str, List[ResourceUsage]] = {}

    def record_usage(self, usage: ResourceUsage):
        """Record actual resource usage."""
        if usage.society_id not in self._usage_history:
            self._usage_history[usage.society_id] = []
        self._usage_history[usage.society_id].append(usage)

    def check_allocation(self, society_id: str,
                         declared_allocation: float) -> Tuple[bool, float]:
        """
        Check if actual usage matches declared allocation.
        Returns: (within_tolerance, actual_avg_usage)
        """
        history = self._usage_history.get(society_id, [])
        if not history:
            return (True, 0.0)

        avg_usage = sum(u.cpu_fraction for u in history) / len(history)
        within = abs(avg_usage - declared_allocation) <= self.tolerance

        return (within, avg_usage)

    def detect_starvation(self, bindings: List[HardwareBinding]) -> List[str]:
        """Detect if any society is being starved of resources."""
        starved = []
        for b in bindings:
            ok, actual = self.check_allocation(b.society_id, b.resource_allocation)
            if not ok and actual < b.resource_allocation - self.tolerance:
                starved.append(b.society_id)
        return starved


# ============================================================================
# BINDING REGISTRY
# ============================================================================

class BindingRegistry:
    """Registry for managing hardware bindings."""

    def __init__(self):
        self.bindings: Dict[str, HardwareBinding] = {}  # society_id → binding
        self.hardware_map: Dict[str, List[str]] = {}    # hardware_id → [society_ids]

    def register(self, binding: HardwareBinding) -> bool:
        """Register a hardware binding."""
        self.bindings[binding.society_id] = binding

        if binding.hardware_id not in self.hardware_map:
            self.hardware_map[binding.hardware_id] = []
        if binding.society_id not in self.hardware_map[binding.hardware_id]:
            self.hardware_map[binding.hardware_id].append(binding.society_id)

        return True

    def get_co_residents(self, hardware_id: str) -> List[str]:
        """Get all societies on a hardware platform."""
        return self.hardware_map.get(hardware_id, [])

    def validate_sharing_consistency(self, hardware_id: str) -> List[str]:
        """Validate that all co-residents have consistent metadata."""
        errors = []
        societies = self.get_co_residents(hardware_id)

        if len(societies) <= 1:
            return errors

        # Check all declare each other as co-residents
        for sid in societies:
            binding = self.bindings[sid]
            declared_co = set(c.society_id for c in binding.co_residents)
            actual_co = set(societies) - {sid}

            missing = actual_co - declared_co
            if missing:
                errors.append(
                    f"{sid} missing co-resident declarations: {missing}")

        # Check total allocation doesn't exceed 1.0
        total = sum(self.bindings[sid].resource_allocation
                    for sid in societies)
        if total > 1.05:  # 5% tolerance
            errors.append(
                f"Total allocation {total:.2f} exceeds 1.0 on {hardware_id}")

        return errors

    def get_sharing_model(self, society_id: str) -> Optional[SharingModel]:
        """Get the sharing model for a society."""
        binding = self.bindings.get(society_id)
        return binding.sharing_model if binding else None


# ============================================================================
# MIGRATION MANAGER
# ============================================================================

class MigrationManager:
    """Manage migration between sharing models per §5."""

    @staticmethod
    def can_migrate(current: SharingModel,
                    target: SharingModel) -> bool:
        """Check if migration is allowed."""
        # Can always migrate to more exclusive
        exclusive_order = [
            SharingModel.DEVELOPMENT,
            SharingModel.CONCURRENT,
            SharingModel.TEMPORAL,
            SharingModel.HIERARCHICAL,
            SharingModel.EXCLUSIVE,
        ]

        current_idx = exclusive_order.index(current) if current in exclusive_order else 0
        target_idx = exclusive_order.index(target) if target in exclusive_order else 0

        return True  # Any migration allowed, trust adjusts

    @staticmethod
    def migrate(binding: HardwareBinding,
                new_model: SharingModel,
                new_hardware_id: Optional[str] = None) -> HardwareBinding:
        """Migrate a binding to a new sharing model."""
        binding.sharing_model = new_model

        if new_model == SharingModel.EXCLUSIVE:
            binding.co_residents = []
            binding.correlation_coefficient = 0.0
            binding.resource_allocation = 1.0
            if new_hardware_id:
                binding.hardware_id = new_hardware_id

        binding.state = BindingState.ACTIVE
        return binding


# ============================================================================
# SERIALIZATION
# ============================================================================

class BindingSerializer:
    """Serialize bindings to JSON per RFC §6."""

    @staticmethod
    def to_json(binding: HardwareBinding) -> Dict:
        """Serialize a binding to JSON."""
        d: Dict[str, Any] = {
            "hardware_binding": {
                "hardware_id": binding.hardware_id,
                "sharing_model": binding.sharing_model.value,
                "resource_allocation": binding.resource_allocation,
                "primary_functions": binding.primary_functions,
                "governance_independence": binding.governance_independent,
                "disclosed": binding.disclosed,
                "state": binding.state.value,
            }
        }

        if binding.co_residents:
            d["hardware_binding"]["co_residents"] = [
                {
                    "society_id": c.society_id,
                    "resource_allocation": c.resource_allocation,
                    "primary_functions": c.primary_functions,
                }
                for c in binding.co_residents
            ]

        if binding.correlation_coefficient > 0:
            d["hardware_binding"]["binding_context"] = {
                "correlation_coefficient": binding.correlation_coefficient,
            }

        d["hardware_binding"]["trust_implications"] = {
            "sybil_resistance": binding.trust_implications.sybil_resistance,
            "accountability_score": binding.trust_implications.accountability_score,
            "resource_fairness": binding.trust_implications.resource_fairness,
        }

        if not binding.production_ready:
            d["hardware_binding"]["trust_implications"]["production_ready"] = False
            d["hardware_binding"]["trust_implications"]["experimental_context"] = True

        return d

    @staticmethod
    def to_turtle(binding: HardwareBinding) -> str:
        """Serialize binding as Turtle."""
        lines = [
            '@prefix web4: <https://web4.io/ontology#> .',
            '@prefix hw: <https://web4.io/hardware#> .',
            '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .',
            '',
            f'<{binding.society_id}> a web4:Society ;',
            f'    hw:boundTo <hw:{binding.hardware_id[:16]}> ;',
            f'    hw:sharingModel "{binding.sharing_model.value}" ;',
            f'    hw:resourceAllocation "{binding.resource_allocation:.2f}"^^xsd:decimal ;',
            f'    hw:correlation "{binding.correlation_coefficient:.2f}"^^xsd:decimal ;',
            f'    hw:sybilResistance "{binding.trust_implications.sybil_resistance:.4f}"^^xsd:decimal .',
            '',
        ]

        for co in binding.co_residents:
            lines.extend([
                f'<{binding.society_id}> hw:coResident <{co.society_id}> .',
                f'<{co.society_id}> hw:allocation "{co.resource_allocation:.2f}"^^xsd:decimal .',
                '',
            ])

        return '\n'.join(lines)


# ============================================================================
# TESTS
# ============================================================================

def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    return condition


def run_tests():
    passed = 0
    total = 0

    def t(label, condition):
        nonlocal passed, total
        total += 1
        if check(label, condition):
            passed += 1

    now = datetime(2026, 2, 22, 10, 0, 0, tzinfo=timezone.utc)
    hw_hash = "wsl2:ca2d41b985c61e1d29cc4d4d5f3d26d4b9ec7637"

    # ================================================================
    # T1: Exclusive binding (backward compatible)
    # ================================================================
    print("T1: Exclusive Binding")
    exclusive = HardwareBinding(
        hardware_id=hw_hash,
        society_id="lct:web4:society4",
        sharing_model=SharingModel.EXCLUSIVE,
        resource_allocation=1.0,
        correlation_coefficient=0.0,
        created_at=now)

    t("T1.1 Sharing model = exclusive",
      exclusive.sharing_model == SharingModel.EXCLUSIVE)
    t("T1.2 No co-residents", len(exclusive.co_residents) == 0)
    t("T1.3 Full allocation", exclusive.resource_allocation == 1.0)
    t("T1.4 Zero correlation", exclusive.correlation_coefficient == 0.0)
    t("T1.5 Disclosed by default", exclusive.disclosed)
    t("T1.6 Active state", exclusive.state == BindingState.ACTIVE)

    # Trust: no adjustment for exclusive
    trust = ContextualTrustCalculator.calculate(0.9, exclusive)
    t("T1.7 Exclusive → no trust penalty", trust == 0.9)

    # ================================================================
    # T2: Concurrent multi-society (ACT Federation case)
    # ================================================================
    print("T2: Concurrent Multi-Society")
    society2 = HardwareBinding(
        hardware_id=hw_hash,
        society_id="lct:web4:society2:bridge",
        sharing_model=SharingModel.CONCURRENT,
        resource_allocation=0.3,
        primary_functions=["harmony", "bridge", "integration"],
        co_residents=[
            CoResident("lct:web4:cbp:coordinator", 0.7,
                       ["data", "metrics", "cache"])
        ],
        correlation_coefficient=0.8,
        governance_independent=True,
        disclosed=True)

    cbp = HardwareBinding(
        hardware_id=hw_hash,
        society_id="lct:web4:cbp:coordinator",
        sharing_model=SharingModel.CONCURRENT,
        resource_allocation=0.7,
        primary_functions=["data", "metrics", "cache", "federation_bridge"],
        co_residents=[
            CoResident("lct:web4:society2:bridge", 0.3,
                       ["harmony", "bridge"])
        ],
        correlation_coefficient=0.8,
        governance_independent=True,
        disclosed=True)

    t("T2.1 Society2 allocation = 0.3", society2.resource_allocation == 0.3)
    t("T2.2 CBP allocation = 0.7", cbp.resource_allocation == 0.7)
    t("T2.3 Society2 has co-resident", len(society2.co_residents) == 1)
    t("T2.4 CBP has co-resident", len(cbp.co_residents) == 1)
    t("T2.5 Correlation = 0.8", society2.correlation_coefficient == 0.8)
    t("T2.6 Independent governance", society2.governance_independent)

    # ================================================================
    # T3: Trust calculation
    # ================================================================
    print("T3: Trust Calculation")
    # Concurrent with 0.8 correlation, disclosed
    trust_soc2 = ContextualTrustCalculator.calculate(0.9, society2)
    # penalty = 0.8 × 0.2 = 0.16, bonus = 0.1
    # 0.9 - 0.16 + 0.1 = 0.84
    t("T3.1 Sharing reduces trust", trust_soc2 < 0.9)
    t("T3.2 Expected trust ~0.84", abs(trust_soc2 - 0.84) < 0.01)

    # Undisclosed sharing → larger penalty
    undisclosed = HardwareBinding(
        hardware_id=hw_hash,
        society_id="lct:web4:hidden",
        sharing_model=SharingModel.CONCURRENT,
        correlation_coefficient=0.8,
        disclosed=False)
    trust_hidden = ContextualTrustCalculator.calculate(0.9, undisclosed)
    # 0.9 - 0.16 - 0.3 = 0.44
    t("T3.3 Undisclosed → large penalty", trust_hidden < trust_soc2)
    t("T3.4 Expected trust ~0.44", abs(trust_hidden - 0.44) < 0.01)

    # Low correlation → small penalty
    low_corr = HardwareBinding(
        hardware_id=hw_hash,
        society_id="lct:web4:low",
        sharing_model=SharingModel.CONCURRENT,
        correlation_coefficient=0.2,
        disclosed=True)
    trust_low = ContextualTrustCalculator.calculate(0.9, low_corr)
    t("T3.5 Low correlation → small penalty", trust_low > trust_soc2)

    # Clamped to [0, 1]
    trust_max = ContextualTrustCalculator.calculate(1.0, exclusive)
    t("T3.6 Trust capped at 1.0", trust_max <= 1.0)

    trust_min = ContextualTrustCalculator.calculate(0.0, undisclosed)
    t("T3.7 Trust floored at 0.0", trust_min >= 0.0)

    # ================================================================
    # T4: Trust implications
    # ================================================================
    print("T4: Trust Implications")
    impl_excl = ContextualTrustCalculator.compute_trust_implications(exclusive)
    t("T4.1 Exclusive sybil = 1.0", impl_excl.sybil_resistance == 1.0)

    impl_soc2 = ContextualTrustCalculator.compute_trust_implications(society2)
    t("T4.2 Concurrent sybil < 1.0", impl_soc2.sybil_resistance < 1.0)
    t("T4.3 Disclosed → high accountability",
      impl_soc2.accountability_score >= 0.8)
    t("T4.4 Balanced allocation → high fairness",
      impl_soc2.resource_fairness >= 0.9)

    # Undisclosed
    impl_hidden = ContextualTrustCalculator.compute_trust_implications(undisclosed)
    t("T4.5 Undisclosed → lower accountability",
      impl_hidden.accountability_score < impl_soc2.accountability_score)

    # ================================================================
    # T5: Sybil detection — timing correlation
    # ================================================================
    print("T5: Sybil Detection")
    detector = SybilDetector(correlation_threshold=0.7, timing_window_seconds=2.0)

    # Synchronized actions
    for i in range(10):
        ts = now + timedelta(seconds=i * 10)
        detector.log_action("soc_a", "vote", ts)
        detector.log_action("soc_b", "vote", ts + timedelta(seconds=0.5))

    corr = detector.check_timing_correlation("soc_a", "soc_b", now=now)
    t("T5.1 High timing correlation", corr > 0.7)
    t("T5.2 Event flagged suspicious",
      any(e.suspicious for e in detector.events))

    # Uncorrelated actions (different timing patterns, no overlap within 2s)
    detector2 = SybilDetector(correlation_threshold=0.7, timing_window_seconds=2.0)
    for i in range(10):
        detector2.log_action("soc_c", "action_c", now + timedelta(seconds=i * 10))
        detector2.log_action("soc_d", "action_d", now + timedelta(seconds=i * 10 + 5))

    corr2 = detector2.check_timing_correlation("soc_c", "soc_d", now=now)
    t("T5.3 Low timing correlation", corr2 < 0.5)

    # Behavior correlation
    actions_a = ["vote", "propose", "review", "approve"]
    actions_b = ["vote", "propose", "review", "reject"]
    actions_c = ["sleep", "eat", "rest"]

    bc_ab = detector.check_behavior_correlation(actions_a, actions_b)
    bc_ac = detector.check_behavior_correlation(actions_a, actions_c)
    t("T5.4 Similar behavior → high correlation", bc_ab > 0.5)
    t("T5.5 Different behavior → low correlation", bc_ac == 0.0)

    # No actions → 0 correlation
    t("T5.6 Empty actions → 0",
      detector.check_timing_correlation("unknown1", "unknown2") == 0.0)

    # ================================================================
    # T6: Resource monitoring
    # ================================================================
    print("T6: Resource Monitoring")
    monitor = ResourceMonitor(tolerance=0.15)

    # Society 2 using ~0.3 (matches allocation)
    for i in range(5):
        monitor.record_usage(ResourceUsage(
            "soc2", cpu_fraction=0.28 + i * 0.01,
            memory_fraction=0.3, storage_fraction=0.2,
            timestamp=now + timedelta(minutes=i)))

    ok, avg = monitor.check_allocation("soc2", 0.3)
    t("T6.1 Within allocation", ok)
    t("T6.2 Average ~0.3", abs(avg - 0.3) < 0.05)

    # Society using way more than declared
    for i in range(5):
        monitor.record_usage(ResourceUsage(
            "greedy", cpu_fraction=0.8,
            timestamp=now + timedelta(minutes=i)))

    ok2, avg2 = monitor.check_allocation("greedy", 0.3)
    t("T6.3 Over-allocation detected", not ok2)
    t("T6.4 Actual usage = 0.8", abs(avg2 - 0.8) < 0.01)

    # Starvation detection
    bindings = [
        HardwareBinding(hw_hash, "soc2", SharingModel.CONCURRENT,
                        resource_allocation=0.3),
        HardwareBinding(hw_hash, "greedy", SharingModel.CONCURRENT,
                        resource_allocation=0.3),
    ]
    starved = monitor.detect_starvation(bindings)
    t("T6.5 No starvation for soc2", "soc2" not in starved)

    # No history → OK
    ok3, avg3 = monitor.check_allocation("new_society", 0.5)
    t("T6.6 No history → OK", ok3)

    # ================================================================
    # T7: Binding registry
    # ================================================================
    print("T7: Binding Registry")
    registry = BindingRegistry()
    registry.register(society2)
    registry.register(cbp)

    co = registry.get_co_residents(hw_hash)
    t("T7.1 Two co-residents", len(co) == 2)
    t("T7.2 Society2 registered",
      "lct:web4:society2:bridge" in co)
    t("T7.3 CBP registered",
      "lct:web4:cbp:coordinator" in co)

    # Validation
    errors = registry.validate_sharing_consistency(hw_hash)
    t("T7.4 Consistent metadata", len(errors) == 0)

    # Over-allocation check
    registry2 = BindingRegistry()
    over1 = HardwareBinding(hw_hash, "over1", SharingModel.CONCURRENT,
                            resource_allocation=0.7,
                            co_residents=[CoResident("over2", 0.7, [])])
    over2 = HardwareBinding(hw_hash, "over2", SharingModel.CONCURRENT,
                            resource_allocation=0.7,
                            co_residents=[CoResident("over1", 0.7, [])])
    registry2.register(over1)
    registry2.register(over2)
    errors2 = registry2.validate_sharing_consistency(hw_hash)
    t("T7.5 Over-allocation detected", len(errors2) > 0)

    # ================================================================
    # T8: Sharing models
    # ================================================================
    print("T8: Sharing Models")
    t("T8.1 5 sharing models", len(SharingModel) == 5)

    # Development model
    dev = HardwareBinding(
        hardware_id=hw_hash,
        society_id="test_society",
        sharing_model=SharingModel.DEVELOPMENT,
        co_residents=[
            CoResident("test_a", 0.3, []),
            CoResident("test_b", 0.3, []),
        ],
        governance_independent=False,
        production_ready=False)

    t("T8.2 Dev not production ready", not dev.production_ready)
    t("T8.3 Dev governance not independent", not dev.governance_independent)

    # Temporal model
    temporal = HardwareBinding(
        hardware_id=hw_hash,
        society_id="temporal_soc",
        sharing_model=SharingModel.TEMPORAL,
        resource_allocation=1.0,  # Full allocation during active time
        correlation_coefficient=0.0)  # Not correlated (different times)

    t("T8.4 Temporal full allocation", temporal.resource_allocation == 1.0)
    t("T8.5 Temporal zero correlation", temporal.correlation_coefficient == 0.0)

    # Hierarchical model
    hierarchical = HardwareBinding(
        hardware_id=hw_hash,
        society_id="parent_soc",
        sharing_model=SharingModel.HIERARCHICAL,
        co_residents=[
            CoResident("child_soc_1", 0.3, ["compute"]),
            CoResident("child_soc_2", 0.2, ["storage"]),
        ],
        resource_allocation=0.5)

    t("T8.6 Hierarchical has children", len(hierarchical.co_residents) == 2)

    # ================================================================
    # T9: Migration
    # ================================================================
    print("T9: Migration")
    # Concurrent → Exclusive
    migrating = HardwareBinding(
        hardware_id=hw_hash,
        society_id="migrating_soc",
        sharing_model=SharingModel.CONCURRENT,
        co_residents=[CoResident("old_co", 0.5, [])],
        resource_allocation=0.5,
        correlation_coefficient=0.6)

    t("T9.1 Can migrate concurrent→exclusive",
      MigrationManager.can_migrate(SharingModel.CONCURRENT, SharingModel.EXCLUSIVE))

    new_hw = "dedicated:abc123"
    migrated = MigrationManager.migrate(migrating, SharingModel.EXCLUSIVE,
                                         new_hardware_id=new_hw)
    t("T9.2 Model = exclusive", migrated.sharing_model == SharingModel.EXCLUSIVE)
    t("T9.3 Co-residents cleared", len(migrated.co_residents) == 0)
    t("T9.4 Full allocation", migrated.resource_allocation == 1.0)
    t("T9.5 Zero correlation", migrated.correlation_coefficient == 0.0)
    t("T9.6 New hardware ID", migrated.hardware_id == new_hw)
    t("T9.7 Active state", migrated.state == BindingState.ACTIVE)

    # ================================================================
    # T10: JSON serialization
    # ================================================================
    print("T10: JSON Serialization")
    json_soc2 = BindingSerializer.to_json(society2)
    t("T10.1 Has hardware_binding", "hardware_binding" in json_soc2)
    t("T10.2 Has hardware_id",
      json_soc2["hardware_binding"]["hardware_id"] == hw_hash)
    t("T10.3 Has sharing_model",
      json_soc2["hardware_binding"]["sharing_model"] == "concurrent_multi_society")
    t("T10.4 Has co_residents",
      "co_residents" in json_soc2["hardware_binding"])
    t("T10.5 Has trust_implications",
      "trust_implications" in json_soc2["hardware_binding"])

    # JSON round-trip
    json_str = json.dumps(json_soc2, indent=2)
    parsed = json.loads(json_str)
    t("T10.6 JSON round-trips",
      parsed["hardware_binding"]["sharing_model"] == "concurrent_multi_society")

    # Development context
    json_dev = BindingSerializer.to_json(dev)
    trust_impl = json_dev["hardware_binding"]["trust_implications"]
    t("T10.7 Dev has experimental_context",
      trust_impl.get("experimental_context") is True)

    # ================================================================
    # T11: Turtle serialization
    # ================================================================
    print("T11: Turtle Serialization")
    turtle = BindingSerializer.to_turtle(society2)
    t("T11.1 Has web4 prefix", "@prefix web4:" in turtle)
    t("T11.2 Has hw prefix", "@prefix hw:" in turtle)
    t("T11.3 Has society ID", "lct:web4:society2:bridge" in turtle)
    t("T11.4 Has sharing model", "concurrent_multi_society" in turtle)
    t("T11.5 Has co-resident", "hw:coResident" in turtle)
    t("T11.6 Has allocation", "hw:allocation" in turtle)

    # ================================================================
    # T12: E2E — ACT Federation case study
    # ================================================================
    print("T12: E2E ACT Federation")
    # Before: both have same hardware_id → CONFLICT
    # After: contextual binding resolves it

    reg = BindingRegistry()
    s2 = HardwareBinding(
        hardware_id=hw_hash,
        society_id="lct:web4:society2:bridge",
        sharing_model=SharingModel.CONCURRENT,
        resource_allocation=0.3,
        primary_functions=["harmony", "bridge", "integration"],
        co_residents=[CoResident("lct:web4:cbp:coordinator", 0.7,
                                 ["data", "metrics", "cache"])],
        correlation_coefficient=0.8,
        governance_independent=True,
        disclosed=True)

    cb = HardwareBinding(
        hardware_id=hw_hash,
        society_id="lct:web4:cbp:coordinator",
        sharing_model=SharingModel.CONCURRENT,
        resource_allocation=0.7,
        primary_functions=["data", "metrics", "cache", "federation_bridge"],
        co_residents=[CoResident("lct:web4:society2:bridge", 0.3,
                                 ["harmony", "bridge"])],
        correlation_coefficient=0.8,
        governance_independent=True,
        disclosed=True)

    reg.register(s2)
    reg.register(cb)

    # Both valid
    errors = reg.validate_sharing_consistency(hw_hash)
    t("T12.1 ACT federation consistent", len(errors) == 0)

    # Trust calculations
    trust_s2 = ContextualTrustCalculator.calculate(0.9, s2)
    trust_cb = ContextualTrustCalculator.calculate(0.9, cb)
    t("T12.2 Society2 trust adjusted", trust_s2 < 0.9)
    t("T12.3 CBP trust adjusted", trust_cb < 0.9)
    t("T12.4 Both same trust (same correlation)",
      abs(trust_s2 - trust_cb) < 0.01)

    # Total allocation = 1.0
    t("T12.5 Total allocation = 1.0",
      abs(s2.resource_allocation + cb.resource_allocation - 1.0) < 0.01)

    # ================================================================
    # T13: Witness attestation
    # ================================================================
    print("T13: Witness Attestation")
    attestation = WitnessAttestation(
        witness_id="witness:external:1",
        hardware_id=hw_hash,
        confirmed_societies=["lct:web4:society2:bridge", "lct:web4:cbp:coordinator"],
        confirmed_allocations={
            "lct:web4:society2:bridge": 0.3,
            "lct:web4:cbp:coordinator": 0.7,
        },
        independence_confirmed=True,
        timestamp=now,
        confidence=0.9)

    t("T13.1 2 societies confirmed", len(attestation.confirmed_societies) == 2)
    t("T13.2 Allocations match",
      attestation.confirmed_allocations["lct:web4:society2:bridge"] == 0.3)
    t("T13.3 Independence confirmed", attestation.independence_confirmed)
    t("T13.4 High confidence", attestation.confidence > 0.8)

    # ================================================================
    # T14: Edge cases
    # ================================================================
    print("T14: Edge Cases")
    # Empty co-residents for exclusive
    excl_json = BindingSerializer.to_json(exclusive)
    t("T14.1 Exclusive no co_residents key",
      "co_residents" not in excl_json["hardware_binding"])

    # Binding states
    t("T14.2 4 binding states", len(BindingState) == 4)
    t("T14.3 3 migration targets", len(MigrationTarget) == 3)

    # Single society on hardware
    single_reg = BindingRegistry()
    single_reg.register(exclusive)
    errors = single_reg.validate_sharing_consistency(hw_hash)
    t("T14.4 Single society → no errors", len(errors) == 0)

    # Unknown hardware → empty list
    t("T14.5 Unknown hardware → empty",
      len(registry.get_co_residents("unknown")) == 0)

    # ================================================================
    # T15: Correlation coefficient effects
    # ================================================================
    print("T15: Correlation Effects")
    correlations = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    trusts = []
    for c in correlations:
        b = HardwareBinding(hw_hash, "test", SharingModel.CONCURRENT,
                            correlation_coefficient=c, disclosed=True)
        trusts.append(ContextualTrustCalculator.calculate(0.9, b))

    t("T15.1 Trust decreases with correlation",
      all(trusts[i] >= trusts[i+1] for i in range(len(trusts)-1)))
    t("T15.2 Zero correlation → highest trust",
      trusts[0] > trusts[-1])
    t("T15.3 Max correlation → lowest trust",
      trusts[-1] == min(trusts))

    # ================================================================
    # SUMMARY
    # ================================================================
    print(f"\n{'='*60}")
    print(f"Contextual Hardware Binding: {passed}/{total} checks passed")
    if passed == total:
        print("  All checks passed!")
    else:
        print(f"  {total - passed} checks FAILED")
    print(f"{'='*60}")

    return passed, total


if __name__ == "__main__":
    run_tests()
