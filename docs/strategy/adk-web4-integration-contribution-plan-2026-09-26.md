# Web4 / Google ADK Integration and Contribution Plan

**Date:** 2026-09-26  
**Status:** strategy / implementation plan  
**Scope:** Web4 integration with Google Agent Development Kit (ADK) and candidate upstream contributions

## 1. Why ADK matters to Web4

Google ADK 2.x is an Apache-2.0, open-source agent runtime with graph workflows, specialist/subagent composition, plugins/callbacks, MCP integration, A2A support, session/state services, evaluation and deployment tooling.

Web4 should not attempt to replace that plumbing.

The opportunity is complementary:

> **ADK answers how agents execute. Web4 answers who acted, under whose authority, with what scope and provenance, under which policy, witnessed by whom, and what happened afterward.**

The strategic objective is therefore:

> **Make Web4 a portable identity / authority / provenance / witnessed-action layer that can sit underneath or alongside ADK without requiring ADK users to adopt the full Web4 ontology.**

SWE-SAGE, a private competition workspace, is the first serious proving ground: it already needs persistent roles, explicit authority, provenance-bearing shared knowledge and witnessed action, and it targets ADK.

## 2. Current ADK contribution landscape

As of 2026-09-26:

- core: `google/adk-python`;
- official community extensions: `google/adk-python-community`;
- both use Apache-2.0;
- substantial core changes should begin with an issue/design discussion;
- Google requires a Contributor License Agreement (CLA);
- accepted core PRs may be landed internally and mirrored back through Copybara rather than merged directly on GitHub.

Relevant work already exists:

- community `AgentGovernancePlugin` for generic runtime governance;
- open community work on scoped delegation / authorization;
- third-party signed tool-receipt implementations;
- ADK core discussion/issues around durable memory, A2A authentication, and provenance for untrusted tool/MCP content.

**Implication:** do not submit another generic allow/deny governance plugin. Web4's contribution must be narrower and deeper.

## 3. Web4 differentiation

The coherent Web4 chain is:

```text
persistent entity identity
        |
role / contextual identity
        |
scoped + revocable delegation
        |
provenance-bound request/context
        |
policy / society-law decision
        |
consequential effect
        |
witnessed result
        |
adjudication / supersession
        |
contextual trust / reputation
```

Existing ADK/community pieces generally address subsets of this chain. Web4's value is binding the chain end to end.

### 3.1 Persistent identity

ADK agent/session identity is primarily runtime identity.

Web4 can add:

- persistent contextual entity identity (LCT / DID mapping);
- role identity distinct from process/session identity;
- identity continuity across model/runtime replacement;
- workload-principal ↔ contextual-identity binding;
- explicit assurance level.

Non-goal: replace OAuth, SPIFFE, IAM or ADK session IDs.

### 3.2 Delegated authority

Web4 adds:

- delegator / delegatee identity;
- monotonic scope narrowing;
- role-bound authority;
- audience;
- expiry / use count;
- revocation;
- assurance requirement;
- downstream re-delegation chain.

Non-goal: replace transport authentication.

### 3.3 Action evidence / AAEP

Use the existing Agent Action Evidence Profile (AAEP) as the narrow interop slice.

Bind:

```text
Action Request
  -> Policy Decision
  -> Result Evidence
```

with separate signers and explicit request / decision / effect/result identity.

This is the strongest candidate for a Web4 contribution because it is portable, independently verifiable, and does not require the rest of Web4.

### 3.4 Provenance-bearing context

Tool/MCP/A2A content should carry provenance sufficient to distinguish:

- source observation;
- external claim;
- derived claim;
- accepted decision;
- refuted/superseded claim.

For ADK integration this means preserving, where available:

- producing entity;
- tool/peer;
- request ID;
- evidence hash/reference;
- timestamp;
- trust/assurance context;
- authority as informational vs consequential;
- later dispositions.

This directly complements ADK's current work on context-boundary provenance for untrusted tool/MCP content.

### 3.5 Contextual trust

T3/V3-style trust should remain optional and downstream of evidence.

Do not make a composite trust score a prerequisite for basic ADK integration.

First contribution surfaces should work with binary/structured facts:

- identity verified?;
- delegation valid?;
- action in scope?;
- policy allowed?;
- result witnessed?;
- evidence complete?;

Trust/reputation can be an optional derived service later.

## 4. Candidate integration package

Develop a clean integration layer before upstreaming.

Proposed shape:

```text
integrations/adk/
  README.md
  LICENSE                  # explicit license decision; see §10
  web4_adk/
    identity.py
    authority.py
    delegation.py
    provenance.py
    action_evidence.py
    plugin.py
    a2a.py
    mcp.py
    adapters/
      hestia.py
      hub.py
  examples/
    governed_tool.py
    delegated_specialist.py
    mcp_provenance.py
    a2a_delegation.py
  tests/
```

