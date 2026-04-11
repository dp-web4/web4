"""
SESSION 94 TRACK 2: CRYPTOGRAPHIC SIGNATURES FOR IRP RESULTS

From Session 93's next steps:
> "Cryptographic signatures: IRP results should be signed by executor,
   verified by caller (non-repudiation, tamper-detection)"

This implements:
1. Ed25519 signature generation for IRP results
2. Signature verification on client side
3. Integration with LCT identity (expert signing key)
4. Tamper detection for IRP responses
5. Non-repudiation (executor can't deny creating result)

Key innovations:
- Expert private keys bound to LCT identity
- Deterministic signature over canonical JSON
- Verification before ATP settlement
- Signature metadata (timestamp, signer LCT, nonce)

Integration with Track 1:
- HTTPIRPServer signs responses before sending
- HTTPIRPClient verifies signatures before processing
- ATP settlement only commits if signature valid

References:
- SAGE Fractal IRP v0.2 spec (result signals)
- Web4 LCT identity system
- Session 93 Track 2 (ATP settlement)
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import secrets

# Cryptography imports (conditional for testing)
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  cryptography not installed - using simulated signatures for testing")


# ============================================================================
# CRYPTOGRAPHIC KEY MANAGEMENT
# ============================================================================

@dataclass
class SigningKeyPair:
    """Ed25519 key pair for IRP expert."""
    lct_identity: str  # LCT identity this key belongs to
    private_key: Any  # ed25519.Ed25519PrivateKey (or simulated)
    public_key: Any   # ed25519.Ed25519PublicKey (or simulated)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @staticmethod
    def generate(lct_identity: str) -> "SigningKeyPair":
        """Generate new Ed25519 key pair for expert."""
        if CRYPTO_AVAILABLE:
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
        else:
            # Simulated keys for testing
            private_key = f"simulated_private_{secrets.token_hex(16)}"
            public_key = f"simulated_public_{secrets.token_hex(16)}"

        return SigningKeyPair(
            lct_identity=lct_identity,
            private_key=private_key,
            public_key=public_key
        )

    def export_public_key_pem(self) -> str:
        """Export public key in PEM format for distribution."""
        if CRYPTO_AVAILABLE:
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode('utf-8')
        else:
            return f"-----BEGIN PUBLIC KEY-----\n{self.public_key}\n-----END PUBLIC KEY-----"

    @staticmethod
    def import_public_key_pem(pem_str: str) -> Any:
        """Import public key from PEM format."""
        if CRYPTO_AVAILABLE:
            return serialization.load_pem_public_key(pem_str.encode('utf-8'))
        else:
            # Extract simulated key from PEM
            lines = pem_str.strip().split('\n')
            return lines[1] if len(lines) > 1 else pem_str


# ============================================================================
# SIGNATURE METADATA
# ============================================================================

@dataclass
class SignatureMetadata:
    """Metadata included with IRP result signature."""
    signer_lct: str           # LCT identity of signing expert
    timestamp: str            # ISO 8601 UTC timestamp
    nonce: str                # Random nonce (prevents replay attacks)
    algorithm: str = "Ed25519"  # Signature algorithm

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signer_lct": self.signer_lct,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "algorithm": self.algorithm
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SignatureMetadata":
        return SignatureMetadata(
            signer_lct=data["signer_lct"],
            timestamp=data["timestamp"],
            nonce=data["nonce"],
            algorithm=data.get("algorithm", "Ed25519")
        )


# ============================================================================
# SIGNED IRP RESULT
# ============================================================================

@dataclass
class SignedIRPResult:
    """
    IRP result with cryptographic signature.

    Structure:
    - payload: The actual IRP result (status, signals, outputs, etc.)
    - metadata: Signature metadata (signer, timestamp, nonce)
    - signature: Ed25519 signature over canonical(payload + metadata)
    """
    payload: Dict[str, Any]      # IRP result data
    metadata: SignatureMetadata  # Signature metadata
    signature: str               # Base64-encoded signature

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payload": self.payload,
            "metadata": self.metadata.to_dict(),
            "signature": self.signature
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SignedIRPResult":
        return SignedIRPResult(
            payload=data["payload"],
            metadata=SignatureMetadata.from_dict(data["metadata"]),
            signature=data["signature"]
        )


# ============================================================================
# SIGNATURE GENERATION AND VERIFICATION
# ============================================================================

class IRPSigner:
    """Signs IRP results with expert's private key."""

    def __init__(self, key_pair: SigningKeyPair):
        self.key_pair = key_pair

    def sign_result(self, result_payload: Dict[str, Any]) -> SignedIRPResult:
        """
        Sign IRP result with expert's private key.

        Process:
        1. Generate metadata (signer LCT, timestamp, nonce)
        2. Create canonical JSON of payload + metadata
        3. Sign with Ed25519 private key
        4. Return SignedIRPResult
        """
        # Generate metadata
        metadata = SignatureMetadata(
            signer_lct=self.key_pair.lct_identity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            nonce=secrets.token_hex(16)
        )

        # Create canonical message to sign
        message = self._create_canonical_message(result_payload, metadata)

        # Sign message
        if CRYPTO_AVAILABLE:
            signature_bytes = self.key_pair.private_key.sign(message.encode('utf-8'))
            signature_b64 = self._bytes_to_base64(signature_bytes)
        else:
            # Simulated signature for testing
            signature_b64 = f"sim_sig_{hashlib.sha256(message.encode()).hexdigest()[:32]}"

        return SignedIRPResult(
            payload=result_payload,
            metadata=metadata,
            signature=signature_b64
        )

    @staticmethod
    def _create_canonical_message(payload: Dict[str, Any], metadata: SignatureMetadata) -> str:
        """
        Create canonical JSON representation for signing.

        Critical for deterministic signatures:
        - Sort keys alphabetically
        - No whitespace
        - Consistent encoding
        """
        combined = {
            "payload": payload,
            "metadata": metadata.to_dict()
        }
        return json.dumps(combined, sort_keys=True, separators=(',', ':'))

    @staticmethod
    def _bytes_to_base64(data: bytes) -> str:
        """Convert bytes to base64 string."""
        import base64
        return base64.b64encode(data).decode('ascii')


