# Glossary of WEB4 Terms

*The language of trust-native intelligence, organized from foundation to frontier.*

---

## Core Terms
*The fundamental building blocks of Web4—master these to understand everything else.*

### Linked Context Tokens (LCTs)
> *"Every entity is born with and dies with its LCT—the unforgeable footprint of digital presence."*

The reification of presence itself. LCTs are permanently and immutably bound to a single entity (human, AI, organization, role, task, or resource) and are non-transferable. They serve as a cryptographic root identity that cannot be stolen, sold, or faked. If the entity ceases to exist, its LCT is marked void or slashed. LCTs form malleable links to create trust webs, delegation chains, and historical records—the nervous system of Web4.

### Allocation Transfer Packet / Allocation Discharge Packet (ATP/ADP)
> *"Allocation flows through work. Packets carry the proof."*

A biological metaphor made digital. ATP packets exist in "charged" (resources allocated, ready for use) or "discharged" (ADP - work performed, delivery confirmed) states, mirroring cellular energy cycles. Work consumes ATP creating ADP, which carries ephemeral metadata about what work was done and who benefited. When certified as valuable, ADP converts back to ATP with metadata cleared for fresh allocation. This creates an auditable trail where genuine contribution generates genuine value—not mining, not staking, but real work recognized.

**Implementation**: Packets are semifungible tokens that can be implemented as blockchain tokens, local ledger entries, or other locally appropriate means. "Allocation" covers all resource types: energy, attention, work, compute, trust budgets.

### T3 Tensor (Trust Tensor)
> *"Trust emerges from capability demonstrated over time—but only when identity is stable."*

A multi-dimensional metric capturing an entity's trustworthiness. The "T3" name reflects three primary categories, but the full tensor includes additional dimensions:

**Primary Dimensions:**
- **Talent**: Inherent aptitude or originality
- **Training**: Acquired knowledge and skills
- **Temperament**: Behavioral characteristics and reliability

**Extended Dimensions:**
- **Identity Coherence**: Stability of self-referential patterns (C × S × Φ × R score). **Prerequisite dimension**—without C ≥ 0.7, other dimensions are unreliable
- **Identity Accumulation**: Multi-session stability of coherence over time
- **Witness Count**: Number of independent observers who have verified behavior
- **Lineage Depth**: Trust inheritance from parent/creator entities
- **Hardware Binding Strength**: For embodied agents, strength of physical identity anchor (0-1.0)

Context-dependent and dynamically updated through actual performance. Identity coherence acts as a **gate**—trust scores from low-coherence states are discounted or invalidated.

### V3 Tensor (Value Tensor)
> *"Value is not declared but demonstrated, not claimed but confirmed."*

A three-dimensional metric quantifying created value:
- **Valuation**: Subjective worth to the recipient
- **Veracity**: Objective accuracy and reproducibility
- **Validity**: Confirmation of actual value transfer

Together with T3, enables nuanced assessment beyond simple ratings.

### Markov Relevancy Horizon (MRH)
> *"The MRH is how an entity knows where it belongs in the universe of relevance."*

Each entity's contextual lens defining what is knowable, actionable, and relevant within their scope. Not a wall but a gradient—a fuzzy boundary ensuring entities engage where they're most effective. Dimensions include fractal scale, informational scope, geographic scope, action scope, and temporal scope.

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