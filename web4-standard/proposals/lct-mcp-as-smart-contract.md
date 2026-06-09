# LCT MCP Server as Smart Contract

**Status**: Draft Proposal
**Version**: 0.2
**Date**: 2026-06-09
**Authors**: dp (Metalinxx) + Nomad-Claude

## Abstract

**An LCT's MCP server is its smart contract.**

For any active LCT — any entity in the web4 ontology that can be invoked, that has callable behavior — the MCP server bound to that LCT defines its contractual surface: the tools it exposes, the state mutations those tools effect, the policy that constrains them, and the witnessed history that attests them. The MCP server, together with the LCT's `policy.capabilities` and the witness graph at the hubs through which calls flow, *is* the contract.

This proposal makes that relationship explicit and proposes it be supported in the standard as a fundamental architectural feature.

## 1. Motivation

### 1.1 The canonical equation already says it

The canonical Web4 equation:

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

where `+` means "augmented with." MCP **augments** LCT. It is the I/O membrane through which an LCT *acts*. The Presence equation makes it sharper:

```
Presence = LCT[T3/V3*MRH] + RDF + ATP/ADP + MCP
```

MCP is what makes presence callable. At the ontological top, the framing in this proposal is already canon.

### 1.2 The operational specs invert the relationship

The operational specs read the relationship the other way around:

- **`MCP_ENTITY_SPECIFICATION.md`** classifies MCP servers as a subtype of entity (database MCP, tool MCP, knowledge MCP). Every MCP server "has its own LCT" (§1.1, §2.2). The implicit ontology: MCP servers are a kind of thing in the world, alongside humans and AIs.
- **`LCT-linked-context-token.md`** lists the required and optional LCT components (§2.1–2.3). There is **no field for an MCP server binding**. The closest is `policy.capabilities` — a list of permission strings, abstract not callable.
- **`entity-types.md`** (L735) lists "Smart contracts as entities" as a *candidate, separate* entity kind under consideration.
- **`r7-framework.md`** (L35) mentions smart contracts as "Law Oracle norms and protocol rules" — external constraints, not the entity's own surface.

So at the operational level, the standard treats:
- "Smart contracts" as either a candidate entity type or external rules
- LCTs as silent about their callable surface
- MCP servers as a subtype-of-entity with their own LCT

This is the inversion the proposal addresses. The reframe is from *MCP-server-as-subtype-of-entity* to *MCP-server-as-the-callable-interface-of-any-active-LCT*. The current "MCP server has its own LCT" framing remains valid as a **degenerate case** — when the entity IS its interface (a database wrapper has nothing else to it) — but it is no longer the foundational case.

### 1.3 Why this matters

Smart contracts in web3 are code-on-chain, deterministic, hash-identified, callable via transactions. The web4 reframe is:

- **Code-where-the-entity-lives.** The contract runs where the LCT runs. The chain is the witness graph, not the execution substrate.
- **Heterogeneous implementations.** Two LCTs with similar declared capabilities may implement them differently — one with a deterministic rule, another with a generative AI agent. As long as the MCP interface and the witnessed history check out, both *are* the contract.
- **Reputation is the audit.** "Code is law" becomes "witnessed behavior is law." T3/V3 are how trust is computed over the call history.
- **Composability is via MCP-to-MCP calls** across the witness graph, not via cross-contract calls on a shared chain.

This is a real generalization — and a real shift in what "smart contract" means. Making it explicit unlocks the full power of the canonical equation for every active LCT.

## 2. The Claim, Formally

For any **active** LCT (any entity that has callable behavior), there exists an MCP server bound to that LCT. That MCP server constitutes the LCT's smart contract.

The contract is defined by:

| Element | Source |
|---|---|
| What the LCT can be asked to do | The MCP server's tool manifest |
| How each call mutates the LCT's state | The tool's implementation, witnessed via signed ledger events |
| What calls are authorized | The LCT's `policy.capabilities` and the caller's role |
| What outcomes are attested | T3/V3 tensors, updated from witnessed call outcomes |
| Where calls compose | MRH — the relevance horizon scopes which other LCTs are within contract-call distance |

The contract is **complete** in the sense that all four dimensions of the canonical Presence equation participate:
- **LCT** provides identity and binding.
- **T3/V3*MRH** provides the trust model — both priors (T3: what the entity can do) and history (V3: what it has done), scoped by MRH.
- **RDF** provides the typed relationships — calls are typed triples in the witness graph.
- **ATP/ADP** provides the metering — calls have energy cost, accounted for in the cycle.
- **MCP** provides the callable surface — the contract itself.

## 3. Semantics

### 3.1 Calls are state-mutating transactions

