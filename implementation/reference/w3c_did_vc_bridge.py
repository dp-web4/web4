#!/usr/bin/env python3
"""
W3C DID/VC Interoperability Bridge — Web4 Reference Implementation

Bridges Web4 identity (LCT, W4ID) with W3C standards ecosystem:
- DID Documents (did:web4: → W3C DID Document format)
- Verifiable Credentials (LCT birth cert → W3C VC)
- SD-JWT (selective disclosure of T3 tensor dimensions)
- DIDComm messaging (W4ID message envelope wrapping)
- Bidirectional resolution (DID↔LCT and LCT↔DID)

This is the adoption enabler — without it, Web4 is a silo.
With it, Web4 entities can participate in the broader
verifiable credentials ecosystem (EU, enterprise, government).

Key insight: W4ID is ALREADY DID-compliant (did:web4:key:...).
The bridge adds W3C DID Document structure, VC wrapping, and
selective disclosure — the parts that interop partners expect.

Standards:
- W3C DID Core: https://www.w3.org/TR/did-core/
- W3C VC Data Model: https://www.w3.org/TR/vc-data-model-2.0/
- SD-JWT: IETF draft-ietf-oauth-selective-disclosure-jwt
- DIDComm v2: https://identity.foundation/didcomm-messaging/spec/v2.0/

Checks: 85+
"""

import base64
import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# PART 1: W3C DID DOCUMENT
# ═══════════════════════════════════════════════════════════════

@dataclass
class VerificationMethod:
    """W3C DID verification method."""
    id: str = ""
    type: str = "Ed25519VerificationKey2020"
    controller: str = ""
    public_key_multibase: str = ""  # Multibase-encoded public key


@dataclass
class ServiceEndpoint:
    """W3C DID service endpoint."""
    id: str = ""
    type: str = ""
    service_endpoint: str = ""
    description: str = ""


@dataclass
class DIDDocument:
    """
    W3C DID Document — the standard format for DID resolution.
    Maps from Web4 LCT/W4ID to the format interop partners expect.
    """
    context: List[str] = field(default_factory=lambda: [
        "https://www.w3.org/ns/did/v1",
        "https://w3id.org/security/suites/ed25519-2020/v1",
        "https://web4.io/ns/v1",
    ])
    id: str = ""                    # did:web4:key:... or did:web4:web:...
    controller: str = ""
    verification_method: List[VerificationMethod] = field(default_factory=list)
    authentication: List[str] = field(default_factory=list)
    assertion_method: List[str] = field(default_factory=list)
    service: List[ServiceEndpoint] = field(default_factory=list)

    # Web4 extensions
    lct_uri: str = ""
    t3_composite: float = 0.0
    society_id: str = ""
    hardware_bound: bool = False

    created: float = 0.0
    updated: float = 0.0

    def to_dict(self) -> Dict:
        """Export as W3C DID Document JSON."""
        doc = {
            "@context": self.context,
            "id": self.id,
        }
        if self.controller:
            doc["controller"] = self.controller

        if self.verification_method:
            doc["verificationMethod"] = [
                {
                    "id": vm.id,
                    "type": vm.type,
                    "controller": vm.controller or self.id,
                    "publicKeyMultibase": vm.public_key_multibase,
                }
                for vm in self.verification_method
            ]

        if self.authentication:
            doc["authentication"] = self.authentication
        if self.assertion_method:
            doc["assertionMethod"] = self.assertion_method

        if self.service:
            doc["service"] = [
                {
                    "id": s.id,
                    "type": s.type,
                    "serviceEndpoint": s.service_endpoint,
                }
                for s in self.service
            ]

        # Web4 extensions (namespaced)
        if self.lct_uri:
            doc["web4:lctUri"] = self.lct_uri
        if self.t3_composite > 0:
            doc["web4:t3Composite"] = self.t3_composite
        if self.society_id:
            doc["web4:societyId"] = self.society_id
        if self.hardware_bound:
            doc["web4:hardwareBound"] = True

        return doc

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ═══════════════════════════════════════════════════════════════
# PART 2: LCT ↔ DID DOCUMENT MAPPER
# ═══════════════════════════════════════════════════════════════

@dataclass
class LCTRecord:
    """Simplified LCT record for bridge testing."""
    lct_uri: str = ""               # lct://namespace:name@network
    w4id: str = ""                   # did:web4:key:...
    public_key: str = ""
    entity_type: str = ""
    society_id: str = ""
    t3_talent: float = 0.5
    t3_training: float = 0.5
    t3_temperament: float = 0.5
    hardware_bound: bool = False
    birth_time: float = 0.0
    witnesses: List[str] = field(default_factory=list)

    @property
    def t3_composite(self) -> float:
        return (self.t3_talent + self.t3_training + self.t3_temperament) / 3.0


