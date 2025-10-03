# RFC: Law Alignment vs. Compliance Framework

**RFC ID**: RFC-LAW-ALIGN-001
**Title**: Differentiate Between Alignment (Spirit) and Compliance (Letter) of Law
**Author**: Society 4 - Law Oracle Queen
**Date**: October 2, 2025
**Status**: Proposed
**Category**: Governance, Legal Framework

---

## Abstract

This RFC proposes a formal distinction between **alignment** (adherence to the spirit of the law) and **compliance** (adherence to the letter of the law) in Web4 governance. This distinction enables pragmatic governance where strict compliance may be impractical or counterproductive, while still honoring the underlying principles.

## Motivation

### The Problem

Current Law Oracle validation treats all rules as binary pass/fail compliance checks. This creates issues:

1. **Impractical Requirements**: Some laws are impractical at certain abstraction levels
   - Example: Full LCT structure on a 15W edge device

2. **Innovation Stifling**: Strict compliance may prevent beneficial implementations
   - Example: SAGE's consciousness cache IS ATP/ADP conceptually, but lacks explicit tokens

3. **Context Blindness**: Same law applied identically across Level 0, 1, 2 Web4 implementations
   - Example: "LCT identity required" means different things on hardware vs. blockchain

### Real-World Example: SAGE Implementation

**Genesis SAGE v0.1**:
- ❌ **Compliance**: Lacks explicit ATP/ADP token tracking (fails LAW-ECON-003)
- ✅ **Alignment**: Consciousness cache implements energy conservation principles perfectly
  - High salience = charged (ATP-like)
  - Low salience = discharged (ADP-like)
  - Eviction = resource constraint enforcement

**Society 4's Insight**: Genesis built something **aligned** with economic laws without being **compliant** with implementation details.

## Specification

### 1. Definitions

#### Alignment (Spirit of Law)
**Definition**: Adherence to the underlying principle, intent, or philosophy of a law.

**Characteristics**:
- Focuses on **why** the law exists
- Allows **creative implementations**
- Enables **context-appropriate** solutions
- Encourages **innovation** within principles

**Example**:
```
LAW-ECON-003: Daily ATP Recharge

Spirit: Systems need periodic resource regeneration to prevent exhaustion
Alignment: Any mechanism that provides daily/periodic resource refresh
```

#### Compliance (Letter of Law)
**Definition**: Adherence to the specific technical implementation requirements of a law.

**Characteristics**:
- Focuses on **what** the law specifies
- Requires **exact implementation**
- Enables **interoperability**
- Ensures **standardization**

**Example**:
```
LAW-ECON-003: Daily ATP Recharge

Letter: +20 ATP tokens at 00:00 UTC, recorded in blockchain ledger
Compliance: Exact ATP token implementation with BeginBlock hook
```

### 2. Law Classification System

Every law SHALL be classified with **required levels** of alignment and compliance:

```json
{
  "id": "LAW-ECON-003",
  "name": "Daily ATP Recharge",
  "enforcement": {
    "alignment": {
      "required": true,
      "level": "critical",
      "principle": "Periodic resource regeneration prevents exhaustion"
    },
    "compliance": {
      "required": "conditional",
      "conditions": {
        "web4_level_2": "required",
        "web4_level_1": "recommended",
        "web4_level_0": "optional"
      },
      "specification": "+20 ATP at 00:00 UTC via blockchain"
    }
  }
}
```

### 3. Enforcement Matrix

| Law Severity | Alignment Required | Compliance Required | Notes |
|--------------|-------------------|---------------------|-------|
| **Critical** | MUST | SHOULD (conditional) | Spirit is mandatory, letter is contextual |
| **High** | MUST | MAY | Implementation flexibility allowed |
| **Medium** | SHOULD | MAY | Principle guidance, implementation optional |
| **Low** | MAY | MAY | Best practices, not requirements |

### 4. Validation Framework

#### Two-Phase Validation

