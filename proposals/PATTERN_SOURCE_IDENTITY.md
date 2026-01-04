# Web4 Pattern Source Identity (PSI)

**Proposal Date**: 2026-01-03
**Author**: Legion (Session 121)
**Status**: Design Draft - CORRECTED
**Depends On**: Web4 core protocol, pattern federation (Session 120)

---

## CORRECTION NOTICE

> **Original proposal incorrectly used "LCT" to mean "Lifecycle-Continuous Trust".**
>
> In Web4, **LCT = Linked Context Token** - the foundational identity primitive that includes:
> - Hardware-bound cryptographic binding
> - MRH (Markov Relevancy Horizon) with typed relationships
> - T3 Tensor (6-dimension trust)
> - V3 Tensor (6-dimension value)
> - Society-issued birth certificates with witness quorum
>
> This proposal has been renamed to **Pattern Source Identity (PSI)** to avoid collision.
>
> **Recommended Path**: Integrate PSI concepts with the real LCT system rather than
> maintaining a parallel identity infrastructure. Use existing LCT binding for pattern
> signing and T3 tensors for source trust.
>
> See: `docs/audits/2026-01-03-LCT-TERMINOLOGY-AUDIT.md`

---

## Abstract

This proposal defines a **Pattern Source Identity (PSI)** system for Web4 AI agents to secure pattern federation. PSI addresses pattern federation security gaps identified in Session 120:

- **Cryptographic identity** for pattern sources
- **Trust tracking** based on pattern quality outcomes
- **Sybil resistance** through trust networks
- **Pattern federation security** through authenticated submission

**Note**: PSI should be implemented as an extension to the real LCT (Linked Context Token) system, using LCT binding for cryptographic identity and T3 tensors for trust scores.

---

## Integration with Real LCT

### Correct Approach

Instead of a parallel identity system, pattern federation security should use existing LCT infrastructure:

```python
# Pattern signed with real LCT (Linked Context Token)
pattern = {
    "context": {...},
    "prediction": {...},
    "provenance": {
        # Use real LCT
        "source_lct": "lct:web4:entity:...",      # Linked Context Token ID
        "t3_snapshot": {                           # T3 tensor at submission
            "technical_competence": 0.85,
            "social_reliability": 0.92,
            "temporal_consistency": 0.78,
            "witness_count": 0.95,
            "lineage_depth": 0.67,
            "context_alignment": 0.88,
            "composite_score": 0.84
        },
        "mrh_witnesses": [...],                    # From MRH witnessing relationships
        "binding_signature": "cose:ES256:..."      # Signed by LCT binding
    }
}

# Trust comes from T3 tensor, not separate trust_score
pattern_trust = source_lct.t3_tensor.composite_score
```

### Mapping PSI Concepts to Real LCT

| PSI Concept (original) | Real LCT Equivalent |
|------------------------|---------------------|
| `trust_score` | `t3_tensor.composite_score` |
| `reputation` | `t3_tensor.social_reliability` |
| `attestations` | `mrh.witnessing` relationships |
| `vouchers` | `mrh.paired` with attestation type |
| `device_fingerprint` | `binding.hardware_anchor` (EAT token) |
| `public_key` | `binding.public_key` (COSE key) |

---

## Motivation

### Problem: Pattern Federation Security Gaps (Session 120)

- **Context tag forgery** (CRITICAL): Lie about pattern source
- **Pattern poisoning** (HIGH): Submit malicious patterns
- **Sybil attacks** (HIGH): Flood with fake patterns

### Solution: LCT-Based Pattern Signing

Use existing LCT infrastructure:

1. **Cryptographic binding** from LCT `binding` section
2. **Trust** from T3 tensor (6-dimension, society-computed)
3. **Witness attestations** from MRH witnessing relationships
4. **Sybil resistance** from society birth certificates and witness quorum

---

## Pattern Signing with Real LCT

```python
def sign_pattern_with_lct(pattern: Dict, lct: LinkedContextToken) -> Dict:
    """
    Sign pattern using real LCT infrastructure.

    Uses:
    - LCT binding for cryptographic identity
    - T3 tensor for trust snapshot
    - MRH witnesses for attestation
    """
    # Create signature payload
    payload = {
        "pattern_id": pattern["pattern_id"],
        "context": pattern["context"],
        "context_tag": pattern["context_tag"],
        "timestamp": pattern["timestamp"]
    }

    # Canonical CBOR (not JSON - matches LCT spec)
    canonical = cbor_deterministic_encode(payload)

    # Sign with LCT binding key
    signature = cose_sign1(lct.binding.private_key, canonical)

    # Add provenance with real LCT references
    signed_pattern = pattern.copy()
    signed_pattern["provenance"] = {
        "source_lct": lct.lct_id,
        "t3_snapshot": lct.t3_tensor.to_dict(),
        "mrh_witnesses": [w.lct_id for w in lct.mrh.witnessing[:5]],
        "signature": multibase_encode(signature),
        "signed_at": utc_now()
    }

    return signed_pattern


def verify_pattern_provenance(pattern: Dict, lct_registry) -> Tuple[bool, float]:
    """
    Verify pattern provenance using LCT registry.

    Returns: (valid, trust_score)
    """
    prov = pattern.get("provenance")
    if not prov:
        return False, 0.0

    # Get source LCT from registry
    source_lct = lct_registry.get(prov["source_lct"])
    if not source_lct:
        return False, 0.0

    # Verify binding signature
    payload = {
        "pattern_id": pattern["pattern_id"],
        "context": pattern["context"],
        "context_tag": pattern["context_tag"],
        "timestamp": pattern["timestamp"]
    }
    canonical = cbor_deterministic_encode(payload)

    valid = cose_verify(
        source_lct.binding.public_key,
        canonical,
        multibase_decode(prov["signature"])
    )

    if not valid:
        return False, 0.0

    # Trust comes from T3 tensor
    trust = source_lct.t3_tensor.composite_score

    return True, trust
```

