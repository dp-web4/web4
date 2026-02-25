# Web4 Validity Protocol v0.1
**Status:** Draft  
**Depends on:** V3 Specification 0.1  

---

# 1. Purpose

The Web4 Validity Protocol defines how entities, agents, models, and dictionaries must emit and verify validity artifacts within the Web4 ecosystem.

It ensures that:

- Trust is artifact-backed.
- Promotions are gated.
- State transitions are contestable.
- Verification remains computationally bounded.

---

# 2. Entity Validity Bundle

Every Web4 entity MUST expose a canonical bundle:

```
entity/
  entity_manifest.json
  events.jsonl
  claims.jsonl
  probe_results.json
  promotion_decision.json
```

---

# 3. Entity Manifest Schema

`entity_manifest.json` MUST include:

- entity_id
- entity_type
- code_hash (if applicable)
- model_hash (if applicable)
- dataset_hash (if applicable)
- parent_entities
- creation_timestamp

---

# 4. Promotion State Machine

Each entity maintains states:

- `candidate`
- `current`
- `deprecated`
- `contested`

Transition from `candidate` → `current` requires:

1. Probe suite pass
2. No invariant violations
3. Recorded `promotion_decision.json`

---

# 5. Probe Requirements

Each entity class defines a minimal probe suite.

Example categories:

- Schema integrity
- Budget compliance (ATP)
- Behavioral stability
- Adversarial resilience
- Resource bounds

Probe execution must be:

- Deterministic
- Replayable
- Cheap (< defined cost threshold)

---

# 6. Contest Mechanism

Any entity may be contested by:

1. Replaying event bundle
2. Running probe suite independently
3. Submitting contradiction artifact

Contested entities transition to `contested` state until resolved.

---

# 7. LCT Integration

Linked Control Tokens (LCTs) carry:

- Pointer to entity_manifest
- Pointer to latest probe_results
- Promotion state
- Validity score (derived from gate history)

Trust derives from repeated probe survival, not narrative claims.

---

# 8. HRM / Agent Integration Example

For an HRM checkpoint:

Bundle includes:

- checkpoint_manifest.json
- probe_results.json
- experience_ids_used
- adapter_hash
- promotion_decision.json

Checkpoint promotion requires:

1. Behavioral probe pass
2. No regression beyond defined threshold
3. Resource compliance maintained

---

# 9. Compliance Rule

Web4 nodes MUST refuse:

- State transitions without validity bundle
- Trust elevation without probe evidence
- Artifact-less claims

---

# 10. Versioning & Evolution

Protocol version must be included in manifest.
Backward compatibility rules apply to probe definitions.
Breaking changes require supermajority policy agreement.

---

# 11. Philosophy

Web4 Validity is:

- Artifact-driven
- Gate-enforced
- Replayable
- Socially legible

Trust becomes the emergent property of structured verification.

