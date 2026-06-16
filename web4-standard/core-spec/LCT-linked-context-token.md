# Linked Context Token (LCT) - Core Specification

**Status**: Core Specification v1.0.0
**Date**: June 15, 2026
**Category**: Identity & Context

## Abstract

The Linked Context Token (LCT) is Web4's foundational presence primitive. An LCT is a verifiable digital presence certificate that binds an entity to its context through witnessed relationships. Unlike traditional identity tokens that assert "who you are," LCTs establish "where you exist" - your position in the web of trust and context.

## Notation

Key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this document are to be interpreted as described in RFC 2119.

## 1. Introduction

### 1.1 Purpose

LCTs solve the fundamental problem of contextual presence in distributed systems:

- **Verifiable Presence**: Cryptographically bound presence anchored to hardware or cryptographic keys
- **Context Emergence**: Identity emerges from relationships, not central authority
- **Trust Propagation**: Trust flows through witnessed connections in the Markov Relevancy Horizon (MRH)
- **Birth Certificates**: Societies issue LCTs as foundational presence documents

### 1.2 Terminology

- **Entity**: Any participant in Web4 (human, AI, society, organization, role, task, resource, device, service, oracle, accumulator, dictionary, hybrid, policy, infrastructure — see `entity-types.md` §2.1 for the canonical 15-type taxonomy)
- **Binding**: Permanent, verifiable cryptographic link between entity and LCT
- **Pairing**: Authorized operational relationship between entities
- **Witnessing**: Trust-building observation by other entities
- **MRH (Markov Relevancy Horizon)**: Dynamic context boundary containing relevant entities
- **Birth Certificate**: LCT issued by a society as foundational presence
- **Society**: Governance context that issues and witnesses LCTs

## 2. LCT Structure

### 2.1 Required Components

Every LCT MUST contain:

1. **Identity** (`lct_id`, `subject`)
2. **Binding** (cryptographic anchor to entity)
3. **MRH** (Markov Relevancy Horizon with relationships)
4. **Policy** (capabilities and constraints)
5. **Trust Tensor (T3)** (3 root dimensions, fractally extensible via RDF sub-dimensions)
6. **Value Tensor (V3)** (3 root dimensions, fractally extensible via RDF sub-dimensions)

### 2.2 Optional Components

LCTs MAY contain:

1. **Birth Certificate** (society-issued foundational identity)
2. **Attestations** (witness observations)
3. **Lineage** (evolution history)
4. **Revocation** (termination record)

### 2.3 Canonical Structure

```json
{
  "@context": ["https://web4.io/contexts/lct.jsonld"],
  "@type": "web4:LinkedContextToken",
  "lct_id": "lct:web4:mb32:...",
  "subject": "did:web4:key:z6Mk...",

  "binding": {
    "entity_type": "human|ai|society|organization|role|task|resource|device|service|oracle|accumulator|dictionary|hybrid|policy|infrastructure",
    "public_key": "mb64:coseKey",
    "hardware_anchor": "eat:mb64:hw:...",
    "created_at": "2025-10-01T00:00:00Z",
    "binding_proof": "cose:Sig_structure"
  },

  "birth_certificate": {
    "issuing_society": "lct:web4:society:...",
    "citizen_role": "lct:web4:role:citizen:...",
    "birth_timestamp": "2025-10-01T00:00:00Z",
    "birth_witnesses": [
      "lct:web4:witness:1...",
      "lct:web4:witness:2...",
      "lct:web4:witness:3..."
    ],
    "genesis_block_hash": "0x...",
    "birth_context": "nation|platform|network|organization|ecosystem"
  },

  "mrh": {
    "bound": [
      {
        "lct_id": "lct:web4:hardware:...",
        "type": "parent|child|sibling",
        "binding_context": "hardware_sovereignty",
        "ts": "2025-10-01T00:00:00Z"
      }
    ],
    "paired": [
      {
        "lct_id": "lct:web4:role:citizen:...",
        "pairing_type": "birth_certificate",
        "permanent": true,
        "ts": "2025-10-01T00:00:00Z"
      }
    ],
    "witnessing": [
      {
        "lct_id": "lct:web4:witness:...",
        "role": "time|audit|oracle|existence|action|state|quality",
        "last_attestation": "2025-10-01T00:00:00Z",
        "witness_count": 42
      }
    ],
    "horizon_depth": 3,
    "last_updated": "2025-10-01T00:00:00Z"
  },

  "policy": {
    "capabilities": [
      "pairing:initiate",
      "metering:grant",
      "write:lct",
      "witness:attest"
    ],
    "constraints": {
      "region": ["us-west", "eu-central"],
      "max_rate": 5000,
      "requires_quorum": true
    }
  },

  "t3_tensor": {
    "talent": 0.85,
    "training": 0.92,
    "temperament": 0.78,
    "sub_dimensions": {
      "talent": {
        "analytical_reasoning": 0.90,
        "creative_problem_solving": 0.80
      }
    },
    "composite_score": 0.85,
    "last_computed": "2025-10-01T00:00:00Z",
    "computation_witnesses": ["lct:web4:oracle:trust:..."]
  },

  "v3_tensor": {
    "valuation": 0.89,
    "veracity": 0.91,
    "validity": 0.76,
    "sub_dimensions": {
      "veracity": {
        "claim_accuracy": 0.93,
        "reproducibility": 0.88
      }
    },
    "composite_score": 0.85,
    "last_computed": "2025-10-01T00:00:00Z",
    "computation_witnesses": ["lct:web4:oracle:value:..."]
  },

  "attestations": [
    {
      "witness": "did:web4:key:z6Mk...",
      "type": "existence",
      "claims": {
        "observed_at": "2025-10-01T00:00:00Z",
        "method": "blockchain_transaction"
      },
      "sig": "cose:ES256:...",
      "ts": "2025-10-01T00:00:00Z"
    }
  ],

  "lineage": [
    {
      "parent": "lct:web4:mb32:previous...",
      "reason": "genesis|rotation|fork|upgrade",
      "ts": "2025-09-01T00:00:00Z"
    }
  ],

  "revocation": {
    "status": "active",
    "ts": null,
    "reason": null
  }
}
```

