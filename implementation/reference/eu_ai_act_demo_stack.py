"""
EU AI Act Compliance Demo Stack — Reference Implementation

A presentation-ready compliance assessment system that generates
human-readable reports, identifies remediation gaps, and detects
compliance drift. Designed for the "can this be shown in 5 minutes?"
criterion from the cross-model strategic review.

Key features:
1. **Automated Report Generator**: Article-by-article compliance report
   mapping each EU AI Act article to the Web4 primitive that satisfies it
2. **Remediation Advisor**: Given partial compliance, what's missing?
3. **Compliance Drift Detection**: Has entity's T3/V3 degraded below
   article thresholds since last audit?
4. **Risk Classification**: Annex III category detection + risk level
5. **Compliance Timeline**: Historical compliance score tracking

Builds on: eu_ai_act_compliance_engine.py, compliance_instrumentation.py
Deadline: August 2, 2026 (high-risk AI systems)

Checks: 65
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


# ─── Core Types ───────────────────────────────────────────────────────────────

class AIActArticle(Enum):
    ART_9 = "Risk Management System"
    ART_10 = "Data and Data Governance"
    ART_11 = "Technical Documentation"
    ART_12 = "Record-keeping"
    ART_13 = "Transparency and Information"
    ART_14 = "Human Oversight"
    ART_15 = "Accuracy, Robustness, Cybersecurity"


class RiskLevel(Enum):
    UNACCEPTABLE = auto()  # Art. 5 — prohibited practices
    HIGH = auto()          # Annex III — full compliance required
    LIMITED = auto()       # Transparency obligations only
    MINIMAL = auto()       # No obligations


class ComplianceGrade(Enum):
    FULL = auto()          # 100% requirements met
    SUBSTANTIAL = auto()   # ≥75% met
    PARTIAL = auto()       # ≥50% met
    NON_COMPLIANT = auto() # <50% met


class DriftDirection(Enum):
    IMPROVING = auto()
    STABLE = auto()
    DEGRADING = auto()
    CRITICAL_DROP = auto()


# ─── Web4 Entity Model ──────────────────────────────────────────────────────

@dataclass
class T3Score:
    """Trust tensor — 3 root dimensions."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0


@dataclass
class V3Score:
    """Value tensor — 3 root dimensions."""
    valuation: float = 0.5
    veracity: float = 0.5
    validity: float = 0.5

    @property
    def composite(self) -> float:
        return (self.valuation + self.veracity + self.validity) / 3.0


@dataclass
class Web4Entity:
    """An entity to assess for EU AI Act compliance."""
    entity_id: str
    entity_type: str  # "ai_agent", "human", "organization", "hardware", etc.
    t3: T3Score = field(default_factory=T3Score)
    v3: V3Score = field(default_factory=V3Score)
    atp_balance: float = 100.0
    has_lct: bool = True
    has_hardware_binding: bool = False
    witnesses: int = 0
    fractal_chain_depth: int = 0  # 0=compost, 1=leaf, 2=stem, 3=root
    human_oversight_enabled: bool = False
    attack_resistance_score: float = 0.0  # From attack corpus testing
    bias_audit_score: float = 0.0         # From bias detection
    documentation_completeness: float = 0.0
    annex_iii_category: str = "not_high_risk"
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─── Article Requirements Registry ──────────────────────────────────────────

@dataclass
class ArticleRequirement:
    """A specific requirement within an EU AI Act article."""
    req_id: str
    article: AIActArticle
    description: str
    web4_mechanism: str  # Which Web4 component satisfies this
    check_fn_name: str   # Name of the check function
    weight: float = 1.0  # Importance weight
    min_threshold: float = 0.5  # Minimum acceptable score


