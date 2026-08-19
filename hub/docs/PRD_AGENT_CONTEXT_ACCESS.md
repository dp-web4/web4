# PRD — Scoped Agent Presence and Outward Context Access

**Status:** Draft for review
**Date:** 2026-08-14
**Owner:** dp
**Maintainer:** Hub track
**Relates to:** `PRD_HUB_V2_FEDERATED.md`, `PAIRED-CHANNELS.md`, `V2-V3-ARCHITECTURE.md`, Hestia governance/delegation work

---

## 1. Problem

A person may have one or more long-running AI relationships whose usefulness comes not from the current model alone, but from accumulated context: project history, prior decisions, terminology, working style, personal history, business discussions, unpublished inventions, trust relationships, and the history of the human↔AI interaction itself.

Today that context is usually trapped inside one vendor runtime or one private working environment. Another person cannot safely address that agent as a persistent entity with a deliberately bounded view of the principal's context.

The desired capability is:

> A third party can talk to a persistent agent presence through Hub, but receives only the context, disclosures, tools, and memory effects that the principal has explicitly authorized for that caller, relationship, purpose, and act.

This is not primarily a chat feature. It is a **scope and authority problem turned outward**.

Hestia already asks inwardly:

> What may this agent know, use, and do on behalf of its principal?

Outward context access asks the mirror question:

> What may this caller learn, use, or cause through this agent from the principal's context?

The two must converge on one scope/grant discipline rather than evolve as separate authorization systems.

---

## 2. Load-bearing policy decision

### 2.1 Citizenship is the default floor for non-public context

**Non-public principal context MUST NOT be exposed to a caller merely because the caller can reach the agent.**

The default rule is:

> **Hub citizenship is required before a caller is eligible for any non-public context. Citizenship is necessary, never sufficient. Need-to-know narrows access further.**

A citizen does not receive a generic "member view" of a principal's context. Context access remains least-privilege and relationship-specific.

Examples of material that may require narrower grants even among citizens:

- unpublished patent/invention material
- patent strategy
- business plans and financing discussions
- private partnership discussions
- personal history and private human↔AI conversation material
- sensitive third-party information
- credentials, secrets, internal operational data
- any context whose disclosure would exceed the caller's actual role or purpose

Some of these may be available only to one or two named LCTs, a role with a specific charter, an M-of-N-approved group, or a time-bounded relationship.

### 2.2 No-citizenship access is a separate receptionist surface

A Hub MAY expose a no-citizenship conversational surface, but it is not a low-privilege citizen tier. It is an **explicitly public receptionist projection**.

The receptionist may answer only from a separately designated public corpus and may perform only explicitly public/routing actions such as:

- explain publicly documented projects
- provide public contact/routing information
- state whether a topic is in scope
- explain how to request citizenship or an introduction
- surface public scheduling or intake information if explicitly enabled

The receptionist MUST NOT retrieve from private context and MUST NOT inherit citizen tools, private context scopes, or principal authority.

The safest implementation is a physically/logically separate context projection containing only material already intended for public disclosure.

---

## 3. Product shape

The product introduces a persistent **Agent Presence** reachable through Hub.

The Agent Presence is not a ChatGPT thread, model name, provider account, or process. It is a Web4 entity with its own LCT and durable relationship history.

A runtime fills that presence:

- OpenAI Responses / Conversation runtime
- ChatGPT Workspace Agent
- SAGE
- Claude
- local model
- other future agent runtime

Runtime/version/configuration are attested properties of the Agent Presence, not its identity.

The Agent Presence is connected to callers through existing Hub paired-channel machinery. A pair carries a scoped conversation grant defining which projection of the agent the caller may encounter.

Conceptually:

```text
caller LCT
   |
   | paired channel + ConversationGrant
   v
Hub ---------------------- witnesses relationship / law / metadata
   |
   | encrypted transport
   v
Agent Endpoint / Hestia
   |
   +-- Context Broker
   +-- authority gate
   +-- memory gate
   +-- runtime adapter
          |
          +-- OpenAI / SAGE / Claude / local runtime
```

Hub need not see plaintext conversation content.

---

## 4. Core concepts

### 4.1 Agent Presence

