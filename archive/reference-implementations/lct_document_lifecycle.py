#!/usr/bin/env python3
"""
LCT Document Lifecycle — Session 20, Track 5

Full lifecycle of Linked Context Token documents from birth to revocation:
- LCT document model (JSON-LD structure with birth certificate)
- Birth ceremony: entity creation with witness attestation
- Activation and trust initialization
- Suspension and reactivation with reason tracking
- Revocation with cascade and cleanup
- Document serialization (JSON-LD, CBOR-like compact, Turtle/N-Triples)
- Cross-reference validation (LCT→entity, LCT→LCT)
- MRH context linking (LCT as presence substrate)
- Temporal validity and expiry management
- LCT migration and entity transfer
- Performance at scale

Reference: LCT-linked-context-token.md, entity lifecycle FSMs,
  BirthCertificate schema, core-protocol.md
"""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ─── Constants ────────────────────────────────────────────────────────────────

class LCTState(Enum):
    NASCENT = "nascent"      # Created but not yet activated
    ACTIVE = "active"        # Fully operational
    SUSPENDED = "suspended"  # Temporarily inactive
    REVOKED = "revoked"      # Permanently deactivated
    EXPIRED = "expired"      # Past validity period


class EntityType(Enum):
    HUMAN = "human"
    AI = "ai"
    ORGANIZATION = "organization"
    DEVICE = "device"
    SERVICE = "service"
    SOCIETY = "society"
    ROLE = "role"
    DICTIONARY = "dictionary"


LCT_CONTEXT = "https://web4.io/ontology#"
LCT_TYPE = "LinkedContextToken"


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class BirthCertificate:
    """Attestation of LCT creation."""
    issuer_id: str
    subject_id: str
    witness_ids: List[str]
    issued_at: float
    entity_type: EntityType
    signature: bytes = b""
    certificate_hash: str = ""

    def compute_hash(self) -> str:
        data = f"{self.issuer_id}:{self.subject_id}:{self.issued_at}:{self.entity_type.value}"
        data += ":" + ",".join(sorted(self.witness_ids))
        return hashlib.sha256(data.encode()).hexdigest()

    def __post_init__(self):
        if not self.certificate_hash:
            self.certificate_hash = self.compute_hash()


@dataclass
class LCTDocument:
    """A Linked Context Token document."""
    lct_id: str
    entity_id: str
    entity_type: EntityType
    state: LCTState = LCTState.NASCENT
    birth_certificate: Optional[BirthCertificate] = None
    created_at: float = 0.0
    activated_at: Optional[float] = None
    suspended_at: Optional[float] = None
    revoked_at: Optional[float] = None
    expires_at: Optional[float] = None
    suspension_reason: Optional[str] = None
    revocation_reason: Optional[str] = None
    parent_lct_id: Optional[str] = None
    child_lct_ids: List[str] = field(default_factory=list)
    mrh_links: Dict[str, str] = field(default_factory=dict)  # target_id → link_type
    trust_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1

    def is_valid(self, now: float = None) -> bool:
        """Check if LCT is currently valid."""
        if now is None:
            now = time.time()
        if self.state not in (LCTState.ACTIVE,):
            return False
        if self.expires_at is not None and now > self.expires_at:
            return False
        return True

    def document_hash(self) -> str:
        """Content-based hash for integrity verification."""
        data = f"{self.lct_id}:{self.entity_id}:{self.state.value}:{self.version}"
        if self.birth_certificate:
            data += ":" + self.birth_certificate.certificate_hash
        return hashlib.sha256(data.encode()).hexdigest()[:32]


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: LCTState
    to_state: LCTState
    timestamp: float
    reason: str
    actor_id: str


# ─── S1: LCT Document Model (JSON-LD) ───────────────────────────────────────

def to_jsonld(lct: LCTDocument) -> Dict[str, Any]:
    """Serialize LCT to JSON-LD format."""
    doc = {
        "@context": LCT_CONTEXT,
        "@type": LCT_TYPE,
        "@id": f"lct:{lct.lct_id}",
        "entityId": lct.entity_id,
        "entityType": lct.entity_type.value,
        "state": lct.state.value,
        "version": lct.version,
        "createdAt": lct.created_at,
    }

    if lct.activated_at is not None:
        doc["activatedAt"] = lct.activated_at
    if lct.expires_at is not None:
        doc["expiresAt"] = lct.expires_at
    if lct.parent_lct_id:
        doc["parentLct"] = f"lct:{lct.parent_lct_id}"
    if lct.child_lct_ids:
        doc["childLcts"] = [f"lct:{cid}" for cid in lct.child_lct_ids]
    if lct.mrh_links:
        doc["mrhLinks"] = [
            {"target": tid, "linkType": lt}
            for tid, lt in lct.mrh_links.items()
        ]
    if lct.birth_certificate:
        doc["birthCertificate"] = {
            "issuer": lct.birth_certificate.issuer_id,
            "subject": lct.birth_certificate.subject_id,
            "witnesses": lct.birth_certificate.witness_ids,
            "issuedAt": lct.birth_certificate.issued_at,
            "hash": lct.birth_certificate.certificate_hash,
        }
    if lct.trust_score > 0:
        doc["trustScore"] = lct.trust_score
    if lct.metadata:
        doc["metadata"] = lct.metadata

    return doc


