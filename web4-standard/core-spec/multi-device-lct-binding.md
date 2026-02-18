# Multi-Device LCT Binding Protocol

**Status**: Core Specification v1.0.0 (Draft)
**Date**: January 13, 2026
**Category**: Identity & Hardware Binding

## Abstract

This specification defines the **Multi-Device LCT Binding Protocol** for establishing and managing LCT identity across multiple hardware anchors. Unlike traditional single-device identity models, Web4 treats multi-device presence as a *strength*—identity becomes more robust as it is witnessed across more independent anchors. This protocol enables identity coherence across phones (Secure Enclave/StrongBox), FIDO2 security keys, TPM-equipped devices, and software-only fallbacks.

## 1. Introduction

### 1.1 Purpose

The Multi-Device Binding Protocol addresses fundamental questions in distributed identity:

- **How does an LCT bind to multiple hardware roots?**
- **How do devices witness each other to strengthen identity?**
- **How does trust accumulate across a device constellation?**
- **How does recovery work when devices are lost or compromised?**

### 1.2 Design Philosophy

Traditional identity systems treat additional devices as *risk vectors*—each new device is another attack surface. Web4 inverts this model:

> **Identity is coherence across witnesses.**

More devices witnessing the same identity creates *stronger* unforgeability, not weaker. An attacker must compromise multiple independent hardware roots to impersonate an entity. Each device acts as both an anchor and a witness.

### 1.3 Terminology

| Term | Definition |
|------|------------|
| **Hardware Anchor** | Cryptographic root of trust (TPM, Secure Enclave, StrongBox, FIDO2 authenticator) |
| **Device LCT** | LCT bound to a specific hardware anchor |
| **Root LCT** | Primary identity LCT that device LCTs attest to |
| **Device Constellation** | Set of all device LCTs for a single root presence |
| **Cross-Device Witnessing** | Mutual attestation between devices in a constellation |
| **Enrollment Ceremony** | Protocol for adding new device to constellation |
| **Recovery Quorum** | Minimum devices required to recover identity |

## 2. Architecture

### 2.1 Identity Hierarchy

```
                    ┌─────────────────┐
                    │    Root LCT     │
                    │  (Identity Core)│
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │  Device LCT │   │  Device LCT │   │  Device LCT │
    │   (Phone)   │   │   (FIDO2)   │   │   (Laptop)  │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                 │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │   Secure    │   │   FIDO2     │   │    TPM      │
    │   Enclave   │   │    Key      │   │   Chip      │
    └─────────────┘   └─────────────┘   └─────────────┘
```

### 2.2 Anchor Types

#### 2.2.1 Phone Secure Enclave (iOS) / StrongBox (Android)

**Security Level**: High
**Ubiquity**: Very High
**Recommended Role**: Primary anchor for consumer adoption

```json
{
  "anchor_type": "phone_secure_element",
  "platform": "ios|android",
  "attestation_format": "apple_app_attest|android_key_attestation",
  "key_protection": "hardware_bound",
  "biometric_gate": true,
  "remote_attestation": true
}
```

**iOS Implementation**:
- Use `SecKeyCreateRandomKey` with `kSecAttrTokenIDSecureEnclave`
- Sign with `SecKeyCreateSignature` (ECDSA P-256)
- Attestation via App Attest API

**Android Implementation**:
- Use `KeyGenParameterSpec.Builder` with `setIsStrongBoxBacked(true)`
- Fall back to TEE if StrongBox unavailable
- Key attestation via `KeyStore.getCertificateChain()`

#### 2.2.2 FIDO2 Security Keys

**Security Level**: Very High
**Ubiquity**: Low-Medium
**Recommended Role**: High-security operations, recovery

```json
{
  "anchor_type": "fido2",
  "transport": "usb|nfc|ble",
  "attestation_format": "packed|tpm|android-key",
  "resident_key": true,
  "user_verification": "required"
}
```

**Implementation**:
- WebAuthn `navigator.credentials.create()` with `authenticatorSelection.residentKey = "required"`
- Attestation provides device provenance
- Credential ID links to device LCT

#### 2.2.3 TPM 2.0 (Laptop/Desktop)