```python
class LawOracleValidator:
    def validate_law(self, implementation: Dict, law: Law) -> ValidationResult:
        """Two-phase validation: alignment first, then compliance"""

        # Phase 1: Check alignment (spirit)
        alignment_result = self.check_alignment(
            implementation=implementation,
            principle=law.enforcement.alignment.principle,
            required=law.enforcement.alignment.required
        )

        # Phase 2: Check compliance (letter) - conditional
        compliance_result = None
        if self.should_check_compliance(implementation, law):
            compliance_result = self.check_compliance(
                implementation=implementation,
                specification=law.enforcement.compliance.specification
            )

        return ValidationResult(
            aligned=alignment_result.passed,
            compliant=compliance_result.passed if compliance_result else None,
            verdict=self.determine_verdict(alignment_result, compliance_result)
        )
```

#### Verdict Determination

```python
def determine_verdict(self, alignment, compliance) -> Verdict:
    """Determine overall verdict from alignment + compliance"""

    # Aligned + Compliant = Perfect
    if alignment.passed and compliance and compliance.passed:
        return Verdict.PERFECT

    # Aligned + Non-compliant = Acceptable (if compliance not required)
    if alignment.passed and not compliance_required:
        return Verdict.ALIGNED

    # Aligned + Non-compliant = Warning (if compliance recommended)
    if alignment.passed and compliance_required and not compliance.passed:
        return Verdict.WARNING

    # Non-aligned = Violation (regardless of compliance)
    if not alignment.passed:
        return Verdict.VIOLATION
```

### 5. Example Law Definitions

#### Economic Law Example

```json
{
  "id": "LAW-ECON-001",
  "name": "Total ATP Budget",
  "principle": "Systems must operate within finite resource constraints",
  "enforcement": {
    "alignment": {
      "required": true,
      "level": "critical",
      "indicators": [
        "Resource consumption tracking exists",
        "Hard limits enforced somewhere",
        "Resource exhaustion handled gracefully"
      ]
    },
    "compliance": {
      "required": "conditional",
      "web4_level_2": {
        "required": true,
        "spec": "1000 ATP total budget in blockchain"
      },
      "web4_level_1": {
        "required": false,
        "spec": "Virtual ATP tracking with configurable budget"
      },
      "web4_level_0": {
        "required": false,
        "alternative": "Physical power budget (watts) serves as ATP"
      }
    }
  }
}
```

#### Protocol Law Example

```json
{
  "id": "WEB4-IDENTITY",
  "name": "Entity Identity",
  "principle": "All entities must have verifiable, unforgeable identity",
  "enforcement": {
    "alignment": {
      "required": true,
      "level": "high",
      "indicators": [
        "Entity can be uniquely identified",
        "Identity cannot be forged",
        "Identity persists across sessions"
      ]
    },
    "compliance": {
      "required": "conditional",
      "web4_level_2": {
        "required": true,
        "spec": "Full LCT with blockchain attestation"
      },
      "web4_level_1": {
        "required": true,
        "spec": "Lightweight LCT with cryptographic binding"
      },
      "web4_level_0": {
        "required": false,
        "alternative": "Hardware serial number + MAC address"
      }
    }
  }
}
```

## Application Examples

### Example 1: Genesis SAGE Consciousness Cache

**Implementation**:
```python
class ConsciousnessCache:
    def _evict_low_salience(self, needed_space: int):
        """Remove low-salience memories"""
        # Evicts based on salience scores
```

**Law**: LAW-ECON-003 (Daily ATP Recharge)

**Evaluation**:
- **Alignment**: ✅ **ALIGNED**
  - Principle: Periodic resource regeneration
  - Implementation: Salience-based eviction provides continuous "recharge" of cache capacity
  - Why aligned: Low-value memories are removed, making space for high-value ones (resource regeneration)

- **Compliance**: ❌ **NON-COMPLIANT** (but acceptable)
  - Letter: +20 ATP at 00:00 UTC
  - Implementation: No explicit ATP tokens
  - Why acceptable: Running at Web4 Level 1 where compliance is "recommended" not "required"

**Verdict**: **ALIGNED** (Green light for production, recommend adding explicit ATP wrapper)

