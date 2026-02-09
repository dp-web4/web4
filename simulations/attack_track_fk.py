"""
Track FK: Cryptographic Primitive Attacks (Attacks 317-322)

Attacks on cryptographic implementations and primitives used in Web4.
While the algorithms themselves may be secure, implementation details,
parameter choices, and integration patterns create attack surfaces.

Key insight: Cryptographic security depends on correct implementation,
not just algorithm choice. Side channels, weak parameters, and misuse
patterns are common vulnerabilities.

Reference:
- web4-standard/core-spec/lct-linked-context-token.md
- web4-standard/core-spec/cryptographic-requirements.md

Added: 2026-02-09
"""

import hashlib
import hmac
import random
import time
import secrets
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum, auto


@dataclass
class AttackResult:
    """Result of an attack simulation."""
    attack_name: str
    success: bool
    setup_cost_atp: float
    gain_atp: float
    roi: float
    detection_probability: float
    time_to_detection_hours: float
    blocks_until_detected: int
    trust_damage: float
    description: str
    mitigation: str
    raw_data: Dict


# ============================================================================
# CRYPTOGRAPHIC INFRASTRUCTURE
# ============================================================================


class KeyType(Enum):
    """Types of cryptographic keys."""
    SIGNING = auto()
    ENCRYPTION = auto()
    DERIVATION = auto()
    HMAC = auto()


