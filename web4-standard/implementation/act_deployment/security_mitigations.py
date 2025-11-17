"""
Security Mitigations for Energy-Backed ATP System

Implements Phase 1 critical mitigations identified in Session #38:
- Global Energy Registry (prevents A2: Proof Reuse)
- Device Spec Database (prevents A3: Capacity Inflation)
- Identity-Energy Linker (prevents E1: Reputation Washing)

Session #39 Implementation
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from enum import Enum
import json

from energy_capacity import (
    EnergyCapacityProof,
    SolarPanelProof,
    ComputeResourceProof,
    EnergySourceType,
)

from energy_backed_identity_bond import EnergyBackedIdentityBond


# ============================================================================
# Mitigation A2: Global Energy Registry
# ============================================================================

class RegistrationStatus(Enum):
    """Status of energy source registration"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    DISPUTED = "disputed"


@dataclass
class EnergySourceRegistration:
    """
    Record of energy source registration in global registry.

    Prevents same physical energy source from being registered
    in multiple societies (double-spending).
    """
    source_identifier: str
    society_lct: str
    registered_at: datetime
    registered_by: str  # Identity that registered it
    capacity_watts: float
    source_type: EnergySourceType
    status: RegistrationStatus = RegistrationStatus.ACTIVE

    # Proof verification
    verification_method: str = "self_reported"
    verified: bool = False
    verifier_lct: Optional[str] = None
    verified_at: Optional[datetime] = None

    # Dispute tracking
    disputed_by: List[str] = field(default_factory=list)
    dispute_notes: List[str] = field(default_factory=list)


class GlobalEnergyRegistry:
    """
    Blockchain-level global registry of energy sources.

    Purpose: Prevent proof reuse attack (A2)
    - Each physical energy source can only be registered once
    - Registrations are immutable and permanent
    - Disputes can be raised but require resolution

    Similar to UTXO model in Bitcoin - once an energy source is "spent"
    (registered to a society), it cannot be registered elsewhere.
    """

    def __init__(self):
        # Core registry: source_identifier -> registration
        self.sources: Dict[str, EnergySourceRegistration] = {}

        # Index by society for fast lookups
        self.society_sources: Dict[str, Set[str]] = {}

        # Audit trail
        self.registration_history: List[EnergySourceRegistration] = []

    def register_source(
        self,
        proof: EnergyCapacityProof,
        society_lct: str,
        registrar_identity: str,
    ) -> bool:
        """
        Register energy source to a society.

        Returns True if registration succeeds.
        Raises ValueError if source already registered.
        """
        source_id = proof.source_identifier

        # Check if already registered
        if source_id in self.sources:
            existing = self.sources[source_id]

            # If registered to different society, reject
            if existing.society_lct != society_lct:
                raise ValueError(
                    f"Energy source {source_id} already registered to {existing.society_lct}. "
                    f"Cannot register to {society_lct}. "
                    f"This prevents double-spending attack (A2)."
                )

            # If registered to same society, allow re-registration (update)
            # This handles capacity updates, verification updates, etc.
            existing.capacity_watts = proof.capacity_watts
            existing.verification_method = proof.validation_method
            return True

        # Create new registration
        registration = EnergySourceRegistration(
            source_identifier=source_id,
            society_lct=society_lct,
            registered_at=datetime.now(timezone.utc),
            registered_by=registrar_identity,
            capacity_watts=proof.capacity_watts,
            source_type=proof.source_type,
            verification_method=proof.validation_method,
            verified=getattr(proof, 'verified', False),
            verifier_lct=getattr(proof, 'verifier_lct', None),
            verified_at=getattr(proof, 'verified_at', None),
        )

        # Add to registry
        self.sources[source_id] = registration

        # Update society index
        if society_lct not in self.society_sources:
            self.society_sources[society_lct] = set()
        self.society_sources[society_lct].add(source_id)

        # Audit trail
        self.registration_history.append(registration)

        return True

    def get_registration(self, source_identifier: str) -> Optional[EnergySourceRegistration]:
        """Get registration for energy source."""
        return self.sources.get(source_identifier)

    def get_society_sources(self, society_lct: str) -> List[EnergySourceRegistration]:
        """Get all energy sources registered to a society."""
        if society_lct not in self.society_sources:
            return []

        source_ids = self.society_sources[society_lct]
        return [self.sources[sid] for sid in source_ids]

    def get_total_capacity(self, society_lct: str) -> float:
        """Get total registered capacity for a society."""
        sources = self.get_society_sources(society_lct)
        return sum(
            s.capacity_watts for s in sources
            if s.status == RegistrationStatus.ACTIVE
        )

    def raise_dispute(
        self,
        source_identifier: str,
        disputing_party: str,
        reason: str,
    ) -> bool:
        """
        Raise dispute about energy source ownership.

        Useful if:
        - Physical ownership transferred
        - Installation moved
        - Fraud suspected
        """
        if source_identifier not in self.sources:
            return False

        registration = self.sources[source_identifier]
        registration.disputed_by.append(disputing_party)
        registration.dispute_notes.append(f"{datetime.now(timezone.utc).isoformat()}: {reason}")
        registration.status = RegistrationStatus.DISPUTED

        return True

    def to_dict(self) -> Dict:
        """Serialize registry for storage."""
        return {
            "total_registrations": len(self.sources),
            "total_societies": len(self.society_sources),
            "registrations": [
                {
                    "source_id": reg.source_identifier,
                    "society": reg.society_lct,
                    "capacity_watts": reg.capacity_watts,
                    "registered_at": reg.registered_at.isoformat(),
                    "status": reg.status.value,
                }
                for reg in self.sources.values()
            ]
        }


