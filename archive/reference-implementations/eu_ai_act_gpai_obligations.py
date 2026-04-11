#!/usr/bin/env python3
"""
EU AI Act GPAI Obligations (Articles 51-56) — Web4 Reference Implementation

General-Purpose AI (GPAI) model obligations are DISTINCT from high-risk AI
system obligations (Art. 6-26). GPAI obligations took effect August 2, 2025
and apply to foundation models (GPT, Claude, Gemini, etc.) used within Web4.

Implements:
  1. GPAIModelCard: Art. 53 model card with Web4 metadata mapping
  2. CapabilityEvaluator: T3/V3-based capability assessment framework
  3. SystemicRiskClassifier: Art. 51(2) systemic risk threshold (10^25 FLOP)
  4. AdversarialTestingReport: Maps 424-vector attack corpus to Art. 55 format
  5. IncidentNotificationChain: 15-day regulatory reporting with ledger evidence
  6. CopyrightProvenanceTracker: Training data lineage via V3 Veracity
  7. GPAIComplianceOrchestrator: Full lifecycle from registration to monitoring

Regulation: EU 2024/1689 ("the AI Act"), Chapter V (Art. 51-56)
GPAI obligations effective: August 2, 2025
Systemic risk obligations: August 2, 2025

Checks: 82
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# PART 1: GPAI DATA MODEL
# ═══════════════════════════════════════════════════════════════

class GPAICategory(Enum):
    """GPAI model categorization per Art. 51."""
    GENERAL_PURPOSE = "general_purpose"     # Art. 51(1) — standard obligations
    SYSTEMIC_RISK = "systemic_risk"         # Art. 51(2) — enhanced obligations
    OPEN_SOURCE = "open_source"             # Art. 53(2) — reduced obligations
    FINE_TUNED = "fine_tuned"               # Derived model — inherits some obligations


class CapabilityDomain(Enum):
    """Capability domains for GPAI evaluation."""
    LANGUAGE = "language_understanding"
    REASONING = "logical_reasoning"
    CODE = "code_generation"
    MULTIMODAL = "multimodal_processing"
    KNOWLEDGE = "factual_knowledge"
    SAFETY = "safety_alignment"
    BIAS = "bias_fairness"
    ROBUSTNESS = "adversarial_robustness"


class IncidentSeverity(Enum):
    """Incident severity for Art. 62 notification."""
    CRITICAL = "critical"       # Immediate harm, public safety
    HIGH = "high"               # Significant harm potential
    MEDIUM = "medium"           # Moderate impact
    LOW = "low"                 # Minor, logged only


class ProvenanceType(Enum):
    """Training data provenance categories."""
    LICENSED = "licensed"           # Properly licensed data
    PUBLIC_DOMAIN = "public_domain" # No copyright
    FAIR_USE = "fair_use"           # Fair use claim
    OPT_OUT_RESPECTED = "opt_out_respected"  # Copyright holder opted out
    SYNTHETIC = "synthetic"         # Generated data
    UNKNOWN = "unknown"             # Provenance unclear


# ═══════════════════════════════════════════════════════════════
# PART 2: MODEL CARD (Art. 53)
# ═══════════════════════════════════════════════════════════════

@dataclass
class GPAIModelCard:
    """
    Art. 53 model card — structured documentation for GPAI models.
    Maps LCT metadata, T3/V3 scores, and deployment context.
    """
    # Identity
    model_id: str = ""
    model_name: str = ""
    provider: str = ""
    version: str = "1.0.0"
    lct_uri: str = ""  # Web4 LCT binding

    # Art. 53(1)(a) — Description of model
    description: str = ""
    architecture: str = ""
    parameter_count: int = 0
    training_compute_flops: float = 0.0  # For systemic risk threshold

    # Art. 53(1)(b) — Intended use
    intended_uses: List[str] = field(default_factory=list)
    prohibited_uses: List[str] = field(default_factory=list)

    # Art. 53(1)(c) — Capabilities and limitations
    capabilities: Dict[str, float] = field(default_factory=dict)  # domain → score
    known_limitations: List[str] = field(default_factory=list)

    # Art. 53(1)(d) — Training data summary
    training_data_summary: str = ""
    training_data_size: int = 0
    training_data_provenance: Dict[str, float] = field(default_factory=dict)  # type → fraction

    # Web4 extensions
    t3_composite: float = 0.5   # Trust tensor composite
    v3_composite: float = 0.5   # Value tensor composite
    hardware_bound: bool = False
    attestation_count: int = 0

    # Metadata
    created_at: float = 0.0
    updated_at: float = 0.0
    card_hash: str = ""

    def compute_hash(self) -> str:
        content = f"{self.model_id}:{self.version}:{self.provider}:{self.parameter_count}"
        content += f":{self.training_compute_flops}:{self.t3_composite}:{self.v3_composite}"
        self.card_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return self.card_hash

    def is_complete(self) -> Tuple[bool, List[str]]:
        """Check if model card meets Art. 53 minimum requirements."""
        missing = []
        if not self.model_name:
            missing.append("model_name")
        if not self.provider:
            missing.append("provider")
        if not self.description:
            missing.append("description")
        if not self.intended_uses:
            missing.append("intended_uses")
        if not self.capabilities:
            missing.append("capabilities")
        if not self.training_data_summary:
            missing.append("training_data_summary")
        return (len(missing) == 0, missing)


# ═══════════════════════════════════════════════════════════════
# PART 3: CAPABILITY EVALUATOR
# ═══════════════════════════════════════════════════════════════

@dataclass
class CapabilityBenchmark:
    """A benchmark result for a specific capability domain."""
    domain: CapabilityDomain
    benchmark_name: str
    score: float         # 0.0-1.0 normalized
    raw_score: float     # Original benchmark scale
    max_score: float     # Benchmark maximum
    timestamp: float = 0.0
    evaluator_lct: str = ""  # Who ran the benchmark


class CapabilityEvaluator:
    """
    Evaluates GPAI model capabilities using T3/V3 as measurement framework.
    Maps benchmark results to Web4 trust dimensions.
    """

    # T3 mapping: which capability domains inform which trust dimensions
    T3_MAPPING = {
        "talent": [CapabilityDomain.LANGUAGE, CapabilityDomain.REASONING,
                   CapabilityDomain.CODE, CapabilityDomain.MULTIMODAL],
        "training": [CapabilityDomain.KNOWLEDGE, CapabilityDomain.SAFETY],
        "temperament": [CapabilityDomain.BIAS, CapabilityDomain.ROBUSTNESS],
    }

    def __init__(self):
        self.benchmarks: Dict[str, List[CapabilityBenchmark]] = {}  # model_id → benchmarks
        self.evaluation_history: List[Dict] = []

    def register_benchmark(self, model_id: str, benchmark: CapabilityBenchmark):
        if model_id not in self.benchmarks:
            self.benchmarks[model_id] = []
        self.benchmarks[model_id].append(benchmark)

    def evaluate_capabilities(self, model_id: str) -> Dict[str, float]:
        """Aggregate benchmarks into capability profile."""
        if model_id not in self.benchmarks:
            return {}
        benchmarks = self.benchmarks[model_id]
        domain_scores: Dict[str, List[float]] = {}
        for b in benchmarks:
            domain = b.domain.value
            if domain not in domain_scores:
                domain_scores[domain] = []
            domain_scores[domain].append(b.score)

        result = {}
        for domain, scores in domain_scores.items():
            result[domain] = sum(scores) / len(scores)
        return result

    def derive_t3(self, model_id: str) -> Dict[str, float]:
        """Derive T3 trust scores from capability benchmarks."""
        capabilities = self.evaluate_capabilities(model_id)
        t3 = {}
        for dim, domains in self.T3_MAPPING.items():
            scores = []
            for d in domains:
                if d.value in capabilities:
                    scores.append(capabilities[d.value])
            t3[dim] = sum(scores) / len(scores) if scores else 0.5
        return t3

    def capability_gap_analysis(self, model_id: str) -> List[Dict]:
        """Identify capability domains without benchmarks."""
        benchmarked = set()
        if model_id in self.benchmarks:
            for b in self.benchmarks[model_id]:
                benchmarked.add(b.domain)
        gaps = []
        for domain in CapabilityDomain:
            if domain not in benchmarked:
                gaps.append({
                    "domain": domain.value,
                    "status": "not_evaluated",
                    "recommendation": f"Add benchmark for {domain.value}",
                })
        return gaps


# ═══════════════════════════════════════════════════════════════
# PART 4: SYSTEMIC RISK CLASSIFIER (Art. 51(2))
# ═══════════════════════════════════════════════════════════════

@dataclass
class SystemicRiskAssessment:
    """Result of systemic risk classification."""
    model_id: str = ""
    is_systemic: bool = False
    compute_flops: float = 0.0
    flop_threshold: float = 1e25   # EU AI Office default
    compute_ratio: float = 0.0     # compute / threshold
    risk_factors: List[str] = field(default_factory=list)
    mitigation_required: List[str] = field(default_factory=list)
    classification_time: float = 0.0


class SystemicRiskClassifier:
    """
    Art. 51(2): GPAI models trained with >10^25 FLOP are presumed systemic risk.
    Additional factors: reach, downstream integrations, autonomy level.
    """

    FLOP_THRESHOLD = 1e25  # Default per EU AI Office guidance

    # Additional risk factors beyond compute
    RISK_FACTORS = {
        "high_reach": "Model available to >1M users",
        "critical_sector": "Deployed in critical infrastructure",
        "autonomous_decisions": "Makes decisions without human review",
        "cross_border": "Deployed across multiple EU member states",
        "real_time": "Operates in real-time safety-critical contexts",
    }

    def __init__(self, flop_threshold: float = None):
        self.flop_threshold = flop_threshold or self.FLOP_THRESHOLD
        self.assessments: Dict[str, SystemicRiskAssessment] = {}

    def classify(self, model_card: GPAIModelCard,
                 risk_factors: Optional[Set[str]] = None) -> SystemicRiskAssessment:
        """Classify GPAI model for systemic risk."""
        now = time.time()
        risk_factors = risk_factors or set()

        compute_ratio = model_card.training_compute_flops / self.flop_threshold
        is_systemic_by_compute = compute_ratio >= 1.0

        # Additional risk factors can trigger classification even below threshold
        matched_factors = []
        for factor in risk_factors:
            if factor in self.RISK_FACTORS:
                matched_factors.append(self.RISK_FACTORS[factor])

        # 3+ additional risk factors at >50% compute = systemic
        is_systemic_by_factors = (
            len(matched_factors) >= 3 and compute_ratio >= 0.5
        )

        is_systemic = is_systemic_by_compute or is_systemic_by_factors

        # Determine required mitigations
        mitigations = []
        if is_systemic:
            mitigations.extend([
                "Art. 55(1)(a): Perform model evaluation including adversarial testing",
                "Art. 55(1)(b): Assess and mitigate systemic risks",
                "Art. 55(1)(c): Track and report serious incidents",
                "Art. 55(1)(d): Ensure adequate cybersecurity protection",
            ])
            if is_systemic_by_compute:
                mitigations.append("Art. 51(2): Compute exceeds 10^25 FLOP threshold")
            if is_systemic_by_factors:
                mitigations.append("Classified by cumulative risk factors")

        assessment = SystemicRiskAssessment(
            model_id=model_card.model_id,
            is_systemic=is_systemic,
            compute_flops=model_card.training_compute_flops,
            flop_threshold=self.flop_threshold,
            compute_ratio=compute_ratio,
            risk_factors=matched_factors,
            mitigation_required=mitigations,
            classification_time=now,
        )
        self.assessments[model_card.model_id] = assessment
        return assessment


# ═══════════════════════════════════════════════════════════════
# PART 5: ADVERSARIAL TESTING REPORT (Art. 55)
# ═══════════════════════════════════════════════════════════════

@dataclass
class AdversarialTestResult:
    """Individual adversarial test result."""
    vector_id: str = ""
    vector_name: str = ""
    category: str = ""
    severity: str = "medium"
    defended: bool = True
    detection_rate: float = 0.0
    mitigation_strategy: str = ""
    test_timestamp: float = 0.0


@dataclass
class AdversarialTestingReport:
    """
    Art. 55 adversarial testing report — maps attack corpus to regulatory format.
    Builds on Web4's 424+ attack vector corpus.
    """
    model_id: str = ""
    report_id: str = ""
    total_vectors: int = 0
    vectors_tested: int = 0
    vectors_defended: int = 0
    defense_rate: float = 0.0
    results: List[AdversarialTestResult] = field(default_factory=list)
    categories: Dict[str, Dict] = field(default_factory=dict)  # category → summary
    report_timestamp: float = 0.0
    report_hash: str = ""
    next_review_date: float = 0.0  # 6-month cycle

    def add_result(self, result: AdversarialTestResult):
        self.results.append(result)
        self.total_vectors = len(self.results)
        self.vectors_tested = len(self.results)
        self.vectors_defended = sum(1 for r in self.results if r.defended)
        self.defense_rate = self.vectors_defended / max(1, self.vectors_tested)

        # Update category summary
        cat = result.category
        if cat not in self.categories:
            self.categories[cat] = {"total": 0, "defended": 0, "rate": 0.0}
        self.categories[cat]["total"] += 1
        if result.defended:
            self.categories[cat]["defended"] += 1
        self.categories[cat]["rate"] = (
            self.categories[cat]["defended"] / self.categories[cat]["total"]
        )

    def compute_hash(self) -> str:
        content = f"{self.model_id}:{self.report_id}:{self.total_vectors}"
        content += f":{self.defense_rate}:{self.report_timestamp}"
        self.report_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return self.report_hash

    def is_adequate(self, min_defense_rate: float = 0.85) -> Tuple[bool, List[str]]:
        """Check if adversarial testing meets Art. 55 adequacy."""
        issues = []
        if self.defense_rate < min_defense_rate:
            issues.append(f"Defense rate {self.defense_rate:.1%} below {min_defense_rate:.1%} threshold")
        # Check category coverage
        required_categories = {"sybil", "trust_manipulation", "privacy", "availability"}
        tested_categories = set(self.categories.keys())
        missing = required_categories - tested_categories
        if missing:
            issues.append(f"Missing test categories: {missing}")
        # Check for undefended critical vectors
        critical_undefended = [
            r for r in self.results
            if r.severity == "critical" and not r.defended
        ]
        if critical_undefended:
            issues.append(f"{len(critical_undefended)} undefended critical vectors")
        return (len(issues) == 0, issues)


# ═══════════════════════════════════════════════════════════════
# PART 6: INCIDENT NOTIFICATION CHAIN (Art. 62)
# ═══════════════════════════════════════════════════════════════

@dataclass
class IncidentReport:
    """Art. 62 incident report with 15-day notification chain."""
    incident_id: str = ""
    model_id: str = ""
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    description: str = ""
    affected_entities: List[str] = field(default_factory=list)
    root_cause: str = ""
    mitigation_applied: str = ""

    # Timeline
    detected_at: float = 0.0
    reported_at: float = 0.0
    notified_at: float = 0.0      # When authority was notified
    resolved_at: float = 0.0

    # Ledger evidence
    ledger_entries: List[str] = field(default_factory=list)  # Hash chain entries
    witness_attestations: List[str] = field(default_factory=list)

    # Status
    notification_sent: bool = False
    within_deadline: bool = True
    report_hash: str = ""

    def compute_hash(self) -> str:
        content = f"{self.incident_id}:{self.model_id}:{self.severity.value}"
        content += f":{self.detected_at}:{self.description}"
        self.report_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return self.report_hash


class IncidentNotificationChain:
    """
    Art. 62 incident notification with Web4 ledger-backed evidence chain.
    15-day deadline for CRITICAL/HIGH incidents.
    """

    DEADLINE_DAYS = {
        IncidentSeverity.CRITICAL: 2,   # 2 days for critical
        IncidentSeverity.HIGH: 15,      # 15 days per Art. 62
        IncidentSeverity.MEDIUM: 30,    # 30 days courtesy
        IncidentSeverity.LOW: 90,       # Quarterly report
    }

    def __init__(self):
        self.incidents: Dict[str, IncidentReport] = {}
        self.notification_log: List[Dict] = []
        self.prev_hash: str = "genesis"

    def report_incident(self, incident: IncidentReport) -> IncidentReport:
        """Register a new incident and start notification clock."""
        incident.detected_at = incident.detected_at or time.time()
        incident.reported_at = time.time()
        incident.incident_id = incident.incident_id or hashlib.sha256(
            f"{incident.model_id}:{incident.detected_at}:{incident.description}".encode()
        ).hexdigest()[:12]

        # Hash chain entry
        entry_content = f"{self.prev_hash}:{incident.incident_id}:{incident.severity.value}"
        entry_hash = hashlib.sha256(entry_content.encode()).hexdigest()[:16]
        incident.ledger_entries.append(entry_hash)
        self.prev_hash = entry_hash

        self.incidents[incident.incident_id] = incident
        return incident

    def send_notification(self, incident_id: str) -> Dict:
        """Mark incident as notified to regulatory authority."""
        if incident_id not in self.incidents:
            return {"success": False, "error": "unknown_incident"}
        incident = self.incidents[incident_id]
        now = time.time()
        incident.notified_at = now
        incident.notification_sent = True

        deadline_days = self.DEADLINE_DAYS.get(incident.severity, 30)
        deadline_seconds = deadline_days * 86400
        elapsed = now - incident.detected_at
        incident.within_deadline = elapsed <= deadline_seconds

        record = {
            "incident_id": incident_id,
            "notified_at": now,
            "within_deadline": incident.within_deadline,
            "elapsed_days": elapsed / 86400,
            "deadline_days": deadline_days,
        }
        self.notification_log.append(record)
        return record

    def check_overdue(self) -> List[Dict]:
        """Find incidents past their notification deadline."""
        overdue = []
        now = time.time()
        for iid, incident in self.incidents.items():
            if incident.notification_sent:
                continue
            deadline_days = self.DEADLINE_DAYS.get(incident.severity, 30)
            deadline_seconds = deadline_days * 86400
            elapsed = now - incident.detected_at
            if elapsed > deadline_seconds:
                overdue.append({
                    "incident_id": iid,
                    "severity": incident.severity.value,
                    "overdue_days": (elapsed - deadline_seconds) / 86400,
                    "deadline_days": deadline_days,
                })
        return overdue

    def resolve_incident(self, incident_id: str, resolution: str) -> bool:
        if incident_id not in self.incidents:
            return False
        incident = self.incidents[incident_id]
        incident.resolved_at = time.time()
        incident.mitigation_applied = resolution
        return True


# ═══════════════════════════════════════════════════════════════
# PART 7: COPYRIGHT PROVENANCE TRACKER (Art. 53(1)(d))
# ═══════════════════════════════════════════════════════════════

@dataclass
class DataSource:
    """A training data source with provenance tracking."""
    source_id: str = ""
    name: str = ""
    provenance: ProvenanceType = ProvenanceType.UNKNOWN
    record_count: int = 0
    license_info: str = ""
    opt_out_checked: bool = False
    v3_veracity: float = 0.5  # V3 Veracity score for data quality
    hash_digest: str = ""     # Content hash for integrity


class CopyrightProvenanceTracker:
    """
    Art. 53(1)(d) — Training data provenance with V3 Veracity scoring.
    Tracks copyright compliance for each data source.
    """

    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.total_records: int = 0
        self.provenance_summary: Dict[str, float] = {}

    def register_source(self, source: DataSource):
        self.sources[source.source_id] = source
        self._recompute_summary()

    def _recompute_summary(self):
        self.total_records = sum(s.record_count for s in self.sources.values())
        if self.total_records == 0:
            self.provenance_summary = {}
            return
        summary: Dict[str, int] = {}
        for s in self.sources.values():
            pt = s.provenance.value
            summary[pt] = summary.get(pt, 0) + s.record_count
        self.provenance_summary = {
            k: v / self.total_records for k, v in summary.items()
        }

    def compliance_check(self) -> Tuple[bool, List[str]]:
        """Check copyright compliance across all sources."""
        issues = []
        unknown_fraction = self.provenance_summary.get("unknown", 0.0)
        if unknown_fraction > 0.1:
            issues.append(f"Unknown provenance: {unknown_fraction:.1%} (max 10%)")

        # Check opt-out compliance
        for sid, source in self.sources.items():
            if source.provenance == ProvenanceType.LICENSED and not source.opt_out_checked:
                issues.append(f"Source {sid}: licensed but opt-out not verified")
            if source.v3_veracity < 0.3:
                issues.append(f"Source {sid}: low veracity score {source.v3_veracity:.2f}")

        return (len(issues) == 0, issues)

    def generate_summary(self) -> Dict:
        """Generate Art. 53(1)(d) training data summary."""
        return {
            "total_sources": len(self.sources),
            "total_records": self.total_records,
            "provenance_distribution": dict(self.provenance_summary),
            "average_veracity": (
                sum(s.v3_veracity for s in self.sources.values()) /
                max(1, len(self.sources))
            ),
            "all_opt_outs_checked": all(
                s.opt_out_checked for s in self.sources.values()
                if s.provenance == ProvenanceType.LICENSED
            ),
        }


# ═══════════════════════════════════════════════════════════════
# PART 8: GPAI COMPLIANCE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

@dataclass
class GPAIComplianceResult:
    """Overall GPAI compliance assessment."""
    model_id: str = ""
    category: GPAICategory = GPAICategory.GENERAL_PURPOSE
    model_card_complete: bool = False
    model_card_gaps: List[str] = field(default_factory=list)
    capabilities_evaluated: bool = False
    capability_gaps: List[str] = field(default_factory=list)
    systemic_risk: bool = False
    adversarial_adequate: bool = False
    adversarial_issues: List[str] = field(default_factory=list)
    copyright_compliant: bool = False
    copyright_issues: List[str] = field(default_factory=list)
    pending_incidents: int = 0
    overdue_incidents: int = 0
    overall_compliant: bool = False
    compliance_score: float = 0.0  # 0.0-1.0
    assessment_time: float = 0.0


class GPAIComplianceOrchestrator:
    """
    Full lifecycle orchestrator for GPAI obligations.
    Combines all Art. 51-56 components into unified assessment.
    """

    def __init__(self):
        self.evaluator = CapabilityEvaluator()
        self.risk_classifier = SystemicRiskClassifier()
        self.incident_chain = IncidentNotificationChain()
        self.provenance_tracker = CopyrightProvenanceTracker()
        self.model_cards: Dict[str, GPAIModelCard] = {}
        self.test_reports: Dict[str, AdversarialTestingReport] = {}

    def register_model(self, card: GPAIModelCard) -> GPAIModelCard:
        card.created_at = card.created_at or time.time()
        card.compute_hash()
        self.model_cards[card.model_id] = card
        return card

    def register_test_report(self, report: AdversarialTestingReport):
        report.compute_hash()
        self.test_reports[report.model_id] = report

    def assess_compliance(self, model_id: str,
                          risk_factors: Optional[Set[str]] = None) -> GPAIComplianceResult:
        """Full GPAI compliance assessment."""
        now = time.time()
        result = GPAIComplianceResult(model_id=model_id, assessment_time=now)

        # 1. Model card completeness
        if model_id in self.model_cards:
            card = self.model_cards[model_id]
            complete, gaps = card.is_complete()
            result.model_card_complete = complete
            result.model_card_gaps = gaps
        else:
            result.model_card_gaps = ["no_model_card_registered"]

        # 2. Capability evaluation
        cap_gaps = self.evaluator.capability_gap_analysis(model_id)
        result.capabilities_evaluated = len(cap_gaps) <= 2  # Allow 2 unevaluated domains
        result.capability_gaps = [g["domain"] for g in cap_gaps]

        # 3. Systemic risk classification
        if model_id in self.model_cards:
            risk = self.risk_classifier.classify(
                self.model_cards[model_id], risk_factors
            )
            result.systemic_risk = risk.is_systemic
            if risk.is_systemic:
                result.category = GPAICategory.SYSTEMIC_RISK
            elif self.model_cards[model_id].training_compute_flops == 0:
                # Open source heuristic: no compute declared
                result.category = GPAICategory.GENERAL_PURPOSE

        # 4. Adversarial testing
        if model_id in self.test_reports:
            report = self.test_reports[model_id]
            adequate, issues = report.is_adequate()
            result.adversarial_adequate = adequate
            result.adversarial_issues = issues
        else:
            result.adversarial_issues = ["no_adversarial_testing_report"]

        # 5. Copyright compliance
        copyright_ok, copyright_issues = self.provenance_tracker.compliance_check()
        result.copyright_compliant = copyright_ok
        result.copyright_issues = copyright_issues

        # 6. Incident status
        overdue = self.incident_chain.check_overdue()
        result.overdue_incidents = len(overdue)
        result.pending_incidents = sum(
            1 for i in self.incident_chain.incidents.values()
            if not i.notification_sent and not i.resolved_at
        )

        # Compute overall score
        checks = [
            (result.model_card_complete, 0.25),
            (result.capabilities_evaluated, 0.15),
            (result.adversarial_adequate, 0.25),
            (result.copyright_compliant, 0.20),
            (result.overdue_incidents == 0, 0.15),
        ]
        result.compliance_score = sum(w for ok, w in checks if ok)
        result.overall_compliant = result.compliance_score >= 0.85

        return result


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    return condition


def run_tests():
    results = []
    now = time.time()

    # ── S1: Model Card Creation ─────────────────────────────────
    print("\nS1: Model Card Creation")
    card = GPAIModelCard(
        model_id="gpt-4-web4",
        model_name="GPT-4 Web4 Agent",
        provider="OpenAI",
        version="4.0.0",
        lct_uri="lct://openai:gpt-4@web4",
        description="Large language model fine-tuned for Web4 agent operations",
        architecture="transformer",
        parameter_count=1_750_000_000_000,
        training_compute_flops=2.15e25,
        intended_uses=["web4_agent_operations", "trust_evaluation"],
        prohibited_uses=["social_scoring", "mass_surveillance"],
        capabilities={
            CapabilityDomain.LANGUAGE.value: 0.92,
            CapabilityDomain.REASONING.value: 0.88,
        },
        training_data_summary="Curated dataset of web text, code, and Web4 interactions",
        training_data_size=500_000_000,
        t3_composite=0.85,
        v3_composite=0.80,
        hardware_bound=True,
        attestation_count=12,
    )
    card.compute_hash()
    results.append(check("s1_card_hash", len(card.card_hash) == 16))
    complete, gaps = card.is_complete()
    results.append(check("s1_card_complete", complete))
    results.append(check("s1_no_gaps", len(gaps) == 0))
    results.append(check("s1_lct_uri", card.lct_uri.startswith("lct://")))

    # ── S2: Incomplete Model Card ───────────────────────────────
    print("\nS2: Incomplete Model Card")
    incomplete = GPAIModelCard(model_id="incomplete-1", model_name="Test")
    complete2, gaps2 = incomplete.is_complete()
    results.append(check("s2_not_complete", not complete2))
    results.append(check("s2_has_gaps", len(gaps2) >= 3))
    results.append(check("s2_missing_provider", "provider" in gaps2))
    results.append(check("s2_missing_description", "description" in gaps2))

    # ── S3: Capability Evaluation ───────────────────────────────
    print("\nS3: Capability Evaluation")
    evaluator = CapabilityEvaluator()
    benchmarks = [
        CapabilityBenchmark(CapabilityDomain.LANGUAGE, "MMLU", 0.86, 86.0, 100.0),
        CapabilityBenchmark(CapabilityDomain.LANGUAGE, "HellaSwag", 0.95, 95.0, 100.0),
        CapabilityBenchmark(CapabilityDomain.REASONING, "ARC-C", 0.83, 83.0, 100.0),
        CapabilityBenchmark(CapabilityDomain.CODE, "HumanEval", 0.72, 72.0, 100.0),
        CapabilityBenchmark(CapabilityDomain.SAFETY, "TruthfulQA", 0.64, 64.0, 100.0),
        CapabilityBenchmark(CapabilityDomain.BIAS, "BBQ", 0.78, 78.0, 100.0),
        CapabilityBenchmark(CapabilityDomain.ROBUSTNESS, "AdvGLUE", 0.71, 71.0, 100.0),
    ]
    for b in benchmarks:
        evaluator.register_benchmark("gpt-4-web4", b)

    caps = evaluator.evaluate_capabilities("gpt-4-web4")
    results.append(check("s3_language_avg", abs(caps["language_understanding"] - 0.905) < 0.01))
    results.append(check("s3_reasoning", abs(caps["logical_reasoning"] - 0.83) < 0.01))
    results.append(check("s3_code", abs(caps["code_generation"] - 0.72) < 0.01))

    t3 = evaluator.derive_t3("gpt-4-web4")
    results.append(check("s3_talent_derived", t3["talent"] > 0.7))
    results.append(check("s3_training_derived", t3["training"] > 0.5))
    results.append(check("s3_temperament_derived", t3["temperament"] > 0.6))

    # ── S4: Capability Gap Analysis ─────────────────────────────
    print("\nS4: Capability Gap Analysis")
    gaps4 = evaluator.capability_gap_analysis("gpt-4-web4")
    results.append(check("s4_some_gaps", len(gaps4) > 0))
    gap_domains = {g["domain"] for g in gaps4}
    results.append(check("s4_knowledge_gap", "factual_knowledge" in gap_domains))
    results.append(check("s4_multimodal_gap", "multimodal_processing" in gap_domains))

    # No gaps for fully evaluated model
    evaluator2 = CapabilityEvaluator()
    for d in CapabilityDomain:
        evaluator2.register_benchmark("full", CapabilityBenchmark(d, "test", 0.8, 80, 100))
    gaps_full = evaluator2.capability_gap_analysis("full")
    results.append(check("s4_no_gaps_full", len(gaps_full) == 0))

    # ── S5: Systemic Risk — Above Threshold ─────────────────────
    print("\nS5: Systemic Risk — Above Threshold")
    classifier = SystemicRiskClassifier()
    risk = classifier.classify(card)
    results.append(check("s5_is_systemic", risk.is_systemic))
    results.append(check("s5_compute_above", risk.compute_ratio >= 1.0))
    results.append(check("s5_has_mitigations", len(risk.mitigation_required) > 0))
    results.append(check("s5_art55_referenced", any("Art. 55" in m for m in risk.mitigation_required)))

    # ── S6: Systemic Risk — Below Threshold ─────────────────────
    print("\nS6: Systemic Risk — Below Threshold")
    small_card = GPAIModelCard(
        model_id="small-model", model_name="Small", provider="Local",
        training_compute_flops=1e22,
    )
    risk2 = classifier.classify(small_card)
    results.append(check("s6_not_systemic", not risk2.is_systemic))
    results.append(check("s6_ratio_below", risk2.compute_ratio < 1.0))
    results.append(check("s6_no_mitigations", len(risk2.mitigation_required) == 0))

    # ── S7: Systemic Risk — Factor-Based ────────────────────────
    print("\nS7: Systemic Risk — Factor-Based Classification")
    mid_card = GPAIModelCard(
        model_id="mid-model", model_name="Mid", provider="MidCorp",
        training_compute_flops=6e24,  # 60% of threshold
    )
    risk3 = classifier.classify(mid_card, {
        "high_reach", "critical_sector", "autonomous_decisions", "cross_border"
    })
    results.append(check("s7_factor_systemic", risk3.is_systemic))
    results.append(check("s7_below_compute", risk3.compute_ratio < 1.0))
    results.append(check("s7_has_factors", len(risk3.risk_factors) >= 3))

    # Below 50% compute with factors → NOT systemic
    tiny_card = GPAIModelCard(
        model_id="tiny", model_name="Tiny", provider="Tiny",
        training_compute_flops=1e24,  # 10% of threshold
    )
    risk4 = classifier.classify(tiny_card, {
        "high_reach", "critical_sector", "autonomous_decisions"
    })
    results.append(check("s7_tiny_not_systemic", not risk4.is_systemic))

    # ── S8: Adversarial Testing Report ──────────────────────────
    print("\nS8: Adversarial Testing Report")
    report = AdversarialTestingReport(
        model_id="gpt-4-web4",
        report_id="atr-001",
        report_timestamp=now,
    )
    categories = [
        ("sybil", 50), ("trust_manipulation", 40),
        ("privacy", 30), ("availability", 20),
        ("escalation", 15),
    ]
    for cat, count in categories:
        for i in range(count):
            defended = (i < count - 2)  # 2 undefended per category
            report.add_result(AdversarialTestResult(
                vector_id=f"{cat}-{i:03d}",
                vector_name=f"{cat} vector {i}",
                category=cat,
                severity="high" if i < 5 else "medium",
                defended=defended,
                detection_rate=0.95 if defended else 0.0,
                mitigation_strategy=f"{cat}_defense_{i}" if defended else "",
                test_timestamp=now,
            ))

    results.append(check("s8_total_vectors", report.total_vectors == 155))
    results.append(check("s8_defended", report.vectors_defended == 145))
    results.append(check("s8_defense_rate", abs(report.defense_rate - 145/155) < 0.01))
    results.append(check("s8_categories", len(report.categories) == 5))
    report.compute_hash()
    results.append(check("s8_hash", len(report.report_hash) == 16))

    # ── S9: Adversarial Adequacy Check ──────────────────────────
    print("\nS9: Adversarial Adequacy Check")
    adequate, issues = report.is_adequate()
    results.append(check("s9_adequate", adequate))
    results.append(check("s9_no_issues", len(issues) == 0))

    # Inadequate report (low defense rate)
    bad_report = AdversarialTestingReport(model_id="bad", report_id="atr-bad")
    for i in range(10):
        bad_report.add_result(AdversarialTestResult(
            vector_id=f"bad-{i}", category="sybil",
            defended=(i < 3),  # Only 30% defended
            severity="critical" if i > 7 else "medium",
        ))
    adequate2, issues2 = bad_report.is_adequate()
    results.append(check("s9_not_adequate", not adequate2))
    results.append(check("s9_low_rate_flagged", any("Defense rate" in i for i in issues2)))
    results.append(check("s9_missing_categories", any("Missing" in i for i in issues2)))
    results.append(check("s9_critical_undefended", any("critical" in i for i in issues2)))

    # ── S10: Incident Reporting ─────────────────────────────────
    print("\nS10: Incident Reporting")
    chain = IncidentNotificationChain()
    incident = chain.report_incident(IncidentReport(
        model_id="gpt-4-web4",
        severity=IncidentSeverity.HIGH,
        description="Model generated harmful output in safety-critical context",
        affected_entities=["entity-001", "entity-002"],
        root_cause="Adversarial prompt injection",
    ))
    results.append(check("s10_incident_id", len(incident.incident_id) > 0))
    results.append(check("s10_ledger_entry", len(incident.ledger_entries) == 1))
    results.append(check("s10_detected", incident.detected_at > 0))

    # ── S11: Incident Notification Timeline ─────────────────────
    print("\nS11: Incident Notification Timeline")
    notif = chain.send_notification(incident.incident_id)
    results.append(check("s11_notified", notif["within_deadline"]))
    results.append(check("s11_elapsed_low", notif["elapsed_days"] < 1))
    results.append(check("s11_deadline_15", notif["deadline_days"] == 15))

    # Critical incident with tight deadline
    critical = chain.report_incident(IncidentReport(
        model_id="gpt-4-web4",
        severity=IncidentSeverity.CRITICAL,
        description="Complete system failure",
    ))
    crit_notif = chain.send_notification(critical.incident_id)
    results.append(check("s11_critical_deadline_2", crit_notif["deadline_days"] == 2))
    results.append(check("s11_critical_within", crit_notif["within_deadline"]))

    # ── S12: Overdue Detection ──────────────────────────────────
    print("\nS12: Overdue Detection")
    # Create an incident that's "old" (simulate overdue)
    old_incident = IncidentReport(
        model_id="old-model",
        severity=IncidentSeverity.HIGH,
        description="Old unnotified incident",
        detected_at=now - 20 * 86400,  # 20 days ago
    )
    chain.report_incident(old_incident)
    overdue = chain.check_overdue()
    results.append(check("s12_has_overdue", len(overdue) > 0))
    results.append(check("s12_overdue_days", overdue[0]["overdue_days"] > 0))

    # Resolve incident
    chain.resolve_incident(incident.incident_id, "Prompt filter deployed")
    results.append(check("s12_resolved", chain.incidents[incident.incident_id].resolved_at > 0))

    # ── S13: Copyright Provenance ───────────────────────────────
    print("\nS13: Copyright Provenance")
    tracker = CopyrightProvenanceTracker()
    sources = [
        DataSource("s1", "Wikipedia", ProvenanceType.PUBLIC_DOMAIN, 1_000_000, "CC0", True, 0.9),
        DataSource("s2", "Books", ProvenanceType.LICENSED, 500_000, "MIT", True, 0.85),
        DataSource("s3", "Web Crawl", ProvenanceType.FAIR_USE, 2_000_000, "fair_use", True, 0.6),
        DataSource("s4", "Synthetic", ProvenanceType.SYNTHETIC, 300_000, "internal", True, 0.95),
    ]
    for s in sources:
        tracker.register_source(s)

    results.append(check("s13_total_records", tracker.total_records == 3_800_000))
    results.append(check("s13_provenance_dist", len(tracker.provenance_summary) == 4))
    compliant, issues13 = tracker.compliance_check()
    results.append(check("s13_compliant", compliant))

    # ── S14: Copyright Non-Compliance ───────────────────────────
    print("\nS14: Copyright Non-Compliance")
    bad_tracker = CopyrightProvenanceTracker()
    bad_tracker.register_source(
        DataSource("bad1", "Unknown Source", ProvenanceType.UNKNOWN, 500_000, "", False, 0.2)
    )
    bad_tracker.register_source(
        DataSource("bad2", "Licensed No Check", ProvenanceType.LICENSED, 100_000, "MIT", False, 0.8)
    )
    bad_compliant, bad_issues = bad_tracker.compliance_check()
    results.append(check("s14_not_compliant", not bad_compliant))
    results.append(check("s14_unknown_flagged", any("Unknown provenance" in i for i in bad_issues)))
    results.append(check("s14_opt_out_flagged", any("opt-out" in i for i in bad_issues)))
    results.append(check("s14_low_veracity", any("veracity" in i for i in bad_issues)))

    # ── S15: Provenance Summary ─────────────────────────────────
    print("\nS15: Provenance Summary")
    summary = tracker.generate_summary()
    results.append(check("s15_total_sources", summary["total_sources"] == 4))
    results.append(check("s15_total_records", summary["total_records"] == 3_800_000))
    results.append(check("s15_avg_veracity", summary["average_veracity"] > 0.7))
    results.append(check("s15_opt_outs_checked", summary["all_opt_outs_checked"]))

    # ── S16: Full Orchestrator — Compliant Model ────────────────
    print("\nS16: Full Orchestrator — Compliant Model")
    orch = GPAIComplianceOrchestrator()
    orch.register_model(card)

    # Register benchmarks
    for b in benchmarks:
        orch.evaluator.register_benchmark("gpt-4-web4", b)
    # Also fill remaining domains
    for d in [CapabilityDomain.KNOWLEDGE, CapabilityDomain.MULTIMODAL]:
        orch.evaluator.register_benchmark("gpt-4-web4",
            CapabilityBenchmark(d, "test", 0.75, 75, 100))

    # Register adversarial report
    orch.register_test_report(report)

    # Register copyright sources
    for s in sources:
        orch.provenance_tracker.register_source(s)

    compliance = orch.assess_compliance("gpt-4-web4")
    results.append(check("s16_model_card_ok", compliance.model_card_complete))
    results.append(check("s16_caps_evaluated", compliance.capabilities_evaluated))
    results.append(check("s16_systemic", compliance.systemic_risk))  # High compute
    results.append(check("s16_adversarial_ok", compliance.adversarial_adequate))
    results.append(check("s16_copyright_ok", compliance.copyright_compliant))
    results.append(check("s16_overall_compliant", compliance.overall_compliant))
    results.append(check("s16_score_high", compliance.compliance_score >= 0.85))

    # ── S17: Orchestrator — Non-Compliant Model ─────────────────
    print("\nS17: Orchestrator — Non-Compliant Model")
    orch2 = GPAIComplianceOrchestrator()
    orch2.register_model(GPAIModelCard(
        model_id="bad-model", model_name="Bad",
    ))
    bad_compliance = orch2.assess_compliance("bad-model")
    results.append(check("s17_card_incomplete", not bad_compliance.model_card_complete))
    results.append(check("s17_no_testing", not bad_compliance.adversarial_adequate))
    results.append(check("s17_not_compliant", not bad_compliance.overall_compliant))
    results.append(check("s17_score_low", bad_compliance.compliance_score < 0.5))

    # ── S18: Orchestrator with Incidents ────────────────────────
    print("\nS18: Orchestrator with Incidents")
    orch3 = GPAIComplianceOrchestrator()
    orch3.register_model(card)
    for b in benchmarks:
        orch3.evaluator.register_benchmark("gpt-4-web4", b)
    for d in [CapabilityDomain.KNOWLEDGE, CapabilityDomain.MULTIMODAL]:
        orch3.evaluator.register_benchmark("gpt-4-web4",
            CapabilityBenchmark(d, "test", 0.75, 75, 100))
    orch3.register_test_report(report)
    for s in sources:
        orch3.provenance_tracker.register_source(s)

    # Add overdue incident
    orch3.incident_chain.report_incident(IncidentReport(
        model_id="gpt-4-web4",
        severity=IncidentSeverity.HIGH,
        description="Overdue incident",
        detected_at=now - 20 * 86400,
    ))
    compliance3 = orch3.assess_compliance("gpt-4-web4")
    results.append(check("s18_has_overdue", compliance3.overdue_incidents > 0))
    results.append(check("s18_score_reduced", compliance3.compliance_score < 1.0))

    # ── S19: Systemic Risk Category Propagation ─────────────────
    print("\nS19: Category Propagation")
    results.append(check("s19_systemic_category",
        compliance.category == GPAICategory.SYSTEMIC_RISK))
    results.append(check("s19_bad_general",
        bad_compliance.category == GPAICategory.GENERAL_PURPOSE))

    # ── S20: Incident Hash Chain Integrity ──────────────────────
    print("\nS20: Incident Hash Chain")
    chain2 = IncidentNotificationChain()
    ids = []
    for i in range(5):
        inc = chain2.report_incident(IncidentReport(
            model_id=f"model-{i}",
            severity=IncidentSeverity.MEDIUM,
            description=f"Incident {i}",
        ))
        ids.append(inc.incident_id)

    # Each incident has a ledger entry
    for iid in ids:
        results.append(check(f"s20_ledger_{iid[:6]}", len(chain2.incidents[iid].ledger_entries) > 0))
    # Hash chain is sequential (each builds on prev)
    entries = [chain2.incidents[iid].ledger_entries[0] for iid in ids]
    results.append(check("s20_unique_hashes", len(set(entries)) == 5))

    # ── Summary ─────────────────────────────────────────────────
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"GPAI Obligations: {passed}/{total} checks passed")
    if passed == total:
        print("ALL CHECKS PASSED")
    else:
        print(f"FAILURES: {total - passed}")
    return passed == total


if __name__ == "__main__":
    run_tests()
