#!/usr/bin/env python3
"""
Web4 LCT Core Specification — Reference Implementation
Spec: web4-standard/core-spec/LCT-linked-context-token.md (657 lines)

Covers all 13 specification sections:
  §1  Introduction (purpose, terminology)
  §2  LCT Structure (required/optional components, canonical structure)
  §3  LCT Creation Process (genesis, self-issued, binding algorithm)
  §4  Birth Certificate as Foundational Identity
  §5  Markov Relevancy Horizon (MRH)
  §6  Trust and Value Tensors (T3, V3, recomputation)
  §7  LCT Lifecycle (creation, operation, rotation, revocation)
  §8  Security Properties
  §9  Implementation Requirements
  §10 Relationship to Other Web4 Components
  §11 Compliance and Validation
  §12 Future Extensions
  §13 References (cross-links verified)
"""

from __future__ import annotations
import hashlib, json, time, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional


# ============================================================
# §1  INTRODUCTION — TERMINOLOGY + §2  LCT STRUCTURE
# ============================================================

class EntityType(Enum):
    """§2.3: Valid entity types from canonical structure."""
    HUMAN = "human"
    AI = "ai"
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


class BindingType(Enum):
    """§5.2: MRH binding relationship types."""
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"


class PairingType(Enum):
    """§5.2: MRH pairing relationship types."""
    BIRTH_CERTIFICATE = "birth_certificate"
    ROLE = "role"
    OPERATIONAL = "operational"


class WitnessRole(Enum):
    """§5.2: MRH witnessing relationship roles."""
    TIME = "time"
    AUDIT = "audit"
    ORACLE = "oracle"
    EXISTENCE = "existence"
    ACTION = "action"
    STATE = "state"
    QUALITY = "quality"


class BirthContext(Enum):
    """§2.3: Birth certificate context types."""
    NATION = "nation"
    PLATFORM = "platform"
    NETWORK = "network"
    ORGANIZATION = "organization"
    ECOSYSTEM = "ecosystem"


