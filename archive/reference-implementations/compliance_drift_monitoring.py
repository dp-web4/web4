#!/usr/bin/env python3
"""
Compliance Drift Monitoring & Alerting System — Web4 Reference Implementation

Continuous monitoring of EU AI Act compliance status with automated alerting
when an entity's compliance degrades between formal assessments. This is the
"always-on" compliance layer that makes Web4 infrastructure sticky — entities
earn Art. 9 (continuous risk management) and Art. 61 (post-market monitoring)
credit automatically by running this system.

Implements:
  1. ComplianceDriftDetector: Monitors T3/V3 tensor trajectories, fires when
     rate-of-change exceeds threshold, predicts time-to-threshold-breach
  2. ArticleRiskRegister: Live register mapping each EU AI Act article to its
     current evidence state and trend
  3. AutomatedIncidentGenerator: When compliance posture drops, auto-generates
     Art. 62 incident report with deadline tracking
  4. RemediationWorkflow: For each compliance gap, identifies which Web4
     primitive to activate and tracks remediation progress
  5. ComplianceTimeline: Historical view of compliance state, reconstructable
     at any past date for regulatory audit
  6. MultiEntityDashboard: Federation-level view of entity compliance status

Pattern: Adapts synthon_decay_precursor.py detection pattern for compliance.
Builds on: eu_ai_act_demo_stack.py, eu_ai_act_compliance_engine.py,
           synthon_decay_precursor.py, reactive_trust_event_bus.py

Checks: 85
"""

import hashlib
import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# PART 1: DATA MODEL
# ═══════════════════════════════════════════════════════════════

class DriftDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    CRITICAL_DROP = "critical_drop"


class AlertSeverity(Enum):
    INFO = "info"           # Logged, no action
    WARNING = "warning"     # Reviewed at next assessment
    HIGH = "high"           # Immediate review needed
    CRITICAL = "critical"   # Automated response triggered


class ComplianceGrade(Enum):
    FULL = "full"                   # ≥90%
    SUBSTANTIAL = "substantial"     # ≥70%
    PARTIAL = "partial"             # ≥50%
    NON_COMPLIANT = "non_compliant" # <50%


class ArticleStatus(Enum):
    COMPLIANT = "compliant"
    AT_RISK = "at_risk"
    DEGRADING = "degrading"
    NON_COMPLIANT = "non_compliant"


class RemediationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class AIActArticle(Enum):
    ART_9 = "Risk Management System"
    ART_10 = "Data and Data Governance"
    ART_11 = "Technical Documentation"
    ART_12 = "Record-keeping"
    ART_13 = "Transparency and Information"
    ART_14 = "Human Oversight"
    ART_15 = "Accuracy, Robustness, Cybersecurity"


@dataclass
class T3Snapshot:
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5
    timestamp: float = 0.0

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0


# ═══════════════════════════════════════════════════════════════
# PART 2: COMPLIANCE DRIFT DETECTOR
# ═══════════════════════════════════════════════════════════════

@dataclass
class DriftAlert:
    """Alert generated when compliance drift is detected."""
    alert_id: str = ""
    entity_id: str = ""
    article: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    direction: DriftDirection = DriftDirection.STABLE
    metric_name: str = ""
    current_value: float = 0.0
    previous_value: float = 0.0
    rate_of_change: float = 0.0
    threshold: float = 0.0
    predicted_breach_time: float = 0.0  # Seconds until threshold breach
    timestamp: float = 0.0
    message: str = ""


