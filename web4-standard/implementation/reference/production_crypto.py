"""
Web4 Production Cryptography
==============================

Production-grade cryptographic operations for Web4 protocol.

Implements the remaining P0 crypto functions beyond Ed25519 signature
verification (crypto_verification.py):

1. ATP Transaction Signing - Sign charge/discharge transactions
2. Delegation Signature Creation - Sign delegation grants
3. Birth Certificate Signing - Society signs birth certificates
4. Message Authentication - HMAC for message integrity

All signatures use Ed25519 for consistency with LCT identities.

Security:
- Constant-time operations (timing attack resistant)
- Canonical message serialization (deterministic)
- Nonce generation for replay protection
- Clear error messages without leaking keys

Author: Legion Autonomous Session (2025-12-05)
Session: Autonomous Web4 Research Track 5
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import hashlib
import base64
import secrets
import logging

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization, hashes, hmac
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    InvalidSignature = Exception

logger = logging.getLogger(__name__)


class CryptoError(Exception):
    """Raised when cryptographic operations fail"""
    pass


# ============================================================================
# ATP Transaction Signing
# ============================================================================

@dataclass
class ATPTransaction:
    """
    ATP charge/discharge transaction.

    Represents a signed ATP transaction that transfers value
    through charging (ADP→ATP) or discharging (ATP→ADP).
    """
    transaction_id: str
    transaction_type: str  # 'charge' or 'discharge'
    from_entity: str  # LCT of sender
    to_entity: str  # LCT of recipient
    amount: int  # ATP amount
    timestamp: float
    nonce: str
    metadata: Dict[str, Any]
    signature: str = ""

    def to_signing_data(self) -> bytes:
        """Get canonical signing data (deterministic JSON)"""
        signing_dict = {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type,
            "from_entity": self.from_entity,
            "to_entity": self.to_entity,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "metadata": self.metadata
        }
        canonical = json.dumps(signing_dict, sort_keys=True, separators=(',', ':'))
        return canonical.encode('utf-8')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


def create_atp_transaction(
    transaction_type: str,
    from_entity: str,
    to_entity: str,
    amount: int,
    private_key: ed25519.Ed25519PrivateKey,
    metadata: Optional[Dict[str, Any]] = None,
    transaction_id: Optional[str] = None
) -> ATPTransaction:
    """
    Create and sign ATP transaction.

    Args:
        transaction_type: 'charge' or 'discharge'
        from_entity: LCT of sender (pool for charge, entity for discharge)
        to_entity: LCT of recipient (entity for charge, pool for discharge)
        amount: ATP amount to transfer
        private_key: Ed25519 private key for signing
        metadata: Optional transaction metadata
        transaction_id: Optional transaction ID (generated if not provided)

    Returns:
        Signed ATPTransaction

    Raises:
        ValueError: If inputs are invalid
        CryptoError: If signing fails
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoError("cryptography library not available")

    if transaction_type not in ('charge', 'discharge'):
        raise ValueError(f"Invalid transaction_type: {transaction_type}")

    if amount <= 0:
        raise ValueError(f"Amount must be positive: {amount}")

    # Generate transaction ID if not provided
    if not transaction_id:
        tx_hash = hashlib.sha256(
            f"{transaction_type}:{from_entity}:{to_entity}:{amount}:{secrets.token_hex(16)}".encode()
        ).hexdigest()
        transaction_id = f"atp:tx:{tx_hash[:16]}"

    # Generate nonce for replay protection
    nonce = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

    # Create transaction
    transaction = ATPTransaction(
        transaction_id=transaction_id,
        transaction_type=transaction_type,
        from_entity=from_entity,
        to_entity=to_entity,
        amount=amount,
        timestamp=datetime.now(timezone.utc).timestamp(),
        nonce=nonce,
        metadata=metadata or {}
    )

    # Sign transaction
    try:
        signing_data = transaction.to_signing_data()
        signature = private_key.sign(signing_data)
        transaction.signature = signature.hex()

        logger.debug(f"Created ATP transaction: {transaction_id} ({transaction_type}, {amount} ATP)")

        return transaction

    except Exception as e:
        logger.error(f"Failed to sign ATP transaction: {e}")
        raise CryptoError(f"Transaction signing failed: {e}")


