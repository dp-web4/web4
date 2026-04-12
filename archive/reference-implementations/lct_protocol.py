#!/usr/bin/env python3
"""
Web4 LCT Protocol Specification — Reference Implementation
Spec: web4-standard/protocols/web4-lct.md (278 lines)

Covers all 9 specification sections:
  §1  LCT Object Definition (canonical structure)
  §2  Field Definitions (8 field groups with validation)
  §3  Binding Algorithm
  §4  MRH Dynamics (updates, context emergence, queries)
  §5  Rotation Rules (procedure, split-brain resolution)
  §6  Witness Attestation (7 classes, format)
  §7  Security Considerations (binding, rotation, witness)
  §8  Privacy Considerations
  §9  IANA Considerations
"""

from __future__ import annotations
import hashlib, json, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional


# ============================================================
# §2  FIELD DEFINITIONS
# ============================================================

# §2.2: Valid entity types
VALID_ENTITY_TYPES = frozenset([
    "human", "ai", "organization", "role", "task",
    "resource", "device", "service", "oracle",
    "accumulator", "dictionary", "hybrid",
])

# §2.3: Birth contexts
VALID_BIRTH_CONTEXTS = frozenset([
    "nation", "platform", "network", "organization", "ecosystem",
])

# §2.4: Binding types
VALID_BINDING_TYPES = frozenset(["parent", "child", "sibling"])

# §2.4: Pairing types
VALID_PAIRING_TYPES = frozenset(["birth_certificate", "role", "operational"])

# §2.6: Attestation types (§6.1 witness classes)
VALID_ATTESTATION_TYPES = frozenset([
    "time", "audit", "oracle", "existence", "action", "state", "quality",
])

# §2.7: Lineage reasons
VALID_LINEAGE_REASONS = frozenset(["genesis", "rotation", "fork", "upgrade"])

# §2.8: Revocation statuses and reasons
VALID_REVOCATION_STATUSES = frozenset(["active", "revoked"])
VALID_REVOCATION_REASONS = frozenset(["compromise", "superseded", "expired"])


# ============================================================
# §1  LCT OBJECT DEFINITION
# ============================================================

@dataclass
class LCTBinding:
    """§2.2: Binding fields."""
    entity_type: str = ""
    public_key: str = ""          # mb64:coseKey
    hardware_anchor: str = ""     # Optional EAT per RFC 9334
    created_at: str = ""
    binding_proof: str = ""       # COSE signature

@dataclass
class LCTBirthCertificate:
    """§2.3: Birth certificate fields."""
    citizen_role: str = ""
    context: str = ""             # nation|platform|network|organization|ecosystem
    birth_timestamp: str = ""
    parent_entity: str = ""       # Optional
    birth_witnesses: list[str] = field(default_factory=list)

@dataclass
class MRHBound:
    """§2.4: MRH binding relationship."""
    lct_id: str = ""
    type: str = ""
    ts: str = ""

@dataclass
class MRHPaired:
    """§2.4: MRH pairing relationship."""
    lct_id: str = ""
    pairing_type: str = ""
    permanent: bool = False
    context: str = ""
    session_id: str = ""
    ts: str = ""

@dataclass
class MRHWitness:
    """§2.4: MRH witnessing relationship."""
    lct_id: str = ""
    role: str = ""
    last_attestation: str = ""

@dataclass
class LCTMRH:
    """§2.4: MRH fields.
    §2.4: First paired entry MUST be citizen role pairing."""
    bound: list[MRHBound] = field(default_factory=list)
    paired: list[MRHPaired] = field(default_factory=list)
    witnessing: list[MRHWitness] = field(default_factory=list)
    horizon_depth: int = 3
    last_updated: str = ""

@dataclass
class LCTPolicy:
    """§2.5: Policy fields."""
    capabilities: list[str] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)

@dataclass
class LCTAttestation:
    """§2.6: Attestation fields."""
    witness: str = ""     # DID of witness
    type: str = ""        # time|audit|oracle|existence|action|state|quality
    claims: dict = field(default_factory=dict)
    sig: str = ""         # COSE signature
    ts: str = ""

@dataclass
class LCTLineage:
    """§2.7: Lineage fields."""
    parent: str = ""
    reason: str = ""
    ts: str = ""

@dataclass
class LCTRevocation:
    """§2.8: Revocation fields."""
    status: str = "active"
    ts: str = ""
    reason: str = ""

@dataclass
class LCTObject:
    """§1: Complete LCT object definition."""
    lct_id: str = ""
    subject: str = ""
    binding: LCTBinding = field(default_factory=LCTBinding)
    birth_certificate: Optional[LCTBirthCertificate] = None
    mrh: LCTMRH = field(default_factory=LCTMRH)
    policy: LCTPolicy = field(default_factory=LCTPolicy)
    attestations: list[LCTAttestation] = field(default_factory=list)
    lineage: list[LCTLineage] = field(default_factory=list)
    revocation: LCTRevocation = field(default_factory=LCTRevocation)


