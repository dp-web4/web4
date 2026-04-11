"""
Parameter Governance & Adaptive Tuning
=======================================

Implements operator-facing configuration for Web4 federations:
parameter hierarchies, adaptive tuning from federation topology,
safety bound validation, migration between parameter versions,
and multi-tenant parameter isolation.

Sections:
  S1  — Parameter Schema & Validation
  S2  — Federation Size Auto-Tuning
  S3  — Trust Dynamics Parameters
  S4  — ATP Economics Parameters
  S5  — Consensus Parameters
  S6  — Safety Bound Verification
  S7  — Parameter Migration & Versioning
  S8  — Multi-Tenant Isolation
  S9  — Sensitivity Analysis
  S10 — Configuration Composition
  S11 — Performance & Scale
"""

from __future__ import annotations
import math
import random
import copy
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Set
from enum import Enum


# ============================================================
# S1 — Parameter Schema & Validation
# ============================================================

class ParamType(Enum):
    FLOAT = "float"
    INT = "int"
    BOOL = "bool"
    STRING = "string"


@dataclass
class ParamSpec:
    name: str
    param_type: ParamType
    default: Any
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    description: str = ""
    required: bool = True
    category: str = "general"

    def validate(self, value: Any) -> Tuple[bool, str]:
        if value is None and self.required:
            return False, f"{self.name}: required but missing"

        if self.param_type == ParamType.FLOAT:
            if not isinstance(value, (int, float)):
                return False, f"{self.name}: expected float, got {type(value).__name__}"
            if self.min_val is not None and value < self.min_val:
                return False, f"{self.name}: {value} < min {self.min_val}"
            if self.max_val is not None and value > self.max_val:
                return False, f"{self.name}: {value} > max {self.max_val}"
        elif self.param_type == ParamType.INT:
            if not isinstance(value, int):
                return False, f"{self.name}: expected int, got {type(value).__name__}"
            if self.min_val is not None and value < self.min_val:
                return False, f"{self.name}: {value} < min {self.min_val}"
            if self.max_val is not None and value > self.max_val:
                return False, f"{self.name}: {value} > max {self.max_val}"
        elif self.param_type == ParamType.BOOL:
            if not isinstance(value, bool):
                return False, f"{self.name}: expected bool"

        return True, ""


@dataclass
class ParameterSet:
    """Named, validated set of configuration parameters."""
    name: str
    version: int = 1
    params: Dict[str, Any] = field(default_factory=dict)
    specs: Dict[str, ParamSpec] = field(default_factory=dict)

    def register(self, spec: ParamSpec):
        self.specs[spec.name] = spec
        if spec.name not in self.params:
            self.params[spec.name] = spec.default

    def set(self, name: str, value: Any) -> Tuple[bool, str]:
        if name not in self.specs:
            return False, f"Unknown parameter: {name}"
        valid, msg = self.specs[name].validate(value)
        if valid:
            self.params[name] = value
        return valid, msg

    def get(self, name: str, default: Any = None) -> Any:
        return self.params.get(name, default)

    def validate_all(self) -> List[str]:
        errors = []
        for name, spec in self.specs.items():
            value = self.params.get(name)
            if value is None and spec.required:
                errors.append(f"{name}: required but missing")
            elif value is not None:
                valid, msg = spec.validate(value)
                if not valid:
                    errors.append(msg)
        return errors

    def diff(self, other: 'ParameterSet') -> Dict[str, Tuple[Any, Any]]:
        """Return parameters that differ between two sets."""
        changes = {}
        all_keys = set(self.params.keys()) | set(other.params.keys())
        for key in all_keys:
            v1 = self.params.get(key)
            v2 = other.params.get(key)
            if v1 != v2:
                changes[key] = (v1, v2)
        return changes


