# RDF: The Ontological Backbone

**The question it answers: how do statements mean anything?**

A trust-native internet is, above all, a system of *statements*: "this agent is bound to this hardware," "this role was performed with this competence," "this act was witnessed by these entities." For those statements to be verifiable, they must first be **machine-readable, typed, and composable**. Web4 expresses every relationship as an **RDF triple** — subject, typed predicate, object — using the W3C Resource Description Framework.

## Why an ontology and not a database

The difference matters more than it first appears. A protocol defines message formats; a database holds rows; an **ontology defines what things mean and how they relate**. When Web4 says "trust," it does not mean a number in someone's table — it means a typed relationship in a graph that any RDF-speaking system can query, extend, and reason over:

```
Alice  —is-bound-to→        Hardware-Anchor-1
Bob    —is-paired-with→     Surgeon-Role
Carol  —witnessed→          DataAnalysis-Act-7
```

Three properties follow directly:

- **Extensibility without central coordination.** Anyone can add a new trust sub-dimension, a new relationship type, or a new witness kind by adding vocabulary — no core-protocol change, no permission from a registry. This is what keeps the standard small while the ecosystem grows.
- **Semantic interoperability.** Web4 statements compose with the existing semantic-web world (W3C vocabularies, SPARQL, linked data) rather than creating another silo.
- **Fractal structure.** The same triple pattern describes a sensor reading, a role assignment, and an inter-society treaty. Meaning scales without changing shape.

## Where the backbone shows up

Every other term in the equation is *realized* in RDF: trust tensors are RDF sub-graphs (not fixed vectors), relevancy horizons are typed relationship graphs (not access-control lists), and presence tokens link into the graph as first-class nodes. The backbone is why the equation's components interlock instead of merely coexisting.

*Normative reference: the ontology artifacts at [`web4-standard/ontology/`](https://github.com/dp-web4/web4/tree/main/web4-standard/ontology) (Turtle + JSON-LD), with the graph model specified in [`MRH_RDF_SPECIFICATION.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/MRH_RDF_SPECIFICATION.md).*
