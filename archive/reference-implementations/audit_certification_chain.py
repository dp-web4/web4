#!/usr/bin/env python3
"""
Audit Certification Chain — Verifiable Compliance Certificates

Connects the compliance engine output to a signed, verifiable certificate
chain. Each certificate is:
  1. Assessed against EU AI Act articles
  2. Signed by the assessor's LCT identity
  3. Hash-chained to previous certificates
  4. Exportable in regulatory format

This is the "last mile" for the EU AI Act demo: a regulator can verify
the chain of certificates from entity creation through ongoing compliance.

Components:
  1. CertificateAuthority — issues and signs compliance certificates
  2. ComplianceCertificate — signed, verifiable compliance attestation
  3. CertificateChain — hash-linked chain of certificates over time
  4. CertificateVerifier — independent verification of certificate chains
  5. RegulatoryExporter — export to regulatory submission format
  6. ContinuousMonitoring — periodic re-certification with drift detection
  7. Multi-entity certification — certify entire teams/organizations

Session: Legion Autonomous 2026-02-26 (Session 10)
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════
# CERTIFICATE DATA MODEL
# ═══════════════════════════════════════════════════════════════

class CertificateType(Enum):
    INITIAL = "initial_certification"
    PERIODIC = "periodic_recertification"
    INCIDENT = "incident_recertification"
    CORRECTIVE = "corrective_action"
    REVOCATION = "revocation"


class CertificateStatus(Enum):
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class ComplianceLevel(Enum):
    FULL = "fully_compliant"
    SUBSTANTIAL = "substantially_compliant"      # ≥6/8 articles
    PARTIAL = "partially_compliant"              # ≥4/8 articles
    NON_COMPLIANT = "non_compliant"              # <4/8 articles
    UNDER_REVIEW = "under_review"


@dataclass
class EntitySnapshot:
    """Frozen state of an entity at certification time."""
    lct_id: str
    entity_type: str
    name: str
    t3_composite: float
    v3_composite: float
    hardware_binding_level: int
    status: str
    risk_level: str
    annex_iii_category: str


@dataclass
class ArticleAssessment:
    """Per-article compliance finding."""
    article: str
    title: str
    status: str  # compliant, partial, non_compliant
    evidence: list[str]
    gaps: list[str] = field(default_factory=list)


@dataclass
class ComplianceCertificate:
    """A signed, verifiable compliance certificate."""
    cert_id: str
    cert_type: CertificateType
    entity: EntitySnapshot
    assessments: list[ArticleAssessment]
    compliance_level: ComplianceLevel
    issued_at: str
    expires_at: str
    issuer_lct_id: str          # Assessor's LCT
    prev_cert_id: str = ""      # Previous certificate in chain
    prev_cert_hash: str = ""
    signature: str = ""         # HMAC signature
    cert_hash: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.cert_hash:
            self.cert_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        content = (
            f"{self.cert_id}:{self.cert_type.value}:{self.entity.lct_id}:"
            f"{self.compliance_level.value}:{self.issued_at}:"
            f"{self.issuer_lct_id}:{self.prev_cert_hash}"
        )
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def sign(self, key: str):
        """Sign certificate with HMAC (simplified — real impl uses Ed25519)."""
        msg = f"{self.cert_hash}:{key}"
        self.signature = hashlib.sha256(msg.encode()).hexdigest()[:32]

    def verify_signature(self, key: str) -> bool:
        expected = hashlib.sha256(f"{self.cert_hash}:{key}".encode()).hexdigest()[:32]
        return self.signature == expected

    @property
    def articles_compliant(self) -> int:
        return sum(1 for a in self.assessments if a.status == "compliant")

    @property
    def articles_total(self) -> int:
        return len(self.assessments)

    def to_regulatory_format(self) -> dict:
        return {
            "eu_ai_act_compliance_certificate": {
                "version": "1.0",
                "regulation": "EU 2024/1689",
                "certificate": {
                    "id": self.cert_id,
                    "type": self.cert_type.value,
                    "status": "valid",
                    "issued": self.issued_at,
                    "expires": self.expires_at,
                    "hash": self.cert_hash,
                    "signature": self.signature,
                },
                "entity": {
                    "lct_id": self.entity.lct_id,
                    "type": self.entity.entity_type,
                    "name": self.entity.name,
                    "risk_level": self.entity.risk_level,
                    "annex_iii_category": self.entity.annex_iii_category,
                    "hardware_binding": self.entity.hardware_binding_level,
                },
                "assessment": {
                    "level": self.compliance_level.value,
                    "articles_compliant": self.articles_compliant,
                    "articles_total": self.articles_total,
                    "details": [{
                        "article": a.article,
                        "title": a.title,
                        "status": a.status,
                        "evidence": a.evidence,
                        "gaps": a.gaps,
                    } for a in self.assessments]
                },
                "issuer": {
                    "lct_id": self.issuer_lct_id,
                },
                "chain": {
                    "prev_cert_id": self.prev_cert_id,
                    "prev_cert_hash": self.prev_cert_hash,
                }
            }
        }


# ═══════════════════════════════════════════════════════════════
# CERTIFICATE AUTHORITY
# ═══════════════════════════════════════════════════════════════

class CertificateAuthority:
    """Issues and manages compliance certificates."""

    def __init__(self, authority_lct_id: str, signing_key: str,
                 validity_days: int = 90):
        self.authority_lct_id = authority_lct_id
        self.signing_key = signing_key
        self.validity_days = validity_days
        self.cert_counter = 0
        self.issued: list[ComplianceCertificate] = []

    def issue(self, entity: EntitySnapshot,
              assessments: list[ArticleAssessment],
              cert_type: CertificateType = CertificateType.INITIAL,
              prev_cert: Optional[ComplianceCertificate] = None,
              metadata: dict = None) -> ComplianceCertificate:
        """Issue a new compliance certificate."""
        # Determine compliance level
        compliant = sum(1 for a in assessments if a.status == "compliant")
        total = len(assessments)

        if compliant == total:
            level = ComplianceLevel.FULL
        elif compliant >= 6:
            level = ComplianceLevel.SUBSTANTIAL
        elif compliant >= 4:
            level = ComplianceLevel.PARTIAL
        else:
            level = ComplianceLevel.NON_COMPLIANT

        now = datetime.utcnow()
        cert = ComplianceCertificate(
            cert_id=f"CERT-{self.cert_counter:06d}",
            cert_type=cert_type,
            entity=entity,
            assessments=assessments,
            compliance_level=level,
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(days=self.validity_days)).isoformat(),
            issuer_lct_id=self.authority_lct_id,
            prev_cert_id=prev_cert.cert_id if prev_cert else "",
            prev_cert_hash=prev_cert.cert_hash if prev_cert else "",
            metadata=metadata or {}
        )
        cert.sign(self.signing_key)
        self.cert_counter += 1

        # Supersede previous certificate
        if prev_cert:
            for issued in self.issued:
                if issued.cert_id == prev_cert.cert_id:
                    issued.metadata["status"] = CertificateStatus.SUPERSEDED.value

        self.issued.append(cert)
        return cert

    def revoke(self, cert_id: str, reason: str) -> Optional[ComplianceCertificate]:
        """Revoke a certificate and issue revocation notice."""
        target = None
        for cert in self.issued:
            if cert.cert_id == cert_id:
                target = cert
                break

        if not target:
            return None

        revocation = self.issue(
            target.entity,
            target.assessments,
            cert_type=CertificateType.REVOCATION,
            prev_cert=target,
            metadata={"reason": reason, "revoked_cert": cert_id}
        )
        target.metadata["status"] = CertificateStatus.REVOKED.value
        return revocation


# ═══════════════════════════════════════════════════════════════
# CERTIFICATE CHAIN & VERIFICATION
# ═══════════════════════════════════════════════════════════════

class CertificateChain:
    """Hash-linked chain of certificates for an entity."""

    def __init__(self, entity_lct_id: str):
        self.entity_lct_id = entity_lct_id
        self.certificates: list[ComplianceCertificate] = []

    def add(self, cert: ComplianceCertificate):
        if cert.entity.lct_id != self.entity_lct_id:
            raise ValueError(f"Certificate for {cert.entity.lct_id} "
                             f"doesn't match chain entity {self.entity_lct_id}")
        self.certificates.append(cert)

    @property
    def current(self) -> Optional[ComplianceCertificate]:
        if not self.certificates:
            return None
        return self.certificates[-1]

    @property
    def length(self) -> int:
        return len(self.certificates)


class CertificateVerifier:
    """Independent verification of certificate chains."""

    def __init__(self, signing_key: str):
        self.signing_key = signing_key

    def verify_certificate(self, cert: ComplianceCertificate) -> dict:
        """Verify a single certificate."""
        results = {
            "cert_id": cert.cert_id,
            "checks": {},
            "valid": True
        }

        # Check hash integrity
        recomputed = cert._compute_hash()
        hash_valid = recomputed == cert.cert_hash
        results["checks"]["hash_integrity"] = hash_valid
        if not hash_valid:
            results["valid"] = False

        # Check signature
        sig_valid = cert.verify_signature(self.signing_key)
        results["checks"]["signature"] = sig_valid
        if not sig_valid:
            results["valid"] = False

        # Check expiry
        try:
            expires = datetime.fromisoformat(cert.expires_at)
            not_expired = expires > datetime.utcnow()
        except ValueError:
            not_expired = False
        results["checks"]["not_expired"] = not_expired

        # Check compliance level consistency
        compliant = cert.articles_compliant
        total = cert.articles_total
        level_consistent = True
        if compliant == total and cert.compliance_level != ComplianceLevel.FULL:
            level_consistent = False
        elif compliant < 4 and cert.compliance_level != ComplianceLevel.NON_COMPLIANT:
            level_consistent = False
        results["checks"]["level_consistent"] = level_consistent
        if not level_consistent:
            results["valid"] = False

        return results

    def verify_chain(self, chain: CertificateChain) -> dict:
        """Verify an entire certificate chain."""
        results = {
            "entity": chain.entity_lct_id,
            "length": chain.length,
            "certificates": [],
            "chain_valid": True,
            "link_valid": True
        }

        for i, cert in enumerate(chain.certificates):
            cert_result = self.verify_certificate(cert)
            results["certificates"].append(cert_result)

            if not cert_result["valid"]:
                results["chain_valid"] = False

            # Verify chain links
            if i > 0:
                prev = chain.certificates[i - 1]
                if cert.prev_cert_hash != prev.cert_hash:
                    results["link_valid"] = False
                    results["chain_valid"] = False

        return results


# ═══════════════════════════════════════════════════════════════
# CONTINUOUS MONITORING
# ═══════════════════════════════════════════════════════════════

class ContinuousMonitor:
    """Monitors entity trust and triggers recertification on drift."""

    def __init__(self, ca: CertificateAuthority, drift_threshold: float = 0.1):
        self.ca = ca
        self.drift_threshold = drift_threshold
        self.snapshots: list[dict] = []
        self.alerts: list[dict] = []

    def record_snapshot(self, entity: EntitySnapshot) -> dict:
        snap = {
            "entity": entity.lct_id,
            "t3": entity.t3_composite,
            "v3": entity.v3_composite,
            "status": entity.status,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.snapshots.append(snap)
        return snap

    def check_drift(self, entity: EntitySnapshot,
                    current_cert: ComplianceCertificate) -> dict:
        """Check if entity has drifted from certified state."""
        cert_t3 = current_cert.entity.t3_composite
        current_t3 = entity.t3_composite
        drift = abs(current_t3 - cert_t3)

        needs_recert = (
            drift > self.drift_threshold or
            entity.status != current_cert.entity.status or
            entity.hardware_binding_level != current_cert.entity.hardware_binding_level
        )

        result = {
            "entity": entity.lct_id,
            "cert_t3": cert_t3,
            "current_t3": current_t3,
            "drift": round(drift, 4),
            "status_changed": entity.status != current_cert.entity.status,
            "hw_changed": entity.hardware_binding_level != current_cert.entity.hardware_binding_level,
            "needs_recertification": needs_recert,
            "reason": []
        }

        if drift > self.drift_threshold:
            result["reason"].append(f"Trust drift {drift:.3f} > threshold {self.drift_threshold}")
        if entity.status != current_cert.entity.status:
            result["reason"].append(f"Status changed: {current_cert.entity.status} → {entity.status}")
        if entity.hardware_binding_level != current_cert.entity.hardware_binding_level:
            result["reason"].append("Hardware binding changed")

        if needs_recert:
            self.alerts.append(result)

        return result


# ═══════════════════════════════════════════════════════════════
# REGULATORY EXPORTER
# ═══════════════════════════════════════════════════════════════

class RegulatoryExporter:
    """Export certificate chains in regulatory submission format."""

    @staticmethod
    def export_chain(chain: CertificateChain,
                     verification: dict) -> dict:
        """Export full chain for regulatory submission."""
        return {
            "eu_ai_act_compliance_submission": {
                "version": "1.0",
                "regulation": "EU 2024/1689",
                "submission_date": datetime.utcnow().isoformat(),
                "entity": {
                    "lct_id": chain.entity_lct_id,
                },
                "certification_history": {
                    "total_certificates": chain.length,
                    "current_certificate": chain.current.cert_id if chain.current else None,
                    "current_level": chain.current.compliance_level.value if chain.current else None,
                    "chain_verified": verification.get("chain_valid", False),
                },
                "certificates": [
                    cert.to_regulatory_format()
                    for cert in chain.certificates
                ],
                "verification": verification
            }
        }

    @staticmethod
    def export_organization(chains: list[CertificateChain],
                            org_name: str) -> dict:
        """Export all entity certificates for an organization."""
        entities = []
        for chain in chains:
            if chain.current:
                entities.append({
                    "lct_id": chain.entity_lct_id,
                    "name": chain.current.entity.name,
                    "type": chain.current.entity.entity_type,
                    "compliance_level": chain.current.compliance_level.value,
                    "cert_count": chain.length,
                    "current_cert": chain.current.cert_id
                })

        return {
            "eu_ai_act_organization_submission": {
                "organization": org_name,
                "submission_date": datetime.utcnow().isoformat(),
                "total_entities": len(entities),
                "entities": entities,
                "compliance_summary": {
                    "full": sum(1 for e in entities if e["compliance_level"] == "fully_compliant"),
                    "substantial": sum(1 for e in entities if e["compliance_level"] == "substantially_compliant"),
                    "partial": sum(1 for e in entities if e["compliance_level"] == "partially_compliant"),
                    "non_compliant": sum(1 for e in entities if e["compliance_level"] == "non_compliant"),
                }
            }
        }


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

    # ─── Setup ────────────────────────────────────────────────────

    signing_key = "web4-compliance-authority-key-2026"
    ca = CertificateAuthority(
        "lct:web4:human:compliance-authority",
        signing_key,
        validity_days=90
    )
    verifier = CertificateVerifier(signing_key)

    # Create entity snapshot
    def make_entity(lct_id: str, name: str, entity_type: str = "ai",
                    t3: float = 0.7, v3: float = 0.75, hw: int = 5,
                    risk: str = "high", annex: str = "employment") -> EntitySnapshot:
        return EntitySnapshot(
            lct_id=lct_id, entity_type=entity_type, name=name,
            t3_composite=t3, v3_composite=v3,
            hardware_binding_level=hw, status="active",
            risk_level=risk, annex_iii_category=annex
        )

    # Create standard assessments
    def make_assessments(compliant_count: int = 8) -> list[ArticleAssessment]:
        articles = [
            ("6", "Classification"), ("9", "Risk Management"),
            ("10", "Data Governance"), ("11", "Technical Documentation"),
            ("12", "Record-Keeping"), ("13", "Transparency"),
            ("14", "Human Oversight"), ("15", "Cybersecurity"),
        ]
        assessments = []
        for i, (art, title) in enumerate(articles):
            status = "compliant" if i < compliant_count else "non_compliant"
            assessments.append(ArticleAssessment(
                article=art, title=title, status=status,
                evidence=[f"Evidence for Art. {art}"],
                gaps=[] if status == "compliant" else [f"Gap in Art. {art}"]
            ))
        return assessments

    # ─── Section 1: Certificate Issuance ──────────────────────────

    print("Section 1: Certificate Issuance")

    entity = make_entity("lct:web4:ai:hiring-bot", "HireBot v3.0")
    assessments = make_assessments(8)  # All compliant

    cert = ca.issue(entity, assessments)
    check(cert.cert_id == "CERT-000000", "First cert ID is CERT-000000")
    check(cert.compliance_level == ComplianceLevel.FULL, "All 8 compliant → FULL")
    check(cert.articles_compliant == 8, "8 articles compliant")
    check(cert.articles_total == 8, "8 articles total")
    check(len(cert.cert_hash) == 32, "Certificate has 32-char hash")
    check(len(cert.signature) == 32, "Certificate is signed (32-char sig)")
    check(cert.cert_type == CertificateType.INITIAL, "Initial certification")
    check(cert.issuer_lct_id == ca.authority_lct_id, "Correct issuer")

    # Compliance levels
    substantial = ca.issue(make_entity("lct:test:1", "Test1"),
                           make_assessments(7))
    check(substantial.compliance_level == ComplianceLevel.SUBSTANTIAL,
          "7/8 compliant → SUBSTANTIAL")

    partial = ca.issue(make_entity("lct:test:2", "Test2"),
                       make_assessments(5))
    check(partial.compliance_level == ComplianceLevel.PARTIAL,
          "5/8 compliant → PARTIAL")

    non_compliant = ca.issue(make_entity("lct:test:3", "Test3"),
                             make_assessments(2))
    check(non_compliant.compliance_level == ComplianceLevel.NON_COMPLIANT,
          "2/8 compliant → NON_COMPLIANT")

    # ─── Section 2: Signature Verification ────────────────────────

    print("Section 2: Signature Verification")

    check(cert.verify_signature(signing_key), "Signature verifies with correct key")
    check(not cert.verify_signature("wrong_key"), "Signature fails with wrong key")

    # Tamper with cert hash → signature fails
    original_hash = cert.cert_hash
    cert.cert_hash = "tampered_hash"
    check(not cert.verify_signature(signing_key), "Tampered hash → sig fails")
    cert.cert_hash = original_hash  # Restore

    # ─── Section 3: Certificate Chain ─────────────────────────────

    print("Section 3: Certificate Chain")

    chain = CertificateChain("lct:web4:ai:hiring-bot")

    # Initial certification
    chain.add(cert)
    check(chain.length == 1, "Chain has 1 certificate")
    check(chain.current.cert_id == cert.cert_id, "Current cert is latest")

    # Periodic recertification
    entity_v2 = make_entity("lct:web4:ai:hiring-bot", "HireBot v3.0", t3=0.75)
    recert = ca.issue(entity_v2, make_assessments(8),
                      cert_type=CertificateType.PERIODIC,
                      prev_cert=cert)
    chain.add(recert)
    check(chain.length == 2, "Chain has 2 certificates")
    check(recert.prev_cert_id == cert.cert_id, "Recert links to initial")
    check(recert.prev_cert_hash == cert.cert_hash, "Recert has prev hash")
    check(recert.cert_type == CertificateType.PERIODIC, "Periodic type")

    # Third certification
    recert2 = ca.issue(entity_v2, make_assessments(8),
                       cert_type=CertificateType.PERIODIC,
                       prev_cert=recert)
    chain.add(recert2)
    check(chain.length == 3, "Chain has 3 certificates")
    check(chain.current.cert_id == recert2.cert_id, "Current is latest")

    # Wrong entity → rejected
    wrong_entity = make_entity("lct:web4:ai:other", "Other Bot")
    wrong_cert = ca.issue(wrong_entity, make_assessments(8))
    try:
        chain.add(wrong_cert)
        check(False, "Wrong entity should raise ValueError")
    except ValueError:
        check(True, "Wrong entity raises ValueError")

    # ─── Section 4: Chain Verification ────────────────────────────

    print("Section 4: Chain Verification")

    result = verifier.verify_chain(chain)
    check(result["chain_valid"], "Certificate chain is valid")
    check(result["link_valid"], "All chain links valid")
    check(result["length"] == 3, "Verified 3 certificates")

    # Verify individual certificates
    for cert_result in result["certificates"]:
        check(cert_result["valid"], f"Cert {cert_result['cert_id']} valid")

    # Check specific verification items
    first_result = result["certificates"][0]
    check(first_result["checks"]["hash_integrity"], "Hash integrity verified")
    check(first_result["checks"]["signature"], "Signature verified")
    check(first_result["checks"]["not_expired"], "Not expired")
    check(first_result["checks"]["level_consistent"], "Level consistent")

    # Tamper with chain link → verification fails
    broken_chain = CertificateChain("lct:web4:ai:hiring-bot")
    broken_chain.add(cert)
    # Create a cert that doesn't link to the previous properly
    bad_link = ca.issue(entity_v2, make_assessments(8),
                        cert_type=CertificateType.PERIODIC)  # No prev_cert!
    broken_chain.add(bad_link)
    broken_result = verifier.verify_chain(broken_chain)
    check(not broken_result["link_valid"], "Broken link detected")

    # ─── Section 5: Regulatory Export ─────────────────────────────

    print("Section 5: Regulatory Export")

    export = RegulatoryExporter.export_chain(chain, result)
    submission = export["eu_ai_act_compliance_submission"]

    check(submission["regulation"] == "EU 2024/1689", "Correct regulation")
    check(submission["certification_history"]["total_certificates"] == 3,
          "3 certificates in history")
    check(submission["certification_history"]["chain_verified"],
          "Chain verified in export")
    check(len(submission["certificates"]) == 3, "3 certificates exported")

    # Each exported cert has regulatory format
    first_export = submission["certificates"][0]["eu_ai_act_compliance_certificate"]
    check(first_export["version"] == "1.0", "Export version 1.0")
    check(first_export["entity"]["lct_id"] == "lct:web4:ai:hiring-bot",
          "Entity LCT in export")
    check(first_export["assessment"]["articles_compliant"] == 8,
          "Articles compliant in export")
    check(first_export["entity"]["hardware_binding"] == 5,
          "Hardware binding in export")

    # Organization export
    chain2 = CertificateChain("lct:web4:service:data-pipeline")
    data_entity = make_entity("lct:web4:service:data-pipeline",
                              "Data Pipeline", "service",
                              t3=0.65, hw=3, annex="not_high_risk", risk="minimal")
    data_cert = ca.issue(data_entity, make_assessments(6))
    chain2.add(data_cert)

    org_export = RegulatoryExporter.export_organization(
        [chain, chain2], "ACME Corporation"
    )
    org = org_export["eu_ai_act_organization_submission"]
    check(org["organization"] == "ACME Corporation", "Org name in export")
    check(org["total_entities"] == 2, "2 entities in org export")
    check(org["compliance_summary"]["full"] == 1, "1 fully compliant")
    check(org["compliance_summary"]["substantial"] == 1, "1 substantially compliant")

    # ─── Section 6: Continuous Monitoring ─────────────────────────

    print("Section 6: Continuous Monitoring")

    monitor = ContinuousMonitor(ca, drift_threshold=0.1)

    # No drift
    entity_stable = make_entity("lct:web4:ai:hiring-bot", "HireBot v3.0", t3=0.72)
    drift_result = monitor.check_drift(entity_stable, cert)
    check(not drift_result["needs_recertification"],
          "No recert needed for small drift")
    check(drift_result["drift"] < 0.1, f"Drift {drift_result['drift']} < 0.1")

    # Trust drift
    entity_drifted = make_entity("lct:web4:ai:hiring-bot", "HireBot v3.0", t3=0.55)
    drift_result2 = monitor.check_drift(entity_drifted, cert)
    check(drift_result2["needs_recertification"],
          f"Recert needed for drift {drift_result2['drift']}")
    check(len(drift_result2["reason"]) > 0, "Drift reason provided")

    # Status change
    entity_dormant = make_entity("lct:web4:ai:hiring-bot", "HireBot v3.0", t3=0.7)
    entity_dormant = EntitySnapshot(
        lct_id="lct:web4:ai:hiring-bot", entity_type="ai", name="HireBot v3.0",
        t3_composite=0.7, v3_composite=0.75, hardware_binding_level=5,
        status="dormant", risk_level="high", annex_iii_category="employment"
    )
    drift_result3 = monitor.check_drift(entity_dormant, cert)
    check(drift_result3["needs_recertification"], "Status change triggers recert")
    check(drift_result3["status_changed"], "Status change detected")

    # Alerts recorded
    check(len(monitor.alerts) >= 2, f"At least 2 alerts ({len(monitor.alerts)})")

    # Snapshot recording
    snap = monitor.record_snapshot(entity_stable)
    check(snap["entity"] == "lct:web4:ai:hiring-bot", "Snapshot entity correct")
    check(snap["t3"] == 0.72, "Snapshot T3 correct")

    # ─── Section 7: Certificate Revocation ────────────────────────

    print("Section 7: Certificate Revocation")

    revocation = ca.revoke(cert.cert_id, "Compliance breach detected")
    check(revocation is not None, "Revocation certificate issued")
    check(revocation.cert_type == CertificateType.REVOCATION, "Type is REVOCATION")
    check(revocation.metadata.get("reason") == "Compliance breach detected",
          "Revocation reason recorded")
    check(revocation.prev_cert_id == cert.cert_id, "Links to revoked cert")

    # Original cert marked as revoked
    check(cert.metadata.get("status") == CertificateStatus.REVOKED.value,
          "Original cert marked revoked")

    # Revoke nonexistent cert
    bad_revoke = ca.revoke("CERT-999999", "test")
    check(bad_revoke is None, "Revoke nonexistent returns None")

    # ─── Section 8: Multi-Entity Scenario ─────────────────────────

    print("Section 8: Multi-Entity Scenario")

    # Create a team of entities
    team_ca = CertificateAuthority(
        "lct:web4:human:team-assessor", signing_key, validity_days=180
    )
    team_verifier = CertificateVerifier(signing_key)
    chains = []

    entities_config = [
        ("lct:web4:ai:agent-1", "Agent Alpha", "ai", 0.8, 5, 8),
        ("lct:web4:ai:agent-2", "Agent Beta", "ai", 0.72, 5, 7),
        ("lct:web4:service:pipeline", "Pipeline", "service", 0.65, 3, 5),
        ("lct:web4:device:sensor", "Sensor Array", "device", 0.58, 4, 5),
    ]

    for lct_id, name, etype, t3, hw, compliant_n in entities_config:
        entity = make_entity(lct_id, name, etype, t3=t3, hw=hw)
        assessments = make_assessments(compliant_n)
        cert = team_ca.issue(entity, assessments)
        ch = CertificateChain(lct_id)
        ch.add(cert)
        chains.append(ch)

    check(len(chains) == 4, "4 entity chains created")

    # Verify all chains
    all_valid = True
    for ch in chains:
        v = team_verifier.verify_chain(ch)
        if not v["chain_valid"]:
            all_valid = False
    check(all_valid, "All 4 entity chains valid")

    # Organization export
    org_export = RegulatoryExporter.export_organization(chains, "ACME Corp")
    org_data = org_export["eu_ai_act_organization_submission"]
    check(org_data["total_entities"] == 4, "4 entities in org export")
    check(org_data["compliance_summary"]["full"] == 1, "1 fully compliant entity")
    check(org_data["compliance_summary"]["substantial"] == 1, "1 substantially compliant")
    check(org_data["compliance_summary"]["partial"] == 2, "2 partially compliant")

    # ─── Section 9: Edge Cases ────────────────────────────────────

    print("Section 9: Edge Cases")

    # Empty chain
    empty = CertificateChain("lct:empty")
    check(empty.current is None, "Empty chain has no current cert")
    check(empty.length == 0, "Empty chain length 0")

    empty_verify = verifier.verify_chain(empty)
    check(empty_verify["chain_valid"], "Empty chain verifies as valid")

    # Zero compliant articles
    zero_entity = make_entity("lct:test:zero", "Zero Compliance")
    zero_cert = ca.issue(zero_entity, make_assessments(0))
    check(zero_cert.compliance_level == ComplianceLevel.NON_COMPLIANT,
          "0/8 → non_compliant")

    # Exactly 4 compliant (threshold)
    threshold_cert = ca.issue(make_entity("lct:test:4", "Threshold"),
                              make_assessments(4))
    check(threshold_cert.compliance_level == ComplianceLevel.PARTIAL,
          "4/8 → partial (threshold)")

    # Exactly 6 compliant
    six_cert = ca.issue(make_entity("lct:test:6", "Six"),
                        make_assessments(6))
    check(six_cert.compliance_level == ComplianceLevel.SUBSTANTIAL,
          "6/8 → substantial")

    # Certificate with metadata
    meta_cert = ca.issue(
        make_entity("lct:test:meta", "Meta Entity"),
        make_assessments(8),
        metadata={"audit_reference": "AUD-2026-001", "notes": "Annual review"}
    )
    check(meta_cert.metadata["audit_reference"] == "AUD-2026-001",
          "Metadata preserved in certificate")

    # Regulatory format includes all required fields
    reg = meta_cert.to_regulatory_format()["eu_ai_act_compliance_certificate"]
    required_sections = ["version", "regulation", "certificate", "entity",
                         "assessment", "issuer", "chain"]
    for section in required_sections:
        check(section in reg, f"Regulatory format has '{section}' section")

    # ─── Summary ──────────────────────────────────────────────────

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Audit Certification Chain: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")

    return passed, failed


if __name__ == "__main__":
    run_checks()
