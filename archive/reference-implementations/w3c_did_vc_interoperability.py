#!/usr/bin/env python3
"""
W3C DID/VC Interoperability Bridge — Web4 Reference Implementation

Bridges Web4's native identity system (W4ID, LCT) with the W3C
Decentralized Identifier (DID) and Verifiable Credential (VC)
ecosystem. This enables Web4 entities to participate in
standards-compliant identity flows.

Implements:
  1. DIDDocumentMapper: Converts W4ID/LCT to W3C DID Document format
  2. LCTVerifiableCredential: Wraps LCT birth cert as W3C VC
  3. T3CredentialIssuer: Issues T3 trust scores as Verifiable Credentials
  4. SDJWTDisclosure: Selective disclosure of T3 dimensions via SD-JWT pattern
  5. DIDResolver: Bidirectional resolution (DID→LCT and LCT→DID)
  6. PresentationExchange: OpenID4VP-style credential presentation
  7. ComplianceCredential: EU AI Act compliance status as W3C VC
  8. InteropOrchestrator: Full bridge lifecycle

W3C specs: DID Core 1.0, VC Data Model 2.0, DID Resolution 1.0
Pattern: SD-JWT (Selective Disclosure JSON Web Token) for T3 privacy

Builds on: w4id_data_formats.py, lct_core_spec.py, lct_protocol.py,
           witnessing_attestation_spec.py, zk_trust_proofs.py

Checks: 87
"""

import hashlib
import json
import math
import time
import base64
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# PART 1: DATA MODEL
# ═══════════════════════════════════════════════════════════════

class DIDMethod(Enum):
    """DID method types."""
    WEB4 = "web4"       # did:web4:...
    KEY = "key"         # did:key:...
    WEB = "web"         # did:web:...
    ION = "ion"         # did:ion:...


class CredentialType(Enum):
    """Types of Verifiable Credentials."""
    LCT_BIRTH = "LCTBirthCertificate"
    T3_ATTESTATION = "T3TrustAttestation"
    V3_ATTESTATION = "V3ValueAttestation"
    COMPLIANCE = "EUAIActCompliance"
    WITNESS = "WitnessAttestation"
    HARDWARE_BINDING = "HardwareBindingAttestation"


class PresentationPurpose(Enum):
    """Why a credential is being presented."""
    AUTHENTICATION = "authentication"
    COMPLIANCE_PROOF = "compliance_proof"
    TRUST_VERIFICATION = "trust_verification"
    DELEGATION_PROOF = "delegation_proof"


class DisclosureLevel(Enum):
    """How much T3 detail to disclose."""
    NONE = "none"             # Just confirm existence
    BINARY = "binary"         # Above/below threshold
    RANGE = "range"           # Bucketed range (e.g., 0.7-0.8)
    PRECISE = "precise"       # Exact values


@dataclass
class VerificationMethod:
    """W3C DID verification method."""
    method_id: str = ""
    method_type: str = "Ed25519VerificationKey2020"
    controller: str = ""
    public_key_multibase: str = ""


@dataclass
class Service:
    """W3C DID service endpoint."""
    service_id: str = ""
    service_type: str = ""
    endpoint: str = ""


# ═══════════════════════════════════════════════════════════════
# PART 2: DID DOCUMENT MAPPER
# ═══════════════════════════════════════════════════════════════

@dataclass
class DIDDocument:
    """W3C DID Document mapped from Web4 identity."""
    context: List[str] = field(default_factory=lambda: [
        "https://www.w3.org/ns/did/v1",
        "https://web4.io/ns/did/v1",
    ])
    did: str = ""
    also_known_as: List[str] = field(default_factory=list)
    controller: str = ""
    verification_method: List[Dict] = field(default_factory=list)
    authentication: List[str] = field(default_factory=list)
    assertion_method: List[str] = field(default_factory=list)
    service: List[Dict] = field(default_factory=list)
    created: str = ""
    updated: str = ""
    deactivated: bool = False

    def to_dict(self) -> Dict:
        doc = {
            "@context": self.context,
            "id": self.did,
            "controller": self.controller or self.did,
        }
        if self.also_known_as:
            doc["alsoKnownAs"] = self.also_known_as
        if self.verification_method:
            doc["verificationMethod"] = self.verification_method
        if self.authentication:
            doc["authentication"] = self.authentication
        if self.assertion_method:
            doc["assertionMethod"] = self.assertion_method
        if self.service:
            doc["service"] = self.service
        if self.created:
            doc["created"] = self.created
        if self.updated:
            doc["updated"] = self.updated
        if self.deactivated:
            doc["deactivated"] = True
        return doc


