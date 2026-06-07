# Web4 Model Context Protocol (MCP) Specification

## Overview

The Model Context Protocol (MCP) serves as the inter-entity communication layer for Web4, enabling entities to exchange information, invoke capabilities, and coordinate actions across the distributed intelligence architecture. MCP bridges the gap between AI models and external resources, making it the nervous system through which Web4 entities interact. Cross-society interaction is MCP's primary expected use case (§1.1, §7); intra-society communication is a special case of the same protocol.

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

### 1.1 MCP as the Inter-Society Interface

The "I/O membrane" framing has a load-bearing consequence: **MCP is the protocol by which sovereign Web4 societies engage each other**.

A society's internal structure is defined by `LCT + T3/V3*MRH + ATP/ADP` over an RDF semantic substrate (see `LCT-linked-context-token.md`, `t3-v3-tensors.md`, `mrh-tensors.md`, `atp-adp-cycle.md`). A society's *external surface* — the productivity it exposes to other societies, the actions it allows outsiders to invoke, the resources it makes queryable — is its MCP server.

When an entity in Society A initiates an R6/R7 action against a resource in Society B, that action is realized as an MCP tool call from A's MCP client to B's MCP server, with Web4 context headers (§4.1) carrying the LCT envelope, the R6 rules/role/reference, and (for R7) the Reputation back-propagation hint.

This dissolves what would otherwise be a separate "cross-society action protocol" question. The cross-society action protocol *is* MCP — per the equation's design. See `inter-society-protocol.md` for genesis/first-contact/secession primitives; this spec's §7 covers the R6/R7 actions those societies perform on each other via MCP.

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
      "v3": {"veracity": 0.92, "validity": 0.88, "valuation": 0.90}
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
    if not verify_atp_stake(web4_context.trust_context.atp_stake):
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
    "session_id": "mcp:session:...",
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

## 7. MCP-R6/R7 Integration and Cross-Society Bindings

This section specifies how MCP interactions bind to Web4's R6/R7 action grammar, including the cross-society case where the calling and responding entities reside in different societies. Cross-society interactions are the *primary* expected use for the Web4 MCP extensions; intra-society MCP interactions are a special case where calling and responding societies happen to be the same.

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

### 7.3 MCP Actions as R7 Transactions

R7 extends R6 with a seventh component — Reputation — that back-propagates to the T3/V3 tensors of the involved entities and (for cross-society actions, see §7.4) to the inter-society trust tensors. See `r7-framework.md` for the canonical R7 definition.

An MCP action MUST be treated as R7 (rather than R6) when ANY of the following holds:

- The action crosses a society boundary (caller and responder are in different societies); cross-society actions are R7 by default because outcomes feed inter-society trust evolution
- The action is consequential per the responding society's policy (high-stakes operations, resource modifications, escalation candidates)
- The caller or responder has explicitly tagged the action as `r7_required: true` in the Web4 Context Headers

R7 MCP actions extend the §7.1 R6 structure with a `reputation` field in the response:

```json
{
  "type": "mcp_invocation_r7",
  "rules": { /* per R6 */ },
  "role":  { /* per R6 */ },
  "request": { /* per R6 */ },
  "reference": { /* per R6 */ },
  "resource": { /* per R6 */ },
  "result": {
    "mcp_response": {...},
    "trust_updates": {...}
  },
  "reputation": {
    "outcome_class": "success | partial | failure | violation",
    "outcome_quality": 0.92,
    "responding_society_signature": "cose:...",
    "trust_dimension_updates": {
      "talent":      { "delta": +0.01, "context": "executed cleanly" },
      "training":    { "delta": +0.005, "context": "evidence accumulated" },
      "temperament": { "delta":  0.00, "context": "no behavioral signal" }
    },
    "propagation_scope": "caller_society | responding_society | both | encompassing_society",
    "witness_signatures": [...]
  }
}
```

**Normative requirements for R7 over MCP:**

