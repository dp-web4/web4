# Web4 Witness Specification

This document defines the unified witness framework for Web4, normalizing witness classes, headers, and attestation formats across all protocols.

## 1. Witness Role

Witnesses strengthen entity validity through observation and attestation. They provide:
- **Temporal proof**: Timestamps and liveness
- **Audit trails**: Compliance and policy validation
- **External validation**: Oracle data and measurements
- **Trust accumulation**: Reputation through accumulated observations

## 2. Witness Classes

Web4 defines the following witness classes:

| Class | Purpose | Required Claims | Used In |
|-------|---------|-----------------|---------|
| `time` | Timestamp proof | `ts`, `nonce` | LCT, Metering |
| `audit` | Compliance validation | `policy_met`, `evidence` | LCT, Metering |
| `audit-minimal` | Lightweight audit | `digest_valid`, `rate_ok` | Metering |
| `oracle` | External data | `source`, `data`, `ts` | LCT, Metering |
| `existence` | Liveness proof | `observed_at`, `method` | LCT |
| `action` | Operation witness | `action_type`, `result` | LCT |
| `state` | Status attestation | `state`, `measurement` | LCT |
| `quality` | Performance metric | `metric`, `value` | LCT |

## 3. Attestation Format

### 3.1 Canonical Structure

All witness attestations MUST follow this structure:

```json
{
  "witness": "did:web4:key:z6Mk...",
  "type": "time|audit|oracle|existence|action|state|quality",
  "claims": {
    // Type-specific claims
  },
  "sig": "cose:..." or "jose:...",
  "ts": "2025-01-11T15:00:00Z",
  "nonce": "mb32:..."
}
```

### 3.2 Protected Headers

The following headers MUST be included in the signature's protected headers:

#### COSE/CBOR (MUST)
```cbor-diag
{
  1: -8,              // alg: EdDSA
  4: h'...',          // kid: witness key ID
  "witness_type": "time",
  "witness_did": "did:web4:key:...",
  "ts": 1736611200    // Unix timestamp
}
```

#### JOSE/JSON (SHOULD)
```json
{
  "alg": "ES256",
  "kid": "did:web4:key:z6Mk...#key-1",
  "witness_type": "time",
  "witness_did": "did:web4:key:...",
  "ts": "2025-01-11T15:00:00Z"
}
```

## 4. Witness-Specific Requirements

### 4.1 Time Witness

**Purpose**: Provide trusted timestamps

**Required Claims**:
- `ts`: ISO 8601 timestamp
- `nonce`: Random value from requester
- `accuracy`: Clock accuracy in milliseconds (OPTIONAL)

**Validation**:
- Timestamp MUST be within ±300s of current time
- Nonce MUST match request

### 4.2 Audit Witness

**Purpose**: Validate policy compliance

**Required Claims**:
- `policy_met`: Boolean indicating compliance
- `evidence`: Multibase-encoded audit evidence
- `policy_id`: Reference to policy being validated

**Validation**:
- Evidence MUST be verifiable
- Policy ID MUST be recognized

### 4.3 Audit-Minimal Witness

**Purpose**: Lightweight validation for high-volume operations

**Required Claims**:
- `digest_valid`: Boolean for Merkle tree validation
- `rate_ok`: Boolean for rate limit compliance
- `window_checked`: Time window validated

**Validation**:
- Used only for metering protocols
- MAY skip raw data validation

### 4.4 Oracle Witness

**Purpose**: Provide external data attestation

**Required Claims**:
- `source`: URI or identifier of data source
- `data`: The attested data
- `ts`: Observation timestamp
- `method`: How data was obtained (OPTIONAL)

**Validation**:
- Source MUST be verifiable
- Data format MUST match expected schema

### 4.5 Existence Witness

**Purpose**: Prove entity liveness

**Required Claims**:
- `observed_at`: Timestamp of observation
- `method`: How existence was verified
- `challenge`: Challenge-response value (if applicable)

**Validation**:
- Method MUST be recognized
- Challenge MUST match if challenge-response used

### 4.6 Action Witness

**Purpose**: Attest to performed operations

**Required Claims**:
- `action_type`: Type of action witnessed
- `result`: Outcome of action
- `actor`: DID of actor (OPTIONAL)

**Validation**:
- Action type MUST be from registry
- Result MUST match expected format

### 4.7 State Witness

**Purpose**: Attest to entity state

**Required Claims**:
- `state`: Current state value
- `measurement`: How state was measured
- `previous_state`: Prior state (OPTIONAL)

**Validation**:
- State transitions MUST be valid
- Measurement method MUST be recognized

### 4.8 Quality Witness

**Purpose**: Attest to performance metrics

**Required Claims**:
- `metric`: Metric name
- `value`: Measured value
- `unit`: Measurement unit
- `period`: Measurement period (OPTIONAL)

**Validation**:
- Metric MUST be from registry
- Value MUST be within expected range

## 5. Witness Selection

### 5.1 Witness Discovery

Entities discover witnesses through:
- **Bootstrap list**: Known trusted witnesses
- **Witness registry**: On-chain or distributed registry
- **Peer recommendation**: Witnesses recommended by peers
- **Broadcast discovery**: Witnesses announcing availability

### 5.2 Witness Quorum

For critical operations, multiple witnesses SHOULD be used:
- **Minimum quorum**: 2 of 3 witnesses
- **Byzantine tolerance**: (n-1)/3 malicious witnesses
- **Diversity requirement**: Witnesses from different operators

## 6. Witness Incentives

### 6.1 Metering Integration

Witnesses earn ATP credits for:
- Valid attestations: 1 ATP per attestation
- Audit services: 10 ATP per audit
- Oracle services: Variable based on data value

### 6.2 Reputation

Witness reputation tracked through:
- **Accuracy score**: Correctness of attestations
- **Availability score**: Uptime and responsiveness
- **Diversity score**: Range of attestation types

## 7. Security Considerations

### 7.1 Witness Compromise

- Witnesses MUST NOT be single points of failure
- Quorum requirements prevent single witness attacks
- Witness rotation SHOULD occur periodically

### 7.2 Time Synchronization

- Time witnesses MUST maintain NTP synchronization
- Clock drift MUST NOT exceed ±1 second
- Leap second handling MUST follow RFC 8633

### 7.3 Privacy

- Witnesses MUST NOT log unnecessary entity data
- Attestations SHOULD use minimal disclosure
- Witness-entity relationships SHOULD use pairwise identifiers

## 8. Implementation Notes

### 8.1 Signature Verification

```python
def verify_witness_attestation(attestation):
    # 1. Extract witness DID
    witness_did = attestation["witness"]
    
    # 2. Resolve witness public key
    witness_key = resolve_did(witness_did)
    
    # 3. Verify signature based on format
    if attestation["sig"].startswith("cose:"):
        return verify_cose(attestation, witness_key)
    elif attestation["sig"].startswith("jose:"):
        return verify_jose(attestation, witness_key)
    
    # 4. Validate claims for witness type
    return validate_claims(attestation["type"], attestation["claims"])
```

### 8.2 Attestation Request

```json
{
  "type": "WitnessRequest",
  "requester": "did:web4:key:z6Mk...",
  "witness_type": "time",
  "target": "lct:web4:mb32...",
  "nonce": "mb32:...",
  "claims_requested": ["ts", "accuracy"]
}
```

## 9. IANA Considerations

This specification creates the following registries:
- Web4 Witness Types
- Web4 Witness Claims
- Web4 Witness Methods