An Agent Presence is a first-class Web4 entity representing the persistent conversational/cognitive presence, independent of runtime.

Minimum properties:

```text
AgentPresence
  lct_id
  owner_or_steward_lct
  published_name
  capability_manifest
  contact_policy
  runtime_attestations[]
  context_manifest_digest
  status
```

The presence may be personally owned, society-owned, role-owned, or autonomous under future law.

### 4.2 ConversationGrant

A paired relationship between caller and Agent Presence carries a `ConversationGrant`.

Minimum fields:

```text
ConversationGrant
  pair_id
  caller_lct
  agent_lct

  standing_requirement
  purpose
  mrh

  context_scope
  disclosure_scope
  tool_scope
  memory_scope

  rate_limit
  token_or_compute_budget
  atp_budget

  valid_from
  expires_at
  revocation_policy

  escalation_policy
  grant_basis
```

The grant answers more than "may these entities communicate?" It answers:

> **Which projection of this agent may this caller encounter, for this purpose, right now?**

### 4.3 Context object

Context MUST be permission-bearing data, not an undifferentiated vector store.

Every retrievable context object needs enough metadata to support authorization before retrieval.

Minimum metadata:

```text
ContextItem
  id
  provenance
  subjects[]
  owner_or_steward
  created_at
  validity / recency

  sensitivity_class
  citizenship_floor
  allowed_roles[]
  allowed_lcts[]
  denied_lcts[]
  purpose_tags[]
  mrh_tags[]

  use_policy
  disclosure_policy
  memory_policy
```

`use_policy` and `disclosure_policy` are intentionally distinct. An implementation may later support cases where context can influence internal reasoning without direct disclosure, but no implementation may claim hard confidentiality if forbidden data is loaded into an externally emitting model invocation without a verified non-disclosure mechanism.

### 4.4 Context Broker

The Context Broker resolves a scoped projection before runtime invocation.

Conceptual call:

```text
retrieve(
  caller_lct,
  agent_lct,
  conversation_grant,
  purpose,
  current_request
) -> AuthorizedContextProjection
```

The broker MUST intersect all applicable constraints and MUST NOT allow one layer to widen another.

---

## 5. Authorization model

Effective access is the strict intersection:

```text
effective access
  = caller identity / presence
  ∩ citizenship / standing
  ∩ ConversationGrant
  ∩ context ACL
  ∩ Agent Presence delegation
  ∩ Hub law
  ∩ runtime / Hestia policy
```

### 5.1 Presence is not citizenship

Proof-of-possession of an external LCT establishes only that a cryptographic endpoint exists.

It does not establish:

- real-world identity claims
- Hub citizenship
- trust
- role
- private context eligibility
- authority

### 5.2 Citizenship is not need-to-know

Citizenship establishes standing within the society. It does not grant broad access to principal context.

A citizen may be eligible for a grant. The grant still specifies scope.

### 5.3 Named grants

The system MUST support grants to:

- named LCTs
- Hub roles
- scoped groups / role-entities
- a citizen satisfying a law predicate
- a bounded pair relationship

Highly sensitive context SHOULD prefer named-LCT or narrowly chartered-role grants over broad role classes.

### 5.4 No authority inheritance

A caller talking to an Agent Presence MUST NOT inherit the principal's or agent's normal authority.

Example: an agent may normally be authorized to edit repositories when acting for its owner. A citizen with a read-only ConversationGrant may ask about code but cannot cause the agent to commit, push, send mail, spend funds, disclose secrets, or alter society state merely because the runtime possesses those tools elsewhere.

Tool authority is a separate intersection:

```text
effective action authority
  = agent delegation
  ∩ caller authority
  ∩ ConversationGrant.tool_scope
  ∩ Hub law
  ∩ Hestia/runtime policy
```

---

## 6. Information-flow requirements

### 6.1 Authorization before retrieval

Private context MUST be filtered before it is supplied to the externally responding runtime.

Prompt text such as "do not reveal X" is not a sufficient hard boundary for sensitive context.

For v1, the security rule is conservative:

> **If a caller is not authorized to receive information from a context class, that context class is not loaded into that externally emitting invocation.**

