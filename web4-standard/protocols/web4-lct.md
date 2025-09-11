# Web4 Lineage and Capability Token (LCT) Specification

This document provides the formal specification for the Lineage and Capability Token (LCT), a core data structure in Web4 that represents a digital entity's identity, capabilities, and history.



_



## 1. LCT Object Definition

```typescript
interface LCT {
  // Identity
  lct_id: string;                    // Globally unique identifier
  subject: string;                    // Entity this LCT represents
  
  // Binding (PERMANENT)
  binding: {
    entity_type: "device" | "service" | "user" | "oracle";
    public_key: string;               // Current public key (Base64)
    hardware_anchor?: string;         // Hardware identity proof
    created_at: string;               // ISO 8601
    binding_proof: string;            // Signature over binding
  };
  
  // Lineage
  lineage: Array<{
    parent_lct?: string;              // Previous LCT if upgraded
    reason: "genesis" | "rotation" | "fork" | "upgrade";
    timestamp: string;
    witness_lcts: string[];           // Who witnessed this transition
  }>;
  
  // Trust Accumulation
  witness_history: Array<{
    witness_lct: string;
    witness_type: "existence" | "action" | "state" | "quality";
    timestamp: string;
    evidence: string;                 // Signature or proof
    trust_delta: number;              // Impact on trust score
  }>;
  
  // Capabilities and Constraints
  capabilities: {
    protocols: string[];              // Supported protocols/extensions
    resources: ResourceQuota[];       // ATP/ADP quotas
    roles: string[];                  // Authorized roles
  };
  
  // Revocation
  revocation?: {
    revoked_at: string;
    reason: string;
    successor_lct?: string;           // If migrated
    final_state: string;              // Last known good state
  };
}
```