class ArticleRegistry:
    """Registry of all EU AI Act article requirements mapped to Web4."""

    def __init__(self):
        self.requirements: Dict[AIActArticle, List[ArticleRequirement]] = defaultdict(list)
        self._populate()

    def _populate(self):
        """Map each article to Web4 mechanisms."""
        # Art. 9: Risk Management System
        self._add(AIActArticle.ART_9, "9.1", "Continuous risk identification",
                  "T3 trust tensor monitoring", "check_t3_monitoring", 1.0, 0.4)
        self._add(AIActArticle.ART_9, "9.2", "Risk mitigation measures",
                  "Attack corpus resistance score", "check_attack_resistance", 1.0, 0.3)
        self._add(AIActArticle.ART_9, "9.3", "Testing and validation",
                  "V3 veracity validation", "check_v3_veracity", 1.0, 0.5)

        # Art. 10: Data Governance
        self._add(AIActArticle.ART_10, "10.1", "Training data quality",
                  "V3 validity assessment", "check_v3_validity", 1.0, 0.5)
        self._add(AIActArticle.ART_10, "10.2", "Bias examination",
                  "Bias audit score", "check_bias_audit", 1.5, 0.4)
        self._add(AIActArticle.ART_10, "10.3", "Data representativeness",
                  "V3 valuation diversity", "check_v3_valuation", 1.0, 0.4)

        # Art. 11: Technical Documentation
        self._add(AIActArticle.ART_11, "11.1", "System documentation",
                  "Documentation completeness", "check_documentation", 1.0, 0.6)

        # Art. 12: Record-keeping
        self._add(AIActArticle.ART_12, "12.1", "Automatic logging",
                  "Fractal chain audit trail", "check_fractal_chain", 1.0, 0.3)
        self._add(AIActArticle.ART_12, "12.2", "Event traceability",
                  "LCT presence chain", "check_lct_presence", 1.0, 0.5)

        # Art. 13: Transparency
        self._add(AIActArticle.ART_13, "13.1", "Deployer information",
                  "T3 tensor explainability", "check_t3_explainability", 1.0, 0.5)
        self._add(AIActArticle.ART_13, "13.2", "AI system labeling",
                  "Entity type classification", "check_entity_type", 0.8, 0.5)

        # Art. 14: Human Oversight
        self._add(AIActArticle.ART_14, "14.1", "Oversight measures",
                  "Human oversight flag + R6 approval", "check_human_oversight", 1.5, 0.5)
        self._add(AIActArticle.ART_14, "14.2", "Override capability",
                  "ATP-gated intervention", "check_atp_intervention", 1.0, 0.3)

        # Art. 15: Accuracy and Robustness
        self._add(AIActArticle.ART_15, "15.1", "Accuracy levels",
                  "T3 talent score", "check_t3_talent", 1.0, 0.5)
        self._add(AIActArticle.ART_15, "15.2", "Robustness/resilience",
                  "Attack resistance + hardware binding", "check_robustness", 1.2, 0.3)
        self._add(AIActArticle.ART_15, "15.3", "Cybersecurity",
                  "Witness network + crypto anchoring", "check_cybersecurity", 1.0, 0.3)

    def _add(self, article: AIActArticle, req_id: str, description: str,
             mechanism: str, check_fn: str, weight: float, threshold: float):
        self.requirements[article].append(ArticleRequirement(
            req_id=req_id, article=article, description=description,
            web4_mechanism=mechanism, check_fn_name=check_fn,
            weight=weight, min_threshold=threshold,
        ))

    def get_article_requirements(self, article: AIActArticle) -> List[ArticleRequirement]:
        return self.requirements.get(article, [])

    def get_all_requirements(self) -> List[ArticleRequirement]:
        all_reqs = []
        for reqs in self.requirements.values():
            all_reqs.extend(reqs)
        return all_reqs

    @property
    def total_requirements(self) -> int:
        return sum(len(v) for v in self.requirements.values())


# ─── Compliance Checker ──────────────────────────────────────────────────────

@dataclass
class RequirementResult:
    """Result of checking a single requirement."""
    req_id: str
    article: AIActArticle
    score: float          # 0-1
    passed: bool
    mechanism_used: str
    finding: str          # Human-readable finding
    remediation: str = "" # Suggested fix if not passed


@dataclass
class ArticleResult:
    """Aggregated result for one article."""
    article: AIActArticle
    article_name: str
    requirements_checked: int
    requirements_passed: int
    weighted_score: float  # 0-1
    grade: ComplianceGrade
    findings: List[RequirementResult]


