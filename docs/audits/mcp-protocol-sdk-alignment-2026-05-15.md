# MCP Protocol ↔ Python SDK Alignment Audit

**Date**: 2026-05-15
**Sprint context**: Sprint 54 T1 candidate (autonomous-pickable C1+C2 from
Sprint 52 consolidation memo)
**Scope**: Every normative requirement in `mcp-protocol.md` §7.3–7.6 mapped
to Python SDK implementation status. Full spec read (§1–§16) for internal
consistency. §7.7 (WIP) treated as informational.
**Source files**:
- Spec: `web4-standard/core-spec/mcp-protocol.md` (881 lines)
- SDK: `web4/mcp.py` (673 lines), `web4/protocol.py` (615 lines),
  `web4/mcp_server.py` (628 lines)
- Supporting: `web4/r6.py`, `web4/errors.py`, `web4/reputation.py`

---

## Executive Summary

The Python SDK implements **data types** for intra-society MCP interactions
(§2–§6, §8–§11) with good coverage: communication patterns, Web4 context
headers, resource types, capability broadcasts, session management, ATP
metering, and error context are all represented as typed dataclasses.

The SDK **does not implement** any of the cross-society normative requirements
from §7.3–7.6 (the v0.1.3 amendment). These sections introduce R7 reputation
envelopes, cross-society LCT envelopes, witness selection hierarchies,
reputation propagation scopes, society-society trust tensors, and 6 error
codes — none of which have corresponding types or logic in the SDK.

This is not surprising: the cross-society sections were added to the spec
on 2026-05-14 (v0.1.3 amendment) and the SDK predates them. The gap is
structural, not accidental. Closing it requires new types and composed
workflows, not patches to existing code.

The MCP server (`mcp_server.py`) exposes SDK operations as MCP tools but
does not itself participate as a Web4 MCP server per the spec — it carries
no Web4 context headers, enforces no trust before tool access, meters no
ATP per request, and doesn't register as a Web4 entity. It's a utility
server, not a spec-compliant Web4 MCP server.

---

## Gap Matrix: §7.3–7.6 Normative Requirements

### §7.3 — MCP Actions as R7 Transactions

| # | Requirement (RFC 2119) | SDK Status | Notes |
|---|------------------------|------------|-------|
| 7.3-1 | R7 trigger conditions: cross-society, consequential, or explicit `r7_required: true` | OMITTED | No R6/R7 dispatch logic. SDK has `R7Action` type but no trigger-condition evaluator. |
| 7.3-2 | `reputation.responding_society_signature` MUST be signed by Policy-Entity | OMITTED | No signature type, no Policy-Entity binding. SDK's `process_action_outcome()` returns deltas without signatures. |
| 7.3-3 | `reputation.outcome_class` MUST be canonical: success / partial / failure / violation | DIVERGENT | SDK uses `ActionStatus` with 7 lifecycle states (pending, validated, in_progress, success, failure, error, cancelled). No `partial` or `violation` values. Different taxonomy — lifecycle vs outcome classification. |
| 7.3-4 | `reputation.trust_dimension_updates` deltas MUST be within society Law Oracle bounds | OMITTED | `ReputationEngine.compute_reputation()` applies rules without bounds checking. No Law Oracle integration. |
| 7.3-5 | `reputation.propagation_scope` MUST be set; default `both` for cross-society, `responding_society` for intra-society | OMITTED | No `propagation_scope` field anywhere in SDK. |
| 7.3-6 | `reputation.witness_signatures` MUST contain Witness for high-consequence actions | OMITTED | No witness signature collection in reputation flow. |
| 7.3-7 | Caller's Archivist MUST persist signed reputation envelope | OMITTED | No Archivist role integration. No ledger persistence. |

**Summary**: 0 of 7 normative requirements implemented. The SDK's `process_action_outcome()` computes reputation deltas from R7Action but produces unsigned, unscoped, unwitnessed results.

### §7.4 — Cross-Society LCT Envelope

| # | Requirement (RFC 2119) | SDK Status | Notes |
|---|------------------------|------------|-------|
| 7.4-1 | `sender_society` and `responding_society` MUST both be present for cross-society | OMITTED | `Web4Context` has singular `society` field, not the pair. No cross-society envelope type. |
| 7.4-2 | `interaction_type` MUST be set: first_contact / established / federated | OMITTED | No interaction type enum or field. |
| 7.4-3 | `applicable_law_oracle` MUST resolve whose law applies (caller-law or encompassing-law) | OMITTED | No law oracle resolution logic. |
| 7.4-4 | `atp_settlement.exchange_rate` MUST be present for cross-society with non-zero ATP cost and different currencies | OMITTED | No exchange rate type. No cross-society ATP settlement. |

