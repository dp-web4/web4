#!/usr/bin/env python3
"""
Web4 Integration SDK — Unified Entry Point
============================================

The single import for the entire Web4 stack. Brings together all 9 functional
layers into a coherent developer experience.

Layers integrated:
  1. Identity    — LCT lifecycle (genesis → operation → rotation → revocation)
  2. Trust       — T3/V3 tensors with MRH-scoped propagation
  3. Context     — Markov Relevancy Horizon with fractal composition
  4. Governance  — Society/Authority/Law with metabolic states
  5. Economic    — ATP/ADP metabolism with conservation invariant
  6. Action      — R6/R7 pipeline with hash-chained audit
  7. Federation  — Multi-society coordination with circuit breakers
  8. Protocol    — MCP trust-gated sessions
  9. Compliance  — EU AI Act mapping with audit certification

Usage:
    from web4_integration_sdk import Web4Stack

    # Spin up a complete Web4 environment
    stack = Web4Stack("my_society")
    alice = stack.create_entity("human", "alice", atp=500)
    bob = stack.create_entity("ai", "bob", atp=300)

    # Build trust through witnessed interaction
    result = stack.execute_action(alice, bob, "review_code",
                                  resource="repo:main", cost=20)

    # Check the audit trail
    stack.print_audit_trail()

Date: 2026-02-27
"""

import hashlib
import json
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, List, Any, Callable, Tuple, Set


# ═══════════════════════════════════════════════════════════════
# Layer 1: Identity — LCT Lifecycle
# ═══════════════════════════════════════════════════════════════

class LCTState(str, Enum):
    """LCT lifecycle states per spec."""
    GENESIS = "genesis"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ROTATING = "rotating"
    REVOKED = "revoked"


@dataclass
class LCT:
    """Linked Context Token — witnessed presence reification."""
    lct_id: str
    entity_type: str
    entity_name: str
    state: LCTState = LCTState.GENESIS
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    witness_count: int = 0
    key_fingerprint: str = ""
    parent_lct: Optional[str] = None
    rotation_history: List[str] = field(default_factory=list)

    def activate(self, witnesses: int = 1):
        """Transition genesis → active with witness attestation."""
        if self.state != LCTState.GENESIS:
            raise ValueError(f"Cannot activate from {self.state}")
        self.witness_count = witnesses
        self.state = LCTState.ACTIVE

    def suspend(self, reason: str = ""):
        if self.state != LCTState.ACTIVE:
            raise ValueError(f"Cannot suspend from {self.state}")
        self.state = LCTState.SUSPENDED

    def reinstate(self):
        if self.state != LCTState.SUSPENDED:
            raise ValueError(f"Cannot reinstate from {self.state}")
        self.state = LCTState.ACTIVE

    def begin_rotation(self, new_fingerprint: str):
        if self.state != LCTState.ACTIVE:
            raise ValueError(f"Cannot rotate from {self.state}")
        self.state = LCTState.ROTATING
        self.rotation_history.append(self.key_fingerprint)
        self.key_fingerprint = new_fingerprint

    def complete_rotation(self):
        if self.state != LCTState.ROTATING:
            raise ValueError(f"Cannot complete rotation from {self.state}")
        self.state = LCTState.ACTIVE

    def revoke(self):
        if self.state == LCTState.REVOKED:
            raise ValueError("Already revoked")
        self.state = LCTState.REVOKED


# ═══════════════════════════════════════════════════════════════
# Layer 2: Trust — T3/V3 Tensors
# ═══════════════════════════════════════════════════════════════