- The `reputation.responding_society_signature` MUST be signed by the responding society's Policy-Entity (the role that made the decision per `society-roles.md` §2.3)
- The `reputation.outcome_class` MUST be one of the canonical values; implementations MUST NOT invent new values without spec extension
- The `reputation.trust_dimension_updates` deltas MUST be within bounds set by the responding society's Law Oracle for the role context (per `t3-v3-tensors.md` parameter governance)
- The `reputation.propagation_scope` MUST be set; absent it, implementations SHOULD default by `cross_society.interaction_type` (§7.4): `responding_society` for intra-society R7; `both` for cross-society `first_contact`/`established` actions; and `encompassing_society` for `federated` actions where caller and responder share an encompassing society (the federation standard per §7.5), falling back to `both` when no encompassing society exists
- For high-consequence actions (per the responding society's classification), `reputation.witness_signatures` MUST contain at least one signature from a Witness role per `society-roles.md` §4.1; the encompassing society's Witness is preferred when one exists

- When `outcome_class` is `violation`, the `trust_dimension_updates` deltas MUST be non-positive (zero or negative); the responding society's Policy-Entity still signs the envelope (the violation is a completed adjudication, not a protocol error); and the caller's Archivist MUST persist it identically to any other R7 outcome. A `violation` is distinct from a §7.6 transport/protocol failure — it indicates the action completed but breached the responding society's rules.

The caller's Archivist (per `society-roles.md` §2.6) MUST persist the signed reputation envelope to the calling society's ledger as part of the audit bundle for this action.

### 7.4 Cross-Society LCT Envelope

When the MCP caller and responder are in different societies, the Web4 Context Headers (§4.1) carry additional cross-society envelope material:

```json
{
  "web4_context": {
    "sender_lct": "lct:web4:entity:...",
    "sender_society": "lct:web4:society:A:...",
    "sender_role": "web4:...",
    "responding_society": "lct:web4:society:B:...",
    "responding_role_expected": "web4:ResourceProvider",
    "cross_society": {
      "interaction_type": "first_contact | established | federated",
      "applicable_law_oracle": "lct:web4:society:A:law-oracle:...  OR  lct:web4:encompassing:law-oracle:...",
      "atp_settlement": {
        "caller_currency": "lct:web4:society:A:atp",
        "caller_amount": 50,
        "responder_currency": "lct:web4:society:B:atp",
        "responder_amount": 70,
        "referent": {
          "kind": "gpu_time",
          "specifier": "A100_80GB",
          "unit": "hour",
          "quantity": 1
        },
        "exchange_agreement_ref": "sha256:..."
      }
    },
    "agency_chain": [ /* per existing §4.1 proof_of_agency */ ],
    "law_hash": "sha256:..."
  }
}
```

**Normative requirements for cross-society LCT envelopes:**

- `sender_society` and `responding_society` MUST both be present; absent these, the call is intra-society and follows §4.1 alone
- `interaction_type` MUST be set: `first_contact` (per `inter-society-protocol.md` §3.1) requires additional discovery exchange before R7 can complete; `established` and `federated` proceed normally
- `applicable_law_oracle` resolves the "whose law applies under cross-society interaction" question by explicit reference. Two patterns are supported:
  - **Caller-law**: sender's Law Oracle governs the call; responder MAY refuse if local law conflicts
  - **Encompassing-law**: when caller and responder share a fractal-encompassing society, that society's Law Oracle governs (per `inter-society-protocol.md` §3.2 Option 3)
- `atp_settlement` MUST be present for cross-society calls with non-zero ATP cost when the two societies use different currencies (see the interim conformance note below for the scope of this MUST while §7.7 is WIP). The settlement block carries both societies' independent valuations of a common referent (per §7.7's referent-grounded model). Implementations MUST populate either:
  - An `exchange_agreement_ref` hash referencing a standing agreement (per §7.7.2 standing-agreement flow), OR
  - Inline `referent` + `caller_amount` + `responder_amount` fields representing a per-transaction negotiation outcome (per §7.7.3 acceptance payload)

  > **Interim conformance note (valid until §7.7 reaches v0.1.0-final):** While §7.7's wire format is marked WIP, implementations that carry the `atp_settlement` block SHOULD populate it using the schema above. Implementations MAY omit `atp_settlement` entirely for cross-society calls where the two societies share a currency or where ATP cost is zero. The MUST applies only to the *presence* of the block when cross-currency settlement is needed; the internal structure stabilizes with §7.7.