def test_section_1():
    checks = []

    ps = ParameterSet("test")
    ps.register(ParamSpec("trust_decay", ParamType.FLOAT, 0.01, 0.001, 0.1,
                          "Trust decay rate per period"))
    ps.register(ParamSpec("max_entities", ParamType.INT, 1000, 10, 100000))
    ps.register(ParamSpec("enable_sybil_check", ParamType.BOOL, True))

    # Defaults set
    checks.append(("defaults_set", ps.get("trust_decay") == 0.01))

    # Valid set
    ok, msg = ps.set("trust_decay", 0.05)
    checks.append(("valid_set", ok and ps.get("trust_decay") == 0.05))

    # Out of range
    ok, msg = ps.set("trust_decay", 0.5)
    checks.append(("out_of_range", not ok))

    # Wrong type
    ok, msg = ps.set("max_entities", 3.14)
    checks.append(("wrong_type", not ok))

    # Unknown parameter
    ok, msg = ps.set("nonexistent", 42)
    checks.append(("unknown_param", not ok))

    # Validate all
    ps.set("trust_decay", 0.02)
    errors = ps.validate_all()
    checks.append(("all_valid", len(errors) == 0))

    # Diff
    ps2 = ParameterSet("test2")
    ps2.register(ParamSpec("trust_decay", ParamType.FLOAT, 0.01))
    ps2.register(ParamSpec("max_entities", ParamType.INT, 1000))
    ps2.set("trust_decay", 0.03)
    diff = ps.diff(ps2)
    checks.append(("diff_found", "trust_decay" in diff))

    return checks


# ============================================================
# S2 — Federation Size Auto-Tuning
# ============================================================

