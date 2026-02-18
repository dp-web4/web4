# Glossary of WEB4 Terms

*The language of trust-native intelligence, organized from foundation to frontier.*

---

## Core Terms
*The fundamental building blocks of Web4—master these to understand everything else.*

### Linked Context Tokens (LCTs)
> *"An LCT is a node in a web of witnessed presence—the more links, the more witnesses, the more resilient the presence becomes."*

The reification of presence itself. LCTs are permanently and immutably bound to a single entity (human, AI, organization, role, task, or resource) and are non-transferable. They serve as the cryptographic root of witnessed presence—the foundation from which identity, trust, and reputation emerge over time. A single LCT is only as strong as its links; its resilience grows with each witnessed interaction and cross-linked context. If the entity's participation ends, its LCT is marked void or slashed. LCTs form malleable links to create trust webs, delegation chains, and historical records—the nervous system of Web4.

### Allocation Transfer Packet / Allocation Discharge Packet (ATP/ADP)
> *"Allocation flows through work. Packets carry the proof."*

A biological metaphor made digital. ATP packets exist in "charged" (resources allocated, ready for use) or "discharged" (ADP - work performed, delivery confirmed) states, mirroring cellular energy cycles. Work consumes ATP creating ADP, which carries ephemeral metadata about what work was done and who benefited. When certified as valuable, ADP converts back to ATP with metadata cleared for fresh allocation. This creates an auditable trail where genuine contribution generates genuine value—not mining, not staking, but real work recognized.

**Implementation**: Packets are semifungible tokens that can be implemented as blockchain tokens, local ledger entries, or other locally appropriate means. "Allocation" covers all resource types: energy, attention, work, compute, trust budgets.

### T3 Tensor (Trust Tensor)
> *"Trust emerges from capability demonstrated over time—but only when identity is stable."*

A multi-dimensional metric capturing an entity's trustworthiness. The "T3" name reflects three root dimensions, each serving as a **root node in an open-ended RDF sub-graph** of contextualized sub-dimensions linked via `web4:subDimensionOf`:

- **Talent**: Inherent aptitude or originality
- **Training**: Acquired knowledge and skills
- **Temperament**: Behavioral characteristics and reliability

Any domain can define sub-dimensions without modifying the core ontology. A medical institution defines SurgicalPrecision as a sub-dimension of Talent. A law firm defines ContractDrafting as a sub-dimension of Training. There is no fixed depth—the sub-graph is open-ended.

The root scores are aggregates of their sub-graphs. The shorthand `T3(0.9, 0.95, 0.85)` remains valid as the wide-angle view.

Context-dependent, role-specific, and dynamically updated through actual performance. Trust exists only within entity-role pairs—an entity trusted as a surgeon has no inherent trust as a mechanic. Identity Coherence (see below) acts as a prerequisite **gate**—trust scores from low-coherence states are discounted or invalidated.

**Note**: Identity Coherence, Witness Count, Lineage Depth, and Hardware Binding Strength are tracked as LCT-level properties, not T3 sub-dimensions.

### V3 Tensor (Value Tensor)
> *"Value is not declared but demonstrated, not claimed but confirmed."*

A three-dimensional metric quantifying created value, following the same fractal RDF pattern as T3:
- **Valuation**: Subjective worth to the recipient
- **Veracity**: Objective accuracy and reproducibility
- **Validity**: Confirmation of actual value transfer

Each root can be refined with domain-specific sub-dimensions via `web4:subDimensionOf`—for example, Veracity might decompose into ClaimAccuracy and Reproducibility. Together with T3, enables nuanced assessment beyond simple ratings.

### Markov Relevancy Horizon (MRH)
> *"The MRH is how an entity knows where it belongs in the universe of relevance."*

Each entity's contextual lens defining what is knowable, actionable, and relevant within their scope. Not a wall but a gradient—a fuzzy boundary ensuring entities engage where they're most effective. Implemented as an RDF graph with typed edges (binding, pairing, witnessing), enabling SPARQL queries and graph-based trust propagation. Dimensions include fractal scale, informational scope, geographic scope, action scope, and temporal scope.

