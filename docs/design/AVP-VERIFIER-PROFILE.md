# AVP Verifier Profile

**Version**: 1.0.0
**Date**: 2026-01-04
**Status**: Implementation Guide
**Canonical Spec**: [ALIVENESS-VERIFICATION-PROTOCOL.md](./ALIVENESS-VERIFICATION-PROTOCOL.md)

---

## Purpose

This document is a focused implementation guide for entities that need to **verify** aliveness proofs. It extracts the essential information from the full AVP specification.

**Audience**: Banks, DAOs, agents, services, and any entity that needs to verify another entity's hardware binding.

---

## 1. The One Rule

> **NEVER trust `proof.public_key`. ALWAYS use the public key from the target's LCT.**

The proof contains a signature. The LCT contains the expected public key. Verify the signature against the LCT's key, not the proof's key. This is non-negotiable.

```python
# WRONG - vulnerable to key substitution
verify(proof.public_key, proof.signature, payload)

# CORRECT - uses known-good key from LCT
verify(target_lct.binding.public_key, proof.signature, payload)
```

---

## 2. Canonical Payload Format

When verifying, you must reconstruct the same payload the prover signed:

```python
def get_signing_payload(challenge: AlivenessChallenge) -> bytes:
    """Reconstruct the canonical payload for verification."""
    components = [
        b"AVP-1.1",                                    # Protocol version
        challenge.challenge_id.encode('utf-8'),
        challenge.nonce,                               # 32 random bytes
        (challenge.verifier_lct_id or "").encode('utf-8'),
        challenge.expires_at.isoformat().encode('utf-8'),
        (challenge.session_id or "").encode('utf-8'),
        bytes.fromhex(challenge.intended_action_hash) if challenge.intended_action_hash else b"",
        (challenge.purpose or "").encode('utf-8'),
    ]

    hasher = hashlib.sha256()
    for component in components:
        hasher.update(component)
    return hasher.digest()
```

**All fields matter**. If any field differs between challenge and verification, the signature will fail.

---

## 3. Verification Steps

```python
def verify_aliveness(
    challenge: AlivenessChallenge,
    proof: AlivenessProof,
    target_lct: LCT
) -> AlivenessVerificationResult:

    # 1. Check freshness
    now = datetime.now(timezone.utc)
    if now > challenge.expires_at:
        return failure(CHALLENGE_EXPIRED)

    # 2. Check challenge correlation
    if proof.challenge_id != challenge.challenge_id:
        return failure(CHALLENGE_ID_MISMATCH)

    # 3. Reconstruct canonical payload
    payload = get_signing_payload(challenge)

    # 4. Get expected key FROM LCT (never from proof)
    expected_key = target_lct.binding.public_key

    # 5. Verify signature
    if not crypto_verify(expected_key, payload, proof.signature):
        return failure(SIGNATURE_INVALID)

    # 6. Return success with trust signals
    return success(
        hardware_type=proof.hardware_type,
        continuity_score=1.0 if proof.hardware_type != "software" else 0.0,
        content_score=1.0 if proof.hardware_type != "software" else 0.85
    )
```

---

## 4. Failure Types Quick Reference

| Failure Type | Meaning | Continuity | Content | Action |
|--------------|---------|------------|---------|--------|
| `NONE` | Success | 1.0 | 1.0 | Full trust |
| `TIMEOUT` | No response | 0.5× | 0.9× | Retry, partial trust |
| `UNREACHABLE` | Network issue | 0.5× | 0.9× | Retry, partial trust |
| `SIGNATURE_INVALID` | Wrong key or tampered | 0.0 | 0.5× | Reject, investigate |
| `KEY_MISMATCH` | Different hardware | 0.0 | 0.0 | Successor flow |
| `PCR_DRIFT_EXPECTED` | Known update | 0.7 | 1.0× | Accept with note |
| `PCR_DRIFT_UNEXPECTED` | Unknown change | 0.3 | 0.7× | Investigate |
| `HARDWARE_COMPROMISED` | Attestation failed | 0.0 | 0.0 | Hard reject |
| `CHALLENGE_EXPIRED` | Too slow | — | — | New challenge |

**Legend**: `×` = multiplier of current trust; absolute values = new trust level

---

## 5. Policy Templates

Choose based on your risk profile:

### High Security (Banks, Healthcare)

```python
policy = TrustDegradationPolicy(
    on_failure=TrustAction.REJECT,
    on_timeout=TrustAction.REJECT,
    require_aliveness_for=["*"],
    aliveness_cache_duration=timedelta(seconds=30),
    max_consecutive_failures=1
)
```

**Behavior**: Verify everything, reject on any failure, no grace period.

### Transactional (Commerce, APIs)

```python
policy = TrustDegradationPolicy(
    on_failure=TrustAction.REQUIRE_REAUTH,
    on_timeout=TrustAction.REDUCED_TRUST,
    require_aliveness_for=["transactions_over_100_atp", "auth_changes"],
    aliveness_cache_duration=timedelta(minutes=15),
    max_consecutive_failures=3
)
```