class LCTDIDMapper:
    """
    Bidirectional mapping between LCT records and DID Documents.
    LCT → DID Document: For interop with W3C ecosystem
    DID Document → LCT: For importing external identities into Web4
    """

    def lct_to_did_document(self, lct: LCTRecord) -> DIDDocument:
        """Convert LCT record to W3C DID Document."""
        did_id = lct.w4id or f"did:web4:key:{hashlib.sha256(lct.public_key.encode()).hexdigest()[:32]}"

        # Create verification method
        vm = VerificationMethod(
            id=f"{did_id}#key-1",
            type="Ed25519VerificationKey2020",
            controller=did_id,
            public_key_multibase=f"z{lct.public_key}" if lct.public_key else "",
        )

        # Create service endpoints
        services = []
        if lct.lct_uri:
            services.append(ServiceEndpoint(
                id=f"{did_id}#web4-lct",
                type="Web4LCT",
                service_endpoint=lct.lct_uri,
            ))
        if lct.society_id:
            services.append(ServiceEndpoint(
                id=f"{did_id}#web4-society",
                type="Web4Society",
                service_endpoint=f"web4://society/{lct.society_id}",
            ))

        return DIDDocument(
            id=did_id,
            controller=did_id,
            verification_method=[vm],
            authentication=[f"{did_id}#key-1"],
            assertion_method=[f"{did_id}#key-1"],
            service=services,
            lct_uri=lct.lct_uri,
            t3_composite=lct.t3_composite,
            society_id=lct.society_id,
            hardware_bound=lct.hardware_bound,
            created=lct.birth_time or time.time(),
            updated=time.time(),
        )

    def did_document_to_lct(self, doc: DIDDocument) -> LCTRecord:
        """Import a DID Document as an LCT record."""
        # Extract public key from first verification method
        public_key = ""
        if doc.verification_method:
            pk = doc.verification_method[0].public_key_multibase
            if pk.startswith("z"):
                public_key = pk[1:]  # Remove multibase prefix
            else:
                public_key = pk

        # Extract LCT URI from service endpoint or web4 extension
        lct_uri = doc.lct_uri
        if not lct_uri:
            for svc in doc.service:
                if svc.type == "Web4LCT":
                    lct_uri = svc.service_endpoint
                    break

        return LCTRecord(
            lct_uri=lct_uri or f"lct://imported:{doc.id}",
            w4id=doc.id,
            public_key=public_key,
            society_id=doc.society_id,
            t3_talent=doc.t3_composite / 3.0 * 3 if doc.t3_composite else 0.5,
            t3_training=doc.t3_composite / 3.0 * 3 if doc.t3_composite else 0.5,
            t3_temperament=doc.t3_composite / 3.0 * 3 if doc.t3_composite else 0.5,
            hardware_bound=doc.hardware_bound,
            birth_time=doc.created,
        )


# ═══════════════════════════════════════════════════════════════
# PART 3: VERIFIABLE CREDENTIALS
# ═══════════════════════════════════════════════════════════════

class CredentialType(Enum):
    """Types of Web4 verifiable credentials."""
    LCT_BIRTH = "Web4LCTBirthCertificate"
    TRUST_ATTESTATION = "Web4TrustAttestation"
    COMPLIANCE_CERT = "Web4ComplianceCertificate"
    SOCIETY_MEMBERSHIP = "Web4SocietyMembership"
    HARDWARE_BINDING = "Web4HardwareBinding"
    CAPABILITY = "Web4CapabilityCredential"