def verify_atp_transaction(
    transaction: ATPTransaction,
    public_key: ed25519.Ed25519PublicKey
) -> bool:
    """
    Verify ATP transaction signature.

    Args:
        transaction: ATP transaction to verify
        public_key: Ed25519 public key of signer

    Returns:
        True if signature is valid

    Raises:
        CryptoError: If verification fails
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoError("cryptography library not available")

    try:
        signing_data = transaction.to_signing_data()
        signature_bytes = bytes.fromhex(transaction.signature)

        public_key.verify(signature_bytes, signing_data)

        logger.debug(f"Verified ATP transaction: {transaction.transaction_id}")
        return True

    except InvalidSignature:
        logger.warning(f"Invalid ATP transaction signature: {transaction.transaction_id}")
        return False

    except Exception as e:
        logger.error(f"ATP transaction verification error: {e}")
        raise CryptoError(f"Verification failed: {e}")


# ============================================================================
# Delegation Signature Creation
# ============================================================================

@dataclass
class SignedDelegation:
    """
    Cryptographically signed delegation.

    Grants authority from delegator (client) to delegatee (agent)
    with ATP budget, permissions, and time constraints.
    """
    delegation_id: str
    delegator_lct: str
    delegatee_lct: str
    role_lct: Optional[str]
    granted_permissions: List[str]
    atp_budget: int
    valid_from: float
    valid_until: float
    organization_id: str
    constraints: Dict[str, Any]
    metadata: Dict[str, Any]
    signature: str = ""
    witness_signatures: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.witness_signatures is None:
            self.witness_signatures = []

    def to_signing_data(self) -> bytes:
        """Get canonical signing data"""
        signing_dict = {
            "delegation_id": self.delegation_id,
            "delegator_lct": self.delegator_lct,
            "delegatee_lct": self.delegatee_lct,
            "role_lct": self.role_lct,
            "granted_permissions": sorted(self.granted_permissions),  # Sorted for determinism
            "atp_budget": self.atp_budget,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "organization_id": self.organization_id,
            "constraints": self.constraints
        }
        canonical = json.dumps(signing_dict, sort_keys=True, separators=(',', ':'))
        return canonical.encode('utf-8')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


def create_delegation(
    delegator_lct: str,
    delegatee_lct: str,
    granted_permissions: List[str],
    atp_budget: int,
    valid_from: datetime,
    valid_until: datetime,
    organization_id: str,
    delegator_private_key: ed25519.Ed25519PrivateKey,
    role_lct: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    delegation_id: Optional[str] = None
) -> SignedDelegation:
    """
    Create and sign delegation.

    Args:
        delegator_lct: Client/principal LCT (delegating authority)
        delegatee_lct: Agent LCT (receiving authority)
        granted_permissions: List of permission claim hashes
        atp_budget: Total ATP budget for delegation
        valid_from: Start time
        valid_until: End time
        organization_id: Organization context
        delegator_private_key: Delegator's Ed25519 private key
        role_lct: Optional role LCT
        constraints: Optional constraint dictionary (e.g., min_t3)
        metadata: Optional metadata
        delegation_id: Optional delegation ID (generated if not provided)

    Returns:
        Signed delegation

    Raises:
        ValueError: If inputs are invalid
        CryptoError: If signing fails
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoError("cryptography library not available")

    # Validation
    if atp_budget <= 0:
        raise ValueError(f"ATP budget must be positive: {atp_budget}")

    if valid_until <= valid_from:
        raise ValueError(f"valid_until must be after valid_from")

    if delegator_lct == delegatee_lct:
        raise ValueError("Cannot delegate to self")

    # Generate delegation ID if not provided
    if not delegation_id:
        delegation_hash = hashlib.sha256(
            f"{delegator_lct}:{delegatee_lct}:{organization_id}:{secrets.token_hex(8)}".encode()
        ).hexdigest()
        delegation_id = f"delegation:{delegation_hash[:16]}"

    # Create delegation
    delegation = SignedDelegation(
        delegation_id=delegation_id,
        delegator_lct=delegator_lct,
        delegatee_lct=delegatee_lct,
        role_lct=role_lct,
        granted_permissions=granted_permissions,
        atp_budget=atp_budget,
        valid_from=valid_from.timestamp(),
        valid_until=valid_until.timestamp(),
        organization_id=organization_id,
        constraints=constraints or {},
        metadata=metadata or {}
    )

    # Sign delegation
    try:
        signing_data = delegation.to_signing_data()
        signature = delegator_private_key.sign(signing_data)
        delegation.signature = signature.hex()

        logger.info(f"Created delegation: {delegation_id} ({delegator_lct} → {delegatee_lct}, {atp_budget} ATP)")

        return delegation

    except Exception as e:
        logger.error(f"Failed to sign delegation: {e}")
        raise CryptoError(f"Delegation signing failed: {e}")


