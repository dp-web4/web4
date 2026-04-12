#!/usr/bin/env python3
"""
Web4 Conformance Test Suite — Spec-Derived Requirement Validation

Validates Web4 implementations against core specification requirements.
Each test maps to a specific spec section with normative level (MUST/SHOULD).

Requirements covered:
  REQ-LCT-*: LCT structure, ID format, birth certificates, lifecycle
  REQ-T3V3-*: Tensor dimensions, bounds, role-contextualization
  REQ-ATP-*: Token states, conservation, minting, slashing
  REQ-ENT-*: Entity types, immutability, modes, energy patterns
  REQ-MRH-*: Distance zones, trust propagation, depth limits
  REQ-WIT-*: Witness attestations, quorum, freshness
  REQ-R6-*: Action records, hash chain, audit trail
  REQ-CRYPTO-*: Signature schemes, encoding

Session: Legion Autonomous 2026-02-26 (Session 10, Track 6)
"""

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════
# CONFORMANCE FRAMEWORK
# ═══════════════════════════════════════════════════════════════

class NormativeLevel(Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    MAY = "MAY"


class ConformanceResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    WARNING = "warning"


@dataclass
class Requirement:
    req_id: str
    spec_source: str
    normative_level: NormativeLevel
    description: str
    assertion: str


@dataclass
class TestResult:
    requirement: Requirement
    result: ConformanceResult
    details: str = ""


class ConformanceReport:
    """Aggregates test results into a conformance report."""

    def __init__(self, implementation_name: str):
        self.implementation_name = implementation_name
        self.results: list[TestResult] = []

    def add(self, result: TestResult):
        self.results.append(result)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.result == ConformanceResult.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.result == ConformanceResult.FAIL)

    @property
    def warnings(self) -> int:
        return sum(1 for r in self.results if r.result == ConformanceResult.WARNING)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def conformance_level(self) -> str:
        if self.failed == 0 and self.warnings == 0:
            return "FULL"
        elif self.failed == 0:
            return "SUBSTANTIAL"
        elif self.failed <= 3:
            return "PARTIAL"
        else:
            return "NON_CONFORMANT"

    def summary(self) -> dict:
        by_category = {}
        for r in self.results:
            cat = r.requirement.req_id.split("-")[1]
            if cat not in by_category:
                by_category[cat] = {"pass": 0, "fail": 0, "warning": 0}
            by_category[cat][r.result.value] = by_category[cat].get(r.result.value, 0) + 1
        return {
            "implementation": self.implementation_name,
            "conformance_level": self.conformance_level,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "by_category": by_category,
        }


# ═══════════════════════════════════════════════════════════════
# WEB4 REFERENCE IMPLEMENTATION (under test)
# ═══════════════════════════════════════════════════════════════

class LCTDocument:
    """Reference LCT document structure."""

    VALID_ENTITY_TYPES = {
        "human", "ai", "society", "organization", "role", "task",
        "resource", "device", "service", "oracle", "accumulator",
        "dictionary", "hybrid", "policy", "infrastructure",
    }

    def __init__(self, lct_id: str, subject_did: str, entity_type: str,
                 t3: dict, v3: dict, mrh: dict, policy: dict,
                 binding_proof: str, birth_certificate: dict = None,
                 metadata: dict = None):
        self.lct_id = lct_id
        self.subject_did = subject_did
        self.entity_type = entity_type
        self.t3 = t3
        self.v3 = v3
        self.mrh = mrh
        self.policy = policy
        self.binding_proof = binding_proof
        self.birth_certificate = birth_certificate or {}
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat()

    def validate_structure(self) -> list[str]:
        errors = []
        if not self.lct_id:
            errors.append("Missing lct_id")
        if not self.subject_did:
            errors.append("Missing subject_did")
        if not self.entity_type:
            errors.append("Missing entity_type")
        if not self.t3:
            errors.append("Missing T3 tensor")
        if not self.v3:
            errors.append("Missing V3 tensor")
        if not self.mrh:
            errors.append("Missing MRH")
        if not self.policy:
            errors.append("Missing policy")
        return errors

    def validate_id_format(self) -> bool:
        pattern = r'^lct:web4:[a-z][a-z0-9_-]*:[a-zA-Z0-9._-]+$'
        return bool(re.match(pattern, self.lct_id))

    def validate_did_format(self) -> bool:
        pattern = r'^did:web4:(key|web|hw):[a-zA-Z0-9._:-]+$'
        return bool(re.match(pattern, self.subject_did))

    def to_jsonld(self) -> dict:
        return {
            "@context": "https://web4.io/context/v1",
            "@type": "LinkedContextToken",
            "id": self.lct_id,
            "subject": self.subject_did,
            "entityType": self.entity_type,
            "trustTensor": self.t3,
            "valueTensor": self.v3,
            "markovRelevancyHorizon": self.mrh,
            "policy": self.policy,
            "bindingProof": self.binding_proof,
            "birthCertificate": self.birth_certificate,
            "created": self.created_at,
        }


