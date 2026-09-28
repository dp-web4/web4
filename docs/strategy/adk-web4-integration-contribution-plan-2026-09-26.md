# Web4 / Google ADK Integration and Contribution Plan

**Date:** 2026-09-28  
**Status:** strategy / implementation plan  
**Scope:** Web4 integration with Google Agent Development Kit (ADK) and candidate upstream contributions

## 1. Why ADK matters to Web4

Google ADK 2.x is an Apache-2.0, open-source agent runtime with graph workflows, specialist/subagent composition, plugins/callbacks, MCP integration, A2A support, session/state services, evaluation and deployment tooling.

Web4 should not attempt to replace that plumbing.

The opportunity is complementary:

> **ADK answers how agents execute. Web4 answers who acted, under whose authority, with what scope and provenance, under which policy, witnessed by whom, and what happened afterward.**

The strategic objective is therefore:

> **Make Web4 a portable identity / authority / provenance / witnessed-action layer that can sit underneath or alongside ADK without requiring ADK users to adopt the full Web4 ontology.**

SWE-SAGE is the first serious proving ground because it already needs persistent roles, explicit authority, shared societal knowledge, Oracle, and witnessed action while targeting ADK in the Kaggle competition.

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
- core issue **#6099** already occupies much of the generic request / decision / outcome ledger design space;
- core RFC **#7103** already asks for provenance on untrusted tool/MCP context;
- graph `_ToolNode` currently calls `tool.run_async(...)` directly rather than traversing the ordinary model-selected tool callback / confirmation path;
- ADK's plugin callback chain stops at the first non-`None` result, so a later evidence plugin may not observe an earlier denial/override;
- ADK after-tool callbacks can run when a callback/confirmation path prevented actual dispatch, so "after tool" is not by itself proof of execution.

The community repository is also not the obvious first publication venue: maintainer guidance on similar integrations has favored a **standalone package** that can later be listed in ADK's integrations documentation.

**Implication:** do not submit another generic allow/deny governance plugin or parallel receipt schema. Web4's first outward contribution should target the less-occupied A2A delegated-authority seam, while action evidence should interoperate with #6099 and provenance work should contribute to #7103.

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

This remains an important Web4 interoperability slice, but it is **not the first outward contribution target** because ADK #6099 and multiple receipt implementations already occupy much of the surrounding space. Our distinctive delta is delegation binding, separate request/decision/result attribution, audience, and explicit unknown/incomplete outcome semantics.

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

Preferred initial publication shape:

```text
web4-adk/
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
    a2a_delegation.py
    governed_tool.py
    mcp_provenance.py
  tests/
```

Start as a standalone package/repository unless ADK maintainers explicitly prefer another venue. This keeps release cadence and licensing deliberate while still allowing later listing in ADK's integrations catalog or migration of narrow generic hooks upstream.

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

## 5. First outward contribution target: A2A delegated authority

### Goal

Allow an ADK agent to call another agent with a machine-verifiable statement of:

> who is acting, on whose behalf, in what role, with which delegated scope, for which audience, until when.

This is currently the least-occupied Web4-native seam and can be prototyped using existing A2A request/execute interception surfaces without first requiring a core ADK change.

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
    revocation reference/freshness
    signature/proof
```

### Receiver behavior

A receiving ADK/A2A service should:

1. authenticate the transport normally;
2. verify contextual identity/delegation separately;
3. reject authority escalation / invalid narrowing;
4. check audience, expiry, revocation and use-count semantics;
5. apply the receiver's local policy at dispatch;
6. preserve provenance for the peer's claims/results;
7. emit action evidence at the assurance level actually observed.

### Non-goals

- replace A2A;
- replace OAuth/IAM/workload identity;
- require `did:web4`;
- require Web4 trust tensors;
- assume sender-side authorization binds the receiver.

The first adapter should accept pluggable identity/credential backends and make delegation verification useful even when the rest of Web4 is absent.

## 6. Second outward target: AAEP-compatible authority and outcome evidence

### Goal

Implement portable action evidence **in conversation with ADK #6099**, not as a parallel claim that ADK lacks a decision ledger.

The distinctive Web4 contribution is:

```text
persistent actor / role
        |