def verify_delegation(
    delegation: SignedDelegation,
    delegator_public_key: ed25519.Ed25519PublicKey
) -> bool:
    """
    Verify delegation signature.

    Args:
        delegation: Delegation to verify
        delegator_public_key: Delegator's Ed25519 public key

    Returns:
        True if signature is valid

    Raises:
        CryptoError: If verification fails
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoError("cryptography library not available")

    try:
        signing_data = delegation.to_signing_data()
        signature_bytes = bytes.fromhex(delegation.signature)

        delegator_public_key.verify(signature_bytes, signing_data)

        logger.debug(f"Verified delegation: {delegation.delegation_id}")
        return True

    except InvalidSignature:
        logger.warning(f"Invalid delegation signature: {delegation.delegation_id}")
        return False

    except Exception as e:
        logger.error(f"Delegation verification error: {e}")
        raise CryptoError(f"Verification failed: {e}")


# ============================================================================
# Birth Certificate Signing
# ============================================================================

@dataclass
class SignedBirthCertificate:
    """
    Cryptographically signed birth certificate.

    Proves LCT was legitimately minted by a society, witnessed
    by authorized entities, and granted initial rights.
    """
    lct_id: str
    entity_type: str
    society_id: str
    law_oracle_id: str
    law_version: str
    birth_timestamp: float
    witnesses: List[str]
    initial_rights: List[str]
    initial_responsibilities: List[str]
    genesis_block: Optional[str] = None
    certificate_hash: str = ""
    society_signature: str = ""
    witness_signatures: Dict[str, str] = None

    def __post_init__(self):
        if self.witness_signatures is None:
            self.witness_signatures = {}
        if not self.certificate_hash:
            self.certificate_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute tamper-evident hash of certificate"""
        cert_data = {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type,
            "society_id": self.society_id,
            "law_oracle_id": self.law_oracle_id,
            "law_version": self.law_version,
            "birth_timestamp": self.birth_timestamp,
            "witnesses": sorted(self.witnesses),
            "genesis_block": self.genesis_block,
            "initial_rights": sorted(self.initial_rights),
            "initial_responsibilities": sorted(self.initial_responsibilities)
        }
        cert_json = json.dumps(cert_data, sort_keys=True)
        return "0x" + hashlib.sha256(cert_json.encode()).hexdigest()

    def to_signing_data(self) -> bytes:
        """Get certificate hash as signing data"""
        return self.certificate_hash.encode('utf-8')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