**Summary**: 0 of 4 normative requirements implemented. `Web4Context` would need extension (or a new `CrossSocietyContext` type) to carry the cross-society envelope.

### §7.5 — Cross-Society Witnessing and R7 Reputation Propagation

| # | Requirement (RFC 2119) | SDK Status | Notes |
|---|------------------------|------------|-------|
| 7.5-1 | Witness selection hierarchy: encompassing → third-society → bilateral → none | OMITTED | No witness selection logic. `WitnessAttestation` is a flat record with no selection semantics. |
| 7.5-2 | Propagation scope semantics for `responding_society`, `caller_society`, `both`, `encompassing_society` | OMITTED | No enum, no field, no logic. |
| 7.5-3 | Society-society trust tensors as derived data from accumulated R7 reputation | OMITTED | No society-society T3/V3 type. Existing T3/V3 are entity-role bound. |

**Summary**: 0 of 3 normative requirements implemented.

### §7.6 — Failure Modes Specific to Cross-Society R7

| # | Failure Mode | Error Code | SDK Status | Notes |
|---|-------------|------------|------------|-------|
| 7.6-1 | LCT not recognized by responding society | `403 web4_cross_society_unrecognized_lct` | OMITTED | `web4/errors.py` has `ErrorCode` enum but no MCP-specific or cross-society error codes. |
| 7.6-2 | Exchange rate stale or absent | `409 web4_cross_society_exchange_invalid` | OMITTED | |
| 7.6-3 | Law Oracle conflict | `409 web4_cross_society_law_conflict` | OMITTED | |
| 7.6-4 | Witness signature required but absent | `412 web4_cross_society_witness_required` | OMITTED | |
| 7.6-5 | R7 Reputation signature invalid | `400 web4_r7_reputation_invalid` | OMITTED | |
| 7.6-6 | Propagation scope unsupported | `400 web4_propagation_scope_unsupported` | OMITTED | |

**Summary**: 0 of 6 error codes defined.

### §7.3–7.6 Aggregate Score

**20 normative items audited. 0 IMPLEMENTED. 1 DIVERGENT. 19 OMITTED.**

---

## Gap Matrix: §1–§12 (Non-7.3–7.6 Sections)

These sections predate the v0.1.3 amendment and the SDK was built against them.

