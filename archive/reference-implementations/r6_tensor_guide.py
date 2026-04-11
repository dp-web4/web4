#!/usr/bin/env python3
"""
Web4 R6 Framework + T3/V3 Tensor Integration Guide — Reference Implementation
Spec: web4-standard/R6_TENSOR_GUIDE.md (810 lines, 7 parts)

Covers:
  Part 1: R6 Action Framework (6 components, lifecycle, confidence calculation)
  Part 2: T3 Tensor System (talent/training/temperament, evolution, decay)
  Part 3: V3 Tensor System (valuation/veracity/validity, calculation, aggregation)
  Part 4: Tensor Interactions (T3→V3 influence, V3→T3 feedback)
  Part 5: Practical Applications (role matching, ATP pricing, team composition)
  Part 6: Implementation Guidelines (tensor storage, update triggers, privacy)
  Part 7: Advanced Patterns (prediction, cross-entity correlation, gaming prevention)

Run:  python3 r6_tensor_guide.py
"""

import time, math, hashlib, json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# ─────────────────────────────────────────────
# Part 1: R6 Action Framework
# ─────────────────────────────────────────────

@dataclass
class Rules:
    """R6 Component 1: What's Possible"""
    applicable: List[str]           # Action types allowed
    constraints: Dict[str, float]   # max_atp, timeout_seconds, quality_threshold
    requirements: Dict[str, Any]    # entity_type, min_t3

    def allows(self, action_type: str) -> bool:
        return action_type in self.applicable

    def check_t3(self, t3: 'T3Tensor') -> bool:
        min_t3 = self.requirements.get("min_t3", {})
        for dim, threshold in min_t3.items():
            if getattr(t3, dim, 0.0) < threshold:
                return False
        return True

@dataclass
class Role:
    """R6 Component 2: Who Can Act"""
    lct: str
    permissions: List[str]
    delegation_from: str = ""
    valid_until: str = ""

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions

@dataclass
class Request:
    """R6 Component 3: What's Wanted"""
    intent: str
    parameters: Dict[str, Any]
    priority: str = "normal"
    requestor: str = ""

@dataclass
class Reference:
    """R6 Component 4: Historical Context"""
    similar_actions: List[Dict[str, Any]] = field(default_factory=list)
    patterns: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5

    def success_rate(self) -> float:
        if not self.similar_actions:
            return 0.5
        successes = sum(1 for a in self.similar_actions if a.get("outcome") == "success")
        return successes / len(self.similar_actions)

@dataclass
class Resource:
    """R6 Component 5: What's Needed"""
    atp_required: float
    compute_units: int = 0
    memory_gb: float = 0.0
    storage_gb: float = 0.0
    estimated_duration: int = 0

    def is_active(self) -> bool:
        """Active resources can complete full R6 transactions"""
        return True  # Default; subclasses override

@dataclass
class ActiveResource(Resource):
    """Entity that can complete full R6 transactions"""
    entity_lct: str = ""
    energy_source: str = "compute"
    fractal_chain: List[str] = field(default_factory=list)

    def is_active(self) -> bool:
        return True

@dataclass
class PassiveResource(Resource):
    """Infrastructure supporting but not completing R6 transactions"""
    entity_lct: str = ""
    purpose: str = "maintenance"
    utilization_by: List[str] = field(default_factory=list)

    def is_active(self) -> bool:
        return False

@dataclass
class ADPProof:
    """Allocation Discharge Packet — proof of work"""
    amount: float
    transaction_id: str
    transaction_hash: str
    energy_spent: float
    fractal_chain: List[str] = field(default_factory=list)
    context_bound: bool = True

@dataclass
class ReputationDistribution:
    """Fractal reputation propagation from ADP"""
    distributions: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def distribute(self, adp_amount: float, fractal_chain: List[str]) -> Dict[str, float]:
        """Distribute reputation up fractal chain per spec:
        performer: 90%, team: 7%, org: 2%, society: 1%"""
        if not fractal_chain:
            return {}
        ratios = [0.01, 0.02, 0.07, 0.90]  # society, org, team, performer
        result = {}
        chain = list(fractal_chain)  # Deepest last
        for i, entity in enumerate(chain):
            ratio = ratios[i] if i < len(ratios) else ratios[-1]
            earned = adp_amount * ratio
            result[entity] = earned
            self.distributions[entity] = {"contribution": ratio, "reputation_earned": earned}
        return result

@dataclass
class Result:
    """R6 Component 6: What Happened"""
    status: str  # success, failure, partial
    output: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    t3_updates: Dict[str, float] = field(default_factory=dict)
    v3_generated: Dict[str, float] = field(default_factory=dict)
    adp_proof: Optional[ADPProof] = None
    reputation_distribution: Optional[Dict[str, float]] = None

# ─── R6 Action Lifecycle ───