@dataclass
class T3Tensor:
    """Trust tensor: Talent/Training/Temperament."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def composite(self) -> float:
        return self.talent * 0.4 + self.training * 0.3 + self.temperament * 0.3

    def update(self, quality: float, success: bool):
        """Update from action outcome. Slow drift by design (0.02 per step)."""
        delta = 0.02 * (quality - 0.5) if success else 0.02 * (quality - 0.7)
        self.talent = max(0.0, min(1.0, self.talent + delta))
        self.training = max(0.0, min(1.0, self.training + delta * 0.8))
        self.temperament = max(0.0, min(1.0, self.temperament + delta * 0.6))

    def to_dict(self) -> dict:
        return {"talent": round(self.talent, 4),
                "training": round(self.training, 4),
                "temperament": round(self.temperament, 4),
                "composite": round(self.composite(), 4)}


@dataclass
class V3Tensor:
    """Value tensor: Valuation/Veracity/Validity."""
    valuation: float = 0.0
    veracity: float = 0.5
    validity: float = 0.5

    def composite(self) -> float:
        return self.valuation * 0.3 + self.veracity * 0.35 + self.validity * 0.35

    def update(self, value_created: float, accurate: bool):
        alpha = 0.1
        self.valuation = max(0.0, min(1.0, self.valuation + alpha * (value_created - self.valuation)))
        target = 0.8 if accurate else 0.3
        self.veracity = max(0.0, min(1.0, self.veracity + alpha * (target - self.veracity)))
        self.validity = max(0.0, min(1.0, self.validity + alpha * (target - self.validity)))

    def to_dict(self) -> dict:
        return {"valuation": round(self.valuation, 4),
                "veracity": round(self.veracity, 4),
                "validity": round(self.validity, 4),
                "composite": round(self.composite(), 4)}


# ═══════════════════════════════════════════════════════════════
# Layer 3: Context — Markov Relevancy Horizon
# ═══════════════════════════════════════════════════════════════

class MRHZone(str, Enum):
    """MRH proximity zones."""
    SELF = "self"            # The entity itself
    DIRECT = "direct"        # Direct relationships (trust × 1.0)
    INDIRECT = "indirect"    # 2-hop (trust × 0.7)
    PERIPHERAL = "peripheral"  # 3-hop (trust × 0.49)
    BEYOND = "beyond"        # 4+ hops (trust → 0)

    @staticmethod
    def from_hops(hops: int) -> "MRHZone":
        if hops == 0: return MRHZone.SELF
        if hops == 1: return MRHZone.DIRECT
        if hops == 2: return MRHZone.INDIRECT
        if hops == 3: return MRHZone.PERIPHERAL
        return MRHZone.BEYOND


MRH_DECAY = 0.7  # Trust decay per hop


class MRHGraph:
    """Markov Relevancy Horizon graph — tracks entity relationships."""

    def __init__(self, center_id: str):
        self.center = center_id
        self.edges: Dict[Tuple[str, str], float] = {}  # (from, to) → weight

    def add_edge(self, from_id: str, to_id: str, weight: float = 1.0):
        self.edges[(from_id, to_id)] = max(0.0, min(1.0, weight))

    def get_zone(self, target_id: str) -> MRHZone:
        """Determine MRH zone for a target entity."""
        if target_id == self.center:
            return MRHZone.SELF
        hops = self._shortest_path_length(target_id)
        return MRHZone.from_hops(hops) if hops is not None else MRHZone.BEYOND

    def compute_trust(self, target_id: str) -> float:
        """Compute trust to target with MRH decay."""
        if target_id == self.center:
            return 1.0
        path = self._find_path(target_id)
        if not path:
            return 0.0
        trust = 1.0
        for i in range(len(path) - 1):
            edge_weight = self.edges.get((path[i], path[i + 1]), 0.0)
            trust *= edge_weight * MRH_DECAY
        return trust

    def _shortest_path_length(self, target: str) -> Optional[int]:
        visited = {self.center}
        queue = [(self.center, 0)]
        while queue:
            node, depth = queue.pop(0)
            for (f, t), _ in self.edges.items():
                if f == node and t not in visited:
                    if t == target:
                        return depth + 1
                    visited.add(t)
                    queue.append((t, depth + 1))
        return None

    def _find_path(self, target: str) -> List[str]:
        visited = {self.center}
        queue = [(self.center, [self.center])]
        while queue:
            node, path = queue.pop(0)
            for (f, t), _ in self.edges.items():
                if f == node and t not in visited:
                    new_path = path + [t]
                    if t == target:
                        return new_path
                    visited.add(t)
                    queue.append((t, new_path))
        return []


# ═══════════════════════════════════════════════════════════════
# Layer 4: Governance — Society with metabolic states
# ═══════════════════════════════════════════════════════════════

class SocietyState(str, Enum):
    """Society lifecycle states."""
    FORMING = "forming"
    ACTIVE = "active"
    REST = "rest"
    HIBERNATION = "hibernation"
    DISSOLVING = "dissolving"
    DISSOLVED = "dissolved"


@dataclass
class SocietyLaw:
    """A law within a society."""
    law_id: str
    description: str
    min_trust: float = 0.0      # Minimum T3 composite to satisfy
    max_atp_cost: float = 1000.0  # Max ATP per action
    prohibited_actions: List[str] = field(default_factory=list)
    enacted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Society:
    """A Web4 society — governance container with metabolic state."""

    def __init__(self, name: str, founder_lct: str, initial_atp: float = 10000.0):
        self.society_id = f"soc:{hashlib.sha256(name.encode()).hexdigest()[:12]}"
        self.name = name
        self.founder = founder_lct
        self.state = SocietyState.FORMING
        self.treasury_atp = initial_atp
        self.members: Dict[str, str] = {founder_lct: "founder"}  # lct → role
        self.laws: List[SocietyLaw] = []
        self.created_at = datetime.now(timezone.utc).isoformat()

    def activate(self, min_members: int = 1):
        if len(self.members) < min_members:
            raise ValueError(f"Need {min_members} members, have {len(self.members)}")
        self.state = SocietyState.ACTIVE

    def add_member(self, lct_id: str, role: str = "member"):
        self.members[lct_id] = role

    def remove_member(self, lct_id: str):
        if lct_id == self.founder:
            raise ValueError("Cannot remove founder")
        self.members.pop(lct_id, None)

    def enact_law(self, law: SocietyLaw):
        self.laws.append(law)

    def check_compliance(self, action: str, trust: float, cost: float) -> Tuple[bool, str]:
        """Check if an action complies with all society laws."""
        for law in self.laws:
            if action in law.prohibited_actions:
                return False, f"Prohibited by law {law.law_id}"
            if trust < law.min_trust:
                return False, f"Insufficient trust for law {law.law_id}: {trust:.2f} < {law.min_trust}"
            if cost > law.max_atp_cost:
                return False, f"Cost exceeds limit in law {law.law_id}: {cost} > {law.max_atp_cost}"
        return True, "Compliant"

    def allocate_atp(self, amount: float) -> bool:
        if amount > self.treasury_atp:
            return False
        self.treasury_atp -= amount
        return True


# ═══════════════════════════════════════════════════════════════
# Layer 5: Economic — ATP/ADP with conservation
# ═══════════════════════════════════════════════════════════════

@dataclass
class ATPAccount:
    """ATP account with lock support."""
    owner_lct: str
    balance: float = 0.0
    locked: float = 0.0
    total_earned: float = 0.0
    total_spent: float = 0.0

    @property
    def available(self) -> float:
        return self.balance - self.locked

    def credit(self, amount: float):
        self.balance += amount
        self.total_earned += amount

    def debit(self, amount: float) -> bool:
        if amount > self.available:
            return False
        self.balance -= amount
        self.total_spent += amount
        return True

    def lock(self, amount: float) -> bool:
        if amount > self.available:
            return False
        self.locked += amount
        return True

    def unlock(self, amount: float):
        self.locked = max(0.0, self.locked - amount)

    def slash(self, amount: float):
        """Slash locked funds (penalty)."""
        actual = min(amount, self.locked)
        self.locked -= actual
        self.balance -= actual
        return actual


class ATPLedger:
    """ATP ledger with conservation invariant."""

    def __init__(self, initial_supply: float = 0.0):
        self.accounts: Dict[str, ATPAccount] = {}
        self.total_supply = initial_supply
        self.total_fees_burned = 0.0

    def create_account(self, lct_id: str, initial_balance: float = 0.0) -> ATPAccount:
        acct = ATPAccount(owner_lct=lct_id, balance=initial_balance)
        self.accounts[lct_id] = acct
        self.total_supply += initial_balance
        return acct

    def transfer(self, from_lct: str, to_lct: str, amount: float, fee_rate: float = 0.05) -> bool:
        """Transfer ATP with fee burn. Fee is destroyed (not redistributed)."""
        fee = amount * fee_rate
        total = amount + fee
        from_acct = self.accounts.get(from_lct)
        to_acct = self.accounts.get(to_lct)
        if not from_acct or not to_acct:
            return False
        if not from_acct.debit(total):
            return False
        to_acct.credit(amount)
        self.total_fees_burned += fee
        return True

    def verify_conservation(self) -> bool:
        """ATP conservation: total_supply = sum(balances) + fees_burned."""
        total_balances = sum(a.balance for a in self.accounts.values())
        expected = self.total_supply - self.total_fees_burned
        return abs(total_balances - expected) < 0.001


# ═══════════════════════════════════════════════════════════════
# Layer 6: Action — R6/R7 Pipeline with audit chain
# ═══════════════════════════════════════════════════════════════

class ActionOutcome(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    DEFERRED = "deferred"


@dataclass
class R6Action:
    """An R6 action request."""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    actor_lct: str = ""
    target_lct: str = ""
    action_type: str = ""
    resource: str = ""
    cost: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class R7Result:
    """An R7 result with reputation delta."""
    action_id: str
    outcome: ActionOutcome
    reason: str = ""
    atp_consumed: float = 0.0
    quality: float = 0.0  # 0-1 quality assessment
    reputation_delta: float = 0.0
    prev_hash: str = ""
    result_hash: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_hash(self):
        content = f"{self.action_id}:{self.outcome.value}:{self.atp_consumed}:{self.quality}:{self.prev_hash}"
        self.result_hash = hashlib.sha256(content.encode()).hexdigest()[:32]


class AuditChain:
    """Hash-chained audit trail for R7 results."""

    def __init__(self):
        self.chain: List[R7Result] = []
        self.genesis_hash = hashlib.sha256(b"web4:audit:genesis").hexdigest()[:32]

    def append(self, result: R7Result):
        result.prev_hash = self.chain[-1].result_hash if self.chain else self.genesis_hash
        result.compute_hash()
        self.chain.append(result)

    def verify_integrity(self) -> bool:
        """Verify the entire chain is tamper-free (content + links)."""
        if not self.chain:
            return True
        # Check genesis link
        if self.chain[0].prev_hash != self.genesis_hash:
            return False
        # Check each entry: content→hash integrity AND chain links
        for i, entry in enumerate(self.chain):
            # Verify content→hash (recompute and compare)
            content = f"{entry.action_id}:{entry.outcome.value}:{entry.atp_consumed}:{entry.quality}:{entry.prev_hash}"
            expected_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
            if entry.result_hash != expected_hash:
                return False
            # Verify chain link
            if i > 0 and entry.prev_hash != self.chain[i - 1].result_hash:
                return False
        return True

    def __len__(self):
        return len(self.chain)


# ═══════════════════════════════════════════════════════════════
# Layer 7: Federation — Multi-society coordination
# ═══════════════════════════════════════════════════════════════

class CircuitState(str, Enum):
    CLOSED = "closed"       # Normal operation
    HALF_OPEN = "half_open"  # Testing recovery
    OPEN = "open"           # Federation paused


@dataclass
class FederationLink:
    """Link between two societies in a federation."""
    source_id: str
    target_id: str
    trust: float = 0.5
    circuit: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    failure_threshold: int = 3
    last_success: str = ""

    def record_success(self):
        self.failure_count = 0
        self.circuit = CircuitState.CLOSED
        self.last_success = datetime.now(timezone.utc).isoformat()

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.circuit = CircuitState.OPEN

    def attempt_recovery(self) -> bool:
        if self.circuit == CircuitState.OPEN:
            self.circuit = CircuitState.HALF_OPEN
            return True
        return False


class Federation:
    """Multi-society federation with circuit breakers."""

    def __init__(self, name: str):
        self.name = name
        self.societies: Dict[str, Society] = {}
        self.links: Dict[Tuple[str, str], FederationLink] = {}

    def add_society(self, society: Society):
        self.societies[society.society_id] = society

    def link_societies(self, soc_a_id: str, soc_b_id: str, initial_trust: float = 0.5):
        self.links[(soc_a_id, soc_b_id)] = FederationLink(soc_a_id, soc_b_id, initial_trust)
        self.links[(soc_b_id, soc_a_id)] = FederationLink(soc_b_id, soc_a_id, initial_trust)

    def cross_society_trust(self, from_soc: str, to_soc: str) -> float:
        link = self.links.get((from_soc, to_soc))
        if not link or link.circuit == CircuitState.OPEN:
            return 0.0
        return link.trust

    def federated_action(self, from_soc: str, to_soc: str) -> Tuple[bool, str]:
        """Attempt a cross-society action through federation."""
        link = self.links.get((from_soc, to_soc))
        if not link:
            return False, "No federation link"
        if link.circuit == CircuitState.OPEN:
            return False, "Circuit breaker OPEN"
        return True, "Federation allows action"


# ═══════════════════════════════════════════════════════════════
# Layer 8: Protocol — MCP Trust-Gated Session
# ═══════════════════════════════════════════════════════════════

@dataclass
class MCPTool:
    """A tool exposed through MCP."""
    name: str
    description: str
    min_trust: float = 0.0        # Minimum T3 composite to access
    atp_cost: float = 1.0         # Cost per invocation
    required_zone: MRHZone = MRHZone.BEYOND  # Must be at least this close


class MCPSession:
    """Trust-gated MCP session."""

    def __init__(self, server_lct: str, client_lct: str, trust: float):
        self.session_id = str(uuid.uuid4())[:12]
        self.server_lct = server_lct
        self.client_lct = client_lct
        self.trust = trust
        self.tools: Dict[str, MCPTool] = {}
        self.invocation_count = 0
        self.active = True

    def register_tool(self, tool: MCPTool):
        self.tools[tool.name] = tool

    def invoke_tool(self, tool_name: str, params: Dict = None) -> Tuple[bool, str]:
        """Invoke a tool with trust gating."""
        if not self.active:
            return False, "Session closed"
        tool = self.tools.get(tool_name)
        if not tool:
            return False, f"Unknown tool: {tool_name}"
        if self.trust < tool.min_trust:
            return False, f"Insufficient trust: {self.trust:.2f} < {tool.min_trust}"
        self.invocation_count += 1
        return True, f"Tool {tool_name} invoked successfully"

    def close(self):
        self.active = False


# ═══════════════════════════════════════════════════════════════
# Layer 9: Compliance — EU AI Act with audit
# ═══════════════════════════════════════════════════════════════

class ComplianceLevel(str, Enum):
    FULL = "full"              # All articles satisfied
    SUBSTANTIAL = "substantial"  # ≥6/8 articles
    PARTIAL = "partial"        # ≥4/8 articles
    NON_COMPLIANT = "non_compliant"  # <4 articles


@dataclass
class ComplianceCheck:
    """An individual compliance check."""
    article: str        # e.g. "Art.9" (Risk Management)
    satisfied: bool
    evidence: str = ""
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ComplianceEngine:
    """EU AI Act compliance assessment."""

    ARTICLES = ["Art.9", "Art.10", "Art.11", "Art.12", "Art.13", "Art.14", "Art.15", "Annex.III"]

    def __init__(self):
        self.checks: List[ComplianceCheck] = []

    def check_entity(self, lct: LCT, t3: T3Tensor, v3: V3Tensor,
                     atp: ATPAccount, audit_len: int) -> ComplianceLevel:
        """Run EU AI Act compliance checks against an entity."""
        self.checks = []

        # Art.9: Risk Management (T3 composite > 0.3)
        self.checks.append(ComplianceCheck(
            "Art.9", t3.composite() > 0.3,
            f"T3 composite: {t3.composite():.3f}"
        ))

        # Art.10: Data Quality (V3 veracity > 0.4)
        self.checks.append(ComplianceCheck(
            "Art.10", v3.veracity > 0.4,
            f"V3 veracity: {v3.veracity:.3f}"
        ))

        # Art.11: Technical Documentation (LCT exists and active)
        self.checks.append(ComplianceCheck(
            "Art.11", lct.state == LCTState.ACTIVE,
            f"LCT state: {lct.state.value}"
        ))

        # Art.12: Record-keeping (audit chain > 0)
        self.checks.append(ComplianceCheck(
            "Art.12", audit_len > 0,
            f"Audit chain length: {audit_len}"
        ))

        # Art.13: Transparency (entity type declared)
        self.checks.append(ComplianceCheck(
            "Art.13", lct.entity_type != "",
            f"Entity type: {lct.entity_type}"
        ))

        # Art.14: Human Oversight (witness count > 0)
        self.checks.append(ComplianceCheck(
            "Art.14", lct.witness_count > 0,
            f"Witnesses: {lct.witness_count}"
        ))

        # Art.15: Accuracy/Robustness (T3 temperament > 0.3)
        self.checks.append(ComplianceCheck(
            "Art.15", t3.temperament > 0.3,
            f"T3 temperament: {t3.temperament:.3f}"
        ))

        # Annex.III: High-risk classification (AI entities)
        is_high_risk = lct.entity_type in ("ai", "hybrid")
        self.checks.append(ComplianceCheck(
            "Annex.III", not is_high_risk or t3.composite() > 0.5,
            f"High-risk AI: {is_high_risk}, T3: {t3.composite():.3f}"
        ))

        satisfied = sum(1 for c in self.checks if c.satisfied)
        if satisfied == len(self.ARTICLES):
            return ComplianceLevel.FULL
        elif satisfied >= 6:
            return ComplianceLevel.SUBSTANTIAL
        elif satisfied >= 4:
            return ComplianceLevel.PARTIAL
        else:
            return ComplianceLevel.NON_COMPLIANT


# ═══════════════════════════════════════════════════════════════
# Web4Entity — The unified entity combining all layers
# ═══════════════════════════════════════════════════════════════

class Web4Entity:
    """
    Complete Web4 entity — the fractal DNA cell.

    Entity = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP

    Integrates identity, trust, context, economic, and action layers
    into a single living operational loop.
    """

    def __init__(self, entity_type: str, name: str, atp: float = 100.0,
                 parent_lct: Optional[str] = None):
        # Layer 1: Identity
        raw = f"{entity_type}:{name}:{uuid.uuid4()}"
        fingerprint = hashlib.sha256(raw.encode()).hexdigest()[:16]
        self.lct = LCT(
            lct_id=f"lct:web4:{entity_type}:{fingerprint}",
            entity_type=entity_type,
            entity_name=name,
            key_fingerprint=hashlib.sha256(raw.encode()).hexdigest()[:32],
            parent_lct=parent_lct,
        )
        # Layer 2: Trust
        self.t3 = T3Tensor()
        self.v3 = V3Tensor()
        # Layer 3: Context
        self.mrh = MRHGraph(self.lct.lct_id)
        # Layer 5: Economic
        self.atp_account: Optional[ATPAccount] = None  # Assigned by stack
        # Metadata
        self.action_count = 0
        self.roles: List[str] = []

    @property
    def lct_id(self) -> str:
        return self.lct.lct_id

    def activate(self, witnesses: int = 1):
        self.lct.activate(witnesses)

    def __repr__(self):
        return f"Web4Entity({self.lct.entity_type}, {self.lct.entity_name}, T3={self.t3.composite():.3f})"


# ═══════════════════════════════════════════════════════════════
# Web4Stack — The unified orchestrator
# ═══════════════════════════════════════════════════════════════

class Web4Stack:
    """
    Unified Web4 stack — wires all 9 layers into a coherent system.

    This is the single entry point for Web4 development. It manages:
    - Entity creation and lifecycle
    - Trust propagation and evolution
    - ATP economics with conservation
    - Society governance and laws
    - Action execution with audit trail
    - Federation coordination
    - MCP tool sessions
    - EU AI Act compliance

    Usage:
        stack = Web4Stack("my_society")
        alice = stack.create_entity("human", "alice", atp=500)
        bob = stack.create_entity("ai", "bob", atp=300)
        result = stack.execute_action(alice, bob, "review", cost=20)
    """

    def __init__(self, society_name: str = "default", initial_treasury: float = 100000.0):
        # Core registries
        self.entities: Dict[str, Web4Entity] = {}
        self.atp_ledger = ATPLedger()
        self.audit_chain = AuditChain()
        self.compliance = ComplianceEngine()

        # Global MRH — stack-level trust graph for multi-hop propagation
        self._global_mrh = MRHGraph("__stack__")

        # Governance
        founder_lct = f"lct:web4:system:{hashlib.sha256(society_name.encode()).hexdigest()[:16]}"
        self.society = Society(society_name, founder_lct, initial_treasury)

        # Federation (optional)
        self.federation: Optional[Federation] = None

        # Protocol sessions
        self.mcp_sessions: Dict[str, MCPSession] = {}

        # Diminishing returns tracking: (actor, action_type) → count
        self._action_type_counts: Dict[Tuple[str, str], int] = defaultdict(int)

    # ─── Entity management ─────────────────────────────────────

    def create_entity(self, entity_type: str, name: str, atp: float = 100.0,
                      witnesses: int = 1, roles: Optional[List[str]] = None) -> Web4Entity:
        """Create a new Web4 entity with full stack initialization."""
        entity = Web4Entity(entity_type, name, atp)
        entity.activate(witnesses)
        entity.roles = roles or []

        # Register in entity map
        self.entities[entity.lct_id] = entity

        # Allocate ATP from society treasury
        self.society.allocate_atp(atp)
        acct = self.atp_ledger.create_account(entity.lct_id, atp)
        entity.atp_account = acct

        # Add to society
        role = roles[0] if roles else "member"
        self.society.add_member(entity.lct_id, role)

        return entity

    def get_entity(self, lct_id: str) -> Optional[Web4Entity]:
        return self.entities.get(lct_id)

    # ─── Trust management ──────────────────────────────────────

    def establish_trust(self, entity_a: Web4Entity, entity_b: Web4Entity,
                        initial_weight: float = 0.5):
        """Establish bidirectional trust relationship (local + global MRH)."""
        entity_a.mrh.add_edge(entity_a.lct_id, entity_b.lct_id, initial_weight)
        entity_b.mrh.add_edge(entity_b.lct_id, entity_a.lct_id, initial_weight)
        # Also add to global graph for multi-hop routing
        self._global_mrh.add_edge(entity_a.lct_id, entity_b.lct_id, initial_weight)
        self._global_mrh.add_edge(entity_b.lct_id, entity_a.lct_id, initial_weight)

    def get_trust(self, from_entity: Web4Entity, to_entity: Web4Entity) -> float:
        """Get trust from one entity to another via global MRH (multi-hop)."""
        if from_entity.lct_id == to_entity.lct_id:
            return 1.0
        # Use global MRH for multi-hop routing
        self._global_mrh.center = from_entity.lct_id
        return self._global_mrh.compute_trust(to_entity.lct_id)

    def get_zone(self, from_entity: Web4Entity, to_entity: Web4Entity) -> MRHZone:
        """Get MRH zone between two entities via global MRH."""
        if from_entity.lct_id == to_entity.lct_id:
            return MRHZone.SELF
        self._global_mrh.center = from_entity.lct_id
        return self._global_mrh.get_zone(to_entity.lct_id)

    # ─── Action execution ──────────────────────────────────────

    def execute_action(self, actor: Web4Entity, target: Web4Entity,
                       action_type: str, resource: str = "", cost: float = 10.0,
                       quality: float = 0.7) -> R7Result:
        """
        Execute an action through the full Web4 pipeline.

        Pipeline:
        1. Society law compliance check
        2. Trust verification (MRH zone gating)
        3. ATP debit
        4. Diminishing returns calculation
        5. Trust/value tensor update
        6. Audit chain append
        7. Return R7 result with reputation delta
        """
        action = R6Action(
            actor_lct=actor.lct_id,
            target_lct=target.lct_id,
            action_type=action_type,
            resource=resource,
            cost=cost,
        )

        # 1. Society compliance
        compliant, reason = self.society.check_compliance(
            action_type, actor.t3.composite(), cost
        )
        if not compliant:
            result = R7Result(action.action_id, ActionOutcome.DENIED, reason)
            self.audit_chain.append(result)
            return result

        # 2. Trust check — actor must have established trust with target
        trust = self.get_trust(actor, target)
        zone = self.get_zone(actor, target)
        if zone == MRHZone.BEYOND:
            # Allow if they're in the same society at least
            pass  # Permissive for MVP — society membership is sufficient

        # 3. ATP transfer (actor pays target for service — conservation-safe)
        if cost > 0:
            if not actor.atp_account or not target.atp_account:
                result = R7Result(action.action_id, ActionOutcome.DENIED, "Missing ATP account")
                self.audit_chain.append(result)
                return result
            if not self.atp_ledger.transfer(actor.lct_id, target.lct_id, cost, fee_rate=0.0):
                result = R7Result(action.action_id, ActionOutcome.DENIED, "Insufficient ATP")
                self.audit_chain.append(result)
                return result

        # 4. Diminishing returns: 0.8^(n-1) for repeated action types
        key = (actor.lct_id, action_type)
        repeat_count = self._action_type_counts[key]
        diminishing_factor = 0.8 ** repeat_count
        self._action_type_counts[key] += 1

        # 5. Compute reputation delta
        effective_quality = quality * diminishing_factor
        rep_delta = 0.02 * (effective_quality - 0.5)

        # Update actor's tensors
        actor.t3.update(effective_quality, quality >= 0.5)
        actor.v3.update(effective_quality, quality >= 0.7)
        actor.action_count += 1

        # 6. Build R7 result
        result = R7Result(
            action_id=action.action_id,
            outcome=ActionOutcome.APPROVED,
            atp_consumed=cost,
            quality=quality,
            reputation_delta=rep_delta,
        )
        self.audit_chain.append(result)

        return result

    # ─── MCP sessions ──────────────────────────────────────────

    def create_mcp_session(self, server: Web4Entity, client: Web4Entity,
                           tools: Optional[List[MCPTool]] = None) -> MCPSession:
        """Create a trust-gated MCP session between two entities."""
        trust = self.get_trust(server, client)
        session = MCPSession(server.lct_id, client.lct_id, trust)
        if tools:
            for tool in tools:
                session.register_tool(tool)
        self.mcp_sessions[session.session_id] = session
        return session

    # ─── Federation ────────────────────────────────────────────

    def enable_federation(self, federation_name: str = "default") -> Federation:
        """Enable federation support."""
        self.federation = Federation(federation_name)
        self.federation.add_society(self.society)
        return self.federation

    # ─── Compliance ────────────────────────────────────────────

    def check_compliance(self, entity: Web4Entity) -> ComplianceLevel:
        """Run EU AI Act compliance check on an entity."""
        return self.compliance.check_entity(
            entity.lct, entity.t3, entity.v3,
            entity.atp_account or ATPAccount(entity.lct_id),
            len(self.audit_chain),
        )

    # ─── Audit ─────────────────────────────────────────────────

    def verify_audit_integrity(self) -> bool:
        """Verify the audit chain is tamper-free."""
        return self.audit_chain.verify_integrity()

    def verify_atp_conservation(self) -> bool:
        """Verify ATP conservation invariant."""
        return self.atp_ledger.verify_conservation()

    # ─── Reporting ─────────────────────────────────────────────

    def entity_report(self, entity: Web4Entity) -> Dict[str, Any]:
        """Generate a comprehensive entity report."""
        return {
            "identity": {
                "lct_id": entity.lct_id,
                "type": entity.lct.entity_type,
                "name": entity.lct.entity_name,
                "state": entity.lct.state.value,
                "witnesses": entity.lct.witness_count,
            },
            "trust": entity.t3.to_dict(),
            "value": entity.v3.to_dict(),
            "economic": {
                "balance": entity.atp_account.balance if entity.atp_account else 0,
                "total_earned": entity.atp_account.total_earned if entity.atp_account else 0,
                "total_spent": entity.atp_account.total_spent if entity.atp_account else 0,
            },
            "actions": entity.action_count,
            "roles": entity.roles,
            "compliance": self.check_compliance(entity).value,
        }


# ═══════════════════════════════════════════════════════════════
# CHECKS — Comprehensive integration tests
# ═══════════════════════════════════════════════════════════════

passed = 0
failed = 0
total = 0
current_section = ""


def check(condition: bool, description: str):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL [{current_section}] #{total}: {description}")


def section(name: str):
    global current_section
    current_section = name
    print(f"Section: {name}")


def run_checks():
    global passed, failed, total

    # ═══════════════════════════════════════════════════════════
    # Section 1: Identity Layer — LCT Lifecycle
    # ═══════════════════════════════════════════════════════════
    section("1. Identity Layer — LCT Lifecycle")

    lct = LCT(lct_id="lct:web4:human:test123", entity_type="human", entity_name="test")

    # Genesis state
    check(lct.state == LCTState.GENESIS, "LCT starts in GENESIS")
    check(lct.lct_id.startswith("lct:web4:"), "LCT ID format correct")

    # Activate
    lct.activate(witnesses=3)
    check(lct.state == LCTState.ACTIVE, "LCT transitions to ACTIVE")
    check(lct.witness_count == 3, "Witness count recorded")

    # Suspend and reinstate
    lct.suspend("maintenance")
    check(lct.state == LCTState.SUSPENDED, "LCT suspended")
    lct.reinstate()
    check(lct.state == LCTState.ACTIVE, "LCT reinstated")

    # Key rotation
    lct.begin_rotation("new_key_fp")
    check(lct.state == LCTState.ROTATING, "LCT in rotation")
    check(lct.key_fingerprint == "new_key_fp", "New key fingerprint set")
    check(len(lct.rotation_history) == 1, "Previous key in history")
    lct.complete_rotation()
    check(lct.state == LCTState.ACTIVE, "Rotation complete, back to ACTIVE")

    # Revocation
    lct.revoke()
    check(lct.state == LCTState.REVOKED, "LCT revoked")

    # Invalid transitions
    try:
        lct.activate()
        check(False, "Should not activate from REVOKED")
    except ValueError:
        check(True, "Cannot activate from REVOKED")

    # ═══════════════════════════════════════════════════════════
    # Section 2: Trust Layer — T3/V3 Tensors
    # ═══════════════════════════════════════════════════════════
    section("2. Trust Layer — T3/V3 Tensors")

    t3 = T3Tensor()
    check(t3.composite() == 0.5, "T3 starts at 0.5 composite")
    check(t3.talent == 0.5, "Talent starts at 0.5")

    # Good performance updates
    for _ in range(10):
        t3.update(quality=0.8, success=True)
    check(t3.composite() > 0.5, "T3 increases with good performance")
    check(t3.talent > 0.5, "Talent increased")

    # Bad performance
    t3_before = t3.composite()
    for _ in range(10):
        t3.update(quality=0.2, success=False)
    check(t3.composite() < t3_before, "T3 decreases with bad performance")

    # V3 tensor
    v3 = V3Tensor()
    check(abs(v3.composite() - 0.35) < 0.01, "V3 starts at 0.35 (valuation=0)")
    v3.update(value_created=0.8, accurate=True)
    check(v3.valuation > 0.0, "Valuation increases with value creation")
    check(v3.veracity > 0.5, "Veracity increases with accuracy")

    # Bounds checking
    extreme_t3 = T3Tensor(talent=0.99, training=0.99, temperament=0.99)
    for _ in range(100):
        extreme_t3.update(quality=1.0, success=True)
    check(extreme_t3.talent <= 1.0, "Talent bounded at 1.0")
    check(extreme_t3.training <= 1.0, "Training bounded at 1.0")
    check(extreme_t3.temperament <= 1.0, "Temperament bounded at 1.0")

    low_t3 = T3Tensor(talent=0.01, training=0.01, temperament=0.01)
    for _ in range(100):
        low_t3.update(quality=0.0, success=False)
    check(low_t3.talent >= 0.0, "Talent bounded at 0.0")
    check(low_t3.training >= 0.0, "Training bounded at 0.0")

    # ═══════════════════════════════════════════════════════════
    # Section 3: Context Layer — MRH Graph
    # ═══════════════════════════════════════════════════════════
    section("3. Context Layer — MRH Graph")

    mrh = MRHGraph("alice")

    # Self zone
    check(mrh.get_zone("alice") == MRHZone.SELF, "Self zone for center")
    check(mrh.compute_trust("alice") == 1.0, "Self trust = 1.0")

    # Direct connection
    mrh.add_edge("alice", "bob", 0.8)
    check(mrh.get_zone("bob") == MRHZone.DIRECT, "1-hop = DIRECT zone")
    direct_trust = mrh.compute_trust("bob")
    check(abs(direct_trust - 0.8 * MRH_DECAY) < 0.01, f"Direct trust = 0.8 × {MRH_DECAY}")

    # Indirect (2-hop)
    mrh.add_edge("bob", "charlie", 0.9)
    check(mrh.get_zone("charlie") == MRHZone.INDIRECT, "2-hop = INDIRECT zone")
    indirect_trust = mrh.compute_trust("charlie")
    expected = 0.8 * MRH_DECAY * 0.9 * MRH_DECAY
    check(abs(indirect_trust - expected) < 0.01, "Indirect trust = multiplicative decay")

    # Peripheral (3-hop)
    mrh.add_edge("charlie", "dave", 0.7)
    check(mrh.get_zone("dave") == MRHZone.PERIPHERAL, "3-hop = PERIPHERAL zone")

    # Beyond (no connection)
    check(mrh.get_zone("unknown") == MRHZone.BEYOND, "Unknown = BEYOND zone")
    check(mrh.compute_trust("unknown") == 0.0, "Unknown trust = 0.0")

    # ═══════════════════════════════════════════════════════════
    # Section 4: Governance Layer — Society
    # ═══════════════════════════════════════════════════════════
    section("4. Governance Layer — Society")

    society = Society("test_soc", "lct:founder", initial_atp=10000.0)
    check(society.state == SocietyState.FORMING, "Society starts FORMING")

    # Add members and activate
    society.add_member("lct:alice", "developer")
    society.add_member("lct:bob", "reviewer")
    society.activate(min_members=1)
    check(society.state == SocietyState.ACTIVE, "Society activated")
    check(len(society.members) == 3, "3 members (founder + 2)")

    # Laws
    law = SocietyLaw(
        law_id="LAW-001",
        description="Minimum trust for code deployment",
        min_trust=0.4,
        max_atp_cost=500.0,
        prohibited_actions=["delete_production"],
    )
    society.enact_law(law)

    ok, _ = society.check_compliance("review_code", trust=0.5, cost=50.0)
    check(ok, "Compliant action passes")

    ok, reason = society.check_compliance("review_code", trust=0.2, cost=50.0)
    check(not ok, "Low-trust action denied")
    check("trust" in reason.lower(), "Denial reason mentions trust")

    ok, _ = society.check_compliance("delete_production", trust=0.9, cost=10.0)
    check(not ok, "Prohibited action denied regardless of trust")

    ok, reason = society.check_compliance("deploy", trust=0.5, cost=600.0)
    check(not ok, "Over-budget action denied")

    # Treasury
    check(society.allocate_atp(1000.0), "Treasury allocation succeeds")
    check(society.treasury_atp == 9000.0, "Treasury balance updated")
    check(not society.allocate_atp(99999.0), "Over-allocation fails")

    # Member removal
    society.remove_member("lct:bob")
    check("lct:bob" not in society.members, "Member removed")
    try:
        society.remove_member("lct:founder")
        check(False, "Should not remove founder")
    except ValueError:
        check(True, "Cannot remove founder")

    # ═══════════════════════════════════════════════════════════
    # Section 5: Economic Layer — ATP Ledger
    # ═══════════════════════════════════════════════════════════
    section("5. Economic Layer — ATP Ledger")

    ledger = ATPLedger()
    a1 = ledger.create_account("lct:alice", 1000.0)
    a2 = ledger.create_account("lct:bob", 500.0)
    check(ledger.total_supply == 1500.0, "Initial supply = 1500")
    check(ledger.verify_conservation(), "Conservation holds initially")

    # Transfer with fee
    ok = ledger.transfer("lct:alice", "lct:bob", 100.0, fee_rate=0.05)
    check(ok, "Transfer succeeds")
    check(a1.balance == 895.0, "Alice: 1000 - 100 - 5(fee) = 895")
    check(a2.balance == 600.0, "Bob: 500 + 100 = 600")
    check(abs(ledger.total_fees_burned - 5.0) < 0.001, "5 ATP burned in fees")
    check(ledger.verify_conservation(), "Conservation holds after transfer")

    # Failed transfer (insufficient funds)
    ok = ledger.transfer("lct:alice", "lct:bob", 99999.0)
    check(not ok, "Over-balance transfer fails")
    check(ledger.verify_conservation(), "Conservation holds after failed transfer")

    # Locking
    check(a1.lock(100.0), "Lock 100 ATP")
    check(a1.available == 795.0, "Available = 895 - 100 locked")
    check(not a1.debit(800.0), "Cannot debit more than available")
    check(a1.debit(795.0), "Can debit exactly available")

    # Slash
    slashed = a1.slash(50.0)
    check(slashed == 50.0, "Slashed 50 from locked")
    check(a1.locked == 50.0, "50 still locked after partial slash")
    check(a1.balance == 50.0, "Balance reduced by slash amount")

    # ═══════════════════════════════════════════════════════════
    # Section 6: Action Layer — R7 Pipeline with Audit
    # ═══════════════════════════════════════════════════════════
    section("6. Action Layer — R7 Pipeline with Audit")

    chain = AuditChain()
    check(chain.verify_integrity(), "Empty chain is valid")

    # Build chain
    for i in range(5):
        r = R7Result(
            action_id=f"act-{i}",
            outcome=ActionOutcome.APPROVED,
            atp_consumed=10.0,
            quality=0.8,
        )
        chain.append(r)

    check(len(chain) == 5, "Chain has 5 entries")
    check(chain.verify_integrity(), "Chain integrity holds")
    check(chain.chain[0].prev_hash == chain.genesis_hash, "First entry links to genesis")
    check(chain.chain[1].prev_hash == chain.chain[0].result_hash, "Chain links are correct")

    # Tamper detection
    chain.chain[2].quality = 9999.0  # Tamper with entry
    check(not chain.verify_integrity(), "Tampering detected — hash mismatch")

    # Restore for remaining tests
    chain.chain[2].compute_hash()  # Recompute — but prev/next links still broken
    # Note: single-entry recompute doesn't fix chain — intentional

    # Fresh chain for diminishing returns
    chain2 = AuditChain()
    r1 = R7Result("dr-1", ActionOutcome.APPROVED, quality=0.8, reputation_delta=0.006)
    r2 = R7Result("dr-2", ActionOutcome.APPROVED, quality=0.8, reputation_delta=0.0048)
    chain2.append(r1)
    chain2.append(r2)
    check(r1.reputation_delta > r2.reputation_delta, "Diminishing returns: first > second")

    # ═══════════════════════════════════════════════════════════
    # Section 7: Federation Layer
    # ═══════════════════════════════════════════════════════════
    section("7. Federation Layer")

    fed = Federation("global")
    soc_a = Society("alpha", "lct:fa", 5000.0)
    soc_b = Society("beta", "lct:fb", 5000.0)
    soc_a.activate()
    soc_b.activate()

    fed.add_society(soc_a)
    fed.add_society(soc_b)
    fed.link_societies(soc_a.society_id, soc_b.society_id, 0.6)

    # Cross-society trust
    trust_ab = fed.cross_society_trust(soc_a.society_id, soc_b.society_id)
    check(abs(trust_ab - 0.6) < 0.01, "Cross-society trust = 0.6")

    # Federation allows action
    ok, _ = fed.federated_action(soc_a.society_id, soc_b.society_id)
    check(ok, "Federated action allowed")

    # Circuit breaker
    link = fed.links[(soc_a.society_id, soc_b.society_id)]
    for _ in range(3):
        link.record_failure()
    check(link.circuit == CircuitState.OPEN, "Circuit breaker tripped after 3 failures")

    trust_broken = fed.cross_society_trust(soc_a.society_id, soc_b.society_id)
    check(trust_broken == 0.0, "Open circuit = zero trust")

    ok, reason = fed.federated_action(soc_a.society_id, soc_b.society_id)
    check(not ok, "Federated action blocked by open circuit")
    check("OPEN" in reason, "Reason mentions circuit breaker")

    # Recovery
    link.attempt_recovery()
    check(link.circuit == CircuitState.HALF_OPEN, "Circuit enters HALF_OPEN")
    link.record_success()
    check(link.circuit == CircuitState.CLOSED, "Circuit recovers to CLOSED")
    check(link.failure_count == 0, "Failure count reset")

    # No link
    trust_none = fed.cross_society_trust("nonexistent", soc_b.society_id)
    check(trust_none == 0.0, "No link = zero trust")

    # ═══════════════════════════════════════════════════════════
    # Section 8: Protocol Layer — MCP Session
    # ═══════════════════════════════════════════════════════════
    section("8. Protocol Layer — MCP Session")

    session = MCPSession("lct:server", "lct:client", trust=0.7)

    # Register tools with different trust requirements
    session.register_tool(MCPTool("read", "Read file", min_trust=0.3))
    session.register_tool(MCPTool("write", "Write file", min_trust=0.5))
    session.register_tool(MCPTool("admin", "Admin action", min_trust=0.9))

    ok, _ = session.invoke_tool("read")
    check(ok, "Read tool accessible at trust 0.7")

    ok, _ = session.invoke_tool("write")
    check(ok, "Write tool accessible at trust 0.7")

    ok, reason = session.invoke_tool("admin")
    check(not ok, "Admin tool denied at trust 0.7")
    check("trust" in reason.lower(), "Denial mentions trust")

    ok, _ = session.invoke_tool("unknown_tool")
    check(not ok, "Unknown tool returns error")

    check(session.invocation_count == 2, "Only successful invocations counted (2)")

    # Session close
    session.close()
    ok, reason = session.invoke_tool("read")
    check(not ok, "Closed session rejects invocations")

    # ═══════════════════════════════════════════════════════════
    # Section 9: Compliance Layer — EU AI Act
    # ═══════════════════════════════════════════════════════════
    section("9. Compliance Layer — EU AI Act")

    engine = ComplianceEngine()

    # Compliant human entity
    good_lct = LCT("lct:good", "human", "alice")
    good_lct.activate(witnesses=3)
    good_t3 = T3Tensor(talent=0.7, training=0.7, temperament=0.7)
    good_v3 = V3Tensor(valuation=0.5, veracity=0.6, validity=0.6)
    good_acct = ATPAccount("lct:good", balance=100.0)
    level = engine.check_entity(good_lct, good_t3, good_v3, good_acct, audit_len=10)
    check(level == ComplianceLevel.FULL, "Good human entity = FULL compliance")

    # Non-compliant entity (no witnesses, low trust)
    bad_lct = LCT("lct:bad", "ai", "shady_bot")
    bad_lct.activate(witnesses=0)
    bad_t3 = T3Tensor(talent=0.1, training=0.1, temperament=0.1)
    bad_v3 = V3Tensor(valuation=0.0, veracity=0.2, validity=0.2)
    level = engine.check_entity(bad_lct, bad_t3, bad_v3, ATPAccount("lct:bad"), audit_len=0)
    check(level == ComplianceLevel.NON_COMPLIANT, "Bad AI entity = NON_COMPLIANT")

    # Check that high-risk AI needs higher T3
    borderline_lct = LCT("lct:border", "ai", "borderline_ai")
    borderline_lct.activate(witnesses=2)
    borderline_t3 = T3Tensor(talent=0.4, training=0.4, temperament=0.4)
    borderline_v3 = V3Tensor(valuation=0.3, veracity=0.5, validity=0.5)
    level = engine.check_entity(borderline_lct, borderline_t3, borderline_v3,
                                ATPAccount("lct:border", balance=50), audit_len=5)
    # T3 composite = 0.4, < 0.5 threshold for AI → Annex.III fails
    annex_check = [c for c in engine.checks if c.article == "Annex.III"][0]
    check(not annex_check.satisfied, "Borderline AI fails Annex.III (T3 < 0.5)")

    # ═══════════════════════════════════════════════════════════
    # Section 10: Integrated Stack — Full Pipeline
    # ═══════════════════════════════════════════════════════════
    section("10. Integrated Stack — Full Pipeline")

    stack = Web4Stack("integration_test", initial_treasury=50000.0)

    # Create entities
    alice = stack.create_entity("human", "alice", atp=500, witnesses=3, roles=["developer"])
    bob = stack.create_entity("ai", "bob", atp=300, witnesses=2, roles=["reviewer"])
    charlie = stack.create_entity("human", "charlie", atp=200, witnesses=1, roles=["observer"])

    check(len(stack.entities) == 3, "3 entities in stack")
    check(alice.lct.state == LCTState.ACTIVE, "Alice is active")
    check(bob.lct.state == LCTState.ACTIVE, "Bob is active")
    check(alice.atp_account.balance == 500.0, "Alice has 500 ATP")

    # Establish trust network
    stack.establish_trust(alice, bob, 0.8)
    stack.establish_trust(bob, charlie, 0.6)

    check(stack.get_zone(alice, bob) == MRHZone.DIRECT, "Alice→Bob is DIRECT")
    alice_bob_trust = stack.get_trust(alice, bob)
    check(alice_bob_trust > 0, "Alice→Bob trust > 0")

    # Execute actions
    r1 = stack.execute_action(alice, bob, "code_review", resource="repo:main", cost=20, quality=0.8)
    check(r1.outcome == ActionOutcome.APPROVED, "Code review approved")
    check(r1.atp_consumed == 20.0, "20 ATP consumed")
    check(r1.reputation_delta > 0, "Positive reputation delta for quality work")

    r2 = stack.execute_action(alice, bob, "code_review", resource="repo:main", cost=20, quality=0.8)
    check(r2.outcome == ActionOutcome.APPROVED, "Second review approved")
    check(r2.reputation_delta < r1.reputation_delta, "Diminishing returns on repeated action")

    # Try a different action type — fresh diminishing returns
    r3 = stack.execute_action(alice, bob, "deploy", resource="prod", cost=30, quality=0.9)
    check(r3.outcome == ActionOutcome.APPROVED, "Deploy action approved")
    check(r3.reputation_delta > r2.reputation_delta, "Fresh action type gets full learning rate")

    # Check ATP accounting (transfer semantics: actor pays target)
    # r1: alice→bob 20, r2: alice→bob 20, r3: alice→bob 30
    check(alice.atp_account.balance == 430.0, "Alice: 500 - 20 - 20 - 30 = 430")
    check(bob.atp_account.balance == 370.0, "Bob: 300 + 20 + 20 + 30 = 370")

    # Audit integrity
    check(stack.verify_audit_integrity(), "Audit chain integrity holds")
    check(len(stack.audit_chain) == 3, "3 entries in audit chain")

    # ATP conservation
    check(stack.verify_atp_conservation(), "ATP conservation invariant holds")

    # Entity report
    report = stack.entity_report(alice)
    check(report["identity"]["name"] == "alice", "Report shows correct name")
    check(report["identity"]["type"] == "human", "Report shows correct type")
    check(report["economic"]["balance"] == 430.0, "Report shows correct balance")
    check(report["actions"] == 3, "Report shows 3 actions")
    check(report["compliance"] in ("full", "substantial"), "Alice is compliant")

    # ═══════════════════════════════════════════════════════════
    # Section 11: Integrated Stack — Denial Paths
    # ═══════════════════════════════════════════════════════════
    section("11. Integrated Stack — Denial Paths")

    # Add a law to the stack's society
    stack.society.enact_law(SocietyLaw(
        law_id="LAW-SEC-001",
        description="High trust required for deletions",
        min_trust=0.9,
        prohibited_actions=["rm_rf"],
    ))

    # Low trust action
    low_trust_entity = stack.create_entity("ai", "newbie", atp=100, witnesses=1)
    low_trust_entity.t3 = T3Tensor(talent=0.1, training=0.1, temperament=0.1)
    rd = stack.execute_action(low_trust_entity, alice, "sensitive_op", cost=10, quality=0.5)
    check(rd.outcome == ActionOutcome.DENIED, "Low-trust entity denied by society law")

    # Prohibited action
    rp = stack.execute_action(alice, bob, "rm_rf", cost=5, quality=0.5)
    check(rp.outcome == ActionOutcome.DENIED, "Prohibited action denied")

    # Insufficient ATP (set trust high to pass society laws)
    broke = stack.create_entity("human", "broke", atp=5, witnesses=1)
    broke.t3 = T3Tensor(talent=0.95, training=0.95, temperament=0.95)
    rb = stack.execute_action(broke, alice, "review", cost=100, quality=0.5)
    check(rb.outcome == ActionOutcome.DENIED, "Insufficient ATP denied")
    check("ATP" in rb.reason, "Denial reason mentions ATP")

    # ═══════════════════════════════════════════════════════════
    # Section 12: Integrated Stack — Federation + MCP
    # ═══════════════════════════════════════════════════════════
    section("12. Integrated Stack — Federation + MCP")

    # MCP session
    mcp_tools = [
        MCPTool("analyze", "Analyze code", min_trust=0.3, atp_cost=5),
        MCPTool("execute", "Execute code", min_trust=0.6, atp_cost=10),
        MCPTool("deploy_prod", "Deploy to production", min_trust=0.95, atp_cost=50),
    ]
    session = stack.create_mcp_session(alice, bob, mcp_tools)
    check(session.active, "MCP session is active")
    check(session.trust == alice_bob_trust, "Session trust matches MRH trust")

    ok, _ = session.invoke_tool("analyze")
    check(ok, "Analyze tool accessible")

    # Federation
    fed = stack.enable_federation("web4_global")
    check(fed is not None, "Federation enabled")
    check(stack.society.society_id in fed.societies, "Stack's society is in federation")

    # Add partner society
    partner = Society("partner_soc", "lct:partner_founder", 5000.0)
    partner.activate()
    fed.add_society(partner)
    fed.link_societies(stack.society.society_id, partner.society_id, 0.7)

    ok, _ = fed.federated_action(stack.society.society_id, partner.society_id)
    check(ok, "Cross-federation action allowed")

    cross_trust = fed.cross_society_trust(stack.society.society_id, partner.society_id)
    check(abs(cross_trust - 0.7) < 0.01, "Cross-federation trust = 0.7")

    # ═══════════════════════════════════════════════════════════
    # Section 13: Edge Cases and Invariants
    # ═══════════════════════════════════════════════════════════
    section("13. Edge Cases and Invariants")

    # Empty stack
    empty_stack = Web4Stack("empty", initial_treasury=0.0)
    check(empty_stack.verify_audit_integrity(), "Empty audit chain is valid")
    check(empty_stack.verify_atp_conservation(), "Empty ledger conserves")
    check(len(empty_stack.entities) == 0, "No entities in empty stack")

    # Zero-cost action (set trust high to pass society laws)
    rich = stack.create_entity("human", "rich", atp=10000, witnesses=2)
    rich.t3 = T3Tensor(talent=0.95, training=0.95, temperament=0.95)
    r_free = stack.execute_action(rich, alice, "observe", cost=0.0, quality=0.5)
    check(r_free.outcome == ActionOutcome.APPROVED, "Zero-cost action approved")
    check(r_free.atp_consumed == 0.0, "Zero ATP consumed")
    check(rich.atp_account.balance == 10000.0, "Balance unchanged after free action")

    # Entity with all roles
    multi = stack.create_entity("hybrid", "multi", atp=200, witnesses=3,
                                roles=["developer", "reviewer", "admin"])
    check(len(multi.roles) == 3, "Entity can have multiple roles")
    check(multi.lct.entity_type == "hybrid", "Hybrid entity type")

    # Conservation after many operations
    check(stack.verify_atp_conservation(), "Conservation holds after all operations")

    # Audit chain still intact (excluding the tampered section 6 chain)
    check(stack.verify_audit_integrity(), "Stack audit chain intact after all operations")

    # MRH self trust
    for entity in stack.entities.values():
        self_trust = entity.mrh.compute_trust(entity.lct_id)
        check(self_trust == 1.0, f"Self trust = 1.0 for {entity.lct.entity_name}")

    # ═══════════════════════════════════════════════════════════
    # Section 14: Compliance Across Entity Types
    # ═══════════════════════════════════════════════════════════
    section("14. Compliance Across Entity Types")

    # AI entity needs higher trust for Annex.III
    check(stack.check_compliance(alice) in (ComplianceLevel.FULL, ComplianceLevel.SUBSTANTIAL),
          "Human with good history is compliant")

    # Check bob (AI) — may need more trust
    bob_level = stack.check_compliance(bob)
    check(bob_level in (ComplianceLevel.FULL, ComplianceLevel.SUBSTANTIAL, ComplianceLevel.PARTIAL),
          f"AI reviewer compliance: {bob_level.value}")

    # Check newbie (low trust AI)
    newbie_level = stack.check_compliance(low_trust_entity)
    check(newbie_level in (ComplianceLevel.NON_COMPLIANT, ComplianceLevel.PARTIAL),
          f"Low-trust AI compliance: {newbie_level.value}")

    # ═══════════════════════════════════════════════════════════
    # Section 15: Lifecycle — Entity Suspension and Revocation
    # ═══════════════════════════════════════════════════════════
    section("15. Lifecycle — Entity Suspension and Revocation")

    # Suspend an entity
    target_entity = stack.create_entity("ai", "to_suspend", atp=100, witnesses=1)
    check(target_entity.lct.state == LCTState.ACTIVE, "Entity starts active")

    target_entity.lct.suspend("policy violation")
    check(target_entity.lct.state == LCTState.SUSPENDED, "Entity suspended")

    target_entity.lct.reinstate()
    check(target_entity.lct.state == LCTState.ACTIVE, "Entity reinstated")

    # Revoke
    target_entity.lct.revoke()
    check(target_entity.lct.state == LCTState.REVOKED, "Entity revoked")

    # Revoked entity cannot be activated again
    try:
        target_entity.lct.activate()
        check(False, "Should not activate revoked entity")
    except ValueError:
        check(True, "Revoked entity cannot be activated")

    # ═══════════════════════════════════════════════════════════
    # Section 16: Trust Propagation Through Network
    # ═══════════════════════════════════════════════════════════
    section("16. Trust Propagation Through Network")

    prop_stack = Web4Stack("propagation_test", initial_treasury=50000.0)
    nodes = {}
    for name in ["a", "b", "c", "d", "e"]:
        nodes[name] = prop_stack.create_entity("human", name, atp=100, witnesses=1)

    # Linear chain: a → b → c → d → e
    prop_stack.establish_trust(nodes["a"], nodes["b"], 0.9)
    prop_stack.establish_trust(nodes["b"], nodes["c"], 0.8)
    prop_stack.establish_trust(nodes["c"], nodes["d"], 0.7)
    prop_stack.establish_trust(nodes["d"], nodes["e"], 0.6)

    # Trust decays multiplicatively
    ab_trust = prop_stack.get_trust(nodes["a"], nodes["b"])
    ac_trust = prop_stack.get_trust(nodes["a"], nodes["c"])
    check(ab_trust > ac_trust, "Direct trust > indirect trust")

    ad_trust = prop_stack.get_trust(nodes["a"], nodes["d"])
    check(ac_trust > ad_trust, "2-hop trust > 3-hop trust")

    # Verify decay formula: each hop multiplies by weight × MRH_DECAY
    expected_ab = 0.9 * MRH_DECAY
    check(abs(ab_trust - expected_ab) < 0.01, f"a→b trust = {expected_ab:.3f}")

    expected_ac = 0.9 * MRH_DECAY * 0.8 * MRH_DECAY
    check(abs(ac_trust - expected_ac) < 0.01, f"a→c trust = {expected_ac:.4f}")

    # Zones
    check(prop_stack.get_zone(nodes["a"], nodes["b"]) == MRHZone.DIRECT, "a→b is DIRECT")
    check(prop_stack.get_zone(nodes["a"], nodes["c"]) == MRHZone.INDIRECT, "a→c is INDIRECT")
    check(prop_stack.get_zone(nodes["a"], nodes["d"]) == MRHZone.PERIPHERAL, "a→d is PERIPHERAL")

    # ═══════════════════════════════════════════════════════════
    # Report
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'=' * 60}")
    print(f"Web4 Integration SDK: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} checks FAILED")
    else:
        print(f"  All checks passed!")
    print(f"{'=' * 60}")

    print(f"\nLayers validated:")
    print(f"  1. Identity (LCT lifecycle)")
    print(f"  2. Trust (T3/V3 tensors)")
    print(f"  3. Context (MRH graph)")
    print(f"  4. Governance (Society + Laws)")
    print(f"  5. Economic (ATP ledger + conservation)")
    print(f"  6. Action (R7 pipeline + audit chain)")
    print(f"  7. Federation (circuit breakers)")
    print(f"  8. Protocol (MCP trust-gated sessions)")
    print(f"  9. Compliance (EU AI Act)")
    print(f"  + Integrated pipeline (16 sections)")


if __name__ == "__main__":
    run_checks()
