"""
Key Management & Ceremony Protocols — Session 22 Track 5
========================================================
Key lifecycle, ceremony workflows, multi-party key generation,
HSM abstraction, rotation policies, and revocation chains.

Sections:
  S1:  Key Types & Lifecycle
  S2:  Key Derivation
  S3:  Key Rotation Protocol
  S4:  Multi-Party Key Generation
  S5:  HSM Abstraction Layer
  S6:  Ceremony Workflow Engine
  S7:  Revocation Chain
  S8:  Key Escrow & Recovery
  S9:  Cross-Federation Key Bridge
  S10: Key Policy Engine
  S11: Performance
"""

from __future__ import annotations
import enum
import hashlib
import hmac
import math
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ── S1: Key Types & Lifecycle ─────────────────────────────────────────

class KeyType(enum.Enum):
    IDENTITY = "identity"         # Long-lived entity identity key
    SIGNING = "signing"           # Short-lived signing key
    ENCRYPTION = "encryption"     # Short-lived encryption key
    DELEGATION = "delegation"     # Scoped delegation key
    SESSION = "session"           # Ephemeral session key
    ATTESTATION = "attestation"   # Hardware attestation key


class KeyState(enum.Enum):
    PENDING = "pending"       # Generated but not activated
    ACTIVE = "active"         # Current active key
    OVERLAP = "overlap"       # Old key still valid during rotation
    SUSPENDED = "suspended"   # Temporarily disabled
    REVOKED = "revoked"       # Permanently revoked
    EXPIRED = "expired"       # Past validity window


KEY_TRANSITIONS: Dict[KeyState, Set[KeyState]] = {
    KeyState.PENDING: {KeyState.ACTIVE, KeyState.REVOKED},
    KeyState.ACTIVE: {KeyState.OVERLAP, KeyState.SUSPENDED, KeyState.REVOKED, KeyState.EXPIRED},
    KeyState.OVERLAP: {KeyState.EXPIRED, KeyState.REVOKED},
    KeyState.SUSPENDED: {KeyState.ACTIVE, KeyState.REVOKED},
    KeyState.REVOKED: set(),   # Terminal
    KeyState.EXPIRED: set(),   # Terminal
}


@dataclass
class KeyMaterial:
    key_id: str
    key_type: KeyType
    state: KeyState = KeyState.PENDING
    version: int = 1
    created_at: float = 0.0
    activated_at: Optional[float] = None
    expires_at: Optional[float] = None
    revoked_at: Optional[float] = None
    public_key: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    private_key_hash: str = ""  # Never store actual private key
    parent_key_id: Optional[str] = None
    entity_id: str = ""
    scope: Optional[str] = None
    state_history: List[Tuple[float, KeyState, KeyState]] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.private_key_hash:
            self.private_key_hash = hashlib.sha256(
                secrets.token_bytes(32)
            ).hexdigest()

    def transition(self, new_state: KeyState, now: Optional[float] = None) -> bool:
        now = now or time.time()
        if new_state not in KEY_TRANSITIONS.get(self.state, set()):
            return False
        old = self.state
        self.state_history.append((now, old, new_state))
        self.state = new_state
        if new_state == KeyState.ACTIVE:
            self.activated_at = now
        elif new_state == KeyState.REVOKED:
            self.revoked_at = now
        return True

    def is_valid(self, now: Optional[float] = None) -> bool:
        now = now or time.time()
        if self.state not in (KeyState.ACTIVE, KeyState.OVERLAP):
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return True


class KeyStore:
    """Manages key lifecycle across entities."""

    def __init__(self):
        self.keys: Dict[str, KeyMaterial] = {}
        self.entity_keys: Dict[str, List[str]] = {}  # entity_id → [key_ids]

    def generate(self, entity_id: str, key_type: KeyType,
                 validity_days: int = 365, scope: Optional[str] = None,
                 parent_key_id: Optional[str] = None) -> KeyMaterial:
        now = time.time()
        key = KeyMaterial(
            key_id=secrets.token_hex(16),
            key_type=key_type,
            entity_id=entity_id,
            scope=scope,
            parent_key_id=parent_key_id,
            created_at=now,
            expires_at=now + validity_days * 86400 if validity_days > 0 else None,
        )
        self.keys[key.key_id] = key
        self.entity_keys.setdefault(entity_id, []).append(key.key_id)
        return key

    def activate(self, key_id: str) -> bool:
        key = self.keys.get(key_id)
        if not key:
            return False
        return key.transition(KeyState.ACTIVE)

    def revoke(self, key_id: str, cascade: bool = False) -> List[str]:
        """Revoke a key, optionally cascading to child keys."""
        revoked = []
        key = self.keys.get(key_id)
        if not key:
            return revoked
        if key.transition(KeyState.REVOKED):
            revoked.append(key_id)

        if cascade:
            for kid, k in self.keys.items():
                if k.parent_key_id == key_id and k.state not in (
                    KeyState.REVOKED, KeyState.EXPIRED
                ):
                    if k.transition(KeyState.REVOKED):
                        revoked.append(kid)
        return revoked

    def active_keys(self, entity_id: str) -> List[KeyMaterial]:
        key_ids = self.entity_keys.get(entity_id, [])
        return [self.keys[kid] for kid in key_ids
                if self.keys[kid].is_valid()]

    def key_by_type(self, entity_id: str,
                    key_type: KeyType) -> Optional[KeyMaterial]:
        for kid in self.entity_keys.get(entity_id, []):
            key = self.keys[kid]
            if key.key_type == key_type and key.is_valid():
                return key
        return None