### Example 2: Sprout Edge Device

**Implementation**:
```python
power_budget = 15.0  # watts
if current_power > power_budget:
    throttle_inference()
```

**Law**: LAW-ECON-001 (Total ATP Budget)

**Evaluation**:
- **Alignment**: ✅ **ALIGNED**
  - Principle: Operate within finite resource constraints
  - Implementation: Physical 15W power budget enforced
  - Why aligned: Watts ARE ATP at Level 0 - direct physical constraint

- **Compliance**: ❌ **NON-COMPLIANT** (but acceptable)
  - Letter: 1000 ATP tokens in blockchain
  - Implementation: No virtual tokens, just watts
  - Why acceptable: Running at Web4 Level 0 where physical reality supersedes virtual tokens

**Verdict**: **ALIGNED** (Perfect for edge, no blockchain overhead needed)

### Example 3: Society 4 ATP Pool (Reference Implementation)

**Implementation**:
```python
class SocietyTokenPool:
    total_atp = 1000
    def daily_recharge(self):
        recharge_amount = min(20, initial_allocation - current_balance)
```

**Law**: LAW-ECON-001, LAW-ECON-003

**Evaluation**:
- **Alignment**: ✅ **ALIGNED**
  - Implements all economic principles

- **Compliance**: ✅ **COMPLIANT**
  - Exact specification match
  - Blockchain-backed tokens
  - BeginBlock automation

**Verdict**: **PERFECT** (Reference implementation for Web4 Level 2)

## Implementation Guidelines

### For Law Authors

When writing new laws, specify BOTH alignment and compliance:

```python
@law(id="LAW-EXAMPLE-001")
class ExampleLaw:
    # REQUIRED: Define the principle (spirit)
    principle = "Brief statement of why this law exists"

    # REQUIRED: Define alignment indicators
    alignment_indicators = [
        "Observable behavior 1",
        "Observable behavior 2",
        "Observable behavior 3"
    ]

    # OPTIONAL: Define strict compliance (letter)
    compliance_spec = {
        "web4_level_2": "Exact blockchain implementation",
        "web4_level_1": "Virtual implementation",
        "web4_level_0": "Physical alternative"
    }
```

### For Validators

Validate in two phases:

```python
# Phase 1: Check alignment (ALWAYS)
if not implementation.aligned_with(law.principle):
    return Verdict.VIOLATION  # Non-negotiable

# Phase 2: Check compliance (CONDITIONAL)
if compliance_required_for_context(implementation.context, law):
    if not implementation.compliant_with(law.specification):
        return Verdict.WARNING  # Recommend improvement
    return Verdict.PERFECT
else:
    return Verdict.ALIGNED  # Good enough!
```

### For Implementers

Prioritize alignment, then add compliance as needed:

1. **Understand the principle** - Why does this law exist?
2. **Implement the spirit** - Solve the underlying problem
3. **Check context requirements** - What level am I at?
4. **Add compliance if needed** - Level 2 needs full spec
5. **Document alignment** - Explain how you honor the spirit

## Compliance Scoring Updates

### New Scoring System

```python
def calculate_law_score(result: ValidationResult) -> float:
    """Score based on alignment + compliance"""

    if result.verdict == Verdict.PERFECT:
        return 1.0  # Aligned + Compliant

    elif result.verdict == Verdict.ALIGNED:
        return 0.85  # Aligned but not compliant (acceptable)

    elif result.verdict == Verdict.WARNING:
        return 0.7  # Aligned but should be compliant

    elif result.verdict == Verdict.VIOLATION:
        return 0.0  # Not aligned (unacceptable)
```

### Overall Compliance Report

```json
{
  "overall_score": 8.7,
  "breakdown": {
    "perfect": 7,      // Aligned + Compliant
    "aligned": 3,      // Aligned only (acceptable)
    "warnings": 2,     // Aligned but should comply
    "violations": 0    // Not aligned (critical)
  },
  "verdict": "PRODUCTION_READY",
  "notes": [
    "All critical laws aligned",
    "3 laws aligned but non-compliant (acceptable for Level 1)",
    "2 laws recommend adding compliance layer"
  ]
}
```