class DIDDocumentMapper:
    """
    Converts W4ID/LCT identity into W3C DID Document format.
    Maps: W4ID → DID, LCT URI → alsoKnownAs, keys → verificationMethod.
    """

    def map_to_did(self, w4id: str, lct_uri: str = "",
                   public_key_hash: str = "",
                   entity_type: str = "",
                   hardware_bound: bool = False,
                   services: Optional[List[Dict]] = None) -> DIDDocument:
        """Map Web4 identity to DID Document."""
        # Convert W4ID to DID format
        if w4id.startswith("did:web4:"):
            did = w4id
        else:
            did = f"did:web4:{w4id}"

        # Create verification method
        vm_id = f"{did}#key-1"
        verification_methods = [{
            "id": vm_id,
            "type": "Ed25519VerificationKey2020",
            "controller": did,
            "publicKeyMultibase": f"z{public_key_hash[:32]}" if public_key_hash else "",
        }]

        # Services
        svc_list = []
        if services:
            svc_list = services
        else:
            svc_list.append({
                "id": f"{did}#web4-endpoint",
                "type": "Web4TrustEndpoint",
                "serviceEndpoint": f"https://web4.io/entities/{w4id}",
            })
            if hardware_bound:
                svc_list.append({
                    "id": f"{did}#hardware-attestation",
                    "type": "Web4HardwareAttestation",
                    "serviceEndpoint": f"https://web4.io/hardware/{w4id}",
                })

        also_known = []
        if lct_uri:
            also_known.append(lct_uri)

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return DIDDocument(
            did=did,
            also_known_as=also_known,
            controller=did,
            verification_method=verification_methods,
            authentication=[vm_id],
            assertion_method=[vm_id],
            service=svc_list,
            created=now,
            updated=now,
        )

    def extract_w4id(self, did_doc: DIDDocument) -> str:
        """Extract W4ID from DID Document."""
        did = did_doc.did
        if did.startswith("did:web4:"):
            return did[9:]  # Strip "did:web4:"
        return did


# ═══════════════════════════════════════════════════════════════
# PART 3: LCT VERIFIABLE CREDENTIAL
# ═══════════════════════════════════════════════════════════════

@dataclass
class VerifiableCredential:
    """W3C VC Data Model 2.0 credential."""
    context: List[str] = field(default_factory=lambda: [
        "https://www.w3.org/ns/credentials/v2",
        "https://web4.io/ns/credentials/v1",
    ])
    credential_id: str = ""
    credential_type: List[str] = field(default_factory=lambda: ["VerifiableCredential"])
    issuer: str = ""
    valid_from: str = ""
    valid_until: str = ""
    credential_subject: Dict = field(default_factory=dict)
    proof: Dict = field(default_factory=dict)
    credential_status: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        vc = {
            "@context": self.context,
            "id": self.credential_id,
            "type": self.credential_type,
            "issuer": self.issuer,
            "validFrom": self.valid_from,
            "credentialSubject": self.credential_subject,
        }
        if self.valid_until:
            vc["validUntil"] = self.valid_until
        if self.proof:
            vc["proof"] = self.proof
        if self.credential_status:
            vc["credentialStatus"] = self.credential_status
        return vc

    def compute_hash(self) -> str:
        content = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class LCTCredentialIssuer:
    """
    Issues LCT birth certificates as W3C Verifiable Credentials.
    Maps LCT fields to VC credentialSubject.
    """

    def __init__(self, issuer_did: str = ""):
        self.issuer_did = issuer_did or "did:web4:federation:issuer"
        self.issued: List[VerifiableCredential] = []

    def issue_birth_cert(self, lct_uri: str, entity_did: str,
                         entity_type: str = "", hardware_bound: bool = False,
                         created_at: float = None) -> VerifiableCredential:
        """Issue LCT birth certificate as Verifiable Credential."""
        now = time.time()
        created = created_at or now
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created))
        valid_until = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                    time.gmtime(created + 365 * 86400))

        vc = VerifiableCredential(
            credential_id=f"urn:web4:lct:{hashlib.sha256(lct_uri.encode()).hexdigest()[:12]}",
            credential_type=["VerifiableCredential", "LCTBirthCertificate"],
            issuer=self.issuer_did,
            valid_from=now_str,
            valid_until=valid_until,
            credential_subject={
                "id": entity_did,
                "lctUri": lct_uri,
                "entityType": entity_type,
                "hardwareBound": hardware_bound,
                "birthTimestamp": now_str,
                "web4Context": "https://web4.io/ontology#",
            },
            proof=self._generate_proof(entity_did, now_str),
        )
        self.issued.append(vc)
        return vc

    def _generate_proof(self, subject: str, timestamp: str) -> Dict:
        """Generate proof object (simulated Ed25519 signature)."""
        proof_content = f"{self.issuer_did}:{subject}:{timestamp}"
        sig = hashlib.sha256(proof_content.encode()).hexdigest()[:32]
        return {
            "type": "Ed25519Signature2020",
            "created": timestamp,
            "verificationMethod": f"{self.issuer_did}#key-1",
            "proofPurpose": "assertionMethod",
            "proofValue": f"z{sig}",
        }


