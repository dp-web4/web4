# LCT Capability Levels Specification

**Status**: Design Draft v1.0
**Date**: 2026-01-03
**Author**: CBP Session (Dennis + Claude)
**Depends On**: LCT Core Spec, T3/V3 Tensors, MRH Specification

---

## Abstract

This specification defines a **capability levels framework** for Linked Context Tokens (LCTs) that enables consistent terminology while accommodating reduced implementations. Not all LCTs require full functionality - an IRP plugin needs different capabilities than a society-issued birth certificate.

The framework establishes:
1. **Six capability levels** (0-5) from stub to hardware-bound
2. **Entity type taxonomy** for fractal LCT usage
3. **Capability query protocol** for cross-domain discovery
4. **Required vs optional fields** per level
5. **Migration path** for upgrading LCT implementations

---

## Design Principles

### 1. Consistent Terminology
All implementations MUST use canonical Web4 terminology:
- **LCT** = Linked Context Token (never "Lifecycle-Continuous Trust" or other variants)
- **T3** = Trust Tensor (6 dimensions: technical_competence, social_reliability, temporal_consistency, witness_count, lineage_depth, context_alignment)
- **V3** = Value Tensor (6 dimensions: energy_balance, contribution_history, resource_stewardship, network_effects, reputation_capital, temporal_value)
- **MRH** = Markov Relevancy Horizon (bound/paired/witnessing relationships)

### 2. Graceful Degradation
Implementations MAY omit features they don't need, but:
- All components MUST be present in the structure (even if stub/empty)
- Capability level MUST be declared explicitly
- External queries MUST return clear capability descriptions

### 3. Fractal Application
LCTs apply at multiple scales:
- **Macro**: Society birth certificates, hardware devices
- **Meso**: Autonomous agents, federated services
- **Micro**: IRP plugins, ephemeral sessions, relationships

### 4. Query Before Trust
Any entity SHOULD be able to query another LCT's capabilities before establishing trust relationships. The response reveals:
- What capability level is implemented
- Which components are functional vs stubbed
- What entity type this LCT represents
- What relationships are supported

---

## Capability Levels

### Level 0: STUB

**Purpose**: Placeholder reference, pending entity, minimal footprint

**Structure**:
```json
{
  "lct_id": "lct:web4:stub:...",
  "capability_level": 0,
  "entity_type": "pending",

  "binding": null,
  "mrh": null,
  "policy": null,
  "t3_tensor": null,
  "v3_tensor": null
}
```

**Requirements**:
- `lct_id`: REQUIRED (valid format)
- `capability_level`: REQUIRED (must be 0)
- `entity_type`: REQUIRED (may be "pending" or "unknown")
- All other fields: null or omitted

**Use Cases**:
- Forward reference before entity exists
- Placeholder in pattern templates
- Reference to external entity not yet resolved

**Trust Implications**:
- Zero trust (untrusted tier)
- Cannot participate in witnessing
- Cannot hold ATP/ADP balance

---

### Level 1: MINIMAL

**Purpose**: Self-issued bootstrap, basic plugin identity

**Structure**:
```json
{
  "lct_id": "lct:web4:minimal:...",
  "subject": "did:web4:key:...",
  "capability_level": 1,
  "entity_type": "plugin",

  "binding": {
    "entity_type": "plugin",
    "public_key": "mb64:...",
    "hardware_anchor": null,
    "created_at": "2026-01-03T00:00:00Z",
    "binding_proof": "cose:..."
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
  }
}
```

**Requirements**:
- All Level 0 fields
- `binding.public_key`: REQUIRED (software key acceptable)
- `binding.binding_proof`: REQUIRED (self-signed)
- `mrh`: REQUIRED (may be empty)
- `t3_tensor`: REQUIRED (low initial values)
- `v3_tensor`: REQUIRED (zero initial values)

**Use Cases**:
- IRP plugin identity
- Self-issued agent bootstrap
- Test/development entities

