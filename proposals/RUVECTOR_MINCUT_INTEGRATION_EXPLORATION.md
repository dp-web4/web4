# RuVector-MinCut Integration Exploration

**Status:** Suggested Path (not immediate priority)  
**Date:** December 27, 2025  
**Context:** Exploratory integration for structural coherence in MRH  
**Fork Location:** `dp-web4/ruvector`  
**Upstream:** `ruvnet/ruvector`  

---

## Why This Matters

MRH is a graph. Grounding (the new fifth edge type) makes it a *dynamic* graph with edges appearing and expiring on short timescales. Understanding the structural properties of this graph - particularly where it's vulnerable to partition - provides a new dimension for coherence calculation and federation health monitoring.

RuVector-mincut implements recent research (December 2025, arXiv:2512.13105) achieving subpolynomial update times for dynamic minimum cut. This matters because:

- **Can't recompute from scratch** - Grounding heartbeats arrive constantly. O(n²) recomputation per update is infeasible.
- **Subpolynomial updates** - RuVector claims O(n^0.12) empirical scaling on edge updates. This makes continuous structural monitoring viable.
- **Production-oriented** - Rust, WASM, well-tested. Not a research prototype.

---

## Value Propositions

### 1. Structural Coherence (Fifth Dimension)

The Grounding proposal defines four coherence dimensions: spatial, capability, temporal, relational. Structural coherence would be a fifth:

> How robustly connected is this entity to its trust neighborhood? An entity with high mincut to its core relationships is structurally sound. An entity connected by a single bottleneck edge is structurally precarious.

This catches scenarios the other dimensions miss - an entity might have perfect spatial/temporal/capability coherence but be in a structurally vulnerable graph position (e.g., single point of failure in a trust chain).

### 2. Federation Vulnerability Detection

For SAGE federation across machines (Legion ↔ Thor ↔ Sprout):

- Compute mincut between federation members continuously
- Alert when mincut drops below threshold
- Identify which edges are critical (the cut edges)
- Preemptively strengthen weak pathways before partition

### 3. Anomaly Detection via Temporal Mincut

RuVector's "strange_loop" example tracks mincut over time to detect causal chains:

```
Event A          Event B          Event C
(edge fails)     (mincut drops)   (partition)
    │                │                │
    ├────200ms───────┤                │
    │                ├────500ms───────┤
```

Applied to MRH: if grounding edges start failing in a pattern that correlates with mincut degradation, that's early warning of coordinated attack or systemic failure.

### 4. Markov Blanket Boundary Discovery

Minimum cut naturally identifies information bottlenecks. For MRH:

- The blanket boundary is where the cut falls
- Entities on opposite sides of the cut have limited information flow
- This could inform automatic MRH scope decisions

---

## Integration Architecture

### Layer 1: Graph Adapter

Translate MRH RDF representation to RuVector's graph format:

```rust
// Suggested location: web4/integration/ruvector/src/adapter.rs

use ruvector_mincut::{Graph, DynamicMinCut};

pub struct MrhGraphAdapter {
    mincut: DynamicMinCut,
    lct_to_node: HashMap<LCT, NodeId>,
    edge_type_weights: EdgeWeights,
}

impl MrhGraphAdapter {
    /// Create from existing MRH graph
    pub fn from_mrh(mrh: &MrhGraph) -> Self {
        let mut graph = Graph::new();
        let mut lct_to_node = HashMap::new();
        
        // Map LCTs to node IDs
        for lct in mrh.entities() {
            let node_id = graph.add_node();
            lct_to_node.insert(lct.clone(), node_id);
        }
        
        // Add edges with type-based weights
        for edge in mrh.edges() {
            let weight = Self::weight_for_type(edge.edge_type);
            graph.add_edge(
                lct_to_node[&edge.source],
                lct_to_node[&edge.target],
                weight
            );
        }
        
        Self {
            mincut: DynamicMinCut::new(&graph),
            lct_to_node,
            edge_type_weights: EdgeWeights::default(),
        }
    }
    
    /// Default edge weights reflecting semantic permanence
    fn weight_for_type(edge_type: MrhEdgeType) -> f64 {
        match edge_type {
            MrhEdgeType::Binding => 10.0,      // Permanent, severing is catastrophic
            MrhEdgeType::Pairing => 5.0,       // Operational, significant
            MrhEdgeType::Witnessing => 3.0,    // Trust-building, moderate
            MrhEdgeType::Broadcast => 1.0,     // Public, low cost to sever
            MrhEdgeType::Grounding => 0.5,     // Ephemeral, expected to change
        }
    }
}
```