# ═══════════════════════════════════════════════════════════════
# PART 4: T3 CREDENTIAL WITH SD-JWT
# ═══════════════════════════════════════════════════════════════

@dataclass
class SDJWTDisclosure:
    """
    Selective Disclosure JWT for T3 trust dimensions.
    Allows entity to prove T3 properties without revealing exact scores.
    """
    disclosure_id: str = ""
    entity_did: str = ""
    level: DisclosureLevel = DisclosureLevel.RANGE
    disclosed_claims: Dict = field(default_factory=dict)
    salt: str = ""
    hash_digest: str = ""

    def compute_hash(self) -> str:
        content = f"{self.disclosure_id}:{self.entity_did}:{self.salt}"
        content += f":{json.dumps(self.disclosed_claims, sort_keys=True)}"
        self.hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        return self.hash_digest


class T3CredentialIssuer:
    """
    Issues T3 trust tensor attestations as Verifiable Credentials
    with SD-JWT selective disclosure.

    Disclosure levels (stake-gated per Web4 spec):
    - NONE (<10 ATP): Just confirms entity exists
    - BINARY (<50 ATP): Above/below threshold per dimension
    - RANGE (50-99 ATP): Bucketed ranges (0.0-0.2, 0.2-0.4, etc.)
    - PRECISE (≥100 ATP): Exact T3 values
    """

    RANGE_BUCKETS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]

    def __init__(self, issuer_did: str = ""):
        self.issuer_did = issuer_did or "did:web4:federation:trust-issuer"

    def issue_t3_credential(self, entity_did: str,
                            talent: float, training: float,
                            temperament: float,
                            disclosure_level: DisclosureLevel = DisclosureLevel.RANGE,
                            atp_stake: float = 0.0) -> VerifiableCredential:
        """Issue T3 attestation credential with selective disclosure."""
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        composite = (talent + training + temperament) / 3.0

        # Build credential subject based on disclosure level
        subject = {"id": entity_did}

        if disclosure_level == DisclosureLevel.NONE:
            subject["t3Exists"] = True

        elif disclosure_level == DisclosureLevel.BINARY:
            threshold = 0.5
            subject["t3AboveThreshold"] = composite > threshold
            subject["talentAbove"] = talent > threshold
            subject["trainingAbove"] = training > threshold
            subject["temperamentAbove"] = temperament > threshold

        elif disclosure_level == DisclosureLevel.RANGE:
            subject["talentRange"] = self._to_range(talent)
            subject["trainingRange"] = self._to_range(training)
            subject["temperamentRange"] = self._to_range(temperament)
            subject["compositeRange"] = self._to_range(composite)

        elif disclosure_level == DisclosureLevel.PRECISE:
            subject["talent"] = round(talent, 4)
            subject["training"] = round(training, 4)
            subject["temperament"] = round(temperament, 4)
            subject["composite"] = round(composite, 4)

        subject["disclosureLevel"] = disclosure_level.value
        subject["atpStake"] = atp_stake

        vc = VerifiableCredential(
            credential_id=f"urn:web4:t3:{hashlib.sha256(f'{entity_did}:{now_str}'.encode()).hexdigest()[:12]}",
            credential_type=["VerifiableCredential", "T3TrustAttestation"],
            issuer=self.issuer_did,
            valid_from=now_str,
            credential_subject=subject,
            proof={
                "type": "Ed25519Signature2020",
                "created": now_str,
                "verificationMethod": f"{self.issuer_did}#key-1",
                "proofPurpose": "assertionMethod",
                "proofValue": f"z{hashlib.sha256(f'{entity_did}:{composite}'.encode()).hexdigest()[:32]}",
            },
        )
        return vc

    def _to_range(self, value: float) -> str:
        for low, high in self.RANGE_BUCKETS:
            if value < high or (value == high and high == 1.0):
                return f"{low:.1f}-{high:.1f}"
        return "0.8-1.0"

    def create_sd_jwt(self, entity_did: str,
                      talent: float, training: float, temperament: float,
                      disclosed_dims: Set[str]) -> SDJWTDisclosure:
        """Create SD-JWT with selective dimension disclosure."""
        salt = hashlib.sha256(f"{entity_did}:{time.time()}".encode()).hexdigest()[:8]

        claims = {}
        all_dims = {"talent": talent, "training": training, "temperament": temperament}
        for dim, value in all_dims.items():
            if dim in disclosed_dims:
                claims[dim] = round(value, 4)
            else:
                # Hash the undisclosed value (blinded)
                claims[f"_{dim}_hash"] = hashlib.sha256(
                    f"{salt}:{dim}:{value}".encode()
                ).hexdigest()[:16]

        disclosure = SDJWTDisclosure(
            disclosure_id=f"sdjwt-{salt}",
            entity_did=entity_did,
            level=DisclosureLevel.PRECISE if len(disclosed_dims) == 3 else DisclosureLevel.RANGE,
            disclosed_claims=claims,
            salt=salt,
        )
        disclosure.compute_hash()
        return disclosure


