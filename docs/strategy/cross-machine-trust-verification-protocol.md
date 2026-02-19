# Cross-Machine Trust Verification Protocol (CMTVP)

**Status**: DRAFT
**Date**: 2026-02-19
**Context**: Bridges hardware-bound entities across heterogeneous machines
**Prerequisite**: TPM2 validation (DONE), AVP protocol (DONE)

---

## 1. Problem Statement

Web4 entities can prove hardware-bound identity on a single machine via the Aliveness Verification Protocol (AVP). But Web4's vision requires entities on **different machines** to verify each other:

- Legion (Intel TPM 2.0, x86_64) ↔ Thor (ARM TrustZone, aarch64)
- Different hardware security modules produce different attestation formats
- No shared trust anchor between machines (each TPM/TrustZone is independent)
- Network adds latency, replay, and relay attack surfaces

**Goal**: Enable mutual trust verification between hardware-bound entities on different machines, producing a verifiable **trust bridge** that both sides can reference.

---

## 2. Design Principles

1. **AVP is the primitive** — Cross-machine verification is mutual AVP, not a new protocol
2. **Heterogeneous hardware is normal** — TPM2 and TrustZone are equally valid Level 5 anchors
3. **Witnesses make it real** — Pairing without witnesses is self-attestation (low trust)
4. **Trust bridges are entities** — The relationship itself gets an LCT
5. **Offline-first** — Protocol must work with store-and-forward, not just real-time

---

## 3. Protocol Overview

### 3.1 Three Phases

```
Phase 1: DISCOVERY    — Entities learn about each other's LCTs
Phase 2: PAIRING      — Mutual AVP + attestation exchange
Phase 3: BRIDGING     — Trust bridge LCT created, witnessed, operational
```

### 3.2 Trust Levels

| Phase | Trust Level | What's Proven |
|-------|-------------|---------------|
| Discovery | 0.0 | Nothing — just awareness |
| Pairing (unwitnessed) | 0.3 | Mutual signature verification |
| Pairing (witnessed) | 0.6 | Third-party attestation of pairing ceremony |
| Bridging (active) | 0.8 | Ongoing mutual AVP with attestation |
| Bridging (established) | 0.95 | Accumulated witness history + consistent PCRs |

---

## 4. Phase 1: Discovery

### 4.1 LCT Exchange Format

Entities discover each other by exchanging **LCT Discovery Records**:

```json
{
  "protocol": "web4-cmtvp-v1",
  "phase": "discovery",
  "lct_id": "lct:web4:ai:abc123...",
  "entity_type": "ai",
  "binding": {
    "hardware_type": "tpm2",
    "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...",
    "hardware_anchor": "eat:mb64:hw:...",
    "trust_ceiling": 1.0,
    "capability_level": 5
  },
  "attestation_format": "tpm2_quote",
  "supported_algorithms": ["ECDSA-SHA256", "ECDSA-SHA384"],
  "machine_fingerprint": "sha256:...",
  "timestamp": "2026-02-19T10:00:00Z",
  "signature": "base64:..."
}
```

### 4.2 Discovery Channels

Discovery records can be exchanged via:

1. **Direct transfer** — USB, local network, QR code (highest trust for initial pairing)
2. **Society registry** — Published in a society's LCT registry (trust depends on society)
3. **Ledger broadcast** — Published on-chain (verifiable timestamp, public)
4. **MCP relay** — Via Model Context Protocol channel (entity-to-entity)

### 4.3 Discovery Validation

Receiving entity MUST validate:

- [ ] `lct_id` format is valid (`lct:web4:{type}:{hash}`)
- [ ] `public_key_pem` parses as valid ECC key
- [ ] `signature` verifies against `public_key_pem` over the record (minus signature)
- [ ] `attestation_format` is supported (currently: `tpm2_quote`, `trustzone_token`, `software_sig`)
- [ ] `timestamp` is within acceptable drift (±5 minutes for real-time, any for async)

---

## 5. Phase 2: Pairing (Mutual AVP)

### 5.1 Mutual Challenge-Response

Both entities simultaneously challenge each other. This is two AVP flows crossing:

```
Legion                              Thor
  │                                   │
  │──── Challenge_L→T ────────────────│
  │                                   │
  │────────────────── Challenge_T→L ──│
  │                                   │
  │   (both sign canonical payloads)  │
  │                                   │
  │──── Proof_L (TPM2 signed) ───────│
  │                                   │
  │────────── Proof_T (TZ signed) ───│
  │                                   │
  │   (both verify with LCT pubkeys) │
  │                                   │
  │──── Attestation_L (TPM quote) ───│
  │                                   │
  │──────── Attestation_T (PSA) ─────│
  │                                   │
  ▼                                   ▼
VERIFIED                          VERIFIED
```

### 5.2 Challenge Construction

Each challenge includes a **pairing context** that binds both parties:

```python
def create_pairing_challenge(
    my_lct_id: str,
    their_lct_id: str,
    purpose: str = "cross-machine-pairing"
) -> AlivenessChallenge:
    """Create AVP challenge with cross-machine pairing context."""
    # Compute intended action hash from both LCT IDs
    pairing_hash = hashlib.sha256(
        f"{my_lct_id}:{their_lct_id}:pairing".encode()
    ).hexdigest()

    return AlivenessChallenge.create(
        verifier_lct_id=my_lct_id,
        purpose=purpose,
        intended_action_hash=pairing_hash,
        ttl_seconds=300  # 5 minutes for cross-machine
    )
```

### 5.3 Cross-Hardware Attestation Comparison

Different hardware produces different attestation formats. The protocol normalizes them:

```
┌─────────────────────────┐    ┌─────────────────────────┐
│   TPM2 Attestation      │    │  TrustZone Attestation  │
│                         │    │                         │
│  Format: TPM2_Quote     │    │  Format: PSA_Token      │
│  PCRs: 0-7, 11         │    │  Claims: boot_seed,     │
│  Algorithm: SHA-256     │    │    sw_components,        │
│  Nonce: included        │    │    implementation_id     │
│  Signature: ECDSA       │    │  Nonce: included        │
│                         │    │  Signature: ECDSA       │
└────────┬────────────────┘    └────────┬────────────────┘
         │                              │
         └──────────┬───────────────────┘
                    │
         ┌──────────▼───────────────────┐
         │  Normalized Attestation       │
         │                               │
         │  boot_integrity: bool         │
         │  key_non_extractable: bool    │
         │  hardware_type: str           │
         │  trust_ceiling: float         │
         │  freshness_nonce: bytes       │
         │  raw_attestation: bytes       │
         └───────────────────────────────┘
```

### 5.4 Normalized Attestation Record

```json
{
  "attestation_type": "normalized_v1",
  "source_format": "tpm2_quote",
  "claims": {
    "boot_integrity": true,
    "key_non_extractable": true,
    "hardware_type": "tpm2",
    "hardware_vendor": "INTC",
    "trust_ceiling": 1.0,
    "freshness_nonce": "hex:...",
    "measurement_time": "2026-02-19T10:01:00Z"
  },
  "raw": {
    "format": "tpm2_quote",
    "pcr_values": {
      "0": "sha256:...",
      "4": "sha256:...",
      "7": "sha256:..."
    },
    "quote_signature": "base64:..."
  }
}
```

### 5.5 Pairing Result

After successful mutual AVP + attestation exchange:

```json
{
  "pairing_id": "pair:web4:abc123:def456",
  "status": "verified",
  "initiator": {
    "lct_id": "lct:web4:ai:abc123",
    "hardware_type": "tpm2",
    "attestation_verified": true,
    "avp_result": {
      "valid": true,
      "continuity_score": 1.0,
      "content_score": 1.0
    }
  },
  "responder": {
    "lct_id": "lct:web4:ai:def456",
    "hardware_type": "trustzone",
    "attestation_verified": true,
    "avp_result": {
      "valid": true,
      "continuity_score": 1.0,
      "content_score": 1.0
    }
  },
  "pairing_timestamp": "2026-02-19T10:01:30Z",
  "witnesses": [],
  "trust_level": 0.3
}
```

Note: trust_level = 0.3 because unwitnessed. Witnesses elevate it.

---

## 6. Phase 3: Trust Bridge

### 6.1 Trust Bridge as Entity

A trust bridge is itself a Web4 entity (type: INFRASTRUCTURE) with its own LCT:

```json
{
  "lct_id": "lct:web4:infrastructure:bridge:...",
  "entity_type": "infrastructure",
  "name": "legion-thor-bridge",
  "binding": {
    "bridge_type": "cross_machine",
    "endpoints": [
      {"lct_id": "lct:web4:ai:abc123", "machine": "legion", "hardware": "tpm2"},
      {"lct_id": "lct:web4:ai:def456", "machine": "thor", "hardware": "trustzone"}
    ],
    "created_from_pairing": "pair:web4:abc123:def456"
  },
  "t3_tensor": {
    "talent": 0.5,
    "training": 0.3,
    "temperament": 0.5
  },
  "health": {
    "last_mutual_avp": "2026-02-19T10:01:30Z",
    "avp_interval_seconds": 3600,
    "consecutive_successes": 0,
    "consecutive_failures": 0,
    "state": "new"
  }
}
```

### 6.2 Trust Bridge States

```
NEW ──(first mutual AVP)──→ ACTIVE
                              │
                    (AVP success) ──→ ESTABLISHED (after N consecutive)
                              │
                    (AVP failure) ──→ DEGRADED
                                        │
                              (recovery) ──→ ACTIVE
                              (N failures) ──→ BROKEN
                                                │
                                      (manual repair) ──→ NEW
```

### 6.3 Trust Bridge Heartbeat

The bridge maintains health through periodic mutual AVP:

```python
class TrustBridgeHeartbeat:
    """Periodic mutual AVP to maintain trust bridge health."""

    def __init__(self, bridge_lct_id: str, interval_seconds: int = 3600):
        self.bridge_lct_id = bridge_lct_id
        self.interval = interval_seconds
        self.consecutive_successes = 0
        self.consecutive_failures = 0

    def check(self, local_provider, remote_lct, remote_public_key) -> bool:
        """Run mutual AVP heartbeat."""
        # 1. Create challenge for remote
        challenge = create_pairing_challenge(
            my_lct_id=local_provider.lct_id,
            their_lct_id=remote_lct.lct_id,
            purpose="bridge-heartbeat"
        )

        # 2. Send challenge, receive proof
        # (transport layer handles serialization/network)
        proof = transport.send_challenge(remote_lct.endpoint, challenge)

        # 3. Verify proof
        result = local_provider.verify_aliveness_proof(
            challenge, proof, remote_public_key
        )

        if result.valid:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0

        return result.valid

    @property
    def bridge_state(self) -> str:
        if self.consecutive_failures >= 5:
            return "BROKEN"
        elif self.consecutive_failures > 0:
            return "DEGRADED"
        elif self.consecutive_successes >= 10:
            return "ESTABLISHED"
        elif self.consecutive_successes > 0:
            return "ACTIVE"
        else:
            return "NEW"

    @property
    def trust_multiplier(self) -> float:
        """Trust multiplier based on bridge health."""
        return {
            "BROKEN": 0.0,
            "DEGRADED": 0.3,
            "NEW": 0.5,
            "ACTIVE": 0.8,
            "ESTABLISHED": 0.95
        }[self.bridge_state]
```

### 6.4 Trust Ceiling Interaction

When two entities with different hardware verify each other, the trust ceiling is the **minimum** of their individual ceilings:

```
Entity A (TPM2):     ceiling = 1.0
Entity B (TrustZone): ceiling = 1.0
Entity C (Software):  ceiling = 0.85

Bridge A↔B:  ceiling = min(1.0, 1.0) = 1.0   ← Hardware-to-hardware
Bridge A↔C:  ceiling = min(1.0, 0.85) = 0.85  ← Weakest link
Bridge B↔C:  ceiling = min(1.0, 0.85) = 0.85  ← Weakest link
```

Effective trust through the bridge:

```
effective_trust = bridge.trust_multiplier * min(A.ceiling, B.ceiling) * min(A.t3.composite, B.t3.composite)
```

---

## 7. Witnessed Pairing Ceremony

### 7.1 Why Witnesses Matter

Unwitnessed pairing has trust_level = 0.3 because:
- Both parties could be controlled by same adversary (Sybil)
- No third-party attestation of the pairing event
- PCR values have no baseline for comparison

### 7.2 Witness Requirements

A witnessed pairing ceremony requires:

1. **At least 1 witness** with established trust (T3 composite > 0.5)
2. **Witness sees both** discovery records and both attestation results
3. **Witness signs** the pairing record (attesting they observed it)
4. **Witness is independent** (not bound to either machine)

### 7.3 Witness Types for Cross-Machine Pairing

| Witness Type | How It Works | Trust Boost |
|-------------|-------------|-------------|
| **Human operator** | Physically present at both machines, verifies displays | +0.3 |
| **Society entity** | Society's oracle witnesses the pairing ceremony | +0.25 |
| **Time oracle** | Timestamps the pairing event on-chain | +0.1 |
| **Network witness** | Third machine observes the exchange | +0.15 |