## 3. LCT Creation Process

### 3.1 Genesis: Birth Certificate from Society

The primary way LCTs are created is through **birth certificate issuance** by a society:

```
1. Entity requests LCT from society
2. Society validates entity meets citizenship requirements
3. Society generates cryptographic binding:
   - Entity provides public key (or hardware anchor)
   - Society witnesses binding ceremony
   - Quorum of society witnesses attest
4. Society mints LCT with birth certificate:
   - Records issuing_society LCT
   - Assigns citizen_role
   - Records birth_witnesses (minimum 3)
   - Anchors to genesis_block_hash
5. Society initializes MRH:
   - Adds birth_witnesses to mrh.witnessing
   - Adds citizen_role to mrh.paired (permanent)
   - Adds hardware binding to mrh.bound
6. Society computes initial T3/V3 tensors
7. Society publishes LCT to registry
8. Birth witnesses attest to creation
```

**Result**: Entity now has verifiable presence within society's context.

### 3.2 Self-Issued LCT (Bootstrap)

In absence of existing society, entities MAY create self-issued LCTs:

```
1. Generate key pair (Ed25519 or P-256)
2. Create binding with hardware anchor (if available)
3. Self-sign binding_proof
4. Initialize empty MRH
5. Omit `birth_certificate` section (self-issued LCTs are Regular LCTs per §4.3)
6. Publish with low initial T3 scores
```

**Limitation**: Self-issued LCTs have low trust until witnessed by established societies.

### 3.3 Binding Algorithm

```python
def create_lct_binding(entity_type, private_key, hardware_anchor=None):
    """
    Create cryptographic binding for LCT.

    Returns: (lct_id, binding_object) — binding_proof is embedded inside binding_object
    per §2.3 canonical structure.
    """
    # 1. Create canonical binding structure (binding_proof added in step 3)
    binding = {
        "entity_type": entity_type,
        "public_key": multibase_encode(cose_key(private_key.public_key)),
        "hardware_anchor": hardware_anchor,  # Optional EAT token
        "created_at": utc_now()
    }

    # 2. Serialize with deterministic CBOR (proof input excludes binding_proof itself)
    binding_cbor = cbor_deterministic_encode(binding)

    # 3. Sign with entity's private key and EMBED proof in the binding object
    #    (matches §2.3 canonical structure where binding_proof is a FIELD of binding)
    binding["binding_proof"] = cose_sign1(private_key, binding_cbor)

    # 4. Generate LCT ID from binding proof hash
    lct_id = "lct:web4:" + multibase32_encode(sha256(binding["binding_proof"]))

    return lct_id, binding
```

## 4. Birth Certificate as Foundational Identity

### 4.1 Role in Society

The birth certificate establishes an entity's **citizenship** within a society:

- **First Witness**: Society is the first to witness entity's existence
- **Permanent Pairing**: Citizen role is permanently paired in MRH
- **Trust Bootstrap**: Society's trust transfers to new entity
- **Governance Rights**: Citizenship grants participation rights

### 4.2 Birth Certificate Requirements

For an LCT to serve as a birth certificate, it MUST:

1. **Contain `birth_certificate` section** with:
   - `issuing_society`: LCT of the society issuing the certificate
   - `citizen_role`: LCT of the role this entity inhabits
   - `birth_witnesses`: Array of ≥3 witness LCTs
   - `birth_timestamp`: ISO 8601 timestamp
   - `birth_context`: Society type classification — one of `nation`, `platform`, `network`, `organization`, `ecosystem` (RECOMMENDED)
   - `genesis_block_hash`: Blockchain anchor for temporal proof (RECOMMENDED; omit if no blockchain anchor is available)

2. **Have permanent citizen pairing** in `mrh.paired`:
   ```json
   {
     "lct_id": "lct:web4:role:citizen:...",
     "pairing_type": "birth_certificate",
     "permanent": true,
     "ts": "2025-10-01T00:00:00Z"
   }
   ```

3. **Be attested by birth witnesses** in `attestations`:
   - Each witness MUST sign existence attestation
   - Minimum quorum: 3 witnesses
   - Witnesses MUST be members of issuing society (enforcement is implementation-defined; the §11.2 reference validator checks quorum and per-witness attestation but does not currently verify society membership)

### 4.3 Birth Certificate vs. Regular LCT

| Property | Birth Certificate LCT | Regular LCT |
|----------|----------------------|-------------|
| Issuer | Society | Self or Society |
| Initial Trust | High (inherited) | Low (self-issued) |
| Citizenship | Yes | Optional |
| MRH Citizen Pairing | Permanent | N/A |
| Witness Quorum | Required (≥3) | Optional |
| Blockchain Anchor | Recommended | Optional |

## 5. Markov Relevancy Horizon (MRH)

### 5.1 Purpose

The MRH defines the **context boundary** for an entity - the set of all entities that are relevant to this LCT's operations, trust calculations, and interactions.

### 5.2 Relationship Types

#### 5.2.1 Binding Relationships (`mrh.bound`)
- **Purpose**: Permanent hierarchical attachments
- **Type**: `parent`, `child`, `sibling`
- **Example**: Device LCT bound to hardware anchor LCT
- **Trust Flow**: Bidirectional, strong

#### 5.2.2 Pairing Relationships (`mrh.paired`)
- **Purpose**: Authorized operational connections
- **Type**: `birth_certificate`, `role`, `operational`
- **Example**: Entity paired with citizen role
- **Trust Flow**: Bidirectional, context-specific
- **Permanence**: Birth certificate pairings are permanent

#### 5.2.3 Witnessing Relationships (`mrh.witnessing`)
- **Purpose**: Trust accumulation through observation
- **Roles**: `time`, `audit`, `oracle`, `existence`, `action`, `state`, `quality`
- **Example**: Time oracle witnessing entity's actions
- **Trust Flow**: Unidirectional (witness → witnessed)

### 5.3 MRH Updates

The MRH is **dynamic** and MUST be updated when:

1. **New Binding**: Adding permanent attachment
2. **New Pairing**: Establishing operational relationship
3. **Witness Event**: Being witnessed or witnessing another
4. **Relationship Revocation**: Removing non-permanent connection
5. **Trust Recomputation**: T3 tensor changes affect horizon

### 5.4 Horizon Depth

The `horizon_depth` parameter controls how many relationship hops to track:

- **Depth 1**: Direct relationships only (bound, paired, witnessing)
- **Depth 2**: Relationships of relationships
- **Depth 3**: Default, balances context vs. performance
- **Depth 4+**: Rare, for high-context entities

## 6. Trust and Value Tensors

### 6.1 Trust Tensor (T3) - REQUIRED

Every LCT MUST contain a `t3_tensor` with the three canonical root dimensions. Each root dimension is an aggregate score of an open-ended RDF sub-graph of contextualized sub-dimensions linked via `web4:subDimensionOf`. See the [T3/V3 Ontology](../ontology/t3v3-ontology.ttl) for formal definitions.