def create_birth_certificate(
    lct_id: str,
    entity_type: str,
    society_id: str,
    law_oracle_id: str,
    law_version: str,
    witnesses: List[str],
    society_private_key: ed25519.Ed25519PrivateKey,
    initial_rights: Optional[List[str]] = None,
    initial_responsibilities: Optional[List[str]] = None,
    genesis_block: Optional[str] = None
) -> SignedBirthCertificate:
    """
    Create and sign birth certificate.

    Args:
        lct_id: LCT identifier being minted
        entity_type: Entity type (HUMAN, AI, SOCIETY, etc.)
        society_id: Society identifier
        law_oracle_id: Law oracle identifier
        law_version: Law version
        witnesses: List of witness LCTs
        society_private_key: Society's Ed25519 private key
        initial_rights: Initial rights granted (default: exist, interact, accumulate_reputation)
        initial_responsibilities: Initial responsibilities (default: abide_law, respect_quorum)
        genesis_block: Optional genesis block reference

    Returns:
        Signed birth certificate

    Raises:
        CryptoError: If signing fails
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoError("cryptography library not available")

    # Defaults
    if initial_rights is None:
        initial_rights = ["exist", "interact", "accumulate_reputation"]
    if initial_responsibilities is None:
        initial_responsibilities = ["abide_law", "respect_quorum"]

    # Create certificate
    certificate = SignedBirthCertificate(
        lct_id=lct_id,
        entity_type=entity_type,
        society_id=society_id,
        law_oracle_id=law_oracle_id,
        law_version=law_version,
        birth_timestamp=datetime.now(timezone.utc).timestamp(),
        witnesses=witnesses,
        initial_rights=initial_rights,
        initial_responsibilities=initial_responsibilities,
        genesis_block=genesis_block
    )

    # Society signs certificate
    try:
        signing_data = certificate.to_signing_data()
        signature = society_private_key.sign(signing_data)
        certificate.society_signature = signature.hex()

        logger.info(f"Created birth certificate: {lct_id} (society={society_id})")

        return certificate

    except Exception as e:
        logger.error(f"Failed to sign birth certificate: {e}")
        raise CryptoError(f"Birth certificate signing failed: {e}")


def add_witness_signature(
    certificate: SignedBirthCertificate,
    witness_lct: str,
    witness_private_key: ed25519.Ed25519PrivateKey
) -> SignedBirthCertificate:
    """
    Add witness signature to birth certificate.

    Args:
        certificate: Birth certificate to witness
        witness_lct: Witness LCT identifier
        witness_private_key: Witness's Ed25519 private key

    Returns:
        Certificate with added witness signature

    Raises:
        ValueError: If witness already signed
        CryptoError: If signing fails
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoError("cryptography library not available")

    if witness_lct in certificate.witness_signatures:
        raise ValueError(f"Witness {witness_lct} already signed")

    try:
        signing_data = certificate.to_signing_data()
        signature = witness_private_key.sign(signing_data)
        certificate.witness_signatures[witness_lct] = signature.hex()

        logger.debug(f"Added witness signature: {witness_lct} on {certificate.lct_id}")

        return certificate

    except Exception as e:
        logger.error(f"Failed to add witness signature: {e}")
        raise CryptoError(f"Witness signing failed: {e}")


def verify_birth_certificate(
    certificate: SignedBirthCertificate,
    society_public_key: ed25519.Ed25519PublicKey,
    witness_public_keys: Optional[Dict[str, ed25519.Ed25519PublicKey]] = None
) -> Tuple[bool, List[str]]:
    """
    Verify birth certificate signatures.

    Args:
        certificate: Birth certificate to verify
        society_public_key: Society's Ed25519 public key
        witness_public_keys: Optional dict of witness_lct → public_key

    Returns:
        (valid, errors) tuple where errors lists any verification failures

    Raises:
        CryptoError: If verification fails
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoError("cryptography library not available")

    errors = []
    signing_data = certificate.to_signing_data()

    # Verify society signature
    try:
        society_sig_bytes = bytes.fromhex(certificate.society_signature)
        society_public_key.verify(society_sig_bytes, signing_data)
    except InvalidSignature:
        errors.append("Invalid society signature")
    except Exception as e:
        errors.append(f"Society signature verification error: {e}")

    # Verify witness signatures
    if witness_public_keys:
        for witness_lct, pub_key in witness_public_keys.items():
            if witness_lct not in certificate.witness_signatures:
                errors.append(f"Missing witness signature: {witness_lct}")
                continue

            try:
                witness_sig_bytes = bytes.fromhex(certificate.witness_signatures[witness_lct])
                pub_key.verify(witness_sig_bytes, signing_data)
            except InvalidSignature:
                errors.append(f"Invalid witness signature: {witness_lct}")
            except Exception as e:
                errors.append(f"Witness {witness_lct} verification error: {e}")

    if errors:
        logger.warning(f"Birth certificate verification failed: {errors}")
        return False, errors

    logger.debug(f"Verified birth certificate: {certificate.lct_id}")
    return True, []


# ============================================================================
# Message Authentication (HMAC)
# ============================================================================

def generate_hmac(
    message: bytes,
    secret_key: bytes,
    algorithm: str = "sha256"
) -> str:
    """
    Generate HMAC for message authentication.

    Args:
        message: Message to authenticate
        secret_key: Shared secret key
        algorithm: Hash algorithm (sha256, sha512)

    Returns:
        HMAC hex string

    Raises:
        ValueError: If algorithm is unsupported
        CryptoError: If HMAC generation fails
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoError("cryptography library not available")

    hash_map = {
        "sha256": hashes.SHA256(),
        "sha512": hashes.SHA512()
    }

    if algorithm not in hash_map:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    try:
        h = hmac.HMAC(secret_key, hash_map[algorithm])
        h.update(message)
        return h.finalize().hex()

    except Exception as e:
        logger.error(f"HMAC generation failed: {e}")
        raise CryptoError(f"HMAC generation failed: {e}")


