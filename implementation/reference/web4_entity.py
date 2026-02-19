"""
Web4 Entity — Fractal DNA Reference Implementation
=====================================================

The Web4 equation describes the CELL, not the system:

    Entity = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP

Each entity is a living operational loop with:
- Its own LCT (identity, witnessed presence)
- Its own T3/V3 (trust/value tensors, evolving)
- Its own MRH (context, relationships)
- Its own ATP/ADP (metabolic budget)
- Its own PolicyGate (conscience checkpoint)
- Its own metabolic states (WAKE/FOCUS/REST/DREAM/CRISIS)

The system is what emerges when cells interact.

This implements the fractal DNA blueprint: the same pattern at every
scale, from a single sensor to a planetary federation.

Date: 2026-02-19
Insight source: private-context/insights/fractal-dna-blueprint-2026-02-19.md
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, List, Any, Callable


# ═══════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════

class EntityType(str, Enum):
    """Web4 entity types (15 canonical types)."""
    HUMAN = "human"
    AI = "ai"
    SOCIETY = "society"
    ORGANIZATION = "organization"
    ROLE = "role"
    TASK = "task"
    RESOURCE = "resource"
    DEVICE = "device"
    SERVICE = "service"
    ORACLE = "oracle"
    ACCUMULATOR = "accumulator"
    DICTIONARY = "dictionary"
    HYBRID = "hybrid"
    POLICY = "policy"
    INFRASTRUCTURE = "infrastructure"


class MetabolicState(str, Enum):
    """Entity metabolic states (bio-inspired)."""
    WAKE = "wake"         # Normal operation, 60s heartbeat
    FOCUS = "focus"       # Intensive processing, increased ATP burn
    REST = "rest"         # Reduced activity, 300s heartbeat
    DREAM = "dream"       # Consolidation/learning, 1800s heartbeat
    CRISIS = "crisis"     # Emergency mode, policy constraints relaxed


class R6Decision(str, Enum):
    """R6 action outcomes."""
    APPROVED = "approved"
    DENIED = "denied"
    DEFERRED = "deferred"


# ═══════════════════════════════════════════════════════════════
# Trust/Value Tensors — Canonical 3-root dimensions
# ═══════════════════════════════════════════════════════════════

@dataclass
class T3Tensor:
    """
    Trust Tensor: 3 root dimensions per CLAUDE.md spec.
    Each is a root node in an open-ended RDF sub-graph
    via web4:subDimensionOf.
    """
    talent: float = 0.5       # Competence, skill, capability
    training: float = 0.5     # Learning quality, data quality, experience
    temperament: float = 0.5  # Behavioral stability, consistency, reliability

    def composite(self) -> float:
        """Weighted composite trust score."""
        return (self.talent * 0.4 + self.training * 0.3 + self.temperament * 0.3)

    def update_from_outcome(self, success: bool, quality: float = 0.5):
        """Update tensor from action outcome."""
        alpha = 0.1  # Learning rate
        target = quality if success else max(0.0, quality - 0.2)

        self.talent = self.talent + alpha * (target - self.talent)
        self.training = self.training + alpha * (0.7 if success else 0.3 - self.training)
        self.temperament = self.temperament + alpha * (0.8 if success else 0.4 - self.temperament)

        # Clamp to [0, 1]
        self.talent = max(0.0, min(1.0, self.talent))
        self.training = max(0.0, min(1.0, self.training))
        self.temperament = max(0.0, min(1.0, self.temperament))

    def to_dict(self) -> dict:
        return {"talent": self.talent, "training": self.training,
                "temperament": self.temperament, "composite": self.composite()}


@dataclass
class V3Tensor:
    """
    Value Tensor: 3 root dimensions per CLAUDE.md spec.
    Tracks the value an entity produces and its verification.
    """
    valuation: float = 0.0    # Economic/utility value created
    veracity: float = 0.5     # Truthfulness, accuracy of outputs
    validity: float = 0.5     # Appropriateness, relevance of actions

    def composite(self) -> float:
        return (self.valuation * 0.3 + self.veracity * 0.35 + self.validity * 0.35)

    def update_from_outcome(self, value_created: float, accurate: bool):
        alpha = 0.1
        self.valuation = self.valuation + alpha * (value_created - self.valuation)
        self.veracity = self.veracity + alpha * ((0.8 if accurate else 0.3) - self.veracity)
        self.validity = self.validity + alpha * ((0.7 if accurate else 0.4) - self.validity)

        self.valuation = max(0.0, min(1.0, self.valuation))
        self.veracity = max(0.0, min(1.0, self.veracity))
        self.validity = max(0.0, min(1.0, self.validity))

    def to_dict(self) -> dict:
        return {"valuation": self.valuation, "veracity": self.veracity,
                "validity": self.validity, "composite": self.composite()}


# ═══════════════════════════════════════════════════════════════
# ATP/ADP — Bio-inspired energy metabolism
# ═══════════════════════════════════════════════════════════════

@dataclass
class ATPBudget:
    """
    Entity's metabolic budget. ATP (charged) → ADP (discharged)
    through work. ADP recharged through value creation.
    """
    atp_balance: float = 100.0    # Available energy
    adp_discharged: float = 0.0   # Energy spent (history)
    daily_recharge: float = 50.0  # ATP recharged per cycle
    max_atp: float = 200.0        # Maximum ATP capacity

    def can_afford(self, cost: float) -> bool:
        return self.atp_balance >= cost

    def debit(self, cost: float) -> bool:
        """Discharge ATP → ADP for an action."""
        if not self.can_afford(cost):
            return False
        self.atp_balance -= cost
        self.adp_discharged += cost
        return True

    def recharge(self, amount: float):
        """Recharge ADP → ATP through value creation."""
        actual = min(amount, self.max_atp - self.atp_balance)
        self.atp_balance += actual
        return actual

    def recharge_daily(self):
        """Daily metabolic recharge."""
        return self.recharge(self.daily_recharge)

    @property
    def energy_ratio(self) -> float:
        """ATP / (ATP + ADP) — metabolic health indicator."""
        total = self.atp_balance + self.adp_discharged
        return self.atp_balance / total if total > 0 else 0.5

    def to_dict(self) -> dict:
        return {"atp": self.atp_balance, "adp": self.adp_discharged,
                "energy_ratio": self.energy_ratio}


# ═══════════════════════════════════════════════════════════════
# R6 — Action framework
# ═══════════════════════════════════════════════════════════════

@dataclass
class R6Request:
    """Structured action request (Rules + Role + Request + Reference + Resource → Result)."""
    r6_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    rules: str = ""                      # Which policy applies
    role: str = ""                       # Actor's role
    request: str = ""                    # What they want to do
    reference: str = ""                  # Context (diff, issue, etc.)
    resource_estimate: float = 10.0      # ATP cost estimate
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class R6Result:
    """Structured action result."""
    r6_id: str
    decision: R6Decision
    reason: str = ""
    atp_consumed: float = 0.0
    trust_delta: float = 0.0
    output_hash: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ═══════════════════════════════════════════════════════════════
# PolicyGate — Conscience checkpoint
# ═══════════════════════════════════════════════════════════════

@dataclass
class PolicyGate:
    """
    Conscience checkpoint at the entity boundary.
    Evaluates whether an action should proceed.
    This IS an IRP energy function: lower energy = better policy fit.
    """
    rules: List[Dict[str, Any]] = field(default_factory=list)
    enforce: bool = True
    accountability_frame: str = "normal"   # normal, crisis, audit
    trust_threshold: float = 0.3           # Minimum T3 composite to act

    def evaluate(self, request: R6Request, t3: T3Tensor, atp: ATPBudget) -> R6Decision:
        """
        Evaluate an action request against policy.
        Returns APPROVED, DENIED, or DEFERRED.
        """
        # Check trust threshold
        if t3.composite() < self.trust_threshold:
            return R6Decision.DENIED

        # Check ATP affordability
        if not atp.can_afford(request.resource_estimate):
            return R6Decision.DENIED

        # Check custom rules
        for rule in self.rules:
            pattern = rule.get("pattern", "")
            if pattern and pattern in request.request:
                action = rule.get("action", "deny")
                if action == "deny":
                    return R6Decision.DENIED

        return R6Decision.APPROVED


# ═══════════════════════════════════════════════════════════════
# Witness Record — MRH relationship trace
# ═══════════════════════════════════════════════════════════════

@dataclass
class WitnessRecord:
    """A witnessed event in the entity's MRH."""
    witness_id: str
    event_type: str           # "action", "outcome", "attestation"
    subject_lct: str
    timestamp: str
    data_hash: str
    witness_lct: str = ""     # Who witnessed this


