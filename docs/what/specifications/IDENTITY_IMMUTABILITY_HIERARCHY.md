# Identity Immutability Hierarchy
*Web4 Specification — March 8, 2026*

## Core Principle

Identity attributes exist on three tiers with fundamentally different trust semantics:

```
IMMUTABLE       — cannot change without physical hardware swap
CHARACTERISTIC  — changes rarely, requires deliberate action
DYNAMIC         — changes frequently, must be discovered/cached
```

This isn't a data modeling choice — it determines what anchors identity, what describes identity, and what locates identity. Conflating tiers (treating IP as identity, treating hostname as anchor) produces fragile systems that lose track of entities across routine network events.

---

## The Three Tiers

### Tier 1: Immutable
*Cannot change without physical hardware replacement*

| Attribute | Notes |
|-----------|-------|
| TPM Endorsement Key (EK) | Burned at manufacture. Never changes. Never leaves hardware. |
| CPU serial number | Hardware-specific. Survives any software change. |
| Secure Enclave key | Apple platforms (macOS, iOS). Equivalent to TPM EK. |

**Trust semantics**: If the immutable anchor matches, identity is continuous across reboots, OS reinstalls, IP changes, even model changes. If it doesn't match, this is either a hardware swap (new identity needed) or spoofing (reject).

The immutable anchor is what makes an entity recognizably continuous across state transitions — what Synchronism calls persistence through phase transitions. The LCT cryptographic root maps to this tier.

### Tier 2: Characteristic
*Semi-stable. Changes rarely and deliberately.*

| Attribute | Notes |
|-----------|-------|
| MAC address | Stable per NIC. Changes on NIC swap or virtualisation. |
| Hostname | Admin-changeable. Should match machine name by convention. |
| GPU UUID | Stable across reboots. Changes if GPU is replaced. |

**Trust semantics**: Characteristic attributes are fingerprints. If MAC doesn't match but immutable anchor does, that's a hardware change event — update the characteristic layer, trust continues. If MAC matches but immutable doesn't, something is wrong.

### Tier 3: Dynamic
*Changes frequently. Must be cached as "last known" and rediscovered.*

| Attribute | Notes |
|-----------|-------|
| IP address | DHCP, network changes, VPN. Not an identity property. |
| Port | Configurable, can change per session. |
| Current model | Changes frequently. |
| Session state | Ephemeral by definition. |

**Trust semantics**: Dynamic attributes are *presence*, not *identity*. An IP change is not an identity event. A machine with a new IP but matching immutable anchor is the same machine. Dynamic attribute staleness should reduce effective trust weight — stale location data is not the same as stale identity.

---

## Mapping to Web4 Vocabulary

| Tier | Web4 Concept | Trust Role |
|------|-------------|------------|
| Immutable | LCT cryptographic root | Identity continuity anchor |
| Characteristic | LCT context attributes | Fingerprint, witness evidence |
| Dynamic | LCT presence/context | Reachability, not identity |

The Web4 equation binds identity through the LCT:

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

The LCT's cryptographic root is the immutable anchor. The characteristic layer provides RDF-queryable identity context. The dynamic layer carries presence state that decays and must be rediscovered.

**Key principle**: IP address is a presence attribute, not an identity attribute. The LCT anchors identity at the immutable layer. Presence (where to reach the entity right now) is discovered dynamically. These must never be conflated.

---

## LCT Attribute Struct Extension

To formally model the hierarchy in `web4-core`, add three attribute types to the `Lct` struct:

```rust
pub struct ImmutableAttributes {
    pub tpm_ek: Option<String>,
    pub cpu_serial: Option<String>,
    pub secure_enclave_key: Option<String>,
    pub genesis_timestamp: Option<String>,
    pub canonical_anchor: Option<String>,
}

pub struct CharacteristicAttributes {
    pub mac_address: Option<String>,
    pub hostname: Option<String>,
    pub gpu_uuid: Option<String>,
    pub last_verified: Option<String>,
}

pub struct DynamicAttributes {
    pub ip_address: Option<String>,
    pub port: Option<u16>,
    pub current_model: Option<String>,
    pub session_id: Option<String>,
    pub last_known_timestamp: Option<String>,
    pub cache_ttl_seconds: Option<u64>,
}
```

Add to `Lct`:
```rust
pub immutable_attributes: Option<ImmutableAttributes>,
pub characteristic_attributes: Option<CharacteristicAttributes>,
pub dynamic_attributes: Option<DynamicAttributes>,
```

Add to `HardwareBinding`:
```rust
pub immutable_component: Option<ImmutableBindingComponent>,
```

Where `ImmutableBindingComponent` distinguishes which tier the binding actually anchors to — a binding to a TPM EK is categorically stronger than a binding to a MAC address.

---

## Trust Computation Implications

1. **Immutable anchor mismatch → hard rejection**: If the TPM EK doesn't match, this is not the same entity. Trust does not transfer.

2. **Characteristic mismatch with immutable match → hardware event**: Log it, update the characteristic layer, trust continues. This is a legitimate state transition.

3. **Dynamic attribute staleness → trust decay**: Old IP data, stale model info, expired session state reduces the *effective* trust weight of dynamic claims. Don't treat a 24-hour-old last-seen-IP the same as a 30-second-old one.

4. **T3 dimensions bind differently per tier**:
   - Talent/Training: grounded in immutable identity (the capability profile of this specific hardware)
   - Temperament: weighted by characteristic attributes (behavioral fingerprint)
   - Dynamic state: modulates V3 (Valuation/Veracity/Validity) of real-time claims

---

## Synthon Framing

A synthon's identity persists through phase transitions. Dynamic attributes are phase-transition variables. The immutable layer is what makes the synthon recognizably continuous across transitions.

The Hill function insight applies here: selective binding at the immutable tier (TPM verification) creates the cooperative binding threshold that distinguishes genuine identity continuity from coincidental attribute overlap. You can't derive the critical threshold analytically — it's empirical, just like p_crit in the coupling-coherence experiment.

---

## Related Documents

- `web4-core/src/lct.rs` — implementation target (Phase 3)
- `hardbound/docs/HARDWARE_BINDING_IDENTITY.md` — enterprise implementation
- `SAGE/sage/federation/fleet.json` — operational three-tier example (v3)
- `private-context/designs/identity-immutability-hierarchy.md` — full design doc with implementation plan
- `Synchronism/Research/Coupling_Coherence_Experiment.md` — p_crit empirical grounding
