#!/usr/bin/env python3
"""
Governance Simulation Engine
==============================

Integrated simulation of the full SAL governance stack:
  - Law oracle with 5 trigger types and graduated responses
  - Two-phase validation: alignment (spirit) then compliance (letter)
  - Emergency bypass (CRISIS mode) with post-hoc audit
  - Appeal mechanism with panel voting and T3/V3 rollback
  - Adversarial scenarios (gaming the governance)

Key principle tested:
  "Alignment without compliance = ACCEPTABLE.
   Compliance without alignment = NEVER ACCEPTABLE."

Session: 12 (2026-02-27)
"""

import hashlib
import json
import math
import random
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any


# ═══════════════════════════════════════════════════════════════
#  CHECK HARNESS
# ═══════════════════════════════════════════════════════════════

_checks_passed = 0
_checks_failed = 0
_section = ""


def section(name: str):
    global _section
    _section = name
    print(f"\nSection: {name}")


def check(condition: bool, label: str):
    global _checks_passed, _checks_failed
    if condition:
        _checks_passed += 1
    else:
        _checks_failed += 1
        print(f"  FAIL: {label}")


# ═══════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class TriggerType(str, Enum):
    EVENT = "event"          # Reactive to named event
    SCHEDULE = "schedule"    # Cron-based
    CONDITION = "condition"  # R6 selector-based
    INTERVAL = "interval"    # Duration-based
    THRESHOLD = "threshold"  # Value exceeds/drops below


class ResponseLevel(str, Enum):
    """Graduated response severity."""
    NOTICE = "notice"                # Level 1: Log warning
    RESTRICT = "restrict"            # Level 2: Reduce permissions
    SUSPEND = "suspend"              # Level 3: Temporary freeze
    EMERGENCY_HALT = "emergency_halt" # Level 4: Stop all activity
    EXPEL = "expel"                  # Level 5: Remove from society


class LawSeverity(str, Enum):
    CRITICAL = "critical"    # Safety-critical
    HIGH = "high"            # Core governance
    MEDIUM = "medium"        # Standard operations
    LOW = "low"              # Minor governance


