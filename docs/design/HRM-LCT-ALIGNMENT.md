# HRM LCT Alignment Requirements

**Status**: Migration Guide v1.0
**Date**: 2026-01-03
**Author**: CBP Session (Dennis + Claude)
**Purpose**: Align HRM LCT implementations with Web4 canonical specification

---

## Issue Summary

HRM currently has **three different LCT implementations** that diverge from the Web4 canonical specification:

| Location | Current Format | Interpretation |
|----------|----------------|----------------|
| `sage/core/lct_identity_integration.py` | `lct:web4:agent:{lineage}@{context}#{task}` | "Lineage-Context-Task" |
| `sage/web4/lct_identity.py` | `lct://{component}:{instance}:{role}@{network}` | URI-style |
| `sage/core/simulated_lct_identity.py` | Ad-hoc ID generation | Machine-bound keys |

**Correct Format** (Web4 canonical):
```
lct:web4:{entity_type}:{hash}
```

**Correct Structure** (Web4 canonical):
```json
{
  "lct_id": "lct:web4:ai:abc123...",
  "capability_level": 3,
  "entity_type": "ai",
  "binding": {...},
  "mrh": {...},
  "t3_tensor": {...},
  "v3_tensor": {...}
}
```

---

## Alignment Requirements

### 1. Terminology Consistency

**All HRM LCT implementations MUST use these terms exactly:**

| Term | Meaning | Never Use |
|------|---------|-----------|
| **LCT** | Linked Context Token | "Lifecycle-Continuous Trust", "Lineage-Context-Task" |
| **T3** | Trust Tensor (6 dims) | T3 = Talent/Training/Temperament (old 3-dim version) |
| **V3** | Value Tensor (6 dims) | V3 = Valuation/Veracity/Validity (old 3-dim version) |
| **MRH** | Markov Relevancy Horizon | "Relevancy Horizon", "Context Horizon" |

### 2. T3 Tensor Dimensions (REQUIRED)

All implementations MUST use these 6 dimensions:

```python
T3_DIMENSIONS = [
    "technical_competence",   # Can entity perform claimed capabilities?
    "social_reliability",     # Does entity honor commitments?
    "temporal_consistency",   # Is behavior consistent over time?
    "witness_count",          # How many entities witness this? (normalized)
    "lineage_depth",          # How deep is trust lineage? (normalized)
    "context_alignment"       # How well aligned with current context?
]
```

**Migration from old 3-dimension T3 (Talent/Training/Temperament):**
```python
def migrate_t3_old_to_new(old_t3):
    """Migrate from old 3-dim to new 6-dim T3."""
    return {
        "technical_competence": old_t3.get("training", 0.5),
        "social_reliability": old_t3.get("temperament", 0.5),
        "temporal_consistency": old_t3.get("temperament", 0.5),
        "witness_count": 0.1,  # Initialize low
        "lineage_depth": 0.1,  # Initialize low
        "context_alignment": old_t3.get("talent", 0.5)
    }
```

### 3. V3 Tensor Dimensions (REQUIRED)

All implementations MUST use these 6 dimensions:

```python
V3_DIMENSIONS = [
    "energy_balance",         # ATP/ADP balance (integer)
    "contribution_history",   # Historical value contributions (0-1)
    "resource_stewardship",   # How well entity manages resources (0-1)
    "network_effects",        # Value created for others (0-1)
    "reputation_capital",     # Accumulated social capital (0-1)
    "temporal_value"          # Value persistence over time (0-1)
]
```

### 4. Capability Levels (REQUIRED)

All LCT implementations MUST declare capability level:

```python
class CapabilityLevel(IntEnum):
    STUB = 0       # Placeholder reference
    MINIMAL = 1    # Self-issued bootstrap
    BASIC = 2      # Operational with relationships
    STANDARD = 3   # Full tensors and attestations
    FULL = 4       # Society-issued with birth certificate
    HARDWARE = 5   # Hardware-bound identity
```

### 5. Entity Types (REQUIRED)

Use canonical entity types:

```python
CORE_ENTITY_TYPES = [
    "human", "ai", "organization", "role", "task",
    "resource", "device", "service", "oracle",
    "accumulator", "dictionary", "hybrid"
]

EXTENDED_ENTITY_TYPES = [
    "plugin", "session", "relationship", "pattern",
    "society", "witness", "pending"
]
```

---

## File-by-File Migration

### 1. `sage/core/lct_identity_integration.py`

