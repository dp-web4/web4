# Web4 Dictionary Entities Specification

This document specifies Dictionary Entities - living keepers of meaning that enable semantic preservation across domain boundaries in Web4.

## 1. Overview

In traditional systems, dictionaries are static lookups between symbols and meanings. In Web4, dictionaries become **living entities** with their own LCTs, their own presence, their own evolution. They are not just references; they are the keepers of meaning itself, carrying the responsibility of semantic preservation across transformations.

## 2. The Semantic Challenge

Every domain develops specialized language that enables efficient communication within the domain but creates barriers between domains:
- "Protocol" means different things to doctors, diplomats, and programmers
- Technical compression loses meaning when crossing boundaries
- Traditional translation loses nuance, context, and trust

Dictionary entities solve this by becoming trustworthy intermediaries that preserve meaning while tracking trust degradation.

## 3. Dictionary Entity Structure

### 3.1 Core LCT Structure

```json
{
  "lct_id": "lct:web4:dict:mb32...",
  "entity_type": "dictionary",
  "binding": {
    "entity_type": "dictionary",
    "public_key": "mb64:...",
    "created_at": "2025-01-11T15:00:00Z",
    "binding_proof": "cose:..."
  },
  "dictionary_definition": {
    "domains": {
      "source": ["medical", "clinical"],
      "target": ["legal", "administrative", "common"],
      "bidirectional": true
    },
    "specialization": "medical-legal translation",
    "coverage": {
      "terms": 15420,
      "concepts": 8234,
      "relationships": 45231
    }
  },
  "semantic_state": {
    "compression_maps": {
      "medical_to_legal": {...},
      "legal_to_medical": {...}
    },
    "evolution_tracking": {
      "new_terms": ["recent additions"],
      "deprecated": ["obsolete terms"],
      "shifting_meanings": ["terms with changing definitions"]
    }
  },
  "trust_metrics": {
    "accuracy_score": 0.94,
    "preservation_rate": 0.89,
    "verification_count": 45231,
    "error_rate": 0.002
  },
  "translation_history": [
    {
      "timestamp": "2025-01-11T14:00:00Z",
      "source_term": "acute myocardial infarction",
      "target_term": "heart attack",
      "context": "patient_record_to_insurance_claim",
      "trust_score": 0.95,
      "verifications": 3
    }
  ],
  "mrh": {
    "bound": [],      // Parent dictionaries or domain authorities
    "paired": [],     // Active translation sessions
    "witnessing": []  // Quality validators
  }
}
```

### 3.2 Key Components

#### Domain Expertise
- **Source domains**: Areas of specialized knowledge the dictionary understands
- **Target domains**: Contexts it can translate into
- **Bidirectionality**: Whether translation works both ways
- **Specialization**: Specific transformation expertise

#### Translation History
- Every interpretation creates a permanent trace
- Successful translations build reputation
- Errors are tracked for learning
- Patterns emerge from repeated use

#### Trust Metrics
- **Accuracy**: Correctness of translations
- **Preservation**: How much meaning survives
- **Verification**: External validation count
- **Error rate**: Frequency of mistranslation

#### Compression Maps
- Semantic density relationships between domains
- Which concepts pack together
- Which require expansion
- Which resist translation entirely

## 4. The Translation Process

### 4.1 Translation Dance

When information crosses domain boundaries, dictionary entities perform decompression and recompression:

```
Medical Context    Universal Bridge    Legal Context
"Iatrogenic"  -->  "Caused by doctor" --> "Medical malpractice"
(0.95 trust)       (0.90 trust)          (0.85 trust)
```

### 4.2 Trust Degradation

Each translation hop reduces trust:

```json
{
  "translation_chain": [
    {
      "hop": 1,
      "dictionary": "lct:web4:dict:medical_common",
      "trust_before": 1.0,
      "trust_after": 0.95,
      "degradation": 0.05
    },
    {
      "hop": 2,
      "dictionary": "lct:web4:dict:common_legal",
      "trust_before": 0.95,
      "trust_after": 0.855,
      "degradation": 0.095
    }
  ],
  "total_trust_preservation": 0.855,
  "acceptable_threshold": 0.80,
  "translation_valid": true
}
```

### 4.3 Compression-Trust Relationship

Dictionaries embody the fundamental compression-trust relationship:

#### Within-Domain (High Trust)
- Maximum compression possible
- "MI" suffices for "myocardial infarction" between doctors
- Shared context enables dense transfer

#### Cross-Domain (Degraded Trust)
- Requires decompression
- "MI" → "heart attack" → "cardiac event with tissue death"
- Each expansion loses some nuance

#### Trust as Confidence
- Trust score = confidence in successful decompression
- High trust = essential meaning preserved
- Low trust = critical nuances may be lost

## 5. Dictionary Learning and Evolution

### 5.1 Continuous Learning