**Trust Implications**:
- Low trust (0.0-0.2 tier)
- Can accumulate trust through witnessing
- Minimal ATP allocation

---

### Level 2: BASIC

**Purpose**: Operational plugins, simple agents with relationships

**Additions over Level 1**:
```json
{
  "capability_level": 2,

  "mrh": {
    "bound": [
      {
        "lct_id": "lct:web4:agent:parent...",
        "type": "parent",
        "binding_context": "deployment",
        "ts": "2026-01-03T00:00:00Z"
      }
    ],
    "paired": [
      {
        "lct_id": "lct:web4:orchestrator:...",
        "pairing_type": "operational",
        "permanent": false,
        "ts": "2026-01-03T00:00:00Z"
      }
    ],
    "witnessing": [],
    "horizon_depth": 2
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
  },

  "policy": {
    "capabilities": ["execute:irp", "read:patterns"],
    "constraints": {
      "max_rate": 100
    }
  }
}
```

**Requirements**:
- All Level 1 fields
- `mrh.bound` OR `mrh.paired`: At least one relationship
- `t3_tensor.dimensions`: All 6 dimensions with non-zero values
- `policy.capabilities`: At least one capability

**Use Cases**:
- Vision/Audio IRP plugins
- Memory plugins
- Federated pattern consumers

**Trust Implications**:
- Low-medium trust (0.2-0.4 tier)
- Can participate in witnessing (as witnessed, not witness)
- Moderate ATP allocation

---

### Level 3: STANDARD

**Purpose**: Autonomous agents, federated entities with full tensor support

**Additions over Level 2**:
```json
{
  "capability_level": 3,

  "mrh": {
    "bound": [...],
    "paired": [...],
    "witnessing": [
      {
        "lct_id": "lct:web4:oracle:time:...",
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
    "computation_witnesses": ["lct:web4:oracle:trust:..."]
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
    "computation_witnesses": ["lct:web4:oracle:value:..."]
  },

  "attestations": [
    {
      "witness": "did:web4:key:...",
      "type": "existence",
      "claims": {...},
      "sig": "cose:ES256:...",
      "ts": "2026-01-03T00:00:00Z"
    }
  ],

  "lineage": []
}
```

**Requirements**:
- All Level 2 fields
- `mrh.witnessing`: At least one witness relationship
- `t3_tensor.computation_witnesses`: At least one oracle
- `v3_tensor.dimensions.energy_balance`: Non-zero ATP
- `attestations`: At least one attestation

**Use Cases**:
- SAGE consciousness instances
- Federation coordinators
- Pattern sources

**Trust Implications**:
- Medium-high trust (0.4-0.6 tier)
- Can witness other entities
- Full ATP participation

---

### Level 4: FULL

**Purpose**: Society-issued identities, core infrastructure

