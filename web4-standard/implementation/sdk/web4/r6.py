"""
Web4 R7 Action Framework

Canonical implementation per web4-standard/core-spec/r7-framework.md.

R7 evolves R6 by making reputation an explicit first-class output:
    Rules + Role + Request + Reference + Resource → Result + Reputation

This module provides DATA STRUCTURES and validation for constructing,
chaining, and inspecting R7 actions. It does NOT evaluate policy or
execute actions — that belongs in PolicyGate/HRM.

Cross-module integration:
- web4.trust: T3/V3 tensors for reputation deltas
- web4.lct: entity identity (LCT IDs, EntityType)
- web4.atp: resource tracking (ATP escrow, consumption)

Naming: the module is r6.py because R6 is the canonical CLAUDE.md term
and the protected acronym. R7 is the current version of the R6 framework.

Validated against: web4-standard/test-vectors/r6/
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .trust import T3, V3, _clamp

__all__ = [
    # Classes
    "R7Action", "ActionChain", "ActionStatus", "ReputationDelta",
    "Rules", "Role", "Request", "ResourceRequirements", "Result",
    "R7Error", "Constraint", "ContributingFactor", "Precedent",
    "Reference", "TensorDelta",
    "ReferenceInvalid", "ReputationComputationError", "RequestMalformed",
    "ResourceInsufficient", "ResultInvalid", "RoleUnauthorized", "RuleViolation",
    # Also in this module but used by reputation
    "ProofOfAgency", "WitnessAttestation",
    # Functions
    "build_action",
    # Constants
    "R7_JSONLD_CONTEXT",
]

# JSON-LD context URI for R7 Action documents
R7_JSONLD_CONTEXT = "https://web4.io/contexts/r7-action.jsonld"


# ── Action Status ───────────────────────────────────────────────

class ActionStatus(str, Enum):
    """R7 action lifecycle states."""
    PENDING = "pending"
    VALIDATED = "validated"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    CANCELLED = "cancelled"


# ── R7 Error Hierarchy ──────────────────────────────────────────

class R7Error(Exception):
    """Base error for R7 action framework."""


class RuleViolation(R7Error):
    """Action violates governing rules."""


class RoleUnauthorized(R7Error):
    """Actor lacks required role or permissions."""


class RequestMalformed(R7Error):
    """Request structure or parameters invalid."""


class ReferenceInvalid(R7Error):
    """Referenced entities not found or invalid."""


class ResourceInsufficient(R7Error):
    """Required resources unavailable."""


class ResultInvalid(R7Error):
    """Result violates output constraints."""


class ReputationComputationError(R7Error):
    """Reputation delta cannot be computed."""


# ── 1. Rules ────────────────────────────────────────────────────

@dataclass(frozen=True)
class Constraint:
    """A single constraint within Rules."""
    constraint_type: str   # e.g. "rate_limit", "atp_minimum", "witness_required"
    value: Any             # threshold or limit

    def to_dict(self) -> Dict:
        """Serialize to dict with 'type' and 'value' keys."""
        return {"type": self.constraint_type, "value": self.value}


@dataclass
class Rules:
    """
    Governing constraints and policies for an R7 action.

    Sources: SAL law norms, smart contracts, role permissions, society policies.
    """
    law_hash: str = ""
    society: str = ""
    constraints: List[Constraint] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    prohibitions: List[str] = field(default_factory=list)

    def has_permission(self, action: str) -> bool:
        """Check if action is permitted (not in prohibitions, in permissions if non-empty)."""
        if action in self.prohibitions:
            return False
        if self.permissions and action not in self.permissions:
            return False
        return True

    def check_constraint(self, constraint_type: str, actual_value: float) -> bool:
        """Check a specific constraint. Returns True if no constraint of that type exists."""
        for c in self.constraints:
            if c.constraint_type == constraint_type:
                if isinstance(c.value, (int, float)):
                    return actual_value >= c.value if constraint_type.endswith("_minimum") else actual_value <= c.value
        return True

    def to_dict(self) -> Dict:
        """Serialize rules to dict with constraints, permissions, and prohibitions."""
        return {
            "lawHash": self.law_hash,
            "society": self.society,
            "constraints": [c.to_dict() for c in self.constraints],
            "permissions": self.permissions,
            "prohibitions": self.prohibitions,
        }


# ── 2. Role ─────────────────────────────────────────────────────

@dataclass
class Role:
    """
    Contextual identity under which an action is performed.

    Both T3 and V3 are stored on the MRH role pairing link.
    There is no global reputation — all reputation is role-contextualized.
    """
    actor: str             # entity LCT ID
    role_lct: str          # role LCT ID (domain-specific, fully flexible)
    paired_at: str = ""    # ISO timestamp of role pairing
    t3_in_role: Optional[T3] = None
    v3_in_role: Optional[V3] = None

    def to_dict(self) -> Dict:
        """Serialize role to dict with actor, role LCT, and optional T3/V3 tensors."""
        d: Dict[str, Any] = {
            "actor": self.actor,
            "roleLCT": self.role_lct,
            "pairedAt": self.paired_at,
        }
        if self.t3_in_role:
            d["t3InRole"] = self.t3_in_role.as_dict()
        if self.v3_in_role:
            d["v3InRole"] = self.v3_in_role.as_dict()
        return d


# ── 3. Request ──────────────────────────────────────────────────

@dataclass
class ProofOfAgency:
    """Proof that an agent is acting on behalf of a principal."""
    grant_id: str
    inclusion_proof: str = ""
    scope: str = ""
    audience: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Serialize proof of agency to dict with grant ID and scope."""
        return {
            "grantId": self.grant_id,
            "inclusionProof": self.inclusion_proof,
            "scope": self.scope,
            "audience": self.audience,
        }


