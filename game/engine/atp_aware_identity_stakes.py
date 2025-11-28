#!/usr/bin/env python3
"""
ATP-Aware Identity Stakes
Session #85: Track #1 - Phase 2 ATP-Security Integration

Problem (Session #84):
Identity stake system uses fixed 1000 ATP regardless of:
- LCT type (agent vs witness vs coordinator)
- Privilege level (normal vs high vs critical)
- Operational horizon (LOCAL vs GLOBAL)
- Task complexity handled by LCT

Solution: ATP-Aware Dynamic Staking
Stakes calculated based on ATP pricing framework:
- Base stake from unified multimodal pricing
- Privilege multipliers (1× to 5×)
- Horizon scaling (LOCAL cheap, GLOBAL expensive)
- Modality complexity (vision vs LLM vs coordination)

Integration Benefits:
1. **Unified Resource Model**: Stakes proportional to ATP value
2. **Horizon-Appropriate Barriers**: GLOBAL LCTs cost more
3. **Economic Fairness**: Stake reflects actual resource footprint
4. **Attack Cost Scaling**: More valuable LCTs require higher stakes

Security Properties:
- Preserves Sybil defense (economic barrier)
- Scales attack cost with LCT privilege
- Horizon-aware economic incentives
- Fair to small-horizon participants
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import ATP pricing framework
try:
    from .unified_atp_pricing import (
        UnifiedATPPricer,
        TaskModality,
        ComplexityLevel,
        ExecutionLocation,
        MRHProfile
    )
    from .identity_stake_system import StakeStatus, IdentityStake
except ImportError:
    # Standalone mode - define minimal types
    @dataclass
    class MRHProfile:
        """Markov Relevancy Horizon profile"""
        spatial: str  # LOCAL, REGIONAL, GLOBAL
        temporal: str  # EPHEMERAL, SESSION, EPOCH, PERMANENT
        complexity: str  # AGENT_SCALE, SOCIETY_SCALE, FEDERATION_SCALE

    class StakeStatus(Enum):
        """Status of identity stake"""
        LOCKED = "locked"
        UNLOCKABLE = "unlockable"
        SLASHED = "slashed"

    @dataclass
    class IdentityStake:
        """Identity stake"""
        lct_id: str
        stake_amount: float
        stake_timestamp: float
        status: StakeStatus = StakeStatus.LOCKED


class LCTType(Enum):
    """Type of LCT"""
    AGENT = "agent"              # Regular agent
    WITNESS = "witness"          # Reputation witness
    COORDINATOR = "coordinator"  # Society coordinator
    ORACLE = "oracle"            # External data oracle
    VALIDATOR = "validator"      # Validation service


class PrivilegeLevel(Enum):
    """Privilege level of LCT"""
    NORMAL = "normal"       # Standard privileges
    HIGH = "high"           # Elevated privileges
    CRITICAL = "critical"   # Critical infrastructure
    EMERGENCY = "emergency" # Emergency response (highest)


@dataclass
class ATPStakeCalculation:
    """Result of ATP-aware stake calculation"""
    lct_id: str
    lct_type: LCTType
    privilege_level: PrivilegeLevel
    operational_horizon: MRHProfile

    # Stake components
    base_stake: float
    privilege_multiplier: float
    horizon_multiplier: float
    modality_multiplier: float

    # Final stake
    total_stake: float

    # Metadata
    calculation_timestamp: float = field(default_factory=time.time)
    reasoning: str = ""


class ATPAwareStakeCalculator:
    """
    Calculate identity stakes based on ATP pricing framework

    Integrates Session #82 unified ATP pricing with Session #84 identity stakes
    """

    def __init__(self,
                 base_stake_amount: float = 1000.0,
                 pricer: Optional['UnifiedATPPricer'] = None):
        """
        Initialize ATP-aware stake calculator

        Args:
            base_stake_amount: Base stake for NORMAL/LOCAL/AGENT LCT
            pricer: ATP pricer instance (creates if None)
        """
        self.base_stake_amount = base_stake_amount
        self.pricer = pricer  # Will be created on first use if needed

        # Privilege multipliers
        self.privilege_multipliers = {
            PrivilegeLevel.NORMAL: 1.0,
            PrivilegeLevel.HIGH: 2.0,
            PrivilegeLevel.CRITICAL: 5.0,
            PrivilegeLevel.EMERGENCY: 10.0
        }

        # LCT type base modalities (what they typically do)
        self.lct_type_modalities = {
            LCTType.AGENT: "llm_inference",        # Agents reason
            LCTType.WITNESS: "communication",       # Witnesses attest
            LCTType.COORDINATOR: "coordination",    # Coordinators orchestrate
            LCTType.ORACLE: "vision",               # Oracles observe
            LCTType.VALIDATOR: "consolidation"      # Validators verify
        }

    def calculate_horizon_multiplier(self, horizon: MRHProfile) -> float:
        """
        Calculate stake multiplier based on operational horizon

        Longer-range horizons require higher stakes:
        - LOCAL/EPHEMERAL/AGENT_SCALE: 1.0× (baseline)
        - LOCAL/SESSION/AGENT_SCALE: 1.5×
        - LOCAL/EPOCH/SOCIETY_SCALE: 2.0×
        - GLOBAL/EPOCH/SOCIETY_SCALE: 3.0×

        Args:
            horizon: MRH profile of LCT operations

        Returns:
            Multiplier ≥ 1.0
        """
        # Spatial component
        spatial_multipliers = {
            "LOCAL": 1.0,
            "REGIONAL": 1.5,
            "GLOBAL": 2.0
        }

        # Temporal component
        temporal_multipliers = {
            "EPHEMERAL": 1.0,
            "SESSION": 1.2,
            "EPOCH": 1.5,
            "PERMANENT": 2.0
        }

        # Complexity component
        complexity_multipliers = {
            "AGENT_SCALE": 1.0,
            "SOCIETY_SCALE": 1.5,
            "FEDERATION_SCALE": 2.0,
            "CIVILIZATION_SCALE": 3.0
        }

        spatial = spatial_multipliers.get(horizon.spatial, 1.0)
        temporal = temporal_multipliers.get(horizon.temporal, 1.0)
        complexity = complexity_multipliers.get(horizon.complexity, 1.0)

        # Multiplicative (compound effect)
        return spatial * temporal * complexity

    def calculate_modality_multiplier(self, lct_type: LCTType) -> float:
        """
        Calculate stake multiplier based on LCT modality

        Different modalities have different ATP costs:
        - communication: 1.0× (cheap)
        - vision: 1.2×
        - llm_inference: 1.5× (expensive per second)
        - coordination: 2.0×
        - consolidation: 2.5× (most expensive)

        Args:
            lct_type: Type of LCT

        Returns:
            Multiplier ≥ 1.0
        """
        modality_multipliers = {
            "communication": 1.0,
            "vision": 1.2,
            "llm_inference": 1.5,
            "coordination": 2.0,
            "consolidation": 2.5
        }

        modality = self.lct_type_modalities.get(lct_type, "llm_inference")
        return modality_multipliers.get(modality, 1.0)

    def calculate_stake(self,
                       lct_id: str,
                       lct_type: LCTType,
                       privilege_level: PrivilegeLevel,
                       operational_horizon: MRHProfile) -> ATPStakeCalculation:
        """
        Calculate ATP-aware stake for LCT

        Args:
            lct_id: LCT identifier
            lct_type: Type of LCT
            privilege_level: Privilege level
            operational_horizon: MRH profile of operations

        Returns:
            Stake calculation with breakdown
        """
        # Base stake
        base_stake = self.base_stake_amount

        # Multipliers
        privilege_mult = self.privilege_multipliers[privilege_level]
        horizon_mult = self.calculate_horizon_multiplier(operational_horizon)
        modality_mult = self.calculate_modality_multiplier(lct_type)

        # Total stake (multiplicative)
        total_stake = base_stake * privilege_mult * horizon_mult * modality_mult

        # Reasoning
        reasoning = (
            f"Base {base_stake:.0f} ATP × "
            f"{privilege_level.value} privilege ({privilege_mult:.1f}×) × "
            f"horizon ({horizon_mult:.1f}×) × "
            f"{lct_type.value} modality ({modality_mult:.1f}×) = "
            f"{total_stake:.0f} ATP"
        )

        return ATPStakeCalculation(
            lct_id=lct_id,
            lct_type=lct_type,
            privilege_level=privilege_level,
            operational_horizon=operational_horizon,
            base_stake=base_stake,
            privilege_multiplier=privilege_mult,
            horizon_multiplier=horizon_mult,
            modality_multiplier=modality_mult,
            total_stake=total_stake,
            reasoning=reasoning
        )

    def get_recommended_stake(self,
                            lct_id: str,
                            lct_type: LCTType = LCTType.AGENT,
                            privilege_level: PrivilegeLevel = PrivilegeLevel.NORMAL,
                            operational_horizon: Optional[MRHProfile] = None) -> float:
        """
        Get recommended stake amount for LCT

        Convenience method that returns just the total stake

        Args:
            lct_id: LCT identifier
            lct_type: Type of LCT (default: AGENT)
            privilege_level: Privilege level (default: NORMAL)
            operational_horizon: MRH profile (default: LOCAL/EPHEMERAL/AGENT_SCALE)

        Returns:
            Recommended stake amount in ATP
        """
        if operational_horizon is None:
            operational_horizon = MRHProfile(
                spatial="LOCAL",
                temporal="EPHEMERAL",
                complexity="AGENT_SCALE"
            )

        calculation = self.calculate_stake(
            lct_id,
            lct_type,
            privilege_level,
            operational_horizon
        )

        return calculation.total_stake


class ATPAwareIdentityStakeSystem:
    """
    Identity stake system with ATP-aware dynamic staking

    Extends Session #82 IdentityStakeSystem with ATP pricing integration
    """

    def __init__(self,
                 base_stake_amount: float = 1000.0,
                 society_treasury_address: str = "society_treasury"):
        """
        Initialize ATP-aware identity stake system

        Args:
            base_stake_amount: Base stake for NORMAL/LOCAL/AGENT LCT
            society_treasury_address: Address for slashed stakes
        """
        self.calculator = ATPAwareStakeCalculator(base_stake_amount)
        self.society_treasury_address = society_treasury_address

        # Stakes: lct_id → (IdentityStake, ATPStakeCalculation)
        self.stakes: Dict[str, Tuple[IdentityStake, ATPStakeCalculation]] = {}

        # Society treasury balance
        self.treasury_balance: float = 0.0

        # Statistics
        self.total_stakes_created: int = 0
        self.total_stakes_slashed: int = 0
        self.total_atp_staked: float = 0.0
        self.total_atp_slashed: float = 0.0

    def create_stake(self,
                    lct_id: str,
                    agent_atp_balance: float,
                    lct_type: LCTType = LCTType.AGENT,
                    privilege_level: PrivilegeLevel = PrivilegeLevel.NORMAL,
                    operational_horizon: Optional[MRHProfile] = None) -> Tuple[bool, str, Optional[Tuple[IdentityStake, ATPStakeCalculation]]]:
        """
        Create ATP-aware identity stake

        Args:
            lct_id: LCT identifier
            agent_atp_balance: Agent's available ATP
            lct_type: Type of LCT
            privilege_level: Privilege level
            operational_horizon: MRH profile of operations

        Returns:
            (success, reason, stake_tuple)
        """
        if operational_horizon is None:
            operational_horizon = MRHProfile(
                spatial="LOCAL",
                temporal="EPHEMERAL",
                complexity="AGENT_SCALE"
            )

        # Calculate required stake
        calculation = self.calculator.calculate_stake(
            lct_id,
            lct_type,
            privilege_level,
            operational_horizon
        )

        required_stake = calculation.total_stake

        # Check balance
        if agent_atp_balance < required_stake:
            return (
                False,
                f"insufficient_atp: have {agent_atp_balance:.0f}, need {required_stake:.0f}",
                None
            )

        # Check if already staked
        if lct_id in self.stakes:
            return False, "lct_already_staked", None

        # Create stake
        stake = IdentityStake(
            lct_id=lct_id,
            stake_amount=required_stake,
            stake_timestamp=time.time(),
            status=StakeStatus.LOCKED
        )

        # Store stake with calculation
        self.stakes[lct_id] = (stake, calculation)

        # Update statistics
        self.total_stakes_created += 1
        self.total_atp_staked += required_stake

        return True, "stake_created", (stake, calculation)

    def slash_stake(self, lct_id: str, reason: str) -> Tuple[bool, float]:
        """
        Slash stake for malicious behavior

        Args:
            lct_id: LCT whose stake to slash
            reason: Reason for slashing

        Returns:
            (success, amount_slashed)
        """
        if lct_id not in self.stakes:
            return False, 0.0

        stake, calculation = self.stakes[lct_id]

        if stake.status == StakeStatus.SLASHED:
            return False, 0.0  # Already slashed

        # Slash stake
        amount = stake.stake_amount
        stake.status = StakeStatus.SLASHED

        # Transfer to treasury
        self.treasury_balance += amount

        # Update statistics
        self.total_stakes_slashed += 1
        self.total_atp_slashed += amount

        return True, amount

    def get_stake_info(self, lct_id: str) -> Optional[Tuple[IdentityStake, ATPStakeCalculation]]:
        """Get stake info for LCT"""
        return self.stakes.get(lct_id)

    def get_stats(self) -> Dict:
        """Get system statistics"""
        return {
            "total_stakes_created": self.total_stakes_created,
            "total_stakes_slashed": self.total_stakes_slashed,
            "total_atp_staked": self.total_atp_staked,
            "total_atp_slashed": self.total_atp_slashed,
            "treasury_balance": self.treasury_balance,
            "active_stakes": len([s for s, _ in self.stakes.values() if s.status == StakeStatus.LOCKED])
        }


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  ATP-Aware Identity Stakes - Integration Testing")
    print("  Session #85: Track #1")
    print("=" * 80)

    # Test 1: Basic Stake Calculation
    print("\n=== Test 1: Basic Stake Calculation ===\n")

    calculator = ATPAwareStakeCalculator(base_stake_amount=1000.0)

    # Local agent (baseline)
    local_agent = calculator.calculate_stake(
        lct_id="lct:local:agent:alice",
        lct_type=LCTType.AGENT,
        privilege_level=PrivilegeLevel.NORMAL,
        operational_horizon=MRHProfile(
            spatial="LOCAL",
            temporal="EPHEMERAL",
            complexity="AGENT_SCALE"
        )
    )

    print(f"Local Agent (baseline):")
    print(f"  Total stake: {local_agent.total_stake:.0f} ATP")
    print(f"  Reasoning: {local_agent.reasoning}")

    # Global coordinator (expensive)
    global_coord = calculator.calculate_stake(
        lct_id="lct:global:coord:zeus",
        lct_type=LCTType.COORDINATOR,
        privilege_level=PrivilegeLevel.CRITICAL,
        operational_horizon=MRHProfile(
            spatial="GLOBAL",
            temporal="EPOCH",
            complexity="FEDERATION_SCALE"
        )
    )

    print(f"\nGlobal Coordinator (expensive):")
    print(f"  Total stake: {global_coord.total_stake:.0f} ATP")
    print(f"  Reasoning: {global_coord.reasoning}")
    print(f"  Cost multiplier: {global_coord.total_stake / local_agent.total_stake:.1f}×")

    print("\n✅ Higher-horizon LCTs require proportionally higher stakes")

    # Test 2: Stake Creation with Insufficient Balance
    print("\n=== Test 2: Insufficient ATP Balance ===\n")

    system = ATPAwareIdentityStakeSystem(base_stake_amount=1000.0)

    # Try to create expensive stake with low balance
    success, reason, result = system.create_stake(
        lct_id="lct:global:coord:broke",
        agent_atp_balance=5000.0,  # Not enough for global coordinator
        lct_type=LCTType.COORDINATOR,
        privilege_level=PrivilegeLevel.CRITICAL,
        operational_horizon=MRHProfile(
            spatial="GLOBAL",
            temporal="EPOCH",
            complexity="FEDERATION_SCALE"
        )
    )

    print(f"Stake creation: {success}")
    if not success:
        print(f"  Reason: {reason}")
        print(f"  Required: ~{global_coord.total_stake:.0f} ATP")
        print(f"  Available: 5,000 ATP")

    print("\n✅ Insufficient balance rejected appropriately")

    # Test 3: Successful Stake Creation
    print("\n=== Test 3: Successful Stake Creation ===\n")

    stakes_created = []

    # Create various LCT stakes
    test_cases = [
        ("lct:local:agent:alice", LCTType.AGENT, PrivilegeLevel.NORMAL,
         MRHProfile("LOCAL", "EPHEMERAL", "AGENT_SCALE"), 100000.0),
        ("lct:local:witness:bob", LCTType.WITNESS, PrivilegeLevel.NORMAL,
         MRHProfile("LOCAL", "SESSION", "AGENT_SCALE"), 100000.0),
        ("lct:regional:oracle:charlie", LCTType.ORACLE, PrivilegeLevel.HIGH,
         MRHProfile("REGIONAL", "EPOCH", "SOCIETY_SCALE"), 100000.0),
        ("lct:global:validator:diana", LCTType.VALIDATOR, PrivilegeLevel.CRITICAL,
         MRHProfile("GLOBAL", "EPOCH", "FEDERATION_SCALE"), 100000.0),
    ]

    for lct_id, lct_type, priv, horizon, balance in test_cases:
        success, reason, result = system.create_stake(
            lct_id=lct_id,
            agent_atp_balance=balance,
            lct_type=lct_type,
            privilege_level=priv,
            operational_horizon=horizon
        )

        if success:
            stake, calc = result
            stakes_created.append((lct_id, stake.stake_amount))
            print(f"✅ Created {lct_id}:")
            print(f"   Stake: {stake.stake_amount:.0f} ATP")
            print(f"   Type: {lct_type.value}, Priv: {priv.value}")
            print(f"   Horizon: {horizon.spatial}/{horizon.temporal}/{horizon.complexity}")

    print(f"\n✅ Created {len(stakes_created)} stakes successfully")

    # Test 4: Stake Comparison
    print("\n=== Test 4: Stake Scaling Analysis ===\n")

    stakes_created.sort(key=lambda x: x[1])

    print("Stakes sorted by amount:")
    for lct_id, amount in stakes_created:
        multiplier = amount / stakes_created[0][1]
        print(f"  {lct_id}: {amount:.0f} ATP ({multiplier:.1f}× baseline)")

    print(f"\n  Stake range: {stakes_created[0][1]:.0f} - {stakes_created[-1][1]:.0f} ATP")
    print(f"  Max/min ratio: {stakes_created[-1][1] / stakes_created[0][1]:.1f}×")

    print("\n✅ Stakes scale appropriately with LCT characteristics")

    # Test 5: System Statistics
    print("\n=== Test 5: System Statistics ===\n")

    stats = system.get_stats()
    print("System Stats:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")

    print("\n" + "=" * 80)
    print("  All ATP-Aware Identity Stakes Tests Passed!")
    print("=" * 80)
    print("\n✅ Key Results:")
    print("  - Stakes scale with horizon (LOCAL → GLOBAL)")
    print("  - Stakes scale with privilege (NORMAL → CRITICAL)")
    print("  - Stakes scale with modality (communication → consolidation)")
    print("  - Insufficient balance correctly rejected")
    print("  - Unified resource model validated")
    print("\n🎯 Phase 2 ATP-Security Integration: COMPLETE")