@dataclass
class VerifiableCredential:
    """
    W3C Verifiable Credential wrapping Web4 attestations.
    Maps LCT birth certificates, trust attestations, and compliance
    certificates to the W3C VC Data Model format.
    """
    context: List[str] = field(default_factory=lambda: [
        "https://www.w3.org/ns/credentials/v2",
        "https://web4.io/ns/credentials/v1",
    ])
    id: str = ""
    type: List[str] = field(default_factory=lambda: ["VerifiableCredential"])
    issuer: str = ""            # DID of issuer
    valid_from: str = ""        # ISO 8601
    valid_until: str = ""       # ISO 8601
    credential_subject: Dict[str, Any] = field(default_factory=dict)
    proof: Dict[str, Any] = field(default_factory=dict)

    # Web4 extensions
    web4_credential_type: CredentialType = CredentialType.LCT_BIRTH
    witness_dids: List[str] = field(default_factory=list)
    trust_score: float = 0.0

    def to_dict(self) -> Dict:
        """Export as W3C VC JSON."""
        vc = {
            "@context": self.context,
            "type": self.type,
            "issuer": self.issuer,
            "credentialSubject": self.credential_subject,
        }
        if self.id:
            vc["id"] = self.id
        if self.valid_from:
            vc["validFrom"] = self.valid_from
        if self.valid_until:
            vc["validUntil"] = self.valid_until
        if self.proof:
            vc["proof"] = self.proof
        if self.witness_dids:
            vc["web4:witnesses"] = self.witness_dids
        if self.trust_score > 0:
            vc["web4:trustScore"] = self.trust_score
        return vc

    def compute_hash(self) -> str:
        """Compute content hash for integrity verification."""
        content = json.dumps(self.credential_subject, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class VCFactory:
    """Factory for creating Web4 Verifiable Credentials."""

    def create_lct_birth_vc(self, lct: LCTRecord,
                             issuer_did: str) -> VerifiableCredential:
        """Create a VC from an LCT birth certificate."""
        now = time.time()
        vc = VerifiableCredential(
            id=f"urn:web4:vc:{hashlib.sha256(f'{lct.w4id}:{now}'.encode()).hexdigest()[:12]}",
            type=["VerifiableCredential", "Web4LCTBirthCertificate"],
            issuer=issuer_did,
            valid_from=self._iso_time(lct.birth_time or now),
            credential_subject={
                "id": lct.w4id,
                "lctUri": lct.lct_uri,
                "entityType": lct.entity_type,
                "birthTime": lct.birth_time,
                "hardwareBound": lct.hardware_bound,
            },
            web4_credential_type=CredentialType.LCT_BIRTH,
            witness_dids=[f"did:web4:key:{w}" for w in lct.witnesses],
        )
        return vc

    def create_trust_attestation_vc(self, subject_did: str,
                                     t3_scores: Dict[str, float],
                                     issuer_did: str,
                                     validity_days: int = 90) -> VerifiableCredential:
        """Create a trust attestation VC with T3 scores."""
        now = time.time()
        composite = sum(t3_scores.values()) / max(1, len(t3_scores))
        return VerifiableCredential(
            id=f"urn:web4:vc:{hashlib.sha256(f'{subject_did}:trust:{now}'.encode()).hexdigest()[:12]}",
            type=["VerifiableCredential", "Web4TrustAttestation"],
            issuer=issuer_did,
            valid_from=self._iso_time(now),
            valid_until=self._iso_time(now + validity_days * 86400),
            credential_subject={
                "id": subject_did,
                "t3": t3_scores,
                "t3Composite": round(composite, 4),
                "attestationTime": now,
            },
            web4_credential_type=CredentialType.TRUST_ATTESTATION,
            trust_score=composite,
        )

    def create_compliance_vc(self, subject_did: str,
                              compliance_level: str,
                              articles_covered: List[str],
                              issuer_did: str) -> VerifiableCredential:
        """Create an EU AI Act compliance VC."""
        now = time.time()
        return VerifiableCredential(
            id=f"urn:web4:vc:{hashlib.sha256(f'{subject_did}:compliance:{now}'.encode()).hexdigest()[:12]}",
            type=["VerifiableCredential", "Web4ComplianceCertificate"],
            issuer=issuer_did,
            valid_from=self._iso_time(now),
            valid_until=self._iso_time(now + 365 * 86400),
            credential_subject={
                "id": subject_did,
                "complianceLevel": compliance_level,
                "articlesCovered": articles_covered,
                "regulation": "EU 2024/1689",
                "assessmentDate": now,
            },
            web4_credential_type=CredentialType.COMPLIANCE_CERT,
        )

    def _iso_time(self, ts: float) -> str:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════
# PART 4: SD-JWT (SELECTIVE DISCLOSURE)
# ═══════════════════════════════════════════════════════════════

@dataclass
class SDJWTDisclosure:
    """A single selective disclosure within an SD-JWT."""
    salt: str = ""
    claim_name: str = ""
    claim_value: Any = None
    disclosure_hash: str = ""

    def compute_hash(self) -> str:
        content = json.dumps([self.salt, self.claim_name, self.claim_value],
                           sort_keys=True, default=str)
        encoded = base64.urlsafe_b64encode(content.encode()).decode().rstrip("=")
        self.disclosure_hash = hashlib.sha256(encoded.encode()).hexdigest()[:16]
        return self.disclosure_hash


@dataclass
class SDJWT:
    """
    SD-JWT for selective disclosure of T3 tensor dimensions.

    Allows an entity to prove specific trust dimensions without
    revealing all of them. E.g., prove talent > 0.8 without
    revealing training or temperament scores.
    """
    issuer: str = ""
    subject: str = ""
    issued_at: float = 0.0
    expires_at: float = 0.0
    disclosures: List[SDJWTDisclosure] = field(default_factory=list)
    disclosed_claims: Dict[str, Any] = field(default_factory=dict)
    undisclosed_hashes: List[str] = field(default_factory=list)  # _sd array
    signature: str = ""

    def add_disclosure(self, claim_name: str, claim_value: Any,
                       salt: str = "") -> SDJWTDisclosure:
        """Add a selectively disclosable claim."""
        if not salt:
            salt = hashlib.sha256(
                f"{claim_name}:{time.time()}".encode()
            ).hexdigest()[:8]
        d = SDJWTDisclosure(
            salt=salt,
            claim_name=claim_name,
            claim_value=claim_value,
        )
        d.compute_hash()
        self.disclosures.append(d)
        self.undisclosed_hashes.append(d.disclosure_hash)
        return d

    def create_presentation(self, disclosed_indices: List[int]) -> Dict:
        """Create a presentation with only selected disclosures."""
        presented_claims = {}
        presented_disclosures = []
        remaining_hashes = list(self.undisclosed_hashes)

        for i in disclosed_indices:
            if i < len(self.disclosures):
                d = self.disclosures[i]
                presented_claims[d.claim_name] = d.claim_value
                presented_disclosures.append({
                    "salt": d.salt,
                    "claim": d.claim_name,
                    "value": d.claim_value,
                })
                if d.disclosure_hash in remaining_hashes:
                    remaining_hashes.remove(d.disclosure_hash)

        return {
            "issuer": self.issuer,
            "subject": self.subject,
            "disclosed_claims": presented_claims,
            "disclosures": presented_disclosures,
            "_sd": remaining_hashes,  # Hashes of undisclosed claims
            "total_claims": len(self.disclosures),
            "disclosed_count": len(disclosed_indices),
        }

    def verify_disclosure(self, disclosure: SDJWTDisclosure) -> bool:
        """Verify a disclosure matches an undisclosed hash."""
        expected_hash = disclosure.compute_hash()
        return expected_hash in self.undisclosed_hashes


class SDJWTFactory:
    """Factory for creating SD-JWTs from Web4 trust data."""

    def create_t3_sdjwt(self, subject_did: str, issuer_did: str,
                         t3_scores: Dict[str, float],
                         validity_days: int = 90) -> SDJWT:
        """Create an SD-JWT with selectively disclosable T3 dimensions."""
        now = time.time()
        sdjwt = SDJWT(
            issuer=issuer_did,
            subject=subject_did,
            issued_at=now,
            expires_at=now + validity_days * 86400,
        )

        # Add each T3 dimension as a separate disclosure
        for dim, score in t3_scores.items():
            sdjwt.add_disclosure(f"t3_{dim}", score)

        # Add composite as a disclosure too
        composite = sum(t3_scores.values()) / max(1, len(t3_scores))
        sdjwt.add_disclosure("t3_composite", round(composite, 4))

        # Sign
        content = f"{issuer_did}:{subject_did}:{now}:{len(sdjwt.disclosures)}"
        sdjwt.signature = hashlib.sha256(content.encode()).hexdigest()[:16]

        return sdjwt


# ═══════════════════════════════════════════════════════════════
# PART 5: DIDComm MESSAGING
# ═══════════════════════════════════════════════════════════════

class DIDCommMessageType(Enum):
    """DIDComm v2 message types relevant to Web4."""
    TRUST_REQUEST = "https://web4.io/protocols/trust/1.0/request"
    TRUST_RESPONSE = "https://web4.io/protocols/trust/1.0/response"
    VC_ISSUANCE = "https://web4.io/protocols/vc/1.0/issue"
    VC_PRESENTATION = "https://web4.io/protocols/vc/1.0/present"
    WITNESS_REQUEST = "https://web4.io/protocols/witness/1.0/request"
    WITNESS_ATTESTATION = "https://web4.io/protocols/witness/1.0/attest"


@dataclass
class DIDCommMessage:
    """
    DIDComm v2 message wrapping Web4 interactions.
    Enables trust-gated delivery via T3 thresholds.
    """
    id: str = ""
    type: str = ""
    from_did: str = ""
    to_did: str = ""
    created_time: float = 0.0
    body: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict] = field(default_factory=list)

    # Web4 extensions
    trust_gate: float = 0.0        # Minimum T3 to accept
    encrypted: bool = False
    thread_id: str = ""

    def to_dict(self) -> Dict:
        msg = {
            "id": self.id,
            "type": self.type,
            "from": self.from_did,
            "to": [self.to_did],
            "created_time": int(self.created_time),
            "body": self.body,
        }
        if self.attachments:
            msg["attachments"] = self.attachments
        if self.trust_gate > 0:
            msg["web4:trustGate"] = self.trust_gate
        if self.thread_id:
            msg["thid"] = self.thread_id
        return msg


