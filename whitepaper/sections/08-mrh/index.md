# MRH: The Markov Relevancy Horizon

**The question it answers: within what context does any of this apply?**

Nothing in Web4 is global — not trust, not authorization, not attention. The **Markov Relevancy Horizon (MRH)** is each entity's zone of relevance: what it can perceive, act on, and be affected by. The equation's central term is `T3/V3 * MRH` — trust *contextualized by* horizon — and the `*` is doing the heaviest lifting in the whole equation.

## The idea

The name borrows deliberately from the Markov property: just as a Markov process's next state depends only on the present state — not the entire past — an entity's *relevant context* is bounded. Not everything everywhere matters to everyone. The MRH makes that boundary explicit, verifiable, and usable:

- What information should reach this entity?
- What actions can it meaningfully take?
- Which other entities fall within its sphere?
- Over what time horizon do its concerns extend?

## Implemented as a graph, not a wall

An MRH is not a perimeter or an access-control list. It is a **typed RDF relationship graph**: entities are nodes; edges carry relationship types (binding, pairing, witnessing, delegation, and others); relevance is computed by *traversal* — what can be reached, through which edge types, within a bounded number of hops. Trust propagates along the same edges with decay: a direct witness relationship carries more weight than one three hops removed.

This gives the horizon three properties a flat boundary cannot have:

- **Asymmetry.** A can be within B's horizon while B is outside A's — delegation and witnessing are directional.
- **Multi-path trust.** Confidence in a distant entity can accumulate along independent graph paths, and be discounted where paths share provenance.
- **Dynamism.** Horizons grow and shrink with demonstrated behavior — a new agent starts narrow and earns reach; a misbehaving one contracts.

## Why the horizon is load-bearing

Two consequences make MRH more than bookkeeping. First, **contextualized trust becomes enforceable**: `T3/V3 * MRH` means the surgeon's tensor simply *does not apply* outside the medical horizon — misapplied reputation is a type error, not a policy violation. Second, **reachability stops implying authorization**: an entity may be network-reachable and still be outside the horizon for an action. In an internet of autonomous agents, that inversion — context as the gate, not connectivity — is the security model.

*Normative reference: [`core-spec/mrh-tensors.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/mrh-tensors.md), with the graph model in [`MRH_RDF_SPECIFICATION.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/MRH_RDF_SPECIFICATION.md).*
