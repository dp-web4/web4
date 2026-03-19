# Attestation Envelope — Unified Hardware Trust Primitive

**Status**: Draft v0.1
**Date**: 2026-03-18
**Scope**: Web4, SAGE, Hardbound — shared across all three repos
**Patent alignment**: US 11,477,027 / US 12,278,913 / US App 19/178,619

## Purpose

One data structure that any verifier can use to answer: **"Is this entity who it claims to be, on hardware it claims to be on, in a state I can trust?"**

The envelope normalizes across hardware anchor types (TPM 2.0, FIDO2/YubiKey, Secure Enclave, software fallback) so that consumers never need to know which hardware produced the attestation. The envelope is the **dictionary entity for hardware trust** — the same pattern as ModelAdapter for model communication and T3/V3 for entity trust.

## Design Principles

1. **Anchor-agnostic consumers.** The verifier sees one envelope shape regardless of hardware. Anchor-specific logic lives in the producer (signer) and the anchor-specific verification module, not in the consumer.

2. **Layered trust, not binary.** Different anchors produce different trust ceilings. A TPM+PCR attestation earns higher trust than a software-only signature. The envelope carries the ceiling; the consumer decides what to require.

3. **Freshness is first-class.** An attestation without a recent nonce is a photocopy. Challenge-response freshness is mandatory, not optional.

4. **Platform state when available.** TPM can provide PCR quotes. FIDO2 can provide authenticator data. SE can provide attestation objects. The envelope carries what's available and marks what's absent.

5. **Patent-aligned fields.** Fields map directly to patent language: controlled object, access data, placing into use, association of identifiable records.

## The Envelope

```typescript
interface AttestationEnvelope {
  // === WHO ===
  entity_id: string;           // LCT ID (e.g., "lct://sage:cbp:agent@raising")
  public_key: string;          // PEM or JWK — the key being attested
  public_key_fingerprint: string; // SHA-256 of public key for quick lookup

  // === WHAT ===
  anchor: {
    type: 'tpm2' | 'fido2' | 'secure_enclave' | 'software';
    manufacturer?: string;     // TPM manufacturer, authenticator AAGUID, etc.
    model?: string;            // Hardware model identifier
    firmware_version?: string; // When available
  };

  // === PROOF ===
  proof: {
    format: 'tpm2_quote' | 'fido2_assertion' | 'se_attestation' | 'ecdsa_software';
    signature: string;         // Base64-encoded signature over challenge
    challenge: string;         // The nonce that was signed (freshness)
    attestation_object?: string; // Raw attestation from hardware (Base64)
    // TPM-specific
    pcr_digest?: string;       // SHA-256 of selected PCRs
    pcr_selection?: number[];  // Which PCRs were included
    // FIDO2-specific
    authenticator_data?: string; // CBOR authenticator data
    client_data_hash?: string;
  };

  // === WHEN ===
  timestamp: number;           // Unix seconds — when this envelope was created
  challenge_issued_at: number; // When the verifier issued the challenge
  challenge_ttl: number;       // Seconds — how long the challenge is valid

  // === WHERE (platform state) ===
  platform_state: {
    available: boolean;        // Whether platform state could be collected
    boot_verified?: boolean;   // Secure boot status
    pcr_values?: Record<number, string>; // PCR index → hex digest
    os_version?: string;
    kernel_version?: string;
  };

  // === TRUST ===
  trust_ceiling: number;       // [0, 1] — max trust this anchor type allows
  // TPM2 = 1.0, FIDO2 = 0.9, SE = 0.85, software = 0.4

  // === METADATA ===
  envelope_version: string;    // "0.1"
  issuer?: string;             // Who produced this envelope (machine name, instance ID)
  purpose?: string;            // Why this attestation was produced
  // "enrollment" | "session_start" | "re_attestation" | "witness" | "migration"
}
```

## Trust Ceilings by Anchor Type

| Anchor | Trust Ceiling | Rationale |
|--------|--------------|-----------|
| `tpm2` + PCR | 1.0 | Hardware-bound key, measured boot, non-exportable |
| `tpm2` (no PCR) | 0.85 | Hardware-bound key but boot state not verified |
| `fido2` | 0.9 | Hardware-bound, user-presence verified, but no platform state |
| `secure_enclave` | 0.85 | Hardware-backed, but attestation format varies |
| `software` | 0.4 | Filesystem key — copyable, no hardware binding |