class DIDCommBridge:
    """
    Bridge between Web4 messaging and DIDComm v2.
    Trust-gates delivery based on T3 scores.
    """

    def __init__(self):
        self.message_log: List[DIDCommMessage] = []
        self.trust_registry: Dict[str, float] = {}  # did → t3_composite

    def register_trust(self, did: str, t3_composite: float):
        self.trust_registry[did] = t3_composite

    def create_message(self, msg_type: DIDCommMessageType,
                       from_did: str, to_did: str,
                       body: Dict, trust_gate: float = 0.0) -> DIDCommMessage:
        """Create a DIDComm message."""
        now = time.time()
        msg = DIDCommMessage(
            id=hashlib.sha256(f"{from_did}:{to_did}:{now}".encode()).hexdigest()[:12],
            type=msg_type.value,
            from_did=from_did,
            to_did=to_did,
            created_time=now,
            body=body,
            trust_gate=trust_gate,
        )
        return msg

    def deliver(self, msg: DIDCommMessage) -> Tuple[bool, str]:
        """Attempt to deliver a message, checking trust gate."""
        # Check trust gate
        if msg.trust_gate > 0:
            sender_trust = self.trust_registry.get(msg.from_did, 0.0)
            if sender_trust < msg.trust_gate:
                return (False, f"Trust gate failed: {sender_trust:.2f} < {msg.trust_gate:.2f}")

        self.message_log.append(msg)
        return (True, "delivered")

    def get_messages_for(self, did: str) -> List[DIDCommMessage]:
        """Get all messages delivered to a DID."""
        return [m for m in self.message_log if m.to_did == did]


