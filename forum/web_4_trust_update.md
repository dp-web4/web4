I've integrated your requested nuance into the WEB4 trust whitepaper. The updated section now clarifies:

1. **Contextual Trust Evaluation** – For each decision, the system evaluates trust in the context of that *specific decision*, not the whole situational model. This involves collapsing the full situational trust tensor into a **decision-relevant sub-tensor** containing only the dimensions pertinent to that decision.

2. **Strategy Selection** – The decision-contextualized trust sub-tensor is then used to determine the most appropriate operational strategy for the given conditions. This ensures that degraded or uncertain inputs directly shape the decision-making approach.

3. **Score Tensor Derivation** – The chosen strategy is applied to further reduce the decision-contextualized sub-tensor into a **score tensor** (which may still be multi-dimensional). This allows for richer action selection than a single scalar score.

4. **Commitment Phase** – The score tensor drives the final selection of an action, including the option to defer or withhold commitment if trust thresholds are not met.

This refinement explicitly shows how WEB4's trust model handles the transition from a broad situational awareness tensor down to a decision-specific, strategy-driven execution — making trust both dynamic and precisely contextualized.

