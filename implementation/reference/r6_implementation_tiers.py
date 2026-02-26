#!/usr/bin/env python3
"""
Web4 R6 Implementation Tiers — Reference Implementation
=========================================================

Implements: web4-standard/core-spec/r6-implementation-guide.md (139 lines)

Three implementation tiers for the R6 framework:
  Tier 1: Observational — audit trail without authorization overhead
  Tier 2: Authorization — full governance with role-based access control
  Tier 3: Training Evaluation — structured AI training exercises

Each tier has its own R6 component structure, state machine, trust model,
and ID format. Tiers are progressive: records from lower tiers can be
imported into higher-tier systems.

Run: python r6_implementation_tiers.py
"""

from __future__ import annotations
import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Optional


# ============================================================
# §1  ID FORMATS (from spec table)
# ============================================================

class IDFormat:
    """Web4 R6 ID format validation and generation."""

    # Patterns from spec
    R6_REQUEST = re.compile(r'^r6:[0-9a-f]{8}$')
    AUDIT_RECORD = re.compile(r'^audit:[0-9a-f]{8}$')
    SESSION_TOKEN = re.compile(r'^web4:session:[0-9a-f]{12}$')
    LCT_HARDBOUND = re.compile(r'^lct:web4:[a-z_]+:[a-zA-Z0-9]+$')

    @staticmethod
    def generate_r6_id() -> str:
        return f"r6:{uuid.uuid4().hex[:8]}"

    @staticmethod
    def generate_audit_id() -> str:
        return f"audit:{uuid.uuid4().hex[:8]}"

    @staticmethod
    def generate_session_token() -> str:
        return f"web4:session:{uuid.uuid4().hex[:12]}"

    @staticmethod
    def generate_lct(entity_type: str, entity_id: str) -> str:
        return f"lct:web4:{entity_type}:{entity_id}"

    @classmethod
    def validate_r6_id(cls, value: str) -> bool:
        return bool(cls.R6_REQUEST.match(value))

    @classmethod
    def validate_audit_id(cls, value: str) -> bool:
        return bool(cls.AUDIT_RECORD.match(value))

    @classmethod
    def validate_session_token(cls, value: str) -> bool:
        return bool(cls.SESSION_TOKEN.match(value))

    @classmethod
    def validate_lct(cls, value: str) -> bool:
        return bool(cls.LCT_HARDBOUND.match(value))


# ============================================================
# §2  R6 STATUS STATE MACHINES
# ============================================================

class ObservationalStatus(Enum):
    """Tier 1: (implicit) → request_created → result_recorded"""
    IMPLICIT = "implicit"
    REQUEST_CREATED = "request_created"
    RESULT_RECORDED = "result_recorded"


class AuthorizationStatus(Enum):
    """Tier 2: Pending → InProgress → Approved/Rejected → Completed/Failed"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingStatus(Enum):
    """Tier 3: (implicit) → include/exclude/review"""
    IMPLICIT = "implicit"
    INCLUDE = "include"
    EXCLUDE = "exclude"
    REVIEW = "review"


# Valid transitions per tier
OBSERVATIONAL_TRANSITIONS = {
    ObservationalStatus.IMPLICIT: {ObservationalStatus.REQUEST_CREATED},
    ObservationalStatus.REQUEST_CREATED: {ObservationalStatus.RESULT_RECORDED},
    ObservationalStatus.RESULT_RECORDED: set(),  # terminal
}

AUTHORIZATION_TRANSITIONS = {
    AuthorizationStatus.PENDING: {AuthorizationStatus.IN_PROGRESS, AuthorizationStatus.CANCELLED},
    AuthorizationStatus.IN_PROGRESS: {
        AuthorizationStatus.APPROVED, AuthorizationStatus.REJECTED, AuthorizationStatus.CANCELLED
    },
    AuthorizationStatus.APPROVED: {AuthorizationStatus.COMPLETED, AuthorizationStatus.FAILED},
    AuthorizationStatus.REJECTED: set(),  # terminal
    AuthorizationStatus.COMPLETED: set(),  # terminal
    AuthorizationStatus.FAILED: set(),  # terminal
    AuthorizationStatus.CANCELLED: set(),  # terminal
}

TRAINING_TRANSITIONS = {
    TrainingStatus.IMPLICIT: {TrainingStatus.INCLUDE, TrainingStatus.EXCLUDE, TrainingStatus.REVIEW},
    TrainingStatus.INCLUDE: set(),
    TrainingStatus.EXCLUDE: set(),
    TrainingStatus.REVIEW: {TrainingStatus.INCLUDE, TrainingStatus.EXCLUDE},
}


class StateMachine:
    """Generic state machine for R6 status tracking."""

    def __init__(self, initial_state, transitions: dict):
        self.state = initial_state
        self.transitions = transitions
        self.history: list[tuple] = [(initial_state, datetime.utcnow(), "init")]

    def can_transition(self, target) -> bool:
        return target in self.transitions.get(self.state, set())

    def transition(self, target, reason: str = "") -> bool:
        if not self.can_transition(target):
            return False
        self.state = target
        self.history.append((target, datetime.utcnow(), reason))
        return True

    @property
    def is_terminal(self) -> bool:
        return len(self.transitions.get(self.state, set())) == 0


# ============================================================
# §3  TIER 1: OBSERVATIONAL
# ============================================================

@dataclass
class ObservationalRules:
    """Tier 1 rules: preferences only."""
    audit_level: str = "full"  # full, summary, minimal


@dataclass
class ObservationalRole:
    """Tier 1 role: session token + binding type."""
    session_token: str = ""
    binding_type: str = "ephemeral"  # ephemeral, persistent


@dataclass
class ObservationalRequest:
    """Tier 1 request: tool, category, target, input_hash."""
    tool: str = ""
    category: str = ""
    target: str = ""
    input_hash: str = ""


@dataclass
class ObservationalReference:
    """Tier 1 reference: session_id, prev_r6, chain_length."""
    session_id: str = ""
    prev_r6: str = ""
    chain_length: int = 0


@dataclass
class ObservationalResource:
    """Tier 1 resource: optional estimates."""
    estimates: dict = field(default_factory=dict)


@dataclass
class ObservationalResult:
    """Tier 1 result: status, output_hash, error, durationMs."""
    status: str = ""
    output_hash: str = ""
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class ObservationalRecord:
    """Complete Tier 1 R6 record — hash-linked JSONL audit chain."""
    r6_id: str = ""
    rules: ObservationalRules = field(default_factory=ObservationalRules)
    role: ObservationalRole = field(default_factory=ObservationalRole)
    request: ObservationalRequest = field(default_factory=ObservationalRequest)
    reference: ObservationalReference = field(default_factory=ObservationalReference)
    resource: ObservationalResource = field(default_factory=ObservationalResource)
    result: Optional[ObservationalResult] = None
    timestamp: str = ""
    record_hash: str = ""

    def compute_hash(self, prev_hash: str = "") -> str:
        """SHA-256 hash including previous record hash for chain integrity."""
        payload = json.dumps({
            "r6_id": self.r6_id,
            "tool": self.request.tool,
            "category": self.request.category,
            "target": self.request.target,
            "input_hash": self.request.input_hash,
            "session_id": self.reference.session_id,
            "prev_r6": self.reference.prev_r6,
            "prev_hash": prev_hash,
            "timestamp": self.timestamp,
        }, sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()


class ObservationalAuditChain:
    """Hash-linked JSONL audit chain for Tier 1."""

    def __init__(self, session_token: str = ""):
        self.session_token = session_token or IDFormat.generate_session_token()
        self.records: list[ObservationalRecord] = []
        self.prev_hash: str = "genesis"

    def before_tool_call(self, tool: str, category: str, target: str,
                         input_data: str = "") -> ObservationalRecord:
        """Hook: before_tool_call — create R6 record."""
        r6_id = IDFormat.generate_r6_id()
        input_hash = hashlib.sha256(input_data.encode()).hexdigest()[:16]
        prev_r6 = self.records[-1].r6_id if self.records else ""

        record = ObservationalRecord(
            r6_id=r6_id,
            rules=ObservationalRules(audit_level="full"),
            role=ObservationalRole(session_token=self.session_token, binding_type="ephemeral"),
            request=ObservationalRequest(
                tool=tool, category=category, target=target, input_hash=input_hash
            ),
            reference=ObservationalReference(
                session_id=self.session_token,
                prev_r6=prev_r6,
                chain_length=len(self.records),
            ),
            resource=ObservationalResource(),
            timestamp=datetime.utcnow().isoformat(),
        )
        record.record_hash = record.compute_hash(self.prev_hash)
        return record

    def after_tool_call(self, record: ObservationalRecord, status: str,
                        output_data: str = "", error: Optional[str] = None,
                        duration_ms: int = 0) -> ObservationalRecord:
        """Hook: after_tool_call — attach result and finalize."""
        output_hash = hashlib.sha256(output_data.encode()).hexdigest()[:16]
        record.result = ObservationalResult(
            status=status, output_hash=output_hash, error=error, duration_ms=duration_ms
        )
        # Recompute hash with result
        record.record_hash = record.compute_hash(self.prev_hash)
        self.prev_hash = record.record_hash
        self.records.append(record)
        return record

    def verify_chain(self) -> tuple[bool, int]:
        """Verify hash-linked chain integrity. Returns (valid, break_index)."""
        prev = "genesis"
        for i, record in enumerate(self.records):
            expected = record.compute_hash(prev)
            if record.record_hash != expected:
                return False, i
            prev = record.record_hash
        return True, -1

    def to_jsonl(self) -> str:
        """Export chain as JSONL (one JSON object per line)."""
        lines = []
        for r in self.records:
            obj = {
                "r6_id": r.r6_id,
                "tool": r.request.tool,
                "category": r.request.category,
                "target": r.request.target,
                "input_hash": r.request.input_hash,
                "session": r.reference.session_id,
                "prev_r6": r.reference.prev_r6,
                "chain_length": r.reference.chain_length,
                "status": r.result.status if r.result else "",
                "output_hash": r.result.output_hash if r.result else "",
                "error": r.result.error if r.result else None,
                "duration_ms": r.result.duration_ms if r.result else 0,
                "timestamp": r.timestamp,
                "hash": r.record_hash,
            }
            lines.append(json.dumps(obj, sort_keys=True))
        return "\n".join(lines)


# ============================================================
# §4  TIER 2: AUTHORIZATION
# ============================================================

class AuthRole(Enum):
    """Tier 2 roles: admin, developer, reviewer, viewer."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