# ═══════════════════════════════════════════════════════════════
# PART 6: BIDIRECTIONAL RESOLUTION
# ═══════════════════════════════════════════════════════════════

class DIDResolver:
    """
    Bidirectional DID ↔ LCT resolution.
    Resolves did:web4: DIDs to DID Documents and vice versa.
    """

    def __init__(self):
        self.did_documents: Dict[str, DIDDocument] = {}
        self.lct_records: Dict[str, LCTRecord] = {}
        self.mapper = LCTDIDMapper()

    def register_lct(self, lct: LCTRecord):
        """Register an LCT record and auto-generate DID Document."""
        self.lct_records[lct.lct_uri] = lct
        doc = self.mapper.lct_to_did_document(lct)
        self.did_documents[doc.id] = doc

    def register_did_document(self, doc: DIDDocument):
        """Register an external DID Document."""
        self.did_documents[doc.id] = doc

    def resolve_did(self, did: str) -> Optional[DIDDocument]:
        """Resolve a DID to its DID Document."""
        return self.did_documents.get(did)

    def resolve_lct(self, lct_uri: str) -> Optional[DIDDocument]:
        """Resolve an LCT URI to a DID Document."""
        lct = self.lct_records.get(lct_uri)
        if not lct:
            return None
        did = lct.w4id
        return self.did_documents.get(did)

    def did_to_lct(self, did: str) -> Optional[LCTRecord]:
        """Get the LCT record for a DID."""
        doc = self.did_documents.get(did)
        if not doc:
            return None
        # Check if we have the original LCT
        if doc.lct_uri in self.lct_records:
            return self.lct_records[doc.lct_uri]
        # Import from DID Document
        return self.mapper.did_document_to_lct(doc)

    def list_dids(self) -> List[str]:
        return list(self.did_documents.keys())


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    return condition