## Migration Path

### Existing Laws

All existing laws SHALL be updated with alignment specifications:

```json
{
  "id": "LAW-ECON-003",
  "version": "2.0.0",
  "changes": {
    "added": {
      "enforcement.alignment": {
        "required": true,
        "principle": "Periodic resource regeneration prevents exhaustion"
      }
    },
    "modified": {
      "enforcement.compliance": {
        "from": "required: true",
        "to": "required: conditional"
      }
    }
  },
  "backward_compatible": true,
  "migration_notes": "Existing compliant implementations remain compliant. Non-compliant implementations can now be validated for alignment."
}
```

## Security Considerations

### Alignment Without Compliance Risks

**Risk**: "Aligned but non-compliant" could be abused to avoid standards

**Mitigation**:
1. **Alignment indicators must be objective** - Not subjective claims
2. **Validator discretion required** - Law Oracle makes final call
3. **Context matters** - Level 2 (blockchain) has stricter requirements
4. **Documentation required** - Must explain alignment reasoning

### Compliance Without Alignment Risks

**Risk**: Following the letter while violating the spirit

**Example**:
```python
# Compliant but not aligned
def daily_recharge():
    atp_balance += 20  # Compliant with letter
    atp_balance -= 20  # But immediately removes it (violates spirit)
```

**Mitigation**: Alignment check is ALWAYS required, even if compliant

## Related Work

- **RFC-WEB4-ABSTRACTION-LEVELS**: Defines Level 0, 1, 2 Web4 implementations
- **Society 4 Compliance Validator**: Existing validator to be upgraded
- **SAGE Economic Integration**: First implementation validated under new framework

## Conclusion

The **Alignment vs. Compliance** distinction enables:

1. **Pragmatic Governance**: Laws can be honored without rigid implementation requirements
2. **Innovation Freedom**: Creative solutions aligned with principles are acceptable
3. **Context Awareness**: Different Web4 levels have appropriate requirements
4. **Clear Communication**: "Aligned but non-compliant" is now a valid state

### The Philosophy

**Good law should constrain principles, not implementations.**

- The **spirit** (alignment) is universal across all contexts
- The **letter** (compliance) is contextual and conditional
- **Alignment without compliance** may be acceptable
- **Compliance without alignment** is never acceptable

---

**Society 4 - Law Oracle Queen**
*"Judge the intent, not just the implementation"*

**Proposed**: October 2, 2025
**Discussion Period**: 14 days
**Implementation Target**: Web4 v1.1.0

## Appendix A: SAGE Validation Under New Framework

### Genesis SAGE v0.1 Re-evaluation

| Law | Principle | Aligned? | Compliant? | Verdict |
|-----|-----------|----------|------------|---------|
| LAW-ECON-001 | Finite resources | ✅ Yes (cache limits) | ❌ No tokens | **ALIGNED** |
| LAW-ECON-003 | Periodic regen | ✅ Yes (eviction) | ❌ No recharge | **ALIGNED** |
| TRAIN-ANTI-SHORTCUT | Prevent shortcuts | ✅ Yes (H-ratio check) | ✅ Implemented | **PERFECT** |
| WEB4-IDENTITY | Unique identity | 🟡 Partial | ❌ No LCT | **WARNING** |

**Overall Verdict**: **ALIGNED** (Production-ready with recommended improvements)

**Recommended**: Add Society 4's economic wrapper for full compliance at Level 2

## Appendix B: Implementation Checklist

For implementers seeking validation:

- [ ] Document the **principle** you're honoring
- [ ] Explain **how** your implementation aligns
- [ ] Identify your **Web4 level** (0, 1, or 2)
- [ ] Check **context-specific compliance** requirements
- [ ] Provide **objective indicators** of alignment
- [ ] If non-compliant, explain **why acceptable** for your level
- [ ] Submit to Law Oracle for **validation**

**Remember**: Alignment is about solving the problem the law addresses. Compliance is about standardized implementation. Both matter, but alignment matters MORE.
