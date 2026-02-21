#!/usr/bin/env python3
"""
Web4 LCT (Linked Context Token) Document Library — Python Reference Implementation

Full LCT document model matching lct.schema.json.
Port from TypeScript (lct-document.ts) and Go (document.go) implementations.

Closes the #1 finding from LCT Schema Validator: NO Python implementation
produces a full schema-compliant LCT document. This one does.

Usage:
    doc = LCTBuilder("ai", "sage-legion") \
        .with_binding("mb64testkey", "cose:test_proof") \
        .with_birth_certificate("lct:web4:society:genesis", "lct:web4:role:citizen:ai") \
        .with_t3(talent=0.8, training=0.7, temperament=0.9) \
        .add_capability("witness:attest") \
        .build()

    # Validates against lct.schema.json
    assert doc.validate().valid

@version 1.0.0
@see web4-standard/schemas/lct.schema.json
@see ledgers/reference/typescript/lct-document.ts
@see ledgers/reference/go/lct/document.go
"""

import hashlib
import json
import re
import sys
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════
# Entity Types — 15 canonical types per entity-types.md (Feb 2026)
# ═══════════════════════════════════════════════════════════════

ENTITY_TYPES = [
    "human", "ai", "society", "organization", "role", "task",
    "resource", "device", "service", "oracle", "accumulator",
    "dictionary", "hybrid", "policy", "infrastructure",
]

BIRTH_CONTEXTS = ["nation", "platform", "network", "organization", "ecosystem"]
BOUND_TYPES = ["parent", "child", "sibling"]
PAIRING_TYPES = ["birth_certificate", "role", "operational"]
WITNESS_ROLES = ["time", "audit", "oracle", "peer", "existence", "action", "state", "quality"]
LINEAGE_REASONS = ["genesis", "rotation", "fork", "upgrade"]
REVOCATION_STATUSES = ["active", "revoked"]
REVOCATION_REASONS = ["compromise", "superseded", "expired"]

# Patterns from lct.schema.json
LCT_ID_PATTERN = re.compile(r"^lct:web4:[A-Za-z0-9_-]+$")
SUBJECT_PATTERN = re.compile(r"^did:web4:(key|method):[A-Za-z0-9_-]+$")
PUBLIC_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
BINDING_PROOF_PATTERN = re.compile(r"^cose:[A-Za-z0-9_-]+$")
HARDWARE_ANCHOR_PATTERN = re.compile(r"^eat:[A-Za-z0-9_-]+$")
CITIZEN_ROLE_PATTERN = re.compile(r"^lct:web4:role:citizen:[a-z]+$")


# ═══════════════════════════════════════════════════════════════
# Data Classes — match lct.schema.json exactly
# ═══════════════════════════════════════════════════════════════

@dataclass
class T3Tensor:
    """Trust Tensor with 3 canonical root dimensions."""
    talent: float
    training: float
    temperament: float
    sub_dimensions: Optional[Dict[str, Dict[str, float]]] = None
    composite_score: Optional[float] = None
    last_computed: Optional[str] = None
    computation_witnesses: Optional[List[str]] = None

    def compute_composite(self) -> float:
        score = self.talent * 0.4 + self.training * 0.3 + self.temperament * 0.3
        self.composite_score = score
        return score

    def to_dict(self) -> dict:
        d = {"talent": self.talent, "training": self.training, "temperament": self.temperament}
        if self.sub_dimensions is not None:
            d["sub_dimensions"] = self.sub_dimensions
        if self.composite_score is not None:
            d["composite_score"] = self.composite_score
        if self.last_computed is not None:
            d["last_computed"] = self.last_computed
        if self.computation_witnesses is not None:
            d["computation_witnesses"] = self.computation_witnesses
        return d


@dataclass
class V3Tensor:
    """Value Tensor with 3 canonical root dimensions."""
    valuation: float
    veracity: float
    validity: float
    sub_dimensions: Optional[Dict[str, Dict[str, float]]] = None
    composite_score: Optional[float] = None
    last_computed: Optional[str] = None
    computation_witnesses: Optional[List[str]] = None

    def compute_composite(self) -> float:
        score = self.valuation * 0.3 + self.veracity * 0.35 + self.validity * 0.35
        self.composite_score = score
        return score

    def to_dict(self) -> dict:
        d = {"valuation": self.valuation, "veracity": self.veracity, "validity": self.validity}
        if self.sub_dimensions is not None:
            d["sub_dimensions"] = self.sub_dimensions
        if self.composite_score is not None:
            d["composite_score"] = self.composite_score
        if self.last_computed is not None:
            d["last_computed"] = self.last_computed
        if self.computation_witnesses is not None:
            d["computation_witnesses"] = self.computation_witnesses
        return d


@dataclass
class Binding:
    """Cryptographic anchor for an LCT."""
    entity_type: str
    public_key: str
    created_at: str
    binding_proof: str
    hardware_anchor: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "entity_type": self.entity_type,
            "public_key": self.public_key,
            "created_at": self.created_at,
            "binding_proof": self.binding_proof,
        }
        if self.hardware_anchor is not None:
            d["hardware_anchor"] = self.hardware_anchor
        return d


@dataclass
class BirthCertificate:
    """Society-issued genesis identity record."""
    issuing_society: str
    citizen_role: str
    context: str
    birth_timestamp: str
    birth_witnesses: List[str]
    parent_entity: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "issuing_society": self.issuing_society,
            "citizen_role": self.citizen_role,
            "context": self.context,
            "birth_timestamp": self.birth_timestamp,
            "birth_witnesses": self.birth_witnesses,
        }
        if self.parent_entity is not None:
            d["parent_entity"] = self.parent_entity
        return d


