# Web4 TypeScript Reference Implementations

TypeScript implementations of Web4 ledger primitives for browser, Node.js, and edge runtimes.

## Modules

### LCT Parser (`lct-parser.ts`)

Parse and validate Linked Context Token URIs.

**Format**: `lct://{component}:{instance}:{role}@{network}?{params}#{hash}`

```typescript
import { parseLctUri, buildLctUri, validateLctUri } from './lct-parser.js';

// Parse an LCT URI
const result = parseLctUri('lct://sage:thinker:expert_42@testnet?trust_threshold=0.75');
if (result.success) {
  console.log(result.identity.component);   // "sage"
  console.log(result.identity.instance);    // "thinker"
  console.log(result.identity.role);        // "expert_42"
  console.log(result.identity.network);     // "testnet"
  console.log(result.identity.trustThreshold); // 0.75
}

// Build an LCT URI
const uri = buildLctUri({
  component: 'mcp',
  instance: 'filesystem',
  role: 'reader',
  network: 'local',
  capabilities: ['read', 'list'],
  publicKeyHash: 'did:key:z6Mk...'
});
// "lct://mcp:filesystem:reader@local?capabilities=read%2Clist#did:key:z6Mk..."

// Validate with warnings
const validation = validateLctUri('lct://mcp:filesystem:reader@local');
console.log(validation.valid);    // true
console.log(validation.warnings); // ["Local network LCTs should include public key hash..."]
```

### Integration with web4-trust-core WASM

```typescript
import { parseLctUri, toEntityId } from './lct-parser.js';
import { EntityTrust, WasmTrustStore } from 'web4-trust-core';

// Parse LCT and convert to entity ID for WASM bindings
const result = parseLctUri('lct://mcp:filesystem:reader@local');
if (result.success) {
  const entityId = toEntityId(result.identity);  // "mcp:filesystem"

  // Use with WASM trust store
  const store = new WasmTrustStore();
  const entity = new EntityTrust(entityId);
  store.save(entity);
}
```

## Running Tests

```bash
# With tsx (recommended)
npx tsx lct-parser.test.ts

# With Deno
deno run lct-parser.test.ts

# With ts-node
npx ts-node lct-parser.test.ts
```

## Specification Compliance

This implementation follows the [LCT Unified Identity Specification](../../../docs/what/specifications/LCT_UNIFIED_IDENTITY_SPECIFICATION.md) v1.0.0.

### Supported Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `version` | string | LCT spec version (default: "1.0.0") |
| `pairing_status` | enum | pending \| active \| suspended \| revoked |
| `trust_threshold` | float | Required trust level (0.0-1.0) |
| `capabilities` | string[] | Comma-separated capability list |

### Fragment

The URI fragment (`#...`) contains an optional public key hash, typically in DID format:
- `#did:key:z6Mk...` - DID key identifier
- `#sha256:abc123...` - Raw hash

## API Reference

### `parseLctUri(uri: string): LCTParseResult`

Parse an LCT URI string into a structured identity object.

**Returns**: `{ success: boolean, identity?: LCTIdentity, errors: string[] }`

### `validateLctUri(uri: string): LCTValidationResult`

Validate an LCT URI with warnings for non-standard but valid URIs.

**Returns**: `{ valid: boolean, errors: string[], warnings: string[] }`

### `buildLctUri(identity: Partial<LCTIdentity>): string`

Construct an LCT URI from identity fields.

### `lctIdentityEquals(a: LCTIdentity, b: LCTIdentity): boolean`

Compare two identities (ignores metadata, compares core fields).

### `lctIdentityCanonical(identity: LCTIdentity): string`

Generate canonical string: `component:instance:role@network`

### `toEntityId(identity: LCTIdentity): string`

Convert to simple `type:name` format for web4-trust-core compatibility.

### `fromEntityId(entityId: string, network?, role?): Partial<LCTIdentity>`

Create identity from simple entity ID.

## See Also

- [LCT Specification](../../../docs/what/specifications/LCT_UNIFIED_IDENTITY_SPECIFICATION.md)
- [web4-trust-core](../../../web4-trust-core/) - WASM trust tensor bindings
- [Python Reference](../python/) - Python ledger implementations
