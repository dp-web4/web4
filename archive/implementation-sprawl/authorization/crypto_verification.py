"""
Web4 Authorization System - Cryptographic Verification
======================================================

Real Ed25519 signature verification for permission claims and delegations.

Integrates with Web4's existing crypto primitives to provide:
- Signature verification for permission claims
- Delegation signature verification
- Witness signature validation
- Public key management

Session #52: AI Agent Authorization & Delegation System
"""

import hashlib
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import Web4 crypto primitives
import sys
from pathlib import Path

# Try to import from act_deployment (where web4_crypto is)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "act_deployment"))
    from web4_crypto import Web4Crypto, KeyPair, CRYPTO_AVAILABLE
    from lct import LCT
except ImportError:
    # Fallback: use cryptography directly
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.exceptions import InvalidSignature
        CRYPTO_AVAILABLE = True
    except ImportError:
        CRYPTO_AVAILABLE = False


class SignatureVerificationError(Exception):
    """Raised when signature verification fails"""
    pass


@dataclass
class VerificationResult:
    """Result of signature verification"""
    valid: bool
    signer_lct: str
    message_hash: str
    error: Optional[str] = None


class CryptoVerifier:
    """
    Cryptographic signature verifier for authorization system.

    Verifies Ed25519 signatures on:
    - Permission claims
    - Agent delegations
    - Witness attestations
    """

    def __init__(self, lct_registry: Optional[Dict[str, bytes]] = None):
        """
        Initialize verifier with optional LCT registry.

        Args:
            lct_registry: Mapping of LCT ID -> public key (bytes)
        """
        self.lct_registry = lct_registry or {}

    def register_public_key(self, lct_id: str, public_key: bytes):
        """
        Register a public key for an LCT.

        Args:
            lct_id: LCT identifier
            public_key: Ed25519 public key (32 bytes)
        """
        if len(public_key) != 32:
            raise ValueError(f"Invalid public key length: {len(public_key)}, expected 32")
        self.lct_registry[lct_id] = public_key

    def get_public_key(self, lct_id: str) -> Optional[bytes]:
        """Get public key for an LCT"""
        return self.lct_registry.get(lct_id)

    def verify_signature(
        self,
        message: bytes,
        signature: bytes,
        signer_lct: str,
        signer_public_key: Optional[bytes] = None
    ) -> VerificationResult:
        """
        Verify an Ed25519 signature.

        Args:
            message: Original message that was signed
            signature: Ed25519 signature (64 bytes)
            signer_lct: LCT of the signer
            signer_public_key: Optional public key (if not in registry)

        Returns:
            VerificationResult with validation status
        """
        # Get public key
        public_key = signer_public_key or self.get_public_key(signer_lct)
        if not public_key:
            return VerificationResult(
                valid=False,
                signer_lct=signer_lct,
                message_hash=hashlib.sha256(message).hexdigest(),
                error=f"No public key found for LCT: {signer_lct}"
            )

        # Check signature length
        if len(signature) != 64:
            return VerificationResult(
                valid=False,
                signer_lct=signer_lct,
                message_hash=hashlib.sha256(message).hexdigest(),
                error=f"Invalid signature length: {len(signature)}, expected 64"
            )

        # Verify using Ed25519
        if not CRYPTO_AVAILABLE:
            return VerificationResult(
                valid=False,
                signer_lct=signer_lct,
                message_hash=hashlib.sha256(message).hexdigest(),
                error="Cryptography library not available"
            )

        try:
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
            public_key_obj.verify(signature, message)

            return VerificationResult(
                valid=True,
                signer_lct=signer_lct,
                message_hash=hashlib.sha256(message).hexdigest()
            )
        except InvalidSignature:
            return VerificationResult(
                valid=False,
                signer_lct=signer_lct,
                message_hash=hashlib.sha256(message).hexdigest(),
                error="Signature verification failed"
            )
        except Exception as e:
            return VerificationResult(
                valid=False,
                signer_lct=signer_lct,
                message_hash=hashlib.sha256(message).hexdigest(),
                error=f"Verification error: {str(e)}"
            )

    def verify_claim_signature(
        self,
        claim_data: Dict,
        signature: bytes,
        issuer_lct: str,
        issuer_public_key: Optional[bytes] = None
    ) -> VerificationResult:
        """
        Verify signature on a permission claim.

        Args:
            claim_data: Claim data dict (subject, permission, resource, etc.)
            signature: Ed25519 signature
            issuer_lct: LCT of issuer
            issuer_public_key: Optional public key

        Returns:
            VerificationResult
        """
        # Create canonical message from claim data
        message = self._canonicalize_claim(claim_data)
        return self.verify_signature(message, signature, issuer_lct, issuer_public_key)

    def verify_delegation_signature(
        self,
        delegation_data: Dict,
        signature: bytes,
        delegator_lct: str,
        delegator_public_key: Optional[bytes] = None
    ) -> VerificationResult:
        """
        Verify signature on an agent delegation.

        Args:
            delegation_data: Delegation data dict
            signature: Ed25519 signature
            delegator_lct: LCT of delegator
            delegator_public_key: Optional public key

        Returns:
            VerificationResult
        """
        message = self._canonicalize_delegation(delegation_data)
        return self.verify_signature(message, signature, delegator_lct, delegator_public_key)

    def verify_witness_signatures(
        self,
        message: bytes,
        witness_signatures: List[Dict],
        min_witnesses: int = 1
    ) -> Tuple[bool, List[str]]:
        """
        Verify multiple witness signatures.

        Args:
            message: Original message
            witness_signatures: List of {lct_id, signature, public_key?}
            min_witnesses: Minimum number of valid witnesses required

        Returns:
            Tuple of (all_valid, list of errors)
        """
        if len(witness_signatures) < min_witnesses:
            return False, [f"Insufficient witnesses: {len(witness_signatures)} < {min_witnesses}"]

        errors = []
        valid_count = 0

        for witness in witness_signatures:
            lct_id = witness.get('lct_id')
            sig_hex = witness.get('signature')
            pub_key_hex = witness.get('public_key')

            if not lct_id or not sig_hex:
                errors.append(f"Missing lct_id or signature in witness record")
                continue

            try:
                signature = bytes.fromhex(sig_hex)
                public_key = bytes.fromhex(pub_key_hex) if pub_key_hex else None

                result = self.verify_signature(message, signature, lct_id, public_key)
                if result.valid:
                    valid_count += 1
                else:
                    errors.append(f"Witness {lct_id} signature invalid: {result.error}")
            except Exception as e:
                errors.append(f"Witness {lct_id} verification error: {str(e)}")

        if valid_count < min_witnesses:
            errors.insert(0, f"Insufficient valid witnesses: {valid_count} < {min_witnesses}")
            return False, errors

        return True, []

    def _canonicalize_claim(self, claim_data: Dict) -> bytes:
        """
        Create canonical message for claim signature.

        Ensures consistent ordering for signature verification.
        """
        canonical = {
            "subject_lct": claim_data.get("subject_lct"),
            "issuer_lct": claim_data.get("issuer_lct"),
            "permission": claim_data.get("permission"),
            "resource": claim_data.get("resource"),
            "scope": claim_data.get("scope"),
            "organization": claim_data.get("organization"),
            "issued_at": claim_data.get("issued_at"),
            "expires_at": claim_data.get("expires_at"),
        }

        # Deterministic JSON serialization
        message_json = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
        return message_json.encode('utf-8')

    def _canonicalize_delegation(self, delegation_data: Dict) -> bytes:
        """
        Create canonical message for delegation signature.

        Ensures consistent ordering for signature verification.
        """
        canonical = {
            "delegation_id": delegation_data.get("delegation_id"),
            "delegator_lct": delegation_data.get("delegator_lct"),
            "delegatee_lct": delegation_data.get("delegatee_lct"),
            "organization": delegation_data.get("organization"),
            "granted_permissions": delegation_data.get("granted_claim_hashes", []),
            "atp_budget": delegation_data.get("atp_budget"),
            "valid_from": delegation_data.get("valid_from"),
            "valid_until": delegation_data.get("valid_until"),
        }

        message_json = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
        return message_json.encode('utf-8')


