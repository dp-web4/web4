"""
Law Alignment vs Compliance Framework — Reference Implementation

Implements RFC-LAW-ALIGN-001:
- Alignment (spirit of law): focuses on WHY the law exists
- Compliance (letter of law): focuses on WHAT the law specifies
- Two-phase validation: alignment first (MUST), compliance second (conditional)
- Enforcement matrix: Critical/High/Medium/Low severity levels
- Web4 capability levels: Level 0 (hardware), Level 1 (virtual), Level 2 (blockchain)
- Verdict system: PERFECT, ALIGNED, WARNING, VIOLATION
- Compliance scoring: 1.0 (perfect), 0.85 (aligned), 0.7 (warning), 0.0 (violation)
- Law classification: alignment required + compliance conditional per level
- Migration support: existing laws upgraded with alignment specifications

Key insight from RFC: "Compliance without alignment is NEVER acceptable.
Alignment without compliance MAY be acceptable."

Spec: web4-standard/rfcs/RFC-LAW-ALIGNMENT-VS-COMPLIANCE.md
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class LawSeverity(Enum):
    """Law severity levels per §3 Enforcement Matrix."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Web4Level(Enum):
    """Web4 implementation levels."""
    LEVEL_0 = 0  # Hardware/physical
    LEVEL_1 = 1  # Virtual/software
    LEVEL_2 = 2  # Blockchain/full


class ComplianceRequirement(Enum):
    """Whether compliance is required for a given context."""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class Verdict(Enum):
    """Validation verdict per §4."""
    PERFECT = "perfect"       # Aligned + Compliant
    ALIGNED = "aligned"       # Aligned but non-compliant (acceptable)
    WARNING = "warning"       # Aligned but should be compliant
    VIOLATION = "violation"   # Not aligned (regardless of compliance)


# Compliance scoring per §Scoring
VERDICT_SCORES = {
    Verdict.PERFECT: 1.0,
    Verdict.ALIGNED: 0.85,
    Verdict.WARNING: 0.7,
    Verdict.VIOLATION: 0.0,
}