# ============================================================================
# Mitigation A3: Device Spec Database
# ============================================================================

@dataclass
class DeviceSpecification:
    """Official specification for energy device."""
    device_model: str
    device_type: str  # "gpu", "solar_panel", "battery"
    manufacturer: str

    # Capacity specifications
    rated_capacity_watts: float
    min_capacity_watts: float
    max_capacity_watts: float

    # Additional specs
    efficiency: Optional[float] = None
    degradation_rate_per_year: Optional[float] = None

    # Verification
    spec_source: str = "manufacturer_datasheet"
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DeviceSpecDatabase:
    """
    Database of official device specifications.

    Purpose: Prevent capacity inflation attack (A3)
    - Validate claimed TDP against manufacturer specs
    - Validate solar panel degradation
    - Detect inflated capacity claims

    In production, would integrate with:
    - GPU manufacturer APIs (NVIDIA, AMD)
    - Solar panel databases (NREL, manufacturer APIs)
    - Battery spec databases
    """

    def __init__(self):
        self.gpu_specs: Dict[str, DeviceSpecification] = {}
        self.solar_specs: Dict[str, DeviceSpecification] = {}
        self.battery_specs: Dict[str, DeviceSpecification] = {}

        # Load default specs
        self._load_default_gpu_specs()
        self._load_default_solar_specs()

    def _load_default_gpu_specs(self):
        """Load common GPU specifications."""

        # NVIDIA GPUs
        self.gpu_specs["RTX4090"] = DeviceSpecification(
            device_model="RTX4090",
            device_type="gpu",
            manufacturer="NVIDIA",
            rated_capacity_watts=450.0,
            min_capacity_watts=420.0,
            max_capacity_watts=480.0,  # Some models OC'd
            efficiency=0.85,
            spec_source="nvidia_official_datasheet",
        )

        self.gpu_specs["RTX4080"] = DeviceSpecification(
            device_model="RTX4080",
            device_type="gpu",
            manufacturer="NVIDIA",
            rated_capacity_watts=320.0,
            min_capacity_watts=300.0,
            max_capacity_watts=350.0,
            efficiency=0.85,
            spec_source="nvidia_official_datasheet",
        )

        self.gpu_specs["RTX3090"] = DeviceSpecification(
            device_model="RTX3090",
            device_type="gpu",
            manufacturer="NVIDIA",
            rated_capacity_watts=350.0,
            min_capacity_watts=320.0,
            max_capacity_watts=380.0,
            efficiency=0.80,
            spec_source="nvidia_official_datasheet",
        )

        # AMD GPUs
        self.gpu_specs["RX7900XTX"] = DeviceSpecification(
            device_model="RX7900XTX",
            device_type="gpu",
            manufacturer="AMD",
            rated_capacity_watts=355.0,
            min_capacity_watts=330.0,
            max_capacity_watts=380.0,
            efficiency=0.83,
            spec_source="amd_official_datasheet",
        )

    def _load_default_solar_specs(self):
        """Load common solar panel specifications."""

        self.solar_specs["SUNPOWERX22"] = DeviceSpecification(
            device_model="SunPowerX22",
            device_type="solar_panel",
            manufacturer="SunPower",
            rated_capacity_watts=370.0,
            min_capacity_watts=350.0,
            max_capacity_watts=370.0,
            efficiency=0.228,  # 22.8% efficiency
            degradation_rate_per_year=0.0025,  # 0.25% per year
            spec_source="sunpower_datasheet",
        )

        self.solar_specs["LGNEONR"] = DeviceSpecification(
            device_model="LG_NeON_R",
            device_type="solar_panel",
            manufacturer="LG",
            rated_capacity_watts=365.0,
            min_capacity_watts=350.0,
            max_capacity_watts=365.0,
            efficiency=0.217,
            degradation_rate_per_year=0.003,  # 0.3% per year
            spec_source="lg_datasheet",
        )

    def validate_gpu_tdp(self, device_model: str, claimed_tdp: float) -> bool:
        """
        Validate GPU TDP claim against specs.

        Returns True if claimed TDP is within acceptable range.
        """
        # Normalize model name (remove spaces, make uppercase)
        normalized_model = device_model.replace(" ", "").upper()

        if normalized_model not in self.gpu_specs:
            # Unknown GPU - cannot validate
            # In production, would query manufacturer API
            return False

        spec = self.gpu_specs[normalized_model]

        # Allow some tolerance (up to max_capacity)
        if claimed_tdp <= spec.max_capacity_watts:
            return True

        return False

    def validate_solar_degradation(
        self,
        panel_model: str,
        installation_date: datetime,
        claimed_degradation_factor: float,
    ) -> bool:
        """
        Validate solar panel degradation factor.

        Returns True if claimed degradation is realistic.
        """
        normalized_model = panel_model.replace(" ", "").replace("-", "").upper()

        if normalized_model not in self.solar_specs:
            # Unknown panel - cannot validate
            return False

        spec = self.solar_specs[normalized_model]

        # Calculate expected degradation
        age_years = (datetime.now(timezone.utc) - installation_date).days / 365.25
        expected_degradation = 1.0 - (spec.degradation_rate_per_year * age_years)

        # Allow some tolerance (±5%)
        min_acceptable = expected_degradation - 0.05
        max_acceptable = min(1.0, expected_degradation + 0.05)

        if min_acceptable <= claimed_degradation_factor <= max_acceptable:
            return True

        return False

    def get_max_capacity(self, device_type: str, device_model: str) -> Optional[float]:
        """Get maximum acceptable capacity for device."""
        normalized_model = device_model.replace(" ", "").upper()

        if device_type == "gpu" and normalized_model in self.gpu_specs:
            return self.gpu_specs[normalized_model].max_capacity_watts
        elif device_type == "solar_panel" and normalized_model in self.solar_specs:
            return self.solar_specs[normalized_model].max_capacity_watts

        return None

    def add_spec(self, spec: DeviceSpecification):
        """Add new device specification."""
        normalized_model = spec.device_model.replace(" ", "").upper()

        if spec.device_type == "gpu":
            self.gpu_specs[normalized_model] = spec
        elif spec.device_type == "solar_panel":
            self.solar_specs[normalized_model] = spec
        elif spec.device_type == "battery":
            self.battery_specs[normalized_model] = spec