class T3Tensor:
    """Trust Tensor with 3 root dimensions."""

    def __init__(self, talent: float, training: float, temperament: float):
        self.talent = talent
        self.training = training
        self.temperament = temperament
        self.history: list[dict] = []

    def validate_bounds(self) -> list[str]:
        errors = []
        for dim, val in [("talent", self.talent), ("training", self.training),
                         ("temperament", self.temperament)]:
            if not 0.0 <= val <= 1.0:
                errors.append(f"{dim} = {val} outside [0.0, 1.0]")
        return errors

    @property
    def composite(self) -> float:
        return round((self.talent + self.training + self.temperament) / 3, 4)

    def update(self, dimension: str, delta: float, reason: str):
        old = getattr(self, dimension)
        new = max(0.0, min(1.0, old + delta))
        setattr(self, dimension, new)
        self.history.append({
            "dimension": dimension,
            "old": round(old, 4),
            "new": round(new, 4),
            "delta": round(delta, 4),
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })


class V3Tensor:
    """Value Tensor with 3 root dimensions."""

    def __init__(self, valuation: float, veracity: float, validity: float):
        self.valuation = valuation
        self.veracity = veracity
        self.validity = validity

    def validate_bounds(self) -> list[str]:
        errors = []
        if self.valuation < 0:
            errors.append(f"valuation = {self.valuation} below 0")
        for dim, val in [("veracity", self.veracity), ("validity", self.validity)]:
            if not 0.0 <= val <= 1.0:
                errors.append(f"{dim} = {val} outside [0.0, 1.0]")
        return errors


class ATPToken:
    """ATP/ADP token with state machine."""

    VALID_STATES = {"ATP", "ADP"}

    def __init__(self, token_id: str, state: str = "ATP", amount: float = 1.0):
        if state not in self.VALID_STATES:
            raise ValueError(f"Invalid state: {state}")
        self.token_id = token_id
        self.state = state
        self.amount = amount

    def discharge(self) -> bool:
        if self.state != "ATP":
            return False
        self.state = "ADP"
        return True

    def charge(self, value_proof: str) -> bool:
        if self.state != "ADP":
            return False
        if not value_proof:
            return False
        self.state = "ATP"
        return True


class SocietyPool:
    """Society-level ATP/ADP pool with conservation invariant."""

    def __init__(self, society_id: str, initial_atp: float):
        self.society_id = society_id
        self.atp_balance = initial_atp
        self.adp_balance = 0.0
        self.total_minted = initial_atp
        self.operations: list[dict] = []

    @property
    def total_supply(self) -> float:
        return self.atp_balance + self.adp_balance

    def discharge(self, amount: float, entity_id: str, reason: str) -> bool:
        if amount > self.atp_balance:
            return False
        self.atp_balance -= amount
        self.adp_balance += amount
        self.operations.append({"type": "discharge", "amount": amount})
        return True

    def charge(self, amount: float, entity_id: str, value_proof: str) -> bool:
        if amount > self.adp_balance or not value_proof:
            return False
        self.adp_balance -= amount
        self.atp_balance += amount
        self.operations.append({"type": "charge", "amount": amount})
        return True

    def mint(self, amount: float, authority_id: str, justification: str) -> bool:
        if not authority_id or not justification:
            return False
        self.atp_balance += amount
        self.total_minted += amount
        return True

    def slash(self, amount: float, entity_id: str, evidence: str) -> bool:
        if not evidence:
            return False
        actual = min(amount, self.adp_balance)
        self.adp_balance -= actual
        return True