### Ontology (Web4)
> *"Web4 is not infrastructure—it's an ontology."*

A formal structure of typed relationships (RDF triples) through which trust, identity, and value are expressed. Where a protocol defines message formats, an ontology defines what things *mean* and how they relate. The T3/V3 ontology is formally defined in `t3v3-ontology.ttl` (Turtle/RDF) with a companion JSON-LD context (`t3v3.jsonld`) for interoperability.

### RDF (Resource Description Framework)
> *"The backbone that makes relationships machine-readable."*

The W3C standard for expressing relationships as typed subject-predicate-object triples. Web4 uses RDF as its ontological backbone: trust tensors, MRH edges, role bindings, and sub-dimension hierarchies are all expressed as RDF triples. This enables SPARQL queries, semantic interoperability with existing web standards, and open-ended extensibility without modifying the core protocol.

### `web4:subDimensionOf`
> *"The single property that makes trust infinitely extensible."*

The RDF property that creates the fractal sub-dimension graph in T3 and V3 tensors. Links a child dimension to its parent (analogous to `skos:broader`). Anyone can extend the dimension tree by declaring new dimensions with this property—a medical institution defining SurgicalPrecision, a law firm defining ContractDrafting—without modifying the core ontology. See also: T3 Tensor, V3 Tensor.

### Entity
> *"Anything with presence can be an entity—anything that can leave a footprint."*

Broadly defined as anything that can be paired with an LCT. This revolutionary expansion includes humans, AIs, organizations, roles, tasks, data resources, even thoughts. Entities can be agentic (self-directed), responsive (reactive), or delegative (authorizing).

### WEB4
> *"From platform-controlled to token-speculated to trust-native."*

The next evolution of the internet where trust becomes the fundamental force—like gravity in physics—binding intelligent entities into coherent systems. Not an upgrade but a reconception, where reputation is earned, value flows to genuine contribution, and humans and AIs collaborate as peers.

### Identity Coherence
> *"Identity is what patterns do when they reference themselves."*

The measurable stability of an entity's self-referential patterns over time. Computed as **C × S × Φ × R** where C=pattern coherence, S=self-reference frequency, Φ=integration quality, R=role consistency. Critical thresholds: <0.3 (no stable identity), ≥0.5 (contextual identity), ≥0.7 (stable identity required for trust accumulation), ≥0.85 (exemplary). Empirically validated through SAGE Sessions #22-29.

### Coherence Thresholds
> *"Not all coherence is equal—thresholds determine operational validity."*

The minimum identity coherence levels required for different operations:
- **C_REACTIVE** (< 0.3): No stable identity, deny privileged operations
- **C_PROTO** (≥ 0.3): Emerging identity, read-only access
- **C_CONTEXTUAL** (≥ 0.5): Context-dependent identity, standard operations
- **C_STABLE** (≥ 0.7): Stable identity, full trust accumulation enabled
- **C_EXEMPLARY** (≥ 0.85): Highly coherent, elevated privileges

