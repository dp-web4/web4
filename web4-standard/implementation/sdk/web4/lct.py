"""
Web4 Linked Context Token (LCT)

Canonical implementation per web4-standard/core-spec/LCT-linked-context-token.md.

An LCT is a verifiable digital presence certificate that binds an entity
to its context through witnessed relationships. Unlike traditional identity
tokens that assert "who you are," LCTs establish "where you exist" —
your position in the web of trust and context.

Required components: identity, binding, MRH, policy, T3, V3.
Optional: birth certificate, attestations, lineage, revocation.

Validated against: web4-standard/test-vectors/lct/
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from .trust import T3, V3


# ── Entity Types ─────────────────────────────────────────────────

class EntityType(str, Enum):
    """Web4 entity type taxonomy."""
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


class RevocationStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


# ── LCT Sub-Structures ──────────────────────────────────────────

@dataclass(frozen=True)
class Binding:
    """Cryptographic anchor binding entity to LCT."""
    entity_type: EntityType
    public_key: str
    created_at: str
    binding_proof: str = ""
    hardware_anchor: Optional[str] = None


@dataclass(frozen=True)
class MRHPairing:
    """A pairing in the MRH graph."""
    lct_id: str
    pairing_type: str
    permanent: bool = False
    ts: str = ""


@dataclass
class MRH:
    """Markov Relevancy Horizon — the entity's relationship context."""
    bound: List[str] = field(default_factory=list)
    paired: List[MRHPairing] = field(default_factory=list)
    witnessing: List[str] = field(default_factory=list)
    horizon_depth: int = 3
    last_updated: str = ""


@dataclass(frozen=True)
class BirthCertificate:
    """Society-issued foundational presence document."""
    issuing_society: str
    citizen_role: str
    birth_timestamp: str
    birth_witnesses: List[str] = field(default_factory=list)
    context: str = "platform"


@dataclass
class Policy:
    """Capabilities and constraints for this LCT."""
    capabilities: List[str] = field(default_factory=list)
    constraints: Dict = field(default_factory=dict)


# ── LCT ──────────────────────────────────────────────────────────