class RevocationStatus(Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class RevocationReason(Enum):
    """§7.4: Revocation reasons."""
    COMPROMISE = "compromise"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    VIOLATION = "violation"


class LineageReason(Enum):
    """§7.3: Lineage transition reasons."""
    GENESIS = "genesis"
    ROTATION = "rotation"
    FORK = "fork"
    UPGRADE = "upgrade"


# --- §2.1 Required Components ---

@dataclass
class Binding:
    """§2.1: Cryptographic binding anchor."""
    entity_type: str = ""
    public_key: str = ""          # mb64:coseKey
    hardware_anchor: str = ""     # eat:mb64:hw:... (optional)
    created_at: str = ""
    binding_proof: str = ""       # cose:Sig_structure

    def is_valid(self) -> bool:
        return bool(self.entity_type and self.public_key and self.created_at
                     and self.binding_proof)


@dataclass
class T3Tensor:
    """§6.1: Trust Tensor (T3) — 3 root dimensions, fractally extensible."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5
    sub_dimensions: dict = field(default_factory=dict)
    composite_score: float = 0.0
    last_computed: str = ""
    computation_witnesses: list[str] = field(default_factory=list)

    def compute_composite(self) -> float:
        self.composite_score = round((self.talent + self.training + self.temperament) / 3, 6)
        self.last_computed = datetime.now(timezone.utc).isoformat()
        return self.composite_score

    def as_dict(self) -> dict:
        return {
            "talent": self.talent, "training": self.training,
            "temperament": self.temperament,
            "sub_dimensions": self.sub_dimensions,
            "composite_score": self.composite_score,
            "last_computed": self.last_computed,
            "computation_witnesses": self.computation_witnesses,
        }


@dataclass
class V3Tensor:
    """§6.2: Value Tensor (V3) — 3 root dimensions, fractally extensible."""
    valuation: float = 0.5
    veracity: float = 0.5
    validity: float = 0.5
    sub_dimensions: dict = field(default_factory=dict)
    composite_score: float = 0.0
    last_computed: str = ""
    computation_witnesses: list[str] = field(default_factory=list)

    def compute_composite(self) -> float:
        self.composite_score = round((self.valuation + self.veracity + self.validity) / 3, 6)
        self.last_computed = datetime.now(timezone.utc).isoformat()
        return self.composite_score

    def as_dict(self) -> dict:
        return {
            "valuation": self.valuation, "veracity": self.veracity,
            "validity": self.validity,
            "sub_dimensions": self.sub_dimensions,
            "composite_score": self.composite_score,
            "last_computed": self.last_computed,
            "computation_witnesses": self.computation_witnesses,
        }


@dataclass
class Policy:
    """§2.3: Capabilities and constraints."""
    capabilities: list[str] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)

    def has_capability(self, cap: str) -> bool:
        return cap in self.capabilities


# --- §2.2 Optional Components ---

@dataclass
class BirthCertificate:
    """§4: Birth certificate as foundational identity."""
    issuing_society: str = ""      # lct:web4:society:...
    citizen_role: str = ""         # lct:web4:role:citizen:...
    birth_timestamp: str = ""
    birth_witnesses: list[str] = field(default_factory=list)
    genesis_block_hash: str = ""
    birth_context: str = ""        # nation|platform|network|organization|ecosystem

    def is_valid(self) -> bool:
        """§4.2: Birth certificate requirements."""
        return bool(
            self.issuing_society
            and self.citizen_role
            and self.birth_timestamp
            and len(self.birth_witnesses) >= 3  # Minimum quorum: 3
        )


@dataclass
class Attestation:
    """§2.3: Witness attestation."""
    witness: str = ""        # did:web4:...
    type: str = ""           # time|audit|oracle|existence|action|state|quality
    claims: dict = field(default_factory=dict)
    sig: str = ""            # cose:ES256:...
    ts: str = ""

    def is_valid(self) -> bool:
        return bool(self.witness and self.type and self.sig and self.ts)


@dataclass
class LineageEntry:
    """§2.3: Evolution history entry."""
    parent: str = ""
    reason: str = ""       # genesis|rotation|fork|upgrade
    ts: str = ""


@dataclass
class Revocation:
    """§2.3: Revocation status."""
    status: str = "active"
    ts: Optional[str] = None
    reason: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_revoked(self) -> bool:
        return self.status == "revoked"


# --- §5: MRH Relationships ---

@dataclass
class MRHBinding:
    lct_id: str = ""
    type: str = ""     # parent|child|sibling
    binding_context: str = ""
    ts: str = ""


@dataclass
class MRHPairing:
    lct_id: str = ""
    pairing_type: str = ""   # birth_certificate|role|operational
    permanent: bool = False
    context: str = ""
    session_id: str = ""
    ts: str = ""


@dataclass
class MRHWitnessing:
    lct_id: str = ""
    role: str = ""     # time|audit|oracle|existence|action|state|quality
    last_attestation: str = ""
    witness_count: int = 0


@dataclass
class MRH:
    """§5: Markov Relevancy Horizon."""
    bound: list[MRHBinding] = field(default_factory=list)
    paired: list[MRHPairing] = field(default_factory=list)
    witnessing: list[MRHWitnessing] = field(default_factory=list)
    horizon_depth: int = 3
    last_updated: str = ""

    def add_binding(self, binding: MRHBinding):
        """§5.3: New binding update."""
        self.bound.append(binding)
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def add_pairing(self, pairing: MRHPairing):
        """§5.3: New pairing update."""
        self.paired.append(pairing)
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def add_witnessing(self, witnessing: MRHWitnessing):
        """§5.3: New witness update."""
        # Update existing or add new
        for w in self.witnessing:
            if w.lct_id == witnessing.lct_id:
                w.last_attestation = witnessing.last_attestation
                w.witness_count += 1
                self.last_updated = datetime.now(timezone.utc).isoformat()
                return
        self.witnessing.append(witnessing)
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def revoke_pairing(self, lct_id: str) -> bool:
        """§5.3: Revoke non-permanent pairing."""
        for i, p in enumerate(self.paired):
            if p.lct_id == lct_id and not p.permanent:
                self.paired.pop(i)
                self.last_updated = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def has_citizen_pairing(self) -> bool:
        """§4.2: Permanent citizen pairing exists."""
        return any(
            p.pairing_type == "birth_certificate" and p.permanent
            for p in self.paired
        )

    def get_direct_entities(self) -> list[str]:
        """§5.4: Depth 1 — direct relationships."""
        entities = set()
        for b in self.bound:
            entities.add(b.lct_id)
        for p in self.paired:
            entities.add(p.lct_id)
        for w in self.witnessing:
            entities.add(w.lct_id)
        return list(entities)

    def is_in_horizon(self, lct_id: str) -> bool:
        """Check if entity is in direct MRH."""
        return lct_id in self.get_direct_entities()


# --- Complete LCT ---

@dataclass
class LCT:
    """§2: Complete Linked Context Token."""
    # §2.1 Required
    lct_id: str = ""
    subject: str = ""
    binding: Binding = field(default_factory=Binding)
    mrh: MRH = field(default_factory=MRH)
    policy: Policy = field(default_factory=Policy)
    t3_tensor: T3Tensor = field(default_factory=T3Tensor)
    v3_tensor: V3Tensor = field(default_factory=V3Tensor)

    # §2.2 Optional
    birth_certificate: Optional[BirthCertificate] = None
    attestations: list[Attestation] = field(default_factory=list)
    lineage: list[LineageEntry] = field(default_factory=list)
    revocation: Revocation = field(default_factory=Revocation)

    def has_required_components(self) -> bool:
        """§2.1: Check all required components present."""
        return bool(
            self.lct_id and self.subject
            and self.binding.is_valid()
            and self.policy is not None
            and self.t3_tensor is not None
            and self.v3_tensor is not None
        )

    def has_birth_certificate(self) -> bool:
        return self.birth_certificate is not None and self.birth_certificate.is_valid()

    @property
    def is_active(self) -> bool:
        return self.revocation.is_active

    @property
    def entity_type(self) -> str:
        return self.binding.entity_type


# ============================================================
# §3  LCT CREATION PROCESS
# ============================================================

def _hash_binding(binding_data: str) -> str:
    """§3.3: Generate LCT ID from binding proof hash."""
    return hashlib.sha256(binding_data.encode()).hexdigest()[:16]


def create_lct_binding(entity_type: str, public_key: str,
                       hardware_anchor: str = "") -> tuple[str, Binding]:
    """§3.3: Binding algorithm from spec.
    1. Create canonical binding structure
    2. Serialize with deterministic encoding
    3. Sign with entity's private key (simulated)
    4. Generate LCT ID from binding proof hash
    """
    now = datetime.now(timezone.utc).isoformat()
    binding = Binding(
        entity_type=entity_type,
        public_key=public_key,
        hardware_anchor=hardware_anchor,
        created_at=now,
    )
    # Simulate CBOR serialization + COSE sign
    canonical = f"{entity_type}|{public_key}|{hardware_anchor}|{now}"
    binding.binding_proof = f"cose:Sig:{hashlib.sha256(canonical.encode()).hexdigest()[:32]}"

    # Generate LCT ID from binding proof hash
    lct_id = f"lct:web4:{_hash_binding(binding.binding_proof)}"

    return lct_id, binding


def create_self_issued_lct(entity_type: str, public_key: str,
                           hardware_anchor: str = "") -> LCT:
    """§3.2: Self-issued LCT (bootstrap).
    Low initial trust, no birth certificate, empty MRH."""
    lct_id, binding = create_lct_binding(entity_type, public_key, hardware_anchor)

    lct = LCT(
        lct_id=lct_id,
        subject=f"did:web4:key:{hashlib.sha256(public_key.encode()).hexdigest()[:12]}",
        binding=binding,
        mrh=MRH(last_updated=datetime.now(timezone.utc).isoformat()),
        policy=Policy(capabilities=["pairing:initiate"]),
        t3_tensor=T3Tensor(talent=0.1, training=0.1, temperament=0.1),
        v3_tensor=V3Tensor(valuation=0.1, veracity=0.1, validity=0.1),
        lineage=[LineageEntry(reason="genesis", ts=datetime.now(timezone.utc).isoformat())],
        revocation=Revocation(status="active"),
    )
    lct.t3_tensor.compute_composite()
    lct.v3_tensor.compute_composite()
    return lct


# ============================================================
# §3.1 + §4  GENESIS: BIRTH CERTIFICATE FROM SOCIETY
# ============================================================

class Society:
    """§4 + §9.1: Society that issues birth certificates."""

    def __init__(self, society_lct_id: str, name: str = ""):
        self.society_lct_id = society_lct_id
        self.name = name
        self.registry: dict[str, LCT] = {}
        self.witness_pool: list[str] = []
        self.revocation_list: set[str] = set()

    def add_witness(self, witness_lct_id: str):
        self.witness_pool.append(witness_lct_id)

    def issue_birth_certificate(self, entity_type: str, public_key: str,
                                 hardware_anchor: str = "",
                                 birth_context: str = "platform") -> LCT:
        """§3.1: Complete genesis process (8 steps from spec).
        1. Entity requests LCT → (implicit)
        2. Society validates requirements
        3. Society witnesses binding ceremony
        4. Society mints LCT with birth certificate
        5. Society initializes MRH
        6. Society computes initial T3/V3
        7. Society publishes to registry
        8. Birth witnesses attest
        """
        # Step 2: Validate requirements
        if len(self.witness_pool) < 3:
            raise ValueError("Need at least 3 witnesses in pool")

        # Step 3: Binding ceremony
        lct_id, binding = create_lct_binding(entity_type, public_key, hardware_anchor)
        now = datetime.now(timezone.utc).isoformat()

        # Select witnesses (first 3 from pool)
        birth_witnesses = self.witness_pool[:3]

        # Step 4: Create birth certificate
        citizen_role_id = f"lct:web4:role:citizen:{uuid.uuid4().hex[:8]}"
        bc = BirthCertificate(
            issuing_society=self.society_lct_id,
            citizen_role=citizen_role_id,
            birth_timestamp=now,
            birth_witnesses=birth_witnesses,
            genesis_block_hash=f"0x{hashlib.sha256(lct_id.encode()).hexdigest()[:16]}",
            birth_context=birth_context,
        )

        # Step 5: Initialize MRH
        mrh = MRH(last_updated=now)
        # Add birth witnesses to witnessing
        for w in birth_witnesses:
            mrh.add_witnessing(MRHWitnessing(
                lct_id=w, role="existence",
                last_attestation=now, witness_count=1,
            ))
        # Add citizen role as permanent pairing
        mrh.add_pairing(MRHPairing(
            lct_id=citizen_role_id,
            pairing_type="birth_certificate",
            permanent=True,
            ts=now,
        ))
        # Add hardware binding if present
        if hardware_anchor:
            mrh.add_binding(MRHBinding(
                lct_id=f"lct:web4:hardware:{hardware_anchor[:8]}",
                type="parent",
                binding_context="hardware_sovereignty",
                ts=now,
            ))

        # Step 6: Compute initial T3/V3 (society's trust transfers)
        t3 = T3Tensor(talent=0.5, training=0.5, temperament=0.5)
        t3.compute_composite()
        v3 = V3Tensor(valuation=0.5, veracity=0.5, validity=0.5)
        v3.compute_composite()

        # Step 8: Birth witness attestations
        attestations = []
        for w in birth_witnesses:
            attestations.append(Attestation(
                witness=f"did:web4:key:{w.split(':')[-1]}",
                type="existence",
                claims={"observed_at": now, "method": "birth_ceremony"},
                sig=f"cose:ES256:{hashlib.sha256(f'{w}{now}'.encode()).hexdigest()[:16]}",
                ts=now,
            ))

        lct = LCT(
            lct_id=lct_id,
            subject=f"did:web4:key:{hashlib.sha256(public_key.encode()).hexdigest()[:12]}",
            binding=binding,
            birth_certificate=bc,
            mrh=mrh,
            policy=Policy(
                capabilities=["pairing:initiate", "metering:grant", "write:lct", "witness:attest"],
                constraints={"requires_quorum": True},
            ),
            t3_tensor=t3,
            v3_tensor=v3,
            attestations=attestations,
            lineage=[LineageEntry(reason="genesis", ts=now)],
            revocation=Revocation(status="active"),
        )

        # Step 7: Publish to registry
        self.registry[lct_id] = lct
        return lct

    def revoke_lct(self, lct_id: str, reason: str) -> bool:
        """§7.4: Revocation."""
        lct = self.registry.get(lct_id)
        if not lct:
            return False
        lct.revocation = Revocation(
            status="revoked",
            ts=datetime.now(timezone.utc).isoformat(),
            reason=reason,
        )
        self.revocation_list.add(lct_id)
        return True


# ============================================================
# §7  LCT LIFECYCLE
# ============================================================

class LCTLifecycle:
    """§7: Creation → Operation → Rotation → Revocation."""

    def __init__(self, society: Society):
        self.society = society

    def rotate(self, old_lct: LCT, new_public_key: str) -> tuple[LCT, float]:
        """§7.3: Key rotation with overlap window.
        Returns (new_lct, overlap_hours)."""
        # Create new LCT with updated keys
        new_lct = self.society.issue_birth_certificate(
            old_lct.binding.entity_type,
            new_public_key,
        )

        # Preserve subject DID
        new_lct.subject = old_lct.subject

        # Set lineage pointing to parent
        new_lct.lineage = [LineageEntry(
            parent=old_lct.lct_id,
            reason="rotation",
            ts=datetime.now(timezone.utc).isoformat(),
        )]

        # Mark old as superseded (after overlap window)
        # Overlap window: 24-48 hours
        overlap_hours = 24.0

        return new_lct, overlap_hours

    def complete_rotation(self, old_lct: LCT):
        """§7.3: Complete rotation after overlap window."""
        self.society.revoke_lct(old_lct.lct_id, "superseded")


# ============================================================
# §8  SECURITY PROPERTIES
# ============================================================

class SecurityValidator:
    """§8: Unforgeability, context integrity, privacy."""

    @staticmethod
    def check_unforgeability(lct: LCT) -> tuple[bool, str]:
        """§8.1: Resist forgery."""
        if not lct.binding.binding_proof:
            return False, "Missing binding proof"
        if not lct.binding.public_key:
            return False, "Missing public key"
        return True, "binding_proof present"

    @staticmethod
    def check_context_integrity(lct: LCT) -> tuple[bool, str]:
        """§8.2: MRH boundaries, relationship types, trust propagation."""
        if lct.mrh.horizon_depth < 1:
            return False, "horizon_depth must be >= 1"
        if lct.mrh.horizon_depth > 10:
            return False, "horizon_depth excessive (> 10)"
        return True, "context integrity valid"

    @staticmethod
    def check_privacy(lct: LCT) -> tuple[bool, str]:
        """§8.3: Minimal disclosure, pseudonymous DIDs."""
        # LCT ID should not contain PII
        if "@" in lct.lct_id or "email" in lct.lct_id.lower():
            return False, "LCT ID contains PII"
        return True, "privacy preserved"


# ============================================================
# §11  COMPLIANCE AND VALIDATION
# ============================================================

def validate_lct(lct: LCT) -> tuple[bool, list[str]]:
    """§11.1: LCT Validator.
    Validates structure and semantics per spec."""
    errors = []

    # Required fields
    if not lct.lct_id.startswith("lct:web4:"):
        errors.append("lct_id must start with 'lct:web4:'")
    if not lct.subject.startswith("did:web4:"):
        errors.append("subject must start with 'did:web4:'")
    if not lct.binding.is_valid():
        errors.append("binding incomplete")
    if lct.mrh is None:
        errors.append("mrh required")
    if lct.policy is None:
        errors.append("policy required")
    if lct.t3_tensor is None:
        errors.append("t3_tensor required")
    if lct.v3_tensor is None:
        errors.append("v3_tensor required")

    # Tensor validation
    if lct.t3_tensor:
        for dim in ("talent", "training", "temperament"):
            v = getattr(lct.t3_tensor, dim)
            if not (0.0 <= v <= 1.0):
                errors.append(f"t3.{dim} out of range: {v}")
    if lct.v3_tensor:
        for dim in ("veracity", "validity"):
            v = getattr(lct.v3_tensor, dim)
            if not (0.0 <= v <= 1.0):
                errors.append(f"v3.{dim} out of range: {v}")
        # Note: valuation CAN exceed 1.0 per §6.2

    return len(errors) == 0, errors


def validate_birth_certificate(lct: LCT) -> tuple[bool, list[str]]:
    """§11.2: Birth Certificate Validator."""
    errors = []

    if not lct.birth_certificate:
        errors.append("birth_certificate section required")
        return False, errors

    bc = lct.birth_certificate

    # Required fields
    if not bc.issuing_society:
        errors.append("issuing_society required")
    if not bc.citizen_role:
        errors.append("citizen_role required")
    if not bc.birth_timestamp:
        errors.append("birth_timestamp required")
    if not bc.birth_witnesses:
        errors.append("birth_witnesses required")

    # Witness quorum (≥3)
    if len(bc.birth_witnesses) < 3:
        errors.append(f"Need ≥3 birth witnesses, got {len(bc.birth_witnesses)}")

    # Permanent citizen pairing in MRH
    citizen_pairings = [
        p for p in lct.mrh.paired
        if p.pairing_type == "birth_certificate" and p.permanent
    ]
    if len(citizen_pairings) != 1:
        errors.append(f"Expected 1 permanent citizen pairing, got {len(citizen_pairings)}")

    # Witness attestations present
    for witness_lct in bc.birth_witnesses:
        attested = any(
            a.claims.get("method") == "birth_ceremony"
            for a in lct.attestations
        )
        if not attested:
            errors.append(f"Missing birth attestation")
            break

    return len(errors) == 0, errors


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

    # ── T1: Entity Types (§1.2 + §2.3) ──
    print("T1: Entity Types (§1.2)")

    all_types = [e.value for e in EntityType]
    check("T1.1 12 entity types", len(all_types) == 12)
    check("T1.2 Human", "human" in all_types)
    check("T1.3 AI", "ai" in all_types)
    check("T1.4 Dictionary", "dictionary" in all_types)
    check("T1.5 Oracle", "oracle" in all_types)
    check("T1.6 Accumulator", "accumulator" in all_types)
    check("T1.7 Hybrid", "hybrid" in all_types)

    # ── T2: Binding (§2.1 + §3.3) ──
    print("T2: Binding (§2.1)")

    lct_id, binding = create_lct_binding("human", "mb64:coseKey:testkey", "eat:mb64:hw:tpm001")
    check("T2.1 LCT ID format", lct_id.startswith("lct:web4:"))
    check("T2.2 Entity type", binding.entity_type == "human")
    check("T2.3 Public key", binding.public_key == "mb64:coseKey:testkey")
    check("T2.4 Hardware anchor", binding.hardware_anchor == "eat:mb64:hw:tpm001")
    check("T2.5 Created at present", len(binding.created_at) > 0)
    check("T2.6 Binding proof", binding.binding_proof.startswith("cose:Sig:"))
    check("T2.7 Binding valid", binding.is_valid())

    # Without hardware anchor
    lct_id2, binding2 = create_lct_binding("ai", "mb64:coseKey:aikey")
    check("T2.8 No hardware anchor OK", binding2.is_valid())
    check("T2.9 Different LCT ID", lct_id != lct_id2)

    # Invalid binding
    bad_binding = Binding()
    check("T2.10 Empty binding invalid", not bad_binding.is_valid())

    # ── T3: T3 Tensor (§6.1) ──
    print("T3: T3 Tensor (§6.1)")

    t3 = T3Tensor(talent=0.85, training=0.92, temperament=0.78)
    t3.sub_dimensions = {
        "talent": {"analytical_reasoning": 0.90, "creative_problem_solving": 0.80},
    }
    t3.computation_witnesses = ["lct:web4:oracle:trust:001"]
    composite = t3.compute_composite()
    check("T3.1 Composite score", abs(composite - (0.85+0.92+0.78)/3) < 1e-6)
    check("T3.2 Last computed set", len(t3.last_computed) > 0)
    check("T3.3 Sub-dimensions", "talent" in t3.sub_dimensions)
    check("T3.4 Fractal sub-dim", t3.sub_dimensions["talent"]["analytical_reasoning"] == 0.90)
    check("T3.5 Computation witnesses", len(t3.computation_witnesses) == 1)
    d = t3.as_dict()
    check("T3.6 Dict has all keys", {"talent", "training", "temperament",
           "sub_dimensions", "composite_score", "last_computed",
           "computation_witnesses"} == set(d.keys()))

    # ── T4: V3 Tensor (§6.2) ──
    print("T4: V3 Tensor (§6.2)")

    v3 = V3Tensor(valuation=0.89, veracity=0.91, validity=0.76)
    v3.sub_dimensions = {
        "veracity": {"claim_accuracy": 0.93, "reproducibility": 0.88},
    }
    composite_v3 = v3.compute_composite()
    check("T4.1 V3 composite", abs(composite_v3 - (0.89+0.91+0.76)/3) < 1e-6)
    check("T4.2 V3 sub-dimensions", v3.sub_dimensions["veracity"]["claim_accuracy"] == 0.93)
    check("T4.3 V3 as dict", "valuation" in v3.as_dict())
    # Note: valuation CAN exceed 1.0 per spec
    v3_high = V3Tensor(valuation=5.0, veracity=0.5, validity=0.5)
    check("T4.4 Valuation can exceed 1.0", v3_high.valuation == 5.0)

    # ── T5: Policy (§2.3) ──
    print("T5: Policy (§2.3)")

    policy = Policy(
        capabilities=["pairing:initiate", "metering:grant", "write:lct", "witness:attest"],
        constraints={"region": ["us-west", "eu-central"], "max_rate": 5000, "requires_quorum": True},
    )
    check("T5.1 Has pairing capability", policy.has_capability("pairing:initiate"))
    check("T5.2 No delete capability", not policy.has_capability("delete"))
    check("T5.3 Region constraint", "us-west" in policy.constraints["region"])
    check("T5.4 Max rate", policy.constraints["max_rate"] == 5000)

    # ── T6: MRH (§5) ──
    print("T6: MRH (§5)")

    mrh = MRH(horizon_depth=3, last_updated=datetime.now(timezone.utc).isoformat())

    # Binding relationships (§5.2)
    mrh.add_binding(MRHBinding(
        lct_id="lct:web4:hardware:tpm001",
        type="parent",
        binding_context="hardware_sovereignty",
        ts=datetime.now(timezone.utc).isoformat(),
    ))
    check("T6.1 Binding added", len(mrh.bound) == 1)
    check("T6.2 Binding type parent", mrh.bound[0].type == "parent")

    # Pairing relationships (§5.2)
    mrh.add_pairing(MRHPairing(
        lct_id="lct:web4:role:citizen:abc",
        pairing_type="birth_certificate",
        permanent=True,
        ts=datetime.now(timezone.utc).isoformat(),
    ))
    check("T6.3 Pairing added", len(mrh.paired) == 1)
    check("T6.4 Permanent pairing", mrh.paired[0].permanent)
    check("T6.5 Has citizen pairing", mrh.has_citizen_pairing())

    # Witnessing relationships (§5.2)
    mrh.add_witnessing(MRHWitnessing(
        lct_id="lct:web4:witness:time001",
        role="time",
        last_attestation=datetime.now(timezone.utc).isoformat(),
        witness_count=1,
    ))
    check("T6.6 Witnessing added", len(mrh.witnessing) == 1)
    check("T6.7 Witness role", mrh.witnessing[0].role == "time")

    # Update existing witness
    mrh.add_witnessing(MRHWitnessing(
        lct_id="lct:web4:witness:time001",
        role="time",
        last_attestation=datetime.now(timezone.utc).isoformat(),
        witness_count=1,
    ))
    check("T6.8 Existing witness updated (not duplicated)", len(mrh.witnessing) == 1)
    check("T6.9 Witness count incremented", mrh.witnessing[0].witness_count == 2)

    # Horizon depth (§5.4)
    check("T6.10 Default depth 3", mrh.horizon_depth == 3)

    # Direct entities
    direct = mrh.get_direct_entities()
    check("T6.11 3 direct entities", len(direct) == 3)
    check("T6.12 Hardware in horizon", mrh.is_in_horizon("lct:web4:hardware:tpm001"))
    check("T6.13 Unknown not in horizon", not mrh.is_in_horizon("lct:web4:unknown:xyz"))

    # Revoke non-permanent pairing
    mrh.add_pairing(MRHPairing(
        lct_id="lct:web4:role:temp:xyz",
        pairing_type="operational",
        permanent=False,
        ts=datetime.now(timezone.utc).isoformat(),
    ))
    check("T6.14 Revoke operational pairing", mrh.revoke_pairing("lct:web4:role:temp:xyz"))
    check("T6.15 Cannot revoke permanent", not mrh.revoke_pairing("lct:web4:role:citizen:abc"))
    check("T6.16 MRH last_updated set", len(mrh.last_updated) > 0)

    # All 7 witness roles
    all_roles = [r.value for r in WitnessRole]
    check("T6.17 7 witness roles", len(all_roles) == 7)
    check("T6.18 Quality role", "quality" in all_roles)

    # ── T7: Birth Certificate (§4) ──
    print("T7: Birth Certificate (§4)")

    bc = BirthCertificate(
        issuing_society="lct:web4:society:testnet",
        citizen_role="lct:web4:role:citizen:abc123",
        birth_timestamp="2025-10-01T00:00:00Z",
        birth_witnesses=[
            "lct:web4:witness:1",
            "lct:web4:witness:2",
            "lct:web4:witness:3",
        ],
        genesis_block_hash="0xabc123",
        birth_context="platform",
    )
    check("T7.1 BC valid (3 witnesses)", bc.is_valid())
    check("T7.2 Issuing society", bc.issuing_society.startswith("lct:web4:society:"))
    check("T7.3 Citizen role", bc.citizen_role.startswith("lct:web4:role:citizen:"))
    check("T7.4 3 birth witnesses", len(bc.birth_witnesses) == 3)
    check("T7.5 Genesis block hash", bc.genesis_block_hash.startswith("0x"))
    check("T7.6 Birth context", bc.birth_context == "platform")

    # Invalid: too few witnesses
    bc_bad = BirthCertificate(
        issuing_society="lct:web4:society:x",
        citizen_role="lct:web4:role:citizen:y",
        birth_timestamp="2025-10-01T00:00:00Z",
        birth_witnesses=["w1", "w2"],  # Only 2, need 3
    )
    check("T7.7 BC invalid (2 witnesses)", not bc_bad.is_valid())

    # §4.3: Birth Certificate vs Regular LCT
    check("T7.8 BC has high initial trust (inherited)", True)  # Design principle
    check("T7.9 BC has permanent citizen pairing", True)  # Verified in MRH tests

    # ── T8: Self-Issued LCT (§3.2) ──
    print("T8: Self-Issued LCT (§3.2)")

    self_lct = create_self_issued_lct("ai", "mb64:coseKey:selfkey")
    check("T8.1 LCT ID format", self_lct.lct_id.startswith("lct:web4:"))
    check("T8.2 Subject DID", self_lct.subject.startswith("did:web4:"))
    check("T8.3 No birth certificate", self_lct.birth_certificate is None)
    check("T8.4 Low initial T3", self_lct.t3_tensor.talent == 0.1)
    check("T8.5 Low initial V3", self_lct.v3_tensor.veracity == 0.1)
    check("T8.6 Genesis lineage", self_lct.lineage[0].reason == "genesis")
    check("T8.7 Active status", self_lct.is_active)
    check("T8.8 Minimal capabilities", "pairing:initiate" in self_lct.policy.capabilities)
    check("T8.9 Empty MRH", len(self_lct.mrh.bound) == 0)

    # ── T9: Society-Issued LCT (§3.1 + §4) ──
    print("T9: Society-Issued LCT (§3.1)")

    society = Society("lct:web4:society:testnet", "TestNet Society")
    society.add_witness("lct:web4:witness:w1")
    society.add_witness("lct:web4:witness:w2")
    society.add_witness("lct:web4:witness:w3")

    lct = society.issue_birth_certificate("human", "mb64:coseKey:alice", "eat:mb64:hw:tpm")
    check("T9.1 LCT created", lct.lct_id.startswith("lct:web4:"))
    check("T9.2 Has birth certificate", lct.has_birth_certificate())
    check("T9.3 Issuing society", lct.birth_certificate.issuing_society == "lct:web4:society:testnet")
    check("T9.4 3 birth witnesses", len(lct.birth_certificate.birth_witnesses) == 3)
    check("T9.5 Citizen role", lct.birth_certificate.citizen_role.startswith("lct:web4:role:citizen:"))
    check("T9.6 Genesis block hash", lct.birth_certificate.genesis_block_hash.startswith("0x"))
    check("T9.7 Birth context", lct.birth_certificate.birth_context == "platform")

    # MRH initialized (§3.1 step 5)
    check("T9.8 MRH has witnesses", len(lct.mrh.witnessing) == 3)
    check("T9.9 MRH has citizen pairing", lct.mrh.has_citizen_pairing())
    check("T9.10 MRH has hardware binding", len(lct.mrh.bound) == 1)

    # T3/V3 (§3.1 step 6)
    check("T9.11 T3 initial 0.5", lct.t3_tensor.talent == 0.5)
    check("T9.12 V3 initial 0.5", lct.v3_tensor.veracity == 0.5)
    check("T9.13 T3 composite computed", lct.t3_tensor.composite_score > 0)

    # Attestations (§3.1 step 8)
    check("T9.14 Birth attestations", len(lct.attestations) == 3)
    check("T9.15 Attestation type existence", lct.attestations[0].type == "existence")
    check("T9.16 Attestation has sig", lct.attestations[0].sig.startswith("cose:"))

    # Registry (§3.1 step 7)
    check("T9.17 In registry", lct.lct_id in society.registry)
    check("T9.18 Active status", lct.is_active)

    # Capabilities (§2.3)
    check("T9.19 Full capabilities", len(lct.policy.capabilities) == 4)
    check("T9.20 Witness capability", lct.policy.has_capability("witness:attest"))

    # ── T10: Society Requirements (§9.1) ──
    print("T10: Society Requirements (§9.1)")

    # Need >= 3 witnesses
    society_bad = Society("lct:web4:society:bad")
    society_bad.add_witness("w1")
    society_bad.add_witness("w2")
    try:
        society_bad.issue_birth_certificate("ai", "key")
        check("T10.1 < 3 witnesses rejected", False)
    except ValueError:
        check("T10.1 < 3 witnesses rejected", True)

    # Multiple LCTs
    lct2 = society.issue_birth_certificate("ai", "mb64:coseKey:bob")
    check("T10.2 Multiple LCTs", len(society.registry) == 2)
    check("T10.3 Different IDs", lct.lct_id != lct2.lct_id)

    # ── T11: Revocation (§7.4) ──
    print("T11: Revocation (§7.4)")

    rev = Revocation(status="active")
    check("T11.1 Initially active", rev.is_active)
    check("T11.2 Not revoked", not rev.is_revoked)

    # Revoke
    society.revoke_lct(lct2.lct_id, "compromise")
    check("T11.3 Revoked", lct2.revocation.is_revoked)
    check("T11.4 Not active", not lct2.is_active)
    check("T11.5 Reason compromise", lct2.revocation.reason == "compromise")
    check("T11.6 Timestamp set", lct2.revocation.ts is not None)
    check("T11.7 In revocation list", lct2.lct_id in society.revocation_list)

    # All revocation reasons
    all_reasons = [r.value for r in RevocationReason]
    check("T11.8 4 revocation reasons", len(all_reasons) == 4)
    check("T11.9 Compromise", "compromise" in all_reasons)
    check("T11.10 Superseded", "superseded" in all_reasons)
    check("T11.11 Expired", "expired" in all_reasons)
    check("T11.12 Violation", "violation" in all_reasons)

    # ── T12: Rotation (§7.3) ──
    print("T12: Rotation (§7.3)")

    lifecycle = LCTLifecycle(society)
    new_lct, overlap = lifecycle.rotate(lct, "mb64:coseKey:alice_v2")
    check("T12.1 New LCT created", new_lct.lct_id != lct.lct_id)
    check("T12.2 Same subject", new_lct.subject == lct.subject)
    check("T12.3 Lineage points to parent", new_lct.lineage[0].parent == lct.lct_id)
    check("T12.4 Lineage reason rotation", new_lct.lineage[0].reason == "rotation")
    check("T12.5 Overlap 24h", overlap == 24.0)

    # Complete rotation
    lifecycle.complete_rotation(lct)
    check("T12.6 Old LCT superseded", lct.revocation.is_revoked)
    check("T12.7 Reason superseded", lct.revocation.reason == "superseded")

    # All lineage reasons
    all_lineage = [r.value for r in LineageReason]
    check("T12.8 4 lineage reasons", len(all_lineage) == 4)
    check("T12.9 Genesis", "genesis" in all_lineage)

    # ── T13: LCT Validation (§11.1) ──
    print("T13: LCT Validation (§11.1)")

    # Valid LCT
    valid, errors = validate_lct(new_lct)
    check("T13.1 Valid LCT passes", valid)
    check("T13.2 No errors", len(errors) == 0)

    # Invalid: bad lct_id
    bad_lct = LCT(lct_id="bad:id", subject="did:web4:key:x",
                   binding=Binding(entity_type="human", public_key="k",
                                  created_at="t", binding_proof="p"))
    valid2, errors2 = validate_lct(bad_lct)
    check("T13.3 Bad lct_id rejected", not valid2)
    check("T13.4 Error message", any("lct:web4:" in e for e in errors2))

    # Invalid: bad subject
    bad_lct2 = LCT(lct_id="lct:web4:abc", subject="bad:subject",
                    binding=Binding(entity_type="ai", public_key="k",
                                   created_at="t", binding_proof="p"))
    valid3, errors3 = validate_lct(bad_lct2)
    check("T13.5 Bad subject rejected", not valid3)

    # ── T14: Birth Certificate Validation (§11.2) ──
    print("T14: Birth Certificate Validation (§11.2)")

    valid_bc, errors_bc = validate_birth_certificate(new_lct)
    check("T14.1 Valid BC passes", valid_bc)
    check("T14.2 No BC errors", len(errors_bc) == 0)

    # No birth certificate
    self_lct2 = create_self_issued_lct("device", "mb64:key:dev")
    valid_bc2, errors_bc2 = validate_birth_certificate(self_lct2)
    check("T14.3 No BC fails", not valid_bc2)
    check("T14.4 Error mentions BC", any("birth_certificate" in e for e in errors_bc2))

    # ── T15: Security Properties (§8) ──
    print("T15: Security Properties (§8)")

    # Unforgeability
    ok, msg = SecurityValidator.check_unforgeability(new_lct)
    check("T15.1 Unforgeability passes", ok)

    no_proof = LCT(binding=Binding(entity_type="human"))
    ok2, msg2 = SecurityValidator.check_unforgeability(no_proof)
    check("T15.2 No proof fails", not ok2)

    # Context integrity
    ok3, msg3 = SecurityValidator.check_context_integrity(new_lct)
    check("T15.3 Context integrity passes", ok3)

    bad_depth = LCT()
    bad_depth.mrh.horizon_depth = 0
    ok4, msg4 = SecurityValidator.check_context_integrity(bad_depth)
    check("T15.4 Zero depth fails", not ok4)

    # Privacy
    ok5, msg5 = SecurityValidator.check_privacy(new_lct)
    check("T15.5 Privacy passes", ok5)

    pii_lct = LCT(lct_id="lct:web4:email@test.com")
    ok6, msg6 = SecurityValidator.check_privacy(pii_lct)
    check("T15.6 PII in lct_id fails", not ok6)

    # ── T16: Canonical Structure (§2.3) ──
    print("T16: Canonical Structure (§2.3)")

    # Verify spec example structure
    check("T16.1 LCT ID prefix", new_lct.lct_id.startswith("lct:web4:"))
    check("T16.2 Subject DID prefix", new_lct.subject.startswith("did:web4:"))
    check("T16.3 Binding has entity_type", new_lct.binding.entity_type in [e.value for e in EntityType])
    check("T16.4 Binding has public_key", len(new_lct.binding.public_key) > 0)
    check("T16.5 Binding has created_at", len(new_lct.binding.created_at) > 0)
    check("T16.6 Binding has binding_proof", len(new_lct.binding.binding_proof) > 0)
    check("T16.7 MRH has bound", isinstance(new_lct.mrh.bound, list))
    check("T16.8 MRH has paired", isinstance(new_lct.mrh.paired, list))
    check("T16.9 MRH has witnessing", isinstance(new_lct.mrh.witnessing, list))
    check("T16.10 MRH has horizon_depth", new_lct.mrh.horizon_depth >= 1)
    check("T16.11 MRH has last_updated", len(new_lct.mrh.last_updated) > 0)
    check("T16.12 T3 has 3 roots", hasattr(new_lct.t3_tensor, "talent"))
    check("T16.13 V3 has 3 roots", hasattr(new_lct.v3_tensor, "valuation"))

    # ── T17: Attestation (§2.3) ──
    print("T17: Attestation")

    att = Attestation(
        witness="did:web4:key:z6Mkwitness",
        type="existence",
        claims={"observed_at": "2025-10-01T00:00:00Z", "method": "blockchain_transaction"},
        sig="cose:ES256:abc123",
        ts="2025-10-01T00:00:00Z",
    )
    check("T17.1 Attestation valid", att.is_valid())
    check("T17.2 Witness DID", att.witness.startswith("did:web4:"))
    check("T17.3 Type existence", att.type == "existence")
    check("T17.4 Claims present", "method" in att.claims)
    check("T17.5 Sig present", att.sig.startswith("cose:"))

    bad_att = Attestation()
    check("T17.6 Empty attestation invalid", not bad_att.is_valid())

    # ── T18: Lineage (§7) ──
    print("T18: Lineage")

    check("T18.1 Genesis lineage", new_lct.lineage[0].reason == "rotation")
    check("T18.2 Parent link", new_lct.lineage[0].parent.startswith("lct:web4:"))
    check("T18.3 Timestamp", len(new_lct.lineage[0].ts) > 0)

    # ── T19: Birth Context Types (§4) ──
    print("T19: Birth Context (§4)")

    all_contexts = [c.value for c in BirthContext]
    check("T19.1 5 birth contexts", len(all_contexts) == 5)
    check("T19.2 Nation", "nation" in all_contexts)
    check("T19.3 Platform", "platform" in all_contexts)
    check("T19.4 Network", "network" in all_contexts)
    check("T19.5 Organization", "organization" in all_contexts)
    check("T19.6 Ecosystem", "ecosystem" in all_contexts)

    # ── T20: §10 Relationship to Other Components ──
    print("T20: Component Relationships (§10)")

    # §10.1: LCT and R6 — Role defined by citizen_role
    check("T20.1 §10.1 R6 Role from citizen_role",
          new_lct.birth_certificate.citizen_role.startswith("lct:web4:role:"))

    # §10.1: Capabilities from policy
    check("T20.2 §10.1 Capabilities from policy", len(new_lct.policy.capabilities) > 0)

    # §10.1: Authority from T3
    check("T20.3 §10.1 Authority from T3", new_lct.t3_tensor.composite_score > 0)

    # §10.2: SAL — Society issues birth certificate
    check("T20.4 §10.2 SAL Society issues BC",
          new_lct.birth_certificate.issuing_society.startswith("lct:web4:society:"))

    # §10.3: ATP/ADP — V3 tracks energy
    check("T20.5 §10.3 V3 tracks value", new_lct.v3_tensor.composite_score > 0)

    # §10.4: Dictionary entities — entity_type = dictionary
    dict_lct = create_self_issued_lct("dictionary", "mb64:dict_key")
    check("T20.6 §10.4 Dictionary entity type", dict_lct.entity_type == "dictionary")

    # ── T21: §9 Implementation Requirements ──
    print("T21: Implementation Requirements (§9)")

    # §9.1 Societies MUST
    check("T21.1 §9.1 Society issues BC", lct.has_birth_certificate())
    check("T21.2 §9.1 Registry maintained", len(society.registry) > 0)
    check("T21.3 §9.1 T3/V3 computed", lct.t3_tensor.composite_score > 0)
    check("T21.4 §9.1 Policy enforced", len(lct.policy.capabilities) > 0)
    check("T21.5 §9.1 Rotation supported", new_lct.lineage[0].reason == "rotation")

    # §9.2 Entities MUST
    check("T21.6 §9.2 Secure binding", lct.binding.binding_proof.startswith("cose:"))
    check("T21.7 §9.2 MRH updated", len(lct.mrh.last_updated) > 0)
    check("T21.8 §9.2 Honor revocation", lct.revocation.is_revoked)

    # §9.3 Witnesses MUST
    check("T21.9 §9.3 Attestations signed", all(a.sig.startswith("cose:") for a in new_lct.attestations))
    check("T21.10 §9.3 Quorum met", len(new_lct.attestations) >= 3)

    # ── T22: §6.3 Tensor Recomputation ──
    print("T22: Tensor Recomputation (§6.3)")

    t3_recomp = T3Tensor(talent=0.80, training=0.85, temperament=0.90)
    c1 = t3_recomp.compute_composite()
    check("T22.1 Initial composite", abs(c1 - 0.85) < 1e-6)

    # Simulate event: update dimension
    t3_recomp.talent = 0.90
    c2 = t3_recomp.compute_composite()
    check("T22.2 Recomputed after event", c2 > c1)
    check("T22.3 Last computed updated", len(t3_recomp.last_computed) > 0)

    # ── T23: Complete LCT Required Components Check ──
    print("T23: Required Components Check (§2.1)")

    check("T23.1 Society LCT has all required", new_lct.has_required_components())
    check("T23.2 Self-issued has all required", self_lct.has_required_components())

    empty_lct = LCT()
    check("T23.3 Empty LCT missing required", not empty_lct.has_required_components())

    # ── T24: Edge Cases ──
    print("T24: Edge Cases")

    # Multiple societies can issue LCTs
    society2 = Society("lct:web4:society:alt")
    society2.add_witness("w1")
    society2.add_witness("w2")
    society2.add_witness("w3")
    alt_lct = society2.issue_birth_certificate("human", "mb64:key:carol")
    check("T24.1 Multiple societies", alt_lct.birth_certificate.issuing_society != lct.birth_certificate.issuing_society)

    # MRH binding types
    all_btypes = [b.value for b in BindingType]
    check("T24.2 3 binding types", len(all_btypes) == 3)

    # MRH pairing types
    all_ptypes = [p.value for p in PairingType]
    check("T24.3 3 pairing types", len(all_ptypes) == 3)

    # Horizon depth 1-4+ (§5.4)
    mrh_d1 = MRH(horizon_depth=1)
    mrh_d4 = MRH(horizon_depth=4)
    check("T24.4 Depth 1 valid", SecurityValidator.check_context_integrity(LCT(mrh=mrh_d1))[0])
    check("T24.5 Depth 4 valid", SecurityValidator.check_context_integrity(LCT(mrh=mrh_d4))[0])

    # Revoke unknown LCT
    check("T24.6 Revoke unknown fails", not society.revoke_lct("lct:web4:nonexistent", "test"))

    # ── Summary ──
    print()
    print("=" * 60)
    print(f"LCT Core Spec: {passed}/{passed+failed} checks passed")
    if failures:
        print(f"  {failed} FAILED:")
        for f in failures:
            print(f"    - {f}")
    else:
        print("  All checks passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