# ── S2: Key Derivation ───────────────────────────────────────────────

class KeyDerivation:
    """HKDF-based key derivation with identity-binding salt."""

    @staticmethod
    def derive(master_key: bytes, context: str, entity_id: str,
               length: int = 32) -> bytes:
        """Derive a key using HMAC-based KDF with identity binding."""
        salt = hashlib.sha256(f"web4:{entity_id}".encode()).digest()
        prk = hmac.new(salt, master_key, hashlib.sha256).digest()
        info = f"web4-key:{context}:{entity_id}".encode()
        # Single-round HKDF-Expand
        okm = hmac.new(prk, info + b'\x01', hashlib.sha256).digest()
        return okm[:length]

    @staticmethod
    def derive_session_key(initiator_nonce: bytes, responder_nonce: bytes,
                           shared_secret: bytes) -> bytes:
        """Derive session key from handshake nonces and shared secret."""
        material = initiator_nonce + responder_nonce + shared_secret
        return hashlib.sha256(material).digest()

    @staticmethod
    def derive_pairwise_id(entity_a: str, entity_b: str,
                           session_salt: bytes) -> str:
        """Session-salted pairwise ID (different per session for privacy)."""
        ids = sorted([entity_a, entity_b])
        material = f"{ids[0]}:{ids[1]}".encode() + session_salt
        return "w4id:pair:" + hashlib.sha256(material).hexdigest()[:16]


# ── S3: Key Rotation Protocol ────────────────────────────────────────

@dataclass
class RotationPolicy:
    max_age_days: int = 90
    overlap_hours: int = 24
    require_quorum: bool = False
    quorum_size: int = 3
    quorum_approvals: int = 0


@dataclass
class RotationEvent:
    old_key_id: str
    new_key_id: str
    timestamp: float
    approvers: List[str]
    overlap_until: float


class KeyRotator:
    """Manages key rotation with overlap period."""

    def __init__(self, store: KeyStore):
        self.store = store
        self.events: List[RotationEvent] = []

    def needs_rotation(self, key: KeyMaterial, policy: RotationPolicy,
                       now: Optional[float] = None) -> bool:
        now = now or time.time()
        if not key.activated_at:
            return False
        age_days = (now - key.activated_at) / 86400
        return age_days >= policy.max_age_days

    def rotate(self, old_key: KeyMaterial, policy: RotationPolicy,
               approvers: Optional[List[str]] = None,
               now: Optional[float] = None) -> Optional[KeyMaterial]:
        now = now or time.time()
        approvers = approvers or []

        if policy.require_quorum and len(approvers) < policy.quorum_size:
            return None

        # Generate new key
        new_key = self.store.generate(
            old_key.entity_id, old_key.key_type,
            parent_key_id=old_key.key_id, scope=old_key.scope
        )
        new_key.version = old_key.version + 1

        # Activate new key
        self.store.activate(new_key.key_id)

        # Move old key to overlap
        old_key.transition(KeyState.OVERLAP, now)
        overlap_until = now + policy.overlap_hours * 3600

        event = RotationEvent(
            old_key.key_id, new_key.key_id, now,
            approvers, overlap_until
        )
        self.events.append(event)
        return new_key

    def expire_overlaps(self, now: Optional[float] = None):
        now = now or time.time()
        for event in self.events:
            if now >= event.overlap_until:
                old = self.store.keys.get(event.old_key_id)
                if old and old.state == KeyState.OVERLAP:
                    old.transition(KeyState.EXPIRED, now)


# ── S4: Multi-Party Key Generation ───────────────────────────────────

@dataclass
class KeyShare:
    share_id: str
    participant_id: str
    share_value: bytes
    commitment: str  # Hash of share for verification


