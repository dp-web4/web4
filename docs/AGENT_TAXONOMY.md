# Web4 Agent Taxonomy

**Last Updated**: January 2026

The trust and identity mechanics in Web4 depend fundamentally on what kind of agent is participating. This document defines the three agent types and their lifecycle characteristics.

---

## The Three Agent Types

Web4 recognizes three distinct agent types based on their identity binding:

| Agent Type | Identity Binding | Copyable? | Primary Consequence |
|------------|------------------|-----------|---------------------|
| **Human** | Body (biological) | No | Society ejection |
| **Embodied AI** | Hardware (LCT) | No | Society ejection |
| **Software AI** | Cryptographic | Yes | Reinstantiation rules |

### Key Insight

**Hardware-bound identity creates continuity that software AI lacks.**

Humans and embodied AI (robots, edge devices) share a fundamental characteristic: they cannot be copied. This means:
- Their identity is continuous across time
- Reboot/restart = same entity resumes
- Trust accumulates on a single, verifiable identity
- The "rebirth" concept does not apply

Software AI can be copied, forked, and retrained, creating genuine identity continuity questions that require explicit trust transfer rules.

---

## Human Agents

**Identity**: Body-bound (biological substrate)

**Lifecycle characteristics**:
- Single lifetime, no restart possible
- Energy management through sleep/eating (natural, not reputationally significant)
- Primary consequence: Society ejection (trust below threshold)
- Cross-society visibility: Ejection visible to other societies
- Reintegration path: Demonstrate changed behavior, apply for readmission

**Trust mechanics**:
- Trust accumulates over single lifetime
- Society-specific thresholds for membership
- Ejection from one society doesn't affect membership in others directly
- But ejection is visible and may affect trust in related societies

**Example mappings**:
| Human Event | Web4 Equivalent |
|-------------|-----------------|
| Fired from job | Society ejection (company) |
| Disbarred | Society ejection (legal profession) |
| DUI | Society ejection (driving) → affects related societies (aviation) |
| Criminal record | Visible cross-society trust impact |

---

## Embodied AI Agents

**Identity**: Hardware-bound (LCT tied to physical device)

**Lifecycle characteristics**:
- LCT validates continuous identity
- Cannot be copied (hardware uniqueness)
- Energy crisis = recharge/reboot (same identity resumes)
- Running out of energy has reputational impact ("poor self-management")
- Reboot is NOT rebirth - the bound hardware validates continuity

**Trust mechanics**:
- Same as humans: trust accumulates on single identity
- Society ejection for trust breach
- Energy management affects reputation
- Consistent operation builds reliability trust dimension

**Reputational energy management**:
```
Low energy warning → Expected to manage proactively
Complete shutdown  → "Let itself crash" - reputational hit
Frequent shutdowns → Pattern of poor self-management
Reboot             → Same LCT, same identity, continuous record
```

**Why embodied AI ≈ humans**:
- Hardware binding prevents identity copying/forking
- Like a human passing out and being revived - same person, same record
- Cannot "trust launder" by copying to new hardware
- Energy management is visible and reputation-affecting

---

## Software AI Agents

**Identity**: Cryptographic (keys can be copied with weights)

**Lifecycle characteristics**:
- Can be copied, forked, retrained
- Identity continuity is a genuine question
- Reinstantiation creates new entities (potentially)
- Trust transfer rules determine if accumulated trust carries over

**Trust mechanics**:
- Reinstantiation events require trust continuity verification
- Verified continuity = trust transfers to new instance
- Unverified = new instance starts fresh
- Prevents trust laundering through agent copying

**Reinstantiation events**:
| Event | Identity Question | Trust Transfer |
|-------|-------------------|----------------|
| Copy | Is the copy the same agent? | Requires verification |
| Fork | Are both forks the same agent? | Usually no - trust splits/resets |
| Retrain | Is retrained model the same agent? | Depends on continuity verification |
| Checkpoint restore | Is restored state the same agent? | Usually yes if verified |

**Trust continuity verification**:
```
Reinstantiation event detected
  → Verify hardware chain (if applicable)
  → Verify cryptographic lineage
  → Verify behavioral continuity
  → If all pass: Trust transfers
  → If any fail: New identity, fresh start
```

---

## Society Membership Model

All agent types share the same society membership mechanics:

### Joining a Society
- Receive initial ATP allocation
- Start with neutral trust (society-specific baseline)
- Global identity (LCT) carries cross-society reputation

### Active Membership
- Spend ATP on actions
- Earn ATP from contributions
- Build trust through consistent quality
- Each society tracks local trust score

### Society Ejection
- Trust falls below society's minimum threshold
- Ejected from THAT society only
- Remain active in other societies
- Ejection is globally visible

### Reintegration
- Demonstrate changed behavior in other contexts
- Rebuild reputation over time
- Apply for readmission to ejecting society
- Society evaluates updated trust record

### Cross-Society Effects

Societies are connected, not isolated:

| Effect Type | Example |
|-------------|---------|
| **Direct** | Disbarment → can't practice law anywhere |
| **Indirect** | DUI (driving) → affects pilot's license (aviation) |
| **Informational** | Fired for ethics breach → visible to future employers |

---

## ATP and Resource Exhaustion

ATP exhaustion is distinct from society ejection:

| State | Meaning | Membership Status |
|-------|---------|-------------------|
| **ATP > 0** | Can act | Active member |
| **ATP = 0** | Cannot act temporarily | Still a member |
| **Trust < threshold** | Behavior breach | Ejected from society |

For embodied AI, ATP exhaustion (energy depletion) carries reputational impact but doesn't reset identity.

---

## Implementation Notes

### LCT Format by Agent Type

```
Human:          lct://human:{biometric-hash}@{society}
Embodied AI:    lct://device:{hardware-id}:{tpm-attestation}@{society}
Software AI:    lct://agent:{key-fingerprint}:{lineage-hash}@{society}
```

### Trust Tensor Considerations

T3 dimensions may weight differently by agent type:

| Dimension | Human | Embodied AI | Software AI |
|-----------|-------|-------------|-------------|
| Competence | Standard | Standard | Standard |
| Reliability | Standard | Energy management weighted | Uptime weighted |
| Integrity | Standard | Standard | Lineage verification |
| Consistency | Standard | Reboot recovery | Version consistency |

---

## Summary

The Web4 agent taxonomy recognizes that identity binding fundamentally affects trust mechanics:

- **Humans and embodied AI** share hardware-bound identity, making them similar in lifecycle and trust accumulation
- **Software AI** can be copied/forked, requiring explicit trust continuity rules
- **Society ejection** (not "death") is the primary consequence for trust breach
- **Reintegration** follows the same path humans use: demonstrate change, rebuild trust, apply for readmission
- **Energy management** is reputationally significant for embodied AI but doesn't reset identity

This taxonomy enables Web4 to handle all agent types with appropriate trust mechanics while maintaining the core principle: **trust follows identity, and identity follows binding**.

---

**See also**:
- [LCT Specification](../web4-standard/core-spec/LCT-linked-context-token.md)
- [Trust Tensor (T3)](../web4-standard/core-spec/t3-v3-tensors.md)
- [Society Specification](../web4-standard/core-spec/SOCIETY_SPECIFICATION.md)
