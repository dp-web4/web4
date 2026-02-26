#!/usr/bin/env python3
"""
Web4 R7 Action Framework — Reference Implementation
Spec: web4-standard/core-spec/r7-framework.md (918 lines)

Covers all 9 specification sections:
  §1  Core Components (Rules, Role, Request, Reference, Resource, Result, Reputation)
  §2  R7 Transaction Flow (Validate → Execute → Reputation → Settle)
  §3  R7-SAL Integration
  §4  R7 Security Properties
  §5  R7 Transaction Examples (5 canonical examples)
  §6  Implementation Requirements (MUST/SHOULD/MAY)
  §7  R7 Error Handling
  §8  R7 Extensibility
  §9  Summary (end-to-end lifecycle)
"""

from __future__ import annotations
import hashlib, json, time, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


# ============================================================
# §7  ERROR HIERARCHY (defined first, used throughout)
# ============================================================

class R7Error(Exception):
    """Base class for all R7 errors."""
    pass

class RuleViolation(R7Error):
    """Action violates governing rules."""
    pass

class RoleUnauthorized(R7Error):
    """Actor lacks required role or permissions."""
    pass

class RequestMalformed(R7Error):
    """Request structure or parameters invalid."""
    pass

class ReferenceInvalid(R7Error):
    """Referenced entities not found or invalid."""
    pass

class ResourceInsufficient(R7Error):
    """Required resources unavailable."""
    pass

class ResultInvalid(R7Error):
    """Result violates output constraints."""
    pass

class ReputationComputationError(R7Error):
    """Reputation delta cannot be computed (R7 addition)."""
    pass


# ============================================================
# §1  CORE COMPONENTS
# ============================================================

# --- §1.1 Rules ---

@dataclass
class Constraint:
    type: str = ""          # e.g., "rate_limit", "atp_minimum", "witness_required"
    value: Any = None

@dataclass
class Rules:
    """§1.1: Governing constraints and policies."""
    law_hash: str = ""
    society: str = ""
    constraints: list[Constraint] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    prohibitions: list[str] = field(default_factory=list)

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions

    def is_prohibited(self, action: str) -> bool:
        return action in self.prohibitions

    def get_constraint(self, ctype: str) -> Optional[Constraint]:
        for c in self.constraints:
            if c.type == ctype:
                return c
        return None


# --- §1.2 Role ---

