# Web4 Standard Addendum 002: Authentication Attribute Classification

**Status**: Draft
**Date**: September 27, 2025
**Category**: Procedural Trust Computation
**Supersedes**: None

## Abstract

This addendum clarifies the classification of authentication attributes used in Web4 trust computations, distinguishing between inherent attributes (cryptographically or biologically bound to entities) and circumstantial attributes (contextual indicators that may change). This distinction is essential for implementing robust authentication strategies that remain resilient when network conditions, physical locations, or other circumstantial factors change.

## 1. Scope and Purpose

This addendum applies to all Web4 implementations that:
- Perform entity authentication
- Calculate trust tensor values
- Make access control decisions
- Establish peer-to-peer connections
- Validate Linked Context Tokens (LCTs)

## 2. Normative Definitions

### 2.1 Inherent Attributes
Attributes that satisfy ALL of the following criteria:
- **Uniquely bound** to a single entity
- **Cryptographically verifiable** or biometrically measurable
- **Non-transferable** without fundamental compromise
- **Persistent** across connection sessions
- **Deterministic** in validation outcome

### 2.2 Circumstantial Attributes
Attributes that exhibit ANY of the following characteristics:
- **Externally assigned** by systems outside entity control
- **Transferable** between entities
- **Mutable** over time
- **Context-dependent** on network or environment
- **Probabilistic** in identity indication

## 3. Attribute Classification

### 3.1 Recognized Inherent Attributes

| Attribute Type | Validation Method | Trust Weight |
|---|---|---|
| Ed25519/Secp256k1 Private Keys | Signature verification | 1.0 |
| TPM/HSM Attestation | Secure hardware verification | 0.95 |
| Biometric Templates | Match-on-device verification | 0.90 |
| Blockchain Validator Keys | Consensus participation proof | 0.95 |
| LCT Generation Patterns | Statistical uniqueness validation | 0.85 |

### 3.2 Common Circumstantial Attributes

| Attribute Type | Typical Lifetime | Trust Weight |
|---|---|---|
| IPv4/IPv6 Addresses | Hours to Months | 0.3 |
| DNS Names | Months to Years | 0.4 |
| Email Addresses | Months to Years | 0.35 |
| Phone Numbers | Years | 0.4 |
| Session Tokens | Minutes to Hours | 0.2 |
| Geographic Location | Seconds to Days | 0.15 |

## 4. Trust Computation Requirements

### 4.1 Minimum Authentication Thresholds

For different transaction types, implementations MUST enforce:

```
Critical Operations (value > 1000 ATP):
  REQUIRE at least one inherent attribute

Standard Operations (value 100-1000 ATP):
  REQUIRE inherent attribute OR
  three independent circumstantial attributes

Low-Risk Operations (value < 100 ATP):
  ACCEPT two circumstantial attributes
```

### 4.2 Trust Tensor Modification

When computing trust tensors, implementations MUST:

```python
def compute_authentication_trust(entity):
    inherent_trust = max([validate(attr) for attr in entity.inherent_attrs])
    circumstantial_trust = product([score(attr) for attr in entity.circumstantial_attrs])

    # Inherent attributes provide floor
    if inherent_trust > 0:
        return max(inherent_trust, 0.5 + 0.5 * circumstantial_trust)
    else:
        # Circumstantial only - capped at 0.7
        return min(0.7, circumstantial_trust)
```

## 5. Implementation Requirements

### 5.1 Attribute Change Handling

Implementations MUST:
- Continue sessions when ONLY circumstantial attributes change
- Re-authenticate when inherent attributes change
- Log all attribute changes with classification
- Notify peers of significant trust score changes

### 5.2 Multi-Factor Composition

When combining multiple circumstantial attributes:
- No more than 3 circumstantial attributes SHALL contribute to trust score
- Diminishing returns MUST apply: `trust = 1 - ∏(1 - attr_trust[i])`
- Time correlation SHALL reduce trust (attributes changing together = suspicious)

## 6. Security Considerations

### 6.1 Downgrade Attacks
Systems MUST NOT allow high-trust sessions to continue using only circumstantial attributes after inherent attribute validation fails.

### 6.2 Circumstantial Attribute Poisoning
Systems SHOULD detect patterns indicating circumstantial attribute manipulation:
- Rapid IP address changes
- Impossible geographic transitions
- Session token replay attempts

### 6.3 Privacy Implications
- Inherent attributes require stronger privacy protection
- Circumstantial attributes may be logged more freely
- Biometric templates must remain on-device

## 7. Backward Compatibility

This addendum is fully backward compatible. Existing implementations may:
1. Continue current authentication methods
2. Gradually adopt classification system
3. Add metadata to indicate classification compliance

## 8. Examples

### 8.1 Federation Node Authentication
```yaml
Scenario: Society node reconnecting after network change
Inherent:
  - Validator signing key (Ed25519)
Circumstantial:
  - New IP address
  - Changed network route
Result: Authentication succeeds based on inherent attribute
```

### 8.2 User Session Continuation
```yaml
Scenario: Mobile user switching from WiFi to cellular
Inherent:
  - Device secure enclave key
Circumstantial:
  - IP address change
  - Network type change
  - Geographic shift
Result: Session continues without re-authentication
```

## 9. References

- Web4 Protocol Specification v1.0, Section 5.3 (Trust Tensors)
- LCT Specification, Section 3.2 (Signature Validation)
- NIST SP 800-63-3 (Digital Identity Guidelines)
- ACT Federation Implementation Lessons

## 10. Acknowledgments

This addendum was motivated by the Society 4 IP address migration incident in the ACT Federation (September 2025), which demonstrated the importance of distinguishing between inherent and circumstantial attributes for resilient authentication.

---

## Appendix A: Quick Reference

**Ask**: "Will this attribute identify the entity if everything else changes?"
- YES → Inherent attribute
- NO → Circumstantial attribute

**Ask**: "Can this attribute be legitimately shared between entities?"
- YES → Circumstantial attribute
- NO → Inherent attribute

**Ask**: "Does losing control of this attribute fundamentally compromise the entity?"
- YES → Inherent attribute
- NO → Circumstantial attribute