class R6ActionLifecycle:
    """Full R6 lifecycle: Intent→RuleCheck→RoleValidation→Request→Reference→Resource→Execute→Result→TensorUpdate→Witness"""

    def __init__(self):
        self.actions: List[Dict] = []

    def calculate_confidence(self, t3: 'T3Tensor', reference: Reference,
                             resource: Resource, role: Role,
                             w1=0.3, w2=0.3, w3=0.2, w4=0.2) -> float:
        """Pre-execution confidence calculation per spec §Confidence"""
        t3_alignment = (t3.talent + t3.training + t3.temperament) / 3.0
        historical_success = reference.success_rate()
        resource_availability = 1.0 if resource.atp_required > 0 else 0.0
        role_match = 1.0 if role.permissions else 0.0
        confidence = (w1 * t3_alignment + w2 * historical_success +
                      w3 * resource_availability + w4 * role_match) / (w1 + w2 + w3 + w4)
        return confidence

    def execute(self, rules: Rules, role: Role, request: Request,
                reference: Reference, resource: Resource,
                performer_t3: 'T3Tensor') -> Result:
        """Execute full R6 lifecycle"""
        # Step 1: Rule check
        if not rules.allows(request.intent):
            return Result(status="rejected", output={"reason": "action_not_allowed"})
        if not rules.check_t3(performer_t3):
            return Result(status="rejected", output={"reason": "t3_below_minimum"})

        # Step 2: Role validation
        required_perms = request.parameters.get("required_permissions", [])
        for perm in required_perms:
            if not role.has_permission(perm):
                return Result(status="rejected", output={"reason": f"missing_permission:{perm}"})

        # Step 3: Confidence check
        confidence = self.calculate_confidence(performer_t3, reference, resource, role)
        if confidence < 0.7:
            return Result(status="low_confidence", output={"confidence": confidence},
                          metrics={"confidence": confidence})

        # Step 4: Resource allocation (ATP)
        atp_allocated = resource.atp_required

        # Step 5: Execute (simulate)
        quality = min(1.0, confidence * 1.1)  # Quality correlates with confidence

        # Step 6: Generate ADP proof
        tx_id = f"r6:tx:{hashlib.sha256(request.intent.encode()).hexdigest()[:16]}"
        adp = ADPProof(
            amount=atp_allocated * 0.95,  # 5% overhead
            transaction_id=tx_id,
            transaction_hash=hashlib.sha256(tx_id.encode()).hexdigest(),
            energy_spent=atp_allocated * 0.95,
            fractal_chain=resource.fractal_chain if isinstance(resource, ActiveResource) else [],
            context_bound=True
        )

        # Step 7: Distribute reputation (active resources only)
        rep_dist = None
        if isinstance(resource, ActiveResource) and resource.fractal_chain:
            rd = ReputationDistribution()
            rep_dist = rd.distribute(adp.amount, resource.fractal_chain)

        # Step 8: Calculate tensor updates
        t3_updates = self._calculate_t3_updates(quality, confidence)
        v3_generated = self._calculate_v3(quality, atp_allocated, adp.amount)

        result = Result(
            status="success",
            output={"quality": quality},
            metrics={"actual_atp": adp.amount, "confidence": confidence, "quality_score": quality},
            t3_updates=t3_updates,
            v3_generated=v3_generated,
            adp_proof=adp,
            reputation_distribution=rep_dist
        )
        self.actions.append({"request": request.intent, "result": result.status})
        return result

    def _calculate_t3_updates(self, quality: float, confidence: float) -> Dict[str, float]:
        if quality > 0.9:
            return {"talent": 0.02, "training": 0.01, "temperament": 0.01}
        elif quality > 0.7:
            return {"talent": 0.0, "training": 0.005, "temperament": 0.005}
        else:
            return {"talent": -0.01, "training": 0.0, "temperament": -0.02}

    def _calculate_v3(self, quality: float, atp_expected: float, atp_earned: float) -> Dict[str, float]:
        valuation = (atp_earned / max(atp_expected, 0.01)) * quality
        veracity = quality
        validity = 1.0 if quality > 0.5 else 0.0
        return {"valuation": valuation, "veracity": veracity, "validity": validity}


# ─────────────────────────────────────────────
# Part 2: T3 Tensor System
# ─────────────────────────────────────────────

@dataclass
class T3Tensor:
    """Three dimensions of trust"""
    talent: float = 0.5       # Inherent capability (high stability, slow growth)
    training: float = 0.5     # Acquired expertise (medium stability, steady growth)
    temperament: float = 0.5  # Behavioral reliability (high stability, quick drop on violation)

    def clamp(self):
        self.talent = max(0.0, min(1.0, self.talent))
        self.training = max(0.0, min(1.0, self.training))
        self.temperament = max(0.0, min(1.0, self.temperament))
        return self

    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def vector(self) -> List[float]:
        return [self.talent, self.training, self.temperament]

# Performance-based T3 update deltas from spec table
T3_DELTAS = {
    "novel_success":     {"talent": (0.02, 0.05), "training": (0.01, 0.02), "temperament": (0.01, 0.01)},
    "standard_success":  {"talent": (0.0, 0.0),   "training": (0.005, 0.01), "temperament": (0.005, 0.005)},
    "learning":          {"talent": (0.01, 0.01),  "training": (0.02, 0.02), "temperament": (0.0, 0.0)},
    "expected_failure":  {"talent": (-0.01, -0.01), "training": (0.0, 0.0),  "temperament": (0.0, 0.0)},
    "unexpected_failure":{"talent": (-0.02, -0.02), "training": (-0.01, -0.01), "temperament": (-0.02, -0.02)},
    "ethics_violation":  {"talent": (-0.05, -0.05), "training": (0.0, 0.0),  "temperament": (-0.10, -0.10)},
    "timeout_abandon":   {"talent": (0.0, 0.0),    "training": (-0.005, -0.005), "temperament": (-0.01, -0.01)},
}

def apply_t3_delta(t3: T3Tensor, outcome: str, intensity: float = 0.5) -> T3Tensor:
    """Apply performance-based T3 update using spec table deltas"""
    if outcome not in T3_DELTAS:
        return t3
    deltas = T3_DELTAS[outcome]
    for dim in ["talent", "training", "temperament"]:
        lo, hi = deltas[dim]
        delta = lo + (hi - lo) * intensity
        setattr(t3, dim, getattr(t3, dim) + delta)
    return t3.clamp()

@dataclass
class ContextualT3:
    """Domain-specific T3 tracking"""
    domain: str
    tensor: T3Tensor
    action_count: int = 0
    last_update: str = ""

class T3DecayCalculator:
    """Monthly decay calculation per spec §T3 Decay"""

    @staticmethod
    def calculate_decay(months_inactive: float, has_bad_history: bool = False) -> Dict[str, float]:
        training_decay = min(0.001 * months_inactive, 0.1)  # Max 10% decay
        temperament_recovery = min(0.01 * months_inactive, 0.05) if has_bad_history else 0.0
        return {
            "talent": 0.0,  # No decay — inherent capability
            "training": -training_decay,
            "temperament": temperament_recovery
        }

    @staticmethod
    def apply_decay(t3: T3Tensor, months_inactive: float, has_bad_history: bool = False) -> T3Tensor:
        decay = T3DecayCalculator.calculate_decay(months_inactive, has_bad_history)
        t3.talent += decay["talent"]
        t3.training += decay["training"]
        t3.temperament += decay["temperament"]
        return t3.clamp()


# ─────────────────────────────────────────────
# Part 3: V3 Tensor System
# ─────────────────────────────────────────────

@dataclass
class V3Tensor:
    """Three dimensions of value"""
    valuation: float = 0.5    # Subjective worth (can exceed 1.0)
    veracity: float = 0.5     # Objective accuracy [0,1]
    validity: float = 0.5     # Confirmed transfer [0,1] binary per transaction