@dataclass
class Request:
    """
    The specific action intent and parameters.

    Every R7 action begins with a request specifying what to do.
    """
    action: str                         # verb (e.g. "analyze_dataset", "delegate")
    target: str = ""                    # target entity or resource
    parameters: Dict[str, Any] = field(default_factory=dict)
    atp_stake: float = 0.0             # ATP staked on this request
    nonce: str = ""                     # unique request identifier
    constraints: Dict[str, Any] = field(default_factory=dict)  # temporal, budget limits
    proof_of_agency: Optional[ProofOfAgency] = None

    def to_dict(self) -> Dict:
        """Serialize request to dict with action, target, ATP stake, and optional proof of agency."""
        d: Dict[str, Any] = {
            "action": self.action,
            "target": self.target,
            "parameters": self.parameters,
            "atpStake": self.atp_stake,
            "nonce": self.nonce,
        }
        if self.constraints:
            d["constraints"] = self.constraints
        if self.proof_of_agency:
            d["proofOfAgency"] = self.proof_of_agency.to_dict()
        return d


# ── 4. Reference ────────────────────────────────────────────────

@dataclass(frozen=True)
class Precedent:
    """A previous action referenced as precedent."""
    action_hash: str
    outcome: str = ""
    relevance: float = 0.0

    def to_dict(self) -> Dict:
        """Serialize precedent to dict with action hash, outcome, and relevance score."""
        return {"actionHash": self.action_hash, "outcome": self.outcome, "relevance": self.relevance}


@dataclass(frozen=True)
class WitnessAttestation:
    """An attestation from a witness."""
    lct: str
    attestation: str = "verified"
    signature: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict:
        """Serialize witness attestation to dict with LCT, attestation type, and signature."""
        return {
            "lct": self.lct,
            "attestation": self.attestation,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }


@dataclass
class Reference:
    """
    Historical context and precedents informing the action.

    Sources: MRH graph, previous actions, law interpretations, witness attestations.
    """
    precedents: List[Precedent] = field(default_factory=list)
    mrh_depth: int = 0
    relevant_entities: List[str] = field(default_factory=list)
    witnesses: List[WitnessAttestation] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Serialize reference to dict with precedents, MRH context, and witnesses."""
        return {
            "precedents": [p.to_dict() for p in self.precedents],
            "mrhContext": {
                "depth": self.mrh_depth,
                "relevantEntities": self.relevant_entities,
            },
            "witnesses": [w.to_dict() for w in self.witnesses],
        }


# ── 5. Resource ─────────────────────────────────────────────────

@dataclass
class ResourceRequirements:
    """Required and available resources for an R7 action."""
    required_atp: float = 0.0
    available_atp: float = 0.0
    compute: Dict[str, Any] = field(default_factory=dict)  # e.g. {"cpu": "2_cores"}
    escrow_amount: float = 0.0
    escrow_condition: str = "result_verified"

    @property
    def has_sufficient_atp(self) -> bool:
        """True if available ATP meets or exceeds required ATP."""
        return self.available_atp >= self.required_atp

    def to_dict(self) -> Dict:
        """Serialize resource requirements to dict with required/available ATP and optional escrow."""
        d: Dict[str, Any] = {
            "required": {"atp": self.required_atp},
            "available": {"atp_balance": self.available_atp},
        }
        if self.compute:
            d["required"]["compute"] = self.compute
        if self.escrow_amount > 0:
            d["escrow"] = {
                "amount": self.escrow_amount,
                "release_condition": self.escrow_condition,
            }
        return d


# ── 6. Result ───────────────────────────────────────────────────

@dataclass
class Result:
    """
    Deterministic outcome of an R7 action execution.

    Even failed actions produce a valid Result.
    """
    status: ActionStatus = ActionStatus.PENDING
    output: Dict[str, Any] = field(default_factory=dict)
    output_hash: str = ""
    error: Optional[str] = None
    atp_consumed: float = 0.0
    resource_consumed: Dict[str, Any] = field(default_factory=dict)
    attestations: List[WitnessAttestation] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Serialize result to dict with status, output, resource consumption, and attestations."""
        d: Dict[str, Any] = {
            "status": self.status.value,
            "resourceConsumed": {"atp": self.atp_consumed},
        }
        if self.status in (ActionStatus.SUCCESS, ActionStatus.PENDING, ActionStatus.VALIDATED):
            d["output"] = self.output
            if self.output_hash:
                d["output"]["hash"] = self.output_hash
        if self.error:
            d["error"] = {"message": self.error}
        if self.resource_consumed:
            d["resourceConsumed"].update(self.resource_consumed)
        if self.attestations:
            d["attestations"] = [a.to_dict() for a in self.attestations]
        return d


# ── 7. Reputation ──────────────────────────────────────────────

@dataclass(frozen=True)
class TensorDelta:
    """Change to a single tensor dimension."""
    change: float
    from_value: float
    to_value: float

    def to_dict(self) -> Dict:
        """Serialize tensor delta to dict with change magnitude and from/to values."""
        return {"change": self.change, "from": self.from_value, "to": self.to_value}


@dataclass(frozen=True)
class ContributingFactor:
    """A factor that contributed to a reputation change."""
    factor: str
    weight: float

    def to_dict(self) -> Dict:
        """Serialize contributing factor to dict with factor name and weight."""
        return {"factor": self.factor, "weight": self.weight}