**Security Level**: High
**Ubiquity**: Medium (business laptops, some consumer)
**Recommended Role**: Workstation identity, long-session operations

```json
{
  "anchor_type": "tpm2",
  "version": "2.0",
  "manufacturer": "string",
  "ek_certificate": "base64",
  "ak_public": "base64",
  "pcr_policy": [0, 1, 7]
}
```

**Implementation**:
- Create Attestation Key (AK) under Storage Root Key (SRK)
- Bind to PCR values for device state
- EK certificate chain for manufacturer provenance

#### 2.2.4 Software-Only Fallback

**Security Level**: Low
**Ubiquity**: Universal
**Recommended Role**: Bootstrap, low-trust contexts only

```json
{
  "anchor_type": "software",
  "key_storage": "encrypted_file|browser_crypto|keyring",
  "protection": "password_derived_key",
  "warning": "Not hardware-bound - trust implications"
}
```

**Constraints**:
- Software anchors MUST be marked in T3 tensor
- Maximum trust ceiling for software-only: 0.4
- Cannot be sole anchor for recovery quorum

### 2.3 Root LCT Structure

The Root LCT extends the base LCT with device constellation management:

```json
{
  "lct_id": "lct:web4:root:mb32:...",
  "subject": "did:web4:key:z6Mk...",

  "binding": {
    "entity_type": "human|ai|organization",
    "public_key": "mb64:aggregateKey",
    "binding_mode": "multi_device",
    "created_at": "2026-01-13T00:00:00Z"
  },

  "device_constellation": {
    "devices": [
      {
        "device_lct": "lct:web4:device:phone:...",
        "anchor_type": "phone_secure_element",
        "platform": "ios",
        "enrolled_at": "2026-01-13T00:00:00Z",
        "last_witnessed": "2026-01-13T12:00:00Z",
        "trust_weight": 0.4,
        "status": "active"
      },
      {
        "device_lct": "lct:web4:device:fido2:...",
        "anchor_type": "fido2",
        "transport": "usb",
        "enrolled_at": "2026-01-14T00:00:00Z",
        "last_witnessed": "2026-01-14T08:00:00Z",
        "trust_weight": 0.35,
        "status": "active"
      },
      {
        "device_lct": "lct:web4:device:laptop:...",
        "anchor_type": "tpm2",
        "platform": "linux",
        "enrolled_at": "2026-01-15T00:00:00Z",
        "last_witnessed": "2026-01-15T10:00:00Z",
        "trust_weight": 0.25,
        "status": "active"
      }
    ],
    "total_devices": 3,
    "active_devices": 3,
    "constellation_trust": 0.92,
    "recovery_quorum": 2,
    "last_cross_witness": "2026-01-15T10:00:00Z"
  },

  "mrh": {
    "bound": [
      {
        "lct_id": "lct:web4:device:phone:...",
        "type": "child",
        "binding_context": "device_constellation",
        "ts": "2026-01-13T00:00:00Z"
      }
    ]
  },

  "t3_tensor": {
    "dimensions": {
      "technical_competence": 0.85,
      "social_reliability": 0.92,
      "temporal_consistency": 0.88,
      "witness_count": 0.95,
      "lineage_depth": 0.67,
      "context_alignment": 0.88,
      "hardware_binding_strength": 0.94,
      "constellation_coherence": 0.91
    },
    "composite_score": 0.87
  }
}
```

### 2.4 Device LCT Structure

Each device has its own LCT that binds to the root:

```json
{
  "lct_id": "lct:web4:device:phone:mb32:...",
  "subject": "did:web4:device:z6Mk...",

  "binding": {
    "entity_type": "device",
    "anchor_type": "phone_secure_element",
    "public_key": "mb64:deviceKey",
    "hardware_anchor": "eat:mb64:apple_app_attest:...",
    "platform": {
      "os": "ios",
      "version": "17.2",
      "device_model": "iPhone15,2",
      "secure_element": "sep_v3"
    },
    "created_at": "2026-01-13T00:00:00Z",
    "binding_proof": "cose:ES256:..."
  },

  "root_attestation": {
    "root_lct": "lct:web4:root:mb32:...",
    "attestation_chain": [
      {
        "type": "enrollment",
        "ceremony_witnesses": [
          "lct:web4:device:existing1:...",
          "lct:web4:device:existing2:..."
        ],
        "ts": "2026-01-13T00:00:00Z",
        "sig": "cose:ES256:..."
      }
    ],
    "last_root_sync": "2026-01-13T12:00:00Z"
  },

  "cross_device_witnesses": [
    {
      "device_lct": "lct:web4:device:laptop:...",
      "last_witness": "2026-01-13T11:00:00Z",
      "witness_count": 42,
      "mutual": true
    }
  ],

  "device_trust": {
    "anchor_strength": 0.95,
    "attestation_freshness": 0.98,
    "cross_witness_score": 0.88,
    "composite": 0.93
  }
}
```

