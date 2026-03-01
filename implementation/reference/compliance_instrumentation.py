"""
Compliance Instrumentation & Audit Pipeline — Session 22 Track 3
================================================================
EU AI Act article mapping, live compliance monitoring, bias detection,
explainability binding, and multi-party audit protocols.

Sections:
  S1:  EU AI Act Article Registry
  S2:  Compliance Observable
  S3:  Bias Detection Engine
  S4:  Explainability Binding
  S5:  Audit Trail Generation
  S6:  Multi-Party Audit Protocol
  S7:  Compliance Certification
  S8:  Risk Management Pipeline
  S9:  Live Compliance Dashboard
  S10: Remediation Tracking
  S11: Performance
"""

from __future__ import annotations
import enum
import hashlib
import hmac
import math
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ── S1: EU AI Act Article Registry ────────────────────────────────────

class AIActArticle(enum.Enum):
    ART_9 = "art_9"    # Risk Management System
    ART_10 = "art_10"  # Data and Data Governance
    ART_11 = "art_11"  # Technical Documentation
    ART_12 = "art_12"  # Record-keeping
    ART_13 = "art_13"  # Transparency and Info to Deployers
    ART_14 = "art_14"  # Human Oversight
    ART_15 = "art_15"  # Accuracy, Robustness, Cybersecurity


class ComplianceLevel(enum.Enum):
    FULL = "full"               # All requirements met
    SUBSTANTIAL = "substantial" # Most requirements met (≥75%)
    PARTIAL = "partial"         # Some requirements met (≥50%)
    NON_COMPLIANT = "non_compliant"  # Below 50%


@dataclass
class ArticleRequirement:
    article: AIActArticle
    requirement_id: str
    description: str
    web4_mechanism: str  # Which Web4 component satisfies this
    weight: float = 1.0  # Importance weight


@dataclass
class ArticleSpec:
    article: AIActArticle
    title: str
    requirements: List[ArticleRequirement] = field(default_factory=list)


def build_article_registry() -> Dict[AIActArticle, ArticleSpec]:
    registry = {}

    # Article 9: Risk Management
    art9 = ArticleSpec(AIActArticle.ART_9, "Risk Management System")
    art9.requirements = [
        ArticleRequirement(AIActArticle.ART_9, "9.1", "Establish risk management system", "T3 tensor monitoring"),
        ArticleRequirement(AIActArticle.ART_9, "9.2a", "Identify and analyze known risks", "Attack surface analysis"),
        ArticleRequirement(AIActArticle.ART_9, "9.2b", "Estimate and evaluate residual risks", "Trust score tracking"),
        ArticleRequirement(AIActArticle.ART_9, "9.3", "Eliminate or reduce risks", "Circuit breaker + freeze"),
        ArticleRequirement(AIActArticle.ART_9, "9.4", "Testing and risk mitigation measures", "458+ attack simulations"),
    ]
    registry[AIActArticle.ART_9] = art9

    # Article 10: Data Governance
    art10 = ArticleSpec(AIActArticle.ART_10, "Data and Data Governance")
    art10.requirements = [
        ArticleRequirement(AIActArticle.ART_10, "10.2", "Data governance practices", "V3 tensor (Veracity)"),
        ArticleRequirement(AIActArticle.ART_10, "10.3", "Training data relevance", "MRH context scoping"),
        ArticleRequirement(AIActArticle.ART_10, "10.4", "Examine for biases", "Bias detection engine"),
        ArticleRequirement(AIActArticle.ART_10, "10.5", "Free of errors", "LCT validation chain"),
    ]
    registry[AIActArticle.ART_10] = art10

    # Article 11: Technical Documentation
    art11 = ArticleSpec(AIActArticle.ART_11, "Technical Documentation")
    art11.requirements = [
        ArticleRequirement(AIActArticle.ART_11, "11.1", "Up-to-date technical documentation", "LCT lifecycle docs"),
        ArticleRequirement(AIActArticle.ART_11, "11.2", "Documentation accessibility", "Schema evolution"),
    ]
    registry[AIActArticle.ART_11] = art11

    # Article 12: Record-keeping
    art12 = ArticleSpec(AIActArticle.ART_12, "Record-keeping")
    art12.requirements = [
        ArticleRequirement(AIActArticle.ART_12, "12.1", "Automatic logging of events", "Hash-chained audit trail"),
        ArticleRequirement(AIActArticle.ART_12, "12.2", "Traceability of operation", "Distributed tracing"),
        ArticleRequirement(AIActArticle.ART_12, "12.3", "Log retention and integrity", "Tamper-evident log"),
    ]
    registry[AIActArticle.ART_12] = art12

    # Article 13: Transparency
    art13 = ArticleSpec(AIActArticle.ART_13, "Transparency and Information to Deployers")
    art13.requirements = [
        ArticleRequirement(AIActArticle.ART_13, "13.1", "Transparency of operation", "Explainability binding"),
        ArticleRequirement(AIActArticle.ART_13, "13.2", "Instructions for use", "SDK documentation"),
        ArticleRequirement(AIActArticle.ART_13, "13.3a", "Intended purpose", "Entity role specification"),
    ]
    registry[AIActArticle.ART_13] = art13

    # Article 14: Human Oversight
    art14 = ArticleSpec(AIActArticle.ART_14, "Human Oversight")
    art14.requirements = [
        ArticleRequirement(AIActArticle.ART_14, "14.1", "Designed for human oversight", "SAL framework"),
        ArticleRequirement(AIActArticle.ART_14, "14.2", "Ability to override decisions", "Emergency freeze"),
        ArticleRequirement(AIActArticle.ART_14, "14.3", "Oversight during operation", "Live dashboard"),
    ]
    registry[AIActArticle.ART_14] = art14

    # Article 15: Accuracy, Robustness, Cybersecurity
    art15 = ArticleSpec(AIActArticle.ART_15, "Accuracy, Robustness, Cybersecurity")
    art15.requirements = [
        ArticleRequirement(AIActArticle.ART_15, "15.1", "Appropriate level of accuracy", "T3 trust accuracy"),
        ArticleRequirement(AIActArticle.ART_15, "15.2", "Resilient to errors", "Fault injection testing"),
        ArticleRequirement(AIActArticle.ART_15, "15.3", "Cybersecurity measures", "Hardware binding + TPM"),
        ArticleRequirement(AIActArticle.ART_15, "15.4", "Redundancy for safety", "Federation consensus"),
    ]
    registry[AIActArticle.ART_15] = art15

    return registry