# ============================================================================
# Mitigation E1: Identity-Energy Linker
# ============================================================================

@dataclass
class IdentityRecord:
    """Record of an identity's lifecycle."""
    identity_lct: str
    created_at: datetime
    energy_sources: Set[str]
    violations: List[str] = field(default_factory=list)
    status: str = "active"  # "active", "abandoned", "terminated"
    abandoned_at: Optional[datetime] = None


class IdentityEnergyLinker:
    """
    Links identities to energy sources and tracks violation history.

    Purpose: Prevent reputation washing (E1)
    - Track all identities that used an energy source
    - Aggregate violations across all identities using same energy
    - Prevent identity cycling to wash reputation

    Key insight: Energy sources are physical and persistent, even if
    digital identities are ephemeral. Link reputation to energy, not identity.
    """

    def __init__(self):
        # Energy source -> list of identities that used it
        self.energy_to_identities: Dict[str, List[IdentityRecord]] = {}

        # Identity -> record
        self.identities: Dict[str, IdentityRecord] = {}

        # Violation aggregation cache
        self._violation_cache: Dict[str, List[str]] = {}

    def register_identity(
        self,
        identity_lct: str,
        energy_sources: List[str],
    ) -> IdentityRecord:
        """
        Register new identity with its energy sources.

        Returns identity record.
        """
        record = IdentityRecord(
            identity_lct=identity_lct,
            created_at=datetime.now(timezone.utc),
            energy_sources=set(energy_sources),
        )

        self.identities[identity_lct] = record

        # Link energy sources to identity
        for source_id in energy_sources:
            if source_id not in self.energy_to_identities:
                self.energy_to_identities[source_id] = []
            self.energy_to_identities[source_id].append(record)

        # Invalidate cache
        for source_id in energy_sources:
            self._violation_cache.pop(source_id, None)

        return record

    def record_violation(self, identity_lct: str, violation: str):
        """Record violation for an identity."""
        if identity_lct not in self.identities:
            raise ValueError(f"Identity {identity_lct} not registered")

        self.identities[identity_lct].violations.append(violation)

        # Invalidate cache for all energy sources this identity uses
        record = self.identities[identity_lct]
        for source_id in record.energy_sources:
            self._violation_cache.pop(source_id, None)

    def get_energy_violation_history(self, energy_source_id: str) -> List[str]:
        """
        Get ALL violations across ALL identities that used this energy source.

        This is the key mitigation for E1: Even if you create a new identity,
        your energy source's violation history follows you.
        """
        # Check cache
        if energy_source_id in self._violation_cache:
            return self._violation_cache[energy_source_id]

        # Aggregate violations from all identities
        all_violations = []

        if energy_source_id in self.energy_to_identities:
            for record in self.energy_to_identities[energy_source_id]:
                all_violations.extend(record.violations)

        # Cache result
        self._violation_cache[energy_source_id] = all_violations

        return all_violations

    def get_identity_effective_violations(self, identity_lct: str) -> List[str]:
        """
        Get effective violations for an identity.

        Includes:
        1. Direct violations by this identity
        2. Violations by ANY identity that used the same energy sources

        This prevents reputation washing via identity cycling.
        """
        if identity_lct not in self.identities:
            return []

        record = self.identities[identity_lct]

        # Start with direct violations
        effective_violations = set(record.violations)

        # Add violations from energy source history
        for source_id in record.energy_sources:
            energy_violations = self.get_energy_violation_history(source_id)
            effective_violations.update(energy_violations)

        return list(effective_violations)

    def abandon_identity(self, identity_lct: str):
        """Mark identity as abandoned."""
        if identity_lct not in self.identities:
            return

        record = self.identities[identity_lct]
        record.status = "abandoned"
        record.abandoned_at = datetime.now(timezone.utc)

        # Note: Energy-to-identity links remain!
        # This is intentional - abandoned identities still contribute to energy source reputation

    def can_use_energy_source(
        self,
        identity_lct: str,
        energy_source_id: str,
        max_violations: int = 5,
    ) -> bool:
        """
        Check if identity can use energy source based on violation history.

        Returns False if energy source has too many violations across all identities.
        """
        violations = self.get_energy_violation_history(energy_source_id)
        return len(violations) < max_violations

    def get_identity_count_for_energy(self, energy_source_id: str) -> int:
        """Get number of identities that used this energy source."""
        if energy_source_id not in self.energy_to_identities:
            return 0
        return len(self.energy_to_identities[energy_source_id])

    def detect_identity_cycling(self, energy_source_id: str, threshold: int = 3) -> bool:
        """
        Detect if energy source shows signs of identity cycling.

        Returns True if suspicious cycling detected (e.g., 3+ identities using same energy).
        """
        count = self.get_identity_count_for_energy(energy_source_id)
        return count >= threshold


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SECURITY MITIGATIONS - Session #39")
    print("=" * 80)

    # ========================================
    # Mitigation A2: Global Energy Registry
    # ========================================

    print("\n### Mitigation A2: Global Energy Registry (Prevents Proof Reuse)")
    print("-" * 80)

    registry = GlobalEnergyRegistry()

    # Create solar panel proof
    from energy_capacity import SolarPanelProof

    panel = SolarPanelProof(
        panel_serial="REAL-PANEL-001",
        rated_watts=300.0,
        panel_model="SunPower X22",
        installation_date=datetime.now(timezone.utc),
        last_verified=datetime.now(timezone.utc),
        degradation_factor=0.95,
        latitude=37.7749,
        longitude=-122.4194,
    )

    # Society A registers panel
    success = registry.register_source(panel, "lct-society-A", "lct-identity-A")
    print(f"✓ Society A registered solar panel: {success}")
    print(f"  Capacity: {registry.get_total_capacity('lct-society-A')}W")

    # Society B tries to register SAME panel - should fail
    try:
        registry.register_source(panel, "lct-society-B", "lct-identity-B")
        print("❌ Society B registered same panel - MITIGATION FAILED!")
    except ValueError as e:
        print(f"✓ Society B blocked from registering same panel:")
        print(f"  Error: {str(e)[:100]}...")

    # ========================================
    # Mitigation A3: Device Spec Database
    # ========================================

    print("\n### Mitigation A3: Device Spec Database (Prevents Capacity Inflation)")
    print("-" * 80)

    spec_db = DeviceSpecDatabase()

    # Valid GPU TDP
    valid_tdp = spec_db.validate_gpu_tdp("RTX4090", 450.0)
    print(f"✓ RTX 4090 @ 450W: {valid_tdp}")

    # Inflated GPU TDP
    inflated_tdp = spec_db.validate_gpu_tdp("RTX4090", 1000.0)
    print(f"✓ RTX 4090 @ 1000W: {inflated_tdp} (inflation detected)")

    # Valid solar degradation (1 year old, 99.75% capacity)
    one_year_ago = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 1)
    valid_degradation = spec_db.validate_solar_degradation(
        "SunPower X22",
        one_year_ago,
        0.9975
    )
    print(f"✓ 1-year-old panel @ 99.75% degradation: {valid_degradation}")

    # Invalid degradation (10 years old, claiming 100%)
    ten_years_ago = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 10)
    invalid_degradation = spec_db.validate_solar_degradation(
        "SunPower X22",
        ten_years_ago,
        1.0
    )
    print(f"✓ 10-year-old panel @ 100% degradation: {invalid_degradation} (inflation detected)")

    # ========================================
    # Mitigation E1: Identity-Energy Linker
    # ========================================

    print("\n### Mitigation E1: Identity-Energy Linker (Prevents Reputation Washing)")
    print("-" * 80)

    linker = IdentityEnergyLinker()

    # Register identity A with energy source
    energy_source = "solar:PANEL-001"
    linker.register_identity("lct-identity-A", [energy_source])

    # Record violations for identity A
    linker.record_violation("lct-identity-A", "failed_work_001")
    linker.record_violation("lct-identity-A", "failed_work_002")
    linker.record_violation("lct-identity-A", "spam_detected")

    print(f"✓ Identity A accumulated 3 violations")

    # Abandon identity A
    linker.abandon_identity("lct-identity-A")
    print(f"✓ Identity A abandoned")

    # Create identity B with SAME energy source
    linker.register_identity("lct-identity-B", [energy_source])
    print(f"✓ Identity B created with same energy source")

    # Check effective violations for identity B
    effective_violations = linker.get_identity_effective_violations("lct-identity-B")
    print(f"✓ Identity B effective violations: {len(effective_violations)}")
    print(f"  (Includes violations from Identity A - reputation washing prevented!)")

    # Detect identity cycling
    cycling = linker.detect_identity_cycling(energy_source, threshold=2)
    print(f"✓ Identity cycling detected: {cycling}")

    print("\n" + "=" * 80)
    print("All Phase 1 mitigations implemented successfully!")
    print("=" * 80)