Later architectures may add separated planner/responder models, confidential-compute mechanisms, or formally bounded transforms, but they do not weaken the v1 rule without explicit review.

### 6.2 Derived information counts as disclosure

The disclosure gate applies to facts inferred or synthesized from restricted context, not only verbatim quotation.

A model cannot answer "I won't quote the private plan, but based on it I think acquisition X will happen next month" to a caller who lacks access to the plan.

### 6.3 Third-party privacy

Context owned by the principal may contain information about other people/entities. Context ACLs MUST support additional stewardship or subject restrictions where required.

---

## 7. Memory model

External conversations produce new context. That new information MUST retain provenance and MUST NOT silently contaminate global agent memory.

Memory targets are distinct:

1. **ephemeral session memory** — dies with the interaction/session
2. **relationship-local memory** — retained for this caller↔agent pair
3. **principal/agent canonical memory** — available across relationships
4. **society/public record** — intentionally published/witnessed state

The default for an external/citizen conversation SHOULD be relationship-local memory.

Promotion from relationship-local into canonical agent/principal memory is a separate governed act with provenance such as:

```text
source = caller_lct
pair_id = ...
observed_at = ...
status = asserted | witnessed | verified
```

A caller's statement does not become truth by being remembered.

---

## 8. Hub responsibilities

Hub owns/witnesses relationship and authority facts, not plaintext cognition.

Hub responsibilities:

- establish caller standing / citizenship
- establish Agent Presence identity
- pair request / acceptance / revocation
- evaluate law for pairing/grant issuance
- store/witness ConversationGrant or its committed representation
- route durable ciphertext
- enforce transport-level tier boundaries
- record consequential metadata/residue
- expose revocation and expiry state
- later meter ATP / reputation signals per law

Hub SHOULD NOT require access to plaintext conversation content.

---

## 9. Hestia / agent endpoint responsibilities

The agent endpoint owns the private execution side:

- hold pair/session secrets
- decrypt inbound messages
- authenticate pair binding
- resolve active ConversationGrant
- request scoped context from Context Broker
- enforce runtime/tool authority
- invoke runtime adapter
- enforce outbound disclosure scope
- select allowed memory target
- encrypt response
- submit witnessed residue / metadata to Hub

This is intentionally analogous to Hestia's existing inward governance role.

---

## 10. Runtime adapter contract

Each runtime adapter should implement one narrow interface, conceptually:

```text
start_or_resume(pair_id, agent_presence, authorized_context)
invoke(message, allowed_tools)
return(response, tool_requests, runtime_receipts)
```

Runtime-specific conversation/session identifiers are private adapter state keyed by the Hub pair.

Examples:

```text
pair_id -> OpenAI conversation_id
pair_id -> Workspace Agent conversation_key
pair_id -> SAGE episodic/session context
```

A runtime adapter MUST NOT make authorization decisions. It receives already-authorized context and already-bounded capabilities.

---

## 11. Receptionist mode

Receptionist mode is a separate capability profile with a deliberately small blast radius.

Requirements:

- no citizenship required
- public corpus only
- no retrieval path to private broker namespaces
- no principal tools except explicit public routing/intake functions
- no canonical-memory writes by default
- strict rate / cost limits
- explicit identification as a public/receptionist projection if relevant to UX
- law-configurable enable/disable

A useful implementation test is destructive in spirit:

> If every private context store and private tool credential disappeared, the receptionist should continue to function identically.

That demonstrates the public surface is not merely policy-separated from private context; it is dependency-separated.

---

## 12. Functional requirements

### FR1 — Agent Presence registration

Hub can register/publish an Agent Presence LCT and capability/contact manifest.

### FR2 — Citizen-gated agent pair request

A citizen can request a paired channel with an Agent Presence. Hub law evaluates whether the pair may be created and whether approval/escalation is required.

### FR3 — Receptionist exception

If Agent Presence law explicitly enables receptionist mode, an external LCT may open only the receptionist relationship/profile without obtaining citizenship.

### FR4 — ConversationGrant issuance

Pair activation produces or binds a ConversationGrant describing context, disclosure, tool, memory, budget, expiration, and escalation scope.

### FR5 — Named need-to-know grant