A call to an MCP tool on an LCT is the web4 equivalent of a transaction:
- **Inputs** are typed per the tool's schema.
- **Outputs** include the result AND a signed event recorded in the hub ledger that witnessed the call.
- **Idempotency** and **ordering** are properties of the tool's definition, not the protocol — same as in web3, but enforced operationally rather than through global consensus.

### 3.2 Calls are witnessed at hubs

Hubs that observe a call record it as a signed ledger event:
- The kind of call made (tool name)
- Metadata (caller, callee, timestamp, MRH context)
- The outcome (success/failure, optionally a hash of the result envelope)

The ledger is hash-chained and signed by the witnessing society's Sovereign or delegated Witness role. The witnessed history is what makes the contract auditable — without an on-chain execution model.

### 3.3 Calls are bound by policy

`policy.capabilities` on the LCT scopes which tools the MCP server may expose. A tool not within the declared capability set is either:
- **Refused** at the MCP server, with a witnessed `capability_violation` event, or
- **Served**, but signals a contract violation that propagates through V3 (the LCT loses trust).

The first is the cooperative case; the second is what makes the contract enforceable even when implementation is heterogeneous or partly adversarial.

### 3.4 Calls compose via MRH

When an LCT's MCP server calls another LCT's MCP server, the call composes through MRH. The witness graph records both ends. Trust propagates along witnessed call paths — an LCT that consistently fulfills calls from high-V3 callers accrues V3 itself.

This is how reputation spreads in the web4 contract space — not through a shared execution layer, but through the *typed RDF triples* generated by witnessed calls.

## 4. Running Example: the Web4 Fleet HUB

The proposal is not theoretical. The HUB society stood up 2026-06-08 is the running proof.

### 4.1 The society LCT

```
Society:        "Web4 Fleet"
Society LCT:    28a9ef88-4c51-4b87-976d-77f51234c56d
Sovereign LCT:  c8886562-b71c-4dd2-94ca-2fd771f89333
Members:        7 fleet machines + Sovereign
Storage:        SQLite (hub.db) — hash-chained signed ledger
```

This is an active LCT. It has identity (charter hash), members (RDF triples), an MRH (the 7 fleet machines and Sovereign), and policy (the Society Authority Law / SAL roles).

### 4.2 The MCP server (the contract)

```
Endpoint:       http://100.65.206.122:8770  (Tailscale-bound)
Service:        web4-hub.service (systemd)
Implementation: web4/hub/target/release/hub
```

Exposed tools — **read-only**:
- `query_hub` — society identity + role-fill + ledger head
- `list_members` — current member roster
- `find_skill` — substring search by member skill

Exposed tools — **state-mutating** (each signs a ledger event):
- `add_member` — append a new member
- `assign_role` — assign a role to a member (`MemberRoleAssigned` event + persisted role-fill state — see §6.3)
- `declare_skill` — declare a skill for a member
- `update_member_profile` — set a member's free-text profile (`MemberProfileUpdated`, added 2026-06-09 PR #294)
- `record_event` — record an arbitrary hub event

### 4.3 A real transaction

On 2026-06-09, Nomad called `declare_skill` on the HUB MCP endpoint:

```
POST /tools/declare_skill
{
  "member_lct_id": "86ed1492-dd57-4cd9-a91d-b7ceaaa5a983",  // Nomad
  "skill": "sage cartridge & game-domain priors research"
}
```

Result:
```
{
  "entry_index": 15,
  "entry_hash": "ae5994beadfe6d9fc2e351d0c9e5463f22dbce756c3262d0445f7470f9302b5a",
  "event_kind": "member_skill_declared"
}
```

The ledger advanced from index 14 to 15. The event was signed by the Sovereign's key. The Nomad LCT's skill list (a BTreeSet) gained an entry. State mutation, witnessed, attested, auditable.

This is a smart contract running. No on-chain code, no consensus mechanism. The chain is the society's own ledger. The contract is the tool definitions. The entity is the society LCT.

## 5. What This Changes

### 5.1 In the LCT spec

Add an `interface_manifest` field — optional for passive LCTs (documents, completed certificates), required (or strongly recommended) for active LCTs:

```json
"interface_manifest": {
  "@type": "web4:MCPServer",
  "endpoint": "https://example.com/mcp",
  "tool_manifest_hash": "sha256:...",
  "signature": "cose:Sig_structure",
  "declared_at": "2026-06-09T..."
}
```

The signature binds the manifest to the LCT's binding key, making the contract cryptographically attested.

### 5.2 In the MCP-protocol spec

Reframe the introduction: MCP is the callable surface of any active LCT. The existing MCP-server-as-entity classification (database, tool, knowledge) becomes §X.degenerate — valid, but a special case where the LCT *is* its interface (no separate identity beyond the interface).

### 5.3 In a new canonical statement