delegation chain + audience
        |
exact canonical request
        |
separately attributable policy decision
        |
actual dispatch observation
        |
returned / presented result
        |
verified effect OR explicit unknown/incomplete
```

### Seven execution facts

Internally preserve these separately even if the external AAEP profile remains compact:

1. intent;
2. authorization;
3. disposition;
4. dispatch;
5. response;
6. presented result;
7. verified effect.

An `after_tool_callback` observation is not sufficient evidence of dispatch because ADK can reach the after path after an override or confirmation refusal. Plugin order can also suppress later observers.

Prefer relying-boundary instrumentation and non-mutating execution observation where available. Propose a new core hook only if the conformance matrix demonstrates that actual dispatch/return cannot be observed externally.

### Minimal AAEP objects

**Action Request**
- actor entity ID and role;
- workload/session binding;
- delegation reference/chain;
- tool/action + target;
- canonical final argument digest;
- audience;
- nonce;
- issued/expiry;
- requested assurance.

**Policy Decision**
- request ID;
- policy/law version;
- allow / deny / obligations / escalate;
- decision authority/signer;
- expiry/use count.

**Result Evidence**
- request/decision IDs;
- which lifecycle boundary was observed;
- actual dispatched arguments where knowable;
- response/output digest where knowable;
- effect status including `unknown` / `incomplete`;
- witness/observer identity and assurance.

Do not compete on "signed JSON receipt." Cryptography is useful only after the signed semantic boundary is correct.

## 7. Third contribution target: provenance boundary for MCP/tool content

ADK currently has an active need around provenance for untrusted tool/MCP content that may later influence consequential tool calls.

Candidate contribution:

- structured provenance wrapper;
- source entity/tool/request binding;
- "observation vs external claim" classification;
- evidence references;
- taint/provenance propagation into later Action Requests;
- callback/helper for policy engines to inspect that lineage.

ADK core RFC **#7103** already owns this question. Contribute a concrete Web4 use case / fixture there rather than opening a competing RFC:

- informational provenance cannot widen delegated authority;
- source lineage survives MCP -> context -> later request where the framework can preserve it;
- missing/tampered lineage becomes UNKNOWN, not trusted;
- provenance and authorization remain separate.

Request a new core hook only if a working adapter demonstrates a specific provenance field or boundary that ADK currently loses.

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

## 9. Relationship to existing ADK community governance and publication venue

Before every contribution:

1. inspect current `AgentGovernancePlugin`;
2. inspect active delegation/authority PRs;
3. inspect #6099 and signed-receipt work;
4. inspect #7103 for provenance overlap;
5. compose where possible;
6. avoid parallel competing abstractions without a demonstrated semantic gap.

### Publication venue

Default to a standalone `web4-adk` package first unless maintainers request otherwise.

Reasons:

- the community repository currently has significant unmerged backlog;
- similar integrations have been steered toward standalone packages listed in ADK's integrations documentation;
- standalone publication makes the AGPL/Apache/patent decision explicit rather than implicit;
- we can prove interoperability and demand before asking core ADK to absorb an abstraction.

The Google forks remain valuable for source inspection, conformance tests and upstream-ready minimal patches.

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

### Phase A0 — forks and baseline

Completed:

- `google/adk-python` -> `dp-web4/adk-python`;
- `google/adk-python-community` -> `dp-web4/adk-python-community`.

Keep clean upstream remotes and record the pinned source revision used by every conformance run.

### Phase A1 — runnable boundary conformance

Before building the package, measure what ADK actually exposes.

Coverage must include:

- allow / deny;
- synthetic before result;
- confirmation pending/refused/approved;
- tool error and recovered error;
- result rewriting;
- plugin order short-circuit;
- cancellation/retry/resume;
- ordinary tool;
- AgentTool/subagent;
- graph `_ToolNode`;
- MCP;
- A2A.

Record intent, authorization, disposition, dispatch, response, presented result and verified effect separately.

Raise `_ToolNode` behavior upstream as a **question** first: developer-selected graph execution may intentionally differ from model-selected tool execution.

### Phase A2 — standalone A2A delegation prototype

Create the narrow standalone `web4-adk` prototype.

Demonstrate:

1. persistent actor/role identity distinct from ADK session identity;
2. delegated scope attached to an A2A request;
3. audience/expiry/revocation/narrowing checks at the receiver;
4. receiver-side local policy;
5. provenance-bound response;
6. no authority expansion from peer text/content.

No full Web4 runtime requirement.

### Phase A3 — AAEP / #6099 interoperability

Add request / decision / result evidence around the working delegation path.

Explicitly document where this implements or extends the #6099 design:

- separate attribution/signers;
- delegation binding;
- audience;
- unknown/incomplete outcomes;
- distinction between dispatch, presented response and verified effect.

Publish independent test vectors/verifier behavior where possible.

### Phase A4 — provenance contribution through #7103

Add one concrete MCP/context provenance fixture to the standalone package and bring the demonstrated use case to #7103.

Do not claim causal attribution through an LLM. Preserve known source lineage and enforce authority independently.

### Phase A5 — integration listing / external adoption

If the package is useful independently:

- publish under the deliberately selected license;
- add runnable examples/tests;
- seek listing in ADK integrations documentation;
- gather external interoperability feedback.

### Phase A6 — core ADK contribution only where necessary

Core contributions should be minimal enabling hooks demonstrated by the previous phases, e.g.:

- a true dispatch observer unavailable externally;
- lifecycle parity needed for graph nodes;
- A2A metadata carrier loss;
- provenance lost across a tool/LLM boundary.

Follow Google's contribution rule: issue/design discussion first for substantial changes.

### Phase A7 — independent interoperability

Success is not "our plugin works."

Success is:

- another implementation can verify Web4/AAEP evidence;
- an ADK app can consume delegation/evidence without running the full Web4 stack;
- Web4 can consume compatible evidence produced elsewhere;
- A2A/MCP peers preserve identity/authority/provenance without shared framework state.

## 12. SWE-SAGE as proving ground

SWE-SAGE should test ADK as runtime plumbing while preserving SAGE/Web4 semantics.

Map:

| SWE-SAGE | ADK | Web4/SAGE-owned meaning |
|---|---|---|
| Lead | root/coordinator agent | persistent role identity, authority |
| Investigator | specialist/subagent | role-private continuity, evidence acquisition |
| Implementer | specialist/subagent | scoped write authority |
| Reviewer | specialist/subagent | independent context/witness experiment |
| Oracle | specialist/subagent | societal-knowledge synthesis |
| role society | ADK workflow graph | identity/continuity semantics |
| MemoryCoordinator | service/tool | cognitive memory semantics |
| Hestia/Web4 gate | plugin/tool wrapper | law/authority/evidence |
| mailbox/handoff | workflow/event artifact | obligation/provenance semantics |

**Rule:** do not let ADK session state become the definition of identity or memory.

## 13. Near-term deliverables

1. complete the ADK callback/dispatch/graph/A2A conformance matrix;
2. raise the `_ToolNode` governance/confirmation difference upstream as a question, not a bug claim;
3. create the standalone `web4-adk` package/repository only after its license/patent boundary is chosen deliberately;
4. prototype A2A delegation with receiver-side verification and monotonic narrowing;
5. add AAEP-shaped request/decision/result evidence aligned explicitly to #6099;
6. contribute the demonstrated provenance use case to #7103;
7. keep SWE-SAGE as a proving ground without making ADK session state define identity/memory;
8. upstream only the smallest missing hooks proved necessary by running code.

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