# Enforcement matrix per §3
ENFORCEMENT_MATRIX = {
    LawSeverity.CRITICAL: {
        "alignment": "MUST",
        "compliance": "SHOULD (conditional)",
    },
    LawSeverity.HIGH: {
        "alignment": "MUST",
        "compliance": "MAY",
    },
    LawSeverity.MEDIUM: {
        "alignment": "SHOULD",
        "compliance": "MAY",
    },
    LawSeverity.LOW: {
        "alignment": "MAY",
        "compliance": "MAY",
    },
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class AlignmentSpec:
    """Alignment specification (spirit of law)."""
    required: bool
    level: LawSeverity
    principle: str
    indicators: List[str] = field(default_factory=list)


@dataclass
class ComplianceSpec:
    """Compliance specification (letter of law) per Web4 level."""
    specification: str
    level_requirements: Dict[int, ComplianceRequirement] = field(default_factory=dict)
    # level_requirements: {0: OPTIONAL, 1: RECOMMENDED, 2: REQUIRED}
    alternatives: Dict[int, str] = field(default_factory=dict)
    # alternatives: {0: "Physical power budget serves as ATP"}


@dataclass
class LawDefinition:
    """Complete law definition with alignment and compliance."""
    id: str
    name: str
    alignment: AlignmentSpec
    compliance: ComplianceSpec
    version: str = "1.0.0"
    related_rfcs: List[str] = field(default_factory=list)


@dataclass
class AlignmentResult:
    """Result of alignment check."""
    passed: bool
    indicators_met: List[str] = field(default_factory=list)
    indicators_missed: List[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class ComplianceResult:
    """Result of compliance check."""
    passed: bool
    specification_met: bool = False
    alternative_used: Optional[str] = None
    reasoning: str = ""


@dataclass
class ValidationResult:
    """Complete validation result."""
    law_id: str
    aligned: bool
    compliant: Optional[bool]  # None if compliance not checked
    verdict: Verdict
    alignment_result: Optional[AlignmentResult] = None
    compliance_result: Optional[ComplianceResult] = None
    score: float = 0.0
    web4_level: Optional[Web4Level] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    """Overall compliance report per §Scoring."""
    results: List[ValidationResult]
    overall_score: float = 0.0
    perfect_count: int = 0
    aligned_count: int = 0
    warning_count: int = 0
    violation_count: int = 0
    production_ready: bool = False
    notes: List[str] = field(default_factory=list)


# ============================================================================
# IMPLEMENTATION
# ============================================================================

@dataclass
class ImplementationDescriptor:
    """Describes an implementation for validation."""
    entity_id: str
    web4_level: Web4Level
    features: Dict[str, Any] = field(default_factory=dict)
    # features: {"has_atp_tracking": True, "has_resource_limits": True, ...}
    descriptions: Dict[str, str] = field(default_factory=dict)
    # descriptions: {"resource_management": "Uses physical watt budget"}


# ============================================================================
# VALIDATORS
# ============================================================================

class AlignmentValidator:
    """Check alignment (spirit of law) per §4 Phase 1."""

    def __init__(self):
        self._custom_checkers: Dict[str, Callable] = {}

    def register_checker(self, law_id: str,
                         checker: Callable[[ImplementationDescriptor], AlignmentResult]):
        """Register a custom alignment checker for a law."""
        self._custom_checkers[law_id] = checker

    def check(self, impl: ImplementationDescriptor,
              law: LawDefinition) -> AlignmentResult:
        """Check if implementation is aligned with law's spirit."""
        # Use custom checker if registered
        if law.id in self._custom_checkers:
            return self._custom_checkers[law.id](impl)

        # Default: check indicators against implementation features
        indicators_met = []
        indicators_missed = []

        for indicator in law.alignment.indicators:
            # Check if any feature matches the indicator
            indicator_lower = indicator.lower()
            matched = False
            for feat_key, feat_val in impl.features.items():
                if feat_val and feat_key.lower() in indicator_lower:
                    matched = True
                    break
                if feat_val and any(
                    word in feat_key.lower()
                    for word in indicator_lower.split()
                    if len(word) > 3
                ):
                    matched = True
                    break

            if matched:
                indicators_met.append(indicator)
            else:
                indicators_missed.append(indicator)

        # Alignment passes if majority of indicators met
        threshold = 0.5
        if law.alignment.level in (LawSeverity.CRITICAL, LawSeverity.HIGH):
            threshold = 0.6

        total = len(law.alignment.indicators)
        met = len(indicators_met)
        passed = (met / total >= threshold) if total > 0 else True

        return AlignmentResult(
            passed=passed,
            indicators_met=indicators_met,
            indicators_missed=indicators_missed,
            reasoning=f"{met}/{total} indicators met (threshold {threshold})")


class ComplianceValidator:
    """Check compliance (letter of law) per §4 Phase 2."""

    def __init__(self):
        self._custom_checkers: Dict[str, Callable] = {}

    def register_checker(self, law_id: str,
                         checker: Callable[[ImplementationDescriptor], ComplianceResult]):
        """Register custom compliance checker."""
        self._custom_checkers[law_id] = checker

    def should_check(self, impl: ImplementationDescriptor,
                     law: LawDefinition) -> bool:
        """Determine if compliance check is needed for this context."""
        level_val = impl.web4_level.value
        req = law.compliance.level_requirements.get(level_val)
        if req is None:
            return False
        return req in (ComplianceRequirement.REQUIRED,
                       ComplianceRequirement.RECOMMENDED)

    def is_required(self, impl: ImplementationDescriptor,
                    law: LawDefinition) -> bool:
        """Check if compliance is strictly required."""
        level_val = impl.web4_level.value
        req = law.compliance.level_requirements.get(level_val)
        return req == ComplianceRequirement.REQUIRED

    def check(self, impl: ImplementationDescriptor,
              law: LawDefinition) -> ComplianceResult:
        """Check if implementation complies with law's letter."""
        if law.id in self._custom_checkers:
            return self._custom_checkers[law.id](impl)

        # Check if specification requirements are met
        spec_key = f"compliant_{law.id.lower().replace('-', '_')}"
        spec_met = impl.features.get(spec_key, False)

        # Check for alternative
        level_val = impl.web4_level.value
        alt = law.compliance.alternatives.get(level_val)
        alt_key = f"alternative_{law.id.lower().replace('-', '_')}"
        alt_used = impl.features.get(alt_key, False)

        return ComplianceResult(
            passed=spec_met or (alt_used and alt is not None),
            specification_met=spec_met,
            alternative_used=alt if alt_used else None,
            reasoning=f"Spec met: {spec_met}, Alt used: {alt_used}")


# ============================================================================
# LAW ORACLE VALIDATOR
# ============================================================================

class LawOracleValidator:
    """Two-phase validation: alignment then compliance per §4."""

    def __init__(self):
        self.alignment_validator = AlignmentValidator()
        self.compliance_validator = ComplianceValidator()

    def validate_law(self, impl: ImplementationDescriptor,
                     law: LawDefinition) -> ValidationResult:
        """Full two-phase validation."""
        # Phase 1: Check alignment (ALWAYS)
        alignment_result = self.alignment_validator.check(impl, law)

        # Phase 2: Check compliance (CONDITIONAL)
        compliance_result = None
        compliance_checked = self.compliance_validator.should_check(impl, law)
        if compliance_checked:
            compliance_result = self.compliance_validator.check(impl, law)

        compliance_required = self.compliance_validator.is_required(impl, law)

        # Determine verdict
        verdict = self._determine_verdict(
            alignment_result, compliance_result, compliance_required)

        return ValidationResult(
            law_id=law.id,
            aligned=alignment_result.passed,
            compliant=compliance_result.passed if compliance_result else None,
            verdict=verdict,
            alignment_result=alignment_result,
            compliance_result=compliance_result,
            score=VERDICT_SCORES[verdict],
            web4_level=impl.web4_level)

    def _determine_verdict(self, alignment: AlignmentResult,
                           compliance: Optional[ComplianceResult],
                           compliance_required: bool) -> Verdict:
        """Determine verdict per §4 Verdict Determination."""
        # Not aligned = VIOLATION (regardless of compliance)
        if not alignment.passed:
            return Verdict.VIOLATION

        # Aligned + Compliant = PERFECT
        if compliance and compliance.passed:
            return Verdict.PERFECT

        # Aligned + Non-compliant where compliance is required = WARNING
        if compliance_required and compliance and not compliance.passed:
            return Verdict.WARNING

        # Aligned + Non-compliant where compliance not required = ALIGNED
        if alignment.passed and (not compliance or not compliance.passed):
            return Verdict.ALIGNED

        return Verdict.ALIGNED

    def validate_all(self, impl: ImplementationDescriptor,
                     laws: List[LawDefinition]) -> ComplianceReport:
        """Validate implementation against all laws."""
        results = [self.validate_law(impl, law) for law in laws]

        perfect = sum(1 for r in results if r.verdict == Verdict.PERFECT)
        aligned = sum(1 for r in results if r.verdict == Verdict.ALIGNED)
        warning = sum(1 for r in results if r.verdict == Verdict.WARNING)
        violation = sum(1 for r in results if r.verdict == Verdict.VIOLATION)

        total_score = sum(r.score for r in results)
        avg_score = total_score / len(results) if results else 0.0

        # Production ready: no violations, all critical laws aligned
        critical_laws = [r for r in results
                         if any(l.alignment.level == LawSeverity.CRITICAL
                                for l in laws if l.id == r.law_id)]
        all_critical_aligned = all(r.aligned for r in critical_laws)
        production_ready = violation == 0 and all_critical_aligned

        notes = []
        if violation > 0:
            notes.append(f"{violation} law violations — not production ready")
        if warning > 0:
            notes.append(f"{warning} laws recommend adding compliance layer")
        if aligned > 0:
            notes.append(f"{aligned} laws aligned but non-compliant (acceptable)")
        if perfect > 0:
            notes.append(f"{perfect} laws fully compliant")

        return ComplianceReport(
            results=results,
            overall_score=round(avg_score * 10, 1),  # Scale to 10
            perfect_count=perfect,
            aligned_count=aligned,
            warning_count=warning,
            violation_count=violation,
            production_ready=production_ready,
            notes=notes)


# ============================================================================
# LAW LIBRARY (Society 4 Example Laws)
# ============================================================================

def create_example_laws() -> List[LawDefinition]:
    """Create Society 4 example laws per RFC Appendix A."""

    laws = []

    # LAW-ECON-001: Total ATP Budget
    laws.append(LawDefinition(
        id="LAW-ECON-001",
        name="Total ATP Budget",
        alignment=AlignmentSpec(
            required=True,
            level=LawSeverity.CRITICAL,
            principle="Systems must operate within finite resource constraints",
            indicators=[
                "resource_tracking",
                "hard_limits",
                "exhaustion_handling",
            ]),
        compliance=ComplianceSpec(
            specification="1000 ATP total budget in blockchain",
            level_requirements={
                0: ComplianceRequirement.OPTIONAL,
                1: ComplianceRequirement.RECOMMENDED,
                2: ComplianceRequirement.REQUIRED,
            },
            alternatives={
                0: "Physical power budget (watts) serves as ATP",
                1: "Virtual ATP tracking with configurable budget",
            })))

    # LAW-ECON-003: Daily ATP Recharge
    laws.append(LawDefinition(
        id="LAW-ECON-003",
        name="Daily ATP Recharge",
        alignment=AlignmentSpec(
            required=True,
            level=LawSeverity.CRITICAL,
            principle="Periodic resource regeneration prevents exhaustion",
            indicators=[
                "periodic_refresh",
                "resource_regeneration",
                "capacity_restoration",
            ]),
        compliance=ComplianceSpec(
            specification="+20 ATP at 00:00 UTC via blockchain",
            level_requirements={
                0: ComplianceRequirement.OPTIONAL,
                1: ComplianceRequirement.RECOMMENDED,
                2: ComplianceRequirement.REQUIRED,
            },
            alternatives={
                0: "Physical recharge cycle",
                1: "Salience-based eviction provides regeneration",
            })))

    # WEB4-IDENTITY: Entity Identity
    laws.append(LawDefinition(
        id="WEB4-IDENTITY",
        name="Entity Identity",
        alignment=AlignmentSpec(
            required=True,
            level=LawSeverity.HIGH,
            principle="All entities must have verifiable, witness-hardened presence",
            indicators=[
                "unique_identification",
                "identity_persistence",
                "forgery_prevention",
            ]),
        compliance=ComplianceSpec(
            specification="Full LCT with blockchain attestation",
            level_requirements={
                0: ComplianceRequirement.OPTIONAL,
                1: ComplianceRequirement.REQUIRED,
                2: ComplianceRequirement.REQUIRED,
            },
            alternatives={
                0: "Hardware serial number + MAC address",
            })))

    # TRAIN-ANTI-SHORTCUT: Anti-Shortcut Training
    laws.append(LawDefinition(
        id="TRAIN-ANTI-SHORTCUT",
        name="Anti-Shortcut Training",
        alignment=AlignmentSpec(
            required=True,
            level=LawSeverity.HIGH,
            principle="Prevent shortcut-based solutions that bypass genuine learning",
            indicators=[
                "shortcut_detection",
                "genuine_learning",
                "quality_validation",
            ]),
        compliance=ComplianceSpec(
            specification="H-ratio check with automated training pipeline",
            level_requirements={
                0: ComplianceRequirement.OPTIONAL,
                1: ComplianceRequirement.RECOMMENDED,
                2: ComplianceRequirement.REQUIRED,
            })))

    # LAW-GOVERNANCE-001: Witness Requirements
    laws.append(LawDefinition(
        id="LAW-GOVERNANCE-001",
        name="Witness Requirements",
        alignment=AlignmentSpec(
            required=False,
            level=LawSeverity.MEDIUM,
            principle="Critical operations should be observed by independent parties",
            indicators=[
                "witness_mechanism",
                "observation_logging",
                "independent_verification",
            ]),
        compliance=ComplianceSpec(
            specification="Minimum 3 witnesses for critical operations",
            level_requirements={
                0: ComplianceRequirement.OPTIONAL,
                1: ComplianceRequirement.OPTIONAL,
                2: ComplianceRequirement.RECOMMENDED,
            })))

    # LAW-BEST-001: Documentation
    laws.append(LawDefinition(
        id="LAW-BEST-001",
        name="Documentation Standards",
        alignment=AlignmentSpec(
            required=False,
            level=LawSeverity.LOW,
            principle="Systems should maintain clear operational documentation",
            indicators=[
                "documentation_exists",
                "operational_guides",
            ]),
        compliance=ComplianceSpec(
            specification="Full API documentation with examples",
            level_requirements={
                0: ComplianceRequirement.OPTIONAL,
                1: ComplianceRequirement.OPTIONAL,
                2: ComplianceRequirement.OPTIONAL,
            })))

    return laws


# ============================================================================
# SERIALIZATION
# ============================================================================

class LawSerializer:
    """Serialize law definitions and results to JSON."""

    @staticmethod
    def law_to_json(law: LawDefinition) -> Dict:
        """Serialize a law definition."""
        d: Dict[str, Any] = {
            "id": law.id,
            "name": law.name,
            "version": law.version,
            "enforcement": {
                "alignment": {
                    "required": law.alignment.required,
                    "level": law.alignment.level.value,
                    "principle": law.alignment.principle,
                    "indicators": law.alignment.indicators,
                },
                "compliance": {
                    "specification": law.compliance.specification,
                },
            },
        }

        # Level requirements
        for level_val, req in law.compliance.level_requirements.items():
            level_key = f"web4_level_{level_val}"
            comp_section = d["enforcement"]["compliance"]
            comp_section[level_key] = {
                "required": req == ComplianceRequirement.REQUIRED,
                "status": req.value,
            }
            if level_val in law.compliance.alternatives:
                comp_section[level_key]["alternative"] = law.compliance.alternatives[level_val]

        return d

    @staticmethod
    def report_to_json(report: ComplianceReport) -> Dict:
        """Serialize a compliance report."""
        return {
            "overall_score": report.overall_score,
            "breakdown": {
                "perfect": report.perfect_count,
                "aligned": report.aligned_count,
                "warnings": report.warning_count,
                "violations": report.violation_count,
            },
            "verdict": "PRODUCTION_READY" if report.production_ready else "NOT_READY",
            "notes": report.notes,
            "results": [
                {
                    "law_id": r.law_id,
                    "aligned": r.aligned,
                    "compliant": r.compliant,
                    "verdict": r.verdict.value,
                    "score": r.score,
                }
                for r in report.results
            ],
        }


# ============================================================================
# LAW MIGRATION
# ============================================================================

class LawMigrator:
    """Migrate existing laws to include alignment specs per §Migration."""

    @staticmethod
    def upgrade_minimal(law_id: str, name: str,
                        principle: str,
                        indicators: List[str],
                        severity: LawSeverity = LawSeverity.HIGH,
                        specification: str = "",
                        level_2_required: bool = True) -> LawDefinition:
        """Upgrade a minimal law to include alignment."""
        return LawDefinition(
            id=law_id,
            name=name,
            version="2.0.0",
            alignment=AlignmentSpec(
                required=True,
                level=severity,
                principle=principle,
                indicators=indicators),
            compliance=ComplianceSpec(
                specification=specification,
                level_requirements={
                    0: ComplianceRequirement.OPTIONAL,
                    1: ComplianceRequirement.RECOMMENDED,
                    2: ComplianceRequirement.REQUIRED if level_2_required else ComplianceRequirement.RECOMMENDED,
                }))

    @staticmethod
    def is_upgraded(law: LawDefinition) -> bool:
        """Check if a law has been upgraded with alignment specs."""
        return (law.alignment is not None and
                law.alignment.principle != "" and
                len(law.alignment.indicators) > 0)


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

    # ================================================================
    # T1: Law severity & enforcement matrix
    # ================================================================
    print("T1: Enforcement Matrix")
    t("T1.1 Critical alignment = MUST",
      ENFORCEMENT_MATRIX[LawSeverity.CRITICAL]["alignment"] == "MUST")
    t("T1.2 Critical compliance = SHOULD",
      "SHOULD" in ENFORCEMENT_MATRIX[LawSeverity.CRITICAL]["compliance"])
    t("T1.3 High alignment = MUST",
      ENFORCEMENT_MATRIX[LawSeverity.HIGH]["alignment"] == "MUST")
    t("T1.4 Low alignment = MAY",
      ENFORCEMENT_MATRIX[LawSeverity.LOW]["alignment"] == "MAY")
    t("T1.5 4 severity levels", len(LawSeverity) == 4)

    # ================================================================
    # T2: Verdict scoring
    # ================================================================
    print("T2: Verdict Scoring")
    t("T2.1 PERFECT = 1.0", VERDICT_SCORES[Verdict.PERFECT] == 1.0)
    t("T2.2 ALIGNED = 0.85", VERDICT_SCORES[Verdict.ALIGNED] == 0.85)
    t("T2.3 WARNING = 0.7", VERDICT_SCORES[Verdict.WARNING] == 0.7)
    t("T2.4 VIOLATION = 0.0", VERDICT_SCORES[Verdict.VIOLATION] == 0.0)

    # ================================================================
    # T3: Example laws creation
    # ================================================================
    print("T3: Example Laws")
    laws = create_example_laws()
    t("T3.1 6 example laws", len(laws) == 6)

    econ1 = next(l for l in laws if l.id == "LAW-ECON-001")
    t("T3.2 ECON-001 is critical",
      econ1.alignment.level == LawSeverity.CRITICAL)
    t("T3.3 ECON-001 alignment required", econ1.alignment.required)
    t("T3.4 ECON-001 has 3 indicators",
      len(econ1.alignment.indicators) == 3)
    t("T3.5 ECON-001 L0 optional",
      econ1.compliance.level_requirements[0] == ComplianceRequirement.OPTIONAL)
    t("T3.6 ECON-001 L2 required",
      econ1.compliance.level_requirements[2] == ComplianceRequirement.REQUIRED)
    t("T3.7 ECON-001 has L0 alternative",
      0 in econ1.compliance.alternatives)

    identity = next(l for l in laws if l.id == "WEB4-IDENTITY")
    t("T3.8 IDENTITY is high severity",
      identity.alignment.level == LawSeverity.HIGH)

    # ================================================================
    # T4: Alignment validation — Society 4 (Level 2, full compliance)
    # ================================================================
    print("T4: Society 4 Validation")
    society4 = ImplementationDescriptor(
        entity_id="lct:web4:society:society4",
        web4_level=Web4Level.LEVEL_2,
        features={
            "resource_tracking": True,
            "hard_limits": True,
            "exhaustion_handling": True,
            "periodic_refresh": True,
            "resource_regeneration": True,
            "capacity_restoration": True,
            "unique_identification": True,
            "identity_persistence": True,
            "forgery_prevention": True,
            "compliant_law_econ_001": True,
            "compliant_law_econ_003": True,
            "compliant_web4_identity": True,
            "shortcut_detection": True,
            "genuine_learning": True,
            "quality_validation": True,
            "compliant_train_anti_shortcut": True,
            "witness_mechanism": True,
            "observation_logging": True,
            "independent_verification": True,
            "compliant_law_governance_001": True,
            "documentation_exists": True,
            "operational_guides": True,
            "compliant_law_best_001": True,
        })

    validator = LawOracleValidator()
    result = validator.validate_law(society4, econ1)
    t("T4.1 Society 4 aligned with ECON-001", result.aligned)
    t("T4.2 Society 4 compliant with ECON-001", result.compliant)
    t("T4.3 PERFECT verdict", result.verdict == Verdict.PERFECT)
    t("T4.4 Score = 1.0", result.score == 1.0)

    # ================================================================
    # T5: Alignment validation — SAGE (Level 1, aligned not compliant)
    # ================================================================
    print("T5: SAGE Validation")
    sage = ImplementationDescriptor(
        entity_id="lct:web4:sage:genesis",
        web4_level=Web4Level.LEVEL_1,
        features={
            "resource_tracking": True,  # Cache limits
            "hard_limits": True,        # Eviction
            "exhaustion_handling": True, # Graceful degradation
            "periodic_refresh": True,   # Salience-based eviction
            "resource_regeneration": True, # Cache capacity regeneration
            "capacity_restoration": True,  # Cache cleanup
            # NOT compliant with blockchain spec
            "unique_identification": True,  # Partial
            "identity_persistence": True,   # Session identity
            "forgery_prevention": True,     # Crypto keys
            "shortcut_detection": True,     # H-ratio
            "genuine_learning": True,
            "quality_validation": True,
            "compliant_train_anti_shortcut": True,
            "witness_mechanism": True,      # IRP witnesses
            "observation_logging": True,    # Audit log
            "independent_verification": True,
            "documentation_exists": True,
            "operational_guides": True,
        })

    result_sage = validator.validate_law(sage, econ1)
    t("T5.1 SAGE aligned with ECON-001", result_sage.aligned)
    t("T5.2 SAGE not compliant (no blockchain)", not result_sage.compliant)
    t("T5.3 ALIGNED verdict (L1 compliance recommended)",
      result_sage.verdict == Verdict.ALIGNED)
    t("T5.4 Score = 0.85", result_sage.score == 0.85)

    # ================================================================
    # T6: Sprout edge device (Level 0)
    # ================================================================
    print("T6: Sprout Validation")
    sprout = ImplementationDescriptor(
        entity_id="lct:web4:sprout:edge1",
        web4_level=Web4Level.LEVEL_0,
        features={
            "resource_tracking": True,   # Watts
            "hard_limits": True,          # 15W cap
            "exhaustion_handling": True,  # Throttle
            "periodic_refresh": True,     # Physical recharge
            "resource_regeneration": True,
            "capacity_restoration": True,
            "alternative_law_econ_001": True,  # Uses watts as ATP
            "unique_identification": True,     # Hardware serial
            "identity_persistence": True,      # Hardware identity
            "forgery_prevention": True,        # Hardware binding
            "shortcut_detection": True,        # N/A for edge
            "genuine_learning": True,
            "quality_validation": True,
            "witness_mechanism": True,         # CAN bus observers
            "observation_logging": True,       # Event log
            "independent_verification": True,
            "documentation_exists": True,
            "operational_guides": True,
        })

    result_sprout = validator.validate_law(sprout, econ1)
    t("T6.1 Sprout aligned", result_sprout.aligned)
    t("T6.2 Sprout L0 → compliance not checked",
      result_sprout.compliant is None)
    t("T6.3 ALIGNED verdict", result_sprout.verdict == Verdict.ALIGNED)

    # ================================================================
    # T7: Violation detection
    # ================================================================
    print("T7: Violation Detection")
    bad_impl = ImplementationDescriptor(
        entity_id="lct:web4:bad:actor",
        web4_level=Web4Level.LEVEL_2,
        features={
            # Missing all alignment indicators
        })

    result_bad = validator.validate_law(bad_impl, econ1)
    t("T7.1 Not aligned", not result_bad.aligned)
    t("T7.2 VIOLATION verdict", result_bad.verdict == Verdict.VIOLATION)
    t("T7.3 Score = 0.0", result_bad.score == 0.0)

    # ================================================================
    # T8: Compliance without alignment (NEVER acceptable)
    # ================================================================
    print("T8: Compliance Without Alignment")
    # Technically compliant but not aligned
    bad_compliant = ImplementationDescriptor(
        entity_id="lct:web4:bad:compliant",
        web4_level=Web4Level.LEVEL_2,
        features={
            # Has blockchain tokens but violates spirit
            "compliant_law_econ_001": True,
            # Missing alignment indicators
        })

    result_bc = validator.validate_law(bad_compliant, econ1)
    t("T8.1 Not aligned despite compliance", not result_bc.aligned)
    t("T8.2 VIOLATION (compliance doesn't save)",
      result_bc.verdict == Verdict.VIOLATION)
    t("T8.3 Key insight: alignment > compliance",
      VERDICT_SCORES[Verdict.VIOLATION] < VERDICT_SCORES[Verdict.ALIGNED])

    # ================================================================
    # T9: Full compliance report
    # ================================================================
    print("T9: Compliance Report")
    report = validator.validate_all(society4, laws)
    t("T9.1 Has 6 results", len(report.results) == 6)
    t("T9.2 Score > 0", report.overall_score > 0)
    t("T9.3 No violations", report.violation_count == 0)
    t("T9.4 Production ready", report.production_ready)
    t("T9.5 Has notes", len(report.notes) > 0)

    # SAGE report
    report_sage = validator.validate_all(sage, laws)
    t("T9.6 SAGE no violations", report_sage.violation_count == 0)
    t("T9.7 SAGE production ready (aligned)", report_sage.production_ready)

    # ================================================================
    # T10: JSON serialization
    # ================================================================
    print("T10: JSON Serialization")
    law_json = LawSerializer.law_to_json(econ1)
    t("T10.1 Has id", law_json["id"] == "LAW-ECON-001")
    t("T10.2 Has enforcement", "enforcement" in law_json)
    t("T10.3 Has alignment", "alignment" in law_json["enforcement"])
    t("T10.4 Has compliance", "compliance" in law_json["enforcement"])
    t("T10.5 Has principle",
      "principle" in law_json["enforcement"]["alignment"])

    report_json = LawSerializer.report_to_json(report)
    t("T10.6 Has overall_score", "overall_score" in report_json)
    t("T10.7 Has breakdown", "breakdown" in report_json)
    t("T10.8 Has verdict", "verdict" in report_json)

    # JSON round-trip
    json_str = json.dumps(report_json, indent=2)
    parsed = json.loads(json_str)
    t("T10.9 JSON round-trips", parsed["overall_score"] == report_json["overall_score"])

    # ================================================================
    # T11: Law migration
    # ================================================================
    print("T11: Law Migration")
    upgraded = LawMigrator.upgrade_minimal(
        "LAW-LEGACY-001", "Legacy Law",
        principle="Systems should log all operations",
        indicators=["operation_logging", "audit_trail"],
        severity=LawSeverity.MEDIUM,
        specification="Full audit log with blockchain backing")

    t("T11.1 Upgraded version = 2.0.0", upgraded.version == "2.0.0")
    t("T11.2 Has principle", upgraded.alignment.principle != "")
    t("T11.3 Has indicators", len(upgraded.alignment.indicators) == 2)
    t("T11.4 Is upgraded", LawMigrator.is_upgraded(upgraded))

    # Minimal (not upgraded)
    minimal = LawDefinition(
        id="LAW-MINIMAL", name="Minimal",
        alignment=AlignmentSpec(required=False, level=LawSeverity.LOW,
                                principle="", indicators=[]),
        compliance=ComplianceSpec(specification="Something"))
    t("T11.5 Minimal not upgraded", not LawMigrator.is_upgraded(minimal))

    # ================================================================
    # T12: Web4 levels
    # ================================================================
    print("T12: Web4 Levels")
    t("T12.1 Level 0 = hardware", Web4Level.LEVEL_0.value == 0)
    t("T12.2 Level 1 = virtual", Web4Level.LEVEL_1.value == 1)
    t("T12.3 Level 2 = blockchain", Web4Level.LEVEL_2.value == 2)
    t("T12.4 3 levels", len(Web4Level) == 3)

    # ================================================================
    # T13: Compliance requirement per level
    # ================================================================
    print("T13: Level-Conditional Compliance")
    # Level 2: compliance REQUIRED for ECON-001
    t("T13.1 L2 should check ECON-001",
      validator.compliance_validator.should_check(society4, econ1))
    t("T13.2 L2 compliance required for ECON-001",
      validator.compliance_validator.is_required(society4, econ1))

    # Level 0: compliance OPTIONAL for ECON-001
    t("T13.3 L0 compliance not required",
      not validator.compliance_validator.is_required(sprout, econ1))

    # Level 1: compliance RECOMMENDED
    t("T13.4 L1 should check (recommended)",
      validator.compliance_validator.should_check(sage, econ1))
    t("T13.5 L1 not strictly required",
      not validator.compliance_validator.is_required(sage, econ1))

    # ================================================================
    # T14: Custom alignment checker
    # ================================================================
    print("T14: Custom Checkers")
    custom_validator = LawOracleValidator()

    def custom_econ_check(impl: ImplementationDescriptor) -> AlignmentResult:
        has_limits = impl.features.get("hard_limits", False)
        return AlignmentResult(
            passed=has_limits,
            indicators_met=["hard_limits"] if has_limits else [],
            indicators_missed=[] if has_limits else ["hard_limits"],
            reasoning="Custom: checked hard limits only")

    custom_validator.alignment_validator.register_checker(
        "LAW-ECON-001", custom_econ_check)

    # With hard limits → aligned
    r = custom_validator.validate_law(society4, econ1)
    t("T14.1 Custom checker: aligned", r.aligned)

    # Without hard limits → violation
    no_limits = ImplementationDescriptor(
        entity_id="bad", web4_level=Web4Level.LEVEL_2, features={})
    r2 = custom_validator.validate_law(no_limits, econ1)
    t("T14.2 Custom checker: violation", not r2.aligned)

    # ================================================================
    # T15: Warning verdict (aligned but should comply)
    # ================================================================
    print("T15: Warning Verdict")
    # Level 2 implementation that's aligned but not compliant
    aligned_not_compliant = ImplementationDescriptor(
        entity_id="lct:web4:partial:impl",
        web4_level=Web4Level.LEVEL_2,
        features={
            "resource_tracking": True,
            "hard_limits": True,
            "exhaustion_handling": True,
            # No compliant_ flag → not compliant
        })

    r = validator.validate_law(aligned_not_compliant, econ1)
    t("T15.1 Aligned", r.aligned)
    t("T15.2 Not compliant", r.compliant is not None and not r.compliant)
    t("T15.3 WARNING verdict (L2 compliance required)",
      r.verdict == Verdict.WARNING)
    t("T15.4 Score = 0.7", r.score == 0.7)

    # ================================================================
    # T16: E2E — SAGE re-evaluation (Appendix A)
    # ================================================================
    print("T16: E2E SAGE Re-evaluation")
    sage_eval = validator.validate_all(sage, laws)

    # Find specific law results
    econ1_r = next(r for r in sage_eval.results if r.law_id == "LAW-ECON-001")
    econ3_r = next(r for r in sage_eval.results if r.law_id == "LAW-ECON-003")
    shortcut_r = next(r for r in sage_eval.results
                       if r.law_id == "TRAIN-ANTI-SHORTCUT")

    t("T16.1 ECON-001: ALIGNED", econ1_r.verdict == Verdict.ALIGNED)
    t("T16.2 ECON-003: ALIGNED", econ3_r.verdict == Verdict.ALIGNED)
    t("T16.3 ANTI-SHORTCUT: PERFECT", shortcut_r.verdict == Verdict.PERFECT)
    t("T16.4 Overall: no violations", sage_eval.violation_count == 0)
    t("T16.5 Overall: production ready", sage_eval.production_ready)

    # ================================================================
    # T17: E2E — Sprout edge device
    # ================================================================
    print("T17: E2E Sprout Edge")
    sprout_eval = validator.validate_all(sprout, laws)
    econ1_s = next(r for r in sprout_eval.results if r.law_id == "LAW-ECON-001")
    t("T17.1 ECON-001: ALIGNED at L0", econ1_s.verdict == Verdict.ALIGNED)
    t("T17.2 No violations", sprout_eval.violation_count == 0)
    t("T17.3 Production ready", sprout_eval.production_ready)

    # ================================================================
    # T18: Edge cases
    # ================================================================
    print("T18: Edge Cases")
    # Empty implementation
    empty = ImplementationDescriptor(
        entity_id="empty", web4_level=Web4Level.LEVEL_0, features={})
    r = validator.validate_law(empty, econ1)
    t("T18.1 Empty impl → violation", r.verdict == Verdict.VIOLATION)

    # Law with no indicators (trivially aligned)
    trivial = LawDefinition(
        id="TRIVIAL", name="Trivial",
        alignment=AlignmentSpec(required=True, level=LawSeverity.LOW,
                                principle="Exists", indicators=[]),
        compliance=ComplianceSpec(specification="None"))
    r = validator.validate_law(empty, trivial)
    t("T18.2 No indicators → aligned", r.aligned)

    # Low severity law — alignment MAY
    low_law = next(l for l in laws if l.id == "LAW-BEST-001")
    t("T18.3 Low severity = MAY",
      ENFORCEMENT_MATRIX[LawSeverity.LOW]["alignment"] == "MAY")

    # ================================================================
    # T19: Report JSON structure
    # ================================================================
    print("T19: Report JSON")
    report_json = LawSerializer.report_to_json(sage_eval)
    t("T19.1 Has breakdown.perfect", "perfect" in report_json["breakdown"])
    t("T19.2 Has breakdown.aligned", "aligned" in report_json["breakdown"])
    t("T19.3 Has breakdown.warnings", "warnings" in report_json["breakdown"])
    t("T19.4 Has breakdown.violations", "violations" in report_json["breakdown"])
    t("T19.5 Has results array", len(report_json["results"]) == 6)

    # ================================================================
    # T20: Compliance alternatives
    # ================================================================
    print("T20: Compliance Alternatives")
    sprout_with_alt = ImplementationDescriptor(
        entity_id="lct:web4:sprout:alt",
        web4_level=Web4Level.LEVEL_0,
        features={
            "resource_tracking": True,
            "hard_limits": True,
            "exhaustion_handling": True,
            "alternative_law_econ_001": True,
        })

    # L0 compliance should not be checked (OPTIONAL)
    should_check = validator.compliance_validator.should_check(sprout_with_alt, econ1)
    t("T20.1 L0 compliance not checked", not should_check)

    # L1 with alternative
    sage_alt = ImplementationDescriptor(
        entity_id="lct:web4:sage:alt",
        web4_level=Web4Level.LEVEL_1,
        features={
            "resource_tracking": True,
            "hard_limits": True,
            "exhaustion_handling": True,
            "alternative_law_econ_001": True,
        })
    r = validator.compliance_validator.check(sage_alt, econ1)
    t("T20.2 Alternative accepted", r.passed)
    t("T20.3 Alternative documented", r.alternative_used is not None)

    # ================================================================
    # T21: Multiple law categories
    # ================================================================
    print("T21: Law Categories")
    critical_laws = [l for l in laws if l.alignment.level == LawSeverity.CRITICAL]
    high_laws = [l for l in laws if l.alignment.level == LawSeverity.HIGH]
    medium_laws = [l for l in laws if l.alignment.level == LawSeverity.MEDIUM]
    low_laws = [l for l in laws if l.alignment.level == LawSeverity.LOW]

    t("T21.1 2 critical laws", len(critical_laws) == 2)
    t("T21.2 2 high laws", len(high_laws) == 2)
    t("T21.3 1 medium law", len(medium_laws) == 1)
    t("T21.4 1 low law", len(low_laws) == 1)

    # ================================================================
    # SUMMARY
    # ================================================================
    print(f"\n{'='*60}")
    print(f"Law Alignment vs Compliance: {passed}/{total} checks passed")
    if passed == total:
        print("  All checks passed!")
    else:
        print(f"  {total - passed} checks FAILED")
    print(f"{'='*60}")

    return passed, total


if __name__ == "__main__":
    run_tests()