def from_jsonld(doc: Dict[str, Any]) -> LCTDocument:
    """Deserialize LCT from JSON-LD format."""
    lct = LCTDocument(
        lct_id=doc["@id"].replace("lct:", ""),
        entity_id=doc["entityId"],
        entity_type=EntityType(doc["entityType"]),
        state=LCTState(doc["state"]),
        version=doc.get("version", 1),
        created_at=doc.get("createdAt", 0),
        activated_at=doc.get("activatedAt"),
        expires_at=doc.get("expiresAt"),
        trust_score=doc.get("trustScore", 0.0),
        metadata=doc.get("metadata", {}),
    )

    if "parentLct" in doc:
        lct.parent_lct_id = doc["parentLct"].replace("lct:", "")
    if "childLcts" in doc:
        lct.child_lct_ids = [cid.replace("lct:", "") for cid in doc["childLcts"]]
    if "mrhLinks" in doc:
        lct.mrh_links = {link["target"]: link["linkType"] for link in doc["mrhLinks"]}

    if "birthCertificate" in doc:
        bc = doc["birthCertificate"]
        lct.birth_certificate = BirthCertificate(
            issuer_id=bc["issuer"],
            subject_id=bc["subject"],
            witness_ids=bc["witnesses"],
            issued_at=bc["issuedAt"],
            entity_type=lct.entity_type,
            certificate_hash=bc["hash"],
        )

    return lct


# ─── S2: Birth Ceremony ─────────────────────────────────────────────────────

class BirthCeremony:
    """Protocol for creating a new LCT with witnessed birth."""

    def __init__(self, min_witnesses: int = 1):
        self.min_witnesses = min_witnesses

    def create(
        self,
        entity_id: str,
        entity_type: EntityType,
        issuer_id: str,
        witness_ids: List[str],
        expires_in: Optional[float] = None,
        parent_lct_id: Optional[str] = None,
    ) -> Optional[LCTDocument]:
        """
        Create a new LCT with birth certificate.
        Requires minimum witnesses.
        """
        if len(witness_ids) < self.min_witnesses:
            return None

        now = time.time()
        lct_id = hashlib.sha256(
            f"{entity_id}:{now}:{issuer_id}".encode()
        ).hexdigest()[:16]

        birth_cert = BirthCertificate(
            issuer_id=issuer_id,
            subject_id=entity_id,
            witness_ids=witness_ids,
            issued_at=now,
            entity_type=entity_type,
        )

        lct = LCTDocument(
            lct_id=lct_id,
            entity_id=entity_id,
            entity_type=entity_type,
            state=LCTState.NASCENT,
            birth_certificate=birth_cert,
            created_at=now,
            expires_at=now + expires_in if expires_in else None,
            parent_lct_id=parent_lct_id,
        )

        return lct


# ─── S3: State Machine ──────────────────────────────────────────────────────

# Valid transitions
VALID_TRANSITIONS = {
    LCTState.NASCENT: {LCTState.ACTIVE, LCTState.REVOKED},
    LCTState.ACTIVE: {LCTState.SUSPENDED, LCTState.REVOKED, LCTState.EXPIRED},
    LCTState.SUSPENDED: {LCTState.ACTIVE, LCTState.REVOKED},
    LCTState.REVOKED: set(),  # Terminal
    LCTState.EXPIRED: set(),  # Terminal
}


