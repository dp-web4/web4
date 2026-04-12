#!/usr/bin/env python3
"""
LCT Lifecycle Integration — Cross-Component Reference Implementation

Exercises the COMPLETE LCT lifecycle by integrating:
  - Security Framework (crypto suites, key management, VCs)
  - SAL (society-authority-law: genesis, law oracle, auditing)
  - LCT Document (canonical structure, schema compliance)
  - T3/V3 Tensors (trust + value computation)
  - MRH (Markov Relevancy Horizon: binding, pairing, witnessing)
  - R6 (law-bound action execution)

Lifecycle stages tested:
  1. Society Formation: create society with authority + law oracle
  2. Entity Genesis: birth certificate issuance with witness quorum
  3. Role Assignment: citizen → authority → witness → auditor
  4. Key Management: generate, rotate, revoke signing keys
  5. Authentication: challenge-response with crypto suite
  6. Authorization: VC issuance and verification
  7. Operation: R6 actions with law hash pinning
  8. Trust Evolution: T3/V3 changes from actions + audits
  9. Rotation: key rotation with lineage tracking
  10. Revocation: entity revocation with MRH preservation

@version 1.0.0
"""

import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Import from existing reference implementations
sys.path.insert(0, __import__('os').path.dirname(__file__))

from security_framework import (
    W4Base1Suite, W4Fips1Suite, KeyManager, KeyStorageMethod,
    Authenticator, CredentialIssuer, CredentialVerifier,
    SuiteNegotiator, SUITE_W4_BASE_1, SUITE_W4_FIPS_1,
    get_suite, canonical_json,
)

from sal_society_authority_law import (
    Society, LawDataset, Norm, Procedure, Interpretation,
    RoleType, SALError, SALEventType,
    T3Tensor, V3Tensor, BirthCertificate,
    AuditRequest, Auditor,
)


# ═══════════════════════════════════════════════════════════════
# Integrated LCT Document (simplified from lct_document.py)
# ═══════════════════════════════════════════════════════════════

@dataclass
class LCTBinding:
    """Cryptographic binding per LCT spec §3.3."""
    entity_type: str
    public_key_hex: str
    key_id: str
    suite_id: str
    hardware_anchor: Optional[str] = None
    created_at: float = 0.0
    binding_proof: str = ""

    def compute_proof(self, suite, private_key) -> str:
        payload = canonical_json({
            "entity_type": self.entity_type,
            "public_key": self.public_key_hex,
            "created_at": self.created_at,
        })
        sig = suite.sign(private_key, payload)
        self.binding_proof = sig.hex()
        return self.binding_proof


@dataclass
class MRHRelationship:
    """MRH relationship entry."""
    lct_id: str
    rel_type: str  # bound, paired, witnessing
    subtype: str   # parent, child, birth_certificate, time, audit, etc.
    permanent: bool = False
    witness_count: int = 0
    timestamp: float = 0.0


