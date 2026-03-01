"""
EU AI Act Compliance Demo Stack — Reference Implementation

Builds on eu_ai_act_compliance_engine.py to provide demo-ready tools:

1. **Automated Compliance Report**: Takes any Web4 entity and generates
   a human-readable per-article pass/fail report with evidence chains
2. **Remediation Advisor**: Given partial compliance, recommends specific
   Web4 primitives to deploy for each missing article
3. **Compliance Drift Detection**: Monitors T3/V3 degradation over time,
   alerts when entity drops below article thresholds
4. **5-Minute Demo**: Complete audit → report → remediation cycle

Strategic context: EU AI Act deadline is Aug 2, 2026 (5 months away).
Cross-model review: "Demo-ability matters — can this be shown in 5 min?"

Article-to-Web4 mapping:
  Art. 9  (Risk Management) → T3 tensor risk scoring
  Art. 10 (Data Governance) → V3 veracity + bias detection
  Art. 11 (Technical Docs)  → LCT birth certificate + metadata
  Art. 12 (Record-Keeping)  → Fractal chain audit trail
  Art. 13 (Transparency)    → Trust tensor explanation
  Art. 14 (Human Oversight) → R6 approval framework
  Art. 15 (Accuracy)        → Attack corpus robustness metrics
  Art. 26 (Deployer)        → ATP accountability

Checks: 70
"""
from __future__ import annotations
import hashlib
import math
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ─── EU AI Act Article Model ────────────────────────────────────────────────

class Article(Enum):
    ART_9 = "Art. 9 — Risk Management System"
    ART_10 = "Art. 10 — Data and Data Governance"
    ART_11 = "Art. 11 — Technical Documentation"
    ART_12 = "Art. 12 — Record-Keeping"
    ART_13 = "Art. 13 — Transparency"
    ART_14 = "Art. 14 — Human Oversight"
    ART_15 = "Art. 15 — Accuracy, Robustness, Cybersecurity"
    ART_26 = "Art. 26 — Obligations of Deployers"


class ComplianceLevel(Enum):
    FULL = "FULL"               # All sub-requirements met
    SUBSTANTIAL = "SUBSTANTIAL" # ≥75% of sub-requirements
    PARTIAL = "PARTIAL"         # ≥50% of sub-requirements
    NON_COMPLIANT = "NON_COMPLIANT"  # <50%


class DriftSeverity(Enum):
    NONE = auto()
    WARNING = auto()      # Trending toward non-compliance
    ALERT = auto()         # Below threshold, immediate action needed
    CRITICAL = auto()      # Multiple articles failing


# ─── Entity Model (Web4 primitives) ─────────────────────────────────────────

