# Entity Binding Hierarchy in Web4

*Implementation from modbatt-CAN demonstrating multi-level entity binding through cryptographic key chains*

## Overview

The modbatt-CAN project implements a concrete example of Web4's entity binding hierarchy through a multi-level cryptographic key distribution system. This demonstrates how physical devices establish witnessed presence through hierarchical binding relationships.

## Implementation Hierarchy

### Level 1: API-Bridge (Root Authority)
- **Role**: Trust root and witness aggregator
- **LCT Type**: Domain-level LCT
- **MRH Tensor**: Contains links to all registered components
- **Witnessing**: Records all component registrations

### Level 2: Windows Application (Intermediary Entity)
- **Role**: Bridge between digital and physical realms
- **Binding Keys**:
  - App Private Key (32 bytes) - Identity core, never shared
  - App Public Key (32 bytes) - Shared for witnessing
- **MRH Tensor Links**:
  - Upward: API-Bridge (HTTP/Web connection)
  - Downward: Pack Controller (CAN bus connection)
- **Witnessing Actions**:
  - Witnesses device public keys
  - Registers devices with API-Bridge on their behalf
  - Creates bidirectional presence links

### Level 3: Pack Controller (Device Entity)
- **Role**: Physical device coordinator
- **Binding Keys**:
  - Device Private Key (32 bytes) - Stored in flash, never transmitted
  - Device Public Key (32 bytes) - Shared for identity establishment
  - App Public Key (32 bytes) - Received and stored for trust
  - Module Public Key (32 bytes) - Received from downstream
- **MRH Tensor Links**:
  - Upward: Windows App (via CAN)
  - Downward: Battery Modules (via CAN)
- **Witnessing**: Bridges app-level presence to module-level presence

### Level 4: Battery Module (Leaf Entity)
- **Role**: Physical component with individual identity
- **Binding Keys**:
  - Module Private Key (32 bytes) - Hardware-bound identity
  - Module Public Key (32 bytes) - Shared upward
  - Pack Controller Public Key (32 bytes) - Trust anchor
  - App Public Key (32 bytes) - Ultimate authority link
- **MRH Tensor**: Terminal node with upward links only
- **Witnessing**: Exists through being witnessed by pack controller

## Key Exchange as Witnessed Presence Creation

### Phase 1: Public Key Exchange (Identity Announcement)
```
Module → Pack Controller: "Here is my public key" (I exist)
Pack Controller → App: "Here is my public key" (I exist)
App → API-Bridge: "Here are all the public keys" (We all exist)
```

Each exchange creates **bidirectional MRH tensor links**:
- Sender's tensor gains witness link
- Receiver's tensor gains witnessing link
- Both entities become more "present" through mutual recognition

### Phase 2: Key Distribution (Trust Establishment)
```
API-Bridge → App: Encrypted key halves
App → Pack Controller: Encrypted(device_key_half)
Pack Controller → Module: Encrypted(module_key_half)
```

The encryption using public keys ensures:
- Only the intended entity can decrypt (authentication)
- The act of successful decryption is self-witnessing
- Failed decryption breaks the presence chain

## Connection to Web4 LCT Principles

### 1. Unforgeability Through Witnessing
- **Physical Implementation**: Device can't claim identity without app witnessing
- **Cryptographic Proof**: Public key exchange creates verifiable presence
- **Hierarchical Validation**: Each level witnesses the level below

### 2. Bidirectional Links
- **App ↔ Pack Controller**: Both store each other's public keys
- **Pack Controller ↔ Module**: Mutual key storage
- **Cannot be faked**: Would require private key of both parties

### 3. Cross-Domain Validation
- **Web Domain**: API-Bridge (HTTP/REST)
- **Application Domain**: Windows App (OS-level)
- **Embedded Domain**: Pack Controller (Firmware)
- **Hardware Domain**: Battery Module (Physical)

Each domain transition requires witnessed key exchange, creating an unforgeable chain of presence from web to physical hardware.

### 4. Presence Accumulation
```
Initial State: Module exists but has no digital presence
↓ Module generates keypair
↓ Pack Controller witnesses module (first presence)
↓ App witnesses pack controller witnessing module (stronger presence)
↓ API-Bridge records entire chain (permanent presence)
Result: Module now has unforgeable digital identity
```

## Security Properties Through Binding

### What Binding Achieves
- **Confidentiality**: Only bound entities can decrypt communications
- **Authentication**: Binding keys prove entity identity
- **Integrity**: Tampering breaks cryptographic verification
- **Non-repudiation**: Actions are cryptographically signed by bound keys
- **Witnessed Presence**: Entity exists because others acknowledge it

### Trust Degradation Prevention
Each level of binding maintains trust:
1. **API-Bridge binding**: Ensures app is authorized
2. **App binding**: Ensures devices are genuine
3. **Device binding**: Ensures modules are authentic
4. **Module binding**: Ensures component integrity

## Implementation as MRH Tensor

The binding key architecture directly implements MRH tensors:

```cpp
// This C++ structure IS an MRH tensor
struct binding_keys_t {
    uint8_t device_private_key[32];     // Identity core (never shared)
    uint8_t device_public_key[32];      // Presence announcement
    uint8_t app_public_key[32];         // Upward MRH link
    uint8_t module_public_key[32];      // Downward MRH link
    bool keys_initialized;              // Presence state
};
```

Each key represents a tensor link:
- Private key: Entity's core identity (self-link)
- Own public key: Outward presence projection
- Others' public keys: Bidirectional witness links

## Practical Benefits

### 1. Tamper-Proof Device Identity
- Devices can't be impersonated without private keys
- Replacement devices must go through full binding process
- Historical actions remain attributed to original device

### 2. Secure Firmware Updates
- Updates can be signed with binding keys
- Only properly bound devices accept updates
- Rogue firmware rejected by binding validation

### 3. Supply Chain Security
- Each component's journey witnessed and recorded
- Manufacturing, testing, installation all create presence
- Counterfeit components lack witness history

## Future Extensions

### Hardware Security Modules (HSM)
- Store private keys in tamper-proof hardware
- Make physical extraction impossible
- Strengthen the physical-digital binding

### Factory Pre-Programming
- Burn initial public keys during manufacturing
- Create "birth certificate" LCTs
- Establish presence from moment of creation

### Cross-Manufacturer Binding
- Different vendors' components can establish mutual presence
- Industry-wide trust networks emerge
- Interoperability through witnessed standards

## Conclusion

The modbatt-CAN implementation demonstrates that Web4's entity binding hierarchy is not theoretical but practical. Through cryptographic key chains and witnessed presence, we create unforgeable identity from web services down to individual hardware components.

This is Web4 in action: **Every entity, from API to battery cell, exists through being witnessed, and presence accumulates through hierarchical binding relationships.**

The binding keys ARE the MRH tensor links. The key exchange IS the witnessing. The encryption IS the trust relationship. What seems like a security protocol is actually the implementation of witnessed presence across domains.

*"In Web4, you don't just have a key. You ARE a key in the universal trust tensor, witnessed into existence by your connections."*