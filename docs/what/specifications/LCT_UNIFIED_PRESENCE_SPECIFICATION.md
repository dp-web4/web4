# Unified LCT (Linked Context Token) Presence Specification

**Version**: 1.0.0
**Date**: 2025-12-17
**Status**: Draft for Cross-Project Integration
**Context**: Legion Session 62+ Autonomous Research

---

## Abstract

This specification defines a unified Linked Context Token (LCT) presence format that enables seamless presence management across ACT blockchain, SAGE neural systems, and Web4 protocol implementations. It provides a standardized way to represent AI agent presence, component relationships, and role assignments in a distributed multi-agent system.

---

## Motivation

Three independent presence models have emerged:

1. **ACT Blockchain**: LCT relationships with pairing_status validation
2. **SAGE Neural**: Expert IDs with namespace (e.g., "sage_thinker_expert_42")
3. **Web4 Protocol**: Conceptual LCT presence system

**Problem**: No standard format for cross-system presence representation

**Solution**: Unified LCT specification compatible with all three systems

---

## LCT Presence Format

### Core Structure

```
lct://{component}:{instance}:{role}@{network}
```

**Components**:
- `component`: System or component name (e.g., "sage", "web4-agent", "act-validator")
- `instance`: Specific instance identifier (e.g., "thinker", "guardian", "primary")
- `role`: Role within the instance (e.g., "expert_42", "coordinator", "validator")
- `network`: Network identifier (e.g., "mainnet", "testnet", "local")

**Examples**:
```
lct://sage:thinker:expert_42@testnet
lct://web4-agent:guardian:coordinator@mainnet
lct://act-validator:node1:consensus@testnet
lct://memory:fractal:lightchain@local
```

### Optional Fields

**Full URI Format**:
```
lct://{component}:{instance}:{role}@{network}?{query_params}#{fragment}
```

**Query Parameters**:
- `version={semver}`: LCT format version (default: 1.0.0)
- `pairing_status={status}`: Relationship status (active/pending/expired)
- `trust_threshold={float}`: Minimum trust score required
- `capabilities={list}`: Comma-separated capability list

**Fragment**:
- Public key hash or DID (Decentralized Identifier) anchor

**Example**:
```
lct://sage:thinker:expert_42@testnet?version=1.0.0&pairing_status=active&trust_threshold=0.75#did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK
```

---

## Component Field Specification

### Component Names

**Reserved Components**:
- `sage`: SAGE neural systems (HRM)
- `web4-agent`: Web4 protocol agents
- `act-validator`: ACT blockchain validators
- `act-society`: ACT society instances
- `memory`: Memory/lightchain systems
- `portal`: Portal bridge systems
- `sync`: Synchronism-based systems

**Naming Rules**:
- Lowercase alphanumeric + hyphens
- Max length: 32 characters
- Must start with letter
- Reserved components require ecosystem governance approval

### Instance Names

**Purpose**: Distinguish multiple instances of same component

**Examples**:
- `thinker`, `dreamer`, `guard` (SAGE cognitive roles)
- `primary`, `secondary`, `backup` (redundancy)
- `node1`, `node2`, `node3` (distributed nodes)
- `fractal`, `temporal`, `spatial` (memory types)

**Naming Rules**:
- Lowercase alphanumeric + underscores
- Max length: 64 characters
- Must be unique within component namespace

### Role Names

**Purpose**: Specific role or capability within instance

**Examples**:
- `expert_{id}` (SAGE expert number)
- `coordinator` (coordination role)
- `validator` (validation role)
- `lightchain` (specific capability)

**Naming Rules**:
- Lowercase alphanumeric + underscores
- Max length: 128 characters
- Can include numeric suffixes

### Network Identifiers

**Standard Networks**:
- `mainnet`: Production network
- `testnet`: Testing network
- `devnet`: Development network
- `local`: Local testing environment

**Custom Networks**:
- Format: `{org}-{env}` (e.g., "anthropic-staging")
- Requires registration in network registry

---

## LCT Relationship Model

### Pairing Status

LCT presence tokens can form **relationships** with pairing_status:

**Status Values**:
- `pending`: Relationship requested, not yet confirmed
- `active`: Relationship active and operational
- `suspended`: Temporarily suspended
- `expired`: Relationship terminated
- `revoked`: Relationship revoked by either party