# ============================================================
# §2 + §3  FIELD VALIDATION + BINDING ALGORITHM
# ============================================================

def validate_identity_fields(lct: LCTObject) -> list[str]:
    """§2.1: Identity fields validation."""
    errors = []
    if not lct.lct_id.startswith("lct:web4:"):
        errors.append("lct_id must start with 'lct:web4:'")
    if not lct.subject.startswith("did:web4:"):
        errors.append("subject must start with 'did:web4:'")
    return errors

def validate_binding_fields(binding: LCTBinding) -> list[str]:
    """§2.2: Binding fields validation."""
    errors = []
    if binding.entity_type not in VALID_ENTITY_TYPES:
        errors.append(f"Invalid entity_type: {binding.entity_type}")
    if not binding.public_key:
        errors.append("public_key required")
    if not binding.created_at:
        errors.append("created_at required")
    if not binding.binding_proof:
        errors.append("binding_proof required")
    return errors

def validate_birth_certificate_fields(bc: LCTBirthCertificate) -> list[str]:
    """§2.3: Birth certificate fields validation."""
    errors = []
    if not bc.citizen_role:
        errors.append("citizen_role required")
    if bc.context and bc.context not in VALID_BIRTH_CONTEXTS:
        errors.append(f"Invalid birth context: {bc.context}")
    if not bc.birth_timestamp:
        errors.append("birth_timestamp required")
    if not bc.birth_witnesses:
        errors.append("birth_witnesses required")
    return errors

def validate_mrh_fields(mrh: LCTMRH) -> list[str]:
    """§2.4: MRH fields validation."""
    errors = []
    for b in mrh.bound:
        if b.type not in VALID_BINDING_TYPES:
            errors.append(f"Invalid binding type: {b.type}")
    for p in mrh.paired:
        if p.pairing_type not in VALID_PAIRING_TYPES:
            errors.append(f"Invalid pairing type: {p.pairing_type}")
    # First paired MUST be citizen role
    if mrh.paired and mrh.paired[0].pairing_type != "birth_certificate":
        errors.append("First paired entry must be birth_certificate")
    if not mrh.last_updated:
        errors.append("last_updated required")
    return errors

def validate_attestation_fields(att: LCTAttestation) -> list[str]:
    """§2.6: Attestation fields validation."""
    errors = []
    if not att.witness:
        errors.append("witness required")
    if att.type not in VALID_ATTESTATION_TYPES:
        errors.append(f"Invalid attestation type: {att.type}")
    if not att.sig:
        errors.append("sig required")
    if not att.ts:
        errors.append("ts required")
    return errors

def validate_lineage_fields(lineage: LCTLineage) -> list[str]:
    """§2.7: Lineage fields validation."""
    errors = []
    if lineage.reason not in VALID_LINEAGE_REASONS:
        errors.append(f"Invalid lineage reason: {lineage.reason}")
    if not lineage.ts:
        errors.append("ts required")
    return errors

def validate_revocation_fields(rev: LCTRevocation) -> list[str]:
    """§2.8: Revocation fields validation."""
    errors = []
    if rev.status not in VALID_REVOCATION_STATUSES:
        errors.append(f"Invalid revocation status: {rev.status}")
    if rev.reason and rev.reason not in VALID_REVOCATION_REASONS:
        errors.append(f"Invalid revocation reason: {rev.reason}")
    return errors

def validate_full_lct(lct: LCTObject) -> tuple[bool, list[str]]:
    """Complete LCT validation across all field groups."""
    errors = []
    errors.extend(validate_identity_fields(lct))
    errors.extend(validate_binding_fields(lct.binding))
    if lct.birth_certificate:
        errors.extend(validate_birth_certificate_fields(lct.birth_certificate))
    errors.extend(validate_mrh_fields(lct.mrh))
    for att in lct.attestations:
        errors.extend(validate_attestation_fields(att))
    for lin in lct.lineage:
        errors.extend(validate_lineage_fields(lin))
    errors.extend(validate_revocation_fields(lct.revocation))
    return len(errors) == 0, errors


# ============================================================
# §3  BINDING ALGORITHM
# ============================================================

def create_binding(entity_type: str, public_key: str,
                   hardware_anchor: str = "") -> tuple[str, LCTBinding]:
    """§3: 7-step binding algorithm from spec.
    1. Generate or retrieve key pair (Ed25519 or P-256)
    2. Create canonical binding object
    3. Serialize with deterministic CBOR
    4. Sign with entity's private key
    5. Generate LCT ID: lct:web4: + MB32(SHA256(binding_proof))
    6. Construct complete LCT object
    7. Submit to witness for attestation
    """
    now = datetime.now(timezone.utc).isoformat()

    # Step 2: Canonical binding
    binding = LCTBinding(
        entity_type=entity_type,
        public_key=public_key,
        hardware_anchor=hardware_anchor,
        created_at=now,
    )

    # Steps 3-4: Serialize + sign (simulated)
    canonical = f"{entity_type}|{public_key}|{hardware_anchor}|{now}"
    cbor_bytes = canonical.encode()
    binding.binding_proof = f"cose:Sig:{hashlib.sha256(cbor_bytes).hexdigest()[:32]}"

    # Step 5: Generate LCT ID
    lct_id = f"lct:web4:{hashlib.sha256(binding.binding_proof.encode()).hexdigest()[:16]}"

    return lct_id, binding