# ═══════════════════════════════════════════════════════════════
# Web4Entity — The Fractal DNA Cell
# ═══════════════════════════════════════════════════════════════

class Web4Entity:
    """
    A Web4 entity: the fractal DNA cell.

    Entity = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP

    This class instantiates the complete Web4 equation as a living
    operational loop. Each entity can:
    - Receive and process R6 action requests
    - Evaluate actions against its PolicyGate
    - Debit ATP for approved actions
    - Update T3/V3 tensors from outcomes
    - Record witness events in its MRH
    - Transition between metabolic states
    - Contain sub-entities (fractal composition)

    The system emerges from entity interactions.
    You don't engineer the mound — you engineer placement rules.
    """

    def __init__(
        self,
        entity_type: EntityType,
        name: str,
        parent: Optional["Web4Entity"] = None,
        atp_allocation: float = 100.0,
    ):
        # === Identity (LCT) ===
        self.entity_type = entity_type
        self.name = name
        self.lct_id = self._generate_lct_id(entity_type, name)
        self.created_at = datetime.now(timezone.utc).isoformat()

        # === Trust / Value (T3/V3) ===
        self.t3 = T3Tensor()
        self.v3 = V3Tensor()

        # === Metabolic Budget (ATP/ADP) ===
        self.atp = ATPBudget(atp_balance=atp_allocation)

        # === PolicyGate (conscience) ===
        self.policy = PolicyGate()

        # === Metabolic State ===
        self.state = MetabolicState.WAKE

        # === MRH (context, relationships, witness history) ===
        self.witnesses: List[WitnessRecord] = []
        self.relationships: Dict[str, str] = {}  # lct_id → relationship_type

        # === Lineage ===
        self.parent_lct: Optional[str] = parent.lct_id if parent else None
        self.children: List["Web4Entity"] = []

        # === Action History ===
        self.action_log: List[R6Result] = []

        # === Effectors (what this entity can do) ===
        self.effectors: Dict[str, Callable] = {}

        # Register with parent if provided
        if parent is not None:
            parent.children.append(self)
            parent.relationships[self.lct_id] = "parent_of"
            self.relationships[parent.lct_id] = "child_of"

    @staticmethod
    def _generate_lct_id(entity_type: EntityType, name: str) -> str:
        """Generate a deterministic LCT ID."""
        raw = f"{entity_type.value}:{name}:{datetime.now(timezone.utc).isoformat()}"
        hash_hex = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"lct:web4:{entity_type.value}:{hash_hex}"

    # ═══════════════════════════════════════════════════════════
    # Core Loop: act() — the IRP step function
    # ═══════════════════════════════════════════════════════════

    def act(self, request: R6Request) -> R6Result:
        """
        Process an R6 action request through the full entity pipeline.

        Pipeline:
        1. PolicyGate evaluation (conscience check)
        2. ATP debit (energy cost)
        3. Execute action (effector dispatch)
        4. Record result (witness)
        5. Update T3/V3 (trust/value evolution)
        6. Check metabolic state transitions

        This IS the IRP step function for this entity.
        """
        # 1. PolicyGate evaluation
        decision = self.policy.evaluate(request, self.t3, self.atp)

        if decision == R6Decision.DENIED:
            result = R6Result(
                r6_id=request.r6_id,
                decision=R6Decision.DENIED,
                reason="PolicyGate denied: insufficient trust or ATP",
                atp_consumed=0.0,
                trust_delta=0.0
            )
            self.action_log.append(result)
            return result

        # 2. ATP debit
        atp_cost = request.resource_estimate
        if not self.atp.debit(atp_cost):
            result = R6Result(
                r6_id=request.r6_id,
                decision=R6Decision.DENIED,
                reason="Insufficient ATP balance",
                atp_consumed=0.0
            )
            self.action_log.append(result)
            return result

        # 3. Execute action (dispatch to effector if registered)
        success = True
        output = None
        if request.request in self.effectors:
            try:
                output = self.effectors[request.request](request)
                success = True
            except Exception as e:
                output = str(e)
                success = False
        else:
            # Default: action succeeds (placeholder for real execution)
            output = f"Executed: {request.request}"

        # 4. Compute output hash
        output_hash = hashlib.sha256(
            json.dumps({"output": str(output), "r6_id": request.r6_id}).encode()
        ).hexdigest()[:16]

        # 5. Update T3/V3 from outcome
        quality = 0.7 if success else 0.3
        self.t3.update_from_outcome(success, quality)
        self.v3.update_from_outcome(
            value_created=quality * 0.8 if success else 0.1,
            accurate=success
        )

        trust_delta = 0.05 if success else -0.1

        # 6. Record witness
        witness = WitnessRecord(
            witness_id=str(uuid.uuid4())[:8],
            event_type="action",
            subject_lct=self.lct_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data_hash=output_hash
        )
        self.witnesses.append(witness)

        # 7. Build result
        result = R6Result(
            r6_id=request.r6_id,
            decision=R6Decision.APPROVED,
            reason=f"Action executed: {request.request}",
            atp_consumed=atp_cost,
            trust_delta=trust_delta,
            output_hash=output_hash
        )
        self.action_log.append(result)

        # 8. Check metabolic state transitions
        self._check_metabolic_state()

        # 9. Recharge ATP proportional to value created
        if success:
            recharge = atp_cost * quality * 0.5  # Partial recharge from value
            self.atp.recharge(recharge)

        return result

    # ═══════════════════════════════════════════════════════════
    # Metabolic State Management
    # ═══════════════════════════════════════════════════════════

    def _check_metabolic_state(self):
        """Transition metabolic state based on energy ratio."""
        ratio = self.atp.energy_ratio
        if ratio < 0.1:
            self.state = MetabolicState.CRISIS
        elif ratio < 0.3:
            self.state = MetabolicState.REST
        elif ratio > 0.8:
            self.state = MetabolicState.FOCUS
        else:
            self.state = MetabolicState.WAKE

    # ═══════════════════════════════════════════════════════════
    # Effector Registration
    # ═══════════════════════════════════════════════════════════

    def register_effector(self, action_name: str, handler: Callable):
        """Register an effector (action handler) for this entity."""
        self.effectors[action_name] = handler

    # ═══════════════════════════════════════════════════════════
    # Witnessing (MRH)
    # ═══════════════════════════════════════════════════════════

    def witness(self, other: "Web4Entity", event_type: str = "observation"):
        """Witness another entity's existence/action."""
        record = WitnessRecord(
            witness_id=str(uuid.uuid4())[:8],
            event_type=event_type,
            subject_lct=other.lct_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data_hash=hashlib.sha256(other.lct_id.encode()).hexdigest()[:16],
            witness_lct=self.lct_id
        )
        self.witnesses.append(record)
        other.witnesses.append(WitnessRecord(
            witness_id=record.witness_id,
            event_type="witnessed_by",
            subject_lct=self.lct_id,
            timestamp=record.timestamp,
            data_hash=record.data_hash,
            witness_lct=self.lct_id
        ))

        # Update relationship
        if other.lct_id not in self.relationships:
            self.relationships[other.lct_id] = "witnessed"
        if self.lct_id not in other.relationships:
            other.relationships[self.lct_id] = "witnessed_by"

    # ═══════════════════════════════════════════════════════════
    # Fractal Composition
    # ═══════════════════════════════════════════════════════════

    def spawn(self, entity_type: EntityType, name: str, atp_share: float = 20.0) -> "Web4Entity":
        """
        Spawn a child entity. Fractal composition: the child
        instantiates the same DNA pattern at a smaller scale.
        ATP is transferred from parent to child.
        """
        if not self.atp.can_afford(atp_share):
            raise ValueError(f"Cannot afford to spawn: need {atp_share} ATP, have {self.atp.atp_balance}")

        child = Web4Entity(
            entity_type=entity_type,
            name=name,
            parent=self,
            atp_allocation=atp_share
        )
        self.atp.debit(atp_share)
        return child

    # ═══════════════════════════════════════════════════════════
    # Introspection
    # ═══════════════════════════════════════════════════════════

    @property
    def coherence(self) -> float:
        """
        Estimated coherence C from trust and value tensors.
        C ≈ 0.7 is the stability threshold (SAGE/Web4/Synchronism convergence).
        """
        t3_c = self.t3.composite()
        v3_c = self.v3.composite()
        energy = self.atp.energy_ratio
        return (t3_c * 0.4 + v3_c * 0.3 + energy * 0.3)

    @property
    def presence_density(self) -> float:
        """
        How 'present' this entity is — function of witness count
        and relationship diversity. Presence accumulates through witnessing.
        """
        witness_count = len(self.witnesses)
        unique_witnesses = len(set(w.witness_lct for w in self.witnesses if w.witness_lct))
        relationship_count = len(self.relationships)

        # Logarithmic scaling — diminishing returns
        import math
        w_score = math.log1p(witness_count) / 10.0
        d_score = math.log1p(unique_witnesses) / 5.0
        r_score = math.log1p(relationship_count) / 5.0

        return min(1.0, (w_score + d_score + r_score) / 3.0)

    def status(self) -> dict:
        """Complete entity status snapshot."""
        return {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "state": self.state.value,
            "t3": self.t3.to_dict(),
            "v3": self.v3.to_dict(),
            "atp": self.atp.to_dict(),
            "coherence": round(self.coherence, 4),
            "presence_density": round(self.presence_density, 4),
            "witnesses": len(self.witnesses),
            "relationships": len(self.relationships),
            "children": len(self.children),
            "actions_taken": len(self.action_log),
            "created_at": self.created_at
        }

    def __repr__(self):
        return (f"Web4Entity({self.entity_type.value}:{self.name}, "
                f"C={self.coherence:.3f}, ATP={self.atp.atp_balance:.1f}, "
                f"state={self.state.value})")