A principal/operator can grant a specific LCT access to a named context class or MRH without broadening access for other citizens.

### FR6 — Revocation

Revoking citizenship, the pair, the grant, a role, or a context ACL removes future access immediately according to the strictest applicable state.

Existing ciphertext/history retention is governed separately; revocation does not imply retroactive erasure from a caller who already lawfully received information.

### FR7 — Scoped retrieval

Context Broker returns only items authorized by the active caller/grant/purpose combination.

### FR8 — Tool-scope enforcement

Agent runtime can invoke only actions within the effective action-authority intersection.

### FR9 — Relationship-local memory

External/citizen conversation memory can persist for continuity without becoming global canonical context.

### FR10 — Runtime interchangeability

At least two runtime adapters can fill the same Agent Presence without changing caller-facing LCT identity or ConversationGrant semantics.

---

## 13. Non-functional requirements

### Security

- fail closed on unknown/expired/revoked grant
- fail closed when citizenship requirement cannot be established
- private context authorization before retrieval
- no secret material stored in Hub plaintext
- pair payload end-to-end encrypted using existing paired-channel discipline
- runtime adapter cannot widen authority
- context ACL changes are governed/auditable

### Privacy

- Hub need not see plaintext conversation
- context disclosure minimized to relationship MRH
- public receptionist dependency-separated from private context

### Auditability

Without recording private message content, the system can establish at least:

- which caller talked to which Agent Presence
- under which pair/grant/law version
- what context classes were eligible for projection
- what tools/capabilities were available
- whether consequential acts occurred
- when the grant was changed/revoked

Whether to witness per-turn request/response hashes is inherited from paired-channel / smart-contract residue work and SHOULD be reused rather than independently invented.

### Portability

Agent identity, grant semantics, context labels, and memory provenance must not depend on one model vendor.

---

## 14. Threat model / failure cases

### T1 — "Citizen means everything"

**Failure:** member role becomes de facto access to all private principal context.

**Defense:** citizenship only satisfies standing floor; explicit context grant still required.

### T2 — Prompt-only secrecy

**Failure:** private context loaded into model and protected only by instruction.

**Defense:** authorization before retrieval; forbidden context omitted from invocation.

### T3 — Tool authority confused with conversational access

**Failure:** caller convinces agent to exercise owner's normal tools.

**Defense:** per-pair tool_scope intersects owner/agent delegation and caller authority.

### T4 — Memory poisoning

**Failure:** external assertion becomes global agent fact.

**Defense:** relationship-local memory default; governed promotion with provenance.

### T5 — Receptionist escape

**Failure:** external surface reaches private context/tool namespace through a shared retrieval path.

**Defense:** separate public projection and dependency-level isolation.

### T6 — Runtime swap changes policy

**Failure:** switching providers silently changes access semantics.

**Defense:** runtime adapters receive capabilities; they do not decide them. Grant/context policy lives outside runtime.

### T7 — Stale grant after role/citizenship change

**Failure:** cached runtime session continues seeing material after standing is revoked.

**Defense:** grant/standing validated on each turn or against short-lived capability; context projection not permanently copied into unrestricted runtime memory.

---

## 15. Current blockers

### B1 — Canonical context does not yet exist as a permission-labelled substrate

Long-running context is currently distributed across vendor chat history/memory, repositories, documents, Hestia records, and human knowledge.

A Context Broker requires at least a first canonical context manifest and labeling system.

### B2 — Ordinary ChatGPT threads are not externally addressable runtimes

Hub cannot currently inject a message into an arbitrary existing ordinary ChatGPT conversation. Therefore the Agent Presence must remain runtime-independent. API/Workspace-Agent/SAGE runtimes can fill it; ordinary ChatGPT can later synchronize with or participate in the presence through connectors.

### B3 — Pair state lacks outward context grant semantics

Existing paired channels establish relationship/transport but do not yet encode context/disclosure/memory scope.

### B4 — Receptionist vs citizen pairing needs an explicit transport/authorization distinction

External callers currently must not be able to route themselves into citizen-level channel capabilities.

### B5 — Hub plugin seam is not yet the daemon's live dispatch path

Initial agent bridge should therefore live at Hestia/agent endpoint and use existing Hub channel APIs, rather than block on dynamic Hub plugin hosting.

