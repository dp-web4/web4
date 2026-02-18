# LCT Minting Implementation Patterns

## Date: January 17, 2025
## Source: ACT Blockchain Implementation

## Overview

Linked Context Tokens (LCTs) are the foundation of Web4 identity. Through implementation, we've discovered key patterns for minting and managing LCTs that maintain their verifiable nature while enabling practical operations.

## Entity Type Taxonomy

### Core Entity Types
Through implementation, we identified fundamental entity categories:

```go
validTypes := map[string]bool{
    "agent":   true,  // Software/AI entities
    "human":   true,  // Human participants
    "device":  true,  // Hardware/IoT devices
    "service": true,  // API endpoints, data sources
    "swarm":   true,  // Collective entities
}
```

### Special Entity Types
- **producer**: Energy generation entities (solar, wind, etc.)
  - High default trust scores
  - Validation requirements for energy claims
  - Special role in ADP→ATP conversion

## LCT ID Generation Pattern

### Deterministic and Unique
```go
// Format: lct-{type}-{name}-{timestamp_nano}
lctId := fmt.Sprintf("lct-%s-%s-%d",
    entityType,
    entityName,
    time.Now().UnixNano())
```

### Why This Pattern Works
1. **Type prefix**: Immediately identifies entity category
2. **Name component**: Human-readable identifier
3. **Nanosecond timestamp**: Ensures uniqueness even for rapid minting
4. **Deterministic**: Can be reconstructed if needed

## Address Derivation

### From LCT ID to Blockchain Address
```go
// Derive address from LCT ID hash
hash := sha256.Sum256([]byte(lctId))
entityAddress := sdk.AccAddress(hash[:20]).String()
```

### Properties
- **Deterministic**: Same LCT always produces same address
- **Collision-resistant**: SHA256 ensures unique addresses
- **Verifiable**: Anyone can verify address matches LCT ID
- **Chain-agnostic**: Pattern works across different blockchains

## Initial Resource Allocation

### ADP Token Assignment
```go
// Default ADP allocation if not specified
adpAmount := msg.InitialAdpAmount
if adpAmount == "" {
    adpAmount = "1000"  // Default society allocation
}
```

### Allocation Principles
- All entities start with ADP (discharged) tokens
- Amount represents society's investment in entity
- No ATP initially (must be earned through value creation)
- Allocation from society pool, not minted

## Metadata Storage Pattern

### Flexible Capability Declaration
```go
// Store metadata as JSON in AuthorizationRules field
if len(msg.Metadata) > 0 {
    metadataStr := "{"
    for k, v := range msg.Metadata {
        metadataStr += fmt.Sprintf(`"%s":"%s",`, k, v)
    }
    metadataStr = metadataStr[:len(metadataStr)-1] + "}"
    lct.AuthorizationRules = metadataStr
}
```

### Common Metadata Fields
- **capabilities**: What the entity can do
- **swarm_role**: Position in collective
- **hardware_id**: Physical device binding
- **api_endpoints**: Service access points
- **trust_anchors**: Initial trust relationships

## LCT State Management

### Status Progression
```go
// Typical lifecycle states
"pending"    → Initial creation
"active"     → Operational entity
"suspended"  → Temporarily disabled
"terminated" → Permanently deactivated
```

### Trust Anchor Pattern
```go
lct.TrustAnchor = creator.String()
```
- Creator becomes initial trust anchor
- Establishes responsibility chain
- Enables permission delegation

## Operational Context

### Context String Pattern
```go
// Format: {type}:{identifier}
lct.OperationalContext = fmt.Sprintf("%s:%s",
    msg.EntityType,
    msg.EntityName)
```

### Context Uses
- Quick entity categorization
- Filtering and searching
- Permission evaluation
- Relationship matching

## Event Emission

### Minting Event Pattern
```go
sdk.NewEvent("lct_minted",
    sdk.NewAttribute("lct_id", lctId),
    sdk.NewAttribute("entity_name", msg.EntityName),
    sdk.NewAttribute("entity_type", msg.EntityType),
    sdk.NewAttribute("entity_address", entityAddress),
    sdk.NewAttribute("adp_balance", adpAmount),
    sdk.NewAttribute("creator", creator.String()),
)
```

### Event Importance
- Creates auditable minting history
- Enables off-chain indexing
- Supports monitoring/analytics
- Provides transparency

## Integration with Other Systems

### T3/V3 Tensor Initialization
```go
// TODO: Initialize trust/value tensors
// trusttensor.InitializeT3(lctId, initialTrustVector)
// trusttensor.InitializeV3(lctId, initialValueVector)
```

Currently placeholder, but structure ready for:
- Initial trust scores based on creator
- Value potential based on entity type
- Capability-based tensor initialization

### Energy Cycle Integration
```go
// Entity immediately eligible for energy operations
// Can request ATP from society pool
// Can discharge ATP for work
// V3 tracking begins with first operation
```

## Security Considerations

### Preventing Duplicate LCTs
```go
// Check for existing LCT before minting
if _, found := ms.Keeper.GetLinkedContextToken(ctx, lctId); found {
    return nil, errors.Wrapf(types.ErrLctExists,
        "LCT already exists: %s", lctId)
}
```

### Entity Type Validation
- Strict whitelist of allowed types
- Prevents arbitrary entity categories
- Maintains semantic clarity

### Creator Authorization
- Only valid blockchain addresses can mint
- Creator becomes trust anchor
- Establishes accountability chain

## Discovered Patterns

### 1. Swarm Entity Minting
Swarms can mint collective LCTs representing group identity:
```
lct-swarm-research_team-1737142857
```
Individual agents maintain separate LCTs but reference swarm

### 2. Device Hierarchies
Physical devices use binding chains:
```
lct-device-battery_pack-xxx
  → witnesses → lct-device-module_1-xxx
  → witnesses → lct-device-cell_1-xxx
```

### 3. Service Meshes
Services declare capabilities in metadata:
```json
{
  "protocol": "http",
  "endpoint": "https://api.example.com",
  "capabilities": "weather,news,search"
}
```

## Implementation Lessons

### What Worked Well
1. **Nanosecond timestamps**: Eliminated collision concerns
2. **Type prefixing**: Made debugging/monitoring easier
3. **Metadata flexibility**: Allowed varied entity needs
4. **Event emission**: Enabled rich off-chain processing

### Challenges Encountered
1. **Metadata size limits**: Need to balance richness vs storage
2. **Type taxonomy**: Required iteration to find right categories
3. **Initial allocations**: Balancing fairness vs anti-spam

## Future Enhancements

### Planned Improvements
1. **Batch minting**: Mint multiple LCTs in one transaction
2. **Template system**: Predefined configs for common entities
3. **Hierarchical types**: Sub-categories (agent:researcher)
4. **Dynamic metadata**: Updateable capability declarations

### Integration Opportunities
1. **MCP compatibility**: Bridge to Model Context Protocol
2. **Hardware attestation**: TPM/secure element integration
3. **Cross-chain recognition**: LCT portability
4. **Identity recovery**: Social recovery mechanisms

## Conclusion

LCT minting patterns have evolved through implementation to balance:
- **Uniqueness**: Verifiable presence
- **Flexibility**: Diverse entity types
- **Efficiency**: Lightweight operations
- **Integration**: Works with other Web4 components

The patterns discovered in ACT provide a solid foundation for Web4 identity that scales from individual devices to collective swarms while maintaining the core principle of verifiable presence through witnessed existence.