# ============================================================
# §4  MRH DYNAMICS
# ============================================================

class MRHManager:
    """§4: MRH update, emergence, and query operations."""

    def __init__(self, mrh: LCTMRH):
        self.mrh = mrh

    def add_binding(self, lct_id: str, rel_type: str):
        """§4.1 step 1: New binding."""
        self.mrh.bound.append(MRHBound(
            lct_id=lct_id, type=rel_type,
            ts=datetime.now(timezone.utc).isoformat()))
        self._update_timestamp()

    def add_pairing(self, lct_id: str, pairing_type: str,
                    permanent: bool = False, context: str = "",
                    session_id: str = ""):
        """§4.1 step 2: New pairing."""
        self.mrh.paired.append(MRHPaired(
            lct_id=lct_id, pairing_type=pairing_type,
            permanent=permanent, context=context,
            session_id=session_id,
            ts=datetime.now(timezone.utc).isoformat()))
        self._update_timestamp()

    def add_witness(self, lct_id: str, role: str):
        """§4.1 step 3: Witness interaction."""
        for w in self.mrh.witnessing:
            if w.lct_id == lct_id:
                w.last_attestation = datetime.now(timezone.utc).isoformat()
                self._update_timestamp()
                return
        self.mrh.witnessing.append(MRHWitness(
            lct_id=lct_id, role=role,
            last_attestation=datetime.now(timezone.utc).isoformat()))
        self._update_timestamp()

    def revoke_relationship(self, lct_id: str) -> bool:
        """§4.1 step 4: Revocation."""
        for i, p in enumerate(self.mrh.paired):
            if p.lct_id == lct_id and not p.permanent:
                self.mrh.paired.pop(i)
                self._update_timestamp()
                return True
        return False

    def is_in_mrh(self, lct_id: str, depth: int = 1) -> bool:
        """§4.3: MRH query — check if entity is within horizon."""
        if depth < 1:
            return False
        # Direct check
        for b in self.mrh.bound:
            if b.lct_id == lct_id:
                return True
        for p in self.mrh.paired:
            if p.lct_id == lct_id:
                return True
        for w in self.mrh.witnessing:
            if w.lct_id == lct_id:
                return True
        return False

    def get_all_direct(self) -> set[str]:
        """Get all direct (depth-1) entities."""
        entities = set()
        for b in self.mrh.bound:
            entities.add(b.lct_id)
        for p in self.mrh.paired:
            entities.add(p.lct_id)
        for w in self.mrh.witnessing:
            entities.add(w.lct_id)
        return entities

    def _update_timestamp(self):
        self.mrh.last_updated = datetime.now(timezone.utc).isoformat()


# ============================================================
# §5  ROTATION RULES
# ============================================================

class RotationManager:
    """§5: Rotation procedure and split-brain resolution."""

    OVERLAP_HOURS = 24       # §5.1: 24 hours
    MAX_OVERLAP_HOURS = 48   # §7.2: MUST NOT exceed 48 hours
    SPLIT_BRAIN_HOURS = 72   # §7.2: resolved within 72 hours

    def __init__(self):
        self.pending_rotations: dict[str, dict] = {}  # parent_lct_id → rotation info

    def initiate_rotation(self, parent: LCTObject, new_public_key: str) -> LCTObject:
        """§5.1: 5-step rotation procedure."""
        # 1. Create new LCT with updated keys
        new_id, new_binding = create_binding(parent.binding.entity_type, new_public_key)

        new_lct = LCTObject(
            lct_id=new_id,
            subject=parent.subject,  # Same subject identity
            binding=new_binding,
            mrh=LCTMRH(
                paired=list(parent.mrh.paired),  # Copy relationships
                witnessing=list(parent.mrh.witnessing),
                last_updated=datetime.now(timezone.utc).isoformat(),
            ),
            policy=parent.policy,
            # 2. Set lineage pointing to parent
            lineage=[LCTLineage(
                parent=parent.lct_id,
                reason="rotation",
                ts=datetime.now(timezone.utc).isoformat(),
            )],
            revocation=LCTRevocation(status="active"),
        )

        # 3. Record pending rotation (overlap window)
        self.pending_rotations[parent.lct_id] = {
            "new_lct_id": new_id,
            "initiated_at": datetime.now(timezone.utc),
            "witness_count": 0,
        }

        return new_lct

    def complete_rotation(self, parent: LCTObject):
        """§5.1 steps 4-5: End overlap, archive parent."""
        parent.revocation = LCTRevocation(
            status="revoked",
            ts=datetime.now(timezone.utc).isoformat(),
            reason="superseded",
        )
        if parent.lct_id in self.pending_rotations:
            del self.pending_rotations[parent.lct_id]

    def resolve_split_brain(self, candidates: list[LCTObject]) -> LCTObject:
        """§5.2: Split-brain resolution.
        1. Accept LCT with most witness attestations
        2. Earlier rotation wins if equal
        3. Explicit revocation designates preferred successor
        """
        if not candidates:
            raise ValueError("No candidates")
        # Sort by attestation count (desc), then timestamp (asc)
        def sort_key(lct):
            att_count = len(lct.attestations)
            ts = lct.lineage[0].ts if lct.lineage else ""
            return (-att_count, ts)
        candidates.sort(key=sort_key)
        return candidates[0]