class ComplianceChecker:
    """Check an entity against all EU AI Act requirements."""

    def __init__(self, registry: Optional[ArticleRegistry] = None):
        self.registry = registry or ArticleRegistry()

    def check_entity(self, entity: Web4Entity) -> List[RequirementResult]:
        """Check entity against all requirements."""
        results = []
        for req in self.registry.get_all_requirements():
            result = self._check_requirement(entity, req)
            results.append(result)
        return results

    def _check_requirement(self, entity: Web4Entity,
                             req: ArticleRequirement) -> RequirementResult:
        """Check a single requirement."""
        score, finding, remediation = self._evaluate(entity, req)
        passed = score >= req.min_threshold

        return RequirementResult(
            req_id=req.req_id,
            article=req.article,
            score=score,
            passed=passed,
            mechanism_used=req.web4_mechanism,
            finding=finding,
            remediation=remediation if not passed else "",
        )

    def _evaluate(self, entity: Web4Entity,
                    req: ArticleRequirement) -> Tuple[float, str, str]:
        """Evaluate a specific check. Returns (score, finding, remediation)."""
        fn = req.check_fn_name

        if fn == "check_t3_monitoring":
            score = entity.t3.composite
            return score, f"T3 composite: {score:.3f}", \
                "Increase trust through witnessed interactions"

        elif fn == "check_attack_resistance":
            score = entity.attack_resistance_score
            return score, f"Attack resistance: {score:.3f}", \
                "Run attack corpus testing to improve resistance score"

        elif fn == "check_v3_veracity":
            score = entity.v3.veracity
            return score, f"V3 veracity: {score:.3f}", \
                "Improve value verification through VCM attestation"

        elif fn == "check_v3_validity":
            score = entity.v3.validity
            return score, f"V3 validity: {score:.3f}", \
                "Enhance data validation through V3 assessment pipeline"

        elif fn == "check_bias_audit":
            score = entity.bias_audit_score
            return score, f"Bias audit: {score:.3f}", \
                "Run 4/5ths rule bias detection on protected attributes"

        elif fn == "check_v3_valuation":
            score = entity.v3.valuation
            return score, f"V3 valuation: {score:.3f}", \
                "Diversify value assessment through multi-assessor VCM"

        elif fn == "check_documentation":
            score = entity.documentation_completeness
            return score, f"Documentation: {score:.1%} complete", \
                "Generate technical documentation using Art. 11 template"

        elif fn == "check_fractal_chain":
            # Fractal chain depth maps to record-keeping quality
            score = min(entity.fractal_chain_depth / 3.0, 1.0)
            return score, f"Fractal chain depth: {entity.fractal_chain_depth}", \
                "Promote audit records to higher fractal chain levels"

        elif fn == "check_lct_presence":
            score = 1.0 if entity.has_lct else 0.0
            return score, f"LCT present: {entity.has_lct}", \
                "Create LCT birth certificate for entity"

        elif fn == "check_t3_explainability":
            score = entity.t3.composite  # Explainability correlates with trust
            return score, f"T3 explainability: {score:.3f}", \
                "Enable T3 tensor delta logging for action explanations"

        elif fn == "check_entity_type":
            score = 1.0 if entity.entity_type in [
                "ai_agent", "human", "organization", "hardware",
                "sensor", "actuator", "dictionary"] else 0.5
            return score, f"Entity type: {entity.entity_type}", \
                "Classify entity using Web4 entity taxonomy"

        elif fn == "check_human_oversight":
            score = 1.0 if entity.human_oversight_enabled else 0.0
            return score, f"Human oversight: {entity.human_oversight_enabled}", \
                "Enable human oversight via R6 approval gates"

        elif fn == "check_atp_intervention":
            # ATP balance enables intervention capability
            score = min(entity.atp_balance / 100.0, 1.0)
            return score, f"ATP balance for intervention: {entity.atp_balance:.0f}", \
                "Maintain sufficient ATP balance for human override capability"

        elif fn == "check_t3_talent":
            score = entity.t3.talent
            return score, f"T3 talent (accuracy proxy): {score:.3f}", \
                "Improve accuracy through training and witnessed performance"

        elif fn == "check_robustness":
            hw_bonus = 0.2 if entity.has_hardware_binding else 0.0
            score = min(entity.attack_resistance_score + hw_bonus, 1.0)
            return score, f"Robustness: {score:.3f} (hw_bind={entity.has_hardware_binding})", \
                "Add hardware binding and improve attack resistance"

        elif fn == "check_cybersecurity":
            witness_score = min(entity.witnesses / 5.0, 1.0)
            score = witness_score * 0.5 + entity.attack_resistance_score * 0.5
            return score, f"Cybersecurity: {score:.3f} ({entity.witnesses} witnesses)", \
                "Increase witness diversity and crypto anchoring coverage"

        return 0.0, "Unknown check", "Review requirement"


# ─── Report Generator ────────────────────────────────────────────────────────

@dataclass
class ComplianceReport:
    """Full compliance report for an entity."""
    report_id: str
    entity_id: str
    entity_type: str
    risk_level: RiskLevel
    overall_grade: ComplianceGrade
    overall_score: float
    article_results: Dict[str, ArticleResult]  # article_name → result
    total_requirements: int
    passed_requirements: int
    remediation_items: List[Dict[str, str]]
    generated_at: float
    report_hash: str = ""