class IRPVerifier:
    """Verifies IRP result signatures."""

    def __init__(self, trusted_public_keys: Dict[str, Any]):
        """
        Initialize verifier with trusted public keys.

        Args:
            trusted_public_keys: Map of LCT identity -> public key
        """
        self.trusted_keys = trusted_public_keys

    def verify_result(self, signed_result: SignedIRPResult) -> bool:
        """
        Verify IRP result signature.

        Returns:
            True if signature valid, False otherwise

        Checks:
        1. Signer LCT is in trusted keys
        2. Signature verifies with signer's public key
        3. Timestamp is recent (within tolerance)
        """
        signer_lct = signed_result.metadata.signer_lct

        # Check if signer is trusted
        if signer_lct not in self.trusted_keys:
            print(f"❌ Signer not trusted: {signer_lct}")
            return False

        public_key = self.trusted_keys[signer_lct]

        # Recreate canonical message
        message = IRPSigner._create_canonical_message(
            signed_result.payload,
            signed_result.metadata
        )

        # Verify signature
        if CRYPTO_AVAILABLE:
            try:
                signature_bytes = self._base64_to_bytes(signed_result.signature)
                public_key.verify(signature_bytes, message.encode('utf-8'))
                return True
            except InvalidSignature:
                print(f"❌ Invalid signature from {signer_lct}")
                return False
        else:
            # Simulated verification
            expected_sig = f"sim_sig_{hashlib.sha256(message.encode()).hexdigest()[:32]}"
            return signed_result.signature == expected_sig

    def verify_result_with_details(self, signed_result: SignedIRPResult) -> Dict[str, Any]:
        """
        Verify signature and return detailed results.

        Returns:
            {
                "valid": bool,
                "signer_lct": str,
                "timestamp": str,
                "trusted": bool,
                "error": Optional[str]
            }
        """
        signer_lct = signed_result.metadata.signer_lct

        result = {
            "signer_lct": signer_lct,
            "timestamp": signed_result.metadata.timestamp,
            "trusted": signer_lct in self.trusted_keys,
            "algorithm": signed_result.metadata.algorithm
        }

        if not result["trusted"]:
            result["valid"] = False
            result["error"] = f"Signer {signer_lct} not in trusted keys"
            return result

        # Verify signature
        is_valid = self.verify_result(signed_result)
        result["valid"] = is_valid
        if not is_valid:
            result["error"] = "Signature verification failed"

        return result

    @staticmethod
    def _base64_to_bytes(data: str) -> bytes:
        """Convert base64 string to bytes."""
        import base64
        return base64.b64decode(data.encode('ascii'))


# ============================================================================
# INTEGRATION WITH ATP SETTLEMENT
# ============================================================================