@dataclass
class LCTDocument:
    """Integrated LCT document combining all components."""
    lct_id: str
    subject_did: str
    binding: LCTBinding
    birth_cert: Optional[BirthCertificate] = None
    mrh_bound: List[MRHRelationship] = field(default_factory=list)
    mrh_paired: List[MRHRelationship] = field(default_factory=list)
    mrh_witnessing: List[MRHRelationship] = field(default_factory=list)
    horizon_depth: int = 3
    policy_capabilities: List[str] = field(default_factory=list)
    policy_constraints: Dict[str, Any] = field(default_factory=dict)
    t3: T3Tensor = field(default_factory=T3Tensor)
    v3: V3Tensor = field(default_factory=V3Tensor)
    lineage: List[Dict] = field(default_factory=list)
    status: str = "active"  # active, superseded, revoked
    revocation_reason: Optional[str] = None
    revoked_at: Optional[float] = None
    vcs: List[str] = field(default_factory=list)  # VC IDs held

    def to_dict(self) -> Dict:
        return {
            "lct_id": self.lct_id,
            "subject": self.subject_did,
            "binding": {
                "entity_type": self.binding.entity_type,
                "public_key": self.binding.public_key_hex,
                "suite_id": self.binding.suite_id,
                "created_at": self.binding.created_at,
            },
            "mrh": {
                "bound": [{"lct_id": r.lct_id, "type": r.subtype} for r in self.mrh_bound],
                "paired": [{"lct_id": r.lct_id, "type": r.subtype, "permanent": r.permanent}
                           for r in self.mrh_paired],
                "witnessing": [{"lct_id": r.lct_id, "role": r.subtype,
                                "witness_count": r.witness_count} for r in self.mrh_witnessing],
                "horizon_depth": self.horizon_depth,
            },
            "policy": {
                "capabilities": self.policy_capabilities,
                "constraints": self.policy_constraints,
            },
            "t3_tensor": {
                "talent": self.t3.talent,
                "training": self.t3.training,
                "temperament": self.t3.temperament,
                "composite_score": self.t3.composite(),
            },
            "v3_tensor": {
                "valuation": self.v3.valuation,
                "veracity": self.v3.veracity,
                "validity": self.v3.validity,
                "composite_score": self.v3.composite(),
            },
            "status": self.status,
            "lineage": self.lineage,
        }

    def revoke(self, reason: str) -> None:
        self.status = "revoked"
        self.revocation_reason = reason
        self.revoked_at = time.time()
        self.policy_capabilities = []  # All capabilities disabled

    def supersede(self, new_lct_id: str) -> None:
        self.status = "superseded"
        self.lineage.append({
            "successor": new_lct_id,
            "reason": "rotation",
            "ts": time.time(),
        })


# ═══════════════════════════════════════════════════════════════
# Integrated Lifecycle Manager
# ═══════════════════════════════════════════════════════════════