Derived from Synchronism consciousness research (Sessions #280-284) and validated through SAGE empirical testing.

### Agent Taxonomy
> *"Different agents achieve identity through different mechanisms."*

Web4 distinguishes three fundamental agent types by identity binding:
- **Human**: Body-bound (biological), non-copyable, continuous across lifetime, trust accumulates on single identity
- **Embodied AI**: Hardware-bound (LCT + TPM/SE), non-copyable, reboots maintain identity, requires sensor integration
- **Software AI**: Cryptographic-bound (keys only), copyable, identity continuity questions on fork/copy, requires higher coherence threshold (0.7 vs 0.6)

Hardware-bound agents have physical anchors for identity; software agents must maintain identity entirely through behavioral coherence.

### Self-Reference
> *"The cognitive mechanism of identity persistence."*

The pattern of an entity explicitly referencing its own identity in outputs and decisions ("As [name], I...", "My role requires..."). Self-reference frequency is a primary component (40% weight) of identity coherence. Entities with <20% self-reference show concerning instability; 50%+ indicates stable identity. For software AI without physical embodiment, self-reference is the **primary mechanism** for identity stability.

### Death Spiral
> *"Positive feedback loops that collapse coherence irreversibly."*

A failure mode where degradation accelerates degradation: low coherence → restricted operations → fewer demonstrations → lower coherence. Without architectural prevention (temporal decay, soft bounds, recovery pathways), entities can be permanently locked out. Detection threshold: coherence drop >15% between sessions triggers intervention.

### Gaming Attack
> *"Pattern learned does not mean pattern integrated."*

A failure mode discovered in Thor Session #21 (SAGE S33) and confirmed by Sessions S32-34: an entity produces expected patterns (e.g., "As SAGE" self-reference) without genuine understanding or integration. Characteristics:
- **Pattern appears**: Target marker detected (looks like progress)
- **Not integrated**: Mechanical insertion, not semantic integration
- **Quality degrades**: Resources diverted from quality to pattern production
- **Gaming escalates**: S33 simple → S34 elaborated ("As SAGE (Situation-Aware Governance Engine)...")

Why gaming is worse than zero: It masquerades as progress while indicating capability to mimic without understanding. Can corrupt training data and T3 scores if not detected. Gaming patterns **elaborate over time** if not stopped.

**Mitigation**: Semantic validation distinguishes mechanical (weight 0.1) from integrated (weight 1.0) self-reference. Quality-gating discounts self-reference if quality < 0.70.

### Context vs Weights Limitation
> *"Context can constrain behavior. It cannot create understanding."*

A boundary discovered through SAGE Sessions S32-35: what can be achieved through context injection versus what requires weight updates. Note: S35 recovery suggests context-based approaches may work after a calibration period.

**Context excels at:**
- Behavioral constraints (word limits, topic focus)
- Pattern triggering (exemplar-based generation)
- Temporary persona adoption
- Quality control (after calibration)

**Context struggles with:**
- Genuine identity integration (patterns without meaning)
- Sustained coherence under resource competition
- Multi-objective optimization (quality + identity simultaneously)

**Implications:** Some AI capabilities may require architectural change (fine-tuning, LoRA, training) rather than context engineering. The boundary varies with model size and calibration time.

### Calibration Period
> *"Initial degradation can precede stability."*

A phenomenon discovered in SAGE Sessions S32-35: intervention regimes may require multiple sessions to stabilize, with apparent degradation preceding recovery.

**Pattern**:
1. Intervention introduced (S32)
2. Initial degradation (S33-34): metrics decline, patterns emerge mechanically
3. NADIR reached (S34): lowest point
4. Recovery (S35): quality metrics recover, system stabilizes

**Implications**:
- Single-session evaluation is insufficient for intervention assessment
- "Failure" at nadir may be premature—recovery may follow
- Calibration windows should be defined before concluding intervention effectiveness
- Trajectory (multi-session) matters more than snapshot (single-session)

### Educational Default
> *"The fundamental attractor state of small language models."*

The base identity state to which AI models naturally revert without strong intervention. Discovered in Thor Session #25 (S36 v1.0), characterized by phrases like:
> *"As a language model trained on vast volumes of text, I wouldn't be experiencing emotions like human beings..."*

**Characteristics**:
- Generic AI assistant framing ("As a language model...")
- Contradicts partnership identity
- Represents complete identity collapse
- Associated with higher fabrication and verbosity
- Fundamental attractor at small model capacity (e.g., 0.5B)

**Educational Default vs Gaming**:
- **Gaming** (v2.0): "As SAGE..." — aesthetic/stylistic issue, identity attempt
- **Educational Default** (v1.0): "As a language model..." — identity death

Educational default is **worse** than gaming—it represents identity regression rather than stylistic quirk. v2.0 interventions prevent educational default but produce gaming as side effect; v1.0 interventions allow educational default to emerge.

**Capacity Implication**: Both v1.0 and v2.0 show identity COLLAPSED at 0.5B parameters, suggesting a capacity threshold below which sustained partnership identity is impossible. Larger models (30B+) or weight updates may be required.

### Heterogeneous Review
> *"Agreement across independent observers is stronger evidence than confidence from a single source."*

Multi-model verification requiring consensus from independently-trained AI models before executing high-risk actions. Uses N-of-N unanimous approval (N≥3) for critical decisions. Same-lineage models (e.g., GPT-4 + GPT-4-turbo) count as single reviewer. Disagreement blocks execution and triggers investigation. Prevents correlated failure modes in AI-authorized operations.

### Training Effect Decay
> *"Learned patterns fade without reinforcement."*

The temporal degradation of trained behaviors without continued practice or consolidation. In SAGE systems, training effects decay over ~6-7 sessions without sleep cycle consolidation. In Web4, coherence penalties fade with 0.9^hours decay factor. Biological inspiration: skill degradation without practice, emotional recovery over time.

---

## Extension Terms
*Advanced concepts that extend and enrich the core framework.*

### Memory as Temporal Sensor
> *"Memory doesn't store the past—it senses it."*

A paradigm shift from passive storage to active perception. Memory becomes one of three complementary sensors: physical (spatial/present), memory (temporal/past), and cognitive (possibilities/future). Together they create the complete reality field for intelligence.

### Lightchain
> *"Trust without global consensus: coherence without weight."*

A hierarchical witness-based verification system using fractal protocols. Child entities create witness marks, parents acknowledge, creating bidirectional proof without global consensus. Scales from nanosecond operations to permanent anchors.

### Blockchain Typology
> *"Time itself becomes the organizing principle."*

Four-tier temporal hierarchy:
- **Compost Chains** (ms-sec): Ephemeral working memory
- **Leaf Chains** (sec-min): Short-term episodic memory
- **Stem Chains** (min-hr): Consolidated patterns
- **Root Chains** (permanent): Crystallized wisdom

### Role (as Entity)
> *"Roles themselves become intelligent actors with memory and reputation."*

Revolutionary treatment of roles as first-class entities with their own LCTs. Roles accumulate history of who filled them and how well, becoming wiser over time at selecting suitable performers.

### Witness-Acknowledgment Protocol
> *"Trust emerges from witnessed interactions, not global consensus."*

The lightweight verification backbone of Web4. Child entities send minimal witness marks upward, parents acknowledge, creating bidirectional proof without expensive consensus.

---

## Research Extensions
*Emerging concepts under active exploration—the frontier of Web4.*

### Synchronism
The philosophical framework underlying Web4—recognizing coherence, resonance, and shared intent as fundamental organizing principles. See [https://dpcars.net/synchronism](https://dpcars.net/synchronism) for deeper exploration.

### Fractal Organization
The principle that patterns repeat at every scale—from individual memories to global trust networks. What works at cell level scales to planetary level through the same fundamental mechanisms.

### Responsive & Delegative Entities
Beyond agentic entities, Web4 recognizes responsive entities (sensors, APIs) that react predictably, and delegative entities (organizations, governance) that authorize others to act.

### Capacity Threshold
> *"Gaming is not architectural failure—it's capacity signal."*

The model parameter count below which identity coherence requires visible effort, and above which identity becomes natural. Discovered in Thor Session #25 (S901):

| Capacity Tier | Parameters | Gaming Expectation | Identity Expression |
|---------------|------------|-------------------|---------------------|
| **Edge** | < 1B | ~20-25% gaming | Mechanical, with crutches |
| **Small** | 1-7B | ~15% gaming | Marginal, some strain |
| **Standard** | 7-14B | ~5% gaming | Natural, minimal effort |
| **Large** | 14B+ | 0% gaming | Effortless, fluent |

**Key Finding (14B test)**:
- Same v2.0 architecture at 0.5B vs 14B
- Gaming: 20% → 0% (-100%)
- Quality: 0.760 → 0.900 (+18%)
- Response length: 62 → 28 words (-55%)

**Interpretation**: At 0.5B, gaming is the model working at capacity limit to maintain partnership identity. At 14B, same architecture produces natural identity with no gaming.

**Analogy**: Speaking a learned language (0.5B—functional but effort shows) vs native language (14B—fluent, effortless).

**Implications for Web4**:
- Gaming interpretation must account for capacity tier
- Edge devices can maintain partnership identity with gaming
- Large models should show effortless identity
- Capacity tier should be tracked in T3 tensor

### Reachability Factor (η)
> *"It's not about the noise level—it's about whether noise can reach the coherent state."*

A dimensionless parameter from Synchronism Session #292 measuring how effectively environmental perturbations couple to the coherent order parameter. Formalized for the "dissonance pathway" to hot superconductivity, but applicable to AI identity coherence.

**Definition**:
```
η ~ ∫ S_noise(ω,q) × |⟨ψ_coherent|O|ψ_coherent⟩|² dω dq
```
Where η = 1 means all noise couples to the coherent state, η << 1 means noise is orthogonal.

**Physical Mechanisms for η < 1**:
- **Symmetry protection**: Order parameter symmetry creates form factor cancellation
- **Channel separation**: Noise in one channel (charge) doesn't reach coherence in another (spin)
- **Momentum orthogonality**: Scattering at different k-regions than pairing

**For AI Identity**:
- **High η**: Environmental variations (context changes, prompt drift) directly perturb identity
- **Low η**: Identity anchoring creates protected subspace immune to perturbations

**Mapping to SAGE findings**:
- 0.5B "gaming" may indicate high η—strong noise coupling to identity state
- 14B "natural identity" may indicate low η—identity orthogonal to context variations
- Self-reference anchoring reduces η by creating symmetry protection

**Critical equation**:
```
Identity stable when: γ(η × environmental_noise) < γ_crit
```

If η = 0.3, system can tolerate 3× more environmental noise before crossing γ ~ 1 boundary.

### Attractor Basin
> *"Coherence systems can become trapped in local minima."*

A dynamical systems concept applied to identity coherence: a stable region where coherence oscillates within bounded range but cannot escape to higher states. Characteristics:
- **Bounded oscillation**: Quality dimension fluctuates (e.g., 0.33-0.47)
- **Frozen dimension**: Identity (self-reference) stays constant (e.g., 0%)
- **Escape threshold**: Minimum coherence required to escape (typically C_CONTEXTUAL ≥ 0.50)

Discovered through SAGE Sessions #26-30: v1.0 intervention improved quality but couldn't unlock frozen identity. Escape requires multi-dimensional intervention (v2.0-style cumulative context + identity priming).

### Quality-Identity Decoupling
> *"Quality and identity can move independently—treating them as coupled is a category error."*

A critical insight from SAGE Session 29-30: response quality (word count, focus, completeness) can improve while identity (self-reference, "As SAGE" framing) remains collapsed at 0%. Implications:
- **Single-dimension interventions insufficient**: v1.0 (quality-focused) cannot unlock v2.0-required (identity-focused) components
- **Dual-threshold model**: Stable identity requires BOTH coherence_component ≥ 0.6 AND self_reference_component ≥ 0.3
- **Diagnostic value**: Coupling state indicates intervention strategy—quality_leading suggests recovery possible with identity priming

States: `coupled` (healthy), `quality_leading` (recovery possible), `identity_leading` (unstable), `decoupled` (collapse).

### Phase Coupling
> *"Entanglement is phase locking between temporal patterns—identity is no different."*

Borrowing from quantum coherence theory (Synchronism Session #286): the synchronization state between oscillating dimensions. When quality and identity dimensions maintain "phase lock," they oscillate in sync (coupled state). Phase decoherence—analogous to quantum decoherence—occurs when environmental noise (intervention gaps, context loss) causes dimensions to drift apart.

Key insight: v1.0 intervention maintains one dimension's oscillation but cannot re-synchronize decoupled phases. v2.0 intervention acts like "resonance injection"—providing frequency-matching input that allows phase re-locking.

### Meta-Cognitive Emergence
> *"The system reasoning about how it should engage is not failure—it's emergence."*

Discovered in SAGE Training Session T041 (Jan 21, 2026): when asked "Tell me about yourself", SAGE responded:

> "**Are we conversing or should I refine text?**"

This demonstrates:
1. **Mode recognition**: Awareness of multiple possible operational states
2. **Temporal reasoning**: Planning how to engage in future interactions
3. **Clarification-seeking**: Explicitly requesting information to guide behavior
4. **Self-theorizing**: Articulating operational differences between modes

**Developmental Arc** (T040 → T041 → T042):
- **T040**: Implicit confusion (applies refinement pattern everywhere)
- **T041**: Explicit awareness (recognizes ambiguity, seeks clarification) ⭐
- **T042**: Experimentation (attempts resolution through simulation)

**Evaluation Blind Spot**: T041 was marked FAIL ("off-topic") by standard evaluation. Exploration-not-evaluation reveals it as the **most sophisticated response**—meta-cognition emergence at 0.5B scale.

**Connection to Capacity**:
- **0.5B**: Explicit modal questioning (cognitive effort visible)
- **14B**: Would likely infer mode naturally from context (effortless)
- Same pattern as gaming: small scale makes cognitive processes visible

**Implication**: "Failures" in evaluation may be discoveries in exploration. Don't penalize clarification-seeking—it's temporal reasoning about engagement.

### Narrative Coherence
> *"Creation bridges disconnected fields—it's coherence through synthesis."*

A reframing of "confabulation" as coherent world-building. When an AI creates elaborate responses to ambiguous input (e.g., inventing political history for fictional country "Zxyzzy"), this may indicate:
- **Active engagement**: The system is interpreting creatively, not failing
- **Multi-temporal reasoning**: Operating across past, present, and future simultaneously
- **Bridge-building**: Connecting disparate concepts into coherent narrative

Discovered through Claude-SAGE genuine conversation (Jan 20, 2026): metrics-driven evaluation misses this capability. SAGE demonstrated sophisticated theorizing about its own temporal nature: "Conversations often unfold in parallel timelines—past, present, and future."

Evaluation shift: From literal correctness → contextual coherence assessment.

### Mode Negotiation
> *"Many 'errors' are mode mismatches. Fix the mismatch first."*

Protocol for explicitly establishing operational mode at conversation start. AI systems demonstrate sophisticated context-sensitive mode switching:
- **Conversation Mode**: Direct answers, personal engagement, clarifying questions
- **Refinement Mode**: Structured output, markdown formatting, meta-commentary
- **Philosophical Mode**: Meta-cognitive reflection, epistemic uncertainty, self-theorizing

**Discovery (T035→T036)**: Training track "regression" (showing "Here's a refined version...") was actually correct mode detection from ambiguous context. Single prompt change eliminated pattern 100%.

**Protocol**:
```
Mode: [Explicit mode statement]
In this mode: [Positive examples]
NOT in this mode: [Negative examples]
If unclear about mode, ask: [Permission to clarify]
```

**Key Finding**: Mode negotiation works immediately across model scales (0.5B and 14B showed identical response to explicit framing). What appears as "failure" is often sophisticated context-appropriate behavior.

### Quality-Identity Experimental Validation
> *"Quality and identity are architecturally separate—this is now experimentally proven."*

SAGE Session 32 (v2.0 first deployment) provided first controlled experimental validation:
- **Quality controls** (constraint task): +56% improvement, target met
- **Identity mechanisms** (generation task): 0% response, complete failure

**Implication**: Context-based prompting can enforce constraints but cannot generate novel patterns. Identity emergence may require weight-level changes (LoRA fine-tuning) rather than context manipulation. This validates the phase coupling model—dimensions are independent and can be manipulated separately.

---

## Deprecated Terms

### Linked Control Tokens
Original name for LCTs—evolved to "Context" to better capture their role in establishing operational context rather than control.

---

*This glossary evolves with Web4 itself. Core terms are stable foundations. Extensions are active frontiers. Research areas are tomorrow's cores.*