@dataclass
class ReputationDelta:
    """
    Explicit trust/value changes resulting from an R7 action.

    This is the R7 innovation: reputation is a first-class output.
    Reputation is ROLE-CONTEXTUALIZED — changes apply to the specific
    MRH role pairing link, not to the entity globally.
    """
    subject_lct: str                                    # whose reputation changed
    role_lct: str                                       # which role context
    action_type: str = ""                               # what action was performed
    action_target: str = ""                             # target of the action
    action_id: str = ""                                 # ledger reference
    rule_triggered: str = ""                            # which rule caused the change
    reason: str = ""
    t3_delta: Dict[str, TensorDelta] = field(default_factory=dict)
    v3_delta: Dict[str, TensorDelta] = field(default_factory=dict)
    contributing_factors: List[ContributingFactor] = field(default_factory=list)
    witnesses: List[WitnessAttestation] = field(default_factory=list)
    timestamp: str = ""

    @property
    def net_trust_change(self) -> float:
        """Sum of all T3 dimension changes."""
        return sum(d.change for d in self.t3_delta.values())

    @property
    def net_value_change(self) -> float:
        """Sum of all V3 dimension changes."""
        return sum(d.change for d in self.v3_delta.values())

    def to_dict(self) -> Dict:
        """Serialize reputation delta to dict with T3/V3 deltas and net change totals."""
        d: Dict[str, Any] = {
            "subject_lct": self.subject_lct,
            "role_lct": self.role_lct,
            "action_type": self.action_type,
            "action_target": self.action_target,
            "action_id": self.action_id,
            "rule_triggered": self.rule_triggered,
            "reason": self.reason,
            "t3_delta": {k: v.to_dict() for k, v in self.t3_delta.items()},
            "v3_delta": {k: v.to_dict() for k, v in self.v3_delta.items()},
            "contributing_factors": [f.to_dict() for f in self.contributing_factors],
            "witnesses": [w.to_dict() for w in self.witnesses],
            "net_trust_change": self.net_trust_change,
            "net_value_change": self.net_value_change,
            "timestamp": self.timestamp,
        }
        return d

    def to_jsonld(self) -> Dict[str, Any]:
        """
        Serialize to spec-compliant JSON-LD per r7-framework.md §1.7.

        Produces the canonical ReputationDelta structure with JSON-LD context,
        spec-compliant field naming (camelCase for ontology alignment), and
        computed net change fields.
        """
        doc: Dict[str, Any] = {
            "@context": [R7_JSONLD_CONTEXT],
            "@type": "ReputationDelta",
            "subject_lct": self.subject_lct,
            "role_lct": self.role_lct,
            "action_type": self.action_type,
            "action_target": self.action_target,
            "action_id": self.action_id,
        }
        if self.rule_triggered:
            doc["rule_triggered"] = self.rule_triggered
        if self.reason:
            doc["reason"] = self.reason
        if self.t3_delta:
            doc["t3_delta"] = {k: v.to_dict() for k, v in self.t3_delta.items()}
        if self.v3_delta:
            doc["v3_delta"] = {k: v.to_dict() for k, v in self.v3_delta.items()}
        if self.contributing_factors:
            doc["contributing_factors"] = [f.to_dict() for f in self.contributing_factors]
        if self.witnesses:
            doc["witnesses"] = [w.to_dict() for w in self.witnesses]
        doc["net_trust_change"] = self.net_trust_change
        doc["net_value_change"] = self.net_value_change
        if self.timestamp:
            doc["timestamp"] = self.timestamp
        return doc

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> ReputationDelta:
        """
        Deserialize from JSON-LD or dict representation.

        Accepts both spec JSON-LD format (with @context) and plain dict format.
        """
        t3_delta: Dict[str, TensorDelta] = {}
        for dim, delta in doc.get("t3_delta", {}).items():
            t3_delta[dim] = TensorDelta(
                change=delta["change"],
                from_value=delta["from"],
                to_value=delta["to"],
            )
        v3_delta: Dict[str, TensorDelta] = {}
        for dim, delta in doc.get("v3_delta", {}).items():
            v3_delta[dim] = TensorDelta(
                change=delta["change"],
                from_value=delta["from"],
                to_value=delta["to"],
            )
        contributing_factors = [
            ContributingFactor(factor=f["factor"], weight=f["weight"])
            for f in doc.get("contributing_factors", [])
        ]
        witnesses = [
            WitnessAttestation(
                lct=w["lct"],
                attestation=w.get("attestation", "verified"),
                signature=w.get("signature", ""),
                timestamp=w.get("timestamp", ""),
            )
            for w in doc.get("witnesses", [])
        ]
        return cls(
            subject_lct=doc["subject_lct"],
            role_lct=doc["role_lct"],
            action_type=doc.get("action_type", ""),
            action_target=doc.get("action_target", ""),
            action_id=doc.get("action_id", ""),
            rule_triggered=doc.get("rule_triggered", ""),
            reason=doc.get("reason", ""),
            t3_delta=t3_delta,
            v3_delta=v3_delta,
            contributing_factors=contributing_factors,
            witnesses=witnesses,
            timestamp=doc.get("timestamp", ""),
        )


# ── R7 Action (Composite) ──────────────────────────────────────