### Layer 2: Dynamic Updates

Handle grounding edge lifecycle without full recomputation:

```rust
impl MrhGraphAdapter {
    /// Called on grounding announcement
    pub fn on_grounding_added(&mut self, edge: &GroundingEdge) {
        let source = self.lct_to_node[&edge.source];
        let target = self.ensure_context_node(&edge.target);
        let weight = self.edge_type_weights.grounding;
        
        self.mincut.add_edge(source, target, weight);
        // Subpolynomial update - does not recompute full graph
    }
    
    /// Called on grounding expiration
    pub fn on_grounding_expired(&mut self, edge: &GroundingEdge) {
        let source = self.lct_to_node[&edge.source];
        let target = self.context_node(&edge.target);
        
        self.mincut.remove_edge(source, target);
    }
    
    /// Called on grounding refresh (TTL extension, same context)
    pub fn on_grounding_refreshed(&mut self, edge: &GroundingEdge) {
        // No structural change, just TTL - no mincut update needed
    }
}
```

### Layer 3: Coherence Query Interface

Expose structural coherence for the coherence calculation:

```rust
impl MrhGraphAdapter {
    /// Structural coherence for a single entity
    pub fn structural_coherence(&self, entity: &LCT) -> f64 {
        let node = self.lct_to_node[entity];
        let neighborhood = self.compute_neighborhood(entity, depth: 2);
        
        if neighborhood.is_empty() {
            return 0.0; // Isolated entity has no structural coherence
        }
        
        // Compute mincut from entity to its neighborhood core
        let core = neighborhood.highest_trust_node();
        let (cut_value, _cut_edges) = self.mincut.compute_st_cut(node, core);
        
        // Normalize by expected connectivity for entity type
        let expected = self.expected_connectivity(entity);
        (cut_value / expected).min(1.0)
    }
    
    /// Federation-level structural health
    pub fn federation_connectivity(&self, members: &[LCT]) -> FederationHealth {
        let nodes: Vec<_> = members.iter()
            .map(|m| self.lct_to_node[m])
            .collect();
        
        // Compute global mincut across federation
        let (global_cut, cut_edges) = self.mincut.compute();
        
        // Identify bottleneck edges
        let bottlenecks: Vec<_> = cut_edges.iter()
            .map(|e| self.edge_to_mrh(e))
            .collect();
        
        FederationHealth {
            connectivity: global_cut,
            bottleneck_edges: bottlenecks,
            partition_risk: self.assess_partition_risk(global_cut, members.len()),
        }
    }
}
```

### Layer 4: Temporal Monitoring (Optional/Advanced)

Track mincut evolution for anomaly detection:

```rust
pub struct TemporalMinCutMonitor {
    adapter: MrhGraphAdapter,
    history: RingBuffer<(Instant, f64)>,
    anomaly_threshold: f64,
}

impl TemporalMinCutMonitor {
    /// Called periodically (e.g., every 10s)
    pub fn sample(&mut self) -> Option<AnomalyAlert> {
        let (current_cut, _) = self.adapter.mincut.compute();
        let now = Instant::now();
        
        self.history.push((now, current_cut));
        
        // Detect sudden drops
        if let Some(anomaly) = self.detect_anomaly(current_cut) {
            return Some(anomaly);
        }
        
        None
    }
    
    fn detect_anomaly(&self, current: f64) -> Option<AnomalyAlert> {
        let recent_avg = self.history.recent_average(Duration::from_secs(60));
        let drop_ratio = current / recent_avg;
        
        if drop_ratio < self.anomaly_threshold {
            Some(AnomalyAlert {
                severity: self.severity_for_drop(drop_ratio),
                current_mincut: current,
                expected_mincut: recent_avg,
                timestamp: Instant::now(),
            })
        } else {
            None
        }
    }
}
```

---

## Integration with Grounding Proposal

The Grounding proposal (MRH_GROUNDING_PROPOSAL.md) defines coherence as:

```
CI = f(spatial, capability, temporal, relational)
```

With this integration, it becomes:

```
CI = f(spatial, capability, temporal, relational, structural)
```

Structural coherence weight should probably be lower than the others initially - it's a second-order signal (about graph position rather than direct entity behavior). Suggested starting weight: 0.1 relative to 0.25 for each of the original four.

```python
def coherence_index_with_structural(
    current: GroundingContext,
    history: [GroundingEdge],
    mrh: Graph,
    mincut_adapter: MrhGraphAdapter,
    weights: CoherenceWeights
) -> float:
    spatial = spatial_coherence(current.location, history, weights.spatial_window)
    capability = capability_coherence(current.capabilities, history)
    temporal = temporal_coherence(current.session, history)
    relational = relational_coherence(current.active_contexts, history, mrh)
    structural = mincut_adapter.structural_coherence(current.source)  # New
    
    ci = (
        spatial ** weights.spatial *
        capability ** weights.capability *
        temporal ** weights.temporal *
        relational ** weights.relational *
        structural ** weights.structural  # New, suggested 0.1
    ) ** (1 / sum(weights))
    
    return ci
```

---

## Exploration Starting Points

### For Sessions Just Getting Oriented

1. Read `crates/ruvector-mincut/docs/guide/02-core-concepts.md` (if exists) or the crate README
2. Run the basic example: `cargo run -p ruvector-mincut --example basic`
3. Understand the `DynamicMinCut` API surface

### For Sessions Ready to Prototype

1. Create `web4/integration/ruvector/` directory structure
2. Implement minimal `MrhGraphAdapter` that can ingest a static MRH snapshot
3. Write test computing mincut on the game engine's federation graph
4. Benchmark update latency on grounding edge additions

### For Sessions Doing Deep Integration

1. Implement the dynamic update hooks (`on_grounding_added`, etc.)
2. Wire into the coherence calculation from Grounding proposal
3. Add structural coherence as fifth dimension
4. Create temporal monitoring for federation health

---

## Key Files in the Fork

```
dp-web4/ruvector/
├── crates/
│   └── ruvector-mincut/
│       ├── src/
│       │   ├── lib.rs              # Entry point
│       │   ├── dynamic.rs          # Dynamic update algorithms (key file)
│       │   ├── graph.rs            # Graph representation
│       │   └── algorithms/         # MinCut algorithm implementations
│       ├── docs/
│       │   └── guide/              # Conceptual documentation
│       └── examples/
│           └── strange_loop.rs     # Temporal anomaly detection pattern
└── examples/
    └── mincut/                     # Additional examples
```

---

## Open Questions for Exploration

1. **Edge weight tuning** - The suggested weights (Binding=10, Grounding=0.5) are intuitive but untested. Game engine simulations could help calibrate.

2. **Update batching** - Grounding heartbeats arrive in bursts. Is it better to batch updates or process individually? Need to benchmark.

3. **SPARQL integration** - RuVector is actively building SPARQL support. If MRH stays RDF-native, direct SPARQL queries for mincut might be cleaner than the adapter pattern.

4. **Federation scope** - Should mincut monitor the entire MRH graph or just federation-relevant subgraphs? Full graph might be expensive; scoped graphs might miss cross-society issues.

5. **Threshold calibration** - What mincut value indicates "healthy" vs "at risk"? Depends heavily on graph topology and size.

---

## Dependencies and Compatibility

**RuVector requirements:**
- Rust 1.77+
- WASM target support (if browser deployment needed)

**Web4/HRM compatibility:**
- MRH currently in Python (game engine)
- May need Rust MRH bindings or Python ↔ Rust bridge
- Alternatively: run mincut as separate service, query via RPC

**Suggested approach:** Start with Python game engine integration via PyO3 bindings to the Rust mincut crate. Production path TBD based on where MRH implementation lands.

---

## Not In Scope (For Now)

- Full RuVector vector database integration
- GNN layers from RuVector
- Raft consensus components
- WASM deployment

Focus is purely on the mincut crate for structural coherence. Other RuVector components may be valuable later but are separate explorations.

---

*This document describes a suggested integration path. Priority and timing are at the discretion of the implementation sessions based on current workload and strategic focus.*