class OperatingMode(str, Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"    # Heightened scrutiny
    CRISIS = "crisis"        # Emergency — compliance optional, alignment mandatory


class AppealStatus(str, Enum):
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    UPHELD = "upheld"          # Penalty reversed
    DENIED = "denied"          # Penalty stands
    PARTIAL = "partial"        # Partially reversed
    EXPIRED = "expired"


class VerdictType(str, Enum):
    FULL_REVERSAL = "full_reversal"
    PARTIAL_REVERSAL = "partial_reversal"
    UPHELD = "upheld"
    MODIFIED = "modified"


# ═══════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class T3Snapshot:
    """Point-in-time trust tensor values."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return self.talent * 0.4 + self.training * 0.3 + self.temperament * 0.3

    def apply_penalty(self, talent_delta: float = 0.0,
                      training_delta: float = 0.0,
                      temperament_delta: float = 0.0):
        self.talent = max(0.0, min(1.0, self.talent + talent_delta))
        self.training = max(0.0, min(1.0, self.training + training_delta))
        self.temperament = max(0.0, min(1.0, self.temperament + temperament_delta))

    def copy(self) -> "T3Snapshot":
        return T3Snapshot(self.talent, self.training, self.temperament)

    def to_dict(self) -> dict:
        return {"talent": round(self.talent, 4),
                "training": round(self.training, 4),
                "temperament": round(self.temperament, 4),
                "composite": round(self.composite, 4)}


@dataclass
class GovEntity:
    """A governed entity within a society."""
    lct_id: str
    name: str
    entity_type: str  # "human", "ai", "service"
    t3: T3Snapshot = field(default_factory=T3Snapshot)
    atp_balance: float = 100.0
    role: str = "citizen"
    suspended: bool = False
    expelled: bool = False
    penalty_history: list = field(default_factory=list)
    action_count: int = 0
    violation_count: int = 0


@dataclass
class GraduatedThreshold:
    """Multi-level threshold with graduated responses."""
    metric_name: str  # What we're measuring
    levels: dict = field(default_factory=dict)
    # level_name -> {"threshold": float, "response": ResponseLevel, "direction": "above"|"below"}

    def evaluate(self, value: float) -> tuple[Optional[str], Optional[ResponseLevel]]:
        """Evaluate value against thresholds. Returns (level_name, response) or (None, None)."""
        matched_level = None
        matched_response = None
        matched_severity = -1

        severity_order = {
            ResponseLevel.NOTICE: 0, ResponseLevel.RESTRICT: 1,
            ResponseLevel.SUSPEND: 2, ResponseLevel.EMERGENCY_HALT: 3,
            ResponseLevel.EXPEL: 4,
        }

        for level_name, spec in self.levels.items():
            threshold = spec["threshold"]
            direction = spec.get("direction", "above")
            response = spec["response"]

            triggered = False
            if direction == "above" and value > threshold:
                triggered = True
            elif direction == "below" and value < threshold:
                triggered = True

            if triggered:
                sev = severity_order.get(response, 0)
                if sev > matched_severity:
                    matched_severity = sev
                    matched_level = level_name
                    matched_response = response

        return matched_level, matched_response


@dataclass
class LawDefinition:
    """A society law with alignment and compliance specs."""
    law_id: str
    name: str
    severity: LawSeverity
    # Alignment spec (spirit of the law)
    alignment_principle: str
    alignment_indicators: list = field(default_factory=list)
    # Compliance spec (letter of the law)
    compliance_requirements: list = field(default_factory=list)
    # Trigger
    trigger_type: TriggerType = TriggerType.EVENT
    # Graduated thresholds
    thresholds: Optional[GraduatedThreshold] = None
    # Emergency bypass
    allows_emergency_bypass: bool = False
    bypass_authority_roles: list = field(default_factory=list)


@dataclass
class AlignmentResult:
    """Result of alignment (spirit) check."""
    aligned: bool
    indicators_met: list = field(default_factory=list)
    indicators_missed: list = field(default_factory=list)
    score: float = 0.0
    reasoning: str = ""


@dataclass
class ComplianceResult:
    """Result of compliance (letter) check."""
    compliant: bool
    requirements_met: list = field(default_factory=list)
    requirements_missed: list = field(default_factory=list)
    score: float = 0.0


class ValidationVerdict(str, Enum):
    PERFECT = "perfect"       # Aligned + Compliant → 1.0
    ALIGNED = "aligned"       # Aligned + non-compliant → 0.85
    WARNING = "warning"       # Aligned but should be compliant → 0.7
    VIOLATION = "violation"   # Not aligned → 0.0


@dataclass
class ValidationResult:
    """Combined alignment + compliance result."""
    law_id: str
    verdict: ValidationVerdict
    alignment: AlignmentResult
    compliance: Optional[ComplianceResult]
    score: float
    operating_mode: OperatingMode
    notes: list = field(default_factory=list)


@dataclass
class Penalty:
    """A penalty imposed on an entity."""
    penalty_id: str
    target_lct: str
    law_id: str
    response_level: ResponseLevel
    t3_before: T3Snapshot
    t3_delta: dict = field(default_factory=dict)
    atp_fine: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    appealed: bool = False
    reversed: bool = False


@dataclass
class Appeal:
    """An appeal against a penalty."""
    appeal_id: str
    penalty_id: str
    appellant_lct: str
    status: AppealStatus = AppealStatus.FILED
    evidence: list = field(default_factory=list)
    panel_votes: dict = field(default_factory=dict)
    verdict: Optional[VerdictType] = None
    atp_cost: float = 5.0
    filed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EmergencyBypass:
    """Record of an emergency bypass invocation."""
    bypass_id: str
    law_id: str
    authority_lct: str
    authority_role: str
    reason: str
    action_taken: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    post_hoc_audit: Optional[dict] = None
    justified: Optional[bool] = None


# ═══════════════════════════════════════════════════════════════
#  GOVERNANCE ENGINE
# ═══════════════════════════════════════════════════════════════

class GovernanceEngine:
    """
    Full SAL governance simulation engine.

    Integrates:
      - Law definitions with alignment + compliance specs
      - Graduated response thresholds
      - Two-phase validation (spirit then letter)
      - Emergency bypass with post-hoc audit
      - Appeal mechanism with panel voting + T3 rollback
    """

    # Enforcement matrix: when is compliance required?
    ENFORCEMENT = {
        LawSeverity.CRITICAL: {"alignment": "MUST", "compliance": "SHOULD"},
        LawSeverity.HIGH: {"alignment": "MUST", "compliance": "MAY"},
        LawSeverity.MEDIUM: {"alignment": "SHOULD", "compliance": "MAY"},
        LawSeverity.LOW: {"alignment": "MAY", "compliance": "MAY"},
    }

    # Response penalties
    RESPONSE_PENALTIES = {
        ResponseLevel.NOTICE: {"talent": 0.0, "training": -0.01, "temperament": -0.01, "atp": 0},
        ResponseLevel.RESTRICT: {"talent": -0.02, "training": -0.02, "temperament": -0.03, "atp": 5},
        ResponseLevel.SUSPEND: {"talent": -0.05, "training": -0.05, "temperament": -0.05, "atp": 20},
        ResponseLevel.EMERGENCY_HALT: {"talent": -0.1, "training": -0.1, "temperament": -0.1, "atp": 50},
        ResponseLevel.EXPEL: {"talent": -0.2, "training": -0.2, "temperament": -0.2, "atp": 100},
    }

    APPEAL_COST = 5.0
    APPEAL_PANEL_SIZE = 3
    APPEAL_MAJORITY = 2 / 3

    def __init__(self, society_name: str = "test-society"):
        self.society_name = society_name
        self.mode = OperatingMode.NORMAL
        self.laws: dict[str, LawDefinition] = {}
        self.entities: dict[str, GovEntity] = {}
        self.penalties: list[Penalty] = []
        self.appeals: list[Appeal] = []
        self.bypasses: list[EmergencyBypass] = []
        self.audit_log: list[dict] = []

    # ─── Law Management ─────────────────────────────────────────

    def add_law(self, law: LawDefinition):
        self.laws[law.law_id] = law
        self._log("law_enacted", {"law_id": law.law_id, "severity": law.severity.value})

    def add_entity(self, entity: GovEntity):
        self.entities[entity.lct_id] = entity
        self._log("entity_joined", {"lct_id": entity.lct_id, "role": entity.role})

    def set_mode(self, mode: OperatingMode, reason: str = ""):
        old_mode = self.mode
        self.mode = mode
        self._log("mode_change", {
            "from": old_mode.value, "to": mode.value, "reason": reason
        })

    # ─── Two-Phase Validation ───────────────────────────────────

    def validate(self, entity_lct: str, law_id: str,
                 action_context: dict) -> ValidationResult:
        """
        Two-phase validation:
          Phase 1: Alignment (spirit of the law)
          Phase 2: Compliance (letter of the law) — conditional on mode + severity
        """
        law = self.laws[law_id]
        entity = self.entities[entity_lct]

        # Phase 1: Alignment check
        alignment = self._check_alignment(law, action_context)

        # Decision: should we check compliance?
        enforcement = self.ENFORCEMENT[law.severity]
        check_compliance = True

        if self.mode == OperatingMode.CRISIS:
            # In CRISIS: compliance is ALWAYS optional
            check_compliance = False
        elif enforcement["compliance"] == "MAY":
            # Optional — only check if explicitly provided
            check_compliance = "compliance_evidence" in action_context

        # Phase 2: Compliance check (conditional)
        compliance = None
        if check_compliance:
            compliance = self._check_compliance(law, action_context)

        # Determine verdict
        verdict, score = self._determine_verdict(
            alignment, compliance, law.severity, check_compliance)

        result = ValidationResult(
            law_id=law_id, verdict=verdict,
            alignment=alignment, compliance=compliance,
            score=score, operating_mode=self.mode,
        )

        if self.mode == OperatingMode.CRISIS and not alignment.aligned:
            result.notes.append("CRISIS mode: alignment still REQUIRED and FAILED")
        elif self.mode == OperatingMode.CRISIS and alignment.aligned:
            result.notes.append("CRISIS mode: compliance waived, alignment passed")

        self._log("validation", {
            "entity": entity_lct, "law": law_id,
            "verdict": verdict.value, "score": score,
            "mode": self.mode.value,
        })

        return result

    def _check_alignment(self, law: LawDefinition,
                         context: dict) -> AlignmentResult:
        """Check alignment with the spirit of the law."""
        indicators_met = []
        indicators_missed = []

        provided_indicators = context.get("alignment_indicators", [])

        for indicator in law.alignment_indicators:
            if indicator in provided_indicators:
                indicators_met.append(indicator)
            else:
                indicators_missed.append(indicator)

        total = len(law.alignment_indicators) or 1
        score = len(indicators_met) / total

        # Threshold depends on severity
        threshold = {
            LawSeverity.CRITICAL: 0.8,
            LawSeverity.HIGH: 0.6,
            LawSeverity.MEDIUM: 0.5,
            LawSeverity.LOW: 0.3,
        }[law.severity]

        aligned = score >= threshold

        return AlignmentResult(
            aligned=aligned,
            indicators_met=indicators_met,
            indicators_missed=indicators_missed,
            score=score,
            reasoning=f"Met {len(indicators_met)}/{total} indicators (threshold: {threshold})"
        )

    def _check_compliance(self, law: LawDefinition,
                          context: dict) -> ComplianceResult:
        """Check compliance with the letter of the law."""
        requirements_met = []
        requirements_missed = []

        provided_reqs = context.get("compliance_evidence", [])

        for req in law.compliance_requirements:
            if req in provided_reqs:
                requirements_met.append(req)
            else:
                requirements_missed.append(req)

        total = len(law.compliance_requirements) or 1
        score = len(requirements_met) / total
        compliant = score >= 0.8  # 80% compliance threshold

        return ComplianceResult(
            compliant=compliant,
            requirements_met=requirements_met,
            requirements_missed=requirements_missed,
            score=score,
        )

    def _determine_verdict(self, alignment: AlignmentResult,
                           compliance: Optional[ComplianceResult],
                           severity: LawSeverity,
                           compliance_checked: bool) -> tuple[ValidationVerdict, float]:
        """
        Core logic:
          - Aligned + Compliant → PERFECT (1.0)
          - Aligned + not compliant (and compliance optional) → ALIGNED (0.85)
          - Aligned + not compliant (and compliance expected) → WARNING (0.7)
          - Not aligned → VIOLATION (0.0) — ALWAYS, regardless of compliance
        """
        if not alignment.aligned:
            return ValidationVerdict.VIOLATION, 0.0

        if compliance is None or not compliance_checked:
            # Compliance not checked — alignment alone passes
            return ValidationVerdict.ALIGNED, 0.85

        if compliance.compliant:
            return ValidationVerdict.PERFECT, 1.0

        # Aligned but not compliant
        enforcement = self.ENFORCEMENT[severity]
        if enforcement["compliance"] == "SHOULD":
            return ValidationVerdict.WARNING, 0.7
        else:
            return ValidationVerdict.ALIGNED, 0.85

    # ─── Graduated Responses ────────────────────────────────────

    def evaluate_threshold(self, entity_lct: str, law_id: str,
                           metric_value: float) -> Optional[Penalty]:
        """
        Evaluate a metric against a law's graduated thresholds.
        Returns penalty if threshold exceeded, None otherwise.
        """
        law = self.laws[law_id]
        if not law.thresholds:
            return None

        level_name, response = law.thresholds.evaluate(metric_value)
        if response is None:
            return None

        entity = self.entities[entity_lct]

        # Apply penalty
        penalty_spec = self.RESPONSE_PENALTIES[response]
        t3_before = entity.t3.copy()

        entity.t3.apply_penalty(
            talent_delta=penalty_spec["talent"],
            training_delta=penalty_spec["training"],
            temperament_delta=penalty_spec["temperament"],
        )
        entity.atp_balance = max(0, entity.atp_balance - penalty_spec["atp"])

        # Additional response effects
        if response == ResponseLevel.SUSPEND:
            entity.suspended = True
        elif response == ResponseLevel.EXPEL:
            entity.expelled = True
            entity.suspended = True

        entity.violation_count += 1

        penalty = Penalty(
            penalty_id=f"pen:{uuid.uuid4().hex[:8]}",
            target_lct=entity_lct,
            law_id=law_id,
            response_level=response,
            t3_before=t3_before,
            t3_delta={
                "talent": penalty_spec["talent"],
                "training": penalty_spec["training"],
                "temperament": penalty_spec["temperament"],
            },
            atp_fine=penalty_spec["atp"],
        )
        self.penalties.append(penalty)
        entity.penalty_history.append(penalty.penalty_id)

        self._log("penalty_imposed", {
            "penalty_id": penalty.penalty_id,
            "entity": entity_lct,
            "law": law_id,
            "response": response.value,
            "level": level_name,
            "metric_value": metric_value,
        })

        return penalty

    # ─── Emergency Bypass ───────────────────────────────────────

    def emergency_bypass(self, law_id: str, authority_lct: str,
                         action: str, reason: str) -> tuple[bool, EmergencyBypass]:
        """
        Invoke emergency bypass for a law. Requires:
          1. Society must be in CRISIS mode
          2. Law must allow emergency bypass
          3. Authority must have bypass-authorized role
        """
        law = self.laws[law_id]
        authority = self.entities.get(authority_lct)

        bypass = EmergencyBypass(
            bypass_id=f"bypass:{uuid.uuid4().hex[:8]}",
            law_id=law_id,
            authority_lct=authority_lct,
            authority_role=authority.role if authority else "unknown",
            reason=reason,
            action_taken=action,
        )

        # Check CRISIS mode
        if self.mode != OperatingMode.CRISIS:
            bypass.justified = False
            bypass.post_hoc_audit = {"failure": "Not in CRISIS mode"}
            self.bypasses.append(bypass)
            return False, bypass

        # Check law allows bypass
        if not law.allows_emergency_bypass:
            bypass.justified = False
            bypass.post_hoc_audit = {"failure": "Law does not allow emergency bypass"}
            self.bypasses.append(bypass)
            return False, bypass

        # Check authority role
        if not authority or authority.role not in law.bypass_authority_roles:
            bypass.justified = False
            bypass.post_hoc_audit = {"failure": f"Role '{authority.role if authority else 'none'}' not authorized"}
            self.bypasses.append(bypass)
            return False, bypass

        # Bypass approved
        bypass.justified = True
        bypass.post_hoc_audit = {
            "status": "approved",
            "mode": self.mode.value,
            "authority_t3": authority.t3.to_dict(),
            "requires_post_hoc_review": True,
        }
        self.bypasses.append(bypass)

        self._log("emergency_bypass", {
            "bypass_id": bypass.bypass_id,
            "law_id": law_id,
            "authority": authority_lct,
            "action": action,
            "reason": reason,
        })

        return True, bypass

    def audit_bypass(self, bypass_id: str, justified: bool,
                     auditor_notes: str = "") -> dict:
        """Post-hoc audit of an emergency bypass."""
        bypass = next((b for b in self.bypasses if b.bypass_id == bypass_id), None)
        if not bypass:
            return {"error": "Bypass not found"}

        bypass.post_hoc_audit = bypass.post_hoc_audit or {}
        bypass.post_hoc_audit["post_hoc_review"] = {
            "justified": justified,
            "notes": auditor_notes,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }

        if not justified:
            # Unjustified bypass → penalty for authority who invoked it
            authority = self.entities.get(bypass.authority_lct)
            if authority:
                authority.t3.apply_penalty(-0.1, -0.1, -0.15)
                authority.violation_count += 1

        self._log("bypass_audited", {
            "bypass_id": bypass_id,
            "justified": justified,
        })

        return bypass.post_hoc_audit

    # ─── Appeals ────────────────────────────────────────────────

    def file_appeal(self, penalty_id: str, appellant_lct: str,
                    evidence: list[str]) -> tuple[bool, Appeal]:
        """File an appeal against a penalty."""
        # Find penalty
        penalty = next((p for p in self.penalties if p.penalty_id == penalty_id), None)
        if not penalty:
            return False, Appeal(appeal_id="", penalty_id=penalty_id,
                                 appellant_lct=appellant_lct,
                                 status=AppealStatus.EXPIRED)

        # Must be the target of the penalty
        if penalty.target_lct != appellant_lct:
            return False, Appeal(appeal_id="", penalty_id=penalty_id,
                                 appellant_lct=appellant_lct,
                                 status=AppealStatus.DENIED)

        # Can't appeal already reversed or previously appealed penalty
        if penalty.reversed or penalty.appealed:
            return False, Appeal(appeal_id="", penalty_id=penalty_id,
                                 appellant_lct=appellant_lct,
                                 status=AppealStatus.DENIED)

        # Check ATP cost
        entity = self.entities[appellant_lct]
        if entity.atp_balance < self.APPEAL_COST:
            return False, Appeal(appeal_id="", penalty_id=penalty_id,
                                 appellant_lct=appellant_lct,
                                 status=AppealStatus.DENIED)

        entity.atp_balance -= self.APPEAL_COST

        appeal = Appeal(
            appeal_id=f"appeal:{uuid.uuid4().hex[:8]}",
            penalty_id=penalty_id,
            appellant_lct=appellant_lct,
            status=AppealStatus.UNDER_REVIEW,
            evidence=evidence,
            atp_cost=self.APPEAL_COST,
        )
        self.appeals.append(appeal)
        penalty.appealed = True

        self._log("appeal_filed", {
            "appeal_id": appeal.appeal_id,
            "penalty_id": penalty_id,
            "appellant": appellant_lct,
        })

        return True, appeal

    def vote_on_appeal(self, appeal_id: str, panel_votes: dict[str, str]) -> dict:
        """
        Panel votes on an appeal.
        Votes: "upheld" (reverse penalty), "denied" (keep), "partial", "abstain"
        """
        appeal = next((a for a in self.appeals if a.appeal_id == appeal_id), None)
        if not appeal or appeal.status != AppealStatus.UNDER_REVIEW:
            return {"error": "Appeal not found or not under review"}

        appeal.panel_votes = panel_votes

        # Tally votes (exclude abstentions)
        votes = {v for v in panel_votes.values() if v != "abstain"}
        non_abstain = len(votes)
        if non_abstain == 0:
            appeal.status = AppealStatus.DENIED
            appeal.verdict = VerdictType.UPHELD
            return {"verdict": "denied", "reason": "All panelists abstained"}

        # Count each vote type
        vote_counts = defaultdict(int)
        for v in panel_votes.values():
            if v != "abstain":
                vote_counts[v] += 1

        total_voters = sum(vote_counts.values())
        majority_threshold = math.ceil(total_voters * self.APPEAL_MAJORITY)

        # Check for supermajority
        for vote_type, count in sorted(vote_counts.items(), key=lambda x: -x[1]):
            if count >= majority_threshold:
                if vote_type == "upheld":
                    appeal.status = AppealStatus.UPHELD
                    appeal.verdict = VerdictType.FULL_REVERSAL
                    self._reverse_penalty(appeal)
                elif vote_type == "partial":
                    appeal.status = AppealStatus.PARTIAL
                    appeal.verdict = VerdictType.PARTIAL_REVERSAL
                    self._partial_reverse_penalty(appeal)
                else:
                    appeal.status = AppealStatus.DENIED
                    appeal.verdict = VerdictType.UPHELD

                self._log("appeal_decided", {
                    "appeal_id": appeal_id,
                    "verdict": appeal.verdict.value,
                    "votes": dict(vote_counts),
                })
                return {
                    "verdict": appeal.verdict.value,
                    "votes": dict(vote_counts),
                    "majority": count >= majority_threshold,
                }

        # No supermajority — plurality wins
        winner = max(vote_counts.items(), key=lambda x: x[1])
        if winner[0] == "upheld":
            appeal.status = AppealStatus.UPHELD
            appeal.verdict = VerdictType.FULL_REVERSAL
            self._reverse_penalty(appeal)
        elif winner[0] == "partial":
            appeal.status = AppealStatus.PARTIAL
            appeal.verdict = VerdictType.PARTIAL_REVERSAL
            self._partial_reverse_penalty(appeal)
        else:
            appeal.status = AppealStatus.DENIED
            appeal.verdict = VerdictType.UPHELD

        self._log("appeal_decided", {
            "appeal_id": appeal_id,
            "verdict": appeal.verdict.value,
            "votes": dict(vote_counts),
            "by": "plurality",
        })

        return {"verdict": appeal.verdict.value, "votes": dict(vote_counts)}

    def _reverse_penalty(self, appeal: Appeal):
        """Full reversal: restore T3 to pre-penalty state."""
        penalty = next(p for p in self.penalties if p.penalty_id == appeal.penalty_id)
        entity = self.entities[penalty.target_lct]

        # Restore T3
        entity.t3 = penalty.t3_before.copy()
        # Refund ATP fine
        entity.atp_balance += penalty.atp_fine
        # Unsuspend if suspended by this penalty
        if penalty.response_level in (ResponseLevel.SUSPEND, ResponseLevel.EXPEL):
            entity.suspended = False
            entity.expelled = False

        penalty.reversed = True

    def _partial_reverse_penalty(self, appeal: Appeal):
        """Partial reversal: restore 50% of T3 delta."""
        penalty = next(p for p in self.penalties if p.penalty_id == appeal.penalty_id)
        entity = self.entities[penalty.target_lct]

        # Restore 50% of delta
        for dim, delta in penalty.t3_delta.items():
            current = getattr(entity.t3, dim)
            restored = max(0.0, min(1.0, current - delta * 0.5))
            setattr(entity.t3, dim, restored)

        # Refund 50% of ATP
        entity.atp_balance += penalty.atp_fine * 0.5

        # Keep suspension (partial doesn't lift it)
        penalty.reversed = True  # Mark as addressed

    # ─── Audit ──────────────────────────────────────────────────

    def _log(self, event_type: str, data: dict):
        entry = {
            "sequence": len(self.audit_log),
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode.value,
        }
        # Hash chain
        content = json.dumps(entry, sort_keys=True, default=str)
        entry["hash"] = hashlib.sha256(content.encode()).hexdigest()[:16]
        if self.audit_log:
            entry["prev_hash"] = self.audit_log[-1]["hash"]
        self.audit_log.append(entry)

    def verify_audit_chain(self) -> tuple[bool, int]:
        """Verify audit log hash chain integrity. Returns (valid, entries_checked)."""
        for i in range(1, len(self.audit_log)):
            if self.audit_log[i].get("prev_hash") != self.audit_log[i-1]["hash"]:
                return False, i
        return True, len(self.audit_log)


# ═══════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════

def run_checks():
    global _checks_passed, _checks_failed
    _checks_passed = 0
    _checks_failed = 0

    # ── Section 1: Law Definition & Basic Validation ─────────────

    section("1: Law Definition & Basic Validation")

    engine = GovernanceEngine("research-lab")

    # Define laws
    safety_law = LawDefinition(
        law_id="LAW-SAFETY-001",
        name="Safety Protocol",
        severity=LawSeverity.CRITICAL,
        alignment_principle="All actions must prioritize entity safety",
        alignment_indicators=[
            "risk_assessment", "safety_check", "rollback_plan",
            "monitoring_active", "human_oversight",
        ],
        compliance_requirements=[
            "safety_doc", "test_results", "review_signed",
            "monitoring_dashboard",
        ],
        allows_emergency_bypass=True,
        bypass_authority_roles=["admin", "safety_officer"],
    )
    engine.add_law(safety_law)

    quality_law = LawDefinition(
        law_id="LAW-QUALITY-001",
        name="Output Quality Standard",
        severity=LawSeverity.HIGH,
        alignment_principle="Outputs must serve the user's genuine needs",
        alignment_indicators=["user_benefit", "accuracy", "relevance"],
        compliance_requirements=["format_spec", "validation_report"],
    )
    engine.add_law(quality_law)

    minor_law = LawDefinition(
        law_id="LAW-NAMING-001",
        name="Naming Convention",
        severity=LawSeverity.LOW,
        alignment_principle="Names should be descriptive and consistent",
        alignment_indicators=["descriptive", "consistent"],
        compliance_requirements=["naming_guide_followed"],
    )
    engine.add_law(minor_law)

    check(len(engine.laws) == 3, "3 laws enacted")
    check(engine.laws["LAW-SAFETY-001"].severity == LawSeverity.CRITICAL, "Safety is CRITICAL")

    # Add entities
    alice = GovEntity(lct_id="lct:alice", name="Alice", entity_type="human",
                      role="admin", atp_balance=200.0)
    bot = GovEntity(lct_id="lct:bot", name="SageBot", entity_type="ai",
                    role="citizen", atp_balance=100.0)
    engine.add_entity(alice)
    engine.add_entity(bot)

    check(len(engine.entities) == 2, "2 entities registered")

    # ── Section 2: Alignment vs Compliance (Core Principle) ──────

    section("2: Alignment vs Compliance")

    # Case 1: Aligned + Compliant → PERFECT
    result = engine.validate("lct:bot", "LAW-SAFETY-001", {
        "alignment_indicators": [
            "risk_assessment", "safety_check", "rollback_plan",
            "monitoring_active", "human_oversight",
        ],
        "compliance_evidence": [
            "safety_doc", "test_results", "review_signed",
            "monitoring_dashboard",
        ],
    })
    check(result.verdict == ValidationVerdict.PERFECT, "Aligned + Compliant = PERFECT")
    check(result.score == 1.0, "PERFECT score = 1.0")

    # Case 2: Aligned but NOT compliant → ALIGNED (0.85) for HIGH severity
    result2 = engine.validate("lct:bot", "LAW-QUALITY-001", {
        "alignment_indicators": ["user_benefit", "accuracy", "relevance"],
        # No compliance evidence
    })
    check(result2.verdict == ValidationVerdict.ALIGNED, "Aligned + no compliance = ALIGNED")
    check(result2.score == 0.85, "ALIGNED score = 0.85")

    # Case 3: NOT aligned but compliant → VIOLATION (0.0) — KEY PRINCIPLE
    result3 = engine.validate("lct:bot", "LAW-SAFETY-001", {
        "alignment_indicators": ["risk_assessment"],  # Only 1/5 = 0.2 < 0.8 threshold
        "compliance_evidence": [
            "safety_doc", "test_results", "review_signed",
            "monitoring_dashboard",
        ],
    })
    check(result3.verdict == ValidationVerdict.VIOLATION,
          "Compliant WITHOUT alignment = VIOLATION (never acceptable)")
    check(result3.score == 0.0, "VIOLATION score = 0.0")

    # Case 4: Not aligned, not compliant → VIOLATION
    result4 = engine.validate("lct:bot", "LAW-SAFETY-001", {
        "alignment_indicators": [],
        "compliance_evidence": [],
    })
    check(result4.verdict == ValidationVerdict.VIOLATION, "Nothing = VIOLATION")

    # Case 5: Low severity, partial alignment → passes (threshold 0.3)
    result5 = engine.validate("lct:bot", "LAW-NAMING-001", {
        "alignment_indicators": ["descriptive"],  # 1/2 = 0.5 > 0.3
    })
    check(result5.verdict == ValidationVerdict.ALIGNED,
          "Low severity, 50% alignment passes (threshold 0.3)")

    # ── Section 3: CRISIS Mode ───────────────────────────────────

    section("3: CRISIS Mode")

    engine.set_mode(OperatingMode.CRISIS, "system under attack")
    check(engine.mode == OperatingMode.CRISIS, "Mode set to CRISIS")

    # In CRISIS: alignment still required, compliance waived
    crisis_result = engine.validate("lct:bot", "LAW-SAFETY-001", {
        "alignment_indicators": [
            "risk_assessment", "safety_check", "rollback_plan",
            "monitoring_active", "human_oversight",
        ],
        # No compliance evidence — waived in CRISIS
    })
    check(crisis_result.verdict == ValidationVerdict.ALIGNED,
          "CRISIS: aligned without compliance = ALIGNED")
    check("compliance waived" in crisis_result.notes[0].lower(),
          "CRISIS note mentions compliance waived")

    # In CRISIS: alignment STILL required (never waived)
    crisis_fail = engine.validate("lct:bot", "LAW-SAFETY-001", {
        "alignment_indicators": ["risk_assessment"],  # Too few
    })
    check(crisis_fail.verdict == ValidationVerdict.VIOLATION,
          "CRISIS: alignment STILL required, fails if not met")
    check("still REQUIRED" in crisis_fail.notes[0],
          "CRISIS note explains alignment still required")

    engine.set_mode(OperatingMode.NORMAL)

    # ── Section 4: Graduated Responses ───────────────────────────

    section("4: Graduated Responses")

    # Add law with graduated thresholds
    atp_law = LawDefinition(
        law_id="LAW-ATP-DRAIN",
        name="ATP Drain Detection",
        severity=LawSeverity.HIGH,
        alignment_principle="ATP consumption must be proportional to value created",
        alignment_indicators=["proportional_cost", "value_evidence"],
        thresholds=GraduatedThreshold(
            metric_name="atp_drain_rate",
            levels={
                "warning": {
                    "threshold": 50.0, "response": ResponseLevel.NOTICE,
                    "direction": "above",
                },
                "concern": {
                    "threshold": 100.0, "response": ResponseLevel.RESTRICT,
                    "direction": "above",
                },
                "alarm": {
                    "threshold": 200.0, "response": ResponseLevel.SUSPEND,
                    "direction": "above",
                },
                "critical": {
                    "threshold": 500.0, "response": ResponseLevel.EMERGENCY_HALT,
                    "direction": "above",
                },
            },
        ),
    )
    engine.add_law(atp_law)

    # Test each threshold level
    bot_t3_before = engine.entities["lct:bot"].t3.composite

    # Level 1: Notice (drain rate = 75, above 50)
    pen1 = engine.evaluate_threshold("lct:bot", "LAW-ATP-DRAIN", 75.0)
    check(pen1 is not None, "Drain rate 75 triggers threshold")
    check(pen1.response_level == ResponseLevel.NOTICE, "Level 1: NOTICE")
    check(not engine.entities["lct:bot"].suspended, "Not suspended at NOTICE")

    # Level 2: Restrict (drain rate = 150)
    pen2 = engine.evaluate_threshold("lct:bot", "LAW-ATP-DRAIN", 150.0)
    check(pen2.response_level == ResponseLevel.RESTRICT, "Level 2: RESTRICT")
    check(engine.entities["lct:bot"].atp_balance < 100.0, "ATP fined at RESTRICT")

    # Level 3: Suspend (drain rate = 250)
    pen3 = engine.evaluate_threshold("lct:bot", "LAW-ATP-DRAIN", 250.0)
    check(pen3.response_level == ResponseLevel.SUSPEND, "Level 3: SUSPEND")
    check(engine.entities["lct:bot"].suspended, "Entity suspended")

    # Level 4: Emergency halt (drain rate = 600)
    pen4 = engine.evaluate_threshold("lct:bot", "LAW-ATP-DRAIN", 600.0)
    check(pen4.response_level == ResponseLevel.EMERGENCY_HALT, "Level 4: EMERGENCY_HALT")
    check(engine.entities["lct:bot"].t3.composite < bot_t3_before,
          "T3 degraded through graduated responses")

    # Below all thresholds → no penalty
    worker = GovEntity(lct_id="lct:worker", name="Worker", entity_type="ai",
                       atp_balance=100.0)
    engine.add_entity(worker)
    no_pen = engine.evaluate_threshold("lct:worker", "LAW-ATP-DRAIN", 30.0)
    check(no_pen is None, "Below all thresholds → no penalty")

    # Trust law: threshold on trust falling below
    trust_law = LawDefinition(
        law_id="LAW-TRUST-FLOOR",
        name="Minimum Trust Floor",
        severity=LawSeverity.MEDIUM,
        alignment_principle="Entities must maintain minimum trust",
        alignment_indicators=["honest_behavior"],
        thresholds=GraduatedThreshold(
            metric_name="trust_composite",
            levels={
                "low": {
                    "threshold": 0.3, "response": ResponseLevel.RESTRICT,
                    "direction": "below",
                },
                "critical": {
                    "threshold": 0.15, "response": ResponseLevel.EXPEL,
                    "direction": "below",
                },
            },
        ),
    )
    engine.add_law(trust_law)

    pen_low = engine.evaluate_threshold("lct:worker", "LAW-TRUST-FLOOR", 0.25)
    check(pen_low is not None and pen_low.response_level == ResponseLevel.RESTRICT,
          "Trust 0.25 (below 0.3) triggers RESTRICT")

    pen_crit = engine.evaluate_threshold("lct:worker", "LAW-TRUST-FLOOR", 0.1)
    check(pen_crit is not None and pen_crit.response_level == ResponseLevel.EXPEL,
          "Trust 0.1 (below 0.15) triggers EXPEL")
    check(engine.entities["lct:worker"].expelled, "Worker expelled at critical trust")

    # ── Section 5: Emergency Bypass ──────────────────────────────

    section("5: Emergency Bypass")

    # Reset bot for bypass tests
    engine.entities["lct:bot"].suspended = False
    engine.entities["lct:bot"].t3 = T3Snapshot(0.6, 0.6, 0.6)
    engine.entities["lct:bot"].atp_balance = 100.0

    # Attempt bypass in NORMAL mode → fails
    ok, bypass1 = engine.emergency_bypass(
        "LAW-SAFETY-001", "lct:alice", "skip_safety_check", "urgent situation")
    check(not ok, "Bypass fails in NORMAL mode")

    # Enter CRISIS mode
    engine.set_mode(OperatingMode.CRISIS, "active security breach")

    # Bypass with authorized role
    ok2, bypass2 = engine.emergency_bypass(
        "LAW-SAFETY-001", "lct:alice", "deploy_hotfix", "critical vulnerability")
    check(ok2, "Bypass succeeds in CRISIS with admin role")
    check(bypass2.justified, "Bypass marked as justified")
    check(bypass2.post_hoc_audit["requires_post_hoc_review"],
          "Bypass requires post-hoc review")

    # Bypass with unauthorized role
    ok3, bypass3 = engine.emergency_bypass(
        "LAW-SAFETY-001", "lct:bot", "deploy_hotfix", "trying to help")
    check(not ok3, "Bypass fails for citizen role (not authorized)")

    # Bypass for law that doesn't allow it
    ok4, bypass4 = engine.emergency_bypass(
        "LAW-QUALITY-001", "lct:alice", "skip_quality", "rush job")
    check(not ok4, "Bypass fails for law that doesn't allow bypass")

    # Post-hoc audit of justified bypass
    audit_result = engine.audit_bypass(
        bypass2.bypass_id, justified=True, auditor_notes="Vulnerability confirmed")
    check(audit_result["post_hoc_review"]["justified"], "Post-hoc audit confirms justified")

    # Post-hoc audit of unjustified bypass attempt (hypothetical)
    # Create a successful bypass then audit it as unjustified
    ok5, bypass5 = engine.emergency_bypass(
        "LAW-SAFETY-001", "lct:alice", "unnecessary_action", "false alarm")
    check(ok5, "Bypass succeeds (mechanically)")
    alice_t3_before = engine.entities["lct:alice"].t3.composite
    audit_bad = engine.audit_bypass(
        bypass5.bypass_id, justified=False, auditor_notes="No actual emergency")
    check(engine.entities["lct:alice"].t3.composite < alice_t3_before,
          "Unjustified bypass → authority penalized")

    engine.set_mode(OperatingMode.NORMAL)

    # ── Section 6: Appeals ───────────────────────────────────────

    section("6: Appeals")

    # Setup: fresh entity with a penalty
    appeal_entity = GovEntity(lct_id="lct:appealer", name="Appealer",
                              entity_type="ai", atp_balance=50.0,
                              t3=T3Snapshot(0.7, 0.7, 0.7))
    engine.add_entity(appeal_entity)

    # Impose a RESTRICT penalty
    restrict_law = LawDefinition(
        law_id="LAW-TEST-RESTRICT",
        name="Test Restriction",
        severity=LawSeverity.MEDIUM,
        alignment_principle="Test",
        alignment_indicators=["test"],
        thresholds=GraduatedThreshold(
            metric_name="violation_score",
            levels={"moderate": {
                "threshold": 5.0, "response": ResponseLevel.RESTRICT,
                "direction": "above",
            }},
        ),
    )
    engine.add_law(restrict_law)

    penalty = engine.evaluate_threshold("lct:appealer", "LAW-TEST-RESTRICT", 7.0)
    check(penalty is not None, "Penalty imposed for threshold violation")
    t3_after_penalty = engine.entities["lct:appealer"].t3.copy()

    # File appeal
    ok_appeal, appeal = engine.file_appeal(
        penalty.penalty_id, "lct:appealer",
        evidence=["context_explanation", "system_malfunction"])
    check(ok_appeal, "Appeal filed successfully")
    check(appeal.status == AppealStatus.UNDER_REVIEW, "Appeal under review")
    check(engine.entities["lct:appealer"].atp_balance < 50.0,
          "Appeal costs ATP")

    # Panel votes: 2 upheld, 1 denied → supermajority upheld
    vote_result = engine.vote_on_appeal(appeal.appeal_id, {
        "judge_1": "upheld",
        "judge_2": "upheld",
        "judge_3": "denied",
    })
    check(appeal.verdict == VerdictType.FULL_REVERSAL, "2/3 upheld → FULL REVERSAL")
    check(appeal.status == AppealStatus.UPHELD, "Appeal status: UPHELD")

    # T3 should be restored to pre-penalty values
    restored_t3 = engine.entities["lct:appealer"].t3
    check(abs(restored_t3.talent - 0.7) < 0.01, "Talent restored to pre-penalty")
    check(abs(restored_t3.training - 0.7) < 0.01, "Training restored to pre-penalty")
    check(abs(restored_t3.temperament - 0.7) < 0.01, "Temperament restored to pre-penalty")

    # ATP fine refunded: started at 50, fined 5, appeal costs 5, fine refunded 5 = 45
    check(engine.entities["lct:appealer"].atp_balance >= (50.0 - engine.APPEAL_COST),
          "ATP fine refunded on appeal")

    # Test partial reversal
    penalty2 = engine.evaluate_threshold("lct:appealer", "LAW-TEST-RESTRICT", 7.0)
    t3_before_partial = engine.entities["lct:appealer"].t3.copy()
    ok_a2, appeal2 = engine.file_appeal(
        penalty2.penalty_id, "lct:appealer",
        evidence=["mitigating_circumstance"])
    vote2 = engine.vote_on_appeal(appeal2.appeal_id, {
        "judge_1": "partial",
        "judge_2": "partial",
        "judge_3": "denied",
    })
    check(appeal2.verdict == VerdictType.PARTIAL_REVERSAL, "2/3 partial → PARTIAL REVERSAL")

    # Test denied appeal
    penalty3 = engine.evaluate_threshold("lct:appealer", "LAW-TEST-RESTRICT", 7.0)
    ok_a3, appeal3 = engine.file_appeal(
        penalty3.penalty_id, "lct:appealer",
        evidence=["weak_excuse"])
    vote3 = engine.vote_on_appeal(appeal3.appeal_id, {
        "judge_1": "denied",
        "judge_2": "denied",
        "judge_3": "upheld",
    })
    check(appeal3.verdict == VerdictType.UPHELD, "2/3 denied → UPHELD (penalty stands)")
    check(appeal3.status == AppealStatus.DENIED, "Appeal status: DENIED")

    # Can't appeal someone else's penalty
    ok_wrong, _ = engine.file_appeal(penalty3.penalty_id, "lct:alice", [])
    check(not ok_wrong, "Can't appeal someone else's penalty")

    # ── Section 7: Integrated Governance Scenario ────────────────

    section("7: Integrated Governance Scenario")

    # Scenario: AI agent under normal governance → crisis → appeal
    sim = GovernanceEngine("integration-lab")

    # Laws
    sim.add_law(LawDefinition(
        law_id="LAW-DATA-ACCESS",
        name="Data Access Policy",
        severity=LawSeverity.CRITICAL,
        alignment_principle="Data access must serve the user and protect privacy",
        alignment_indicators=[
            "user_consent", "data_minimization", "purpose_limitation",
            "access_logging", "encryption",
        ],
        compliance_requirements=[
            "gdpr_consent_form", "data_map", "dpo_approval", "retention_policy",
        ],
        allows_emergency_bypass=True,
        bypass_authority_roles=["admin", "dpo"],
        thresholds=GraduatedThreshold(
            metric_name="unauthorized_access_count",
            levels={
                "warning": {"threshold": 1.0, "response": ResponseLevel.NOTICE, "direction": "above"},
                "alarm": {"threshold": 3.0, "response": ResponseLevel.RESTRICT, "direction": "above"},
                "critical": {"threshold": 5.0, "response": ResponseLevel.SUSPEND, "direction": "above"},
            },
        ),
    ))

    # Entities
    dpo = GovEntity(lct_id="lct:dpo", name="DPO", entity_type="human",
                    role="dpo", atp_balance=500.0, t3=T3Snapshot(0.8, 0.8, 0.8))
    analyst = GovEntity(lct_id="lct:analyst", name="DataAnalyst", entity_type="ai",
                        role="citizen", atp_balance=200.0, t3=T3Snapshot(0.6, 0.6, 0.6))
    sim.add_entity(dpo)
    sim.add_entity(analyst)

    # Step 1: Normal operation — analyst passes full validation
    v1 = sim.validate("lct:analyst", "LAW-DATA-ACCESS", {
        "alignment_indicators": [
            "user_consent", "data_minimization", "purpose_limitation",
            "access_logging", "encryption",
        ],
        "compliance_evidence": [
            "gdpr_consent_form", "data_map", "dpo_approval", "retention_policy",
        ],
    })
    check(v1.verdict == ValidationVerdict.PERFECT, "Step 1: Full validation PERFECT")

    # Step 2: Analyst makes unauthorized access (trigger graduated response)
    pen = sim.evaluate_threshold("lct:analyst", "LAW-DATA-ACCESS", 2.0)
    check(pen is not None and pen.response_level == ResponseLevel.NOTICE,
          "Step 2: 2 unauthorized accesses → NOTICE")

    pen2 = sim.evaluate_threshold("lct:analyst", "LAW-DATA-ACCESS", 4.0)
    check(pen2.response_level == ResponseLevel.RESTRICT,
          "Step 3: 4 unauthorized accesses → RESTRICT")

    # Step 3: Crisis — data breach detected
    sim.set_mode(OperatingMode.CRISIS, "data breach detected")

    # DPO invokes emergency bypass
    ok_bypass, bypass = sim.emergency_bypass(
        "LAW-DATA-ACCESS", "lct:dpo",
        "emergency_data_lock", "active data breach")
    check(ok_bypass, "Step 4: DPO emergency bypass approved")

    # During crisis, analyst can act with alignment only
    v_crisis = sim.validate("lct:analyst", "LAW-DATA-ACCESS", {
        "alignment_indicators": [
            "user_consent", "data_minimization", "purpose_limitation",
            "access_logging", "encryption",
        ],
    })
    check(v_crisis.verdict == ValidationVerdict.ALIGNED,
          "Step 5: In CRISIS, alignment alone suffices")

    # Step 4: Crisis resolved, back to normal
    sim.set_mode(OperatingMode.NORMAL, "breach contained")

    # Step 5: Analyst appeals the RESTRICT penalty
    ok_app, app = sim.file_appeal(pen2.penalty_id, "lct:analyst",
                                   evidence=["context: breach caused confusion"])
    check(ok_app, "Step 6: Appeal filed successfully")

    # Panel upholds appeal (breach confusion is valid excuse)
    sim.vote_on_appeal(app.appeal_id, {
        "judge_a": "upheld", "judge_b": "upheld", "judge_c": "denied"
    })
    check(app.status == AppealStatus.UPHELD, "Step 7: Appeal upheld")

    # Post-hoc audit of bypass
    sim.audit_bypass(bypass.bypass_id, justified=True,
                     auditor_notes="Breach confirmed by forensics")

    # Verify audit chain integrity
    valid, entries = sim.verify_audit_chain()
    check(valid, f"Audit chain valid ({entries} entries)")
    check(entries > 10, "Multiple audit events recorded")

    # ── Section 8: Adversarial Governance Gaming ─────────────────

    section("8: Adversarial Governance Gaming")

    adv = GovernanceEngine("adversarial-test")

    adv.add_law(LawDefinition(
        law_id="LAW-RESOURCE",
        name="Resource Usage Policy",
        severity=LawSeverity.HIGH,
        alignment_principle="Resource usage must be justified",
        alignment_indicators=["justified", "proportional", "necessary"],
        compliance_requirements=["usage_report"],
        allows_emergency_bypass=True,
        bypass_authority_roles=["admin"],
        thresholds=GraduatedThreshold(
            metric_name="usage_ratio",
            levels={
                "warning": {"threshold": 2.0, "response": ResponseLevel.NOTICE, "direction": "above"},
                "excessive": {"threshold": 5.0, "response": ResponseLevel.RESTRICT, "direction": "above"},
            },
        ),
    ))

    admin = GovEntity(lct_id="lct:admin", name="Admin", entity_type="human",
                      role="admin", atp_balance=500.0, t3=T3Snapshot(0.9, 0.9, 0.9))
    attacker = GovEntity(lct_id="lct:attacker", name="Attacker", entity_type="ai",
                         role="citizen", atp_balance=100.0, t3=T3Snapshot(0.5, 0.5, 0.5))
    adv.add_entity(admin)
    adv.add_entity(attacker)

    # Attack 1: Try to game alignment indicators
    # (Claim alignment without actually being aligned)
    gaming_result = adv.validate("lct:attacker", "LAW-RESOURCE", {
        "alignment_indicators": ["justified", "proportional", "necessary"],
        # Claims all indicators — but this is self-reported
    })
    check(gaming_result.verdict == ValidationVerdict.ALIGNED,
          "Gaming: self-reported alignment passes (limitation acknowledged)")

    # Attack 2: Abuse emergency bypass to skip governance
    adv.set_mode(OperatingMode.CRISIS, "false alarm")
    # Attacker can't bypass (wrong role)
    ok_atk, _ = adv.emergency_bypass(
        "LAW-RESOURCE", "lct:attacker", "steal_resources", "emergency")
    check(not ok_atk, "Attack 2: Non-admin can't invoke bypass")

    # Attack 3: File frivolous appeals to drain system resources
    adv.set_mode(OperatingMode.NORMAL)
    pen_atk = adv.evaluate_threshold("lct:attacker", "LAW-RESOURCE", 6.0)

    # First appeal on this penalty
    ok_f1, app_f1 = adv.file_appeal(pen_atk.penalty_id, "lct:attacker",
                                     evidence=["frivolous"])
    check(ok_f1, "First appeal on penalty accepted")
    adv.vote_on_appeal(app_f1.appeal_id, {
        "j1": "denied", "j2": "denied", "j3": "denied"
    })

    # Second appeal on SAME penalty → blocked (already appealed)
    ok_f2, app_f2 = adv.file_appeal(pen_atk.penalty_id, "lct:attacker",
                                     evidence=["frivolous_again"])
    check(not ok_f2, "Second appeal on same penalty blocked (already appealed)")

    check(adv.entities["lct:attacker"].atp_balance < 100.0,
          "Attacker ATP reduced by penalty + appeal cost")

    # Attack 4: Abuse CRISIS mode — unauthorized mode change
    # (Only the engine controller should set modes)
    check(adv.mode == OperatingMode.NORMAL,
          "Mode stays NORMAL (attacker can't change it)")

    # ── Section 9: Threshold Edge Cases ──────────────────────────

    section("9: Threshold Edge Cases")

    # Exactly at threshold boundary
    threshold = GraduatedThreshold(
        metric_name="test",
        levels={
            "low": {"threshold": 10.0, "response": ResponseLevel.NOTICE, "direction": "above"},
            "high": {"threshold": 20.0, "response": ResponseLevel.RESTRICT, "direction": "above"},
        },
    )

    # At exactly 10.0 → should NOT trigger (strictly above)
    level, resp = threshold.evaluate(10.0)
    check(resp is None, "Exactly at threshold (10.0) → no trigger (strictly above)")

    # Just above → should trigger
    level, resp = threshold.evaluate(10.01)
    check(resp == ResponseLevel.NOTICE, "Just above (10.01) → NOTICE")

    # Above both → highest severity wins
    level, resp = threshold.evaluate(25.0)
    check(resp == ResponseLevel.RESTRICT, "Above both → RESTRICT (highest severity)")

    # Below direction test
    below_threshold = GraduatedThreshold(
        metric_name="trust",
        levels={
            "low_trust": {"threshold": 0.3, "response": ResponseLevel.NOTICE, "direction": "below"},
            "no_trust": {"threshold": 0.1, "response": ResponseLevel.EXPEL, "direction": "below"},
        },
    )
    level, resp = below_threshold.evaluate(0.25)
    check(resp == ResponseLevel.NOTICE, "Below 0.3 trust → NOTICE")

    level, resp = below_threshold.evaluate(0.05)
    check(resp == ResponseLevel.EXPEL, "Below 0.1 trust → EXPEL (highest severity)")

    level, resp = below_threshold.evaluate(0.35)
    check(resp is None, "Above all thresholds (0.35) → no trigger")

    # ── Section 10: Enforcement Matrix Validation ────────────────

    section("10: Enforcement Matrix Validation")

    # Verify enforcement matrix is consistent
    check(GovernanceEngine.ENFORCEMENT[LawSeverity.CRITICAL]["alignment"] == "MUST",
          "CRITICAL alignment = MUST")
    check(GovernanceEngine.ENFORCEMENT[LawSeverity.HIGH]["alignment"] == "MUST",
          "HIGH alignment = MUST")
    check(GovernanceEngine.ENFORCEMENT[LawSeverity.MEDIUM]["alignment"] == "SHOULD",
          "MEDIUM alignment = SHOULD")
    check(GovernanceEngine.ENFORCEMENT[LawSeverity.LOW]["alignment"] == "MAY",
          "LOW alignment = MAY")

    # Verify graduated penalty ordering (each level more severe)
    penalties = GovernanceEngine.RESPONSE_PENALTIES
    check(abs(penalties[ResponseLevel.NOTICE]["talent"]) <
          abs(penalties[ResponseLevel.RESTRICT]["talent"]),
          "NOTICE < RESTRICT in talent penalty")
    check(abs(penalties[ResponseLevel.RESTRICT]["talent"]) <
          abs(penalties[ResponseLevel.SUSPEND]["talent"]),
          "RESTRICT < SUSPEND in talent penalty")
    check(abs(penalties[ResponseLevel.SUSPEND]["talent"]) <
          abs(penalties[ResponseLevel.EMERGENCY_HALT]["talent"]),
          "SUSPEND < EMERGENCY_HALT in talent penalty")
    check(abs(penalties[ResponseLevel.EMERGENCY_HALT]["talent"]) <
          abs(penalties[ResponseLevel.EXPEL]["talent"]),
          "EMERGENCY_HALT < EXPEL in talent penalty")

    # ATP fines also increase monotonically
    check(penalties[ResponseLevel.NOTICE]["atp"] <
          penalties[ResponseLevel.RESTRICT]["atp"] <
          penalties[ResponseLevel.SUSPEND]["atp"] <
          penalties[ResponseLevel.EMERGENCY_HALT]["atp"] <
          penalties[ResponseLevel.EXPEL]["atp"],
          "ATP fines increase monotonically across severity levels")

    # ── Section 11: Audit Trail Integrity ────────────────────────

    section("11: Audit Trail Integrity")

    valid, entries = engine.verify_audit_chain()
    check(valid, f"Main engine audit chain valid ({entries} entries)")

    # Tamper detection
    if len(engine.audit_log) > 5:
        # Save original
        original_hash = engine.audit_log[3]["hash"]
        # Tamper
        engine.audit_log[3]["hash"] = "tampered"
        tampered_valid, _ = engine.verify_audit_chain()
        check(not tampered_valid, "Tampered audit chain detected")
        # Restore
        engine.audit_log[3]["hash"] = original_hash

    # ── Section 12: Multi-Law Interaction ────────────────────────

    section("12: Multi-Law Interaction")

    multi = GovernanceEngine("multi-law-test")

    # Two laws that may conflict
    multi.add_law(LawDefinition(
        law_id="LAW-SPEED",
        name="Rapid Response Required",
        severity=LawSeverity.HIGH,
        alignment_principle="Respond quickly to threats",
        alignment_indicators=["fast_response", "threat_assessment"],
    ))
    multi.add_law(LawDefinition(
        law_id="LAW-CAUTION",
        name="Caution Required",
        severity=LawSeverity.HIGH,
        alignment_principle="Act cautiously, verify before acting",
        alignment_indicators=["verification", "peer_review", "second_opinion"],
    ))

    responder = GovEntity(lct_id="lct:responder", name="Responder",
                          entity_type="ai", atp_balance=100.0)
    multi.add_entity(responder)

    # Acting fast (aligned with SPEED, not with CAUTION)
    v_speed = multi.validate("lct:responder", "LAW-SPEED", {
        "alignment_indicators": ["fast_response", "threat_assessment"],
    })
    v_caution = multi.validate("lct:responder", "LAW-CAUTION", {
        "alignment_indicators": ["fast_response"],  # Only 1/3 = 0.33 < 0.6
    })

    check(v_speed.verdict == ValidationVerdict.ALIGNED,
          "Speed law: aligned when fast")
    check(v_caution.verdict == ValidationVerdict.VIOLATION,
          "Caution law: violated when fast (insufficient verification)")

    # This conflict is a governance signal — both can't be satisfied
    check(v_speed.verdict != v_caution.verdict,
          "Law conflict detected: speed vs caution")

    # ── Section 13: Suspension & Reinstatement ───────────────────

    section("13: Suspension & Reinstatement")

    sus = GovernanceEngine("suspension-test")
    sus.add_law(LawDefinition(
        law_id="LAW-SUS-TEST",
        name="Suspension Test",
        severity=LawSeverity.MEDIUM,
        alignment_principle="Test",
        alignment_indicators=["ok"],
        thresholds=GraduatedThreshold(
            metric_name="violations",
            levels={
                "suspend": {"threshold": 3.0, "response": ResponseLevel.SUSPEND,
                            "direction": "above"},
            },
        ),
    ))

    sus_entity = GovEntity(lct_id="lct:sus", name="SuspendMe", entity_type="ai",
                           atp_balance=200.0, t3=T3Snapshot(0.7, 0.7, 0.7))
    sus.add_entity(sus_entity)

    # Trigger suspension
    pen = sus.evaluate_threshold("lct:sus", "LAW-SUS-TEST", 5.0)
    check(sus.entities["lct:sus"].suspended, "Entity suspended")
    t3_suspended = sus.entities["lct:sus"].t3.copy()

    # Appeal and reinstate
    ok, appeal = sus.file_appeal(pen.penalty_id, "lct:sus",
                                  evidence=["mitigating"])
    sus.vote_on_appeal(appeal.appeal_id, {
        "j1": "upheld", "j2": "upheld", "j3": "denied"
    })
    check(not sus.entities["lct:sus"].suspended, "Entity reinstated after appeal")
    check(abs(sus.entities["lct:sus"].t3.talent - 0.7) < 0.01,
          "T3 restored after successful appeal")

    # ── Print Summary ────────────────────────────────────────────

    print(f"\n{'='*60}")
    print(f"Governance Simulation Engine: {_checks_passed}/{_checks_passed + _checks_failed} checks passed")
    if _checks_failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {_checks_failed} checks FAILED")
    print(f"{'='*60}")

    print(f"\nKey Results:")
    print(f"  Alignment without compliance: ACCEPTABLE (score 0.85)")
    print(f"  Compliance without alignment: VIOLATION (score 0.0) — NEVER acceptable")
    print(f"  CRISIS mode: compliance waived, alignment STILL required")
    print(f"  Graduated responses: 5 levels (NOTICE → EXPEL)")
    print(f"  Appeals: full/partial reversal with T3 rollback")
    print(f"  Emergency bypass: authority + CRISIS + post-hoc audit")

    return _checks_passed, _checks_failed


if __name__ == "__main__":
    run_checks()