class MultiPartyKeyGen:
    """Distributed key generation with Shamir-style shares."""

    def __init__(self, threshold: int, total_shares: int):
        self.threshold = threshold
        self.total_shares = total_shares
        self.shares: Dict[str, KeyShare] = {}
        self.commitments: Dict[str, str] = {}

    def generate_shares(self, master_secret: bytes) -> List[KeyShare]:
        """Split secret into shares (simplified XOR-based for reference)."""
        shares = []
        # Generate random shares for all but last
        accumulated = bytes(len(master_secret))
        for i in range(self.total_shares - 1):
            share_value = secrets.token_bytes(len(master_secret))
            accumulated = bytes(a ^ b for a, b in zip(accumulated, share_value))
            share = KeyShare(
                share_id=f"share_{i}",
                participant_id=f"participant_{i}",
                share_value=share_value,
                commitment=hashlib.sha256(share_value).hexdigest(),
            )
            shares.append(share)
            self.shares[share.share_id] = share
            self.commitments[share.share_id] = share.commitment

        # Last share is XOR of all others with master secret
        final_value = bytes(a ^ b for a, b in zip(accumulated, master_secret))
        final_share = KeyShare(
            share_id=f"share_{self.total_shares - 1}",
            participant_id=f"participant_{self.total_shares - 1}",
            share_value=final_value,
            commitment=hashlib.sha256(final_value).hexdigest(),
        )
        shares.append(final_share)
        self.shares[final_share.share_id] = final_share
        self.commitments[final_share.share_id] = final_share.commitment
        return shares

    def verify_share(self, share: KeyShare) -> bool:
        expected = hashlib.sha256(share.share_value).hexdigest()
        return hmac.compare_digest(share.commitment, expected)

    def reconstruct(self, shares: List[KeyShare]) -> Optional[bytes]:
        """Reconstruct secret from all shares (simplified XOR)."""
        if len(shares) < self.total_shares:
            return None

        # Verify all commitments
        for share in shares:
            if not self.verify_share(share):
                return None

        result = bytes(len(shares[0].share_value))
        for share in shares:
            result = bytes(a ^ b for a, b in zip(result, share.share_value))
        return result


# ── S5: HSM Abstraction Layer ────────────────────────────────────────

class HSMType(enum.Enum):
    TPM2 = "tpm2"
    SECURE_ENCLAVE = "secure_enclave"
    PKCS11 = "pkcs11"
    SOFTWARE = "software"  # Software-only fallback


@dataclass
class HSMCapabilities:
    hsm_type: HSMType
    supports_ecdsa_p256: bool = True
    supports_ecdsa_p384: bool = False
    supports_ed25519: bool = False
    supports_key_wrapping: bool = True
    max_key_size: int = 384
    persistent_storage: bool = True
    attestation_support: bool = False


@dataclass
class HSMOperation:
    op_type: str  # "sign", "verify", "encrypt", "decrypt", "generate", "wrap"
    key_id: str
    data: bytes
    result: Optional[bytes] = None
    success: bool = False
    latency_ms: float = 0.0


class HSMAdapter:
    """Abstract HSM interface with software fallback."""

    def __init__(self, hsm_type: HSMType = HSMType.SOFTWARE):
        self.hsm_type = hsm_type
        self.capabilities = self._default_capabilities(hsm_type)
        self.stored_keys: Dict[str, bytes] = {}
        self.operations: List[HSMOperation] = []

    def _default_capabilities(self, hsm_type: HSMType) -> HSMCapabilities:
        caps = {
            HSMType.TPM2: HSMCapabilities(
                HSMType.TPM2, True, False, False, True, 256, True, True
            ),
            HSMType.SECURE_ENCLAVE: HSMCapabilities(
                HSMType.SECURE_ENCLAVE, True, True, False, True, 384, True, True
            ),
            HSMType.PKCS11: HSMCapabilities(
                HSMType.PKCS11, True, True, True, True, 512, True, False
            ),
            HSMType.SOFTWARE: HSMCapabilities(
                HSMType.SOFTWARE, True, True, True, True, 4096, False, False
            ),
        }
        return caps[hsm_type]

    def generate_key(self, key_id: str) -> HSMOperation:
        t0 = time.time()
        key = secrets.token_bytes(32)
        self.stored_keys[key_id] = key
        op = HSMOperation("generate", key_id, b"", key, True,
                          (time.time() - t0) * 1000)
        self.operations.append(op)
        return op

    def sign(self, key_id: str, data: bytes) -> HSMOperation:
        t0 = time.time()
        key = self.stored_keys.get(key_id)
        if not key:
            op = HSMOperation("sign", key_id, data, None, False, 0)
            self.operations.append(op)
            return op
        sig = hmac.new(key, data, hashlib.sha256).digest()
        op = HSMOperation("sign", key_id, data, sig, True,
                          (time.time() - t0) * 1000)
        self.operations.append(op)
        return op

    def verify(self, key_id: str, data: bytes,
               signature: bytes) -> HSMOperation:
        t0 = time.time()
        key = self.stored_keys.get(key_id)
        if not key:
            op = HSMOperation("verify", key_id, data, None, False, 0)
            self.operations.append(op)
            return op
        expected = hmac.new(key, data, hashlib.sha256).digest()
        ok = hmac.compare_digest(signature, expected)
        op = HSMOperation("verify", key_id, data,
                          b'\x01' if ok else b'\x00', ok,
                          (time.time() - t0) * 1000)
        self.operations.append(op)
        return op


# ── S6: Ceremony Workflow Engine ─────────────────────────────────────

class CeremonyType(enum.Enum):
    KEY_GENERATION = "key_generation"
    KEY_ROTATION = "key_rotation"
    KEY_RECOVERY = "key_recovery"
    ENTITY_ONBOARDING = "entity_onboarding"
    ENTITY_REVOCATION = "entity_revocation"