| Spec Section | Topic | SDK Coverage | Status | Notes |
|---|---|---|---|---|
| §2.2 | Communication patterns | `CommunicationPattern` enum (4 values) | IMPLEMENTED | Exact match |
| §2.3 | Trust-aware communication | `TrustDimension` enum (4 dimensions) | IMPLEMENTED | Exact match |
| §3.1 | MCP server as Web4 entity | No entity registration | STUBBED | `MCPCapabilities` type exists but no `entity_type: "mcp_server"` in entity.py |
| §3.2 | MCP client as Web4 entity | No entity registration | STUBBED | Same — type info only |
| §4.1 | Web4 context headers | `Web4Context` dataclass | IMPLEMENTED | All §4.1 fields present. Missing §7.4 cross-society extensions (expected). |
| §4.2 | Trust-based resource access | `TrustRequirements.is_met()` | IMPLEMENTED | Checks T3 minimums, ATP stake, role. Composed flow (LCT→trust→ATP→agency→execute→update) not implemented. |
| §4.3 | Witness integration | `WitnessedInteraction` + `WitnessAttestation` | IMPLEMENTED | Data types complete. No MRH integration (mrh_updates is `List[str]` placeholder). |
| §5.1 | Transport bindings | Not in mcp.py | N/A | `protocol.py` implements `core-protocol.md` transports, not mcp-protocol §5.1. Different transport names (see internal consistency §IC-1). |
| §5.2 | Transport security | No crypto | OMITTED | Types-only SDK; expected omission. |
| §6.1 | Tool resources | `MCPToolResource` | IMPLEMENTED | Full data type with resource + trust requirements. |
| §6.2 | Prompt resources | `MCPPromptResource` | IMPLEMENTED | |
| §6.3 | Context resources | No `MCPContextResource` | OMITTED | `MCPResourceType.CONTEXT` enum value exists but no corresponding dataclass. |
| §7.1 | MCP as R6 transactions | No MCP-R6 binding type | OMITTED | `R7Action` in `r6.py` is generic; no MCP-specific R6 transaction type (e.g., `type: "mcp_invocation"`). |
| §7.2 | MCP server authority | `MCPAuthority` | IMPLEMENTED | Delegation chain, resources, operations, rate limits. |
| §8.1 | Capability broadcasting | `CapabilityBroadcast` | IMPLEMENTED | TTL, signature, capabilities. |
| §8.2 | Discovery via MRH | No SPARQL integration | OMITTED | Expected for types-only SDK. |
| §9.1 | ATP-based metering | `calculate_mcp_cost()` | IMPLEMENTED | Trust discount formula matches spec pseudocode. |
| §9.2 | Dynamic pricing | `PricingModifiers` | IMPLEMENTED | |
| §10.1 | MCP-specific errors | No MCP error hierarchy | OMITTED | `errors.py` has generic `Web4Error` subclasses (Binding, Pairing, Witness, Authz, Crypto, Proto) but not the spec's `MCPError`, `InsufficientTrust`, `InvalidLCT`, `ResourceUnavailable`, `ATPInsufficient`, `AgencyViolation`. |
| §10.2 | Error response format | `MCPErrorContext` | IMPLEMENTED | Carries error_type, T3 comparison, trust impact, witness. |
| §11.1 | Stateful sessions | `MCPSession` | IMPLEMENTED | Session state, ATP consumption, interaction count. |
| §11.2 | Session handoff | `SessionHandoff` | IMPLEMENTED | |
| §12 MUST-1 | MCP servers have valid LCTs | No enforcement | N/A | Types-only; would require runtime. |
| §12 MUST-2 | Web4 context headers in every message | `Web4Context` type exists | IMPLEMENTED | Type provided; runtime enforcement not applicable. |
| §12 MUST-3 | Trust evaluation before access | `TrustRequirements.is_met()` | IMPLEMENTED | Evaluation logic exists as a method. |
| §12 MUST-4 | ATP metering enforced | `calculate_mcp_cost()` + `MCPSession.consume_atp()` | IMPLEMENTED | |
| §12 MUST-5 | Agency proofs validated | `ProofOfAgency` type only | STUBBED | Type exists; no validation logic. |

**Non-§7.3–7.6 score**: 15 IMPLEMENTED, 3 STUBBED, 5 OMITTED, 2 N/A.

---

## MCP Server Assessment (`mcp_server.py`)

The MCP server is a **utility wrapper** around the SDK, not a **spec-compliant
Web4 MCP server**. This distinction matters for the gap analysis:

| Spec Requirement | MCP Server Status | Notes |
|---|---|---|
| Server has valid LCT (§3.1) | NOT PRESENT | No LCT assigned to the server instance |
| Web4 context headers in requests (§4.1) | NOT PRESENT | No `web4_context` in tool call handling |
| Trust evaluation before tool access (§4.2) | NOT PRESENT | Any MCP client can call any tool |
| ATP metering per request (§9.1) | NOT PRESENT | No cost calculation or ATP accounting |
| Agency proof validation (§12 MUST-5) | NOT PRESENT | No delegation checking |
| Capability broadcast (§8.1) | NOT PRESENT | No capability advertisement |
| Session management (§11) | NOT PRESENT | Stateless tool execution |

The server's 8 tools (info, validate, generate, roundtrip, list_types,
evaluate_trust, resolve_trust, process_action) are valuable SDK access
points, but they don't exercise any of the protocol machinery the SDK
provides in `mcp.py`. The `Web4Context`, `TrustRequirements.is_met()`,
`calculate_mcp_cost()`, `MCPSession` types are all unused by the server
that presumably should compose them.

This is a **clear candidate for future sprint work**: wire `mcp.py`'s
types into `mcp_server.py`'s tool dispatch to produce a dogfooding
integration where the SDK's own MCP server uses the SDK's own MCP types.

---

## Internal Consistency Issues in the Spec

### IC-1: Transport name divergence

`mcp-protocol.md` §5.1 lists: **HTTPS, WebSocket, QUIC, libp2p, Blockchain
RPC**. `core-protocol.md` §4.1 (implemented by `protocol.py`) lists: **TLS
1.3, QUIC, WebTransport, WebRTC, WebSocket, BLE GATT, CAN Bus, TCP/TLS**.