@dataclass
class R7Action:
    """
    Complete R7 action: Rules + Role + Request + Reference + Resource → Result + Reputation.

    An R7Action is the fundamental unit of work in Web4. Every transaction,
    query, delegation, or interaction is structured as an R7Action.
    """
    rules: Rules = field(default_factory=Rules)
    role: Role = field(default_factory=lambda: Role(actor="", role_lct=""))
    request: Request = field(default_factory=lambda: Request(action=""))
    reference: Reference = field(default_factory=Reference)
    resource: ResourceRequirements = field(default_factory=ResourceRequirements)
    result: Result = field(default_factory=Result)
    reputation: Optional[ReputationDelta] = None

    # Chain linking
    action_id: str = ""
    prev_action_hash: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.action_id:
            self.action_id = self._generate_id()

    def _generate_id(self) -> str:
        raw = f"{self.role.actor}:{self.request.action}:{self.request.nonce}:{self.timestamp}"
        h = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"r7:{h}"

    # ── Validation ──────────────────────────────────────────────

    def validate(self) -> List[str]:
        """
        Pre-execution validation. Returns list of error strings (empty = valid).

        Checks structure completeness, permission alignment, and resource sufficiency.
        Does NOT evaluate policy (that's PolicyGate's job).
        """
        errors = []

        # Actor and role must be present
        if not self.role.actor:
            errors.append("role.actor is required")
        if not self.role.role_lct:
            errors.append("role.role_lct is required")

        # Request must have an action
        if not self.request.action:
            errors.append("request.action is required")

        # Permission check
        if not self.rules.has_permission(self.request.action):
            errors.append(f"action '{self.request.action}' is not permitted by rules")

        # Resource sufficiency
        if not self.resource.has_sufficient_atp:
            errors.append(
                f"insufficient ATP: need {self.resource.required_atp}, "
                f"have {self.resource.available_atp}"
            )

        # ATP stake consistency
        if self.request.atp_stake > 0 and self.resource.required_atp < self.request.atp_stake:
            errors.append("resource.required_atp must be >= request.atp_stake")

        return errors

    @property
    def is_valid(self) -> bool:
        """True if the action passes all structural validation checks."""
        return len(self.validate()) == 0

    # ── Reputation Computation ──────────────────────────────────

    def compute_reputation(
        self,
        quality: float,
        rule_triggered: str = "",
        reason: str = "",
        factors: Optional[List[ContributingFactor]] = None,
    ) -> ReputationDelta:
        """
        Compute reputation delta from action outcome.

        Uses the role's current T3/V3 and the action's quality score
        to produce T3/V3 deltas. Quality is in [0, 1]:
          quality < 0.5 → negative reputation change
          quality = 0.5 → no change
          quality > 0.5 → positive reputation change

        The deltas are computed using T3.update() logic so they're
        consistent with the canonical trust update mechanism.
        """
        current_t3 = self.role.t3_in_role or T3()
        current_v3 = self.role.v3_in_role or V3()

        # Compute T3 delta via canonical update
        updated_t3 = current_t3.update(quality)
        t3_delta = {}
        for dim in ("talent", "training", "temperament"):
            old = getattr(current_t3, dim)
            new = getattr(updated_t3, dim)
            change = round(new - old, 10)
            if change != 0:
                t3_delta[dim] = TensorDelta(change=change, from_value=old, to_value=new)

        # Compute V3 delta (proportional to quality deviation from 0.5)
        # V3 uses simpler update: veracity/validity shift toward quality signal
        v3_delta_value = 0.02 * (quality - 0.5)
        v3_delta = {}
        if v3_delta_value != 0:
            for dim in ("veracity", "validity"):
                old = getattr(current_v3, dim)
                new = _clamp(old + v3_delta_value)
                change = round(new - old, 10)
                if change != 0:
                    v3_delta[dim] = TensorDelta(change=change, from_value=old, to_value=new)

        ts = datetime.now(timezone.utc).isoformat()

        if not reason:
            if self.result.status == ActionStatus.SUCCESS:
                reason = f"Completed {self.request.action} on {self.request.target}"
            elif self.result.status == ActionStatus.FAILURE:
                reason = f"Failed {self.request.action}: {self.result.error or 'unknown'}"
            else:
                reason = f"Action {self.request.action} outcome quality={quality}"

        rep = ReputationDelta(
            subject_lct=self.role.actor,
            role_lct=self.role.role_lct,
            action_type=self.request.action,
            action_target=self.request.target,
            action_id=self.action_id,
            rule_triggered=rule_triggered,
            reason=reason,
            t3_delta=t3_delta,
            v3_delta=v3_delta,
            contributing_factors=factors or [],
            timestamp=ts,
        )
        self.reputation = rep
        return rep

    # ── Hash Chain ──────────────────────────────────────────────

    def canonical_hash(self) -> str:
        """
        Compute canonical hash for chain linking and cross-language interop.

        Canonical form: sorted JSON of the action's essential fields.
        """
        canonical = {
            "action_id": self.action_id,
            "role": self.role.to_dict(),
            "request": self.request.to_dict(),
            "rules": self.rules.to_dict(),
            "resource": self.resource.to_dict(),
            "result": self.result.to_dict(),
            "prev_action_hash": self.prev_action_hash,
            "timestamp": self.timestamp,
        }
        if self.reputation:
            canonical["reputation"] = self.reputation.to_dict()
        raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    # ── Serialization ───────────────────────────────────────────

    def to_dict(self) -> Dict:
        """Serialize complete R7 action to dictionary."""
        d: Dict[str, Any] = {
            "action_id": self.action_id,
            "timestamp": self.timestamp,
            "prev_action_hash": self.prev_action_hash,
            "rules": self.rules.to_dict(),
            "role": self.role.to_dict(),
            "request": self.request.to_dict(),
            "reference": self.reference.to_dict(),
            "resource": self.resource.to_dict(),
            "result": self.result.to_dict(),
        }
        if self.reputation:
            d["reputation"] = self.reputation.to_dict()
        return d

    def to_jsonld(self) -> Dict[str, Any]:
        """
        Serialize to spec-compliant JSON-LD per r7-framework.md.

        Produces the canonical R7 Action document with:
        - @context header for JSON-LD processors
        - All 7 components (Rules/Role/Request/Reference/Resource/Result/Reputation)
        - Spec-compliant field naming matching the R7 framework spec
        - Reputation included when computed (first-class output)
        - Chain linking fields for audit trail
        """
        doc: Dict[str, Any] = {
            "@context": [R7_JSONLD_CONTEXT],
            "@type": "R7Action",
            "action_id": self.action_id,
            "timestamp": self.timestamp,
        }
        if self.prev_action_hash:
            doc["prev_action_hash"] = self.prev_action_hash

        # 1. Rules
        doc["rules"] = self.rules.to_dict()

        # 2. Role
        doc["role"] = self.role.to_dict()

        # 3. Request
        doc["request"] = self.request.to_dict()

        # 4. Reference — include only when populated
        ref_dict = self.reference.to_dict()
        if (self.reference.precedents or self.reference.witnesses
                or self.reference.relevant_entities):
            doc["reference"] = ref_dict
        else:
            doc["reference"] = ref_dict

        # 5. Resource
        doc["resource"] = self.resource.to_dict()

        # 6. Result
        doc["result"] = self.result.to_dict()

        # 7. Reputation — first-class output, included when computed
        if self.reputation:
            # Inline reputation without redundant @context
            rep = self.reputation.to_dict()
            doc["reputation"] = rep

        return doc

    def to_jsonld_string(self, indent: int = 2) -> str:
        """Serialize to spec-compliant JSON-LD string."""
        return json.dumps(self.to_jsonld(), indent=indent)

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> R7Action:
        """
        Deserialize from spec-compliant JSON-LD or dict representation.

        Handles both JSON-LD format (with @context/@type) and plain dict.
        Reconstructs all 7 components from nested structures.
        """
        # 1. Rules
        rules_data = doc.get("rules", {})
        constraints = [
            Constraint(constraint_type=c["type"], value=c["value"])
            for c in rules_data.get("constraints", [])
        ]
        rules = Rules(
            law_hash=rules_data.get("lawHash", ""),
            society=rules_data.get("society", ""),
            constraints=constraints,
            permissions=rules_data.get("permissions", []),
            prohibitions=rules_data.get("prohibitions", []),
        )

        # 2. Role
        role_data = doc.get("role", {})
        t3_in_role = None
        v3_in_role = None
        if "t3InRole" in role_data:
            t3d = role_data["t3InRole"]
            t3_in_role = T3(
                talent=t3d.get("talent", 0.5),
                training=t3d.get("training", 0.5),
                temperament=t3d.get("temperament", 0.5),
            )
        if "v3InRole" in role_data:
            v3d = role_data["v3InRole"]
            v3_in_role = V3(
                valuation=v3d.get("valuation", 0.5),
                veracity=v3d.get("veracity", 0.5),
                validity=v3d.get("validity", 0.5),
            )
        role = Role(
            actor=role_data.get("actor", ""),
            role_lct=role_data.get("roleLCT", ""),
            paired_at=role_data.get("pairedAt", ""),
            t3_in_role=t3_in_role,
            v3_in_role=v3_in_role,
        )

        # 3. Request
        req_data = doc.get("request", {})
        proof = None
        if "proofOfAgency" in req_data:
            pa = req_data["proofOfAgency"]
            proof = ProofOfAgency(
                grant_id=pa.get("grantId", ""),
                inclusion_proof=pa.get("inclusionProof", ""),
                scope=pa.get("scope", ""),
                audience=pa.get("audience", []),
            )
        request = Request(
            action=req_data.get("action", ""),
            target=req_data.get("target", ""),
            parameters=req_data.get("parameters", {}),
            atp_stake=req_data.get("atpStake", 0.0),
            nonce=req_data.get("nonce", ""),
            constraints=req_data.get("constraints", {}),
            proof_of_agency=proof,
        )

        # 4. Reference
        ref_data = doc.get("reference", {})
        precedents = [
            Precedent(
                action_hash=p.get("actionHash", ""),
                outcome=p.get("outcome", ""),
                relevance=p.get("relevance", 0.0),
            )
            for p in ref_data.get("precedents", [])
        ]
        mrh_ctx = ref_data.get("mrhContext", {})
        witnesses_ref = [
            WitnessAttestation(
                lct=w.get("lct", ""),
                attestation=w.get("attestation", "verified"),
                signature=w.get("signature", ""),
                timestamp=w.get("timestamp", ""),
            )
            for w in ref_data.get("witnesses", [])
        ]
        reference = Reference(
            precedents=precedents,
            mrh_depth=mrh_ctx.get("depth", 0),
            relevant_entities=mrh_ctx.get("relevantEntities", []),
            witnesses=witnesses_ref,
        )

        # 5. Resource
        res_data = doc.get("resource", {})
        req_res = res_data.get("required", {})
        avail_res = res_data.get("available", {})
        escrow_data = res_data.get("escrow", {})
        resource = ResourceRequirements(
            required_atp=req_res.get("atp", 0.0),
            available_atp=avail_res.get("atp_balance", 0.0),
            compute=req_res.get("compute", {}),
            escrow_amount=escrow_data.get("amount", 0.0),
            escrow_condition=escrow_data.get("release_condition", "result_verified"),
        )

        # 6. Result
        result_data = doc.get("result", {})
        result_attestations = [
            WitnessAttestation(
                lct=a.get("lct", ""),
                attestation=a.get("attestation", "verified"),
                signature=a.get("signature", ""),
                timestamp=a.get("timestamp", ""),
            )
            for a in result_data.get("attestations", [])
        ]
        result = Result(
            status=ActionStatus(result_data.get("status", "pending")),
            output=result_data.get("output", {}),
            output_hash=result_data.get("output", {}).get("hash", ""),
            error=result_data.get("error", {}).get("message") if isinstance(result_data.get("error"), dict) else result_data.get("error"),
            atp_consumed=result_data.get("resourceConsumed", {}).get("atp", 0.0),
            attestations=result_attestations,
        )

        # 7. Reputation (optional)
        reputation = None
        if "reputation" in doc:
            reputation = ReputationDelta.from_jsonld(doc["reputation"])

        action = cls.__new__(cls)
        action.rules = rules
        action.role = role
        action.request = request
        action.reference = reference
        action.resource = resource
        action.result = result
        action.reputation = reputation
        action.action_id = doc.get("action_id", "")
        action.prev_action_hash = doc.get("prev_action_hash", "")
        action.timestamp = doc.get("timestamp", "")
        return action

    @classmethod
    def from_jsonld_string(cls, s: str) -> R7Action:
        """Deserialize from spec-compliant JSON-LD string."""
        return cls.from_jsonld(json.loads(s))