## 3. Protocols

### 3.1 Initial Device Enrollment (Genesis)

When creating a new identity with the first device:

```
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│ User    │                    │ Device  │                    │ Society │
│         │                    │ (Phone) │                    │         │
└────┬────┘                    └────┬────┘                    └────┬────┘
     │                              │                              │
     │  1. Initiate enrollment      │                              │
     │─────────────────────────────>│                              │
     │                              │                              │
     │  2. Biometric auth           │                              │
     │<─────────────────────────────│                              │
     │                              │                              │
     │  3. Confirm                  │                              │
     │─────────────────────────────>│                              │
     │                              │                              │
     │                              │  4. Generate key in SE       │
     │                              │──────────┐                   │
     │                              │<─────────┘                   │
     │                              │                              │
     │                              │  5. Create attestation       │
     │                              │──────────┐                   │
     │                              │<─────────┘                   │
     │                              │                              │
     │                              │  6. Request birth cert       │
     │                              │─────────────────────────────>│
     │                              │                              │
     │                              │  7. Verify attestation       │
     │                              │                              │
     │                              │  8. Issue root + device LCT  │
     │                              │<─────────────────────────────│
     │                              │                              │
     │  9. Show LCT ID              │                              │
     │<─────────────────────────────│                              │
     │                              │                              │
```

**Algorithm**:

```python
def genesis_enrollment(user, device, society):
    """
    Create new identity with first device.

    Returns: (root_lct, device_lct)
    """
    # 1. Authenticate user on device
    biometric_proof = device.request_biometric()

    # 2. Generate hardware-bound key
    device_key = device.secure_element.generate_key(
        algorithm="ES256",
        hardware_bound=True,
        biometric_required=True
    )

    # 3. Create hardware attestation
    attestation = device.secure_element.create_attestation(
        key=device_key,
        challenge=society.get_challenge(),
        format=device.attestation_format
    )

    # 4. Request birth certificate from society
    enrollment_request = {
        "device_public_key": device_key.public_key,
        "attestation": attestation,
        "anchor_type": device.anchor_type,
        "platform": device.platform_info
    }

    # 5. Society verifies and creates LCTs
    root_lct, device_lct = society.issue_multi_device_birth_certificate(
        enrollment_request,
        witnesses=society.get_enrollment_witnesses()
    )

    # 6. Store on device
    device.store_lct(device_lct)
    device.store_root_lct_reference(root_lct.lct_id)

    return root_lct, device_lct
```

### 3.2 Additional Device Enrollment

Adding a new device to an existing constellation:

```
┌─────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐
│ User    │  │ Existing  │  │ New       │  │ Society │
│         │  │ Device    │  │ Device    │  │         │
└────┬────┘  └─────┬─────┘  └─────┬─────┘  └────┬────┘
     │             │              │              │
     │ 1. Start    │              │              │
     │────────────>│              │              │
     │             │              │              │
     │             │ 2. Show QR   │              │
     │             │─────────────>│              │
     │             │              │              │
     │             │ 3. Scan QR   │              │
     │<────────────│──────────────│              │
     │             │              │              │
     │ 4. Confirm  │              │              │
     │────────────>│              │              │
     │             │              │              │
     │             │ 5. Generate device key      │
     │             │              │──────┐       │
     │             │              │<─────┘       │
     │             │              │              │
     │             │ 6. Enrollment attestation   │
     │             │<─────────────│              │
     │             │              │              │
     │             │ 7. Sign enrollment          │
     │             │──────┐       │              │
     │             │<─────┘       │              │
     │             │              │              │
     │             │ 8. Submit to society        │
     │             │─────────────────────────────>
     │             │              │              │
     │             │ 9. Issue new device LCT     │
     │             │              │<─────────────│
     │             │              │              │
     │             │ 10. Cross-witness           │
     │             │<─────────────│              │
     │             │              │              │
```