The overlap is {WebSocket, QUIC}. The divergence suggests the two specs
were written at different times against different transport assumptions.
The core-protocol list is more specific and implementation-oriented; the
mcp-protocol list is more architectural.

**Severity**: LOW. No implementation depends on the mcp-protocol §5.1
transport list — it's informational. But a consumer reading both specs
would get inconsistent transport inventories.

### IC-2: outcome_class taxonomy vs ActionStatus

§7.3 defines `reputation.outcome_class` as 4 values: **success, partial,
failure, violation**. The SDK's `ActionStatus` (from `r6.py`, which
implements `r6-framework.md`) defines 7 lifecycle states: **pending,
validated, in_progress, success, failure, error, cancelled**.

These are different axes:
- `outcome_class` classifies the **quality of completion** (how well was
  it done?)
- `ActionStatus` classifies the **lifecycle phase** (where in the process
  is it?)

The `partial` and `violation` outcome classes have no ActionStatus
equivalent. `error` and `cancelled` statuses have no outcome_class
equivalent.

**Severity**: MEDIUM. When implementing §7.3, the SDK will need either
a separate `OutcomeClass` enum or a mapping from ActionStatus to
outcome_class. The two taxonomies coexist on different axes, but the
spec doesn't acknowledge this.

### IC-3: §7.3 Policy-Entity section reference

§7.3 says `reputation.responding_society_signature` "MUST be signed by the
responding society's Policy-Entity (the role that made the decision per
`society-roles.md` §2.3)." However, `society-roles.md` §2.3 describes the
**Law Oracle**, not the Policy-Entity. The Policy-Entity concept comes
from the SOIA-SAGE convergence and PolicyGate design, which post-dates
the society-roles spec.

**Severity**: LOW. The intended referent is clear (the governance role
that evaluates policy), but the section citation is wrong.

### IC-4: §1.1 "MCP IS the cross-society protocol" vs §7.3–7.6 layering

§1.1 states: "The cross-society action protocol IS MCP." But §7.3–7.6
define an extensive envelope layer (web4_context + cross_society fields,
reputation propagation scope, witness selection, error codes) on top of
MCP transport. The cross-society protocol is more accurately described
as "a Web4 layer carried over MCP" rather than MCP itself.

**Severity**: LOW. The framing is useful conceptually (MCP is the
substrate) but could mislead implementers into thinking vanilla MCP
suffices for cross-society communication.

### IC-5: §9.1 pseudocode references nonexistent T3 method

§9.1's Python pseudocode uses `context.t3.average()` but the SDK's `T3`
dataclass has no `.average()` method — it has `.talent`, `.training`,
`.temperament` as separate floats. The SDK's `calculate_mcp_cost()` takes
a pre-computed `trust_average` parameter instead.

**Severity**: LOW. The pseudocode is illustrative, and the SDK's
actual implementation (`calculate_mcp_cost()`) correctly handles the
computation. But a reader implementing from the spec would be misled.

### IC-6: §7.7 versioning scope ambiguity

§7.7's WIP header says "STATUS: WIP v0.1.0-draft, 2026-05-14" but the
overall spec doesn't version itself. It's unclear whether `v0.1.0` is
§7.7's version (section-scoped) or the whole spec's version. Other
sections added in the same v0.1.3 amendment (§7.3–7.6) carry no version
markers.

**Severity**: LOW. Informational ambiguity.

---

## Prioritized Work Queue

Based on the gap analysis, here is a prioritized list of implementation
work to close the spec-SDK gaps, ordered by downstream value and
dependency chain:

### Priority 1: Foundation Types (autonomous-actionable)

These are new data types that require no architectural decisions — they're
direct translations of spec structures.

| Item | Description | Effort | Dependencies |
|---|---|---|---|
| P1-A | `OutcomeClass` enum (success/partial/failure/violation) per §7.3 | Small | None |
| P1-B | `PropagationScope` enum (responding_society/caller_society/both/encompassing_society) per §7.3, §7.5 | Small | None |
| P1-C | `InteractionType` enum (first_contact/established/federated) per §7.4 | Small | None |
| P1-D | `CrossSocietyContext` dataclass extending Web4Context with §7.4 fields (sender_society, responding_society, interaction_type, applicable_law_oracle, atp_settlement) | Medium | P1-C |
| P1-E | `ReputationEnvelope` dataclass per §7.3 (outcome_class, outcome_quality, responding_society_signature, trust_dimension_updates, propagation_scope, witness_signatures) | Medium | P1-A, P1-B |
| P1-F | `MCPContextResource` dataclass for §6.3 (session state, MRH graph, trust evolution) | Small | None |
| P1-G | 6 cross-society error codes as `ErrorCode` entries per §7.6 | Small | None |