class CeremonyState(enum.Enum):
    INITIATED = "initiated"
    WITNESSING = "witnessing"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CeremonyStep:
    step_id: int
    description: str
    required_witnesses: int
    actual_witnesses: List[str] = field(default_factory=list)
    completed: bool = False

    @property
    def has_quorum(self) -> bool:
        return len(self.actual_witnesses) >= self.required_witnesses


@dataclass
class Ceremony:
    ceremony_id: str
    ceremony_type: CeremonyType
    entity_id: str
    state: CeremonyState = CeremonyState.INITIATED
    steps: List[CeremonyStep] = field(default_factory=list)
    initiated_by: str = ""
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    state_history: List[Tuple[float, CeremonyState]] = field(default_factory=list)

    def _transition(self, new_state: CeremonyState):
        self.state_history.append((time.time(), new_state))
        self.state = new_state


class CeremonyEngine:
    """Orchestrates multi-step ceremony workflows."""

    def __init__(self):
        self.ceremonies: Dict[str, Ceremony] = {}

    def create_ceremony(self, ceremony_type: CeremonyType,
                        entity_id: str, initiated_by: str) -> Ceremony:
        ceremony = Ceremony(
            ceremony_id=secrets.token_hex(8),
            ceremony_type=ceremony_type,
            entity_id=entity_id,
            initiated_by=initiated_by,
        )

        # Define steps based on ceremony type
        if ceremony_type == CeremonyType.KEY_GENERATION:
            ceremony.steps = [
                CeremonyStep(1, "Verify entity identity", 1),
                CeremonyStep(2, "Generate key material", 1),
                CeremonyStep(3, "Witness key activation", 2),
            ]
        elif ceremony_type == CeremonyType.KEY_ROTATION:
            ceremony.steps = [
                CeremonyStep(1, "Verify current key ownership", 1),
                CeremonyStep(2, "Generate new key", 1),
                CeremonyStep(3, "Witness rotation", 2),
                CeremonyStep(4, "Activate new key", 1),
            ]
        elif ceremony_type == CeremonyType.KEY_RECOVERY:
            ceremony.steps = [
                CeremonyStep(1, "Verify identity via witnesses", 3),
                CeremonyStep(2, "Collect key shares", 2),
                CeremonyStep(3, "Reconstruct key", 1),
                CeremonyStep(4, "Activate recovered key", 2),
            ]
        elif ceremony_type == CeremonyType.ENTITY_ONBOARDING:
            ceremony.steps = [
                CeremonyStep(1, "Generate identity key", 1),
                CeremonyStep(2, "Bind to hardware", 1),
                CeremonyStep(3, "Witness birth", 2),
                CeremonyStep(4, "Activate entity", 1),
            ]
        elif ceremony_type == CeremonyType.ENTITY_REVOCATION:
            ceremony.steps = [
                CeremonyStep(1, "Submit revocation request", 1),
                CeremonyStep(2, "Witness approval", 3),
                CeremonyStep(3, "Execute revocation cascade", 1),
            ]

        self.ceremonies[ceremony.ceremony_id] = ceremony
        return ceremony

    def witness_step(self, ceremony_id: str, step_id: int,
                     witness_id: str) -> bool:
        ceremony = self.ceremonies.get(ceremony_id)
        if not ceremony or ceremony.state in (
            CeremonyState.COMPLETED, CeremonyState.FAILED,
            CeremonyState.CANCELLED
        ):
            return False

        for step in ceremony.steps:
            if step.step_id == step_id:
                if witness_id not in step.actual_witnesses:
                    step.actual_witnesses.append(witness_id)
                return True
        return False

    def advance(self, ceremony_id: str) -> CeremonyState:
        ceremony = self.ceremonies.get(ceremony_id)
        if not ceremony:
            return CeremonyState.FAILED

        # Check all steps up to current
        for step in ceremony.steps:
            if not step.completed:
                if step.has_quorum:
                    step.completed = True
                    ceremony._transition(CeremonyState.WITNESSING)
                else:
                    return ceremony.state

        # All steps completed
        ceremony._transition(CeremonyState.COMPLETED)
        ceremony.completed_at = time.time()
        return ceremony.state

    def cancel(self, ceremony_id: str) -> bool:
        ceremony = self.ceremonies.get(ceremony_id)
        if ceremony and ceremony.state not in (
            CeremonyState.COMPLETED, CeremonyState.CANCELLED
        ):
            ceremony._transition(CeremonyState.CANCELLED)
            return True
        return False


# ── S7: Revocation Chain ─────────────────────────────────────────────

@dataclass
class RevocationEntry:
    key_id: str
    entity_id: str
    reason: str
    revoked_at: float
    revoked_by: str
    cascade_from: Optional[str] = None
    content_hash: str = ""
    prev_hash: str = ""

    def compute_hash(self) -> str:
        data = f"{self.key_id}:{self.entity_id}:{self.revoked_at}:{self.reason}"
        return hashlib.sha256(data.encode()).hexdigest()