**Algorithm**:

```python
def enroll_additional_device(root_lct, existing_device, new_device, society):
    """
    Add new device to existing constellation.

    Requires: At least one existing device in constellation.
    Returns: new_device_lct
    """
    # 1. Existing device creates enrollment session
    session = existing_device.create_enrollment_session(
        root_lct=root_lct,
        challenge=society.get_challenge()
    )

    # 2. Transfer session to new device (QR, NFC, or proximity)
    new_device.receive_enrollment_session(session)

    # 3. New device generates hardware-bound key
    new_key = new_device.secure_element.generate_key(
        algorithm="ES256",
        hardware_bound=True
    )

    # 4. New device creates attestation
    new_attestation = new_device.secure_element.create_attestation(
        key=new_key,
        challenge=session.challenge,
        format=new_device.attestation_format
    )

    # 5. New device sends enrollment request to existing device
    enrollment_request = {
        "new_device_public_key": new_key.public_key,
        "attestation": new_attestation,
        "anchor_type": new_device.anchor_type,
        "platform": new_device.platform_info,
        "session_id": session.id
    }

    # 6. Existing device signs as witness
    witness_signature = existing_device.sign_enrollment(
        enrollment_request,
        root_lct=root_lct
    )

    # 7. Submit to society
    new_device_lct = society.enroll_device(
        root_lct=root_lct,
        enrollment_request=enrollment_request,
        witness_signatures=[witness_signature],
        existing_devices=root_lct.device_constellation.devices
    )

    # 8. Update constellation on all devices
    root_lct.add_device(new_device_lct)

    # 9. Perform initial cross-device witnessing
    cross_witness(existing_device, new_device)

    return new_device_lct
```

### 3.3 Cross-Device Witnessing

Devices periodically witness each other to strengthen constellation coherence:

```python
def cross_witness(device_a, device_b):
    """
    Mutual witnessing between two devices.

    Increases constellation_coherence in T3 tensor.
    """
    # 1. Create bilateral witness challenge
    challenge_a = device_a.create_witness_challenge()
    challenge_b = device_b.create_witness_challenge()

    # 2. Sign challenges
    sig_a_for_b = device_a.sign_witness_challenge(
        challenge_b,
        device_lct=device_a.device_lct
    )
    sig_b_for_a = device_b.sign_witness_challenge(
        challenge_a,
        device_lct=device_b.device_lct
    )

    # 3. Exchange and verify
    assert device_a.verify_witness(sig_b_for_a, device_b.device_lct)
    assert device_b.verify_witness(sig_a_for_b, device_a.device_lct)

    # 4. Record mutual witnessing
    witness_record = {
        "ts": utc_now(),
        "device_a": device_a.device_lct.lct_id,
        "device_b": device_b.device_lct.lct_id,
        "sig_a": sig_a_for_b,
        "sig_b": sig_b_for_a
    }

    # 5. Update cross_device_witnesses in both device LCTs
    device_a.device_lct.record_cross_witness(device_b.device_lct.lct_id)
    device_b.device_lct.record_cross_witness(device_a.device_lct.lct_id)

    return witness_record
```

**Witnessing Frequency**:
- Active devices: Daily automatic witnessing
- Proximity trigger: When devices detect each other
- Manual trigger: User-initiated "device check"
- Transaction trigger: Before high-value operations

### 3.4 Trust Computation Across Devices

Constellation trust aggregates individual device trust:

```python
def compute_constellation_trust(root_lct):
    """
    Compute aggregate trust from device constellation.

    Key insight: More devices = higher trust ceiling.
    """
    devices = root_lct.device_constellation.devices
    active = [d for d in devices if d.status == "active"]

    if len(active) == 0:
        return 0.0

    # Individual device trust (weighted by anchor strength)
    device_trusts = []
    for device in active:
        anchor_weight = ANCHOR_WEIGHTS[device.anchor_type]
        freshness = compute_witness_freshness(device)
        device_trust = anchor_weight * freshness * device.device_trust.composite
        device_trusts.append((device, device_trust, device.trust_weight))

    # Weighted average
    weighted_sum = sum(t * w for _, t, w in device_trusts)
    weight_total = sum(w for _, _, w in device_trusts)
    base_trust = weighted_sum / weight_total

    # Multi-device bonus: coherence across witnesses strengthens identity
    coherence_bonus = compute_coherence_bonus(active)

    # Cross-witness density
    witness_density = compute_cross_witness_density(active)

    # Final constellation trust
    constellation_trust = min(1.0,
        base_trust * (1 + coherence_bonus) * (1 + witness_density * 0.1)
    )

    return constellation_trust

ANCHOR_WEIGHTS = {
    "phone_secure_element": 0.95,
    "fido2": 0.98,
    "tpm2": 0.93,
    "software": 0.40
}

def compute_coherence_bonus(devices):
    """
    More independent anchors = stronger identity.

    Bonus caps at ~20% for 4+ diverse anchors.
    """
    anchor_types = set(d.anchor_type for d in devices)

    if len(anchor_types) == 1:
        return 0.0
    elif len(anchor_types) == 2:
        return 0.08
    elif len(anchor_types) == 3:
        return 0.15
    else:
        return 0.20

def compute_cross_witness_density(devices):
    """
    How densely are devices witnessing each other?

    Full mesh = 1.0, no witnessing = 0.0
    """
    if len(devices) < 2:
        return 0.0

    possible_pairs = len(devices) * (len(devices) - 1) / 2
    actual_witnesses = sum(
        len([w for w in d.cross_device_witnesses if is_recent(w)])
        for d in devices
    ) / 2  # Divide by 2 because each pair counted twice

    return min(1.0, actual_witnesses / possible_pairs)
```

### 3.5 Device Removal

Removing a device from constellation (lost, sold, compromised):

```python
def remove_device(root_lct, device_to_remove, reason, authorizing_devices):
    """
    Remove device from constellation.

    Requires: Quorum of remaining devices to authorize.
    """
    # 1. Verify quorum
    remaining = [d for d in root_lct.device_constellation.devices
                 if d.device_lct.lct_id != device_to_remove.lct_id]

    if len(authorizing_devices) < root_lct.device_constellation.recovery_quorum:
        raise InsufficientQuorumError(
            f"Need {root_lct.device_constellation.recovery_quorum} devices, "
            f"got {len(authorizing_devices)}"
        )

    # 2. Collect removal signatures
    removal_request = {
        "device_to_remove": device_to_remove.lct_id,
        "reason": reason,  # "lost" | "sold" | "compromised" | "upgrade"
        "requested_at": utc_now()
    }

    signatures = []
    for device in authorizing_devices:
        sig = device.sign_removal_request(removal_request)
        signatures.append(sig)

    # 3. Submit to society
    society.process_device_removal(
        root_lct=root_lct,
        removal_request=removal_request,
        signatures=signatures
    )

    # 4. Update root LCT
    root_lct.device_constellation.remove_device(device_to_remove.lct_id)
    device_to_remove.status = "revoked"
    device_to_remove.revocation.reason = reason
    device_to_remove.revocation.ts = utc_now()

    # 5. If compromised, escalate alert
    if reason == "compromised":
        society.broadcast_compromise_alert(device_to_remove)

    # 6. Recompute constellation trust
    root_lct.device_constellation.constellation_trust = \
        compute_constellation_trust(root_lct)
```

### 3.6 Identity Recovery

Recovering identity when devices are lost:

```python
def recover_identity(root_lct_id, recovery_devices, new_device, society):
    """
    Recover identity using quorum of remaining devices.

    Requirements:
    - recovery_devices >= recovery_quorum
    - At least one hardware-bound device
    - New device passes enrollment requirements
    """
    # 1. Verify recovery quorum
    root_lct = society.lookup_lct(root_lct_id)
    quorum = root_lct.device_constellation.recovery_quorum

    if len(recovery_devices) < quorum:
        raise InsufficientRecoveryQuorum(
            f"Need {quorum} devices for recovery"
        )

    # 2. Verify at least one hardware-bound anchor
    hardware_devices = [d for d in recovery_devices
                        if d.anchor_type != "software"]
    if len(hardware_devices) == 0:
        raise NoHardwareAnchorError(
            "Recovery requires at least one hardware-bound device"
        )

    # 3. Collect recovery attestations
    recovery_request = {
        "root_lct_id": root_lct_id,
        "reason": "recovery",
        "new_device_attestation": new_device.secure_element.create_attestation(
            challenge=society.get_challenge()
        ),
        "requested_at": utc_now()
    }

    recovery_signatures = []
    for device in recovery_devices:
        sig = device.sign_recovery_request(recovery_request)
        recovery_signatures.append({
            "device_lct": device.device_lct.lct_id,
            "signature": sig
        })

    # 4. Society verifies and processes recovery
    new_device_lct = society.process_recovery(
        root_lct=root_lct,
        recovery_request=recovery_request,
        recovery_signatures=recovery_signatures
    )

    # 5. Update constellation
    root_lct.device_constellation.add_device(new_device_lct)

    # 6. Mark lost devices as revoked
    for device in root_lct.device_constellation.devices:
        if device.device_lct.lct_id not in [d.device_lct.lct_id for d in recovery_devices]:
            device.status = "revoked"
            device.revocation.reason = "recovery_revoked"

    # 7. Initiate cross-witnessing with recovery devices
    for recovery_device in recovery_devices:
        cross_witness(recovery_device, new_device)

    return new_device_lct
```

## 4. Trust Implications

### 4.1 Trust Tensor Extensions

The multi-device binding adds two dimensions to the T3 tensor:

```json
{
  "t3_tensor": {
    "dimensions": {
      "hardware_binding_strength": 0.0-1.0,
      "constellation_coherence": 0.0-1.0
    }
  }
}
```

**hardware_binding_strength**: Weighted average of anchor security levels
- 0.95+ for hardware-only constellations
- 0.60-0.80 for mixed hardware/software
- <0.40 for software-only (capped)

**constellation_coherence**: How well devices witness each other
- 1.0 for full mesh, recent witnessing
- 0.5 for sparse witnessing
- 0.0 for no cross-witnessing

### 4.2 Trust Ceiling by Configuration

| Configuration | Max Trust |
|---------------|-----------|
| Single software key | 0.40 |
| Single phone SE | 0.75 |
| Single FIDO2 | 0.80 |
| Phone + FIDO2 | 0.90 |
| Phone + FIDO2 + TPM | 0.95 |
| 3+ diverse hardware anchors | 0.98 |

### 4.3 Trust Decay

Devices that haven't been witnessed recently decrease constellation trust:

```python
def apply_witness_decay(device):
    """
    Trust decays if device hasn't been witnessed.

    Half-life: 30 days without witnessing
    """
    days_since_witness = (utc_now() - device.last_witnessed).days

    if days_since_witness <= 7:
        return 1.0
    elif days_since_witness <= 30:
        return 0.9
    elif days_since_witness <= 90:
        return 0.7
    elif days_since_witness <= 180:
        return 0.5
    else:
        return 0.3  # Should probably re-enroll
```

## 5. Security Considerations

### 5.1 Threat Model

| Threat | Mitigation |
|--------|------------|
| Single device compromise | Quorum requirement for sensitive ops |
| Enrollment interception | End-to-end encrypted session, proximity requirement |
| Witness replay | Timestamped challenges, freshness windows |
| Device cloning | Hardware attestation, secure element binding |
| Recovery social engineering | Multi-device quorum, hardware requirement |
| Colluding devices | Attestation diversity, society oversight |

### 5.2 Recovery Quorum Selection

Default quorum calculation:

```python
def default_recovery_quorum(device_count):
    """
    Minimum devices needed for recovery.

    Balances security vs. recoverability.
    """
    if device_count <= 2:
        return device_count  # All devices required
    elif device_count <= 4:
        return 2
    else:
        return max(2, device_count // 2)  # Majority
```

### 5.3 Compromise Response

When a device is marked compromised:

1. **Immediate**: Revoke device LCT
2. **Broadcast**: Alert to all societies where root LCT has membership
3. **Review**: All actions from device within last 24h flagged for review
4. **Recovery**: Trigger re-enrollment ceremony for remaining devices