# ── S2: Compliance Observable ─────────────────────────────────────────

@dataclass
class ComplianceObservation:
    article: AIActArticle
    requirement_id: str
    status: ComplianceLevel
    evidence: str
    timestamp: float = field(default_factory=time.time)
    entity_id: Optional[str] = None
    score: float = 1.0  # 0.0-1.0 compliance score


class ComplianceObservable:
    """Collects and evaluates compliance observations."""

    def __init__(self):
        self.observations: List[ComplianceObservation] = []
        self.listeners: List[Callable[[ComplianceObservation], None]] = []

    def observe(self, obs: ComplianceObservation):
        self.observations.append(obs)
        for listener in self.listeners:
            listener(obs)

    def subscribe(self, listener: Callable[[ComplianceObservation], None]):
        self.listeners.append(listener)

    def article_score(self, article: AIActArticle) -> float:
        article_obs = [o for o in self.observations if o.article == article]
        if not article_obs:
            return 0.0
        return sum(o.score for o in article_obs) / len(article_obs)

    def overall_level(self) -> ComplianceLevel:
        if not self.observations:
            return ComplianceLevel.NON_COMPLIANT
        avg = sum(o.score for o in self.observations) / len(self.observations)
        if avg >= 0.9:
            return ComplianceLevel.FULL
        elif avg >= 0.75:
            return ComplianceLevel.SUBSTANTIAL
        elif avg >= 0.5:
            return ComplianceLevel.PARTIAL
        return ComplianceLevel.NON_COMPLIANT

    def by_entity(self, entity_id: str) -> List[ComplianceObservation]:
        return [o for o in self.observations if o.entity_id == entity_id]

    def non_compliant_areas(self) -> List[Tuple[AIActArticle, str, float]]:
        """Return (article, requirement_id, score) for failing requirements."""
        req_scores: Dict[Tuple[AIActArticle, str], List[float]] = {}
        for o in self.observations:
            key = (o.article, o.requirement_id)
            req_scores.setdefault(key, []).append(o.score)
        result = []
        for (art, req_id), scores in req_scores.items():
            avg = sum(scores) / len(scores)
            if avg < 0.5:
                result.append((art, req_id, avg))
        return result


# ── S3: Bias Detection Engine ────────────────────────────────────────

@dataclass
class ProtectedGroup:
    attribute: str   # e.g., "region", "org_size"
    value: str       # e.g., "EU", "small"
    count: int = 0
    positive_outcomes: int = 0

    @property
    def positive_rate(self) -> float:
        if self.count == 0:
            return 0.0
        return self.positive_outcomes / self.count


@dataclass
class BiasReport:
    attribute: str
    groups: Dict[str, ProtectedGroup]
    disparate_impact_ratios: Dict[Tuple[str, str], float]
    biased_pairs: List[Tuple[str, str, float]]  # (group_a, group_b, ratio)
    overall_fair: bool