@dataclass
class ActionResult:
    """Input for V3 calculation"""
    atp_earned: float
    atp_expected: float
    recipient_satisfaction: float = 0.8
    verified_outputs: int = 1
    total_outputs: int = 1
    witness_confidence: float = 0.9
    delivered: bool = True

def calculate_v3(result: ActionResult) -> V3Tensor:
    """Per-action V3 calculation per spec §V3 Calculation"""
    valuation = (result.atp_earned / max(result.atp_expected, 0.01)) * result.recipient_satisfaction
    veracity = (result.verified_outputs / max(result.total_outputs, 1)) * result.witness_confidence
    validity = 1.0 if result.delivered else 0.0
    return V3Tensor(valuation=valuation, veracity=veracity, validity=validity)

@dataclass
class V3Aggregate:
    """Aggregate V3 tracking over time"""
    total_value_atp: float = 0.0
    transaction_count: int = 0
    sum_valuation: float = 0.0
    sum_veracity: float = 0.0
    successful_deliveries: int = 0

    def record(self, v3: V3Tensor, atp: float):
        self.total_value_atp += atp
        self.transaction_count += 1
        self.sum_valuation += v3.valuation
        self.sum_veracity += v3.veracity
        if v3.validity >= 1.0:
            self.successful_deliveries += 1

    def average_valuation(self) -> float:
        return self.sum_valuation / max(self.transaction_count, 1)

    def veracity_score(self) -> float:
        return self.sum_veracity / max(self.transaction_count, 1)

    def validity_rate(self) -> float:
        return self.successful_deliveries / max(self.transaction_count, 1)


# ─────────────────────────────────────────────
# Part 4: Tensor Interactions
# ─────────────────────────────────────────────

def predict_v3_from_t3(t3: T3Tensor) -> Dict[str, float]:
    """T3→V3 influence per spec §T3→V3"""
    valuation_boost = t3.talent * 0.2
    veracity_base = 0.5 + (t3.training * 0.5)
    validity_probability = 0.7 + (t3.temperament * 0.3)
    return {
        "expected_valuation": 0.8 + valuation_boost,
        "expected_veracity": veracity_base,
        "expected_validity": validity_probability
    }

def update_t3_from_v3(t3: T3Tensor, v3: V3Tensor) -> Dict[str, float]:
    """V3→T3 feedback per spec §V3→T3"""
    updates = {}
    # Exceptional valuation indicates talent
    if v3.valuation > 1.2:
        updates["talent"] = 0.02
    # High veracity validates training
    if v3.veracity > 0.95:
        updates["training"] = 0.01
    # Perfect validity reinforces temperament
    if v3.validity == 1.0:
        updates["temperament"] = 0.005
    # Poor performance decreases
    if v3.valuation < 0.5:
        updates["talent"] = updates.get("talent", 0.0) - 0.01
    if v3.veracity < 0.7:
        updates["training"] = updates.get("training", 0.0) - 0.01
    if v3.validity < 1.0:
        updates["temperament"] = updates.get("temperament", 0.0) - 0.02
    return updates

def apply_v3_feedback(t3: T3Tensor, v3: V3Tensor) -> T3Tensor:
    """Apply V3→T3 updates"""
    updates = update_t3_from_v3(t3, v3)
    for dim, delta in updates.items():
        setattr(t3, dim, getattr(t3, dim) + delta)
    return t3.clamp()


# ─────────────────────────────────────────────
# Part 5: Practical Applications
# ─────────────────────────────────────────────

@dataclass
class RoleRequirements:
    """Requirements for a role"""
    min_talent: float = 0.0
    min_training: float = 0.0
    min_temperament: float = 0.0
    talent_weight: float = 0.33
    training_weight: float = 0.34
    temperament_weight: float = 0.33

def match_entity_to_role(t3: T3Tensor, req: RoleRequirements) -> Dict[str, Any]:
    """Role matching with tensors per spec §Role Matching"""
    talent_ok = t3.talent >= req.min_talent
    training_ok = t3.training >= req.min_training
    temperament_ok = t3.temperament >= req.min_temperament
    score = (req.talent_weight * t3.talent +
             req.training_weight * t3.training +
             req.temperament_weight * t3.temperament)
    gaps = {}
    if not talent_ok:
        gaps["talent"] = req.min_talent - t3.talent
    if not training_ok:
        gaps["training"] = req.min_training - t3.training
    if not temperament_ok:
        gaps["temperament"] = req.min_temperament - t3.temperament
    return {
        "qualified": talent_ok and training_ok and temperament_ok,
        "match_score": score,
        "gaps": gaps
    }

def calculate_atp_price(base_cost: float, t3: T3Tensor, v3_avg_valuation: float,
                        complexity: float) -> float:
    """ATP pricing with tensors per spec §ATP Pricing"""
    t3_multiplier = 1 + (t3.talent * 0.3 + t3.training * 0.2 + t3.temperament * 0.1)
    v3_multiplier = v3_avg_valuation
    complexity_multiplier = 1 + (complexity * 0.5)
    return base_cost * t3_multiplier * v3_multiplier * complexity_multiplier

@dataclass
class TeamMember:
    """Entity available for team composition"""
    entity_id: str
    t3: T3Tensor
    domains: Dict[str, T3Tensor] = field(default_factory=dict)

def optimize_team(available: List[TeamMember], capabilities: List[str]) -> Dict[str, Any]:
    """Team composition optimization per spec §Team Composition"""
    team = []
    for cap in capabilities:
        best = max(available, key=lambda e: (
            e.domains[cap].composite() if cap in e.domains else e.t3.composite()
        ))
        team.append({"entity": best.entity_id, "role": cap,
                      "confidence": best.domains.get(cap, best.t3).composite()})
    # Aggregate team tensors
    if team:
        avg_t = sum(m["confidence"] for m in team) / len(team)
    else:
        avg_t = 0.0
    return {"team": team, "team_confidence": avg_t}


# ─────────────────────────────────────────────
# Part 6: Implementation Guidelines
# ─────────────────────────────────────────────

