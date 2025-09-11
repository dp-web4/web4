


# MRH Tensor Formal Specification

This document provides the formal specification for the Multi-Relational Hypergraph (MRH) tensor, a core data structure in Web4 used to represent the complex, multi-dimensional relationships between entities. The MRH tensor is a dynamic, evolving representation of trust, built from the accumulation of witnessed interactions.

## 1. MRH Tensor JSON Schema

```json
{
  "mrh_tensor": {
    "entity_lct": "lct:web4:...",
    "links": [
      {
        "target_lct": "lct:web4:...",
        "link_type": "witnessed_by|witnessing|bound_to|paired_with",
        "strength": 0.0-1.0,
        "evidence_count": integer,
        "last_interaction": "iso8601",
        "bidirectional": boolean
      }
    ],
    "trust_metrics": {
      "T3": [capability_dimensions],
      "V3": [value_dimensions]
    },
    "horizon": {
      "max_depth": integer,
      "time_window": "duration",
      "relevance_threshold": 0.0-1.0
    }
  }
}
```

## 2. MRH Tensor Components

### 2.1. `entity_lct`

The Lineage and Capability Token (LCT) of the entity that this MRH tensor describes.

### 2.2. `links`

An array of objects, each representing a link to another entity. Each link object has the following properties:

-   **`target_lct`**: The LCT of the entity that is the target of the link.
-   **`link_type`**: The type of relationship between the two entities. This can be one of `witnessed_by`, `witnessing`, `bound_to`, or `paired_with`.
-   **`strength`**: A floating-point number between 0.0 and 1.0 representing the strength of the relationship.
-   **`evidence_count`**: The number of pieces of evidence that support this link.
-   **`last_interaction`**: The timestamp of the last interaction between the two entities.
-   **`bidirectional`**: A boolean value indicating whether the link is bidirectional.

### 2.3. `trust_metrics`

An object containing the trust metrics for the entity. These metrics are used to evaluate the trustworthiness of the entity in different contexts.

-   **`T3`**: A set of capability dimensions, representing the entity's ability to perform certain actions.
-   **`V3`**: A set of value dimensions, representing the entity's alignment with certain values.

### 2.4. `horizon`

An object that defines the scope of the MRH tensor.

-   **`max_depth`**: The maximum number of hops to consider when traversing the trust graph.
-   **`time_window`**: The time window to consider when evaluating trust.
-   **`relevance_threshold`**: The minimum relevance score for a link to be included in the trust graph.