class ComplianceDriftDetector:
    """
    Monitors T3/V3 tensor trajectories and compliance scores.
    Fires alerts when rate-of-change exceeds configurable thresholds.
    Predicts time-to-threshold-breach using exponential smoothing.
    """

    # Alert thresholds (rate of change per measurement interval)
    DEGRADATION_THRESHOLD = -0.05   # >5% drop = WARNING
    CRITICAL_THRESHOLD = -0.15      # >15% drop = CRITICAL
    COMPLIANCE_FLOOR = 0.5          # Below this = NON_COMPLIANT

    # Exponential smoothing parameter
    ALPHA = 0.3

    def __init__(self):
        self.entity_histories: Dict[str, List[Dict]] = {}
        self.smoothed_values: Dict[str, float] = {}
        self.smoothed_trends: Dict[str, float] = {}
        self.alerts: List[DriftAlert] = []
        self.alert_counter = 0

    def record_measurement(self, entity_id: str, metric_name: str,
                           value: float, timestamp: float = None) -> Optional[DriftAlert]:
        """Record a new metric value and check for drift."""
        ts = timestamp or time.time()
        key = f"{entity_id}:{metric_name}"

        if key not in self.entity_histories:
            self.entity_histories[key] = []
            self.smoothed_values[key] = value
            self.smoothed_trends[key] = 0.0

        history = self.entity_histories[key]
        history.append({"value": value, "timestamp": ts})

        # Exponential smoothing
        prev_smoothed = self.smoothed_values[key]
        new_smoothed = self.ALPHA * value + (1 - self.ALPHA) * prev_smoothed
        new_trend = self.ALPHA * (new_smoothed - prev_smoothed) + (1 - self.ALPHA) * self.smoothed_trends[key]

        self.smoothed_values[key] = new_smoothed
        self.smoothed_trends[key] = new_trend

        # Calculate rate of change
        if len(history) < 2:
            return None

        prev_value = history[-2]["value"]
        rate = value - prev_value

        # Determine drift direction
        if rate > 0.02:
            direction = DriftDirection.IMPROVING
        elif rate > self.DEGRADATION_THRESHOLD:
            direction = DriftDirection.STABLE
        elif rate > self.CRITICAL_THRESHOLD:
            direction = DriftDirection.DEGRADING
        else:
            direction = DriftDirection.CRITICAL_DROP

        # Generate alert if warranted
        if direction in (DriftDirection.DEGRADING, DriftDirection.CRITICAL_DROP):
            severity = (AlertSeverity.CRITICAL if direction == DriftDirection.CRITICAL_DROP
                        else AlertSeverity.WARNING)

            # Predict time to threshold breach
            predicted_breach = self._predict_breach(key, self.COMPLIANCE_FLOOR)

            self.alert_counter += 1
            alert = DriftAlert(
                alert_id=f"DRIFT-{self.alert_counter:04d}",
                entity_id=entity_id,
                article="",  # Filled by caller
                severity=severity,
                direction=direction,
                metric_name=metric_name,
                current_value=value,
                previous_value=prev_value,
                rate_of_change=rate,
                threshold=self.COMPLIANCE_FLOOR,
                predicted_breach_time=predicted_breach,
                timestamp=ts,
                message=f"{metric_name} dropped {abs(rate):.3f} ({direction.value})",
            )
            self.alerts.append(alert)
            return alert

        return None

    def _predict_breach(self, key: str, threshold: float) -> float:
        """Predict seconds until threshold breach using trend extrapolation."""
        current = self.smoothed_values.get(key, 0.5)
        trend = self.smoothed_trends.get(key, 0.0)

        if trend >= 0:
            return float('inf')  # Not degrading
        if current <= threshold:
            return 0.0  # Already breached

        # Time to breach = (current - threshold) / |trend|
        # Assume one measurement per "time unit"
        steps_to_breach = (current - threshold) / abs(trend)
        return steps_to_breach

    def get_entity_status(self, entity_id: str) -> Dict:
        """Get current drift status for all metrics of an entity."""
        status = {}
        for key, history in self.entity_histories.items():
            eid, metric = key.split(":", 1)
            if eid != entity_id:
                continue
            if not history:
                continue
            current = history[-1]["value"]
            trend = self.smoothed_trends.get(key, 0.0)
            if trend > 0.01:
                direction = DriftDirection.IMPROVING
            elif trend > -0.02:
                direction = DriftDirection.STABLE
            elif trend > -0.08:
                direction = DriftDirection.DEGRADING
            else:
                direction = DriftDirection.CRITICAL_DROP
            status[metric] = {
                "current": current,
                "trend": trend,
                "direction": direction.value,
                "smoothed": self.smoothed_values.get(key, current),
            }
        return status


# ═══════════════════════════════════════════════════════════════
# PART 3: ARTICLE RISK REGISTER
# ═══════════════════════════════════════════════════════════════

@dataclass
class ArticleRiskEntry:
    """Risk register entry for a single EU AI Act article."""
    article: AIActArticle
    status: ArticleStatus = ArticleStatus.COMPLIANT
    current_score: float = 1.0
    trend: DriftDirection = DriftDirection.STABLE
    last_assessment: float = 0.0
    evidence_count: int = 0
    alert_count: int = 0
    risk_description: str = ""


