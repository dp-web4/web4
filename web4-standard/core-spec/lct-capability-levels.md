# LCT Capability Levels - Core Specification

**Status**: Core Specification v1.0.0
**Date**: January 3, 2026
**Category**: Identity & Context
**Depends On**: LCT Core Spec, T3/V3 Tensors, MRH Specification

## Abstract

This specification defines a **capability levels framework** for Linked Context Tokens (LCTs) that enables consistent terminology while accommodating reduced implementations. LCTs are used fractally across Web4 - from hardware-bound device identities to ephemeral IRP plugin instances. This specification establishes:

1. **Six capability levels** (0-5) from stub to hardware-bound
2. **Entity type taxonomy** for fractal LCT usage
3. **Capability query protocol** for cross-domain discovery
4. **Required vs optional fields** per level
5. **Stub format** for unimplemented components

## 1. Introduction

### 1.1 Purpose

Not all LCTs require full functionality. An IRP plugin needs different capabilities than a society-issued birth certificate. However, **terminology must remain consistent** - an LCT is always a Linked Context Token, T3 always has 6 dimensions, MRH always contains bound/paired/witnessing relationships.

This specification allows:
- **Reduced implementations** for edge/embedded contexts
- **Consistent structure** across all capability levels
- **Capability discovery** before establishing trust relationships
- **Clear upgrade paths** from minimal to full LCT

### 1.2 Terminology

All implementations MUST use these terms exactly:

| Term | Meaning | NEVER Use |
|------|---------|-----------|
| **LCT** | Linked Context Token | "Lifecycle-Continuous Trust", "Lineage-Context-Task" |
| **T3** | Trust Tensor (6 dimensions) | Old 3-dimension "Talent/Training/Temperament" |
| **V3** | Value Tensor (6 dimensions) | Old 3-dimension "Valuation/Veracity/Validity" |
| **MRH** | Markov Relevancy Horizon | "Relevancy Horizon", "Context Horizon" |

### 1.3 Design Principles

1. **Terminology is sacred** - Names have one meaning everywhere
2. **Implementation is flexible** - Components can be stubs
3. **All fields present** - Structure is consistent, values may be null
4. **Query before trust** - Capability discovery precedes relationships
5. **Fractal application** - Same framework at all scales

## 2. Capability Levels

### 2.1 Level Definitions

| Level | Name | Description | Trust Tier |
|-------|------|-------------|------------|
| 0 | STUB | Placeholder reference, pending entity | Untrusted |
| 1 | MINIMAL | Self-issued bootstrap, basic plugin identity | 0.0-0.2 |
| 2 | BASIC | Operational plugins with relationships | 0.2-0.4 |
| 3 | STANDARD | Autonomous agents with full tensors | 0.4-0.6 |
| 4 | FULL | Society-issued with birth certificate | 0.6-0.8 |
| 5 | HARDWARE | Hardware-bound identity (TPM/TrustZone) | 0.8-1.0 |

### 2.2 Level 0: STUB

**Purpose**: Placeholder reference for entities not yet instantiated.

**Required Fields**:
- `lct_id`: Valid format (`lct:web4:{type}:...`)
- `capability_level`: 0
- `entity_type`: REQUIRED (may be "pending")

**All Other Fields**: null or omitted

```json
{
  "lct_id": "lct:web4:pending:placeholder123",
  "capability_level": 0,
  "entity_type": "pending",
  "binding": null,
  "mrh": null,
  "t3_tensor": null,
  "v3_tensor": null
}
```

**Use Cases**:
- Forward reference before entity exists
- Placeholder in pattern templates
- Reference to unresolved external entity

### 2.3 Level 1: MINIMAL

**Purpose**: Self-issued bootstrap, basic plugin identity.

**Required Fields**:
- All Level 0 fields
- `binding.public_key`: Software key (Ed25519 or P-256)
- `binding.binding_proof`: Self-signed
- `mrh`: Empty but present
- `t3_tensor`: All 6 dimensions with initial values
- `v3_tensor`: All 6 dimensions with zero values