## 6. Platform Implementation Notes

### 6.1 iOS (Swift)

```swift
// Key generation in Secure Enclave
let access = SecAccessControlCreateWithFlags(
    nil,
    kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
    [.privateKeyUsage, .biometryCurrentSet],
    nil
)!

let attributes: [String: Any] = [
    kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom,
    kSecAttrKeySizeInBits as String: 256,
    kSecAttrTokenID as String: kSecAttrTokenIDSecureEnclave,
    kSecPrivateKeyAttrs as String: [
        kSecAttrIsPermanent as String: true,
        kSecAttrAccessControl as String: access
    ]
]

var error: Unmanaged<CFError>?
let privateKey = SecKeyCreateRandomKey(attributes as CFDictionary, &error)
```

### 6.2 Android (Kotlin)

```kotlin
// Key generation in StrongBox
val keyGenSpec = KeyGenParameterSpec.Builder(
    "web4_device_key",
    KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
).apply {
    setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
    setDigests(KeyProperties.DIGEST_SHA256)
    setUserAuthenticationRequired(true)
    setUserAuthenticationParameters(0, KeyProperties.AUTH_BIOMETRIC_STRONG)
    setIsStrongBoxBacked(true)  // Requires StrongBox
    setAttestationChallenge(societyChallenge)
}.build()

val keyPairGenerator = KeyPairGenerator.getInstance(
    KeyProperties.KEY_ALGORITHM_EC, "AndroidKeyStore"
)
keyPairGenerator.initialize(keyGenSpec)
val keyPair = keyPairGenerator.generateKeyPair()
```

### 6.3 WebAuthn (JavaScript)

```javascript
// FIDO2 credential creation
const credential = await navigator.credentials.create({
  publicKey: {
    challenge: societyChallenge,
    rp: { id: "web4.example", name: "Web4 Identity" },
    user: {
      id: rootLctIdBytes,
      name: userDisplayName,
      displayName: userDisplayName
    },
    pubKeyCredParams: [
      { alg: -7, type: "public-key" }  // ES256
    ],
    authenticatorSelection: {
      authenticatorAttachment: "cross-platform",
      residentKey: "required",
      userVerification: "required"
    },
    attestation: "direct"
  }
});
```

## 7. Integration with Other Specs

### 7.1 LCT Core Spec

This protocol extends [`LCT-linked-context-token.md`](LCT-linked-context-token.md):
- Adds `device_constellation` to root LCT structure
- Adds `root_attestation` and `cross_device_witnesses` to device LCT
- Extends T3 tensor with `hardware_binding_strength` and `constellation_coherence`

### 7.2 Society Specification

Societies implementing this protocol MUST:
- Support multi-device birth certificate issuance
- Verify hardware attestations for enrolled devices
- Maintain device constellation state in LCT registry
- Enforce recovery quorum for identity recovery

### 7.3 ATP/ADP Cycle

Device operations consume ATP:
- Enrollment ceremony: 10 ATP
- Cross-device witnessing: 1 ATP per pair
- Device removal: 5 ATP
- Recovery ceremony: 20 ATP

## 8. References

- **LCT Core Specification**: [`LCT-linked-context-token.md`](LCT-linked-context-token.md)
- **T3/V3 Tensors**: [`t3-v3-tensors.md`](t3-v3-tensors.md)
- **Society Specification**: [`SOCIETY_SPECIFICATION.md`](SOCIETY_SPECIFICATION.md)
- **ATP/ADP Cycle**: [`atp-adp-cycle.md`](atp-adp-cycle.md)
- **Apple App Attest**: https://developer.apple.com/documentation/devicecheck/establishing_your_app_s_integrity
- **Android Key Attestation**: https://developer.android.com/training/articles/security-key-attestation
- **WebAuthn**: https://www.w3.org/TR/webauthn-2/
- **TPM 2.0 Specification**: https://trustedcomputinggroup.org/resource/tpm-library-specification/

---

**Version**: 1.0.0 (Draft)
**Status**: Core Specification
**Last Updated**: January 13, 2026

*"Identity is not a single point. It is the coherence pattern across all your witnesses."*