Possible public API:

```python
Web4Plugin(
    identity_provider=...,
    authority_provider=...,
    policy_provider=...,
    evidence_sink=...,
)
```

The plugin should compose with ADK's existing governance plugin rather than replace it.

## 5. First contribution target: Web4 action evidence plugin

### Goal

Produce portable, independently inspectable action evidence around ADK tool execution.

### Lifecycle

```text
ADK agent proposes tool call
        |
resolve persistent actor + role
        |
resolve delegation / authority
        |
before-tool policy decision
        |
Action Request + Policy Decision persisted
        |
ADK executes or refuses
        |
actual result/error observed
        |
Result Evidence persisted
        |
optional witness / ledger anchor
```

### Minimal fields

**Action Request**
- actor entity ID;
- role;
- workload/session principal;
- delegation reference;
- tool/action;
- target;
- canonical argument digest;
- audience;
- nonce;
- issued/expiry;
- requested assurance.

**Policy Decision**
- request ID;
- policy/law version;
- decision: allow / deny / allow-with-obligations / escalate;
- obligations;
- decision authority;
- expiry/use count.

**Result Evidence**
- request ID;
- decision ID;
- actual tool invoked;
- input/output digests;
- success/error/incomplete;
- witness identity;
- sequence/prior-hash where used.

### Differentiation from existing signed receipt work

Do not compete on "signed JSON receipt."

Web4 adds:

- durable actor/role identity;
- delegated authority lineage;
- explicit policy decision object;
- audience/assurance;
- separate signer semantics;
- incomplete/missing evidence state;
- supersession/adjudication;
- trust/reputation derivation downstream.

## 6. Second contribution target: Web4 delegation adapter for ADK/A2A

### Goal

Allow an ADK agent to call another agent with a machine-verifiable statement of:

> who is acting, on whose behalf, in what role, with which delegated scope, for which audience, until when.

### Envelope

Conceptually:

```text
A2A message
  +
Web4 delegation context
    actor
    delegator
    role
    scope
    audience
    expiry
    nonce
    assurance
    chain
    signature/proof
```

### Receiver behavior

A receiving ADK/A2A service can:

1. authenticate the transport normally;
2. verify contextual identity/delegation separately;
3. reject authority escalation;
4. apply local policy/law;
5. emit Action Evidence;
6. retain provenance for the peer's claims/results.

### Non-goals

- replace A2A;
- replace OAuth/IAM;
- require `did:web4`;
- require Web4 trust tensors.

The first adapter should accept pluggable identity/credential backends.

## 7. Third contribution target: provenance boundary for MCP/tool content

ADK currently has an active need around provenance for untrusted tool/MCP content that may later influence consequential tool calls.

Candidate contribution:

- structured provenance wrapper;
- source entity/tool/request binding;
- "observation vs external claim" classification;
- evidence references;
- taint/provenance propagation into later Action Requests;
- callback/helper for policy engines to inspect that lineage.

This is potentially a **core ADK RFC** if current plugin/event metadata cannot carry the needed provenance cleanly.

Do not open a core PR until the community integration demonstrates the concrete missing hook.

## 8. Memory integration

Do not upstream the full SAGE memory architecture.

A useful ADK/Web4 seam is provenance-aware memory records:

```text
content
record kind
contributed_by
source evidence
reviewed_by
supported_by
disputed_by
refuted_by
supersedes
scope / audience
MRH/applicability
```

Possible paths:

1. keep this entirely in SWE-SAGE/Web4;
2. provide an ADK `BaseMemoryService` adapter if it proves independently useful;
3. upstream only generic provenance fields/interfaces after demonstrated need.

Oracle and role-private continuity remain SAGE concepts unless broader ADK demand emerges.

## 9. Relationship to existing ADK community governance

Before every contribution:

1. inspect current `AgentGovernancePlugin`;
2. inspect active delegation/authority PRs;
3. inspect signed-receipt work;
4. compose where possible;
5. avoid parallel competing abstractions without a demonstrated semantic gap.

Likely positioning:

```text
ADK AgentGovernancePlugin
  generic policy enforcement
             |
             +--> Web4 authority/evidence provider
                    identity
                    delegation
                    AAEP evidence
                    provenance
                    witnessed result
```

or, if plugin composition is awkward:

```text
Web4Plugin
  produces identity/authority/evidence context
       |
existing governance plugin
  consumes policy-relevant context
```

## 10. Licensing / IP boundary

This requires deliberate handling.

### ADK

- Apache-2.0;
- Google CLA required for contributions.

### Web4

- repository default: AGPL-3.0-or-later;
- patent notice includes pending claims around witnessed trust verification, governed delegation and hardware-attested accountability;
- commercial licensing exists separately.

### Rule

Do **not** casually copy AGPL Web4 implementation code into an Apache upstream PR.

For upstream/community contribution candidates:

1. define a small independently implementable contract;
2. implement the adapter cleanly for the intended Apache contribution;
3. make the copyright/licensing decision explicit;
4. confirm contributor provenance;
5. ensure any patent implications are deliberate;
6. retain the richer Web4/Hestia/Hardbound implementations in their existing licensing boundary unless explicitly relicensed.

Because MetaLINXX owns relevant Web4 work/patent rights, it can choose to license a narrow adapter permissively while keeping the broader implementation under existing terms; that choice should be explicit per contribution.

## 11. Contribution ladder

### Phase A0 — fork and baseline

Fork:

- `google/adk-python` -> `dp-web4/adk-python`;
- `google/adk-python-community` -> `dp-web4/adk-python-community`.

Clone locally.

Record:

- upstream remotes;
- current ADK versions;
- CLA status;
- build/test commands;
- relevant open issues/PRs.

No Web4 code changes yet.

### Phase A1 — architecture reconnaissance

Map:

- `BasePlugin` callbacks;
- workflow graph lifecycle hooks;
- agent/subagent identity surfaces;
- tool invocation context;
- event metadata;
- memory service interfaces;
- MCP toolset boundaries;
- A2A request/response metadata;
- authentication hooks.

Output:

- exact extension points;
- missing hooks;
- where Web4 can remain external.

### Phase A2 — local Web4/ADK prototype

Build in our tree first.

Demonstrate:

1. persistent Web4 identity mapped to ADK role;
2. delegated scope applied to one tool call;
3. allow/deny/escalate decision;
4. AAEP request/decision/result evidence;
5. result witnessed/verified offline;
6. provenance retained through a specialist/subagent handoff.

Use the private SWE-SAGE workspace as a second host where practical.

### Phase A3 — community contribution

Target `google/adk-python-community` first.

Preferred first artifact:

> **Web4 action evidence + delegated authority integration for ADK**

Requirements:

- narrow scope;
- Apache-compatible contribution;
- no full Web4 ontology dependency;
- tests;
- runnable sample;
- explicit threat/assurance model;
- interoperates with existing governance plugin where possible.

### Phase A4 — A2A integration

Prototype contextual delegation over A2A.

Measure:

- authority propagation;
- monotonic narrowing;
- revocation;
- confused-deputy resistance;
- audience binding;
- provenance across remote response.

Then decide whether this is:

- community plugin only;
- A2A profile/spec proposal;
- ADK core hook request.

### Phase A5 — MCP provenance integration

Prototype provenance wrapping for MCP/tool output.

If the current ADK callback/event contract cannot preserve it end to end, prepare a narrowly scoped core RFC referencing a working external implementation.

### Phase A6 — core ADK contribution only where necessary

Core contributions should be minimal enabling hooks, e.g.:

- metadata carrier unavailable to plugins;
- lifecycle callback missing for graph nodes;
- A2A hook needed to bind delegation context;
- provenance field lost across tool/LLM boundary.

Follow Google's contribution rule: issue/design discussion first for substantial changes.

### Phase A7 — independent interoperability

Success is not "our plugin works."

Success is:

- another implementation can verify Web4/AAEP evidence;
- an ADK app can consume Web4 evidence without running Web4;
- Web4 can consume compatible evidence produced by another implementation;
- A2A/MCP peers can preserve identity/authority/provenance without shared framework state.

## 12. SWE-SAGE as proving ground

SWE-SAGE is private during the active competition; its role design, runtime mapping and
competition packaging live there, not here. What this public plan relies on from it is the
boundary it tests:

- ADK is execution plumbing; persistent role identity, role-private continuity, shared
  knowledge with provenance, and law/authority/evidence are owned outside ADK;
- a fresh ADK process must be able to rehydrate those roles from durable external state;
- ADK session state never becomes the definition of identity or memory.

Findings from it return here only as generic ADK/Web4 results, per SWE-SAGE's own
publication rule.

## 13. Near-term deliverables

1. fork core + community repos;
2. complete ADK extension-point map;
3. build one local governed-tool example against Web4 action evidence;
4. run it in the private SWE-SAGE workspace with two persistent roles;
5. prove offline evidence verification;
6. compare against existing community governance/delegation plugins;
7. choose the first upstream/community issue;
8. open an issue before any substantial PR;
9. keep contribution small enough to review independently of Web4's broader architecture.

## 14. Decision criteria

Proceed toward upstream contribution when:

- the integration solves a problem visible to ordinary ADK users;
- the missing behavior is not already covered by existing plugins;
- the interface is useful without adopting Web4;
- it has a falsifiable security/assurance claim;
- it has tests and independent verification;
- licensing/patent boundaries are explicit.

Keep work in Web4 only when:

- it depends on the full society/trust ontology;
- it depends on Hestia/Hardbound assurance features;
- the interface has not stabilized;
- upstream hooks are sufficient and no ADK change is needed.