class LCTLifecycleManager:
    """
    Orchestrates the full LCT lifecycle:
    society → genesis → operation → rotation → revocation.
    """

    def __init__(self, society: Society, key_manager: KeyManager,
                 authenticator: Authenticator):
        self.society = society
        self.km = key_manager
        self.auth = authenticator
        self.documents: Dict[str, LCTDocument] = {}
        self.vc_verifier = CredentialVerifier()
        self._lct_counter = 0

    def create_entity(self, entity_type: str, suite_id: str = SUITE_W4_BASE_1,
                      capabilities: Optional[List[str]] = None,
                      ) -> Tuple[LCTDocument, Optional[str]]:
        """
        Full entity genesis: key gen → binding → birth cert → LCT doc.
        """
        # 1. Generate signing key
        key = self.km.generate_key(suite_id, "signing")
        suite = get_suite(suite_id)

        # 2. Create binding
        self._lct_counter += 1
        now = time.time()
        binding = LCTBinding(
            entity_type=entity_type,
            public_key_hex=key.public_key_bytes.hex(),
            key_id=key.key_id,
            suite_id=suite_id,
            created_at=now,
        )
        binding.compute_proof(suite, key.private_key)

        # 3. Generate LCT ID
        lct_id = f"lct:web4:{entity_type}:{self._lct_counter}:{hashlib.sha256(key.public_key_bytes).hexdigest()[:8]}"
        subject_did = f"did:web4:key:{key.public_key_bytes.hex()[:16]}"

        # 4. Issue birth certificate via society
        cert, err = self.society.issue_birth_certificate(lct_id)
        if err:
            return None, err

        # 5. Create LCT document
        doc = LCTDocument(
            lct_id=lct_id,
            subject_did=subject_did,
            binding=binding,
            birth_cert=cert,
            t3=self.society.entities[lct_id].t3,
            v3=self.society.entities[lct_id].v3,
            policy_capabilities=capabilities or [
                "pairing:initiate", "metering:grant", "witness:attest",
            ],
        )

        # 6. Add MRH entries
        doc.mrh_paired.append(MRHRelationship(
            lct_id=cert.citizen_role_lct,
            rel_type="paired",
            subtype="birth_certificate",
            permanent=True,
            timestamp=now,
        ))

        # Add witness relationships from birth
        for wit in cert.witnesses:
            doc.mrh_witnessing.append(MRHRelationship(
                lct_id=wit,
                rel_type="witnessing",
                subtype="existence",
                witness_count=1,
                timestamp=now,
            ))

        self.documents[lct_id] = doc
        return doc, None

    def authenticate_entity(self, lct_id: str) -> Tuple[bool, str]:
        """Authenticate entity via challenge-response."""
        doc = self.documents.get(lct_id)
        if not doc or doc.status != "active":
            return False, "inactive_or_unknown"

        key = self.km.get_key(doc.binding.key_id)
        if not key or key.revoked:
            return False, "key_revoked"

        challenge = self.auth.create_challenge(doc.binding.suite_id)
        response = self.auth.respond_to_challenge(challenge, key)
        return self.auth.verify_response(response)

    def issue_vc(self, issuer_lct: str, subject_lct: str,
                 claims: Dict[str, Any], ttl: Optional[float] = None,
                 ) -> Optional[Any]:
        """Issue VC from one entity to another."""
        issuer_doc = self.documents.get(issuer_lct)
        subject_doc = self.documents.get(subject_lct)
        if not issuer_doc or not subject_doc:
            return None

        key = self.km.get_key(issuer_doc.binding.key_id)
        if not key:
            return None

        issuer = CredentialIssuer(key)
        vc = issuer.issue(subject_doc.subject_did, claims, ttl)
        subject_doc.vcs.append(vc.vc_id)
        return vc

    def execute_action(self, lct_id: str, action_type: str,
                       resource_value: Any) -> Tuple[bool, str, Optional[Dict]]:
        """Execute R6 action through society."""
        doc = self.documents.get(lct_id)
        if not doc or doc.status != "active":
            return False, "inactive_entity", None

        success, reason, result = self.society.execute_r6(lct_id, action_type, resource_value)

        if success:
            # Sync T3/V3 from society back to doc
            entity = self.society.entities[lct_id]
            doc.t3 = entity.t3
            doc.v3 = entity.v3

        return success, reason, result

    def rotate_key(self, lct_id: str) -> Tuple[Optional[LCTDocument], Optional[str]]:
        """
        Rotate entity's key per LCT spec §7.3.

        Creates new LCT with new binding, preserves MRH and T3/V3.
        Old LCT is superseded.
        """
        old_doc = self.documents.get(lct_id)
        if not old_doc or old_doc.status != "active":
            return None, "inactive_entity"

        old_key = self.km.get_key(old_doc.binding.key_id)
        if not old_key:
            return None, "key_not_found"

        # Rotate key in manager
        new_key = self.km.rotate_key(old_key.key_id)
        suite = get_suite(new_key.suite_id)

        # Create new binding
        new_binding = LCTBinding(
            entity_type=old_doc.binding.entity_type,
            public_key_hex=new_key.public_key_bytes.hex(),
            key_id=new_key.key_id,
            suite_id=new_key.suite_id,
            created_at=time.time(),
        )
        new_binding.compute_proof(suite, new_key.private_key)

        # New LCT ID
        self._lct_counter += 1
        new_lct_id = f"lct:web4:{old_doc.binding.entity_type}:{self._lct_counter}:{hashlib.sha256(new_key.public_key_bytes).hexdigest()[:8]}"

        # Create new document preserving MRH and trust
        new_doc = LCTDocument(
            lct_id=new_lct_id,
            subject_did=old_doc.subject_did,  # Same subject DID
            binding=new_binding,
            birth_cert=old_doc.birth_cert,
            mrh_bound=list(old_doc.mrh_bound),
            mrh_paired=list(old_doc.mrh_paired),
            mrh_witnessing=list(old_doc.mrh_witnessing),
            horizon_depth=old_doc.horizon_depth,
            policy_capabilities=list(old_doc.policy_capabilities),
            policy_constraints=dict(old_doc.policy_constraints),
            t3=old_doc.t3,
            v3=old_doc.v3,
            lineage=[{
                "parent": old_doc.lct_id,
                "reason": "rotation",
                "ts": time.time(),
            }],
        )

        # Supersede old document
        old_doc.supersede(new_lct_id)

        self.documents[new_lct_id] = new_doc
        return new_doc, None

    def revoke_entity(self, lct_id: str, reason: str) -> bool:
        """Revoke entity per LCT spec §7.4."""
        doc = self.documents.get(lct_id)
        if not doc:
            return False

        doc.revoke(reason)

        # Revoke key
        key = self.km.get_key(doc.binding.key_id)
        if key and not key.revoked:
            self.km.revoke_key(key.key_id)

        return True

    def add_witness(self, lct_id: str, witness_lct: str,
                    witness_role: str = "existence") -> bool:
        """Add witness attestation to entity's MRH."""
        doc = self.documents.get(lct_id)
        if not doc or doc.status != "active":
            return False

        # Check if already witnessing
        for w in doc.mrh_witnessing:
            if w.lct_id == witness_lct and w.subtype == witness_role:
                w.witness_count += 1
                return True

        doc.mrh_witnessing.append(MRHRelationship(
            lct_id=witness_lct,
            rel_type="witnessing",
            subtype=witness_role,
            witness_count=1,
            timestamp=time.time(),
        ))
        return True


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def create_test_infrastructure():
    """Create integrated test infrastructure."""
    law = LawDataset(
        law_id="web4://law/integration/1.0.0",
        version="v1.0.0",
        norms=[
            Norm("LAW-ATP-LIMIT", "r6.resource.atp", "<=", 100, "ATP cap"),
            Norm("LAW-RATE", "r6.resource.rate", "<=", 5000, "Rate limit"),
        ],
        procedures=[
            Procedure("PROC-WIT-3", requires_witnesses=3),
        ],
        interpretations=[
            Interpretation("INT-1", reason="Initial"),
        ],
    )
    society = Society(
        society_lct="lct:web4:society:integration",
        authority_lct="lct:web4:authority:integration",
        law=law,
        quorum_size=3,
    )
    for i in range(3):
        society.register_witness(f"lct:web4:witness:int:{i}")

    km = KeyManager(KeyStorageMethod.ENCRYPTED)
    auth = Authenticator(challenge_ttl=300.0)
    mgr = LCTLifecycleManager(society, km, auth)

    return mgr