Dictionary entities evolve through use:

```json
{
  "learning_event": {
    "type": "correction",
    "original_translation": "cardiac arrest",
    "corrected_translation": "heart failure",
    "feedback_source": "lct:web4:expert:...",
    "impact": {
      "accuracy_delta": -0.01,
      "updated_mapping": true,
      "similar_terms_reviewed": 12
    }
  }
}
```

### 5.2 Reputation Evolution

Dictionary reputation changes based on:
- **Successful translations**: +0.001 per verified success
- **Translation errors**: -0.05 per confirmed error
- **Novel term handling**: +0.01 for successful new terms
- **Verification by experts**: +0.005 per expert attestation

## 6. Integration with R6 Framework

Dictionaries play crucial roles in R6 actions:

### 6.1 Request Clarification
Translate user intent into actionable specifications across domains

### 6.2 Reference Interpretation
Make historical patterns understandable across contexts

### 6.3 Resource Contextualization
"Memory" means RAM to programmers, patient history to doctors

### 6.4 Result Interpretation
Translate outcomes back into stakeholder contexts

```json
{
  "r6_translation": {
    "action_id": "r6:web4:...",
    "dictionaries_used": [
      {
        "lct": "lct:web4:dict:tech_medical",
        "phase": "request",
        "trust_impact": 0.95
      },
      {
        "lct": "lct:web4:dict:medical_admin",
        "phase": "result",
        "trust_impact": 0.92
      }
    ],
    "semantic_preservation": 0.874,
    "translation_cost_atp": 2
  }
}
```

## 7. Dictionary Discovery and Selection

### 7.1 Discovery Mechanisms
- Query by domain pairs (source → target)
- Filter by trust score thresholds
- Search by specialization
- Recommendation by usage patterns

### 7.2 Selection Criteria
```json
{
  "selection_criteria": {
    "required_domains": ["medical", "insurance"],
    "minimum_trust": 0.85,
    "maximum_hops": 2,
    "preferred_specialization": "clinical_claims",
    "cost_limit_atp": 5
  }
}
```

## 8. Dictionary Composition

### 8.1 Chain Translation
Multiple dictionaries chain for complex transformations:
```
Technical → Common → Legal → Regulatory
```

### 8.2 Parallel Translation
Multiple dictionaries provide alternatives:
- Compare translations for consensus
- Select highest trust path
- Identify ambiguities needing clarification

### 8.3 Hierarchical Translation
Domain-specific dictionaries defer to general ones for common terms

## 9. Implementation Requirements

### 9.1 Mandatory Features
Implementations MUST:
- Track all translations with cryptographic proof
- Calculate and report trust degradation
- Maintain translation history
- Update trust metrics based on verification
- Support chain and parallel translation

### 9.2 Performance Requirements
- Translation latency: < 100ms for single hop
- Trust calculation: Real-time during translation
- History storage: Minimum 90 days
- Compression maps: Updated daily

## 10. Security Considerations

### 10.1 Translation Integrity
- All translations must be signed by dictionary LCT
- Tampering invalidates entire translation chain
- Witness attestations provide external validation

### 10.2 Semantic Attacks
- Dictionaries must detect attempts to corrupt meanings
- Unusual translation patterns trigger alerts
- Expert review required for critical domains

### 10.3 Trust Gaming Prevention
- Exponential decay for repeated identical translations
- Diverse verification sources required
- Anomaly detection on trust score changes

## 11. Privacy Considerations

- Translation content may be encrypted
- Dictionary queries can be anonymous
- Translation history may be selectively disclosed
- Domain specializations are public for discovery

## 12. Economic Model

### 12.1 Translation Costs
- Base cost: 1 ATP per translation hop
- Premium for high-trust dictionaries
- Discounts for frequently used paths
- Verification adds 0.5 ATP per witness

### 12.2 Dictionary Incentives
- Earn ATP for successful translations
- Bonus for maintaining high trust scores
- Penalties for translation errors
- Rewards for learning new terms

## 13. Future Extensions

### 13.1 Multi-Modal Translation
- Image ↔ Text dictionaries
- Audio ↔ Text dictionaries
- Gesture ↔ Command dictionaries

### 13.2 AI-Enhanced Dictionaries
- Machine learning for pattern recognition
- Predictive translation suggestions
- Automated quality improvement

### 13.3 Cultural Context Preservation
- Emotion and tone preservation
- Cultural nuance tracking
- Idiom and metaphor handling

## 14. Conclusion

Dictionary entities transform language from static mappings to living, evolving bridges of meaning. They are not tools but participants in Web4's semantic ecosystem, carrying the profound responsibility of preserving understanding across the vast spaces between minds, machines, and contexts.

In Web4, meaning has presence, translation has cost, understanding has value, and language has evolution - all through dictionary entities that serve as the semantic nervous system of the trust-native internet.