def verify_hmac(
    message: bytes,
    secret_key: bytes,
    provided_hmac: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify HMAC for message authentication.

    Args:
        message: Message to verify
        secret_key: Shared secret key
        provided_hmac: HMAC to verify (hex string)
        algorithm: Hash algorithm (sha256, sha512)

    Returns:
        True if HMAC is valid

    Raises:
        CryptoError: If verification fails
    """
    if not CRYPTO_AVAILABLE:
        raise CryptoError("cryptography library not available")

    try:
        expected_hmac = generate_hmac(message, secret_key, algorithm)
        return secrets.compare_digest(expected_hmac, provided_hmac)

    except Exception as e:
        logger.error(f"HMAC verification failed: {e}")
        raise CryptoError(f"HMAC verification failed: {e}")


# ============================================================================
# Utility Functions
# ============================================================================

def generate_nonce(length: int = 16) -> str:
    """
    Generate cryptographically secure random nonce.

    Args:
        length: Nonce length in bytes (default 16)

    Returns:
        Base64-encoded nonce string
    """
    return base64.b64encode(secrets.token_bytes(length)).decode('ascii')


def hash_message(message: bytes, algorithm: str = "sha256") -> str:
    """
    Hash message with specified algorithm.

    Args:
        message: Message to hash
        algorithm: Hash algorithm (sha256, sha512)

    Returns:
        Hex-encoded hash

    Raises:
        ValueError: If algorithm unsupported
    """
    if algorithm == "sha256":
        return "0x" + hashlib.sha256(message).hexdigest()
    elif algorithm == "sha512":
        return "0x" + hashlib.sha512(message).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


# Example usage
if __name__ == '__main__':
    if CRYPTO_AVAILABLE:
        from crypto_verification import generate_test_keypair

        print("=== Web4 Production Crypto Examples ===\n")

        # Generate test keys
        society_privkey, society_pubkey = generate_test_keypair()
        delegator_privkey, delegator_pubkey = generate_test_keypair()
        delegatee_privkey, delegatee_pubkey = generate_test_keypair()

        # Example 1: ATP Transaction
        print("1. ATP Transaction Signing")
        atp_tx = create_atp_transaction(
            transaction_type="charge",
            from_entity="pool:energy:grid001",
            to_entity="lct:ai:agent:001",
            amount=1000,
            private_key=society_privkey,
            metadata={"energy_kwh": 10.5}
        )
        print(f"   ✓ Created ATP transaction: {atp_tx.transaction_id}")
        print(f"   ✓ Amount: {atp_tx.amount} ATP")

        valid = verify_atp_transaction(atp_tx, society_pubkey)
        print(f"   ✓ Signature valid: {valid}\n")

        # Example 2: Delegation
        print("2. Delegation Signing")
        from datetime import timedelta
        delegation = create_delegation(
            delegator_lct="lct:human:client:001",
            delegatee_lct="lct:ai:agent:001",
            granted_permissions=["read:*", "write:code:*"],
            atp_budget=5000,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
            organization_id="org:web4:default",
            delegator_private_key=delegator_privkey,
            constraints={"min_t3": 0.7}
        )
        print(f"   ✓ Created delegation: {delegation.delegation_id}")
        print(f"   ✓ ATP budget: {delegation.atp_budget}")

        valid = verify_delegation(delegation, delegator_pubkey)
        print(f"   ✓ Signature valid: {valid}\n")

        # Example 3: Birth Certificate
        print("3. Birth Certificate Signing")
        birth_cert = create_birth_certificate(
            lct_id="lct:ai:agent:newborn:001",
            entity_type="AI",
            society_id="web4:default",
            law_oracle_id="oracle:law:default",
            law_version="v1.0.0",
            witnesses=["witness:001", "witness:002"],
            society_private_key=society_privkey
        )
        print(f"   ✓ Created birth certificate: {birth_cert.lct_id}")
        print(f"   ✓ Certificate hash: {birth_cert.certificate_hash[:32]}...")

        valid, errors = verify_birth_certificate(birth_cert, society_pubkey)
        print(f"   ✓ Signature valid: {valid}\n")

        print("=== All production crypto examples completed ===")
    else:
        print("cryptography library not available - install with: pip install cryptography")