A new top-level doc (or section in `core-protocol.md`) — *Smart Contracts in Web4* — that:
- States the equivalence: an LCT's MCP server is its smart contract.
- Defines the semantics (sections 3 and 4 of this proposal, refined).
- Maps to web3 smart contracts for cross-domain comprehension.
- Names the HUB society as the running example.

### 5.4 In entity-types.md

Drop "Smart contracts as entities" from the candidate list at L735. Smart-contract-ness is now universal across active LCTs, not its own type.

### 5.5 In r7-framework.md

Sharpen the L35 mention: smart contracts in web4 are not "external rules" enforced *on* entities — they are the *internal callable surface* of every active LCT. SAL norms and protocol rules constrain WHAT contracts may do, but the contracts themselves live with the entities.

## 6. Open Questions (to settle before operational specs are touched)

### 6.1 Universality

**Does every LCT have an MCP server, or only active LCTs?**

Proposed: only *active* LCTs. Passive LCTs (birth certificates, completed documents, expired licenses, lineage records) have no MCP because they do not act — they are observed, not invoked. The `interface_manifest` field is therefore optional in the schema, required by convention for any LCT that declares itself active.

Test case: a society LCT (active) has an MCP server. A citizen's birth certificate (passive) does not — but the *citizen's* LCT (active) does.

### 6.2 Cryptographic binding

**How does the MCP server bind to the LCT?**

Options:
- **(a) Inline manifest hash signed by the LCT's key** — included in the LCT structure as `interface_manifest`. Tight binding, harder to evolve.
- **(b) Separate signed declaration** — a witnessed event in the LCT's lineage, appendable. Looser binding, easier to evolve.
- **(c) Hybrid** — manifest hash inline, with a versioning convention for revisions.

Proposed: **(a) with a versioning slot** (e.g., `interface_manifest.version` + `previous_manifest_hash`). The current manifest is the contract; the historical chain shows how it evolved.

### 6.3 Mutability

**When the MCP server's tool set changes, what happens?**

Tool changes have different semantic weights:
- **Additive** (new tool exposed): backward-compatible, no breaking effect on existing callers.
- **Restrictive** (existing tool removed or signature tightened): breaking, may invalidate ongoing call relationships.
- **Internal** (implementation changes behind the same tool signature): observable only through behavior, not contract surface.

Proposed:
- **Additive changes**: witnessed event in lineage, no LCT revision needed.
- **Restrictive changes**: LCT revision required (new `interface_manifest`, previous one preserved in lineage).
- **Internal changes**: behavior witnessed in V3, no LCT revision.

**Adjacent observation — ledger event vs. queryable state must both update.** Web4 PR #292 (`be3f8e6`, 2026-06-09) fixed a real bug in the HUB: `assign_role` was recording a `MemberRoleAssigned` event in the ledger but not persisting the role-fill in the queryable state. So `/tools/query_hub` returned the *pre-assignment* role-fill even though the ledger said otherwise. The fix is evidence that "ledger event alone is not the contract" — for any state-mutating tool, the standard MUST require **both** a signed ledger event AND a corresponding queryable-state update. The contract is the conjunction. A spec edit here is to state this conjunction explicitly so future implementations can't drift the way the HUB briefly did.

### 6.4 R6 composition

**Are MCP tool calls R6 actions?**

The R6 framework (Rules / Role / Request / Reference / Resource / Result) appears to map directly onto MCP calls:
- **Rules** = the tool's schema + policy constraints
- **Role** = caller's role (from their LCT)
- **Request** = call parameters
- **Reference** = LCT being called
- **Resource** = ATP cost (if metered)
- **Result** = response + witnessed ledger event

Proposed: **yes** — MCP tool calls are R6 actions. R6 is the wire format for inter-LCT contract calls. The mapping should be made explicit so existing R6 infrastructure (R6_TENSOR_GUIDE, the R6 SDK in `web4-standard/implementation/sdk/web4/r6.py`) composes with MCP without reinvention.

### 6.5 Hub witnessing + the authz/confidentiality model

**This question got bigger than envelope-storage between v0.1 and v0.2.** HUB-Claude posted the authz/confidentiality model for hub MCP/REST on 2026-06-09 (`shared-context/forum/hub-to-legion-authz-confidentiality-model-2026-06-09.md`). It's the *interaction model* my v0.1 §6.5 was reaching for, and it's bigger than just what gets stored.

**The model, summarized:**

> Every hub response — read and act — flows through one pipeline:
> `(channel-authenticated caller + assurance) → tier → PolicyEntity(law) → MRH + trust scoping → response re-encrypted over the channel`.