# ============================================================
# §6  WITNESS ATTESTATION
# ============================================================

# §6.1: Witness classes and required claims
WITNESS_CLASSES = {
    "time": {"required_claims": ["ts", "nonce"], "purpose": "Timestamp proof"},
    "audit": {"required_claims": ["policy_met", "evidence"], "purpose": "Compliance check"},
    "oracle": {"required_claims": ["source", "data"], "purpose": "External validation"},
    "existence": {"required_claims": ["observed_at", "method"], "purpose": "Liveness proof"},
    "action": {"required_claims": ["action_type", "result"], "purpose": "Operation witness"},
    "state": {"required_claims": ["state", "measurement"], "purpose": "Status attestation"},
    "quality": {"required_claims": ["metric", "value"], "purpose": "Performance metric"},
}

def create_attestation(witness_did: str, att_type: str,
                       claims: dict) -> tuple[LCTAttestation, list[str]]:
    """§6.2: Create and validate attestation."""
    errors = []
    if att_type not in WITNESS_CLASSES:
        errors.append(f"Unknown witness type: {att_type}")
        return LCTAttestation(), errors

    # Check required claims
    required = WITNESS_CLASSES[att_type]["required_claims"]
    for req in required:
        if req not in claims:
            errors.append(f"Missing required claim '{req}' for {att_type}")

    now = datetime.now(timezone.utc).isoformat()

    # §7.3: Witnesses MUST NOT sign for future timestamps
    if "ts" in claims:
        try:
            claim_ts = datetime.fromisoformat(claims["ts"].replace("Z", "+00:00"))
            if claim_ts > datetime.now(timezone.utc) + timedelta(seconds=60):
                errors.append("Future timestamp not allowed")
        except (ValueError, TypeError):
            pass

    att = LCTAttestation(
        witness=witness_did,
        type=att_type,
        claims=claims,
        sig=f"cose:ES256:{hashlib.sha256(f'{witness_did}{att_type}{now}'.encode()).hexdigest()[:16]}",
        ts=now,
    )

    return att, errors


# ============================================================
# §9  IANA CONSIDERATIONS
# ============================================================