```json
{
  "t3_tensor": {
    "talent": 0.0-1.0,                    // Role-specific capability (root aggregate)
    "training": 0.0-1.0,                  // Role-specific expertise (root aggregate)
    "temperament": 0.0-1.0,               // Role-specific reliability (root aggregate)
    "sub_dimensions": {},                  // OPTIONAL: domain-specific refinements
    "composite_score": 0.0-1.0,           // Weighted average of roots
    "last_computed": "ISO 8601",
    "computation_witnesses": ["lct:..."]  // Who computed these scores?
  }
}
```

**Root dimensions**:
- **Talent**: Can this entity perform the task? (capability/aptitude)
- **Training**: Has it learned how? (knowledge/experience)
- **Temperament**: Will it behave appropriately? (disposition/reliability)

**Canonical weights**: the normative source for these constants is the protocol-invariant parameter table in [`t3-v3-tensors.md` §10.2](t3-v3-tensors.md) (which declares itself "the normative source for all protocol-invariant formulas, weights, and constants"). Implementations MUST compute `composite_score` as the weighted sum of the three root dimensions stated there:

```
composite_score = 0.4 · talent + 0.3 · training + 0.3 · temperament
```

Each root dimension is itself an aggregate over its (optional) RDF sub-graph of sub-dimensions; sub-dimension aggregation into roots is implementation-defined (typically arithmetic mean of leaves linked via `web4:subDimensionOf`). Computed composites are therefore in `[0.0, 1.0]` whenever roots are.

**Computation**: Societies or trust oracles compute T3 tensors based on:
- Historical behavior
- Witness attestations
- MRH relationship quality
- Time-weighted decay

### 6.2 Value Tensor (V3) - REQUIRED

Every LCT MUST contain a `v3_tensor` with the three canonical root dimensions, following the same fractal sub-dimension pattern as T3:

```json
{
  "v3_tensor": {
    "valuation": 0.0+,                    // Subjective worth (can exceed 1.0)
    "veracity": 0.0-1.0,                  // Truthfulness/accuracy (root aggregate)
    "validity": 0.0-1.0,                  // Soundness of reasoning (root aggregate)
    "sub_dimensions": {},                  // OPTIONAL: domain-specific refinements
    "composite_score": 0.0+,              // CAN exceed 1.0 when valuation does (see note)
    "last_computed": "ISO 8601",
    "computation_witnesses": ["lct:..."]
  }
}
```

**Root dimensions**:
- **Valuation**: How is value assessed? (subjective worth)
- **Veracity**: How truthful are claims? (accuracy/reproducibility)
- **Validity**: How sound is the reasoning? (confirmed value delivery)

**Canonical weights**: as with T3, the normative source for these constants is the protocol-invariant parameter table in [`t3-v3-tensors.md` §10.2](t3-v3-tensors.md). Implementations MUST compute `composite_score` as the weighted sum of the three root dimensions stated there:

```
composite_score = 0.3 · valuation + 0.35 · veracity + 0.35 · validity
```

Sub-dimension aggregation into roots mirrors the T3 pattern (implementation-defined; typically arithmetic mean of leaves linked via `web4:subDimensionOf`). Because `valuation` is permitted to exceed `1.0` (see comment above), the composite arithmetic CAN exceed `1.0` in pathological cases; behavior under that condition (clamp at `1.0`, rescale, or extend the composite range) is currently underspecified and tracked as a known design question.

**Computation**: Societies or value oracles compute V3 tensors based on:
- Energy economics (ATP/ADP)
- Contribution metrics
- Resource management
- Network impact

### 6.3 Tensor Recomputation

T3 and V3 tensors SHOULD be recomputed:
- **On demand**: When trust/value query is made
- **Periodically**: Daily or after significant events
- **After attestation**: When new witness attests
- **After transaction**: When ATP/ADP balance changes

## 7. LCT Lifecycle

### 7.1 Creation (Genesis)

```
Entity → Society: Request LCT
Society → Entity: Validate requirements
Society → Witnesses: Convene quorum
Witnesses → Society: Attest to binding
Society → Blockchain: Mint LCT
Society → Entity: Issue birth certificate
```

### 7.2 Operation (Active)

```
Entity uses LCT for:
- Pairing with other entities
- Requesting capabilities
- Accumulating witness attestations
- Participating in society governance
- Energy transactions (ATP/ADP)
```

### 7.3 Rotation (Key Update)

```
Entity → Society: Request rotation
Society: Create new LCT
  - New binding with new keys
  - Same subject DID
  - Lineage points to parent LCT
Society: Overlap window (24-48 hours)
  - Both LCTs valid (new LCT status = "active"; parent stays "active" until retired)
  - Relationships migrate to new LCT
Society: Retire parent LCT
  - Mark as "superseded"
  - Update lineage in new LCT
```