# ── Action Chain ────────────────────────────────────────────────

class ActionChain:
    """
    An ordered chain of R7 actions linked by hash.

    Each action references the previous action's canonical hash,
    creating a tamper-evident audit trail.
    """

    def __init__(self):
        self._actions: List[R7Action] = []

    def append(self, action: R7Action) -> R7Action:
        """
        Append an action to the chain, linking it to the previous action.

        Returns the action with prev_action_hash set.
        """
        if self._actions:
            action.prev_action_hash = self._actions[-1].canonical_hash()
        self._actions.append(action)
        return action

    @property
    def length(self) -> int:
        """Number of actions in the chain."""
        return len(self._actions)

    @property
    def actions(self) -> List[R7Action]:
        """Copy of all actions in chain order."""
        return list(self._actions)

    @property
    def head(self) -> Optional[R7Action]:
        """Most recent action in the chain, or None if empty."""
        return self._actions[-1] if self._actions else None

    def verify_chain(self) -> bool:
        """Verify the integrity of the hash chain. Returns True if valid."""
        if len(self._actions) <= 1:
            return True
        for i in range(1, len(self._actions)):
            expected = self._actions[i - 1].canonical_hash()
            if self._actions[i].prev_action_hash != expected:
                return False
        return True

    def to_dict(self) -> Dict:
        """Serialize chain to dict with all actions and chain validity status."""
        return {
            "length": self.length,
            "actions": [a.to_dict() for a in self._actions],
            "chain_valid": self.verify_chain(),
        }

    def to_jsonld(self) -> Dict[str, Any]:
        """
        Serialize to spec-compliant JSON-LD.

        Produces an ActionChain document with all actions as JSON-LD,
        chain validity status, and hash linking preserved.
        """
        return {
            "@context": [R7_JSONLD_CONTEXT],
            "@type": "ActionChain",
            "length": self.length,
            "actions": [a.to_jsonld() for a in self._actions],
            "chain_valid": self.verify_chain(),
        }

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> ActionChain:
        """
        Deserialize from JSON-LD or dict representation.

        Reconstructs the chain from serialized actions. Does NOT
        recompute prev_action_hash links — preserves them as-is
        for chain integrity verification.
        """
        chain = cls()
        for action_doc in doc.get("actions", []):
            action = R7Action.from_jsonld(action_doc)
            chain._actions.append(action)
        return chain