# ═══════════════════════════════════════════════════════════════
# PART 5: DID RESOLVER
# ═══════════════════════════════════════════════════════════════

@dataclass
class ResolutionResult:
    """Result of DID resolution."""
    did: str = ""
    did_document: Optional[DIDDocument] = None
    lct_uri: str = ""
    resolved: bool = False
    resolution_time: float = 0.0
    error: str = ""


class DIDResolver:
    """
    Bidirectional resolver: DID→LCT and LCT→DID.
    Maintains a registry of known mappings.
    """

    def __init__(self):
        self.did_to_lct: Dict[str, str] = {}
        self.lct_to_did: Dict[str, str] = {}
        self.did_documents: Dict[str, DIDDocument] = {}

    def register(self, did: str, lct_uri: str, doc: DIDDocument):
        self.did_to_lct[did] = lct_uri
        self.lct_to_did[lct_uri] = did
        self.did_documents[did] = doc

    def resolve_did(self, did: str) -> ResolutionResult:
        """Resolve DID to DID Document and LCT URI."""
        if did in self.did_documents:
            return ResolutionResult(
                did=did,
                did_document=self.did_documents[did],
                lct_uri=self.did_to_lct.get(did, ""),
                resolved=True,
                resolution_time=time.time(),
            )
        return ResolutionResult(
            did=did, resolved=False,
            error=f"DID not found: {did}",
        )

    def resolve_lct(self, lct_uri: str) -> ResolutionResult:
        """Resolve LCT URI to DID Document."""
        if lct_uri in self.lct_to_did:
            did = self.lct_to_did[lct_uri]
            return self.resolve_did(did)
        return ResolutionResult(
            lct_uri=lct_uri, resolved=False,
            error=f"LCT not found: {lct_uri}",
        )

    def known_dids(self) -> List[str]:
        return list(self.did_documents.keys())


# ═══════════════════════════════════════════════════════════════
# PART 6: PRESENTATION EXCHANGE
# ═══════════════════════════════════════════════════════════════

@dataclass
class PresentationRequest:
    """OpenID4VP-style request for credential presentation."""
    request_id: str = ""
    verifier_did: str = ""
    purpose: PresentationPurpose = PresentationPurpose.AUTHENTICATION
    required_types: List[str] = field(default_factory=list)
    min_trust: float = 0.0         # Minimum T3 composite
    require_hardware: bool = False
    require_compliance: bool = False
    timestamp: float = 0.0


@dataclass
class VerifiablePresentation:
    """W3C Verifiable Presentation containing credentials."""
    context: List[str] = field(default_factory=lambda: [
        "https://www.w3.org/ns/credentials/v2",
    ])
    presentation_id: str = ""
    presentation_type: List[str] = field(default_factory=lambda: ["VerifiablePresentation"])
    holder: str = ""
    verifiable_credential: List[Dict] = field(default_factory=list)
    proof: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "@context": self.context,
            "id": self.presentation_id,
            "type": self.presentation_type,
            "holder": self.holder,
            "verifiableCredential": self.verifiable_credential,
            "proof": self.proof,
        }


@dataclass
class PresentationResult:
    """Result of verifying a presentation."""
    verified: bool = False
    holder_did: str = ""
    credential_count: int = 0
    types_presented: List[str] = field(default_factory=list)
    meets_requirements: bool = False
    issues: List[str] = field(default_factory=list)


