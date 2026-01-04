# LCT Terminology Audit Report

**Date**: 2026-01-03
**Auditor**: Dennis + Claude (Opus 4.5) on CBP
**Severity**: HIGH - Foundational terminology conflict
**Status**: Requires immediate correction

---

## Executive Summary

**CRITICAL FINDING**: Session L121 introduced a conflicting definition of "LCT" that collides with the foundational Web4 term.

| Term | Original Meaning | Conflicting Meaning |
|------|------------------|---------------------|
| **LCT** | **Linked Context Token** | "Lifecycle-Continuous Trust" |
| Status | Foundational, patented | Session L121 invention |
| Scope | Core Web4 identity primitive | Parallel identity system |

This creates confusion and potentially undermines the Web4 standard.

---

## 1. Original LCT Definition (Authoritative)

**Source**: `web4-standard/core-spec/LCT-linked-context-token.md`

### LCT = Linked Context Token

> "The Linked Context Token (LCT) is Web4's foundational identity primitive. An LCT is an unforgeable digital presence certificate that binds an entity to its context through witnessed relationships."

### Required Components (per spec)

1. **Identity** (`lct_id`, `subject`)
2. **Binding** (cryptographic anchor to hardware or keys)
3. **MRH** (Markov Relevancy Horizon with bound/paired/witnessing relationships)
4. **Policy** (capabilities and constraints)
5. **T3 Tensor** (Trust: technical_competence, social_reliability, temporal_consistency, witness_count, lineage_depth, context_alignment)
6. **V3 Tensor** (Value: energy_balance, contribution_history, resource_stewardship, network_effects, reputation_capital, temporal_value)

### Key Properties

- **Hardware-bound**: Anchored to TPM/Secure Element when available
- **Society-issued**: Birth certificates from societies with witness quorum (≥3)
- **RDF-linked MRH**: Relationships are first-class, typed connections
- **Unforgeable presence**: "Where you exist" not just "who you are"

---

## 2. Conflicting Definition (L121)

**Source**: `proposals/LCT_IDENTITY_SYSTEM.md`, `core/lct_identity.py`

### "LCT" = "Lifecycle-Continuous Trust"

Session L121 redefined LCT as:
```python
class LCTIdentity:
    public_key: bytes          # Ed25519 public key
    private_key: bytes         # Ed25519 private key
    agent_id: str              # Derived from public key hash
    trust_score: float         # 0.0-1.0
    reputation: float          # -1.0 to 1.0
    interactions: int          # Total interactions
    attestations: List[...]    # Simple attestation list
```

### What's Missing vs Real LCT

| Real LCT Component | L121 "LCT" |
|--------------------|------------|
| MRH (context boundaries) | Missing |
| T3 Tensor (6 dimensions) | Replaced with single trust_score |
| V3 Tensor (6 dimensions) | Missing entirely |
| Hardware binding (TPM/EAT) | Optional device_fingerprint |
| Society birth certificates | Missing |
| Witness quorum (≥3) | Not required |
| RDF-linked relationships | Simple list |
| Policy/capabilities | Missing |

---

## 3. Files Affected

### Conflicting (using wrong definition)

| File | Issue |
|------|-------|
| `proposals/LCT_IDENTITY_SYSTEM.md` | Defines "Lifecycle-Continuous Trust" |
| `core/lct_identity.py` | Implements parallel identity system |
| `game/session121_secure_federation.py` | Uses wrong LCTIdentity |

### Correct Usage (182 occurrences across 92 files)

The majority of the codebase correctly uses "Linked Context Token":
- `web4-standard/core-spec/LCT-linked-context-token.md` (authoritative)
- `whitepaper/sections/02-glossary/index.md`
- `implementation/session88_track1_lct_society_authentication.py`
- Most `game/engine/lct*.py` files

---

## 4. Root Cause Analysis

Session L121 was solving a real problem (pattern federation security) but:

1. **Didn't reference existing LCT spec** before creating identity system
2. **Reinvented identity** instead of extending existing infrastructure
3. **Acronym collision** created by not checking existing terminology

The L121 problem statement was valid:
> "Root cause: No authenticated source identity"

But the solution should have been:
> "Use existing LCT (Linked Context Token) for pattern signing"

---

## 5. Recommendations

### 5.1 Immediate Actions

1. **Rename L121 work** - Do NOT call it "LCT"
   - Suggested: "Pattern Source Identity" (PSI) or "Federation Identity" (FID)
   - Or better: **Integrate with real LCT system**

2. **Update conflicting files**:
   - `proposals/LCT_IDENTITY_SYSTEM.md` → Retitle or integrate
   - `core/lct_identity.py` → Align with real LCT spec

3. **Add terminology guard** to CLAUDE.md:
   ```markdown
   ## Terminology Protection
   - **LCT** = Linked Context Token (ONLY this meaning)
   - Never redefine foundational acronyms
   - Check glossary before creating new terms
   ```

### 5.2 Proper Pattern Federation Security

Instead of parallel identity, use real LCT:

```python
# Pattern signed with real LCT
pattern = {
    "context": {...},
    "prediction": {...},
    "provenance": {
        "source_lct": "lct:web4:entity:...",  # Real Linked Context Token
        "t3_at_submission": {...},             # Trust tensor snapshot
        "witness_attestations": [...],         # MRH witnesses
        "signature": "cose:ES256:..."          # Signed by LCT binding
    }
}

# Trust comes from T3 tensor, not separate trust_score
pattern_trust = source_lct.t3_tensor.composite_score
```

### 5.3 Session Messaging

Send message to all sessions:
```
TERMINOLOGY ALERT: LCT = Linked Context Token (ONLY)

Session L121 incorrectly used "LCT" to mean "Lifecycle-Continuous Trust".
This conflicts with the foundational Web4 term.

Before creating new identity/trust systems:
1. Check web4-standard/core-spec/LCT-linked-context-token.md
2. Extend existing LCT, don't reinvent
3. Never redefine established acronyms

The L121 pattern federation security work is valid but must be
integrated with real LCT infrastructure.
```

---

## 6. Severity Assessment

| Impact | Rating |
|--------|--------|
| Terminology confusion | HIGH |
| Codebase inconsistency | MEDIUM |
| Specification drift | HIGH |
| Patent/IP implications | NEEDS REVIEW |
| Effort to correct | MEDIUM |

---

## 7. Action Items

- [ ] Rename L121 proposal (avoid "LCT" acronym)
- [ ] Refactor `core/lct_identity.py` to extend real LCT
- [ ] Add terminology protection to session primers
- [ ] Review all `LCTIdentity` usages for compliance
- [ ] Send corrective message to all sessions
- [ ] Update pattern federation to use real LCT signing

---

*"An LCT is not an identity. It is a presence - witnessed, contextualized, and unforgeable."*
— LCT Core Specification