**Current Issues:**
- Uses "Lineage-Context-Task" interpretation
- Format: `lct:web4:agent:{lineage}@{context}#{task}`
- Incompatible with canonical LCT structure

**Required Changes:**

```python
# BEFORE (incorrect)
class LCTIdentity:
    def __init__(self, lineage: str, context: str, task: str):
        self.lct_id = f"lct:web4:agent:{lineage}@{context}#{task}"

# AFTER (correct)
from web4.core.lct_capability_levels import (
    LCT, CapabilityLevel, EntityType, create_minimal_lct
)

class LCTIdentity:
    def __init__(self, entity_type: EntityType = EntityType.AI,
                 level: CapabilityLevel = CapabilityLevel.STANDARD):
        self._lct = create_minimal_lct(
            entity_type=entity_type,
            level=level,
            name="sage-agent"
        )

    @property
    def lct_id(self) -> str:
        return self._lct.lct_id
```

**Backward Compatibility:**
- Keep old methods but deprecate
- Parse old format and migrate to new structure
- Log warning when old format detected

### 2. `sage/web4/lct_identity.py`

**Current Issues:**
- Uses URI-style format: `lct://{component}:{instance}:{role}@{network}`
- Has good validation logic but wrong format
- Contains useful parsing utilities

**Required Changes:**

```python
# BEFORE (incorrect)
def construct_lct(component: str, instance: str, role: str, network: str) -> str:
    return f"lct://{component}:{instance}:{role}@{network}"

# AFTER (correct)
def construct_lct(entity_type: EntityType, name: str,
                  level: CapabilityLevel = CapabilityLevel.MINIMAL) -> LCT:
    """Create LCT with proper canonical format."""
    return create_minimal_lct(
        entity_type=entity_type,
        level=level,
        name=name
    )
```

**Preserve:**
- Validation logic (adapt to new format)
- Parsing utilities (for migration)
- Error handling patterns

### 3. `sage/core/simulated_lct_identity.py`

**Current Status:**
- Good machine fingerprinting
- Good signing/verification
- Compatible API design
- Uses Ed25519 keys

**Required Changes:**
- Integrate with `LCT` class from capability levels
- Use canonical T3/V3 tensors
- Add capability level support
- Rename class to avoid "simulated" confusion

```python
# BEFORE
class SimulatedLCTIdentity:
    def __init__(self):
        ...

# AFTER
class LCTIdentityProvider:
    """
    LCT Identity Provider for SAGE.

    Provides cryptographic identity with software keys.
    Drop-in replacement for TPM version coming later.
    """
    def __init__(self, capability_level: CapabilityLevel = CapabilityLevel.STANDARD):
        self.capability_level = capability_level
        ...

    def create_identity(self, entity_type: EntityType, name: str) -> LCT:
        """Create new LCT with cryptographic binding."""
        lct = create_minimal_lct(
            entity_type=entity_type,
            level=self.capability_level,
            name=name
        )
        # Add binding with generated key
        lct.binding.public_key = self._generate_public_key()
        lct.binding.binding_proof = self._sign_binding(lct)
        return lct
```

---

## IRP Plugin LCT Integration

IRP plugins SHOULD have LCTs at Level 1 or 2:

### Plugin Registration

```python
class IRPPlugin:
    def __init__(self, name: str, orchestrator_lct: str):
        # Create Level 2 plugin LCT
        self.lct = create_minimal_lct(
            entity_type=EntityType.PLUGIN,
            level=CapabilityLevel.BASIC,
            name=name,
            parent_lct=orchestrator_lct
        )

        # Set plugin capabilities
        self.lct.policy.capabilities = [
            "execute:irp",
            "read:patterns"
        ]

    def update_trust_from_refinement(self, success: bool, iterations: int):
        """Update T3 based on IRP refinement success."""
        if success:
            self.lct.t3_tensor.technical_competence = min(1.0,
                self.lct.t3_tensor.technical_competence + 0.01)
            self.lct.t3_tensor.temporal_consistency = min(1.0,
                self.lct.t3_tensor.temporal_consistency + 0.005)
        else:
            self.lct.t3_tensor.technical_competence = max(0.0,
                self.lct.t3_tensor.technical_competence - 0.02)

        self.lct.t3_tensor.recompute_composite()
```

### Plugin Discovery