class LCTLifecycleManager:
    """Manage LCT state transitions."""

    def __init__(self):
        self.lcts: Dict[str, LCTDocument] = {}
        self.transitions: List[StateTransition] = []

    def register(self, lct: LCTDocument):
        self.lcts[lct.lct_id] = lct

    def transition(
        self, lct_id: str, new_state: LCTState, reason: str, actor_id: str,
    ) -> bool:
        """
        Attempt a state transition.
        Returns True if successful, False if invalid.
        """
        lct = self.lcts.get(lct_id)
        if not lct:
            return False

        valid_next = VALID_TRANSITIONS.get(lct.state, set())
        if new_state not in valid_next:
            return False

        now = time.time()
        old_state = lct.state

        # Apply transition
        lct.state = new_state
        if new_state == LCTState.ACTIVE and lct.activated_at is None:
            lct.activated_at = now
        elif new_state == LCTState.SUSPENDED:
            lct.suspended_at = now
            lct.suspension_reason = reason
        elif new_state == LCTState.REVOKED:
            lct.revoked_at = now
            lct.revocation_reason = reason

        self.transitions.append(StateTransition(
            old_state, new_state, now, reason, actor_id,
        ))

        return True

    def activate(self, lct_id: str, actor_id: str) -> bool:
        return self.transition(lct_id, LCTState.ACTIVE, "activation", actor_id)

    def suspend(self, lct_id: str, reason: str, actor_id: str) -> bool:
        return self.transition(lct_id, LCTState.SUSPENDED, reason, actor_id)

    def reactivate(self, lct_id: str, actor_id: str) -> bool:
        return self.transition(lct_id, LCTState.ACTIVE, "reactivation", actor_id)

    def revoke(self, lct_id: str, reason: str, actor_id: str) -> bool:
        return self.transition(lct_id, LCTState.REVOKED, reason, actor_id)

    def check_expiry(self, now: float = None) -> List[str]:
        """Check and expire LCTs past their validity."""
        if now is None:
            now = time.time()
        expired = []
        for lct_id, lct in self.lcts.items():
            if lct.state == LCTState.ACTIVE and lct.expires_at and now > lct.expires_at:
                self.transition(lct_id, LCTState.EXPIRED, "expiry", "system")
                expired.append(lct_id)
        return expired

    def cascade_revoke(self, lct_id: str, reason: str, actor_id: str) -> List[str]:
        """Revoke an LCT and all its children."""
        revoked = []
        queue = [lct_id]
        while queue:
            current = queue.pop(0)
            if self.revoke(current, reason, actor_id):
                revoked.append(current)
                lct = self.lcts.get(current)
                if lct:
                    queue.extend(lct.child_lct_ids)
        return revoked


# ─── S4: Compact Serialization ──────────────────────────────────────────────

def to_compact(lct: LCTDocument) -> bytes:
    """
    Compact binary-like serialization (CBOR-inspired but simplified).
    Format: JSON with short keys for efficiency.
    """
    compact = {
        "i": lct.lct_id,
        "e": lct.entity_id,
        "t": lct.entity_type.value,
        "s": lct.state.value,
        "v": lct.version,
        "c": lct.created_at,
    }
    if lct.activated_at is not None:
        compact["a"] = lct.activated_at
    if lct.expires_at is not None:
        compact["x"] = lct.expires_at
    if lct.trust_score > 0:
        compact["ts"] = round(lct.trust_score, 4)
    if lct.parent_lct_id:
        compact["p"] = lct.parent_lct_id
    if lct.child_lct_ids:
        compact["ch"] = lct.child_lct_ids
    if lct.birth_certificate:
        compact["bc"] = lct.birth_certificate.certificate_hash
    if lct.mrh_links:
        compact["m"] = lct.mrh_links

    return json.dumps(compact, separators=(",", ":")).encode()


def from_compact(data: bytes) -> LCTDocument:
    """Deserialize from compact format."""
    compact = json.loads(data.decode())
    lct = LCTDocument(
        lct_id=compact["i"],
        entity_id=compact["e"],
        entity_type=EntityType(compact["t"]),
        state=LCTState(compact["s"]),
        version=compact.get("v", 1),
        created_at=compact.get("c", 0),
        activated_at=compact.get("a"),
        expires_at=compact.get("x"),
        trust_score=compact.get("ts", 0.0),
        parent_lct_id=compact.get("p"),
        child_lct_ids=compact.get("ch", []),
        mrh_links=compact.get("m", {}),
    )
    return lct


# ─── S5: N-Triples Serialization ────────────────────────────────────────────

def to_ntriples(lct: LCTDocument) -> str:
    """Serialize LCT to N-Triples (RDF) format."""
    subject = f"<{LCT_CONTEXT}{lct.lct_id}>"
    triples = []

    def triple(s, p, o):
        triples.append(f"{s} <{LCT_CONTEXT}{p}> {o} .")

    triple(subject, "type", f'"{LCT_TYPE}"')
    triple(subject, "entityId", f'"{lct.entity_id}"')
    triple(subject, "entityType", f'"{lct.entity_type.value}"')
    triple(subject, "state", f'"{lct.state.value}"')
    triple(subject, "version", f'"{lct.version}"^^<xsd:integer>')
    triple(subject, "createdAt", f'"{lct.created_at}"^^<xsd:double>')

    if lct.trust_score > 0:
        triple(subject, "trustScore", f'"{lct.trust_score}"^^<xsd:double>')

    if lct.parent_lct_id:
        triple(subject, "parentLct", f"<{LCT_CONTEXT}{lct.parent_lct_id}>")

    for child_id in lct.child_lct_ids:
        triple(subject, "childLct", f"<{LCT_CONTEXT}{child_id}>")

    for target, link_type in lct.mrh_links.items():
        triple(subject, f"mrhLink:{link_type}", f'"{target}"')

    if lct.birth_certificate:
        triple(subject, "birthCertHash", f'"{lct.birth_certificate.certificate_hash}"')

    return "\n".join(triples)


def count_triples(ntriples: str) -> int:
    """Count triples in N-Triples output."""
    return len([line for line in ntriples.strip().split("\n") if line.strip()])