**Additions over Level 3**:
```json
{
  "capability_level": 4,

  "birth_certificate": {
    "issuing_society": "lct:web4:society:...",
    "citizen_role": "lct:web4:role:citizen:...",
    "birth_timestamp": "2026-01-03T00:00:00Z",
    "birth_witnesses": [
      "lct:web4:witness:1...",
      "lct:web4:witness:2...",
      "lct:web4:witness:3..."
    ],
    "genesis_block_hash": "0x...",
    "birth_context": "federation"
  },

  "mrh": {
    "paired": [
      {
        "lct_id": "lct:web4:role:citizen:...",
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

**Requirements**:
- All Level 3 fields
- `birth_certificate`: REQUIRED with all fields
- `birth_certificate.birth_witnesses`: Minimum 3
- `mrh.paired`: Permanent citizen role pairing
- `lineage`: At least genesis entry
- `revocation`: Status tracking

**Use Cases**:
- Human identities
- Organization identities
- Society member agents

**Trust Implications**:
- High trust (0.6-0.8 tier)
- Can issue attestations
- Full governance participation

---

### Level 5: HARDWARE-BOUND

**Purpose**: Physical devices, critical infrastructure with hardware attestation

**Additions over Level 4**:
```json
{
  "capability_level": 5,

  "binding": {
    "entity_type": "device",
    "public_key": "mb64:coseKey...",
    "hardware_anchor": "eat:mb64:hw:...",
    "hardware_type": "tpm2|trustzone|secure_element",
    "attestation_chain": [
      "eat:manufacturer:...",
      "eat:platform:...",
      "eat:application:..."
    ],
    "created_at": "2026-01-03T00:00:00Z",
    "binding_proof": "cose:ES256:..."
  },

  "hardware_attestation": {
    "platform": "linux-tpm2|arm-trustzone|ios-se|android-se",
    "key_storage": "tpm|trustzone|secure_enclave",
    "boot_integrity": true,
    "pcr_values": {...},
    "last_attestation": "2026-01-03T00:00:00Z"
  }
}
```

**Requirements**:
- All Level 4 fields
- `binding.hardware_anchor`: REQUIRED (valid EAT token)
- `binding.hardware_type`: REQUIRED
- `hardware_attestation`: REQUIRED
- Hardware key cannot be extracted

**Use Cases**:
- Physical IoT devices
- Secure servers
- Edge computing nodes
- Critical infrastructure

**Trust Implications**:
- Very high trust (0.8-1.0 tier)
- Root of trust for witness chains
- Maximum ATP privileges

---

## Entity Types

The following entity types are recognized across all capability levels:

### Core Types (from spec)
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

### Extended Types (for fractal use)
| Type | Description | Typical Level |
|------|-------------|---------------|
| `plugin` | IRP plugin component | 1-2 |
| `session` | Ephemeral conversation | 1-2 |
| `relationship` | Connection-as-entity | 1-2 |
| `pattern` | Pattern template | 1-3 |
| `society` | Governance context | 4-5 |
| `witness` | Attestation provider | 3-4 |
| `pending` | Not yet instantiated | 0 |

---

## Capability Query Protocol

### Query Request

Any entity can query another's capabilities:

```json
{
  "query_type": "capability_discovery",
  "target_lct": "lct:web4:agent:...",
  "requester_lct": "lct:web4:plugin:...",
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

### Query Response

```json
{
  "response_type": "capability_discovery",
  "source_lct": "lct:web4:agent:...",
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

  "trust_tier": "standard",
  "composite_t3": 0.59,
  "composite_v3": 0.51,

  "timestamp": "2026-01-03T00:00:00Z",
  "signature": "cose:ES256:..."
}
```

### Validation Rules

The query response MUST be:
1. **Signed** by the source LCT's binding key
2. **Current** (timestamp within 5 minutes)
3. **Accurate** (misrepresentation is trust violation)
4. **Complete** (all requested fields present)

---

## Component Stubs

When a component is not implemented, it MUST be present as a stub:

### T3 Tensor Stub
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

### Birth Certificate Stub
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

### Hardware Attestation Stub
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

---

## Level Upgrade Path

Entities can upgrade their capability level by adding required components:

### Level 1 → Level 2
- Establish at least one MRH relationship
- Populate all 6 T3 dimensions
- Define at least one policy capability

### Level 2 → Level 3
- Add witness relationships
- Get oracle-computed tensors
- Acquire ATP balance
- Receive at least one attestation

### Level 3 → Level 4
- Obtain birth certificate from society
- Establish permanent citizen pairing
- Meet witness quorum (3+)
- Initialize lineage tracking

### Level 4 → Level 5
- Bind to hardware security module
- Generate EAT attestation chain
- Prove boot integrity
- Cannot be done post-hoc (requires hardware from start)

---

## Cross-Domain Communication

When LCTs from different domains interact:

1. **Capability Discovery**: Query each other's capability levels
2. **Common Ground**: Establish minimum shared capability level
3. **Adaptation**: Higher-level entity MAY simplify for lower-level
4. **Trust Calculation**: Use lowest common T3 computation method
5. **Relationship Type**: Constrained by lower entity's supported types

### Example: Level 5 Device ↔ Level 2 Plugin

```python
def establish_relationship(high_lct, low_lct):
    # Query capabilities
    high_caps = high_lct.query_capabilities()
    low_caps = low_lct.query_capabilities()

    # Find common level
    common_level = min(high_caps.level, low_caps.level)  # 2

    # Constrain relationship types
    allowed = set(high_caps.can_pair_with) & set(low_caps.can_be_paired_with)

    # Use simpler trust calculation
    if low_caps.t3_tensor.oracle_computed:
        trust = low_caps.composite_t3
    else:
        trust = self_computed_trust(low_lct)

    # Create relationship at common level
    return create_pairing(high_lct, low_lct, level=common_level, trust=trust)
```

---

## Implementation Notes

### For IRP Plugins (Level 1-2)

IRP plugins SHOULD implement at minimum:
- Level 1 structure with Ed25519 binding
- Parent binding to orchestrator LCT
- T3 tensor with self-computed values
- Update T3 based on IRP refinement success

```python
class IRPPluginLCT:
    def __init__(self, plugin_name: str, parent_lct: str):
        self.capability_level = 1
        self.entity_type = "plugin"
        self.lct_id = generate_lct_id(plugin_name)

        # Minimal binding
        self.binding = {
            "entity_type": "plugin",
            "public_key": generate_ed25519_key(),
            "hardware_anchor": None,  # Stub
            "created_at": utc_now()
        }

        # Parent relationship
        self.mrh = {
            "bound": [{"lct_id": parent_lct, "type": "parent"}],
            "paired": [],
            "witnessing": [],
            "horizon_depth": 1
        }

        # Initial low trust
        self.t3_tensor = T3Tensor.minimal()
        self.v3_tensor = V3Tensor.zero()

    def update_trust_from_refinement(self, success: bool, iterations: int):
        """Update T3 based on IRP iteration success"""
        if success:
            self.t3_tensor.technical_competence += 0.01
            self.t3_tensor.temporal_consistency += 0.005
        else:
            self.t3_tensor.technical_competence -= 0.02
        self.t3_tensor.recompute_composite()
```

### For Consciousness Agents (Level 3)

SAGE instances SHOULD implement:
- Level 3 structure with attestation collection
- Oracle-computed T3/V3 (or self-computed with disclosure)
- Witnessing relationships with sensors
- ATP balance for attention allocation

### For Hardware Devices (Level 5)

Devices MUST implement:
- Level 5 structure with hardware attestation
- TPM or TrustZone key storage
- Boot integrity verification
- EAT attestation chain

---

## Migration from HRM Implementations

### Thor's LCT Format

**Current** (incorrect):
```
lct:web4:agent:{lineage}@{context}#{task}
```

**Corrected**:
```json
{
  "lct_id": "lct:web4:agent:...",
  "entity_type": "ai",
  "capability_level": 3,
  ...standard structure...
}
```

### Legion's LCT Format

**Current** (incorrect):
```
lct://{component}:{instance}:{role}@{network}
```

**Corrected**:
```json
{
  "lct_id": "lct:web4:plugin:...",
  "entity_type": "plugin",
  "capability_level": 2,
  ...standard structure...
}
```

### Migration Steps

1. Parse existing format to extract components
2. Map to canonical entity_type
3. Determine appropriate capability_level
4. Create standard structure with correct terminology
5. Populate T3/V3 from existing trust metrics
6. Establish MRH from existing relationships

---

## References

- **LCT Core Spec**: `web4-standard/core-spec/LCT-linked-context-token.md`
- **T3/V3 Tensors**: `web4-standard/core-spec/t3-v3-tensors.md`
- **MRH Specification**: `web4-standard/core-spec/mrh-tensors.md`
- **PSI Proposal**: `proposals/PATTERN_SOURCE_IDENTITY.md`

---

**Version**: 1.0.0-draft
**Status**: Design Draft
**Last Updated**: 2026-01-03

*"An LCT at any level is still an LCT - the terminology is sacred, the implementation is flexible."*
