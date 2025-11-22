# Trust Tensor Evolution Visualizer

Interactive demonstration of Web4-style trust dynamics over time.

## What This Shows

This example visualizes how trust between two entities evolves through a sequence of interactions. It captures several key Web4 ideas:

- **Asymmetric trust**
  - Positive interactions increase trust gradually.
  - Negative interactions can decrease trust much more quickly.
- **Temporal memory**
  - Trust is not a static score; it is a history-dependent trajectory.
  - Recent interactions influence the current state more than distant ones.
- **Uncertainty**
  - Early in a relationship, trust is uncertain and volatile.
  - As more interactions occur, certainty increases and the band tightens.
- **Contextual trust (T3)**
  - In full Web4, trust is a role-contextual tensor `T3(entity, role)`.
  - This visualizer focuses on a single relationship as a 1D slice of that tensor.

The green line shows the current trust estimate (from −1: strong distrust to +1: strong trust). The shaded band shows uncertainty: a wide band means low certainty, a narrow band means the system is more sure about its estimate.

## Files

- `index.html` – Main page containing layout and wiring of controls.
- `styles.css` – Visual styling for the demo.
- `trust-dynamics.js` – Simple trust state model and update rules.
- `visualization.js` – D3-based visualization of trust history and uncertainty.
- `IMPLEMENTATION_GUIDE.md` – Design notes and facilitation guide.

## Running the Demo

No build step is required.

1. Open `examples/trust-visualizer/index.html` in a modern browser (Chrome, Edge, Firefox, Safari).
2. Use the buttons to add interactions:
   - **Positive (+)** – successful interaction.
   - **Negative (−)** – failed or harmful interaction.
   - **Neutral (○)** – low-signal interaction.
   - **Random** – random mix of the above.
3. Observe how the trust line and uncertainty band evolve.

If you run a static file server from the repo root, you can also visit the file via `http://localhost:PORT/examples/trust-visualizer/index.html`.

## Trust Dynamics (Simplified)

The core model is implemented in `trust-dynamics.js` as a `TrustState` class:

- State:
  - `value` ∈ [−1, +1] – current trust level.
  - `certainty` ∈ [0, 1] – how confident we are in that estimate.
  - `history` – list of points `{time, value, certainty, outcome, magnitude}`.
- Update rules (simplified T3 temporal dynamics):
  - Positive outcome: move slowly toward +1.
  - Negative outcome: move more aggressively toward −1.
  - Neutral: small drift back toward 0.
  - Any interaction: increases certainty, which also decays slightly over time.

This is intentionally simple and self-contained so it can be understood at a glance during an event. It is compatible in spirit with the `T3Tensor` definition and MRH-based trust propagation in `web4-standard/implementation/reference/mrh_graph.py`, but does not depend on Python code.

## Relation to Web4

- **T3 (Trust Tensor)** – In the standard, T3 is a role-contextual tensor attached to `(entity_lct, role_lct)` pairs.
- **MRH (Markov Relevancy Horizon)** – Trust can propagate across a graph of entities, decaying with distance and role.
- **This demo** – Focuses on a single `(entity, role)` relationship, showing how repeated interactions can build, break, and rebuild trust over time.

Future integrations could:

- Pull real T3 values from the MRH implementation and use them as starting points.
- Visualize multiple entities and paths from `MRHGraph.find_paths` and `propagate_trust`.
- Compare this simplified dynamics with full Web4 trust propagation over an MRH graph.

## Demo Script (for Events)

1. **Initial state**  
   "These entities just met. Neutral trust, low certainty, wide uncertainty band."

2. **Positive streak**  
   "Click Positive a few times. Trust climbs slowly; certainty increases; the band narrows."

3. **Single negative event**  
   "Now click Negative once. Trust drops sharply. Notice how one bad interaction can undo many good ones."

4. **Rebuilding**  
   "Try rebuilding trust with more positive interactions. It recovers, but more slowly than it fell. History matters."

5. **Connect to Web4**  
   "In Web4, this kind of dynamic trust is attached to Linked Context Tokens and specific roles, and can propagate across networks. This visualizer shows a single relationship so we can feel the behavior before diving into tensors and graphs."

---

Built as a Web4 example for the Windsurf + AIC event.