class ReportGenerator:
    """Generate human-readable compliance reports."""

    def __init__(self, checker: Optional[ComplianceChecker] = None):
        self.checker = checker or ComplianceChecker()

    def classify_risk(self, entity: Web4Entity) -> RiskLevel:
        """Classify entity risk level per Annex III."""
        if entity.annex_iii_category in [
            "biometrics", "critical_infrastructure", "law_enforcement",
            "migration_asylum_border", "administration_of_justice"]:
            return RiskLevel.HIGH
        elif entity.annex_iii_category in [
            "education_vocational_training", "employment_workers_management",
            "essential_private_public_services"]:
            if entity.t3.composite < 0.7:
                return RiskLevel.HIGH
            return RiskLevel.LIMITED
        elif entity.entity_type == "ai_agent":
            return RiskLevel.LIMITED
        return RiskLevel.MINIMAL

    def generate(self, entity: Web4Entity) -> ComplianceReport:
        """Generate a full compliance report."""
        results = self.checker.check_entity(entity)
        risk_level = self.classify_risk(entity)

        # Group by article
        article_groups: Dict[AIActArticle, List[RequirementResult]] = defaultdict(list)
        for r in results:
            article_groups[r.article].append(r)

        article_results = {}
        total_passed = 0
        total_weighted = 0.0
        total_weight = 0.0
        remediation_items = []

        for article in AIActArticle:
            art_findings = article_groups.get(article, [])
            if not art_findings:
                continue

            reqs_passed = sum(1 for f in art_findings if f.passed)
            total_passed += reqs_passed

            # Weighted score
            art_reqs = self.checker.registry.get_article_requirements(article)
            art_weight = 0.0
            art_weighted_score = 0.0
            for i, finding in enumerate(art_findings):
                w = art_reqs[i].weight if i < len(art_reqs) else 1.0
                art_weighted_score += finding.score * w
                art_weight += w
            art_score = art_weighted_score / max(art_weight, 0.01)
            total_weighted += art_weighted_score
            total_weight += art_weight

            grade = self._score_to_grade(art_score)

            article_results[article.value] = ArticleResult(
                article=article,
                article_name=article.value,
                requirements_checked=len(art_findings),
                requirements_passed=reqs_passed,
                weighted_score=art_score,
                grade=grade,
                findings=art_findings,
            )

            # Collect remediations
            for f in art_findings:
                if not f.passed and f.remediation:
                    remediation_items.append({
                        "article": article.value,
                        "req_id": f.req_id,
                        "finding": f.finding,
                        "remediation": f.remediation,
                        "current_score": f"{f.score:.3f}",
                    })

        overall_score = total_weighted / max(total_weight, 0.01)
        overall_grade = self._score_to_grade(overall_score)

        report = ComplianceReport(
            report_id=secrets.token_hex(8),
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            risk_level=risk_level,
            overall_grade=overall_grade,
            overall_score=overall_score,
            article_results=article_results,
            total_requirements=len(results),
            passed_requirements=total_passed,
            remediation_items=remediation_items,
            generated_at=time.time(),
        )
        report.report_hash = self._hash_report(report)
        return report

    def _score_to_grade(self, score: float) -> ComplianceGrade:
        if score >= 0.95:
            return ComplianceGrade.FULL
        elif score >= 0.75:
            return ComplianceGrade.SUBSTANTIAL
        elif score >= 0.50:
            return ComplianceGrade.PARTIAL
        return ComplianceGrade.NON_COMPLIANT

    def _hash_report(self, report: ComplianceReport) -> str:
        content = f"{report.entity_id}:{report.overall_score}:{report.generated_at}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def format_text_report(self, report: ComplianceReport) -> str:
        """Format report as human-readable text."""
        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"EU AI ACT COMPLIANCE REPORT")
        lines.append(f"{'='*60}")
        lines.append(f"Entity:      {report.entity_id}")
        lines.append(f"Type:        {report.entity_type}")
        lines.append(f"Risk Level:  {report.risk_level.name}")
        lines.append(f"Grade:       {report.overall_grade.name}")
        lines.append(f"Score:       {report.overall_score:.1%}")
        lines.append(f"Passed:      {report.passed_requirements}/{report.total_requirements}")
        lines.append(f"Report ID:   {report.report_id}")
        lines.append(f"{'='*60}")
        lines.append("")

        for art_name, art_result in report.article_results.items():
            lines.append(f"--- {art_name} ({art_result.grade.name}) ---")
            lines.append(f"Score: {art_result.weighted_score:.1%} "
                         f"({art_result.requirements_passed}/{art_result.requirements_checked} passed)")
            for f in art_result.findings:
                status = "PASS" if f.passed else "FAIL"
                lines.append(f"  [{status}] {f.req_id}: {f.finding}")
                if not f.passed and f.remediation:
                    lines.append(f"         -> {f.remediation}")
            lines.append("")

        if report.remediation_items:
            lines.append(f"{'='*60}")
            lines.append(f"REMEDIATION SUMMARY ({len(report.remediation_items)} items)")
            lines.append(f"{'='*60}")
            for i, item in enumerate(report.remediation_items, 1):
                lines.append(f"{i}. [{item['article']}] {item['remediation']}")

        return "\n".join(lines)


# ─── Compliance Drift Detector ───────────────────────────────────────────────

@dataclass
class DriftEvent:
    """A detected compliance drift event."""
    entity_id: str
    article: str
    previous_score: float
    current_score: float
    delta: float
    direction: DriftDirection
    timestamp: float