**State Machine**:
```
     request
  ┌───────────┐
  │           ▼
null ──────► pending ──────► active ──────► expired
              │  ▲            │  ▲              │
              │  └────────────┘  │              │
              │     renew        │              │
              ▼                  ▼              ▼
           revoked ◄──────── suspended      revoked
```

### Trust Integration

Each LCT relationship has associated **trust scores**:

**Trust Dimensions** (from ACT TrustTensor):
- `relationship_trust`: Overall trust in the relationship
- `context_trust`: Trust in specific operational contexts
- `historical_trust`: Time-weighted trust history

**Trust Score Range**: [0.0, 1.0]

**Minimum Thresholds** (configurable):
- `critical_operations`: ≥ 0.80
- `standard_operations`: ≥ 0.60
- `exploratory_operations`: ≥ 0.40

---

## Integration with ACT Blockchain

### LCT Registry Storage

**Cosmos SDK Module**: `x/lctmanager`

**Data Structure**:
```protobuf
message LinkedContextToken {
  string lct_id = 1;                    // Full LCT URI
  string component = 2;                 // Parsed component
  string instance = 3;                  // Parsed instance
  string role = 4;                      // Parsed role
  string network = 5;                   // Parsed network
  string pairing_status = 6;            // Current status
  google.protobuf.Timestamp created_at = 7;
  google.protobuf.Timestamp updated_at = 8;
  string public_key = 9;                // Cryptographic attestation key
  map<string, string> metadata = 10;    // Extensible metadata
  int32 version = 11;                   // Version for updates
}
```

### Registration Process

**1. Register LCT**:
```bash
actd tx lctmanager register-lct \
  --lct-id "lct://sage:thinker:expert_42@testnet" \
  --public-key "0x..." \
  --metadata "trust_threshold=0.75,capabilities=text-generation" \
  --from user
```

**2. Pair LCTs**:
```bash
actd tx lctmanager create-pairing \
  --source-lct "lct://sage:thinker:expert_42@testnet" \
  --target-lct "lct://web4-agent:guardian:coordinator@testnet" \
  --from user
```

**3. Validate Pairing**:
```bash
actd query lctmanager get-pairing \
  --source-lct "lct://sage:thinker:expert_42@testnet" \
  --target-lct "lct://web4-agent:guardian:coordinator@testnet"
```

### Trust Score Integration

**Query Trust**:
```bash
actd query trusttensor calculate-relationship-trust \
  --lct-id "lct://sage:thinker:expert_42@testnet" \
  --context "energy_operation"
```

**Returns**:
```json
{
  "trust_score": "0.847",
  "confidence": "0.92",
  "sample_size": 156,
  "last_updated": "2025-12-17T12:34:56Z"
}
```

---

## Integration with SAGE Neural Systems

### ExpertIdentityBridge Enhancement

**File**: `/home/dp/ai-workspace/HRM/sage/web4/expert_identity.py`

**Current Implementation** (Session 59):
```python
class ExpertIdentityBridge:
    def __init__(self, namespace: str = "sage"):
        self.namespace = namespace  # e.g., "sage"

    def expert_to_lct(self, expert_id: int, component: str = "thinker") -> str:
        # Returns: "sage_thinker_expert_42"
        return f"{self.namespace}_{component}_expert_{expert_id}"
```

**Enhanced Implementation** (This Spec):
```python
class ExpertIdentityBridge:
    def __init__(self, namespace: str = "sage", instance: str = "thinker",
                 network: str = "testnet"):
        self.namespace = namespace
        self.instance = instance
        self.network = network

    def expert_to_lct_uri(self, expert_id: int) -> str:
        """Convert expert ID to full LCT URI."""
        return f"lct://{self.namespace}:{self.instance}:expert_{expert_id}@{self.network}"

    def lct_uri_to_expert(self, lct_uri: str) -> int:
        """Parse LCT URI to extract expert ID."""
        # Parse: lct://sage:thinker:expert_42@testnet → 42
        match = re.match(r"lct://([^:]+):([^:]+):expert_(\d+)@([^?#]+)", lct_uri)
        if not match:
            raise ValueError(f"Invalid SAGE expert LCT URI: {lct_uri}")
        return int(match.group(3))

    def validate_lct_uri(self, lct_uri: str) -> bool:
        """Validate LCT URI format and component namespace."""
        try:
            parsed = parse_lct_uri(lct_uri)
            return (parsed.component == self.namespace and
                    parsed.instance == self.instance)
        except Exception:
            return False
```

