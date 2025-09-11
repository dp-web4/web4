# Web4 Lineage and Capability Token (LCT) Specification

This document provides the formal specification for the Lineage and Capability Token (LCT), a core data structure in Web4 that represents a digital entity's identity, capabilities, and history.

## 1. LCT Object Definition

The canonical LCT object MUST be represented as follows:

```json
{
  "lct_id": "lct:web4:mb32...",
  "subject": "did:web4:key:z6Mk...",
  "binding": {
    "entity_type": "device|service|user|oracle",
    "public_key": "mb64:coseKey",
    "hardware_anchor": "eat:mb64",         // optional EAT attestation
    "created_at": "2025-09-11T15:00:00Z",
    "binding_proof": "cose:Sig_structure"   // COSE Sig over canonical LCT fields
  },
  "policy": {
    "capabilities": ["pairing:initiate","metering:grant","write:lct"],
    "constraints": {"region":["us-west"], "max_rate": 5000}
  },
  "attestations": [
    {"witness":"did:web4:...","type":"time","sig":"cose:...","ts":"..."}
  ],
  "lineage": [{"parent":"lct:web4:...","reason":"rotate","ts":"..."}],
  "revocation": {"status":"active|revoked","ts":"...", "reason":"compromise|superseded"}
}
```

## 2. Field Definitions

### 2.1 Identity Fields

- **lct_id** (REQUIRED): Globally unique identifier in the format `lct:web4:<multibase-encoded-hash>`
- **subject** (REQUIRED): The DID of the entity this LCT represents, format `did:web4:<method-specific-id>`

### 2.2 Binding Fields

The binding establishes the permanent, unforgeable link between the LCT and its entity:

- **entity_type** (REQUIRED): One of `"device"`, `"service"`, `"user"`, or `"oracle"`
- **public_key** (REQUIRED): The entity's public key in COSE key format, multibase-encoded
- **hardware_anchor** (OPTIONAL): Entity Attestation Token (EAT) per RFC 9334 for hardware-backed identity
- **created_at** (REQUIRED): ISO 8601 timestamp of binding creation
- **binding_proof** (REQUIRED): COSE signature over the canonical binding fields

### 2.3 Policy Fields

- **capabilities** (REQUIRED): Array of capability strings the entity is authorized for
- **constraints** (OPTIONAL): Object containing operational constraints

### 2.4 Attestation Fields

Each attestation represents a witnessing event:

- **witness** (REQUIRED): DID of the witnessing entity
- **type** (REQUIRED): One of `"time"`, `"audit"`, `"oracle"`, `"existence"`, `"action"`, `"state"`, `"quality"`
- **sig** (REQUIRED): COSE signature from the witness
- **ts** (REQUIRED): ISO 8601 timestamp of witnessing

### 2.5 Lineage Fields

Tracks the evolution of the LCT:

- **parent** (OPTIONAL): Previous LCT ID if this is a successor
- **reason** (REQUIRED): One of `"genesis"`, `"rotation"`, `"fork"`, `"upgrade"`
- **ts** (REQUIRED): ISO 8601 timestamp of transition

### 2.6 Revocation Fields

When present, indicates the LCT is no longer active:

- **status** (REQUIRED): Either `"active"` or `"revoked"`
- **ts** (REQUIRED): ISO 8601 timestamp of status change
- **reason** (OPTIONAL): One of `"compromise"`, `"superseded"`, `"expired"`

## 3. Binding Algorithm

To create a binding between an entity and an LCT:

```
1. Generate or retrieve entity key pair (Ed25519 or P-256)
2. Create canonical binding object:
   binding = {
     entity_type: <type>,
     public_key: <multibase(COSE_Key)>,
     hardware_anchor: <optional_EAT>,
     created_at: <current_timestamp>
   }
3. Serialize binding using deterministic CBOR
4. Sign with entity's private key: binding_proof = Sign(sk, CBOR(binding))
5. Generate LCT ID: lct_id = "lct:web4:" + MB32(SHA256(binding_proof))
6. Construct complete LCT object
7. Submit to witness for attestation
```

## 4. Rotation Rules

LCT rotation allows key updates while maintaining identity continuity:

### 4.1 Rotation Procedure

1. **Create new LCT** with updated keys
2. **Set lineage** pointing to parent LCT
3. **Overlap window**: Both LCTs valid for 24 hours
4. **Grace period end**: Only new LCT accepted
5. **Archive parent**: Mark as superseded

### 4.2 Split-Brain Resolution

If multiple successors claim the same parent:

1. **Witness quorum**: Accept LCT with most witness attestations
2. **Timestamp priority**: Earlier rotation wins if witness count equal
3. **Explicit revocation**: Parent can designate preferred successor

## 5. Witness Attestation

Witnesses strengthen LCT validity through observation:

### 5.1 Witness Classes

| Class | Purpose | Required Claims |
|-------|---------|-----------------|
| time | Timestamp proof | `ts`, `nonce` |
| audit | Compliance check | `policy_met`, `evidence` |
| oracle | External validation | `source`, `data` |
| existence | Liveness proof | `observed_at`, `method` |
| action | Operation witness | `action_type`, `result` |
| state | Status attestation | `state`, `measurement` |
| quality | Performance metric | `metric`, `value` |

### 5.2 Attestation Format

```json
{
  "witness": "did:web4:key:z6Mk...",
  "type": "audit",
  "claims": {
    "policy_met": true,
    "evidence": "mb64:..."
  },
  "sig": "cose:ES256:...",
  "ts": "2025-09-11T15:00:00Z"
}
```

## 6. Security Considerations

### 6.1 Binding Security

- Private keys MUST never be included in LCT
- Hardware anchors SHOULD use secure elements when available
- Binding proofs MUST use approved signature algorithms

### 6.2 Rotation Security

- Overlap windows MUST NOT exceed 48 hours
- Parent LCT MUST NOT be reactivated after rotation
- Split-brain scenarios MUST be resolved within 72 hours

### 6.3 Witness Security

- Witnesses MUST NOT sign attestations for future timestamps
- Witness signatures MUST be verifiable against witness LCT
- Compromised witnesses SHOULD be excluded from quorum calculations

## 7. Privacy Considerations

- LCT IDs SHOULD NOT contain personally identifiable information
- Attestation history MAY be pruned after relevance window
- Capabilities SHOULD use least-privilege principle

## 8. IANA Considerations

This specification requests registration of:

- LCT URI scheme: `lct:web4:`
- Entity types registry
- Witness type registry
- Revocation reason codes