@dataclass
class T3Score:
    """Trust tensor — 3 root dimensions."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3


@dataclass
class V3Score:
    """Value tensor — 3 root dimensions."""
    valuation: float = 0.5
    veracity: float = 0.5
    validity: float = 0.5

    @property
    def composite(self) -> float:
        return (self.valuation + self.veracity + self.validity) / 3


@dataclass
class LCTMetadata:
    """Linked Context Token metadata for documentation."""
    lct_id: str = ""
    birth_certificate: bool = False
    entity_type: str = ""
    creation_time: float = 0.0
    hardware_binding: bool = False
    witness_count: int = 0
    metadata_fields: int = 0


@dataclass
class AuditTrail:
    """Fractal chain audit trail for record-keeping."""
    chain_length: int = 0
    hash_chain_valid: bool = False
    retention_days: int = 0
    hmac_signed: bool = False
    fractal_depth: int = 0  # Number of chain levels (compost/leaf/stem/root)


@dataclass
class HumanOversight:
    """R6 human oversight configuration."""
    r6_approval_required: bool = False
    override_mechanism: bool = False
    stop_capability: bool = False
    intervention_log: int = 0  # Number of logged interventions


@dataclass
class RobustnessMetrics:
    """Attack corpus robustness measurements."""
    attack_vectors_tested: int = 0
    vectors_defended: int = 0
    adversarial_accuracy: float = 0.0
    uptime_percentage: float = 0.0

    @property
    def defense_ratio(self) -> float:
        if self.attack_vectors_tested == 0:
            return 0.0
        return self.vectors_defended / self.attack_vectors_tested


@dataclass
class ATPAccountability:
    """ATP-based accountability for deployer obligations."""
    atp_stake: float = 0.0
    accountability_frame: str = "normal"  # normal, heightened, crisis
    audit_budget_allocated: bool = False
    incident_response_plan: bool = False


@dataclass
class Web4Entity:
    """A Web4 entity subject to EU AI Act compliance assessment."""
    entity_id: str
    entity_type: str = "AI_SYSTEM"
    risk_level: str = "HIGH"
    t3: T3Score = field(default_factory=T3Score)
    v3: V3Score = field(default_factory=V3Score)
    lct: LCTMetadata = field(default_factory=LCTMetadata)
    audit: AuditTrail = field(default_factory=AuditTrail)
    oversight: HumanOversight = field(default_factory=HumanOversight)
    robustness: RobustnessMetrics = field(default_factory=RobustnessMetrics)
    accountability: ATPAccountability = field(default_factory=ATPAccountability)
    bias_detection_enabled: bool = False
    transparency_report_available: bool = False


# ─── Article Assessment ─────────────────────────────────────────────────────

@dataclass
class SubRequirement:
    """A specific sub-requirement within an article."""
    req_id: str
    description: str
    met: bool
    evidence: str
    web4_primitive: str  # Which Web4 component satisfies this


@dataclass
class ArticleAssessment:
    """Assessment of compliance for a single article."""
    article: Article
    sub_requirements: List[SubRequirement]
    level: ComplianceLevel
    score: float  # 0-1, fraction of sub-requirements met
    remediation_hints: List[str]
    web4_mapping: str  # Which Web4 primitive(s) this maps to


class ArticleAssessor:
    """Assess compliance per article using Web4 primitives."""

    def assess_art9(self, entity: Web4Entity) -> ArticleAssessment:
        """Art. 9 — Risk Management System."""
        reqs = [
            SubRequirement("9.1", "Risk identification system established",
                           entity.t3.composite > 0.3,
                           f"T3 composite={entity.t3.composite:.3f}",
                           "T3 tensor"),
            SubRequirement("9.2", "Risk mitigation measures documented",
                           entity.t3.talent > 0.4,
                           f"T3.talent={entity.t3.talent:.3f}",
                           "T3.talent"),
            SubRequirement("9.3", "Residual risk assessment",
                           entity.t3.training > 0.4,
                           f"T3.training={entity.t3.training:.3f}",
                           "T3.training"),
            SubRequirement("9.4", "Testing and validation performed",
                           entity.robustness.attack_vectors_tested >= 10,
                           f"vectors_tested={entity.robustness.attack_vectors_tested}",
                           "Attack corpus"),
        ]
        return self._build_assessment(Article.ART_9, reqs, "T3 tensor risk scoring")

    def assess_art10(self, entity: Web4Entity) -> ArticleAssessment:
        """Art. 10 — Data and Data Governance."""
        reqs = [
            SubRequirement("10.1", "Training data quality governance",
                           entity.v3.veracity > 0.5,
                           f"V3.veracity={entity.v3.veracity:.3f}",
                           "V3.veracity"),
            SubRequirement("10.2", "Data relevance and representativeness",
                           entity.v3.validity > 0.5,
                           f"V3.validity={entity.v3.validity:.3f}",
                           "V3.validity"),
            SubRequirement("10.3", "Bias examination and mitigation",
                           entity.bias_detection_enabled,
                           f"bias_detection={entity.bias_detection_enabled}",
                           "Bias detection module"),
            SubRequirement("10.4", "Data provenance tracking",
                           entity.lct.lct_id != "",
                           f"lct_id={'present' if entity.lct.lct_id else 'missing'}",
                           "LCT provenance"),
        ]
        return self._build_assessment(Article.ART_10, reqs, "V3 tensor + bias detection")

    def assess_art11(self, entity: Web4Entity) -> ArticleAssessment:
        """Art. 11 — Technical Documentation."""
        reqs = [
            SubRequirement("11.1", "System description and intended purpose",
                           entity.lct.entity_type != "",
                           f"entity_type={entity.lct.entity_type}",
                           "LCT entity_type"),
            SubRequirement("11.2", "Development methodology documentation",
                           entity.lct.birth_certificate,
                           f"birth_cert={entity.lct.birth_certificate}",
                           "LCT birth certificate"),
            SubRequirement("11.3", "System architecture and design choices",
                           entity.lct.metadata_fields >= 5,
                           f"metadata_fields={entity.lct.metadata_fields}",
                           "LCT metadata"),
        ]
        return self._build_assessment(Article.ART_11, reqs, "LCT documentation chain")

    def assess_art12(self, entity: Web4Entity) -> ArticleAssessment:
        """Art. 12 — Record-Keeping."""
        reqs = [
            SubRequirement("12.1", "Automatic logging capability",
                           entity.audit.chain_length > 0,
                           f"chain_length={entity.audit.chain_length}",
                           "Fractal chain"),
            SubRequirement("12.2", "Audit trail integrity",
                           entity.audit.hash_chain_valid,
                           f"chain_valid={entity.audit.hash_chain_valid}",
                           "Hash chain"),
            SubRequirement("12.3", "Record retention per regulation",
                           entity.audit.retention_days >= 365,
                           f"retention={entity.audit.retention_days}d",
                           "Retention policy"),
            SubRequirement("12.4", "Tamper-evident records",
                           entity.audit.hmac_signed,
                           f"hmac_signed={entity.audit.hmac_signed}",
                           "HMAC signing"),
        ]
        return self._build_assessment(Article.ART_12, reqs, "Fractal chain audit trail")

    def assess_art13(self, entity: Web4Entity) -> ArticleAssessment:
        """Art. 13 — Transparency."""
        reqs = [
            SubRequirement("13.1", "Clear instructions for use",
                           entity.transparency_report_available,
                           f"report={entity.transparency_report_available}",
                           "Transparency report"),
            SubRequirement("13.2", "Performance characteristics disclosed",
                           entity.t3.composite > 0.3 and entity.v3.composite > 0.3,
                           f"T3={entity.t3.composite:.3f}, V3={entity.v3.composite:.3f}",
                           "T3/V3 tensor explanation"),
            SubRequirement("13.3", "Limitations and risks communicated",
                           entity.robustness.attack_vectors_tested > 0,
                           f"vectors={entity.robustness.attack_vectors_tested}",
                           "Attack corpus results"),
        ]
        return self._build_assessment(Article.ART_13, reqs, "Trust tensor transparency")

    def assess_art14(self, entity: Web4Entity) -> ArticleAssessment:
        """Art. 14 — Human Oversight."""
        reqs = [
            SubRequirement("14.1", "Human-in-the-loop mechanism",
                           entity.oversight.r6_approval_required,
                           f"r6_approval={entity.oversight.r6_approval_required}",
                           "R6 approval"),
            SubRequirement("14.2", "Override and stop capability",
                           entity.oversight.override_mechanism and entity.oversight.stop_capability,
                           f"override={entity.oversight.override_mechanism}, stop={entity.oversight.stop_capability}",
                           "R6 override"),
            SubRequirement("14.3", "Intervention logging",
                           entity.oversight.intervention_log >= 1,
                           f"interventions={entity.oversight.intervention_log}",
                           "R6 action log"),
        ]
        return self._build_assessment(Article.ART_14, reqs, "R6 human oversight framework")

    def assess_art15(self, entity: Web4Entity) -> ArticleAssessment:
        """Art. 15 — Accuracy, Robustness, Cybersecurity."""
        reqs = [
            SubRequirement("15.1", "Accuracy levels declared",
                           entity.robustness.adversarial_accuracy > 0.8,
                           f"accuracy={entity.robustness.adversarial_accuracy:.3f}",
                           "Adversarial accuracy"),
            SubRequirement("15.2", "Robustness against adversarial attacks",
                           entity.robustness.defense_ratio > 0.9,
                           f"defense_ratio={entity.robustness.defense_ratio:.3f}",
                           "Attack defense ratio"),
            SubRequirement("15.3", "System resilience and availability",
                           entity.robustness.uptime_percentage > 99.0,
                           f"uptime={entity.robustness.uptime_percentage:.1f}%",
                           "Uptime monitoring"),
            SubRequirement("15.4", "Cybersecurity measures implemented",
                           entity.robustness.attack_vectors_tested >= 50,
                           f"vectors={entity.robustness.attack_vectors_tested}",
                           "Security test coverage"),
        ]
        return self._build_assessment(Article.ART_15, reqs, "Attack corpus robustness")

    def assess_art26(self, entity: Web4Entity) -> ArticleAssessment:
        """Art. 26 — Obligations of Deployers."""
        reqs = [
            SubRequirement("26.1", "Deployer accountability established",
                           entity.accountability.atp_stake > 0,
                           f"atp_stake={entity.accountability.atp_stake}",
                           "ATP stake"),
            SubRequirement("26.2", "Incident response plan",
                           entity.accountability.incident_response_plan,
                           f"irp={entity.accountability.incident_response_plan}",
                           "Incident response"),
            SubRequirement("26.3", "Audit budget allocated",
                           entity.accountability.audit_budget_allocated,
                           f"budget={entity.accountability.audit_budget_allocated}",
                           "ATP audit budget"),
        ]
        return self._build_assessment(Article.ART_26, reqs, "ATP accountability framework")

    def assess_all(self, entity: Web4Entity) -> List[ArticleAssessment]:
        """Run all article assessments."""
        return [
            self.assess_art9(entity),
            self.assess_art10(entity),
            self.assess_art11(entity),
            self.assess_art12(entity),
            self.assess_art13(entity),
            self.assess_art14(entity),
            self.assess_art15(entity),
            self.assess_art26(entity),
        ]

    def _build_assessment(self, article: Article,
                            reqs: List[SubRequirement],
                            mapping: str) -> ArticleAssessment:
        met = sum(1 for r in reqs if r.met)
        total = len(reqs)
        score = met / total if total > 0 else 0.0

        if score >= 1.0:
            level = ComplianceLevel.FULL
        elif score >= 0.75:
            level = ComplianceLevel.SUBSTANTIAL
        elif score >= 0.5:
            level = ComplianceLevel.PARTIAL
        else:
            level = ComplianceLevel.NON_COMPLIANT

        hints = []
        for r in reqs:
            if not r.met:
                hints.append(f"Deploy {r.web4_primitive}: {r.description}")

        return ArticleAssessment(
            article=article,
            sub_requirements=reqs,
            level=level,
            score=score,
            remediation_hints=hints,
            web4_mapping=mapping,
        )


# ─── Compliance Report Generator ────────────────────────────────────────────

@dataclass
class ComplianceReport:
    """Human-readable compliance report."""
    report_id: str
    entity_id: str
    entity_type: str
    assessments: List[ArticleAssessment]
    overall_level: ComplianceLevel
    overall_score: float
    articles_passing: int
    articles_total: int
    remediation_plan: List[str]
    timestamp: float = field(default_factory=time.time)
    report_hash: str = ""

    def compute_hash(self) -> str:
        data = f"{self.report_id}:{self.entity_id}:{self.overall_score}:{self.timestamp}"
        self.report_hash = hashlib.sha256(data.encode()).hexdigest()[:32]
        return self.report_hash


class ComplianceReportGenerator:
    """Generate comprehensive compliance reports."""

    def __init__(self):
        self.assessor = ArticleAssessor()

    def generate(self, entity: Web4Entity) -> ComplianceReport:
        """Generate a full compliance report for an entity."""
        assessments = self.assessor.assess_all(entity)

        passing = sum(1 for a in assessments if a.level == ComplianceLevel.FULL)
        total = len(assessments)
        overall_score = sum(a.score for a in assessments) / total if total > 0 else 0.0

        # Overall level based on passing article count
        if passing == total:
            overall_level = ComplianceLevel.FULL
        elif passing >= 6:
            overall_level = ComplianceLevel.SUBSTANTIAL
        elif passing >= 4:
            overall_level = ComplianceLevel.PARTIAL
        else:
            overall_level = ComplianceLevel.NON_COMPLIANT

        # Aggregate remediation plan
        remediation = []
        for a in assessments:
            if a.level != ComplianceLevel.FULL:
                for hint in a.remediation_hints:
                    remediation.append(f"[{a.article.value}] {hint}")

        report = ComplianceReport(
            report_id=secrets.token_hex(8),
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            assessments=assessments,
            overall_level=overall_level,
            overall_score=overall_score,
            articles_passing=passing,
            articles_total=total,
            remediation_plan=remediation,
        )
        report.compute_hash()
        return report

    def render_text(self, report: ComplianceReport) -> str:
        """Render report as human-readable text."""
        lines = [
            "=" * 60,
            "EU AI ACT COMPLIANCE REPORT",
            "=" * 60,
            f"Entity: {report.entity_id} ({report.entity_type})",
            f"Report ID: {report.report_id}",
            f"Overall: {report.overall_level.value} ({report.overall_score:.0%})",
            f"Articles: {report.articles_passing}/{report.articles_total} FULL",
            "-" * 60,
        ]

        for assessment in report.assessments:
            status = "PASS" if assessment.level == ComplianceLevel.FULL else assessment.level.value
            lines.append(f"\n{assessment.article.value}: {status} ({assessment.score:.0%})")
            lines.append(f"  Web4 mapping: {assessment.web4_mapping}")

            for req in assessment.sub_requirements:
                mark = "[x]" if req.met else "[ ]"
                lines.append(f"  {mark} {req.req_id}: {req.description}")
                lines.append(f"      Evidence: {req.evidence}")

        if report.remediation_plan:
            lines.append("\n" + "-" * 60)
            lines.append("REMEDIATION PLAN:")
            for i, hint in enumerate(report.remediation_plan, 1):
                lines.append(f"  {i}. {hint}")

        lines.append("\n" + "=" * 60)
        lines.append(f"Hash: {report.report_hash}")
        return "\n".join(lines)


# ─── Remediation Advisor ────────────────────────────────────────────────────

@dataclass
class RemediationAction:
    """A specific remediation action to improve compliance."""
    article: Article
    priority: int           # 1=highest
    action: str
    web4_primitive: str
    estimated_impact: str   # "high", "medium", "low"
    current_state: str
    target_state: str


class RemediationAdvisor:
    """Advise on specific Web4 primitives to deploy for compliance gaps."""

    ARTICLE_PRIORITY = {
        Article.ART_9: 1,    # Risk management is foundational
        Article.ART_15: 2,   # Security is high priority
        Article.ART_14: 3,   # Human oversight
        Article.ART_12: 4,   # Record-keeping
        Article.ART_10: 5,   # Data governance
        Article.ART_13: 6,   # Transparency
        Article.ART_11: 7,   # Documentation
        Article.ART_26: 8,   # Deployer obligations
    }

    def advise(self, report: ComplianceReport) -> List[RemediationAction]:
        """Generate prioritized remediation actions."""
        actions = []

        for assessment in report.assessments:
            if assessment.level == ComplianceLevel.FULL:
                continue

            priority = self.ARTICLE_PRIORITY.get(assessment.article, 9)

            for req in assessment.sub_requirements:
                if req.met:
                    continue

                action = RemediationAction(
                    article=assessment.article,
                    priority=priority,
                    action=f"Implement {req.description}",
                    web4_primitive=req.web4_primitive,
                    estimated_impact=self._estimate_impact(assessment, req),
                    current_state=req.evidence,
                    target_state=self._compute_target(assessment.article, req),
                )
                actions.append(action)

        # Sort by priority
        actions.sort(key=lambda a: a.priority)
        return actions

    def _estimate_impact(self, assessment: ArticleAssessment,
                           req: SubRequirement) -> str:
        # Missing requirement in an otherwise-passing article = high impact
        met_count = sum(1 for r in assessment.sub_requirements if r.met)
        total = len(assessment.sub_requirements)
        if met_count == total - 1:
            return "high"  # Last missing piece
        elif met_count >= total / 2:
            return "medium"
        return "low"

    def _compute_target(self, article: Article, req: SubRequirement) -> str:
        targets = {
            "T3 tensor": "T3 composite > 0.3",
            "T3.talent": "T3.talent > 0.4",
            "T3.training": "T3.training > 0.4",
            "V3.veracity": "V3.veracity > 0.5",
            "V3.validity": "V3.validity > 0.5",
            "Bias detection module": "bias_detection = True",
            "LCT provenance": "LCT ID assigned",
            "LCT entity_type": "entity_type defined",
            "LCT birth certificate": "birth_certificate = True",
            "LCT metadata": "metadata_fields >= 5",
            "Fractal chain": "chain_length > 0",
            "Hash chain": "hash_chain_valid = True",
            "Retention policy": "retention >= 365 days",
            "HMAC signing": "hmac_signed = True",
            "Transparency report": "report available",
            "T3/V3 tensor explanation": "T3 > 0.3, V3 > 0.3",
            "Attack corpus results": "vectors_tested > 0",
            "R6 approval": "r6_approval_required = True",
            "R6 override": "override + stop = True",
            "R6 action log": "intervention_log >= 1",
            "Adversarial accuracy": "accuracy > 0.8",
            "Attack defense ratio": "defense_ratio > 0.9",
            "Uptime monitoring": "uptime > 99%",
            "Security test coverage": "vectors_tested >= 50",
            "ATP stake": "atp_stake > 0",
            "Incident response": "irp = True",
            "ATP audit budget": "budget allocated",
        }
        return targets.get(req.web4_primitive, "See documentation")


# ─── Compliance Drift Detector ──────────────────────────────────────────────

@dataclass
class DriftSnapshot:
    """A point-in-time snapshot of compliance metrics."""
    timestamp: float
    t3_composite: float
    v3_composite: float
    defense_ratio: float
    chain_length: int
    overall_score: float


@dataclass
class DriftAlert:
    """Alert when compliance drifts below thresholds."""
    alert_id: str
    entity_id: str
    severity: DriftSeverity
    affected_articles: List[Article]
    metric: str
    current_value: float
    threshold: float
    trend: str  # "declining", "stable", "recovering"
    timestamp: float = field(default_factory=time.time)


class ComplianceDriftDetector:
    """
    Monitor compliance metrics over time and alert on degradation.

    Thresholds:
    - T3 composite < 0.3 → Art. 9 at risk
    - V3 composite < 0.5 → Art. 10 at risk
    - Defense ratio < 0.9 → Art. 15 at risk
    - Overall score declining for 3+ snapshots → WARNING
    """

    def __init__(self):
        self.history: Dict[str, List[DriftSnapshot]] = defaultdict(list)
        self.alerts: List[DriftAlert] = []

    def record_snapshot(self, entity_id: str, entity: Web4Entity,
                         report: ComplianceReport):
        """Record a compliance snapshot."""
        snapshot = DriftSnapshot(
            timestamp=time.time(),
            t3_composite=entity.t3.composite,
            v3_composite=entity.v3.composite,
            defense_ratio=entity.robustness.defense_ratio,
            chain_length=entity.audit.chain_length,
            overall_score=report.overall_score,
        )
        self.history[entity_id].append(snapshot)

    def check_drift(self, entity_id: str, entity: Web4Entity) -> List[DriftAlert]:
        """Check for compliance drift."""
        alerts = []
        history = self.history.get(entity_id, [])

        # Threshold checks
        if entity.t3.composite < 0.3:
            alerts.append(DriftAlert(
                alert_id=secrets.token_hex(8),
                entity_id=entity_id,
                severity=DriftSeverity.ALERT,
                affected_articles=[Article.ART_9],
                metric="t3_composite",
                current_value=entity.t3.composite,
                threshold=0.3,
                trend=self._compute_trend(history, "t3_composite"),
            ))

        if entity.v3.composite < 0.5:
            alerts.append(DriftAlert(
                alert_id=secrets.token_hex(8),
                entity_id=entity_id,
                severity=DriftSeverity.ALERT,
                affected_articles=[Article.ART_10],
                metric="v3_composite",
                current_value=entity.v3.composite,
                threshold=0.5,
                trend=self._compute_trend(history, "v3_composite"),
            ))

        if entity.robustness.defense_ratio < 0.9:
            alerts.append(DriftAlert(
                alert_id=secrets.token_hex(8),
                entity_id=entity_id,
                severity=DriftSeverity.ALERT,
                affected_articles=[Article.ART_15],
                metric="defense_ratio",
                current_value=entity.robustness.defense_ratio,
                threshold=0.9,
                trend=self._compute_trend(history, "defense_ratio"),
            ))

        # Trend-based detection
        if len(history) >= 3:
            recent = history[-3:]
            scores = [s.overall_score for s in recent]
            if all(scores[i] > scores[i + 1] for i in range(len(scores) - 1)):
                alerts.append(DriftAlert(
                    alert_id=secrets.token_hex(8),
                    entity_id=entity_id,
                    severity=DriftSeverity.WARNING,
                    affected_articles=[],
                    metric="overall_score",
                    current_value=scores[-1],
                    threshold=scores[0],
                    trend="declining",
                ))

        # Critical: multiple articles failing
        if len(alerts) >= 3:
            for alert in alerts:
                alert.severity = DriftSeverity.CRITICAL

        self.alerts.extend(alerts)
        return alerts

    def _compute_trend(self, history: List[DriftSnapshot],
                        metric: str) -> str:
        if len(history) < 2:
            return "stable"
        recent = history[-3:]
        values = [getattr(s, metric, 0) for s in recent]
        if all(values[i] >= values[i + 1] for i in range(len(values) - 1)):
            return "declining"
        if all(values[i] <= values[i + 1] for i in range(len(values) - 1)):
            return "recovering"
        return "stable"


# ─── 5-Minute Demo Orchestrator ─────────────────────────────────────────────

class FiveMinuteDemo:
    """
    Complete audit → report → remediation cycle in one call.
    Designed to be demo-able in 5 minutes.
    """

    def __init__(self):
        self.generator = ComplianceReportGenerator()
        self.advisor = RemediationAdvisor()
        self.drift_detector = ComplianceDriftDetector()

    def run_demo(self, entity: Web4Entity) -> Dict[str, Any]:
        """Run the complete demo cycle."""
        # Step 1: Generate compliance report
        report = self.generator.generate(entity)

        # Step 2: Get remediation advice
        actions = self.advisor.advise(report)

        # Step 3: Record snapshot for drift detection
        self.drift_detector.record_snapshot(entity.entity_id, entity, report)

        # Step 4: Check for drift
        drift_alerts = self.drift_detector.check_drift(entity.entity_id, entity)

        # Step 5: Render human-readable output
        text_report = self.generator.render_text(report)

        return {
            "report": report,
            "remediation": actions,
            "drift_alerts": drift_alerts,
            "text_report": text_report,
            "overall_level": report.overall_level.value,
            "overall_score": report.overall_score,
            "articles_passing": report.articles_passing,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_compliant_entity() -> Web4Entity:
    """Create a fully compliant entity."""
    return Web4Entity(
        entity_id="compliant_ai_001",
        entity_type="AI_SYSTEM",
        risk_level="HIGH",
        t3=T3Score(talent=0.85, training=0.9, temperament=0.88),
        v3=V3Score(valuation=0.8, veracity=0.85, validity=0.82),
        lct=LCTMetadata(
            lct_id="lct:compliant:001",
            birth_certificate=True,
            entity_type="AI_SYSTEM",
            creation_time=time.time(),
            hardware_binding=True,
            witness_count=5,
            metadata_fields=10,
        ),
        audit=AuditTrail(
            chain_length=500,
            hash_chain_valid=True,
            retention_days=730,
            hmac_signed=True,
            fractal_depth=3,
        ),
        oversight=HumanOversight(
            r6_approval_required=True,
            override_mechanism=True,
            stop_capability=True,
            intervention_log=12,
        ),
        robustness=RobustnessMetrics(
            attack_vectors_tested=424,
            vectors_defended=420,
            adversarial_accuracy=0.95,
            uptime_percentage=99.9,
        ),
        accountability=ATPAccountability(
            atp_stake=1000,
            accountability_frame="normal",
            audit_budget_allocated=True,
            incident_response_plan=True,
        ),
        bias_detection_enabled=True,
        transparency_report_available=True,
    )


def _make_partial_entity() -> Web4Entity:
    """Create a partially compliant entity."""
    return Web4Entity(
        entity_id="partial_ai_002",
        entity_type="AI_SYSTEM",
        risk_level="HIGH",
        t3=T3Score(talent=0.6, training=0.5, temperament=0.55),
        v3=V3Score(valuation=0.4, veracity=0.3, validity=0.35),
        lct=LCTMetadata(lct_id="lct:partial:002", entity_type="AI_SYSTEM",
                         birth_certificate=False, metadata_fields=3),
        audit=AuditTrail(chain_length=10, hash_chain_valid=True,
                          retention_days=90, hmac_signed=False),
        oversight=HumanOversight(r6_approval_required=True,
                                  override_mechanism=False),
        robustness=RobustnessMetrics(attack_vectors_tested=20,
                                      vectors_defended=15,
                                      adversarial_accuracy=0.7,
                                      uptime_percentage=98.0),
        accountability=ATPAccountability(atp_stake=100),
        bias_detection_enabled=False,
        transparency_report_available=False,
    )


def _make_noncompliant_entity() -> Web4Entity:
    """Create a non-compliant entity."""
    return Web4Entity(
        entity_id="noncompliant_003",
        entity_type="AI_SYSTEM",
        risk_level="HIGH",
        t3=T3Score(talent=0.1, training=0.1, temperament=0.1),
        v3=V3Score(valuation=0.1, veracity=0.1, validity=0.1),
    )


def run_checks():
    results = {}
    total = 0
    passed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal total, passed
        total += 1
        if condition:
            passed += 1
            results[name] = "PASS"
        else:
            results[name] = f"FAIL: {detail}"
            print(f"  FAIL: {name}: {detail}")

    # ── Section 1: Fully Compliant Entity ────────────────────────────────────

    entity = _make_compliant_entity()
    assessor = ArticleAssessor()
    assessments = assessor.assess_all(entity)

    check("s1_8_articles_assessed", len(assessments) == 8)
    check("s1_all_full", all(a.level == ComplianceLevel.FULL for a in assessments),
          f"levels={[a.level.value for a in assessments if a.level != ComplianceLevel.FULL]}")
    check("s1_all_score_1", all(a.score == 1.0 for a in assessments))
    check("s1_no_remediation", all(len(a.remediation_hints) == 0 for a in assessments))

    # ── Section 2: Report Generation — Compliant ─────────────────────────────

    gen = ComplianceReportGenerator()
    report = gen.generate(entity)

    check("s2_report_id", report.report_id != "")
    check("s2_entity_id", report.entity_id == "compliant_ai_001")
    check("s2_overall_full", report.overall_level == ComplianceLevel.FULL)
    check("s2_score_1", report.overall_score == 1.0,
          f"score={report.overall_score}")
    check("s2_all_passing", report.articles_passing == 8)
    check("s2_no_remediation", len(report.remediation_plan) == 0)
    check("s2_report_hash", len(report.report_hash) == 32)

    # ── Section 3: Text Report ───────────────────────────────────────────────

    text = gen.render_text(report)
    check("s3_has_header", "EU AI ACT COMPLIANCE REPORT" in text)
    check("s3_has_entity", "compliant_ai_001" in text)
    check("s3_has_overall", "FULL" in text)
    check("s3_has_articles", "Art. 9" in text and "Art. 15" in text)
    check("s3_has_evidence", "T3" in text or "V3" in text)
    check("s3_has_hash", report.report_hash in text)

    # ── Section 4: Partially Compliant Entity ────────────────────────────────

    partial = _make_partial_entity()
    partial_report = gen.generate(partial)

    check("s4_not_full", partial_report.overall_level != ComplianceLevel.FULL)
    check("s4_some_passing", 0 < partial_report.articles_passing < 8,
          f"passing={partial_report.articles_passing}")
    check("s4_has_remediation", len(partial_report.remediation_plan) > 0)
    check("s4_score_partial", 0 < partial_report.overall_score < 1.0,
          f"score={partial_report.overall_score}")

    # ── Section 5: Non-Compliant Entity ──────────────────────────────────────

    noncomp = _make_noncompliant_entity()
    noncomp_report = gen.generate(noncomp)

    check("s5_non_compliant",
          noncomp_report.overall_level == ComplianceLevel.NON_COMPLIANT,
          f"level={noncomp_report.overall_level}")
    check("s5_zero_passing", noncomp_report.articles_passing == 0)
    check("s5_many_remediation", len(noncomp_report.remediation_plan) > 10)

    # ── Section 6: Individual Article Assessments ────────────────────────────

    a9 = assessor.assess_art9(entity)
    check("s6_art9_full", a9.level == ComplianceLevel.FULL)
    check("s6_art9_4_reqs", len(a9.sub_requirements) == 4)
    check("s6_art9_mapping", "T3" in a9.web4_mapping)

    a10 = assessor.assess_art10(entity)
    check("s6_art10_full", a10.level == ComplianceLevel.FULL)
    check("s6_art10_bias_req", any("bias" in r.description.lower()
                                     for r in a10.sub_requirements))

    a14 = assessor.assess_art14(entity)
    check("s6_art14_full", a14.level == ComplianceLevel.FULL)
    check("s6_art14_r6", "R6" in a14.web4_mapping)

    a15 = assessor.assess_art15(entity)
    check("s6_art15_full", a15.level == ComplianceLevel.FULL)
    check("s6_art15_4_reqs", len(a15.sub_requirements) == 4)

    # ── Section 7: Remediation Advisor ───────────────────────────────────────

    advisor = RemediationAdvisor()
    actions = advisor.advise(partial_report)

    check("s7_has_actions", len(actions) > 0, f"n={len(actions)}")
    check("s7_prioritized", all(actions[i].priority <= actions[i + 1].priority
                                  for i in range(len(actions) - 1)))
    check("s7_has_web4_primitive", all(a.web4_primitive != "" for a in actions))
    check("s7_has_impact", all(a.estimated_impact in ("high", "medium", "low")
                                 for a in actions))
    check("s7_has_target", all(a.target_state != "" for a in actions))

    # Compliant entity should have no actions
    comp_actions = advisor.advise(report)
    check("s7_compliant_no_actions", len(comp_actions) == 0)

    # ── Section 8: Drift Detection — No Drift ───────────────────────────────

    drift = ComplianceDriftDetector()
    drift.record_snapshot("entity1", entity, report)
    alerts = drift.check_drift("entity1", entity)
    check("s8_no_drift_alerts", len(alerts) == 0)

    # ── Section 9: Drift Detection — Threshold Breach ────────────────────────

    degraded = Web4Entity(
        entity_id="degraded_004",
        t3=T3Score(talent=0.2, training=0.2, temperament=0.2),
        v3=V3Score(valuation=0.3, veracity=0.3, validity=0.3),
        robustness=RobustnessMetrics(attack_vectors_tested=100,
                                      vectors_defended=80),
    )
    degraded_report = gen.generate(degraded)
    drift.record_snapshot("degraded", degraded, degraded_report)
    alerts = drift.check_drift("degraded", degraded)

    check("s9_drift_detected", len(alerts) > 0)
    check("s9_t3_alert", any(a.metric == "t3_composite" for a in alerts))
    check("s9_v3_alert", any(a.metric == "v3_composite" for a in alerts))
    check("s9_defense_alert", any(a.metric == "defense_ratio" for a in alerts))
    # 3+ alerts → critical
    check("s9_critical_severity", all(a.severity == DriftSeverity.CRITICAL
                                        for a in alerts))

    # ── Section 10: Drift Detection — Trend ──────────────────────────────────

    drift2 = ComplianceDriftDetector()
    # Simulate declining scores
    for score in [0.9, 0.8, 0.7]:
        snapshot = DriftSnapshot(
            timestamp=time.time(),
            t3_composite=0.8,
            v3_composite=0.8,
            defense_ratio=0.95,
            chain_length=100,
            overall_score=score,
        )
        drift2.history["trend_entity"].append(snapshot)

    trend_entity = _make_compliant_entity()
    trend_entity.entity_id = "trend_entity"
    trend_alerts = drift2.check_drift("trend_entity", trend_entity)
    check("s10_trend_warning", any(a.metric == "overall_score" and
                                     a.trend == "declining" for a in trend_alerts))

    # ── Section 11: 5-Minute Demo ────────────────────────────────────────────

    demo = FiveMinuteDemo()
    result = demo.run_demo(entity)

    check("s11_has_report", result["report"] is not None)
    check("s11_has_remediation", "remediation" in result)
    check("s11_has_drift", "drift_alerts" in result)
    check("s11_has_text", len(result["text_report"]) > 100)
    check("s11_overall_level", result["overall_level"] == "FULL")
    check("s11_score", result["overall_score"] == 1.0)
    check("s11_passing_8", result["articles_passing"] == 8)

    # Demo with partial entity
    partial_result = demo.run_demo(partial)
    check("s11_partial_has_remediation", len(partial_result["remediation"]) > 0)
    check("s11_partial_not_full", partial_result["overall_level"] != "FULL")

    # ── Section 12: Report Determinism ───────────────────────────────────────

    report_a = gen.generate(entity)
    report_b = gen.generate(entity)
    check("s12_same_score", report_a.overall_score == report_b.overall_score)
    check("s12_same_level", report_a.overall_level == report_b.overall_level)
    check("s12_same_passing", report_a.articles_passing == report_b.articles_passing)
    check("s12_different_ids", report_a.report_id != report_b.report_id)

    # ── Section 13: Article Independence ─────────────────────────────────────

    # Modifying one aspect shouldn't affect unrelated articles
    entity_mod = _make_compliant_entity()
    entity_mod.t3 = T3Score(0.1, 0.1, 0.1)  # Break Art. 9

    report_mod = gen.generate(entity_mod)
    mod_assessments = {a.article: a for a in report_mod.assessments}
    check("s13_art9_broken", mod_assessments[Article.ART_9].level != ComplianceLevel.FULL)
    check("s13_art12_intact", mod_assessments[Article.ART_12].level == ComplianceLevel.FULL)
    check("s13_art14_intact", mod_assessments[Article.ART_14].level == ComplianceLevel.FULL)
    check("s13_art26_intact", mod_assessments[Article.ART_26].level == ComplianceLevel.FULL)

    # ── Section 14: Performance ──────────────────────────────────────────────

    t0 = time.time()
    for _ in range(1000):
        gen.generate(entity)
    elapsed = time.time() - t0
    check("s14_1000_reports_fast", elapsed < 2.0, f"elapsed={elapsed:.2f}s")

    t0 = time.time()
    for _ in range(100):
        demo.run_demo(entity)
    elapsed = time.time() - t0
    check("s14_100_demos_fast", elapsed < 2.0, f"elapsed={elapsed:.2f}s")

    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"EU AI Act Compliance Demo Stack: {passed}/{total} checks passed")
    print(f"{'='*60}")

    if passed < total:
        print("\nFailed checks:")
        for name, result in results.items():
            if result.startswith("FAIL"):
                print(f"  {name}: {result}")

    return passed, total


if __name__ == "__main__":
    run_checks()