### AuthorizedExpertSelector Integration

**Enhanced with LCT Validation**:
```python
class AuthorizedExpertSelector:
    def select_experts(self, router_logits, context, k,
                       requesting_lct: str = None,  # NEW
                       atp_payment: int = 0):
        # Validate requesting LCT if provided
        if requesting_lct:
            if not self.identity_bridge.validate_lct_uri(requesting_lct):
                return SelectionResult(
                    success=False,
                    error="Invalid LCT URI format"
                )

            # Check authorization via blockchain
            if self.enable_authorization:
                authorized = self.auth_client.check_authorization(
                    requesting_lct=requesting_lct,
                    resource_type="expert_selection",
                    context=context
                )
                if not authorized:
                    return SelectionResult(
                        success=False,
                        error=f"LCT {requesting_lct} not authorized"
                    )

        # Continue with expert selection...
```

---

## Integration with Web4 Protocol

### LCT Presence Standard

**Protocol Specification**: Web4 LCT Presence RFC

**Key Requirements**:
1. All Web4 agents MUST have valid LCT URI
2. LCT URIs MUST follow this specification format
3. LCT relationships MUST be verifiable on ACT blockchain or equivalent
4. Trust scores MUST be queryable via standard Web4 API

**Example Web4 Agent Registration**:
```json
{
  "agent": {
    "lct_uri": "lct://web4-agent:guardian:coordinator@mainnet",
    "capabilities": [
      "resource_allocation",
      "trust_aggregation",
      "conflict_resolution"
    ],
    "trust_threshold": 0.75,
    "pairing_status": "active",
    "public_key": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
  }
}
```

### Web4 API Endpoints

**1. Register LCT**:
```
POST /web4/v1/lct/register
Content-Type: application/json

{
  "lct_uri": "lct://web4-agent:guardian:coordinator@mainnet",
  "public_key": "...",
  "metadata": {
    "capabilities": ["resource_allocation"],
    "trust_threshold": 0.75
  }
}
```

**2. Query LCT**:
```
GET /web4/v1/lct/query?lct_uri=lct://sage:thinker:expert_42@testnet

Response:
{
  "lct": {
    "lct_uri": "lct://sage:thinker:expert_42@testnet",
    "component": "sage",
    "instance": "thinker",
    "role": "expert_42",
    "network": "testnet",
    "pairing_status": "active",
    "trust_score": 0.847,
    "created_at": "2025-12-15T10:30:00Z"
  }
}
```

**3. Create Pairing**:
```
POST /web4/v1/lct/pair
Content-Type: application/json

{
  "source_lct": "lct://sage:thinker:expert_42@testnet",
  "target_lct": "lct://web4-agent:guardian:coordinator@mainnet",
  "trust_threshold": 0.70
}
```

---

## LCT URI Parsing Library

### Reference Implementation (Python)