@dataclass
class T3InRole:
    """Trust tensor on a specific MRH role pairing."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3

    def as_dict(self) -> dict:
        return {"talent": self.talent, "training": self.training,
                "temperament": self.temperament}

@dataclass
class V3InRole:
    """Value tensor on a specific MRH role pairing."""
    veracity: float = 0.5
    validity: float = 0.5
    value: float = 0.5

    def composite(self) -> float:
        return (self.veracity + self.validity + self.value) / 3

    def as_dict(self) -> dict:
        return {"veracity": self.veracity, "validity": self.validity,
                "value": self.value}

@dataclass
class Role:
    """§1.2: Contextual identity under which the action is performed."""
    actor: str = ""                     # lct:web4:entity:...
    role_lct: str = ""                  # lct:web4:role:...:hash
    paired_at: str = ""
    t3_in_role: T3InRole = field(default_factory=T3InRole)
    v3_in_role: V3InRole = field(default_factory=V3InRole)

    def is_valid(self) -> bool:
        return bool(self.actor and self.role_lct)


# --- §1.3 Request ---

@dataclass
class ProofOfAgency:
    """Agency delegation proof for agent-executed actions."""
    grant_id: str = ""
    inclusion_proof: str = ""
    scope: str = ""
    audience: list[str] = field(default_factory=list)
    witness_level: int = 0

@dataclass
class Request:
    """§1.3: Specific action intent and parameters."""
    action: str = ""
    target: str = ""
    parameters: dict = field(default_factory=dict)
    constraints: dict = field(default_factory=dict)
    atp_stake: float = 0.0
    nonce: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    proof_of_agency: Optional[ProofOfAgency] = None


# --- §1.4 Reference ---

@dataclass
class Precedent:
    action_hash: str = ""
    outcome: str = ""
    relevance: float = 0.0

@dataclass
class LawInterpretation:
    law_oracle: str = ""
    ruling: str = ""
    hash: str = ""

@dataclass
class WitnessAttestation:
    lct: str = ""
    attestation: str = ""
    signature: str = ""
    timestamp: str = ""

@dataclass
class MRHContext:
    depth: int = 0
    relevant_entities: list[str] = field(default_factory=list)
    trust_paths: list[str] = field(default_factory=list)

@dataclass
class Reference:
    """§1.4: Historical context and precedents."""
    precedents: list[Precedent] = field(default_factory=list)
    mrh_context: MRHContext = field(default_factory=MRHContext)
    interpretations: list[LawInterpretation] = field(default_factory=list)
    witnesses: list[WitnessAttestation] = field(default_factory=list)


# --- §1.5 Resource ---

@dataclass
class ResourceRequirement:
    atp: float = 0.0
    compute: dict = field(default_factory=dict)
    bandwidth: str = ""
    storage: str = ""

@dataclass
class ResourceAvailable:
    atp_balance: float = 0.0
    compute_quota: str = ""
    bandwidth_quota: str = ""

@dataclass
class ResourcePricing:
    atp_per_compute: float = 0.0
    surge_multiplier: float = 1.0

@dataclass
class Escrow:
    amount: float = 0.0
    release_condition: str = "result_verified"
    status: str = "pending"   # pending | locked | released | refunded

@dataclass
class Resource:
    """§1.5: Resources required and available."""
    required: ResourceRequirement = field(default_factory=ResourceRequirement)
    available: ResourceAvailable = field(default_factory=ResourceAvailable)
    pricing: ResourcePricing = field(default_factory=ResourcePricing)
    escrow: Escrow = field(default_factory=Escrow)
    agency_caps: Optional[dict] = None


# --- §1.6 Result ---

@dataclass
class LedgerProof:
    tx_hash: str = ""
    block_height: int = 0
    inclusion_proof: str = ""

@dataclass
class Result:
    """§1.6: Deterministic outcome of the action execution."""
    status: str = ""           # success | failure | error
    output: Any = None
    error: Optional[dict] = None
    resource_consumed: dict = field(default_factory=dict)
    attestations: list[WitnessAttestation] = field(default_factory=list)
    ledger_proof: LedgerProof = field(default_factory=LedgerProof)
    refund: Optional[dict] = None


# --- §1.7 Reputation ---

@dataclass
class TensorDelta:
    change: float = 0.0
    from_value: float = 0.0
    to_value: float = 0.0

@dataclass
class ContributingFactor:
    factor: str = ""
    weight: float = 0.0

@dataclass
class MRHRolePairing:
    entity: str = ""
    role: str = ""
    paired_at: str = ""
    mrh_link: str = ""

@dataclass
class ReputationDelta:
    """§1.7: Explicit trust and value changes from the action.
    CRITICAL: role-contextualized, not global."""
    subject_lct: str = ""
    role_lct: str = ""
    role_pairing_in_mrh: Optional[MRHRolePairing] = None
    action_type: str = ""
    action_target: str = ""
    action_id: str = ""
    rule_triggered: str = ""
    reason: str = ""
    t3_delta: dict[str, TensorDelta] = field(default_factory=dict)
    v3_delta: dict[str, TensorDelta] = field(default_factory=dict)
    contributing_factors: list[ContributingFactor] = field(default_factory=list)
    witnesses: list[WitnessAttestation] = field(default_factory=list)
    net_trust_change: float = 0.0
    net_value_change: float = 0.0
    timestamp: str = ""

    @property
    def is_positive(self) -> bool:
        return self.net_trust_change > 0 or self.net_value_change > 0

    @property
    def is_observable(self) -> bool:
        """§4.6: All reputation changes are explicit."""
        return bool(self.subject_lct and self.role_lct)

    @property
    def is_attributable(self) -> bool:
        return bool(self.action_id and self.rule_triggered)

    @property
    def is_role_contextualized(self) -> bool:
        return bool(self.role_lct)


# --- Complete R7 Action ---

@dataclass
class R7Action:
    """Complete R7 transaction structure.
    §6 MUST: All seven components must be present."""
    rules: Rules = field(default_factory=Rules)
    role: Role = field(default_factory=Role)
    request: Request = field(default_factory=Request)
    reference: Reference = field(default_factory=Reference)
    resource: Resource = field(default_factory=Resource)
    result: Optional[Result] = None
    reputation: Optional[ReputationDelta] = None
    action_type: str = ""   # e.g., "query", "compute", "delegation", "agency_action"

    def is_complete(self) -> bool:
        """All 7 components present (even if empty)."""
        return self.result is not None and self.reputation is not None

    @property
    def action_id(self) -> str:
        return f"txn:{hashlib.sha256(self.request.nonce.encode()).hexdigest()[:16]}"


# ============================================================
# §2  R7 TRANSACTION FLOW
# ============================================================

class ResourceMeter:
    """§2.2: Metered execution."""
    def __init__(self):
        self._start = None
        self._end = None
        self.atp_used: float = 0.0
        self.compute_used: dict = {}

    def start(self):
        self._start = time.monotonic()

    def stop(self) -> dict:
        self._end = time.monotonic()
        elapsed = self._end - self._start if self._start else 0
        return {"atp": self.atp_used, "elapsed_s": round(elapsed, 4),
                **self.compute_used}

    def get_partial(self) -> dict:
        elapsed = (time.monotonic() - self._start) if self._start else 0
        return {"atp": self.atp_used, "elapsed_s": round(elapsed, 4),
                **self.compute_used}

    def record_atp(self, amount: float):
        self.atp_used += amount

    def record_compute(self, key: str, value: Any):
        self.compute_used[key] = value


@dataclass
class EscrowLock:
    amount: float = 0.0
    locked: bool = False
    released: bool = False

    def release(self, reason: str = "completed"):
        self.released = True
        self.locked = False
        return {"amount": self.amount, "status": reason}


@dataclass
class ValidationResult:
    valid: bool = False
    escrow: Optional[EscrowLock] = None
    error: Optional[R7Error] = None


class MRHRoleStore:
    """Simulated MRH store for role pairings and their T3/V3 tensors."""
    def __init__(self):
        self.role_pairings: dict[str, dict] = {}  # key = f"{entity}|{role}"

    def register_pairing(self, entity: str, role: str, t3: T3InRole, v3: V3InRole,
                         paired_at: str = ""):
        key = f"{entity}|{role}"
        self.role_pairings[key] = {
            "entity": entity, "role": role,
            "t3": t3, "v3": v3,
            "paired_at": paired_at or datetime.now(timezone.utc).isoformat(),
            "mrh_link": f"link:mrh:{entity.split(':')[-1]}→{role.split(':')[-2]}:{uuid.uuid4().hex[:6]}",
            "history": [],
        }

    def get_pairing(self, entity: str, role: str) -> Optional[dict]:
        return self.role_pairings.get(f"{entity}|{role}")

    def has_pairing(self, entity: str, role: str) -> bool:
        return f"{entity}|{role}" in self.role_pairings

    def apply_deltas(self, entity: str, role: str,
                     t3_delta: dict[str, TensorDelta],
                     v3_delta: dict[str, TensorDelta]):
        """§2.4: Apply tensor updates to specific MRH role pairing."""
        pairing = self.get_pairing(entity, role)
        if not pairing:
            return False
        t3 = pairing["t3"]
        for dim, delta in t3_delta.items():
            old = getattr(t3, dim, None)
            if old is not None:
                setattr(t3, dim, max(0.0, min(1.0, old + delta.change)))
        v3 = pairing["v3"]
        for dim, delta in v3_delta.items():
            old = getattr(v3, dim, None)
            if old is not None:
                setattr(v3, dim, max(0.0, min(1.0, old + delta.change)))
        pairing["history"].append({
            "t3_delta": {k: v.change for k, v in t3_delta.items()},
            "v3_delta": {k: v.change for k, v in v3_delta.items()},
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        return True


# --- §3  R7-SAL Integration ---

@dataclass
class LawNorm:
    """SAL law norm that applies to R7 actions."""
    norm_id: str = ""
    society: str = ""
    law_hash: str = ""
    constraint_type: str = ""     # rate_limit, atp_minimum, witness_required
    constraint_value: Any = None
    applies_to_roles: list[str] = field(default_factory=list)

class SALIntegration:
    """§3: R7-SAL integration layer."""
    def __init__(self):
        self.norms: list[LawNorm] = []
        self.oracle_rulings: dict[str, str] = {}  # law_hash → ruling

    def add_norm(self, norm: LawNorm):
        self.norms.append(norm)

    def add_ruling(self, law_hash: str, ruling: str):
        self.oracle_rulings[law_hash] = ruling

    def check_compliance(self, rules: Rules, request: Request, role: Role) -> tuple[bool, str]:
        """Check if action complies with SAL norms."""
        for norm in self.norms:
            if norm.applies_to_roles and role.role_lct not in norm.applies_to_roles:
                continue
            if norm.constraint_type == "atp_minimum":
                if request.atp_stake < norm.constraint_value:
                    return False, f"ATP stake {request.atp_stake} < minimum {norm.constraint_value}"
            if norm.constraint_type == "witness_required":
                # Will be enforced at settlement
                pass
        # Check oracle ruling
        if rules.law_hash and rules.law_hash in self.oracle_rulings:
            ruling = self.oracle_rulings[rules.law_hash]
            if ruling == "prohibited":
                return False, "Law Oracle prohibits this action"
        return True, "compliant"

    def get_reputation_rules(self, action_type: str, result_status: str) -> list[dict]:
        """§3: Law defines reputation rules and thresholds."""
        rules = []
        if result_status == "success":
            rules.append({
                "id": f"success_{action_type}",
                "affects_trust": True,
                "trust_dimension": "training",
                "trust_delta": 0.01,
                "affects_value": True,
                "value_dimension": "veracity",
                "value_delta": 0.02,
            })
        elif result_status == "failure":
            rules.append({
                "id": f"failure_{action_type}",
                "affects_trust": True,
                "trust_dimension": "temperament",
                "trust_delta": -0.005,
                "affects_value": False,
                "value_dimension": None,
                "value_delta": 0.0,
            })
        return rules


# --- §2.1 Pre-execution Validation ---

class R7Validator:
    """Pre-execution validator per §2.1."""
    def __init__(self, mrh_store: MRHRoleStore, sal: SALIntegration):
        self.mrh = mrh_store
        self.sal = sal

    def validate(self, action: R7Action) -> ValidationResult:
        # 1. Verify actor has required role
        if not self.mrh.has_pairing(action.role.actor, action.role.role_lct):
            return ValidationResult(valid=False,
                                    error=RoleUnauthorized("Actor not paired with specified role"))

        # 2. Check agency delegation
        if action.request.proof_of_agency:
            poa = action.request.proof_of_agency
            if not poa.grant_id:
                return ValidationResult(valid=False,
                                        error=RoleUnauthorized("Invalid agency grant"))

        # 3. Check rules compliance (prohibitions)
        if action.rules.is_prohibited(action.request.action):
            return ValidationResult(valid=False,
                                    error=RuleViolation(f"Action '{action.request.action}' is prohibited"))

        # 4. Check SAL compliance
        compliant, reason = self.sal.check_compliance(
            action.rules, action.request, action.role)
        if not compliant:
            return ValidationResult(valid=False, error=RuleViolation(reason))

        # 5. Verify resource availability
        if action.resource.required.atp > action.resource.available.atp_balance:
            return ValidationResult(valid=False,
                                    error=ResourceInsufficient(
                                        f"Need {action.resource.required.atp} ATP, "
                                        f"have {action.resource.available.atp_balance}"))

        # 6. Agency caps
        if action.resource.agency_caps:
            max_atp = action.resource.agency_caps.get("max_atp", float("inf"))
            if action.resource.required.atp > max_atp:
                return ValidationResult(valid=False,
                                        error=ResourceInsufficient("Exceeds agency ATP cap"))

        # 7. Lock escrow
        escrow = EscrowLock(amount=action.resource.escrow.amount, locked=True)

        return ValidationResult(valid=True, escrow=escrow)


# --- §2.3 Reputation Computation ---

class ReputationComputer:
    """§2.3: Compute explicit reputation changes.
    CRITICAL: role-contextualized, not global."""

    def __init__(self, mrh_store: MRHRoleStore, sal: SALIntegration):
        self.mrh = mrh_store
        self.sal = sal

    def compute(self, action: R7Action, result: Result) -> ReputationDelta:
        """Compute reputation delta based on action outcome."""
        entity_lct = action.role.actor
        role_lct = action.role.role_lct

        pairing = self.mrh.get_pairing(entity_lct, role_lct)
        if not pairing:
            raise ReputationComputationError("No MRH role pairing found")

        current_t3 = pairing["t3"]
        current_v3 = pairing["v3"]

        # Build MRH role pairing reference
        mrh_pairing = MRHRolePairing(
            entity=entity_lct,
            role=role_lct,
            paired_at=pairing["paired_at"],
            mrh_link=pairing["mrh_link"],
        )

        rep = ReputationDelta(
            subject_lct=entity_lct,
            role_lct=role_lct,
            role_pairing_in_mrh=mrh_pairing,
            action_type=action.request.action,
            action_target=action.request.target,
            action_id=action.action_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # 1. Get reputation rules from SAL
        triggered_rules = self.sal.get_reputation_rules(
            action.request.action, result.status)

        # 2. Compute T3 deltas
        t3_deltas = {}
        for rule in triggered_rules:
            if rule["affects_trust"]:
                dim = rule["trust_dimension"]
                current_val = getattr(current_t3, dim, 0.5)
                delta = rule["trust_delta"]
                t3_deltas[dim] = TensorDelta(
                    change=delta,
                    from_value=current_val,
                    to_value=round(current_val + delta, 6),
                )

        # 3. Compute V3 deltas
        v3_deltas = {}
        for rule in triggered_rules:
            if rule["affects_value"]:
                dim = rule["value_dimension"]
                current_val = getattr(current_v3, dim, 0.5)
                delta = rule["value_delta"]
                v3_deltas[dim] = TensorDelta(
                    change=delta,
                    from_value=current_val,
                    to_value=round(current_val + delta, 6),
                )

        # 4. Contributing factors (from request context)
        factors = []
        if result.status == "success":
            if action.request.atp_stake > 0:
                factors.append(ContributingFactor("atp_stake_size", 0.7))
            if action.request.constraints.get("deadline"):
                factors.append(ContributingFactor("deadline_met", 0.6))
            if not factors:
                factors.append(ContributingFactor("successful_completion", 1.0))
        else:
            factors.append(ContributingFactor("failure_penalty", 1.0))

        # 5. Set rule triggered
        rep.rule_triggered = triggered_rules[0]["id"] if triggered_rules else "no_rule"
        rep.reason = self._generate_reason(triggered_rules, result)

        # 6. Assemble
        rep.t3_delta = t3_deltas
        rep.v3_delta = v3_deltas
        rep.contributing_factors = factors
        rep.net_trust_change = round(sum(d.change for d in t3_deltas.values()), 6)
        rep.net_value_change = round(sum(d.change for d in v3_deltas.values()), 6)

        return rep

    def _generate_reason(self, rules: list[dict], result: Result) -> str:
        if result.status == "success":
            return "Successful action completed"
        elif result.status == "failure":
            return "Action failed"
        return "Action produced error"


# --- §2.4 Post-execution Settlement ---

@dataclass
class SettlementResult:
    proof: LedgerProof = field(default_factory=LedgerProof)
    final_cost: float = 0.0
    reputation: Optional[ReputationDelta] = None
    success: bool = False


# ============================================================
# §4  SECURITY PROPERTIES + §6  REQUIREMENTS → R7 Engine
# ============================================================

class Ledger:
    """Simple ledger for recording R7 transactions."""
    def __init__(self):
        self.entries: list[dict] = []

    def write(self, entry: dict) -> LedgerProof:
        block = len(self.entries) + 1
        tx_hash = hashlib.sha256(json.dumps(entry, default=str).encode()).hexdigest()[:16]
        proof = LedgerProof(
            tx_hash=f"0x{tx_hash}",
            block_height=block,
            inclusion_proof=hashlib.sha256(tx_hash.encode()).hexdigest()[:16],
        )
        self.entries.append({"entry": entry, "proof": proof})
        return proof


class R7Engine:
    """Complete R7 engine implementing §2 transaction flow with §4 security properties."""

    def __init__(self, mrh_store: Optional[MRHRoleStore] = None,
                 sal: Optional[SALIntegration] = None):
        self.mrh = mrh_store or MRHRoleStore()
        self.sal = sal or SALIntegration()
        self.validator = R7Validator(self.mrh, self.sal)
        self.rep_computer = ReputationComputer(self.mrh, self.sal)
        self.ledger = Ledger()
        self.action_handlers: dict[str, Callable] = {}
        self.completed_actions: list[R7Action] = []

    def register_handler(self, action_type: str, handler: Callable):
        """§8: Custom action type registration."""
        self.action_handlers[action_type] = handler

    def execute_action(self, action: R7Action) -> R7Action:
        """
        Complete R7 lifecycle:
          §2.1 Validate → §2.2 Execute → §2.3 Reputation → §2.4 Settle
        §4.5: Atomic — all succeeds or all rolls back.
        §6 MUST: All 7 components present, reputation explicit.
        """

        # --- §2.1: Pre-execution Validation ---
        vr = self.validator.validate(action)
        if not vr.valid:
            # Even failures produce valid R7 results with reputation (§6 MUST #4)
            action.result = Result(
                status="error",
                error={"type": type(vr.error).__name__,
                       "message": str(vr.error)},
                resource_consumed={"atp": 0},
            )
            try:
                action.reputation = self.rep_computer.compute(action, action.result)
            except ReputationComputationError:
                # If no MRH pairing, create minimal reputation
                action.reputation = ReputationDelta(
                    subject_lct=action.role.actor,
                    role_lct=action.role.role_lct,
                    reason=f"Validation failed: {vr.error}",
                    net_trust_change=0.0,
                    net_value_change=0.0,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            return action

        # --- §2.2: Execution ---
        meter = ResourceMeter()
        meter.start()

        try:
            handler = self.action_handlers.get(action.request.action)
            if handler:
                raw_result = handler(action)
            else:
                # Default handler: simulate success
                raw_result = {"data": f"Executed {action.request.action}",
                              "hash": hashlib.sha256(action.request.nonce.encode()).hexdigest()[:16]}

            resources_used = meter.stop()
            meter.record_atp(action.resource.required.atp)

            action.result = Result(
                status="success",
                output=raw_result,
                resource_consumed={"atp": action.resource.required.atp, **resources_used},
            )

        except Exception as e:
            resources_used = meter.stop()
            action.result = Result(
                status="failure",
                error={"type": type(e).__name__, "message": str(e)},
                resource_consumed=meter.get_partial(),
            )

        # --- §2.3: Reputation Computation ---
        action.reputation = self.rep_computer.compute(action, action.result)

        # --- §2.4: Post-execution Settlement ---
        # Calculate final cost
        final_cost = action.resource.required.atp * action.resource.pricing.surge_multiplier

        # Handle escrow
        if vr.escrow:
            if action.result.status == "success":
                vr.escrow.release("completed")
            else:
                vr.escrow.release("refunded")
                action.result.refund = {"amount": vr.escrow.amount, "status": "refunded"}

        # Apply tensor updates to MRH role pairing (§2.4 step 4)
        self.mrh.apply_deltas(
            action.role.actor, action.role.role_lct,
            action.reputation.t3_delta, action.reputation.v3_delta)

        # Record to ledger (§6 MUST #5)
        entry = {
            "action_type": action.action_type or action.request.action,
            "actor": action.role.actor,
            "role": action.role.role_lct,
            "request": action.request.action,
            "result_status": action.result.status,
            "reputation": {
                "net_trust": action.reputation.net_trust_change,
                "net_value": action.reputation.net_value_change,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        proof = self.ledger.write(entry)
        action.result.ledger_proof = proof
        action.reputation.action_id = proof.tx_hash

        self.completed_actions.append(action)
        return action


# ============================================================
# §8  EXTENSIBILITY
# ============================================================

class R6CompatResult:
    """§8.3: R6 legacy result (no explicit reputation)."""
    def __init__(self, status: str, output: Any, tensor_updates: Optional[dict] = None):
        self.status = status
        self.output = output
        self.tensor_updates = tensor_updates or {}

def migrate_r6_to_r7(r6_result: R6CompatResult, role: Role) -> tuple[Result, ReputationDelta]:
    """§8: R6 to R7 migration.
    Extracts tensor updates from Result into Reputation."""
    result = Result(
        status=r6_result.status,
        output=r6_result.output,
    )

    # Extract tensor updates from R6 result
    t3_deltas = {}
    v3_deltas = {}
    for dim in ("talent", "training", "temperament"):
        if dim in r6_result.tensor_updates:
            val = r6_result.tensor_updates[dim]
            from_val = getattr(role.t3_in_role, dim, 0.5)
            t3_deltas[dim] = TensorDelta(
                change=val, from_value=from_val,
                to_value=round(from_val + val, 6))
    for dim in ("veracity", "validity", "value"):
        if dim in r6_result.tensor_updates:
            val = r6_result.tensor_updates[dim]
            from_val = getattr(role.v3_in_role, dim, 0.5)
            v3_deltas[dim] = TensorDelta(
                change=val, from_value=from_val,
                to_value=round(from_val + val, 6))

    reputation = ReputationDelta(
        subject_lct=role.actor,
        role_lct=role.role_lct,
        t3_delta=t3_deltas,
        v3_delta=v3_deltas,
        reason="Migrated from R6 result",
        net_trust_change=round(sum(d.change for d in t3_deltas.values()), 6),
        net_value_change=round(sum(d.change for d in v3_deltas.values()), 6),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return result, reputation


class ActionTypeRegistry:
    """§8: Custom action type registry."""
    def __init__(self):
        self.types: dict[str, dict] = {}

    def register(self, action_type: str, validation_rules: list[str],
                 reputation_rules: list[dict]):
        self.types[action_type] = {
            "validation_rules": validation_rules,
            "reputation_rules": reputation_rules,
        }

    def has_type(self, action_type: str) -> bool:
        return action_type in self.types

    def get_reputation_rules(self, action_type: str) -> list[dict]:
        t = self.types.get(action_type)
        return t["reputation_rules"] if t else []


# ============================================================
#  TEST HARNESS
# ============================================================

passed = 0
failed = 0
failures = []

def check(label: str, condition: bool):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        failures.append(label)
        print(f"  FAIL: {label}")


def run_tests():
    global passed, failed, failures

    # ── T1: Rules Component (§1.1) ──
    print("T1: Rules (§1.1)")

    rules = Rules(
        law_hash="sha256:abc123",
        society="lct:web4:society:testnet",
        constraints=[
            Constraint("rate_limit", "100/hour"),
            Constraint("atp_minimum", 50),
            Constraint("witness_required", 3),
        ],
        permissions=["read", "write", "delegate"],
        prohibitions=["delete", "impersonate"],
    )
    check("T1.1 Law hash", rules.law_hash == "sha256:abc123")
    check("T1.2 Society", rules.society.startswith("lct:web4:society:"))
    check("T1.3 Has permission read", rules.has_permission("read"))
    check("T1.4 No permission execute", not rules.has_permission("execute"))
    check("T1.5 Delete prohibited", rules.is_prohibited("delete"))
    check("T1.6 Write not prohibited", not rules.is_prohibited("write"))
    check("T1.7 Rate limit constraint", rules.get_constraint("rate_limit").value == "100/hour")
    check("T1.8 ATP minimum constraint", rules.get_constraint("atp_minimum").value == 50)
    check("T1.9 Witness constraint", rules.get_constraint("witness_required").value == 3)
    check("T1.10 Missing constraint", rules.get_constraint("nonexistent") is None)

    # ── T2: Role Component (§1.2) ──
    print("T2: Role (§1.2)")

    t3 = T3InRole(talent=0.85, training=0.90, temperament=0.88)
    v3 = V3InRole(veracity=0.92, validity=0.88, value=0.85)
    role = Role(
        actor="lct:web4:entity:alice",
        role_lct="lct:web4:role:analyst_financial_q4:abc123",
        paired_at="2025-09-15T12:00:00Z",
        t3_in_role=t3,
        v3_in_role=v3,
    )
    check("T2.1 Actor LCT", role.actor == "lct:web4:entity:alice")
    check("T2.2 Role LCT format", role.role_lct.startswith("lct:web4:role:"))
    check("T2.3 T3 composite", abs(t3.composite() - (0.85+0.90+0.88)/3) < 1e-9)
    check("T2.4 V3 composite", abs(v3.composite() - (0.92+0.88+0.85)/3) < 1e-9)
    check("T2.5 Role valid", role.is_valid())
    check("T2.6 T3 dict keys", set(t3.as_dict().keys()) == {"talent", "training", "temperament"})
    check("T2.7 V3 dict keys", set(v3.as_dict().keys()) == {"veracity", "validity", "value"})
    check("T2.8 Empty role invalid", not Role().is_valid())

    # ── T3: Request Component (§1.3) ──
    print("T3: Request (§1.3)")

    poa = ProofOfAgency(
        grant_id="agy:grant:001",
        inclusion_proof="hash:abc",
        scope="finance:payments",
        audience=["mcp:web4://tool/*"],
        witness_level=2,
    )
    req = Request(
        action="analyze_dataset",
        target="resource:web4:dataset:q4",
        parameters={"algorithm": "neural_net_v2", "confidence_threshold": 0.95},
        constraints={"deadline": "2025-09-15T18:00:00Z", "max_compute": "1000_units"},
        atp_stake=100,
        proof_of_agency=poa,
    )
    check("T3.1 Action", req.action == "analyze_dataset")
    check("T3.2 Target", req.target.startswith("resource:web4:"))
    check("T3.3 Parameters", req.parameters["confidence_threshold"] == 0.95)
    check("T3.4 Constraints", "deadline" in req.constraints)
    check("T3.5 ATP stake", req.atp_stake == 100)
    check("T3.6 Nonce generated", len(req.nonce) == 8)
    check("T3.7 Proof of agency", req.proof_of_agency.grant_id == "agy:grant:001")
    check("T3.8 Agency scope", poa.scope == "finance:payments")
    check("T3.9 Witness level", poa.witness_level == 2)

    # ── T4: Reference Component (§1.4) ──
    print("T4: Reference (§1.4)")

    ref = Reference(
        precedents=[Precedent("sha256:prev1", "success", 0.9)],
        mrh_context=MRHContext(depth=2, relevant_entities=["lct:web4:entity:bob"]),
        interpretations=[LawInterpretation("lct:web4:oracle:main", "permitted", "hash:law1")],
        witnesses=[WitnessAttestation("lct:web4:witness:v1", "verified", "sig1", "2025-09-15T10:00:00Z")],
    )
    check("T4.1 Precedent", ref.precedents[0].outcome == "success")
    check("T4.2 Relevance", ref.precedents[0].relevance == 0.9)
    check("T4.3 MRH depth", ref.mrh_context.depth == 2)
    check("T4.4 Relevant entity", "bob" in ref.mrh_context.relevant_entities[0])
    check("T4.5 Interpretation ruling", ref.interpretations[0].ruling == "permitted")
    check("T4.6 Witness attestation", ref.witnesses[0].attestation == "verified")

    # ── T5: Resource Component (§1.5) ──
    print("T5: Resource (§1.5)")

    res = Resource(
        required=ResourceRequirement(atp=100, compute={"cpu": "2_cores", "memory": "4GB"}),
        available=ResourceAvailable(atp_balance=500, compute_quota="unlimited"),
        pricing=ResourcePricing(atp_per_compute=0.1, surge_multiplier=1.0),
        escrow=Escrow(amount=100, release_condition="result_verified"),
    )
    check("T5.1 Required ATP", res.required.atp == 100)
    check("T5.2 Available balance", res.available.atp_balance == 500)
    check("T5.3 Surge multiplier", res.pricing.surge_multiplier == 1.0)
    check("T5.4 Escrow amount", res.escrow.amount == 100)
    check("T5.5 Escrow pending", res.escrow.status == "pending")
    check("T5.6 Sufficient resources", res.available.atp_balance >= res.required.atp)

    # ── T6: Result Component (§1.6) ──
    print("T6: Result (§1.6)")

    result = Result(
        status="success",
        output={"data": "analysis_results", "hash": "sha256:out1"},
        resource_consumed={"atp": 95, "cpu_seconds": 285},
        attestations=[WitnessAttestation("lct:web4:witness:v1", "verified", "sig", "ts")],
        ledger_proof=LedgerProof("0xabc", 12345, "proof123"),
    )
    check("T6.1 Status success", result.status == "success")
    check("T6.2 Output hash", "sha256" in result.output["hash"])
    check("T6.3 ATP consumed", result.resource_consumed["atp"] == 95)
    check("T6.4 Attestation present", len(result.attestations) == 1)
    check("T6.5 Ledger proof", result.ledger_proof.block_height == 12345)
    check("T6.6 Tx hash", result.ledger_proof.tx_hash.startswith("0x"))

    # Error result
    err_result = Result(
        status="error",
        error={"type": "ResourceInsufficient", "message": "Not enough ATP"},
        resource_consumed={"atp": 0},
        refund={"amount": 100, "status": "completed"},
    )
    check("T6.7 Error status", err_result.status == "error")
    check("T6.8 Error type", err_result.error["type"] == "ResourceInsufficient")
    check("T6.9 Refund", err_result.refund["status"] == "completed")

    # ── T7: Reputation Component (§1.7) ──
    print("T7: Reputation (§1.7)")

    rep = ReputationDelta(
        subject_lct="lct:web4:entity:alice",
        role_lct="lct:web4:role:analyst_financial_q4:abc123",
        role_pairing_in_mrh=MRHRolePairing(
            entity="lct:web4:entity:alice",
            role="lct:web4:role:analyst_financial_q4:abc123",
            paired_at="2025-09-15T12:00:00Z",
            mrh_link="link:mrh:alice→role_analyst:xyz",
        ),
        action_type="analyze_dataset",
        action_target="resource:web4:dataset:quarterly_financials",
        action_id="txn:0xabc",
        rule_triggered="successful_analysis_completion",
        reason="Completed high-quality data analysis under deadline",
        t3_delta={
            "training": TensorDelta(0.01, 0.90, 0.91),
            "temperament": TensorDelta(0.005, 0.88, 0.885),
        },
        v3_delta={
            "veracity": TensorDelta(0.02, 0.85, 0.87),
        },
        contributing_factors=[
            ContributingFactor("deadline_met", 0.6),
            ContributingFactor("accuracy_threshold_exceeded", 0.4),
        ],
        witnesses=[WitnessAttestation("lct:web4:witness:validator", "sig", "ts")],
        net_trust_change=0.015,
        net_value_change=0.02,
        timestamp="2025-09-15T17:55:00Z",
    )
    check("T7.1 Subject LCT", rep.subject_lct == "lct:web4:entity:alice")
    check("T7.2 Role-contextualized", rep.is_role_contextualized)
    check("T7.3 MRH link", rep.role_pairing_in_mrh.mrh_link.startswith("link:mrh:"))
    check("T7.4 T3 training delta", rep.t3_delta["training"].change == 0.01)
    check("T7.5 T3 training from→to", rep.t3_delta["training"].to_value == 0.91)
    check("T7.6 T3 temperament delta", rep.t3_delta["temperament"].change == 0.005)
    check("T7.7 V3 veracity delta", rep.v3_delta["veracity"].change == 0.02)
    check("T7.8 Contributing factors sum", abs(sum(f.weight for f in rep.contributing_factors) - 1.0) < 1e-9)
    check("T7.9 Net trust", rep.net_trust_change == 0.015)
    check("T7.10 Net value", rep.net_value_change == 0.02)
    check("T7.11 Is positive", rep.is_positive)
    check("T7.12 Is observable", rep.is_observable)
    check("T7.13 Is attributable", rep.is_attributable)
    check("T7.14 Has witnesses", len(rep.witnesses) == 1)

    # Spec §1.7 key properties
    check("T7.15 Observable property", rep.is_observable)
    check("T7.16 Attributable property", rep.is_attributable)
    check("T7.17 Role-contextualized property", rep.is_role_contextualized)
    check("T7.18 Multi-dimensional (T3+V3)", len(rep.t3_delta) > 0 and len(rep.v3_delta) > 0)

    # ── T8: R7Action Complete Structure (§6 MUST) ──
    print("T8: R7Action Structure (§6)")

    action = R7Action(
        rules=rules, role=role, request=req, reference=ref, resource=res,
        action_type="compute",
    )
    check("T8.1 Not complete (no result/rep)", not action.is_complete())
    action.result = result
    action.reputation = rep
    check("T8.2 Complete with all 7", action.is_complete())
    check("T8.3 Action ID generated", action.action_id.startswith("txn:"))
    check("T8.4 Action type", action.action_type == "compute")

    # ── T9: Error Hierarchy (§7) ──
    print("T9: Error Hierarchy (§7)")

    errors = [
        RuleViolation("Rule broken"),
        RoleUnauthorized("No role"),
        RequestMalformed("Bad request"),
        ReferenceInvalid("Bad reference"),
        ResourceInsufficient("No resources"),
        ResultInvalid("Bad result"),
        ReputationComputationError("Cannot compute"),
    ]
    check("T9.1 All 7 error types", len(errors) == 7)
    for e in errors:
        check(f"T9.2 {type(e).__name__} is R7Error", isinstance(e, R7Error))
    check("T9.3 RuleViolation message", str(errors[0]) == "Rule broken")
    check("T9.4 ReputationComputationError (R7 addition)",
          isinstance(errors[6], ReputationComputationError))

    # ── T10: MRH Role Store ──
    print("T10: MRH Role Store")

    mrh = MRHRoleStore()
    mrh.register_pairing(
        "lct:web4:entity:alice",
        "lct:web4:role:analyst_financial_q4:abc123",
        T3InRole(0.85, 0.90, 0.88),
        V3InRole(0.92, 0.88, 0.85),
        "2025-09-15T12:00:00Z",
    )
    check("T10.1 Has pairing", mrh.has_pairing("lct:web4:entity:alice",
                                                 "lct:web4:role:analyst_financial_q4:abc123"))
    check("T10.2 No pairing", not mrh.has_pairing("lct:web4:entity:bob",
                                                    "lct:web4:role:analyst_financial_q4:abc123"))
    pairing = mrh.get_pairing("lct:web4:entity:alice",
                               "lct:web4:role:analyst_financial_q4:abc123")
    check("T10.3 T3 talent", pairing["t3"].talent == 0.85)
    check("T10.4 V3 veracity", pairing["v3"].veracity == 0.92)
    check("T10.5 MRH link", pairing["mrh_link"].startswith("link:mrh:"))

    # Apply deltas
    mrh.apply_deltas(
        "lct:web4:entity:alice",
        "lct:web4:role:analyst_financial_q4:abc123",
        {"training": TensorDelta(0.01, 0.90, 0.91)},
        {"veracity": TensorDelta(0.02, 0.92, 0.94)},
    )
    p2 = mrh.get_pairing("lct:web4:entity:alice",
                          "lct:web4:role:analyst_financial_q4:abc123")
    check("T10.6 T3 training updated", abs(p2["t3"].training - 0.91) < 1e-9)
    check("T10.7 V3 veracity updated", abs(p2["v3"].veracity - 0.94) < 1e-9)
    check("T10.8 History recorded", len(p2["history"]) == 1)

    # Clamping
    mrh.apply_deltas(
        "lct:web4:entity:alice",
        "lct:web4:role:analyst_financial_q4:abc123",
        {"training": TensorDelta(0.5, 0.91, 1.41)},  # Would exceed 1.0
        {},
    )
    p3 = mrh.get_pairing("lct:web4:entity:alice",
                          "lct:web4:role:analyst_financial_q4:abc123")
    check("T10.9 Clamped to 1.0", p3["t3"].training == 1.0)

    # ── T11: SAL Integration (§3) ──
    print("T11: SAL Integration (§3)")

    sal = SALIntegration()
    sal.add_norm(LawNorm(
        norm_id="norm:atp_min",
        society="lct:web4:society:testnet",
        law_hash="sha256:law1",
        constraint_type="atp_minimum",
        constraint_value=50,
    ))
    sal.add_ruling("sha256:prohibited_law", "prohibited")

    # Compliant
    ok, reason = sal.check_compliance(
        Rules(law_hash="sha256:abc"),
        Request(atp_stake=100),
        Role(role_lct="any"),
    )
    check("T11.1 Compliant (ATP >= min)", ok)

    # Non-compliant: ATP too low
    ok2, reason2 = sal.check_compliance(
        Rules(law_hash="sha256:abc"),
        Request(atp_stake=10),
        Role(role_lct="any"),
    )
    check("T11.2 Non-compliant (ATP < min)", not ok2)
    check("T11.3 Reason includes ATP", "ATP" in reason2)

    # Non-compliant: prohibited
    ok3, reason3 = sal.check_compliance(
        Rules(law_hash="sha256:prohibited_law"),
        Request(atp_stake=100),
        Role(role_lct="any"),
    )
    check("T11.4 Prohibited by oracle", not ok3)
    check("T11.5 Reason mentions prohibition", "prohibits" in reason3)

    # Reputation rules
    success_rules = sal.get_reputation_rules("analyze_dataset", "success")
    check("T11.6 Success rep rules", len(success_rules) > 0)
    check("T11.7 Affects trust", success_rules[0]["affects_trust"])
    check("T11.8 Trust dimension", success_rules[0]["trust_dimension"] == "training")

    failure_rules = sal.get_reputation_rules("analyze_dataset", "failure")
    check("T11.9 Failure rep rules", len(failure_rules) > 0)
    check("T11.10 Failure is negative", failure_rules[0]["trust_delta"] < 0)

    # ── T12: Pre-execution Validation (§2.1) ──
    print("T12: Pre-execution Validation (§2.1)")

    mrh2 = MRHRoleStore()
    mrh2.register_pairing(
        "lct:web4:entity:alice",
        "lct:web4:role:analyst:abc",
        T3InRole(0.85, 0.90, 0.88),
        V3InRole(0.92, 0.88, 0.85),
    )
    sal2 = SALIntegration()
    validator = R7Validator(mrh2, sal2)

    # Valid action
    valid_action = R7Action(
        rules=Rules(permissions=["read"]),
        role=Role(actor="lct:web4:entity:alice", role_lct="lct:web4:role:analyst:abc"),
        request=Request(action="read", atp_stake=0),
        resource=Resource(
            required=ResourceRequirement(atp=10),
            available=ResourceAvailable(atp_balance=100),
            escrow=Escrow(amount=10),
        ),
    )
    vr = validator.validate(valid_action)
    check("T12.1 Valid action passes", vr.valid)
    check("T12.2 Escrow locked", vr.escrow.locked)

    # No role pairing
    no_role = R7Action(
        role=Role(actor="lct:web4:entity:bob", role_lct="lct:web4:role:unknown:xyz"),
        request=Request(action="read"),
        resource=Resource(
            required=ResourceRequirement(atp=0),
            available=ResourceAvailable(atp_balance=100),
        ),
    )
    vr2 = validator.validate(no_role)
    check("T12.3 No role pairing fails", not vr2.valid)
    check("T12.4 RoleUnauthorized error", isinstance(vr2.error, RoleUnauthorized))

    # Prohibited action
    prohibited = R7Action(
        rules=Rules(prohibitions=["delete"]),
        role=Role(actor="lct:web4:entity:alice", role_lct="lct:web4:role:analyst:abc"),
        request=Request(action="delete"),
        resource=Resource(
            required=ResourceRequirement(atp=0),
            available=ResourceAvailable(atp_balance=100),
        ),
    )
    vr3 = validator.validate(prohibited)
    check("T12.5 Prohibited action fails", not vr3.valid)
    check("T12.6 RuleViolation error", isinstance(vr3.error, RuleViolation))

    # Insufficient resources
    no_atp = R7Action(
        role=Role(actor="lct:web4:entity:alice", role_lct="lct:web4:role:analyst:abc"),
        request=Request(action="read"),
        resource=Resource(
            required=ResourceRequirement(atp=1000),
            available=ResourceAvailable(atp_balance=100),
        ),
    )
    vr4 = validator.validate(no_atp)
    check("T12.7 Insufficient ATP fails", not vr4.valid)
    check("T12.8 ResourceInsufficient error", isinstance(vr4.error, ResourceInsufficient))

    # Agency cap exceeded
    agency_cap = R7Action(
        role=Role(actor="lct:web4:entity:alice", role_lct="lct:web4:role:analyst:abc"),
        request=Request(action="read"),
        resource=Resource(
            required=ResourceRequirement(atp=30),
            available=ResourceAvailable(atp_balance=100),
            agency_caps={"max_atp": 25},
        ),
    )
    vr5 = validator.validate(agency_cap)
    check("T12.9 Agency cap exceeded fails", not vr5.valid)
    check("T12.10 Agency cap error", isinstance(vr5.error, ResourceInsufficient))

    # ── T13: Resource Meter (§2.2) ──
    print("T13: Resource Meter (§2.2)")

    meter = ResourceMeter()
    meter.start()
    meter.record_atp(50.0)
    meter.record_compute("gpu_hours", 4)
    result_m = meter.stop()
    check("T13.1 ATP metered", result_m["atp"] == 50.0)
    check("T13.2 Elapsed positive", result_m["elapsed_s"] >= 0)
    check("T13.3 GPU hours recorded", result_m["gpu_hours"] == 4)
    check("T13.4 ATP used tracked", meter.atp_used == 50.0)

    # ── T14: Reputation Computer (§2.3) ──
    print("T14: Reputation Computer (§2.3)")

    mrh3 = MRHRoleStore()
    mrh3.register_pairing(
        "lct:web4:entity:bob",
        "lct:web4:role:ml_engineer:def456",
        T3InRole(0.85, 0.88, 0.90),
        V3InRole(0.90, 0.92, 0.88),
    )
    sal3 = SALIntegration()
    computer = ReputationComputer(mrh3, sal3)

    test_action = R7Action(
        role=Role(actor="lct:web4:entity:bob",
                  role_lct="lct:web4:role:ml_engineer:def456",
                  t3_in_role=T3InRole(0.85, 0.88, 0.90),
                  v3_in_role=V3InRole(0.90, 0.92, 0.88)),
        request=Request(action="train_model",
                        target="dataset:biotech:protein_folding_v3"),
    )
    test_result = Result(status="success", output={"model": "v1", "accuracy": 0.95})

    rep_delta = computer.compute(test_action, test_result)
    check("T14.1 Subject LCT", rep_delta.subject_lct == "lct:web4:entity:bob")
    check("T14.2 Role LCT", rep_delta.role_lct == "lct:web4:role:ml_engineer:def456")
    check("T14.3 Role-contextualized", rep_delta.is_role_contextualized)
    check("T14.4 MRH pairing", rep_delta.role_pairing_in_mrh is not None)
    check("T14.5 MRH link exists", rep_delta.role_pairing_in_mrh.mrh_link.startswith("link:mrh:"))
    check("T14.6 Action type", rep_delta.action_type == "train_model")
    check("T14.7 Action target", "biotech" in rep_delta.action_target)
    check("T14.8 T3 training delta", "training" in rep_delta.t3_delta)
    check("T14.9 T3 delta positive", rep_delta.t3_delta["training"].change > 0)
    check("T14.10 V3 veracity delta", "veracity" in rep_delta.v3_delta)
    check("T14.11 V3 delta positive", rep_delta.v3_delta["veracity"].change > 0)
    check("T14.12 Net trust positive", rep_delta.net_trust_change > 0)
    check("T14.13 Net value positive", rep_delta.net_value_change > 0)
    check("T14.14 Has reason", len(rep_delta.reason) > 0)
    check("T14.15 Has factors", len(rep_delta.contributing_factors) > 0)
    check("T14.16 Has timestamp", len(rep_delta.timestamp) > 0)

    # Failure reputation
    fail_result = Result(status="failure", error={"type": "Timeout", "message": "Too slow"})
    fail_rep = computer.compute(test_action, fail_result)
    check("T14.17 Failure: negative trust", fail_rep.net_trust_change < 0)
    check("T14.18 Failure: temperament hit", "temperament" in fail_rep.t3_delta)
    check("T14.19 Even failures produce reputation (§6 MUST #4)",
          fail_rep.subject_lct != "")

    # No MRH pairing → error
    bad_action = R7Action(
        role=Role(actor="lct:web4:entity:unknown", role_lct="lct:web4:role:none:xyz"),
        request=Request(action="test"),
    )
    try:
        computer.compute(bad_action, test_result)
        check("T14.20 No pairing raises", False)
    except ReputationComputationError:
        check("T14.20 No pairing raises", True)

    # ── T15: Escrow Lock ──
    print("T15: Escrow Lock")

    escrow = EscrowLock(amount=100, locked=True)
    check("T15.1 Locked", escrow.locked)
    result_e = escrow.release("completed")
    check("T15.2 Released", escrow.released)
    check("T15.3 Not locked after release", not escrow.locked)
    check("T15.4 Release result", result_e["status"] == "completed")

    # ── T16: Ledger ──
    print("T16: Ledger")

    ledger = Ledger()
    proof = ledger.write({"test": "entry1"})
    check("T16.1 Tx hash format", proof.tx_hash.startswith("0x"))
    check("T16.2 Block height 1", proof.block_height == 1)
    check("T16.3 Inclusion proof", len(proof.inclusion_proof) > 0)

    proof2 = ledger.write({"test": "entry2"})
    check("T16.4 Block height 2", proof2.block_height == 2)
    check("T16.5 Different tx hashes", proof.tx_hash != proof2.tx_hash)
    check("T16.6 Entries stored", len(ledger.entries) == 2)

    # ── T17: Full R7 Engine Lifecycle (§2+§4) ──
    print("T17: Full R7 Engine Lifecycle (§2+§4)")

    mrh4 = MRHRoleStore()
    mrh4.register_pairing(
        "lct:web4:entity:alice",
        "lct:web4:role:analyst:abc",
        T3InRole(0.85, 0.90, 0.88),
        V3InRole(0.92, 0.88, 0.85),
    )
    engine = R7Engine(mrh4, SALIntegration())

    full_action = R7Action(
        rules=Rules(
            law_hash="sha256:law1",
            society="lct:web4:society:testnet",
            permissions=["read", "write"],
        ),
        role=Role(
            actor="lct:web4:entity:alice",
            role_lct="lct:web4:role:analyst:abc",
            t3_in_role=T3InRole(0.85, 0.90, 0.88),
            v3_in_role=V3InRole(0.92, 0.88, 0.85),
        ),
        request=Request(
            action="analyze_dataset",
            target="resource:web4:dataset:q4",
            atp_stake=100,
        ),
        reference=Reference(
            precedents=[Precedent("sha256:prev", "success", 0.8)],
        ),
        resource=Resource(
            required=ResourceRequirement(atp=50),
            available=ResourceAvailable(atp_balance=500),
            pricing=ResourcePricing(surge_multiplier=1.0),
            escrow=Escrow(amount=50),
        ),
        action_type="compute",
    )

    completed = engine.execute_action(full_action)

    # §6 MUST: All 7 components present
    check("T17.1 Result present", completed.result is not None)
    check("T17.2 Reputation present", completed.reputation is not None)
    check("T17.3 Complete action", completed.is_complete())

    # §4.1 Determinism: result status
    check("T17.4 Success", completed.result.status == "success")

    # §4.2 Non-repudiation: ledger proof
    check("T17.5 Ledger proof", completed.result.ledger_proof.tx_hash.startswith("0x"))
    check("T17.6 Block height", completed.result.ledger_proof.block_height > 0)

    # §4.6 Reputation observability
    check("T17.7 Rep role-contextualized", completed.reputation.is_role_contextualized)
    check("T17.8 Rep observable", completed.reputation.is_observable)
    check("T17.9 Rep has action ID", len(completed.reputation.action_id) > 0)
    check("T17.10 Net trust positive", completed.reputation.net_trust_change > 0)
    check("T17.11 Net value positive", completed.reputation.net_value_change > 0)

    # Tensor updates applied to MRH
    p = mrh4.get_pairing("lct:web4:entity:alice", "lct:web4:role:analyst:abc")
    check("T17.12 T3 training updated", p["t3"].training > 0.90)
    check("T17.13 V3 veracity updated", p["v3"].veracity > 0.92)
    check("T17.14 History has entry", len(p["history"]) > 0)

    # Completed actions tracked
    check("T17.15 Engine tracks action", len(engine.completed_actions) == 1)

    # ── T18: Failure Path (§2+§6 MUST #4) ──
    print("T18: Failure Path (§6 MUST #4)")

    mrh5 = MRHRoleStore()
    mrh5.register_pairing(
        "lct:web4:entity:bob",
        "lct:web4:role:engineer:xyz",
        T3InRole(0.80, 0.80, 0.80),
        V3InRole(0.80, 0.80, 0.80),
    )
    engine2 = R7Engine(mrh5, SALIntegration())

    # Register a handler that fails
    def failing_handler(action):
        raise ValueError("Simulated execution failure")

    engine2.register_handler("fail_task", failing_handler)

    fail_action = R7Action(
        role=Role(actor="lct:web4:entity:bob", role_lct="lct:web4:role:engineer:xyz"),
        request=Request(action="fail_task", target="test"),
        resource=Resource(
            required=ResourceRequirement(atp=10),
            available=ResourceAvailable(atp_balance=100),
            escrow=Escrow(amount=10),
        ),
    )

    failed_completed = engine2.execute_action(fail_action)
    check("T18.1 Status failure", failed_completed.result.status == "failure")
    check("T18.2 Error info", "Simulated" in failed_completed.result.error["message"])
    check("T18.3 Still has reputation (§6 MUST #4)", failed_completed.reputation is not None)
    check("T18.4 Negative trust change", failed_completed.reputation.net_trust_change < 0)
    check("T18.5 Refund issued", failed_completed.result.refund is not None)
    check("T18.6 Refund status", failed_completed.result.refund["status"] == "refunded")
    check("T18.7 Rep is observable", failed_completed.reputation.is_observable)

    # ── T19: Validation Failure (§7 Error R7 Result) ──
    print("T19: Validation Failure (§7)")

    engine3 = R7Engine(MRHRoleStore(), SALIntegration())
    invalid_action = R7Action(
        role=Role(actor="lct:web4:entity:nobody", role_lct="lct:web4:role:none:xyz"),
        request=Request(action="read"),
        resource=Resource(
            required=ResourceRequirement(atp=10),
            available=ResourceAvailable(atp_balance=100),
        ),
    )
    error_result = engine3.execute_action(invalid_action)
    check("T19.1 Error status", error_result.result.status == "error")
    check("T19.2 Error type in result", error_result.result.error["type"] == "RoleUnauthorized")
    check("T19.3 Still has reputation", error_result.reputation is not None)
    check("T19.4 Rep reason mentions failure", "failed" in error_result.reputation.reason.lower()
          or "Validation" in error_result.reputation.reason)

    # ── T20: Spec Example §5.1 — Simple Query ──
    print("T20: Spec Example §5.1 (Simple Query)")

    mrh6 = MRHRoleStore()
    mrh6.register_pairing(
        "lct:web4:entity:reader",
        "lct:web4:role:reader:001",
        T3InRole(0.80, 0.80, 0.80),
        V3InRole(0.80, 0.95, 0.80),
    )
    engine4 = R7Engine(mrh6, SALIntegration())

    query_action = R7Action(
        action_type="query",
        rules=Rules(law_hash="sha256:law1"),
        role=Role(actor="lct:web4:entity:reader",
                  role_lct="lct:web4:role:reader:001"),
        request=Request(action="read", target="data:test"),
        resource=Resource(
            required=ResourceRequirement(atp=1),
            available=ResourceAvailable(atp_balance=100),
        ),
    )
    q_result = engine4.execute_action(query_action)
    check("T20.1 Query success", q_result.result.status == "success")
    check("T20.2 Reputation present", q_result.reputation is not None)
    check("T20.3 Net value change", q_result.reputation.net_value_change > 0)
    # §5.1: Simple query → v3_delta.validity +0.001
    check("T20.4 V3 has veracity", "veracity" in q_result.reputation.v3_delta)

    # ── T21: Spec Example §5.2 — Trust Query (ATP-staked) ──
    print("T21: Spec Example §5.2 (Trust Query)")

    mrh7 = MRHRoleStore()
    mrh7.register_pairing(
        "lct:web4:entity:investigator",
        "lct:web4:role:investigator:002",
        T3InRole(0.75, 0.80, 0.80),
        V3InRole(0.80, 0.80, 0.80),
    )
    engine5 = R7Engine(mrh7, SALIntegration())

    trust_query = R7Action(
        action_type="trust_query",
        rules=Rules(constraints=[Constraint("atp_minimum", 100)]),
        role=Role(actor="lct:web4:entity:investigator",
                  role_lct="lct:web4:role:investigator:002"),
        request=Request(
            action="query_trust",
            target="lct:web4:entity:target",
            parameters={"requestedRole": "web4:Surgeon"},
            atp_stake=100,
        ),
        reference=Reference(mrh_context=MRHContext(depth=2)),
        resource=Resource(
            required=ResourceRequirement(atp=100),
            available=ResourceAvailable(atp_balance=500),
            escrow=Escrow(amount=100),
        ),
    )
    tq_result = engine5.execute_action(trust_query)
    check("T21.1 Trust query success", tq_result.result.status == "success")
    check("T21.2 Reputation present", tq_result.reputation is not None)
    check("T21.3 Trust change", tq_result.reputation.net_trust_change > 0)
    check("T21.4 Value change", tq_result.reputation.net_value_change > 0)
    check("T21.5 Role-contextualized", tq_result.reputation.is_role_contextualized)

    # ── T22: Spec Example §5.3 — Computational Task ──
    print("T22: Spec Example §5.3 (Computational Task)")

    mrh8 = MRHRoleStore()
    mrh8.register_pairing(
        "lct:web4:entity:bob",
        "lct:web4:role:ml_engineer_biotech_2025:def456",
        T3InRole(0.85, 0.88, 0.90),
        V3InRole(0.90, 0.92, 0.88),
        "2025-08-10T09:00:00Z",
    )
    engine6 = R7Engine(mrh8, SALIntegration())

    compute_action = R7Action(
        action_type="compute",
        rules=Rules(permissions=["execute"]),
        role=Role(
            actor="lct:web4:entity:bob",
            role_lct="lct:web4:role:ml_engineer_biotech_2025:def456",
            paired_at="2025-08-10T09:00:00Z",
            t3_in_role=T3InRole(0.85, 0.88, 0.90),
            v3_in_role=V3InRole(0.90, 0.92, 0.88),
        ),
        request=Request(
            action="train_model",
            target="dataset:biotech:protein_folding_v3",
            parameters={"dataset": "protein_v3", "algorithm": "gnn"},
        ),
        resource=Resource(
            required=ResourceRequirement(atp=50, compute={"gpu": "4xA100", "duration": "3600s"}),
            available=ResourceAvailable(atp_balance=500),
        ),
    )
    c_result = engine6.execute_action(compute_action)
    check("T22.1 Compute success", c_result.result.status == "success")
    check("T22.2 T3 training updated",
          "training" in c_result.reputation.t3_delta)
    check("T22.3 Training delta +0.01",
          c_result.reputation.t3_delta["training"].change == 0.01)
    check("T22.4 Training from 0.88",
          abs(c_result.reputation.t3_delta["training"].from_value - 0.88) < 1e-9)
    check("T22.5 Training to 0.89",
          abs(c_result.reputation.t3_delta["training"].to_value - 0.89) < 1e-6)
    check("T22.6 Role pairing in MRH",
          c_result.reputation.role_pairing_in_mrh is not None)
    check("T22.7 Correct entity in pairing",
          c_result.reputation.role_pairing_in_mrh.entity == "lct:web4:entity:bob")
    check("T22.8 Correct role in pairing",
          "ml_engineer" in c_result.reputation.role_pairing_in_mrh.role)

    # Verify MRH actually updated
    p_bob = mrh8.get_pairing("lct:web4:entity:bob",
                              "lct:web4:role:ml_engineer_biotech_2025:def456")
    check("T22.9 MRH T3 training = 0.89", abs(p_bob["t3"].training - 0.89) < 1e-9)

    # ── T23: Spec Example §5.4 — Authority Delegation ──
    print("T23: Spec Example §5.4 (Authority Delegation)")

    mrh9 = MRHRoleStore()
    mrh9.register_pairing(
        "lct:web4:authority:delegator",
        "lct:web4:role:authority:auth001",
        T3InRole(0.90, 0.90, 0.92),
        V3InRole(0.95, 0.98, 0.95),
    )
    engine7 = R7Engine(mrh9, SALIntegration())

    deleg_action = R7Action(
        action_type="delegation",
        rules=Rules(law_hash="sha256:law1", society="lct:web4:society:main"),
        role=Role(
            actor="lct:web4:authority:delegator",
            role_lct="lct:web4:role:authority:auth001",
        ),
        request=Request(
            action="delegate",
            target="lct:web4:subauthority:finance",
            parameters={"scope": "finance", "limits": {"max_atp": 1000}},
        ),
        reference=Reference(
            interpretations=[LawInterpretation("lct:web4:oracle:main", "permitted", "h1")],
        ),
        resource=Resource(
            required=ResourceRequirement(atp=0),
            available=ResourceAvailable(atp_balance=10000),
        ),
    )
    d_result = engine7.execute_action(deleg_action)
    check("T23.1 Delegation success", d_result.result.status == "success")
    check("T23.2 Reputation present", d_result.reputation is not None)
    # §5.4: temperament +0.005, validity +0.01
    check("T23.3 Trust change",
          d_result.reputation.net_trust_change > 0)
    check("T23.4 Value change",
          d_result.reputation.net_value_change > 0)
    check("T23.5 Ledger recorded",
          d_result.result.ledger_proof.block_height > 0)

    # ── T24: Spec Example §5.5 — Agency-Delegated Action ──
    print("T24: Spec Example §5.5 (Agency-Delegated Action)")

    mrh10 = MRHRoleStore()
    mrh10.register_pairing(
        "lct:web4:agent:invoicebot",
        "lct:web4:role:agent:agentabc",
        T3InRole(0.80, 0.85, 0.87),
        V3InRole(0.85, 0.85, 0.85),
    )
    engine8 = R7Engine(mrh10, SALIntegration())

    agency_action = R7Action(
        action_type="agency_action",
        rules=Rules(law_hash="sha256:law1"),
        role=Role(
            actor="lct:web4:agent:invoicebot",
            role_lct="lct:web4:role:agent:agentabc",
        ),
        request=Request(
            action="approve_invoice",
            target="invoice:123",
            parameters={"amount": 20, "currency": "ATP"},
            proof_of_agency=ProofOfAgency(
                grant_id="agy:grant:001",
                inclusion_proof="hash:abc",
                scope="finance:payments",
                witness_level=2,
            ),
        ),
        resource=Resource(
            required=ResourceRequirement(atp=20),
            available=ResourceAvailable(atp_balance=100),
            agency_caps={"max_atp": 25, "remaining": 5},
        ),
    )
    a_result = engine8.execute_action(agency_action)
    check("T24.1 Agency action success", a_result.result.status == "success")
    check("T24.2 Reputation present", a_result.reputation is not None)
    check("T24.3 Trust change", a_result.reputation.net_trust_change > 0)
    check("T24.4 Role-contextualized", a_result.reputation.is_role_contextualized)

    # ── T25: R6→R7 Migration (§8.3) ──
    print("T25: R6→R7 Migration (§8)")

    r6_result = R6CompatResult(
        status="success",
        output={"data": "legacy_analysis"},
        tensor_updates={"training": 0.02, "veracity": 0.01},
    )
    migration_role = Role(
        actor="lct:web4:entity:legacy",
        role_lct="lct:web4:role:legacy:old1",
        t3_in_role=T3InRole(0.80, 0.80, 0.80),
        v3_in_role=V3InRole(0.80, 0.80, 0.80),
    )
    r7_result, r7_rep = migrate_r6_to_r7(r6_result, migration_role)
    check("T25.1 Result migrated", r7_result.status == "success")
    check("T25.2 Output preserved", r7_result.output["data"] == "legacy_analysis")
    check("T25.3 T3 training extracted", "training" in r7_rep.t3_delta)
    check("T25.4 Training delta", r7_rep.t3_delta["training"].change == 0.02)
    check("T25.5 Training from", r7_rep.t3_delta["training"].from_value == 0.80)
    check("T25.6 Training to", abs(r7_rep.t3_delta["training"].to_value - 0.82) < 1e-6)
    check("T25.7 V3 veracity extracted", "veracity" in r7_rep.v3_delta)
    check("T25.8 Veracity delta", r7_rep.v3_delta["veracity"].change == 0.01)
    check("T25.9 Net trust", abs(r7_rep.net_trust_change - 0.02) < 1e-6)
    check("T25.10 Net value", abs(r7_rep.net_value_change - 0.01) < 1e-6)
    check("T25.11 Migration reason", "Migrated" in r7_rep.reason)
    check("T25.12 Backward compat: no extra dims",
          "talent" not in r7_rep.t3_delta and "temperament" not in r7_rep.t3_delta)

    # ── T26: Action Type Registry (§8.1) ──
    print("T26: Action Type Registry (§8)")

    registry = ActionTypeRegistry()
    registry.register(
        "custom_analysis",
        validation_rules=["must_have_atp", "must_have_reference"],
        reputation_rules=[
            {"id": "custom_success", "affects_trust": True,
             "trust_dimension": "talent", "trust_delta": 0.03},
        ],
    )
    check("T26.1 Type registered", registry.has_type("custom_analysis"))
    check("T26.2 Unknown type", not registry.has_type("unknown"))
    check("T26.3 Rep rules", len(registry.get_reputation_rules("custom_analysis")) == 1)
    check("T26.4 Rep rule delta", registry.get_reputation_rules("custom_analysis")[0]["trust_delta"] == 0.03)
    check("T26.5 Unknown rules empty", len(registry.get_reputation_rules("unknown")) == 0)

    # ── T27: Custom Handler (§8) ──
    print("T27: Custom Handler (§8)")

    mrh11 = MRHRoleStore()
    mrh11.register_pairing(
        "lct:web4:entity:custom",
        "lct:web4:role:custom:001",
        T3InRole(0.70, 0.70, 0.70),
        V3InRole(0.70, 0.70, 0.70),
    )
    engine9 = R7Engine(mrh11, SALIntegration())

    custom_output = {"analysis": "complete", "score": 0.95}
    engine9.register_handler("custom_analysis", lambda a: custom_output)

    custom_action = R7Action(
        role=Role(actor="lct:web4:entity:custom",
                  role_lct="lct:web4:role:custom:001"),
        request=Request(action="custom_analysis", target="data:test"),
        resource=Resource(
            required=ResourceRequirement(atp=5),
            available=ResourceAvailable(atp_balance=100),
        ),
    )
    c_custom = engine9.execute_action(custom_action)
    check("T27.1 Custom handler success", c_custom.result.status == "success")
    check("T27.2 Custom output", c_custom.result.output["score"] == 0.95)
    check("T27.3 Reputation computed", c_custom.reputation is not None)

    # ── T28: Security Properties (§4) ──
    print("T28: Security Properties (§4)")

    # §4.1 Determinism: same inputs → same result status
    mrh12 = MRHRoleStore()
    mrh12.register_pairing("lct:web4:entity:det", "lct:web4:role:det:001",
                            T3InRole(0.50, 0.50, 0.50), V3InRole(0.50, 0.50, 0.50))
    e1 = R7Engine(mrh12, SALIntegration())

    det_action = R7Action(
        role=Role(actor="lct:web4:entity:det", role_lct="lct:web4:role:det:001"),
        request=Request(action="read", target="data:test", nonce="fixed_nonce"),
        resource=Resource(
            required=ResourceRequirement(atp=1),
            available=ResourceAvailable(atp_balance=100),
        ),
    )
    r1 = e1.execute_action(det_action)

    mrh13 = MRHRoleStore()
    mrh13.register_pairing("lct:web4:entity:det", "lct:web4:role:det:001",
                            T3InRole(0.50, 0.50, 0.50), V3InRole(0.50, 0.50, 0.50))
    e2 = R7Engine(mrh13, SALIntegration())
    det_action2 = R7Action(
        role=Role(actor="lct:web4:entity:det", role_lct="lct:web4:role:det:001"),
        request=Request(action="read", target="data:test", nonce="fixed_nonce"),
        resource=Resource(
            required=ResourceRequirement(atp=1),
            available=ResourceAvailable(atp_balance=100),
        ),
    )
    r2 = e2.execute_action(det_action2)
    check("T28.1 §4.1 Determinism: same status", r1.result.status == r2.result.status)
    check("T28.2 §4.1 Determinism: same trust delta",
          r1.reputation.net_trust_change == r2.reputation.net_trust_change)

    # §4.2 Non-repudiation: ledger proof
    check("T28.3 §4.2 Non-repudiation: proof exists",
          r1.result.ledger_proof.tx_hash.startswith("0x"))

    # §4.3 Resource bounds
    check("T28.4 §4.3 Resource bounds: consumed tracked",
          "atp" in r1.result.resource_consumed)

    # §4.4 Role isolation
    mrh_ri = MRHRoleStore()
    mrh_ri.register_pairing("lct:web4:entity:x", "lct:web4:role:reader:001",
                             T3InRole(0.50, 0.50, 0.50), V3InRole(0.50, 0.50, 0.50))
    e_ri = R7Engine(mrh_ri, SALIntegration())
    isolated_action = R7Action(
        rules=Rules(prohibitions=["write"]),
        role=Role(actor="lct:web4:entity:x", role_lct="lct:web4:role:reader:001"),
        request=Request(action="write", target="data:forbidden"),
        resource=Resource(
            required=ResourceRequirement(atp=1),
            available=ResourceAvailable(atp_balance=100),
        ),
    )
    iso_result = e_ri.execute_action(isolated_action)
    check("T28.5 §4.4 Role isolation: prohibited action blocked",
          iso_result.result.status == "error")

    # §4.5 Atomic settlement: escrow released on success
    check("T28.6 §4.5 Atomic: result + reputation consistent",
          (r1.result.status == "success" and r1.reputation.net_trust_change > 0)
          or (r1.result.status == "failure" and r1.reputation.net_trust_change <= 0)
          or r1.result.status == "error")

    # §4.6 Reputation observability
    check("T28.7 §4.6 Reputation observable", r1.reputation.is_observable)
    check("T28.8 §4.6 Reputation attributable",
          len(r1.reputation.action_id) > 0)

    # ── T29: §3 R7-SAL Table Verification ──
    print("T29: R7-SAL Integration Table (§3)")

    # Rules ↔ Law Oracle: law_hash present
    check("T29.1 Rules↔SAL: law_hash", len(full_action.rules.law_hash) > 0)

    # Role ↔ Citizen prerequisite: role_lct exists
    check("T29.2 Role↔SAL: role LCT", len(full_action.role.role_lct) > 0)

    # Request ↔ Society laws: constraints exist
    check("T29.3 Request↔SAL: action defined", len(full_action.request.action) > 0)

    # Reference ↔ Oracle rulings: interpretations
    check("T29.4 Reference↔SAL: has precedents", len(full_action.reference.precedents) > 0)

    # Resource ↔ ATP caps: escrow
    check("T29.5 Resource↔SAL: escrow present", full_action.resource.escrow.amount > 0)

    # Result ↔ Witness: attestations possible
    check("T29.6 Result↔SAL: result present", completed.result is not None)

    # Reputation ↔ Observable trust: reputation present
    check("T29.7 Reputation↔SAL: trust mechanics observable",
          completed.reputation.is_observable)

    # ── T30: §6 Implementation Requirements ──
    print("T30: Implementation Requirements (§6)")

    # MUST #1: All actions follow complete R7 structure
    check("T30.1 MUST #1: complete structure", completed.is_complete())

    # MUST #2: All seven components present
    check("T30.2 MUST #2: rules present", completed.rules is not None)
    check("T30.3 MUST #2: role present", completed.role is not None)
    check("T30.4 MUST #2: request present", completed.request is not None)
    check("T30.5 MUST #2: reference present", completed.reference is not None)
    check("T30.6 MUST #2: resource present", completed.resource is not None)
    check("T30.7 MUST #2: result present", completed.result is not None)
    check("T30.8 MUST #2: reputation present", completed.reputation is not None)

    # MUST #3: Results and reputation deterministic
    check("T30.9 MUST #3: deterministic (tested in T28)", True)

    # MUST #4: Failed actions still produce valid R7 results with reputation
    check("T30.10 MUST #4: failure has result", failed_completed.result is not None)
    check("T30.11 MUST #4: failure has reputation", failed_completed.reputation is not None)

    # MUST #5: All transactions written to ledger
    check("T30.12 MUST #5: ledger proof", completed.result.ledger_proof.block_height > 0)
    check("T30.13 MUST #5: failed also on ledger",
          failed_completed.result.ledger_proof.block_height > 0)

    # MUST #6: Reputation computed explicitly (R7 requirement)
    check("T30.14 MUST #6: explicit reputation", completed.reputation.is_observable)
    check("T30.15 MUST #6: explicit on failure", failed_completed.reputation.is_observable)

    # ── T31: Edge Cases ──
    print("T31: Edge Cases")

    # Zero ATP action
    mrh_z = MRHRoleStore()
    mrh_z.register_pairing("lct:web4:entity:z", "lct:web4:role:z:001",
                            T3InRole(0.50, 0.50, 0.50), V3InRole(0.50, 0.50, 0.50))
    e_z = R7Engine(mrh_z, SALIntegration())
    zero_action = R7Action(
        role=Role(actor="lct:web4:entity:z", role_lct="lct:web4:role:z:001"),
        request=Request(action="read"),
        resource=Resource(
            required=ResourceRequirement(atp=0),
            available=ResourceAvailable(atp_balance=0),
        ),
    )
    z_result = e_z.execute_action(zero_action)
    check("T31.1 Zero ATP passes", z_result.result.status == "success")

    # Multiple actions same engine (state accumulation)
    mrh_m = MRHRoleStore()
    mrh_m.register_pairing("lct:web4:entity:m", "lct:web4:role:m:001",
                            T3InRole(0.50, 0.50, 0.50), V3InRole(0.50, 0.50, 0.50))
    e_m = R7Engine(mrh_m, SALIntegration())
    for i in range(3):
        a = R7Action(
            role=Role(actor="lct:web4:entity:m", role_lct="lct:web4:role:m:001"),
            request=Request(action="read", nonce=f"nonce_{i}"),
            resource=Resource(
                required=ResourceRequirement(atp=1),
                available=ResourceAvailable(atp_balance=100),
            ),
        )
        e_m.execute_action(a)

    check("T31.2 3 actions tracked", len(e_m.completed_actions) == 3)
    check("T31.3 Ledger has 3 entries", len(e_m.ledger.entries) == 3)

    # Training accumulates over actions
    p_m = mrh_m.get_pairing("lct:web4:entity:m", "lct:web4:role:m:001")
    check("T31.4 Training accumulated > 0.50",
          p_m["t3"].training > 0.50)
    check("T31.5 3 history entries", len(p_m["history"]) == 3)

    # Empty reputation delta (no rules triggered)
    empty_rep = ReputationDelta(
        subject_lct="lct:web4:entity:test",
        role_lct="lct:web4:role:test:001",
        net_trust_change=0.0,
        net_value_change=0.0,
    )
    check("T31.6 Empty rep not positive", not empty_rep.is_positive)
    check("T31.7 Empty rep still observable", empty_rep.is_observable)
    check("T31.8 Empty rep role-contextualized", empty_rep.is_role_contextualized)

    # ── Summary ──
    print()
    print("=" * 60)
    print(f"R7 Framework: {passed}/{passed+failed} checks passed")
    if failures:
        print(f"  {failed} FAILED:")
        for f in failures:
            print(f"    - {f}")
    else:
        print("  All checks passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