class ArticleRiskRegister:
    """
    Live register mapping each EU AI Act article to current compliance
    status, evidence state, and trend. Updated in real-time.
    """

    # Article → T3 dimension mapping (which T3 dimension most affects which article)
    ARTICLE_T3_MAPPING = {
        AIActArticle.ART_9: "composite",     # Risk management uses overall T3
        AIActArticle.ART_10: "training",     # Data governance = training data quality
        AIActArticle.ART_11: "composite",    # Technical docs = overall capability
        AIActArticle.ART_12: "composite",    # Record-keeping = general discipline
        AIActArticle.ART_13: "temperament",  # Transparency = behavioral predictability
        AIActArticle.ART_14: "temperament",  # Human oversight = responsiveness
        AIActArticle.ART_15: "talent",       # Accuracy/robustness = core capability
    }

    # Minimum T3 scores for article compliance
    ARTICLE_THRESHOLDS = {
        AIActArticle.ART_9: 0.6,
        AIActArticle.ART_10: 0.5,
        AIActArticle.ART_11: 0.4,
        AIActArticle.ART_12: 0.4,
        AIActArticle.ART_13: 0.5,
        AIActArticle.ART_14: 0.55,
        AIActArticle.ART_15: 0.65,
    }

    def __init__(self):
        self.entries: Dict[AIActArticle, ArticleRiskEntry] = {}
        for art in AIActArticle:
            self.entries[art] = ArticleRiskEntry(article=art)

    def update_from_t3(self, t3: T3Snapshot, alerts: List[DriftAlert] = None):
        """Update risk register from T3 tensor snapshot."""
        now = t3.timestamp or time.time()
        alerts = alerts or []

        for article, entry in self.entries.items():
            dim = self.ARTICLE_T3_MAPPING.get(article, "composite")
            if dim == "composite":
                score = t3.composite
            else:
                score = getattr(t3, dim, t3.composite)

            threshold = self.ARTICLE_THRESHOLDS.get(article, 0.5)
            entry.current_score = score
            entry.last_assessment = now

            # Count relevant alerts
            art_alerts = [a for a in alerts if article.value in a.article]
            entry.alert_count = len(art_alerts)

            # Determine status
            if score >= threshold + 0.15:
                entry.status = ArticleStatus.COMPLIANT
            elif score >= threshold:
                entry.status = ArticleStatus.AT_RISK
            elif score >= threshold - 0.1:
                entry.status = ArticleStatus.DEGRADING
            else:
                entry.status = ArticleStatus.NON_COMPLIANT

    def get_at_risk_articles(self) -> List[ArticleRiskEntry]:
        """Get all articles that are at risk or worse."""
        return [
            e for e in self.entries.values()
            if e.status in (ArticleStatus.AT_RISK, ArticleStatus.DEGRADING,
                            ArticleStatus.NON_COMPLIANT)
        ]

    def overall_risk_score(self) -> float:
        """Aggregate risk score across all articles."""
        if not self.entries:
            return 0.0
        return sum(e.current_score for e in self.entries.values()) / len(self.entries)


# ═══════════════════════════════════════════════════════════════
# PART 4: AUTOMATED INCIDENT GENERATOR
# ═══════════════════════════════════════════════════════════════

@dataclass
class ComplianceIncident:
    """Auto-generated incident when compliance drops."""
    incident_id: str = ""
    entity_id: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    trigger_alert: str = ""  # Alert ID that triggered this
    article_affected: str = ""
    description: str = ""
    detected_at: float = 0.0
    deadline: float = 0.0      # Notification deadline
    notified: bool = False
    resolved: bool = False
    resolution: str = ""


class AutomatedIncidentGenerator:
    """
    Generates Art. 62 incident reports when compliance posture drops.
    Tracks notification deadlines.
    """

    DEADLINE_HOURS = {
        AlertSeverity.CRITICAL: 48,    # 2 days
        AlertSeverity.HIGH: 360,       # 15 days
        AlertSeverity.WARNING: 720,    # 30 days
        AlertSeverity.INFO: 2160,      # 90 days
    }

    def __init__(self):
        self.incidents: Dict[str, ComplianceIncident] = {}
        self.incident_counter = 0

    def generate_from_alert(self, alert: DriftAlert) -> ComplianceIncident:
        """Auto-generate incident from drift alert."""
        self.incident_counter += 1
        deadline_hours = self.DEADLINE_HOURS.get(alert.severity, 720)

        incident = ComplianceIncident(
            incident_id=f"INC-{self.incident_counter:04d}",
            entity_id=alert.entity_id,
            severity=alert.severity,
            trigger_alert=alert.alert_id,
            article_affected=alert.article,
            description=f"Compliance drift detected: {alert.message}",
            detected_at=alert.timestamp,
            deadline=alert.timestamp + deadline_hours * 3600,
        )
        self.incidents[incident.incident_id] = incident
        return incident

    def check_overdue(self, current_time: float = None) -> List[ComplianceIncident]:
        now = current_time or time.time()
        return [
            inc for inc in self.incidents.values()
            if not inc.notified and not inc.resolved and now > inc.deadline
        ]

    def resolve(self, incident_id: str, resolution: str) -> bool:
        if incident_id not in self.incidents:
            return False
        self.incidents[incident_id].resolved = True
        self.incidents[incident_id].resolution = resolution
        return True


# ═══════════════════════════════════════════════════════════════
# PART 5: REMEDIATION WORKFLOW
# ═══════════════════════════════════════════════════════════════

@dataclass
class RemediationTask:
    """A specific remediation action tracked to completion."""
    task_id: str = ""
    incident_id: str = ""
    entity_id: str = ""
    article: str = ""
    action: str = ""
    web4_primitive: str = ""
    status: RemediationStatus = RemediationStatus.PENDING
    created_at: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0
    effectiveness: float = 0.0  # 0.0-1.0 — did the fix work?