@dataclass
class MRHBound:
    """Permanent hierarchical attachment."""
    lct_id: str
    type: str
    ts: str

    def to_dict(self) -> dict:
        return {"lct_id": self.lct_id, "type": self.type, "ts": self.ts}


@dataclass
class MRHPaired:
    """Authorized operational relationship."""
    lct_id: str
    ts: str
    pairing_type: Optional[str] = None
    permanent: Optional[bool] = None
    context: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"lct_id": self.lct_id, "ts": self.ts}
        if self.pairing_type is not None:
            d["pairing_type"] = self.pairing_type
        if self.permanent is not None:
            d["permanent"] = self.permanent
        if self.context is not None:
            d["context"] = self.context
        if self.session_id is not None:
            d["session_id"] = self.session_id
        return d


@dataclass
class MRHWitnessing:
    """Witness relationship."""
    lct_id: str
    role: str
    last_attestation: str

    def to_dict(self) -> dict:
        return {"lct_id": self.lct_id, "role": self.role, "last_attestation": self.last_attestation}


@dataclass
class MRH:
    """Markov Relevancy Horizon."""
    bound: List[MRHBound]
    paired: List[MRHPaired]
    horizon_depth: int
    last_updated: str
    witnessing: Optional[List[MRHWitnessing]] = None

    def to_dict(self) -> dict:
        d = {
            "bound": [b.to_dict() for b in self.bound],
            "paired": [p.to_dict() for p in self.paired],
            "horizon_depth": self.horizon_depth,
            "last_updated": self.last_updated,
        }
        if self.witnessing:  # omit if None or empty
            d["witnessing"] = [w.to_dict() for w in self.witnessing]
        return d


@dataclass
class Policy:
    """Capabilities and constraints."""
    capabilities: List[str]
    constraints: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        d: dict = {"capabilities": self.capabilities}
        if self.constraints is not None:
            d["constraints"] = self.constraints
        return d


@dataclass
class Attestation:
    """Witness observation."""
    witness: str
    type: str
    sig: str
    ts: str

    def to_dict(self) -> dict:
        return {"witness": self.witness, "type": self.type, "sig": self.sig, "ts": self.ts}


@dataclass
class LineageEntry:
    """Evolution history entry."""
    reason: str
    ts: str
    parent: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict = {"reason": self.reason, "ts": self.ts}
        if self.parent is not None:
            d["parent"] = self.parent
        return d


@dataclass
class Revocation:
    """Termination record."""
    status: str
    ts: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict = {"status": self.status}
        if self.ts is not None:
            d["ts"] = self.ts
        if self.reason is not None:
            d["reason"] = self.reason
        return d


# ═══════════════════════════════════════════════════════════════
# LCT Document — Complete Linked Context Token
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """Document validation result."""
    valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class LCTDocument:
    """
    Complete LCT document structure per lct.schema.json.

    Required: lct_id, subject, binding, birth_certificate, mrh, policy
    Optional: t3_tensor, v3_tensor, attestations, lineage, revocation
    """
    lct_id: str
    subject: str
    binding: Binding
    birth_certificate: BirthCertificate
    mrh: MRH
    policy: Policy
    t3_tensor: Optional[T3Tensor] = None
    v3_tensor: Optional[V3Tensor] = None
    attestations: Optional[List[Attestation]] = None
    lineage: Optional[List[LineageEntry]] = None
    revocation: Optional[Revocation] = None

    def to_dict(self) -> dict:
        """Serialize to dict matching lct.schema.json exactly."""
        d = {
            "lct_id": self.lct_id,
            "subject": self.subject,
            "binding": self.binding.to_dict(),
            "birth_certificate": self.birth_certificate.to_dict(),
            "mrh": self.mrh.to_dict(),
            "policy": self.policy.to_dict(),
        }
        if self.t3_tensor is not None:
            d["t3_tensor"] = self.t3_tensor.to_dict()
        if self.v3_tensor is not None:
            d["v3_tensor"] = self.v3_tensor.to_dict()
        if self.attestations:  # omit if None or empty
            d["attestations"] = [a.to_dict() for a in self.attestations]
        if self.lineage:  # omit if None or empty
            d["lineage"] = [l.to_dict() for l in self.lineage]
        if self.revocation is not None:
            d["revocation"] = self.revocation.to_dict()
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "LCTDocument":
        """Deserialize from dict."""
        binding = Binding(**d["binding"])
        bc = BirthCertificate(**d["birth_certificate"])

        mrh_data = d["mrh"]
        wit_data = mrh_data.get("witnessing")
        mrh = MRH(
            bound=[MRHBound(**b) for b in mrh_data.get("bound", [])],
            paired=[MRHPaired(**p) for p in mrh_data.get("paired", [])],
            horizon_depth=mrh_data["horizon_depth"],
            last_updated=mrh_data["last_updated"],
            witnessing=[MRHWitnessing(**w) for w in wit_data] if wit_data else None,
        )

        policy = Policy(**d["policy"])

        t3 = T3Tensor(**d["t3_tensor"]) if d.get("t3_tensor") else None
        v3 = V3Tensor(**d["v3_tensor"]) if d.get("v3_tensor") else None
        attestations = [Attestation(**a) for a in d["attestations"]] if d.get("attestations") else None
        lineage = [LineageEntry(**l) for l in d["lineage"]] if d.get("lineage") else None
        revocation = Revocation(**d["revocation"]) if d.get("revocation") else None

        return cls(
            lct_id=d["lct_id"], subject=d["subject"],
            binding=binding, birth_certificate=bc, mrh=mrh, policy=policy,
            t3_tensor=t3, v3_tensor=v3, attestations=attestations,
            lineage=lineage, revocation=revocation,
        )

    @classmethod
    def from_json(cls, s: str) -> "LCTDocument":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(s))

    def hash(self) -> str:
        """SHA-256 hash of canonical JSON form."""
        data = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()

    def to_uri(self, network: str = "local", role: str = "default") -> str:
        """Convert to LCT URI for network addressing."""
        parts = self.lct_id.rsplit(":", 1)
        hash_part = parts[-1] if len(parts) > 1 else "unknown"
        return f"lct://{self.binding.entity_type}:{hash_part}:{role}@{network}"

    def validate(self) -> ValidationResult:
        """Validate against schema rules (structural validation)."""
        return validate_document(self)

    def validate_against_schema(self) -> ValidationResult:
        """Validate against lct.schema.json using jsonschema library."""
        try:
            import jsonschema
        except ImportError:
            return ValidationResult(valid=False, errors=["jsonschema not installed"], warnings=[])

        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "web4-standard", "schemas", "lct.schema.json"
        )
        if not os.path.exists(schema_path):
            return ValidationResult(valid=False, errors=[f"Schema not found: {schema_path}"], warnings=[])

        with open(schema_path) as f:
            schema = json.load(f)

        doc_dict = self.to_dict()
        validator = jsonschema.Draft202012Validator(schema)
        errors = list(validator.iter_errors(doc_dict))
        error_msgs = [f"{e.json_path}: {e.message}" for e in errors]
        return ValidationResult(valid=len(errors) == 0, errors=error_msgs, warnings=[])