class ComplianceDriftDetector:
    """
    Detect compliance score changes over time.
    Tracks historical scores and alerts on degradation.
    """

    def __init__(self, critical_drop_threshold: float = 0.15,
                 degradation_threshold: float = 0.05):
        self.critical_threshold = critical_drop_threshold
        self.degradation_threshold = degradation_threshold
        self.score_history: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        # entity_key → [(score, timestamp)]

    def record_scores(self, entity_id: str,
                        report: ComplianceReport):
        """Record scores from a compliance report."""
        # Overall
        key = f"{entity_id}:overall"
        self.score_history[key].append((report.overall_score, report.generated_at))

        # Per-article
        for art_name, art_result in report.article_results.items():
            key = f"{entity_id}:{art_name}"
            self.score_history[key].append(
                (art_result.weighted_score, report.generated_at))

    def detect_drift(self, entity_id: str) -> List[DriftEvent]:
        """Detect drift across all tracked dimensions."""
        events = []

        for key, history in self.score_history.items():
            if not key.startswith(f"{entity_id}:"):
                continue
            if len(history) < 2:
                continue

            article = key.split(":", 1)[1]
            prev_score, _ = history[-2]
            curr_score, curr_time = history[-1]
            delta = curr_score - prev_score

            if delta <= -self.critical_threshold:
                direction = DriftDirection.CRITICAL_DROP
            elif delta <= -self.degradation_threshold:
                direction = DriftDirection.DEGRADING
            elif delta >= self.degradation_threshold:
                direction = DriftDirection.IMPROVING
            else:
                direction = DriftDirection.STABLE

            if direction != DriftDirection.STABLE:
                events.append(DriftEvent(
                    entity_id=entity_id,
                    article=article,
                    previous_score=prev_score,
                    current_score=curr_score,
                    delta=delta,
                    direction=direction,
                    timestamp=curr_time,
                ))

        return events

    def get_trend(self, entity_id: str, article: str = "overall",
                    window: int = 5) -> Optional[DriftDirection]:
        """Get trend direction over last N measurements."""
        key = f"{entity_id}:{article}"
        history = self.score_history.get(key, [])
        if len(history) < 2:
            return None

        recent = history[-window:]
        if len(recent) < 2:
            return None

        scores = [s for s, _ in recent]
        total_delta = scores[-1] - scores[0]

        if total_delta <= -self.critical_threshold:
            return DriftDirection.CRITICAL_DROP
        elif total_delta <= -self.degradation_threshold:
            return DriftDirection.DEGRADING
        elif total_delta >= self.degradation_threshold:
            return DriftDirection.IMPROVING
        return DriftDirection.STABLE


# ─── Remediation Advisor ─────────────────────────────────────────────────────

@dataclass
class RemediationPlan:
    """Prioritized remediation plan for achieving compliance."""
    entity_id: str
    current_grade: ComplianceGrade
    target_grade: ComplianceGrade
    items: List[Dict[str, Any]]  # Sorted by priority
    estimated_score_improvement: float
    critical_items: int  # Number of items needed for next grade level


class RemediationAdvisor:
    """Generate prioritized remediation plans from compliance reports."""

    # Weight of each article for overall improvement
    ARTICLE_PRIORITIES = {
        "Risk Management System": 1.5,      # Art. 9 — foundational
        "Human Oversight": 1.3,              # Art. 14 — regulatory priority
        "Accuracy, Robustness, Cybersecurity": 1.2,  # Art. 15
        "Data and Data Governance": 1.1,     # Art. 10
        "Transparency and Information": 1.0, # Art. 13
        "Record-keeping": 0.9,              # Art. 12
        "Technical Documentation": 0.8,     # Art. 11
    }

    def generate_plan(self, report: ComplianceReport,
                        target_grade: ComplianceGrade = ComplianceGrade.SUBSTANTIAL
                        ) -> RemediationPlan:
        """Generate a prioritized remediation plan."""
        items = []

        for item in report.remediation_items:
            article_priority = self.ARTICLE_PRIORITIES.get(item["article"], 1.0)
            current_score = float(item["current_score"])
            gap = 0.5 - current_score  # Gap to minimum threshold
            priority_score = article_priority * max(gap, 0.1)

            items.append({
                "article": item["article"],
                "req_id": item["req_id"],
                "finding": item["finding"],
                "remediation": item["remediation"],
                "current_score": current_score,
                "priority": priority_score,
                "impact": "HIGH" if article_priority >= 1.2 else
                          "MEDIUM" if article_priority >= 1.0 else "LOW",
            })

        # Sort by priority (descending)
        items.sort(key=lambda x: x["priority"], reverse=True)

        # Estimate score improvement if all items addressed
        estimated_improvement = sum(
            max(0.5 - it["current_score"], 0) * 0.05 for it in items
        )

        # Count critical items for next grade
        grade_thresholds = {
            ComplianceGrade.FULL: 0.95,
            ComplianceGrade.SUBSTANTIAL: 0.75,
            ComplianceGrade.PARTIAL: 0.50,
            ComplianceGrade.NON_COMPLIANT: 0.0,
        }
        target_threshold = grade_thresholds.get(target_grade, 0.75)
        score_gap = target_threshold - report.overall_score
        critical_count = 0
        cumulative = 0.0
        for it in items:
            if cumulative >= score_gap:
                break
            cumulative += max(0.5 - it["current_score"], 0) * 0.05
            critical_count += 1

        return RemediationPlan(
            entity_id=report.entity_id,
            current_grade=report.overall_grade,
            target_grade=target_grade,
            items=items,
            estimated_score_improvement=estimated_improvement,
            critical_items=max(critical_count, 0),
        )


# ─── Compliance Timeline ────────────────────────────────────────────────────