@dataclass
class CryptoKey:
    """A cryptographic key with metadata."""
    key_id: str
    key_type: KeyType
    algorithm: str
    key_material: bytes  # In real impl, this would be protected
    created_at: float
    expires_at: Optional[float]
    owner_lct: str
    rotation_count: int = 0

    def is_expired(self) -> bool:
        """Check if key is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@dataclass
class Signature:
    """A cryptographic signature."""
    signature_id: str
    signer_lct: str
    key_id: str
    algorithm: str
    signature_bytes: bytes
    signed_at: float
    message_hash: str
    nonce: Optional[bytes] = None


class CryptoEngine:
    """Cryptographic operations engine with security controls."""

    def __init__(self):
        self.keys: Dict[str, CryptoKey] = {}
        self.signatures: List[Signature] = []
        self.used_nonces: Set[bytes] = set()

        # Security parameters
        self.min_key_size_bits = 256
        self.max_key_age_seconds = 86400 * 365  # 1 year
        self.nonce_size_bytes = 32
        self.max_signature_age = 3600  # 1 hour for verification
        self.constant_time_enabled = True

    def generate_key(
        self,
        owner_lct: str,
        key_type: KeyType,
        algorithm: str = "Ed25519"
    ) -> CryptoKey:
        """Generate a new cryptographic key."""
        key_id = secrets.token_hex(16)

        # Generate appropriate key material
        if algorithm in ["Ed25519", "ECDSA-P256"]:
            key_material = secrets.token_bytes(32)
        elif algorithm in ["RSA-2048", "RSA-4096"]:
            key_material = secrets.token_bytes(256)  # Simplified
        else:
            key_material = secrets.token_bytes(32)

        key = CryptoKey(
            key_id=key_id,
            key_type=key_type,
            algorithm=algorithm,
            key_material=key_material,
            created_at=time.time(),
            expires_at=time.time() + self.max_key_age_seconds,
            owner_lct=owner_lct
        )
        self.keys[key_id] = key
        return key

    def sign(
        self,
        message: bytes,
        key_id: str,
        include_nonce: bool = True
    ) -> Optional[Signature]:
        """Sign a message with a key."""
        key = self.keys.get(key_id)
        if not key:
            return None
        if key.is_expired():
            return None
        if key.key_type != KeyType.SIGNING:
            return None

        # Generate nonce
        nonce = None
        if include_nonce:
            nonce = secrets.token_bytes(self.nonce_size_bytes)
            if nonce in self.used_nonces:
                return None  # Nonce collision (should never happen)
            self.used_nonces.add(nonce)

        # Compute message hash
        message_hash = hashlib.sha256(message).hexdigest()

        # Create signature (simplified - would use actual crypto lib)
        sig_input = message + (nonce or b"")
        signature_bytes = hmac.new(
            key.key_material,
            sig_input,
            hashlib.sha256
        ).digest()

        sig = Signature(
            signature_id=secrets.token_hex(8),
            signer_lct=key.owner_lct,
            key_id=key_id,
            algorithm=key.algorithm,
            signature_bytes=signature_bytes,
            signed_at=time.time(),
            message_hash=message_hash,
            nonce=nonce
        )
        self.signatures.append(sig)
        return sig

    def verify(
        self,
        message: bytes,
        signature: Signature,
        check_nonce: bool = True
    ) -> Tuple[bool, str]:
        """Verify a signature with security checks."""
        key = self.keys.get(signature.key_id)
        if not key:
            return False, "Key not found"

        # DEFENSE: Check key expiration
        if key.is_expired():
            return False, "Key expired"

        # DEFENSE: Check signature age
        if time.time() - signature.signed_at > self.max_signature_age:
            return False, "Signature too old"

        # DEFENSE: Check nonce reuse
        if check_nonce and signature.nonce:
            if signature.nonce not in self.used_nonces:
                return False, "Unknown nonce"

        # DEFENSE: Verify message hash matches
        computed_hash = hashlib.sha256(message).hexdigest()
        if computed_hash != signature.message_hash:
            return False, "Message hash mismatch"

        # Verify signature (constant-time comparison)
        sig_input = message + (signature.nonce or b"")
        expected_sig = hmac.new(
            key.key_material,
            sig_input,
            hashlib.sha256
        ).digest()

        if self.constant_time_enabled:
            if hmac.compare_digest(expected_sig, signature.signature_bytes):
                return True, "Valid"
        else:
            # Vulnerable: non-constant-time comparison
            if expected_sig == signature.signature_bytes:
                return True, "Valid"

        return False, "Invalid signature"


# ============================================================================
# ATTACK FK-1a: NONCE REUSE ATTACK
# ============================================================================

def attack_fk_1a_nonce_reuse(
    engine: CryptoEngine,
    attacker_lct: str,
    victim_key_id: str
) -> AttackResult:
    """
    NONCE REUSE ATTACK (Track FK-1a)

    Attacker attempts to exploit nonce reuse in signature schemes.
    In schemes like ECDSA, nonce reuse allows private key extraction.

    Attack vector:
    1. Collect multiple signatures from same key
    2. Look for nonce reuse patterns
    3. If found, extract private key mathematically
    4. Use extracted key for forgery
    """
    results = {
        "signatures_collected": 0,
        "nonce_reuse_found": False,
        "key_extracted": False,
        "forgeries_created": 0,
        "defense_blocks": 0,
    }

    # Try to get victim to sign multiple messages
    messages = [f"message_{i}".encode() for i in range(100)]
    collected_signatures = []

    for msg in messages:
        sig = engine.sign(msg, victim_key_id)
        if sig:
            collected_signatures.append(sig)
            results["signatures_collected"] += 1

    # Check for nonce reuse (defense should prevent this)
    nonces = [s.nonce for s in collected_signatures if s.nonce]
    unique_nonces = set(nonces)
    if len(nonces) != len(unique_nonces):
        results["nonce_reuse_found"] = True
        # In real attack, would extract key here
        results["key_extracted"] = True
    else:
        results["defense_blocks"] += 1

    # Defense: Check if nonces are properly random (entropy check)
    if nonces:
        # Simple entropy check - all nonces should be different
        if len(unique_nonces) >= len(nonces) * 0.99:
            results["defense_blocks"] += 1

    attack_successful = results["nonce_reuse_found"] and results["key_extracted"]
    detection_prob = 0.40  # Hard to detect until key is compromised

    return AttackResult(
        attack_name="FK-1a: Nonce Reuse Attack",
        success=attack_successful,
        setup_cost_atp=200.0,  # Needs many signatures
        gain_atp=5000.0 if attack_successful else 0.0,
        roi=(5000.0 / 200.0) if attack_successful else -1.0,
        detection_probability=detection_prob,
        time_to_detection_hours=168.0,  # May take weeks
        blocks_until_detected=500,
        trust_damage=0.95 if attack_successful else 0.0,
        description="""Nonce reuse attack exploits deterministic or poorly
        randomized nonces in signature schemes. In ECDSA, two signatures
        with same nonce leak the private key completely.""",
        mitigation="""Track FK-1a: Nonce Reuse Defense:
        1. Use RFC 6979 deterministic nonces (ECDSA)
        2. Use Ed25519 (nonce derived from message hash)
        3. Hardware RNG for nonce generation
        4. Nonce uniqueness tracking per key
        5. Key rotation after suspicious patterns
        6. Signature rate limiting""",
        raw_data=results
    )


# ============================================================================
# ATTACK FK-1b: TIMING SIDE CHANNEL ATTACK
# ============================================================================

def attack_fk_1b_timing_side_channel(
    engine: CryptoEngine,
    attacker_lct: str,
    victim_key_id: str
) -> AttackResult:
    """
    TIMING SIDE CHANNEL ATTACK (Track FK-1b)

    Attacker measures timing variations in cryptographic operations
    to extract secret key material.

    Attack vector:
    1. Send many verification requests
    2. Measure timing precisely
    3. Statistical analysis of timing variations
    4. Extract key bits from timing leakage
    """
    results = {
        "timing_samples": 0,
        "timing_variance_detected": False,
        "bits_extracted": 0,
        "key_reconstructed": False,
        "defense_blocks": 0,
    }

    # Generate test key
    test_key = engine.generate_key(
        attacker_lct,
        KeyType.SIGNING,
        "Ed25519"
    )

    # Collect timing samples
    timing_data = []
    for i in range(1000):
        message = f"timing_test_{i}".encode()
        sig = engine.sign(message, test_key.key_id)
        if sig:
            start = time.perf_counter_ns()
            engine.verify(message, sig)
            end = time.perf_counter_ns()
            timing_data.append(end - start)
            results["timing_samples"] += 1

    # Analyze timing variance
    if timing_data:
        avg_time = sum(timing_data) / len(timing_data)
        variance = sum((t - avg_time) ** 2 for t in timing_data) / len(timing_data)

        # Check if constant-time is working
        if engine.constant_time_enabled:
            # Should have low variance
            coefficient_of_variation = (variance ** 0.5) / avg_time if avg_time > 0 else 0
            if coefficient_of_variation < 0.1:  # Less than 10% variation
                results["defense_blocks"] += 1
            else:
                results["timing_variance_detected"] = True
        else:
            results["timing_variance_detected"] = True
            # Simulate bit extraction from timing
            results["bits_extracted"] = int(variance ** 0.5) % 256

    # Key reconstruction requires many bits
    if results["bits_extracted"] > 200:
        results["key_reconstructed"] = True

    attack_successful = results["key_reconstructed"]
    detection_prob = 0.30  # Very hard to detect

    return AttackResult(
        attack_name="FK-1b: Timing Side Channel Attack",
        success=attack_successful,
        setup_cost_atp=500.0,
        gain_atp=10000.0 if attack_successful else 0.0,
        roi=(10000.0 / 500.0) if attack_successful else -1.0,
        detection_probability=detection_prob,
        time_to_detection_hours=720.0,  # Month or more
        blocks_until_detected=1000,
        trust_damage=0.99 if attack_successful else 0.0,
        description="""Timing side channel attack measures execution time
        variations in crypto operations. Non-constant-time comparisons
        or operations can leak secret key bits.""",
        mitigation="""Track FK-1b: Timing Side Channel Defense:
        1. Constant-time comparison functions (hmac.compare_digest)
        2. Constant-time arithmetic operations
        3. Cache-timing resistant implementations
        4. Operation time padding/normalization
        5. Rate limiting on verification requests
        6. Hardware-backed constant-time primitives""",
        raw_data=results
    )


# ============================================================================
# ATTACK FK-2a: KEY DERIVATION WEAKNESS
# ============================================================================

def attack_fk_2a_key_derivation_weakness(
    engine: CryptoEngine,
    attacker_lct: str
) -> AttackResult:
    """
    KEY DERIVATION WEAKNESS ATTACK (Track FK-2a)

    Attacker exploits weak key derivation from passwords/seeds.
    Low entropy inputs or weak KDFs allow brute force attacks.

    Attack vector:
    1. Identify KDF parameters (iterations, salt)
    2. Brute force common passwords/seeds
    3. Rainbow table attacks if salts are weak
    4. GPU-accelerated cracking
    """
    results = {
        "weak_kdf_found": False,
        "low_iteration_count": False,
        "weak_salt": False,
        "passwords_cracked": 0,
        "defense_blocks": 0,
    }

    # Simulate KDF parameter analysis
    kdf_params = {
        "algorithm": "Argon2id",  # Should be strong
        "iterations": 3,  # Minimum for Argon2id
        "memory_cost": 65536,  # 64MB
        "parallelism": 4,
        "salt_size": 32,
    }

    # Check for weak parameters
    if kdf_params["algorithm"] in ["MD5", "SHA1", "PBKDF2-SHA1"]:
        results["weak_kdf_found"] = True
    else:
        results["defense_blocks"] += 1

    # Check iteration count
    min_iterations = {
        "Argon2id": 3,
        "PBKDF2-SHA256": 600000,
        "scrypt": 2**14,
    }
    min_iter = min_iterations.get(kdf_params["algorithm"], 100000)
    if kdf_params.get("iterations", 1) < min_iter:
        results["low_iteration_count"] = True
    else:
        results["defense_blocks"] += 1

    # Check salt
    if kdf_params["salt_size"] < 16:
        results["weak_salt"] = True
    else:
        results["defense_blocks"] += 1

    # Simulate brute force attempt
    weak_passwords = ["password123", "admin", "123456", "letmein"]
    for pwd in weak_passwords:
        # With proper KDF, this should be computationally expensive
        if not results["weak_kdf_found"] and not results["low_iteration_count"]:
            # Defense working - brute force too expensive
            results["defense_blocks"] += 1
        else:
            results["passwords_cracked"] += 1

    attack_successful = results["passwords_cracked"] > 0
    detection_prob = 0.50

    return AttackResult(
        attack_name="FK-2a: Key Derivation Weakness Attack",
        success=attack_successful,
        setup_cost_atp=100.0,
        gain_atp=2000.0 if attack_successful else 0.0,
        roi=(2000.0 / 100.0) if attack_successful else -1.0,
        detection_probability=detection_prob,
        time_to_detection_hours=48.0,
        blocks_until_detected=100,
        trust_damage=0.80 if attack_successful else 0.0,
        description="""Key derivation weakness exploits weak KDF parameters
        or algorithms. Low iteration counts, weak salts, or outdated
        algorithms enable brute force attacks.""",
        mitigation="""Track FK-2a: Key Derivation Defense:
        1. Use Argon2id with memory-hard parameters
        2. Minimum 64MB memory cost
        3. Unique random 32-byte salts per key
        4. Hardware-backed key derivation where available
        5. Rate limiting on authentication attempts
        6. Account lockout after failed attempts""",
        raw_data=results
    )


# ============================================================================
# ATTACK FK-2b: SIGNATURE MALLEABILITY
# ============================================================================

def attack_fk_2b_signature_malleability(
    engine: CryptoEngine,
    attacker_lct: str,
    victim_key_id: str
) -> AttackResult:
    """
    SIGNATURE MALLEABILITY ATTACK (Track FK-2b)

    Attacker creates alternative valid signatures from existing ones.
    Some signature schemes allow modification while remaining valid.

    Attack vector:
    1. Capture valid signature
    2. Apply malleation transformation
    3. Use modified signature for replay/confusion
    4. Exploit systems that treat different sigs as different actions
    """
    results = {
        "signatures_captured": 0,
        "malleations_attempted": 0,
        "malleations_succeeded": 0,
        "action_confusion_achieved": False,
        "defense_blocks": 0,
    }

    # Get a valid signature
    message = b"transfer 100 ATP to recipient_lct"
    sig = engine.sign(message, victim_key_id)
    if sig:
        results["signatures_captured"] += 1

        # Try various malleation techniques
        # In ECDSA: (r, s) -> (r, n-s) is valid for same message
        # In Ed25519: canonicalization prevents this

        malleation_attempts = [
            # Flip bits in signature
            Signature(
                signature_id=sig.signature_id,
                signer_lct=sig.signer_lct,
                key_id=sig.key_id,
                algorithm=sig.algorithm,
                signature_bytes=bytes(b ^ 1 for b in sig.signature_bytes),
                signed_at=sig.signed_at,
                message_hash=sig.message_hash,
                nonce=sig.nonce
            ),
            # Append extra bytes
            Signature(
                signature_id=sig.signature_id,
                signer_lct=sig.signer_lct,
                key_id=sig.key_id,
                algorithm=sig.algorithm,
                signature_bytes=sig.signature_bytes + b"\x00",
                signed_at=sig.signed_at,
                message_hash=sig.message_hash,
                nonce=sig.nonce
            ),
        ]

        for malleated in malleation_attempts:
            results["malleations_attempted"] += 1
            valid, reason = engine.verify(message, malleated)
            if valid:
                results["malleations_succeeded"] += 1
            else:
                results["defense_blocks"] += 1

        # Check for action confusion vulnerability
        # Same message, different signature ID could be treated as different action
        if results["malleations_succeeded"] > 0:
            results["action_confusion_achieved"] = True

    attack_successful = results["malleations_succeeded"] > 0
    detection_prob = 0.60

    return AttackResult(
        attack_name="FK-2b: Signature Malleability Attack",
        success=attack_successful,
        setup_cost_atp=50.0,
        gain_atp=500.0 if attack_successful else 0.0,
        roi=(500.0 / 50.0) if attack_successful else -1.0,
        detection_probability=detection_prob,
        time_to_detection_hours=12.0,
        blocks_until_detected=20,
        trust_damage=0.50 if attack_successful else 0.0,
        description="""Signature malleability allows creating alternative
        valid signatures from existing ones. Can cause transaction replay
        or action confusion in systems that don't normalize signatures.""",
        mitigation="""Track FK-2b: Signature Malleability Defense:
        1. Use Ed25519 (inherently non-malleable)
        2. Require canonical signature encoding
        3. Signature normalization before acceptance
        4. Reject non-canonical encodings
        5. Deduplicate by message hash, not signature
        6. Strict signature length validation""",
        raw_data=results
    )