class RemediationWorkflow:
    """
    Tracks remediation from incident detection through resolution.
    Maps each gap to the specific Web4 primitive that fixes it.
    """

    # Gap → remediation mapping
    REMEDIATION_MAP = {
        "t3_composite": ("Enable continuous T3 monitoring", "T3/V3 Reputation Engine"),
        "talent": ("Improve adversarial testing coverage", "Red Team Simulator"),
        "training": ("Enhance data governance tracking", "Copyright Provenance Tracker"),
        "temperament": ("Increase behavioral monitoring", "PolicyGate IRP"),
        "compliance_score": ("Run full compliance re-assessment", "EU AI Act Compliance Engine"),
        "audit_coverage": ("Initiate multi-party audit", "Audit Certification Chain"),
    }

    def __init__(self):
        self.tasks: Dict[str, RemediationTask] = {}
        self.task_counter = 0

    def create_task(self, incident: ComplianceIncident,
                    metric_name: str = "") -> RemediationTask:
        self.task_counter += 1
        action, primitive = self.REMEDIATION_MAP.get(
            metric_name, ("Review compliance posture", "EU AI Act Compliance Engine")
        )

        task = RemediationTask(
            task_id=f"TASK-{self.task_counter:04d}",
            incident_id=incident.incident_id,
            entity_id=incident.entity_id,
            article=incident.article_affected,
            action=action,
            web4_primitive=primitive,
            status=RemediationStatus.PENDING,
            created_at=time.time(),
        )
        self.tasks[task.task_id] = task
        return task

    def start_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        task.status = RemediationStatus.IN_PROGRESS
        task.started_at = time.time()
        return True

    def complete_task(self, task_id: str, effectiveness: float) -> bool:
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        task.status = RemediationStatus.COMPLETED
        task.completed_at = time.time()
        task.effectiveness = effectiveness
        return True

    def get_pending_tasks(self, entity_id: str = None) -> List[RemediationTask]:
        tasks = [t for t in self.tasks.values()
                 if t.status in (RemediationStatus.PENDING, RemediationStatus.IN_PROGRESS)]
        if entity_id:
            tasks = [t for t in tasks if t.entity_id == entity_id]
        return tasks

    def remediation_effectiveness(self) -> float:
        """Average effectiveness of completed remediations."""
        completed = [t for t in self.tasks.values()
                     if t.status == RemediationStatus.COMPLETED]
        if not completed:
            return 0.0
        return sum(t.effectiveness for t in completed) / len(completed)


# ═══════════════════════════════════════════════════════════════
# PART 6: COMPLIANCE TIMELINE
# ═══════════════════════════════════════════════════════════════

@dataclass
class TimelineEntry:
    """A point-in-time compliance snapshot."""
    entity_id: str = ""
    timestamp: float = 0.0
    grade: ComplianceGrade = ComplianceGrade.FULL
    score: float = 1.0
    t3_composite: float = 0.5
    article_statuses: Dict[str, str] = field(default_factory=dict)
    alerts_active: int = 0
    incidents_open: int = 0
    hash_digest: str = ""
    prev_hash: str = ""


class ComplianceTimeline:
    """
    Historical record of compliance state. Can reconstruct compliance
    posture at any past date for regulatory audit.
    """

    def __init__(self):
        self.timelines: Dict[str, List[TimelineEntry]] = {}
        self.prev_hashes: Dict[str, str] = {}

    def record_snapshot(self, entity_id: str, score: float,
                        t3_composite: float,
                        article_statuses: Dict[str, str] = None,
                        alerts_active: int = 0,
                        incidents_open: int = 0) -> TimelineEntry:
        now = time.time()
        if entity_id not in self.timelines:
            self.timelines[entity_id] = []
            self.prev_hashes[entity_id] = "genesis"

        # Determine grade
        if score >= 0.9:
            grade = ComplianceGrade.FULL
        elif score >= 0.7:
            grade = ComplianceGrade.SUBSTANTIAL
        elif score >= 0.5:
            grade = ComplianceGrade.PARTIAL
        else:
            grade = ComplianceGrade.NON_COMPLIANT

        prev_hash = self.prev_hashes[entity_id]
        content = f"{entity_id}:{now}:{score}:{t3_composite}:{prev_hash}"
        entry_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        entry = TimelineEntry(
            entity_id=entity_id,
            timestamp=now,
            grade=grade,
            score=score,
            t3_composite=t3_composite,
            article_statuses=article_statuses or {},
            alerts_active=alerts_active,
            incidents_open=incidents_open,
            hash_digest=entry_hash,
            prev_hash=prev_hash,
        )
        self.timelines[entity_id].append(entry)
        self.prev_hashes[entity_id] = entry_hash
        return entry

    def get_at_time(self, entity_id: str, target_time: float) -> Optional[TimelineEntry]:
        """Reconstruct compliance state at a specific time."""
        if entity_id not in self.timelines:
            return None
        timeline = self.timelines[entity_id]
        # Find the most recent entry before target_time
        best = None
        for entry in timeline:
            if entry.timestamp <= target_time:
                best = entry
        return best

    def grade_changes(self, entity_id: str) -> List[Dict]:
        """Find all points where compliance grade changed."""
        if entity_id not in self.timelines:
            return []
        timeline = self.timelines[entity_id]
        changes = []
        for i in range(1, len(timeline)):
            if timeline[i].grade != timeline[i-1].grade:
                changes.append({
                    "from_grade": timeline[i-1].grade.value,
                    "to_grade": timeline[i].grade.value,
                    "timestamp": timeline[i].timestamp,
                    "score_before": timeline[i-1].score,
                    "score_after": timeline[i].score,
                })
        return changes

    def verify_chain(self, entity_id: str) -> bool:
        """Verify hash chain integrity."""
        if entity_id not in self.timelines:
            return True
        timeline = self.timelines[entity_id]
        for i in range(1, len(timeline)):
            if timeline[i].prev_hash != timeline[i-1].hash_digest:
                return False
        return True