```json
{
  "lct_id": "lct:web4:plugin:vision-irp-abc123",
  "capability_level": 1,
  "entity_type": "plugin",
  "subject": "did:web4:key:abc123",

  "binding": {
    "entity_type": "plugin",
    "public_key": "mb64:ed25519:...",
    "hardware_anchor": null,
    "created_at": "2026-01-03T00:00:00Z",
    "binding_proof": "cose:ES256:..."
  },

  "mrh": {
    "bound": [],
    "paired": [],
    "witnessing": [],
    "horizon_depth": 1,
    "last_updated": "2026-01-03T00:00:00Z"
  },

  "policy": {
    "capabilities": [],
    "constraints": {}
  },

  "t3_tensor": {
    "dimensions": {
      "technical_competence": 0.1,
      "social_reliability": 0.1,
      "temporal_consistency": 0.1,
      "witness_count": 0.0,
      "lineage_depth": 0.0,
      "context_alignment": 0.1
    },
    "composite_score": 0.067,
    "last_computed": "2026-01-03T00:00:00Z",
    "computation_witnesses": []
  },

  "v3_tensor": {
    "dimensions": {
      "energy_balance": 0,
      "contribution_history": 0.0,
      "resource_stewardship": 0.0,
      "network_effects": 0.0,
      "reputation_capital": 0.0,
      "temporal_value": 0.0
    },
    "composite_score": 0.0,
    "last_computed": "2026-01-03T00:00:00Z",
    "computation_witnesses": []
  },

  "birth_certificate": {
    "stub": true,
    "reason": "Self-issued entity"
  }
}
```

**Use Cases**:
- IRP plugin identity
- Self-issued agent bootstrap
- Test/development entities

### 2.4 Level 2: BASIC

**Purpose**: Operational plugins with established relationships.

**Additional Requirements over Level 1**:
- `mrh.bound` OR `mrh.paired`: At least one relationship
- `t3_tensor.dimensions`: All 6 with non-zero values
- `policy.capabilities`: At least one capability

```json
{
  "capability_level": 2,

  "mrh": {
    "bound": [
      {
        "lct_id": "lct:web4:ai:orchestrator",
        "type": "parent",
        "binding_context": "deployment",
        "ts": "2026-01-03T00:00:00Z"
      }
    ],
    "paired": [],
    "witnessing": [],
    "horizon_depth": 2
  },

  "policy": {
    "capabilities": ["execute:irp", "read:patterns"],
    "constraints": {
      "max_rate": 100
    }
  },

  "t3_tensor": {
    "dimensions": {
      "technical_competence": 0.5,
      "social_reliability": 0.4,
      "temporal_consistency": 0.3,
      "witness_count": 0.2,
      "lineage_depth": 0.3,
      "context_alignment": 0.5
    },
    "composite_score": 0.37
  }
}
```

**Use Cases**:
- Vision/Audio IRP plugins
- Memory plugins
- Federated pattern consumers

### 2.5 Level 3: STANDARD

**Purpose**: Autonomous agents with full tensor support.

**Additional Requirements over Level 2**:
- `mrh.witnessing`: At least one witness relationship
- `t3_tensor.computation_witnesses`: At least one oracle
- `v3_tensor.dimensions.energy_balance`: Non-zero ATP
- `attestations`: At least one attestation

```json
{
  "capability_level": 3,

  "mrh": {
    "bound": [...],
    "paired": [...],
    "witnessing": [
      {
        "lct_id": "lct:web4:oracle:time:global",
        "role": "time",
        "last_attestation": "2026-01-03T00:00:00Z",
        "witness_count": 10
      }
    ],
    "horizon_depth": 3
  },

  "t3_tensor": {
    "dimensions": {
      "technical_competence": 0.7,
      "social_reliability": 0.6,
      "temporal_consistency": 0.65,
      "witness_count": 0.5,
      "lineage_depth": 0.4,
      "context_alignment": 0.7
    },
    "composite_score": 0.59,
    "computation_witnesses": ["lct:web4:oracle:trust:federation"]
  },

  "v3_tensor": {
    "dimensions": {
      "energy_balance": 100,
      "contribution_history": 0.5,
      "resource_stewardship": 0.6,
      "network_effects": 0.4,
      "reputation_capital": 0.5,
      "temporal_value": 0.55
    },
    "composite_score": 0.51,
    "computation_witnesses": ["lct:web4:oracle:value:federation"]
  },

  "attestations": [
    {
      "witness": "did:web4:key:oracle123",
      "type": "existence",
      "claims": {"observed_at": "2026-01-03T00:00:00Z"},
      "sig": "cose:ES256:...",
      "ts": "2026-01-03T00:00:00Z"
    }
  ]
}
```