These ceilings are the max. Actual trust is `min(ceiling, earned_trust_from_behavior)`.

## Verification

A verifier checks:

1. **Freshness**: `challenge_issued_at + challenge_ttl > now` — reject stale attestations
2. **Signature**: verify `proof.signature` against `public_key` using `proof.format`-specific logic
3. **Challenge**: confirm the signed challenge matches one the verifier issued
4. **Platform state** (if required): check PCR values against policy
5. **Trust ceiling**: apply the ceiling based on anchor type
6. **Entity**: confirm `entity_id` matches the expected entity

The verifier does NOT need to know the anchor-specific verification details — those are encapsulated in anchor-type verification modules.

## Anchor-Type Verification Modules

Each anchor type has a verification module that knows how to:
- Validate the proof format
- Check hardware-specific attestation objects
- Extract platform state
- Determine the appropriate trust ceiling

```
web4/
  trust/
    attestation/
      envelope.py          # AttestationEnvelope dataclass
      verify.py            # verify_envelope(envelope, challenge) → VerificationResult
      anchors/
        tpm2.py            # TPM 2.0 specific verification
        fido2.py           # FIDO2/WebAuthn specific verification
        secure_enclave.py  # Apple SE specific verification
        software.py        # Software-only fallback verification
```

## How Each Repo Uses It

### SAGE — Identity authorization

```python
# On startup: produce attestation, unseal identity
envelope = create_attestation(
    entity_id=instance.lct_id,
    anchor=detect_hardware_anchor(),
    challenge=generate_challenge(),
    purpose='session_start',
)
identity_secret = unseal_with_attestation(envelope)
# identity_secret is now available in memory for signing

# On federation: send envelope to peers
peer.send_attestation(envelope)
```

The three-layer identity split:
- `identity.json` → public manifest (references envelope)
- `identity.sealed` → hardware-gated secret (unseals only with valid attestation)
- `identity.attest.json` → cached attestation envelope

### Hardbound — Governance verification

```python
# On bind: verify hardware and create governed actor
envelope = request_attestation(actor, challenge)
result = verify_envelope(envelope, challenge)
if result.trust_ceiling < required_ceiling:
    reject("hardware anchor insufficient for this role")
actor.bind(envelope)

# On action authorization: check attestation freshness
if envelope.timestamp < now - MAX_ATTESTATION_AGE:
    require_re_attestation(actor)
```

### Web4 — Entity trust computation

```python
# Trust from attestation feeds into T3/V3
t3.talent = min(t3.talent, envelope.trust_ceiling)
# Hardware ceiling caps the talent dimension

# Device constellation trust
constellation_trust = geometric_mean([
    device.envelope.trust_ceiling
    for device in constellation.active_devices
])
```

## Patent Mapping

| Patent Concept | Envelope Field(s) |
|---------------|-------------------|
| Controlled object | `entity_id`, `anchor.*` |
| Access data | `public_key`, `proof.*` |
| Authentication controller | Verification logic + `trust_ceiling` |
| Placing into use | `purpose='session_start'` + successful verification |
| Identifiable record association | Two envelopes cross-signed + `purpose='witness'` |
| Communication between records | Mutual attestation + session key derivation |

## Freshness Model

Attestation freshness decays over time:

```
effective_trust = trust_ceiling × freshness_factor
freshness_factor = max(0, 1 - (now - timestamp) / max_age)
```

Default `max_age` by purpose:
- `session_start`: 8 hours
- `re_attestation`: 24 hours
- `witness`: 1 hour
- `enrollment`: one-time (verified at enrollment, then trust tracks independently)

## Migration and Recovery

When a device is lost or replaced:

1. New device creates its own attestation envelope
2. Existing constellation devices cross-witness the new enrollment
3. Recovery quorum (N of M existing devices) must attest
4. Old device's envelope is revoked — its trust ceiling drops to 0
5. New device inherits the entity's earned trust (not the ceiling — that comes from its own hardware)

This ensures identity portability works the way SAGE already demonstrated (Sprout → CBP transfer) but with hardware-gated security instead of plaintext file copying.

## Version History

- **v0.1** (2026-03-18): Initial draft. Defines envelope structure, trust ceilings, verification flow, repo usage patterns, and patent mapping.