class ClaimSigner:
    """
    Utility for signing permission claims and delegations.

    Used by issuers to create cryptographically signed claims.
    """

    def __init__(self, private_key: bytes, public_key: bytes, lct_id: str):
        """
        Initialize signer with keypair.

        Args:
            private_key: Ed25519 private key (32 bytes)
            public_key: Ed25519 public key (32 bytes)
            lct_id: LCT identifier of signer
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Cryptography library not available")

        if len(private_key) != 32:
            raise ValueError(f"Invalid private key length: {len(private_key)}")
        if len(public_key) != 32:
            raise ValueError(f"Invalid public key length: {len(public_key)}")

        self.private_key = private_key
        self.public_key = public_key
        self.lct_id = lct_id

    def sign_claim(self, claim_data: Dict) -> bytes:
        """
        Sign a permission claim.

        Args:
            claim_data: Claim data dict

        Returns:
            Ed25519 signature (64 bytes)
        """
        verifier = CryptoVerifier()
        message = verifier._canonicalize_claim(claim_data)

        private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key)
        signature = private_key_obj.sign(message)
        return signature

    def sign_delegation(self, delegation_data: Dict) -> bytes:
        """
        Sign an agent delegation.

        Args:
            delegation_data: Delegation data dict

        Returns:
            Ed25519 signature (64 bytes)
        """
        verifier = CryptoVerifier()
        message = verifier._canonicalize_delegation(delegation_data)

        private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key)
        signature = private_key_obj.sign(message)
        return signature


# Utility functions for common operations

def verify_claim(
    claim_data: Dict,
    signature_hex: str,
    issuer_public_key_hex: str
) -> bool:
    """
    Convenience function to verify a claim signature.

    Args:
        claim_data: Claim data dictionary
        signature_hex: Hex-encoded signature
        issuer_public_key_hex: Hex-encoded issuer public key

    Returns:
        True if signature is valid
    """
    try:
        verifier = CryptoVerifier()
        signature = bytes.fromhex(signature_hex)
        public_key = bytes.fromhex(issuer_public_key_hex)

        result = verifier.verify_claim_signature(
            claim_data,
            signature,
            claim_data['issuer_lct'],
            public_key
        )
        return result.valid
    except Exception:
        return False


def verify_delegation(
    delegation_data: Dict,
    signature_hex: str,
    delegator_public_key_hex: str
) -> bool:
    """
    Convenience function to verify a delegation signature.

    Args:
        delegation_data: Delegation data dictionary
        signature_hex: Hex-encoded signature
        delegator_public_key_hex: Hex-encoded delegator public key

    Returns:
        True if signature is valid
    """
    try:
        verifier = CryptoVerifier()
        signature = bytes.fromhex(signature_hex)
        public_key = bytes.fromhex(delegator_public_key_hex)

        result = verifier.verify_delegation_signature(
            delegation_data,
            signature,
            delegation_data['delegator_lct'],
            public_key
        )
        return result.valid
    except Exception:
        return False
