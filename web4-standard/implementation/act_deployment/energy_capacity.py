"""
Energy Capacity Proof System

Implements proof-of-energy-capacity for ATP charging.
ATP can only be charged when backed by verifiable energy sources.

Part of Session #36 implementation (Phase 1).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Protocol
from abc import ABC, abstractmethod
from enum import Enum
import hashlib
import json


# ============================================================================
# Energy Source Types
# ============================================================================

class EnergySourceType(Enum):
    """Categories of energy sources that can back ATP."""
    SOLAR = "solar"
    COMPUTE = "compute"
    GRID = "grid"
    HUMAN = "human"
    BATTERY = "battery"
    WIND = "wind"
    NUCLEAR = "nuclear"


# ============================================================================
# Energy Capacity Proof Interface
# ============================================================================

class EnergyCapacityProof(Protocol):
    """
    Protocol defining what constitutes proof of energy capacity.

    Any energy source must implement this interface to back ATP.
    """

    @property
    def source_type(self) -> EnergySourceType:
        """Type of energy source."""
        ...

    @property
    def capacity_watts(self) -> float:
        """Rated capacity in watts."""
        ...

    @property
    def source_identifier(self) -> str:
        """Unique identifier for this energy source."""
        ...

    @property
    def validation_method(self) -> str:
        """How this capacity was verified."""
        ...

    @property
    def timestamp(self) -> datetime:
        """When this proof was generated."""
        ...

    def is_valid(self) -> bool:
        """Verify this proof is still valid."""
        ...

    def verify_capacity(self) -> bool:
        """Verify the claimed capacity actually exists."""
        ...

    def to_dict(self) -> Dict:
        """Serialize to dictionary for storage/transmission."""
        ...


# ============================================================================
# Solar Panel Energy Proof
# ============================================================================

@dataclass
class SolarPanelProof:
    """
    Proof of solar panel energy capacity.

    Verifies panel exists and has claimed wattage rating.
    """
    panel_serial: str
    rated_watts: float
    panel_model: str
    installation_date: datetime
    last_verified: datetime
    verification_method: str = "hardware_query"  # or "utility_cert", "manual_inspection"

    # Performance derating (panels degrade over time)
    degradation_factor: float = 1.0  # 1.0 = new, 0.8 = 20% degraded

    # Location context (affects available hours)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @property
    def source_type(self) -> EnergySourceType:
        return EnergySourceType.SOLAR

    @property
    def capacity_watts(self) -> float:
        """Effective capacity accounting for degradation."""
        return self.rated_watts * self.degradation_factor

    @property
    def source_identifier(self) -> str:
        return f"solar:{self.panel_serial}"

    @property
    def validation_method(self) -> str:
        return f"solar_panel:{self.verification_method}"

    @property
    def timestamp(self) -> datetime:
        return self.last_verified

    def is_valid(self) -> bool:
        """Proof valid for 30 days."""
        age = datetime.now(timezone.utc) - self.last_verified
        return age < timedelta(days=30)

    def verify_capacity(self) -> bool:
        """
        Verify solar panel capacity.

        In real system, would query:
        - Hardware monitoring (inverter API)
        - Utility certification
        - Physical inspection records

        For now, validates proof structure.
        """
        if self.rated_watts <= 0:
            return False
        if self.degradation_factor < 0.5 or self.degradation_factor > 1.0:
            return False  # Unrealistic degradation
        if not self.panel_serial:
            return False
        return True

    def to_dict(self) -> Dict:
        return {
            "source_type": self.source_type.value,
            "panel_serial": self.panel_serial,
            "rated_watts": self.rated_watts,
            "capacity_watts": self.capacity_watts,
            "panel_model": self.panel_model,
            "installation_date": self.installation_date.isoformat(),
            "last_verified": self.last_verified.isoformat(),
            "verification_method": self.verification_method,
            "degradation_factor": self.degradation_factor,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


# ============================================================================
# Compute Resource Energy Proof
# ============================================================================

@dataclass
class ComputeResourceProof:
    """
    Proof of compute resource energy capacity.

    Verifies GPU/CPU exists and has known TDP (Thermal Design Power).
    """
    device_type: str  # "gpu", "cpu", "tpu", "fpga"
    device_model: str  # "RTX4090", "Jetson Orin NX", "Threadripper 7970X"
    device_id: str  # Serial, UUID, or hardware ID
    tdp_watts: float  # Thermal Design Power

    last_verified: datetime
    verification_method: str = "hardware_query"  # or "specs_lookup", "power_measurement"

    # Runtime context
    utilization_factor: float = 1.0  # 1.0 = full power, 0.5 = half power
    idle_power_watts: float = 0.0  # Baseline power consumption

    @property
    def source_type(self) -> EnergySourceType:
        return EnergySourceType.COMPUTE

    @property
    def capacity_watts(self) -> float:
        """
        Effective capacity based on utilization.

        idle_power + (tdp - idle_power) * utilization
        """
        active_power = (self.tdp_watts - self.idle_power_watts) * self.utilization_factor
        return self.idle_power_watts + active_power

    @property
    def source_identifier(self) -> str:
        return f"{self.device_type}:{self.device_id}"

    @property
    def validation_method(self) -> str:
        return f"compute:{self.device_model}:{self.verification_method}"

    @property
    def timestamp(self) -> datetime:
        return self.last_verified

    def is_valid(self) -> bool:
        """Proof valid for 1 day (compute can change rapidly)."""
        age = datetime.now(timezone.utc) - self.last_verified
        return age < timedelta(days=1)

    def verify_capacity(self) -> bool:
        """
        Verify compute resource capacity.

        In real system, would:
        - Query CUDA/ROCm for GPU info
        - Read CPU specs from /proc/cpuinfo
        - Cross-check against manufacturer specs database
        - Measure actual power consumption

        For now, validates proof structure.
        """
        if self.tdp_watts <= 0:
            return False
        if self.utilization_factor < 0 or self.utilization_factor > 1.0:
            return False
        if self.idle_power_watts < 0 or self.idle_power_watts > self.tdp_watts:
            return False
        if not self.device_id:
            return False
        return True

    def to_dict(self) -> Dict:
        return {
            "source_type": self.source_type.value,
            "device_type": self.device_type,
            "device_model": self.device_model,
            "device_id": self.device_id,
            "tdp_watts": self.tdp_watts,
            "capacity_watts": self.capacity_watts,
            "last_verified": self.last_verified.isoformat(),
            "verification_method": self.verification_method,
            "utilization_factor": self.utilization_factor,
            "idle_power_watts": self.idle_power_watts,
        }


# ============================================================================
# Grid Connection Energy Proof
# ============================================================================

@dataclass
class GridConnectionProof:
    """
    Proof of grid electricity allocation.

    Verifies society has allocated grid power capacity.
    """
    meter_id: str
    allocated_watts: float
    utility_provider: str
    account_number: str

    last_verified: datetime
    verification_method: str = "utility_api"  # or "meter_reading", "bill_verification"

    # Rate limiting (grid has time-of-use constraints)
    peak_hours: Optional[List[int]] = None  # Hours when capacity reduced
    peak_reduction_factor: float = 1.0  # 0.5 = half capacity during peak

    @property
    def source_type(self) -> EnergySourceType:
        return EnergySourceType.GRID

    @property
    def capacity_watts(self) -> float:
        """
        Grid capacity (may vary by time of day).

        For simplicity, returns allocated watts.
        Real system would check time-of-use.
        """
        return self.allocated_watts

    @property
    def source_identifier(self) -> str:
        return f"grid:{self.meter_id}"

    @property
    def validation_method(self) -> str:
        return f"grid:{self.utility_provider}:{self.verification_method}"

    @property
    def timestamp(self) -> datetime:
        return self.last_verified

    def is_valid(self) -> bool:
        """Proof valid for 7 days."""
        age = datetime.now(timezone.utc) - self.last_verified
        return age < timedelta(days=7)

    def verify_capacity(self) -> bool:
        """
        Verify grid allocation.

        In real system, would:
        - Query utility API for account status
        - Verify meter readings
        - Check payment status
        - Validate allocation limits

        For now, validates proof structure.
        """
        if self.allocated_watts <= 0:
            return False
        if not self.meter_id or not self.account_number:
            return False
        if self.peak_reduction_factor < 0 or self.peak_reduction_factor > 1.0:
            return False
        return True

    def to_dict(self) -> Dict:
        return {
            "source_type": self.source_type.value,
            "meter_id": self.meter_id,
            "allocated_watts": self.allocated_watts,
            "capacity_watts": self.capacity_watts,
            "utility_provider": self.utility_provider,
            "account_number": self.account_number,
            "last_verified": self.last_verified.isoformat(),
            "verification_method": self.verification_method,
            "peak_hours": self.peak_hours,
            "peak_reduction_factor": self.peak_reduction_factor,
        }


# ============================================================================
# Human Labor Energy Proof
# ============================================================================

@dataclass
class HumanLaborProof:
    """
    Proof of human labor energy capacity.

    Humans are energy sources (100W metabolic rate).
    """
    human_lct: str  # LCT identifier for human
    last_verified: datetime
    metabolic_rate_watts: float = 100.0  # Average human ~100W
    available_hours_per_day: float = 8.0  # Work hours
    verification_method: str = "work_history"  # or "self_attestation", "vouching"

    # Skill/efficiency multiplier (skilled labor more effective)
    skill_multiplier: float = 1.0  # 1.0 = baseline, 2.0 = 2x effective

    @property
    def source_type(self) -> EnergySourceType:
        return EnergySourceType.HUMAN

    @property
    def capacity_watts(self) -> float:
        """
        Human energy capacity.

        Average human: 100W * 8 hours/day = 800 Wh/day
        Skilled human: 100W * 2.0 skill * 8 hours = 1600 Wh/day
        """
        return self.metabolic_rate_watts * self.skill_multiplier

    @property
    def source_identifier(self) -> str:
        return f"human:{self.human_lct}"

    @property
    def validation_method(self) -> str:
        return f"human:{self.verification_method}"

    @property
    def timestamp(self) -> datetime:
        return self.last_verified

    def is_valid(self) -> bool:
        """Proof valid for 1 day (humans need daily verification)."""
        age = datetime.now(timezone.utc) - self.last_verified
        return age < timedelta(days=1)

    def verify_capacity(self) -> bool:
        """
        Verify human labor capacity.

        In real system, would:
        - Check work history (ADP records)
        - Validate skills/credentials
        - Check vouching/reputation
        - Verify time availability

        For now, validates proof structure.
        """
        if self.metabolic_rate_watts < 50 or self.metabolic_rate_watts > 200:
            return False  # Unrealistic metabolic rate
        if self.available_hours_per_day < 0 or self.available_hours_per_day > 16:
            return False  # Unrealistic work hours
        if self.skill_multiplier < 0.5 or self.skill_multiplier > 10.0:
            return False  # Unrealistic skill multiplier
        if not self.human_lct:
            return False
        return True

    def to_dict(self) -> Dict:
        return {
            "source_type": self.source_type.value,
            "human_lct": self.human_lct,
            "metabolic_rate_watts": self.metabolic_rate_watts,
            "capacity_watts": self.capacity_watts,
            "available_hours_per_day": self.available_hours_per_day,
            "last_verified": self.last_verified.isoformat(),
            "verification_method": self.verification_method,
            "skill_multiplier": self.skill_multiplier,
        }


# ============================================================================
# Battery Storage Energy Proof
# ============================================================================

@dataclass
class BatteryStorageProof:
    """
    Proof of battery storage energy capacity.

    Batteries store energy for later use.
    """
    battery_id: str
    capacity_wh: float  # Watt-hours of storage
    current_charge_wh: float  # Current stored energy
    max_discharge_rate_watts: float  # Maximum power output
    chemistry: str  # "lithium-ion", "lead-acid", "lithium-polymer"
    last_verified: datetime
    cycles_remaining: Optional[int] = None  # Battery lifecycle
    verification_method: str = "battery_management_system"

    @property
    def source_type(self) -> EnergySourceType:
        return EnergySourceType.BATTERY

    @property
    def capacity_watts(self) -> float:
        """
        Battery output capacity (max discharge rate).

        Note: This is power (watts), not energy (watt-hours).
        Actual available energy is current_charge_wh.
        """
        return self.max_discharge_rate_watts

    @property
    def source_identifier(self) -> str:
        return f"battery:{self.battery_id}"

    @property
    def validation_method(self) -> str:
        return f"battery:{self.chemistry}:{self.verification_method}"

    @property
    def timestamp(self) -> datetime:
        return self.last_verified

    def is_valid(self) -> bool:
        """Proof valid for 1 hour (battery state changes rapidly)."""
        age = datetime.now(timezone.utc) - self.last_verified
        return age < timedelta(hours=1)

    def verify_capacity(self) -> bool:
        """
        Verify battery capacity.

        In real system, would:
        - Query battery management system
        - Verify charge state
        - Check discharge capability
        - Validate lifecycle remaining

        For now, validates proof structure.
        """
        if self.capacity_wh <= 0:
            return False
        if self.current_charge_wh < 0 or self.current_charge_wh > self.capacity_wh:
            return False
        if self.max_discharge_rate_watts <= 0:
            return False
        if not self.battery_id:
            return False
        return True

    def to_dict(self) -> Dict:
        return {
            "source_type": self.source_type.value,
            "battery_id": self.battery_id,
            "capacity_wh": self.capacity_wh,
            "current_charge_wh": self.current_charge_wh,
            "max_discharge_rate_watts": self.max_discharge_rate_watts,
            "capacity_watts": self.capacity_watts,
            "chemistry": self.chemistry,
            "cycles_remaining": self.cycles_remaining,
            "last_verified": self.last_verified.isoformat(),
            "verification_method": self.verification_method,
        }


# ============================================================================
# Energy Capacity Validator
# ============================================================================

class EnergyCapacityValidator:
    """
    Validates energy capacity proofs.

    Central validation logic for all energy source types.
    """

    def __init__(self):
        self.validation_cache: Dict[str, bool] = {}
        self.cache_duration = timedelta(minutes=5)

    def validate_proof(self, proof: EnergyCapacityProof) -> bool:
        """
        Validate an energy capacity proof.

        Checks:
        1. Proof is not expired
        2. Proof structure is valid
        3. Capacity can be verified
        """
        # Check cache
        cache_key = self._get_cache_key(proof)
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]

        # Validate
        is_valid = (
            proof.is_valid() and
            proof.verify_capacity() and
            proof.capacity_watts > 0
        )

        # Cache result
        self.validation_cache[cache_key] = is_valid

        return is_valid

    def validate_total_capacity(
        self,
        proofs: List[EnergyCapacityProof],
        required_watts: float
    ) -> bool:
        """
        Validate that total capacity meets requirement.

        Used when charging ATP - must have enough backing.
        """
        total_capacity = 0.0

        for proof in proofs:
            if not self.validate_proof(proof):
                continue  # Skip invalid proofs
            total_capacity += proof.capacity_watts

        return total_capacity >= required_watts

    def get_total_capacity(self, proofs: List[EnergyCapacityProof]) -> float:
        """Calculate total valid capacity across all proofs."""
        total = 0.0
        for proof in proofs:
            if self.validate_proof(proof):
                total += proof.capacity_watts
        return total

    def _get_cache_key(self, proof: EnergyCapacityProof) -> str:
        """Generate cache key for proof."""
        data = f"{proof.source_identifier}:{proof.timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# ============================================================================
# Energy Capacity Registry
# ============================================================================

@dataclass
class EnergyCapacityRegistry:
    """
    Registry of energy sources for a society.

    Manages all energy capacity proofs for ATP backing.
    """
    society_lct: str
    energy_sources: List[EnergyCapacityProof] = field(default_factory=list)
    validator: EnergyCapacityValidator = field(default_factory=EnergyCapacityValidator)

    def register_source(self, proof: EnergyCapacityProof) -> bool:
        """
        Register a new energy source.

        Returns True if source is valid and registered.
        """
        if not self.validator.validate_proof(proof):
            return False

        # Check if source already registered
        existing = self.find_source(proof.source_identifier)
        if existing:
            # Update existing source
            self.energy_sources.remove(existing)

        self.energy_sources.append(proof)
        return True

    def unregister_source(self, source_identifier: str) -> bool:
        """Remove energy source from registry."""
        source = self.find_source(source_identifier)
        if source:
            self.energy_sources.remove(source)
            return True
        return False

    def find_source(self, source_identifier: str) -> Optional[EnergyCapacityProof]:
        """Find energy source by identifier."""
        for source in self.energy_sources:
            if source.source_identifier == source_identifier:
                return source
        return None

    def get_total_capacity(self) -> float:
        """Get total valid energy capacity."""
        return self.validator.get_total_capacity(self.energy_sources)

    def get_valid_sources(self) -> List[EnergyCapacityProof]:
        """Get all currently valid energy sources."""
        return [
            source for source in self.energy_sources
            if self.validator.validate_proof(source)
        ]

    def cleanup_expired_sources(self) -> int:
        """Remove expired sources. Returns count removed."""
        expired = [
            source for source in self.energy_sources
            if not source.is_valid()
        ]
        for source in expired:
            self.energy_sources.remove(source)
        return len(expired)

    def to_dict(self) -> Dict:
        """Serialize registry to dictionary."""
        return {
            "society_lct": self.society_lct,
            "total_capacity_watts": self.get_total_capacity(),
            "source_count": len(self.get_valid_sources()),
            "sources": [source.to_dict() for source in self.get_valid_sources()],
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Society with mixed energy sources

    print("Energy Capacity Proof System - Example Usage\n")
    print("=" * 70)

    # Create society registry
    registry = EnergyCapacityRegistry(society_lct="lct-society-sage-123")

    # 1. Solar panel
    solar = SolarPanelProof(
        panel_serial="SOLAR-XYZ-789",
        rated_watts=300.0,
        panel_model="SunPower 300W",
        installation_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        last_verified=datetime.now(timezone.utc),
        degradation_factor=0.95,  # 5% degraded
        latitude=37.7749,
        longitude=-122.4194,
    )
    registry.register_source(solar)
    print(f"✓ Registered solar panel: {solar.capacity_watts}W")

    # 2. GPU compute
    gpu = ComputeResourceProof(
        device_type="gpu",
        device_model="RTX4090",
        device_id="GPU-0000:01:00.0",
        tdp_watts=450.0,
        last_verified=datetime.now(timezone.utc),
        utilization_factor=0.8,  # 80% utilization
        idle_power_watts=50.0,
    )
    registry.register_source(gpu)
    print(f"✓ Registered GPU: {gpu.capacity_watts}W")

    # 3. Grid connection
    grid = GridConnectionProof(
        meter_id="METER-ABC-123",
        allocated_watts=1000.0,
        utility_provider="PG&E",
        account_number="ACCT-456789",
        last_verified=datetime.now(timezone.utc),
    )
    registry.register_source(grid)
    print(f"✓ Registered grid: {grid.capacity_watts}W")

    # 4. Human labor
    human = HumanLaborProof(
        human_lct="lct-human-alice-001",
        metabolic_rate_watts=100.0,
        available_hours_per_day=8.0,
        last_verified=datetime.now(timezone.utc),
        skill_multiplier=1.5,  # 1.5x skilled
    )
    registry.register_source(human)
    print(f"✓ Registered human: {human.capacity_watts}W")

    # 5. Battery storage
    battery = BatteryStorageProof(
        battery_id="BATT-TESLA-001",
        capacity_wh=13500.0,  # Tesla Powerwall
        current_charge_wh=10000.0,
        max_discharge_rate_watts=5000.0,
        chemistry="lithium-ion",
        cycles_remaining=3000,
        last_verified=datetime.now(timezone.utc),
    )
    registry.register_source(battery)
    print(f"✓ Registered battery: {battery.capacity_watts}W")

    # Summary
    print("\n" + "=" * 70)
    print(f"Society: {registry.society_lct}")
    print(f"Total Energy Capacity: {registry.get_total_capacity():.2f}W")
    print(f"Valid Sources: {len(registry.get_valid_sources())}")

    print("\nEnergy Mix:")
    for source in registry.get_valid_sources():
        print(f"  - {source.source_type.value}: {source.capacity_watts:.2f}W")

    print("\n" + "=" * 70)
    print("✅ Energy capacity proof system operational")