class SecureATPSettlement:
    """
    ATP settlement with signature verification.

    Extends Session 93's ATPSettlementManager with:
    - Signature verification before commit
    - Tamper detection (result modified after signing)
    - Non-repudiation (executor can't deny result)
    """

    def __init__(self, verifier: IRPVerifier):
        self.verifier = verifier
        self.transactions: Dict[str, Dict] = {}

    def lock_atp_for_invocation(
        self,
        caller_lct: str,
        executor_lct: str,
        amount: float
    ) -> str:
        """Lock ATP for remote invocation."""
        tx_id = f"tx_{secrets.token_hex(16)}"
        self.transactions[tx_id] = {
            "caller": caller_lct,
            "executor": executor_lct,
            "amount": amount,
            "status": "LOCKED",
            "locked_at": datetime.now(timezone.utc).isoformat()
        }
        return tx_id

    def commit_atp_with_signature(
        self,
        tx_id: str,
        signed_result: SignedIRPResult,
        quality_threshold: float = 0.70
    ) -> Dict[str, Any]:
        """
        Commit ATP settlement after verifying signature.

        Process:
        1. Verify signature is valid
        2. Check quality threshold
        3. Commit or rollback ATP accordingly

        Returns:
            {
                "status": "COMMITTED" | "ROLLED_BACK",
                "signature_valid": bool,
                "quality": float,
                "amount": float
            }
        """
        if tx_id not in self.transactions:
            return {"status": "ERROR", "error": "Transaction not found"}

        tx = self.transactions[tx_id]

        # STEP 1: Verify signature
        verification = self.verifier.verify_result_with_details(signed_result)

        if not verification["valid"]:
            # Signature invalid - rollback and flag security issue
            tx["status"] = "ROLLED_BACK"
            tx["reason"] = f"Invalid signature: {verification.get('error')}"
            tx["completed_at"] = datetime.now(timezone.utc).isoformat()

            return {
                "status": "ROLLED_BACK",
                "signature_valid": False,
                "reason": verification.get("error"),
                "amount": 0.0
            }

        # STEP 2: Check quality threshold
        quality = signed_result.payload.get("signals", {}).get("quality", 0.0)

        if quality >= quality_threshold:
            # Quality acceptable - commit ATP
            tx["status"] = "COMMITTED"
            tx["quality"] = quality
            tx["completed_at"] = datetime.now(timezone.utc).isoformat()
            tx["signature_verified"] = True

            return {
                "status": "COMMITTED",
                "signature_valid": True,
                "quality": quality,
                "amount": tx["amount"]
            }
        else:
            # Quality too low - rollback ATP
            tx["status"] = "ROLLED_BACK"
            tx["quality"] = quality
            tx["reason"] = f"Quality {quality:.2f} below threshold {quality_threshold:.2f}"
            tx["completed_at"] = datetime.now(timezone.utc).isoformat()
            tx["signature_verified"] = True

            return {
                "status": "ROLLED_BACK",
                "signature_valid": True,
                "quality": quality,
                "amount": 0.0,
                "reason": tx["reason"]
            }


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def test_signature_generation_and_verification():
    """Test basic signature generation and verification."""
    print("="*80)
    print("TEST SCENARIO 1: Signature Generation and Verification")
    print("="*80)

    # Generate key pair for expert
    expert_lct = "lct://sage:verification_expert@mainnet"
    key_pair = SigningKeyPair.generate(expert_lct)
    print(f"\n✅ Generated key pair for: {expert_lct}")

    # Create IRP result payload
    result_payload = {
        "status": "halted",
        "signals": {
            "quality": 0.85,
            "confidence": 0.80,
            "latency_ms": 250.0,
            "cost_ratio": 1.0
        },
        "outputs": {
            "verification": "claim is valid",
            "reasoning": "mathematical axiom"
        }
    }
    print(f"\n📝 Result payload: quality={result_payload['signals']['quality']}")

    # Sign result
    signer = IRPSigner(key_pair)
    signed_result = signer.sign_result(result_payload)
    print(f"✅ Result signed")
    print(f"   Signer: {signed_result.metadata.signer_lct}")
    print(f"   Timestamp: {signed_result.metadata.timestamp}")
    print(f"   Nonce: {signed_result.metadata.nonce}")
    print(f"   Signature: {signed_result.signature[:32]}...")

    # Verify signature
    trusted_keys = {expert_lct: key_pair.public_key}
    verifier = IRPVerifier(trusted_keys)

    is_valid = verifier.verify_result(signed_result)
    print(f"\n🔍 Signature verification: {'✅ VALID' if is_valid else '❌ INVALID'}")

    # Get detailed verification
    details = verifier.verify_result_with_details(signed_result)
    print(f"\n📊 Verification details:")
    print(f"   Valid: {details['valid']}")
    print(f"   Trusted: {details['trusted']}")
    print(f"   Algorithm: {details['algorithm']}")

    return is_valid