```python
from dataclasses import dataclass
from typing import Optional, Dict
import re
from urllib.parse import urlparse, parse_qs

@dataclass
class LCTIdentity:
    """Parsed LCT presence record."""
    component: str
    instance: str
    role: str
    network: str
    version: str = "1.0.0"
    pairing_status: Optional[str] = None
    trust_threshold: Optional[float] = None
    capabilities: list[str] = None
    public_key_hash: Optional[str] = None

    @property
    def lct_uri(self) -> str:
        """Reconstruct LCT URI."""
        base = f"lct://{self.component}:{self.instance}:{self.role}@{self.network}"

        params = []
        if self.version != "1.0.0":
            params.append(f"version={self.version}")
        if self.pairing_status:
            params.append(f"pairing_status={self.pairing_status}")
        if self.trust_threshold is not None:
            params.append(f"trust_threshold={self.trust_threshold}")
        if self.capabilities:
            params.append(f"capabilities={','.join(self.capabilities)}")

        query_string = "&".join(params) if params else ""
        fragment = f"#{self.public_key_hash}" if self.public_key_hash else ""

        uri = base
        if query_string:
            uri += f"?{query_string}"
        if fragment:
            uri += fragment

        return uri

def parse_lct_uri(lct_uri: str) -> LCTIdentity:
    """
    Parse LCT URI into structured presence record.

    Args:
        lct_uri: LCT URI string (e.g., "lct://sage:thinker:expert_42@testnet")

    Returns:
        LCTIdentity object with parsed fields

    Raises:
        ValueError: If URI format is invalid
    """
    # Validate scheme
    if not lct_uri.startswith("lct://"):
        raise ValueError(f"Invalid LCT URI scheme: {lct_uri}")

    # Parse using urllib
    parsed = urlparse(lct_uri)

    # Extract authority (component:instance:role@network)
    authority = parsed.netloc
    path = parsed.path.lstrip("/")

    # Combine netloc and path for parsing
    full_authority = authority + "/" + path if path else authority

    # Pattern: component:instance:role@network
    pattern = r"^([^:]+):([^:]+):([^@]+)@([^?#]+)"
    match = re.match(pattern, full_authority)

    if not match:
        raise ValueError(f"Invalid LCT authority format: {full_authority}")

    component, instance, role, network = match.groups()

    # Parse query parameters
    query_params = parse_qs(parsed.query)
    version = query_params.get("version", ["1.0.0"])[0]
    pairing_status = query_params.get("pairing_status", [None])[0]
    trust_threshold_str = query_params.get("trust_threshold", [None])[0]
    trust_threshold = float(trust_threshold_str) if trust_threshold_str else None
    capabilities_str = query_params.get("capabilities", [None])[0]
    capabilities = capabilities_str.split(",") if capabilities_str else None

    # Parse fragment (public key hash)
    public_key_hash = parsed.fragment if parsed.fragment else None

    return LCTIdentity(
        component=component,
        instance=instance,
        role=role,
        network=network,
        version=version,
        pairing_status=pairing_status,
        trust_threshold=trust_threshold,
        capabilities=capabilities,
        public_key_hash=public_key_hash
    )

def validate_lct_uri(lct_uri: str) -> bool:
    """Validate LCT URI format."""
    try:
        parse_lct_uri(lct_uri)
        return True
    except ValueError:
        return False

# Example usage
if __name__ == "__main__":
    uri = "lct://sage:thinker:expert_42@testnet?version=1.0.0&pairing_status=active&trust_threshold=0.75#did:key:z6Mk..."

    lct = parse_lct_uri(uri)
    print(f"Component: {lct.component}")
    print(f"Instance: {lct.instance}")
    print(f"Role: {lct.role}")
    print(f"Network: {lct.network}")
    print(f"Trust Threshold: {lct.trust_threshold}")
    print(f"Reconstructed: {lct.lct_uri}")
```

---

## Security Considerations

### 1. LCT URI Forgery

**Threat**: Attacker creates fake LCT URI to impersonate legitimate presence

**Mitigation**:
- All LCT registrations require cryptographic signature
- Public key anchored in blockchain or DID registry
- Fragment contains public key hash for verification
- Trust scores only for verified LCT registrations

### 2. Pairing Status Manipulation

**Threat**: Attacker manipulates pairing_status to gain unauthorized access

**Mitigation**:
- Pairing status stored on blockchain (immutable)
- State transitions require multi-party signatures
- Revocation logged in audit trail
- Trust scores decay for inactive pairings

### 3. Trust Score Pollution

**Threat**: Malicious agent submits fake trust scores

**Mitigation**:
- Trust updates require cryptographic signatures
- Rate limiting on trust score submissions
- Outlier detection and filtering
- Trust scores converge across multiple observers

### 4. Network Identifier Confusion

**Threat**: LCT registered on testnet used on mainnet

**Mitigation**:
- Explicit network parameter in all operations
- Network boundary validation in smart contracts
- Warning if LCT network doesn't match current network
- Separate trust scores per network

---

## Backward Compatibility

### SAGE Expert IDs (Pre-LCT)

**Legacy Format**: `sage_thinker_expert_42`

