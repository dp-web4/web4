# Web4 Quick Reference Guide

## Entity Types

### Primary Categories

| Type | Mode | Description | Example Use Cases |
|------|------|-------------|-------------------|
| **Human** | Agentic | Individual persons | End users, developers, administrators |
| **AI** | Agentic | Artificial intelligence agents | Chatbots, analysis engines, autonomous agents |
| **Organization** | Delegative | Collective entities | Companies, DAOs, communities |
| **Role** | Delegative | Functions as first-class entities | Developer, Auditor, Energy Provider |
| **Task** | Responsive | Work units with objectives | Data processing job, verification task |
| **Resource** | Responsive | Data, services, or assets | Databases, APIs, compute resources |
| **Device** | Responsive/Agentic | Physical or virtual hardware | IoT sensors, servers, vehicles |
| **Service** | Responsive | Software services | Web services, microservices |
| **Oracle** | Responsive | External data providers | Price feeds, weather data |
| **Accumulator** | Responsive | Broadcast recorders | Presence validators, history indexers |
| **Dictionary** | Responsive | Semantic bridges | Medical-legal translator, tech interpreter |
| **Hybrid** | Mixed | Combined entity types | Human-AI teams, cyborg systems |

### Behavioral Modes

- **Agentic**: Self-directed, goal-seeking, initiates interactions
- **Responsive**: Reactive, deterministic, accepts but doesn't initiate
- **Delegative**: Authorizes others, grants permissions, defines scope

## Relationship Mechanisms

### BINDING (Permanent Attachment)
```abnf
binding-request = "BIND/1.0" SP entity-type SP public-key SP hardware-id
```
- Creates parent-child relationships
- Permanent and unforgeable
- Updates both entities' MRH

### PAIRING (Operational Relationships)

**Three Modes:**
1. **Direct**: P2P, entities negotiate directly
2. **Witnessed**: P2P with third-party attestation
3. **Authorized**: Mediated by authority entity

```abnf
direct-pairing = "PAIR/1.0" SP "DIRECT" SP lct-a SP lct-b SP context SP rules
witnessed-pairing = "PAIR/1.0" SP "WITNESSED" SP lct-a SP lct-b SP witness SP context SP rules
authorized-pairing = "PAIR/1.0" SP "AUTHORIZED" SP lct-a SP lct-b SP authority SP context SP rules
```
- Context-specific operations
- Session-based with keys
- Enables R6 actions between entities

### WITNESSING (Trust Building)
```abnf
witness-assertion = "WTNS/1.0" SP observer-lct SP observed-lct SP evidence
```
- Creates bidirectional trust links
- Evidence types: EXISTENCE, ACTION, STATE, TRANSITION
- Accumulates to strengthen presence

### BROADCAST (Discovery)
```abnf
broadcast-message = "CAST/1.0" SP sender-id SP message-type SP payload
```
- Unidirectional announcements
- No relationship formed
- Enables accumulator-based witnessing

## R6 Action Framework

Every interaction follows: **Rules + Role + Request + Reference + Resource → Result**

```json
{
  "r6_action": {
    "action_id": "r6:web4:mb32...",
    "rules": {
      "applicable": ["transfer", "compute"],
      "constraints": ["max_atp: 100"]
    },
    "role": {
      "lct": "lct:web4:role:...",
      "permissions": ["read", "write"]
    },
    "request": {
      "intent": "process_data",
      "parameters": {...}
    },
    "reference": {
      "similar_actions": ["r6:web4:..."],
      "confidence": 0.92
    },
    "resource": {
      "atp_required": 10,
      "compute_units": 500
    },
    "result": {
      "outcome": "success",
      "t3_impact": {...},
      "v3_generated": {...}
    }
  }
}
```

## T3/V3 Tensors

### T3 (Trust) Dimensions
| Dimension | Range | Measures | Updates |
|-----------|-------|----------|---------|
| **Talent** | 0.0-1.0 | Natural aptitude | Novel solutions: +0.02-0.05 |
| **Training** | 0.0-1.0 | Acquired expertise | Success: +0.005-0.01, Decay: -0.001/month |
| **Temperament** | 0.0-1.0 | Reliability | Consistency: +0.005, Violations: -0.10 |

### V3 (Value) Dimensions
| Dimension | Range | Measures | Calculation |
|-----------|-------|----------|-------------|
| **Valuation** | Variable | Subjective worth | ATP_earned / ATP_expected |
| **Veracity** | 0.0-1.0 | Objective accuracy | verified_claims / total_claims |
| **Validity** | 0.0-1.0 | Successful delivery | 1.0 if delivered, else 0.0 |

## LCT Structure

```json
{
  "lct_id": "lct:web4:mb32...",
  "subject": "did:web4:key:...",
  "binding": {
    "entity_type": "human",
    "public_key": "mb64:...",
    "created_at": "2025-01-11T15:00:00Z"
  },
  "mrh": {
    "bound": [],     // Parent/child relationships
    "paired": [],    // Operational relationships
    "witnessing": [] // Trust attestations
  },
  "policy": {
    "capabilities": ["pairing:initiate"],
    "constraints": {}
  }
}
```

## MRH (Markov Relevancy Horizon)

Dynamic context emerging from relationships:

- **bound**: Permanent binding relationships (parent/child/sibling)
- **paired**: Active operational relationships with context
- **witnessing**: Entities providing attestations
- **horizon_depth**: Maximum relationship depth to track (default: 3)

Updates occur on:
- New binding/pairing/witnessing
- Relationship revocation
- Context changes

## Dictionary Entity Operations

### Translation Process
```
Source Domain → Dictionary → Target Domain
"Iatrogenic" → "Caused by doctor" → "Medical malpractice"
(0.95 trust) → (0.90 trust) → (0.85 trust)
```

### Trust Degradation
- Each hop reduces trust by ~5-10%
- Minimum acceptable threshold: 0.80
- Failed translations void results

## Cryptographic Baseline (W4-BASE-1)

**MUST Implement:**
- X25519 for key exchange
- Ed25519 for signatures
- ChaCha20-Poly1305 for encryption
- SHA-256 for hashing
- CBOR for serialization

**SHOULD Implement:**
- P-256/ES256 for ecosystem bridging
- JSON as alternative encoding

## Error Handling (RFC 9457)

```json
{
  "type": "https://web4.io/errors/invalid-lct",
  "title": "Invalid LCT Structure",
  "status": 400,
  "detail": "Missing required field: binding.public_key",
  "instance": "/lct/validate/abc123"
}
```

## Common Patterns

### Role-Agent Pairing
1. Agent pairs with Role LCT
2. Permissions transfer to agent
3. Performance tracked on both
4. Reputation impacts both entities

### Dictionary Chain Translation
1. Select dictionaries by domain pairs
2. Calculate trust degradation path
3. Perform sequential translation
4. Verify minimum trust threshold

### Witness Accumulation
1. Entity performs action
2. Multiple witnesses observe
3. Attestations added to LCT
4. Trust score increases

### Broadcast Discovery
1. Entity broadcasts capabilities
2. Accumulators record broadcasts
3. Other entities query accumulators
4. Pairing initiated if match found

## Implementation Checklist

- [ ] Implement W4-BASE-1 crypto suite
- [ ] Support all 12 entity types
- [ ] Handle 4 relationship mechanisms
- [ ] Process R6 actions
- [ ] Calculate T3/V3 tensors
- [ ] Maintain MRH dynamically
- [ ] Support dictionary translation
- [ ] Enable broadcast accumulation
- [ ] Follow RFC 9457 for errors
- [ ] Provide test vectors