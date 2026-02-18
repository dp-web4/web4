# Web4 Model Context Protocol (MCP) Specification

## Overview

The Model Context Protocol (MCP) serves as the inter-entity communication layer for Web4, enabling entities to exchange information, invoke capabilities, and coordinate actions across the distributed intelligence architecture. MCP bridges the gap between AI models and external resources, making it the nervous system through which Web4 entities interact.

## 1. MCP in the Web4 Equation

MCP is the **I/O membrane** in the canonical Web4 equation:

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
        ↑      ↑     ↑       ↑          ↑
        │      │     │       │          └── Energy metabolism
        │      │     │       └── Trust contextualized by horizon
        │      │     └── Presence substrate
        │      └── Ontological backbone (semantic structure)
        └── I/O membrane (this spec)
```

Every component communicates through MCP, but the semantic structure of what flows through MCP is defined by RDF:
- **LCTs** exchange identity proofs and context as RDF-typed entities
- **MRH** graphs are queried and updated via SPARQL over RDF
- **T3/V3** tensors are role-bound via RDF triples and propagated through typed edges
- **SAL** laws and policies are enforced as RDF governance structures
- **AGY** delegations are validated and executed with RDF-typed authority chains

## 2. Core Concepts

### 2.1 MCP as Entity Communication

In Web4, MCP servers are first-class entities that are both:
- **Responsive**: Return results to queries
- **Delegative**: Front-end for tools, processes, databases

This dual nature makes MCP servers perfect intermediaries for Web4's trust-native architecture.

### 2.2 Communication Patterns

MCP enables four primary communication patterns aligned with Web4 relationships:

| Pattern | Web4 Relationship | MCP Mechanism |
|---------|-------------------|---------------|
| **Request-Response** | Pairing | Resource invocation with results |
| **Delegation** | Binding | Tool/resource access on behalf of entity |
| **Observation** | Witnessing | Event streams and attestations |
| **Broadcast** | Announcement | Capability advertisements |

### 2.3 Trust-Aware Communication

Every MCP interaction carries trust context:
- **Sender Trust**: T3/V3 tensors of requesting entity
- **Channel Trust**: Security and reliability of connection
- **Content Trust**: Verifiability of exchanged data
- **Result Trust**: Confidence in response accuracy

## 3. MCP-Web4 Entity Integration

### 3.1 MCP Server as Web4 Entity

Every MCP server has an LCT and participates as a full Web4 entity:

```json
{
  "lct_id": "lct:web4:mcp:server:...",
  "entity_type": "mcp_server",
  "capabilities": {
    "tools": ["database_query", "api_invoke", "compute_task"],
    "protocols": ["mcp/1.0", "web4/1.0"],
    "trust_requirements": {
      "minimum_t3": {"talent": 0.5, "training": 0.6},
      "atp_stake": 10
    }
  },
  "mrh": {
    "bound": ["lct:web4:resource:database", "lct:web4:api:external"],
    "paired": ["lct:web4:client:...", "lct:web4:agent:..."],
    "witnessing": ["lct:web4:oracle:..."]
  }
}
```

### 3.2 MCP Client as Web4 Entity

MCP clients (including AI models) are also Web4 entities:

```json
{
  "lct_id": "lct:web4:mcp:client:...",
  "entity_type": "mcp_client",
  "model_info": {
    "type": "ai_model",
    "capabilities": ["reasoning", "generation", "analysis"],
    "context_window": 200000,
    "trust_profile": {
      "t3": {"talent": 0.9, "training": 0.95, "temperament": 0.85},
      "v3": {"veracity": 0.92, "validity": 0.88, "value": 0.90}
    }
  }
}
```

## 4. MCP Protocol Extensions for Web4

### 4.1 Web4 Context Headers

Every MCP message includes Web4 context:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "database_query",
    "arguments": {...}
  },
  "web4_context": {
    "sender_lct": "lct:web4:client:...",
    "sender_role": "web4:DataAnalyst",
    "trust_context": {
      "t3_in_role": {"talent": 0.85, "training": 0.90},
      "atp_stake": 50
    },
    "mrh_depth": 2,
    "society": "lct:web4:society:...",
    "law_hash": "sha256:...",
    "proof_of_agency": {
      "grant_id": "agy:...",
      "scope": "data:analysis"
    }
  }
}
```

### 4.2 Trust-Based Resource Access

MCP servers evaluate trust before granting access:

```python
def handle_resource_request(request, web4_context):
    # 1. Verify entity identity
    if not verify_lct(web4_context.sender_lct):
        return Error("Invalid LCT")
    
    # 2. Check trust requirements
    if not meets_trust_requirements(web4_context.trust_context):
        return Error("Insufficient trust")
    
    # 3. Verify ATP stake if required
    if not verify_atp_stake(web4_context.atp_stake):
        return Error("Insufficient ATP stake")
    
    # 4. Check agency delegation if present
    if web4_context.proof_of_agency:
        if not verify_agency(web4_context.proof_of_agency):
            return Error("Invalid agency proof")
    
    # 5. Execute request with metering
    result = execute_with_metering(request)
    
    # 6. Update trust tensors
    update_trust_tensors(web4_context.sender_lct, result)
    
    return result
```

