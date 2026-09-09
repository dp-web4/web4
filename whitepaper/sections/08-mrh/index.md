# MRH: The Markov Relevancy Horizon

**The question it answers: within what context does any of this apply?**

Nothing in Web4 is global — not trust, not authorization, not attention. The **Markov Relevancy Horizon (MRH)** is each entity's zone of relevance: what it can perceive, act on, and be affected by. The equation's central term is `T3/V3 * MRH` — trust *contextualized by* horizon — and the `*` is doing the heaviest lifting in the whole equation.

The MRH is not an external structure consulted about an entity. As the LCT section established, it is a **required component inside every LCT** — each presence carries its own horizon, and the horizon travels with the token.

## The idea

The name borrows deliberately from the Markov property: just as a Markov process's next state depends only on the present state — not the entire past — an entity's *relevant context* is bounded. Not everything everywhere matters to everyone. The MRH makes that boundary explicit, verifiable, and usable:

- What information should reach this entity?
- What actions can it meaningfully take?
- Which other entities fall within its sphere?
- Over what time horizon do its concerns extend?

## The three canonical relationships

An MRH is a **typed RDF relationship graph**, and its edges come in exactly three canonical kinds — the same three predicates the RDF section introduced — each with its own trust semantics:

- **`web4:boundTo` — permanent hierarchical attachments.** Parent, child, and sibling bindings: the entity's own hardware anchors, its device constellation, its lineage. Trust flows bidirectionally and strongly — these are the edges an entity cannot disown without ceasing to be itself.
- **`web4:pairedWith` — authorized operational connections.** Pairings to roles and counterparties, created by explicit authorization. Birth-certificate pairings (the citizen role granted at issuance) are permanent; ordinary operational pairings need not be.
- **`web4:witnessedBy` — trust through observation.** The witnessing fabric made graph-shaped. Witness edges carry a *kind* — time, audit, oracle, existence, action, state, quality — plus a running count and a last-attestation timestamp. Trust flows one way: from the witness toward the witnessed, as accumulated corroboration.

Relevance is computed by **traversal**: what can be reached from this LCT's node, through which edge types, within a bounded number of hops. The bound has a default — `horizon_depth: 3` — and it is where the "Markov" in the name becomes literal: beyond the depth bound, relationships are *defined as irrelevant*. Not distrusted — out of scope.

## Trust propagates along the edges

The horizon is not only a filter; it is a medium. Confidence in a distant entity is computed over the paths that reach it, and the standard defines three propagation algorithms a relying party can choose among: **multiplicative** (path trust decays hop by hop, default factor 0.7 — a direct witness outweighs a friend of a friend of a friend), **probabilistic** (independent paths combine noisy-OR style: `1 − ∏(1 − path_trust)` — corroboration along genuinely independent routes accumulates), and **maximal** (the best single path governs). Because paths are graph objects, provenance is inspectable: two paths that secretly share an origin can be discounted as one.

The graph is **dynamic by obligation**, not by convention: the standard requires the MRH to be updated on every new binding, pairing, witness event, revocation, and trust recomputation. Horizons grow and shrink with demonstrated behavior — a new agent starts narrow and earns reach; a misbehaving one contracts.

This gives the horizon three properties a flat boundary cannot have:

- **Asymmetry.** A can be within B's horizon while B is outside A's — delegation and witnessing are directional.
- **Multi-path trust.** Confidence in a distant entity can accumulate along independent graph paths, and be discounted where paths share provenance.
- **Dynamism.** Reach is earned and lost on the record, in both directions.

## Why the horizon is load-bearing

Two consequences make MRH more than bookkeeping. First, **contextualized trust becomes enforceable**. Role-scoped trust queries evaluate *inside* the graph: ask for an entity's trust as a surgeon outside the medical horizon and the defined answer is not "low" — it is 0.0, out of context. `T3/V3 * MRH` means the surgeon's tensor simply *does not apply* elsewhere; misapplied reputation is a type error, not a policy violation. Second, **reachability stops implying authorization**: an entity may be network-reachable and still be outside the horizon for an action. The same scoping disciplines the trust machinery itself — reputation witnesses, for instance, are drawn from MRH-proximate entities rather than the open network. In an internet of autonomous agents, that inversion — context as the gate, not connectivity — is the security model.

*Normative reference: [`core-spec/mrh-tensors.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/mrh-tensors.md), with the graph model in [`MRH_RDF_SPECIFICATION.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/MRH_RDF_SPECIFICATION.md) and the MRH's residence inside the token in [`core-spec/LCT-linked-context-token.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/LCT-linked-context-token.md).*