class TensorStore:
    """In-memory tensor storage (models SQL schema from spec §Storage)"""

    def __init__(self):
        self.t3_global: Dict[str, T3Tensor] = {}
        self.t3_contextual: Dict[Tuple[str, str], ContextualT3] = {}
        self.v3_history: List[Dict] = []

    def set_t3(self, lct_id: str, t3: T3Tensor):
        self.t3_global[lct_id] = t3

    def get_t3(self, lct_id: str) -> Optional[T3Tensor]:
        return self.t3_global.get(lct_id)

    def set_contextual_t3(self, lct_id: str, domain: str, t3: T3Tensor, count: int = 0):
        self.t3_contextual[(lct_id, domain)] = ContextualT3(domain=domain, tensor=t3, action_count=count)

    def get_contextual_t3(self, lct_id: str, domain: str) -> Optional[ContextualT3]:
        return self.t3_contextual.get((lct_id, domain))

    def record_v3(self, action_id: str, lct_id: str, v3: V3Tensor, atp: float):
        self.v3_history.append({
            "action_id": action_id,
            "lct_id": lct_id,
            "valuation": v3.valuation,
            "veracity": v3.veracity,
            "validity": v3.validity,
            "atp_generated": atp
        })

class TensorManager:
    """Update triggers per spec §Update Triggers"""

    def __init__(self, store: TensorStore):
        self.store = store

    def on_r6_complete(self, performer_lct: str, result: Result):
        t3 = self.store.get_t3(performer_lct)
        if not t3:
            return
        # Apply T3 updates
        for dim, delta in result.t3_updates.items():
            setattr(t3, dim, getattr(t3, dim) + delta)
        t3.clamp()
        # Record V3
        if result.v3_generated:
            v3 = V3Tensor(**result.v3_generated)
            self.store.record_v3(f"v3:{performer_lct}", performer_lct, v3,
                                 result.metrics.get("actual_atp", 0.0))

class TensorPrivacy:
    """Privacy levels per spec §Privacy Considerations"""

    FULL = "full"       # bound/paired
    CONTEXTUAL = "contextual"  # witnessing
    PUBLIC = "public"   # default

    def __init__(self, store: TensorStore):
        self.store = store
        self.relationships: Dict[Tuple[str, str], str] = {}

    def set_relationship(self, a: str, b: str, rel_type: str):
        self.relationships[(a, b)] = rel_type
        self.relationships[(b, a)] = rel_type

    def get_visible_tensors(self, requester: str, target: str) -> Dict[str, Any]:
        rel = self.relationships.get((requester, target), "none")
        t3 = self.store.get_t3(target) or T3Tensor()
        if rel in ("bound", "paired"):
            return {"t3": {"talent": t3.talent, "training": t3.training,
                           "temperament": t3.temperament}, "level": self.FULL}
        elif rel == "witnessing":
            return {"t3": {"composite": t3.composite()}, "level": self.CONTEXTUAL}
        else:
            return {"t3": {"composite": round(t3.composite(), 1)}, "level": self.PUBLIC}


# ─────────────────────────────────────────────
# Part 7: Advanced Patterns
# ─────────────────────────────────────────────