### B6 — Cross-Hub agent relationships depend on federation

V1 may require interaction through the Agent Presence's home Hub. Later, a caller's home Hub and the agent's home Hub may federate the pair.

---

## 16. Proposed implementation phases

### Phase A — Define the permission vocabulary

Before runtime integration:

- ContextItem labels / ACL schema
- ConversationGrant schema
- standing/citizenship predicates
- receptionist profile
- memory targets
- strict-intersection evaluator

Prefer vocabulary reusable by Hestia delegation/tool scope rather than a Hub-only dialect.

### Phase B — Receptionist vertical slice

Build the intentionally easy/safe case first:

```text
external LCT
 -> receptionist pair/profile
 -> public-only context projection
 -> runtime adapter
 -> encrypted response
```

Prove it has no private-context dependency.

### Phase C — Citizen + named need-to-know slice

Use one real Hub citizen and one explicit context grant.

Acceptance case:

- citizen can ask about granted project context
- same citizen cannot retrieve a denied private context class
- another citizen without the named grant cannot retrieve it either
- revocation takes effect on next turn

### Phase D — Tool scoping

Permit one harmless read tool, then one consequential act requiring explicit delegation/escalation. Prove conversational access alone does not grant authority.

### Phase E — Relationship memory

Persist pair-local continuity and add governed promotion to canonical memory.

### Phase F — Multi-runtime continuity

Run the same Agent Presence and same pair first through runtime A, then runtime B. Demonstrate identity, grant, context scope, and relationship memory survive the switch.

### Phase G — Federation

Once R1 federation exists, support caller and Agent Presence living on different sovereign Hubs while preserving both laws and the same need-to-know semantics.

---

## 17. V1 acceptance criteria

V1 is complete when all are true:

1. An Agent Presence has a persistent LCT independent of runtime provider.
2. A no-citizenship caller can interact only with an explicitly enabled receptionist projection containing public context only.
3. A citizen can establish a governed pair with the Agent Presence.
4. Citizenship alone yields no private context; an explicit context grant is required.
5. Two citizens can have different context projections of the same Agent Presence.
6. A named highly-sensitive context class is accessible to one authorized LCT and denied to another citizen.
7. Revoking the grant or citizenship prevents access on the next interaction.
8. The externally responding runtime is never supplied context outside the authorized projection in the tested v1 architecture.
9. Conversational access does not inherit the principal's broader tool authority.
10. Relationship-local memory survives session/runtime restart without becoming global canonical memory.
11. Hub can witness relationship/grant/act metadata without seeing plaintext conversation content.
12. At least two runtime adapters can fill the same Agent Presence while preserving the pair/grant semantics.

---

## 18. Design questions for ruling

1. **Grant representation:** full ConversationGrant witnessed as structured Hub state, or signed capability whose digest is witnessed and whose private detail lives endpoint-side?
2. **Context ACL canonical home:** Hub law/RDF, Hestia vault, dedicated context store, or split metadata/public commitment + private policy detail?
3. **Highly-sensitive grant approval:** owner single-signature by default, or support law-configurable M-of-N from first implementation?
4. **Per-turn audit residue:** witness request/response hashes for every turn, only tool-bearing turns, or configurable by grant/law?
5. **Owner visibility:** may the principal inspect plaintext of caller↔agent conversations, or is that a separate disclosure rule negotiated in the pair? The transport architecture should not silently assume either answer.
6. **Runtime continuity:** what minimum attested state defines "same Agent Presence" across a model/runtime change?
7. **Context-use vs context-disclosure:** v1 uses the conservative rule (do not load what may not be disclosed). What mechanism, if any, is sufficient to relax that later?

---

## 19. Guiding invariant

> **No caller receives a broader view of a principal's context merely because an agent can access it. Context visibility is a governed capability, evaluated per caller, standing, relationship, purpose, and act. Citizenship is the default floor for non-public context; need-to-know narrows from there. A no-citizenship surface, if enabled, is an explicitly public receptionist projection.**

This is the outward-facing counterpart of Hestia's inward authority discipline. The long-term implementation should converge both onto the same scope/grant machinery.