# ─── S6: Cross-Reference Validation ─────────────────────────────────────────

class LCTGraph:
    """Validate cross-references between LCT documents."""

    def __init__(self):
        self.lcts: Dict[str, LCTDocument] = {}

    def add(self, lct: LCTDocument):
        self.lcts[lct.lct_id] = lct

    def validate_references(self) -> List[str]:
        """Validate all cross-references. Returns list of errors."""
        errors = []
        for lct_id, lct in self.lcts.items():
            # Check parent reference
            if lct.parent_lct_id and lct.parent_lct_id not in self.lcts:
                errors.append(f"{lct_id}: parent {lct.parent_lct_id} not found")

            # Check child references
            for child_id in lct.child_lct_ids:
                if child_id not in self.lcts:
                    errors.append(f"{lct_id}: child {child_id} not found")

            # Check parent-child symmetry
            if lct.parent_lct_id and lct.parent_lct_id in self.lcts:
                parent = self.lcts[lct.parent_lct_id]
                if lct_id not in parent.child_lct_ids:
                    errors.append(f"{lct_id}: not listed in parent {lct.parent_lct_id}'s children")

        return errors

    def validate_birth_certs(self) -> List[str]:
        """Validate all birth certificates."""
        errors = []
        for lct_id, lct in self.lcts.items():
            if lct.birth_certificate is None:
                errors.append(f"{lct_id}: missing birth certificate")
                continue
            expected_hash = lct.birth_certificate.compute_hash()
            if lct.birth_certificate.certificate_hash != expected_hash:
                errors.append(f"{lct_id}: birth certificate hash mismatch")

        return errors

    def find_orphans(self) -> List[str]:
        """Find LCTs that reference a parent that doesn't list them as children."""
        orphans = []
        for lct_id, lct in self.lcts.items():
            if lct.parent_lct_id:
                parent = self.lcts.get(lct.parent_lct_id)
                if parent and lct_id not in parent.child_lct_ids:
                    orphans.append(lct_id)
        return orphans


# ─── S7: MRH Context Linking ────────────────────────────────────────────────

class MRHZone(Enum):
    SELF = 0
    DIRECT = 1
    INDIRECT = 2
    PERIPHERAL = 3
    BEYOND = 4


def link_mrh(lct: LCTDocument, target_id: str, link_type: str):
    """Add an MRH context link from this LCT to a target."""
    lct.mrh_links[target_id] = link_type


def compute_mrh_zone(graph: LCTGraph, source_id: str, target_id: str) -> MRHZone:
    """Compute MRH zone between two LCTs via parent/child links."""
    if source_id == target_id:
        return MRHZone.SELF

    # BFS through parent-child graph
    visited = {source_id}
    frontier = [source_id]
    hops = 0

    while frontier and hops < 5:
        hops += 1
        next_frontier = []
        for node_id in frontier:
            node = graph.lcts.get(node_id)
            if not node:
                continue
            neighbors = set()
            if node.parent_lct_id:
                neighbors.add(node.parent_lct_id)
            neighbors.update(node.child_lct_ids)
            # Also check mrh_links
            neighbors.update(node.mrh_links.keys())

            for n in neighbors:
                if n == target_id:
                    if hops == 1:
                        return MRHZone.DIRECT
                    elif hops == 2:
                        return MRHZone.INDIRECT
                    else:
                        return MRHZone.PERIPHERAL
                if n not in visited:
                    visited.add(n)
                    next_frontier.append(n)
        frontier = next_frontier

    return MRHZone.BEYOND


# ─── S8: Temporal Validity ──────────────────────────────────────────────────

def check_validity_window(lct: LCTDocument, now: float) -> Tuple[bool, str]:
    """Check if an LCT is within its validity window."""
    if lct.state == LCTState.REVOKED:
        return False, "revoked"
    if lct.state == LCTState.EXPIRED:
        return False, "expired"
    if lct.state == LCTState.NASCENT:
        return False, "not_activated"
    if lct.state == LCTState.SUSPENDED:
        return False, "suspended"
    if lct.expires_at is not None and now > lct.expires_at:
        return False, "past_expiry"
    return True, "valid"


def remaining_validity(lct: LCTDocument, now: float) -> Optional[float]:
    """Seconds until LCT expires. None if no expiry."""
    if lct.expires_at is None:
        return None
    return max(0, lct.expires_at - now)


# ─── S9: LCT Migration ─────────────────────────────────────────────────────

@dataclass
class MigrationRecord:
    """Record of LCT entity transfer."""
    lct_id: str
    old_entity_id: str
    new_entity_id: str
    migrated_at: float
    migrated_by: str
    reason: str