class RevocationChain:
    """Hash-chained revocation list."""

    def __init__(self):
        self.entries: List[RevocationEntry] = []
        self.revoked_keys: Set[str] = set()
        self.prev_hash = "genesis"

    def revoke(self, key_id: str, entity_id: str, reason: str,
               revoked_by: str,
               cascade_from: Optional[str] = None) -> RevocationEntry:
        entry = RevocationEntry(
            key_id=key_id, entity_id=entity_id,
            reason=reason, revoked_at=time.time(),
            revoked_by=revoked_by, cascade_from=cascade_from,
        )
        entry.content_hash = entry.compute_hash()
        entry.prev_hash = self.prev_hash
        self.prev_hash = entry.content_hash
        self.entries.append(entry)
        self.revoked_keys.add(key_id)
        return entry

    def is_revoked(self, key_id: str) -> bool:
        return key_id in self.revoked_keys

    def verify_chain(self) -> bool:
        prev = "genesis"
        for entry in self.entries:
            if entry.prev_hash != prev:
                return False
            if entry.content_hash != entry.compute_hash():
                return False
            prev = entry.content_hash
        return True

    def cascade_tree(self, root_key_id: str) -> List[str]:
        """Find all keys revoked as a cascade from root."""
        return [e.key_id for e in self.entries
                if e.cascade_from == root_key_id]


# ── S8: Key Escrow & Recovery ────────────────────────────────────────

@dataclass
class EscrowEntry:
    entity_id: str
    custodian_id: str
    encrypted_share: bytes
    share_hash: str
    created_at: float = field(default_factory=time.time)


class KeyEscrow:
    """Manages key escrow with designated custodians."""

    def __init__(self, required_custodians: int = 3):
        self.required_custodians = required_custodians
        self.entries: Dict[str, List[EscrowEntry]] = {}  # entity_id → entries

    def deposit(self, entity_id: str, custodian_id: str,
                share: bytes) -> EscrowEntry:
        # "Encrypt" share for custodian (simplified: XOR with custodian key)
        custodian_key = hashlib.sha256(
            f"custodian:{custodian_id}".encode()
        ).digest()
        encrypted = bytes(a ^ b for a, b in zip(share, custodian_key[:len(share)]))

        entry = EscrowEntry(
            entity_id=entity_id,
            custodian_id=custodian_id,
            encrypted_share=encrypted,
            share_hash=hashlib.sha256(share).hexdigest(),
        )
        self.entries.setdefault(entity_id, []).append(entry)
        return entry

    def recover(self, entity_id: str,
                custodian_approvals: Dict[str, bytes]) -> Optional[List[bytes]]:
        """Recover shares from approved custodians."""
        entries = self.entries.get(entity_id, [])
        if len(custodian_approvals) < self.required_custodians:
            return None

        recovered = []
        for entry in entries:
            if entry.custodian_id in custodian_approvals:
                custodian_key = hashlib.sha256(
                    f"custodian:{entry.custodian_id}".encode()
                ).digest()
                share = bytes(
                    a ^ b for a, b in
                    zip(entry.encrypted_share, custodian_key[:len(entry.encrypted_share)])
                )
                # Verify share
                if hashlib.sha256(share).hexdigest() == entry.share_hash:
                    recovered.append(share)
        return recovered if len(recovered) >= self.required_custodians else None

    def custodian_count(self, entity_id: str) -> int:
        return len(self.entries.get(entity_id, []))


# ── S9: Cross-Federation Key Bridge ──────────────────────────────────

@dataclass
class KeyBridge:
    federation_a: str
    federation_b: str
    bridge_key_id: str
    trust_level: float
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    active: bool = True

    def is_valid(self, now: Optional[float] = None) -> bool:
        now = now or time.time()
        return self.active and (self.expires_at == 0 or now < self.expires_at)


class FederationKeyBridge:
    """Manages cryptographic bridges between federations."""

    def __init__(self):
        self.bridges: Dict[str, KeyBridge] = {}

    def create_bridge(self, fed_a: str, fed_b: str,
                      trust_level: float,
                      validity_days: int = 30) -> KeyBridge:
        now = time.time()
        bridge = KeyBridge(
            federation_a=fed_a,
            federation_b=fed_b,
            bridge_key_id=secrets.token_hex(16),
            trust_level=trust_level,
            created_at=now,
            expires_at=now + validity_days * 86400,
        )
        self.bridges[bridge.bridge_key_id] = bridge
        return bridge

    def find_bridges(self, fed_a: str, fed_b: str) -> List[KeyBridge]:
        now = time.time()
        return [b for b in self.bridges.values()
                if ((b.federation_a == fed_a and b.federation_b == fed_b) or
                    (b.federation_a == fed_b and b.federation_b == fed_a))
                and b.is_valid(now)]

    def transitive_trust(self, fed_a: str, fed_b: str) -> float:
        """Direct bridge trust, multiplicative."""
        bridges = self.find_bridges(fed_a, fed_b)
        if not bridges:
            return 0.0
        return max(b.trust_level for b in bridges)

    def revoke_bridge(self, bridge_key_id: str) -> bool:
        bridge = self.bridges.get(bridge_key_id)
        if bridge:
            bridge.active = False
            return True
        return False


