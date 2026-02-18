# LCT Documentation Index

**Last Updated**: February 5, 2026

LCT (Linked Context Token) documentation is distributed across multiple files. This index provides a roadmap.

---

## Start Here

| Document | Purpose | Audience |
|----------|---------|----------|
| [LCT_UNIFIED_IDENTITY_SPECIFICATION.md](../what/specifications/LCT_UNIFIED_IDENTITY_SPECIFICATION.md) | **Canonical spec** for cross-system LCT format | Implementers |
| [GLOSSARY.md](GLOSSARY.md) | Quick definition of LCT and related terms | Everyone |
| [web4-standard/core-spec/LCT-linked-context-token.md](../../web4-standard/core-spec/LCT-linked-context-token.md) | Core protocol specification | Protocol designers |

---

## Specifications

### Core Protocol
| File | Description |
|------|-------------|
| [`web4-standard/core-spec/LCT-linked-context-token.md`](../../web4-standard/core-spec/LCT-linked-context-token.md) | Original LCT specification |
| [`web4-standard/core-spec/multi-device-lct-binding.md`](../../web4-standard/core-spec/multi-device-lct-binding.md) | **Multi-device binding protocol** (Jan 2026) |
| [`LCT_UNIFIED_IDENTITY_SPECIFICATION.md`](../what/specifications/LCT_UNIFIED_IDENTITY_SPECIFICATION.md) | Cross-system identity format (Dec 2025) |
| [`web4-standard/implementation/act_deployment/LCT_SPECIFICATION.md`](../../web4-standard/implementation/act_deployment/LCT_SPECIFICATION.md) | ACT blockchain integration spec |

### Permissions & Authorization
| File | Description |
|------|-------------|
| [`LCT_UNIFIED_PERMISSION_STANDARD.md`](../what/specifications/LCT_UNIFIED_PERMISSION_STANDARD.md) | Permission model specification |
| [`archive/game-prototype/engine/LCT_DATABASE_SCHEMA.md`](../../archive/game-prototype/engine/LCT_DATABASE_SCHEMA.md) | Database schema for LCT storage (archived) |

### Integration Patterns
| File | Description |
|------|-------------|
| [`web4-standard/implementation/LCT_MINTING_PATTERNS.md`](../../web4-standard/implementation/LCT_MINTING_PATTERNS.md) | Patterns for creating new LCTs |
| [`lct_witnessed_presence.md`](../why/lct_witnessed_presence.md) | How presence accumulates through witnessing |
| [`entity_binding_hierarchy.md`](../how/entity_binding_hierarchy.md) | Multi-level binding patterns |
| [`binding_pairing_witnessing_broadcast.md`](../why/binding_pairing_witnessing_broadcast.md) | Relationship mechanisms |

---

## Implementation

### Game Engine (Archived - was prototype, now see 4-life)
| File | Description |
|------|-------------|
| [`archive/game-prototype/engine/lct.py`](../../archive/game-prototype/engine/lct.py) | Core LCT class |
| [`archive/game-prototype/engine/lct_identity.py`](../../archive/game-prototype/engine/lct_identity.py) | Identity management |
| [`archive/game-prototype/engine/lct_permissions.py`](../../archive/game-prototype/engine/lct_permissions.py) | Permission checking |
| [`archive/game-prototype/engine/lct_unified_permissions.py`](../../archive/game-prototype/engine/lct_unified_permissions.py) | Unified permission model |
| [`archive/game-prototype/engine/identity_registry.py`](../../archive/game-prototype/engine/identity_registry.py) | LCT registry |
| [`archive/game-prototype/engine/identity_consensus.py`](../../archive/game-prototype/engine/identity_consensus.py) | Consensus on identity state |
| [`archive/game-prototype/engine/identity_stake_system.py`](../../archive/game-prototype/engine/identity_stake_system.py) | Economic Sybil resistance |

### SAGE Integration
| File | Description |
|------|-------------|
| [`archive/game-prototype/engine/sage_lct_integration.py`](../../archive/game-prototype/engine/sage_lct_integration.py) | Edge device LCT patterns |
| [`archive/game-prototype/engine/sage_web4_bridge.py`](../../archive/game-prototype/engine/sage_web4_bridge.py) | Cross-system coordination |

### Reference Implementation
| File | Description |
|------|-------------|
| [`web4-standard/implementation/reference/authorization_lct_integration.py`](../../web4-standard/implementation/reference/authorization_lct_integration.py) | Authorization + LCT integration |

---

## Phase Completion Reports

These documents track the implementation progress of the LCT presence system:

| Phase | Document | Status |
|-------|----------|--------|
| Phase 1 | Core identity | Complete |
| Phase 2 | [`LCT_IDENTITY_PHASE2_COMPLETE.md`](../what/specifications/LCT_IDENTITY_PHASE2_COMPLETE.md) | Complete |
| Phase 3 | [`LCT_IDENTITY_PHASE3_COMPLETE.md`](../what/specifications/LCT_IDENTITY_PHASE3_COMPLETE.md) | Complete |
| Phase 4 | ATP Integration | Complete |
| E2E | [`LCT_E2E_INTEGRATION_COMPLETE.md`](../what/specifications/LCT_E2E_INTEGRATION_COMPLETE.md) | Complete |

---

## LCT URI Format

The unified LCT format for cross-system identity:

```
lct://{component}:{instance}:{role}@{network}
```

**Examples**:
```
lct://sage:thor-001:expert@mainnet      # SAGE expert on mainnet
lct://act:validator-5:node@testnet      # ACT validator on testnet
lct://web4:society-alpha:member@local   # Web4 society member locally
```

**Components**:
- `component`: System type (sage, act, web4)
- `instance`: Specific instance identifier
- `role`: Functional role within the system
- `network`: Network/environment (mainnet, testnet, local)

---

## Demo Scripts (Archived)

| Script | What It Tests |
|--------|--------------|
| `archive/game-prototype/run_lct_e2e_integration_test.py` | Full LCT presence system |
| `archive/game-prototype/run_sage_lct_integration_test.py` | SAGE edge device patterns |
| `archive/game-prototype/run_identity_consensus_test.py` | Identity consensus |

---

## Related Documentation

- [GLOSSARY.md](GLOSSARY.md) - Term definitions
- [STATUS.md](../../STATUS.md) - Overall project status
- [archive/game-prototype/ARCHIVED.md](../../archive/game-prototype/ARCHIVED.md) - Game prototype archive

---

**Canonical specification**: [`LCT_UNIFIED_IDENTITY_SPECIFICATION.md`](../what/specifications/LCT_UNIFIED_IDENTITY_SPECIFICATION.md)