class LCTMigrator:
    """Handle entity transfers between LCTs."""

    def __init__(self, manager: LCTLifecycleManager):
        self.manager = manager
        self.migrations: List[MigrationRecord] = []

    def transfer_entity(
        self,
        lct_id: str,
        new_entity_id: str,
        actor_id: str,
        reason: str,
    ) -> bool:
        """
        Transfer an LCT to a new entity.
        LCT must be active. Increments version.
        """
        lct = self.manager.lcts.get(lct_id)
        if not lct or lct.state != LCTState.ACTIVE:
            return False

        old_entity = lct.entity_id
        lct.entity_id = new_entity_id
        lct.version += 1

        self.migrations.append(MigrationRecord(
            lct_id=lct_id,
            old_entity_id=old_entity,
            new_entity_id=new_entity_id,
            migrated_at=time.time(),
            migrated_by=actor_id,
            reason=reason,
        ))

        return True

    def migration_history(self, lct_id: str) -> List[MigrationRecord]:
        return [m for m in self.migrations if m.lct_id == lct_id]


# ─── S10: Batch Operations ──────────────────────────────────────────────────

def batch_create(
    ceremony: BirthCeremony,
    entities: List[Tuple[str, EntityType]],
    issuer_id: str,
    witness_ids: List[str],
) -> List[LCTDocument]:
    """Create multiple LCTs in batch."""
    results = []
    for entity_id, entity_type in entities:
        lct = ceremony.create(entity_id, entity_type, issuer_id, witness_ids)
        if lct:
            results.append(lct)
    return results


def batch_serialize(lcts: List[LCTDocument], format: str = "jsonld") -> List[Any]:
    """Serialize multiple LCTs."""
    if format == "jsonld":
        return [to_jsonld(lct) for lct in lcts]
    elif format == "compact":
        return [to_compact(lct) for lct in lcts]
    elif format == "ntriples":
        return [to_ntriples(lct) for lct in lcts]
    return []


# ─── S11: Performance ───────────────────────────────────────────────────────

# Included in checks