# ── S10: Key Policy Engine ───────────────────────────────────────────

@dataclass
class KeyPolicy:
    name: str
    key_type: KeyType
    max_validity_days: int
    min_key_bits: int
    rotation_required: bool
    max_rotation_age_days: int = 90
    require_hsm: bool = False
    require_witnesses: int = 0
    allow_export: bool = False


class KeyPolicyEngine:
    """Validates key operations against policies."""

    def __init__(self):
        self.policies: Dict[KeyType, KeyPolicy] = {}

    def register_policy(self, policy: KeyPolicy):
        self.policies[policy.key_type] = policy

    def validate_key(self, key: KeyMaterial,
                     now: Optional[float] = None) -> List[str]:
        now = now or time.time()
        violations = []
        policy = self.policies.get(key.key_type)
        if not policy:
            return violations

        # Check validity period
        if key.expires_at:
            validity_days = (key.expires_at - key.created_at) / 86400
            if validity_days > policy.max_validity_days:
                violations.append(
                    f"Validity {validity_days:.0f}d > max {policy.max_validity_days}d"
                )

        # Check rotation age
        if policy.rotation_required and key.activated_at:
            age_days = (now - key.activated_at) / 86400
            if age_days > policy.max_rotation_age_days:
                violations.append(
                    f"Key age {age_days:.0f}d > max rotation age {policy.max_rotation_age_days}d"
                )

        # Check key size (using public key length as proxy)
        key_bits = len(key.public_key) * 8
        if key_bits < policy.min_key_bits:
            violations.append(
                f"Key size {key_bits} bits < min {policy.min_key_bits} bits"
            )

        return violations

    def check_operation(self, key: KeyMaterial,
                        operation: str) -> Tuple[bool, List[str]]:
        """Check if operation is allowed by policy."""
        violations = self.validate_key(key)
        policy = self.policies.get(key.key_type)

        if not key.is_valid():
            violations.append("Key is not in valid state")

        if operation == "export" and policy and not policy.allow_export:
            violations.append("Key export not allowed by policy")

        return len(violations) == 0, violations


# ── S11: Performance ──────────────────────────────────────────────────