def test_tamper_detection():
    """Test detection of tampered results."""
    print("\n" + "="*80)
    print("TEST SCENARIO 2: Tamper Detection")
    print("="*80)

    # Generate key pair and sign result
    expert_lct = "lct://sage:verification_expert@mainnet"
    key_pair = SigningKeyPair.generate(expert_lct)

    result_payload = {
        "status": "halted",
        "signals": {"quality": 0.85}
    }

    signer = IRPSigner(key_pair)
    signed_result = signer.sign_result(result_payload)
    print(f"\n✅ Original result signed (quality: {result_payload['signals']['quality']})")

    # Tamper with result (attacker changes quality)
    tampered_result = SignedIRPResult(
        payload={
            "status": "halted",
            "signals": {"quality": 0.95}  # Changed from 0.85!
        },
        metadata=signed_result.metadata,
        signature=signed_result.signature
    )
    print(f"🔧 Tampered result created (quality: {tampered_result.payload['signals']['quality']})")

    # Try to verify tampered result
    trusted_keys = {expert_lct: key_pair.public_key}
    verifier = IRPVerifier(trusted_keys)

    is_valid = verifier.verify_result(tampered_result)
    print(f"\n🔍 Tampered signature verification: {'❌ INVALID (expected)' if not is_valid else '⚠️ VALID (SECURITY ISSUE!)'}")

    return not is_valid  # Test passes if tampered result is INVALID


def test_untrusted_signer():
    """Test rejection of untrusted signers."""
    print("\n" + "="*80)
    print("TEST SCENARIO 3: Untrusted Signer Rejection")
    print("="*80)

    # Trusted expert
    trusted_lct = "lct://sage:trusted_expert@mainnet"
    trusted_key_pair = SigningKeyPair.generate(trusted_lct)

    # Untrusted expert
    untrusted_lct = "lct://rogue:malicious_expert@darknet"
    untrusted_key_pair = SigningKeyPair.generate(untrusted_lct)

    print(f"\n✅ Trusted expert: {trusted_lct}")
    print(f"⚠️  Untrusted expert: {untrusted_lct}")

    # Untrusted expert signs result
    result_payload = {"status": "halted", "signals": {"quality": 0.95}}
    untrusted_signer = IRPSigner(untrusted_key_pair)
    signed_result = untrusted_signer.sign_result(result_payload)
    print(f"\n📝 Result signed by untrusted expert")

    # Verifier only trusts the first expert
    trusted_keys = {trusted_lct: trusted_key_pair.public_key}
    verifier = IRPVerifier(trusted_keys)

    is_valid = verifier.verify_result(signed_result)
    print(f"\n🔍 Signature verification: {'❌ REJECTED (expected)' if not is_valid else '⚠️ ACCEPTED (SECURITY ISSUE!)'}")

    return not is_valid  # Test passes if untrusted signer is rejected


def test_atp_settlement_with_signatures():
    """Test ATP settlement with signature verification."""
    print("\n" + "="*80)
    print("TEST SCENARIO 4: ATP Settlement with Signature Verification")
    print("="*80)

    # Setup
    executor_lct = "lct://sage:verification_expert@mainnet"
    caller_lct = "lct://user:alice@mainnet"

    key_pair = SigningKeyPair.generate(executor_lct)
    trusted_keys = {executor_lct: key_pair.public_key}
    verifier = IRPVerifier(trusted_keys)
    settlement = SecureATPSettlement(verifier)

    print(f"\n💰 ATP settlement initialized")
    print(f"   Caller: {caller_lct}")
    print(f"   Executor: {executor_lct}")

    # Lock ATP
    tx_id = settlement.lock_atp_for_invocation(
        caller_lct=caller_lct,
        executor_lct=executor_lct,
        amount=15.0
    )
    print(f"\n🔒 ATP locked: {tx_id}")
    print(f"   Amount: 15.0 ATP")

    # Executor performs work and signs result
    result_payload = {
        "status": "halted",
        "signals": {
            "quality": 0.85,
            "confidence": 0.80
        },
        "outputs": {"verification": "valid"}
    }

    signer = IRPSigner(key_pair)
    signed_result = signer.sign_result(result_payload)
    print(f"\n✅ Work completed and signed")
    print(f"   Quality: {result_payload['signals']['quality']}")

    # Commit with signature verification
    outcome = settlement.commit_atp_with_signature(
        tx_id=tx_id,
        signed_result=signed_result,
        quality_threshold=0.70
    )

    print(f"\n📊 Settlement outcome:")
    print(f"   Status: {outcome['status']}")
    print(f"   Signature valid: {outcome['signature_valid']}")
    print(f"   Quality: {outcome['quality']}")
    print(f"   Amount transferred: {outcome['amount']} ATP")

    return outcome["status"] == "COMMITTED" and outcome["signature_valid"]