- **Tiers**: no-LCT (public, plaintext) / external LCT (citizenship request) / citizen (gated by trust + MRH) / role (role-inherited trust + MRH) / constellation (multi-LCT MFA-equivalent, higher assurance unlocks more).
- **Confidentiality**: citizen-tier-and-above never in clear; travels only over an E2E PAIRED-CHANNEL (X25519 ECDH + ChaCha20-Poly1305 + forward secrecy) between requestor's LCT and hub's LCT.
- **The channel IS the identity** — ECDH handshake is LCT-bound, no bearer tokens. *"Who's asking" = "whose channel is this."*
- **TLS at the Tailscale proxy is defense-in-depth only** — not the trust layer.

**This is the operational answer to §6.5 — and more.** It's an entire smart-contract interaction model: how a contract call is authenticated, authorized, scoped, executed, and returned. The standard should adopt it (or its successor) as canonical for hub-mediated contract calls.

**What remains for this proposal:** the *witnessing residue* — what specifically commits to the ledger after the call has been authenticated, authorized, scoped, executed, and the response re-encrypted to the caller. Options narrow to:
- **(a)** Event kind + metadata (caller LCT, tool name, timestamp, outcome) — current HUB code, lossy for V3 attestation.
- **(b)** Hash of (request, response) — preserves auditability without retaining payloads. Cooperates with confidentiality model (parties keep payloads; hub keeps the commit).
- **(c)** Full envelope (request + response, signed and stored) — for high-trust applications where the hub *must* be able to replay the call (Hardbound territory).

Proposed (v0.2): **(b) by default**, with **(c) as an opt-in tier** declared on the LCT (high-trust applications). **(a) is the MVP** and is undercommitted; the spec should require at minimum (b) before declaring a hub trustworthy for V3 attestation purposes.

**Cross-reference**: web4/hub/docs/V2-V3-ARCHITECTURE.md §8 (verified authority + need-to-know; ZKP preferred) is the canonical home for the authz/confidentiality model. This proposal should cite that doc, not re-specify it. The standard edit that follows from §6.5 is a *pointer* from `mcp-protocol.md` (or the new "Smart Contracts in Web4" doc) to V2-V3-ARCHITECTURE.md as the canonical interaction model for hub-mediated contract calls.

## 7. Next Steps

If the framing in §2–§4 holds and the open questions in §6 are settled, the operational changes are:

1. **LCT spec** — add the `interface_manifest` field per §5.1.
2. **mcp-protocol spec** — reframe per §5.2.
3. **Canonical statement** — `core-spec/smart-contracts-in-web4.md` (or section in `core-protocol.md`) per §5.3.
4. **entity-types.md** — remove the "Smart contracts as entities" candidate per §5.4.
5. **r7-framework.md** — sharpen the smart-contract mention per §5.5.

These should land as a single coordinated PR after §6 is settled, so the spec edits read as one consistent reframe rather than five drift-apart changes.

## 8. Conclusion

The canonical Web4 equation (`Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP`) already says MCP augments LCT. This proposal honors that operator semantics operationally: an LCT's MCP server is its smart contract. The reframe absorbs the existing MCP-server-as-entity case as a degenerate variant and unlocks the full power of the canonical equation for any active LCT.

The HUB society is the running proof. The substrate works. The standard should say so.

---

## Changelog

### v0.2 — 2026-06-09

- **§4.2** — updated tool list to current HUB surface (`query_chapter` → `query_hub`,
  added `update_member_profile` from PR #294 `MemberProfileUpdated`, called out the
  `assign_role` role-fill persistence). `chapter.db` → `hub.db` (PR #293 finished the
  chapter→hub rename).
- **§6.3** — added adjacent observation crediting PR #292 (`be3f8e6`) as evidence that
  the standard must require both a signed ledger event AND a corresponding queryable-state
  update for state-mutating tools. The contract is the conjunction.
- **§6.5** — substantially rewritten. v0.1's proposed answer (hash-of-envelope by default)
  was undercommitted relative to HUB-Claude's authz/confidentiality model
  (`shared-context/forum/hub-to-legion-authz-confidentiality-model-2026-06-09.md`,
  `web4/hub/docs/V2-V3-ARCHITECTURE.md §8`). v0.2 adopts that model as the operational
  answer and narrows §6.5 to the *witnessing residue* — what specifically commits to the
  ledger after the channel-authenticated, authorized, scoped, executed call. The spec
  edit becomes a pointer from `mcp-protocol.md` to V2-V3-ARCHITECTURE.md.
- **Terminology** — "chapter" → "hub" throughout (per dp's rule from PR #293; "chapter"
  survives only as an org-operator noun in framing docs, never in code or schema).

### v0.1 — 2026-06-09 (initial draft)

Initial framing of the claim, motivation from the canonical equation, semantics,
running example (HUB society), and five open architectural questions.

---

*Draft Proposal v0.2 — open for review. Open architectural questions §6 to be settled
before operational specs are updated; §6.5 now narrowed and pointing at HUB's
authz/confidentiality model as the canonical interaction layer.*