# ── Builder (convenience) ──────────────────────────────────────

def build_action(
    actor: str,
    role_lct: str,
    action: str,
    target: str = "",
    *,
    t3: Optional[T3] = None,
    v3: Optional[V3] = None,
    atp_stake: float = 0.0,
    available_atp: float = 0.0,
    permissions: Optional[List[str]] = None,
    society: str = "",
    law_hash: str = "",
    nonce: str = "",
    parameters: Optional[Dict[str, Any]] = None,
) -> R7Action:
    """
    Convenience builder for common R7 actions.

    Creates a complete R7Action with sensible defaults. Useful for
    constructing actions programmatically without manually assembling
    all 7 components.
    """
    ts = datetime.now(timezone.utc).isoformat()

    rules = Rules(
        law_hash=law_hash,
        society=society,
        permissions=permissions or [],
    )

    role = Role(
        actor=actor,
        role_lct=role_lct,
        paired_at=ts,
        t3_in_role=t3,
        v3_in_role=v3,
    )

    req = Request(
        action=action,
        target=target,
        atp_stake=atp_stake,
        nonce=nonce or hashlib.sha256(f"{actor}:{action}:{ts}".encode()).hexdigest()[:8],
        parameters=parameters or {},
    )

    resource = ResourceRequirements(
        required_atp=atp_stake,
        available_atp=available_atp,
    )

    return R7Action(
        rules=rules,
        role=role,
        request=req,
        resource=resource,
        timestamp=ts,
    )