# ═══════════════════════════════════════════════════════════════
# PART 7: MULTI-ENTITY DASHBOARD
# ═══════════════════════════════════════════════════════════════

@dataclass
class EntityComplianceSummary:
    """Summary of a single entity's compliance for dashboard."""
    entity_id: str = ""
    current_grade: ComplianceGrade = ComplianceGrade.FULL
    current_score: float = 1.0
    drift_direction: DriftDirection = DriftDirection.STABLE
    open_alerts: int = 0
    open_incidents: int = 0
    pending_remediations: int = 0
    at_risk_articles: int = 0


class MultiEntityDashboard:
    """
    Federation-level compliance dashboard. Aggregates entity status
    into a single view for compliance officers.
    """

    def __init__(self):
        self.entity_summaries: Dict[str, EntityComplianceSummary] = {}

    def update_entity(self, summary: EntityComplianceSummary):
        self.entity_summaries[summary.entity_id] = summary

    def federation_compliance_score(self) -> float:
        """Average compliance score across all entities."""
        if not self.entity_summaries:
            return 0.0
        return sum(s.current_score for s in self.entity_summaries.values()) / len(self.entity_summaries)

    def entities_by_grade(self) -> Dict[str, List[str]]:
        """Group entities by compliance grade."""
        by_grade: Dict[str, List[str]] = {}
        for eid, summary in self.entity_summaries.items():
            grade = summary.current_grade.value
            if grade not in by_grade:
                by_grade[grade] = []
            by_grade[grade].append(eid)
        return by_grade

    def degrading_entities(self) -> List[EntityComplianceSummary]:
        """Find entities currently drifting toward non-compliance."""
        return [
            s for s in self.entity_summaries.values()
            if s.drift_direction in (DriftDirection.DEGRADING, DriftDirection.CRITICAL_DROP)
        ]

    def compliance_distribution(self) -> Dict[str, int]:
        """Count entities at each compliance grade."""
        dist: Dict[str, int] = {}
        for summary in self.entity_summaries.values():
            grade = summary.current_grade.value
            dist[grade] = dist.get(grade, 0) + 1
        return dist

    def risk_heatmap(self) -> List[Dict]:
        """Entities ranked by risk (lowest score first)."""
        ranked = sorted(
            self.entity_summaries.values(),
            key=lambda s: s.current_score,
        )
        return [
            {
                "entity_id": s.entity_id,
                "score": s.current_score,
                "grade": s.current_grade.value,
                "drift": s.drift_direction.value,
                "alerts": s.open_alerts,
            }
            for s in ranked
        ]


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

    # ── S1: Drift Detection — Stable ────────────────────────────
    print("\nS1: Drift Detection — Stable")
    detector = ComplianceDriftDetector()
    # First measurement (baseline)
    alert = detector.record_measurement("e1", "t3_composite", 0.85, now)
    results.append(check("s1_no_alert_first", alert is None))

    # Stable measurement
    alert2 = detector.record_measurement("e1", "t3_composite", 0.84, now + 1)
    results.append(check("s1_no_alert_stable", alert2 is None))

    # ── S2: Drift Detection — Degrading ─────────────────────────
    print("\nS2: Drift Detection — Degrading")
    det2 = ComplianceDriftDetector()
    det2.record_measurement("e2", "talent", 0.80, now)
    alert3 = det2.record_measurement("e2", "talent", 0.72, now + 1)
    results.append(check("s2_degrading_alert", alert3 is not None))
    results.append(check("s2_warning_severity", alert3.severity == AlertSeverity.WARNING))
    results.append(check("s2_direction", alert3.direction == DriftDirection.DEGRADING))
    results.append(check("s2_rate_negative", alert3.rate_of_change < 0))

    # ── S3: Drift Detection — Critical Drop ─────────────────────
    print("\nS3: Drift Detection — Critical Drop")
    det3 = ComplianceDriftDetector()
    det3.record_measurement("e3", "temperament", 0.90, now)
    alert4 = det3.record_measurement("e3", "temperament", 0.70, now + 1)
    results.append(check("s3_critical_alert", alert4 is not None))
    results.append(check("s3_critical_severity", alert4.severity == AlertSeverity.CRITICAL))
    results.append(check("s3_critical_direction",
        alert4.direction == DriftDirection.CRITICAL_DROP))

    # ── S4: Breach Prediction ───────────────────────────────────
    print("\nS4: Breach Prediction")
    det4 = ComplianceDriftDetector()
    # Build history with steady decline
    for i in range(10):
        det4.record_measurement("e4", "composite", 0.9 - i * 0.03, now + i)
    # Should predict breach
    key = "e4:composite"
    trend = det4.smoothed_trends[key]
    results.append(check("s4_negative_trend", trend < 0))
    breach_time = det4._predict_breach(key, 0.5)
    results.append(check("s4_finite_breach", breach_time < float('inf')))
    results.append(check("s4_breach_positive", breach_time > 0))

    # Non-degrading → infinite prediction
    det4b = ComplianceDriftDetector()
    det4b.record_measurement("e4b", "score", 0.9, now)
    det4b.record_measurement("e4b", "score", 0.92, now + 1)
    breach2 = det4b._predict_breach("e4b:score", 0.5)
    results.append(check("s4_no_breach", breach2 == float('inf')))

    # ── S5: Entity Status ───────────────────────────────────────
    print("\nS5: Entity Status")
    status = det4.get_entity_status("e4")
    results.append(check("s5_has_composite", "composite" in status))
    results.append(check("s5_degrading_dir",
        status["composite"]["direction"] in ("degrading", "critical_drop")))
    results.append(check("s5_has_trend", "trend" in status["composite"]))

    # ── S6: Article Risk Register ───────────────────────────────
    print("\nS6: Article Risk Register")
    register = ArticleRiskRegister()
    # High T3 → all compliant
    register.update_from_t3(T3Snapshot(0.85, 0.80, 0.82, now))
    at_risk = register.get_at_risk_articles()
    results.append(check("s6_none_at_risk", len(at_risk) == 0))
    results.append(check("s6_all_compliant",
        all(e.status == ArticleStatus.COMPLIANT for e in register.entries.values())))

    # ── S7: Article Risk — Low T3 ──────────────────────────────
    print("\nS7: Article Risk — Low T3")
    register2 = ArticleRiskRegister()
    register2.update_from_t3(T3Snapshot(0.40, 0.30, 0.35, now))
    at_risk2 = register2.get_at_risk_articles()
    results.append(check("s7_some_at_risk", len(at_risk2) > 0))
    # Art 15 needs talent ≥ 0.65, talent=0.40 → non-compliant
    art15_entry = register2.entries[AIActArticle.ART_15]
    results.append(check("s7_art15_bad",
        art15_entry.status in (ArticleStatus.NON_COMPLIANT, ArticleStatus.DEGRADING)))

    # ── S8: Article Risk — Overall Score ────────────────────────
    print("\nS8: Overall Risk Score")
    score_high = ArticleRiskRegister()
    score_high.update_from_t3(T3Snapshot(0.9, 0.9, 0.9, now))
    results.append(check("s8_high_score", score_high.overall_risk_score() > 0.8))

    score_low = ArticleRiskRegister()
    score_low.update_from_t3(T3Snapshot(0.3, 0.3, 0.3, now))
    results.append(check("s8_low_score", score_low.overall_risk_score() < 0.4))

    # ── S9: Automated Incident Generation ───────────────────────
    print("\nS9: Incident Generation")
    gen = AutomatedIncidentGenerator()
    test_alert = DriftAlert(
        alert_id="DRIFT-0001",
        entity_id="e1",
        severity=AlertSeverity.HIGH,
        direction=DriftDirection.DEGRADING,
        metric_name="t3_composite",
        current_value=0.55,
        previous_value=0.70,
        rate_of_change=-0.15,
        timestamp=now,
        message="t3_composite dropped 0.150",
    )
    incident = gen.generate_from_alert(test_alert)
    results.append(check("s9_incident_created", incident.incident_id == "INC-0001"))
    results.append(check("s9_entity_id", incident.entity_id == "e1"))
    results.append(check("s9_severity", incident.severity == AlertSeverity.HIGH))
    results.append(check("s9_deadline_set", incident.deadline > now))

    # ── S10: Incident Deadline ──────────────────────────────────
    print("\nS10: Incident Deadline")
    # HIGH = 15 days = 360 hours
    expected_deadline = now + 360 * 3600
    results.append(check("s10_deadline_15d",
        abs(incident.deadline - expected_deadline) < 1.0))

    # Critical = 2 days
    crit_alert = DriftAlert(
        alert_id="DRIFT-0002", entity_id="e2",
        severity=AlertSeverity.CRITICAL, timestamp=now,
        message="critical",
    )
    crit_incident = gen.generate_from_alert(crit_alert)
    expected_crit = now + 48 * 3600
    results.append(check("s10_critical_2d",
        abs(crit_incident.deadline - expected_crit) < 1.0))

    # ── S11: Overdue Detection ──────────────────────────────────
    print("\nS11: Overdue Detection")
    # Not overdue yet
    overdue = gen.check_overdue(now + 1000)
    results.append(check("s11_not_overdue", len(overdue) == 0))

    # After deadline
    overdue2 = gen.check_overdue(now + 400 * 3600)  # Well past 15 days
    results.append(check("s11_overdue_found", len(overdue2) > 0))

    # Resolve incident
    gen.resolve(incident.incident_id, "Fixed by retraining")
    overdue3 = gen.check_overdue(now + 400 * 3600)
    results.append(check("s11_resolved_not_overdue",
        not any(o.incident_id == incident.incident_id for o in overdue3)))

    # ── S12: Remediation Workflow ───────────────────────────────
    print("\nS12: Remediation Workflow")
    workflow = RemediationWorkflow()
    task = workflow.create_task(incident, "talent")
    results.append(check("s12_task_created", task.task_id == "TASK-0001"))
    results.append(check("s12_pending", task.status == RemediationStatus.PENDING))
    results.append(check("s12_has_action", task.action != ""))
    results.append(check("s12_has_primitive", task.web4_primitive == "Red Team Simulator"))

    # Start and complete
    workflow.start_task(task.task_id)
    results.append(check("s12_in_progress",
        workflow.tasks[task.task_id].status == RemediationStatus.IN_PROGRESS))

    workflow.complete_task(task.task_id, 0.85)
    results.append(check("s12_completed",
        workflow.tasks[task.task_id].status == RemediationStatus.COMPLETED))
    results.append(check("s12_effectiveness",
        workflow.tasks[task.task_id].effectiveness == 0.85))

    # ── S13: Remediation Effectiveness ──────────────────────────
    print("\nS13: Remediation Effectiveness")
    # Create a second task
    task2 = workflow.create_task(crit_incident, "training")
    workflow.start_task(task2.task_id)
    workflow.complete_task(task2.task_id, 0.70)

    avg_eff = workflow.remediation_effectiveness()
    results.append(check("s13_avg_effectiveness", abs(avg_eff - 0.775) < 0.01))

    # Pending tasks
    task3 = workflow.create_task(crit_incident, "composite")
    pending = workflow.get_pending_tasks()
    results.append(check("s13_has_pending", len(pending) == 1))

    # ── S14: Compliance Timeline ────────────────────────────────
    print("\nS14: Compliance Timeline")
    timeline = ComplianceTimeline()
    for i in range(5):
        score = 0.95 - i * 0.1
        timeline.record_snapshot(
            "e1", score, 0.85 - i * 0.05,
            article_statuses={"Art 9": "compliant"},
        )

    results.append(check("s14_entries", len(timeline.timelines["e1"]) == 5))
    results.append(check("s14_chain_valid", timeline.verify_chain("e1")))

    # ── S15: Timeline — Grade Changes ───────────────────────────
    print("\nS15: Timeline — Grade Changes")
    changes = timeline.grade_changes("e1")
    results.append(check("s15_has_changes", len(changes) > 0))
    # 0.95→FULL, 0.85→FULL, 0.75→SUBSTANTIAL, 0.65→PARTIAL, 0.55→PARTIAL
    results.append(check("s15_grade_drop",
        any(c["to_grade"] in ("substantial", "partial") for c in changes)))

    # ── S16: Timeline — Point-in-Time Reconstruction ────────────
    print("\nS16: Timeline Reconstruction")
    entries = timeline.timelines["e1"]
    # Get state at time of 3rd entry
    target = entries[2].timestamp
    reconstructed = timeline.get_at_time("e1", target)
    results.append(check("s16_reconstructed", reconstructed is not None))
    results.append(check("s16_correct_score",
        abs(reconstructed.score - 0.75) < 0.01))

    # Future time → latest entry
    future = timeline.get_at_time("e1", now + 999999)
    results.append(check("s16_future_latest", future is not None))
    results.append(check("s16_future_score",
        abs(future.score - 0.55) < 0.01))

    # ── S17: Timeline — Hash Chain Integrity ────────────────────
    print("\nS17: Hash Chain Integrity")
    results.append(check("s17_valid_chain", timeline.verify_chain("e1")))

    # Tamper with chain
    timeline.timelines["e1"][2].hash_digest = "tampered"
    results.append(check("s17_tamper_detected", not timeline.verify_chain("e1")))

    # Fix it back (for subsequent tests)
    content = f"e1:{entries[2].timestamp}:{entries[2].score}:{entries[2].t3_composite}:{entries[2].prev_hash}"
    entries[2].hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]

    # ── S18: Multi-Entity Dashboard ─────────────────────────────
    print("\nS18: Multi-Entity Dashboard")
    dashboard = MultiEntityDashboard()
    entities = [
        EntityComplianceSummary("e1", ComplianceGrade.FULL, 0.95,
            DriftDirection.STABLE, 0, 0, 0, 0),
        EntityComplianceSummary("e2", ComplianceGrade.SUBSTANTIAL, 0.75,
            DriftDirection.DEGRADING, 2, 1, 1, 2),
        EntityComplianceSummary("e3", ComplianceGrade.PARTIAL, 0.55,
            DriftDirection.CRITICAL_DROP, 5, 3, 3, 4),
        EntityComplianceSummary("e4", ComplianceGrade.FULL, 0.92,
            DriftDirection.IMPROVING, 0, 0, 0, 0),
        EntityComplianceSummary("e5", ComplianceGrade.NON_COMPLIANT, 0.30,
            DriftDirection.CRITICAL_DROP, 8, 5, 4, 7),
    ]
    for e in entities:
        dashboard.update_entity(e)

    fed_score = dashboard.federation_compliance_score()
    results.append(check("s18_fed_score", abs(fed_score - 0.694) < 0.01))

    # ── S19: Dashboard — Entity Grouping ────────────────────────
    print("\nS19: Dashboard Grouping")
    by_grade = dashboard.entities_by_grade()
    results.append(check("s19_full_count", len(by_grade.get("full", [])) == 2))
    results.append(check("s19_non_compliant", len(by_grade.get("non_compliant", [])) == 1))

    degrading = dashboard.degrading_entities()
    results.append(check("s19_degrading_count", len(degrading) == 3))  # e2=DEGRADING, e3=CRITICAL, e5=CRITICAL

    dist = dashboard.compliance_distribution()
    results.append(check("s19_distribution", sum(dist.values()) == 5))

    # ── S20: Dashboard — Risk Heatmap ───────────────────────────
    print("\nS20: Risk Heatmap")
    heatmap = dashboard.risk_heatmap()
    results.append(check("s20_sorted", heatmap[0]["score"] <= heatmap[-1]["score"]))
    results.append(check("s20_worst_first", heatmap[0]["entity_id"] == "e5"))
    results.append(check("s20_best_last", heatmap[-1]["entity_id"] == "e1"))
    results.append(check("s20_has_drift", "drift" in heatmap[0]))

    # ── S21: End-to-End Flow ────────────────────────────────────
    print("\nS21: End-to-End Flow")
    # Simulate: entity starts healthy → degrades → alert → incident → remediate
    e2e_detector = ComplianceDriftDetector()
    e2e_gen = AutomatedIncidentGenerator()
    e2e_workflow = RemediationWorkflow()
    e2e_timeline = ComplianceTimeline()

    # Healthy
    e2e_detector.record_measurement("e2e", "composite", 0.90, now)
    e2e_timeline.record_snapshot("e2e", 0.90, 0.90)

    # Degradation
    e2e_alert = e2e_detector.record_measurement("e2e", "composite", 0.70, now + 1)
    results.append(check("s21_alert_fired", e2e_alert is not None))

    # Generate incident
    e2e_incident = e2e_gen.generate_from_alert(e2e_alert)
    results.append(check("s21_incident_created", e2e_incident is not None))

    # Create remediation
    e2e_task = e2e_workflow.create_task(e2e_incident, "composite")
    results.append(check("s21_task_created", e2e_task is not None))

    # Execute remediation
    e2e_workflow.start_task(e2e_task.task_id)
    e2e_workflow.complete_task(e2e_task.task_id, 0.90)

    # Record recovery
    e2e_detector.record_measurement("e2e", "composite", 0.88, now + 2)
    e2e_timeline.record_snapshot("e2e", 0.88, 0.88)

    # Verify timeline
    results.append(check("s21_timeline_entries", len(e2e_timeline.timelines["e2e"]) == 2))
    results.append(check("s21_chain_valid", e2e_timeline.verify_chain("e2e")))

    # ── Summary ─────────────────────────────────────────────────
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"Compliance Drift Monitoring: {passed}/{total} checks passed")
    if passed == total:
        print("ALL CHECKS PASSED")
    else:
        print(f"FAILURES: {total - passed}")
    return passed == total


if __name__ == "__main__":
    run_tests()