# Role-based permissions
AUTH_PERMISSIONS = {
    AuthRole.ADMIN: {"create", "approve", "reject", "cancel", "view", "configure"},
    AuthRole.DEVELOPER: {"create", "cancel", "view"},
    AuthRole.REVIEWER: {"approve", "reject", "view"},
    AuthRole.VIEWER: {"view"},
}


@dataclass
class AuthorizationRules:
    """Tier 2 rules: applicable rules from policy engine."""
    applicable_rules: list[str] = field(default_factory=list)
    requires_approval: bool = True
    min_approval_role: AuthRole = AuthRole.REVIEWER


@dataclass
class AuthorizationRoleContext:
    """Tier 2 role: actor LCT, role, team LCT."""
    actor_lct: str = ""
    actor_role: AuthRole = AuthRole.VIEWER
    team_lct: str = ""


@dataclass
class AuthorizationRequest:
    """Tier 2 request: action_type, target, description, rationale, success_criteria."""
    action_type: str = ""
    target: str = ""
    description: str = ""
    rationale: str = ""
    success_criteria: list[str] = field(default_factory=list)


@dataclass
class AuthorizationReference:
    """Tier 2 reference: prev_bundle_id, related_requests, context_notes."""
    prev_bundle_id: str = ""
    related_requests: list[str] = field(default_factory=list)
    context_notes: str = ""


@dataclass
class AuthorizationResourceSpec:
    """Tier 2 resource: ATP estimate/actual, resource requirements."""
    atp_estimate: float = 0.0
    atp_actual: float = 0.0
    resource_requirements: dict = field(default_factory=dict)


