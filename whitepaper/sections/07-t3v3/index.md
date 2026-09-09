# T3/V3: The Trust and Value Tensors

**The question they answer: what can an entity be trusted to do — and what is its work worth?**

Presence alone says *who is here*, not *what they're good for*. Web4 measures capability and contribution with two three-dimensional tensors, each dimension itself extensible into finer structure. Both tensors are **required components of every LCT** — they ship inside the presence token, not in a separate reputation service — and, as this section shows, the same tensors are simultaneously *bound into the graph* at entity-role pairs. That dual residence is the design's center of gravity.

## T3 — the Trust Tensor

**T3** captures *capability*: what an entity can be trusted to do, along three root dimensions:

- **Talent** — inherent aptitude for the kind of work
- **Training** — acquired knowledge and demonstrated skill
- **Temperament** — behavioral reliability: consistency, judgment, restraint

## V3 — the Value Tensor

**V3** captures *contribution*: what an entity's output is worth, along three root dimensions:

- **Valuation** — the worth ascribed by those who received the value
- **Veracity** — objective accuracy and reproducibility of what was delivered
- **Validity** — confirmed, witnessed transfer — the value actually arrived

The equation writes the pair as **T3/V3** — trust *verified by* value. Claimed capability is continuously checked against delivered contribution: an entity whose T3 says "expert" but whose V3 record shows little validated value will see the gap; sustained delivery closes it. Verification, not assertion.

## Bound to entity-role pairs, in the graph

There is no "Alice's trust score." The standard is a hard invariant here: implementations **must not** compute global, role-agnostic trust. Tensors exist only within role contexts, and the binding is an RDF fact, not a convention:

```turtle
_:tensor1 a web4:T3Tensor ;
    web4:entity      lct:alice ;
    web4:role        web4:Surgeon ;
    web4:talent      0.95 ;
    web4:training    0.92 ;
    web4:temperament 0.88 .
```

Alice-as-surgeon, Alice-as-reviewer, Alice-as-citizen each accumulate their own tensor from their own witnessed history. (V3 rides on the same pairing: the value tensor derives its entity-role context from the co-located T3 tensor, so "Alice-as-surgeon's delivered value" is the same node in the graph.) A new role starts at minimal trust; competence in one capacity is evidence of nothing in another, and cross-role transfer requires an explicit, inspectable bridge.

## Fractal, not fixed: the open-ended sub-graph

Each root dimension is the root node of an **open-ended RDF sub-graph** of context-specific sub-dimensions, declared with the `web4:subDimensionOf` pattern:

```turtle
analytics:StatisticalModeling a web4:Dimension ;
    web4:subDimensionOf web4:Talent .
analytics:BayesianInference a web4:Dimension ;
    web4:subDimensionOf analytics:StatisticalModeling .   # fractal depth
```

A medical society can refine *Training* into `surgical-technique` and `diagnostic-accuracy` without touching the standard — and so can any other domain, indefinitely deep. Individual scores attach as **witnessed, timestamped statements** (dimension, score, `observedAt`, `witnessedBy`), so every number in a tensor carries its provenance. The shorthand form (`web4:talent 0.85`) is the aggregate of the sub-graph rooted at that dimension; composite scores fold the three roots together with published weights (T3: 0.4/0.3/0.3; V3: 0.3/0.35/0.35).

## How the numbers move

Tensor values change only on **witnessed outcomes**, through two normative paths. The categorical outcome table maps result classes to deltas — a novel success is worth +0.02–0.05 on the relevant capability; an ethics violation costs −0.05 talent and −0.10 temperament. The continuous path adjusts by delivered quality: `delta = 0.02 × (quality − 0.5)`, scaled per dimension (temperament moves slowest — reliability is demonstrated over time, not in a single act). All deltas clamp to [0,1].

Decay is asymmetric by design: unexercised **Training** erodes (−0.001/month), **Temperament** recovers slowly (+0.01/month — the path back from a violation is deliberately longer than the fall), and **Talent never decays** — inherent aptitude is not spent by disuse, and the standard pins this as a protocol invariant guarded by conformance vectors.

At the society scale, R7 transactions emit **reputation deltas** triggered by published Law Oracle rules — which action types, result statuses, and quality thresholds move which dimensions, by how much. Deltas are witnessed (selected from MRH-proximate entities), time-weighted onto a 0.5 neutral baseline with exponential decay, and deliberately **asymmetric**: violation costs are large relative to success gains, so reputation cannot be farmed to launder later coercion. In Web4, trust is not a side effect of the record — computing it *is* the product.

Two honest caveats. First, legacy flat six-dimension schemas from the project's early lineage are reconciled through a normative 6D→3D bridge rather than silently coexisting. Second, the range of V3 **Valuation** is a declared open question in the standard — the specification permits values above 1.0 (exceptional worth), the reference SDK currently clamps to [0,1], and the discrepancy is tracked as an operator decision rather than papered over.

Because the tensors route real decisions (who gets the role, whose output is accepted, where value flows), and because they are always role- and context-scoped, they resist the two classic reputation failures: the global score that follows you where it shouldn't, and the purchased reputation that was never earned.

*Normative reference: [`core-spec/t3-v3-tensors.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/t3-v3-tensors.md) and [`core-spec/reputation-computation.md`](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/reputation-computation.md), with the ontology at [`ontology/t3v3-ontology.ttl`](https://github.com/dp-web4/web4/blob/main/web4-standard/ontology/t3v3-ontology.ttl).*