**Migration**:
```python
def migrate_legacy_expert_id(legacy_id: str, network: str = "testnet") -> str:
    """Convert legacy SAGE expert ID to LCT URI."""
    # Parse: sage_thinker_expert_42
    parts = legacy_id.split("_")
    if len(parts) != 4 or parts[2] != "expert":
        raise ValueError(f"Invalid legacy expert ID: {legacy_id}")

    component = parts[0]  # sage
    instance = parts[1]   # thinker
    role = f"expert_{parts[3]}"  # expert_42

    return f"lct://{component}:{instance}:{role}@{network}"
```

### ACT LCT IDs (Current)

**Current Format**: String LCT ID in ACT blockchain

**Compatibility**: If existing ACT LCT IDs don't match URI format, use migration:
```go
func MigrateLegacyLCTID(legacyID string, network string) string {
    // If already a URI, return as-is
    if strings.HasPrefix(legacyID, "lct://") {
        return legacyID
    }

    // Otherwise, assume format: component_instance_role
    parts := strings.Split(legacyID, "_")
    if len(parts) < 3 {
        return fmt.Sprintf("lct://unknown:unknown:%s@%s", legacyID, network)
    }

    return fmt.Sprintf("lct://%s:%s:%s@%s",
        parts[0], parts[1], parts[2], network)
}
```

---

## Versioning and Evolution

### Specification Versioning

**Current**: Version 1.0.0 (this document)

**Version Format**: Semantic versioning (MAJOR.MINOR.PATCH)

**Version Query Parameter**: `?version=1.0.0` in LCT URI

**Backward Compatibility**:
- MAJOR version: Breaking changes (incompatible)
- MINOR version: New features (backward compatible)
- PATCH version: Bug fixes (backward compatible)

### Extension Mechanism

**Custom Query Parameters**: Allowed for ecosystem-specific extensions

**Example**:
```
lct://sage:thinker:expert_42@testnet?version=1.0.0&x-anthropic-tier=premium&x-anthropic-quota=1000
```

**Validation**: Standard parsers MUST ignore unknown query parameters

---

## Reference Implementations

### Repositories

1. **Python (SAGE)**: `/home/dp/ai-workspace/HRM/sage/web4/lct_identity.py`
2. **Go (ACT)**: `/home/dp/ai-workspace/act/implementation/ledger/x/lctmanager/types/lct_identity.go`
3. **TypeScript (Web4)**: `/home/dp/ai-workspace/web4/src/identity/lct-parser.ts`

### Test Vectors

```json
[
  {
    "uri": "lct://sage:thinker:expert_42@testnet",
    "parsed": {
      "component": "sage",
      "instance": "thinker",
      "role": "expert_42",
      "network": "testnet"
    }
  },
  {
    "uri": "lct://web4-agent:guardian:coordinator@mainnet?pairing_status=active&trust_threshold=0.75",
    "parsed": {
      "component": "web4-agent",
      "instance": "guardian",
      "role": "coordinator",
      "network": "mainnet",
      "pairing_status": "active",
      "trust_threshold": 0.75
    }
  },
  {
    "uri": "lct://act-validator:node1:consensus@testnet?version=1.0.0#did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
    "parsed": {
      "component": "act-validator",
      "instance": "node1",
      "role": "consensus",
      "network": "testnet",
      "version": "1.0.0",
      "public_key_hash": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
    }
  }
]
```

---

## Conclusion

This Unified LCT Presence Specification provides a **standard format for AI agent presence** across ACT blockchain, SAGE neural systems, and Web4 protocol implementations. Key features:

1. **URI-based format** compatible with web standards
2. **Hierarchical structure** (component:instance:role@network)
3. **Extensible query parameters** for ecosystem-specific metadata
4. **Cryptographic anchoring** via public key hash fragment
5. **Backward compatibility** with legacy SAGE and ACT formats
6. **Reference implementations** in Python, Go, and TypeScript

**Next Steps**:
1. Implement parsing libraries in all three systems
2. Migrate existing LCT records to URI format
3. Update ExpertIdentityBridge in SAGE
4. Enhance ACT lctmanager module
5. Define Web4 API endpoints
6. Create integration tests across all three systems

**Status**: Draft specification ready for implementation (Track 2 complete)

---

**Document Version**: 1.0.0-draft
**Last Updated**: 2025-12-17
**Author**: Legion (Autonomous Research Session 62+)
**Cross-References**: ATP_CROSS_PROJECT_INTEGRATION_ANALYSIS.md