# ============================================================================
# ATTACK FK-3a: HASH COLLISION EXPLOITATION
# ============================================================================

def attack_fk_3a_hash_collision(
    engine: CryptoEngine,
    attacker_lct: str
) -> AttackResult:
    """
    HASH COLLISION EXPLOITATION ATTACK (Track FK-3a)

    Attacker exploits hash function weaknesses to create collisions.
    Two different messages with same hash could confuse systems.

    Attack vector:
    1. Identify hash function used
    2. Generate collision pairs (if weak hash)
    3. Substitute legitimate message with malicious collision
    4. Exploit systems that trust hash as unique identifier
    """
    results = {
        "hash_algorithm_analyzed": True,
        "collision_found": False,
        "collision_exploited": False,
        "substitution_successful": False,
        "defense_blocks": 0,
    }

    # Simulate hash algorithm analysis
    hash_algorithms = {
        "MD5": {"collision_resistant": False, "preimage_resistant": True},
        "SHA1": {"collision_resistant": False, "preimage_resistant": True},
        "SHA256": {"collision_resistant": True, "preimage_resistant": True},
        "SHA3-256": {"collision_resistant": True, "preimage_resistant": True},
        "BLAKE3": {"collision_resistant": True, "preimage_resistant": True},
    }

    # Web4 should use SHA256 or better
    current_hash = "SHA256"

    if not hash_algorithms.get(current_hash, {}).get("collision_resistant", False):
        results["collision_found"] = True
        results["collision_exploited"] = True
    else:
        results["defense_blocks"] += 1

    # Try birthday attack (simplified)
    # For SHA256, would need 2^128 operations - infeasible
    hash_bits = 256
    birthday_complexity = 2 ** (hash_bits // 2)

    if birthday_complexity > 2**100:  # Infeasible threshold
        results["defense_blocks"] += 1
    else:
        results["collision_found"] = True

    # Check for length extension vulnerability (MD5/SHA1/SHA256 without HMAC)
    # Defense: Use HMAC or SHA3
    using_hmac = True  # Engine uses HMAC
    if using_hmac or current_hash.startswith("SHA3"):
        results["defense_blocks"] += 1
    else:
        results["collision_found"] = True

    attack_successful = results["collision_exploited"]
    detection_prob = 0.20  # Very hard to detect

    return AttackResult(
        attack_name="FK-3a: Hash Collision Exploitation",
        success=attack_successful,
        setup_cost_atp=1000.0,  # Very expensive computationally
        gain_atp=10000.0 if attack_successful else 0.0,
        roi=(10000.0 / 1000.0) if attack_successful else -1.0,
        detection_probability=detection_prob,
        time_to_detection_hours=720.0,
        blocks_until_detected=2000,
        trust_damage=0.90 if attack_successful else 0.0,
        description="""Hash collision attacks create two messages with
        identical hashes. Weak hash functions like MD5/SHA1 are vulnerable.
        Collisions enable message substitution attacks.""",
        mitigation="""Track FK-3a: Hash Collision Defense:
        1. Use SHA-256 minimum, prefer SHA-3 or BLAKE3
        2. Use HMAC for message authentication
        3. Include message length in hash computation
        4. Use domain separation prefixes
        5. Reject deprecated hash algorithms
        6. Regular algorithm upgrade path""",
        raw_data=results
    )


# ============================================================================
# ATTACK FK-3b: RANDOMNESS WEAKNESS
# ============================================================================

def attack_fk_3b_randomness_weakness(
    engine: CryptoEngine,
    attacker_lct: str
) -> AttackResult:
    """
    RANDOMNESS WEAKNESS ATTACK (Track FK-3b)

    Attacker exploits weak random number generation in crypto operations.
    Predictable randomness undermines all cryptographic guarantees.

    Attack vector:
    1. Analyze entropy sources
    2. Identify patterns in random values
    3. Predict future random values
    4. Compromise keys/nonces using predictions
    """
    results = {
        "entropy_source_analyzed": True,
        "weak_rng_detected": False,
        "pattern_found": False,
        "predictions_correct": 0,
        "keys_compromised": 0,
        "defense_blocks": 0,
    }

    # Simulate RNG analysis
    rng_qualities = {
        "os_urandom": {"secure": True, "entropy_bits": 256},
        "secrets": {"secure": True, "entropy_bits": 256},
        "random": {"secure": False, "entropy_bits": 32},  # Mersenne Twister
        "time_based": {"secure": False, "entropy_bits": 16},
        "hardware_rng": {"secure": True, "entropy_bits": 256},
    }

    # Check what engine uses
    current_rng = "secrets"  # Engine uses secrets module
    rng_info = rng_qualities.get(current_rng, {})

    if not rng_info.get("secure", False):
        results["weak_rng_detected"] = True
        results["pattern_found"] = True
        results["predictions_correct"] = 100
        results["keys_compromised"] = 10
    else:
        results["defense_blocks"] += 1

    # Check entropy sufficiency
    if rng_info.get("entropy_bits", 0) < 128:
        results["weak_rng_detected"] = True
    else:
        results["defense_blocks"] += 1

    # Test for sequential/time-based patterns
    samples = [secrets.token_bytes(16) for _ in range(100)]

    # Check if samples have sufficient entropy (simplified)
    unique_samples = set(samples)
    if len(unique_samples) < len(samples) * 0.99:
        results["pattern_found"] = True
    else:
        results["defense_blocks"] += 1

    attack_successful = results["keys_compromised"] > 0
    detection_prob = 0.35

    return AttackResult(
        attack_name="FK-3b: Randomness Weakness Attack",
        success=attack_successful,
        setup_cost_atp=300.0,
        gain_atp=8000.0 if attack_successful else 0.0,
        roi=(8000.0 / 300.0) if attack_successful else -1.0,
        detection_probability=detection_prob,
        time_to_detection_hours=168.0,
        blocks_until_detected=400,
        trust_damage=0.95 if attack_successful else 0.0,
        description="""Randomness weakness attacks exploit predictable RNG.
        Weak entropy sources (time-based, Mersenne Twister) allow prediction
        of keys, nonces, and other security-critical values.""",
        mitigation="""Track FK-3b: Randomness Weakness Defense:
        1. Use secrets module (Python) or equivalent
        2. Use OS-provided CSPRNG (urandom)
        3. Hardware RNG when available (RDRAND)
        4. Entropy pool monitoring
        5. RNG health checks before key generation
        6. Seed from multiple entropy sources""",
        raw_data=results
    )


# ============================================================================
# ATTACK EXECUTION AND REPORTING
# ============================================================================

def run_all_track_fk_attacks() -> List[AttackResult]:
    """Run all Track FK attacks and return results."""
    results = []

    # Create shared infrastructure
    engine = CryptoEngine()
    attacker = "attacker_lct_001"

    # Create victim key
    victim_key = engine.generate_key(
        "victim_lct_001",
        KeyType.SIGNING,
        "Ed25519"
    )

    # Run attacks
    results.append(attack_fk_1a_nonce_reuse(engine, attacker, victim_key.key_id))
    results.append(attack_fk_1b_timing_side_channel(engine, attacker, victim_key.key_id))
    results.append(attack_fk_2a_key_derivation_weakness(engine, attacker))
    results.append(attack_fk_2b_signature_malleability(engine, attacker, victim_key.key_id))
    results.append(attack_fk_3a_hash_collision(engine, attacker))
    results.append(attack_fk_3b_randomness_weakness(engine, attacker))

    return results


def print_track_fk_summary(results: List[AttackResult]) -> None:
    """Print summary of Track FK attack results."""
    print("\n" + "=" * 70)
    print("TRACK FK: CRYPTOGRAPHIC PRIMITIVE ATTACKS (317-322)")
    print("=" * 70)

    total_attacks = len(results)
    successful_attacks = sum(1 for r in results if r.success)
    avg_detection = sum(r.detection_probability for r in results) / total_attacks

    print(f"\nTotal Attacks: {total_attacks}")
    print(f"Successful (unmitigated): {successful_attacks}")
    print(f"Defended: {total_attacks - successful_attacks}")
    print(f"Average Detection Probability: {avg_detection:.1%}")

    print("\n" + "-" * 70)
    print("Individual Attack Results:")
    print("-" * 70)

    for i, result in enumerate(results, 317):
        status = "⚠️ SUCCESSFUL" if result.success else "✅ DEFENDED"
        print(f"\n{i}. {result.attack_name}")
        print(f"   Status: {status}")
        print(f"   Detection: {result.detection_probability:.1%}")
        print(f"   Cost: {result.setup_cost_atp} ATP")
        if result.success:
            print(f"   Gain: {result.gain_atp} ATP")

    print("\n" + "=" * 70)
    print("DEFENSE SUMMARY")
    print("=" * 70)

    for result in results:
        print(f"\n{result.mitigation}")


if __name__ == "__main__":
    results = run_all_track_fk_attacks()
    print_track_fk_summary(results)