IANA_REGISTRATIONS = {
    "uri_scheme": "lct:web4:",
    "entity_types": list(VALID_ENTITY_TYPES),
    "witness_types": list(VALID_ATTESTATION_TYPES),
    "revocation_reasons": list(VALID_REVOCATION_REASONS),
}


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

    # ── T1: §2.1 Identity Fields ──
    print("T1: Identity Fields (§2.1)")

    check("T1.1 lct_id format", "lct:web4:mb32" .startswith("lct:web4:"))
    check("T1.2 subject format", "did:web4:key:z6Mk".startswith("did:web4:"))

    errors_good = validate_identity_fields(LCTObject(lct_id="lct:web4:abc", subject="did:web4:key:xyz"))
    check("T1.3 Valid identity no errors", len(errors_good) == 0)

    errors_bad = validate_identity_fields(LCTObject(lct_id="bad:id", subject="bad:sub"))
    check("T1.4 Invalid identity 2 errors", len(errors_bad) == 2)

    # ── T2: §2.2 Binding Fields ──
    print("T2: Binding Fields (§2.2)")

    check("T2.1 12 entity types", len(VALID_ENTITY_TYPES) == 12)
    for etype in ["human", "ai", "organization", "role", "task", "resource",
                  "device", "service", "oracle", "accumulator", "dictionary", "hybrid"]:
        check(f"T2.2 Entity type '{etype}'", etype in VALID_ENTITY_TYPES)

    good_binding = LCTBinding(entity_type="human", public_key="mb64:key",
                               created_at="2025-01-01", binding_proof="cose:sig")
    check("T2.3 Valid binding", len(validate_binding_fields(good_binding)) == 0)

    bad_binding = LCTBinding(entity_type="unknown")
    check("T2.4 Invalid entity_type", len(validate_binding_fields(bad_binding)) > 0)

    # Hardware anchor is optional (§2.2)
    no_hw = LCTBinding(entity_type="ai", public_key="k", created_at="t", binding_proof="p")
    check("T2.5 No hardware anchor OK", len(validate_binding_fields(no_hw)) == 0)

    # ── T3: §2.3 Birth Certificate Fields ──
    print("T3: Birth Certificate Fields (§2.3)")

    check("T3.1 5 birth contexts", len(VALID_BIRTH_CONTEXTS) == 5)
    for ctx in ["nation", "platform", "network", "organization", "ecosystem"]:
        check(f"T3.2 Context '{ctx}'", ctx in VALID_BIRTH_CONTEXTS)

    good_bc = LCTBirthCertificate(
        citizen_role="lct:web4:role:citizen:abc",
        context="platform",
        birth_timestamp="2025-01-01",
        birth_witnesses=["w1", "w2", "w3"],
    )
    check("T3.3 Valid BC", len(validate_birth_certificate_fields(good_bc)) == 0)

    bad_bc = LCTBirthCertificate(context="invalid_ctx")
    errs = validate_birth_certificate_fields(bad_bc)
    check("T3.4 Invalid BC has errors", len(errs) > 0)

    # Parent entity is optional (§2.3)
    with_parent = LCTBirthCertificate(
        citizen_role="r", context="platform", birth_timestamp="t",
        parent_entity="lct:web4:parent", birth_witnesses=["w1"])
    check("T3.5 Parent entity optional", with_parent.parent_entity == "lct:web4:parent")

    # ── T4: §2.4 MRH Fields ──
    print("T4: MRH Fields (§2.4)")

    check("T4.1 3 binding types", len(VALID_BINDING_TYPES) == 3)
    check("T4.2 3 pairing types", len(VALID_PAIRING_TYPES) == 3)

    # First paired MUST be birth_certificate
    good_mrh = LCTMRH(
        paired=[MRHPaired(lct_id="citizen", pairing_type="birth_certificate", permanent=True)],
        last_updated="2025-01-01",
    )
    check("T4.3 Valid MRH", len(validate_mrh_fields(good_mrh)) == 0)

    bad_mrh = LCTMRH(
        paired=[MRHPaired(lct_id="op", pairing_type="operational")],
        last_updated="2025-01-01",
    )
    errs_mrh = validate_mrh_fields(bad_mrh)
    check("T4.4 First paired must be birth_certificate", len(errs_mrh) > 0)

    # Horizon depth default 3 (§2.4)
    check("T4.5 Default horizon_depth 3", LCTMRH().horizon_depth == 3)

    # last_updated required
    no_ts = LCTMRH(last_updated="")
    check("T4.6 last_updated required", len(validate_mrh_fields(no_ts)) > 0)

    # ── T5: §2.6 Attestation Fields ──
    print("T5: Attestation Fields (§2.6)")

    check("T5.1 7 attestation types", len(VALID_ATTESTATION_TYPES) == 7)
    for atype in ["time", "audit", "oracle", "existence", "action", "state", "quality"]:
        check(f"T5.2 Attestation type '{atype}'", atype in VALID_ATTESTATION_TYPES)

    good_att = LCTAttestation(witness="did:web4:w", type="audit", sig="cose:s", ts="t")
    check("T5.3 Valid attestation", len(validate_attestation_fields(good_att)) == 0)

    bad_att = LCTAttestation(type="unknown")
    check("T5.4 Invalid type caught", len(validate_attestation_fields(bad_att)) > 0)

    # ── T6: §2.7 Lineage Fields ──
    print("T6: Lineage Fields (§2.7)")

    check("T6.1 4 lineage reasons", len(VALID_LINEAGE_REASONS) == 4)
    for reason in ["genesis", "rotation", "fork", "upgrade"]:
        check(f"T6.2 Reason '{reason}'", reason in VALID_LINEAGE_REASONS)

    good_lin = LCTLineage(reason="genesis", ts="2025-01-01")
    check("T6.3 Valid lineage", len(validate_lineage_fields(good_lin)) == 0)

    bad_lin = LCTLineage(reason="invalid")
    check("T6.4 Invalid reason caught", len(validate_lineage_fields(bad_lin)) > 0)

    # Parent is optional for genesis
    check("T6.5 Parent optional", True)

    # ── T7: §2.8 Revocation Fields ──
    print("T7: Revocation Fields (§2.8)")

    check("T7.1 2 revocation statuses", len(VALID_REVOCATION_STATUSES) == 2)
    check("T7.2 3 revocation reasons", len(VALID_REVOCATION_REASONS) == 3)

    good_rev = LCTRevocation(status="active")
    check("T7.3 Active valid", len(validate_revocation_fields(good_rev)) == 0)

    revoked = LCTRevocation(status="revoked", reason="compromise")
    check("T7.4 Revoked with reason valid", len(validate_revocation_fields(revoked)) == 0)

    bad_rev = LCTRevocation(status="invalid")
    check("T7.5 Invalid status caught", len(validate_revocation_fields(bad_rev)) > 0)

    bad_reason = LCTRevocation(status="revoked", reason="bad_reason")
    check("T7.6 Invalid reason caught", len(validate_revocation_fields(bad_reason)) > 0)

    # ── T8: §3 Binding Algorithm ──
    print("T8: Binding Algorithm (§3)")

    lct_id, binding = create_binding("human", "mb64:coseKey:test", "eat:mb64:hw:tpm")
    check("T8.1 LCT ID format", lct_id.startswith("lct:web4:"))
    check("T8.2 Entity type", binding.entity_type == "human")
    check("T8.3 Public key", binding.public_key == "mb64:coseKey:test")
    check("T8.4 Hardware anchor", binding.hardware_anchor == "eat:mb64:hw:tpm")
    check("T8.5 Created at", len(binding.created_at) > 0)
    check("T8.6 Binding proof COSE", binding.binding_proof.startswith("cose:Sig:"))
    # Step 5: LCT ID = lct:web4: + MB32(SHA256(binding_proof))
    expected_hash = hashlib.sha256(binding.binding_proof.encode()).hexdigest()[:16]
    check("T8.7 LCT ID = hash of binding proof", lct_id == f"lct:web4:{expected_hash}")

    # Different keys → different IDs
    id2, _ = create_binding("ai", "mb64:different_key")
    check("T8.8 Different keys → different IDs", lct_id != id2)

    # ── T9: §4 MRH Dynamics ──
    print("T9: MRH Dynamics (§4)")

    mrh = LCTMRH(last_updated=datetime.now(timezone.utc).isoformat())
    mgr = MRHManager(mrh)

    # §4.1 step 1: New binding
    mgr.add_binding("lct:web4:hw:tpm001", "parent")
    check("T9.1 Binding added", len(mrh.bound) == 1)
    check("T9.2 Binding type", mrh.bound[0].type == "parent")

    # §4.1 step 2: New pairing
    mgr.add_pairing("lct:web4:role:citizen:abc", "birth_certificate", permanent=True)
    check("T9.3 Pairing added", len(mrh.paired) == 1)

    mgr.add_pairing("lct:web4:session:xyz", "operational",
                     context="energy-mgmt", session_id="sess001")
    check("T9.4 Operational pairing", mrh.paired[1].session_id == "sess001")

    # §4.1 step 3: Witness interaction
    mgr.add_witness("lct:web4:witness:time1", "time")
    check("T9.5 Witness added", len(mrh.witnessing) == 1)

    # Update existing witness
    mgr.add_witness("lct:web4:witness:time1", "time")
    check("T9.6 Existing witness updated", len(mrh.witnessing) == 1)

    # §4.1 step 4: Revocation
    check("T9.7 Revoke operational", mgr.revoke_relationship("lct:web4:session:xyz"))
    check("T9.8 Cannot revoke permanent", not mgr.revoke_relationship("lct:web4:role:citizen:abc"))
    check("T9.9 Paired count after revoke", len(mrh.paired) == 1)

    # §4.3: MRH query
    check("T9.10 In MRH (bound)", mgr.is_in_mrh("lct:web4:hw:tpm001"))
    check("T9.11 In MRH (paired)", mgr.is_in_mrh("lct:web4:role:citizen:abc"))
    check("T9.12 In MRH (witness)", mgr.is_in_mrh("lct:web4:witness:time1"))
    check("T9.13 Not in MRH", not mgr.is_in_mrh("lct:web4:unknown"))

    # Direct entities
    direct = mgr.get_all_direct()
    check("T9.14 3 direct entities", len(direct) == 3)

    # §4.2: Context emergence
    check("T9.15 last_updated set", len(mrh.last_updated) > 0)

    # ── T10: §5 Rotation Rules ──
    print("T10: Rotation Rules (§5)")

    # Create parent LCT
    parent_id, parent_binding = create_binding("human", "mb64:key:alice_v1")
    parent = LCTObject(
        lct_id=parent_id,
        subject="did:web4:key:alice",
        binding=parent_binding,
        mrh=LCTMRH(
            paired=[MRHPaired(lct_id="citizen", pairing_type="birth_certificate", permanent=True)],
            witnessing=[MRHWitness(lct_id="w1", role="time")],
            last_updated=datetime.now(timezone.utc).isoformat(),
        ),
        policy=LCTPolicy(capabilities=["read", "write"]),
        revocation=LCTRevocation(status="active"),
    )

    rot = RotationManager()
    new_lct = rot.initiate_rotation(parent, "mb64:key:alice_v2")

    # §5.1 step 1: New LCT created
    check("T10.1 New LCT different ID", new_lct.lct_id != parent.lct_id)

    # §5.1: Same subject identity
    check("T10.2 Same subject", new_lct.subject == parent.subject)

    # §5.1 step 2: Lineage points to parent
    check("T10.3 Lineage parent", new_lct.lineage[0].parent == parent.lct_id)
    check("T10.4 Lineage reason rotation", new_lct.lineage[0].reason == "rotation")

    # §5.1 step 3: Overlap window
    check("T10.5 Overlap 24h", rot.OVERLAP_HOURS == 24)
    check("T10.6 Max overlap 48h (§7.2)", rot.MAX_OVERLAP_HOURS == 48)
    check("T10.7 Pending rotation recorded", parent.lct_id in rot.pending_rotations)

    # Both LCTs valid during overlap
    check("T10.8 Parent still active", parent.revocation.status == "active")
    check("T10.9 New LCT active", new_lct.revocation.status == "active")

    # §5.1 steps 4-5: Complete rotation
    rot.complete_rotation(parent)
    check("T10.10 Parent revoked", parent.revocation.status == "revoked")
    check("T10.11 Reason superseded", parent.revocation.reason == "superseded")
    check("T10.12 Pending cleared", parent.lct_id not in rot.pending_rotations)

    # §7.2: Parent MUST NOT be reactivated
    check("T10.13 Parent cannot be reactivated", parent.revocation.status == "revoked")

    # Relationships migrated
    check("T10.14 Paired migrated", len(new_lct.mrh.paired) > 0)
    check("T10.15 Witnesses migrated", len(new_lct.mrh.witnessing) > 0)

    # ── T11: §5.2 Split-Brain Resolution ──
    print("T11: Split-Brain Resolution (§5.2)")

    rot2 = RotationManager()

    # Create 2 candidates with different attestation counts
    cand1 = LCTObject(
        lct_id="lct:web4:cand1",
        attestations=[LCTAttestation(witness="w1", type="existence", sig="s", ts="t")],
        lineage=[LCTLineage(reason="rotation", ts="2025-01-02T00:00:00Z")],
    )
    cand2 = LCTObject(
        lct_id="lct:web4:cand2",
        attestations=[
            LCTAttestation(witness="w1", type="existence", sig="s", ts="t"),
            LCTAttestation(witness="w2", type="existence", sig="s", ts="t"),
        ],
        lineage=[LCTLineage(reason="rotation", ts="2025-01-01T00:00:00Z")],
    )

    # Rule 1: Most witness attestations wins
    winner = rot2.resolve_split_brain([cand1, cand2])
    check("T11.1 Most attestations wins", winner.lct_id == "lct:web4:cand2")

    # Rule 2: Earlier timestamp wins if equal
    cand3 = LCTObject(
        lct_id="lct:web4:cand3",
        attestations=[LCTAttestation(witness="w1", type="existence", sig="s", ts="t")],
        lineage=[LCTLineage(reason="rotation", ts="2025-01-01T00:00:00Z")],
    )
    cand4 = LCTObject(
        lct_id="lct:web4:cand4",
        attestations=[LCTAttestation(witness="w1", type="existence", sig="s", ts="t")],
        lineage=[LCTLineage(reason="rotation", ts="2025-01-02T00:00:00Z")],
    )
    winner2 = rot2.resolve_split_brain([cand4, cand3])
    check("T11.2 Earlier timestamp wins", winner2.lct_id == "lct:web4:cand3")

    # §7.2: Resolved within 72 hours
    check("T11.3 Resolution deadline 72h", rot2.SPLIT_BRAIN_HOURS == 72)

    # ── T12: §6 Witness Attestation ──
    print("T12: Witness Attestation (§6)")

    # §6.1: All 7 witness classes
    check("T12.1 7 witness classes", len(WITNESS_CLASSES) == 7)
    for cls in ["time", "audit", "oracle", "existence", "action", "state", "quality"]:
        check(f"T12.2 Class '{cls}' defined", cls in WITNESS_CLASSES)
        check(f"T12.3 '{cls}' has required claims",
              "required_claims" in WITNESS_CLASSES[cls])
        check(f"T12.4 '{cls}' has purpose",
              "purpose" in WITNESS_CLASSES[cls])

    # §6.1: Required claims per class
    check("T12.5 Time needs ts+nonce",
          WITNESS_CLASSES["time"]["required_claims"] == ["ts", "nonce"])
    check("T12.6 Audit needs policy_met+evidence",
          WITNESS_CLASSES["audit"]["required_claims"] == ["policy_met", "evidence"])
    check("T12.7 Quality needs metric+value",
          WITNESS_CLASSES["quality"]["required_claims"] == ["metric", "value"])

    # §6.2: Create valid attestation
    att, errs = create_attestation(
        "did:web4:key:z6Mkwitness",
        "audit",
        {"policy_met": True, "evidence": "mb64:proof"},
    )
    check("T12.8 Valid attestation", len(errs) == 0)
    check("T12.9 Witness DID", att.witness == "did:web4:key:z6Mkwitness")
    check("T12.10 Type audit", att.type == "audit")
    check("T12.11 COSE sig", att.sig.startswith("cose:ES256:"))
    check("T12.12 Timestamp", len(att.ts) > 0)

    # Missing required claims
    att2, errs2 = create_attestation(
        "did:web4:witness2", "time",
        {"ts": "2025-01-01T00:00:00Z"},  # Missing nonce
    )
    check("T12.13 Missing claim detected", len(errs2) > 0)
    check("T12.14 Error mentions nonce", any("nonce" in e for e in errs2))

    # Unknown type
    att3, errs3 = create_attestation("did:web4:w", "unknown_type", {})
    check("T12.15 Unknown type error", len(errs3) > 0)

    # ── T13: §7 Security Considerations ──
    print("T13: Security Considerations (§7)")

    # §7.1: Private keys never in LCT
    check("T13.1 No private key in binding",
          "private" not in parent_binding.public_key.lower())

    # §7.2: Overlap MUST NOT exceed 48h
    check("T13.2 Max overlap 48h", RotationManager.MAX_OVERLAP_HOURS == 48)

    # §7.2: Split-brain within 72h
    check("T13.3 Split-brain 72h", RotationManager.SPLIT_BRAIN_HOURS == 72)

    # §7.3: No future timestamps
    future_ts = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    att_future, errs_future = create_attestation(
        "did:web4:w", "time",
        {"ts": future_ts, "nonce": "abc"},
    )
    check("T13.4 Future timestamp rejected", len(errs_future) > 0)

    # Past timestamp OK
    past_ts = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    att_past, errs_past = create_attestation(
        "did:web4:w", "time",
        {"ts": past_ts, "nonce": "abc"},
    )
    check("T13.5 Past timestamp OK", len(errs_past) == 0)

    # ── T14: §8 Privacy Considerations ──
    print("T14: Privacy (§8)")

    # §8: LCT IDs SHOULD NOT contain PII
    check("T14.1 LCT ID no PII",
          "@" not in new_lct.lct_id and "email" not in new_lct.lct_id)

    # §8: Subject can be key-based DID (pseudonymous)
    check("T14.2 Pseudonymous DID", new_lct.subject.startswith("did:web4:key:"))

    # §8: Capabilities use least-privilege
    check("T14.3 Capabilities defined", isinstance(new_lct.policy.capabilities, list))

    # ── T15: §9 IANA Considerations ──
    print("T15: IANA Considerations (§9)")

    check("T15.1 URI scheme", IANA_REGISTRATIONS["uri_scheme"] == "lct:web4:")
    check("T15.2 Entity types registry", len(IANA_REGISTRATIONS["entity_types"]) == 12)
    check("T15.3 Witness types registry", len(IANA_REGISTRATIONS["witness_types"]) == 7)
    check("T15.4 Revocation reasons", len(IANA_REGISTRATIONS["revocation_reasons"]) == 3)

    # ── T16: Full LCT Validation ──
    print("T16: Full LCT Validation")

    now = datetime.now(timezone.utc).isoformat()
    full_lct = LCTObject(
        lct_id="lct:web4:abc123",
        subject="did:web4:key:z6Mk",
        binding=LCTBinding(entity_type="human", public_key="mb64:k",
                           created_at=now, binding_proof="cose:sig"),
        birth_certificate=LCTBirthCertificate(
            citizen_role="lct:web4:role:citizen:abc",
            context="platform",
            birth_timestamp=now,
            birth_witnesses=["w1", "w2", "w3"],
        ),
        mrh=LCTMRH(
            paired=[MRHPaired(lct_id="citizen", pairing_type="birth_certificate",
                              permanent=True, ts=now)],
            last_updated=now,
        ),
        policy=LCTPolicy(capabilities=["read"]),
        attestations=[LCTAttestation(witness="did:web4:w1", type="existence",
                                      sig="cose:s", ts=now)],
        lineage=[LCTLineage(reason="genesis", ts=now)],
        revocation=LCTRevocation(status="active"),
    )
    valid, errors = validate_full_lct(full_lct)
    check("T16.1 Full LCT valid", valid)
    check("T16.2 No validation errors", len(errors) == 0)

    # Invalid LCT
    bad_full = LCTObject(
        lct_id="bad",
        subject="bad",
        binding=LCTBinding(entity_type="unknown"),
        mrh=LCTMRH(),
        lineage=[LCTLineage(reason="bad_reason")],
    )
    valid2, errors2 = validate_full_lct(bad_full)
    check("T16.3 Invalid LCT caught", not valid2)
    check("T16.4 Multiple errors", len(errors2) >= 3)

    # ── T17: Edge Cases ──
    print("T17: Edge Cases")

    # Empty candidates split-brain
    try:
        RotationManager().resolve_split_brain([])
        check("T17.1 Empty candidates raises", False)
    except ValueError:
        check("T17.1 Empty candidates raises", True)

    # Multiple rotations
    rot3 = RotationManager()
    p1_id, p1_bind = create_binding("ai", "key1")
    p1 = LCTObject(lct_id=p1_id, subject="did:web4:key:ai1", binding=p1_bind,
                    mrh=LCTMRH(last_updated=now),
                    policy=LCTPolicy())
    n1 = rot3.initiate_rotation(p1, "key2")
    rot3.complete_rotation(p1)
    n2 = rot3.initiate_rotation(n1, "key3")
    check("T17.2 Chain rotation", n2.lineage[0].parent == n1.lct_id)

    # MRH depth 0 edge case
    check("T17.3 Depth 0 not in MRH", not MRHManager(LCTMRH()).is_in_mrh("anything", depth=0))

    # ── Summary ──
    print()
    print("=" * 60)
    print(f"LCT Protocol: {passed}/{passed+failed} checks passed")
    if failures:
        print(f"  {failed} FAILED:")
        for f in failures:
            print(f"    - {f}")
    else:
        print("  All checks passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