**Relationship to §4.1 Web4 Context Headers:**

The cross-society envelope extends — it does not replace — the §4.1 header. The
following reconciles the fields that change shape between the two sections:

- `sender_society` is the cross-society form of §4.1 `society`. For
  cross-society envelopes (`sender_society` and `responding_society` both
  present) `sender_society` carries the sending society's LCT and §4.1
  `society` is omitted. Intra-society calls continue to use §4.1 `society`
  alone and MUST NOT set `sender_society`. A recipient MUST treat
  `sender_society` and §4.1 `society` as the same logical field (sending
  society identity) and MUST NOT require both in one envelope.
- `agency_chain` is the ordered-list form of §4.1 `proof_of_agency`. Each
  element MUST be a §4.1 `proof_of_agency` object (`{grant_id, scope}`),
  ordered from the originating grant to the most recent delegation; a
  single-element `agency_chain` is wire-equivalent to one §4.1
  `proof_of_agency`. The chain MUST be non-empty when present.

### 7.5 Cross-Society Witnessing and R7 Reputation Propagation

Cross-society R7 actions interact with the witness role per `society-roles.md` §4.1. When an entity in Society A acts on a resource in Society B via MCP:

**Witness selection** (in priority order):

1. **Encompassing society's Witness** — when A and B share a fractal-encompassing society D, D's Witness role provides neutral attestation peer to both A and B
2. **Third-society Witness** — when A and B do not share an encompassing D, they MAY invoke witnesses from a third society both trust (selection negotiated at first contact or by standing arrangement)
3. **Bilateral witness** — A and B each provide a Witness; cross-signed attestations record the action in both ledgers
4. **No witness** — low-consequence R6 calls MAY proceed without witnessing; for high-consequence actions, R7 MUST NOT proceed without witnessing (consistent with the §7.3 normative requirement that `reputation.witness_signatures` MUST carry at least one Witness signature for high-consequence actions)

**R7 Reputation propagation** rules:

| `propagation_scope` | Effect |
|---|---|
| `responding_society` | Only Society B's view of the calling entity's T3/V3 updates. A does not record the Reputation in its own ledger. Used for intra-society or low-consequence cases. |
| `caller_society` | Only Society A's view of the responding society / resource updates. B does not record the Reputation. Unusual; when both sides need to record, use the single `both` value below rather than combining scopes (`propagation_scope` is a single enum, not a set). |
| `both` | Both A and B record the signed Reputation envelope to their respective ledgers. A updates its T3/V3 view of B; B updates its T3/V3 view of A's calling entity. Standard for cross-society R7 without an encompassing D. |
| `encompassing_society` | The Reputation also propagates to the encompassing society's ledger and contributes to its society-society trust tensor between A and B. Standard for cross-society R7 within a federation. |

**Society-society trust tensors** (derived data structure):

When R7 Reputation propagates to `encompassing_society` scope across multiple actions, the encompassing society accumulates a `society-society T3/V3 tensor` between A and B. This tensor's structure mirrors the entity-role T3/V3 (three root dimensions, each an RDF sub-graph via `web4:subDimensionOf`) but with the entity-role pair replaced by a society-society pair. The structure is observable to A and B (each can query the encompassing society's view of their relationship) but neither can directly write to it — it's derived from witnessed action outcomes.

This resolves the `inter-society-protocol.md` §9 future-work item "society-society trust tensors": they exist as the accumulated R7-Reputation projection at the encompassing society's scope.

### 7.6 Failure Modes Specific to Cross-Society R7

| Failure | MCP Error Code | Recovery |
|---|---|---|
| Caller's LCT not recognized by responding society | `403 web4_cross_society_unrecognized_lct` | First-contact protocol per `inter-society-protocol.md` §3 |
| Exchange rate stale or absent | `409 web4_cross_society_exchange_invalid` | Renegotiate per inter-society protocol |
| Applicable Law Oracle disagrees with responding society's Law Oracle | `409 web4_cross_society_law_conflict` | If caller and responder share an encompassing society, escalate to its Law Oracle; otherwise no shared authority can adjudicate, so the responder refuses (the caller MAY retry under caller-law if the responder's local law permits) |
| Witness signature required but absent | `412 web4_cross_society_witness_required` | Acquire witness and retry |
| R7 Reputation signature invalid | `400 web4_r7_reputation_invalid` | Responding society's Policy-Entity must re-sign |
| Propagation scope unsupported by responding society | `400 web4_propagation_scope_unsupported` | Caller must request a supported scope |