### 7.4 Revocation (Termination)

```
Authority → LCT: Revoke
Reasons:
  - compromise: Keys compromised
  - superseded: Rotated to new LCT
  - expired: Time-bounded LCT ended
  - violation: Policy violation

Effect:
  - status = "revoked"
  - All capabilities disabled
  - MRH relationships preserved (read-only)
  - Lineage continues (for successor)
```

## 8. Security Properties

### 8.1 Unforgeability

LCTs resist forgery because:
- **Cryptographic binding**: Requires private key signature
- **Hardware anchors**: Optional TPM/secure element attestation
- **Witness quorum**: Birth requires a quorum (≥3) of witnesses (witness distinctness / anti-collusion is not asserted by this property alone — birth witnesses are members of the issuing society per §4.2)
- **Blockchain anchor**: Genesis block hash creates temporal proof (when present; `genesis_block_hash` is RECOMMENDED, not required — see §4.2)

### 8.2 Context Integrity

LCTs maintain context integrity through:
- **MRH boundaries**: Explicit relevancy limits
- **Relationship types**: Binding vs. pairing vs. witnessing
- **Trust propagation**: T3 flows only through verified relationships
- **Horizon depth**: Limits transitive trust distance

### 8.3 Privacy Preservation

LCTs protect privacy through:
- **Minimal disclosure**: Only expose necessary capabilities
- **Pseudonymous DIDs**: Subject can be key-based DID
- **Selective attestation**: Non-birth attestations may share only relevant witnesses (birth certificates require the full `birth_witnesses` set per §11.2, so selective disclosure does not apply to them)
- **MRH pruning**: Old relationships can be archived

## 9. Implementation Requirements

### 9.1 Societies MUST

- Implement birth certificate issuance with witness quorum
- Maintain LCT registry (on-chain or distributed)
- Compute T3/V3 tensors or delegate to oracles
- Enforce policy constraints
- Support LCT rotation with overlap windows

### 9.2 Entities MUST

- Securely store private keys for binding
- Update MRH when relationships change
- Request tensor recomputation after significant events
- Honor revocation status
- Implement witness attestation protocols

### 9.3 Witnesses MUST

- Sign attestations only for observed events
- Never attest to future timestamps (verification is implementation-defined — the protocol mandates no reference clock, skew tolerance, or error path; treat as an advisory honesty constraint on witnesses)
- Maintain witness reputation (their own T3)
- Participate in quorum requirements
- Revoke compromised attestations

## 10. Relationship to Other Web4 Components

### 10.1 LCT and R6 Framework

LCTs enable R6 actions (Rules + Role + Request + Reference + Resource → Result):
- **Role**: Defined by citizen_role in birth certificate
- **Capabilities**: Listed in policy section
- **Authority**: Derived from T3 tensor
- **Metering**: Tracked via V3 tensor and ATP/ADP

### 10.2 LCT and SAL (Society-Authority-Law)

LCTs are governed by SAL:
- **Society**: Issues birth certificate
- **Authority**: Society's governance structure
- **Law**: Policy constraints and norms

### 10.3 LCT and ATP/ADP

LCTs track energy economics:
- **V3 tensor**: ATP/ADP balance MAY be tracked via a context-specific `energy_balance` sub-dimension (see `lct-capability-levels.md`)
- **Transactions**: Recorded in society's energy cycle ledger
- **Metering**: Capabilities consume ATP

### 10.4 LCT and Dictionary Entities

Dictionaries are entities with special LCTs:
- **Entity type**: `dictionary`
- **Purpose**: Maintain semantic domains
- **Trust**: High T3 for terminology consistency
- **Witnessing**: Cross-domain translation events

## 11. Compliance and Validation

### 11.1 LCT Validator

Implementations MUST provide validation for:

```python
def validate_lct(lct):
    """Validate LCT structure and semantics."""
    assert lct["lct_id"].startswith("lct:web4:")
    assert lct["subject"].startswith("did:web4:")
    assert "binding" in lct
    assert "mrh" in lct
    assert "policy" in lct
    assert "t3_tensor" in lct
    assert "v3_tensor" in lct

    # Birth certificate validation
    if "birth_certificate" in lct:
        assert len(lct["birth_certificate"]["birth_witnesses"]) >= 3
        assert any(
            p["pairing_type"] == "birth_certificate" and p["permanent"]
            for p in lct["mrh"]["paired"]
        )

    # Tensor validation (implementation-defined helpers — see expected semantics below)
    validate_t3_tensor(lct["t3_tensor"])   # implementation-defined
    validate_v3_tensor(lct["v3_tensor"])   # implementation-defined

    # Binding proof verification (implementation-defined — see expected semantics below)
    verify_binding_proof(lct["binding"], lct["binding"]["binding_proof"])   # implementation-defined

    return True
```