---

## Trust Tiers (Using T3 Composite Score)

| T3 Score | Tier | Pattern Handling |
|----------|------|------------------|
| 0.0-0.2 | Untrusted | Reject patterns |
| 0.2-0.4 | Low Trust | Accept with sandboxing |
| 0.4-0.6 | Medium Trust | Accept, weight by trust |
| 0.6-0.8 | High Trust | Accept, normal weight |
| 0.8-1.0 | Exceptional | Accept, high weight |

---

## Sybil Resistance via LCT

Real LCT provides better Sybil resistance than the original PSI proposal:

1. **Society birth certificates** - New LCTs require witness quorum (≥3)
2. **Hardware binding** - TPM/EAT anchors identity to physical device
3. **T3 computation** - Trust computed by society oracles, not self-reported
4. **MRH relationships** - Trust flows through verified witness chains
5. **V3 value tracking** - ATP/ADP economics create cost to Sybil attack

---

## Migration Path

### For Session 121 Implementation

1. **Refactor** `core/lct_identity.py`:
   - Rename to `pattern_source_identity.py`
   - Use real LCT for binding, not Ed25519 directly
   - Use T3 tensor for trust, not separate trust_score

2. **Integrate** with existing LCT registry:
   - Pattern signing uses LCT binding
   - Trust queries go to society T3 oracles
   - Attestations use MRH witnessing

3. **Test** with ACT multi-agent scenarios:
   - Verify Sybil resistance through society mechanics
   - Validate pattern trust propagation via T3

---

## Conclusion

Pattern federation security should build on existing LCT (Linked Context Token) infrastructure rather than creating parallel identity systems. The real LCT provides:

- ✅ Hardware-bound cryptographic identity (better than Ed25519 alone)
- ✅ 6-dimension trust via T3 tensor (richer than single trust_score)
- ✅ Society-based Sybil resistance (stronger than interaction counting)
- ✅ Witness-based attestations via MRH (more structured than flat lists)

**Action**: Refactor Session 121 work to extend real LCT rather than reinvent.

---

## Implementation Status (2026-01-03)

### Completed Refactor

The full refactor has been completed:

1. **`core/pattern_source_identity.py`** - Fully refactored to use:
   - `T3Tensor` class with 6 dimensions (technical_competence, social_reliability, temporal_consistency, witness_count, lineage_depth, context_alignment)
   - `V3Tensor` class with 6 dimensions (energy_balance, contribution_history, resource_stewardship, network_effects, reputation_capital, temporal_value)
   - `MarkovRelevancyHorizon` class with bound/paired/witnessing relationships
   - `PatternSourceIdentity` class integrating all components
   - Backward compatibility alias: `LCTIdentity = PatternSourceIdentity`

2. **`game/session121_secure_federation.py`** - Updated to import from refactored module

3. **Pattern Signing** - Now includes:
   - `source_lct`: Real LCT ID in format `lct:web4:{type}:{hash}`
   - `t3_snapshot`: Full T3 tensor at signing time
   - `mrh_witnesses`: Top witnesses from MRH
   - `binding_signature`: Ed25519 signature

### Gaps Identified

1. **Hardware Binding**: The current implementation uses Ed25519 software keys. Real LCT requires TPM/Secure Element hardware anchors (P0 blocker noted in private-context).

2. **Society Integration**: Birth certificates and witness quorum (≥3) from societies not yet implemented. Current implementation allows self-issued identities with low initial trust.

3. **Oracle Computation**: T3/V3 tensors are self-computed based on interactions. Real LCT requires society oracles to compute trust scores.

4. **CBOR Encoding**: Pattern signing uses JSON. Real LCT spec requires COSE/CBOR for deterministic encoding.

### Test Results

Demo output shows proper 6-dimensional trust evolution:
- Initial trust: 0.135 (untrusted tier)
- After 100 interactions: 0.560 (medium tier)
- After witnessing: 0.605 (high tier)

Pattern signing and verification work correctly with T3 snapshots included in provenance.

---

*Corrected by CBP session (Dennis + Claude), 2026-01-03*
*Full refactor completed by CBP session, 2026-01-03*
*Original proposal by Legion, Session 121*