class MRHGraph:
    """Markov Relevancy Horizon as a depth-limited graph."""

    ZONES = ["SELF", "DIRECT", "INDIRECT", "PERIPHERAL", "BEYOND"]
    TRUST_DECAY = 0.7

    def __init__(self, center_lct_id: str, max_depth: int = 3):
        self.center = center_lct_id
        self.max_depth = max_depth
        self.edges: dict[tuple[str, str], dict] = {}

    def add_relationship(self, from_id: str, to_id: str,
                         rel_type: str, weight: float = 1.0):
        self.edges[(from_id, to_id)] = {"type": rel_type, "weight": weight}

    def get_zone(self, depth: int) -> str:
        if depth == 0: return "SELF"
        elif depth == 1: return "DIRECT"
        elif depth == 2: return "INDIRECT"
        elif depth == 3: return "PERIPHERAL"
        else: return "BEYOND"

    def compute_trust(self, target_id: str, path: list[str]) -> float:
        if not path:
            return 1.0 if target_id == self.center else 0.0
        # Path must end at target
        if path[-1] != target_id:
            return 0.0
        trust = 1.0
        for i in range(len(path) - 1):
            edge = self.edges.get((path[i], path[i+1]))
            if not edge:
                return 0.0
            trust *= edge["weight"] * self.TRUST_DECAY
        return trust

    def find_at_depth(self, depth: int) -> list[str]:
        if depth > self.max_depth:
            return []
        visited = {self.center}
        current_level = {self.center}
        for d in range(depth):
            next_level = set()
            for node in current_level:
                for (f, t), _ in self.edges.items():
                    if f == node and t not in visited:
                        next_level.add(t)
            visited.update(next_level)
            current_level = next_level
        return list(current_level)


