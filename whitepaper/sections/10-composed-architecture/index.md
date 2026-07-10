# Built on the Foundation

The six primitives of the equation are the alphabet. This section covers the words Web4 spells with them: how actions happen, how roles work, how groups govern themselves, and how meaning survives crossing domains. Each is specified in the standard; each is *composed from* the primitives rather than added beside them.

## The R6/R7 action grammar

Every action in Web4 — from a tool call to a governance decision — has the same anatomy, named **R6**:

```
Rules + Role + Request + Reference + Resource → Result
```

- **Rules** — what governs the action (law, contracts, protocol constraints)
- **Role** — the capacity in which the actor acts (with that role's T3/V3 and permissions)
- **Request** — the explicit intent: what is to be achieved, with acceptance criteria
- **Reference** — the context brought to bear: history, memory, relevant precedent
- **Resource** — what the action consumes (ATP allocation, compute, attention)
- **Result** — what actually happened, signed and witnessed

**R7** extends the grammar with a seventh element as first-class *output*: **Reputation**. The delta between Request and Result feeds back into the actor's T3/V3 tensors — every action doesn't just produce an outcome, it *updates the trust record*. This is the mechanism behind the earlier claim that trust is computed rather than declared: R7 is where the computation happens, one action at a time.

The grammar makes action **auditable by shape**: any observer can ask of any act — under what rules? in which role? requested what? on what basis? at what cost? with what result, and what did it do to reputation?

## Roles as first-class entities

In Web4, a role is not a label on a user — it is an **entity with its own LCT**. "Data Analyst" has presence: its own requirements, its own permission boundaries, and its own accumulated history of who has performed it and how well. When an agent takes on a role, their LCTs pair; performance updates both records — the agent's tensor *in that role*, and the role's own history.

This one move does a lot of work. It is why trust can be role-scoped (the tensor binds to the *pairing*), why delegation is inspectable (authority flows through explicit role links), and why capability markets become possible (roles can be discovered and matched on verifiable history rather than claimed credentials).

## Societies, authority, and law (SAL)

Entities coordinate in **societies**: groups with membership, shared rules, and collective memory. The **Society–Authority–Law** pattern specifies how governance works without a central platform:

- **Society** — a bounded group of LCT-bearing members; an entity in its own right, with its own presence
- **Authority** — delegated, never assumed: specific powers flow to specific roles through explicit, revocable grants (the **AGY** delegation pattern), every grant an inspectable link in the graph
- **Law** — *data, not code comments*: the society's rules are published as inspectable, versioned artifacts that gate actions through the R6 grammar's **Rules** slot. Members can read the law that binds them; enforcement decisions cite the rule they applied

A society's record-keeping runs on **witnessing**: acts are recorded, hash-chained, and counter-signed by members, making the collective memory tamper-evident without requiring a global blockchain. Societies interact with other societies through the same MCP membrane individuals use — governance, like everything else in Web4, is fractal.

Two protocol layers complete the picture. **ACP** (Agentic Context Protocol) extends MCP for agents that *initiate* rather than merely respond — plan, seek approval, execute, record — keeping autonomous action inside the accountability grammar. And **dictionary entities** handle meaning across boundaries: living, LCT-bearing translators between domain vocabularies that accumulate their own trust records as they translate, so that semantic fidelity itself becomes witnessed and measurable ("compression-trust").

*Normative references: [`r6-framework.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/r6-framework.md) · [`r7-framework.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/r7-framework.md) · [`society-roles.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/society-roles.md) · [`web4-society-authority-law.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/web4-society-authority-law.md) · [`acp-framework.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/acp-framework.md) · [`dictionary-entities.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/dictionary-entities.md).*
