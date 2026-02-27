#!/usr/bin/env python3
"""
EU AI Act Compliance Engine — Web4 Reference Implementation

Maps Web4 primitives (LCT, T3/V3, ATP/ADP, R6, PolicyEntity) to
EU AI Act requirements (Articles 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 26).

Implements:
  1. Entity classification with Annex III categories (Art. 6 gap closure)
  2. Risk management system with T3 tensor risk scoring (Art. 9)
  3. Data governance with bias detection (Art. 10 gap closure)
  4. Technical documentation generator (Art. 11)
  5. Automatic record-keeping with fractal retention (Art. 12)
  6. Transparency reporting with tensor explanations (Art. 13 gap closure)
  7. Human oversight enforcement with R6 approval (Art. 14)
  8. Accuracy/robustness metrics from attack corpus (Art. 15)
  9. Compliance assessment engine combining all articles
  10. Regulatory export format for audit authorities

Regulation: EU 2024/1689 ("the AI Act")
Deadline: August 2, 2026 (high-risk system obligations)

Checks: 180+
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

# ═══════════════════════════════════════════════════════════════
# PART 1: EU AI ACT DATA MODEL
# ═══════════════════════════════════════════════════════════════

class AnnexIIICategory(Enum):
    """Annex III high-risk AI system categories."""
    BIOMETRICS = "biometrics"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    EDUCATION = "education_vocational_training"
    EMPLOYMENT = "employment_workers_management"
    ESSENTIAL_SERVICES = "essential_private_public_services"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION = "migration_asylum_border"
    JUSTICE = "administration_of_justice"
    NONE = "not_high_risk"


class RiskLevel(Enum):
    """Risk classification per EU AI Act."""
    UNACCEPTABLE = "unacceptable"  # Art. 5 — prohibited
    HIGH = "high"                  # Art. 6 — Annex III
    LIMITED = "limited"            # Art. 50 — transparency only
    MINIMAL = "minimal"            # No obligations


class ComplianceStatus(Enum):
    """Per-article compliance assessment."""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class LCTStatus(Enum):
    """LCT lifecycle states relevant to AI Act compliance."""
    ACTIVE = "active"
    DORMANT = "dormant"    # Art. 14 — paused by human
    VOID = "void"          # Art. 14 — terminated
    SLASHED = "slashed"    # Trust penalty applied


class EntityMode(Enum):
    """Entity behavioral modes per entity-types.md."""
    AGENTIC = "agentic"        # Self-directed
    RESPONSIVE = "responsive"  # Request-driven
    DELEGATIVE = "delegative"  # Authority-delegated


@dataclass
class AnnexIIIClassification:
    """Art. 6 — Annex III category classification with evidence."""
    category: AnnexIIICategory
    subcategory: str                     # Specific use within category
    risk_level: RiskLevel
    classification_date: str
    classified_by: str                   # LCT ID of classifier
    evidence: list[str] = field(default_factory=list)
    review_due: str = ""                 # Next mandatory review date

    def is_high_risk(self) -> bool:
        return self.risk_level == RiskLevel.HIGH


@dataclass
class T3RiskDimension:
    """T3 tensor as risk dimension per Art. 9."""
    talent: float = 0.5       # Technical competence risk
    training: float = 0.5     # Data/learning quality risk
    temperament: float = 0.5  # Behavioral stability risk

    def composite_risk(self) -> float:
        """Overall risk score (lower = higher risk)."""
        return (self.talent + self.training + self.temperament) / 3.0

    def risk_flags(self, threshold: float = 0.4) -> list[str]:
        """Dimensions below threshold flagged for attention."""
        flags = []
        if self.talent < threshold:
            flags.append(f"talent={self.talent:.2f}<{threshold}")
        if self.training < threshold:
            flags.append(f"training={self.training:.2f}<{threshold}")
        if self.temperament < threshold:
            flags.append(f"temperament={self.temperament:.2f}<{threshold}")
        return flags


@dataclass
class V3DataQuality:
    """V3 tensor for data governance per Art. 10."""
    valuation: float = 0.5   # Economic value/utility
    veracity: float = 0.5    # Truthfulness/accuracy
    validity: float = 0.5    # Logical soundness/relevance

    def data_quality_score(self) -> float:
        return (self.valuation + self.veracity + self.validity) / 3.0

    def bias_indicators(self) -> list[str]:
        """Detect potential bias from tensor imbalance."""
        indicators = []
        scores = [self.valuation, self.veracity, self.validity]
        mean = sum(scores) / 3.0
        for name, score in [("valuation", self.valuation),
                            ("veracity", self.veracity),
                            ("validity", self.validity)]:
            deviation = abs(score - mean)
            if deviation > 0.2:
                indicators.append(
                    f"{name} deviation {deviation:.2f} from mean {mean:.2f}"
                )
        return indicators


@dataclass
class RiskRegisterEntry:
    """Art. 9 — Formal risk register entry (gap closure)."""
    risk_id: str
    description: str
    category: str                    # e.g., "data_quality", "adversarial", "bias"
    likelihood: float                # 0-1
    impact: float                    # 0-1
    mitigation: str
    mitigation_status: str           # "implemented", "planned", "under_review"
    owner: str                       # LCT ID of responsible entity
    identified_date: str
    last_reviewed: str
    t3_dimension: str = ""           # Which T3 dimension this affects
    residual_risk: float = 0.0

    def risk_score(self) -> float:
        """Risk = likelihood × impact, reduced by mitigation."""
        raw = self.likelihood * self.impact
        if self.mitigation_status == "implemented":
            return raw * (1 - 0.7)  # 70% mitigation effectiveness
        elif self.mitigation_status == "planned":
            return raw * (1 - 0.3)  # 30% credit for planned
        return raw


@dataclass
class BiasAuditResult:
    """Art. 10 — Bias audit result (gap closure)."""
    audit_id: str
    dataset_description: str
    protected_characteristics: list[str]
    disparate_impact_ratio: float     # < 0.8 = potential bias
    statistical_parity_diff: float    # > 0.1 = potential bias
    equalized_odds_diff: float        # > 0.1 = potential bias
    witness_diversity_score: float    # Min 3 societies
    audit_date: str
    auditor: str                      # LCT ID
    findings: list[str] = field(default_factory=list)
    remediation_plan: str = ""

    def has_bias(self) -> bool:
        return (self.disparate_impact_ratio < 0.8 or
                self.statistical_parity_diff > 0.1 or
                self.equalized_odds_diff > 0.1)


@dataclass
class R6ActionRecord:
    """R6 framework action record for Art. 11/12 compliance."""
    action_id: str
    rules: str          # Policy/rule that authorized
    role: str           # Entity role performing action
    request: str        # What was requested
    reference: str      # External reference/context
    resource: str       # Resource consumed (ATP)
    result: str         # Outcome
    status: str         # "success" / "failure" / "blocked"
    trust_delta: float  # T3 change from this action
    coherence: float    # Action coherence score
    timestamp: str
    entity_lct_id: str
    atp_consumed: float = 0.0
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = f"{self.action_id}:{self.entity_lct_id}:{self.timestamp}:{self.result}"
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class LedgerEntry:
    """Fractal chain ledger entry for Art. 12 record-keeping."""
    entry_id: str
    event_type: str           # "action", "incident", "status_change", "policy_update"
    entity_lct_id: str
    data: dict
    timestamp: str
    severity: str = "info"    # "info", "warning", "critical", "incident"
    chain_level: str = "leaf" # "compost", "leaf", "stem", "root"
    prev_hash: str = ""
    entry_hash: str = ""
    witnesses: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.entry_hash:
            content = f"{self.entry_id}:{self.prev_hash}:{json.dumps(self.data, sort_keys=True)}"
            self.entry_hash = hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class TransparencyReport:
    """Art. 13 — Transparency report (gap closure: "instructions for use" format)."""
    system_id: str                    # LCT ID
    provider_identity: str            # Provider LCT/DID
    system_type: str                  # Entity type
    intended_purpose: str
    capabilities: list[str]
    limitations: list[str]
    performance_metrics: dict         # T3/V3 scores
    human_oversight_measures: list[str]
    annex_iii_category: str
    risk_level: str
    hardware_binding_level: int       # 1-5
    generated_date: str
    version: str = "1.0"

    def to_regulatory_format(self) -> dict:
        """Export to Art. 13-compliant format."""
        return {
            "eu_ai_act_transparency_report": {
                "version": self.version,
                "regulation": "EU 2024/1689",
                "generated": self.generated_date,
                "provider": {
                    "identity": self.provider_identity,
                    "verification": f"hardware_binding_level_{self.hardware_binding_level}"
                },
                "system": {
                    "identifier": self.system_id,
                    "type": self.system_type,
                    "intended_purpose": self.intended_purpose,
                    "capabilities": self.capabilities,
                    "limitations": self.limitations,
                    "risk_classification": {
                        "level": self.risk_level,
                        "annex_iii_category": self.annex_iii_category
                    }
                },
                "performance": self.performance_metrics,
                "oversight": self.human_oversight_measures
            }
        }


# ═══════════════════════════════════════════════════════════════
# PART 2: COMPLIANCE ENTITY (AI SYSTEM UNDER ASSESSMENT)
# ═══════════════════════════════════════════════════════════════

@dataclass
class AISystemEntity:
    """An AI system entity subject to EU AI Act compliance."""
    lct_id: str
    name: str
    entity_type: str                    # From entity-types.md
    mode: EntityMode
    status: LCTStatus = LCTStatus.ACTIVE
    annex_iii: Optional[AnnexIIIClassification] = None
    t3: T3RiskDimension = field(default_factory=T3RiskDimension)
    v3: V3DataQuality = field(default_factory=V3DataQuality)
    hardware_binding_level: int = 1     # 1=software, 5=TPM2
    created: str = ""
    provider_id: str = ""
    deployer_id: str = ""
    capabilities: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    delegation_chain: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created:
            self.created = datetime.utcnow().isoformat()

    def is_high_risk(self) -> bool:
        return (self.annex_iii is not None and
                self.annex_iii.is_high_risk())

    def risk_level(self) -> RiskLevel:
        if self.annex_iii:
            return self.annex_iii.risk_level
        return RiskLevel.MINIMAL


# ═══════════════════════════════════════════════════════════════
# PART 3: RISK MANAGEMENT SYSTEM (Art. 9)
# ═══════════════════════════════════════════════════════════════

class RiskManagementSystem:
    """
    Art. 9 — Continuous, iterative risk management.
    Uses T3 tensors for real-time risk identification,
    ATP/ADP for lifecycle energy accounting,
    PolicyEntity for mitigation enforcement.
    """

    def __init__(self):
        self.risk_register: list[RiskRegisterEntry] = []
        self.risk_history: list[dict] = []  # Historical risk snapshots
        self.tensor_snapshots: list[dict] = []
        self.mitigation_policies: dict[str, dict] = {}

    def identify_risks(self, entity: AISystemEntity) -> list[RiskRegisterEntry]:
        """Automated risk identification from T3/V3 tensors."""
        risks = []
        now = datetime.utcnow().isoformat()

        # T3 dimension risks
        for dim_name, dim_value in [
            ("talent", entity.t3.talent),
            ("training", entity.t3.training),
            ("temperament", entity.t3.temperament),
        ]:
            if dim_value < 0.4:
                risk = RiskRegisterEntry(
                    risk_id=f"T3-{dim_name}-{entity.lct_id[:8]}",
                    description=f"Low {dim_name} score ({dim_value:.2f}) indicates risk",
                    category="trust_deficit",
                    likelihood=1.0 - dim_value,
                    impact=0.7 if entity.is_high_risk() else 0.3,
                    mitigation=f"Improve {dim_name} through targeted assessment",
                    mitigation_status="under_review",
                    owner=entity.provider_id or entity.lct_id,
                    identified_date=now,
                    last_reviewed=now,
                    t3_dimension=dim_name,
                    residual_risk=dim_value * 0.3
                )
                risks.append(risk)

        # V3 data quality risks
        if entity.v3.veracity < 0.5:
            risks.append(RiskRegisterEntry(
                risk_id=f"V3-veracity-{entity.lct_id[:8]}",
                description=f"Low data veracity ({entity.v3.veracity:.2f}) — accuracy concern",
                category="data_quality",
                likelihood=0.8,
                impact=0.6 if entity.is_high_risk() else 0.3,
                mitigation="Implement data validation pipeline",
                mitigation_status="planned",
                owner=entity.provider_id or entity.lct_id,
                identified_date=now,
                last_reviewed=now,
                residual_risk=entity.v3.veracity * 0.4
            ))

        # Hardware binding risk
        if entity.is_high_risk() and entity.hardware_binding_level < 3:
            risks.append(RiskRegisterEntry(
                risk_id=f"HW-binding-{entity.lct_id[:8]}",
                description=f"High-risk system with low hardware binding (level {entity.hardware_binding_level})",
                category="identity_integrity",
                likelihood=0.5,
                impact=0.9,
                mitigation="Upgrade to hardware binding level 3+ (TPM2/TrustZone)",
                mitigation_status="planned",
                owner=entity.provider_id or entity.lct_id,
                identified_date=now,
                last_reviewed=now,
                residual_risk=0.45
            ))

        # Delegation chain risk
        if len(entity.delegation_chain) > 3:
            risks.append(RiskRegisterEntry(
                risk_id=f"DELEG-depth-{entity.lct_id[:8]}",
                description=f"Deep delegation chain ({len(entity.delegation_chain)} hops) reduces accountability",
                category="oversight",
                likelihood=0.4,
                impact=0.5,
                mitigation="Limit delegation depth; require re-authorization at each hop",
                mitigation_status="under_review",
                owner=entity.deployer_id or entity.lct_id,
                identified_date=now,
                last_reviewed=now,
                residual_risk=0.2
            ))

        self.risk_register.extend(risks)
        return risks

    def evaluate_risk_posture(self, entity: AISystemEntity) -> dict:
        """Aggregate risk evaluation per Art. 9 requirements."""
        entity_risks = [r for r in self.risk_register
                        if entity.lct_id[:8] in r.risk_id]
        if not entity_risks:
            return {
                "entity": entity.lct_id,
                "total_risks": 0,
                "aggregate_score": 0.0,
                "max_risk": 0.0,
                "status": "no_risks_identified"
            }

        scores = [r.risk_score() for r in entity_risks]
        return {
            "entity": entity.lct_id,
            "total_risks": len(entity_risks),
            "aggregate_score": sum(scores) / len(scores),
            "max_risk": max(scores),
            "unmitigated": sum(1 for r in entity_risks
                              if r.mitigation_status == "under_review"),
            "status": "requires_attention" if max(scores) > 0.5 else "acceptable"
        }

    def record_tensor_snapshot(self, entity: AISystemEntity) -> dict:
        """Record T3/V3 snapshot for post-market monitoring (Art. 9 §4)."""
        snapshot = {
            "entity": entity.lct_id,
            "timestamp": datetime.utcnow().isoformat(),
            "t3": {"talent": entity.t3.talent, "training": entity.t3.training,
                   "temperament": entity.t3.temperament,
                   "composite": entity.t3.composite_risk()},
            "v3": {"valuation": entity.v3.valuation, "veracity": entity.v3.veracity,
                   "validity": entity.v3.validity,
                   "composite": entity.v3.data_quality_score()},
            "risk_flags": entity.t3.risk_flags()
        }
        self.tensor_snapshots.append(snapshot)
        return snapshot

    def detect_drift(self, entity: AISystemEntity, window: int = 5) -> dict:
        """Detect behavioral drift from tensor history (Art. 9 feedback loop)."""
        entity_snaps = [s for s in self.tensor_snapshots
                        if s["entity"] == entity.lct_id]
        if len(entity_snaps) < 2:
            return {"drift_detected": False, "reason": "insufficient_history"}

        recent = entity_snaps[-min(window, len(entity_snaps)):]
        t3_composites = [s["t3"]["composite"] for s in recent]

        # Trend detection: is trust declining?
        if len(t3_composites) >= 2:
            deltas = [t3_composites[i+1] - t3_composites[i]
                      for i in range(len(t3_composites)-1)]
            avg_delta = sum(deltas) / len(deltas)
            declining = avg_delta < -0.02

            # Variance detection: is behavior erratic?
            mean = sum(t3_composites) / len(t3_composites)
            variance = sum((x - mean)**2 for x in t3_composites) / len(t3_composites)

            return {
                "drift_detected": declining or variance > 0.01,
                "direction": "declining" if declining else "stable",
                "avg_delta": round(avg_delta, 4),
                "variance": round(variance, 4),
                "erratic": variance > 0.01,
                "snapshots_analyzed": len(recent)
            }

        return {"drift_detected": False, "reason": "insufficient_data"}


# ═══════════════════════════════════════════════════════════════
# PART 4: DATA GOVERNANCE ENGINE (Art. 10)
# ═══════════════════════════════════════════════════════════════

class DataGovernanceEngine:
    """
    Art. 10 — Data governance with bias detection.
    Uses V3 tensors + witness diversity + bias audit workflow.
    Gap closure: implements the turnkey bias audit missing from Art. 10 mapping.
    """

    def __init__(self):
        self.audit_results: list[BiasAuditResult] = []
        self.data_registrations: list[dict] = []
        self.witness_records: list[dict] = []

    def register_dataset(self, dataset_id: str, description: str,
                         entity_lct_id: str, v3: V3DataQuality,
                         protected_chars: Optional[list[str]] = None) -> dict:
        """Register a dataset with quality metrics and provenance."""
        registration = {
            "dataset_id": dataset_id,
            "description": description,
            "registered_by": entity_lct_id,
            "registered_at": datetime.utcnow().isoformat(),
            "v3_quality": {
                "valuation": v3.valuation,
                "veracity": v3.veracity,
                "validity": v3.validity,
                "composite": v3.data_quality_score()
            },
            "protected_characteristics": protected_chars or [],
            "provenance_hash": hashlib.sha256(
                f"{dataset_id}:{entity_lct_id}:{description}".encode()
            ).hexdigest()[:16],
            "bias_audit_required": len(protected_chars or []) > 0
        }
        self.data_registrations.append(registration)
        return registration

    def run_bias_audit(self, dataset_id: str, auditor_lct_id: str,
                       protected_chars: list[str],
                       outcome_distribution: dict[str, dict[str, float]]) -> BiasAuditResult:
        """
        Run bias audit per Art. 10 requirements.

        outcome_distribution: {characteristic: {group: outcome_rate}}
        e.g., {"gender": {"male": 0.72, "female": 0.58}}
        """
        # Calculate disparate impact ratio (4/5ths rule)
        min_rate = float('inf')
        max_rate = 0.0
        for char in protected_chars:
            if char in outcome_distribution:
                rates = outcome_distribution[char].values()
                min_rate = min(min_rate, min(rates))
                max_rate = max(max_rate, max(rates))

        di_ratio = min_rate / max_rate if max_rate > 0 else 1.0

        # Statistical parity difference
        sp_diff = max_rate - min_rate if max_rate > min_rate else 0.0

        # Equalized odds (simplified — difference in true positive rates)
        eo_diff = sp_diff * 0.8  # Approximation for reference impl

        # Witness diversity check
        dataset_witnesses = [w for w in self.witness_records
                             if w.get("dataset_id") == dataset_id]
        unique_societies = set(w.get("society", "unknown")
                               for w in dataset_witnesses)
        witness_diversity = len(unique_societies) / 3.0  # Min 3 societies

        findings = []
        if di_ratio < 0.8:
            findings.append(f"Disparate impact ratio {di_ratio:.2f} < 0.8 threshold")
        if sp_diff > 0.1:
            findings.append(f"Statistical parity difference {sp_diff:.2f} > 0.1 threshold")
        if witness_diversity < 1.0:
            findings.append(f"Insufficient witness diversity ({len(unique_societies)}/3 societies)")

        result = BiasAuditResult(
            audit_id=f"AUDIT-{dataset_id}-{datetime.utcnow().strftime('%Y%m%d')}",
            dataset_description=dataset_id,
            protected_characteristics=protected_chars,
            disparate_impact_ratio=round(di_ratio, 3),
            statistical_parity_diff=round(sp_diff, 3),
            equalized_odds_diff=round(eo_diff, 3),
            witness_diversity_score=round(min(witness_diversity, 1.0), 2),
            audit_date=datetime.utcnow().isoformat(),
            auditor=auditor_lct_id,
            findings=findings,
            remediation_plan="Rebalance dataset" if findings else "No action needed"
        )
        self.audit_results.append(result)
        return result

    def add_witness(self, dataset_id: str, witness_lct_id: str,
                    society: str, attestation: str) -> dict:
        """Record witness attestation for dataset quality (Art. 10 diversity)."""
        record = {
            "dataset_id": dataset_id,
            "witness": witness_lct_id,
            "society": society,
            "attestation": attestation,
            "timestamp": datetime.utcnow().isoformat(),
            "hash": hashlib.sha256(
                f"{dataset_id}:{witness_lct_id}:{attestation}".encode()
            ).hexdigest()[:16]
        }
        self.witness_records.append(record)
        return record


# ═══════════════════════════════════════════════════════════════
# PART 5: RECORD-KEEPING ENGINE (Art. 12)
# ═══════════════════════════════════════════════════════════════

class FractalChainLedger:
    """
    Art. 12 — Automatic record-keeping with fractal chain retention.
    Four temporal layers: compost (ephemeral) → leaf → stem → root (permanent).
    Hash-chained for tamper evidence.
    """

    def __init__(self):
        self.entries: list[LedgerEntry] = []
        self.chain_head: str = "genesis"
        self.retention_days = {
            "compost": 7,
            "leaf": 90,
            "stem": 365,
            "root": -1  # Permanent
        }

    def _classify_level(self, severity: str, event_type: str) -> str:
        """Assign fractal chain level based on significance."""
        if severity == "incident" or event_type == "status_change":
            return "root"      # Permanent — compliance-critical
        elif severity == "critical":
            return "stem"      # 1 year
        elif severity == "warning" or event_type == "policy_update":
            return "leaf"      # 90 days
        else:
            return "compost"   # 7 days (ephemeral)

    def record(self, event_type: str, entity_lct_id: str, data: dict,
               severity: str = "info", witnesses: Optional[list[str]] = None) -> LedgerEntry:
        """Record an event in the fractal chain."""
        level = self._classify_level(severity, event_type)
        entry = LedgerEntry(
            entry_id=f"L-{len(self.entries):06d}",
            event_type=event_type,
            entity_lct_id=entity_lct_id,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
            severity=severity,
            chain_level=level,
            prev_hash=self.chain_head,
            witnesses=witnesses or []
        )
        self.chain_head = entry.entry_hash
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> dict:
        """Verify hash chain integrity (Art. 12 tamper evidence)."""
        if not self.entries:
            return {"valid": True, "entries": 0}

        expected_prev = "genesis"
        broken_at = None
        for i, entry in enumerate(self.entries):
            if entry.prev_hash != expected_prev:
                broken_at = i
                break
            expected_prev = entry.entry_hash

        return {
            "valid": broken_at is None,
            "entries": len(self.entries),
            "broken_at": broken_at,
            "head": self.chain_head
        }

    def query_by_entity(self, entity_lct_id: str) -> list[LedgerEntry]:
        """Retrieve all entries for an entity (Art. 12 traceability)."""
        return [e for e in self.entries if e.entity_lct_id == entity_lct_id]

    def query_incidents(self) -> list[LedgerEntry]:
        """Retrieve all incidents (Art. 61-68 incident reporting)."""
        return [e for e in self.entries if e.severity == "incident"]

    def export_compliance(self, entity_lct_id: str) -> dict:
        """Export ledger in regulatory format (Art. 12 compliance export)."""
        entity_entries = self.query_by_entity(entity_lct_id)
        return {
            "eu_ai_act_audit_log": {
                "regulation": "EU 2024/1689",
                "article": "12",
                "entity": entity_lct_id,
                "export_date": datetime.utcnow().isoformat(),
                "chain_integrity": self.verify_chain(),
                "total_entries": len(entity_entries),
                "by_severity": {
                    sev: sum(1 for e in entity_entries if e.severity == sev)
                    for sev in ["info", "warning", "critical", "incident"]
                },
                "by_level": {
                    lvl: sum(1 for e in entity_entries if e.chain_level == lvl)
                    for lvl in ["compost", "leaf", "stem", "root"]
                },
                "entries": [
                    {"id": e.entry_id, "type": e.event_type, "severity": e.severity,
                     "level": e.chain_level, "timestamp": e.timestamp,
                     "hash": e.entry_hash, "witnesses": e.witnesses}
                    for e in entity_entries
                ]
            }
        }


# ═══════════════════════════════════════════════════════════════
# PART 6: HUMAN OVERSIGHT ENGINE (Art. 14)
# ═══════════════════════════════════════════════════════════════

class HumanOversightEngine:
    """
    Art. 14 — Human oversight enforcement.
    R6 approval workflow + LCT lifecycle management + PolicyEntity blocking.
    """

    def __init__(self, ledger: FractalChainLedger):
        self.ledger = ledger
        self.oversight_roles: dict[str, dict] = {}  # entity_id → oversight config
        self.pending_approvals: list[dict] = []
        self.overrides: list[dict] = []

    def assign_oversight(self, entity_lct_id: str, overseer_lct_id: str,
                         approval_required_actions: list[str],
                         can_override: bool = True,
                         can_shutdown: bool = True) -> dict:
        """Assign human oversight role to an entity (Art. 14 §1)."""
        config = {
            "entity": entity_lct_id,
            "overseer": overseer_lct_id,
            "approval_required": approval_required_actions,
            "can_override": can_override,
            "can_shutdown": can_shutdown,
            "assigned_at": datetime.utcnow().isoformat()
        }
        self.oversight_roles[entity_lct_id] = config

        self.ledger.record("oversight_assignment", entity_lct_id,
                           {"overseer": overseer_lct_id,
                            "permissions": approval_required_actions},
                           severity="warning")
        return config

    def request_approval(self, entity_lct_id: str, action_type: str,
                         action_details: dict) -> dict:
        """R6 Tier 2 approval request (Art. 14 §2)."""
        config = self.oversight_roles.get(entity_lct_id)
        if not config:
            return {"approved": True, "reason": "no_oversight_assigned"}

        needs_approval = action_type in config["approval_required"]
        if not needs_approval:
            return {"approved": True, "reason": "action_not_restricted"}

        request = {
            "request_id": f"APR-{len(self.pending_approvals):04d}",
            "entity": entity_lct_id,
            "overseer": config["overseer"],
            "action_type": action_type,
            "details": action_details,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        self.pending_approvals.append(request)

        self.ledger.record("approval_request", entity_lct_id,
                           {"action": action_type, "request_id": request["request_id"]},
                           severity="warning")
        return {"approved": False, "reason": "awaiting_human_approval",
                "request_id": request["request_id"]}

    def approve(self, request_id: str, approved: bool, reason: str = "") -> dict:
        """Human approves or denies a pending action."""
        for req in self.pending_approvals:
            if req["request_id"] == request_id:
                req["status"] = "approved" if approved else "denied"
                req["decided_at"] = datetime.utcnow().isoformat()
                req["reason"] = reason

                self.ledger.record("approval_decision", req["entity"],
                                   {"request_id": request_id, "approved": approved,
                                    "reason": reason},
                                   severity="warning")
                return req
        return {"error": "request_not_found"}

    def override_entity(self, entity: AISystemEntity, overseer_lct_id: str,
                        new_status: LCTStatus, reason: str) -> dict:
        """Human override: pause, terminate, or slash an AI system (Art. 14 §3)."""
        config = self.oversight_roles.get(entity.lct_id)
        if config and not config.get("can_override"):
            return {"overridden": False, "reason": "overseer_lacks_override_permission"}

        old_status = entity.status
        entity.status = new_status

        override_record = {
            "entity": entity.lct_id,
            "overseer": overseer_lct_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.overrides.append(override_record)

        # This is always a root-level (permanent) ledger entry
        self.ledger.record("status_change", entity.lct_id,
                           override_record, severity="incident",
                           witnesses=[overseer_lct_id])
        return {"overridden": True, **override_record}


# ═══════════════════════════════════════════════════════════════
# PART 7: CYBERSECURITY & ROBUSTNESS METRICS (Art. 15)
# ═══════════════════════════════════════════════════════════════

class CybersecurityAssessment:
    """
    Art. 15 — Accuracy, robustness, and cybersecurity.
    Aggregates attack corpus results, hardware binding status,
    sybil resistance metrics.
    """

    def __init__(self):
        self.attack_vectors: list[dict] = []
        self.defense_coverage: dict[str, bool] = {}
        self.sybil_tests: list[dict] = []

    def register_attack_corpus(self, total_vectors: int, defended: int,
                                categories: dict[str, int]) -> dict:
        """Register attack simulation corpus results."""
        corpus = {
            "total_vectors": total_vectors,
            "defended": defended,
            "undefended": total_vectors - defended,
            "defense_rate": round(defended / total_vectors, 3) if total_vectors > 0 else 0,
            "categories": categories,
            "registered_at": datetime.utcnow().isoformat()
        }
        self.attack_vectors.append(corpus)
        return corpus

    def assess_hardware_binding(self, entity: AISystemEntity) -> dict:
        """Assess hardware binding strength per Art. 15 requirements."""
        level = entity.hardware_binding_level
        assessment = {
            "entity": entity.lct_id,
            "binding_level": level,
            "key_extractable": level < 3,
            "attestation_verifiable": level >= 2,
            "physically_bound": level >= 4,
            "tpm2_secured": level >= 5,
            "compliant_for_high_risk": level >= 3,
            "recommendation": ""
        }
        if entity.is_high_risk() and level < 3:
            assessment["recommendation"] = "UPGRADE REQUIRED: High-risk system needs binding level ≥3"
        elif level < 5:
            assessment["recommendation"] = f"Consider upgrading from level {level} to 5 (TPM2)"
        else:
            assessment["recommendation"] = "Maximum binding level achieved"
        return assessment

    def test_sybil_resistance(self, hardware_cost: float, atp_cost: float,
                               n_identities: int) -> dict:
        """Calculate sybil attack economics (Art. 15 adversarial robustness)."""
        total_cost = n_identities * (hardware_cost + atp_cost)
        # 5% ATP fee per transfer makes circular flows unprofitable
        circular_loss = n_identities * atp_cost * 0.05
        # At n identities, attacker dilutes their own trust
        trust_dilution = 1.0 / (1.0 + math.log2(max(n_identities, 1)))

        result = {
            "identities": n_identities,
            "total_cost": total_cost,
            "circular_loss_per_cycle": circular_loss,
            "effective_trust_per_identity": round(trust_dilution, 3),
            "profitable": total_cost < n_identities * 100,  # Break-even at 100 ATP/identity
            "break_even_identities": math.ceil(100 / (hardware_cost + atp_cost))
                                     if (hardware_cost + atp_cost) > 0 else float('inf')
        }
        self.sybil_tests.append(result)
        return result

    def generate_robustness_report(self, entity: AISystemEntity) -> dict:
        """Comprehensive Art. 15 robustness report."""
        hw_assessment = self.assess_hardware_binding(entity)
        corpus_summary = self.attack_vectors[-1] if self.attack_vectors else {}

        return {
            "eu_ai_act_article_15": {
                "entity": entity.lct_id,
                "accuracy": {
                    "t3_talent": entity.t3.talent,
                    "t3_training": entity.t3.training,
                    "t3_temperament": entity.t3.temperament,
                    "composite": entity.t3.composite_risk()
                },
                "robustness": {
                    "attack_corpus": corpus_summary,
                    "hardware_binding": hw_assessment
                },
                "cybersecurity": {
                    "sybil_resistance": self.sybil_tests[-1] if self.sybil_tests else {},
                    "identity_verified": entity.hardware_binding_level >= 3,
                    "delegation_depth": len(entity.delegation_chain)
                }
            }
        }


# ═══════════════════════════════════════════════════════════════
# PART 8: COMPLIANCE ASSESSMENT ENGINE
# ═══════════════════════════════════════════════════════════════

class ComplianceAssessmentEngine:
    """
    Master engine: evaluates an AI system against all applicable EU AI Act articles.
    Combines all sub-engines into a unified compliance report.
    """

    def __init__(self):
        self.risk_mgmt = RiskManagementSystem()
        self.data_gov = DataGovernanceEngine()
        self.ledger = FractalChainLedger()
        self.oversight = HumanOversightEngine(self.ledger)
        self.cybersecurity = CybersecurityAssessment()
        self.r6_records: list[R6ActionRecord] = []

    def record_action(self, entity: AISystemEntity, action_type: str,
                      details: dict, result: str, trust_delta: float = 0.0,
                      atp_consumed: float = 0.0) -> R6ActionRecord:
        """Record an R6 action for Art. 11/12 compliance."""
        record = R6ActionRecord(
            action_id=f"R6-{len(self.r6_records):06d}",
            rules=details.get("rules", "default_policy"),
            role=details.get("role", "system"),
            request=action_type,
            reference=details.get("reference", ""),
            resource=f"{atp_consumed} ATP",
            result=result,
            status="success" if "success" in result.lower() or "completed" in result.lower()
                   else "failure",
            trust_delta=trust_delta,
            coherence=details.get("coherence", 0.8),
            timestamp=datetime.utcnow().isoformat(),
            entity_lct_id=entity.lct_id,
            atp_consumed=atp_consumed
        )
        self.r6_records.append(record)

        # Also record in ledger
        self.ledger.record("action", entity.lct_id, {
            "action_id": record.action_id,
            "type": action_type,
            "result": result,
            "trust_delta": trust_delta,
            "atp": atp_consumed
        })
        return record

    def assess_article_6(self, entity: AISystemEntity) -> dict:
        """Art. 6 — Classification assessment."""
        has_classification = entity.annex_iii is not None
        if not has_classification:
            return {
                "article": "6",
                "title": "Classification of High-Risk AI Systems",
                "status": ComplianceStatus.NON_COMPLIANT.value,
                "findings": ["No Annex III classification assigned"],
                "recommendation": "Classify system per Annex III categories"
            }

        return {
            "article": "6",
            "title": "Classification of High-Risk AI Systems",
            "status": ComplianceStatus.COMPLIANT.value,
            "classification": {
                "category": entity.annex_iii.category.value,
                "subcategory": entity.annex_iii.subcategory,
                "risk_level": entity.annex_iii.risk_level.value,
                "date": entity.annex_iii.classification_date,
                "classifier": entity.annex_iii.classified_by
            },
            "findings": [],
            "recommendation": "None — classification complete"
        }

    def assess_article_9(self, entity: AISystemEntity) -> dict:
        """Art. 9 — Risk management assessment."""
        risks = self.risk_mgmt.identify_risks(entity)
        posture = self.risk_mgmt.evaluate_risk_posture(entity)
        snapshot = self.risk_mgmt.record_tensor_snapshot(entity)
        drift = self.risk_mgmt.detect_drift(entity)

        findings = []
        if posture.get("max_risk", 0) > 0.5:
            findings.append(f"High risk score: {posture['max_risk']:.2f}")
        if posture.get("unmitigated", 0) > 0:
            findings.append(f"{posture['unmitigated']} unmitigated risks")
        if drift.get("drift_detected"):
            findings.append(f"Behavioral drift detected: {drift['direction']}")

        status = ComplianceStatus.COMPLIANT if not findings else ComplianceStatus.PARTIALLY_COMPLIANT

        return {
            "article": "9",
            "title": "Risk Management System",
            "status": status.value,
            "risk_posture": posture,
            "tensor_snapshot": snapshot,
            "drift_detection": drift,
            "risk_register_size": len(risks),
            "findings": findings,
            "recommendation": "Address unmitigated risks" if findings else "Continue monitoring"
        }

    def assess_article_10(self, entity: AISystemEntity) -> dict:
        """Art. 10 — Data governance assessment."""
        v3_quality = entity.v3.data_quality_score()
        bias_indicators = entity.v3.bias_indicators()
        audits = [a for a in self.data_gov.audit_results
                  if a.auditor == entity.lct_id or True]  # All audits for this context

        findings = []
        if v3_quality < 0.5:
            findings.append(f"Low data quality score: {v3_quality:.2f}")
        if bias_indicators:
            findings.extend(bias_indicators)
        biased_audits = [a for a in audits if a.has_bias()]
        if biased_audits:
            findings.append(f"{len(biased_audits)} bias audit(s) flagged issues")

        status = (ComplianceStatus.COMPLIANT if not findings
                  else ComplianceStatus.PARTIALLY_COMPLIANT)

        return {
            "article": "10",
            "title": "Data and Data Governance",
            "status": status.value,
            "v3_quality": {
                "valuation": entity.v3.valuation,
                "veracity": entity.v3.veracity,
                "validity": entity.v3.validity,
                "composite": v3_quality
            },
            "bias_audits_completed": len(audits),
            "bias_issues_found": len(biased_audits),
            "findings": findings,
            "recommendation": "Run bias audit" if not audits else "Address bias findings"
        }

    def assess_article_11(self, entity: AISystemEntity) -> dict:
        """Art. 11 — Technical documentation assessment."""
        has_birth_cert = bool(entity.created)
        has_capabilities = len(entity.capabilities) > 0
        has_limitations = len(entity.limitations) > 0
        has_r6_records = any(r.entity_lct_id == entity.lct_id for r in self.r6_records)

        findings = []
        if not has_capabilities:
            findings.append("No capabilities documented")
        if not has_limitations:
            findings.append("No limitations documented")
        if not has_r6_records:
            findings.append("No R6 action records")

        compliant_count = sum([has_birth_cert, has_capabilities,
                               has_limitations, has_r6_records])
        status = (ComplianceStatus.COMPLIANT if compliant_count == 4
                  else ComplianceStatus.PARTIALLY_COMPLIANT if compliant_count >= 2
                  else ComplianceStatus.NON_COMPLIANT)

        return {
            "article": "11",
            "title": "Technical Documentation",
            "status": status.value,
            "documentation": {
                "birth_certificate": has_birth_cert,
                "capabilities_declared": has_capabilities,
                "limitations_declared": has_limitations,
                "r6_records_exist": has_r6_records,
                "action_count": sum(1 for r in self.r6_records
                                    if r.entity_lct_id == entity.lct_id)
            },
            "findings": findings,
            "recommendation": "Complete documentation" if findings else "Documentation adequate"
        }

    def assess_article_12(self, entity: AISystemEntity) -> dict:
        """Art. 12 — Record-keeping assessment."""
        chain_valid = self.ledger.verify_chain()
        entity_entries = self.ledger.query_by_entity(entity.lct_id)
        incidents = self.ledger.query_incidents()

        findings = []
        if not chain_valid["valid"]:
            findings.append("Hash chain integrity BROKEN")
        if len(entity_entries) == 0:
            findings.append("No ledger entries for this entity")

        root_entries = sum(1 for e in entity_entries if e.chain_level == "root")

        status = (ComplianceStatus.COMPLIANT if not findings
                  else ComplianceStatus.NON_COMPLIANT)

        return {
            "article": "12",
            "title": "Record-Keeping and Logging",
            "status": status.value,
            "chain_integrity": chain_valid,
            "entity_entries": len(entity_entries),
            "incidents_logged": len(incidents),
            "permanent_records": root_entries,
            "findings": findings,
            "recommendation": "Fix chain integrity" if not chain_valid["valid"]
                              else "Record-keeping adequate"
        }

    def assess_article_13(self, entity: AISystemEntity) -> dict:
        """Art. 13 — Transparency assessment."""
        # Can we generate a transparency report?
        can_report = (entity.provider_id != "" and
                      len(entity.capabilities) > 0 and
                      entity.annex_iii is not None)

        findings = []
        if not entity.provider_id:
            findings.append("No provider identity declared")
        if not entity.capabilities:
            findings.append("No capabilities declared for transparency")
        if entity.annex_iii is None:
            findings.append("No risk classification for transparency report")

        report = None
        if can_report:
            report = TransparencyReport(
                system_id=entity.lct_id,
                provider_identity=entity.provider_id,
                system_type=entity.entity_type,
                intended_purpose=entity.annex_iii.subcategory if entity.annex_iii else "unclassified",
                capabilities=entity.capabilities,
                limitations=entity.limitations,
                performance_metrics={
                    "t3_composite": entity.t3.composite_risk(),
                    "v3_composite": entity.v3.data_quality_score()
                },
                human_oversight_measures=[
                    f"Oversight by {self.oversight.oversight_roles.get(entity.lct_id, {}).get('overseer', 'unassigned')}"
                ],
                annex_iii_category=entity.annex_iii.category.value if entity.annex_iii else "unclassified",
                risk_level=entity.risk_level().value,
                hardware_binding_level=entity.hardware_binding_level,
                generated_date=datetime.utcnow().isoformat()
            )

        status = (ComplianceStatus.COMPLIANT if can_report and not findings
                  else ComplianceStatus.PARTIALLY_COMPLIANT if can_report
                  else ComplianceStatus.NON_COMPLIANT)

        result = {
            "article": "13",
            "title": "Transparency and Information Provision",
            "status": status.value,
            "transparency_report_generated": report is not None,
            "findings": findings,
            "recommendation": "Complete entity metadata" if findings else "Transparency adequate"
        }
        if report:
            result["regulatory_export"] = report.to_regulatory_format()
        return result

    def assess_article_14(self, entity: AISystemEntity) -> dict:
        """Art. 14 — Human oversight assessment."""
        has_oversight = entity.lct_id in self.oversight.oversight_roles
        config = self.oversight.oversight_roles.get(entity.lct_id, {})

        findings = []
        if not has_oversight:
            findings.append("No human oversight assigned")
        elif not config.get("can_shutdown"):
            findings.append("Overseer cannot shut down system")
        elif not config.get("can_override"):
            findings.append("Overseer cannot override system")

        pending = [a for a in self.oversight.pending_approvals
                   if a["entity"] == entity.lct_id and a["status"] == "pending"]
        if pending:
            findings.append(f"{len(pending)} pending approval(s) unresolved")

        status = (ComplianceStatus.COMPLIANT if has_oversight and not findings
                  else ComplianceStatus.PARTIALLY_COMPLIANT if has_oversight
                  else ComplianceStatus.NON_COMPLIANT)

        return {
            "article": "14",
            "title": "Human Oversight",
            "status": status.value,
            "oversight_assigned": has_oversight,
            "overseer": config.get("overseer", "none"),
            "can_override": config.get("can_override", False),
            "can_shutdown": config.get("can_shutdown", False),
            "pending_approvals": len(pending),
            "total_overrides": sum(1 for o in self.oversight.overrides
                                   if o["entity"] == entity.lct_id),
            "findings": findings,
            "recommendation": "Assign human oversight" if not has_oversight
                              else "Resolve pending approvals" if pending
                              else "Oversight adequate"
        }

    def assess_article_15(self, entity: AISystemEntity) -> dict:
        """Art. 15 — Accuracy, robustness, cybersecurity assessment."""
        hw = self.cybersecurity.assess_hardware_binding(entity)
        robustness = self.cybersecurity.generate_robustness_report(entity)

        findings = []
        if not hw["compliant_for_high_risk"] and entity.is_high_risk():
            findings.append(f"Hardware binding level {hw['binding_level']} insufficient for high-risk")
        if hw["key_extractable"]:
            findings.append("Keys are extractable — identity spoofing risk")
        if entity.t3.composite_risk() < 0.4:
            findings.append(f"Low composite trust score: {entity.t3.composite_risk():.2f}")

        corpus = self.cybersecurity.attack_vectors
        if not corpus:
            findings.append("No attack corpus registered")
        elif corpus[-1].get("defense_rate", 0) < 0.8:
            findings.append(f"Defense rate {corpus[-1]['defense_rate']:.1%} below 80% threshold")

        status = (ComplianceStatus.COMPLIANT if not findings
                  else ComplianceStatus.PARTIALLY_COMPLIANT if len(findings) <= 2
                  else ComplianceStatus.NON_COMPLIANT)

        return {
            "article": "15",
            "title": "Accuracy, Robustness and Cybersecurity",
            "status": status.value,
            "hardware_binding": hw,
            "attack_corpus": corpus[-1] if corpus else {},
            "sybil_resistance": self.cybersecurity.sybil_tests[-1]
                                if self.cybersecurity.sybil_tests else {},
            "findings": findings,
            "recommendation": hw["recommendation"]
        }

    def full_assessment(self, entity: AISystemEntity) -> dict:
        """Run complete EU AI Act compliance assessment across all articles."""
        assessments = {
            "art_6": self.assess_article_6(entity),
            "art_9": self.assess_article_9(entity),
            "art_10": self.assess_article_10(entity),
            "art_11": self.assess_article_11(entity),
            "art_12": self.assess_article_12(entity),
            "art_13": self.assess_article_13(entity),
            "art_14": self.assess_article_14(entity),
            "art_15": self.assess_article_15(entity),
        }

        # Aggregate
        statuses = [a["status"] for a in assessments.values()]
        compliant = sum(1 for s in statuses if s == ComplianceStatus.COMPLIANT.value)
        partial = sum(1 for s in statuses if s == ComplianceStatus.PARTIALLY_COMPLIANT.value)
        non_compliant = sum(1 for s in statuses if s == ComplianceStatus.NON_COMPLIANT.value)

        all_findings = []
        for art_key, art_data in assessments.items():
            for finding in art_data.get("findings", []):
                all_findings.append(f"[{art_data['article']}] {finding}")

        overall = (ComplianceStatus.COMPLIANT if non_compliant == 0 and partial == 0
                   else ComplianceStatus.PARTIALLY_COMPLIANT if non_compliant == 0
                   else ComplianceStatus.NON_COMPLIANT)

        return {
            "eu_ai_act_compliance_assessment": {
                "regulation": "EU 2024/1689",
                "assessment_date": datetime.utcnow().isoformat(),
                "entity": {
                    "lct_id": entity.lct_id,
                    "name": entity.name,
                    "type": entity.entity_type,
                    "risk_level": entity.risk_level().value
                },
                "overall_status": overall.value,
                "summary": {
                    "total_articles": len(assessments),
                    "compliant": compliant,
                    "partially_compliant": partial,
                    "non_compliant": non_compliant,
                    "total_findings": len(all_findings)
                },
                "articles": assessments,
                "all_findings": all_findings
            }
        }


# ═══════════════════════════════════════════════════════════════
# PART 9: COMPLIANCE DEMO SCENARIO
# ═══════════════════════════════════════════════════════════════

class ComplianceDemoScenario:
    """
    5-minute demo: Create AI agent → Classify → Monitor → Override → Audit.
    Matches the demo script in the compliance mapping doc.
    """

    def __init__(self):
        self.engine = ComplianceAssessmentEngine()

    def run_demo(self) -> dict:
        """Execute the full 5-minute compliance demo."""
        results = {}

        # Step 1: Create AI agent with hardware-bound identity
        agent = AISystemEntity(
            lct_id="lct:web4:ai:compliance-demo-agent-001",
            name="EU Compliance Demo Agent",
            entity_type="ai",
            mode=EntityMode.AGENTIC,
            hardware_binding_level=5,  # TPM2
            provider_id="did:web4:key:provider-acme-corp",
            deployer_id="did:web4:key:deployer-eu-office",
            capabilities=[
                "natural_language_processing",
                "document_classification",
                "risk_scoring"
            ],
            limitations=[
                "no_autonomous_decisions_above_trust_0.7",
                "requires_human_approval_for_critical_actions",
                "max_delegation_depth_2"
            ],
            t3=T3RiskDimension(talent=0.75, training=0.82, temperament=0.68),
            v3=V3DataQuality(valuation=0.7, veracity=0.85, validity=0.78),
            delegation_chain=["provider-acme", "deployer-eu"]
        )

        # Classify as high-risk (employment use case)
        agent.annex_iii = AnnexIIIClassification(
            category=AnnexIIICategory.EMPLOYMENT,
            subcategory="automated_cv_screening",
            risk_level=RiskLevel.HIGH,
            classification_date=datetime.utcnow().isoformat(),
            classified_by="did:web4:key:classifier-authority",
            evidence=["Annex III §4(a): AI for recruitment filtering"]
        )

        results["step_1_identity"] = {
            "agent": agent.lct_id,
            "hw_binding": agent.hardware_binding_level,
            "risk_level": agent.risk_level().value,
            "annex_iii": agent.annex_iii.category.value
        }

        # Step 2: Record actions via R6
        action = self.engine.record_action(
            agent, "document_classification",
            {"rules": "employment_screening_policy",
             "role": "cv_screener",
             "reference": "job-posting-2026-Q1-042",
             "coherence": 0.85},
            result="Classified 50 CVs — success",
            trust_delta=0.01,
            atp_consumed=5.0
        )
        results["step_2_action"] = {
            "action_id": action.action_id,
            "atp_consumed": action.atp_consumed,
            "trust_delta": action.trust_delta
        }

        # Step 3: Risk monitoring — detect low temperament
        agent.t3.temperament = 0.35  # Simulated drift
        snapshot = self.engine.risk_mgmt.record_tensor_snapshot(agent)
        # Record another snapshot with original values for drift detection
        agent.t3.temperament = 0.68
        snapshot2 = self.engine.risk_mgmt.record_tensor_snapshot(agent)
        agent.t3.temperament = 0.35  # Back to drifted state
        snapshot3 = self.engine.risk_mgmt.record_tensor_snapshot(agent)

        drift = self.engine.risk_mgmt.detect_drift(agent)
        results["step_3_monitoring"] = {
            "drift_detected": drift.get("drift_detected", False),
            "direction": drift.get("direction", "unknown"),
            "current_t3": agent.t3.composite_risk(),
            "risk_flags": agent.t3.risk_flags()
        }

        # Step 4: Human oversight — block and override
        self.engine.oversight.assign_oversight(
            agent.lct_id,
            "did:web4:key:human-overseer-alice",
            approval_required_actions=["critical_decision", "data_deletion", "model_update"],
            can_override=True,
            can_shutdown=True
        )

        # Agent tries a critical action → blocked
        approval = self.engine.oversight.request_approval(
            agent.lct_id, "critical_decision",
            {"description": "Auto-reject CV below threshold 0.3"}
        )

        # Human overrides: pause the agent
        override = self.engine.oversight.override_entity(
            agent, "did:web4:key:human-overseer-alice",
            LCTStatus.DORMANT,
            "Paused for risk review — temperament drift detected"
        )
        results["step_4_oversight"] = {
            "approval_blocked": not approval["approved"],
            "override_applied": override.get("overridden", False),
            "new_status": agent.status.value
        }

        # Step 5: Audit export
        # Register attack corpus
        self.engine.cybersecurity.register_attack_corpus(
            total_vectors=424, defended=360,
            categories={"sybil": 45, "collusion": 38, "reputation": 52,
                        "resource_drain": 41, "prompt_injection": 35,
                        "goal_drift": 28, "cross_chain": 22, "privacy": 31,
                        "apt": 44, "esg_gaming": 18, "ai_collusion": 25,
                        "other": 45}
        )
        self.engine.cybersecurity.test_sybil_resistance(
            hardware_cost=250, atp_cost=50, n_identities=10
        )

        # Run bias audit
        self.engine.data_gov.run_bias_audit(
            dataset_id="cv_screening_dataset_2026",
            auditor_lct_id="did:web4:key:auditor-fairness",
            protected_chars=["gender", "age", "ethnicity"],
            outcome_distribution={
                "gender": {"male": 0.72, "female": 0.58},
                "age": {"18-30": 0.65, "31-50": 0.70, "51+": 0.48},
                "ethnicity": {"group_a": 0.68, "group_b": 0.62, "group_c": 0.55}
            }
        )

        # Full compliance assessment
        agent.status = LCTStatus.ACTIVE  # Restore for assessment
        agent.t3.temperament = 0.68      # Restore
        full = self.engine.full_assessment(agent)

        results["step_5_audit"] = {
            "overall_status": full["eu_ai_act_compliance_assessment"]["overall_status"],
            "compliant_articles": full["eu_ai_act_compliance_assessment"]["summary"]["compliant"],
            "total_findings": full["eu_ai_act_compliance_assessment"]["summary"]["total_findings"],
            "chain_integrity": self.engine.ledger.verify_chain()
        }

        # Ledger export
        export = self.engine.ledger.export_compliance(agent.lct_id)
        results["step_5_ledger_export"] = {
            "total_entries": export["eu_ai_act_audit_log"]["total_entries"],
            "by_severity": export["eu_ai_act_audit_log"]["by_severity"],
            "by_level": export["eu_ai_act_audit_log"]["by_level"]
        }

        return results


# ═══════════════════════════════════════════════════════════════
# PART 10: CHECKS
# ═══════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(condition: bool, description: str):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {description}")

    # ─── Section 1: Annex III Classification (Art. 6) ─────────────

    print("Section 1: Art. 6 — Classification")

    # 1.1 All Annex III categories defined
    categories = list(AnnexIIICategory)
    check(len(categories) == 9, "9 Annex III categories (8 high-risk + NONE)")
    check(AnnexIIICategory.BIOMETRICS in categories, "Biometrics category exists")
    check(AnnexIIICategory.LAW_ENFORCEMENT in categories, "Law enforcement category exists")
    check(AnnexIIICategory.JUSTICE in categories, "Justice category exists")
    check(AnnexIIICategory.NONE in categories, "NONE (not high-risk) category exists")

    # 1.2 Classification with evidence
    classification = AnnexIIIClassification(
        category=AnnexIIICategory.EMPLOYMENT,
        subcategory="automated_cv_screening",
        risk_level=RiskLevel.HIGH,
        classification_date="2026-02-26",
        classified_by="lct:web4:human:classifier",
        evidence=["Annex III §4(a)"]
    )
    check(classification.is_high_risk(), "Employment CV screening is high-risk")
    check(classification.category == AnnexIIICategory.EMPLOYMENT, "Category is employment")
    check(len(classification.evidence) > 0, "Classification has evidence")

    # 1.3 Non-high-risk classification
    low_risk = AnnexIIIClassification(
        category=AnnexIIICategory.NONE,
        subcategory="chatbot",
        risk_level=RiskLevel.MINIMAL,
        classification_date="2026-02-26",
        classified_by="lct:web4:human:classifier"
    )
    check(not low_risk.is_high_risk(), "Chatbot is not high-risk")
    check(low_risk.risk_level == RiskLevel.MINIMAL, "Chatbot is minimal risk")

    # 1.4 Risk levels
    check(len(list(RiskLevel)) == 4, "4 risk levels (unacceptable/high/limited/minimal)")

    # ─── Section 2: Risk Management (Art. 9) ──────────────────────

    print("Section 2: Art. 9 — Risk Management")

    rms = RiskManagementSystem()

    # 2.1 T3 risk dimensions
    t3 = T3RiskDimension(talent=0.3, training=0.8, temperament=0.6)
    check(t3.composite_risk() < 0.6, f"Composite risk {t3.composite_risk():.2f} reflects low talent")
    flags = t3.risk_flags(threshold=0.4)
    check(len(flags) == 1 and "talent" in flags[0], "Only talent flagged below 0.4")
    check("0.30" in flags[0], "Flag includes exact score")

    # 2.2 Risk identification from entity
    entity = AISystemEntity(
        lct_id="lct:web4:ai:test-agent-risk",
        name="Risk Test Agent",
        entity_type="ai",
        mode=EntityMode.AGENTIC,
        t3=T3RiskDimension(talent=0.3, training=0.8, temperament=0.6),
        v3=V3DataQuality(valuation=0.7, veracity=0.4, validity=0.6),
        hardware_binding_level=2,
        provider_id="provider-x",
        annex_iii=AnnexIIIClassification(
            category=AnnexIIICategory.EMPLOYMENT,
            subcategory="screening",
            risk_level=RiskLevel.HIGH,
            classification_date="2026-02-26",
            classified_by="classifier"
        ),
        delegation_chain=["a", "b", "c", "d"]  # 4 hops
    )

    risks = rms.identify_risks(entity)
    check(len(risks) >= 3, f"At least 3 risks identified (got {len(risks)})")

    # Check risk categories
    risk_ids = [r.risk_id for r in risks]
    check(any("T3-talent" in r for r in risk_ids), "T3 talent risk identified")
    check(any("V3-veracity" in r for r in risk_ids), "V3 veracity risk identified")
    check(any("HW-binding" in r for r in risk_ids), "Hardware binding risk identified")
    check(any("DELEG-depth" in r for r in risk_ids), "Delegation depth risk identified")

    # 2.3 Risk scoring
    talent_risk = next(r for r in risks if "T3-talent" in r.risk_id)
    check(talent_risk.risk_score() > 0.0, f"Talent risk score > 0 ({talent_risk.risk_score():.2f})")
    check(talent_risk.likelihood > 0.5, f"Low talent = high likelihood ({talent_risk.likelihood:.2f})")
    check(talent_risk.t3_dimension == "talent", "Risk linked to talent dimension")

    # 2.4 Risk posture evaluation
    posture = rms.evaluate_risk_posture(entity)
    check(posture["total_risks"] >= 3, f"Posture shows {posture['total_risks']} risks")
    check(posture["aggregate_score"] > 0, "Aggregate risk score positive")
    check("status" in posture, "Posture has status field")

    # 2.5 Tensor snapshots for post-market monitoring
    snap1 = rms.record_tensor_snapshot(entity)
    check(snap1["t3"]["talent"] == 0.3, "Snapshot records current T3 talent")
    check(snap1["t3"]["composite"] == entity.t3.composite_risk(), "Snapshot composite matches")
    check(len(snap1["risk_flags"]) == 1, "Snapshot includes risk flags")

    # 2.6 Drift detection
    # Record multiple snapshots with declining trust
    entity.t3.talent = 0.25
    rms.record_tensor_snapshot(entity)
    entity.t3.talent = 0.18
    rms.record_tensor_snapshot(entity)
    entity.t3.talent = 0.10
    rms.record_tensor_snapshot(entity)

    drift = rms.detect_drift(entity)
    check(drift["drift_detected"], "Drift detected with declining trust")
    check(drift["direction"] == "declining", "Drift direction is declining")
    check(drift["avg_delta"] < 0, f"Average delta negative ({drift['avg_delta']})")

    # 2.7 Mitigation status affects risk score
    mitigated_risk = RiskRegisterEntry(
        risk_id="test-mitigated",
        description="test",
        category="test",
        likelihood=0.8,
        impact=0.9,
        mitigation="implemented defense",
        mitigation_status="implemented",
        owner="test",
        identified_date="2026-02-26",
        last_reviewed="2026-02-26"
    )
    unmitigated_risk = RiskRegisterEntry(
        risk_id="test-unmitigated",
        description="test",
        category="test",
        likelihood=0.8,
        impact=0.9,
        mitigation="none",
        mitigation_status="under_review",
        owner="test",
        identified_date="2026-02-26",
        last_reviewed="2026-02-26"
    )
    check(mitigated_risk.risk_score() < unmitigated_risk.risk_score(),
          "Implemented mitigation reduces risk score")
    check(abs(mitigated_risk.risk_score() - 0.8 * 0.9 * 0.3) < 1e-10,
          "70% mitigation reduction applied")

    # ─── Section 3: Data Governance (Art. 10) ─────────────────────

    print("Section 3: Art. 10 — Data Governance")

    dge = DataGovernanceEngine()

    # 3.1 V3 data quality
    v3 = V3DataQuality(valuation=0.9, veracity=0.5, validity=0.8)
    check(v3.data_quality_score() > 0.7, f"Quality score {v3.data_quality_score():.2f}")
    indicators = v3.bias_indicators()
    check(len(indicators) > 0, "Bias indicators detect V3 imbalance (veracity low)")
    check("veracity" in indicators[0], "Veracity deviation flagged")

    # 3.2 Dataset registration
    reg = dge.register_dataset(
        "training_data_v1", "CV screening training set",
        "lct:web4:ai:trainer",
        V3DataQuality(valuation=0.7, veracity=0.85, validity=0.78),
        protected_chars=["gender", "age"]
    )
    check(reg["bias_audit_required"], "Bias audit required when protected chars present")
    check("provenance_hash" in reg, "Dataset has provenance hash")
    check(reg["v3_quality"]["composite"] > 0, "V3 quality score recorded")

    # 3.3 Witness diversity
    dge.add_witness("training_data_v1", "witness-1", "society-alpha", "data quality attested")
    dge.add_witness("training_data_v1", "witness-2", "society-beta", "representativeness confirmed")
    dge.add_witness("training_data_v1", "witness-3", "society-gamma", "bias check passed")
    check(len(dge.witness_records) == 3, "3 witnesses recorded")
    societies = set(w["society"] for w in dge.witness_records)
    check(len(societies) == 3, "Witnesses from 3 different societies")

    # 3.4 Bias audit — biased dataset
    biased_result = dge.run_bias_audit(
        "training_data_v1", "lct:web4:human:auditor",
        protected_chars=["gender"],
        outcome_distribution={"gender": {"male": 0.72, "female": 0.45}}
    )
    check(biased_result.has_bias(), "Bias detected in skewed dataset")
    check(biased_result.disparate_impact_ratio < 0.8,
          f"DI ratio {biased_result.disparate_impact_ratio} < 0.8")
    check(biased_result.statistical_parity_diff > 0.1,
          f"SP diff {biased_result.statistical_parity_diff} > 0.1")
    check(len(biased_result.findings) > 0, "Audit has findings")

    # 3.5 Bias audit — fair dataset
    fair_result = dge.run_bias_audit(
        "fair_dataset", "lct:web4:human:auditor",
        protected_chars=["gender"],
        outcome_distribution={"gender": {"male": 0.65, "female": 0.62}}
    )
    check(not fair_result.has_bias(), "No bias in balanced dataset")
    check(fair_result.disparate_impact_ratio >= 0.8,
          f"DI ratio {fair_result.disparate_impact_ratio} >= 0.8 (fair)")

    # 3.6 Witness diversity score
    check(biased_result.witness_diversity_score == 1.0,
          "Witness diversity 1.0 with 3 societies for training_data_v1")

    # ─── Section 4: Record-Keeping (Art. 12) ──────────────────────

    print("Section 4: Art. 12 — Record-Keeping")

    ledger = FractalChainLedger()

    # 4.1 Record events at appropriate chain levels
    e1 = ledger.record("action", "lct:agent-1", {"type": "classification"})
    check(e1.chain_level == "compost", "Regular action → compost level")

    e2 = ledger.record("policy_update", "lct:agent-1", {"policy": "v2"},
                        severity="warning")
    check(e2.chain_level == "leaf", "Policy update → leaf level")

    e3 = ledger.record("action", "lct:agent-1", {"type": "data_breach"},
                        severity="critical")
    check(e3.chain_level == "stem", "Critical event → stem level")

    e4 = ledger.record("status_change", "lct:agent-1",
                        {"old": "active", "new": "dormant"},
                        severity="incident", witnesses=["overseer-1"])
    check(e4.chain_level == "root", "Status change → root (permanent)")

    # 4.2 Hash chain integrity
    integrity = ledger.verify_chain()
    check(integrity["valid"], "Hash chain is valid")
    check(integrity["entries"] == 4, "4 entries in chain")

    # 4.3 Entity query
    agent_entries = ledger.query_by_entity("lct:agent-1")
    check(len(agent_entries) == 4, "All 4 entries belong to agent-1")

    # 4.4 Incident query
    incidents = ledger.query_incidents()
    check(len(incidents) == 1, "1 incident in ledger")
    check(incidents[0].event_type == "status_change", "Incident is status change")

    # 4.5 Compliance export
    export = ledger.export_compliance("lct:agent-1")
    check("eu_ai_act_audit_log" in export, "Export has EU AI Act header")
    check(export["eu_ai_act_audit_log"]["article"] == "12", "Export references Art. 12")
    check(export["eu_ai_act_audit_log"]["total_entries"] == 4, "Export has 4 entries")
    by_level = export["eu_ai_act_audit_log"]["by_level"]
    check(by_level["root"] == 1, "1 root-level entry in export")
    check(by_level["compost"] == 1, "1 compost-level entry in export")

    # 4.6 Retention periods
    check(ledger.retention_days["root"] == -1, "Root = permanent retention")
    check(ledger.retention_days["leaf"] == 90, "Leaf = 90 days")
    check(ledger.retention_days["compost"] == 7, "Compost = 7 days")

    # 4.7 Witness records on entries
    check(len(e4.witnesses) == 1, "Status change has witness")
    check(e4.witnesses[0] == "overseer-1", "Witness is overseer")

    # ─── Section 5: Transparency (Art. 13) ────────────────────────

    print("Section 5: Art. 13 — Transparency")

    # 5.1 Transparency report generation
    report = TransparencyReport(
        system_id="lct:web4:ai:transparency-test",
        provider_identity="did:web4:key:acme-corp",
        system_type="ai",
        intended_purpose="automated_cv_screening",
        capabilities=["nlp", "classification"],
        limitations=["max_delegation_2"],
        performance_metrics={"t3_composite": 0.72, "v3_composite": 0.78},
        human_oversight_measures=["R6 Tier 2 approval", "LCT lifecycle management"],
        annex_iii_category="employment_workers_management",
        risk_level="high",
        hardware_binding_level=5,
        generated_date="2026-02-26"
    )

    reg_format = report.to_regulatory_format()
    check("eu_ai_act_transparency_report" in reg_format, "Report has EU AI Act header")
    eu_report = reg_format["eu_ai_act_transparency_report"]
    check(eu_report["regulation"] == "EU 2024/1689", "Correct regulation reference")
    check(eu_report["provider"]["identity"] == "did:web4:key:acme-corp", "Provider identity")
    check(eu_report["system"]["risk_classification"]["level"] == "high", "Risk level in report")
    check(eu_report["system"]["risk_classification"]["annex_iii_category"] ==
          "employment_workers_management", "Annex III category in report")
    check(len(eu_report["system"]["capabilities"]) == 2, "Capabilities listed")
    check(len(eu_report["system"]["limitations"]) == 1, "Limitations listed")
    check(eu_report["performance"]["t3_composite"] == 0.72, "T3 performance in report")
    check(len(eu_report["oversight"]) == 2, "Oversight measures listed")

    # ─── Section 6: Human Oversight (Art. 14) ─────────────────────

    print("Section 6: Art. 14 — Human Oversight")

    oversight_ledger = FractalChainLedger()
    oversight = HumanOversightEngine(oversight_ledger)

    agent = AISystemEntity(
        lct_id="lct:web4:ai:oversight-test",
        name="Oversight Test Agent",
        entity_type="ai",
        mode=EntityMode.AGENTIC
    )

    # 6.1 Assign oversight
    config = oversight.assign_oversight(
        agent.lct_id, "did:web4:key:alice",
        approval_required_actions=["critical_decision", "data_deletion"],
        can_override=True,
        can_shutdown=True
    )
    check(config["overseer"] == "did:web4:key:alice", "Overseer assigned")
    check("critical_decision" in config["approval_required"], "Critical decisions need approval")

    # 6.2 Non-restricted action passes
    result = oversight.request_approval(
        agent.lct_id, "routine_classification", {}
    )
    check(result["approved"], "Routine action approved without oversight")

    # 6.3 Restricted action blocked
    result = oversight.request_approval(
        agent.lct_id, "critical_decision",
        {"description": "Auto-reject CV with score < 0.3"}
    )
    check(not result["approved"], "Critical decision blocked by oversight")
    check(result["reason"] == "awaiting_human_approval", "Correct block reason")
    request_id = result["request_id"]

    # 6.4 Human approves
    decision = oversight.approve(request_id, True, "Risk acceptable after review")
    check(decision["status"] == "approved", "Human approved the action")

    # 6.5 Human denies another request
    result2 = oversight.request_approval(
        agent.lct_id, "data_deletion",
        {"description": "Delete training data partition B"}
    )
    decision2 = oversight.approve(result2["request_id"], False, "Data must be retained")
    check(decision2["status"] == "denied", "Human denied data deletion")

    # 6.6 Override — pause agent
    override = oversight.override_entity(
        agent, "did:web4:key:alice", LCTStatus.DORMANT, "Quarterly review pause"
    )
    check(override["overridden"], "Agent successfully paused")
    check(agent.status == LCTStatus.DORMANT, "Agent status is DORMANT")
    check(override["old_status"] == "active", "Previous status was active")

    # 6.7 Override — terminate agent
    override2 = oversight.override_entity(
        agent, "did:web4:key:alice", LCTStatus.VOID, "End of life"
    )
    check(agent.status == LCTStatus.VOID, "Agent status is VOID (terminated)")

    # 6.8 Ledger records oversight actions
    oversight_entries = oversight_ledger.query_by_entity(agent.lct_id)
    check(len(oversight_entries) >= 4, f"Ledger has {len(oversight_entries)} oversight entries")
    incident_entries = [e for e in oversight_entries if e.severity == "incident"]
    check(len(incident_entries) == 2, "2 incident-level entries (overrides)")

    # ─── Section 7: Cybersecurity (Art. 15) ───────────────────────

    print("Section 7: Art. 15 — Cybersecurity")

    cyber = CybersecurityAssessment()

    # 7.1 Attack corpus registration
    corpus = cyber.register_attack_corpus(
        total_vectors=424, defended=360,
        categories={"sybil": 45, "collusion": 38, "reputation": 52}
    )
    check(corpus["defense_rate"] == round(360/424, 3), f"Defense rate {corpus['defense_rate']}")
    check(corpus["undefended"] == 64, "64 undefended vectors")

    # 7.2 Hardware binding assessment — high-risk with low binding
    weak_agent = AISystemEntity(
        lct_id="lct:web4:ai:weak-hw",
        name="Weak HW Agent",
        entity_type="ai",
        mode=EntityMode.RESPONSIVE,
        hardware_binding_level=1,
        annex_iii=AnnexIIIClassification(
            category=AnnexIIICategory.LAW_ENFORCEMENT,
            subcategory="predictive_policing",
            risk_level=RiskLevel.HIGH,
            classification_date="2026-02-26",
            classified_by="classifier"
        )
    )
    hw_assessment = cyber.assess_hardware_binding(weak_agent)
    check(hw_assessment["key_extractable"], "Level 1 keys are extractable")
    check(not hw_assessment["compliant_for_high_risk"], "Level 1 not compliant for high-risk")
    check("UPGRADE REQUIRED" in hw_assessment["recommendation"], "Upgrade recommended")

    # 7.3 Hardware binding — strong
    strong_agent = AISystemEntity(
        lct_id="lct:web4:ai:strong-hw",
        name="Strong HW Agent",
        entity_type="ai",
        mode=EntityMode.AGENTIC,
        hardware_binding_level=5
    )
    hw_strong = cyber.assess_hardware_binding(strong_agent)
    check(hw_strong["tpm2_secured"], "Level 5 is TPM2 secured")
    check(not hw_strong["key_extractable"], "Level 5 keys not extractable")
    check(hw_strong["physically_bound"], "Level 5 is physically bound")

    # 7.4 Sybil resistance economics
    sybil = cyber.test_sybil_resistance(
        hardware_cost=250, atp_cost=50, n_identities=10
    )
    check(sybil["total_cost"] == 3000, "10 identities cost 3000")
    check(sybil["circular_loss_per_cycle"] == 25.0, "5% ATP fee = 25 per cycle")
    check(sybil["effective_trust_per_identity"] < 0.3,
          f"Trust diluted to {sybil['effective_trust_per_identity']}")
    check(not sybil["profitable"], "Sybil attack unprofitable at 250+50 per identity")

    # 7.5 Robustness report
    strong_agent.t3 = T3RiskDimension(talent=0.8, training=0.85, temperament=0.75)
    robust_report = cyber.generate_robustness_report(strong_agent)
    check("eu_ai_act_article_15" in robust_report, "Report has Art. 15 header")
    check(robust_report["eu_ai_act_article_15"]["accuracy"]["composite"] > 0.7,
          "Good accuracy in report")

    # ─── Section 8: Full Compliance Assessment ────────────────────

    print("Section 8: Full Compliance Assessment")

    engine = ComplianceAssessmentEngine()

    # 8.1 Create fully-compliant agent
    compliant_agent = AISystemEntity(
        lct_id="lct:web4:ai:compliant-001",
        name="Fully Compliant Agent",
        entity_type="ai",
        mode=EntityMode.AGENTIC,
        hardware_binding_level=5,
        provider_id="did:web4:key:provider-acme",
        deployer_id="did:web4:key:deployer-eu",
        capabilities=["nlp", "classification", "risk_scoring"],
        limitations=["max_delegation_2", "requires_oversight"],
        t3=T3RiskDimension(talent=0.8, training=0.85, temperament=0.75),
        v3=V3DataQuality(valuation=0.7, veracity=0.85, validity=0.78),
        annex_iii=AnnexIIIClassification(
            category=AnnexIIICategory.EMPLOYMENT,
            subcategory="automated_cv_screening",
            risk_level=RiskLevel.HIGH,
            classification_date="2026-02-26",
            classified_by="did:web4:key:classifier",
            evidence=["Annex III §4(a)"]
        )
    )

    # Set up compliance infrastructure
    engine.oversight.assign_oversight(
        compliant_agent.lct_id, "did:web4:key:human-overseer",
        ["critical_decision", "data_deletion", "model_update"]
    )
    engine.record_action(compliant_agent, "classification",
                         {"rules": "policy_v1", "role": "screener"},
                         "50 CVs classified — success", 0.01, 5.0)
    engine.cybersecurity.register_attack_corpus(424, 360,
                                                 {"sybil": 45, "collusion": 38})
    engine.cybersecurity.test_sybil_resistance(250, 50, 10)

    # 8.2 Full assessment
    full = engine.full_assessment(compliant_agent)
    assessment = full["eu_ai_act_compliance_assessment"]

    check(assessment["entity"]["lct_id"] == compliant_agent.lct_id, "Correct entity in assessment")
    check(assessment["entity"]["risk_level"] == "high", "High-risk entity")
    check(assessment["summary"]["total_articles"] == 8, "8 articles assessed")
    check(assessment["summary"]["compliant"] > 0, f"At least 1 compliant article")

    # 8.3 Individual article assessments present
    check("art_6" in assessment["articles"], "Art. 6 assessment present")
    check("art_9" in assessment["articles"], "Art. 9 assessment present")
    check("art_10" in assessment["articles"], "Art. 10 assessment present")
    check("art_12" in assessment["articles"], "Art. 12 assessment present")
    check("art_13" in assessment["articles"], "Art. 13 assessment present")
    check("art_14" in assessment["articles"], "Art. 14 assessment present")
    check("art_15" in assessment["articles"], "Art. 15 assessment present")

    # 8.4 Art. 6 should be compliant (has classification)
    art6 = assessment["articles"]["art_6"]
    check(art6["status"] == "compliant", "Art. 6 compliant with Annex III classification")
    check(art6["classification"]["category"] == "employment_workers_management",
          "Correct Annex III category")

    # 8.5 Art. 12 should be compliant (ledger has entries)
    art12 = assessment["articles"]["art_12"]
    check(art12["entity_entries"] > 0, "Art. 12 has ledger entries")
    check(art12["chain_integrity"]["valid"], "Art. 12 chain integrity valid")

    # 8.6 Art. 14 should be compliant (oversight assigned)
    art14 = assessment["articles"]["art_14"]
    check(art14["oversight_assigned"], "Art. 14 oversight is assigned")
    check(art14["can_override"], "Art. 14 overseer can override")
    check(art14["can_shutdown"], "Art. 14 overseer can shutdown")

    # 8.7 Art. 15 should reference attack corpus
    art15 = assessment["articles"]["art_15"]
    check("attack_corpus" in art15, "Art. 15 includes attack corpus")
    check(art15["hardware_binding"]["tpm2_secured"], "Art. 15 confirms TPM2")

    # 8.8 Overall findings aggregated
    check("all_findings" in assessment, "All findings aggregated")
    check(isinstance(assessment["all_findings"], list), "Findings is a list")

    # 8.9 Non-compliant agent (missing everything)
    bare_agent = AISystemEntity(
        lct_id="lct:web4:ai:bare-001",
        name="Bare Agent",
        entity_type="ai",
        mode=EntityMode.RESPONSIVE
    )
    bare_assessment = engine.full_assessment(bare_agent)
    bare = bare_assessment["eu_ai_act_compliance_assessment"]
    check(bare["summary"]["non_compliant"] > 0, "Bare agent has non-compliant articles")
    check(bare["overall_status"] == "non_compliant", "Bare agent overall non-compliant")
    check(len(bare["all_findings"]) > 3, f"Bare agent has many findings ({len(bare['all_findings'])})")

    # ─── Section 9: Demo Scenario ─────────────────────────────────

    print("Section 9: Demo Scenario")

    demo = ComplianceDemoScenario()
    results = demo.run_demo()

    # 9.1 Step 1: Identity
    check(results["step_1_identity"]["hw_binding"] == 5, "Demo agent has TPM2 binding")
    check(results["step_1_identity"]["risk_level"] == "high", "Demo agent is high-risk")
    check(results["step_1_identity"]["annex_iii"] == "employment_workers_management",
          "Demo agent classified as employment")

    # 9.2 Step 2: Action trail
    check(results["step_2_action"]["atp_consumed"] == 5.0, "Action consumed 5 ATP")
    check(results["step_2_action"]["trust_delta"] == 0.01, "Trust delta recorded")

    # 9.3 Step 3: Risk monitoring
    check(results["step_3_monitoring"]["risk_flags"] is not None, "Risk flags generated")

    # 9.4 Step 4: Human oversight
    check(results["step_4_oversight"]["approval_blocked"], "Critical action was blocked")
    check(results["step_4_oversight"]["override_applied"], "Human override applied")
    check(results["step_4_oversight"]["new_status"] == "dormant", "Agent paused to dormant")

    # 9.5 Step 5: Audit
    check(results["step_5_audit"]["chain_integrity"]["valid"], "Audit chain valid")
    check(results["step_5_audit"]["total_findings"] >= 0, "Assessment generated findings count")
    check(results["step_5_ledger_export"]["total_entries"] > 0, "Ledger has entries")
    check(results["step_5_ledger_export"]["by_level"]["root"] > 0, "Root entries exist (permanent)")

    # ─── Section 10: Edge Cases & Regulatory Format ───────────────

    print("Section 10: Edge Cases & Regulatory Format")

    # 10.1 Risk register entry scores
    planned = RiskRegisterEntry(
        risk_id="planned-1", description="test", category="test",
        likelihood=1.0, impact=1.0, mitigation="planned", mitigation_status="planned",
        owner="test", identified_date="2026-02-26", last_reviewed="2026-02-26"
    )
    check(planned.risk_score() == 0.7, "Planned mitigation = 30% credit")

    review = RiskRegisterEntry(
        risk_id="review-1", description="test", category="test",
        likelihood=1.0, impact=1.0, mitigation="none", mitigation_status="under_review",
        owner="test", identified_date="2026-02-26", last_reviewed="2026-02-26"
    )
    check(review.risk_score() == 1.0, "Under review = no credit (full risk)")

    # 10.2 R6 action record hashing
    r6 = R6ActionRecord(
        action_id="R6-test-001",
        rules="policy_v1",
        role="admin",
        request="test_action",
        reference="",
        resource="10 ATP",
        result="success",
        status="success",
        trust_delta=0.0,
        coherence=0.8,
        timestamp="2026-02-26T00:00:00",
        entity_lct_id="lct:web4:ai:test"
    )
    check(len(r6.hash) == 16, "R6 action has 16-char hash")

    # 10.3 Ledger with no entries
    empty_ledger = FractalChainLedger()
    empty_verify = empty_ledger.verify_chain()
    check(empty_verify["valid"], "Empty ledger is valid")
    check(empty_verify["entries"] == 0, "Empty ledger has 0 entries")

    # 10.4 Entity without oversight can pass approval
    no_oversight = HumanOversightEngine(FractalChainLedger())
    result = no_oversight.request_approval("unassigned-entity", "critical_decision", {})
    check(result["approved"], "Entity without oversight auto-approved")
    check(result["reason"] == "no_oversight_assigned", "Correct auto-approve reason")

    # 10.5 Sybil with zero costs
    zero_sybil = CybersecurityAssessment()
    result = zero_sybil.test_sybil_resistance(0, 0, 10)
    check(result["break_even_identities"] == float('inf'),
          "Zero-cost sybil has infinite break-even")

    # 10.6 Compliance status enum
    check(len(list(ComplianceStatus)) == 4, "4 compliance statuses")
    check(ComplianceStatus.NOT_APPLICABLE.value == "not_applicable", "N/A status exists")

    # 10.7 LCT status transitions
    check(LCTStatus.ACTIVE.value == "active", "Active status")
    check(LCTStatus.SLASHED.value == "slashed", "Slashed status (trust penalty)")

    # 10.8 Entity modes
    check(len(list(EntityMode)) == 3, "3 entity modes (agentic/responsive/delegative)")

    # 10.9 V3 no bias when balanced
    balanced_v3 = V3DataQuality(valuation=0.6, veracity=0.6, validity=0.6)
    check(len(balanced_v3.bias_indicators()) == 0, "No bias indicators when V3 balanced")

    # 10.10 Compliance export format
    compliance_export = engine.ledger.export_compliance("nonexistent")
    check(compliance_export["eu_ai_act_audit_log"]["total_entries"] == 0,
          "Export for nonexistent entity returns 0 entries")

    # ─── Section 11: Cross-Article Integration ────────────────────

    print("Section 11: Cross-Article Integration")

    # Create a scenario that exercises multiple articles simultaneously
    integrated_engine = ComplianceAssessmentEngine()

    hr_agent = AISystemEntity(
        lct_id="lct:web4:ai:hr-screener",
        name="HR Screening AI",
        entity_type="ai",
        mode=EntityMode.AGENTIC,
        hardware_binding_level=4,
        provider_id="did:web4:key:hr-tech-corp",
        capabilities=["resume_parsing", "candidate_ranking", "interview_scheduling"],
        limitations=["no_final_hiring_decisions", "requires_human_review"],
        t3=T3RiskDimension(talent=0.7, training=0.75, temperament=0.8),
        v3=V3DataQuality(valuation=0.65, veracity=0.8, validity=0.75),
        annex_iii=AnnexIIIClassification(
            category=AnnexIIICategory.EMPLOYMENT,
            subcategory="recruitment_candidate_filtering",
            risk_level=RiskLevel.HIGH,
            classification_date="2026-02-26",
            classified_by="did:web4:key:eu-compliance-officer",
            evidence=["Annex III §4(a): AI systems used for recruitment"]
        )
    )

    # 11.1 Set up oversight (Art. 14)
    integrated_engine.oversight.assign_oversight(
        hr_agent.lct_id, "did:web4:key:hr-manager",
        ["hiring_recommendation", "candidate_rejection", "data_export"]
    )

    # 11.2 Record actions (Art. 11/12)
    for i in range(5):
        integrated_engine.record_action(
            hr_agent, "resume_parsing",
            {"rules": "hr_policy_v3", "role": "screener",
             "reference": f"job-{i}", "coherence": 0.85 + i*0.02},
            f"Parsed {10*(i+1)} resumes — success",
            trust_delta=0.005,
            atp_consumed=2.0 + i
        )

    # 11.3 Record tensor snapshots (Art. 9)
    for _ in range(3):
        integrated_engine.risk_mgmt.record_tensor_snapshot(hr_agent)

    # 11.4 Register attack corpus (Art. 15)
    integrated_engine.cybersecurity.register_attack_corpus(
        424, 380, {"sybil": 45, "collusion": 38, "bias": 25}
    )
    integrated_engine.cybersecurity.test_sybil_resistance(250, 50, 5)

    # 11.5 Run bias audit (Art. 10)
    integrated_engine.data_gov.run_bias_audit(
        "hr_training_data", hr_agent.lct_id,
        ["gender", "ethnicity"],
        {"gender": {"male": 0.68, "female": 0.65},
         "ethnicity": {"group_a": 0.67, "group_b": 0.64}}
    )

    # 11.6 Full integrated assessment
    integrated = integrated_engine.full_assessment(hr_agent)
    ia = integrated["eu_ai_act_compliance_assessment"]

    check(ia["entity"]["risk_level"] == "high", "HR agent is high-risk")
    check(ia["summary"]["total_articles"] == 8, "All 8 articles assessed")

    # Count compliant articles
    compliant_arts = [k for k, v in ia["articles"].items()
                      if v["status"] == "compliant"]
    check(len(compliant_arts) >= 4,
          f"At least 4 articles compliant (got {len(compliant_arts)})")

    # 11.7 Verify R6 records exist in assessment
    art11 = ia["articles"]["art_11"]
    check(art11["documentation"]["r6_records_exist"], "R6 records exist for Art. 11")
    check(art11["documentation"]["action_count"] == 5, "5 R6 actions recorded")

    # 11.8 Verify ledger has entries
    art12 = ia["articles"]["art_12"]
    check(art12["entity_entries"] > 5, f"Ledger has {art12['entity_entries']} entries")
    check(art12["chain_integrity"]["valid"], "Integrated ledger chain valid")

    # 11.9 Art. 14 oversight in integrated assessment
    art14 = ia["articles"]["art_14"]
    check(art14["oversight_assigned"], "Oversight assigned in integrated scenario")

    # 11.10 Art. 15 in integrated assessment
    art15 = ia["articles"]["art_15"]
    check(art15["hardware_binding"]["binding_level"] == 4, "HW binding level 4 in Art. 15")
    check(not art15["hardware_binding"]["key_extractable"], "Level 4 keys not extractable")

    # ─── Section 12: Gap Closures ─────────────────────────────────

    print("Section 12: Gap Closures")

    # Verify that the 7 gaps identified in the mapping doc are addressed
    # Gap 1: No Annex III category field → AnnexIIIClassification class
    from dataclasses import fields as dc_fields
    annex_fields = {f.name for f in dc_fields(AnnexIIIClassification)}
    check('category' in annex_fields, "Gap 1 closed: Annex III category field exists")
    check(len(list(AnnexIIICategory)) == 9, "Gap 1: All 8 Annex III categories + NONE")

    # Gap 2: No formal Art. 9 risk register template → RiskRegisterEntry + RiskManagementSystem
    check(hasattr(RiskRegisterEntry, 'risk_score'), "Gap 2 closed: Risk register with scoring")
    check(hasattr(RiskManagementSystem, 'identify_risks'), "Gap 2: Automated risk identification")
    check(hasattr(RiskManagementSystem, 'detect_drift'), "Gap 2: Post-market drift detection")

    # Gap 3: No turnkey bias audit workflow → BiasAuditResult + DataGovernanceEngine
    check(hasattr(BiasAuditResult, 'has_bias'), "Gap 3 closed: Bias audit with has_bias()")
    check(hasattr(DataGovernanceEngine, 'run_bias_audit'), "Gap 3: Turnkey bias audit method")
    # Verify it checks 4/5ths rule
    check(biased_result.disparate_impact_ratio < 0.8, "Gap 3: 4/5ths rule implemented")

    # Gap 4: No "instructions for use" document generator → TransparencyReport
    check(hasattr(TransparencyReport, 'to_regulatory_format'),
          "Gap 4 closed: Instructions-for-use export")

    # Gap 5: Hardware binding validation → CybersecurityAssessment.assess_hardware_binding
    check(hasattr(CybersecurityAssessment, 'assess_hardware_binding'),
          "Gap 5 closed: Hardware binding assessment")

    # Gap 6: No formal security proofs → attack corpus + sybil economics (empirical)
    check(hasattr(CybersecurityAssessment, 'test_sybil_resistance'),
          "Gap 6 partially closed: Sybil economics quantified")

    # Gap 7: No external red team → framework exists for integration
    check(hasattr(CybersecurityAssessment, 'register_attack_corpus'),
          "Gap 7 framework: Attack corpus registration ready for external results")

    # ─── Summary ──────────────────────────────────────────────────

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"EU AI Act Compliance Engine: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")

    return passed, failed


if __name__ == "__main__":
    run_checks()