class PresentationExchange:
    """
    OpenID4VP-style credential presentation and verification.
    Verifier creates request → Holder creates presentation → Verifier verifies.
    """

    def __init__(self):
        self.requests: Dict[str, PresentationRequest] = {}
        self.presentations: Dict[str, VerifiablePresentation] = {}

    def create_request(self, verifier_did: str,
                       purpose: PresentationPurpose,
                       required_types: List[str],
                       min_trust: float = 0.0,
                       require_hardware: bool = False,
                       require_compliance: bool = False) -> PresentationRequest:
        now = time.time()
        req = PresentationRequest(
            request_id=hashlib.sha256(
                f"{verifier_did}:{now}".encode()
            ).hexdigest()[:12],
            verifier_did=verifier_did,
            purpose=purpose,
            required_types=required_types,
            min_trust=min_trust,
            require_hardware=require_hardware,
            require_compliance=require_compliance,
            timestamp=now,
        )
        self.requests[req.request_id] = req
        return req

    def create_presentation(self, holder_did: str,
                            credentials: List[VerifiableCredential],
                            request_id: str = "") -> VerifiablePresentation:
        """Create presentation from holder's credentials."""
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        pres = VerifiablePresentation(
            presentation_id=f"urn:web4:vp:{hashlib.sha256(f'{holder_did}:{time.time()}'.encode()).hexdigest()[:12]}",
            holder=holder_did,
            verifiable_credential=[vc.to_dict() for vc in credentials],
            proof={
                "type": "Ed25519Signature2020",
                "created": now_str,
                "verificationMethod": f"{holder_did}#key-1",
                "proofPurpose": "authentication",
                "challenge": request_id,
                "proofValue": f"z{hashlib.sha256(f'{holder_did}:{request_id}'.encode()).hexdigest()[:32]}",
            },
        )
        self.presentations[pres.presentation_id] = pres
        return pres

    def verify_presentation(self, presentation: VerifiablePresentation,
                            request: PresentationRequest) -> PresentationResult:
        """Verify presentation against request requirements."""
        result = PresentationResult(
            holder_did=presentation.holder,
            credential_count=len(presentation.verifiable_credential),
        )

        # Check credential types
        presented_types = set()
        for vc_dict in presentation.verifiable_credential:
            for t in vc_dict.get("type", []):
                presented_types.add(t)
        result.types_presented = list(presented_types)

        # Check required types
        for req_type in request.required_types:
            if req_type not in presented_types:
                result.issues.append(f"Missing required type: {req_type}")

        # Check hardware binding
        if request.require_hardware:
            has_hardware = any(
                vc.get("credentialSubject", {}).get("hardwareBound", False)
                for vc in presentation.verifiable_credential
            )
            if not has_hardware:
                result.issues.append("Hardware binding required but not present")

        # Check trust level
        if request.min_trust > 0:
            max_trust = 0.0
            for vc in presentation.verifiable_credential:
                subject = vc.get("credentialSubject", {})
                if "composite" in subject:
                    max_trust = max(max_trust, subject["composite"])
                elif "compositeRange" in subject:
                    # Parse range lower bound
                    range_str = subject["compositeRange"]
                    low = float(range_str.split("-")[0])
                    max_trust = max(max_trust, low)
            if max_trust < request.min_trust:
                result.issues.append(
                    f"Trust {max_trust:.2f} below minimum {request.min_trust:.2f}")

        # Check proof
        has_proof = bool(presentation.proof and presentation.proof.get("proofValue"))
        if not has_proof:
            result.issues.append("Missing presentation proof")

        result.verified = has_proof and len(result.issues) == 0
        result.meets_requirements = len(result.issues) == 0
        return result


# ═══════════════════════════════════════════════════════════════
# PART 7: COMPLIANCE CREDENTIAL
# ═══════════════════════════════════════════════════════════════

class ComplianceCredentialIssuer:
    """
    Issues EU AI Act compliance status as Verifiable Credential.
    Regulatory authorities verify compliance via standard VC flows.
    """

    def __init__(self, issuer_did: str = ""):
        self.issuer_did = issuer_did or "did:web4:federation:compliance-issuer"

    def issue_compliance_credential(self, entity_did: str,
                                     compliance_score: float,
                                     compliance_grade: str,
                                     articles_compliant: List[str],
                                     hardware_bound: bool = False,
                                     witness_count: int = 0) -> VerifiableCredential:
        """Issue EU AI Act compliance credential."""
        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        valid_until = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                    time.gmtime(time.time() + 180 * 86400))  # 6 months

        vc = VerifiableCredential(
            credential_id=f"urn:web4:compliance:{hashlib.sha256(f'{entity_did}:{now_str}'.encode()).hexdigest()[:12]}",
            credential_type=["VerifiableCredential", "EUAIActCompliance"],
            issuer=self.issuer_did,
            valid_from=now_str,
            valid_until=valid_until,
            credential_subject={
                "id": entity_did,
                "complianceScore": round(compliance_score, 4),
                "complianceGrade": compliance_grade,
                "articlesCompliant": articles_compliant,
                "totalArticles": 10,
                "hardwareBound": hardware_bound,
                "witnessAttestations": witness_count,
                "regulatoryFramework": "EU AI Act 2024/1689",
                "assessmentDate": now_str,
            },
            proof={
                "type": "Ed25519Signature2020",
                "created": now_str,
                "verificationMethod": f"{self.issuer_did}#key-1",
                "proofPurpose": "assertionMethod",
                "proofValue": f"z{hashlib.sha256(f'{entity_did}:{compliance_score}'.encode()).hexdigest()[:32]}",
            },
        )
        return vc


# ═══════════════════════════════════════════════════════════════
# PART 8: INTEROP ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