**Use Cases**:
- SAGE consciousness instances
- Federation coordinators
- Pattern sources

### 2.6 Level 4: FULL

**Purpose**: Society-issued identities with birth certificates.

**Additional Requirements over Level 3**:
- `birth_certificate`: Complete with all fields
- `birth_certificate.birth_witnesses`: Minimum 3
- `mrh.paired`: Permanent citizen role pairing
- `lineage`: At least genesis entry
- `revocation`: Status tracking

```json
{
  "capability_level": 4,

  "birth_certificate": {
    "issuing_society": "lct:web4:society:web4-foundation",
    "citizen_role": "lct:web4:role:citizen:researcher",
    "birth_timestamp": "2026-01-03T00:00:00Z",
    "birth_witnesses": [
      "lct:web4:witness:1",
      "lct:web4:witness:2",
      "lct:web4:witness:3"
    ],
    "genesis_block_hash": "0x...",
    "birth_context": "federation"
  },

  "mrh": {
    "paired": [
      {
        "lct_id": "lct:web4:role:citizen:researcher",
        "pairing_type": "birth_certificate",
        "permanent": true,
        "ts": "2026-01-03T00:00:00Z"
      }
    ]
  },

  "lineage": [
    {
      "parent": null,
      "reason": "genesis",
      "ts": "2026-01-03T00:00:00Z"
    }
  ],

  "revocation": {
    "status": "active",
    "ts": null,
    "reason": null
  }
}
```

**Use Cases**:
- Human identities
- Organization identities
- Core infrastructure entities

### 2.7 Level 5: HARDWARE

**Purpose**: Hardware-bound identity with TPM/TrustZone attestation.

**Additional Requirements over Level 4**:
- `binding.hardware_anchor`: Valid EAT token
- `binding.hardware_type`: "tpm2", "trustzone", or "secure_element"
- `hardware_attestation`: Complete attestation section

```json
{
  "capability_level": 5,

  "binding": {
    "entity_type": "device",
    "public_key": "mb64:coseKey:...",
    "hardware_anchor": "eat:mb64:hw:...",
    "hardware_type": "tpm2",
    "attestation_chain": [
      "eat:manufacturer:...",
      "eat:platform:...",
      "eat:application:..."
    ],
    "created_at": "2026-01-03T00:00:00Z",
    "binding_proof": "cose:ES256:..."
  },

  "hardware_attestation": {
    "platform": "linux-tpm2",
    "key_storage": "tpm",
    "boot_integrity": true,
    "pcr_values": {
      "0": "...",
      "7": "..."
    },
    "last_attestation": "2026-01-03T00:00:00Z"
  }
}
```

**Use Cases**:
- Physical IoT devices
- Secure servers
- Edge computing nodes
- Critical infrastructure

## 3. Entity Types

### 3.1 Core Entity Types

These entity types are defined in the LCT Core Specification:

| Type | Description | Typical Level |
|------|-------------|---------------|
| `human` | Human identity | 4-5 |
| `ai` | AI agent/consciousness | 2-4 |
| `organization` | Collective/company | 4 |
| `role` | Functional role | 1-3 |
| `task` | Ephemeral task context | 1-2 |
| `resource` | Data/asset reference | 1-3 |
| `device` | Physical hardware | 3-5 |
| `service` | API/service endpoint | 2-4 |
| `oracle` | External data provider | 3-4 |
| `accumulator` | Aggregation entity | 2-3 |
| `dictionary` | Semantic domain keeper | 3-4 |
| `hybrid` | Multiple types | varies |

### 3.2 Extended Entity Types

These additional types support fractal LCT usage:

| Type | Description | Typical Level |
|------|-------------|---------------|
| `plugin` | IRP plugin component | 1-2 |
| `session` | Ephemeral conversation | 1-2 |
| `relationship` | Connection-as-entity | 1-2 |
| `pattern` | Pattern template | 1-3 |
| `society` | Governance context | 4-5 |
| `witness` | Attestation provider | 3-4 |
| `pending` | Not yet instantiated | 0 |

### 3.3 Entity-Level Compatibility

Implementations SHOULD enforce these typical level ranges:

```python
ENTITY_LEVEL_RANGES = {
    "human": (4, 5),
    "ai": (2, 4),
    "plugin": (1, 2),
    "device": (3, 5),
    "session": (1, 2),
    "society": (4, 5),
    # ... etc
}
```

## 4. Capability Query Protocol

### 4.1 Purpose

Any entity SHOULD be able to query another LCT's capabilities before establishing trust relationships. This enables:

- **Compatibility checking** before pairing
- **Trust tier assessment** without full LCT exchange
- **Feature negotiation** for cross-domain communication

### 4.2 Query Request

```json
{
  "query_type": "capability_discovery",
  "target_lct": "lct:web4:ai:target-agent",
  "requester_lct": "lct:web4:plugin:requesting-plugin",
  "requested_info": [
    "capability_level",
    "entity_type",
    "supported_components",
    "relationship_types",
    "trust_tier"
  ],
  "timestamp": "2026-01-03T00:00:00Z",
  "signature": "cose:ES256:..."
}
```

### 4.3 Query Response

```json
{
  "response_type": "capability_discovery",
  "source_lct": "lct:web4:ai:target-agent",
  "capability_level": 3,
  "entity_type": "ai",

  "supported_components": {
    "binding": {
      "implemented": true,
      "hardware_anchored": false,
      "key_algorithm": "Ed25519"
    },
    "mrh": {
      "implemented": true,
      "relationship_types": ["bound", "paired", "witnessing"],
      "horizon_depth": 3
    },
    "t3_tensor": {
      "implemented": true,
      "dimensions": 6,
      "oracle_computed": true
    },
    "v3_tensor": {
      "implemented": true,
      "dimensions": 6,
      "oracle_computed": true
    },
    "birth_certificate": {
      "implemented": false,
      "stub": true
    },
    "attestations": {
      "implemented": true,
      "count": 5
    },
    "lineage": {
      "implemented": false,
      "stub": true
    }
  },

  "relationship_support": {
    "can_be_bound_by": ["device", "organization"],
    "can_pair_with": ["plugin", "service", "ai", "human"],
    "can_witness": ["plugin", "task", "session"],
    "can_be_witnessed_by": ["oracle", "human", "ai"]
  },

  "trust_tier": "medium",
  "composite_t3": 0.59,
  "composite_v3": 0.51,

  "timestamp": "2026-01-03T00:00:00Z",
  "signature": "cose:ES256:..."
}
```

### 4.4 Response Validation

The query response MUST be:

1. **Signed** by the source LCT's binding key
2. **Current** (timestamp within 5 minutes)
3. **Accurate** (misrepresentation is trust violation)
4. **Complete** (all requested fields present)

## 5. Stub Format

### 5.1 Purpose

When a component is not implemented, it MUST be present as a **stub** rather than omitted. This ensures:

- Consistent structure across all capability levels
- Clear indication of what is/isn't supported
- Forward compatibility for upgrades

### 5.2 Stub Structure

All stubs MUST contain:

```json
{
  "stub": true,
  "reason": "Human-readable explanation"
}
```

### 5.3 Component Stubs

#### T3 Tensor Stub
```json
{
  "t3_tensor": {
    "dimensions": {
      "technical_competence": null,
      "social_reliability": null,
      "temporal_consistency": null,
      "witness_count": null,
      "lineage_depth": null,
      "context_alignment": null
    },
    "composite_score": null,
    "stub": true,
    "reason": "Level 0 entity"
  }
}
```

#### Birth Certificate Stub
```json
{
  "birth_certificate": {
    "issuing_society": null,
    "citizen_role": null,
    "birth_witnesses": [],
    "stub": true,
    "reason": "Self-issued entity"
  }
}
```