**Behavior**: Verify high-value ops, allow reduced trust on timeout, cache results.

### Social/Collaborative

```python
policy = TrustDegradationPolicy(
    on_failure=TrustAction.REDUCED_TRUST,
    on_timeout=TrustAction.REDUCED_TRUST,
    require_aliveness_for=["relationship_changes"],
    aliveness_cache_duration=timedelta(hours=1),
    max_consecutive_failures=10
)
```

**Behavior**: Patient with failures, only verify relationship changes, long cache.

### Intra-Synthon (Federated Machines)

```python
policy = TrustDegradationPolicy(
    on_failure=TrustAction.REDUCED_TRUST,
    on_timeout=TrustAction.REDUCED_TRUST,
    software_trust_ceiling=0.9,
    require_aliveness_for=["federation_sync", "trust_propagation"],
    aliveness_cache_duration=timedelta(hours=4),
    max_consecutive_failures=20,
    grace_period=timedelta(hours=24)
)
```

**Behavior**: High baseline trust, very patient, but verify critical sync operations.

---

## 6. Dual-Axis Trust Model

AVP provides two independent signals:

| Axis | What It Measures | Source |
|------|------------------|--------|
| **Continuity** | "Same hardware instance?" | TPM/TrustZone signature |
| **Content** | "Data authentic?" | Any valid signature |

**Software binding** provides content trust only (continuity = 0).
**Hardware binding** provides both.

Your policy decides how to combine them:

```python
# Conservative: require both
effective_trust = min(continuity_score, content_score)

# Content-focused: weight content higher
effective_trust = continuity_score * 0.3 + content_score * 0.7

# Geometric mean (balanced)
effective_trust = (continuity_score * content_score) ** 0.5
```

---

## 7. SAGE PCR Selection

For TPM attestation, use standardized PCR sets:

```python
# Minimal (quick check)
SAGE_PCR_MINIMAL = {0, 4, 7}  # BIOS, bootloader, Secure Boot

# Full embodiment attestation
SAGE_PCR_FULL = {0, 1, 2, 3, 4, 5, 6, 7, 11}  # Boot chain + NV counters
```

When evaluating PCR drift:
- **Expected drift**: Known updates, config changes → `PCR_DRIFT_EXPECTED`
- **Unexpected drift**: Unknown changes → `PCR_DRIFT_UNEXPECTED`

Maintain a reference window of acceptable PCR values, not exact matches.

---

## 8. Succession Handling

When `KEY_MISMATCH` occurs, the entity may present a `SuccessionCertificate`:

```python
def handle_succession(
    old_lct: LCT,
    new_lct: LCT,
    certificate: SuccessionCertificate
) -> float:

    # 1. Verify certificate signature (by old embodied entity)
    if not verify(old_lct.binding.public_key, certificate.predecessor_signature):
        return 0.0  # Forged certificate

    # 2. Check certificate validity
    if not certificate.is_valid() or certificate.revoked:
        return 0.0

    # 3. Verify DNA inheritance (optional but recommended)
    if certificate.dna_inheritance_hash:
        if new_lct.experience_hash != certificate.dna_inheritance_hash:
            return 0.0  # Wrong experience loaded

    # 4. Grant bounded initial trust
    return min(
        certificate.max_inherited_trust,  # Usually 0.5
        old_trust * 0.5  # Never more than half of old trust
    )
```

**Key insight**: Succession is inheritance, not resurrection. Trust must be re-earned.

---

## 9. Common Mistakes

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| Trusting `proof.public_key` | Key substitution attack | Use LCT's public key |
| Signing just the nonce | Replay attacks | Use full canonical payload |
| Exact PCR matching | Breaks on updates | Use reference windows |
| Binary trust (0 or 1) | Loses nuance | Use dual-axis scores |
| Same policy for all | Over/under-securing | Choose by use case |
| Caching too long | Stale aliveness | Match cache to risk |

---

## 10. Minimal Implementation Checklist

- [ ] Store target LCT's public key (from LCT, never from proof)
- [ ] Implement canonical payload reconstruction
- [ ] Choose a policy template appropriate to your use case
- [ ] Handle at least: `NONE`, `TIMEOUT`, `SIGNATURE_INVALID`, `KEY_MISMATCH`
- [ ] Cache verification results (with appropriate TTL)
- [ ] Log all verification attempts (for audit)
- [ ] Implement graceful degradation (not just accept/reject)

---

## References

- [Full AVP Specification](./ALIVENESS-VERIFICATION-PROTOCOL.md)
- [Hardware Binding Architecture](./HARDWARE-BINDING-IMPLEMENTATION-PLAN.md)
- [LCT Binding Module](../../core/lct_binding/)

---

*"LCT continuity is a claim; aliveness is the evidence. Relationships are contracts conditioned on evidence, not artifacts conditioned on secrecy."*
