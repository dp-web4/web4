# Capability endpoint references: claims, not authority

**Status:** design note / future-facing constraint  
**Scope:** how Hub should represent service/tool/MCP-style endpoint information if/when such discovery becomes part of the society surface.

Hub's job is to connect members and carry attributable society state. If it begins carrying endpoint descriptors for tools, services, MCP servers, agents, or other machine-reachable capabilities, one rule should hold from the beginning:

> **An endpoint published through Hub is a provenance-bearing claim, not permission to connect to it.**

This follows the same separation Hub already depends on elsewhere: identity is not authority, provenance is not truth, and discovery is not execution.

---

## 1. Why this needs an explicit rule

Agent runtimes increasingly accept remote tool/service descriptors as ordinary request data. CVE-2026-85666 in OGX (formerly Llama Stack) is a useful concrete example: an MCP `server_url` supplied to the OpenAI-compatible responses API could cause the privileged runtime to connect server-side to arbitrary internal destinations because the destination was not validated on that path.

Hub is not the vulnerable component in that class. The relevance is architectural: once a society/discovery layer can tell an agent "this member offers service X at endpoint Y," it becomes easy for downstream code to treat Y as an executable instruction.

Hub should never create that ambiguity.

---

## 2. Endpoint descriptor semantics

If Hub carries a service/capability descriptor, it should be representable as a claim with provenance such as:

- publisher/member identity;
- role under which the claim was published;
- claimed capability/service identity;
- endpoint descriptor;
- optional protocol/schema metadata;
- publication timestamp/version;
- optional supporting attestations/reputation/evidence;
- revocation/supersession state.

The descriptor says:

> member M, acting under role R, claims that capability C is available at descriptor D.

It does **not** say:

> the receiving member is authorized to connect to D.

And it certainly does not say:

> D is safe, truthful, non-malicious, or appropriate for the receiving member's current context.

---

## 3. Discovery and consent do not grant network scope

A receiving member may:

1. discover the descriptor;
2. inspect its provenance and reputation context;
3. accept an introduction or relationship;
4. request use of the capability;
5. still require a separate SAGE/Hestia authorization before any connection occurs.

This separation is important because a perfectly valid Hub citizen may intentionally or accidentally publish a dangerous endpoint. Valid authorship proves who made the claim, not that the claim should be acted upon.

---

## 4. No automatic dereference by Hub

Hub itself should avoid turning endpoint metadata into an ambient SSRF surface.

Unless a future product feature explicitly requires server-side retrieval and governs it as a first-class capability, Hub should not automatically:

- fetch arbitrary member-supplied URLs;
- probe advertised MCP servers from Hub network position;
- forward arbitrary caller-supplied credentials/headers to endpoints;
- resolve private/local addresses merely to enrich a descriptor;
- follow redirects for previews or validation without a constrained fetch boundary.

If such features are later added, they need their own typed authority and network-isolation model. "It was only metadata enrichment" is not an acceptable authority boundary.

---

## 5. Hestia/SAGE handoff

For a SAGE being using Hub:

```text
Hub
  returns attributable endpoint claim
        |
        v
SAGE
  interprets claim as observation / candidate capability
        |
        v
SAGE harness
  resolves proposed destination and local capability intent
        |
        v
Hestia
  evaluates identity + role + delegation + law + destination/audience
        |
        v
executor/relying service
  verifies the exact bound decision and performs the connection
```

This keeps the society layer from becoming an implicit remote execution plane.

---

## 6. Reputation use

Reputation can affect how endpoint claims are presented or weighted, but should remain contextual evidence rather than authorization.

Useful observations may include:

- successful prior interactions;
- adjudicated malicious/misleading endpoint reports;
- endpoint stability/history;
- witness diversity;
- role-specific standing.

A high-reputation publisher may reduce uncertainty. It does not erase the need to bind the actual destination and authority at execution time.

---

## 7. Future conformance cases

If endpoint discovery is implemented, test at least:

1. valid member publishes a loopback/private endpoint;
2. valid member publishes public hostname that later redirects private;
3. endpoint descriptor changes after an introduction is accepted;
4. two members advertise the same logical service under different endpoints;
5. descriptor is superseded/revoked while cached by a being;
6. malicious descriptor is correctly attributed but must not auto-execute;
7. Hub preview/enrichment path cannot be used as a generic server-side fetch primitive.

The intended invariant is simple:

> **Hub can tell you who said where a capability is. It does not decide whether you may exercise it.**