@dataclass
class FederationSizeConfig:
    """Auto-derive parameters from federation size n."""

    @staticmethod
    def derive(n: int) -> Dict[str, Any]:
        """Derive optimal parameters for federation of size n."""
        return {
            # CFL stability: α·dt/dx² ≤ 0.5
            "diffusion_alpha": min(0.4, 0.5 / max(1, n / 100)),
            "diffusion_dt": 0.1,
            "diffusion_dx": 1.0,

            # Trust gravity field: σ = n/4 for edge force propagation
            "gravity_sigma": max(2.0, n / 4.0),

            # Gossip: fan_out = ceil(log2(n)) for O(log n) convergence
            "gossip_fan_out": max(2, math.ceil(math.log2(max(2, n)))),
            "gossip_max_rounds": math.ceil(2 * math.log2(max(2, n))),

            # BFT: max faults = (n-1)/3
            "bft_max_faults": (n - 1) // 3,
            "bft_quorum": 2 * ((n - 1) // 3) + 1,

            # ATP: initial allocation scaled to n
            "initial_atp_per_entity": max(50.0, 1000.0 / math.sqrt(n)),
            "total_initial_supply": n * max(50.0, 1000.0 / math.sqrt(n)),
            "transaction_fee_rate": 0.05,

            # Sybil: hardware cost threshold
            "sybil_hardware_cost": 250.0,
            "sybil_profitable_threshold": max(3, n // 10),

            # Inequality bounds
            "target_gini": min(0.5, 0.3 + 0.02 * math.log(max(1, n))),
            "max_top1_share": min(0.5, 1.0 / math.sqrt(n)),
            "anti_concentration_cap": max(0.05, 1.0 / math.sqrt(n)),
        }

    @staticmethod
    def verify_cfl(alpha: float, dt: float, dx: float) -> bool:
        """Verify CFL stability condition."""
        return alpha * dt / (dx ** 2) <= 0.5


def test_section_2():
    checks = []

    # Small federation
    small = FederationSizeConfig.derive(10)
    checks.append(("small_gossip", small["gossip_fan_out"] >= 2))
    checks.append(("small_bft", small["bft_max_faults"] == 3))

    # Medium federation
    med = FederationSizeConfig.derive(100)
    checks.append(("med_gossip", med["gossip_fan_out"] == 7))
    checks.append(("med_sigma", med["gravity_sigma"] == 25.0))

    # Large federation
    large = FederationSizeConfig.derive(1000)
    checks.append(("large_gossip", large["gossip_fan_out"] == 10))
    checks.append(("large_bft", large["bft_max_faults"] == 333))

    # CFL verification
    checks.append(("cfl_small", FederationSizeConfig.verify_cfl(
        small["diffusion_alpha"], small["diffusion_dt"], small["diffusion_dx"])))
    checks.append(("cfl_large", FederationSizeConfig.verify_cfl(
        large["diffusion_alpha"], large["diffusion_dt"], large["diffusion_dx"])))

    # ATP scales inversely with sqrt(n)
    checks.append(("atp_decreases",
                    small["initial_atp_per_entity"] > large["initial_atp_per_entity"]))

    # Anti-concentration decreases with size
    checks.append(("anti_conc_shrinks",
                    small["anti_concentration_cap"] > large["anti_concentration_cap"]))

    return checks


# ============================================================
# S3 — Trust Dynamics Parameters
# ============================================================

@dataclass
class TrustDynamicsConfig:
    """Parameters governing trust evolution."""
    decay_rate: float = 0.01         # per period
    update_step: float = 0.02        # per quality observation
    quality_midpoint: float = 0.5    # neutral quality
    min_trust: float = 0.0
    max_trust: float = 0.95          # never reaches 1.0
    diminishing_base: float = 0.8    # repeated action dampening
    diminishing_floor: float = 0.1   # minimum learning rate

    def trust_delta(self, quality: float) -> float:
        return self.update_step * (quality - self.quality_midpoint)

    def diminished_delta(self, quality: float, repetition: int) -> float:
        factor = max(self.diminishing_floor,
                     self.diminishing_base ** (repetition - 1))
        return self.trust_delta(quality) * factor

    def clamp(self, trust: float) -> float:
        return max(self.min_trust, min(self.max_trust, trust))

    def convergence_time(self, initial: float, target: float) -> int:
        """Estimate periods needed to reach target from initial with max quality."""
        if target <= initial:
            return 0
        current = initial
        steps = 0
        while current < target and steps < 10000:
            delta = self.trust_delta(1.0)  # max quality
            current = self.clamp(current + delta)
            steps += 1
        return steps


def test_section_3():
    checks = []

    config = TrustDynamicsConfig()

    # Delta at midpoint is zero
    checks.append(("zero_at_midpoint", config.trust_delta(0.5) == 0.0))

    # Positive delta for high quality
    checks.append(("positive_high", config.trust_delta(0.8) > 0))

    # Negative delta for low quality
    checks.append(("negative_low", config.trust_delta(0.2) < 0))

    # Diminishing returns
    d1 = config.diminished_delta(0.8, 1)
    d3 = config.diminished_delta(0.8, 3)
    d10 = config.diminished_delta(0.8, 10)
    checks.append(("diminishing_decreases", d1 > d3 > d10))
    checks.append(("diminishing_floor", d10 >= config.diminishing_floor * config.trust_delta(0.8) - 0.001))

    # Convergence time
    steps = config.convergence_time(0.3, 0.8)
    checks.append(("convergence_bounded", 0 < steps < 100))

    # Clamping
    checks.append(("clamp_max", config.clamp(1.5) == 0.95))
    checks.append(("clamp_min", config.clamp(-0.5) == 0.0))

    return checks


# ============================================================
# S4 — ATP Economics Parameters
# ============================================================

@dataclass
class ATPEconomicsConfig:
    """Parameters for ATP economic model."""
    initial_supply_per_entity: float = 100.0
    transaction_fee_rate: float = 0.05
    max_balance: float = 10000.0
    min_transfer: float = 1.0
    staking_lock_periods: int = 5
    reward_pool_fraction: float = 0.1  # fraction of fees → rewards
    demurrage_rate: float = 0.001      # per-period balance decay

    def validate(self) -> List[str]:
        errors = []
        if self.transaction_fee_rate < 0 or self.transaction_fee_rate > 1:
            errors.append("fee_rate must be in [0, 1]")
        if self.initial_supply_per_entity <= 0:
            errors.append("initial_supply must be positive")
        if self.max_balance < self.initial_supply_per_entity:
            errors.append("max_balance must be >= initial_supply")
        if self.reward_pool_fraction < 0 or self.reward_pool_fraction > 1:
            errors.append("reward_pool_fraction must be in [0, 1]")
        if self.demurrage_rate < 0:
            errors.append("demurrage_rate must be non-negative")
        return errors

    def effective_transfer(self, amount: float) -> Tuple[float, float]:
        """Return (amount_received, fee)."""
        fee = amount * self.transaction_fee_rate
        return amount - fee, fee

    def sybil_break_even(self, n_identities: int, hardware_cost: float = 250.0) -> float:
        """Net gain/loss for n sybil identities."""
        total_grant = n_identities * self.initial_supply_per_entity
        total_cost = n_identities * hardware_cost
        return total_grant - total_cost


def test_section_4():
    checks = []

    config = ATPEconomicsConfig()

    # Validation
    errors = config.validate()
    checks.append(("default_valid", len(errors) == 0))

    bad = ATPEconomicsConfig(transaction_fee_rate=1.5)
    checks.append(("bad_fee_rate", len(bad.validate()) > 0))

    bad2 = ATPEconomicsConfig(max_balance=50.0, initial_supply_per_entity=100.0)
    checks.append(("bad_max_balance", len(bad2.validate()) > 0))

    # Effective transfer
    received, fee = config.effective_transfer(100.0)
    checks.append(("fee_correct", abs(fee - 5.0) < 0.01))
    checks.append(("received_correct", abs(received - 95.0) < 0.01))

    # Sybil analysis
    gain_1 = config.sybil_break_even(1)
    gain_5 = config.sybil_break_even(5)
    checks.append(("single_loss", gain_1 < 0))  # 100 - 250 = -150
    checks.append(("sybil_5_loss", gain_5 < 0))  # 500 - 1250 = -750

    # Without hardware cost
    gain_no_hw = config.sybil_break_even(5, hardware_cost=0.0)
    checks.append(("no_hw_profitable", gain_no_hw > 0))

    return checks


# ============================================================
# S5 — Consensus Parameters
# ============================================================

@dataclass
class ConsensusConfig:
    """Parameters for federation consensus."""
    n_nodes: int = 10
    protocol: str = "pbft"  # "pbft", "raft", "gossip"
    timeout_ms: int = 5000
    max_rounds: int = 100

    @property
    def max_faults(self) -> int:
        if self.protocol == "pbft":
            return (self.n_nodes - 1) // 3
        elif self.protocol == "raft":
            return (self.n_nodes - 1) // 2
        return 0

    @property
    def quorum(self) -> int:
        if self.protocol == "pbft":
            return 2 * self.max_faults + 1
        elif self.protocol == "raft":
            return self.max_faults + 1
        return self.n_nodes

    @property
    def message_complexity(self) -> str:
        if self.protocol == "pbft":
            return f"O(n²) = {self.n_nodes ** 2}"
        elif self.protocol == "raft":
            return f"O(n) = {self.n_nodes}"
        elif self.protocol == "gossip":
            fan = max(2, math.ceil(math.log2(self.n_nodes)))
            return f"O(n·log(n)) = {self.n_nodes * fan}"
        return "unknown"

    def validate(self) -> List[str]:
        errors = []
        if self.n_nodes < 4 and self.protocol == "pbft":
            errors.append("PBFT requires >= 4 nodes")
        if self.n_nodes < 3 and self.protocol == "raft":
            errors.append("Raft requires >= 3 nodes")
        if self.timeout_ms < 100:
            errors.append("Timeout too low (< 100ms)")
        return errors


def test_section_5():
    checks = []

    pbft = ConsensusConfig(n_nodes=10, protocol="pbft")
    checks.append(("pbft_faults", pbft.max_faults == 3))
    checks.append(("pbft_quorum", pbft.quorum == 7))

    raft = ConsensusConfig(n_nodes=5, protocol="raft")
    checks.append(("raft_faults", raft.max_faults == 2))
    checks.append(("raft_quorum", raft.quorum == 3))

    # Validation
    bad = ConsensusConfig(n_nodes=2, protocol="pbft")
    checks.append(("pbft_too_small", len(bad.validate()) > 0))

    good = ConsensusConfig(n_nodes=100, protocol="pbft")
    checks.append(("large_valid", len(good.validate()) == 0))

    # Message complexity
    checks.append(("pbft_n2", "100" in pbft.message_complexity))
    checks.append(("raft_n", "5" in raft.message_complexity))

    return checks


# ============================================================
# S6 — Safety Bound Verification
# ============================================================

@dataclass
class SafetyVerifier:
    """Verify that a parameter configuration satisfies safety bounds."""

    @staticmethod
    def verify_cfl(alpha: float, dt: float, dx: float) -> Tuple[bool, str]:
        ratio = alpha * dt / (dx ** 2)
        if ratio > 0.5:
            return False, f"CFL violation: α·dt/dx² = {ratio:.4f} > 0.5"
        return True, f"CFL satisfied: {ratio:.4f} ≤ 0.5"

    @staticmethod
    def verify_sybil_resistance(initial_grant: float, hardware_cost: float,
                                registration_fee: float = 0.0) -> Tuple[bool, str]:
        net = initial_grant - hardware_cost - registration_fee
        if net > 0:
            return False, f"Sybil profitable: net gain {net:.2f} per identity"
        return True, f"Sybil unprofitable: net loss {abs(net):.2f} per identity"

    @staticmethod
    def verify_inequality_bound(n: int, target_gini: float,
                                allocation: str = "sqrt") -> Tuple[bool, str]:
        # Theoretical Gini for different allocation schemes
        if allocation == "flat":
            expected_gini = 0.0
        elif allocation == "proportional":
            # For uniform trust distribution, Gini ≈ 1/3
            expected_gini = 0.33
        elif allocation == "sqrt":
            # sqrt reduces concentration: Gini ≈ 0.15-0.25
            expected_gini = 0.20
        else:
            expected_gini = 0.5

        if expected_gini > target_gini:
            return False, f"Expected Gini {expected_gini:.2f} > target {target_gini:.2f}"
        return True, f"Expected Gini {expected_gini:.2f} ≤ target {target_gini:.2f}"

    @staticmethod
    def verify_consensus_safety(n: int, f: int, protocol: str) -> Tuple[bool, str]:
        if protocol == "pbft":
            required = 3 * f + 1
            if n < required:
                return False, f"PBFT: need n ≥ 3f+1 = {required}, have {n}"
        elif protocol == "raft":
            required = 2 * f + 1
            if n < required:
                return False, f"Raft: need n ≥ 2f+1 = {required}, have {n}"
        return True, f"Consensus safety verified for n={n}, f={f}"

    @staticmethod
    def verify_conservation(total_minted: float, total_balances: float,
                            total_fees: float, total_staked: float) -> Tuple[bool, str]:
        expected = total_minted
        actual = total_balances + total_fees + total_staked
        diff = abs(expected - actual)
        if diff > 0.01:
            return False, f"Conservation violation: |{expected:.2f} - {actual:.2f}| = {diff:.4f}"
        return True, "Conservation holds"


def test_section_6():
    checks = []
    v = SafetyVerifier()

    # CFL
    ok, _ = v.verify_cfl(0.4, 0.1, 1.0)
    checks.append(("cfl_ok", ok))
    ok, _ = v.verify_cfl(1.0, 1.0, 1.0)
    checks.append(("cfl_fail", not ok))

    # Sybil
    ok, _ = v.verify_sybil_resistance(100.0, 250.0)
    checks.append(("sybil_resistant", ok))
    ok, _ = v.verify_sybil_resistance(500.0, 100.0)
    checks.append(("sybil_vulnerable", not ok))

    # Inequality
    ok, _ = v.verify_inequality_bound(100, 0.5, "sqrt")
    checks.append(("gini_ok", ok))
    ok, _ = v.verify_inequality_bound(100, 0.1, "proportional")
    checks.append(("gini_fail", not ok))

    # Consensus
    ok, _ = v.verify_consensus_safety(10, 3, "pbft")
    checks.append(("consensus_ok", ok))
    ok, _ = v.verify_consensus_safety(5, 3, "pbft")
    checks.append(("consensus_fail", not ok))

    # Conservation
    ok, _ = v.verify_conservation(1000.0, 900.0, 50.0, 50.0)
    checks.append(("conservation_ok", ok))
    ok, _ = v.verify_conservation(1000.0, 800.0, 50.0, 50.0)
    checks.append(("conservation_fail", not ok))

    return checks


# ============================================================
# S7 — Parameter Migration & Versioning
# ============================================================

@dataclass
class ParameterMigration:
    """Migrate between parameter set versions."""
    from_version: int
    to_version: int
    transforms: Dict[str, Any]  # {param_name: new_default_or_transform}
    removals: Set[str] = field(default_factory=set)
    additions: Dict[str, ParamSpec] = field(default_factory=dict)

    def apply(self, params: ParameterSet) -> ParameterSet:
        if params.version != self.from_version:
            raise ValueError(f"Expected version {self.from_version}, got {params.version}")

        new_params = ParameterSet(name=params.name, version=self.to_version)

        # Copy specs and values, applying transforms
        for name, spec in params.specs.items():
            if name in self.removals:
                continue
            new_params.register(spec)
            if name in self.transforms:
                transform = self.transforms[name]
                if callable(transform):
                    new_params.set(name, transform(params.get(name)))
                else:
                    new_params.set(name, transform)
            else:
                new_params.set(name, params.get(name))

        # Add new parameters
        for name, spec in self.additions.items():
            new_params.register(spec)

        return new_params


def test_section_7():
    checks = []

    # Create v1 config
    v1 = ParameterSet("test", version=1)
    v1.register(ParamSpec("trust_decay", ParamType.FLOAT, 0.01))
    v1.register(ParamSpec("old_param", ParamType.FLOAT, 0.5))
    v1.set("trust_decay", 0.02)

    # Migration v1 → v2
    migration = ParameterMigration(
        from_version=1,
        to_version=2,
        transforms={"trust_decay": lambda v: v * 2},  # double the decay
        removals={"old_param"},
        additions={"new_param": ParamSpec("new_param", ParamType.FLOAT, 0.3, 0.0, 1.0)},
    )

    v2 = migration.apply(v1)
    checks.append(("version_bumped", v2.version == 2))
    checks.append(("transform_applied", abs(v2.get("trust_decay") - 0.04) < 0.001))
    checks.append(("old_removed", v2.get("old_param") is None))
    checks.append(("new_added", v2.get("new_param") == 0.3))

    # Wrong version raises
    try:
        migration.apply(v2)
        checks.append(("wrong_version_error", False))
    except ValueError:
        checks.append(("wrong_version_error", True))

    # Static transform (not callable)
    migration2 = ParameterMigration(
        from_version=2, to_version=3,
        transforms={"trust_decay": 0.05},
    )
    v3 = migration2.apply(v2)
    checks.append(("static_transform", abs(v3.get("trust_decay") - 0.05) < 0.001))

    return checks


# ============================================================
# S8 — Multi-Tenant Isolation
# ============================================================

@dataclass
class TenantConfig:
    tenant_id: str
    params: ParameterSet
    parent_tenant: Optional[str] = None


@dataclass
class MultiTenantManager:
    """Manage parameter sets for multiple tenants with inheritance."""
    tenants: Dict[str, TenantConfig] = field(default_factory=dict)
    global_defaults: ParameterSet = field(default_factory=lambda: ParameterSet("global"))

    def create_tenant(self, tenant_id: str, parent_id: Optional[str] = None) -> TenantConfig:
        if parent_id and parent_id in self.tenants:
            parent = self.tenants[parent_id]
            params = ParameterSet(f"tenant-{tenant_id}", version=parent.params.version)
            for name, spec in parent.params.specs.items():
                params.register(spec)
                params.set(name, parent.params.get(name))
        else:
            params = ParameterSet(f"tenant-{tenant_id}",
                                  version=self.global_defaults.version)
            for name, spec in self.global_defaults.specs.items():
                params.register(spec)
                params.set(name, self.global_defaults.get(name))

        config = TenantConfig(tenant_id, params, parent_tenant=parent_id)
        self.tenants[tenant_id] = config
        return config

    def get_effective(self, tenant_id: str, param_name: str) -> Any:
        """Get parameter value with inheritance chain."""
        if tenant_id not in self.tenants:
            return self.global_defaults.get(param_name)
        config = self.tenants[tenant_id]
        value = config.params.get(param_name)
        if value is not None:
            return value
        if config.parent_tenant:
            return self.get_effective(config.parent_tenant, param_name)
        return self.global_defaults.get(param_name)

    def isolation_check(self) -> bool:
        """Verify no tenant can see another tenant's params."""
        for t1_id, t1 in self.tenants.items():
            for t2_id, t2 in self.tenants.items():
                if t1_id != t2_id and t1.parent_tenant != t2_id and t2.parent_tenant != t1_id:
                    # Non-related tenants should have independent param objects
                    if t1.params is t2.params:
                        return False
        return True


def test_section_8():
    checks = []

    mgr = MultiTenantManager()
    mgr.global_defaults.register(ParamSpec("trust_decay", ParamType.FLOAT, 0.01))
    mgr.global_defaults.register(ParamSpec("max_entities", ParamType.INT, 1000))

    # Create tenants
    t1 = mgr.create_tenant("alpha")
    t2 = mgr.create_tenant("beta")
    t1.params.set("trust_decay", 0.05)

    checks.append(("tenant_created", len(mgr.tenants) == 2))
    checks.append(("tenant_override", mgr.get_effective("alpha", "trust_decay") == 0.05))
    checks.append(("tenant_default", mgr.get_effective("beta", "trust_decay") == 0.01))

    # Isolation
    checks.append(("isolation", mgr.isolation_check()))
    t2.params.set("trust_decay", 0.03)
    checks.append(("no_crosstalk", mgr.get_effective("alpha", "trust_decay") == 0.05))

    # Inheritance
    child = mgr.create_tenant("alpha-sub", parent_id="alpha")
    checks.append(("inherited", mgr.get_effective("alpha-sub", "trust_decay") == 0.05))
    child.params.set("trust_decay", 0.07)
    checks.append(("child_override", mgr.get_effective("alpha-sub", "trust_decay") == 0.07))
    checks.append(("parent_unchanged", mgr.get_effective("alpha", "trust_decay") == 0.05))

    return checks


# ============================================================
# S9 — Sensitivity Analysis
# ============================================================

def sensitivity_analysis(base_params: Dict[str, float],
                         evaluate: callable,
                         perturbation: float = 0.1) -> Dict[str, float]:
    """Compute sensitivity of output to each parameter via finite differences."""
    base_result = evaluate(base_params)
    sensitivities = {}

    for param, value in base_params.items():
        if value == 0:
            continue
        perturbed = dict(base_params)
        delta = abs(value) * perturbation
        perturbed[param] = value + delta
        perturbed_result = evaluate(perturbed)
        sensitivity = (perturbed_result - base_result) / delta
        sensitivities[param] = sensitivity

    return sensitivities


def test_section_9():
    checks = []

    # Simple model: trust = talent * w1 + training * w2 + temperament * w3
    def trust_model(params):
        return (params["talent"] * params["w_talent"] +
                params["training"] * params["w_training"] +
                params["temperament"] * params["w_temperament"])

    base = {"talent": 0.6, "training": 0.5, "temperament": 0.7,
            "w_talent": 0.33, "w_training": 0.33, "w_temperament": 0.34}

    sens = sensitivity_analysis(base, trust_model)

    # Weights should be sensitive (changing weight changes output proportional to dim value)
    checks.append(("weight_sensitivity", all(abs(sens[f"w_{d}"]) > 0 for d in ["talent", "training", "temperament"])))

    # Dimension values should be sensitive (proportional to weight)
    checks.append(("dim_sensitivity", all(abs(sens[d]) > 0 for d in ["talent", "training", "temperament"])))

    # Higher weight → more sensitive to that dimension
    # talent weight sensitivity = talent value = 0.6
    # training weight sensitivity = training value = 0.5
    checks.append(("talent_more_sensitive", abs(sens["w_talent"]) > abs(sens["w_training"])))

    # Gini model: sqrt allocation reduces Gini sensitivity to trust distribution
    def gini_model(params):
        n = int(params["n_entities"])
        trusts = [params["base_trust"] + (params["trust_spread"] * i / (n - 1))
                  for i in range(n)]
        if params.get("sqrt_alloc", 0) > 0.5:
            total_sqrt = sum(math.sqrt(t) for t in trusts)
            alloc = [1000.0 * math.sqrt(t) / total_sqrt for t in trusts]
        else:
            total_t = sum(trusts)
            alloc = [1000.0 * t / total_t for t in trusts]
        sorted_a = sorted(alloc)
        n_a = len(sorted_a)
        total = sum(sorted_a)
        cum = 0.0
        area = 0.0
        for v in sorted_a:
            cum += v
            area += cum
        b = area / (n_a * total)
        return 1.0 - 2.0 * b + 1.0 / n_a

    base_gini = {"n_entities": 20.0, "base_trust": 0.1, "trust_spread": 0.8, "sqrt_alloc": 0.0}
    base_gini_sqrt = {"n_entities": 20.0, "base_trust": 0.1, "trust_spread": 0.8, "sqrt_alloc": 1.0}

    sens_prop = sensitivity_analysis(base_gini, gini_model)
    sens_sqrt = sensitivity_analysis(base_gini_sqrt, gini_model)

    # Sqrt allocation reduces sensitivity to trust_spread
    checks.append(("sqrt_reduces_sensitivity",
                    abs(sens_sqrt.get("trust_spread", 0)) < abs(sens_prop.get("trust_spread", 0))))

    return checks


# ============================================================
# S10 — Configuration Composition
# ============================================================

@dataclass
class ConfigLayer:
    """A layer in the configuration hierarchy."""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # higher priority overrides lower


def compose_configs(layers: List[ConfigLayer]) -> Dict[str, Any]:
    """Compose multiple config layers by priority (higher wins)."""
    sorted_layers = sorted(layers, key=lambda l: l.priority)
    result = {}
    for layer in sorted_layers:
        result.update(layer.params)
    return result


def validate_composed(config: Dict[str, Any],
                      constraints: List[callable]) -> List[str]:
    """Validate composed configuration against constraints."""
    errors = []
    for constraint in constraints:
        try:
            ok, msg = constraint(config)
            if not ok:
                errors.append(msg)
        except Exception as e:
            errors.append(f"Constraint error: {e}")
    return errors


def test_section_10():
    checks = []

    # Layer composition
    defaults = ConfigLayer("defaults", {"trust_decay": 0.01, "max_entities": 1000, "fee_rate": 0.05}, priority=0)
    env = ConfigLayer("environment", {"max_entities": 500}, priority=1)
    override = ConfigLayer("operator", {"trust_decay": 0.02}, priority=2)

    composed = compose_configs([defaults, env, override])
    checks.append(("override_applied", composed["trust_decay"] == 0.02))
    checks.append(("env_applied", composed["max_entities"] == 500))
    checks.append(("default_kept", composed["fee_rate"] == 0.05))

    # Validation constraints
    constraints = [
        lambda c: (c.get("fee_rate", 0) <= 0.1, "Fee rate too high"),
        lambda c: (c.get("max_entities", 0) >= 10, "Too few entities"),
        lambda c: (c.get("trust_decay", 0) > 0, "Trust decay must be positive"),
    ]

    errors = validate_composed(composed, constraints)
    checks.append(("all_constraints_pass", len(errors) == 0))

    # Bad config
    bad = ConfigLayer("bad", {"fee_rate": 0.5}, priority=3)
    bad_composed = compose_configs([defaults, bad])
    errors = validate_composed(bad_composed, constraints)
    checks.append(("constraint_violation", len(errors) > 0))

    # Priority order matters
    low = ConfigLayer("low", {"x": 1}, priority=1)
    high = ConfigLayer("high", {"x": 2}, priority=2)
    checks.append(("priority_order", compose_configs([low, high])["x"] == 2))
    checks.append(("priority_order_reversed", compose_configs([high, low])["x"] == 2))

    return checks


# ============================================================
# S11 — Performance & Scale
# ============================================================

def test_section_11():
    checks = []

    import time as time_mod

    # Parameter set creation at scale
    start = time_mod.perf_counter()
    for n in [10, 100, 1000, 10000]:
        config = FederationSizeConfig.derive(n)
        SafetyVerifier.verify_cfl(config["diffusion_alpha"], config["diffusion_dt"],
                                  config["diffusion_dx"])
    derive_time = time_mod.perf_counter() - start
    checks.append(("derive_fast", derive_time < 0.1))

    # Multi-tenant at scale
    mgr = MultiTenantManager()
    mgr.global_defaults.register(ParamSpec("decay", ParamType.FLOAT, 0.01, 0.0, 1.0))
    mgr.global_defaults.register(ParamSpec("entities", ParamType.INT, 100, 1, 100000))

    start = time_mod.perf_counter()
    for i in range(100):
        t = mgr.create_tenant(f"t{i}")
        t.params.set("decay", 0.01 + i * 0.001)
    tenant_time = time_mod.perf_counter() - start
    checks.append(("100_tenants_fast", tenant_time < 1.0))

    # Isolation at scale
    checks.append(("isolation_100", mgr.isolation_check()))

    # Sensitivity analysis performance
    def model(p):
        return sum(v * (i + 1) for i, (k, v) in enumerate(sorted(p.items())))

    big_params = {f"p{i}": random.uniform(0.1, 1.0) for i in range(50)}
    start = time_mod.perf_counter()
    sens = sensitivity_analysis(big_params, model)
    sens_time = time_mod.perf_counter() - start
    checks.append(("50_param_sensitivity_fast", sens_time < 1.0))
    checks.append(("50_sensitivities", len(sens) == 50))

    # Config composition at scale
    layers = [ConfigLayer(f"layer_{i}", {f"p{j}": random.random()
              for j in range(i, i + 10)}, priority=i) for i in range(100)]
    start = time_mod.perf_counter()
    composed = compose_configs(layers)
    compose_time = time_mod.perf_counter() - start
    checks.append(("100_layers_fast", compose_time < 0.1))

    return checks


# ============================================================
# Main
# ============================================================

def main():
    random.seed(42)

    sections = [
        ("S1 Parameter Schema & Validation", test_section_1),
        ("S2 Federation Size Auto-Tuning", test_section_2),
        ("S3 Trust Dynamics Parameters", test_section_3),
        ("S4 ATP Economics Parameters", test_section_4),
        ("S5 Consensus Parameters", test_section_5),
        ("S6 Safety Bound Verification", test_section_6),
        ("S7 Parameter Migration & Versioning", test_section_7),
        ("S8 Multi-Tenant Isolation", test_section_8),
        ("S9 Sensitivity Analysis", test_section_9),
        ("S10 Configuration Composition", test_section_10),
        ("S11 Performance & Scale", test_section_11),
    ]

    total_pass = 0
    total_fail = 0
    failures = []

    for name, test_fn in sections:
        checks = test_fn()
        passed = sum(1 for _, ok in checks if ok)
        failed = sum(1 for _, ok in checks if not ok)
        total_pass += passed
        total_fail += failed
        status = "✓" if failed == 0 else "✗"
        print(f"  {status} {name}: {passed}/{passed+failed}")
        for check_name, ok in checks:
            if not ok:
                failures.append(f"    FAIL: {check_name}")

    print(f"\nTotal: {total_pass}/{total_pass+total_fail}")
    if failures:
        print(f"\nFailed checks:")
        for f in failures:
            print(f)


if __name__ == "__main__":
    main()