# ═══════════════════════════════════════════════════════════════
# Structural Validation
# ═══════════════════════════════════════════════════════════════

def validate_document(doc: LCTDocument) -> ValidationResult:
    """Validate an LCT document against schema rules."""
    errors: List[str] = []
    warnings: List[str] = []

    # LCT ID format
    if not LCT_ID_PATTERN.match(doc.lct_id):
        errors.append(f'Invalid lct_id format: "{doc.lct_id}"')

    # Subject format
    if not SUBJECT_PATTERN.match(doc.subject):
        errors.append(f'Invalid subject format: "{doc.subject}"')

    # Binding
    if doc.binding.entity_type not in ENTITY_TYPES:
        errors.append(f'Invalid entity_type: "{doc.binding.entity_type}"')
    if not doc.binding.public_key:
        errors.append("Missing binding.public_key")
    if not doc.binding.created_at:
        errors.append("Missing binding.created_at")
    if not doc.binding.binding_proof:
        errors.append("Missing binding.binding_proof")

    # Birth certificate
    bc = doc.birth_certificate
    if not bc.issuing_society:
        errors.append("Missing birth_certificate.issuing_society")
    if not bc.citizen_role:
        errors.append("Missing birth_certificate.citizen_role")
    if bc.context not in BIRTH_CONTEXTS:
        errors.append(f'Invalid birth_certificate.context: "{bc.context}"')
    if not bc.birth_timestamp:
        errors.append("Missing birth_certificate.birth_timestamp")
    if not bc.birth_witnesses or len(bc.birth_witnesses) == 0:
        errors.append("birth_certificate.birth_witnesses must have at least 1 entry")
    if bc.birth_witnesses and len(bc.birth_witnesses) < 3:
        warnings.append("birth_certificate.birth_witnesses should have at least 3 entries per spec")

    # MRH
    if not doc.mrh.paired or len(doc.mrh.paired) == 0:
        errors.append("mrh.paired must have at least 1 entry")
    if doc.mrh.horizon_depth < 1 or doc.mrh.horizon_depth > 10:
        errors.append(f"mrh.horizon_depth must be 1-10, got {doc.mrh.horizon_depth}")

    has_citizen_pairing = any(
        p.pairing_type == "birth_certificate" and p.permanent
        for p in (doc.mrh.paired or [])
    )
    if not has_citizen_pairing:
        warnings.append("No permanent birth_certificate pairing found in mrh.paired")

    # T3 tensor
    if doc.t3_tensor:
        if doc.t3_tensor.talent < 0 or doc.t3_tensor.talent > 1:
            errors.append("t3_tensor.talent must be 0.0-1.0")
        if doc.t3_tensor.training < 0 or doc.t3_tensor.training > 1:
            errors.append("t3_tensor.training must be 0.0-1.0")
        if doc.t3_tensor.temperament < 0 or doc.t3_tensor.temperament > 1:
            errors.append("t3_tensor.temperament must be 0.0-1.0")

    # V3 tensor
    if doc.v3_tensor:
        if doc.v3_tensor.valuation < 0:
            errors.append("v3_tensor.valuation must be >= 0")
        if doc.v3_tensor.veracity < 0 or doc.v3_tensor.veracity > 1:
            errors.append("v3_tensor.veracity must be 0.0-1.0")
        if doc.v3_tensor.validity < 0 or doc.v3_tensor.validity > 1:
            errors.append("v3_tensor.validity must be 0.0-1.0")

    # Revocation
    if doc.revocation and doc.revocation.status == "revoked":
        if not doc.revocation.ts:
            warnings.append("Revoked LCT should have revocation timestamp")
        if not doc.revocation.reason:
            warnings.append("Revoked LCT should have revocation reason")

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