#### Hardware Attestation Stub
```json
{
  "hardware_attestation": {
    "platform": null,
    "key_storage": "software",
    "stub": true,
    "reason": "Software-only binding"
  }
}
```

## 6. Level Upgrade Path

### 6.1 Upgrade Requirements

Entities MAY upgrade their capability level by adding required components:

| Upgrade | Requirements |
|---------|--------------|
| 0 → 1 | Add binding with public key, initialize T3/V3 |
| 1 → 2 | Establish MRH relationship, add policy capability |
| 2 → 3 | Add witnessing, get oracle tensors, receive attestation |
| 3 → 4 | Obtain birth certificate from society |
| 4 → 5 | Bind to hardware (cannot be done post-hoc) |

### 6.2 Upgrade Constraints

- Level 5 (HARDWARE) requires hardware binding from creation
- Level 4 (FULL) requires society issuance
- Lower levels can self-upgrade by meeting requirements
- Downgrades are not permitted (would break trust chains)

## 7. Cross-Domain Communication

### 7.1 Common Ground Protocol

When LCTs from different domains interact:

1. **Capability Discovery**: Query each other's capability levels
2. **Common Ground**: Establish minimum shared capability level
3. **Adaptation**: Higher-level entity MAY simplify for lower-level
4. **Trust Calculation**: Use lowest common T3 computation method
5. **Relationship Type**: Constrained by lower entity's supported types

### 7.2 Example: Level 5 Device ↔ Level 2 Plugin

```
Device (Level 5) wants to pair with Plugin (Level 2)

1. Device queries Plugin capabilities
   → Response: Level 2, can_pair_with: [ai, plugin, service]

2. Establish common level = min(5, 2) = 2
   → Use Level 2 relationship semantics

3. Check compatibility
   → Device is not in Plugin's can_pair_with list
   → Relationship denied OR Device presents as "service" role

4. If compatible, create pairing at Level 2
   → Plugin's MRH updated with Device as paired entity
   → Trust derived from Plugin's self-computed T3
```

## 8. Implementation Requirements

### 8.1 Validators MUST

- Verify `lct_id` format: `lct:web4:{entity_type}:{hash}`
- Verify `capability_level` matches implemented components
- Verify all 6 T3 dimensions present (value or null)
- Verify all 6 V3 dimensions present (value or null)
- Verify stubs have `stub: true` and `reason` fields

### 8.2 Entities MUST

- Declare accurate capability level
- Respond truthfully to capability queries
- Include stubs for unimplemented components
- Use canonical terminology in all communications

### 8.3 Societies MUST

- Issue birth certificates only to Level 4+ entities
- Maintain witness quorum (≥3) for birth certificates
- Compute T3/V3 via oracles for Level 3+ entities
- Enforce capability level requirements for membership

## 9. Security Considerations

### 9.1 Capability Misrepresentation

Falsely claiming higher capability level is a trust violation:

- **Detection**: Capability queries reveal actual implementation
- **Consequence**: T3 scores degraded, potential revocation
- **Prevention**: Validators check claimed vs actual components

### 9.2 Stub Exploitation

Stubs must not create security vulnerabilities:

- **Stubs are explicit**: `stub: true` clearly marks unimplemented
- **Stubs are not defaults**: Cannot rely on stub behavior
- **Stubs block operations**: Stubbed components cannot be used

### 9.3 Level Upgrade Attacks

Unauthorized level upgrades are prevented by:

- **Society issuance** required for Level 4
- **Hardware binding** cannot be added post-hoc for Level 5
- **Witness attestation** required for Level 3
- **MRH relationships** must be mutual for Level 2

## 10. References

- **LCT Core Specification**: `core-spec/LCT-linked-context-token.md`
- **T3/V3 Tensor Specification**: `core-spec/t3-v3-tensors.md`
- **MRH Specification**: `core-spec/mrh-tensors.md`
- **Reference Implementation**: `implementation/reference/lct_capability_levels.py`

---

**Version**: 1.0.0
**Status**: Core Specification
**Last Updated**: January 3, 2026

*"An LCT at any level is still an LCT - the terminology is sacred, the implementation is flexible."*