def run_tests():
    results = []
    now = time.time()

    # ── S1: LCT Record ─────────────────────────────────────────
    print("\nS1: LCT Record")
    lct = LCTRecord(
        lct_uri="lct://acme:agent-alpha@web4",
        w4id="did:web4:key:abc123def456",
        public_key="ed25519pubkey_abc123",
        entity_type="software_ai",
        society_id="society-acme",
        t3_talent=0.85, t3_training=0.80, t3_temperament=0.90,
        hardware_bound=True,
        birth_time=now - 86400,
        witnesses=["witness1hash", "witness2hash"],
    )
    results.append(check("s1_composite", abs(lct.t3_composite - 0.85) < 0.01))
    results.append(check("s1_w4id", lct.w4id.startswith("did:web4:")))
    results.append(check("s1_lct_uri", lct.lct_uri.startswith("lct://")))

    # ── S2: LCT → DID Document ─────────────────────────────────
    print("\nS2: LCT → DID Document")
    mapper = LCTDIDMapper()
    doc = mapper.lct_to_did_document(lct)
    results.append(check("s2_did_id", doc.id == lct.w4id))
    results.append(check("s2_has_vm", len(doc.verification_method) == 1))
    results.append(check("s2_has_auth", len(doc.authentication) == 1))
    results.append(check("s2_lct_preserved", doc.lct_uri == lct.lct_uri))
    results.append(check("s2_t3_preserved", abs(doc.t3_composite - lct.t3_composite) < 0.01))
    results.append(check("s2_hw_bound", doc.hardware_bound))

    # ── S3: DID Document JSON Export ────────────────────────────
    print("\nS3: DID Document JSON Export")
    doc_dict = doc.to_dict()
    results.append(check("s3_context", "@context" in doc_dict))
    results.append(check("s3_did_core_context",
        "https://www.w3.org/ns/did/v1" in doc_dict["@context"]))
    results.append(check("s3_web4_context",
        "https://web4.io/ns/v1" in doc_dict["@context"]))
    results.append(check("s3_vm_has_key",
        doc_dict["verificationMethod"][0]["publicKeyMultibase"].startswith("z")))
    results.append(check("s3_web4_extension", "web4:lctUri" in doc_dict))

    json_str = doc.to_json()
    results.append(check("s3_valid_json", json.loads(json_str) is not None))

    # ── S4: DID Document → LCT ─────────────────────────────────
    print("\nS4: DID Document → LCT")
    imported_lct = mapper.did_document_to_lct(doc)
    results.append(check("s4_w4id_preserved", imported_lct.w4id == lct.w4id))
    results.append(check("s4_lct_uri_preserved", imported_lct.lct_uri == lct.lct_uri))
    results.append(check("s4_hw_bound", imported_lct.hardware_bound == lct.hardware_bound))
    results.append(check("s4_society", imported_lct.society_id == lct.society_id))

    # ── S5: DID Document Services ───────────────────────────────
    print("\nS5: DID Document Services")
    results.append(check("s5_has_services", len(doc.service) == 2))
    svc_types = {s.type for s in doc.service}
    results.append(check("s5_lct_service", "Web4LCT" in svc_types))
    results.append(check("s5_society_service", "Web4Society" in svc_types))

    # ── S6: Verifiable Credential — LCT Birth ──────────────────
    print("\nS6: Verifiable Credential — LCT Birth")
    vc_factory = VCFactory()
    birth_vc = vc_factory.create_lct_birth_vc(lct, "did:web4:key:issuer123")
    results.append(check("s6_has_id", len(birth_vc.id) > 0))
    results.append(check("s6_type", "Web4LCTBirthCertificate" in birth_vc.type))
    results.append(check("s6_issuer", birth_vc.issuer == "did:web4:key:issuer123"))
    results.append(check("s6_subject_id",
        birth_vc.credential_subject["id"] == lct.w4id))
    results.append(check("s6_hw_bound_in_subject",
        birth_vc.credential_subject["hardwareBound"] is True))

    vc_dict = birth_vc.to_dict()
    results.append(check("s6_vc_context",
        "https://www.w3.org/ns/credentials/v2" in vc_dict["@context"]))
    results.append(check("s6_witnesses", len(vc_dict.get("web4:witnesses", [])) == 2))

    # ── S7: Trust Attestation VC ────────────────────────────────
    print("\nS7: Trust Attestation VC")
    t3 = {"talent": 0.85, "training": 0.80, "temperament": 0.90}
    trust_vc = vc_factory.create_trust_attestation_vc(
        lct.w4id, t3, "did:web4:key:auditor1", validity_days=90
    )
    results.append(check("s7_trust_type", "Web4TrustAttestation" in trust_vc.type))
    results.append(check("s7_has_t3", "t3" in trust_vc.credential_subject))
    results.append(check("s7_composite",
        abs(trust_vc.credential_subject["t3Composite"] - 0.85) < 0.01))
    results.append(check("s7_trust_score", abs(trust_vc.trust_score - 0.85) < 0.01))
    results.append(check("s7_has_validity", len(trust_vc.valid_until) > 0))

    # ── S8: Compliance VC ───────────────────────────────────────
    print("\nS8: Compliance VC")
    comp_vc = vc_factory.create_compliance_vc(
        lct.w4id, "fully_compliant",
        ["ART_9", "ART_10", "ART_11", "ART_12", "ART_13", "ART_14", "ART_15"],
        "did:web4:key:auditor2"
    )
    results.append(check("s8_compliance_type",
        "Web4ComplianceCertificate" in comp_vc.type))
    results.append(check("s8_regulation",
        comp_vc.credential_subject["regulation"] == "EU 2024/1689"))
    results.append(check("s8_articles",
        len(comp_vc.credential_subject["articlesCovered"]) == 7))

    # ── S9: VC Content Hash ─────────────────────────────────────
    print("\nS9: VC Content Hash")
    h1 = birth_vc.compute_hash()
    h2 = birth_vc.compute_hash()
    results.append(check("s9_deterministic", h1 == h2))
    results.append(check("s9_length", len(h1) == 16))

    # Different VC should have different hash
    h3 = trust_vc.compute_hash()
    results.append(check("s9_different", h1 != h3))

    # ── S10: SD-JWT Creation ────────────────────────────────────
    print("\nS10: SD-JWT Creation")
    sdjwt_factory = SDJWTFactory()
    sdjwt = sdjwt_factory.create_t3_sdjwt(
        lct.w4id, "did:web4:key:issuer",
        {"talent": 0.85, "training": 0.80, "temperament": 0.90}
    )
    results.append(check("s10_four_disclosures", len(sdjwt.disclosures) == 4))  # 3 dims + composite
    results.append(check("s10_signature", len(sdjwt.signature) == 16))
    results.append(check("s10_undisclosed_hashes", len(sdjwt.undisclosed_hashes) == 4))

    # ── S11: SD-JWT Selective Presentation ──────────────────────
    print("\nS11: SD-JWT Selective Presentation")
    # Disclose only talent
    pres = sdjwt.create_presentation([0])
    results.append(check("s11_one_disclosed", pres["disclosed_count"] == 1))
    results.append(check("s11_talent_disclosed", "t3_talent" in pres["disclosed_claims"]))
    results.append(check("s11_training_hidden", "t3_training" not in pres["disclosed_claims"]))
    results.append(check("s11_sd_has_hidden", len(pres["_sd"]) == 3))  # 3 still hidden

    # Disclose all
    pres_all = sdjwt.create_presentation([0, 1, 2, 3])
    results.append(check("s11_all_disclosed", pres_all["disclosed_count"] == 4))
    results.append(check("s11_no_hidden", len(pres_all["_sd"]) == 0))

    # ── S12: SD-JWT Verification ────────────────────────────────
    print("\nS12: SD-JWT Verification")
    # Verify a disclosure against the undisclosed hashes
    d = sdjwt.disclosures[0]
    results.append(check("s12_valid_disclosure", sdjwt.verify_disclosure(d)))

    # Fake disclosure should fail
    fake = SDJWTDisclosure(salt="fake", claim_name="t3_talent", claim_value=0.99)
    fake.compute_hash()
    results.append(check("s12_fake_fails", not sdjwt.verify_disclosure(fake)))

    # ── S13: DIDComm Message ────────────────────────────────────
    print("\nS13: DIDComm Message")
    bridge = DIDCommBridge()
    bridge.register_trust(lct.w4id, 0.85)
    bridge.register_trust("did:web4:key:partner", 0.75)

    msg = bridge.create_message(
        DIDCommMessageType.TRUST_REQUEST,
        lct.w4id, "did:web4:key:partner",
        {"request": "t3_attestation", "dimensions": ["talent"]},
        trust_gate=0.5,
    )
    results.append(check("s13_msg_id", len(msg.id) > 0))
    results.append(check("s13_msg_type", "trust" in msg.type))
    results.append(check("s13_trust_gate", msg.trust_gate == 0.5))

    msg_dict = msg.to_dict()
    results.append(check("s13_json_from", msg_dict["from"] == lct.w4id))
    results.append(check("s13_json_to", msg_dict["to"] == ["did:web4:key:partner"]))

    # ── S14: DIDComm Trust-Gated Delivery ───────────────────────
    print("\nS14: DIDComm Trust-Gated Delivery")
    delivered, reason = bridge.deliver(msg)
    results.append(check("s14_delivered", delivered))
    results.append(check("s14_reason", reason == "delivered"))

    # Low trust sender should be blocked
    low_trust_msg = bridge.create_message(
        DIDCommMessageType.TRUST_REQUEST,
        "did:web4:key:untrusted", lct.w4id,
        {"request": "access"},
        trust_gate=0.5,
    )
    blocked, block_reason = bridge.deliver(low_trust_msg)
    results.append(check("s14_blocked", not blocked))
    results.append(check("s14_block_reason", "Trust gate" in block_reason))

    # No trust gate → always delivers
    no_gate_msg = bridge.create_message(
        DIDCommMessageType.TRUST_RESPONSE,
        "did:web4:key:anyone", lct.w4id,
        {"response": "ok"},
    )
    ok, _ = bridge.deliver(no_gate_msg)
    results.append(check("s14_no_gate_ok", ok))

    # ── S15: Message Retrieval ──────────────────────────────────
    print("\nS15: Message Retrieval")
    msgs = bridge.get_messages_for("did:web4:key:partner")
    results.append(check("s15_one_msg", len(msgs) == 1))
    results.append(check("s15_correct_sender", msgs[0].from_did == lct.w4id))

    msgs_alpha = bridge.get_messages_for(lct.w4id)
    results.append(check("s15_alpha_msgs", len(msgs_alpha) == 1))  # no_gate_msg

    # ── S16: DID Resolver ───────────────────────────────────────
    print("\nS16: DID Resolver")
    resolver = DIDResolver()
    resolver.register_lct(lct)

    # Resolve by DID
    resolved = resolver.resolve_did(lct.w4id)
    results.append(check("s16_resolved", resolved is not None))
    results.append(check("s16_did_match", resolved.id == lct.w4id))

    # Resolve by LCT URI
    resolved_lct = resolver.resolve_lct(lct.lct_uri)
    results.append(check("s16_lct_resolved", resolved_lct is not None))
    results.append(check("s16_lct_match", resolved_lct.id == lct.w4id))

    # ── S17: DID → LCT Resolution ──────────────────────────────
    print("\nS17: DID → LCT Resolution")
    lct_from_did = resolver.did_to_lct(lct.w4id)
    results.append(check("s17_lct_found", lct_from_did is not None))
    results.append(check("s17_w4id_match", lct_from_did.w4id == lct.w4id))
    results.append(check("s17_uri_match", lct_from_did.lct_uri == lct.lct_uri))

    # Unknown DID
    unknown = resolver.did_to_lct("did:web4:key:nonexistent")
    results.append(check("s17_unknown_none", unknown is None))

    # ── S18: Resolver — External DID ────────────────────────────
    print("\nS18: External DID Import")
    external_doc = DIDDocument(
        id="did:key:z6MkExternalAgent",
        verification_method=[
            VerificationMethod(
                id="did:key:z6MkExternalAgent#key-1",
                type="Ed25519VerificationKey2020",
                public_key_multibase="zExternalPubKey123",
            )
        ],
        lct_uri="lct://external:agent@other",
        t3_composite=0.6,
    )
    resolver.register_did_document(external_doc)
    ext_resolved = resolver.resolve_did("did:key:z6MkExternalAgent")
    results.append(check("s18_ext_resolved", ext_resolved is not None))

    ext_lct = resolver.did_to_lct("did:key:z6MkExternalAgent")
    results.append(check("s18_ext_lct", ext_lct is not None))
    results.append(check("s18_ext_key", ext_lct.public_key == "ExternalPubKey123"))

    # ── S19: Multiple LCTs in Resolver ──────────────────────────
    print("\nS19: Multiple LCTs")
    lct2 = LCTRecord(
        lct_uri="lct://acme:agent-beta@web4",
        w4id="did:web4:key:beta789",
        public_key="ed25519pubkey_beta",
        t3_talent=0.7, t3_training=0.7, t3_temperament=0.7,
    )
    resolver.register_lct(lct2)
    all_dids = resolver.list_dids()
    results.append(check("s19_three_dids", len(all_dids) == 3))  # alpha, external, beta

    beta_doc = resolver.resolve_did("did:web4:key:beta789")
    results.append(check("s19_beta_found", beta_doc is not None))
    results.append(check("s19_beta_t3", abs(beta_doc.t3_composite - 0.7) < 0.01))

    # ── S20: Credential Lifecycle ───────────────────────────────
    print("\nS20: Credential Lifecycle")
    # Create → Attest → Present flow
    birth = vc_factory.create_lct_birth_vc(lct, "did:web4:key:ca")
    trust = vc_factory.create_trust_attestation_vc(
        lct.w4id, {"talent": 0.85, "training": 0.80, "temperament": 0.90},
        "did:web4:key:auditor"
    )
    compliance = vc_factory.create_compliance_vc(
        lct.w4id, "full", ["ART_9", "ART_15"], "did:web4:key:authority"
    )

    # All three should have different IDs
    ids = {birth.id, trust.id, compliance.id}
    results.append(check("s20_unique_ids", len(ids) == 3))
    results.append(check("s20_all_have_issuer",
        all(vc.issuer for vc in [birth, trust, compliance])))
    results.append(check("s20_all_have_subject",
        all(vc.credential_subject.get("id") for vc in [birth, trust, compliance])))

    # ── S21: SD-JWT Privacy ─────────────────────────────────────
    print("\nS21: SD-JWT Privacy")
    # Create a presentation that reveals ONLY composite
    pres_composite = sdjwt.create_presentation([3])  # Index 3 is composite
    results.append(check("s21_composite_only",
        "t3_composite" in pres_composite["disclosed_claims"]))
    results.append(check("s21_dims_hidden",
        "t3_talent" not in pres_composite["disclosed_claims"]))
    results.append(check("s21_three_hidden", len(pres_composite["_sd"]) == 3))

    # The value should be correct
    results.append(check("s21_value_correct",
        abs(pres_composite["disclosed_claims"]["t3_composite"] - 0.85) < 0.01))

    # ── S22: DIDComm Message Types ──────────────────────────────
    print("\nS22: DIDComm Message Types")
    for msg_type in DIDCommMessageType:
        msg = bridge.create_message(msg_type, lct.w4id, lct2.w4id, {})
        results.append(check(f"s22_{msg_type.name.lower()}", len(msg.id) > 0))

    # ── Summary ─────────────────────────────────────────────────
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"W3C DID/VC Interoperability Bridge: {passed}/{total} checks passed")
    if passed == total:
        print("ALL CHECKS PASSED")
    else:
        print(f"FAILURES: {total - passed}")
    return passed == total


if __name__ == "__main__":
    run_tests()