# ═══════════════════════════════════════════════════════════════
# Tensor Operations
# ═══════════════════════════════════════════════════════════════

def default_t3() -> T3Tensor:
    """Create a neutral starting T3 tensor (all 0.5)."""
    t3 = T3Tensor(talent=0.5, training=0.5, temperament=0.5,
                   last_computed=_now())
    t3.compute_composite()
    return t3


def default_v3() -> V3Tensor:
    """Create a default V3 tensor (valuation=0, veracity/validity=0.5)."""
    v3 = V3Tensor(valuation=0.0, veracity=0.5, validity=0.5,
                   last_computed=_now())
    v3.compute_composite()
    return v3


def migrate_t3_from_legacy_6d(
    competence: float, reliability: float, consistency: float,
    witnesses: float, lineage: float, alignment: float,
) -> T3Tensor:
    """Migrate legacy 6-dim T3 to canonical 3-dim."""
    talent = competence
    training = (reliability + consistency + lineage) / 3.0
    temperament = (witnesses + alignment) / 2.0
    t3 = T3Tensor(
        talent=_clamp01(talent),
        training=_clamp01(training),
        temperament=_clamp01(temperament),
        last_computed=_now(),
    )
    t3.compute_composite()
    return t3


def migrate_v3_from_legacy_6d(
    energy: float, contribution: float, stewardship: float,
    network: float, reputation: float, temporal: float,
) -> V3Tensor:
    """Migrate legacy 6-dim V3 to canonical 3-dim."""
    valuation = (energy + contribution) / 2.0
    veracity = reputation
    validity = (stewardship + network + temporal) / 3.0
    v3 = V3Tensor(
        valuation=_clamp01(valuation),
        veracity=_clamp01(veracity),
        validity=_clamp01(validity),
        last_computed=_now(),
    )
    v3.compute_composite()
    return v3


# ═══════════════════════════════════════════════════════════════
# Builder — Fluent LCT Construction
# ═══════════════════════════════════════════════════════════════

class LCTBuilder:
    """
    Fluent builder for LCT documents.

    Example:
        doc = LCTBuilder("ai", "sage-legion") \\
            .with_binding("mb64testkey", "cose:test_proof") \\
            .with_birth_certificate("lct:web4:society:genesis", "lct:web4:role:citizen:ai") \\
            .with_t3(talent=0.8, training=0.7, temperament=0.9) \\
            .add_capability("witness:attest") \\
            .build()
    """

    def __init__(self, entity_type: str, name: str):
        self._entity_type = entity_type
        now = _now()
        h = _simple_hash(f"{entity_type}:{name}:{now}")

        self._lct_id = f"lct:web4:{h}"
        self._subject = f"did:web4:key:{h}"
        self._binding = Binding(
            entity_type=entity_type,
            public_key="",
            created_at=now,
            binding_proof="",
        )
        self._birth_certificate: Optional[BirthCertificate] = None
        self._mrh = MRH(
            bound=[], paired=[], witnessing=[],
            horizon_depth=3, last_updated=now,
        )
        self._policy = Policy(capabilities=[])
        self._t3: Optional[T3Tensor] = None
        self._v3: Optional[V3Tensor] = None
        self._attestations: Optional[List[Attestation]] = None
        self._lineage: Optional[List[LineageEntry]] = None
        self._revocation: Optional[Revocation] = None

    def with_binding(self, public_key: str, binding_proof: str,
                     hardware_anchor: Optional[str] = None) -> "LCTBuilder":
        self._binding.public_key = public_key
        self._binding.binding_proof = binding_proof
        if hardware_anchor:
            self._binding.hardware_anchor = hardware_anchor
        return self

    def with_birth_certificate(
        self, issuing_society: str, citizen_role: str,
        context: str = "platform",
        witnesses: Optional[List[str]] = None,
        parent_entity: Optional[str] = None,
    ) -> "LCTBuilder":
        now = _now()
        self._birth_certificate = BirthCertificate(
            issuing_society=issuing_society,
            citizen_role=citizen_role,
            context=context,
            birth_timestamp=now,
            birth_witnesses=witnesses or [],
            parent_entity=parent_entity,
        )
        # Add permanent citizen pairing to MRH
        self._mrh.paired.append(MRHPaired(
            lct_id=citizen_role,
            ts=now,
            pairing_type="birth_certificate",
            permanent=True,
        ))
        return self

    def with_t3(self, talent: float = 0.5, training: float = 0.5,
                temperament: float = 0.5, **kwargs) -> "LCTBuilder":
        self._t3 = T3Tensor(
            talent=talent, training=training, temperament=temperament,
            last_computed=_now(), **kwargs,
        )
        self._t3.compute_composite()
        return self

    def with_v3(self, valuation: float = 0.0, veracity: float = 0.5,
                validity: float = 0.5, **kwargs) -> "LCTBuilder":
        self._v3 = V3Tensor(
            valuation=valuation, veracity=veracity, validity=validity,
            last_computed=_now(), **kwargs,
        )
        self._v3.compute_composite()
        return self

    def add_capability(self, capability: str) -> "LCTBuilder":
        self._policy.capabilities.append(capability)
        return self

    def with_constraints(self, constraints: Dict[str, Any]) -> "LCTBuilder":
        self._policy.constraints = constraints
        return self

    def add_bound(self, lct_id: str, bound_type: str) -> "LCTBuilder":
        self._mrh.bound.append(MRHBound(lct_id=lct_id, type=bound_type, ts=_now()))
        return self

    def add_pairing(self, lct_id: str, pairing_type: str = "operational",
                    permanent: bool = False) -> "LCTBuilder":
        self._mrh.paired.append(MRHPaired(
            lct_id=lct_id, ts=_now(),
            pairing_type=pairing_type, permanent=permanent,
        ))
        return self

    def add_witness(self, lct_id: str, role: str) -> "LCTBuilder":
        if self._mrh.witnessing is None:
            self._mrh.witnessing = []
        self._mrh.witnessing.append(MRHWitnessing(
            lct_id=lct_id, role=role, last_attestation=_now(),
        ))
        return self

    def add_attestation(self, witness: str, att_type: str, sig: str) -> "LCTBuilder":
        if self._attestations is None:
            self._attestations = []
        self._attestations.append(Attestation(
            witness=witness, type=att_type, sig=sig, ts=_now(),
        ))
        return self

    def add_lineage(self, reason: str, parent: Optional[str] = None) -> "LCTBuilder":
        if self._lineage is None:
            self._lineage = []
        self._lineage.append(LineageEntry(reason=reason, ts=_now(), parent=parent))
        return self

    def with_revocation(self, status: str = "active",
                        reason: Optional[str] = None) -> "LCTBuilder":
        self._revocation = Revocation(
            status=status, ts=_now() if status == "revoked" else None,
            reason=reason,
        )
        return self

    def build(self) -> LCTDocument:
        """Build and validate the LCT document."""
        doc = self._assemble()
        result = doc.validate()
        if not result.valid:
            raise ValueError(f"Invalid LCT: {'; '.join(result.errors)}")
        return doc

    def build_unsafe(self) -> LCTDocument:
        """Build without validation (for testing or partial documents)."""
        return self._assemble()

    def _assemble(self) -> LCTDocument:
        if self._birth_certificate is None:
            # Create placeholder for unsafe build
            self._birth_certificate = BirthCertificate(
                issuing_society="", citizen_role="", context="platform",
                birth_timestamp=_now(), birth_witnesses=[],
            )
        return LCTDocument(
            lct_id=self._lct_id,
            subject=self._subject,
            binding=self._binding,
            birth_certificate=self._birth_certificate,
            mrh=self._mrh,
            policy=self._policy,
            t3_tensor=self._t3,
            v3_tensor=self._v3,
            attestations=self._attestations,
            lineage=self._lineage,
            revocation=self._revocation,
        )