def predict_tensor_evolution(t3: T3Tensor, planned_actions: List[str]) -> Dict[str, Any]:
    """Tensor prediction per spec §Tensor Prediction"""
    current = T3Tensor(t3.talent, t3.training, t3.temperament)
    for action in planned_actions:
        success_prob = current.composite()
        if success_prob > 0.5:
            current = apply_t3_delta(current, "standard_success", 0.5)
        else:
            current = apply_t3_delta(current, "expected_failure", 0.5)
    return {"predicted_t3": current, "actions_modeled": len(planned_actions)}

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity for tensor comparison"""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

def analyze_tensor_correlations(entities: List[Tuple[str, T3Tensor]]) -> Dict[str, float]:
    """Cross-entity tensor correlation per spec §Cross-Entity Correlation"""
    correlations = {}
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            id_a, t3_a = entities[i]
            id_b, t3_b = entities[j]
            sim = cosine_similarity(t3_a.vector(), t3_b.vector())
            correlations[f"{id_a}:{id_b}"] = sim
    return correlations

# ─── Anti-Gaming Properties (from spec §Anti-Gaming) ───

class AntiGamingValidator:
    """Validates anti-gaming properties per spec"""

    @staticmethod
    def reputation_requires_proof(result: Result) -> bool:
        """Cannot claim reputation without ADP"""
        if result.reputation_distribution and not result.adp_proof:
            return False
        return True

    @staticmethod
    def context_bound(adp: ADPProof) -> bool:
        """ADP only updates reputation for THIS transaction"""
        return adp.context_bound

    @staticmethod
    def single_use(used_adps: set, adp: ADPProof) -> bool:
        """ADP can only return to pool once"""
        if adp.transaction_id in used_adps:
            return False
        return True

    @staticmethod
    def energy_conservation(reputation_total: float, adp_amount: float) -> bool:
        """Total reputation ≤ ADP amount"""
        return reputation_total <= adp_amount + 0.001  # Float tolerance

    @staticmethod
    def fractal_verification(entity_lct: str, fractal_chain: List[str]) -> bool:
        """Cannot claim credit for work outside delegation chain"""
        return entity_lct in fractal_chain

# ─── Efficiency Pressure (from spec §Efficiency Pressure) ───

def calculate_efficiency(productive_atp: float, overhead_atp: float) -> Dict[str, float]:
    """Active/Passive distinction creates optimization pressure"""
    total = productive_atp + overhead_atp
    if total == 0:
        return {"efficiency": 0.0, "reputation": 0.0}
    efficiency = productive_atp / total
    reputation = productive_atp  # Only productive work earns reputation
    return {"efficiency": efficiency, "reputation": reputation}


# ═══════════════════════════════════════════════
# TEST SUITE
# ═══════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    # ─── Part 1: R6 Action Framework ───
    print("Part 1: R6 Action Framework")

    # T1: Rules
    rules = Rules(
        applicable=["data_processing", "analysis", "reporting"],
        constraints={"max_atp": 100, "quality_threshold": 0.85},
        requirements={"entity_type": ["human", "ai"], "min_t3": {"talent": 0.6, "training": 0.7, "temperament": 0.8}}
    )
    check("T1.1 Rules allows valid action", rules.allows("analysis"))
    check("T1.2 Rules rejects invalid action", not rules.allows("hacking"))
    t3_good = T3Tensor(0.8, 0.9, 0.95)
    t3_bad = T3Tensor(0.3, 0.4, 0.5)
    check("T1.3 T3 check passes for qualified entity", rules.check_t3(t3_good))
    check("T1.4 T3 check fails for unqualified entity", not rules.check_t3(t3_bad))

    # T2: Role
    role = Role(lct="lct:web4:role:analyst", permissions=["data:read", "compute:execute", "report:write"])
    check("T2.1 Role has permission", role.has_permission("data:read"))
    check("T2.2 Role lacks permission", not role.has_permission("admin:delete"))

    # T3: Request
    req = Request(intent="analyze_user_behavior", parameters={"dataset": "usage_logs"}, priority="normal")
    check("T3.1 Request intent", req.intent == "analyze_user_behavior")
    check("T3.2 Request priority", req.priority == "normal")

    # T4: Reference
    ref = Reference(similar_actions=[
        {"action_id": "r6:1", "similarity": 0.92, "outcome": "success"},
        {"action_id": "r6:2", "similarity": 0.85, "outcome": "success"},
        {"action_id": "r6:3", "similarity": 0.78, "outcome": "failure"},
    ])
    check("T4.1 Success rate", abs(ref.success_rate() - 2/3) < 0.01)
    empty_ref = Reference()
    check("T4.2 Empty reference defaults to 0.5", empty_ref.success_rate() == 0.5)

    # T5: Resources (Active vs Passive)
    active = ActiveResource(atp_required=55, entity_lct="lct:web4:ai:claude",
                            energy_source="compute",
                            fractal_chain=["lct:society", "lct:org", "lct:team", "lct:claude"])
    passive = PassiveResource(atp_required=10, entity_lct="lct:web4:infra:db",
                              purpose="maintenance", utilization_by=["lct:claude"])
    check("T5.1 Active resource is active", active.is_active())
    check("T5.2 Passive resource is not active", not passive.is_active())

    # T6: ADP Proof
    adp = ADPProof(amount=52, transaction_id="r6:tx:abc", transaction_hash="sha256:...",
                   energy_spent=52.0, fractal_chain=["s", "o", "t", "p"], context_bound=True)
    check("T6.1 ADP context bound", adp.context_bound)
    check("T6.2 ADP amount", adp.amount == 52)

    # T7: Reputation Distribution
    rd = ReputationDistribution()
    chain = ["lct:society", "lct:org", "lct:team", "lct:performer"]
    dist = rd.distribute(100.0, chain)
    check("T7.1 Society gets 1%", abs(dist["lct:society"] - 1.0) < 0.01)
    check("T7.2 Org gets 2%", abs(dist["lct:org"] - 2.0) < 0.01)
    check("T7.3 Team gets 7%", abs(dist["lct:team"] - 7.0) < 0.01)
    check("T7.4 Performer gets 90%", abs(dist["lct:performer"] - 90.0) < 0.01)
    total_rep = sum(dist.values())
    check("T7.5 Total reputation == 100", abs(total_rep - 100.0) < 0.01)

    # T8: R6 Lifecycle
    lifecycle = R6ActionLifecycle()
    rules2 = Rules(applicable=["analysis"], constraints={"max_atp": 100},
                   requirements={"min_t3": {"talent": 0.5}})
    role2 = Role(lct="r", permissions=["data:read"])
    req2 = Request(intent="analysis", parameters={})
    ref2 = Reference(similar_actions=[{"outcome": "success"}, {"outcome": "success"}])
    res2 = ActiveResource(atp_required=50, fractal_chain=["s", "o", "t", "p"])
    t3_performer = T3Tensor(0.8, 0.85, 0.9)

    result = lifecycle.execute(rules2, role2, req2, ref2, res2, t3_performer)
    check("T8.1 Successful R6 action", result.status == "success")
    check("T8.2 ADP proof generated", result.adp_proof is not None)
    check("T8.3 T3 updates present", len(result.t3_updates) > 0)
    check("T8.4 V3 generated", len(result.v3_generated) > 0)
    check("T8.5 Reputation distributed", result.reputation_distribution is not None)

    # T9: Confidence calculation
    conf = lifecycle.calculate_confidence(t3_performer, ref2, res2, role2)
    check("T9.1 Confidence > 0.7", conf > 0.7)
    low_t3 = T3Tensor(0.2, 0.2, 0.2)
    low_ref = Reference(similar_actions=[{"outcome": "failure"}, {"outcome": "failure"}])
    conf_low = lifecycle.calculate_confidence(low_t3, low_ref, res2, role2)
    check("T9.2 Low confidence < 0.7", conf_low < 0.7)

    # T10: Rejection paths
    bad_rules = Rules(applicable=["other"], constraints={}, requirements={})
    result_rej = lifecycle.execute(bad_rules, role2, req2, ref2, res2, t3_performer)
    check("T10.1 Action rejected for invalid type", result_rej.status == "rejected")
    check("T10.2 Rejection reason", "not_allowed" in result_rej.output.get("reason", ""))

    # Low T3 rejection
    strict_rules = Rules(applicable=["analysis"], constraints={},
                         requirements={"min_t3": {"talent": 0.99}})
    result_t3 = lifecycle.execute(strict_rules, role2, req2, ref2, res2, t3_performer)
    check("T10.3 T3 below minimum rejected", result_t3.status == "rejected")

    # Low confidence (use rules with no T3 minimum so confidence check is reached)
    rules_no_min = Rules(applicable=["analysis"], constraints={}, requirements={})
    result_low = lifecycle.execute(rules_no_min, role2, req2, low_ref, res2, low_t3)
    check("T10.4 Low confidence action", result_low.status == "low_confidence")

    print()
    # ─── Part 2: T3 Tensor System ───
    print("Part 2: T3 Tensor System")

    # T11: T3 basics
    t3 = T3Tensor(0.75, 0.82, 0.91)
    check("T11.1 T3 talent", t3.talent == 0.75)
    check("T11.2 T3 composite", abs(t3.composite() - (0.75 + 0.82 + 0.91) / 3) < 0.001)
    check("T11.3 T3 vector", t3.vector() == [0.75, 0.82, 0.91])

    # T12: T3 deltas
    t3a = T3Tensor(0.5, 0.5, 0.5)
    apply_t3_delta(t3a, "novel_success", 1.0)
    check("T12.1 Novel success increases talent", t3a.talent > 0.5)
    check("T12.2 Novel success increases training", t3a.training > 0.5)
    check("T12.3 Novel success increases temperament", t3a.temperament > 0.5)

    t3b = T3Tensor(0.5, 0.5, 0.5)
    apply_t3_delta(t3b, "ethics_violation", 1.0)
    check("T12.4 Ethics violation drops talent", t3b.talent < 0.5)
    check("T12.5 Ethics violation drops temperament hard", t3b.temperament <= 0.4)

    t3c = T3Tensor(0.5, 0.5, 0.5)
    apply_t3_delta(t3c, "standard_success", 1.0)
    check("T12.6 Standard success: talent unchanged", t3c.talent == 0.5)
    check("T12.7 Standard success: training increases", t3c.training > 0.5)

    t3d = T3Tensor(0.5, 0.5, 0.5)
    apply_t3_delta(t3d, "timeout_abandon", 1.0)
    check("T12.8 Timeout: training decreases", t3d.training < 0.5)
    check("T12.9 Timeout: temperament decreases", t3d.temperament < 0.5)
    check("T12.10 Timeout: talent unchanged", t3d.talent == 0.5)

    # T13: Clamping
    t3e = T3Tensor(1.5, -0.3, 0.5)
    t3e.clamp()
    check("T13.1 Clamp upper bound", t3e.talent == 1.0)
    check("T13.2 Clamp lower bound", t3e.training == 0.0)
    check("T13.3 Clamp no-op", t3e.temperament == 0.5)

    # T14: Contextual T3
    ctx = ContextualT3(domain="data_analysis", tensor=T3Tensor(0.85, 0.90, 0.95), action_count=145)
    check("T14.1 Contextual domain", ctx.domain == "data_analysis")
    check("T14.2 Contextual tensor talent", ctx.tensor.talent == 0.85)
    check("T14.3 Action count tracked", ctx.action_count == 145)

    # T15: Decay
    decay = T3DecayCalculator.calculate_decay(6.0, False)
    check("T15.1 Talent no decay", decay["talent"] == 0.0)
    check("T15.2 Training decays", decay["training"] < 0)
    check("T15.3 Training max 10%", abs(decay["training"]) <= 0.1)
    check("T15.4 No recovery without bad history", decay["temperament"] == 0.0)

    decay_bad = T3DecayCalculator.calculate_decay(6.0, True)
    check("T15.5 Temperament recovers with bad history", decay_bad["temperament"] > 0)
    check("T15.6 Recovery max 5%", decay_bad["temperament"] <= 0.05)

    t3f = T3Tensor(0.8, 0.8, 0.8)
    T3DecayCalculator.apply_decay(t3f, 12.0, False)
    check("T15.7 Talent unchanged after decay", t3f.talent == 0.8)
    check("T15.8 Training decreased after decay", t3f.training < 0.8)

    # Long inactivity
    decay_long = T3DecayCalculator.calculate_decay(200.0, False)
    check("T15.9 Training decay capped at 0.1", abs(decay_long["training"]) == 0.1)

    print()
    # ─── Part 3: V3 Tensor System ───
    print("Part 3: V3 Tensor System")

    # T16: V3 basics
    v3 = V3Tensor(0.89, 0.94, 0.97)
    check("T16.1 V3 valuation", v3.valuation == 0.89)
    check("T16.2 V3 veracity", v3.veracity == 0.94)
    check("T16.3 V3 validity", v3.validity == 0.97)

    # T17: V3 calculation
    ar = ActionResult(atp_earned=52, atp_expected=55, recipient_satisfaction=0.91,
                      verified_outputs=7, total_outputs=7, witness_confidence=0.95, delivered=True)
    v3_calc = calculate_v3(ar)
    check("T17.1 Valuation = earned/expected * satisfaction",
          abs(v3_calc.valuation - (52/55 * 0.91)) < 0.01)
    check("T17.2 Veracity = verified/total * witness",
          abs(v3_calc.veracity - (7/7 * 0.95)) < 0.01)
    check("T17.3 Validity = 1.0 when delivered", v3_calc.validity == 1.0)

    ar_fail = ActionResult(atp_earned=0, atp_expected=50, delivered=False)
    v3_fail = calculate_v3(ar_fail)
    check("T17.4 Validity = 0.0 when not delivered", v3_fail.validity == 0.0)

    # T18: V3 aggregate
    agg = V3Aggregate()
    agg.record(V3Tensor(0.9, 0.95, 1.0), 50)
    agg.record(V3Tensor(0.8, 0.85, 1.0), 40)
    agg.record(V3Tensor(0.7, 0.75, 0.0), 30)
    check("T18.1 Transaction count", agg.transaction_count == 3)
    check("T18.2 Total value ATP", agg.total_value_atp == 120)
    check("T18.3 Average valuation", abs(agg.average_valuation() - 0.8) < 0.01)
    check("T18.4 Validity rate", abs(agg.validity_rate() - 2/3) < 0.01)
    check("T18.5 Successful deliveries", agg.successful_deliveries == 2)

    print()
    # ─── Part 4: Tensor Interactions ───
    print("Part 4: Tensor Interactions")

    # T19: T3→V3 prediction
    t3_high = T3Tensor(0.9, 0.9, 0.9)
    pred = predict_v3_from_t3(t3_high)
    check("T19.1 High talent → high valuation", pred["expected_valuation"] > 0.9)
    check("T19.2 High training → high veracity", pred["expected_veracity"] > 0.9)
    check("T19.3 High temperament → high validity", pred["expected_validity"] > 0.9)

    t3_low = T3Tensor(0.1, 0.1, 0.1)
    pred_low = predict_v3_from_t3(t3_low)
    check("T19.4 Low talent → lower valuation", pred_low["expected_valuation"] < pred["expected_valuation"])
    check("T19.5 Low training → lower veracity", pred_low["expected_veracity"] < pred["expected_veracity"])

    # T20: V3→T3 feedback
    v3_excellent = V3Tensor(1.5, 0.98, 1.0)
    updates = update_t3_from_v3(T3Tensor(), v3_excellent)
    check("T20.1 Exceptional valuation → talent increase", updates.get("talent", 0) > 0)
    check("T20.2 High veracity → training increase", updates.get("training", 0) > 0)
    check("T20.3 Perfect validity → temperament increase", updates.get("temperament", 0) > 0)

    v3_poor = V3Tensor(0.3, 0.5, 0.0)
    updates_poor = update_t3_from_v3(T3Tensor(), v3_poor)
    check("T20.4 Low valuation → talent decrease", updates_poor.get("talent", 0) < 0)
    check("T20.5 Low veracity → training decrease", updates_poor.get("training", 0) < 0)
    check("T20.6 Failed validity → temperament decrease", updates_poor.get("temperament", 0) < 0)

    # T21: Apply feedback loop
    t3_loop = T3Tensor(0.5, 0.5, 0.5)
    v3_good = V3Tensor(1.3, 0.96, 1.0)
    apply_v3_feedback(t3_loop, v3_good)
    check("T21.1 Feedback increases talent", t3_loop.talent > 0.5)
    check("T21.2 Feedback increases training", t3_loop.training > 0.5)
    check("T21.3 Feedback increases temperament", t3_loop.temperament > 0.5)

    print()
    # ─── Part 5: Practical Applications ───
    print("Part 5: Practical Applications")

    # T22: Role matching
    req_role = RoleRequirements(min_talent=0.6, min_training=0.7, min_temperament=0.8,
                                talent_weight=0.4, training_weight=0.3, temperament_weight=0.3)
    match_good = match_entity_to_role(T3Tensor(0.8, 0.85, 0.9), req_role)
    check("T22.1 Qualified entity", match_good["qualified"])
    check("T22.2 No gaps", len(match_good["gaps"]) == 0)
    check("T22.3 Match score > 0", match_good["match_score"] > 0)

    match_bad = match_entity_to_role(T3Tensor(0.3, 0.4, 0.5), req_role)
    check("T22.4 Unqualified entity", not match_bad["qualified"])
    check("T22.5 Gaps identified", len(match_bad["gaps"]) == 3)
    check("T22.6 Talent gap calculated", abs(match_bad["gaps"]["talent"] - 0.3) < 0.01)

    # T23: ATP pricing
    price = calculate_atp_price(10.0, T3Tensor(0.9, 0.8, 0.7), 0.9, 0.5)
    check("T23.1 Price > base", price > 10.0)
    price_low = calculate_atp_price(10.0, T3Tensor(0.1, 0.1, 0.1), 0.5, 0.0)
    check("T23.2 Low T3/V3 = lower price", price_low < price)
    price_complex = calculate_atp_price(10.0, T3Tensor(0.9, 0.8, 0.7), 0.9, 1.0)
    check("T23.3 Higher complexity = higher price", price_complex > price)

    # T24: Team composition
    members = [
        TeamMember("alice", T3Tensor(0.9, 0.7, 0.8), {"analysis": T3Tensor(0.95, 0.9, 0.85)}),
        TeamMember("bob", T3Tensor(0.6, 0.9, 0.9), {"engineering": T3Tensor(0.65, 0.95, 0.9)}),
        TeamMember("carol", T3Tensor(0.7, 0.8, 0.95), {"design": T3Tensor(0.75, 0.85, 0.98)}),
    ]
    team = optimize_team(members, ["analysis", "engineering", "design"])
    check("T24.1 Team has 3 members", len(team["team"]) == 3)
    check("T24.2 Alice matched to analysis", team["team"][0]["entity"] == "alice")
    check("T24.3 Bob matched to engineering", team["team"][1]["entity"] == "bob")
    check("T24.4 Carol matched to design", team["team"][2]["entity"] == "carol")
    check("T24.5 Team confidence > 0", team["team_confidence"] > 0)

    print()
    # ─── Part 6: Implementation Guidelines ───
    print("Part 6: Implementation Guidelines")

    # T25: TensorStore
    store = TensorStore()
    store.set_t3("alice", T3Tensor(0.8, 0.85, 0.9))
    alice_t3 = store.get_t3("alice")
    check("T25.1 Store T3", alice_t3 is not None)
    check("T25.2 Retrieve T3 talent", alice_t3.talent == 0.8)

    store.set_contextual_t3("alice", "data_analysis", T3Tensor(0.9, 0.95, 0.95), 100)
    ctx_t3 = store.get_contextual_t3("alice", "data_analysis")
    check("T25.3 Contextual T3 stored", ctx_t3 is not None)
    check("T25.4 Contextual domain", ctx_t3.domain == "data_analysis")
    check("T25.5 Action count", ctx_t3.action_count == 100)

    store.record_v3("act:1", "alice", V3Tensor(0.9, 0.95, 1.0), 50)
    check("T25.6 V3 history recorded", len(store.v3_history) == 1)
    check("T25.7 V3 history lct_id", store.v3_history[0]["lct_id"] == "alice")

    # T26: TensorManager
    manager = TensorManager(store)
    result_mgr = Result(status="success", t3_updates={"talent": 0.01, "training": 0.005},
                        v3_generated={"valuation": 0.9, "veracity": 0.95, "validity": 1.0},
                        metrics={"actual_atp": 50})
    manager.on_r6_complete("alice", result_mgr)
    updated = store.get_t3("alice")
    check("T26.1 Manager updated talent", updated.talent > 0.8)
    check("T26.2 Manager updated training", updated.training > 0.85)
    check("T26.3 V3 history grew", len(store.v3_history) == 2)

    # T27: TensorPrivacy
    privacy = TensorPrivacy(store)
    privacy.set_relationship("bob", "alice", "bound")
    privacy.set_relationship("carol", "alice", "witnessing")

    vis_full = privacy.get_visible_tensors("bob", "alice")
    check("T27.1 Bound → full visibility", vis_full["level"] == "full")
    check("T27.2 Full has talent", "talent" in vis_full["t3"])

    vis_ctx = privacy.get_visible_tensors("carol", "alice")
    check("T27.3 Witnessing → contextual", vis_ctx["level"] == "contextual")
    check("T27.4 Contextual has composite", "composite" in vis_ctx["t3"])

    vis_pub = privacy.get_visible_tensors("unknown", "alice")
    check("T27.5 Unknown → public", vis_pub["level"] == "public")
    check("T27.6 Public has composite only", "composite" in vis_pub["t3"])
    check("T27.7 Public lacks talent", "talent" not in vis_pub["t3"])

    print()
    # ─── Part 7: Advanced Patterns ───
    print("Part 7: Advanced Patterns")

    # T28: Tensor prediction
    t3_pred = T3Tensor(0.6, 0.6, 0.6)
    pred_result = predict_tensor_evolution(t3_pred, ["action1", "action2", "action3"])
    check("T28.1 Prediction returns T3", "predicted_t3" in pred_result)
    check("T28.2 Actions modeled", pred_result["actions_modeled"] == 3)
    check("T28.3 Training improved (standard success)", pred_result["predicted_t3"].training > 0.6)

    # T29: Cross-entity correlation
    entities = [
        ("alice", T3Tensor(0.9, 0.9, 0.9)),
        ("bob", T3Tensor(0.9, 0.85, 0.9)),
        ("carol", T3Tensor(0.1, 0.1, 0.1)),
    ]
    corrs = analyze_tensor_correlations(entities)
    check("T29.1 3 entities → 3 pairs", len(corrs) == 3)
    check("T29.2 Similar entities high correlation", corrs["alice:bob"] > 0.99)
    check("T29.3 Dissimilar entities same direction (cos sim = 1.0 for parallel vectors)",
          corrs["alice:carol"] > 0.9)  # Same direction (all positive), different magnitude

    # T30: Anti-gaming validation
    agv = AntiGamingValidator()

    # Reputation requires proof
    result_with_rep = Result(status="success",
                             reputation_distribution={"p": 90},
                             adp_proof=ADPProof(100, "tx1", "h1", 100.0))
    check("T30.1 Reputation with ADP = valid", agv.reputation_requires_proof(result_with_rep))

    result_no_adp = Result(status="success", reputation_distribution={"p": 90}, adp_proof=None)
    check("T30.2 Reputation without ADP = invalid", not agv.reputation_requires_proof(result_no_adp))

    # Context bound
    adp_bound = ADPProof(50, "tx2", "h2", 50.0, context_bound=True)
    check("T30.3 ADP is context-bound", agv.context_bound(adp_bound))

    # Single use
    used = {"tx_old"}
    check("T30.4 New ADP is single-use", agv.single_use(used, ADPProof(50, "tx_new", "h", 50.0)))
    check("T30.5 Reused ADP rejected", not agv.single_use(used, ADPProof(50, "tx_old", "h", 50.0)))

    # Energy conservation
    check("T30.6 Total rep ≤ ADP", agv.energy_conservation(100.0, 100.0))
    check("T30.7 Total rep > ADP rejected", not agv.energy_conservation(101.0, 100.0))

    # Fractal verification
    chain = ["society", "org", "team", "performer"]
    check("T30.8 Entity in chain = valid", agv.fractal_verification("performer", chain))
    check("T30.9 Entity not in chain = invalid", not agv.fractal_verification("outsider", chain))

    # T31: Efficiency pressure
    eff_good = calculate_efficiency(900, 100)
    check("T31.1 Efficient actor: 90%", abs(eff_good["efficiency"] - 0.9) < 0.01)
    check("T31.2 Efficient reputation = 900", eff_good["reputation"] == 900)

    eff_bad = calculate_efficiency(400, 600)
    check("T31.3 Inefficient actor: 40%", abs(eff_bad["efficiency"] - 0.4) < 0.01)
    check("T31.4 Inefficient reputation = 400", eff_bad["reputation"] == 400)

    eff_zero = calculate_efficiency(0, 0)
    check("T31.5 Zero ATP = zero efficiency", eff_zero["efficiency"] == 0.0)

    # T32: Cosine similarity
    check("T32.1 Identical vectors = 1.0", abs(cosine_similarity([1, 1, 1], [1, 1, 1]) - 1.0) < 0.001)
    check("T32.2 Orthogonal vectors = 0.0", abs(cosine_similarity([1, 0, 0], [0, 1, 0])) < 0.001)
    check("T32.3 Zero vector = 0.0", cosine_similarity([0, 0, 0], [1, 1, 1]) == 0.0)

    # T33: Full R6 lifecycle with energy flow
    print()
    print("Integration: Full R6 lifecycle with energy flow")
    lc = R6ActionLifecycle()
    full_rules = Rules(applicable=["analyze"], constraints={"max_atp": 200},
                       requirements={"min_t3": {"talent": 0.5}})
    full_role = Role(lct="analyst", permissions=["data:read"])
    full_req = Request(intent="analyze", parameters={})
    full_ref = Reference(similar_actions=[{"outcome": "success"}] * 5)
    full_res = ActiveResource(atp_required=100, fractal_chain=["soc", "org", "team", "me"])
    full_t3 = T3Tensor(0.8, 0.9, 0.95)

    full_result = lc.execute(full_rules, full_role, full_req, full_ref, full_res, full_t3)
    check("T33.1 Full lifecycle succeeds", full_result.status == "success")
    check("T33.2 ADP generated", full_result.adp_proof is not None)
    check("T33.3 ADP context-bound", full_result.adp_proof.context_bound)
    check("T33.4 Reputation distributed", full_result.reputation_distribution is not None)
    check("T33.5 Energy conserved",
          sum(full_result.reputation_distribution.values()) <= full_result.adp_proof.amount + 0.01)

    # Verify passive resource has no reputation
    passive_res = PassiveResource(atp_required=10, purpose="maintenance")
    passive_result = lc.execute(full_rules, full_role, full_req, full_ref, passive_res, full_t3)
    check("T33.6 Passive resource: no reputation distribution", passive_result.reputation_distribution is None)

    # T34: All 7 outcome types exercised
    print()
    print("Integration: All T3 delta outcome types")
    for outcome_name in T3_DELTAS:
        t3_test = T3Tensor(0.5, 0.5, 0.5)
        apply_t3_delta(t3_test, outcome_name, 0.5)
        changed = t3_test.talent != 0.5 or t3_test.training != 0.5 or t3_test.temperament != 0.5
        # learning has talent delta (+0.01) and training delta (+0.02) so it always changes
        # standard_success: talent 0 so talent unchanged, but training changes
        check(f"T34.{list(T3_DELTAS.keys()).index(outcome_name)+1} {outcome_name} modifies tensor", changed)

    # ─── Summary ───
    print()
    print("=" * 60)
    if failed == 0:
        print(f"R6 Tensor Guide: {passed}/{total} checks passed")
        print("  All checks passed!")
    else:
        print(f"R6 Tensor Guide: {passed}/{total} checks passed, {failed} FAILED")
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    run_tests()