def run_checks():
    checks: List[Tuple[str, bool]] = []

    # ── S1: Key Types & Lifecycle ─────────────────────────────────────
    store = KeyStore()
    key = store.generate("entity_1", KeyType.IDENTITY)
    checks.append(("s1_key_generated", key.key_id in store.keys))
    checks.append(("s1_pending", key.state == KeyState.PENDING))

    store.activate(key.key_id)
    checks.append(("s1_active", key.state == KeyState.ACTIVE))
    checks.append(("s1_valid", key.is_valid()))

    # Invalid transition
    checks.append(("s1_no_pending", not key.transition(KeyState.PENDING)))

    # Revoke with cascade
    child = store.generate("entity_1", KeyType.SIGNING, parent_key_id=key.key_id)
    store.activate(child.key_id)
    revoked = store.revoke(key.key_id, cascade=True)
    checks.append(("s1_cascade_revoke", len(revoked) == 2))
    checks.append(("s1_child_revoked", child.state == KeyState.REVOKED))

    # Active keys query
    key2 = store.generate("entity_1", KeyType.ENCRYPTION)
    store.activate(key2.key_id)
    active = store.active_keys("entity_1")
    checks.append(("s1_active_keys", len(active) == 1))  # Only key2 active

    # ── S2: Key Derivation ────────────────────────────────────────────
    master = secrets.token_bytes(32)
    dk1 = KeyDerivation.derive(master, "signing", "entity_1")
    dk2 = KeyDerivation.derive(master, "signing", "entity_2")
    checks.append(("s2_different_entities", dk1 != dk2))

    dk3 = KeyDerivation.derive(master, "signing", "entity_1")
    checks.append(("s2_deterministic", dk1 == dk3))

    dk4 = KeyDerivation.derive(master, "encryption", "entity_1")
    checks.append(("s2_different_context", dk1 != dk4))

    # Session key derivation
    sk = KeyDerivation.derive_session_key(
        secrets.token_bytes(32), secrets.token_bytes(32), master
    )
    checks.append(("s2_session_key", len(sk) == 32))

    # Pairwise ID
    salt1 = secrets.token_bytes(16)
    salt2 = secrets.token_bytes(16)
    pid1 = KeyDerivation.derive_pairwise_id("a", "b", salt1)
    pid2 = KeyDerivation.derive_pairwise_id("a", "b", salt2)
    checks.append(("s2_pairwise_salted", pid1 != pid2))
    # Order-independent
    pid3 = KeyDerivation.derive_pairwise_id("b", "a", salt1)
    checks.append(("s2_pairwise_symmetric", pid1 == pid3))

    # ── S3: Key Rotation ──────────────────────────────────────────────
    rot_store = KeyStore()
    rot_key = rot_store.generate("entity_rot", KeyType.SIGNING)
    rot_store.activate(rot_key.key_id)
    rot_key.activated_at = time.time() - 100 * 86400  # 100 days ago

    rotator = KeyRotator(rot_store)
    policy = RotationPolicy(max_age_days=90)

    checks.append(("s3_needs_rotation", rotator.needs_rotation(rot_key, policy)))

    new_key = rotator.rotate(rot_key, policy)
    checks.append(("s3_rotated", new_key is not None))
    checks.append(("s3_new_active", new_key.state == KeyState.ACTIVE))
    checks.append(("s3_old_overlap", rot_key.state == KeyState.OVERLAP))
    checks.append(("s3_version_inc", new_key.version == rot_key.version + 1))
    checks.append(("s3_both_valid", rot_key.is_valid() and new_key.is_valid()))

    # Quorum-required rotation
    quorum_policy = RotationPolicy(max_age_days=90, require_quorum=True, quorum_size=3)
    q_key = rot_store.generate("entity_q", KeyType.IDENTITY)
    rot_store.activate(q_key.key_id)
    q_key.activated_at = time.time() - 100 * 86400
    no_quorum = rotator.rotate(q_key, quorum_policy, approvers=["w1", "w2"])
    checks.append(("s3_quorum_denied", no_quorum is None))

    quorum_ok = rotator.rotate(q_key, quorum_policy, approvers=["w1", "w2", "w3"])
    checks.append(("s3_quorum_accepted", quorum_ok is not None))

    # ── S4: Multi-Party Key Generation ────────────────────────────────
    mpkg = MultiPartyKeyGen(threshold=3, total_shares=5)
    secret = secrets.token_bytes(32)
    shares = mpkg.generate_shares(secret)
    checks.append(("s4_shares_count", len(shares) == 5))

    # Verify all shares
    all_valid = all(mpkg.verify_share(s) for s in shares)
    checks.append(("s4_shares_valid", all_valid))

    # Reconstruct
    recovered = mpkg.reconstruct(shares)
    checks.append(("s4_reconstruct", recovered == secret))

    # Tampered share fails
    tampered = KeyShare(shares[0].share_id, shares[0].participant_id,
                        secrets.token_bytes(32), shares[0].commitment)
    checks.append(("s4_tamper_detected", not mpkg.verify_share(tampered)))

    # ── S5: HSM Abstraction ───────────────────────────────────────────
    hsm = HSMAdapter(HSMType.SOFTWARE)
    gen_op = hsm.generate_key("test_key")
    checks.append(("s5_key_generated", gen_op.success))

    sign_op = hsm.sign("test_key", b"hello web4")
    checks.append(("s5_signed", sign_op.success and sign_op.result is not None))

    verify_op = hsm.verify("test_key", b"hello web4", sign_op.result)
    checks.append(("s5_verified", verify_op.success))

    # Bad signature
    bad_verify = hsm.verify("test_key", b"hello web4", b"bad_sig" * 4)
    checks.append(("s5_bad_sig_fails", not bad_verify.success))

    # Missing key
    missing = hsm.sign("nonexistent", b"data")
    checks.append(("s5_missing_key", not missing.success))

    # HSM types
    tpm = HSMAdapter(HSMType.TPM2)
    checks.append(("s5_tpm_attestation", tpm.capabilities.attestation_support))

    # ── S6: Ceremony Workflow ─────────────────────────────────────────
    engine = CeremonyEngine()
    ceremony = engine.create_ceremony(
        CeremonyType.KEY_GENERATION, "entity_c", "admin"
    )
    checks.append(("s6_ceremony_created", ceremony.ceremony_id in engine.ceremonies))
    checks.append(("s6_has_steps", len(ceremony.steps) == 3))

    # Witness step 1
    engine.witness_step(ceremony.ceremony_id, 1, "witness_a")
    engine.advance(ceremony.ceremony_id)
    checks.append(("s6_step1_done", ceremony.steps[0].completed))

    # Witness step 2
    engine.witness_step(ceremony.ceremony_id, 2, "witness_a")
    engine.advance(ceremony.ceremony_id)

    # Step 3 needs 2 witnesses
    engine.witness_step(ceremony.ceremony_id, 3, "witness_a")
    engine.advance(ceremony.ceremony_id)
    checks.append(("s6_step3_not_done", not ceremony.steps[2].completed))

    engine.witness_step(ceremony.ceremony_id, 3, "witness_b")
    state = engine.advance(ceremony.ceremony_id)
    checks.append(("s6_completed", state == CeremonyState.COMPLETED))

    # Cancel ceremony
    cancel_c = engine.create_ceremony(CeremonyType.ENTITY_REVOCATION, "x", "a")
    checks.append(("s6_cancel", engine.cancel(cancel_c.ceremony_id)))

    # ── S7: Revocation Chain ──────────────────────────────────────────
    chain = RevocationChain()
    chain.revoke("key_1", "entity_1", "compromise", "admin")
    chain.revoke("key_2", "entity_1", "cascade", "admin", cascade_from="key_1")

    checks.append(("s7_revoked", chain.is_revoked("key_1")))
    checks.append(("s7_cascade", chain.is_revoked("key_2")))
    checks.append(("s7_chain_valid", chain.verify_chain()))
    checks.append(("s7_cascade_tree", len(chain.cascade_tree("key_1")) == 1))

    # Not revoked
    checks.append(("s7_not_revoked", not chain.is_revoked("key_3")))

    # ── S8: Key Escrow ────────────────────────────────────────────────
    escrow = KeyEscrow(required_custodians=3)
    share_data = [secrets.token_bytes(32) for _ in range(4)]

    for i, share in enumerate(share_data):
        escrow.deposit("entity_e", f"custodian_{i}", share)

    checks.append(("s8_deposited", escrow.custodian_count("entity_e") == 4))

    # Recovery with enough custodians
    approvals = {f"custodian_{i}": b"approved" for i in range(3)}
    recovered_shares = escrow.recover("entity_e", approvals)
    checks.append(("s8_recovered", recovered_shares is not None and len(recovered_shares) >= 3))

    # Recovery with too few
    few = {"custodian_0": b"approved"}
    checks.append(("s8_too_few", escrow.recover("entity_e", few) is None))

    # ── S9: Cross-Federation Key Bridge ───────────────────────────────
    bridge_mgr = FederationKeyBridge()
    bridge = bridge_mgr.create_bridge("fed_a", "fed_b", trust_level=0.8)
    checks.append(("s9_bridge_created", bridge.bridge_key_id in bridge_mgr.bridges))

    bridges = bridge_mgr.find_bridges("fed_a", "fed_b")
    checks.append(("s9_found", len(bridges) == 1))

    # Symmetric lookup
    bridges_rev = bridge_mgr.find_bridges("fed_b", "fed_a")
    checks.append(("s9_symmetric", len(bridges_rev) == 1))

    trust = bridge_mgr.transitive_trust("fed_a", "fed_b")
    checks.append(("s9_trust", abs(trust - 0.8) < 0.01))

    # Revoke bridge
    bridge_mgr.revoke_bridge(bridge.bridge_key_id)
    checks.append(("s9_revoked", bridge_mgr.transitive_trust("fed_a", "fed_b") == 0.0))

    # ── S10: Key Policy ───────────────────────────────────────────────
    policy_engine = KeyPolicyEngine()
    policy_engine.register_policy(KeyPolicy(
        "identity_policy", KeyType.IDENTITY,
        max_validity_days=365, min_key_bits=256,
        rotation_required=True, max_rotation_age_days=90,
    ))

    # Valid key
    valid_key = store.generate("entity_p", KeyType.IDENTITY)
    store.activate(valid_key.key_id)
    violations = policy_engine.validate_key(valid_key)
    checks.append(("s10_valid_key", len(violations) == 0))

    # Old key needs rotation
    old_key = store.generate("entity_old", KeyType.IDENTITY)
    store.activate(old_key.key_id)
    old_key.activated_at = time.time() - 100 * 86400
    old_violations = policy_engine.validate_key(old_key)
    checks.append(("s10_needs_rotation", any("rotation" in v for v in old_violations)))

    # Operation check
    ok, issues = policy_engine.check_operation(valid_key, "sign")
    checks.append(("s10_sign_ok", ok))

    ok_export, export_issues = policy_engine.check_operation(valid_key, "export")
    checks.append(("s10_export_denied", any("export" in i for i in export_issues)))

    # ── S11: Performance ──────────────────────────────────────────────
    # 1K key generation
    t0 = time.time()
    perf_store = KeyStore()
    for i in range(1000):
        k = perf_store.generate(f"entity_{i % 100}", KeyType.SIGNING)
        perf_store.activate(k.key_id)
    dt = time.time() - t0
    checks.append(("s11_1k_keys", dt < 3.0))

    # 10K HSM operations
    t0 = time.time()
    perf_hsm = HSMAdapter()
    perf_hsm.generate_key("perf_key")
    for i in range(10000):
        perf_hsm.sign("perf_key", f"data_{i}".encode())
    dt = time.time() - t0
    checks.append(("s11_10k_hsm", dt < 5.0))

    # 1K ceremony workflows
    t0 = time.time()
    perf_engine = CeremonyEngine()
    for i in range(1000):
        c = perf_engine.create_ceremony(
            CeremonyType.KEY_GENERATION, f"e_{i}", "admin"
        )
        for step in c.steps:
            for w in range(step.required_witnesses):
                perf_engine.witness_step(c.ceremony_id, step.step_id, f"w_{w}")
        perf_engine.advance(c.ceremony_id)
    dt = time.time() - t0
    checks.append(("s11_1k_ceremonies", dt < 5.0))

    # ── Report ────────────────────────────────────────────────────────
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    width = 60
    title = f"Key Management & Ceremonies — {passed}/{total} checks passed"
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
    print(f"\n  Time: {time.time() - t0:.2f}s\n")
    return passed == total


if __name__ == "__main__":
    success = run_checks()
    raise SystemExit(0 if success else 1)