class BiasDetector:
    """Detects disparate impact across protected attributes (4/5ths rule)."""

    THRESHOLD = 0.8  # 4/5ths rule

    def __init__(self):
        self.groups: Dict[str, Dict[str, ProtectedGroup]] = {}

    def record_outcome(self, attribute: str, value: str, positive: bool):
        if attribute not in self.groups:
            self.groups[attribute] = {}
        if value not in self.groups[attribute]:
            self.groups[attribute][value] = ProtectedGroup(attribute, value)
        group = self.groups[attribute][value]
        group.count += 1
        if positive:
            group.positive_outcomes += 1

    def analyze(self, attribute: str) -> BiasReport:
        groups = self.groups.get(attribute, {})
        ratios: Dict[Tuple[str, str], float] = {}
        biased: List[Tuple[str, str, float]] = []

        group_names = list(groups.keys())
        for i, g1 in enumerate(group_names):
            for g2 in group_names[i + 1:]:
                rate1 = groups[g1].positive_rate
                rate2 = groups[g2].positive_rate
                if rate2 > 0:
                    ratio = rate1 / rate2
                    ratios[(g1, g2)] = ratio
                    if ratio < self.THRESHOLD:
                        biased.append((g1, g2, ratio))
                if rate1 > 0:
                    ratio_rev = rate2 / rate1
                    ratios[(g2, g1)] = ratio_rev
                    if ratio_rev < self.THRESHOLD:
                        biased.append((g2, g1, ratio_rev))

        return BiasReport(
            attribute, groups, ratios, biased,
            overall_fair=len(biased) == 0
        )


# ── S4: Explainability Binding ────────────────────────────────────────

@dataclass
class TrustDelta:
    entity_id: str
    dimension: str     # "talent", "training", "temperament"
    old_value: float
    new_value: float
    change: float
    timestamp: float


@dataclass
class ExplainableAction:
    action_id: str
    action_type: str   # e.g., "delegation", "revocation", "trust_update"
    entity_id: str
    timestamp: float
    trust_deltas: List[TrustDelta] = field(default_factory=list)
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)
    r6_reference: Optional[str] = None  # R6 action reference


class ExplainabilityEngine:
    """Binds T3 tensor changes to specific actions with reasoning."""

    def __init__(self):
        self.actions: List[ExplainableAction] = []
        self.entity_history: Dict[str, List[TrustDelta]] = {}

    def record_action(self, action: ExplainableAction):
        self.actions.append(action)
        for delta in action.trust_deltas:
            self.entity_history.setdefault(delta.entity_id, []).append(delta)

    def explain_entity(self, entity_id: str) -> List[ExplainableAction]:
        return [a for a in self.actions if a.entity_id == entity_id]

    def explain_change(self, entity_id: str, dimension: str,
                       since: float = 0.0) -> List[TrustDelta]:
        deltas = self.entity_history.get(entity_id, [])
        return [d for d in deltas
                if d.dimension == dimension and d.timestamp >= since]

    def cumulative_change(self, entity_id: str, dimension: str) -> float:
        deltas = self.entity_history.get(entity_id, [])
        return sum(d.change for d in deltas if d.dimension == dimension)

    def audit_trail(self, entity_id: str) -> List[Dict[str, Any]]:
        """Full audit trail for an entity's trust changes."""
        trail = []
        for action in self.actions:
            if action.entity_id == entity_id:
                trail.append({
                    "action_id": action.action_id,
                    "type": action.action_type,
                    "timestamp": action.timestamp,
                    "reasoning": action.reasoning,
                    "deltas": [(d.dimension, d.change) for d in action.trust_deltas],
                    "evidence_count": len(action.evidence),
                })
        return trail


# ── S5: Audit Trail Generation ───────────────────────────────────────

@dataclass
class AuditEntry:
    entry_id: str
    timestamp: float
    event_type: str
    entity_id: str
    details: Dict[str, Any]
    content_hash: str = ""
    prev_hash: str = ""
    hmac_signature: str = ""

    def compute_hash(self) -> str:
        content = f"{self.entry_id}:{self.timestamp}:{self.event_type}:{self.entity_id}:{self.details}"
        return hashlib.sha256(content.encode()).hexdigest()