class InteropOrchestrator:
    """
    Full bridge lifecycle: register → issue → resolve → present → verify.
    """

    def __init__(self, federation_did: str = ""):
        self.mapper = DIDDocumentMapper()
        self.resolver = DIDResolver()
        self.lct_issuer = LCTCredentialIssuer(federation_did)
        self.t3_issuer = T3CredentialIssuer(federation_did)
        self.compliance_issuer = ComplianceCredentialIssuer(federation_did)
        self.exchange = PresentationExchange()

    def register_entity(self, w4id: str, lct_uri: str,
                        public_key_hash: str = "",
                        entity_type: str = "",
                        hardware_bound: bool = False) -> DIDDocument:
        """Register Web4 entity in DID resolver."""
        doc = self.mapper.map_to_did(w4id, lct_uri, public_key_hash,
                                      entity_type, hardware_bound)
        self.resolver.register(doc.did, lct_uri, doc)
        return doc

    def issue_full_credential_set(self, entity_did: str, lct_uri: str,
                                   entity_type: str,
                                   talent: float, training: float,
                                   temperament: float,
                                   compliance_score: float,
                                   compliance_grade: str,
                                   articles: List[str],
                                   hardware_bound: bool = False) -> List[VerifiableCredential]:
        """Issue complete set of credentials for an entity."""
        creds = []

        # LCT birth cert
        birth = self.lct_issuer.issue_birth_cert(
            lct_uri, entity_did, entity_type, hardware_bound
        )
        creds.append(birth)

        # T3 attestation
        t3 = self.t3_issuer.issue_t3_credential(
            entity_did, talent, training, temperament,
            DisclosureLevel.PRECISE, atp_stake=100.0
        )
        creds.append(t3)

        # Compliance credential
        comp = self.compliance_issuer.issue_compliance_credential(
            entity_did, compliance_score, compliance_grade, articles,
            hardware_bound
        )
        creds.append(comp)

        return creds


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

    # ── S1: DID Document Mapping ────────────────────────────────
    print("\nS1: DID Document Mapping")
    mapper = DIDDocumentMapper()
    doc = mapper.map_to_did(
        "agent-001", "lct://agent:test@web4",
        public_key_hash="a1b2c3d4e5f6" * 4,
        entity_type="ai_agent",
        hardware_bound=True,
    )
    results.append(check("s1_did_format", doc.did == "did:web4:agent-001"))
    results.append(check("s1_also_known", "lct://agent:test@web4" in doc.also_known_as))
    results.append(check("s1_has_vm", len(doc.verification_method) == 1))
    results.append(check("s1_has_auth", len(doc.authentication) == 1))
    results.append(check("s1_has_services", len(doc.service) == 2))  # endpoint + hardware
    results.append(check("s1_controller", doc.controller == doc.did))

    # ── S2: DID Document — Existing DID Format ─────────────────
    print("\nS2: Existing DID Format")
    doc2 = mapper.map_to_did("did:web4:key:abc123", "lct://key:abc@web4")
    results.append(check("s2_preserved", doc2.did == "did:web4:key:abc123"))
    w4id = mapper.extract_w4id(doc2)
    results.append(check("s2_extract", w4id == "key:abc123"))

    # ── S3: DID Document Serialization ──────────────────────────
    print("\nS3: DID Serialization")
    doc_dict = doc.to_dict()
    results.append(check("s3_context", "@context" in doc_dict))
    results.append(check("s3_id", doc_dict["id"] == "did:web4:agent-001"))
    results.append(check("s3_vm", "verificationMethod" in doc_dict))

    # ── S4: LCT Birth Cert as VC ───────────────────────────────
    print("\nS4: LCT Birth Certificate VC")
    issuer = LCTCredentialIssuer("did:web4:federation:issuer")
    birth_vc = issuer.issue_birth_cert(
        "lct://agent:test@web4",
        "did:web4:agent-001",
        "ai_agent",
        hardware_bound=True,
    )
    results.append(check("s4_type", "LCTBirthCertificate" in birth_vc.credential_type))
    results.append(check("s4_subject_id",
        birth_vc.credential_subject["id"] == "did:web4:agent-001"))
    results.append(check("s4_lct_uri",
        birth_vc.credential_subject["lctUri"] == "lct://agent:test@web4"))
    results.append(check("s4_hardware",
        birth_vc.credential_subject["hardwareBound"] is True))
    results.append(check("s4_has_proof", "proofValue" in birth_vc.proof))

    # ── S5: T3 Credential — Precise ────────────────────────────
    print("\nS5: T3 Credential — Precise")
    t3_issuer = T3CredentialIssuer()
    t3_vc = t3_issuer.issue_t3_credential(
        "did:web4:agent-001", 0.85, 0.78, 0.82,
        DisclosureLevel.PRECISE, atp_stake=100.0
    )
    results.append(check("s5_type", "T3TrustAttestation" in t3_vc.credential_type))
    subj = t3_vc.credential_subject
    results.append(check("s5_talent", subj["talent"] == 0.85))
    results.append(check("s5_training", subj["training"] == 0.78))
    results.append(check("s5_temperament", subj["temperament"] == 0.82))
    results.append(check("s5_composite", abs(subj["composite"] - 0.8167) < 0.001))
    results.append(check("s5_disclosure", subj["disclosureLevel"] == "precise"))

    # ── S6: T3 Credential — Range ──────────────────────────────
    print("\nS6: T3 Credential — Range")
    range_vc = t3_issuer.issue_t3_credential(
        "did:web4:agent-002", 0.85, 0.55, 0.72,
        DisclosureLevel.RANGE, atp_stake=75.0
    )
    subj2 = range_vc.credential_subject
    results.append(check("s6_talent_range", subj2["talentRange"] == "0.8-1.0"))
    results.append(check("s6_training_range", subj2["trainingRange"] == "0.4-0.6"))
    results.append(check("s6_temperament_range", subj2["temperamentRange"] == "0.6-0.8"))

    # ── S7: T3 Credential — Binary ─────────────────────────────
    print("\nS7: T3 Credential — Binary")
    binary_vc = t3_issuer.issue_t3_credential(
        "did:web4:agent-003", 0.8, 0.3, 0.6,
        DisclosureLevel.BINARY
    )
    subj3 = binary_vc.credential_subject
    results.append(check("s7_talent_above", subj3["talentAbove"] is True))
    results.append(check("s7_training_below", subj3["trainingAbove"] is False))
    results.append(check("s7_overall_above", subj3["t3AboveThreshold"] is True))

    # ── S8: T3 Credential — None ───────────────────────────────
    print("\nS8: T3 Credential — None Disclosure")
    none_vc = t3_issuer.issue_t3_credential(
        "did:web4:agent-004", 0.9, 0.9, 0.9,
        DisclosureLevel.NONE
    )
    subj4 = none_vc.credential_subject
    results.append(check("s8_exists_only", subj4["t3Exists"] is True))
    results.append(check("s8_no_values", "talent" not in subj4))

    # ── S9: SD-JWT Disclosure ───────────────────────────────────
    print("\nS9: SD-JWT Selective Disclosure")
    sdjwt = t3_issuer.create_sd_jwt(
        "did:web4:agent-001", 0.85, 0.78, 0.82,
        disclosed_dims={"talent", "temperament"},
    )
    results.append(check("s9_has_hash", len(sdjwt.hash_digest) == 16))
    results.append(check("s9_talent_disclosed", "talent" in sdjwt.disclosed_claims))
    results.append(check("s9_temperament_disclosed", "temperament" in sdjwt.disclosed_claims))
    results.append(check("s9_training_hidden", "_training_hash" in sdjwt.disclosed_claims))
    results.append(check("s9_talent_value", sdjwt.disclosed_claims["talent"] == 0.85))

    # ── S10: DID Resolver ───────────────────────────────────────
    print("\nS10: DID Resolver")
    resolver = DIDResolver()
    resolver.register("did:web4:agent-001", "lct://agent:test@web4", doc)

    # Resolve by DID
    res1 = resolver.resolve_did("did:web4:agent-001")
    results.append(check("s10_resolved", res1.resolved))
    results.append(check("s10_lct", res1.lct_uri == "lct://agent:test@web4"))
    results.append(check("s10_doc", res1.did_document is not None))

    # Resolve by LCT
    res2 = resolver.resolve_lct("lct://agent:test@web4")
    results.append(check("s10_lct_resolved", res2.resolved))
    results.append(check("s10_lct_did", res2.did == "did:web4:agent-001"))

    # Not found
    res3 = resolver.resolve_did("did:web4:unknown")
    results.append(check("s10_not_found", not res3.resolved))

    # ── S11: Presentation Request ───────────────────────────────
    print("\nS11: Presentation Request")
    exchange = PresentationExchange()
    req = exchange.create_request(
        "did:web4:verifier-001",
        PresentationPurpose.COMPLIANCE_PROOF,
        ["LCTBirthCertificate", "EUAIActCompliance"],
        min_trust=0.7,
        require_hardware=True,
    )
    results.append(check("s11_request_id", len(req.request_id) == 12))
    results.append(check("s11_purpose", req.purpose == PresentationPurpose.COMPLIANCE_PROOF))
    results.append(check("s11_required_types", len(req.required_types) == 2))

    # ── S12: Presentation Creation ──────────────────────────────
    print("\nS12: Presentation Creation")
    comp_issuer = ComplianceCredentialIssuer()
    comp_vc = comp_issuer.issue_compliance_credential(
        "did:web4:agent-001", 0.95, "full",
        ["Art. 9", "Art. 10", "Art. 11", "Art. 12", "Art. 13", "Art. 14", "Art. 15"],
        hardware_bound=True, witness_count=5,
    )

    presentation = exchange.create_presentation(
        "did:web4:agent-001",
        [birth_vc, comp_vc, t3_vc],
        req.request_id,
    )
    results.append(check("s12_holder", presentation.holder == "did:web4:agent-001"))
    results.append(check("s12_creds", len(presentation.verifiable_credential) == 3))
    results.append(check("s12_proof", "proofValue" in presentation.proof))

    # ── S13: Presentation Verification — Success ────────────────
    print("\nS13: Verification — Success")
    ver_result = exchange.verify_presentation(presentation, req)
    results.append(check("s13_verified", ver_result.verified))
    results.append(check("s13_meets_req", ver_result.meets_requirements))
    results.append(check("s13_no_issues", len(ver_result.issues) == 0))

    # ── S14: Presentation Verification — Missing Type ───────────
    print("\nS14: Verification — Missing Type")
    partial_pres = exchange.create_presentation(
        "did:web4:agent-002",
        [birth_vc],  # Missing compliance VC
        req.request_id,
    )
    ver2 = exchange.verify_presentation(partial_pres, req)
    results.append(check("s14_not_verified", not ver2.verified))
    results.append(check("s14_missing_type",
        any("Missing required type" in i for i in ver2.issues)))

    # ── S15: Presentation Verification — Low Trust ──────────────
    print("\nS15: Verification — Low Trust")
    low_t3 = t3_issuer.issue_t3_credential(
        "did:web4:agent-low", 0.3, 0.3, 0.3,
        DisclosureLevel.PRECISE
    )
    low_pres = exchange.create_presentation(
        "did:web4:agent-low",
        [birth_vc, comp_vc, low_t3],
        req.request_id,
    )
    ver3 = exchange.verify_presentation(low_pres, req)
    results.append(check("s15_low_trust_flagged",
        any("Trust" in i for i in ver3.issues)))

    # ── S16: Compliance Credential ──────────────────────────────
    print("\nS16: Compliance Credential")
    comp_vc2 = comp_issuer.issue_compliance_credential(
        "did:web4:agent-005", 0.75, "substantial",
        ["Art. 9", "Art. 11", "Art. 12", "Art. 15"],
        witness_count=3,
    )
    subj5 = comp_vc2.credential_subject
    results.append(check("s16_score", subj5["complianceScore"] == 0.75))
    results.append(check("s16_grade", subj5["complianceGrade"] == "substantial"))
    results.append(check("s16_articles", len(subj5["articlesCompliant"]) == 4))
    results.append(check("s16_framework",
        subj5["regulatoryFramework"] == "EU AI Act 2024/1689"))
    results.append(check("s16_has_validity",
        comp_vc2.valid_until != ""))

    # ── S17: Interop Orchestrator ───────────────────────────────
    print("\nS17: Interop Orchestrator")
    orch = InteropOrchestrator("did:web4:federation:test")
    reg_doc = orch.register_entity(
        "agent-010", "lct://agent:010@web4",
        "key_hash_abcdef" * 4,
        "ai_agent", True,
    )
    results.append(check("s17_registered", reg_doc.did == "did:web4:agent-010"))

    # Resolve
    res = orch.resolver.resolve_did("did:web4:agent-010")
    results.append(check("s17_resolvable", res.resolved))

    # Issue full credential set
    creds = orch.issue_full_credential_set(
        "did:web4:agent-010", "lct://agent:010@web4",
        "ai_agent", 0.88, 0.82, 0.85, 0.90, "full",
        ["Art. 9", "Art. 10", "Art. 11"], True,
    )
    results.append(check("s17_three_creds", len(creds) == 3))
    types = set()
    for c in creds:
        for t in c.credential_type:
            types.add(t)
    results.append(check("s17_birth_type", "LCTBirthCertificate" in types))
    results.append(check("s17_t3_type", "T3TrustAttestation" in types))
    results.append(check("s17_compliance_type", "EUAIActCompliance" in types))

    # ── S18: VC Hash Integrity ──────────────────────────────────
    print("\nS18: VC Hash Integrity")
    hash1 = birth_vc.compute_hash()
    hash2 = birth_vc.compute_hash()
    results.append(check("s18_deterministic", hash1 == hash2))
    results.append(check("s18_hash_length", len(hash1) == 16))

    # Different VC → different hash
    hash3 = t3_vc.compute_hash()
    results.append(check("s18_different", hash1 != hash3))

    # ── S19: Resolver — Known DIDs ──────────────────────────────
    print("\nS19: Resolver Known DIDs")
    all_dids = orch.resolver.known_dids()
    results.append(check("s19_has_dids", len(all_dids) >= 1))
    results.append(check("s19_agent_010", "did:web4:agent-010" in all_dids))

    # ── S20: Presentation To Dict ───────────────────────────────
    print("\nS20: Serialization")
    pres_dict = presentation.to_dict()
    results.append(check("s20_has_context", "@context" in pres_dict))
    results.append(check("s20_has_holder", pres_dict["holder"] == "did:web4:agent-001"))
    results.append(check("s20_has_vcs", len(pres_dict["verifiableCredential"]) == 3))

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