### 4.3 Witness Integration

MCP servers can act as witnesses for interactions:

```json
{
  "witness_attestation": {
    "witnessed_interaction": {
      "client": "lct:web4:client:...",
      "server": "lct:web4:server:...",
      "action": "database_query",
      "timestamp": "2025-09-15T12:00:00Z",
      "success": true
    },
    "witness": "lct:web4:mcp:server:...",
    "signature": "cose:...",
    "mrh_update": {
      "add_witnessing": ["lct:web4:client:...", "lct:web4:server:..."]
    }
  }
}
```

## 5. MCP Transport Bindings

### 5.1 Supported Transports

MCP in Web4 supports multiple transport layers:

| Transport | Use Case | Trust Level |
|-----------|----------|-------------|
| **HTTPS** | Standard web communication | Medium |
| **WebSocket** | Real-time bidirectional | Medium |
| **QUIC** | Low-latency, multiplexed | High |
| **libp2p** | P2P decentralized | Variable |
| **Blockchain RPC** | On-chain verification | Highest |

### 5.2 Transport Security

All MCP communications MUST:
- Use TLS 1.3 or higher (except blockchain)
- Include HPKE encryption for sensitive data
- Implement replay protection via nonces
- Support channel binding for ATP stakes

## 6. MCP Resource Types

### 6.1 Tool Resources

Tools exposed via MCP are Web4 resources:

```json
{
  "resource_type": "mcp_tool",
  "tool_definition": {
    "name": "analyze_dataset",
    "description": "Statistical analysis of datasets",
    "input_schema": {...},
    "output_schema": {...},
    "resource_requirements": {
      "compute": "medium",
      "memory": "4GB",
      "atp_cost": 10
    },
    "trust_requirements": {
      "minimum_t3": {"training": 0.7},
      "role_required": "web4:DataAnalyst"
    }
  }
}
```

### 6.2 Prompt Resources

Prompts are first-class MCP resources:

```json
{
  "resource_type": "mcp_prompt",
  "prompt_definition": {
    "name": "code_review",
    "template": "Review the following code for...",
    "variables": ["code", "language", "focus_areas"],
    "expected_output": "structured_review",
    "atp_cost": 5
  }
}
```

### 6.3 Context Resources

Shared context maintained across interactions:

```json
{
  "resource_type": "mcp_context",
  "context_state": {
    "session_id": "sess:...",
    "accumulated_facts": [...],
    "mrh_graph": {
      "entities": [...],
      "relationships": [...]
    },
    "trust_evolution": {
      "interaction_count": 42,
      "success_rate": 0.95,
      "t3_delta": {"temperament": +0.02}
    }
  }
}
```

## 7. MCP-R6 Integration

### 7.1 MCP Actions as R6 Transactions

Every MCP interaction maps to R6:

```json
{
  "type": "mcp_invocation",
  "rules": {
    "mcp_protocol": "1.0",
    "web4_compliance": true
  },
  "role": {
    "entity": "lct:web4:client:...",
    "roleType": "web4:Developer"
  },
  "request": {
    "action": "tools/call",
    "target": "mcp://server/tool",
    "parameters": {...},
    "mcp_headers": {...}
  },
  "reference": {
    "prior_interactions": [...],
    "trust_proofs": [...]
  },
  "resource": {
    "required": {
      "atp": 10,
      "bandwidth": "1MB"
    }
  },
  "result": {
    "mcp_response": {...},
    "trust_updates": {...}
  }
}
```

### 7.2 MCP Server Authority

MCP servers can have delegated authority:

```json
{
  "mcp_authority": {
    "server": "lct:web4:mcp:server:...",
    "delegated_from": "lct:web4:organization:...",
    "scope": {
      "resources": ["database", "api", "compute"],
      "operations": ["read", "write", "execute"],
      "limits": {
        "max_atp_per_request": 100,
        "rate_limit": "1000/hour"
      }
    },
    "valid_until": "2025-12-31T23:59:59Z"
  }
}
```

## 8. MCP Discovery and Advertisement

### 8.1 Capability Broadcasting

MCP servers broadcast capabilities:

```json
{
  "broadcast_type": "mcp_capabilities",
  "server": "lct:web4:mcp:server:...",
  "capabilities": {
    "tools": [...],
    "prompts": [...],
    "contexts": [...],
    "protocols": ["mcp/1.0", "web4/1.0"],
    "trust_level": "high",
    "availability": 0.999
  },
  "broadcast_signature": "cose:...",
  "ttl": 3600
}
```

### 8.2 Discovery via MRH

Entities discover MCP servers through MRH queries:

```sparql
SELECT ?server ?capability ?trust WHERE {
  ?server a web4:MCPServer ;
          web4:hasCapability ?capability ;
          web4:trustScore ?trust .
  ?server web4:witnessedBy ?witness .
  FILTER(?trust > 0.8)
}
```

## 9. MCP Metering and Pricing

### 9.1 ATP-Based Metering

All MCP interactions are metered in ATP:

```python
class MCPMeter:
    def calculate_cost(self, request, context):
        base_cost = self.resource_costs[request.tool]
        trust_modifier = 1.0 - (context.t3.average() * 0.2)  # Higher trust = lower cost
        complexity_factor = self.estimate_complexity(request)
        
        total_cost = base_cost * trust_modifier * complexity_factor
        
        return min(total_cost, context.atp_cap)  # Respect caps
```

### 9.2 Dynamic Pricing

Prices adjust based on demand and trust:

```json
{
  "pricing_model": {
    "base_prices": {
      "simple_query": 1,
      "complex_analysis": 10,
      "heavy_compute": 100
    },
    "modifiers": {
      "high_trust_discount": 0.8,
      "peak_demand_surge": 1.5,
      "bulk_discount": 0.9
    },
    "settlement": "immediate"
  }
}
```

## 10. Error Handling

### 10.1 MCP-Specific Errors

```python
class MCPError(Exception):
    pass

class InsufficientTrust(MCPError):
    """Client doesn't meet trust requirements"""

class InvalidLCT(MCPError):
    """Client LCT cannot be verified"""

class ResourceUnavailable(MCPError):
    """Requested resource temporarily unavailable"""

class ATPInsufficient(MCPError):
    """Client has insufficient ATP for request"""

class AgencyViolation(MCPError):
    """Request violates agency delegation scope"""
```

### 10.2 Error Response Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Insufficient trust",
    "data": {
      "error_type": "InsufficientTrust",
      "required_t3": {"training": 0.7},
      "provided_t3": {"training": 0.5},
      "suggestion": "Build trust through successful interactions"
    }
  },
  "web4_context": {
    "error_witnessed": true,
    "witness": "lct:web4:witness:...",
    "trust_impact": {"t3": {"temperament": -0.01}}
  }
}
```

## 11. MCP Session Management

### 11.1 Stateful Sessions

MCP supports stateful sessions with context preservation:

```json
{
  "session": {
    "id": "mcp:session:...",
    "client": "lct:web4:client:...",
    "server": "lct:web4:server:...",
    "established": "2025-09-15T10:00:00Z",
    "context": {
      "accumulated_state": {...},
      "trust_evolution": {...},
      "atp_consumed": 47,
      "atp_remaining": 53
    },
    "timeout": 3600
  }
}
```

### 11.2 Session Handoff

Sessions can be transferred between servers:

```json
{
  "handoff_request": {
    "session_id": "mcp:session:...",
    "from_server": "lct:web4:server:A",
    "to_server": "lct:web4:server:B",
    "context_transfer": {
      "state": {...},
      "trust_proofs": [...],
      "witness_attestations": [...]
    },
    "client_consent": "signature:..."
  }
}
```

## 12. Implementation Requirements

### MUST Requirements
1. All MCP servers MUST have valid LCTs
2. All interactions MUST include Web4 context headers
3. Trust evaluation MUST precede resource access
4. ATP metering MUST be enforced
5. Agency proofs MUST be validated when present

### SHOULD Requirements
1. Servers SHOULD witness significant interactions
2. Clients SHOULD cache server capabilities
3. Sessions SHOULD preserve context across requests
4. Errors SHOULD include trust impact assessment
5. Pricing SHOULD reflect trust levels

### MAY Requirements
1. Servers MAY require ATP stakes for high-value resources
2. Clients MAY negotiate prices before execution
3. Sessions MAY be encrypted end-to-end
4. Servers MAY delegate to other servers
5. Clients MAY request specific witness involvement

## 13. Security Considerations

### 13.1 Authentication
- All entities authenticated via LCT signatures
- Optional multi-factor via witness attestation
- Session tokens bound to transport layer

### 13.2 Authorization
- Role-based access control via Web4 roles
- Agency delegation validated per request
- Resource caps enforced per society law

### 13.3 Confidentiality
- HPKE encryption for sensitive data
- Perfect forward secrecy via ephemeral keys
- Context isolation between sessions

### 13.4 Integrity
- All messages signed with LCT keys
- Replay protection via nonces
- Witness attestations for critical operations

## 14. Privacy Considerations

- Trust scores revealed only as needed
- MRH queries scoped to relevance
- Agency relationships disclosed per law
- Session context deleted after timeout
- Minimal logging of interaction details

## 15. Future Extensions

Potential enhancements under consideration:
- **Batch Operations**: Multiple requests in single transaction
- **Streaming Results**: Progressive response delivery
- **Federated Queries**: Cross-server coordination
- **Predictive Caching**: Anticipate client needs based on trust patterns
- **Reputation Markets**: Trade trust scores for resource access

## 16. Summary

MCP serves as the critical communication layer that enables Web4's distributed intelligence architecture. By treating both MCP clients and servers as first-class Web4 entities with LCTs, trust tensors, and relationship graphs, MCP transforms from a simple protocol into the nervous system of Web4's trust-native internet.

Every MCP interaction becomes a trust-building exercise, where successful communications strengthen the fabric of digital relationships while failures are learned from and witnessed. This creates an antifragile system that grows stronger through use.

---

*"In Web4, MCP isn't just how entities talk—it's how they build trust, delegate authority, and weave the fabric of distributed intelligence."*