**Relationship to §7.7.7 error codes**: When §7.7 rate negotiation is in force, its §7.7.7 failure table provides *refined* error codes for the rate-specific sub-domain (e.g., `409 web4_rate_standing_expired`, `409 web4_rate_valuation_mismatch`). These refine the generic `409 web4_cross_society_exchange_invalid` code above. An implementation that does not yet implement §7.7 SHOULD use the §7.6 code for all rate-related failures; an implementation that does implement §7.7 SHOULD use the §7.7.7 codes for failures occurring within the rate negotiation flow and the §7.6 code only for rate failures outside that flow (e.g., a stale rate discovered at action-invocation time without an active negotiation context).

### 7.7 Exchange Rate Negotiation — Referent-Grounded (WIP)

> **STATUS: WIP v0.1.0-draft, 2026-05-14.** This section is incomplete pending fleet review. The architecture (referent-grounding, per-transaction scoping with fallbacks) is settled; the precise message schemas and error semantics may evolve. Implementations SHOULD NOT depend on the wire format until v0.1.0-final.
>
> **Subsection conformance status:**
> - §7.7.1 (architectural premise): **Normative** — the referent-grounded model IS the Web4 model; this is a design invariant, not WIP.
> - §7.7.2 (negotiation flow): **Normative-draft** — role assignments (Treasurer) and flow structure are settled; step numbering may change.
> - §7.7.3 (message format): **Normative-draft** — field semantics are stable; wire-format details (field names, nesting) may evolve before v0.1.0-final.
> - §7.7.4 (what's sovereign): **Normative** — the form-vs-substance boundary is a design invariant.
> - §7.7.5 (per-transaction vs standing): **Informative** — implementation guidance only; no conformance requirements.
> - §7.7.6 (oracle reference): **Informative** — implementation guidance only; no conformance requirements.
> - §7.7.7 (failure modes): **Normative-draft** — error codes are stable identifiers; HTTP status codes and recovery text may evolve.

The existing §7.4 specifies that cross-society MCP calls with non-zero ATP cost carry an `atp_settlement` block with both societies' valuations of a common referent (or a hash referencing a standing agreement). This section specifies *how that rate agreement is arrived at* in a way that preserves society sovereignty (per `inter-society-protocol.md` §4) while enabling implementations to interoperate.

#### 7.7.1 Architectural premise: rates are referent-grounded, not abstract

A common reading of "exchange rate" imports the foreign-exchange market mental model: two societies maintain a floating bilateral rate `ATP_A : ATP_B` independent of any particular transaction, periodically renegotiated, applied uniformly to all cross-society activity. **This is NOT the Web4 model.**

In Web4, exchange rates are **grounded in the substance of the R6/R7 action being performed** — the actual work, resource, or value at stake. The negotiation seeks a **common referent** both societies can independently value, then each settles in its own ATP at its own declared valuation of the referent.

Examples of common referents:
- Kilowatt-hours of energy
- GPU-time (specified hardware class, e.g., "1 hour of A100 80GB")
- CPU-time (specified architecture, e.g., "1 core-hour of Graviton4")
- Storage-time (e.g., "1 TB-month of NVMe storage")
- Senior-engineer attention-hours
- Tokens of a specified foundation model
- Physical commodities (specified by reference standard)
- Bandwidth (e.g., "1 TB of egress")

**Per-transaction scoping is ideal** — each R6/R7 action carries its own rate, anchored to its own referent. This avoids stale market rates, eliminates the maintenance overhead of ongoing rate relationships, and makes disputes tractable by appealing to the physical referent rather than abstract currency politics.

**Standing agreements are practical fallback** — for bulk or recurring transactions, societies MAY negotiate a standing rate with explicit validity window. The standing rate is itself referent-grounded (the agreement names the referent and the rate per unit of referent).

**Oracle reference is third-party fallback** — when two societies cannot independently value the referent (e.g., a referent specific to one society's domain), they MAY reference a third-party Oracle society's published price for the referent. The Oracle's own T3 trust governs how much weight either society places on the reference.

#### 7.7.2 Negotiation flow

The negotiation is conducted between the calling and responding societies' **Treasurer** roles (per `society-roles.md` §2.4) via MCP tool calls. The Treasurer is the role authorized to make and accept rate commitments on behalf of the society's ATP pool.

For a per-transaction negotiation, the flow embeds in the R6/R7 action:

```
1. Calling society's Administrator routes the R7 action to the responder's MCP server
2. Responder's Policy-Entity evaluates the action (per §7.3) — if approved-pending-settlement,
   passes to responder's Treasurer for rate determination
3. Responder's Treasurer proposes a referent + rate (see §7.7.3 message format)
4. Caller's Treasurer evaluates: accept, counter-offer, or reject
5. On acceptance, transaction proceeds with rate locked to the transaction
6. R7 settlement updates both societies' ATP accounts per the agreed rate
```

For a standing-agreement negotiation, the flow is decoupled from any specific transaction:

```
1. Either society's Treasurer initiates with rate proposal for one or more referents
2. Counter-society's Treasurer responds with accept/counter/reject per referent
3. On acceptance, agreement is published to both societies' ledgers with validity window
4. Subsequent R7 actions reference the standing agreement hash (per §7.4 atp_settlement)
```

#### 7.7.3 Message format

Rate proposals, counter-offers, and acceptances are MCP tool calls. The tool name SHOULD be `web4_rate_propose`, `web4_rate_counter`, `web4_rate_accept`, `web4_rate_reject` for spec-conformance, though societies MAY use society-specific tool names that wrap these semantics.

Rate proposal payload:

```json
{
  "rate_proposal": {
    "proposal_id": "uuid:...",
    "scope": "transaction | standing",
    "transaction_ref": "lct:web4:action:...",   // present when scope=transaction
    "validity_window": {                          // present when scope=standing
      "starts": "2026-05-14T00:00:00Z",
      "ends": "2026-06-14T00:00:00Z"
    },
    "referent": {
      "kind": "energy | gpu_time | cpu_time | storage_time | attention | tokens | commodity | bandwidth | custom",
      "specifier": "A100_80GB | Graviton4 | NVMe | senior_engineer | gpt-4 | ...",
      "unit": "kwh | hour | core_hour | tb_month | hour | token | ...",
      "reference_standard": "url:... | doi:... | lct:oracle:..."
    },
    "rate": {
      "amount_in_proposer_atp": 50,
      "per_unit_of_referent": 1
    },
    "proposer_society": "lct:web4:society:A:...",
    "proposer_treasurer": "lct:web4:society:A:treasurer:...",
    "signature": "cose:..."
  }
}
```

Counter-offer payload:

```json
{
  "rate_counter": {
    "counter_id": "uuid:...",
    "responds_to": "uuid:...",   // proposal_id being countered
    "alternative_referent": { /* if proposing different referent */ },
    "alternative_rate": { /* if proposing different rate against same or different referent */ },
    "reason": "referent_not_measurable | valuation_too_low | scope_too_broad | other",
    "responding_society": "lct:web4:society:B:...",
    "responding_treasurer": "lct:web4:society:B:treasurer:...",
    "signature": "cose:..."
  }
}
```

Acceptance payload:

```json
{
  "rate_accept": {
    "accept_id": "uuid:...",
    "accepts": "uuid:...",   // proposal_id or counter_id being accepted
    "agreed_referent": { /* canonical referent */ },
    "agreed_rate_caller_atp": { "amount": 50, "per_unit": 1 },
    "agreed_rate_responder_atp": { "amount": 70, "per_unit": 1 },
    "accepting_society": "lct:web4:society:...",
    "accepting_treasurer": "lct:web4:society:...:treasurer:...",
    "signature": "cose:..."
  }
}
```

Note that the acceptance carries **both societies' valuations** of the same referent — this is the load-bearing property of referent-grounding. Each society settles in its own ATP at its own declared valuation; the agreement records both valuations so that R7 settlement (per §7.3) updates each society's account correctly.

#### 7.7.4 What's society-sovereign (substance)

The spec specifies the *message format* and *protocol flow*. It does NOT specify:

- **What referent a Treasurer proposes** — depends on the work being done and the society's accounting
- **What valuation a Treasurer declares** — per the society's ATP reification policy (per `inter-society-protocol.md` §4)
- **What logic a Treasurer uses to accept, counter, or reject** — bilateral bargaining, market-derived pricing, third-party oracle reference, arbitration, fixed-policy — all are valid strategies
- **How long a Treasurer takes to respond** — society policy; the proposer MAY include a timeout in the proposal but the responder is not obligated to meet it
- **Whether to use per-transaction or standing agreement** — society policy per pair-relationship

This is the same form-vs-substance split that runs through Web4: the protocol specifies how parties communicate; the strategy is sovereign.

#### 7.7.5 Per-transaction vs. standing agreement guidance (informative)

This subsection expands, with implementation rationale, the per-transaction-vs-standing distinction established normatively in §7.7.1; it adds no conformance requirements of its own.

Per-transaction scoping is ideal because:
- No stale rates
- No ongoing rate-relationship maintenance overhead
- Each transaction's rate is anchored to its specific referent (easier to audit, dispute, reproduce)
- Naturally scales to one-off transactions between societies with no prior relationship

Standing agreements are practical when:
- Same referent recurs across many transactions (bulk compute, ongoing service)
- Negotiation latency would exceed transaction value
- Pre-commitment of resources is required before transaction begins
- Operational simplicity outweighs the cost of occasional staleness

As informative guidance (no conformance force), implementations typically default to per-transaction unless the calling Treasurer explicitly references a standing agreement hash. By convention, a standing agreement can be unilaterally terminated by either Treasurer with notice per the agreement's own terms — commonly a 24-hour default where the agreement is silent on its termination notice.

#### 7.7.6 Oracle reference (informative)

This subsection expands the third-party-oracle fallback introduced in §7.7.1; it adds no conformance requirements of its own. When two societies cannot independently value a referent, they may reference a third-party Oracle society. The Oracle publishes prices for common referents via its own MCP server (typically `web4_referent_price` tool). The two negotiating Treasurers each query the Oracle independently and use the returned price as their proposed rate, with explicit `reference_standard` in the proposal naming the Oracle's LCT.

The Oracle's own T3 trust governs how much weight is placed on the reference. Oracle pricing does NOT remove the requirement that each society's Treasurer separately sign the agreement — the Oracle is an input to the negotiation, not the authority. This preserves the anti-hierarchical-by-design property: no Oracle has unilateral authority over what rates two societies use; both societies retain refusal authority.

#### 7.7.7 Failure modes specific to rate negotiation

| Failure | MCP Error Code | Recovery |
|---|---|---|
| Referent not measurable by responding society | `400 web4_rate_referent_unmeasurable` | Counter-offer with alternative referent |
| Referent specifier unrecognized | `400 web4_rate_referent_unknown` | Counter-offer with reference_standard |
| Rate signature invalid | `400 web4_rate_signature_invalid` | Re-sign |
| Timeout exceeded by responder | `408 web4_rate_negotiation_timeout` | Re-propose with longer timeout or abandon |
| Standing agreement expired | `409 web4_rate_standing_expired` | Renegotiate or use per-transaction |
| Acceptance valuation differs from proposal | `409 web4_rate_valuation_mismatch` | Counter-offer with corrected valuation |
| Oracle reference unavailable | `502 web4_rate_oracle_unreachable` | Use different oracle or direct negotiation |

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
        
        return min(total_cost, context.atp_remaining)  # Cap at the session's remaining ATP balance (per §11)
```

### 9.2 Dynamic Pricing (informative)

Prices adjust based on demand and trust.  The modifiers below are
**illustrative society-configurable parameters**, not protocol constants.
§9.1 defines the canonical metering formula; here `high_trust_discount: 0.8`
is the endpoint that §9.1's formula reaches at maximum trust
(T3 average = 1.0 → `1.0 − 1.0 × 0.2 = 0.8`).  A society's pricing
configuration supplies these values; the metering engine applies them per §9.1.

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