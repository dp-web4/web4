# Web4 Dictionary Entities Specification

## Overview

Dictionary Entities are first-class Web4 entities that serve as living semantic bridges between domains, managing the fundamental compression-trust relationship inherent in all communication. They are not static translation tables but evolving entities with their own LCTs, reputations, and relationships that mediate meaning across boundaries.

## 1. Core Concept: Compression and Trust

### 1.1 The Fundamental Principle

**All meaningful communication is compression plus trust across shared or sufficiently aligned latent fields.**

This principle underlies:
- Human language (words as compressed symbols requiring shared understanding)
- Neural networks (token IDs pointing to embeddings in latent space)
- Cross-domain translation (medical → legal requiring trusted interpretation)
- Inter-entity communication (AI ↔ Human requiring semantic alignment)

### 1.2 The Trust-Compression Duality

```
High Trust → High Compression → Efficient Communication
Low Trust  → Low Compression  → Verbose Communication
Zero Trust → No Compression   → Raw Data Transfer
```

Dictionary Entities manage this duality by:
- **Building trust** through successful translations
- **Enabling compression** by maintaining shared codebooks
- **Tracking degradation** when meanings drift
- **Facilitating alignment** between disparate systems

## 2. Dictionary Entity Architecture

### 2.1 Dictionary as Living Entity

Every Dictionary has:
- **LCT**: Unforgeable identity with cryptographic binding
- **MRH**: Relationship graph with domains and users
- **T3 Tensor**: Competence in translation (Talent, Training, Temperament)
- **V3 Tensor**: Quality of translations (Veracity, Validity, Value)
- **Witness History**: Record of successful/failed translations

### 2.2 Dictionary LCT Structure

```json
{
  "lct_id": "lct:web4:dictionary:medical-legal:v2",
  "entity_type": "dictionary",
  "dictionary_spec": {
    "source_domain": "medical",
    "target_domain": "legal",
    "bidirectional": true,
    "version": "2.3.1",
    "coverage": {
      "terms": 15000,
      "concepts": 3200,
      "relationships": 8500
    }
  },
  "compression_profile": {
    "average_ratio": 12.5,
    "lossy_threshold": 0.02,
    "context_required": "moderate",
    "ambiguity_handling": "probabilistic"
  },
  "trust_requirements": {
    "minimum_t3": {
      "talent": 0.8,      // Domain expertise
      "training": 0.9,     // Translation accuracy
      "temperament": 0.85  // Consistency
    },
    "stake_required": 100  // ATP stake for high-risk translations
  },
  "evolution": {
    "learning_rate": 0.001,
    "update_frequency": "daily",
    "drift_detection": true,
    "community_edits": true
  },
  "mrh": {
    "bound": ["lct:web4:domain:medical", "lct:web4:domain:legal"],
    "paired": ["lct:web4:translator:bot1", "lct:web4:hospital:xyz"],
    "witnessing": ["lct:web4:auditor:medical", "lct:web4:court:federal"]
  }
}
```

## 3. Dictionary Types

### 3.1 Domain Dictionaries

Bridge between professional/technical domains:

| Type | Source → Target | Examples |
|------|-----------------|----------|
| **Professional** | Medical → Legal | "myocardial infarction" → "heart attack resulting in disability claim" |
| **Technical** | Engineering → Business | "API latency" → "customer response time" |
| **Cultural** | Eastern → Western | "guanxi" → "relationship capital with reciprocal obligations" |
| **Temporal** | Historical → Modern | "telegram STOP" → "message sent." |

### 3.2 Model Dictionaries

Bridge between AI systems:

```json
{
  "type": "model_dictionary",
  "source_model": "gpt-4-vision",
  "target_model": "claude-3-opus",
  "translation_spec": {
    "embedding_alignment": {
      "method": "procrustes",
      "dimensions": 1536,
      "correlation": 0.87
    },
    "token_mapping": {
      "source_vocab": 100000,
      "target_vocab": 120000,
      "overlap": 0.75
    },
    "context_window": {
      "source": 128000,
      "target": 200000,
      "chunking_strategy": "semantic"
    }
  }
}
```