```python
def discover_plugin_capabilities(plugin_lct_id: str) -> Dict:
    """Query a plugin's capabilities before trusting it."""
    plugin_lct = lct_registry.get(plugin_lct_id)
    if not plugin_lct:
        return {"error": "Plugin not found"}

    caps = query_capabilities(plugin_lct)

    return {
        "plugin_id": plugin_lct_id,
        "capability_level": caps.capability_level.name,
        "trust_tier": caps.trust_tier,
        "can_pair_with": caps.can_pair_with,
        "t3_score": caps.composite_t3
    }
```

---

## Capability Query for Cross-Domain Communication

When HRM entities communicate with Web4 entities:

```python
async def establish_federation_trust(local_lct: LCT, remote_lct_id: str):
    """Establish trust relationship with remote entity."""

    # 1. Query remote capabilities
    remote_caps = await federation.query_capabilities(remote_lct_id)

    # 2. Find common capability level
    common_level = min(local_lct.capability_level, remote_caps.capability_level)

    # 3. Validate compatibility
    if common_level < CapabilityLevel.BASIC:
        raise InsufficientCapabilityError(
            f"Cannot federate with Level {common_level} entity"
        )

    # 4. Check relationship support
    if "ai" not in remote_caps.can_pair_with:
        raise RelationshipNotSupportedError(
            f"Remote entity cannot pair with AI agents"
        )

    # 5. Establish pairing
    local_lct.mrh.add_paired(
        remote_lct_id,
        subtype="federation",
        permanent=False
    )

    return {
        "status": "paired",
        "common_level": common_level,
        "remote_trust_tier": remote_caps.trust_tier
    }
```

---

## Stub Support for Reduced Implementations

IRP plugins MAY use stub components:

```python
# Level 1 plugin with stubs
plugin_lct = LCT(
    lct_id="lct:web4:plugin:vision-irp",
    capability_level=CapabilityLevel.MINIMAL,
    entity_type=EntityType.PLUGIN,

    # Minimal binding
    binding=LCTBinding(entity_type="plugin", public_key="..."),

    # Empty MRH
    mrh=MRH(),

    # Minimal T3
    t3_tensor=T3Tensor.create_minimal(),

    # Zero V3
    v3_tensor=V3Tensor.create_zero(),

    # Stub birth certificate (not applicable to plugins)
    birth_certificate=BirthCertificate.create_stub("Plugins don't have birth certificates")
)
```

---

## Migration Timeline

### Phase 1: Alignment (Immediate)
1. Import `lct_capability_levels.py` into HRM
2. Create adapter layer for existing code
3. Add deprecation warnings to old functions

### Phase 2: Refactor (Next Session)
1. Refactor `lct_identity_integration.py`
2. Refactor `lct_identity.py`
3. Update `simulated_lct_identity.py`

### Phase 3: Integration (Future)
1. Connect to Web4 federation
2. Implement capability discovery
3. Add hardware binding support

---

## Testing

### Validation Tests

```python
def test_lct_level_validation():
    """Test that LCT meets claimed level requirements."""
    lct = create_minimal_lct(
        entity_type=EntityType.PLUGIN,
        level=CapabilityLevel.BASIC
    )

    result = validate_lct_level(lct)
    assert result.valid, f"Validation failed: {result.errors}"
    assert result.current_level >= CapabilityLevel.BASIC

def test_capability_query():
    """Test capability discovery protocol."""
    lct = create_minimal_lct(
        entity_type=EntityType.AI,
        level=CapabilityLevel.STANDARD
    )

    caps = query_capabilities(lct)
    assert caps.capability_level == CapabilityLevel.STANDARD
    assert caps.t3_implemented
    assert "plugin" in caps.can_witness
```

### Migration Tests

```python
def test_old_format_migration():
    """Test migration from old LCT format."""
    old_lct_id = "lct:web4:agent:thor@sage#consciousness"

    new_lct = migrate_lct_from_old_format(old_lct_id)

    assert new_lct.lct_id.startswith("lct:web4:")
    assert new_lct.entity_type == EntityType.AI
    assert new_lct.capability_level >= CapabilityLevel.MINIMAL
```

---

## References

- **LCT Capability Levels**: `docs/design/LCT-CAPABILITY-LEVELS.md`
- **Reference Implementation**: `core/lct_capability_levels.py`
- **Web4 LCT Spec**: `web4-standard/core-spec/LCT-linked-context-token.md`
- **PSI Proposal**: `proposals/PATTERN_SOURCE_IDENTITY.md`

---

**Version**: 1.0.0
**Status**: Migration Guide
**Last Updated**: 2026-01-03

*"Terminology is sacred. Implementation is flexible. Both must be consistent."*