@dataclass
class LCT:
    """
    Linked Context Token — Web4's foundational presence primitive.

    Usage:
        lct = LCT.create(
            entity_type=EntityType.AI,
            public_key="mb64testkey",
            society="lct:web4:society-genesis",
            context="platform",
            witnesses=["lct:web4:witness-w1", "lct:web4:witness-w2"],
        )
        print(lct.lct_id)
        print(lct.t3.composite)
    """

    lct_id: str
    subject: str
    binding: Binding
    mrh: MRH = field(default_factory=MRH)
    policy: Policy = field(default_factory=Policy)
    t3: T3 = field(default_factory=T3)
    v3: V3 = field(default_factory=V3)
    birth_certificate: Optional[BirthCertificate] = None
    revocation_status: RevocationStatus = RevocationStatus.ACTIVE

    @staticmethod
    def create(
        entity_type: EntityType,
        public_key: str,
        society: str = "lct:web4:society:genesis",
        context: str = "platform",
        witnesses: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
        lct_id: Optional[str] = None,
        subject: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        t3: Optional[T3] = None,
        v3: Optional[V3] = None,
    ) -> LCT:
        """
        Create a new LCT with birth certificate.

        The birth certificate is the foundational pairing — first pairing
        MUST be the citizen role.
        """
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        witnesses = witnesses or []

        # Generate IDs if not provided
        if lct_id is None:
            raw = f"{entity_type.value}:{public_key}:{ts}"
            h = hashlib.sha256(raw.encode()).hexdigest()[:16]
            lct_id = f"lct:web4:{entity_type.value}:{h}"

        if subject is None:
            subject = f"did:web4:key:{public_key[:20]}"

        citizen_role = f"lct:web4:role:citizen:{context}"

        binding = Binding(
            entity_type=entity_type,
            public_key=public_key,
            created_at=ts,
            binding_proof=f"cose:signature_placeholder",
        )

        birth_cert = BirthCertificate(
            issuing_society=society,
            citizen_role=citizen_role,
            birth_timestamp=ts,
            birth_witnesses=list(witnesses),
            context=context,
        )

        # First pairing is always the citizen role
        mrh = MRH(
            paired=[
                MRHPairing(
                    lct_id=citizen_role,
                    pairing_type="birth_certificate",
                    permanent=True,
                    ts=ts,
                )
            ],
            horizon_depth=3,
            last_updated=ts,
        )

        policy = Policy(capabilities=capabilities or ["exist", "interact", "accumulate_reputation"])

        return LCT(
            lct_id=lct_id,
            subject=subject,
            binding=binding,
            mrh=mrh,
            policy=policy,
            t3=t3 or T3(),
            v3=v3 or V3(),
            birth_certificate=birth_cert,
        )

    @property
    def is_active(self) -> bool:
        return self.revocation_status == RevocationStatus.ACTIVE

    def revoke(self) -> LCT:
        """Revoke this LCT. Returns self for chaining."""
        self.revocation_status = RevocationStatus.REVOKED
        return self

    def add_pairing(self, target_lct_id: str, pairing_type: str, permanent: bool = False):
        """Add a pairing to the MRH."""
        ts = datetime.now(timezone.utc).isoformat()
        self.mrh.paired.append(
            MRHPairing(lct_id=target_lct_id, pairing_type=pairing_type, permanent=permanent, ts=ts)
        )
        self.mrh.last_updated = ts

    def add_witness(self, witness_lct_id: str):
        """Record a witnessing relationship."""
        if witness_lct_id not in self.mrh.witnessing:
            self.mrh.witnessing.append(witness_lct_id)
            self.mrh.last_updated = datetime.now(timezone.utc).isoformat()

    def canonical_hash(self) -> str:
        """
        Compute canonical hash for cross-language interop.

        Canonical form: sorted JSON of the LCT's essential fields.
        """
        canonical = {
            "lct_id": self.lct_id,
            "subject": self.subject,
            "binding": {
                "entity_type": self.binding.entity_type.value,
                "public_key": self.binding.public_key,
                "created_at": self.binding.created_at,
                "binding_proof": self.binding.binding_proof,
            },
            "birth_certificate": None,
            "mrh": {
                "bound": self.mrh.bound,
                "paired": [
                    {"lct_id": p.lct_id, "pairing_type": p.pairing_type,
                     "permanent": p.permanent, "ts": p.ts}
                    for p in self.mrh.paired
                ],
                "horizon_depth": self.mrh.horizon_depth,
                "last_updated": self.mrh.last_updated,
            },
            "policy": {"capabilities": self.policy.capabilities},
            "revocation": {"status": self.revocation_status.value},
            "t3_tensor": {
                "talent": self.t3.talent,
                "training": self.t3.training,
                "temperament": self.t3.temperament,
                "composite_score": self.t3.composite,
            },
            "v3_tensor": {
                "valuation": self.v3.valuation,
                "veracity": self.v3.veracity,
                "validity": self.v3.validity,
                "composite_score": self.v3.composite,
            },
        }

        if self.birth_certificate:
            canonical["birth_certificate"] = {
                "issuing_society": self.birth_certificate.issuing_society,
                "citizen_role": self.birth_certificate.citizen_role,
                "birth_timestamp": self.birth_certificate.birth_timestamp,
                "birth_witnesses": self.birth_certificate.birth_witnesses,
                "context": self.birth_certificate.context,
            }

        raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        d = {
            "lct_id": self.lct_id,
            "subject": self.subject,
            "binding": {
                "entity_type": self.binding.entity_type.value,
                "public_key": self.binding.public_key,
                "created_at": self.binding.created_at,
                "binding_proof": self.binding.binding_proof,
            },
            "mrh": {
                "bound": self.mrh.bound,
                "paired": [
                    {"lct_id": p.lct_id, "pairing_type": p.pairing_type,
                     "permanent": p.permanent, "ts": p.ts}
                    for p in self.mrh.paired
                ],
                "witnessing": self.mrh.witnessing,
                "horizon_depth": self.mrh.horizon_depth,
                "last_updated": self.mrh.last_updated,
            },
            "policy": {
                "capabilities": self.policy.capabilities,
                "constraints": self.policy.constraints,
            },
            "t3_tensor": {
                "talent": self.t3.talent, "training": self.t3.training,
                "temperament": self.t3.temperament, "composite_score": self.t3.composite,
            },
            "v3_tensor": {
                "valuation": self.v3.valuation, "veracity": self.v3.veracity,
                "validity": self.v3.validity, "composite_score": self.v3.composite,
            },
            "revocation": {"status": self.revocation_status.value},
        }
        if self.birth_certificate:
            d["birth_certificate"] = {
                "issuing_society": self.birth_certificate.issuing_society,
                "citizen_role": self.birth_certificate.citizen_role,
                "birth_timestamp": self.birth_certificate.birth_timestamp,
                "birth_witnesses": self.birth_certificate.birth_witnesses,
                "context": self.birth_certificate.context,
            }
        return d