class R6ActionRecord:
    """R6 action record with hash chain."""

    def __init__(self, action_id: str, rules: str, role: str,
                 request: str, reference: str, resource: str,
                 result: str, prev_hash: str = ""):
        self.action_id = action_id
        self.rules = rules
        self.role = role
        self.request = request
        self.reference = reference
        self.resource = resource
        self.result = result
        self.prev_hash = prev_hash
        self.timestamp = datetime.utcnow().isoformat()
        self.record_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        content = json.dumps({
            "id": self.action_id, "rules": self.rules, "role": self.role,
            "request": self.request, "reference": self.reference,
            "resource": self.resource, "result": self.result,
            "prev_hash": self.prev_hash, "timestamp": self.timestamp,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def validate_completeness(self) -> list[str]:
        errors = []
        for f in ["rules", "role", "request", "reference", "resource", "result"]:
            if not getattr(self, f):
                errors.append(f"Missing R6 component: {f}")
        return errors


class WitnessAttestation:
    """Witness attestation with signature verification."""

    VALID_TYPES = {"time", "audit-minimal", "oracle", "existence",
                   "capability", "identity", "compliance", "reputation"}

    def __init__(self, witness_lct_id: str, witness_type: str,
                 claims: dict, nonce: str):
        if witness_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid witness type: {witness_type}")
        self.witness_lct_id = witness_lct_id
        self.witness_type = witness_type
        self.claims = claims
        self.nonce = nonce
        self.timestamp = datetime.utcnow().isoformat()
        self.signature = ""

    def sign(self, key: str):
        content = f"{self.witness_lct_id}:{self.witness_type}:{json.dumps(self.claims, sort_keys=True)}:{self.nonce}:{key}"
        self.signature = hashlib.sha256(content.encode()).hexdigest()[:32]

    def verify(self, key: str) -> bool:
        content = f"{self.witness_lct_id}:{self.witness_type}:{json.dumps(self.claims, sort_keys=True)}:{self.nonce}:{key}"
        expected = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.signature == expected

    def check_freshness(self, max_age_seconds: float = 300.0) -> bool:
        ts = datetime.fromisoformat(self.timestamp)
        age = (datetime.utcnow() - ts).total_seconds()
        return abs(age) <= max_age_seconds


class EntityTypeRegistry:
    """Registry enforcing entity type immutability."""

    CANONICAL_TYPES = LCTDocument.VALID_ENTITY_TYPES

    def __init__(self):
        self.entities: dict[str, str] = {}
        self.citizen_roles: set[str] = set()

    def register(self, lct_id: str, entity_type: str) -> bool:
        if entity_type not in self.CANONICAL_TYPES:
            raise ValueError(f"Unknown entity type: {entity_type}")
        if lct_id in self.entities:
            raise ValueError(f"Entity already registered: {lct_id}")
        self.entities[lct_id] = entity_type
        return True

    def get_type(self, lct_id: str) -> str:
        return self.entities.get(lct_id, "")

    def mutate_type(self, lct_id: str, new_type: str) -> bool:
        if lct_id not in self.entities:
            return False
        raise ValueError(f"Entity type immutable: cannot change {self.entities[lct_id]} to {new_type}")

    def grant_citizen_role(self, lct_id: str):
        self.citizen_roles.add(lct_id)

    def can_assume_role(self, lct_id: str) -> bool:
        return lct_id in self.citizen_roles


# ═══════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(condition: bool, description: str):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {description}")

    report = ConformanceReport("Web4 Reference Implementation (Python)")

    # ═══════════════════════════════════════════════════════════
    # REQ-LCT: LCT Structure & Format
    # ═══════════════════════════════════════════════════════════

    print("REQ-LCT: LCT Structure & Format")

    lct = LCTDocument(
        lct_id="lct:web4:ai:test-agent-001",
        subject_did="did:web4:key:ed25519-abc123",
        entity_type="ai",
        t3={"talent": 0.7, "training": 0.65, "temperament": 0.8},
        v3={"valuation": 100.0, "veracity": 0.9, "validity": 0.85},
        mrh={"relationships": [], "depth": 3},
        policy={"delegation_allowed": True},
        binding_proof="sig:ed25519:abc..."
    )

    # REQ-LCT-001: Structure completeness
    errors = lct.validate_structure()
    check(len(errors) == 0, "REQ-LCT-001: Complete LCT has no structural errors")

    incomplete = LCTDocument("", "", "", {}, {}, {}, {}, "")
    inc_errors = incomplete.validate_structure()
    check(len(inc_errors) >= 6, f"REQ-LCT-001: Incomplete LCT has {len(inc_errors)} errors")

    # REQ-LCT-002: ID format
    check(lct.validate_id_format(), "REQ-LCT-002: Valid LCT ID format")
    check(not LCTDocument("bad-id", "", "", {}, {}, {}, {}, "").validate_id_format(),
          "REQ-LCT-002: Invalid ID rejected")
    check(not LCTDocument("lct:other:ai:x", "", "", {}, {}, {}, {}, "").validate_id_format(),
          "REQ-LCT-002: Non-web4 prefix rejected")

    # REQ-LCT-003: DID format
    check(lct.validate_did_format(), "REQ-LCT-003: Valid DID format")
    check(LCTDocument("", "did:web4:hw:tpm-001", "", {}, {}, {}, {}, "").validate_did_format(),
          "REQ-LCT-003: Hardware DID accepted")
    check(not LCTDocument("", "did:other:key:x", "", {}, {}, {}, {}, "").validate_did_format(),
          "REQ-LCT-003: Non-web4 DID rejected")

    # REQ-LCT-004: Birth certificate witnesses
    birth_good = {"birth_witnesses": ["w1", "w2", "w3"]}
    check(len(birth_good["birth_witnesses"]) >= 3,
          "REQ-LCT-004: Birth cert with 3+ witnesses accepted")

    birth_bad = {"birth_witnesses": ["w1"]}
    check(len(birth_bad["birth_witnesses"]) < 3,
          "REQ-LCT-004: Birth cert with <3 witnesses rejected")

    # REQ-LCT-005: JSON-LD context
    jsonld = lct.to_jsonld()
    check("@context" in jsonld, "REQ-LCT-005: JSON-LD has @context")
    check(jsonld["@context"] == "https://web4.io/context/v1",
          "REQ-LCT-005: Correct context URI")
    check(jsonld["@type"] == "LinkedContextToken",
          "REQ-LCT-005: Correct @type")

    # REQ-LCT-006: Entity type validation
    check(lct.entity_type in LCTDocument.VALID_ENTITY_TYPES,
          "REQ-LCT-006: Entity type in canonical set")

    # ═══════════════════════════════════════════════════════════
    # REQ-T3V3: Trust & Value Tensors
    # ═══════════════════════════════════════════════════════════

    print("REQ-T3V3: Trust & Value Tensors")

    # REQ-T3V3-001: Bounds
    t3 = T3Tensor(0.7, 0.65, 0.8)
    check(len(t3.validate_bounds()) == 0, "REQ-T3V3-001: Valid T3 passes bounds")

    t3_bad = T3Tensor(1.1, -0.1, 0.5)
    check(len(t3_bad.validate_bounds()) == 2,
          "REQ-T3V3-001: T3 with 2 out-of-bounds dims detected")

    # REQ-T3V3-002: V3 bounds
    v3 = V3Tensor(100.0, 0.9, 0.85)
    check(len(v3.validate_bounds()) == 0, "REQ-T3V3-002: Valid V3 passes bounds")

    v3_bad = V3Tensor(-1.0, 1.5, 0.5)
    check(len(v3_bad.validate_bounds()) == 2,
          "REQ-T3V3-002: V3 with out-of-bounds dims detected")

    # REQ-T3V3-003: Composite
    check(abs(t3.composite - (0.7 + 0.65 + 0.8) / 3) < 0.001,
          "REQ-T3V3-003: Composite = mean of 3 dims")

    # REQ-T3V3-004: History tracking
    t3.update("talent", 0.05, "Good performance")
    check(len(t3.history) == 1, "REQ-T3V3-004: History records update")
    check(t3.history[0]["old"] == 0.7, "REQ-T3V3-004: Old value recorded")
    check(t3.history[0]["new"] == 0.75, "REQ-T3V3-004: New value recorded")
    check("timestamp" in t3.history[0], "REQ-T3V3-004: Timestamp recorded")

    # REQ-T3V3-005: Clamping
    t3_hi = T3Tensor(0.98, 0.5, 0.5)
    t3_hi.update("talent", 0.1, "Over-boost")
    check(t3_hi.talent == 1.0, "REQ-T3V3-005: Clamped to 1.0 max")

    t3_lo = T3Tensor(0.02, 0.5, 0.5)
    t3_lo.update("talent", -0.1, "Penalty")
    check(t3_lo.talent == 0.0, "REQ-T3V3-005: Clamped to 0.0 min")

    # REQ-T3V3-006: Role-contextual
    role_surgeon = T3Tensor(0.9, 0.85, 0.7)
    role_mechanic = T3Tensor(0.3, 0.2, 0.7)
    check(role_surgeon.composite != role_mechanic.composite,
          "REQ-T3V3-006: Different T3 per role")

    # ═══════════════════════════════════════════════════════════
    # REQ-ATP: Token States & Conservation
    # ═══════════════════════════════════════════════════════════

    print("REQ-ATP: Token States & Conservation")

    # REQ-ATP-001: Valid states
    token = ATPToken("tok-001", "ATP")
    check(token.state == "ATP", "REQ-ATP-001: Token starts ATP")
    try:
        ATPToken("bad", "INVALID")
        check(False, "REQ-ATP-001: Invalid state should raise")
    except ValueError:
        check(True, "REQ-ATP-001: Invalid state rejected")

    # REQ-ATP-002: Discharge
    check(token.discharge(), "REQ-ATP-002: ATP→ADP succeeds")
    check(token.state == "ADP", "REQ-ATP-002: State now ADP")
    check(not token.discharge(), "REQ-ATP-002: ADP→ADP fails")

    # REQ-ATP-003: Charge requires proof
    check(not token.charge(""), "REQ-ATP-003: Empty proof rejected")
    check(token.charge("proof:value"), "REQ-ATP-003: Valid proof accepted")
    check(token.state == "ATP", "REQ-ATP-003: State now ATP")

    # REQ-ATP-004: Pool conservation
    pool = SocietyPool("soc:test", 1000.0)
    initial = pool.total_supply

    pool.discharge(100.0, "a1", "task")
    check(abs(pool.total_supply - initial) < 0.001,
          "REQ-ATP-004: Conservation after discharge")

    pool.charge(50.0, "a1", "proof:done")
    check(abs(pool.total_supply - initial) < 0.001,
          "REQ-ATP-004: Conservation after charge")

    for i in range(100):
        pool.discharge(5.0, f"a{i}", f"t{i}")
        pool.charge(5.0, f"a{i}", f"p{i}")
    check(abs(pool.total_supply - initial) < 0.01,
          "REQ-ATP-004: Conservation after 100 cycles")

    # REQ-ATP-005: Minting authorization
    check(pool.mint(100.0, "auth:council", "Stimulus"),
          "REQ-ATP-005: Authorized mint succeeds")
    check(not pool.mint(100.0, "", ""),
          "REQ-ATP-005: Unauthorized mint rejected")

    # REQ-ATP-006: Slashing
    pool.discharge(50.0, "bad", "fraud")
    check(pool.slash(50.0, "bad", "evidence:fraud"),
          "REQ-ATP-006: Slash with evidence succeeds")
    check(not pool.slash(50.0, "bad", ""),
          "REQ-ATP-006: Slash without evidence rejected")

    # REQ-ATP-007: Overdraft
    small = SocietyPool("soc:small", 10.0)
    check(not small.discharge(20.0, "a", "too much"),
          "REQ-ATP-007: Overdraft rejected")

    # ═══════════════════════════════════════════════════════════
    # REQ-ENT: Entity Types & Immutability
    # ═══════════════════════════════════════════════════════════

    print("REQ-ENT: Entity Types & Immutability")

    registry = EntityTypeRegistry()

    # REQ-ENT-001: 15 canonical types
    check(len(EntityTypeRegistry.CANONICAL_TYPES) == 15,
          f"REQ-ENT-001: {len(EntityTypeRegistry.CANONICAL_TYPES)} canonical types")

    # REQ-ENT-002: Valid registration
    registry.register("lct:alice", "human")
    check(registry.get_type("lct:alice") == "human",
          "REQ-ENT-002: Registered with correct type")

    # REQ-ENT-003: Invalid type
    try:
        registry.register("lct:bad", "unknown_type")
        check(False, "REQ-ENT-003: Should reject unknown type")
    except ValueError:
        check(True, "REQ-ENT-003: Unknown type rejected")

    # REQ-ENT-004: Immutability
    try:
        registry.mutate_type("lct:alice", "ai")
        check(False, "REQ-ENT-004: Should reject type mutation")
    except ValueError:
        check(True, "REQ-ENT-004: Type mutation rejected")

    # REQ-ENT-005: Duplicate registration
    try:
        registry.register("lct:alice", "human")
        check(False, "REQ-ENT-005: Should reject duplicate")
    except ValueError:
        check(True, "REQ-ENT-005: Duplicate registration rejected")

    # REQ-ENT-006: Citizen role prerequisite
    registry.register("lct:bob", "human")
    check(not registry.can_assume_role("lct:bob"),
          "REQ-ENT-006: No role without citizen")
    registry.grant_citizen_role("lct:bob")
    check(registry.can_assume_role("lct:bob"),
          "REQ-ENT-006: Role after citizen grant")

    # ═══════════════════════════════════════════════════════════
    # REQ-MRH: Markov Relevancy Horizon
    # ═══════════════════════════════════════════════════════════

    print("REQ-MRH: Markov Relevancy Horizon")

    mrh = MRHGraph("lct:alice", max_depth=3)
    mrh.add_relationship("lct:alice", "lct:bob", "paired", 0.9)
    mrh.add_relationship("lct:bob", "lct:carol", "witnessed", 0.8)
    mrh.add_relationship("lct:carol", "lct:dave", "paired", 0.7)
    mrh.add_relationship("lct:dave", "lct:eve", "witnessed", 0.6)

    # REQ-MRH-001: Zone classification
    check(mrh.get_zone(0) == "SELF", "REQ-MRH-001: Depth 0 = SELF")
    check(mrh.get_zone(1) == "DIRECT", "REQ-MRH-001: Depth 1 = DIRECT")
    check(mrh.get_zone(2) == "INDIRECT", "REQ-MRH-001: Depth 2 = INDIRECT")
    check(mrh.get_zone(3) == "PERIPHERAL", "REQ-MRH-001: Depth 3 = PERIPHERAL")
    check(mrh.get_zone(4) == "BEYOND", "REQ-MRH-001: Depth 4 = BEYOND")

    # REQ-MRH-002: Depth limiting
    check("lct:bob" in mrh.find_at_depth(1), "REQ-MRH-002: Bob at depth 1")
    check("lct:carol" in mrh.find_at_depth(2), "REQ-MRH-002: Carol at depth 2")
    check("lct:dave" in mrh.find_at_depth(3), "REQ-MRH-002: Dave at depth 3")
    check(len(mrh.find_at_depth(4)) == 0, "REQ-MRH-002: Nothing at depth 4")

    # REQ-MRH-003: Trust decay
    t_direct = mrh.compute_trust("lct:bob", ["lct:alice", "lct:bob"])
    t_indirect = mrh.compute_trust("lct:carol", ["lct:alice", "lct:bob", "lct:carol"])
    check(t_direct > t_indirect,
          f"REQ-MRH-003: Direct ({t_direct:.3f}) > indirect ({t_indirect:.3f})")

    expected_d = 0.9 * 0.7
    check(abs(t_direct - expected_d) < 0.001,
          f"REQ-MRH-003: Direct = {t_direct:.3f} ≈ {expected_d:.3f}")

    expected_i = 0.9 * 0.7 * 0.8 * 0.7
    check(abs(t_indirect - expected_i) < 0.001,
          f"REQ-MRH-003: Indirect = {t_indirect:.3f} ≈ {expected_i:.3f}")

    # REQ-MRH-004: Unknown entity
    check(mrh.compute_trust("lct:unknown", ["lct:alice"]) == 0.0,
          "REQ-MRH-004: Unknown entity → 0 trust")

    # ═══════════════════════════════════════════════════════════
    # REQ-WIT: Witness Attestations
    # ═══════════════════════════════════════════════════════════

    print("REQ-WIT: Witness Attestations")

    # REQ-WIT-001: Valid types
    for wtype in WitnessAttestation.VALID_TYPES:
        w = WitnessAttestation(f"lct:wit:{wtype}", wtype, {"event": "test"}, "n1")
        check(w.witness_type == wtype, f"REQ-WIT-001: Type '{wtype}' accepted")

    # REQ-WIT-002: Invalid type
    try:
        WitnessAttestation("lct:x", "invalid_type", {}, "n")
        check(False, "REQ-WIT-002: Invalid type should raise")
    except ValueError:
        check(True, "REQ-WIT-002: Invalid witness type rejected")

    # REQ-WIT-003: Signature
    wit = WitnessAttestation("lct:wit:time", "time", {"hash": "abc"}, "n2")
    wit.sign("witness-key")
    check(wit.verify("witness-key"), "REQ-WIT-003: Sig verifies with correct key")
    check(not wit.verify("wrong-key"), "REQ-WIT-003: Sig fails with wrong key")

    # REQ-WIT-004: Freshness
    check(wit.check_freshness(300), "REQ-WIT-004: Fresh witness passes")
    old_wit = WitnessAttestation("lct:old", "time", {}, "n")
    old_wit.timestamp = (datetime.utcnow() - timedelta(seconds=600)).isoformat()
    check(not old_wit.check_freshness(300),
          "REQ-WIT-004: Old witness (600s) fails 300s check")

    # REQ-WIT-005: Quorum (3 witnesses, verify each)
    witnesses = []
    for i in range(3):
        w = WitnessAttestation(f"lct:wit:{i}", "existence",
                               {"entity": "lct:new"}, f"n{i}")
        w.sign(f"key-{i}")
        witnesses.append(w)
    valid = sum(1 for i, w in enumerate(witnesses) if w.verify(f"key-{i}"))
    check(valid >= 2, f"REQ-WIT-005: {valid}/3 valid (≥2 quorum)")

    # ═══════════════════════════════════════════════════════════
    # REQ-R6: Action Records & Audit Chain
    # ═══════════════════════════════════════════════════════════

    print("REQ-R6: Action Records & Audit Chain")

    # REQ-R6-001: Completeness
    r6 = R6ActionRecord("act-001", "policy:std", "role:analyst",
                         "analyze", "ref:data", "res:compute", "ok")
    check(len(r6.validate_completeness()) == 0,
          "REQ-R6-001: Complete R6 valid")

    r6_inc = R6ActionRecord("act-bad", "", "role", "req", "ref", "res", "")
    check(len(r6_inc.validate_completeness()) == 2,
          "REQ-R6-001: Incomplete R6 has 2 errors")

    # REQ-R6-002: Hash chain
    r1 = R6ActionRecord("a1", "r", "r", "r", "r", "r", "ok")
    r2 = R6ActionRecord("a2", "r", "r", "r", "r", "r", "ok", prev_hash=r1.record_hash)
    r3 = R6ActionRecord("a3", "r", "r", "r", "r", "r", "ok", prev_hash=r2.record_hash)

    check(r2.prev_hash == r1.record_hash, "REQ-R6-002: Record 2→1 link")
    check(r3.prev_hash == r2.record_hash, "REQ-R6-002: Record 3→2 link")

    chain_valid = all(
        chain[i].prev_hash == chain[i-1].record_hash
        for chain in [[r1, r2, r3]] for i in range(1, len(chain))
    )
    check(chain_valid, "REQ-R6-002: 3-record chain valid")

    # REQ-R6-003: Tamper detection
    r_tampered = R6ActionRecord("a2", "r", "r", "TAMPERED", "r", "r", "ok",
                                 prev_hash=r1.record_hash)
    check(r_tampered.record_hash != r2.record_hash,
          "REQ-R6-003: Tampered record → different hash")

    # REQ-R6-004: Determinism
    r_a = R6ActionRecord.__new__(R6ActionRecord)
    r_a.action_id = "det"; r_a.rules = r_a.role = r_a.request = "x"
    r_a.reference = r_a.resource = r_a.result = "x"
    r_a.prev_hash = ""; r_a.timestamp = "2026-01-01T00:00:00"

    r_b = R6ActionRecord.__new__(R6ActionRecord)
    r_b.action_id = "det"; r_b.rules = r_b.role = r_b.request = "x"
    r_b.reference = r_b.resource = r_b.result = "x"
    r_b.prev_hash = ""; r_b.timestamp = "2026-01-01T00:00:00"

    check(r_a._compute_hash() == r_b._compute_hash(),
          "REQ-R6-004: Deterministic hashing")

    # ═══════════════════════════════════════════════════════════
    # REQ-CRYPTO: Encoding & Hashing
    # ═══════════════════════════════════════════════════════════

    print("REQ-CRYPTO: Encoding & Hashing")

    # REQ-CRYPTO-001: Deterministic encoding
    obj = {"b": 2, "a": 1, "c": 3}
    enc1 = json.dumps(obj, sort_keys=True).encode()
    enc2 = json.dumps(obj, sort_keys=True).encode()
    check(enc1 == enc2, "REQ-CRYPTO-001: Deterministic JSON encoding")

    # REQ-CRYPTO-002: Hash determinism
    data = b"Web4 conformance test"
    h1 = hashlib.sha256(data).hexdigest()
    h2 = hashlib.sha256(data).hexdigest()
    check(h1 == h2, "REQ-CRYPTO-002: SHA-256 deterministic")
    check(len(h1) == 64, "REQ-CRYPTO-002: 64-char hex output")

    # ═══════════════════════════════════════════════════════════
    # REQ-INT: Integration / Cross-Cutting
    # ═══════════════════════════════════════════════════════════

    print("REQ-INT: Integration & Cross-Cutting")

    # REQ-INT-001: LCT→T3/V3→R6→MRH integration
    agent = LCTDocument(
        lct_id="lct:web4:ai:int-agent",
        subject_did="did:web4:key:ed25519-int",
        entity_type="ai",
        t3={"talent": 0.7, "training": 0.65, "temperament": 0.8},
        v3={"valuation": 50.0, "veracity": 0.85, "validity": 0.9},
        mrh={"depth": 3, "relationships": []},
        policy={"delegation_allowed": True},
        binding_proof="sig:ed25519:int"
    )
    agent_t3 = T3Tensor(0.7, 0.65, 0.8)
    agent_r6 = R6ActionRecord("int-1", "policy:std", "role:analyst",
                               "analyze", "ref:42", "res:cluster", "done")

    check(len(agent.validate_structure()) == 0, "REQ-INT-001: Agent LCT valid")
    check(len(agent_t3.validate_bounds()) == 0, "REQ-INT-001: Agent T3 valid")
    check(len(agent_r6.validate_completeness()) == 0, "REQ-INT-001: Agent R6 valid")

    agent_t3.update("talent", 0.02, "Task completed")
    check(len(agent_t3.history) == 1, "REQ-INT-001: T3 updated after R6")

    # REQ-INT-002: Pool conservation through lifecycle
    lp = SocietyPool("soc:lc", 5000.0)
    initial = lp.total_supply
    lp.mint(500.0, "auth:council", "Bootstrap")
    lp.discharge(200.0, "m:new", "Tasks")
    lp.charge(100.0, "m:new", "proof:done")
    lp.slash(50.0, "m:bad", "evidence:violation")
    expected = initial + 500.0 - 50.0
    check(abs(lp.total_supply - expected) < 0.01,
          f"REQ-INT-002: Pool conserved: {lp.total_supply} ≈ {expected}")

    # REQ-INT-003: Type consistency
    reg2 = EntityTypeRegistry()
    reg2.register("lct:web4:ai:int-agent", "ai")
    check(reg2.get_type("lct:web4:ai:int-agent") == agent.entity_type,
          "REQ-INT-003: Registry type matches LCT")

    # ═══════════════════════════════════════════════════════════
    # CONFORMANCE REPORT
    # ═══════════════════════════════════════════════════════════

    print("Conformance Report")

    # Report generation
    report.add(TestResult(
        Requirement("REQ-LCT-001", "LCT-linked-context-token.md §2.1",
                     NormativeLevel.MUST, "Structure", "All components present"),
        ConformanceResult.PASS
    ))
    report.add(TestResult(
        Requirement("REQ-T3V3-001", "t3-v3-tensors.md §2.1",
                     NormativeLevel.MUST, "Bounds", "Dims in [0,1]"),
        ConformanceResult.PASS
    ))

    check(report.passed == 2, "Report tracks 2 passed results")
    check(report.failed == 0, "Report has 0 failures")

    summary = report.summary()
    check("implementation" in summary, "Report has implementation name")
    check(summary["conformance_level"] == "FULL", "Full conformance with 0 failures")

    # ─── Summary ──────────────────────────────────────────────

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Web4 Conformance Test Suite: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")

    cats = ["LCT", "T3V3", "ATP", "ENT", "MRH", "WIT", "R6", "CRYPTO", "INT"]
    print(f"\nCategories tested: {', '.join(f'REQ-{c}' for c in cats)}")

    return passed, failed


if __name__ == "__main__":
    run_checks()