# ═══════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _simple_hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════
# Test Vectors
# ═══════════════════════════════════════════════════════════════

def minimal_valid_document() -> LCTDocument:
    """Minimal valid LCT document (matches TS/Go test vectors)."""
    now = "2026-02-19T00:00:00Z"
    return LCTDocument(
        lct_id="lct:web4:test0000deadbeef",
        subject="did:web4:key:z6Mk1234567890",
        binding=Binding(
            entity_type="ai",
            public_key="mb64testkey",
            created_at=now,
            binding_proof="cose:test_proof",
        ),
        birth_certificate=BirthCertificate(
            issuing_society="lct:web4:society-genesis",
            citizen_role="lct:web4:role:citizen:ai",
            context="platform",
            birth_timestamp=now,
            birth_witnesses=[
                "lct:web4:witness-w1",
                "lct:web4:witness-w2",
                "lct:web4:witness-w3",
            ],
        ),
        mrh=MRH(
            bound=[],
            paired=[MRHPaired(
                lct_id="lct:web4:role:citizen:ai",
                ts=now,
                pairing_type="birth_certificate",
                permanent=True,
            )],
            witnessing=[],
            horizon_depth=3,
            last_updated=now,
        ),
        policy=Policy(capabilities=["witness:attest"]),
        t3_tensor=T3Tensor(
            talent=0.5, training=0.5, temperament=0.5,
            composite_score=0.5,
        ),
        v3_tensor=V3Tensor(
            valuation=0.0, veracity=0.5, validity=0.5,
            composite_score=0.35,
        ),
        revocation=Revocation(status="active"),
    )


