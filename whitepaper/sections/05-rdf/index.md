# RDF: The Ontological Backbone

**The question it answers: how do statements mean anything?**

A trust-native internet is, above all, a system of *statements*: "this agent is bound to this hardware," "this role was performed with this competence," "this act was witnessed by these entities." For those statements to be verifiable, they must first be **machine-readable, typed, and composable**. Web4 expresses every relationship as an **RDF triple** — subject, typed predicate, object — using the W3C Resource Description Framework.

## Why an ontology and not a database

The difference matters more than it first appears. A protocol defines message formats; a database holds rows; an **ontology defines what things mean and how they relate**. When Web4 says "trust," it does not mean a number in someone's table — it means a typed relationship in a graph that any RDF-speaking system can query, extend, and reason over.

This is not a metaphor layered over a conventional store; the vocabulary is concrete and published. Web4's statements live under two namespaces — `web4:` for the ontology, `lct:` for presence instances — and the canonical relationships are real predicates with defined semantics:

```turtle
@prefix web4: <https://web4.io/ontology#> .
@prefix lct:  <https://web4.io/lct/> .

lct:alice   web4:boundTo      lct:device-anchor-1 .   # permanent hierarchical attachment
lct:bob     web4:pairedWith   lct:surgeon-role .      # authorized operational connection
lct:carol   web4:witnessedBy  lct:audit-oracle-7 .    # trust through observation
```

Each root predicate fans out into sub-properties — `web4:parentBinding`, `web4:energyPairing`, `web4:timeWitness`, and their siblings, all `rdfs:subPropertyOf web4:hasRelationship` — so a query can ask the coarse question ("is there *any* relationship?") or the precise one ("is there a *witnessing* relationship of the *audit* kind?") against the same graph. Edge metadata (what kind of binding, since when, how many times observed) rides on the triples through RDF reification, so the graph carries not just *that* two entities relate, but the witnessed terms on which they do.

Three properties follow directly:

- **Extensibility without central coordination.** Anyone can add a new trust sub-dimension, a new relationship type, or a new witness kind by adding vocabulary — no core-protocol change, no permission from a registry. This is what keeps the standard small while the ecosystem grows. The pattern that makes this safe is `web4:subDimensionOf`: new terms declare what they refine, so extensions slot *into* the existing graph instead of forking it (the T3/V3 section uses this to make trust itself open-ended).
- **Semantic interoperability.** Web4 statements compose with the existing semantic-web world (W3C vocabularies, SPARQL, linked data) rather than creating another silo. A relevancy query is a SPARQL traversal with a depth bound, not a proprietary API call.
- **Fractal structure.** The same triple pattern describes a sensor reading, a role assignment, and an inter-society treaty. Meaning scales without changing shape.

## Where the backbone shows up

Every other term in the equation is *realized* in RDF. The LCT itself is a JSON-LD node (`@type: web4:LinkedContextToken`) whose identifier resolves into the graph. Its MRH — the relevancy horizon — is exactly the subgraph of typed `boundTo` / `pairedWith` / `witnessedBy` edges rooted at that node, traversable within a bounded depth. Trust and value tensors are RDF sub-graphs rooted at three dimensions each (not fixed vectors), with scores attached as witnessed, timestamped statements. The backbone is why the equation's components interlock instead of merely coexisting: they are all the same graph, viewed from different terms.

*Normative reference: the ontology artifacts at [`web4-standard/ontology/`](https://github.com/dp-web4/web4/tree/main/web4-standard/ontology) (Turtle + JSON-LD), with the relationship vocabulary in [`core-spec/mrh-tensors.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/mrh-tensors.md) and the graph model in [`MRH_RDF_SPECIFICATION.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/MRH_RDF_SPECIFICATION.md).*