class AuditTrail:
    """Hash-chained, HMAC-signed audit trail."""

    def __init__(self, signing_key: bytes = b"audit_key"):
        self.entries: List[AuditEntry] = []
        self.signing_key = signing_key
        self.prev_hash = "genesis"

    def append(self, event_type: str, entity_id: str,
               details: Dict[str, Any]) -> AuditEntry:
        entry = AuditEntry(
            entry_id=secrets.token_hex(8),
            timestamp=time.time(),
            event_type=event_type,
            entity_id=entity_id,
            details=details,
        )
        entry.content_hash = entry.compute_hash()
        entry.prev_hash = self.prev_hash
        chain_data = f"{entry.content_hash}:{entry.prev_hash}"
        entry.hmac_signature = hmac.new(
            self.signing_key, chain_data.encode(), hashlib.sha256
        ).hexdigest()
        self.prev_hash = entry.content_hash
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> Tuple[bool, List[str]]:
        errors = []
        prev = "genesis"
        for i, entry in enumerate(self.entries):
            expected_hash = entry.compute_hash()
            if entry.content_hash != expected_hash:
                errors.append(f"Entry {i}: content hash mismatch")
            if entry.prev_hash != prev:
                errors.append(f"Entry {i}: chain break (prev_hash mismatch)")
            chain_data = f"{entry.content_hash}:{entry.prev_hash}"
            expected_sig = hmac.new(
                self.signing_key, chain_data.encode(), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(entry.hmac_signature, expected_sig):
                errors.append(f"Entry {i}: HMAC signature invalid")
            prev = entry.content_hash
        return len(errors) == 0, errors

    def entries_for_entity(self, entity_id: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.entity_id == entity_id]


# ── S6: Multi-Party Audit Protocol ───────────────────────────────────

@dataclass
class Auditor:
    auditor_id: str
    trust_score: float
    completed_audits: int = 0
    accuracy_rate: float = 1.0
    stake: float = 50.0


@dataclass
class AuditVote:
    auditor_id: str
    compliance_level: ComplianceLevel
    confidence: float
    findings: List[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class AuditResult:
    target_entity: str
    votes: List[AuditVote]
    consensus_level: Optional[ComplianceLevel]
    quorum_met: bool
    agreement_ratio: float


class MultiPartyAudit:
    """M-of-N quorum audit with consensus on compliance level."""

    def __init__(self, required_quorum: float = 2 / 3):
        self.required_quorum = required_quorum
        self.auditors: Dict[str, Auditor] = {}
        self.results: List[AuditResult] = []

    def register_auditor(self, auditor: Auditor):
        self.auditors[auditor.auditor_id] = auditor

    def submit_vote(self, target: str, vote: AuditVote) -> bool:
        if vote.auditor_id not in self.auditors:
            return False
        # Find or create result for target
        result = None
        for r in self.results:
            if r.target_entity == target and r.consensus_level is None:
                result = r
                break
        if result is None:
            result = AuditResult(target, [], None, False, 0.0)
            self.results.append(result)
        result.votes.append(vote)
        return True

    def evaluate(self, target: str) -> Optional[AuditResult]:
        result = None
        for r in self.results:
            if r.target_entity == target:
                result = r
                break
        if not result or not result.votes:
            return None

        n_auditors = len(self.auditors)
        n_votes = len(result.votes)
        result.quorum_met = n_votes >= math.ceil(n_auditors * self.required_quorum)

        if not result.quorum_met:
            return result

        # Majority vote on compliance level
        level_votes: Dict[ComplianceLevel, float] = {}
        for vote in result.votes:
            auditor = self.auditors.get(vote.auditor_id)
            weight = auditor.trust_score if auditor else 0.5
            level_votes[vote.compliance_level] = (
                level_votes.get(vote.compliance_level, 0.0) + weight
            )

        total_weight = sum(level_votes.values())
        if total_weight > 0:
            best_level = max(level_votes, key=lambda l: level_votes[l])
            result.consensus_level = best_level
            result.agreement_ratio = level_votes[best_level] / total_weight

        return result


# ── S7: Compliance Certification ─────────────────────────────────────

@dataclass
class ComplianceCertificate:
    cert_id: str
    entity_id: str
    level: ComplianceLevel
    articles_covered: List[AIActArticle]
    issued_at: float
    expires_at: float
    issuer_id: str
    audit_result_hash: str
    signature: str = ""
    revoked: bool = False

    def is_valid(self, current_time: float) -> bool:
        return (not self.revoked and
                self.issued_at <= current_time <= self.expires_at)


class CertificationAuthority:
    """Issues and manages compliance certificates."""

    def __init__(self, authority_id: str, signing_key: bytes = b"ca_key"):
        self.authority_id = authority_id
        self.signing_key = signing_key
        self.certificates: Dict[str, ComplianceCertificate] = {}

    def issue(self, entity_id: str, level: ComplianceLevel,
              articles: List[AIActArticle],
              audit_hash: str,
              validity_days: int = 365) -> ComplianceCertificate:
        now = time.time()
        cert = ComplianceCertificate(
            cert_id=secrets.token_hex(16),
            entity_id=entity_id,
            level=level,
            articles_covered=articles,
            issued_at=now,
            expires_at=now + validity_days * 86400,
            issuer_id=self.authority_id,
            audit_result_hash=audit_hash,
        )
        # Sign
        sign_data = f"{cert.cert_id}:{cert.entity_id}:{cert.level.value}:{audit_hash}"
        cert.signature = hmac.new(
            self.signing_key, sign_data.encode(), hashlib.sha256
        ).hexdigest()
        self.certificates[cert.cert_id] = cert
        return cert

    def verify(self, cert: ComplianceCertificate) -> bool:
        sign_data = f"{cert.cert_id}:{cert.entity_id}:{cert.level.value}:{cert.audit_result_hash}"
        expected = hmac.new(
            self.signing_key, sign_data.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(cert.signature, expected)

    def revoke(self, cert_id: str) -> bool:
        cert = self.certificates.get(cert_id)
        if cert:
            cert.revoked = True
            return True
        return False

    def active_certs(self, entity_id: str,
                     current_time: float) -> List[ComplianceCertificate]:
        return [c for c in self.certificates.values()
                if c.entity_id == entity_id and c.is_valid(current_time)]


# ── S8: Risk Management Pipeline ─────────────────────────────────────

class RiskLevel(enum.Enum):
    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"


@dataclass
class RiskAssessment:
    entity_id: str
    risk_level: RiskLevel
    risk_factors: Dict[str, float]  # factor_name → severity
    mitigations: List[str]
    residual_risk: float  # After mitigations
    timestamp: float = field(default_factory=time.time)


class RiskPipeline:
    """Continuous risk assessment pipeline per Art. 9."""

    def __init__(self):
        self.assessments: List[RiskAssessment] = []
        self.risk_thresholds = {
            RiskLevel.MINIMAL: 0.2,
            RiskLevel.LIMITED: 0.4,
            RiskLevel.HIGH: 0.7,
            RiskLevel.UNACCEPTABLE: 1.0,
        }

    def assess(self, entity_id: str, trust_score: float,
               attack_surface: int, has_hardware_binding: bool,
               witness_count: int) -> RiskAssessment:
        factors: Dict[str, float] = {}

        # Trust-based risk (low trust = high risk)
        factors["trust_deficit"] = max(0, 1.0 - trust_score)

        # Attack surface exposure
        factors["attack_surface"] = min(1.0, attack_surface / 100)

        # Hardware binding (absence = risk)
        factors["no_hardware"] = 0.0 if has_hardware_binding else 0.5

        # Witness coverage (few witnesses = risk)
        factors["low_witnesses"] = max(0, 1.0 - witness_count / 5)

        # Aggregate
        raw_risk = sum(factors.values()) / len(factors)

        # Mitigations reduce residual risk
        mitigations = []
        mitigation_effect = 0.0
        if has_hardware_binding:
            mitigations.append("hardware_bound")
            mitigation_effect += 0.15
        if trust_score > 0.7:
            mitigations.append("high_trust")
            mitigation_effect += 0.1
        if witness_count >= 3:
            mitigations.append("well_witnessed")
            mitigation_effect += 0.1

        residual = max(0, raw_risk - mitigation_effect)

        # Classify
        risk_level = RiskLevel.MINIMAL
        for level, threshold in sorted(self.risk_thresholds.items(),
                                       key=lambda x: x[1]):
            if residual <= threshold:
                risk_level = level
                break

        assessment = RiskAssessment(
            entity_id, risk_level, factors, mitigations, residual
        )
        self.assessments.append(assessment)
        return assessment

    def entity_risk_trend(self, entity_id: str) -> List[float]:
        return [a.residual_risk for a in self.assessments
                if a.entity_id == entity_id]


# ── S9: Live Compliance Dashboard ─────────────────────────────────────

@dataclass
class DashboardSnapshot:
    timestamp: float
    overall_level: ComplianceLevel
    article_scores: Dict[str, float]  # article_name → score
    non_compliant_count: int
    active_certs: int
    risk_distribution: Dict[str, int]  # risk_level → count
    recent_events: List[str]


class ComplianceDashboard:
    """Aggregates compliance data into dashboard snapshots."""

    def __init__(self):
        self.snapshots: List[DashboardSnapshot] = []

    def create_snapshot(
        self,
        observable: ComplianceObservable,
        cert_authority: CertificationAuthority,
        risk_pipeline: RiskPipeline,
        current_time: float,
    ) -> DashboardSnapshot:
        # Article scores
        article_scores = {}
        for article in AIActArticle:
            score = observable.article_score(article)
            article_scores[article.value] = score

        # Non-compliant areas
        non_compliant = observable.non_compliant_areas()

        # Active certificates
        active = sum(1 for c in cert_authority.certificates.values()
                     if c.is_valid(current_time))

        # Risk distribution
        risk_dist: Dict[str, int] = {}
        for a in risk_pipeline.assessments:
            risk_dist[a.risk_level.value] = risk_dist.get(a.risk_level.value, 0) + 1

        # Recent events
        recent = [f"{o.article.value}:{o.requirement_id} ({o.status.value})"
                  for o in observable.observations[-5:]]

        snapshot = DashboardSnapshot(
            current_time, observable.overall_level(),
            article_scores, len(non_compliant), active,
            risk_dist, recent
        )
        self.snapshots.append(snapshot)
        return snapshot

    def compliance_trend(self) -> List[Tuple[float, str]]:
        return [(s.timestamp, s.overall_level.value) for s in self.snapshots]


# ── S10: Remediation Tracking ─────────────────────────────────────────

class RemediationStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"


@dataclass
class RemediationItem:
    item_id: str
    article: AIActArticle
    requirement_id: str
    description: str
    priority: int  # 1=critical, 2=high, 3=medium, 4=low
    status: RemediationStatus = RemediationStatus.OPEN
    assigned_to: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None


class RemediationTracker:
    """Tracks compliance remediation items."""

    def __init__(self):
        self.items: Dict[str, RemediationItem] = {}

    def create(self, article: AIActArticle, requirement_id: str,
               description: str, priority: int = 3) -> RemediationItem:
        item = RemediationItem(
            item_id=secrets.token_hex(8),
            article=article,
            requirement_id=requirement_id,
            description=description,
            priority=priority,
        )
        self.items[item.item_id] = item
        return item

    def resolve(self, item_id: str) -> bool:
        item = self.items.get(item_id)
        if item:
            item.status = RemediationStatus.RESOLVED
            item.resolved_at = time.time()
            return True
        return False

    def open_items(self) -> List[RemediationItem]:
        return [i for i in self.items.values()
                if i.status in (RemediationStatus.OPEN, RemediationStatus.IN_PROGRESS)]

    def by_priority(self) -> Dict[int, List[RemediationItem]]:
        result: Dict[int, List[RemediationItem]] = {}
        for item in self.items.values():
            result.setdefault(item.priority, []).append(item)
        return result

    def resolution_rate(self) -> float:
        if not self.items:
            return 0.0
        resolved = sum(1 for i in self.items.values()
                       if i.status == RemediationStatus.RESOLVED)
        return resolved / len(self.items)


# ── S11: Performance ──────────────────────────────────────────────────

def run_checks():
    checks: List[Tuple[str, bool]] = []

    # ── S1: EU AI Act Article Registry ────────────────────────────────
    registry = build_article_registry()
    checks.append(("s1_all_articles", len(registry) == 7))

    art9 = registry[AIActArticle.ART_9]
    checks.append(("s1_art9_reqs", len(art9.requirements) >= 4))
    checks.append(("s1_art9_mechanisms", all(r.web4_mechanism for r in art9.requirements)))

    total_reqs = sum(len(a.requirements) for a in registry.values())
    checks.append(("s1_total_reqs", total_reqs >= 20))

    # ── S2: Compliance Observable ─────────────────────────────────────
    observable = ComplianceObservable()

    # Record good observations
    for article in [AIActArticle.ART_9, AIActArticle.ART_10, AIActArticle.ART_12]:
        observable.observe(ComplianceObservation(
            article, "test_req", ComplianceLevel.FULL,
            "Implemented", entity_id="entity_1", score=0.95
        ))

    # Record poor observation
    observable.observe(ComplianceObservation(
        AIActArticle.ART_13, "13.1", ComplianceLevel.NON_COMPLIANT,
        "Not implemented", entity_id="entity_1", score=0.2
    ))

    checks.append(("s2_observation_count", len(observable.observations) == 4))
    checks.append(("s2_art9_score", observable.article_score(AIActArticle.ART_9) > 0.9))
    checks.append(("s2_non_compliant", len(observable.non_compliant_areas()) > 0))
    checks.append(("s2_by_entity", len(observable.by_entity("entity_1")) == 4))

    # Listener
    listener_calls = []
    observable.subscribe(lambda o: listener_calls.append(o))
    observable.observe(ComplianceObservation(
        AIActArticle.ART_14, "14.1", ComplianceLevel.SUBSTANTIAL,
        "Partially implemented", score=0.8
    ))
    checks.append(("s2_listener_fired", len(listener_calls) == 1))

    # ── S3: Bias Detection ────────────────────────────────────────────
    detector = BiasDetector()

    # Simulate outcomes for two regions
    for _ in range(100):
        detector.record_outcome("region", "EU", positive=True)
    for _ in range(20):
        detector.record_outcome("region", "EU", positive=False)
    for _ in range(60):
        detector.record_outcome("region", "non_EU", positive=True)
    for _ in range(60):
        detector.record_outcome("region", "non_EU", positive=False)

    report = detector.analyze("region")
    eu_rate = report.groups["EU"].positive_rate
    non_eu_rate = report.groups["non_EU"].positive_rate
    checks.append(("s3_eu_rate", abs(eu_rate - 100 / 120) < 0.01))
    checks.append(("s3_non_eu_rate", abs(non_eu_rate - 0.5) < 0.01))

    # 4/5ths rule: non_EU/EU = 0.5/0.833 = 0.6 < 0.8 → biased
    checks.append(("s3_bias_detected", not report.overall_fair))
    checks.append(("s3_biased_pairs", len(report.biased_pairs) > 0))

    # Fair case
    fair_detector = BiasDetector()
    for _ in range(100):
        fair_detector.record_outcome("size", "large", positive=True)
    for _ in range(20):
        fair_detector.record_outcome("size", "large", positive=False)
    for _ in range(90):
        fair_detector.record_outcome("size", "small", positive=True)
    for _ in range(30):
        fair_detector.record_outcome("size", "small", positive=False)
    fair_report = fair_detector.analyze("size")
    checks.append(("s3_fair_case", fair_report.overall_fair))

    # ── S4: Explainability Binding ────────────────────────────────────
    engine = ExplainabilityEngine()

    action = ExplainableAction(
        action_id="act_001", action_type="trust_update",
        entity_id="entity_1", timestamp=1000.0,
        trust_deltas=[
            TrustDelta("entity_1", "talent", 0.5, 0.6, 0.1, 1000.0),
            TrustDelta("entity_1", "training", 0.7, 0.75, 0.05, 1000.0),
        ],
        reasoning="Successful task completion observed",
        evidence=["task_result_hash_abc123"],
    )
    engine.record_action(action)

    # Another action
    action2 = ExplainableAction(
        action_id="act_002", action_type="delegation",
        entity_id="entity_1", timestamp=1001.0,
        trust_deltas=[
            TrustDelta("entity_1", "talent", 0.6, 0.55, -0.05, 1001.0),
        ],
        reasoning="Delegation task partially failed",
    )
    engine.record_action(action2)

    checks.append(("s4_actions_recorded", len(engine.actions) == 2))
    checks.append(("s4_explain_entity", len(engine.explain_entity("entity_1")) == 2))
    checks.append(("s4_cumulative_talent", abs(engine.cumulative_change("entity_1", "talent") - 0.05) < 0.001))
    checks.append(("s4_audit_trail", len(engine.audit_trail("entity_1")) == 2))

    talent_changes = engine.explain_change("entity_1", "talent")
    checks.append(("s4_talent_changes", len(talent_changes) == 2))

    # ── S5: Audit Trail ──────────────────────────────────────────────
    trail = AuditTrail()
    trail.append("trust_update", "entity_1", {"talent": 0.6, "delta": 0.1})
    trail.append("delegation", "entity_1", {"scope": "read", "target": "entity_2"})
    trail.append("revocation", "entity_2", {"reason": "compromise"})

    checks.append(("s5_chain_length", len(trail.entries) == 3))

    valid, errors = trail.verify_chain()
    checks.append(("s5_chain_valid", valid))
    checks.append(("s5_no_errors", len(errors) == 0))

    # Tamper detection
    trail.entries[1].details = {"tampered": True}
    valid_after, tamper_errors = trail.verify_chain()
    checks.append(("s5_tamper_detected", not valid_after))
    checks.append(("s5_tamper_errors", len(tamper_errors) > 0))

    # Entity filtering
    e1_entries = trail.entries_for_entity("entity_1")
    checks.append(("s5_entity_filter", len(e1_entries) == 2))

    # ── S6: Multi-Party Audit ─────────────────────────────────────────
    audit = MultiPartyAudit(required_quorum=2 / 3)
    audit.register_auditor(Auditor("aud1", 0.9))
    audit.register_auditor(Auditor("aud2", 0.85))
    audit.register_auditor(Auditor("aud3", 0.8))

    audit.submit_vote("entity_1", AuditVote(
        "aud1", ComplianceLevel.FULL, 0.9, ["All clear"]
    ))
    audit.submit_vote("entity_1", AuditVote(
        "aud2", ComplianceLevel.FULL, 0.85, ["Minor issues"]
    ))

    result = audit.evaluate("entity_1")
    checks.append(("s6_quorum_met", result is not None and result.quorum_met))
    checks.append(("s6_consensus", result is not None and result.consensus_level == ComplianceLevel.FULL))
    checks.append(("s6_agreement", result is not None and result.agreement_ratio > 0.5))

    # Not enough votes
    audit2 = MultiPartyAudit(required_quorum=2 / 3)
    audit2.register_auditor(Auditor("a1", 0.9))
    audit2.register_auditor(Auditor("a2", 0.9))
    audit2.register_auditor(Auditor("a3", 0.9))
    audit2.submit_vote("entity_x", AuditVote("a1", ComplianceLevel.PARTIAL, 0.5, []))
    result2 = audit2.evaluate("entity_x")
    checks.append(("s6_quorum_not_met", result2 is not None and not result2.quorum_met))

    # ── S7: Compliance Certification ──────────────────────────────────
    ca = CertificationAuthority("web4_ca")

    cert = ca.issue(
        "entity_1", ComplianceLevel.FULL,
        [AIActArticle.ART_9, AIActArticle.ART_10, AIActArticle.ART_15],
        "audit_hash_abc"
    )
    checks.append(("s7_cert_issued", cert.cert_id in ca.certificates))
    checks.append(("s7_cert_valid", cert.is_valid(time.time())))
    checks.append(("s7_cert_verified", ca.verify(cert)))

    # Revoke
    ca.revoke(cert.cert_id)
    checks.append(("s7_revoked", cert.revoked))
    checks.append(("s7_revoked_invalid", not cert.is_valid(time.time())))

    # Active certs
    cert2 = ca.issue("entity_1", ComplianceLevel.SUBSTANTIAL,
                     [AIActArticle.ART_12], "hash2")
    active = ca.active_certs("entity_1", time.time())
    checks.append(("s7_active_count", len(active) == 1))  # Only cert2 (cert revoked)

    # ── S8: Risk Management Pipeline ──────────────────────────────────
    pipeline = RiskPipeline()

    # Low risk entity
    low_risk = pipeline.assess("entity_low", 0.9, 10, True, 5)
    checks.append(("s8_low_risk", low_risk.risk_level == RiskLevel.MINIMAL))
    checks.append(("s8_has_mitigations", len(low_risk.mitigations) >= 2))

    # High risk entity
    high_risk = pipeline.assess("entity_high", 0.2, 80, False, 0)
    checks.append(("s8_high_risk", high_risk.risk_level in (RiskLevel.HIGH, RiskLevel.UNACCEPTABLE)))
    checks.append(("s8_high_residual", high_risk.residual_risk > low_risk.residual_risk))

    # Risk trend
    for i in range(5):
        pipeline.assess("entity_trend", 0.5 + i * 0.1, 50, True, i)
    trend = pipeline.entity_risk_trend("entity_trend")
    checks.append(("s8_trend_improving", trend[-1] < trend[0]))

    # ── S9: Live Dashboard ────────────────────────────────────────────
    dashboard = ComplianceDashboard()
    snap = dashboard.create_snapshot(observable, ca, pipeline, time.time())

    checks.append(("s9_has_snapshot", len(dashboard.snapshots) == 1))
    checks.append(("s9_article_scores", len(snap.article_scores) == 7))
    checks.append(("s9_risk_dist", len(snap.risk_distribution) > 0))
    checks.append(("s9_recent_events", len(snap.recent_events) > 0))

    # ── S10: Remediation Tracking ─────────────────────────────────────
    tracker = RemediationTracker()
    item1 = tracker.create(AIActArticle.ART_13, "13.1",
                           "Implement transparency interface", priority=1)
    item2 = tracker.create(AIActArticle.ART_10, "10.4",
                           "Add bias monitoring", priority=2)

    checks.append(("s10_items_created", len(tracker.items) == 2))
    checks.append(("s10_open_items", len(tracker.open_items()) == 2))

    tracker.resolve(item1.item_id)
    checks.append(("s10_resolved", item1.status == RemediationStatus.RESOLVED))
    checks.append(("s10_open_after_resolve", len(tracker.open_items()) == 1))
    checks.append(("s10_resolution_rate", tracker.resolution_rate() == 0.5))

    by_priority = tracker.by_priority()
    checks.append(("s10_priority_sorted", 1 in by_priority and 2 in by_priority))

    # ── S11: Performance ──────────────────────────────────────────────
    t0 = time.time()
    # 10K compliance observations
    perf_obs = ComplianceObservable()
    for i in range(10000):
        perf_obs.observe(ComplianceObservation(
            list(AIActArticle)[i % 7], f"req_{i}",
            ComplianceLevel.FULL, f"evidence_{i}", score=0.9
        ))
    dt = time.time() - t0
    checks.append(("s11_10k_observations", dt < 3.0))

    # 1K bias detections
    t0 = time.time()
    perf_bias = BiasDetector()
    for i in range(1000):
        perf_bias.record_outcome("attr", f"group_{i % 5}", positive=i % 3 != 0)
    for j in range(5):
        perf_bias.analyze("attr")
    dt = time.time() - t0
    checks.append(("s11_1k_bias", dt < 3.0))

    # 1K audit trail entries
    t0 = time.time()
    perf_trail = AuditTrail()
    for i in range(1000):
        perf_trail.append("event", f"entity_{i % 100}", {"i": i})
    valid, _ = perf_trail.verify_chain()
    dt = time.time() - t0
    checks.append(("s11_1k_audit", dt < 5.0 and valid))

    # ── Report ────────────────────────────────────────────────────────
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    width = 60
    title = f"Compliance Instrumentation — {passed}/{total} checks passed"
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
    print(f"\n  Time: {time.time() - t0:.2f}s\n")
    return passed == total


if __name__ == "__main__":
    success = run_checks()
    raise SystemExit(0 if success else 1)