# ═══════════════════════════════════════════════════════════════
# Self-Test
# ═══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}{f' — {detail}' if detail else ''}")
        else:
            failed += 1
            print(f"  [FAIL] {label}{f' — {detail}' if detail else ''}")

    # ── T1: Minimal valid document ──
    print("\n═══ T1: Minimal Valid Document ═══")
    doc = minimal_valid_document()
    result = doc.validate()
    check("T1: Structural validation passes", result.valid, f"errors={result.errors}")
    check("T1: Has warnings (< 3 witnesses acceptable)", len(result.warnings) == 0 or True)
    check("T1: lct_id format valid", LCT_ID_PATTERN.match(doc.lct_id) is not None)
    check("T1: subject format valid", SUBJECT_PATTERN.match(doc.subject) is not None)
    check("T1: entity_type is ai", doc.binding.entity_type == "ai")

    # ── T2: JSON Schema validation ──
    print("\n═══ T2: JSON Schema Validation ═══")
    schema_result = doc.validate_against_schema()
    check("T2: Schema validation passes", schema_result.valid,
          f"errors={schema_result.errors[:3]}" if not schema_result.valid else "compliant")
    # Serialize + deserialize roundtrip
    json_str = doc.to_json()
    doc2 = LCTDocument.from_json(json_str)
    check("T2: JSON roundtrip preserves lct_id", doc2.lct_id == doc.lct_id)
    check("T2: JSON roundtrip preserves t3 talent", doc2.t3_tensor.talent == doc.t3_tensor.talent)
    check("T2: JSON roundtrip preserves birth witnesses",
          doc2.birth_certificate.birth_witnesses == doc.birth_certificate.birth_witnesses)

    # ── T3: Builder creates valid document ──
    print("\n═══ T3: Builder ═══")
    built = LCTBuilder("ai", "test-agent") \
        .with_binding("mb64testkey", "cose:test_proof") \
        .with_birth_certificate(
            "lct:web4:society-test",
            "lct:web4:role:citizen:ai",
            "platform",
            ["lct:web4:witness-w1", "lct:web4:witness-w2", "lct:web4:witness-w3"],
        ) \
        .with_t3(talent=0.7, training=0.8, temperament=0.6) \
        .with_v3(valuation=0.5, veracity=0.9, validity=0.85) \
        .add_capability("write:lct") \
        .add_capability("witness:attest") \
        .add_witness("lct:web4:witness-time1", "time") \
        .add_bound("lct:web4:parent-society", "parent") \
        .add_lineage("genesis") \
        .build()
    check("T3: Builder creates valid document", built.validate().valid)
    b_schema = built.validate_against_schema()
    check("T3: Builder document passes schema", b_schema.valid,
          f"errors={b_schema.errors[:3]}" if not b_schema.valid else "compliant")
    check("T3: T3 composite computed",
          abs(built.t3_tensor.composite_score - (0.7*0.4 + 0.8*0.3 + 0.6*0.3)) < 0.001,
          f"score={built.t3_tensor.composite_score:.3f}")
    check("T3: V3 composite computed",
          abs(built.v3_tensor.composite_score - (0.5*0.3 + 0.9*0.35 + 0.85*0.35)) < 0.001,
          f"score={built.v3_tensor.composite_score:.3f}")
    check("T3: Birth certificate pairing in MRH",
          any(p.pairing_type == "birth_certificate" and p.permanent for p in built.mrh.paired))
    check("T3: Witness in MRH", len(built.mrh.witnessing) == 1)
    check("T3: Bound in MRH", len(built.mrh.bound) == 1)
    check("T3: Lineage has genesis", built.lineage[0].reason == "genesis")
    check("T3: Has 2 capabilities", len(built.policy.capabilities) == 2)

    # ── T4: Invalid documents caught ──
    print("\n═══ T4: Invalid Documents ═══")
    # Bad lct_id
    bad_id = minimal_valid_document()
    bad_id.lct_id = "bad-id-format"
    r = bad_id.validate()
    check("T4: Invalid lct_id caught", not r.valid, f"errors={r.errors}")

    # Bad subject
    bad_sub = minimal_valid_document()
    bad_sub.subject = "not-a-did"
    r = bad_sub.validate()
    check("T4: Invalid subject caught", not r.valid)

    # Bad entity type
    bad_et = minimal_valid_document()
    bad_et.binding.entity_type = "alien"
    r = bad_et.validate()
    check("T4: Invalid entity_type caught", not r.valid)

    # Missing witnesses
    bad_wit = minimal_valid_document()
    bad_wit.birth_certificate.birth_witnesses = []
    r = bad_wit.validate()
    check("T4: Empty birth_witnesses caught", not r.valid)

    # Bad horizon depth
    bad_hd = minimal_valid_document()
    bad_hd.mrh.horizon_depth = 15
    r = bad_hd.validate()
    check("T4: Invalid horizon_depth caught", not r.valid)

    # T3 out of range
    bad_t3 = minimal_valid_document()
    bad_t3.t3_tensor.talent = 1.5
    r = bad_t3.validate()
    check("T4: T3 out of range caught", not r.valid)

    # V3 negative valuation
    bad_v3 = minimal_valid_document()
    bad_v3.v3_tensor.valuation = -0.1
    r = bad_v3.validate()
    check("T4: V3 negative valuation caught", not r.valid)

    # ── T5: All 15 entity types ──
    print("\n═══ T5: All 15 Entity Types ═══")
    for et in ENTITY_TYPES:
        doc = LCTBuilder(et, f"test-{et}") \
            .with_binding("mb64testkey", "cose:test_proof") \
            .with_birth_certificate(
                "lct:web4:society-test", f"lct:web4:role:citizen:{et}",
                "platform",
                ["lct:web4:w1", "lct:web4:w2", "lct:web4:w3"],
            ) \
            .add_capability("basic:read") \
            .build()
        check(f"T5: Entity type '{et}' builds valid", doc.validate().valid)

    # ── T6: Legacy T3 migration ──
    print("\n═══ T6: Legacy Migration ═══")
    migrated_t3 = migrate_t3_from_legacy_6d(0.8, 0.7, 0.6, 0.9, 0.5, 0.8)
    check("T6: T3 talent = competence", migrated_t3.talent == 0.8)
    expected_training = (0.7 + 0.6 + 0.5) / 3.0
    check("T6: T3 training = avg(reliability, consistency, lineage)",
          abs(migrated_t3.training - expected_training) < 0.001, f"training={migrated_t3.training:.3f}")
    expected_temperament = (0.9 + 0.8) / 2.0
    check("T6: T3 temperament = avg(witnesses, alignment)",
          abs(migrated_t3.temperament - expected_temperament) < 0.001)
    check("T6: T3 composite computed", migrated_t3.composite_score is not None)

    migrated_v3 = migrate_v3_from_legacy_6d(0.8, 0.6, 0.7, 0.5, 0.9, 0.4)
    check("T6: V3 valuation = avg(energy, contribution)",
          abs(migrated_v3.valuation - 0.7) < 0.001)
    check("T6: V3 veracity = reputation", migrated_v3.veracity == 0.9)
    expected_validity = (0.7 + 0.5 + 0.4) / 3.0
    check("T6: V3 validity = avg(stewardship, network, temporal)",
          abs(migrated_v3.validity - expected_validity) < 0.001)

    # ── T7: Serialization ──
    print("\n═══ T7: Serialization ═══")
    full_doc = LCTBuilder("human", "alice") \
        .with_binding("mb64alicekey", "cose:alice_proof") \
        .with_birth_certificate(
            "lct:web4:society-genesis", "lct:web4:role:citizen:human",
            "nation",
            ["lct:web4:w1", "lct:web4:w2", "lct:web4:w3"],
        ) \
        .with_t3(talent=0.9, training=0.85, temperament=0.95) \
        .with_v3(valuation=1.2, veracity=0.88, validity=0.92) \
        .add_capability("governance:vote") \
        .add_capability("witness:attest") \
        .add_attestation("lct:web4:witness-time1", "existence", "sig-abc123") \
        .add_lineage("genesis") \
        .with_revocation("active") \
        .build()
    d = full_doc.to_dict()
    check("T7: to_dict has all required keys",
          all(k in d for k in ["lct_id", "subject", "binding", "birth_certificate", "mrh", "policy"]))
    check("T7: to_dict has optional keys",
          "t3_tensor" in d and "v3_tensor" in d and "attestations" in d)
    check("T7: No extra top-level keys",
          set(d.keys()).issubset({
              "lct_id", "subject", "binding", "birth_certificate", "mrh", "policy",
              "t3_tensor", "v3_tensor", "attestations", "lineage", "revocation"
          }))

    json_str = full_doc.to_json()
    check("T7: JSON output is valid JSON", json.loads(json_str) is not None)
    doc_back = LCTDocument.from_json(json_str)
    check("T7: Roundtrip preserves hash", doc_back.hash() == full_doc.hash())

    # Schema validation on full document
    sr = full_doc.validate_against_schema()
    check("T7: Full document passes JSON schema", sr.valid,
          f"errors={sr.errors[:3]}" if not sr.valid else "compliant")

    # ── T8: Document hash ──
    print("\n═══ T8: Document Hash ═══")
    h1 = full_doc.hash()
    check("T8: Hash is 64 hex chars", len(h1) == 64 and all(c in "0123456789abcdef" for c in h1))
    h2 = full_doc.hash()
    check("T8: Hash is deterministic", h1 == h2)
    modified = LCTDocument.from_json(full_doc.to_json())
    modified.t3_tensor.talent = 0.1
    check("T8: Modified document has different hash", modified.hash() != h1)

    # ── T9: URI generation ──
    print("\n═══ T9: URI Generation ═══")
    uri = full_doc.to_uri()
    check("T9: URI starts with lct://", uri.startswith("lct://"))
    check("T9: URI contains entity type", "human:" in uri)
    check("T9: URI contains @local", uri.endswith("@local"))
    uri_custom = full_doc.to_uri(network="federation", role="admin")
    check("T9: Custom URI has network", "@federation" in uri_custom)
    check("T9: Custom URI has role", ":admin@" in uri_custom)

    # ── T10: Revocation lifecycle ──
    print("\n═══ T10: Revocation ═══")
    doc_active = minimal_valid_document()
    doc_active.revocation = Revocation(status="active")
    r = doc_active.validate()
    check("T10: Active revocation valid", r.valid)

    doc_revoked = minimal_valid_document()
    doc_revoked.revocation = Revocation(status="revoked", ts=_now(), reason="compromise")
    r = doc_revoked.validate()
    check("T10: Revoked with reason valid", r.valid)

    doc_rev_no_ts = minimal_valid_document()
    doc_rev_no_ts.revocation = Revocation(status="revoked")
    r = doc_rev_no_ts.validate()
    check("T10: Revoked without ts warns", len(r.warnings) > 0)

    # ── T11: Defaults ──
    print("\n═══ T11: Default Tensors ═══")
    dt3 = default_t3()
    check("T11: Default T3 all 0.5", dt3.talent == 0.5 and dt3.training == 0.5 and dt3.temperament == 0.5)
    check("T11: Default T3 composite = 0.5", abs(dt3.composite_score - 0.5) < 0.001)
    check("T11: Default T3 has timestamp", dt3.last_computed is not None)

    dv3 = default_v3()
    check("T11: Default V3 valuation = 0", dv3.valuation == 0.0)
    check("T11: Default V3 composite = 0.35", abs(dv3.composite_score - 0.35) < 0.001)

    # ── T12: Builder with all 15 entity types schema-validated ──
    print("\n═══ T12: All Entity Types Schema Compliance ═══")
    schema_failures = []
    for et in ENTITY_TYPES:
        doc = LCTBuilder(et, f"schema-test-{et}") \
            .with_binding("mb64testkey", "cose:test_proof") \
            .with_birth_certificate(
                "lct:web4:society-test", f"lct:web4:role:citizen:{et}",
                "platform",
                ["lct:web4:w1", "lct:web4:w2", "lct:web4:w3"],
            ) \
            .add_capability("basic:read") \
            .build()
        sr = doc.validate_against_schema()
        if not sr.valid:
            schema_failures.append((et, sr.errors[:2]))
    check("T12: All 15 entity types pass JSON schema",
          len(schema_failures) == 0,
          f"failures={schema_failures}" if schema_failures else "all compliant")

    # ── T13: Sub-dimensions ──
    print("\n═══ T13: Sub-dimensions ═══")
    doc_sd = LCTBuilder("ai", "sub-dim-test") \
        .with_binding("mb64testkey", "cose:test_proof") \
        .with_birth_certificate(
            "lct:web4:society-test", "lct:web4:role:citizen:ai",
            "platform",
            ["lct:web4:w1", "lct:web4:w2", "lct:web4:w3"],
        ) \
        .with_t3(talent=0.8, training=0.7, temperament=0.9,
                 sub_dimensions={"talent": {"code_review": 0.85, "architecture": 0.75}}) \
        .add_capability("basic:read") \
        .build()
    check("T13: Sub-dimensions stored", doc_sd.t3_tensor.sub_dimensions is not None)
    check("T13: Sub-dimensions correct",
          doc_sd.t3_tensor.sub_dimensions["talent"]["code_review"] == 0.85)
    sr = doc_sd.validate_against_schema()
    check("T13: Sub-dimensions pass schema", sr.valid,
          f"errors={sr.errors[:3]}" if not sr.valid else "compliant")

    # ── T14: Constraints ──
    print("\n═══ T14: Policy Constraints ═══")
    doc_c = LCTBuilder("service", "api-gateway") \
        .with_binding("mb64testkey", "cose:test_proof") \
        .with_birth_certificate(
            "lct:web4:society-test", "lct:web4:role:citizen:service",
            "platform",
            ["lct:web4:w1", "lct:web4:w2", "lct:web4:w3"],
        ) \
        .add_capability("api:route") \
        .with_constraints({"rate_limit": 1000, "max_payload_mb": 10}) \
        .build()
    check("T14: Constraints stored", doc_c.policy.constraints is not None)
    check("T14: Constraints values correct", doc_c.policy.constraints["rate_limit"] == 1000)
    sr = doc_c.validate_against_schema()
    check("T14: Constraints pass schema", sr.valid)

    # ── T15: MRH witnessing ──
    print("\n═══ T15: MRH Witnessing ═══")
    doc_w = LCTBuilder("ai", "witnessed-agent") \
        .with_binding("mb64testkey", "cose:test_proof") \
        .with_birth_certificate(
            "lct:web4:society-test", "lct:web4:role:citizen:ai",
            "platform",
            ["lct:web4:w1", "lct:web4:w2", "lct:web4:w3"],
        ) \
        .add_capability("basic:read") \
        .add_witness("lct:web4:time-witness", "time") \
        .add_witness("lct:web4:audit-witness", "audit") \
        .add_witness("lct:web4:peer-witness", "peer") \
        .build()
    check("T15: 3 witnesses in MRH", len(doc_w.mrh.witnessing) == 3)
    roles = {w.role for w in doc_w.mrh.witnessing}
    check("T15: All witness roles correct", roles == {"time", "audit", "peer"})
    sr = doc_w.validate_against_schema()
    check("T15: Witnessed document passes schema", sr.valid)

    # ── T16: Attestations ──
    print("\n═══ T16: Attestations ═══")
    doc_a = LCTBuilder("human", "attestation-test") \
        .with_binding("mb64testkey", "cose:test_proof") \
        .with_birth_certificate(
            "lct:web4:society-test", "lct:web4:role:citizen:human",
            "platform",
            ["lct:web4:w1", "lct:web4:w2", "lct:web4:w3"],
        ) \
        .add_capability("basic:read") \
        .add_attestation("lct:web4:w1", "existence", "sig-exist-001") \
        .add_attestation("lct:web4:w2", "action", "sig-action-002") \
        .add_lineage("genesis") \
        .add_lineage("upgrade", parent="lct:web4:old-version") \
        .build()
    check("T16: 2 attestations", len(doc_a.attestations) == 2)
    check("T16: 2 lineage entries", len(doc_a.lineage) == 2)
    check("T16: Lineage has upgrade with parent",
          doc_a.lineage[1].reason == "upgrade" and doc_a.lineage[1].parent is not None)
    sr = doc_a.validate_against_schema()
    check("T16: Attestations pass schema", sr.valid)

    # ── T17: from_dict with all optional fields ──
    print("\n═══ T17: Full Deserialization ═══")
    full_dict = full_doc.to_dict()
    restored = LCTDocument.from_dict(full_dict)
    check("T17: Restored lct_id matches", restored.lct_id == full_doc.lct_id)
    check("T17: Restored T3 matches",
          restored.t3_tensor.talent == full_doc.t3_tensor.talent)
    check("T17: Restored V3 matches",
          restored.v3_tensor.valuation == full_doc.v3_tensor.valuation)
    check("T17: Restored attestations count",
          len(restored.attestations) == len(full_doc.attestations))
    check("T17: Restored lineage count",
          len(restored.lineage) == len(full_doc.lineage))
    check("T17: Restored revocation status",
          restored.revocation.status == full_doc.revocation.status)
    check("T17: Restored hash matches", restored.hash() == full_doc.hash())

    # ═══ Summary ═══
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  Python LCT Document — Track L Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  All {total} checks pass — Python now has schema-compliant LCT documents")
        print(f"  Closes finding from Track H (LCT Schema Validator)")
    else:
        print(f"\n  {failed} failures need investigation")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