@dataclass
class AuthorizationResult:
    """Tier 2 result: full governance result."""
    status: str = ""
    success: bool = False
    reason: str = ""
    atp_consumed: float = 0.0
    trust_delta: dict = field(default_factory=dict)
    coherence: float = 0.0
    bundle_id: str = ""
    learnings: list[str] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class T3TrustTensor:
    """Trust tensor: Talent / Training / Temperament."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def average(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def update(self, delta: dict) -> dict:
        """Apply delta, return {dim: {from, to, change}}."""
        changes = {}
        for dim in ["talent", "training", "temperament"]:
            if dim in delta:
                old = getattr(self, dim)
                new_val = max(0.0, min(1.0, old + delta[dim]))
                setattr(self, dim, new_val)
                changes[dim] = {"from": old, "to": new_val, "change": new_val - old}
        return changes


@dataclass
class AuthorizationBundle:
    """Complete Tier 2 R6 bundle."""
    bundle_id: str = ""
    rules: AuthorizationRules = field(default_factory=AuthorizationRules)
    role: AuthorizationRoleContext = field(default_factory=AuthorizationRoleContext)
    request: AuthorizationRequest = field(default_factory=AuthorizationRequest)
    reference: AuthorizationReference = field(default_factory=AuthorizationReference)
    resource: AuthorizationResourceSpec = field(default_factory=AuthorizationResourceSpec)
    result: Optional[AuthorizationResult] = None
    state_machine: StateMachine = field(default_factory=lambda: StateMachine(
        AuthorizationStatus.PENDING, AUTHORIZATION_TRANSITIONS
    ))
    trust_tensor: T3TrustTensor = field(default_factory=T3TrustTensor)
    created_at: str = ""


class AuthorizationEngine:
    """Tier 2 authorization engine with approval workflow."""

    def __init__(self):
        self.bundles: dict[str, AuthorizationBundle] = {}
        self.actors: dict[str, T3TrustTensor] = {}  # actor_lct → T3

    def register_actor(self, lct: str, role: AuthRole,
                       t3: Optional[T3TrustTensor] = None) -> T3TrustTensor:
        t3 = t3 or T3TrustTensor()
        self.actors[lct] = t3
        return t3

    def create_request(self, actor_lct: str, actor_role: AuthRole,
                       action_type: str, target: str, description: str,
                       rationale: str, atp_estimate: float = 0.0,
                       success_criteria: list[str] | None = None,
                       team_lct: str = "") -> Optional[AuthorizationBundle]:
        """Create a new authorization request (requires 'create' permission)."""
        if "create" not in AUTH_PERMISSIONS.get(actor_role, set()):
            return None

        bundle_id = IDFormat.generate_r6_id()
        bundle = AuthorizationBundle(
            bundle_id=bundle_id,
            rules=AuthorizationRules(requires_approval=True),
            role=AuthorizationRoleContext(
                actor_lct=actor_lct, actor_role=actor_role, team_lct=team_lct
            ),
            request=AuthorizationRequest(
                action_type=action_type, target=target,
                description=description, rationale=rationale,
                success_criteria=success_criteria or [],
            ),
            resource=AuthorizationResourceSpec(atp_estimate=atp_estimate),
            trust_tensor=self.actors.get(actor_lct, T3TrustTensor()),
            created_at=datetime.utcnow().isoformat(),
        )
        self.bundles[bundle_id] = bundle
        return bundle

    def approve(self, bundle_id: str, approver_role: AuthRole,
                reason: str = "") -> bool:
        """Approve a request (requires 'approve' permission)."""
        if "approve" not in AUTH_PERMISSIONS.get(approver_role, set()):
            return False
        bundle = self.bundles.get(bundle_id)
        if not bundle:
            return False
        # Must be in_progress to approve
        if bundle.state_machine.state != AuthorizationStatus.IN_PROGRESS:
            # Try auto-transition pending → in_progress → approved
            if bundle.state_machine.state == AuthorizationStatus.PENDING:
                bundle.state_machine.transition(AuthorizationStatus.IN_PROGRESS, "auto")
            else:
                return False
        return bundle.state_machine.transition(AuthorizationStatus.APPROVED, reason)

    def reject(self, bundle_id: str, approver_role: AuthRole,
               reason: str = "") -> bool:
        if "reject" not in AUTH_PERMISSIONS.get(approver_role, set()):
            return False
        bundle = self.bundles.get(bundle_id)
        if not bundle:
            return False
        if bundle.state_machine.state == AuthorizationStatus.PENDING:
            bundle.state_machine.transition(AuthorizationStatus.IN_PROGRESS, "auto")
        return bundle.state_machine.transition(AuthorizationStatus.REJECTED, reason)

    def cancel(self, bundle_id: str, actor_lct: str, actor_role: AuthRole) -> bool:
        """Cancel request (by requester)."""
        if "cancel" not in AUTH_PERMISSIONS.get(actor_role, set()):
            return False
        bundle = self.bundles.get(bundle_id)
        if not bundle:
            return False
        if bundle.role.actor_lct != actor_lct and actor_role != AuthRole.ADMIN:
            return False
        return bundle.state_machine.transition(AuthorizationStatus.CANCELLED, "cancelled by requester")

    def complete(self, bundle_id: str, success: bool, atp_consumed: float = 0.0,
                 trust_delta: dict | None = None, learnings: list[str] | None = None,
                 surprises: list[str] | None = None) -> bool:
        """Complete an approved request."""
        bundle = self.bundles.get(bundle_id)
        if not bundle:
            return False
        if bundle.state_machine.state != AuthorizationStatus.APPROVED:
            return False

        target_status = AuthorizationStatus.COMPLETED if success else AuthorizationStatus.FAILED
        result = AuthorizationResult(
            status=target_status.value,
            success=success,
            atp_consumed=atp_consumed,
            trust_delta=trust_delta or {},
            bundle_id=bundle_id,
            learnings=learnings or [],
            surprises=surprises or [],
        )
        bundle.result = result
        bundle.resource.atp_actual = atp_consumed

        # Apply T3 updates
        if trust_delta:
            actor_t3 = self.actors.get(bundle.role.actor_lct)
            if actor_t3:
                actor_t3.update(trust_delta)

        return bundle.state_machine.transition(target_status, "execution complete")


# ============================================================
# §5  TIER 3: TRAINING EVALUATION
# ============================================================

class OperationalMode(Enum):
    """Tier 3 operational modes."""
    CONVERSATION = "conversation"
    REFINEMENT = "refinement"
    PHILOSOPHICAL = "philosophical"


class TrainingRole(Enum):
    """Tier 3 training roles."""
    LEARNING_PARTNER = "learning_partner"
    PRACTICE_STUDENT = "practice_student"
    SKILL_PRACTITIONER = "skill_practitioner"


@dataclass
class TrainingRules:
    """Tier 3 rules: mode, success_criteria, allow_meta_cognitive."""
    mode: OperationalMode = OperationalMode.CONVERSATION
    success_criteria: list[str] = field(default_factory=list)
    allow_meta_cognitive: bool = True


@dataclass
class TrainingRoleContext:
    """Tier 3 role: lct, position, relationship_to, phase, permissions."""
    lct: str = ""
    position: TrainingRole = TrainingRole.LEARNING_PARTNER
    relationship_to: str = ""
    phase: str = "initial"
    permissions: list[str] = field(default_factory=list)


@dataclass
class TrainingRequest:
    """Tier 3 request: exercise type and parameters."""
    exercise_type: str = ""
    prompt: str = ""
    intent: str = ""
    expected_pattern: str = ""
    parameters: dict = field(default_factory=dict)


@dataclass
class TrainingReference:
    """Tier 3 reference: session history."""
    previous_session: str = ""
    skill_track: str = ""
    session_exercises_so_far: int = 0


@dataclass
class TrainingResourceSpec:
    """Tier 3 resource: model, budget, context."""
    model: str = ""
    atp_budget: float = 0.0
    context_window: int = 0
    temperature: float = 0.7


@dataclass
class MetaCognitiveSignals:
    """Detected meta-cognitive signals in training response."""
    clarification_requests: int = 0
    modal_awareness: bool = False
    self_correction: bool = False
    uncertainty_expression: bool = False
    reasoning_transparency: bool = False

    def score(self) -> float:
        signals = [
            self.clarification_requests > 0,
            self.modal_awareness,
            self.self_correction,
            self.uncertainty_expression,
            self.reasoning_transparency,
        ]
        return sum(1.0 for s in signals if s) / len(signals)


@dataclass
class TrainingResult:
    """Tier 3 result: evaluation outcome."""
    status: str = ""  # include/exclude/review
    mode_detection: str = ""
    quality: float = 0.0
    meta_cognitive: MetaCognitiveSignals = field(default_factory=MetaCognitiveSignals)
    t3_updates: dict = field(default_factory=dict)


@dataclass
class TrainingExercise:
    """Complete Tier 3 R6 exercise record."""
    exercise_id: str = ""
    rules: TrainingRules = field(default_factory=TrainingRules)
    role: TrainingRoleContext = field(default_factory=TrainingRoleContext)
    request: TrainingRequest = field(default_factory=TrainingRequest)
    reference: TrainingReference = field(default_factory=TrainingReference)
    resource: TrainingResourceSpec = field(default_factory=TrainingResourceSpec)
    result: Optional[TrainingResult] = None
    state_machine: StateMachine = field(default_factory=lambda: StateMachine(
        TrainingStatus.IMPLICIT, TRAINING_TRANSITIONS
    ))
    t3_trajectory: T3TrustTensor = field(default_factory=T3TrustTensor)


class TrainingEvaluator:
    """Tier 3 training evaluation engine."""

    def __init__(self):
        self.exercises: list[TrainingExercise] = []
        self.skill_tracks: dict[str, list[TrainingExercise]] = {}
        self.t3_trajectories: dict[str, list[T3TrustTensor]] = {}  # lct → history

    def create_exercise(self, exercise_type: str, prompt: str, intent: str,
                        expected_pattern: str, mode: OperationalMode,
                        role: TrainingRole, lct: str = "",
                        skill_track: str = "", model: str = "",
                        atp_budget: float = 0.0,
                        success_criteria: list[str] | None = None) -> TrainingExercise:
        exercise = TrainingExercise(
            exercise_id=IDFormat.generate_r6_id(),
            rules=TrainingRules(
                mode=mode,
                success_criteria=success_criteria or [],
                allow_meta_cognitive=True,
            ),
            role=TrainingRoleContext(
                lct=lct or IDFormat.generate_lct("trainee", uuid.uuid4().hex[:8]),
                position=role,
                phase="active",
            ),
            request=TrainingRequest(
                exercise_type=exercise_type,
                prompt=prompt,
                intent=intent,
                expected_pattern=expected_pattern,
            ),
            reference=TrainingReference(
                skill_track=skill_track,
                session_exercises_so_far=len(self.exercises),
            ),
            resource=TrainingResourceSpec(model=model, atp_budget=atp_budget),
        )
        self.exercises.append(exercise)
        if skill_track:
            self.skill_tracks.setdefault(skill_track, []).append(exercise)
        return exercise

    def evaluate(self, exercise: TrainingExercise, response: str,
                 quality: float, mode_detected: str = "",
                 meta_signals: MetaCognitiveSignals | None = None) -> TrainingResult:
        """Evaluate a training response."""
        meta = meta_signals or MetaCognitiveSignals()

        # Determine T3 updates based on quality and meta-cognitive score
        t3_updates = {}
        meta_score = meta.score()

        if quality >= 0.8:
            t3_updates["training"] = 0.01 * quality
            t3_updates["talent"] = 0.005 * quality
        elif quality < 0.4:
            t3_updates["training"] = -0.005

        if meta_score >= 0.6:
            t3_updates["temperament"] = 0.01 * meta_score

        # Determine inclusion status
        if quality >= 0.7 and meta_score >= 0.4:
            status = "include"
        elif quality < 0.3:
            status = "exclude"
        else:
            status = "review"

        result = TrainingResult(
            status=status,
            mode_detection=mode_detected or exercise.rules.mode.value,
            quality=quality,
            meta_cognitive=meta,
            t3_updates=t3_updates,
        )
        exercise.result = result

        # Transition state machine
        target_map = {
            "include": TrainingStatus.INCLUDE,
            "exclude": TrainingStatus.EXCLUDE,
            "review": TrainingStatus.REVIEW,
        }
        exercise.state_machine.transition(target_map[status], f"quality={quality:.2f}")

        # Track T3 trajectory
        if exercise.role.lct:
            trajectory = self.t3_trajectories.setdefault(exercise.role.lct, [])
            t3 = T3TrustTensor()
            if trajectory:
                last = trajectory[-1]
                t3 = T3TrustTensor(
                    talent=last.talent, training=last.training, temperament=last.temperament
                )
            t3.update(t3_updates)
            trajectory.append(t3)
            exercise.t3_trajectory = t3

        return result

    def get_trajectory(self, lct: str) -> list[T3TrustTensor]:
        return self.t3_trajectories.get(lct, [])

    def get_skill_summary(self, skill_track: str) -> dict:
        """Summary of exercises in a skill track."""
        exercises = self.skill_tracks.get(skill_track, [])
        if not exercises:
            return {"count": 0}
        evaluated = [e for e in exercises if e.result]
        included = [e for e in evaluated if e.result.status == "include"]
        excluded = [e for e in evaluated if e.result.status == "exclude"]
        review = [e for e in evaluated if e.result.status == "review"]
        avg_quality = (sum(e.result.quality for e in evaluated) / len(evaluated)) if evaluated else 0

        return {
            "count": len(exercises),
            "evaluated": len(evaluated),
            "included": len(included),
            "excluded": len(excluded),
            "review": len(review),
            "avg_quality": round(avg_quality, 4),
        }


# ============================================================
# §6  TIER UPGRADE PATH
# ============================================================

class TierUpgradeManager:
    """Manages progressive adoption: Tier 1 → Tier 2 → Tier 3."""

    @staticmethod
    def import_observational_to_authorization(
        obs_chain: ObservationalAuditChain,
        auth_engine: AuthorizationEngine,
        actor_lct: str,
        actor_role: AuthRole = AuthRole.DEVELOPER,
    ) -> list[AuthorizationBundle]:
        """Import Tier 1 records into Tier 2 system (spec: audit trail format compatible)."""
        bundles = []
        for record in obs_chain.records:
            bundle = auth_engine.create_request(
                actor_lct=actor_lct,
                actor_role=actor_role,
                action_type=record.request.tool,
                target=record.request.target,
                description=f"Imported from observational: {record.request.category}",
                rationale="Tier upgrade import",
            )
            if bundle and record.result:
                # Auto-approve and complete imported records
                auth_engine.approve(bundle.bundle_id, AuthRole.ADMIN, "import auto-approve")
                auth_engine.complete(
                    bundle.bundle_id,
                    success=(record.result.status == "success"),
                    atp_consumed=0.0,
                )
            if bundle:
                bundles.append(bundle)
        return bundles

    @staticmethod
    def import_authorization_to_training(
        auth_engine: AuthorizationEngine,
        training_eval: TrainingEvaluator,
        skill_track: str = "imported",
    ) -> list[TrainingExercise]:
        """Import Tier 2 completed bundles into Tier 3 for training evaluation."""
        exercises = []
        for bundle_id, bundle in auth_engine.bundles.items():
            if bundle.state_machine.state in (
                AuthorizationStatus.COMPLETED, AuthorizationStatus.FAILED
            ):
                ex = training_eval.create_exercise(
                    exercise_type="imported_action",
                    prompt=bundle.request.description,
                    intent=bundle.request.rationale,
                    expected_pattern="successful_completion",
                    mode=OperationalMode.REFINEMENT,
                    role=TrainingRole.SKILL_PRACTITIONER,
                    skill_track=skill_track,
                )
                # Auto-evaluate based on bundle outcome
                quality = 0.8 if bundle.result and bundle.result.success else 0.3
                # Imported records get baseline meta-cognitive signals
                import_meta = MetaCognitiveSignals(
                    reasoning_transparency=True,
                    modal_awareness=True,
                    self_correction=(bundle.result and bundle.result.success),
                ) if quality >= 0.7 else MetaCognitiveSignals()
                training_eval.evaluate(ex, "imported", quality, meta_signals=import_meta)
                exercises.append(ex)
        return exercises


# ============================================================
# §7  TRUST INTEGRATION LEVELS
# ============================================================

class TrustIntegrationLevel(Enum):
    """Trust model per tier (from spec table)."""
    RELYING_PARTY = "relying_party"          # Tier 1: no built-in trust
    T3_TENSOR = "t3_tensor"                  # Tier 2: full T3
    T3_DEVELOPMENTAL = "t3_developmental"    # Tier 3: T3 with trajectory


@dataclass
class TrustIntegration:
    """Maps tier to trust integration level and capabilities."""
    tier: int
    level: TrustIntegrationLevel
    has_t3: bool = False
    has_trajectory: bool = False
    has_atp: bool = False

    @classmethod
    def for_tier(cls, tier: int) -> TrustIntegration:
        if tier == 1:
            return cls(1, TrustIntegrationLevel.RELYING_PARTY)
        elif tier == 2:
            return cls(2, TrustIntegrationLevel.T3_TENSOR, has_t3=True, has_atp=True)
        elif tier == 3:
            return cls(3, TrustIntegrationLevel.T3_DEVELOPMENTAL,
                       has_t3=True, has_trajectory=True, has_atp=True)
        raise ValueError(f"Unknown tier: {tier}")


# ============================================================
# TESTS
# ============================================================

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name: str, condition: bool):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    # ── T1: ID Format Generation ──
    print("T1: ID Format Generation")

    r6id = IDFormat.generate_r6_id()
    check("T1.1 R6 ID format valid", IDFormat.validate_r6_id(r6id))
    check("T1.2 R6 ID prefix", r6id.startswith("r6:"))
    check("T1.3 R6 ID length", len(r6id) == 11)  # r6: + 8 hex

    audit_id = IDFormat.generate_audit_id()
    check("T1.4 Audit ID format valid", IDFormat.validate_audit_id(audit_id))
    check("T1.5 Audit ID prefix", audit_id.startswith("audit:"))

    session = IDFormat.generate_session_token()
    check("T1.6 Session token format valid", IDFormat.validate_session_token(session))
    check("T1.7 Session token prefix", session.startswith("web4:session:"))

    lct = IDFormat.generate_lct("root", "abc123")
    check("T1.8 LCT format valid", IDFormat.validate_lct(lct))
    check("T1.9 LCT value", lct == "lct:web4:root:abc123")

    # Invalid formats
    check("T1.10 Invalid R6 ID rejected", not IDFormat.validate_r6_id("r6:xyz"))
    check("T1.11 Invalid audit ID rejected", not IDFormat.validate_audit_id("audit:toolong1234"))
    check("T1.12 Invalid session rejected", not IDFormat.validate_session_token("web4:session:short"))
    check("T1.13 Invalid LCT rejected", not IDFormat.validate_lct("lct:web4:"))

    # Uniqueness
    ids = {IDFormat.generate_r6_id() for _ in range(100)}
    check("T1.14 R6 IDs unique", len(ids) == 100)

    # ── T2: Observational State Machine ──
    print("T2: Observational State Machine")

    sm = StateMachine(ObservationalStatus.IMPLICIT, OBSERVATIONAL_TRANSITIONS)
    check("T2.1 Initial state implicit", sm.state == ObservationalStatus.IMPLICIT)
    check("T2.2 Can transition to request_created", sm.can_transition(ObservationalStatus.REQUEST_CREATED))
    check("T2.3 Cannot skip to result_recorded", not sm.can_transition(ObservationalStatus.RESULT_RECORDED))

    ok = sm.transition(ObservationalStatus.REQUEST_CREATED, "tool called")
    check("T2.4 Transition to request_created", ok)
    check("T2.5 State is request_created", sm.state == ObservationalStatus.REQUEST_CREATED)

    ok = sm.transition(ObservationalStatus.RESULT_RECORDED, "tool returned")
    check("T2.6 Transition to result_recorded", ok)
    check("T2.7 Is terminal", sm.is_terminal)
    check("T2.8 History length", len(sm.history) == 3)

    # ── T3: Authorization State Machine ──
    print("T3: Authorization State Machine")

    sm = StateMachine(AuthorizationStatus.PENDING, AUTHORIZATION_TRANSITIONS)
    check("T3.1 Starts pending", sm.state == AuthorizationStatus.PENDING)

    # Happy path: pending → in_progress → approved → completed
    check("T3.2 Can go to in_progress", sm.can_transition(AuthorizationStatus.IN_PROGRESS))
    sm.transition(AuthorizationStatus.IN_PROGRESS)
    check("T3.3 In progress", sm.state == AuthorizationStatus.IN_PROGRESS)

    check("T3.4 Can approve", sm.can_transition(AuthorizationStatus.APPROVED))
    sm.transition(AuthorizationStatus.APPROVED)
    check("T3.5 Approved", sm.state == AuthorizationStatus.APPROVED)

    check("T3.6 Can complete", sm.can_transition(AuthorizationStatus.COMPLETED))
    sm.transition(AuthorizationStatus.COMPLETED)
    check("T3.7 Completed terminal", sm.is_terminal)

    # Rejection path
    sm2 = StateMachine(AuthorizationStatus.PENDING, AUTHORIZATION_TRANSITIONS)
    sm2.transition(AuthorizationStatus.IN_PROGRESS)
    sm2.transition(AuthorizationStatus.REJECTED)
    check("T3.8 Rejected terminal", sm2.is_terminal)

    # Cancellation from pending
    sm3 = StateMachine(AuthorizationStatus.PENDING, AUTHORIZATION_TRANSITIONS)
    check("T3.9 Can cancel from pending", sm3.can_transition(AuthorizationStatus.CANCELLED))
    sm3.transition(AuthorizationStatus.CANCELLED)
    check("T3.10 Cancelled terminal", sm3.is_terminal)

    # Failure path
    sm4 = StateMachine(AuthorizationStatus.PENDING, AUTHORIZATION_TRANSITIONS)
    sm4.transition(AuthorizationStatus.IN_PROGRESS)
    sm4.transition(AuthorizationStatus.APPROVED)
    sm4.transition(AuthorizationStatus.FAILED)
    check("T3.11 Failed terminal", sm4.is_terminal)

    # Cannot go backwards
    sm5 = StateMachine(AuthorizationStatus.PENDING, AUTHORIZATION_TRANSITIONS)
    sm5.transition(AuthorizationStatus.IN_PROGRESS)
    sm5.transition(AuthorizationStatus.APPROVED)
    check("T3.12 Cannot go back to pending", not sm5.can_transition(AuthorizationStatus.PENDING))

    # ── T4: Training State Machine ──
    print("T4: Training State Machine")

    sm = StateMachine(TrainingStatus.IMPLICIT, TRAINING_TRANSITIONS)
    check("T4.1 Starts implicit", sm.state == TrainingStatus.IMPLICIT)
    check("T4.2 Can include", sm.can_transition(TrainingStatus.INCLUDE))
    check("T4.3 Can exclude", sm.can_transition(TrainingStatus.EXCLUDE))
    check("T4.4 Can review", sm.can_transition(TrainingStatus.REVIEW))

    sm.transition(TrainingStatus.INCLUDE)
    check("T4.5 Include terminal", sm.is_terminal)

    # Review → include path
    sm2 = StateMachine(TrainingStatus.IMPLICIT, TRAINING_TRANSITIONS)
    sm2.transition(TrainingStatus.REVIEW)
    check("T4.6 Review not terminal", not sm2.is_terminal)
    check("T4.7 Review can include", sm2.can_transition(TrainingStatus.INCLUDE))
    sm2.transition(TrainingStatus.INCLUDE)
    check("T4.8 Review→Include terminal", sm2.is_terminal)

    # Review → exclude path
    sm3 = StateMachine(TrainingStatus.IMPLICIT, TRAINING_TRANSITIONS)
    sm3.transition(TrainingStatus.REVIEW)
    sm3.transition(TrainingStatus.EXCLUDE)
    check("T4.9 Review→Exclude terminal", sm3.is_terminal)

    # ── T5: Observational Audit Chain ──
    print("T5: Observational Audit Chain")

    chain = ObservationalAuditChain()
    check("T5.1 Chain created", len(chain.records) == 0)
    check("T5.2 Session token valid", IDFormat.validate_session_token(chain.session_token))

    # Record 1
    rec1 = chain.before_tool_call("read_file", "filesystem", "/tmp/test.py", "test input")
    check("T5.3 R6 ID generated", IDFormat.validate_r6_id(rec1.r6_id))
    check("T5.4 Tool recorded", rec1.request.tool == "read_file")
    check("T5.5 Category recorded", rec1.request.category == "filesystem")
    check("T5.6 Input hash non-empty", len(rec1.request.input_hash) > 0)
    check("T5.7 Chain length 0", rec1.reference.chain_length == 0)
    check("T5.8 Prev R6 empty (first)", rec1.reference.prev_r6 == "")

    chain.after_tool_call(rec1, "success", "file contents here", duration_ms=50)
    check("T5.9 Record appended", len(chain.records) == 1)
    check("T5.10 Result attached", rec1.result is not None)
    check("T5.11 Status success", rec1.result.status == "success")
    check("T5.12 Duration recorded", rec1.result.duration_ms == 50)

    # Record 2
    rec2 = chain.before_tool_call("write_file", "filesystem", "/tmp/out.py", "output")
    check("T5.13 Second record chain_length 1", rec2.reference.chain_length == 1)
    check("T5.14 Prev R6 links to first", rec2.reference.prev_r6 == rec1.r6_id)
    chain.after_tool_call(rec2, "success", "written", duration_ms=30)
    check("T5.15 Two records", len(chain.records) == 2)

    # Record 3 with error
    rec3 = chain.before_tool_call("exec", "shell", "rm -rf /", "dangerous")
    chain.after_tool_call(rec3, "error", "", error="permission denied", duration_ms=5)
    check("T5.16 Error recorded", rec3.result.error == "permission denied")
    check("T5.17 Three records", len(chain.records) == 3)

    # Chain verification
    valid, break_idx = chain.verify_chain()
    check("T5.18 Chain valid", valid)
    check("T5.19 No break index", break_idx == -1)

    # Tamper detection
    chain.records[1].request.target = "/tmp/TAMPERED.py"
    valid, break_idx = chain.verify_chain()
    check("T5.20 Tampered chain invalid", not valid)
    check("T5.21 Break at index 1", break_idx == 1)

    # Restore
    chain.records[1].request.target = "/tmp/out.py"

    # JSONL export
    jsonl = chain.to_jsonl()
    lines = jsonl.strip().split("\n")
    check("T5.22 JSONL line count", len(lines) == 3)
    first_line = json.loads(lines[0])
    check("T5.23 JSONL has r6_id", "r6_id" in first_line)
    check("T5.24 JSONL has hash", "hash" in first_line)

    # ── T6: Observational Rules Variants ──
    print("T6: Observational Rules Variants")

    rules_full = ObservationalRules(audit_level="full")
    rules_summary = ObservationalRules(audit_level="summary")
    rules_minimal = ObservationalRules(audit_level="minimal")
    check("T6.1 Full audit level", rules_full.audit_level == "full")
    check("T6.2 Summary audit level", rules_summary.audit_level == "summary")
    check("T6.3 Minimal audit level", rules_minimal.audit_level == "minimal")

    # Binding types
    role_eph = ObservationalRole(session_token="test", binding_type="ephemeral")
    role_per = ObservationalRole(session_token="test", binding_type="persistent")
    check("T6.4 Ephemeral binding", role_eph.binding_type == "ephemeral")
    check("T6.5 Persistent binding", role_per.binding_type == "persistent")

    # ── T7: Authorization Engine ──
    print("T7: Authorization Engine")

    engine = AuthorizationEngine()
    dev_lct = "lct:web4:human:dev001"
    admin_lct = "lct:web4:human:admin01"

    engine.register_actor(dev_lct, AuthRole.DEVELOPER, T3TrustTensor(0.7, 0.8, 0.9))
    engine.register_actor(admin_lct, AuthRole.ADMIN, T3TrustTensor(0.9, 0.9, 0.9))

    # Developer creates request
    bundle = engine.create_request(
        actor_lct=dev_lct, actor_role=AuthRole.DEVELOPER,
        action_type="deploy", target="production",
        description="Deploy v2.0 to production",
        rationale="Release milestone",
        atp_estimate=100.0,
        success_criteria=["all tests pass", "no downtime"],
    )
    check("T7.1 Bundle created", bundle is not None)
    check("T7.2 Bundle ID valid", IDFormat.validate_r6_id(bundle.bundle_id))
    check("T7.3 State is pending", bundle.state_machine.state == AuthorizationStatus.PENDING)
    check("T7.4 Actor recorded", bundle.role.actor_lct == dev_lct)
    check("T7.5 Action type recorded", bundle.request.action_type == "deploy")
    check("T7.6 ATP estimate recorded", bundle.resource.atp_estimate == 100.0)
    check("T7.7 Success criteria", len(bundle.request.success_criteria) == 2)

    # Viewer cannot create
    viewer_bundle = engine.create_request(
        actor_lct="lct:web4:human:viewer01", actor_role=AuthRole.VIEWER,
        action_type="deploy", target="production",
        description="Unauthorized", rationale="N/A",
    )
    check("T7.8 Viewer cannot create", viewer_bundle is None)

    # Reviewer approves
    ok = engine.approve(bundle.bundle_id, AuthRole.REVIEWER, "Looks good")
    check("T7.9 Reviewer can approve", ok)
    check("T7.10 State approved", bundle.state_machine.state == AuthorizationStatus.APPROVED)

    # Complete with trust delta
    ok = engine.complete(
        bundle.bundle_id, success=True, atp_consumed=85.0,
        trust_delta={"training": 0.01, "temperament": 0.005},
        learnings=["Deployment was smooth"],
        surprises=["Faster than expected"],
    )
    check("T7.11 Completed", ok)
    check("T7.12 State completed", bundle.state_machine.state == AuthorizationStatus.COMPLETED)
    check("T7.13 ATP consumed recorded", bundle.resource.atp_actual == 85.0)
    check("T7.14 Result has learnings", len(bundle.result.learnings) == 1)
    check("T7.15 T3 updated", engine.actors[dev_lct].training > 0.8)

    # ── T8: Authorization Rejection ──
    print("T8: Authorization Rejection")

    bundle2 = engine.create_request(
        actor_lct=dev_lct, actor_role=AuthRole.DEVELOPER,
        action_type="delete_db", target="production",
        description="Delete production database",
        rationale="Cleanup",
    )
    ok = engine.reject(bundle2.bundle_id, AuthRole.REVIEWER, "Too dangerous")
    check("T8.1 Rejected", ok)
    check("T8.2 State rejected", bundle2.state_machine.state == AuthorizationStatus.REJECTED)
    check("T8.3 Terminal", bundle2.state_machine.is_terminal)

    # Cannot complete rejected bundle
    ok = engine.complete(bundle2.bundle_id, success=True)
    check("T8.4 Cannot complete rejected", not ok)

    # ── T9: Authorization Cancellation ──
    print("T9: Authorization Cancellation")

    bundle3 = engine.create_request(
        actor_lct=dev_lct, actor_role=AuthRole.DEVELOPER,
        action_type="refactor", target="auth_module",
        description="Refactor auth", rationale="Cleaner code",
    )
    # Developer can cancel own request
    ok = engine.cancel(bundle3.bundle_id, dev_lct, AuthRole.DEVELOPER)
    check("T9.1 Developer cancels own", ok)
    check("T9.2 State cancelled", bundle3.state_machine.state == AuthorizationStatus.CANCELLED)

    # Another developer cannot cancel someone else's
    bundle4 = engine.create_request(
        actor_lct=dev_lct, actor_role=AuthRole.DEVELOPER,
        action_type="test", target="suite",
        description="Run tests", rationale="CI",
    )
    ok = engine.cancel(bundle4.bundle_id, "lct:web4:human:other", AuthRole.DEVELOPER)
    check("T9.3 Other dev cannot cancel", not ok)

    # Admin can cancel anyone's
    ok = engine.cancel(bundle4.bundle_id, admin_lct, AuthRole.ADMIN)
    check("T9.4 Admin can cancel anyone", ok)

    # ── T10: Authorization Permissions Matrix ──
    print("T10: Authorization Permissions Matrix")

    check("T10.1 Admin has all", len(AUTH_PERMISSIONS[AuthRole.ADMIN]) == 6)
    check("T10.2 Developer can create", "create" in AUTH_PERMISSIONS[AuthRole.DEVELOPER])
    check("T10.3 Developer cannot approve", "approve" not in AUTH_PERMISSIONS[AuthRole.DEVELOPER])
    check("T10.4 Reviewer can approve", "approve" in AUTH_PERMISSIONS[AuthRole.REVIEWER])
    check("T10.5 Reviewer cannot create", "create" not in AUTH_PERMISSIONS[AuthRole.REVIEWER])
    check("T10.6 Viewer can only view", AUTH_PERMISSIONS[AuthRole.VIEWER] == {"view"})

    # Developer cannot approve
    bundle5 = engine.create_request(
        actor_lct=dev_lct, actor_role=AuthRole.DEVELOPER,
        action_type="build", target="app",
        description="Build", rationale="Release",
    )
    ok = engine.approve(bundle5.bundle_id, AuthRole.DEVELOPER, "self-approve")
    check("T10.7 Developer cannot approve", not ok)

    # ── T11: T3 Trust Tensor ──
    print("T11: T3 Trust Tensor")

    t3 = T3TrustTensor(0.7, 0.8, 0.9)
    check("T11.1 Talent", t3.talent == 0.7)
    check("T11.2 Training", t3.training == 0.8)
    check("T11.3 Temperament", t3.temperament == 0.9)
    check("T11.4 Average", abs(t3.average() - 0.8) < 0.001)

    changes = t3.update({"talent": 0.05, "training": -0.1})
    check("T11.5 Talent updated", abs(t3.talent - 0.75) < 0.001)
    check("T11.6 Training updated", abs(t3.training - 0.7) < 0.001)
    check("T11.7 Temperament unchanged", abs(t3.temperament - 0.9) < 0.001)
    check("T11.8 Change dict has from/to", "from" in changes["talent"])
    check("T11.9 Change dict correct", abs(changes["talent"]["from"] - 0.7) < 0.001)

    # Clamping
    t3b = T3TrustTensor(0.95, 0.05, 0.5)
    t3b.update({"talent": 0.2, "training": -0.1})
    check("T11.10 Clamped to 1.0", t3b.talent == 1.0)
    check("T11.11 Clamped to 0.0", t3b.training == 0.0)

    # ── T12: Training Evaluator ──
    print("T12: Training Evaluator")

    evaluator = TrainingEvaluator()
    trainee_lct = "lct:web4:ai:trainee001"

    ex1 = evaluator.create_exercise(
        exercise_type="conversation",
        prompt="Explain Web4 trust tensors",
        intent="Test understanding of T3",
        expected_pattern="accurate_explanation",
        mode=OperationalMode.CONVERSATION,
        role=TrainingRole.LEARNING_PARTNER,
        lct=trainee_lct,
        skill_track="web4_fundamentals",
        model="claude-opus-4-6",
        atp_budget=50.0,
        success_criteria=["covers T3 dimensions", "provides examples"],
    )
    check("T12.1 Exercise created", ex1 is not None)
    check("T12.2 Exercise ID valid", IDFormat.validate_r6_id(ex1.exercise_id))
    check("T12.3 Mode conversation", ex1.rules.mode == OperationalMode.CONVERSATION)
    check("T12.4 Role learning_partner", ex1.role.position == TrainingRole.LEARNING_PARTNER)
    check("T12.5 Skill track set", ex1.reference.skill_track == "web4_fundamentals")
    check("T12.6 State implicit", ex1.state_machine.state == TrainingStatus.IMPLICIT)

    # High quality evaluation → include
    meta1 = MetaCognitiveSignals(
        clarification_requests=1, modal_awareness=True,
        self_correction=True, uncertainty_expression=True,
        reasoning_transparency=True,
    )
    result1 = evaluator.evaluate(ex1, "Trust tensors are T3 = Talent + Training + Temperament...",
                                  quality=0.9, meta_signals=meta1)
    check("T12.7 Result status include", result1.status == "include")
    check("T12.8 Quality recorded", result1.quality == 0.9)
    check("T12.9 Meta-cognitive score", meta1.score() == 1.0)
    check("T12.10 T3 updates present", len(result1.t3_updates) > 0)
    check("T12.11 State machine include", ex1.state_machine.state == TrainingStatus.INCLUDE)

    # Low quality → exclude
    ex2 = evaluator.create_exercise(
        exercise_type="refinement",
        prompt="Optimize this SQL query",
        intent="Test optimization skills",
        expected_pattern="improved_query",
        mode=OperationalMode.REFINEMENT,
        role=TrainingRole.PRACTICE_STUDENT,
        lct=trainee_lct,
        skill_track="web4_fundamentals",
    )
    result2 = evaluator.evaluate(ex2, "I don't know SQL", quality=0.1)
    check("T12.12 Low quality excluded", result2.status == "exclude")
    check("T12.13 State machine exclude", ex2.state_machine.state == TrainingStatus.EXCLUDE)

    # Medium quality → review
    ex3 = evaluator.create_exercise(
        exercise_type="philosophical",
        prompt="Discuss alignment vs compliance",
        intent="Test philosophical reasoning",
        expected_pattern="nuanced_discussion",
        mode=OperationalMode.PHILOSOPHICAL,
        role=TrainingRole.SKILL_PRACTITIONER,
        lct=trainee_lct,
        skill_track="web4_fundamentals",
    )
    result3 = evaluator.evaluate(ex3, "Partial answer about alignment...", quality=0.5)
    check("T12.14 Medium quality review", result3.status == "review")
    check("T12.15 State machine review", ex3.state_machine.state == TrainingStatus.REVIEW)

    # ── T13: Training T3 Trajectory ──
    print("T13: Training T3 Trajectory")

    trajectory = evaluator.get_trajectory(trainee_lct)
    check("T13.1 Trajectory has entries", len(trajectory) == 3)
    check("T13.2 First entry talent increased", trajectory[0].talent > 0.5)
    check("T13.3 Second entry training decreased", trajectory[1].training < trajectory[0].training)

    # Skill summary
    summary = evaluator.get_skill_summary("web4_fundamentals")
    check("T13.4 Summary count 3", summary["count"] == 3)
    check("T13.5 Summary evaluated 3", summary["evaluated"] == 3)
    check("T13.6 Summary included 1", summary["included"] == 1)
    check("T13.7 Summary excluded 1", summary["excluded"] == 1)
    check("T13.8 Summary review 1", summary["review"] == 1)
    check("T13.9 Average quality", 0.0 < summary["avg_quality"] < 1.0)

    # Empty skill track
    empty_summary = evaluator.get_skill_summary("nonexistent")
    check("T13.10 Empty summary", empty_summary["count"] == 0)

    # ── T14: Meta-Cognitive Signals ──
    print("T14: Meta-Cognitive Signals")

    mc_all = MetaCognitiveSignals(
        clarification_requests=3, modal_awareness=True,
        self_correction=True, uncertainty_expression=True,
        reasoning_transparency=True,
    )
    check("T14.1 All signals score 1.0", mc_all.score() == 1.0)

    mc_none = MetaCognitiveSignals()
    check("T14.2 No signals score 0.0", mc_none.score() == 0.0)

    mc_partial = MetaCognitiveSignals(
        clarification_requests=1, modal_awareness=False,
        self_correction=True, uncertainty_expression=False,
        reasoning_transparency=False,
    )
    check("T14.3 Partial score", abs(mc_partial.score() - 0.4) < 0.001)

    # ── T15: Tier Upgrade: Observational → Authorization ──
    print("T15: Tier Upgrade: Observational → Authorization")

    obs_chain = ObservationalAuditChain()
    rec = obs_chain.before_tool_call("analyze", "data", "dataset.csv", "config")
    obs_chain.after_tool_call(rec, "success", "analysis complete", duration_ms=200)
    rec2 = obs_chain.before_tool_call("export", "data", "results.json", "export cfg")
    obs_chain.after_tool_call(rec2, "success", "exported", duration_ms=100)
    rec3 = obs_chain.before_tool_call("notify", "comm", "team", "msg")
    obs_chain.after_tool_call(rec3, "error", "", error="timeout", duration_ms=5000)

    upgrade_engine = AuthorizationEngine()
    upgrade_engine.register_actor("lct:web4:human:upgrader", AuthRole.DEVELOPER)

    imported = TierUpgradeManager.import_observational_to_authorization(
        obs_chain, upgrade_engine, "lct:web4:human:upgrader", AuthRole.DEVELOPER
    )
    check("T15.1 Imported 3 records", len(imported) == 3)
    check("T15.2 First completed", imported[0].state_machine.state == AuthorizationStatus.COMPLETED)
    check("T15.3 Second completed", imported[1].state_machine.state == AuthorizationStatus.COMPLETED)
    check("T15.4 Third failed (error)", imported[2].state_machine.state == AuthorizationStatus.FAILED)
    check("T15.5 Description mentions import", "Imported" in imported[0].request.description)

    # ── T16: Tier Upgrade: Authorization → Training ──
    print("T16: Tier Upgrade: Authorization → Training")

    training_eval = TrainingEvaluator()
    imported_exercises = TierUpgradeManager.import_authorization_to_training(
        upgrade_engine, training_eval, skill_track="imported_actions"
    )
    # upgrade_engine has bundles from T7-T9 plus T15 imports
    completed_or_failed = [
        b for b in upgrade_engine.bundles.values()
        if b.state_machine.state in (AuthorizationStatus.COMPLETED, AuthorizationStatus.FAILED)
    ]
    check("T16.1 Imported exercises match", len(imported_exercises) == len(completed_or_failed))
    check("T16.2 All have results", all(e.result is not None for e in imported_exercises))

    # Check success-based quality
    success_exercises = [e for e in imported_exercises if e.result.quality >= 0.7]
    check("T16.3 High quality for successes", len(success_exercises) > 0)

    summary = training_eval.get_skill_summary("imported_actions")
    check("T16.4 Summary populated", summary["count"] > 0)

    # ── T17: Trust Integration Levels ──
    print("T17: Trust Integration Levels")

    ti1 = TrustIntegration.for_tier(1)
    check("T17.1 Tier 1 relying party", ti1.level == TrustIntegrationLevel.RELYING_PARTY)
    check("T17.2 Tier 1 no T3", not ti1.has_t3)
    check("T17.3 Tier 1 no ATP", not ti1.has_atp)
    check("T17.4 Tier 1 no trajectory", not ti1.has_trajectory)

    ti2 = TrustIntegration.for_tier(2)
    check("T17.5 Tier 2 T3 tensor", ti2.level == TrustIntegrationLevel.T3_TENSOR)
    check("T17.6 Tier 2 has T3", ti2.has_t3)
    check("T17.7 Tier 2 has ATP", ti2.has_atp)
    check("T17.8 Tier 2 no trajectory", not ti2.has_trajectory)

    ti3 = TrustIntegration.for_tier(3)
    check("T17.9 Tier 3 developmental", ti3.level == TrustIntegrationLevel.T3_DEVELOPMENTAL)
    check("T17.10 Tier 3 has T3", ti3.has_t3)
    check("T17.11 Tier 3 has trajectory", ti3.has_trajectory)
    check("T17.12 Tier 3 has ATP", ti3.has_atp)

    # Invalid tier
    try:
        TrustIntegration.for_tier(4)
        check("T17.13 Invalid tier raises", False)
    except ValueError:
        check("T17.13 Invalid tier raises", True)

    # ── T18: Authorization Failure Path ──
    print("T18: Authorization Failure Path")

    fail_engine = AuthorizationEngine()
    fail_engine.register_actor("lct:web4:ai:agent01", AuthRole.DEVELOPER,
                                T3TrustTensor(0.6, 0.6, 0.6))

    fb = fail_engine.create_request(
        actor_lct="lct:web4:ai:agent01", actor_role=AuthRole.DEVELOPER,
        action_type="analyze", target="dataset",
        description="Analyze customer data",
        rationale="Quarterly report",
        atp_estimate=50.0,
    )
    fail_engine.approve(fb.bundle_id, AuthRole.REVIEWER, "approved")
    fail_engine.complete(
        fb.bundle_id, success=False, atp_consumed=45.0,
        trust_delta={"training": -0.005, "temperament": -0.01},
        learnings=["Data format was unexpected"],
        surprises=["Missing columns in dataset"],
    )
    check("T18.1 State failed", fb.state_machine.state == AuthorizationStatus.FAILED)
    check("T18.2 Result not success", not fb.result.success)
    check("T18.3 T3 training decreased", fail_engine.actors["lct:web4:ai:agent01"].training < 0.6)
    check("T18.4 T3 temperament decreased", fail_engine.actors["lct:web4:ai:agent01"].temperament < 0.6)
    check("T18.5 Learnings recorded", len(fb.result.learnings) == 1)
    check("T18.6 Surprises recorded", len(fb.result.surprises) == 1)

    # ── T19: Multiple Chains Independence ──
    print("T19: Multiple Chains Independence")

    chain_a = ObservationalAuditChain()
    chain_b = ObservationalAuditChain()

    rec_a = chain_a.before_tool_call("tool_a", "cat_a", "target_a", "input_a")
    chain_a.after_tool_call(rec_a, "success", "out_a")

    rec_b = chain_b.before_tool_call("tool_b", "cat_b", "target_b", "input_b")
    chain_b.after_tool_call(rec_b, "success", "out_b")

    check("T19.1 Different sessions", chain_a.session_token != chain_b.session_token)
    check("T19.2 Different R6 IDs", chain_a.records[0].r6_id != chain_b.records[0].r6_id)
    check("T19.3 Different hashes", chain_a.records[0].record_hash != chain_b.records[0].record_hash)

    valid_a, _ = chain_a.verify_chain()
    valid_b, _ = chain_b.verify_chain()
    check("T19.4 Chain A valid", valid_a)
    check("T19.5 Chain B valid", valid_b)

    # ── T20: Operational Modes ──
    print("T20: Operational Modes")

    check("T20.1 Conversation mode", OperationalMode.CONVERSATION.value == "conversation")
    check("T20.2 Refinement mode", OperationalMode.REFINEMENT.value == "refinement")
    check("T20.3 Philosophical mode", OperationalMode.PHILOSOPHICAL.value == "philosophical")

    # Training roles
    check("T20.4 Learning partner", TrainingRole.LEARNING_PARTNER.value == "learning_partner")
    check("T20.5 Practice student", TrainingRole.PRACTICE_STUDENT.value == "practice_student")
    check("T20.6 Skill practitioner", TrainingRole.SKILL_PRACTITIONER.value == "skill_practitioner")

    # ── T21: Authorization Engine — Multiple Bundles ──
    print("T21: Authorization Engine — Multiple Bundles")

    multi_engine = AuthorizationEngine()
    multi_engine.register_actor("lct:web4:human:alice", AuthRole.DEVELOPER)
    multi_engine.register_actor("lct:web4:human:bob", AuthRole.DEVELOPER)

    b_alice = multi_engine.create_request(
        actor_lct="lct:web4:human:alice", actor_role=AuthRole.DEVELOPER,
        action_type="build", target="frontend",
        description="Build frontend", rationale="Sprint 3",
    )
    b_bob = multi_engine.create_request(
        actor_lct="lct:web4:human:bob", actor_role=AuthRole.DEVELOPER,
        action_type="build", target="backend",
        description="Build backend", rationale="Sprint 3",
    )
    check("T21.1 Two bundles created", len(multi_engine.bundles) >= 2)
    check("T21.2 Different IDs", b_alice.bundle_id != b_bob.bundle_id)
    check("T21.3 Different actors", b_alice.role.actor_lct != b_bob.role.actor_lct)

    # Approve both
    multi_engine.approve(b_alice.bundle_id, AuthRole.ADMIN)
    multi_engine.approve(b_bob.bundle_id, AuthRole.ADMIN)
    check("T21.4 Alice approved", b_alice.state_machine.state == AuthorizationStatus.APPROVED)
    check("T21.5 Bob approved", b_bob.state_machine.state == AuthorizationStatus.APPROVED)

    # Complete one, fail other
    multi_engine.complete(b_alice.bundle_id, success=True, atp_consumed=30)
    multi_engine.complete(b_bob.bundle_id, success=False, atp_consumed=40)
    check("T21.6 Alice completed", b_alice.state_machine.state == AuthorizationStatus.COMPLETED)
    check("T21.7 Bob failed", b_bob.state_machine.state == AuthorizationStatus.FAILED)

    # ── T22: Chain Hash Determinism ──
    print("T22: Chain Hash Determinism")

    # Same inputs produce same hash
    chain1 = ObservationalAuditChain(session_token="web4:session:aabbccddeeff")
    chain2 = ObservationalAuditChain(session_token="web4:session:aabbccddeeff")

    r1 = ObservationalRecord(
        r6_id="r6:00000001",
        request=ObservationalRequest(tool="test", category="cat", target="tgt", input_hash="abc123"),
        reference=ObservationalReference(session_id="web4:session:aabbccddeeff"),
        timestamp="2025-01-01T00:00:00",
    )
    r2 = ObservationalRecord(
        r6_id="r6:00000001",
        request=ObservationalRequest(tool="test", category="cat", target="tgt", input_hash="abc123"),
        reference=ObservationalReference(session_id="web4:session:aabbccddeeff"),
        timestamp="2025-01-01T00:00:00",
    )
    hash1 = r1.compute_hash("genesis")
    hash2 = r2.compute_hash("genesis")
    check("T22.1 Deterministic hashing", hash1 == hash2)

    # Different inputs produce different hash
    r3 = ObservationalRecord(
        r6_id="r6:00000002",
        request=ObservationalRequest(tool="test", category="cat", target="tgt", input_hash="abc123"),
        reference=ObservationalReference(session_id="web4:session:aabbccddeeff"),
        timestamp="2025-01-01T00:00:00",
    )
    hash3 = r3.compute_hash("genesis")
    check("T22.2 Different ID different hash", hash1 != hash3)

    # Different prev_hash produces different hash
    hash4 = r1.compute_hash("different_prev")
    check("T22.3 Different prev different hash", hash1 != hash4)

    # ── T23: State Machine History ──
    print("T23: State Machine History")

    sm = StateMachine(AuthorizationStatus.PENDING, AUTHORIZATION_TRANSITIONS)
    sm.transition(AuthorizationStatus.IN_PROGRESS, "started review")
    sm.transition(AuthorizationStatus.APPROVED, "reviewer approved")
    sm.transition(AuthorizationStatus.COMPLETED, "execution done")

    check("T23.1 History has 4 entries", len(sm.history) == 4)
    check("T23.2 First entry init", sm.history[0][2] == "init")
    check("T23.3 Second entry reason", sm.history[1][2] == "started review")
    check("T23.4 Third entry reason", sm.history[2][2] == "reviewer approved")
    check("T23.5 Fourth entry reason", sm.history[3][2] == "execution done")
    check("T23.6 History states correct",
          [h[0] for h in sm.history] == [
              AuthorizationStatus.PENDING, AuthorizationStatus.IN_PROGRESS,
              AuthorizationStatus.APPROVED, AuthorizationStatus.COMPLETED
          ])

    # ── T24: Training Evaluation Boundary Cases ──
    print("T24: Training Evaluation Boundary Cases")

    boundary_eval = TrainingEvaluator()
    boundary_lct = "lct:web4:ai:boundary01"

    # Exactly at include threshold (0.7 quality, 0.4 meta)
    ex_boundary = boundary_eval.create_exercise(
        exercise_type="conversation", prompt="Test", intent="Test",
        expected_pattern="test", mode=OperationalMode.CONVERSATION,
        role=TrainingRole.LEARNING_PARTNER, lct=boundary_lct,
        skill_track="boundary_tests",
    )
    meta_boundary = MetaCognitiveSignals(
        clarification_requests=1, modal_awareness=True,
    )  # score = 2/5 = 0.4
    res = boundary_eval.evaluate(ex_boundary, "response", quality=0.7, meta_signals=meta_boundary)
    check("T24.1 Boundary quality 0.7 + meta 0.4 = include", res.status == "include")

    # Just below include (quality 0.69)
    ex_below = boundary_eval.create_exercise(
        exercise_type="conversation", prompt="Test", intent="Test",
        expected_pattern="test", mode=OperationalMode.CONVERSATION,
        role=TrainingRole.LEARNING_PARTNER, lct=boundary_lct,
        skill_track="boundary_tests",
    )
    res2 = boundary_eval.evaluate(ex_below, "response", quality=0.69, meta_signals=meta_boundary)
    check("T24.2 Below threshold = review", res2.status == "review")

    # Quality 0.7 but meta below 0.4
    ex_low_meta = boundary_eval.create_exercise(
        exercise_type="conversation", prompt="Test", intent="Test",
        expected_pattern="test", mode=OperationalMode.CONVERSATION,
        role=TrainingRole.LEARNING_PARTNER, lct=boundary_lct,
        skill_track="boundary_tests",
    )
    meta_low = MetaCognitiveSignals(clarification_requests=1)  # score = 1/5 = 0.2
    res3 = boundary_eval.evaluate(ex_low_meta, "response", quality=0.7, meta_signals=meta_low)
    check("T24.3 Good quality but low meta = review", res3.status == "review")

    # Exactly at exclude threshold (0.3)
    ex_exclude_boundary = boundary_eval.create_exercise(
        exercise_type="conversation", prompt="Test", intent="Test",
        expected_pattern="test", mode=OperationalMode.CONVERSATION,
        role=TrainingRole.LEARNING_PARTNER, lct=boundary_lct,
        skill_track="boundary_tests",
    )
    res4 = boundary_eval.evaluate(ex_exclude_boundary, "response", quality=0.3)
    check("T24.4 Quality 0.3 = review (not exclude)", res4.status == "review")

    ex_just_below = boundary_eval.create_exercise(
        exercise_type="conversation", prompt="Test", intent="Test",
        expected_pattern="test", mode=OperationalMode.CONVERSATION,
        role=TrainingRole.LEARNING_PARTNER, lct=boundary_lct,
        skill_track="boundary_tests",
    )
    res5 = boundary_eval.evaluate(ex_just_below, "response", quality=0.29)
    check("T24.5 Quality 0.29 = exclude", res5.status == "exclude")

    # ── T25: Full Lifecycle ──
    print("T25: Full Lifecycle (Tier 1 → 2 → 3)")

    # Tier 1: Observe
    lifecycle_chain = ObservationalAuditChain()
    for i in range(5):
        rec = lifecycle_chain.before_tool_call(
            f"tool_{i}", "category", f"target_{i}", f"input_{i}"
        )
        status = "success" if i < 4 else "error"
        error = "timeout" if i == 4 else None
        lifecycle_chain.after_tool_call(rec, status, f"output_{i}", error=error, duration_ms=i * 10)

    valid, _ = lifecycle_chain.verify_chain()
    check("T25.1 Lifecycle chain valid", valid)
    check("T25.2 5 observational records", len(lifecycle_chain.records) == 5)

    # Tier 2: Import and authorize
    lifecycle_engine = AuthorizationEngine()
    lifecycle_engine.register_actor("lct:web4:human:ops", AuthRole.DEVELOPER, T3TrustTensor(0.7, 0.7, 0.7))

    imported_bundles = TierUpgradeManager.import_observational_to_authorization(
        lifecycle_chain, lifecycle_engine, "lct:web4:human:ops"
    )
    check("T25.3 5 bundles imported", len(imported_bundles) == 5)

    completed_count = sum(
        1 for b in imported_bundles
        if b.state_machine.state == AuthorizationStatus.COMPLETED
    )
    failed_count = sum(
        1 for b in imported_bundles
        if b.state_machine.state == AuthorizationStatus.FAILED
    )
    check("T25.4 4 completed (successes)", completed_count == 4)
    check("T25.5 1 failed (error)", failed_count == 1)

    # Tier 3: Import for training
    lifecycle_trainer = TrainingEvaluator()
    training_exercises = TierUpgradeManager.import_authorization_to_training(
        lifecycle_engine, lifecycle_trainer, "lifecycle_track"
    )
    check("T25.6 5 exercises imported", len(training_exercises) == 5)

    summary = lifecycle_trainer.get_skill_summary("lifecycle_track")
    check("T25.7 Summary evaluated", summary["evaluated"] == 5)
    check("T25.8 Summary has included", summary["included"] > 0)

    # ── T26: Observational Chain with Custom Session ──
    print("T26: Custom Session and Edge Cases")

    custom_session = "web4:session:112233445566"
    custom_chain = ObservationalAuditChain(session_token=custom_session)
    check("T26.1 Custom session preserved", custom_chain.session_token == custom_session)

    # Empty chain verification
    valid, _ = custom_chain.verify_chain()
    check("T26.2 Empty chain valid", valid)

    # JSONL of empty chain
    jsonl = custom_chain.to_jsonl()
    check("T26.3 Empty chain JSONL empty", jsonl == "")

    # Single record chain
    rec = custom_chain.before_tool_call("single", "test", "one", "data")
    custom_chain.after_tool_call(rec, "success", "done")
    valid, _ = custom_chain.verify_chain()
    check("T26.4 Single record chain valid", valid)

    # ── Summary ──
    print(f"\n{'='*60}")
    print(f"R6 Implementation Tiers: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")

    return passed, total


if __name__ == "__main__":
    run_tests()