### 7.4 Ceremony Protocol

```
Witness
  │
  ├── Observes Discovery exchange
  │     └── Validates both LCTs
  │
  ├── Observes Mutual AVP
  │     └── Verifies both proofs independently
  │
  ├── Observes Attestation exchange
  │     └── Validates both attestations
  │
  ├── Signs PairingWitnessRecord
  │     └── Includes hash of all observations
  │
  └── Publishes attestation
        └── Adds to both entities' MRH witness records
```

---

## 8. Security Analysis

### 8.1 Threat Model

| Threat | Mitigation |
|--------|-----------|
| **Relay attack** | AVP canonical payload binds verifier + session + action hash |
| **Replay attack** | Challenge nonce + timestamp + TTL (300s for pairing) |
| **Sybil (fake machine)** | Hardware attestation (TPM quote / PSA token) + witness |
| **MITM on network** | Signatures on all messages; public keys from LCT, not wire |
| **Clock skew** | TTL tolerance + time oracle witness |
| **PCR tampering** | PCR values are read-only hardware registers; tampering changes them |
| **Stolen public key** | Public keys are public; security comes from private key in hardware |
| **Hardware compromise** | PCR drift detection triggers bridge DEGRADED/BROKEN state |

### 8.2 Attack Surface Compared to AVP

| Property | Single-Machine AVP | Cross-Machine CMTVP |
|----------|-------------------|---------------------|
| Network required | No | Yes |
| Replay window | 60s | 300s (wider for network) |
| Witness required | No | Recommended |
| Hardware heterogeneity | No | Yes |
| Trust ceiling | Direct | min(A, B) |

---

## 9. Implementation Roadmap

### Phase 1: Simulation (Current)

- [x] AVP protocol implemented and tested on Legion TPM2
- [x] Trust bridge concept defined (this document)
- [ ] Implement `TrustBridge` class extending `Web4Entity`
- [ ] Simulate cross-machine verification with two `Web4Entity` instances

### Phase 2: Local Network (Next)

- [ ] JSON-over-HTTPS transport for challenge/proof/attestation
- [ ] Implement on Legion (TPM2) with Python server
- [ ] Test with software provider on same machine (simulate Thor)

### Phase 3: Cross-Machine (Requires Thor OP-TEE)

- [ ] Set up TrustZone binding on Thor (OP-TEE)
- [ ] Implement TrustZoneProvider in `core/lct_binding/`
- [ ] First real cross-machine pairing: Legion TPM2 ↔ Thor TrustZone
- [ ] Measure latency, failure modes, PCR drift patterns

### Phase 4: Federation

- [ ] Society entity witnesses cross-machine pairings
- [ ] Trust bridge registry (society-level)
- [ ] Multi-hop trust: A↔B↔C transitivity with trust decay

---

## 10. Connection to Fractal DNA

The cross-machine trust verification protocol is the **inter-cellular signaling** of the fractal DNA pattern. Just as biological cells communicate through membrane proteins and signaling molecules:

| Biological | CMTVP |
|-----------|-------|
| Cell membrane | Hardware security boundary (TPM/TrustZone) |
| Membrane proteins | LCT public keys (exported identity) |
| Signaling molecules | AVP challenges and proofs |
| Cell-cell junction | Trust bridge LCT |
| Tissue formation | Federation of verified machines |
| Immune recognition | Cross-attestation verification |

The trust bridge IS the synthon boundary — the membrane through which entities on different machines interact without losing their individual identity.

---

## 11. Open Questions

1. **Trust decay over distance**: Should trust through a 3-hop bridge (A↔B↔C↔D) decay multiplicatively or with a floor?
2. **Offline bridge maintenance**: How long can a bridge survive without heartbeat before degrading? Current: 3 missed heartbeats.
3. **Bridge key rotation**: When one endpoint rotates keys, how does the bridge handle the transition?
4. **Heterogeneous attestation equivalence**: Are TPM2 PCR quotes and TrustZone PSA tokens truly equivalent for trust purposes? Or should we weight them differently?
5. **Transport security**: Do we need TLS for the challenge/proof exchange, or is the cryptographic binding sufficient? (Likely sufficient for integrity, but confidentiality may matter for privacy.)

---

*"The system is what emerges when cells interact. The trust bridge is how they interact."*