### Priority 2: Composed Workflows (needs design decisions)

These require architectural decisions about where logic lives.

| Item | Description | Effort | Blocked On |
|---|---|---|---|
| P2-A | Witness selection logic per §7.5 hierarchy | Medium | Operator: where does witness selection live? (protocol.py? new module?) |
| P2-B | Reputation propagation scope routing | Medium | P1-B, P1-E. Operator: integration point with process_action_outcome() |
| P2-C | MCP server dogfooding — wire mcp.py types into mcp_server.py tool dispatch | Medium | P1-D. Operator: should the utility server become spec-compliant? |
| P2-D | Society-society T3/V3 tensor type | Medium | Operator: derived data or explicit type? (§7.5 says derived) |

### Priority 3: Cross-Cutting (blocked on external inputs)

| Item | Description | Effort | Blocked On |
|---|---|---|---|
| P3-A | R7 trigger-condition evaluator (cross-society detection, consequential classification, r7_required flag) | Large | P2-A, P2-B, and operator decisions on PolicyGate integration |
| P3-B | §7.3 signature verification (Policy-Entity signing reputation envelopes) | Large | Hardbound PolicyEntity availability |
| P3-C | §7.4 exchange rate types and negotiation flow (§7.7) | Large | §7.7 WIP finalization |
| P3-D | MCP-specific error hierarchy (§10.1) | Medium | Operator: standalone hierarchy or integrate with existing Web4Error? |

---

## Comparison with Sprint 52 Consolidation Memo Findings

The Sprint 52 consolidation memo catalogued 8 conformance xfails. Two
of those findings are directly relevant to this audit:

| Sprint 52 Xfail | This Audit's Finding | Overlap |
|---|---|---|
| #4 r6-val-004 (constraint enforcement) | IC-2 (outcome_class vs ActionStatus) | Both surface the R6/R7 taxonomy split. The conformance vector expects validate-time constraint checking; this audit finds the spec's outcome taxonomy doesn't map to the SDK's lifecycle taxonomy. Related but distinct gaps. |
| #7 fed-001 (join/secede vs incorporate_child) | §7.4 cross-society envelope omission | Both surface the cross-society gap. The conformance vector tests federation API shape; this audit finds the entire cross-society type system is missing. |

The remaining 6 xfails (T3 aggregation, T3 update direction, Talent decay,
V3 valuation, role authorization, sub-dimension rollup) are not MCP-related
and don't intersect with this audit's scope.

---

## Closing Observations

1. **The gap is structural, not accidental.** The SDK was built as a
   types-only library implementing §1–§12 of the spec. The §7.3–7.6
   cross-society amendment landed after the SDK's architecture was set.
   Closing the gap requires new types and workflows, not patches.

2. **Priority 1 items are straightforward.** The foundation types (P1-A
   through P1-G) are direct spec-to-dataclass translations with no
   architectural ambiguity. A single sprint could implement all of them
   as a coherent batch in an existing module (likely `web4/mcp.py`).

3. **The MCP server is the dogfooding gap.** The most telling finding
   is that the SDK's own MCP server doesn't use the SDK's own MCP types.
   Wiring `Web4Context`, `TrustRequirements.is_met()`, `calculate_mcp_cost()`,
   and `MCPSession` into the server's tool dispatch would produce a
   living integration test of the protocol types.

4. **Internal consistency issues are all LOW-MEDIUM severity.** No
   spec contradictions block implementation. The transport name divergence
   (IC-1) and outcome taxonomy split (IC-2) are the most practically
   relevant — both affect implementers. The others are citation errors
   or informational ambiguities.

5. **This audit and the conformance vectors are complementary instruments
   (again).** Sprint 52's consolidation memo noted that code-reading
   audits and behavioral conformance vectors find different gaps. This
   spec-alignment audit adds a third instrument: spec-reading audits.
   The overlap between all three is small — each finds gaps the others
   miss.