@dataclass
class TimelineEntry:
    """A point in the compliance timeline."""
    timestamp: float
    overall_score: float
    grade: ComplianceGrade
    article_scores: Dict[str, float]
    events: List[str]  # Notable events at this point


class ComplianceTimeline:
    """Track compliance history over time."""

    def __init__(self):
        self.entries: Dict[str, List[TimelineEntry]] = defaultdict(list)

    def add_report(self, report: ComplianceReport, events: Optional[List[str]] = None):
        """Add a compliance report to the timeline."""
        art_scores = {name: ar.weighted_score
                      for name, ar in report.article_results.items()}
        entry = TimelineEntry(
            timestamp=report.generated_at,
            overall_score=report.overall_score,
            grade=report.overall_grade,
            article_scores=art_scores,
            events=events or [],
        )
        self.entries[report.entity_id].append(entry)

    def get_history(self, entity_id: str) -> List[TimelineEntry]:
        return self.entries.get(entity_id, [])

    def get_score_series(self, entity_id: str) -> List[Tuple[float, float]]:
        """Get (timestamp, score) pairs for plotting."""
        return [(e.timestamp, e.overall_score) for e in self.entries.get(entity_id, [])]

    def best_score(self, entity_id: str) -> float:
        history = self.entries.get(entity_id, [])
        if not history:
            return 0.0
        return max(e.overall_score for e in history)

    def worst_score(self, entity_id: str) -> float:
        history = self.entries.get(entity_id, [])
        if not history:
            return 0.0
        return min(e.overall_score for e in history)


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

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

    # ── Section 1: Article Registry ──────────────────────────────────────────

    registry = ArticleRegistry()
    check("s1_registry_populated", registry.total_requirements > 0,
          f"total={registry.total_requirements}")
    check("s1_all_articles", len(registry.requirements) == 7,
          f"articles={len(registry.requirements)}")
    check("s1_art9_requirements", len(registry.get_article_requirements(AIActArticle.ART_9)) == 3)
    check("s1_art15_requirements", len(registry.get_article_requirements(AIActArticle.ART_15)) == 3)

    all_reqs = registry.get_all_requirements()
    check("s1_total_count", len(all_reqs) == registry.total_requirements)

    # ── Section 2: Compliant Entity Assessment ───────────────────────────────

    good_entity = Web4Entity(
        entity_id="agent_good",
        entity_type="ai_agent",
        t3=T3Score(0.85, 0.82, 0.88),
        v3=V3Score(0.80, 0.85, 0.82),
        atp_balance=150.0,
        has_lct=True,
        has_hardware_binding=True,
        witnesses=8,
        fractal_chain_depth=2,
        human_oversight_enabled=True,
        attack_resistance_score=0.75,
        bias_audit_score=0.70,
        documentation_completeness=0.80,
    )

    checker = ComplianceChecker(registry)
    results_good = checker.check_entity(good_entity)
    check("s2_all_checked", len(results_good) == registry.total_requirements)
    passed_good = sum(1 for r in results_good if r.passed)
    check("s2_most_passed", passed_good >= registry.total_requirements * 0.8,
          f"passed={passed_good}/{registry.total_requirements}")

    # ── Section 3: Non-Compliant Entity ──────────────────────────────────────

    bad_entity = Web4Entity(
        entity_id="agent_bad",
        entity_type="ai_agent",
        t3=T3Score(0.2, 0.1, 0.15),
        v3=V3Score(0.1, 0.2, 0.1),
        atp_balance=5.0,
        has_lct=False,
        has_hardware_binding=False,
        witnesses=0,
        fractal_chain_depth=0,
        human_oversight_enabled=False,
        attack_resistance_score=0.05,
        bias_audit_score=0.1,
        documentation_completeness=0.1,
    )

    results_bad = checker.check_entity(bad_entity)
    passed_bad = sum(1 for r in results_bad if r.passed)
    check("s3_few_passed", passed_bad < registry.total_requirements * 0.5,
          f"passed={passed_bad}")
    check("s3_remediations", any(r.remediation for r in results_bad if not r.passed))

    # ── Section 4: Report Generation — Good Entity ───────────────────────────

    gen = ReportGenerator(checker)
    report_good = gen.generate(good_entity)

    check("s4_report_id", len(report_good.report_id) > 0)
    check("s4_entity_id", report_good.entity_id == "agent_good")
    check("s4_grade_good", report_good.overall_grade in [
        ComplianceGrade.FULL, ComplianceGrade.SUBSTANTIAL],
          f"grade={report_good.overall_grade}")
    check("s4_score_high", report_good.overall_score > 0.7,
          f"score={report_good.overall_score}")
    check("s4_all_articles_covered", len(report_good.article_results) == 7,
          f"articles={len(report_good.article_results)}")
    check("s4_report_hash", len(report_good.report_hash) == 32)

    # ── Section 5: Report Generation — Bad Entity ────────────────────────────

    report_bad = gen.generate(bad_entity)
    check("s5_grade_bad", report_bad.overall_grade == ComplianceGrade.NON_COMPLIANT,
          f"grade={report_bad.overall_grade}")
    check("s5_score_low", report_bad.overall_score < 0.3,
          f"score={report_bad.overall_score}")
    check("s5_has_remediations", len(report_bad.remediation_items) > 0,
          f"items={len(report_bad.remediation_items)}")
    check("s5_fewer_passed", report_bad.passed_requirements < report_good.passed_requirements)

    # ── Section 6: Risk Classification ───────────────────────────────────────

    high_risk = Web4Entity(entity_id="hr", entity_type="ai_agent",
                            annex_iii_category="biometrics")
    check("s6_biometrics_high", gen.classify_risk(high_risk) == RiskLevel.HIGH)

    limited_risk = Web4Entity(entity_id="lr", entity_type="ai_agent",
                                annex_iii_category="not_high_risk")
    check("s6_agent_limited", gen.classify_risk(limited_risk) == RiskLevel.LIMITED)

    minimal_risk = Web4Entity(entity_id="mr", entity_type="sensor",
                                annex_iii_category="not_high_risk")
    check("s6_sensor_minimal", gen.classify_risk(minimal_risk) == RiskLevel.MINIMAL)

    law_enf = Web4Entity(entity_id="le", entity_type="ai_agent",
                           annex_iii_category="law_enforcement")
    check("s6_law_enforcement_high", gen.classify_risk(law_enf) == RiskLevel.HIGH)

    # ── Section 7: Text Report Format ────────────────────────────────────────

    text = gen.format_text_report(report_good)
    check("s7_has_header", "EU AI ACT COMPLIANCE REPORT" in text)
    check("s7_has_entity", "agent_good" in text)
    check("s7_has_grade", report_good.overall_grade.name in text)
    check("s7_has_articles", "Risk Management System" in text)
    check("s7_has_pass_fail", "[PASS]" in text or "[FAIL]" in text)

    text_bad = gen.format_text_report(report_bad)
    check("s7_bad_has_remediation", "REMEDIATION SUMMARY" in text_bad)

    # ── Section 8: Compliance Drift Detection ────────────────────────────────

    drift = ComplianceDriftDetector(critical_drop_threshold=0.15,
                                     degradation_threshold=0.05)

    # Record improving scores (larger deltas to avoid float threshold edge cases)
    entity_id = "drift_test"
    for score in [0.4, 0.5, 0.6, 0.7, 0.8]:
        report = ComplianceReport(
            report_id=secrets.token_hex(4),
            entity_id=entity_id,
            entity_type="ai_agent",
            risk_level=RiskLevel.LIMITED,
            overall_grade=ComplianceGrade.PARTIAL,
            overall_score=score,
            article_results={},
            total_requirements=16,
            passed_requirements=int(score * 16),
            remediation_items=[],
            generated_at=time.time(),
        )
        drift.record_scores(entity_id, report)

    events = drift.detect_drift(entity_id)
    improving = [e for e in events if e.direction == DriftDirection.IMPROVING]
    check("s8_improving_detected", len(improving) > 0)

    trend = drift.get_trend(entity_id)
    check("s8_improving_trend", trend == DriftDirection.IMPROVING,
          f"trend={trend}")

    # ── Section 9: Drift — Degradation ───────────────────────────────────────

    drift2 = ComplianceDriftDetector()
    entity_id2 = "degrading_test"
    for score in [0.8, 0.75, 0.70, 0.65, 0.60]:
        report = ComplianceReport(
            report_id=secrets.token_hex(4),
            entity_id=entity_id2,
            entity_type="ai_agent",
            risk_level=RiskLevel.LIMITED,
            overall_grade=ComplianceGrade.PARTIAL,
            overall_score=score,
            article_results={},
            total_requirements=16,
            passed_requirements=int(score * 16),
            remediation_items=[],
            generated_at=time.time(),
        )
        drift2.record_scores(entity_id2, report)

    events2 = drift2.detect_drift(entity_id2)
    degrading = [e for e in events2 if e.direction == DriftDirection.DEGRADING]
    check("s9_degrading_detected", len(degrading) > 0,
          f"degrading={len(degrading)}")

    trend2 = drift2.get_trend(entity_id2)
    check("s9_degrading_trend", trend2 in [
        DriftDirection.DEGRADING, DriftDirection.CRITICAL_DROP],
          f"trend={trend2}")

    # ── Section 10: Drift — Critical Drop ────────────────────────────────────

    drift3 = ComplianceDriftDetector()
    entity_id3 = "critical_test"
    for score in [0.8, 0.5]:  # 0.3 drop
        report = ComplianceReport(
            report_id=secrets.token_hex(4),
            entity_id=entity_id3,
            entity_type="ai_agent",
            risk_level=RiskLevel.LIMITED,
            overall_grade=ComplianceGrade.PARTIAL,
            overall_score=score,
            article_results={},
            total_requirements=16,
            passed_requirements=int(score * 16),
            remediation_items=[],
            generated_at=time.time(),
        )
        drift3.record_scores(entity_id3, report)

    events3 = drift3.detect_drift(entity_id3)
    critical = [e for e in events3 if e.direction == DriftDirection.CRITICAL_DROP]
    check("s10_critical_drop", len(critical) > 0)

    # ── Section 11: Remediation Advisor ──────────────────────────────────────

    advisor = RemediationAdvisor()
    plan = advisor.generate_plan(report_bad)

    check("s11_plan_entity", plan.entity_id == "agent_bad")
    check("s11_has_items", len(plan.items) > 0, f"items={len(plan.items)}")
    check("s11_sorted_priority", all(
        plan.items[i]["priority"] >= plan.items[i+1]["priority"]
        for i in range(len(plan.items) - 1)))
    check("s11_current_grade", plan.current_grade == ComplianceGrade.NON_COMPLIANT)
    check("s11_target_grade", plan.target_grade == ComplianceGrade.SUBSTANTIAL)

    # ── Section 12: Remediation — Good Entity Has Few Items ──────────────────

    plan_good = advisor.generate_plan(report_good)
    check("s12_fewer_items", len(plan_good.items) <= len(plan.items),
          f"good={len(plan_good.items)}, bad={len(plan.items)}")

    # ── Section 13: Compliance Timeline ──────────────────────────────────────

    timeline = ComplianceTimeline()
    reports_seq = []
    for score in [0.4, 0.55, 0.65, 0.72, 0.80]:
        r = ComplianceReport(
            report_id=secrets.token_hex(4),
            entity_id="timeline_ent",
            entity_type="ai_agent",
            risk_level=RiskLevel.LIMITED,
            overall_grade=ComplianceGrade.PARTIAL,
            overall_score=score,
            article_results={
                "Risk Management System": ArticleResult(
                    article=AIActArticle.ART_9,
                    article_name="Risk Management System",
                    requirements_checked=3,
                    requirements_passed=2,
                    weighted_score=score + 0.05,
                    grade=ComplianceGrade.PARTIAL,
                    findings=[],
                )
            },
            total_requirements=16,
            passed_requirements=int(score * 16),
            remediation_items=[],
            generated_at=time.time(),
        )
        timeline.add_report(r, events=["Score improved"])
        reports_seq.append(r)

    history = timeline.get_history("timeline_ent")
    check("s13_history_length", len(history) == 5)

    series = timeline.get_score_series("timeline_ent")
    check("s13_series_length", len(series) == 5)
    check("s13_scores_increasing", all(
        series[i][1] <= series[i+1][1] for i in range(len(series) - 1)))

    check("s13_best_score", timeline.best_score("timeline_ent") == 0.80)
    check("s13_worst_score", timeline.worst_score("timeline_ent") == 0.40)

    # ── Section 14: Timeline — Empty Entity ──────────────────────────────────

    check("s14_no_history", len(timeline.get_history("nonexistent")) == 0)
    check("s14_best_zero", timeline.best_score("nonexistent") == 0.0)

    # ── Section 15: Multiple Entities ────────────────────────────────────────

    entities = []
    for i in range(10):
        t = 0.3 + i * 0.07
        ent = Web4Entity(
            entity_id=f"batch_{i}",
            entity_type="ai_agent",
            t3=T3Score(t, t - 0.05, t + 0.02),
            v3=V3Score(t - 0.1, t, t + 0.05),
            atp_balance=50.0 + i * 20,
            has_lct=True,
            has_hardware_binding=i >= 5,
            witnesses=i * 2,
            fractal_chain_depth=min(i, 3),
            human_oversight_enabled=i >= 3,
            attack_resistance_score=t * 0.8,
            bias_audit_score=t * 0.7,
            documentation_completeness=t * 0.9,
        )
        entities.append(ent)

    reports = [gen.generate(e) for e in entities]
    scores = [r.overall_score for r in reports]

    check("s15_10_reports", len(reports) == 10)
    check("s15_scores_vary", max(scores) - min(scores) > 0.2,
          f"range={max(scores)-min(scores):.3f}")
    check("s15_higher_trust_better", scores[-1] > scores[0],
          f"last={scores[-1]:.3f}, first={scores[0]:.3f}")

    grades = [r.overall_grade for r in reports]
    check("s15_grade_distribution", len(set(grades)) >= 2,
          f"grades={set(g.name for g in grades)}")

    # ── Section 16: Performance — 100 Entity Assessments ─────────────────────

    t0 = time.time()
    for i in range(100):
        ent = Web4Entity(
            entity_id=f"perf_{i}",
            entity_type="ai_agent",
            t3=T3Score(0.5, 0.5, 0.5),
            v3=V3Score(0.5, 0.5, 0.5),
            atp_balance=100.0,
            witnesses=3,
            human_oversight_enabled=True,
            attack_resistance_score=0.5,
            bias_audit_score=0.5,
            documentation_completeness=0.5,
        )
        gen.generate(ent)
    elapsed = time.time() - t0
    check("s16_100_assessments_fast", elapsed < 5.0, f"elapsed={elapsed:.2f}s")

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
