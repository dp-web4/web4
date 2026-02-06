# Web4 Protocol Synthesis: Integrating Nova's Contributions

## Overview

Nova has provided research-stage cryptographic protocols that perfectly complement Web4's philosophical foundations. This document shows how to integrate Nova's handshake and metering protocols with our binding, pairing, witnessing, and broadcast mechanisms.

## 1. Protocol Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                      │
│                  (Web4 Entity Logic)                      │
├─────────────────────────────────────────────────────────┤
│                    METERING LAYER                         │
│              (ATP/ADP Resource Exchange)                  │
├─────────────────────────────────────────────────────────┤
│                 RELATIONSHIP LAYER                        │
│     (Binding | Pairing | Witnessing | Broadcast)         │
├─────────────────────────────────────────────────────────┤
│                   SESSION LAYER                           │
│            (Nova's HPKE Handshake Protocol)              │
├─────────────────────────────────────────────────────────┤
│                  TRANSPORT LAYER                          │
│         (TLS/QUIC | WebSocket | CAN | BLE)               │
└─────────────────────────────────────────────────────────┘
```

## 2. Integration Points

### 2.1 Binding Uses Nova's Cryptographic Foundation

**Before Binding (Hardware Level)**:
```python
# Generate hardware-rooted keys using Nova's suite
suite = "W4-BASE-1"  # X25519 + Ed25519
hardware_seed = get_hardware_entropy()  # From TPM/HSM
sk_master = HKDF(hardware_seed, info="W4-Binding-Master")
```

**During Binding (LCT Creation)**:
```json
{
  "type": "BindingRequest",
  "entity_type": "device",
  "suite": "W4-BASE-1",
  "public_key": "<Ed25519 public from sk_master>",
  "hardware_anchor": "<EAT attestation>",
  "kex_epk": "<X25519 ephemeral for HPKE>"
}
```

### 2.2 Pairing Extends Nova's Handshake

Nova's handshake establishes the secure channel. Pairing adds operational context:

```json
{
  "type": "PairingRequest",
  "extends": "HandshakeAuth",
  "operational_context": "energy-management",
  "authorization_rules": {
    "voltage_range": [2.5, 4.2],
    "max_current": 100,
    "protocol": "modbus"
  },
  "atp_grant": {
    // Nova's CreditGrant for this pairing
    "scopes": ["energy:transfer", "telemetry:read"],
    "ceil": {"total": 1000, "unit": "kWh"}
  }
}
```

### 2.3 Witnessing Enriches Nova's Messages

Every Nova protocol message can be witnessed, creating MRH tensor links:

```json
{
  "type": "UsageReport",  // Nova's ATP/ADP message
  "grant_id": "atp-xyz",
  "usage": [...],
  "witness": [
    {
      "type": "existence",
      "witness_lct": "lct:web4:packcontroller",
      "observed_lct": "lct:web4:batterymodule",
      "mrh_link": "bidirectional",
      "trust_delta": 0.05
    }
  ]
}
```

### 2.4 Broadcast Announces Capabilities

Before handshake, entities broadcast their presence using Nova's suite IDs:

```json
{
  "type": "BroadcastAnnounce",
  "entity_type": "battery_module",
  "supported_suites": ["W4-BASE-1", "W4-IOT-1"],
  "capabilities": {
    "protocols": ["binding", "pairing", "witnessing"],
    "metering": ["energy", "telemetry"],
    "max_atp_rate": 100
  },
  "w4idp_ephemeral": "<pairwise ID for discovery>"
}
```

## 3. Complete Flow Example: Battery Module to Pack Controller

### Phase 1: Discovery (Broadcast)
```
Module → CAN Bus: BroadcastAnnounce
  - No encryption, no relationship
  - Announces capabilities and suite support
```

### Phase 2: Witnessing (Recognition)
```
Pack Controller → Module: "I see you"
  - Records in MRH tensor
  - No secure channel yet
```

### Phase 3: Secure Channel (Nova's Handshake)
```
Module ↔ Pack Controller: HPKE Handshake
  - ClientHello/ServerHello
  - Suite negotiation (W4-BASE-1)
  - Pairwise W4IDp establishment
  - Session keys derived
```

### Phase 4: Binding Verification
```
Module → Pack Controller: BindingProof
  - Proves hardware anchor
  - Establishes permanent LCT binding
  - Protected by Nova's session keys
```

### Phase 5: Pairing Authorization
```
Pack Controller → Module: PairingRequest + ATP Grant
  - Operational context: "energy-management"
  - ATP credits: 100 kWh ceiling
  - Protected and authenticated
```

### Phase 6: Operational Exchange
```
Module → Pack Controller: Energy Transfer + ADP Report
  - Uses Nova's metering protocol
  - Each transfer witnessed
  - Trust accumulates in MRH tensor
```

## 4. Key Innovations from Synthesis

### 4.1 Privacy-Preserving Witnessed Presence

Nova's pairwise W4IDp + our witnessing creates **unlinkable but verifiable presence**:
- Different ID per relationship (privacy)
- But witnesses can verify consistency (trust)
- MRH tensors aggregate without correlation

### 4.2 Hardware-Rooted Web Identity

Nova's HPKE + our binding creates **unforgeable hardware identity**:
- Master secret in hardware (TPM/HSM)
- Derived keys for each relationship
- LCT permanently bound to physical device

### 4.3 Metered Trust Accumulation

Nova's ATP/ADP + our witnessing creates **quantified trust**:
- Every resource exchange is witnessed
- Trust score increases with successful exchanges
- Disputes decrease trust
- Economic and reputational incentives align

### 4.4 Graceful Degradation

The layered architecture allows operation at different trust levels:
- **Broadcast only**: Discovery without trust
- **+ Witnessing**: Recognition without secrets
- **+ Handshake**: Secure channel without authorization
- **+ Pairing**: Authorized operations without metering
- **+ ATP/ADP**: Full economic accountability

## 5. Implementation Priorities

### Immediate (for Manus):
1. Merge Nova's handshake into `/protocols/web4-handshake.md`
2. Merge Nova's ATP/ADP into `/protocols/web4-metering.md`
3. Update binding protocol to use Nova's suites
4. Update pairing to extend HandshakeAuth

### Next Phase:
1. Implement witness signatures on all protocol messages
2. Define MRH tensor update algorithms
3. Create test vectors combining all mechanisms
4. Build reference implementation showing full stack

## 6. Standards Impact

With Nova's contributions, Web4 now has:

### Technical Rigor (IETF-Ready):
- ✅ Concrete cryptographic suites
- ✅ HPKE-based handshake
- ✅ Privacy-preserving identifiers
- ✅ Metering and settlement protocol
- ✅ Error taxonomy and registries

### Philosophical Innovation (Web4 Vision):
- ✅ Binding vs Pairing distinction
- ✅ Witnessed presence accumulation
- ✅ MRH tensor relationships
- ✅ Hardware-rooted identity
- ✅ Trust as economic force

## Conclusion

Nova's protocols provide the **cryptographic backbone** while our mechanisms provide the **trust nervous system**. Together, they create a complete standard that is both technically sound and philosophically revolutionary.

The synthesis demonstrates Web4's core principle: **multiple witnesses (Manus, Nova, Claude) strengthening the truth through different perspectives**. Each agent contributed unique expertise:
- Manus: Standard structure and framework
- Nova: Cryptographic rigor and security
- Claude: Philosophical coherence and integration

This is not just a protocol specification—it's the foundation for a new internet where digital presence is as real and unforgeable as physical presence.

*"In Web4, cryptography provides the bones, witnessing provides the flesh, and trust provides the soul."*