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
from typing import Any, Dict, List, Optional

from .trust import T3, V3

# JSON-LD context URI for spec-compliant LCT documents
LCT_JSONLD_CONTEXT = "https://web4.io/contexts/lct.jsonld"


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
    genesis_block_hash: Optional[str] = None


@dataclass(frozen=True)
class Attestation:
    """Witness observation recorded on the LCT. Spec §2.3."""
    witness: str
    type: str
    claims: Dict[str, Any] = field(default_factory=dict)
    sig: str = ""
    ts: str = ""


@dataclass(frozen=True)
class LineageEntry:
    """LCT evolution history entry. Spec §2.3."""
    parent: str
    reason: str  # genesis | rotation | fork | upgrade
    ts: str = ""


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

    Spec-compliant serialization:
        doc = lct.to_jsonld()  # produces §2.3 canonical structure
        lct2 = LCT.from_jsonld(doc)  # roundtrip
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
    revocation_ts: Optional[str] = None
    revocation_reason: Optional[str] = None
    attestations: List[Attestation] = field(default_factory=list)
    lineage: List[LineageEntry] = field(default_factory=list)

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

    def revoke(self, reason: Optional[str] = None) -> LCT:
        """Revoke this LCT. Returns self for chaining."""
        self.revocation_status = RevocationStatus.REVOKED
        self.revocation_ts = datetime.now(timezone.utc).isoformat()
        self.revocation_reason = reason
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

    def add_attestation(self, witness: str, type: str, claims: Optional[Dict[str, Any]] = None,
                        sig: str = "", ts: Optional[str] = None) -> Attestation:
        """Add a witness attestation to this LCT."""
        att = Attestation(
            witness=witness,
            type=type,
            claims=claims or {},
            sig=sig,
            ts=ts or datetime.now(timezone.utc).isoformat(),
        )
        self.attestations.append(att)
        return att

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
        """Serialize to dictionary (SDK internal format, backward-compatible)."""
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

    # ── Spec-Compliant Serialization (§2.3) ──────────────────────

    def to_jsonld(self) -> Dict[str, Any]:
        """
        Serialize to spec-compliant JSON-LD per LCT spec §2.3.

        Produces the canonical LCT document structure with:
        - @context header for JSON-LD processors
        - Spec-compliant field naming and nesting
        - Structured MRH entries (bound/witnessing as objects)
        - Full T3/V3 tensor representation with composite scores
        - Optional sections included only when populated
        """
        doc: Dict[str, Any] = {
            "@context": [LCT_JSONLD_CONTEXT],
            "lct_id": self.lct_id,
            "subject": self.subject,
        }

        # Binding — spec §2.3
        binding: Dict[str, Any] = {
            "entity_type": self.binding.entity_type.value,
            "public_key": self.binding.public_key,
            "created_at": self.binding.created_at,
            "binding_proof": self.binding.binding_proof,
        }
        if self.binding.hardware_anchor:
            binding["hardware_anchor"] = self.binding.hardware_anchor
        doc["binding"] = binding

        # Birth certificate — spec §2.3 (optional)
        if self.birth_certificate:
            bc: Dict[str, Any] = {
                "issuing_society": self.birth_certificate.issuing_society,
                "citizen_role": self.birth_certificate.citizen_role,
                "birth_timestamp": self.birth_certificate.birth_timestamp,
                "birth_witnesses": list(self.birth_certificate.birth_witnesses),
                "birth_context": self.birth_certificate.context,
            }
            if self.birth_certificate.genesis_block_hash:
                bc["genesis_block_hash"] = self.birth_certificate.genesis_block_hash
            doc["birth_certificate"] = bc

        # MRH — spec §2.3 (structured entries)
        mrh: Dict[str, Any] = {
            "bound": [
                {"lct_id": b} if isinstance(b, str) else b
                for b in self.mrh.bound
            ],
            "paired": [
                {
                    "lct_id": p.lct_id,
                    "pairing_type": p.pairing_type,
                    "permanent": p.permanent,
                    "ts": p.ts,
                }
                for p in self.mrh.paired
            ],
            "witnessing": [
                {"lct_id": w} if isinstance(w, str) else w
                for w in self.mrh.witnessing
            ],
            "horizon_depth": self.mrh.horizon_depth,
            "last_updated": self.mrh.last_updated,
        }
        doc["mrh"] = mrh

        # Policy — spec §2.3
        doc["policy"] = {
            "capabilities": list(self.policy.capabilities),
            "constraints": dict(self.policy.constraints),
        }

        # T3 tensor — spec §2.3
        doc["t3_tensor"] = {
            "talent": self.t3.talent,
            "training": self.t3.training,
            "temperament": self.t3.temperament,
            "composite_score": self.t3.composite,
        }

        # V3 tensor — spec §2.3
        doc["v3_tensor"] = {
            "valuation": self.v3.valuation,
            "veracity": self.v3.veracity,
            "validity": self.v3.validity,
            "composite_score": self.v3.composite,
        }

        # Attestations — spec §2.3 (optional, included when populated)
        if self.attestations:
            doc["attestations"] = [
                {
                    "witness": a.witness,
                    "type": a.type,
                    "claims": dict(a.claims),
                    "sig": a.sig,
                    "ts": a.ts,
                }
                for a in self.attestations
            ]

        # Lineage — spec §2.3 (optional, included when populated)
        if self.lineage:
            doc["lineage"] = [
                {"parent": le.parent, "reason": le.reason, "ts": le.ts}
                for le in self.lineage
            ]

        # Revocation — spec §2.3
        doc["revocation"] = {
            "status": self.revocation_status.value,
            "ts": self.revocation_ts,
            "reason": self.revocation_reason,
        }

        return doc

    def to_jsonld_string(self, indent: int = 2) -> str:
        """Serialize to spec-compliant JSON-LD string."""
        return json.dumps(self.to_jsonld(), indent=indent)

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> LCT:
        """
        Deserialize from spec-compliant JSON-LD (§2.3 canonical structure).

        Handles both spec format (structured MRH entries, birth_context)
        and SDK internal format for flexibility.
        """
        # Binding
        b = doc["binding"]
        binding = Binding(
            entity_type=EntityType(b["entity_type"]),
            public_key=b["public_key"],
            created_at=b["created_at"],
            binding_proof=b.get("binding_proof", ""),
            hardware_anchor=b.get("hardware_anchor"),
        )

        # MRH
        mrh_data = doc.get("mrh", {})
        # Parse bound entries — accept both strings and objects
        raw_bound = mrh_data.get("bound", [])
        bound: List[str] = []
        for entry in raw_bound:
            if isinstance(entry, str):
                bound.append(entry)
            elif isinstance(entry, dict):
                bound.append(entry["lct_id"])

        # Parse paired entries
        paired: List[MRHPairing] = []
        for p in mrh_data.get("paired", []):
            paired.append(MRHPairing(
                lct_id=p["lct_id"],
                pairing_type=p["pairing_type"],
                permanent=p.get("permanent", False),
                ts=p.get("ts", ""),
            ))

        # Parse witnessing entries — accept both strings and objects
        raw_witnessing = mrh_data.get("witnessing", [])
        witnessing: List[str] = []
        for entry in raw_witnessing:
            if isinstance(entry, str):
                witnessing.append(entry)
            elif isinstance(entry, dict):
                witnessing.append(entry["lct_id"])

        mrh = MRH(
            bound=bound,
            paired=paired,
            witnessing=witnessing,
            horizon_depth=mrh_data.get("horizon_depth", 3),
            last_updated=mrh_data.get("last_updated", ""),
        )

        # Policy
        pol_data = doc.get("policy", {})
        policy = Policy(
            capabilities=pol_data.get("capabilities", []),
            constraints=pol_data.get("constraints", {}),
        )

        # T3/V3 tensors
        t3_data = doc.get("t3_tensor", {})
        t3 = T3(
            talent=t3_data.get("talent", 0.5),
            training=t3_data.get("training", 0.5),
            temperament=t3_data.get("temperament", 0.5),
        )

        v3_data = doc.get("v3_tensor", {})
        v3 = V3(
            valuation=v3_data.get("valuation", 0.5),
            veracity=v3_data.get("veracity", 0.5),
            validity=v3_data.get("validity", 0.5),
        )

        # Birth certificate (optional)
        birth_certificate = None
        bc_data = doc.get("birth_certificate")
        if bc_data:
            # Accept both spec format (birth_context) and SDK format (context)
            context = bc_data.get("birth_context", bc_data.get("context", "platform"))
            birth_certificate = BirthCertificate(
                issuing_society=bc_data["issuing_society"],
                citizen_role=bc_data["citizen_role"],
                birth_timestamp=bc_data["birth_timestamp"],
                birth_witnesses=bc_data.get("birth_witnesses", []),
                context=context,
                genesis_block_hash=bc_data.get("genesis_block_hash"),
            )

        # Revocation
        rev_data = doc.get("revocation", {})
        revocation_status = RevocationStatus(rev_data.get("status", "active"))
        revocation_ts = rev_data.get("ts")
        revocation_reason = rev_data.get("reason")

        # Attestations (optional)
        attestations: List[Attestation] = []
        for a in doc.get("attestations", []):
            attestations.append(Attestation(
                witness=a["witness"],
                type=a["type"],
                claims=a.get("claims", {}),
                sig=a.get("sig", ""),
                ts=a.get("ts", ""),
            ))

        # Lineage (optional)
        lineage: List[LineageEntry] = []
        for le in doc.get("lineage", []):
            lineage.append(LineageEntry(
                parent=le["parent"],
                reason=le["reason"],
                ts=le.get("ts", ""),
            ))

        return cls(
            lct_id=doc["lct_id"],
            subject=doc["subject"],
            binding=binding,
            mrh=mrh,
            policy=policy,
            t3=t3,
            v3=v3,
            birth_certificate=birth_certificate,
            revocation_status=revocation_status,
            revocation_ts=revocation_ts,
            revocation_reason=revocation_reason,
            attestations=attestations,
            lineage=lineage,
        )

    @classmethod
    def from_jsonld_string(cls, s: str) -> LCT:
        """Deserialize from JSON-LD string."""
        return cls.from_jsonld(json.loads(s))