# ══════════════════════════════════════════════════════════════════════════════
#  CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def run_checks():
    checks = []

    # ── S1: LCT Document Model ───────────────────────────────────────────

    cert = BirthCertificate("issuer1", "entity1", ["w1", "w2"], time.time(), EntityType.HUMAN)
    lct = LCTDocument(
        lct_id="lct001",
        entity_id="entity1",
        entity_type=EntityType.HUMAN,
        state=LCTState.ACTIVE,
        birth_certificate=cert,
        created_at=time.time(),
        activated_at=time.time(),
        trust_score=0.7,
        metadata={"role": "researcher"},
    )

    # S1.1: JSON-LD serialization
    jsonld = to_jsonld(lct)
    checks.append(("s1_jsonld_context", jsonld["@context"] == LCT_CONTEXT))
    checks.append(("s1_jsonld_type", jsonld["@type"] == LCT_TYPE))
    checks.append(("s1_jsonld_id", "lct:lct001" == jsonld["@id"]))

    # S1.2: JSON-LD roundtrip
    restored = from_jsonld(jsonld)
    checks.append(("s1_roundtrip_entity", restored.entity_id == "entity1"))
    checks.append(("s1_roundtrip_state", restored.state == LCTState.ACTIVE))
    checks.append(("s1_roundtrip_type", restored.entity_type == EntityType.HUMAN))

    # S1.3: Birth certificate in JSON-LD
    checks.append(("s1_birth_cert", "birthCertificate" in jsonld))

    # S1.4: Document hash deterministic
    h1 = lct.document_hash()
    h2 = lct.document_hash()
    checks.append(("s1_hash_deterministic", h1 == h2))

    # ── S2: Birth Ceremony ───────────────────────────────────────────────

    ceremony = BirthCeremony(min_witnesses=2)

    # S2.1: Create with enough witnesses
    born = ceremony.create("alice", EntityType.HUMAN, "admin", ["w1", "w2"])
    checks.append(("s2_birth_success", born is not None and born.state == LCTState.NASCENT))

    # S2.2: Insufficient witnesses rejected
    rejected = ceremony.create("bob", EntityType.AI, "admin", ["w1"])
    checks.append(("s2_insufficient_witnesses", rejected is None))

    # S2.3: Birth certificate has hash
    checks.append(("s2_cert_hash", born is not None and bool(born.birth_certificate.certificate_hash)))

    # S2.4: LCT ID is unique (content-derived)
    born2 = ceremony.create("alice2", EntityType.HUMAN, "admin", ["w1", "w2"])
    checks.append(("s2_unique_id", born is not None and born2 is not None and born.lct_id != born2.lct_id))

    # S2.5: Parent link
    child = ceremony.create("child1", EntityType.ROLE, "admin", ["w1", "w2"],
                           parent_lct_id=born.lct_id if born else "")
    checks.append(("s2_parent_link", child is not None and child.parent_lct_id is not None))

    # S2.6: Expiry
    expiring = ceremony.create("temp", EntityType.SERVICE, "admin", ["w1", "w2"], expires_in=3600)
    checks.append(("s2_expiry_set", expiring is not None and expiring.expires_at is not None))

    # ── S3: State Machine ────────────────────────────────────────────────

    mgr = LCTLifecycleManager()
    test_lct = ceremony.create("test_entity", EntityType.HUMAN, "admin", ["w1", "w2"])
    if test_lct:
        mgr.register(test_lct)

    # S3.1: Activate from NASCENT
    activated = mgr.activate(test_lct.lct_id, "admin")
    checks.append(("s3_activate", activated and test_lct.state == LCTState.ACTIVE))

    # S3.2: Cannot activate already active
    double_activate = mgr.activate(test_lct.lct_id, "admin")
    checks.append(("s3_no_double_activate", not double_activate))

    # S3.3: Suspend from ACTIVE
    suspended = mgr.suspend(test_lct.lct_id, "maintenance", "admin")
    checks.append(("s3_suspend", suspended and test_lct.state == LCTState.SUSPENDED))

    # S3.4: Reactivate from SUSPENDED
    reactivated = mgr.reactivate(test_lct.lct_id, "admin")
    checks.append(("s3_reactivate", reactivated and test_lct.state == LCTState.ACTIVE))

    # S3.5: Revoke from ACTIVE
    revoked = mgr.revoke(test_lct.lct_id, "compromised", "admin")
    checks.append(("s3_revoke", revoked and test_lct.state == LCTState.REVOKED))

    # S3.6: Cannot reactivate from REVOKED (terminal)
    from_revoked = mgr.reactivate(test_lct.lct_id, "admin")
    checks.append(("s3_revoked_terminal", not from_revoked))

    # S3.7: Transition history
    checks.append(("s3_history", len(mgr.transitions) >= 4))

    # S3.8: Expiry check
    exp_lct = ceremony.create("exp_entity", EntityType.SERVICE, "admin", ["w1", "w2"], expires_in=1)
    if exp_lct:
        mgr.register(exp_lct)
        mgr.activate(exp_lct.lct_id, "admin")
        expired = mgr.check_expiry(time.time() + 10)
        checks.append(("s3_expiry", exp_lct.lct_id in expired))

    # S3.9: Cascade revocation
    parent_lct = ceremony.create("parent", EntityType.ORGANIZATION, "admin", ["w1", "w2"])
    child_lct1 = ceremony.create("child_a", EntityType.HUMAN, "admin", ["w1", "w2"])
    child_lct2 = ceremony.create("child_b", EntityType.HUMAN, "admin", ["w1", "w2"])
    if parent_lct and child_lct1 and child_lct2:
        parent_lct.child_lct_ids = [child_lct1.lct_id, child_lct2.lct_id]
        mgr.register(parent_lct)
        mgr.register(child_lct1)
        mgr.register(child_lct2)
        mgr.activate(parent_lct.lct_id, "admin")
        mgr.activate(child_lct1.lct_id, "admin")
        mgr.activate(child_lct2.lct_id, "admin")
        cascade_result = mgr.cascade_revoke(parent_lct.lct_id, "org_dissolved", "admin")
        checks.append(("s3_cascade", len(cascade_result) == 3))

    # ── S4: Compact Serialization ────────────────────────────────────────

    # S4.1: Compact roundtrip
    compact = to_compact(lct)
    restored_compact = from_compact(compact)
    checks.append(("s4_compact_roundtrip", restored_compact.entity_id == lct.entity_id))

    # S4.2: Compact is smaller than JSON-LD
    jsonld_size = len(json.dumps(to_jsonld(lct)).encode())
    compact_size = len(compact)
    checks.append(("s4_compact_smaller", compact_size < jsonld_size))

    # S4.3: Compact preserves state
    checks.append(("s4_compact_state", restored_compact.state == lct.state))

    # S4.4: Compact preserves type
    checks.append(("s4_compact_type", restored_compact.entity_type == lct.entity_type))

    # ── S5: N-Triples Serialization ──────────────────────────────────────

    # S5.1: N-Triples output
    nt = to_ntriples(lct)
    checks.append(("s5_ntriples_output", len(nt) > 0))

    # S5.2: Contains entity type triple
    checks.append(("s5_has_entity_type", "entityType" in nt))

    # S5.3: Contains state triple
    checks.append(("s5_has_state", "state" in nt))

    # S5.4: Triple count (at least 6 core triples)
    tc = count_triples(nt)
    checks.append(("s5_triple_count", tc >= 6))

    # S5.5: Birth cert hash in triples
    checks.append(("s5_birth_cert_hash", "birthCertHash" in nt))

    # ── S6: Cross-Reference Validation ───────────────────────────────────

    graph = LCTGraph()
    parent = LCTDocument("p1", "parent_entity", EntityType.ORGANIZATION,
                        child_lct_ids=["c1", "c2"],
                        birth_certificate=BirthCertificate("i", "p", ["w"], time.time(), EntityType.ORGANIZATION))
    c1 = LCTDocument("c1", "child1", EntityType.HUMAN, parent_lct_id="p1",
                     birth_certificate=BirthCertificate("i", "c1", ["w"], time.time(), EntityType.HUMAN))
    c2 = LCTDocument("c2", "child2", EntityType.HUMAN, parent_lct_id="p1",
                     birth_certificate=BirthCertificate("i", "c2", ["w"], time.time(), EntityType.HUMAN))
    graph.add(parent)
    graph.add(c1)
    graph.add(c2)

    # S6.1: Valid references
    errors = graph.validate_references()
    checks.append(("s6_valid_refs", len(errors) == 0))

    # S6.2: Missing child detected
    parent2 = LCTDocument("p2", "parent2", EntityType.ORGANIZATION,
                         child_lct_ids=["missing_child"],
                         birth_certificate=BirthCertificate("i", "p2", ["w"], time.time(), EntityType.ORGANIZATION))
    graph.add(parent2)
    errors = graph.validate_references()
    checks.append(("s6_missing_child", any("missing_child" in e for e in errors)))

    # S6.3: Birth cert validation
    bc_errors = graph.validate_birth_certs()
    checks.append(("s6_valid_certs", len(bc_errors) == 0))

    # S6.4: Orphan detection
    orphan = LCTDocument("orphan", "orph", EntityType.HUMAN, parent_lct_id="p1",
                         birth_certificate=BirthCertificate("i", "o", ["w"], time.time(), EntityType.HUMAN))
    graph.add(orphan)
    orphans = graph.find_orphans()
    checks.append(("s6_orphan_detected", "orphan" in orphans))

    # ── S7: MRH Context Linking ──────────────────────────────────────────

    mrh_graph = LCTGraph()
    l1 = LCTDocument("l1", "e1", EntityType.HUMAN,
                     birth_certificate=BirthCertificate("i", "e1", ["w"], time.time(), EntityType.HUMAN))
    l2 = LCTDocument("l2", "e2", EntityType.HUMAN,
                     birth_certificate=BirthCertificate("i", "e2", ["w"], time.time(), EntityType.HUMAN))
    l3 = LCTDocument("l3", "e3", EntityType.HUMAN,
                     birth_certificate=BirthCertificate("i", "e3", ["w"], time.time(), EntityType.HUMAN))
    l1.child_lct_ids = ["l2"]
    l2.parent_lct_id = "l1"
    l2.child_lct_ids = ["l3"]
    l3.parent_lct_id = "l2"
    mrh_graph.add(l1)
    mrh_graph.add(l2)
    mrh_graph.add(l3)

    # S7.1: Self zone
    checks.append(("s7_self_zone", compute_mrh_zone(mrh_graph, "l1", "l1") == MRHZone.SELF))

    # S7.2: Direct zone (parent-child)
    checks.append(("s7_direct_zone", compute_mrh_zone(mrh_graph, "l1", "l2") == MRHZone.DIRECT))

    # S7.3: Indirect zone (2 hops)
    checks.append(("s7_indirect_zone", compute_mrh_zone(mrh_graph, "l1", "l3") == MRHZone.INDIRECT))

    # S7.4: Beyond zone (unreachable)
    l4 = LCTDocument("l4", "e4", EntityType.HUMAN,
                     birth_certificate=BirthCertificate("i", "e4", ["w"], time.time(), EntityType.HUMAN))
    mrh_graph.add(l4)
    checks.append(("s7_beyond_zone", compute_mrh_zone(mrh_graph, "l1", "l4") == MRHZone.BEYOND))

    # S7.5: MRH link adds connectivity
    link_mrh(l1, "l4", "witness")
    checks.append(("s7_mrh_link", compute_mrh_zone(mrh_graph, "l1", "l4") == MRHZone.DIRECT))

    # ── S8: Temporal Validity ────────────────────────────────────────────

    now = time.time()
    valid_lct = LCTDocument("v1", "e1", EntityType.HUMAN, state=LCTState.ACTIVE,
                           expires_at=now + 3600)
    expired_lct = LCTDocument("v2", "e2", EntityType.HUMAN, state=LCTState.ACTIVE,
                             expires_at=now - 100)
    suspended_lct = LCTDocument("v3", "e3", EntityType.HUMAN, state=LCTState.SUSPENDED)
    no_expiry = LCTDocument("v4", "e4", EntityType.HUMAN, state=LCTState.ACTIVE)

    # S8.1: Valid LCT
    ok, reason = check_validity_window(valid_lct, now)
    checks.append(("s8_valid", ok and reason == "valid"))

    # S8.2: Expired LCT
    ok, reason = check_validity_window(expired_lct, now)
    checks.append(("s8_expired", not ok and reason == "past_expiry"))

    # S8.3: Suspended LCT
    ok, reason = check_validity_window(suspended_lct, now)
    checks.append(("s8_suspended", not ok and reason == "suspended"))

    # S8.4: Remaining validity
    remaining = remaining_validity(valid_lct, now)
    checks.append(("s8_remaining", remaining is not None and remaining > 3500))

    # S8.5: No expiry → None
    checks.append(("s8_no_expiry", remaining_validity(no_expiry, now) is None))

    # S8.6: Past expiry → 0
    checks.append(("s8_past_zero", remaining_validity(expired_lct, now) == 0))

    # ── S9: LCT Migration ───────────────────────────────────────────────

    mig_mgr = LCTLifecycleManager()
    mig_lct = ceremony.create("orig_entity", EntityType.HUMAN, "admin", ["w1", "w2"])
    if mig_lct:
        mig_mgr.register(mig_lct)
        mig_mgr.activate(mig_lct.lct_id, "admin")
        migrator = LCTMigrator(mig_mgr)

        # S9.1: Transfer entity
        transferred = migrator.transfer_entity(mig_lct.lct_id, "new_entity", "admin", "ownership_change")
        checks.append(("s9_transfer", transferred and mig_lct.entity_id == "new_entity"))

        # S9.2: Version incremented
        checks.append(("s9_version_inc", mig_lct.version == 2))

        # S9.3: Migration history
        history = migrator.migration_history(mig_lct.lct_id)
        checks.append(("s9_history", len(history) == 1 and history[0].old_entity_id == "orig_entity"))

        # S9.4: Cannot transfer revoked LCT
        mig_mgr.revoke(mig_lct.lct_id, "test", "admin")
        checks.append(("s9_no_revoked_transfer", not migrator.transfer_entity(mig_lct.lct_id, "other", "admin", "test")))

    # ── S10: Batch Operations ────────────────────────────────────────────

    batch_ceremony = BirthCeremony(min_witnesses=1)
    entities = [
        ("batch_a", EntityType.HUMAN),
        ("batch_b", EntityType.AI),
        ("batch_c", EntityType.DEVICE),
    ]
    batch = batch_create(batch_ceremony, entities, "admin", ["w1"])

    # S10.1: Batch creation
    checks.append(("s10_batch_create", len(batch) == 3))

    # S10.2: Batch JSON-LD serialization
    jsonld_batch = batch_serialize(batch, "jsonld")
    checks.append(("s10_batch_jsonld", len(jsonld_batch) == 3))

    # S10.3: Batch compact serialization
    compact_batch = batch_serialize(batch, "compact")
    checks.append(("s10_batch_compact", len(compact_batch) == 3))

    # S10.4: Batch N-Triples
    nt_batch = batch_serialize(batch, "ntriples")
    checks.append(("s10_batch_ntriples", len(nt_batch) == 3))

    # ── S11: Performance ─────────────────────────────────────────────────

    import random
    rng = random.Random(42)

    # S11.1: Create 500 LCTs
    t0 = time.time()
    perf_ceremony = BirthCeremony(min_witnesses=1)
    perf_lcts = []
    for i in range(500):
        lct = perf_ceremony.create(f"entity_{i}", EntityType.HUMAN, "admin", ["w1"])
        if lct:
            perf_lcts.append(lct)
    elapsed = time.time() - t0
    checks.append(("s11_create_500", len(perf_lcts) == 500 and elapsed < 2.0))

    # S11.2: Serialize 500 to JSON-LD
    t0 = time.time()
    for lct in perf_lcts:
        to_jsonld(lct)
    elapsed = time.time() - t0
    checks.append(("s11_jsonld_500", elapsed < 2.0))

    # S11.3: Compact roundtrip 500
    t0 = time.time()
    for lct in perf_lcts:
        data = to_compact(lct)
        from_compact(data)
    elapsed = time.time() - t0
    checks.append(("s11_compact_500", elapsed < 2.0))

    # S11.4: State transitions at scale
    t0 = time.time()
    perf_mgr = LCTLifecycleManager()
    for lct in perf_lcts[:100]:
        perf_mgr.register(lct)
        perf_mgr.activate(lct.lct_id, "admin")
        perf_mgr.suspend(lct.lct_id, "test", "admin")
        perf_mgr.reactivate(lct.lct_id, "admin")
    elapsed = time.time() - t0
    checks.append(("s11_transitions_300", elapsed < 2.0))

    # S11.5: Graph validation at scale
    t0 = time.time()
    perf_graph = LCTGraph()
    for lct in perf_lcts[:200]:
        perf_graph.add(lct)
    errors = perf_graph.validate_references()
    bc_errors = perf_graph.validate_birth_certs()
    elapsed = time.time() - t0
    checks.append(("s11_validate_200", elapsed < 2.0))

    # ── Print Results ────────────────────────────────────────────────────
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"\n{'='*60}")
    print(f"  LCT Document Lifecycle — {passed}/{total} checks passed")
    print(f"{'='*60}")

    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    if passed < total:
        print(f"\n  FAILURES:")
        for name, ok in checks:
            if not ok:
                print(f"    ✗ {name}")

    print()
    return passed, total


if __name__ == "__main__":
    run_checks()