def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(condition, label):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✓ {label}")
        else:
            failed += 1
            print(f"  ✗ {label}")

    # ─── T1: Society Formation ──────────────────────────────────
    print("\n═══ T1: Society Formation ═══")

    mgr = create_test_infrastructure()
    soc = mgr.society
    check(soc.society_lct == "lct:web4:society:integration", "Society created")
    check(len(soc.witnesses) == 3, "3 witnesses registered")
    check(soc.law_oracle.current_law.version == "v1.0.0", "Law v1.0.0 active")
    check(soc.triples.ask(soc.society_lct, "web4:hasAuthority", soc.authority_lct), "Authority triple")
    check(soc.triples.ask(soc.society_lct, "web4:hasLawOracle", soc.law_oracle.oracle_lct), "Law oracle triple")

    # ─── T2: Entity Genesis (Key + Binding + Birth Cert) ───────
    print("\n═══ T2: Entity Genesis ═══")

    alice, err_alice = mgr.create_entity("human")
    check(err_alice is None, "Alice created without error")
    check(alice.lct_id.startswith("lct:web4:human:"), "LCT ID starts with lct:web4:human:")
    check(alice.subject_did.startswith("did:web4:key:"), "Subject DID starts with did:web4:key:")
    check(alice.binding.entity_type == "human", "Binding type: human")
    check(alice.binding.suite_id == SUITE_W4_BASE_1, "Suite: W4-BASE-1")
    check(len(alice.binding.binding_proof) > 0, "Binding proof generated")
    check(alice.birth_cert is not None, "Birth certificate issued")
    check(alice.birth_cert.verify(), "Birth cert integrity verified")
    check(alice.status == "active", "Status: active")

    # MRH populated
    check(len(alice.mrh_paired) == 1, "1 citizen pairing in MRH")
    check(alice.mrh_paired[0].permanent, "Citizen pairing is permanent")
    check(len(alice.mrh_witnessing) == 3, "3 birth witnesses in MRH")

    # ─── T3: Multiple Entity Types ─────────────────────────────
    print("\n═══ T3: Multiple Entity Types ═══")

    bob, _ = mgr.create_entity("ai")
    check(bob.binding.entity_type == "ai", "Bob is AI entity")

    svc, _ = mgr.create_entity("service")
    check(svc.binding.entity_type == "service", "Service entity created")

    dev, _ = mgr.create_entity("device")
    check(dev.binding.entity_type == "device", "Device entity created")

    check(len(mgr.documents) == 4, "4 entities in lifecycle manager")
    check(len(mgr.km.keys) == 4, "4 keys in key manager")

    # ─── T4: Authentication ─────────────────────────────────────
    print("\n═══ T4: Authentication ═══")

    auth_ok, auth_reason = mgr.authenticate_entity(alice.lct_id)
    check(auth_ok, "Alice authenticates successfully")
    check(auth_reason == "authenticated", "Reason: authenticated")

    auth_bob, _ = mgr.authenticate_entity(bob.lct_id)
    check(auth_bob, "Bob authenticates successfully")

    # Non-existent entity
    auth_fake, reason_fake = mgr.authenticate_entity("lct:web4:fake:999")
    check(not auth_fake, "Fake entity fails auth")
    check(reason_fake == "inactive_or_unknown", "Reason: inactive_or_unknown")

    # ─── T5: VC Issuance and Verification ───────────────────────
    print("\n═══ T5: VC Issuance and Verification ═══")

    vc = mgr.issue_vc(
        alice.lct_id, bob.lct_id,
        claims={"access_level": "standard", "scope": ["read", "execute"]},
        ttl=3600.0,
    )
    check(vc is not None, "VC issued from Alice to Bob")
    check(vc.subject_did == bob.subject_did, "VC subject is Bob")
    check(vc.get_claim("access_level") == "standard", "Access level claim")
    check(bob.lct_id in [d.lct_id for d in mgr.documents.values() if vc.vc_id in d.vcs],
          "VC tracked in Bob's document")

    # Verify
    valid_vc, reason_vc = mgr.vc_verifier.verify(vc)
    check(valid_vc, "VC verifies")

    # ─── T6: R6 Action Execution ────────────────────────────────
    print("\n═══ T6: R6 Action Execution ═══")

    ok1, _, result1 = mgr.execute_action(alice.lct_id, "atp", 50)
    check(ok1, "Compliant action succeeds")
    check(result1["law_hash"] == soc.law_oracle.current_law.hash, "Law hash in result")

    ok2, reason2, _ = mgr.execute_action(alice.lct_id, "atp", 200)
    check(not ok2, "Non-compliant action rejected")
    check("LAW_VIOLATION" in reason2, "Violation reason")

    ok3, reason3, _ = mgr.execute_action("lct:web4:fake:999", "atp", 10)
    check(not ok3, "Non-existent entity rejected")

    # ─── T7: Trust Evolution ────────────────────────────────────
    print("\n═══ T7: Trust Evolution ═══")

    t3_before = alice.t3.composite()
    v3_before = alice.v3.validity

    # Execute multiple compliant actions
    for _ in range(5):
        mgr.execute_action(alice.lct_id, "atp", 10)

    v3_after = alice.v3.validity
    check(v3_after > v3_before, "V3 validity increases with compliant actions")
    check(abs(v3_after - v3_before - 0.05) < 0.001, "5 actions × 0.01 = +0.05 validity")

    # ─── T8: Role Assignment ────────────────────────────────────
    print("\n═══ T8: Role Assignment ═══")

    err_auth = soc.bind_role(alice.lct_id, RoleType.AUTHORITY,
                              scope="operations", delegated_by=soc.authority_lct)
    check(err_auth is None, "Alice gets authority role")

    err_aud = soc.bind_role(bob.lct_id, RoleType.AUDITOR)
    check(err_aud is None, "Bob gets auditor role")

    err_wit = soc.bind_role(svc.lct_id, RoleType.WITNESS)
    check(err_wit is None, "Service gets witness role")

    # Verify roles in society
    check(RoleType.AUTHORITY.value in soc.entities[alice.lct_id].roles, "Alice has authority")
    check(RoleType.AUDITOR.value in soc.entities[bob.lct_id].roles, "Bob has auditor")
    check(RoleType.WITNESS.value in soc.entities[svc.lct_id].roles, "Service has witness")

    # ─── T9: Auditing ──────────────────────────────────────────
    print("\n═══ T9: Auditing ═══")

    alice_t3_before = alice.t3.temperament
    req = AuditRequest(
        society_lct=soc.society_lct,
        targets=[alice.lct_id],
        scope=["operations"],
        basis=["hash:performance_review_q1"],
        proposed_t3={"training": 0.05},
        proposed_v3={"validity": 0.02},
    )
    ok_audit, _, transcript = soc.audit_entity(bob.lct_id, req)
    check(ok_audit, "Audit succeeds")
    check(transcript.evidence_verified, "Evidence verified")
    check(transcript.applied_t3["training"] == 0.05, "Training +0.05 applied")

    # Sync updated tensors to document
    alice.t3 = soc.entities[alice.lct_id].t3
    alice.v3 = soc.entities[alice.lct_id].v3

    # ─── T10: Witness Attestation ──────────────────────────────
    print("\n═══ T10: Witness Attestation ═══")

    wit_before = len(alice.mrh_witnessing)
    mgr.add_witness(alice.lct_id, "lct:web4:oracle:trust:1", "quality")
    check(len(alice.mrh_witnessing) == wit_before + 1, "New witness added to MRH")

    # Increment existing witness
    mgr.add_witness(alice.lct_id, "lct:web4:oracle:trust:1", "quality")
    quality_witnesses = [w for w in alice.mrh_witnessing if w.subtype == "quality"]
    check(quality_witnesses[0].witness_count == 2, "Existing witness count incremented")

    # Different witness role
    mgr.add_witness(alice.lct_id, "lct:web4:oracle:time:1", "time")
    check(any(w.subtype == "time" for w in alice.mrh_witnessing), "Time witness added")

    # ─── T11: Key Rotation ──────────────────────────────────────
    print("\n═══ T11: Key Rotation ═══")

    old_lct_id = alice.lct_id
    old_subject = alice.subject_did
    old_key_id = alice.binding.key_id

    new_alice, rot_err = mgr.rotate_key(alice.lct_id)
    check(rot_err is None, "Rotation succeeds")
    check(new_alice.lct_id != old_lct_id, "New LCT ID differs")
    check(new_alice.subject_did == old_subject, "Same subject DID preserved")
    check(new_alice.binding.key_id != old_key_id, "New key assigned")
    check(len(new_alice.lineage) == 1, "Lineage references parent")
    check(new_alice.lineage[0]["parent"] == old_lct_id, "Lineage parent is old LCT")
    check(new_alice.status == "active", "New doc is active")

    # Old document superseded
    old_doc = mgr.documents[old_lct_id]
    check(old_doc.status == "superseded", "Old doc superseded")

    # MRH preserved
    check(len(new_alice.mrh_paired) == len(old_doc.mrh_paired), "MRH paired preserved")
    check(len(new_alice.mrh_witnessing) >= 3, "MRH witnessing preserved (≥3 birth witnesses)")

    # T3/V3 preserved
    check(new_alice.t3.composite() == old_doc.t3.composite(), "T3 composite preserved")
    check(new_alice.v3.composite() == old_doc.v3.composite(), "V3 composite preserved")

    # ─── T12: Post-Rotation Authentication ──────────────────────
    print("\n═══ T12: Post-Rotation Authentication ═══")

    auth_new, _ = mgr.authenticate_entity(new_alice.lct_id)
    check(auth_new, "New LCT authenticates")

    auth_old, reason_old = mgr.authenticate_entity(old_lct_id)
    check(not auth_old, "Old LCT cannot authenticate (key revoked)")

    # ─── T13: Revocation ────────────────────────────────────────
    print("\n═══ T13: Revocation ═══")

    revoked = mgr.revoke_entity(dev.lct_id, "compromise")
    check(revoked, "Device revocation succeeds")
    check(mgr.documents[dev.lct_id].status == "revoked", "Status: revoked")
    check(mgr.documents[dev.lct_id].revocation_reason == "compromise", "Reason: compromise")
    check(len(mgr.documents[dev.lct_id].policy_capabilities) == 0, "Capabilities cleared")

    # Revoked entity cannot authenticate
    auth_rev, reason_rev = mgr.authenticate_entity(dev.lct_id)
    check(not auth_rev, "Revoked entity cannot authenticate")

    # Revoked entity cannot execute actions
    ok_rev, reason_rev_act, _ = mgr.execute_action(dev.lct_id, "atp", 10)
    check(not ok_rev, "Revoked entity cannot execute actions")

    # MRH preserved (read-only) per spec §7.4
    check(len(mgr.documents[dev.lct_id].mrh_paired) > 0, "MRH preserved after revocation")

    # ─── T14: LCT Document Serialization ───────────────────────
    print("\n═══ T14: LCT Document Serialization ═══")

    doc_dict = new_alice.to_dict()
    check("lct_id" in doc_dict, "Serialized: lct_id")
    check("subject" in doc_dict, "Serialized: subject")
    check("binding" in doc_dict, "Serialized: binding")
    check("mrh" in doc_dict, "Serialized: mrh")
    check("policy" in doc_dict, "Serialized: policy")
    check("t3_tensor" in doc_dict, "Serialized: t3_tensor")
    check("v3_tensor" in doc_dict, "Serialized: v3_tensor")
    check("status" in doc_dict, "Serialized: status")
    check("lineage" in doc_dict, "Serialized: lineage")

    # T3/V3 composites
    check(0 < doc_dict["t3_tensor"]["composite_score"] <= 1.0, "T3 composite in range")
    check(0 < doc_dict["v3_tensor"]["composite_score"] <= 1.0, "V3 composite in range")

    # MRH structure
    check(len(doc_dict["mrh"]["paired"]) > 0, "MRH paired non-empty")
    check(doc_dict["mrh"]["horizon_depth"] == 3, "Horizon depth = 3")

    # ─── T15: Ledger Audit Trail ────────────────────────────────
    print("\n═══ T15: Ledger Audit Trail ═══")

    check(soc.ledger.verify_chain(), "Full ledger chain valid")
    check(len(soc.ledger.entries) >= 4, f"≥4 ledger entries ({len(soc.ledger.entries)})")

    births = soc.ledger.events("sal.birth")
    check(len(births) == 4, "4 birth events (alice, bob, service, device)")

    roles = soc.ledger.events("sal.role")
    check(len(roles) >= 3, "≥3 role bind events")

    audits = soc.ledger.events("sal.audit")
    check(len(audits) >= 1, "≥1 audit event")

    # ─── T16: Full Lifecycle Summary ────────────────────────────
    print("\n═══ T16: Full Lifecycle Summary ═══")

    # Count entities by status
    active_count = sum(1 for d in mgr.documents.values() if d.status == "active")
    superseded_count = sum(1 for d in mgr.documents.values() if d.status == "superseded")
    revoked_count = sum(1 for d in mgr.documents.values() if d.status == "revoked")

    check(active_count == 3, f"3 active entities (bob, svc, new_alice)")
    check(superseded_count == 1, "1 superseded (old alice)")
    check(revoked_count == 1, "1 revoked (device)")

    # Total entities managed
    check(len(mgr.documents) == 5, "5 total documents managed")

    # Key manager state
    active_keys = mgr.km.get_active_keys()
    check(len(active_keys) == 3, "3 active keys (bob, svc, new_alice)")

    # ─── T17: Cross-Component Consistency ───────────────────────
    print("\n═══ T17: Cross-Component Consistency ═══")

    # Every active entity has a valid birth cert
    for lct_id, doc in mgr.documents.items():
        if doc.status == "active":
            check(doc.birth_cert is not None and doc.birth_cert.verify(),
                  f"{lct_id}: birth cert valid")

    # Every active entity has citizen role in society
    for lct_id, doc in mgr.documents.items():
        if doc.status == "active" and lct_id in soc.entities:
            entity = soc.entities[lct_id]
            check(RoleType.CITIZEN.value in entity.roles,
                  f"{lct_id}: has citizen role")

    # Every active entity has MRH citizen pairing
    for lct_id, doc in mgr.documents.items():
        if doc.status == "active":
            has_citizen_pair = any(
                r.subtype == "birth_certificate" and r.permanent
                for r in doc.mrh_paired
            )
            check(has_citizen_pair, f"{lct_id}: permanent citizen pairing in MRH")

    # ─── T18: FIPS Suite Entity ─────────────────────────────────
    print("\n═══ T18: FIPS Suite Entity ═══")

    fips_entity, err_fips = mgr.create_entity("service", suite_id=SUITE_W4_FIPS_1)
    check(err_fips is None, "FIPS entity created")
    check(fips_entity.binding.suite_id == SUITE_W4_FIPS_1, "Binding uses FIPS-1")

    auth_fips, _ = mgr.authenticate_entity(fips_entity.lct_id)
    check(auth_fips, "FIPS entity authenticates")

    # Issue VC across suites
    cross_vc = mgr.issue_vc(
        new_alice.lct_id, fips_entity.lct_id,
        claims={"cross_suite": True},
    )
    check(cross_vc is not None, "Cross-suite VC issued (BASE-1 → FIPS-1)")

    # ─── T19: Suite Negotiation Integration ─────────────────────
    print("\n═══ T19: Suite Negotiation Integration ═══")

    alice_neg = SuiteNegotiator([SUITE_W4_BASE_1])
    fips_neg = SuiteNegotiator([SUITE_W4_BASE_1, SUITE_W4_FIPS_1])

    agreed = alice_neg.negotiate(fips_neg.supported)
    check(agreed == SUITE_W4_BASE_1, "BASE-1 only entity negotiates BASE-1")

    agreed2 = fips_neg.negotiate(fips_neg.supported)
    check(agreed2 == SUITE_W4_FIPS_1, "Both FIPS → FIPS preferred")

    # ─── T20: VC Revocation Integration ─────────────────────────
    print("\n═══ T20: VC Revocation Integration ═══")

    vc_to_revoke = mgr.issue_vc(
        bob.lct_id, new_alice.lct_id,
        claims={"temp_access": True},
        ttl=3600.0,
    )
    valid_before, _ = mgr.vc_verifier.verify(vc_to_revoke)
    check(valid_before, "VC valid before revocation")

    mgr.vc_verifier.revoke(vc_to_revoke.vc_id)
    valid_after, reason_after = mgr.vc_verifier.verify(vc_to_revoke)
    check(not valid_after, "VC invalid after revocation")
    check(reason_after == "revoked", "Reason: revoked")

    # ─── T21: Genesis Closure ───────────────────────────────────
    print("\n═══ T21: Genesis Closure ═══")

    for lct_id, doc in mgr.documents.items():
        if doc.status == "active" and lct_id in soc.entities:
            valid_gc, issues = soc.validate_genesis_closure(lct_id)
            check(valid_gc, f"{lct_id}: passes genesis closure")

    # ═══════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'═' * 60}")
    print(f"LCT Lifecycle Integration: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed ✓")

    # Statistics
    print(f"\n  Entities managed: {len(mgr.documents)}")
    print(f"  Keys generated: {len(mgr.km.keys)}")
    print(f"  Ledger entries: {len(soc.ledger.entries)}")
    print(f"  MRH triples: {len(soc.triples.triples)}")
    print(f"  Active: {active_count} | Superseded: {superseded_count} | Revoked: {revoked_count}")
    print(f"{'═' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