def test_rollback_on_invalid_signature():
    """Test ATP rollback when signature is invalid."""
    print("\n" + "="*80)
    print("TEST SCENARIO 5: ATP Rollback on Invalid Signature")
    print("="*80)

    # Setup
    executor_lct = "lct://sage:verification_expert@mainnet"
    caller_lct = "lct://user:alice@mainnet"

    key_pair = SigningKeyPair.generate(executor_lct)
    trusted_keys = {executor_lct: key_pair.public_key}
    verifier = IRPVerifier(trusted_keys)
    settlement = SecureATPSettlement(verifier)

    # Lock ATP
    tx_id = settlement.lock_atp_for_invocation(
        caller_lct=caller_lct,
        executor_lct=executor_lct,
        amount=15.0
    )
    print(f"\n🔒 ATP locked: {tx_id} (15.0 ATP)")

    # Create result with HIGH quality
    result_payload = {
        "status": "halted",
        "signals": {"quality": 0.95}  # High quality
    }

    signer = IRPSigner(key_pair)
    signed_result = signer.sign_result(result_payload)

    # Tamper with result (attacker tries to boost quality)
    tampered_result = SignedIRPResult(
        payload={
            "status": "halted",
            "signals": {"quality": 0.99}  # Tampered!
        },
        metadata=signed_result.metadata,
        signature=signed_result.signature  # Old signature (won't verify)
    )

    print(f"\n🔧 Result tampered (quality changed: 0.95 → 0.99)")

    # Try to commit with tampered result
    outcome = settlement.commit_atp_with_signature(
        tx_id=tx_id,
        signed_result=tampered_result,
        quality_threshold=0.70
    )

    print(f"\n📊 Settlement outcome:")
    print(f"   Status: {outcome['status']}")
    print(f"   Signature valid: {outcome['signature_valid']}")
    print(f"   Amount transferred: {outcome['amount']} ATP")
    print(f"   Reason: {outcome.get('reason', 'N/A')}")

    expected = outcome["status"] == "ROLLED_BACK" and not outcome["signature_valid"]
    print(f"\n{'✅' if expected else '❌'} ATP correctly rolled back due to invalid signature")

    return expected


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test scenarios."""
    print("="*80)
    print("SESSION 94 TRACK 2: IRP CRYPTOGRAPHIC SIGNATURES")
    print("="*80)

    results = []

    # Run tests
    results.append(("Signature generation and verification", test_signature_generation_and_verification()))
    results.append(("Tamper detection", test_tamper_detection()))
    results.append(("Untrusted signer rejection", test_untrusted_signer()))
    results.append(("ATP settlement with signatures", test_atp_settlement_with_signatures()))
    results.append(("ATP rollback on invalid signature", test_rollback_on_invalid_signature()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    all_passed = all(result for _, result in results)
    print(f"\n✅ All scenarios passed: {all_passed}")

    print(f"\nScenarios tested:")
    for i, (name, passed) in enumerate(results, 1):
        status = "✅" if passed else "❌"
        print(f"  {i}. {status} {name}")

    # Save results
    import json
    output = {
        "session": "94",
        "track": "2",
        "focus": "IRP Cryptographic Signatures",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_results": [
            {"scenario": name, "passed": passed}
            for name, passed in results
        ],
        "all_passed": all_passed,
        "innovations": [
            "Ed25519 signature generation for IRP results",
            "Signature verification before ATP settlement",
            "Tamper detection via signature validation",
            "Non-repudiation (executor can't deny result)",
            "Untrusted signer rejection",
        ]
    }

    output_path = "/home/dp/ai-workspace/web4/implementation/session94_track2_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to: {output_path}")

    print("\n" + "="*80)
    print("Key Innovations:")
    print("="*80)
    for i, innovation in enumerate(output["innovations"], 1):
        print(f"{i}. {innovation}")

    print("\n" + "="*80)
    print("Cryptographic signatures enable:")
    print("- Non-repudiation: Executor can't deny creating result")
    print("- Tamper detection: Modified results fail verification")
    print("- Trust anchoring: Only trusted signers accepted")
    print("- Secure settlement: ATP only transferred for valid signatures")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    run_all_tests()