**Implementation-defined helpers** (expected semantics for the three calls above):

- `validate_t3_tensor(t3)`: MUST check that `talent`, `training`, `temperament` are present and each in `[0.0, 1.0]`; that `composite_score` is in `[0.0, 1.0]` and matches the §6.1 canonical weight formula within a documented tolerance (e.g. ±0.01 for rounding); and that any `sub_dimensions` entries are valid `web4:subDimensionOf` RDF sub-graphs of the corresponding root.
- `validate_v3_tensor(v3)`: MUST check that `valuation` ≥ `0.0` (per §6.2 it MAY exceed `1.0`); that `veracity` and `validity` are each in `[0.0, 1.0]`; that `composite_score` matches the §6.2 canonical weight formula within tolerance; and (as above) that any sub-dimensions are valid RDF sub-graphs.
- `verify_binding_proof(binding, binding_proof)`: MUST verify that `binding_proof` is a valid COSE_Sign1 signature over the deterministic CBOR encoding of `binding` (with `binding_proof` itself excluded from the signed input) using the public key in `binding.public_key`, per the §3.3 binding algorithm.

### 11.2 Birth Certificate Validator

```python
def validate_birth_certificate(lct):
    """Validate birth certificate requirements."""
    assert "birth_certificate" in lct
    bc = lct["birth_certificate"]

    # Required fields
    assert "issuing_society" in bc
    assert "citizen_role" in bc
    assert "birth_timestamp" in bc
    assert "birth_witnesses" in bc

    # Witness quorum
    assert len(bc["birth_witnesses"]) >= 3

    # Permanent citizen pairing
    citizen_pairing = [
        p for p in lct["mrh"]["paired"]
        if p["pairing_type"] == "birth_certificate"
    ]
    assert len(citizen_pairing) == 1
    assert citizen_pairing[0]["permanent"] == True

    # Witness attestations
    for witness in bc["birth_witnesses"]:
        assert witness_attested(lct, witness)   # implementation-defined

    return True
```

**Implementation-defined helper** (expected semantics for the call above, mirroring the §11.1 trio):

- `witness_attested(lct, witness)`: MUST verify that the LCT carries an existence attestation from `witness` for this birth — i.e. an entry in `lct["attestations"]` whose witness LCT equals `witness`, whose `type` covers the birth/existence claim, and (at the verifying party's assurance level) whose signature is a valid COSE_Sign1 over the attested claims using that witness's bound public key. A present-only check (entry exists) is the minimum; a COSE-verified check is RECOMMENDED. The collection consulted is the LCT's `attestations` array (§2.3); implementations MAY additionally consult an out-of-band witness registry.

## 12. Future Extensions

### 12.1 Planned Features

- **Multi-society citizenship**: Entity holds birth certificates from multiple societies
- **Delegation chains**: LCTs can delegate capabilities to child LCTs
- **Emergency recovery**: Social recovery for compromised LCTs
- **Cross-chain portability**: LCT migration between blockchains
- **Quantum-resistant bindings**: Post-quantum signature algorithms

### 12.2 Research Directions

- **Tensor compression**: Efficient T3/V3 representation
- **MRH optimization**: Graph compression for large horizons
- **Trust prediction**: ML models for T3 forecasting
- **Privacy-preserving tensors**: ZKP for selective tensor disclosure

## 13. References

- **Web4 Core Protocol**: `core-spec/core-protocol.md`
- **MRH Specification**: `core-spec/mrh-tensors.md`
- **T3/V3 Tensors**: `core-spec/t3-v3-tensors.md`
- **R6 Framework**: `core-spec/r6-framework.md`
- **SAL Specification**: `core-spec/web4-society-authority-law.md`
- **ATP/ADP Cycle**: `core-spec/atp-adp-cycle.md`
- **Entity Types**: `core-spec/entity-types.md`
- **LCT Capability Levels**: `core-spec/lct-capability-levels.md`
- **LCT Protocol Details**: `protocols/web4-lct.md`

---

**Version**: 1.0.0
**Status**: Core Specification
**Last Updated**: June 15, 2026

*"An LCT is not an identity. It is a presence - witnessed, contextualized, and witness-hardened."*