# ═══════════════════════════════════════════════════════════════
# Demo: Fractal DNA in action
# ═══════════════════════════════════════════════════════════════

def demo():
    """
    Demonstrate the fractal DNA pattern: entities at multiple scales,
    all running the same Web4 equation.
    """
    print("=" * 60)
    print("  WEB4 FRACTAL DNA — Reference Implementation")
    print("  'The equation describes the cell, not the system.'")
    print("=" * 60)

    # Level 1: Society entity
    print("\n--- Level 1: Society ---")
    society = Web4Entity(EntityType.SOCIETY, "research-federation", atp_allocation=500.0)
    print(f"  {society}")
    print(f"  Status: {json.dumps(society.status(), indent=2)[:200]}...")

    # Level 2: AI agent spawned by society
    print("\n--- Level 2: AI Agent (spawned by society) ---")
    agent = society.spawn(EntityType.AI, "sage-legion", atp_share=100.0)
    print(f"  {agent}")
    print(f"  Parent: {agent.parent_lct}")

    # Level 3: Task spawned by agent
    print("\n--- Level 3: Task (spawned by agent) ---")
    task = agent.spawn(EntityType.TASK, "analyze-data", atp_share=20.0)
    print(f"  {task}")
    print(f"  Parent: {task.parent_lct}")
    print(f"  Grandparent: {society.lct_id}")

    # Witness chain: society witnesses agent, agent witnesses task
    print("\n--- Witnessing Chain ---")
    society.witness(agent, "creation")
    agent.witness(task, "delegation")
    print(f"  Society witnessed agent: {len(society.witnesses)} records")
    print(f"  Agent witnessed task: {len(agent.witnesses)} records")
    print(f"  Task witnessed by: {len(task.witnesses)} records")

    # Agent performs actions
    print("\n--- Agent Performing Actions ---")
    for i, action_name in enumerate(["fetch_data", "analyze_patterns", "generate_report"]):
        request = R6Request(
            rules="research-policy-v1",
            role=agent.lct_id,
            request=action_name,
            reference=f"dataset-{i+1}",
            resource_estimate=15.0
        )
        result = agent.act(request)
        print(f"  Action {i+1}: {action_name} -> {result.decision.value} "
              f"(ATP: {result.atp_consumed:.1f}, T3: {agent.t3.composite():.3f})")

    # Task performs sub-action
    print("\n--- Task Performing Sub-Action ---")
    sub_request = R6Request(
        rules="task-policy-v1",
        role=task.lct_id,
        request="compute_statistics",
        resource_estimate=5.0
    )
    sub_result = task.act(sub_request)
    print(f"  Sub-action: compute_statistics -> {sub_result.decision.value}")

    # Show fractal structure
    print("\n--- Fractal Structure ---")
    print(f"  Society:  C={society.coherence:.3f}, ATP={society.atp.atp_balance:.1f}, "
          f"children={len(society.children)}, witnesses={len(society.witnesses)}")
    print(f"  ├── Agent: C={agent.coherence:.3f}, ATP={agent.atp.atp_balance:.1f}, "
          f"children={len(agent.children)}, witnesses={len(agent.witnesses)}")
    print(f"  │   └── Task: C={task.coherence:.3f}, ATP={task.atp.atp_balance:.1f}, "
          f"witnesses={len(task.witnesses)}")

    # Demonstrate policy denial
    print("\n--- PolicyGate Denial ---")
    agent.policy.rules.append({"pattern": "delete_all", "action": "deny"})
    dangerous_request = R6Request(
        rules="research-policy-v1",
        role=agent.lct_id,
        request="delete_all_records",
        resource_estimate=5.0
    )
    denied_result = agent.act(dangerous_request)
    print(f"  Request: delete_all_records -> {denied_result.decision.value}")
    print(f"  Reason: {denied_result.reason}")

    # Demonstrate ATP exhaustion → CRISIS state
    print("\n--- ATP Exhaustion → CRISIS State ---")
    for i in range(10):
        expensive_request = R6Request(
            request=f"expensive_op_{i}",
            resource_estimate=20.0
        )
        result = agent.act(expensive_request)
        if result.decision == R6Decision.DENIED:
            print(f"  Action {i}: DENIED (ATP exhausted)")
            break
    print(f"  Agent state: {agent.state.value}")
    print(f"  Agent ATP: {agent.atp.atp_balance:.1f}")

    # Final status
    print("\n--- Final Entity Status ---")
    for entity in [society, agent, task]:
        s = entity.status()
        print(f"  {s['name']:20s} | C={s['coherence']:.3f} | ATP={s['atp']['atp']:.1f} | "
              f"state={s['state']:7s} | actions={s['actions_taken']} | presence={s['presence_density']:.3f}")

    print("\n" + "=" * 60)
    print("  Each entity runs the SAME equation at its own scale.")
    print("  The system emerges from their interactions.")
    print("  'You don't engineer the mound — you engineer placement rules.'")
    print("=" * 60)


if __name__ == "__main__":
    demo()