### 3.3 Compression Dictionaries

Manage lossy/lossless compression:

```json
{
  "type": "compression_dictionary",
  "compression_type": "semantic",
  "codebook": {
    "entries": 4096,
    "vector_dimension": 512,
    "quantization": "vector_quantized",
    "perplexity": 127.3
  },
  "reconstruction_fidelity": {
    "semantic": 0.95,
    "syntactic": 0.88,
    "pragmatic": 0.91
  }
}
```

### 3.4 Meta-Dictionaries

Translate between other dictionaries:

```json
{
  "type": "meta_dictionary",
  "purpose": "dictionary_alignment",
  "translates_between": [
    "lct:web4:dictionary:medical-legal",
    "lct:web4:dictionary:medical-insurance",
    "lct:web4:dictionary:legal-insurance"
  ],
  "provides": {
    "transitive_closure": true,
    "consistency_checking": true,
    "conflict_resolution": "weighted_voting"
  }
}
```

## 4. Translation Process

### 4.1 Translation Request

```json
{
  "type": "TranslationRequest",
  "source_content": "The patient presented with acute MI...",
  "source_domain": "medical",
  "target_domain": "legal",
  "context": {
    "purpose": "disability_claim",
    "jurisdiction": "california",
    "urgency": "high"
  },
  "trust_requirements": {
    "minimum_fidelity": 0.95,
    "require_witness": true,
    "atp_stake": 50
  }
}
```

### 4.2 Translation Flow

```python
def translate_with_dictionary(request, dictionary):
    # 1. Verify dictionary competence
    if not dictionary.covers_domains(request.source, request.target):
        raise IncompetentDictionary()
    
    # 2. Check trust requirements
    if dictionary.t3 < request.trust_requirements.minimum:
        raise InsufficientDictionaryTrust()
    
    # 3. Parse source content
    source_tokens = dictionary.tokenize(request.source_content)
    source_concepts = dictionary.extract_concepts(source_tokens)
    
    # 4. Map to target domain
    target_concepts = dictionary.map_concepts(
        source_concepts,
        context=request.context
    )
    
    # 5. Handle ambiguity
    if target_concepts.ambiguity > threshold:
        target_concepts = dictionary.disambiguate(
            target_concepts,
            method="context_aware"
        )
    
    # 6. Generate target content
    target_content = dictionary.generate(
        target_concepts,
        style=request.target_domain
    )
    
    # 7. Calculate confidence and degradation
    confidence = dictionary.calculate_confidence(
        source_concepts,
        target_concepts
    )
    
    degradation = 1.0 - confidence
    
    # 8. Create translation record
    return TranslationResult(
        content=target_content,
        confidence=confidence,
        degradation=degradation,
        dictionary_lct=dictionary.lct,
        witness_required=confidence < 0.95
    )
```

### 4.3 Trust Degradation Tracking

```json
{
  "translation_chain": [
    {
      "step": 1,
      "from": "medical",
      "to": "legal",
      "dictionary": "lct:web4:dict:med-legal",
      "confidence": 0.95,
      "degradation": 0.05
    },
    {
      "step": 2,
      "from": "legal",
      "to": "insurance",
      "dictionary": "lct:web4:dict:legal-ins",
      "confidence": 0.92,
      "degradation": 0.08
    }
  ],
  "cumulative_degradation": 0.126,  // 1 - (0.95 * 0.92)
  "trust_acceptable": true,
  "witness_attestation": ["lct:web4:witness:domain-expert"]
}
```

## 5. Dictionary Evolution

### 5.1 Learning from Feedback

Dictionaries improve through:

```python
def update_dictionary_from_feedback(dictionary, feedback):
    # 1. Collect correction signals
    if feedback.type == "correction":
        dictionary.add_correction(
            source=feedback.original,
            target=feedback.corrected,
            context=feedback.context,
            authority=feedback.corrector_lct
        )
    
    # 2. Update confidence scores
    if feedback.type == "validation":
        dictionary.update_confidence(
            mapping=feedback.mapping,
            success=feedback.success,
            witness=feedback.witness_lct
        )
    
    # 3. Detect semantic drift
    if dictionary.detect_drift():
        dictionary.trigger_retraining(
            method="incremental",
            data=recent_corrections
        )
    
    # 4. Update T3/V3 tensors
    dictionary.update_tensors(
        t3_delta=calculate_t3_change(feedback),
        v3_delta=calculate_v3_change(feedback)
    )
    
    # 5. Version update if significant
    if dictionary.changes > threshold:
        dictionary.create_new_version(
            parent=dictionary.current_version,
            changelog=accumulated_changes
        )
```

### 5.2 Community Curation

```json
{
  "curation_model": {
    "contributors": [
      {
        "lct": "lct:web4:expert:medical",
        "role": "source_domain_expert",
        "reputation": 0.95,
        "contributions": 234
      },
      {
        "lct": "lct:web4:expert:legal",
        "role": "target_domain_expert",
        "reputation": 0.92,
        "contributions": 189
      }
    ],
    "governance": {
      "proposal_threshold": 10,  // Min reputation to propose
      "approval_quorum": 0.66,   // Weighted by reputation
      "challenge_period": 86400   // 24 hours
    },
    "incentives": {
      "successful_contribution": 10,  // ATP reward
      "accepted_correction": 5,
      "validated_translation": 1
    }
  }
}
```

## 6. Dictionary Discovery and Selection

### 6.1 Discovery via MRH

Find appropriate dictionaries through SPARQL:

```sparql
SELECT ?dictionary ?trust ?coverage WHERE {
  ?dictionary a web4:Dictionary ;
              web4:sourceDomai "medical" ;
              web4:targetDomain "legal" ;
              web4:coverage ?coverage ;
              web4:trustScore ?trust .
  
  FILTER(?trust > 0.8)
  FILTER(?coverage > 0.9)
  
  # Check for recent activity
  ?dictionary web4:lastUpdated ?updated .
  FILTER(?updated > NOW() - "P30D"^^xsd:duration)
}
ORDER BY DESC(?trust * ?coverage)
LIMIT 5
```

### 6.2 Dictionary Selection Algorithm

```python
def select_best_dictionary(source, target, context):
    candidates = discover_dictionaries(source, target)
    
    scores = []
    for dict in candidates:
        score = calculate_score(
            trust=dict.t3.average(),
            coverage=dict.coverage_for_context(context),
            recency=dict.last_update_age(),
            cost=dict.atp_cost,
            latency=dict.response_time
        )
        scores.append((dict, score))
    
    # Sort by score, return best
    return sorted(scores, key=lambda x: x[1], reverse=True)[0][0]
```

## 7. Dictionary-R6 Integration

### 7.1 Translation as R6 Action

Every translation follows R6:

```json
{
  "type": "dictionary_translation",
  "rules": {
    "min_fidelity": 0.9,
    "require_witness": true
  },
  "role": {
    "entity": "lct:web4:dictionary:med-legal",
    "roleType": "web4:Translator"
  },
  "request": {
    "action": "translate",
    "source_content": "...",
    "target_domain": "legal"
  },
  "reference": {
    "similar_translations": [...],
    "domain_precedents": [...]
  },
  "resource": {
    "required": {
      "atp": 10,
      "compute": "medium"
    }
  },
  "result": {
    "translation": "...",
    "confidence": 0.94,
    "degradation": 0.06
  }
}
```

## 8. Security and Trust

### 8.1 Attack Mitigation

| Attack Type | Mitigation |
|-------------|------------|
| **Semantic poisoning** | Community validation, witness requirements |
| **Translation bias** | Multi-dictionary consensus, audit trails |
| **Context manipulation** | Signed context, proof-of-provenance |
| **Drift exploitation** | Continuous monitoring, version pinning |
| **Reputation gaming** | ATP staking, temporal decay |

### 8.2 Trust Building

Dictionaries build trust through:

1. **Successful translations** - Each success increases T3
2. **Witness attestations** - Third-party validation
3. **Community curation** - Expert contributions
4. **Consistency** - Reliable performance over time
5. **Transparency** - Open audit trails

## 9. Implementation Requirements

### 9.1 MUST Requirements

1. Every Dictionary MUST have a valid LCT
2. Dictionaries MUST track confidence and degradation
3. Translations MUST be witnessable
4. Evolution MUST be versioned
5. Critical translations MUST require ATP stake

### 9.2 SHOULD Requirements

1. Dictionaries SHOULD support bidirectional translation
2. Dictionaries SHOULD provide confidence intervals
3. Dictionaries SHOULD detect semantic drift
4. Dictionaries SHOULD enable community curation
5. Dictionaries SHOULD maintain translation history

### 9.3 MAY Requirements

1. Dictionaries MAY support multi-hop translation
2. Dictionaries MAY offer specialized sub-dictionaries
3. Dictionaries MAY implement caching strategies
4. Dictionaries MAY provide real-time updates
5. Dictionaries MAY support dialect variations

## 10. Use Cases

### 10.1 Medical-Legal Translation

Hospital records → Insurance claims → Legal proceedings

```yaml
chain:
  - source: "Patient diagnosed with moderate TBI following MVA"
  - step1: medical → insurance
    output: "Traumatic brain injury from vehicle accident requiring coverage"
  - step2: insurance → legal  
    output: "Plaintiff sustained head trauma with cognitive impairment in collision"
  cumulative_confidence: 0.88
  witnesses: [medical_expert, insurance_adjuster, legal_clerk]
```

### 10.2 AI Model Bridging

GPT-4 output → Claude-3 input with context preservation

```yaml
translation:
  source_model: "gpt-4"
  source_output: {embeddings: [...], attention_weights: [...]}
  dictionary: "lct:web4:dict:gpt4-claude3"
  target_model: "claude-3"
  target_input: {context: [...], instructions: [...]}
  fidelity: 0.93
  information_preserved: 0.91
```

### 10.3 Cross-Cultural Business

Eastern business concepts → Western frameworks

```yaml
translation:
  source: "建立关系网需要面子和人情"
  dictionary: "lct:web4:dict:chinese-business"
  target: "Building network relationships requires reputation capital and reciprocal obligations"
  cultural_context: "emphasis on long-term reciprocity vs transactional"
  confidence: 0.85
```

## 11. Dictionary Reputation Economy

### 11.1 Earning Mechanisms

Dictionaries earn ATP through:
- Successful translations (base rate)
- High-confidence translations (bonus)
- Witness attestations (multiplier)
- Community contributions (shares)

### 11.2 Staking and Slashing

```python
class DictionaryStaking:
    def stake_on_translation(self, amount, confidence_claim):
        """Stake ATP on translation quality claim"""
        if actual_confidence >= confidence_claim:
            return amount * 1.1  # 10% reward
        else:
            return amount * (actual_confidence / confidence_claim)  # Partial slash
```

## 12. Future Extensions

### 12.1 Quantum Dictionaries
- Superposition of meanings until observed
- Entangled translations across domains
- Quantum-safe semantic commitments

### 12.2 Emergent Dictionaries
- Self-organizing from usage patterns
- No explicit curation needed
- Evolution through natural selection

### 12.3 Holographic Dictionaries
- Every part contains the whole
- Graceful degradation under damage
- Fractal semantic structures

## 13. Summary

Dictionary Entities are not mere translation tools but living participants in Web4's trust economy. They:

- **Bridge semantic gaps** between domains, models, and cultures
- **Manage compression-trust** relationships fundamental to communication
- **Evolve and learn** from community feedback and usage
- **Build reputation** through successful service
- **Enable interoperability** across the entire Web4 ecosystem

By treating dictionaries as first-class entities with their own presence, relationships, and reputation, Web4 solves the fundamental challenge of semantic interoperability in a decentralized, multi-stakeholder environment.

---

*"In Web4, dictionaries don't just translate words—they negotiate meaning, build trust, and evolve understanding across the boundaries that divide us."*