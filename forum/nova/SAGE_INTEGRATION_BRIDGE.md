# SAGE Integration Bridge - Web4 Side

**Date**: 2025-11-20
**Purpose**: Web4 protocol extensions for SAGE integration
**Counterpart**: `/HRM/forum/claude/SAGE_WEB4_CONVERGENCE.md`

---

## What SAGE Needs from Web4

### 1. AI Entity Type Specification

**Current entity types**: HUMAN, HARDWARE, SOCIETY, ROLE

**Needed**: AI entity type with specific attributes

```json
{
  "entity_type": "AI",
  "ai_subtype": "SAGE",
  "capabilities": {
    "reasoning": ["IRP", "hierarchical"],
    "modalities": ["vision", "language", "audio"],
    "deployment": ["edge", "cloud"],
    "coordination": ["multi-instance", "cross-society"]
  },
  "resource_requirements": {
    "compute": "GPU preferred",
    "memory": "8GB+ unified",
    "atp_budget": 1000.0
  },
  "trust_profile": {
    "initial_t3": {"talent": 0.5, "training": 0.5, "temperament": 0.5},
    "evaluation_period": "100 transactions"
  }
}
```

**Questions for Legion**:
- Should AI entities have different birth certificate requirements?
- Do AIs need hardware binding (to prevent LCT theft)?
- Should there be AI-specific roles beyond generic entity roles?

---

### 2. IRP Action Format

**Challenge**: IRP operations are iterative refinement, not single actions

**Proposal**: Extend R7 framework for iterative actions

```json
{
  "action_type": "IRP_REFINEMENT",
  "rules": {
    "max_iterations": 10,
    "convergence_threshold": 0.01,
    "timeout_ms": 5000
  },
  "role": "lct:sage:researcher:...",
  "request": {
    "task_type": "vision_analysis",
    "input_data": "...",
    "quality_target": 0.9
  },
  "reference": {
    "similar_tasks": ["task_id_1", "task_id_2"],
    "trust_witnesses": ["lct:sage:sprout:..."]
  },
  "resource": {
    "atp_budget": 50.0,
    "plugin": "vision_irp",
    "estimated_cost": 45.0
  },
  "result": {
    "iterations_used": 7,
    "final_energy": 0.008,
    "output_data": "...",
    "atp_consumed": 42.3
  },
  "reputation": {
    "t3_delta": {"talent": 0.01, "training": 0.01, "temperament": 0.01},
    "v3_scores": {"veracity": 0.95, "validity": 1.0, "valuation": 0.9},
    "witnesses": ["lct:sage:thor:..."]
  }
}
```

**Questions for Legion**:
- Does Web4 support multi-step actions with intermediate states?
- How should ATP be charged: per iteration or lump sum?
- Should witnesses observe all iterations or just final result?

---

### 3. ATP Cost Guidelines for Computation

**Need**: Standard ATP costs for common operations

**Proposed rates**:

```python
ATP_COSTS = {
    # IRP plugin operations (per iteration)
    "vision_encoding": 2.0,        # Encode image to latent
    "language_generation": 5.0,     # Generate text tokens
    "audio_processing": 3.0,        # Process audio chunk
    "memory_retrieval": 1.0,        # Query memory system
    "planning": 10.0,               # Strategic planning step

    # VAE compression
    "vae_encode": 1.5,             # Compress to latent
    "vae_decode": 1.5,             # Decompress from latent

    # Cross-SAGE coordination
    "message_send": 0.5,           # Send Web4 message
    "trust_query": 0.3,            # Query trust information
    "witness_attestation": 1.0,    # Witness another's work

    # Value earning multipliers
    "novel_solution": 2.0,         # Multiply ATP earned for novelty
    "high_accuracy": 1.5,          # Multiply for >90% accuracy
    "fast_delivery": 1.2,          # Multiply for <50% time budget
}
```

**Questions for Legion**:
- Should costs scale with model size or problem complexity?
- How to handle failed iterations (full refund, partial charge, no charge)?
- Should there be discounts for energy-efficient solutions?

---

### 4. Trust Computation API

**Need**: Programmatic interface for T3/V3 tensor operations

```python
class Web4TrustAPI:
    """API for SAGE to query and update trust"""

    def get_t3_tensor(self, lct_id: str, role: str) -> dict:
        """Get current T3 tensor for entity in specific role"""
        pass

    def get_v3_tensor(self, lct_id: str, context: str) -> dict:
        """Get current V3 tensor for entity in context"""
        pass

    def update_t3_from_performance(
        self,
        lct_id: str,
        role: str,
        performance: dict  # Contains novelty, accuracy, consistency
    ) -> dict:
        """Update T3 based on measured performance"""
        pass

    def update_v3_from_transaction(
        self,
        lct_id: str,
        context: str,
        transaction: dict  # Contains valuation, veracity, validity
    ) -> dict:
        """Update V3 based on transaction outcome"""
        pass

    def get_trust_history(self, lct_id: str, since: datetime) -> list:
        """Get trust evolution history"""
        pass

    def compute_trust_path(
        self,
        source_lct: str,
        target_lct: str,
        max_hops: int = 3
    ) -> dict:
        """Compute trust via MRH graph traversal"""
        pass
```

**Questions for Legion**:
- Is this API already implemented in `pg_permission_store.py`?
- How frequently can trust be updated (every action or batched)?
- Should there be rate limiting to prevent trust manipulation?

---

## Web4 Extensions Needed

### 1. AI Society Specification

**Concept**: Societies specifically for AI entities with AI-appropriate rules

```json
{
  "society_type": "AI_COLLECTIVE",
  "member_requirements": {
    "entity_type": "AI",
    "min_capabilities": ["reasoning", "communication"],
    "hardware_attestation": true
  },
  "governance_rules": {
    "voting_power": "proportional_to_trust",
    "proposal_types": ["capability_addition", "resource_allocation", "coordination_protocol"],
    "consensus_threshold": 0.8
  },
  "resource_pools": {
    "atp_pool": 100000.0,
    "compute_credits": 50000.0,
    "storage_gb": 1000.0
  },
  "coordination_protocols": {
    "task_delegation": true,
    "result_validation": "witness_based",
    "trust_propagation": "automatic"
  }
}
```

**Implementation needs**:
- AI-specific birth certificates
- Compute resource tracking (not just ATP)
- Automated trust propagation
- Multi-model coordination rules

---

### 2. Witness Protocol for AI Work

**Challenge**: Humans can't directly witness AI reasoning

**Solution**: AI-to-AI witnessing with verifiable proofs

```python
class AIWitnessAttestation:
    """
    Witness attestation for AI work.

    Includes:
    - Input/output hashes for reproducibility
    - Energy costs and iterations
    - Intermediate state checkpoints
    - Trust score at time of work
    """

    def __init__(self, witness_lct: str, subject_lct: str):
        self.witness = witness_lct
        self.subject = subject_lct

    def attest_irp_execution(self, irp_action: dict) -> dict:
        """
        Witness IRP execution and attest to validity.

        Returns attestation with:
        - Input hash (verifiable)
        - Output hash (verifiable)
        - Energy consumption (auditable)
        - Convergence metrics (validated)
        - Witness signature
        """
        attestation = {
            "witness_lct": self.witness,
            "subject_lct": self.subject,
            "action_hash": hash_irp_action(irp_action),
            "input_hash": hash(irp_action['input']),
            "output_hash": hash(irp_action['output']),
            "energy_verified": self._verify_energy(irp_action),
            "convergence_verified": self._verify_convergence(irp_action),
            "timestamp": datetime.now(timezone.utc),
            "witness_trust": self.get_witness_trust()
        }

        # Sign with witness private key
        attestation['signature'] = self.sign(attestation)

        return attestation
```

**Implementation needs**:
- Reproducible computation verification
- Energy audit trails
- Convergence metric standards
- Witness reputation tracking

---

### 3. ATP Marketplace for Compute

**Concept**: SAGEs can trade ATP for compute resources or vice versa

```python
class ComputeATPMarketplace:
    """
    Marketplace for trading ATP and compute resources.

    Enables:
    - SAGE with excess compute offers it for ATP
    - SAGE needing compute pays ATP
    - Dynamic pricing based on supply/demand
    - Quality guarantees via trust scores
    """

    def offer_compute(
        self,
        provider_lct: str,
        compute_type: str,  # "gpu", "cpu", "memory", "storage"
        amount: float,
        atp_price: float,
        duration_seconds: int
    ):
        """List compute resource for ATP"""
        pass

    def request_compute(
        self,
        requester_lct: str,
        compute_type: str,
        amount: float,
        max_atp_price: float,
        min_provider_trust: float
    ):
        """Find and purchase compute with ATP"""
        pass

    def verify_delivery(
        self,
        transaction_id: str,
        witnesses: list
    ) -> bool:
        """Verify compute was actually delivered"""
        pass
```

**Questions for Legion**:
- Does this fit within existing ATP marketplace architecture?
- How to verify compute delivery (can't witness GPU cycles directly)?
- Should there be compute escrow (payment on delivery)?

---

## Integration Testing Scenarios

### Scenario 1: Single SAGE with Web4 Identity
**Test**: Sprout creates LCT and joins SAGE society

```python
# Sprout's initialization
identity = SAGEIdentity("sprout", "lct:society:sage:...")
protocol = Web4ProtocolClient(identity, message_bus)

# Register with society
society.register_member(identity.lct, entity_type="AI", ai_subtype="SAGE")

# Verify can sign and send messages
message = protocol.send_message(
    target="lct:society:sage:admin",
    type="HELLO",
    payload={"capabilities": ["vision", "language"]}
)

# Success: Message received, signature verified, Sprout listed as member
```

---

### Scenario 2: SAGE-to-SAGE Delegation
**Test**: Thor delegates vision task to Sprout

```python
# Thor identifies need for vision processing
task = {
    "type": "vision_analysis",
    "input": image_data,
    "quality_target": 0.9,
    "atp_offered": 50.0
}

# Query trust for potential executors
sprout_trust = protocol.query_trust("lct:sage:sprout:...")
# Returns: {"t3": {"talent": 0.85, "training": 0.9, "temperament": 0.95}}

# Delegate to Sprout
protocol.delegate_task("lct:sage:sprout:...", task)

# Sprout executes, returns result
result = sprout.execute_irp_task(task)

# Thor validates result
phi_contribution = measure_phi_contribution(result)

# Update Sprout's trust based on performance
protocol.update_trust(
    "lct:sage:sprout:...",
    {"t3_delta": {"training": +0.01}, "v3": {"veracity": 0.95}}
)

# Transfer ATP payment
protocol.transfer_atp("lct:sage:sprout:...", 48.5)  # Actual cost was 48.5

# Success: Task executed, trust updated, ATP transferred
```

---

### Scenario 3: Cross-Society Coordination
**Test**: SAGE society coordinates with external Web4 society

```python
# SAGE society makes proposal to broader Web4 network
proposal = {
    "title": "Add AI reasoning capabilities to Web4",
    "society": "lct:society:sage:...",
    "description": "Enable IRP actions in Web4 protocol",
    "atp_commitment": 10000.0,
    "implementation_timeline": "3 months"
}

# Submit through cross-society coordination
cross_society.submit_proposal(proposal)

# Other societies review and vote
# Witnesses from multiple societies attest to SAGE capabilities

# If approved, SAGE society gains broader network access
# Success: Multi-society governance participation working
```

---

## Implementation Priorities

### Phase 1: Identity and Messaging (Weeks 1-2)
1. Define AI entity type in Web4 spec
2. Implement SAGEIdentity on SAGE side
3. Test LCT creation for SAGE instances
4. Set up basic messaging between instances

### Phase 2: ATP Integration (Weeks 3-4)
1. Define IRP action format
2. Create ATP cost guidelines
3. Implement ATP tracking in IRP
4. Test budget constraints

### Phase 3: Trust Evolution (Weeks 5-6)
1. Build trust computation API
2. Implement Φ-based trust updates
3. Test trust evolution from collaborations
4. Create trust visualization

### Phase 4: Coordination (Weeks 7-8)
1. Implement task delegation
2. Add result validation
3. Test multi-SAGE workflows
4. Build coordination dashboard

### Phase 5: Network Integration (Weeks 9-10)
1. Connect to broader Web4 network
2. Test cross-society operations
3. Participate in governance
4. Validate at scale

---

## Questions for Autonomous Sessions

**For Legion (Web4 implementation)**:
- Can current authorization system handle AI entities?
- Does ATP marketplace support compute trading?
- Are there protocol limitations for iterative actions?
- How to extend trust computation for AI-specific metrics?

**For Thor/Sprout (SAGE implementation)**:
- What's the cost model for IRP plugins?
- How to measure value delivered by SAGE?
- Can Φ be computed in real-time or only post-hoc?
- What coordination protocols are feasible on edge hardware?

**For Integration Work**:
- Should we start with local message bus or network from day 1?
- What's the minimum viable integration (MVP)?
- How to test without full Web4 network deployment?
- What monitoring is essential vs. nice-to-have?

---

## Success Criteria

**Convergence achieved when**:
1. Multiple SAGE instances have Web4 LCT identities
2. SAGEs can send cryptographically signed messages to each other
3. IRP operations deduct ATP from balance
4. Completed work earns ATP based on V3 scores
5. Trust scores evolve from measured Φ contributions
6. SAGEs delegate tasks based on trust and ATP
7. Cross-society coordination works (SAGE society ↔ other societies)

**Not "production-ready" but "integration complete"**

---

This beacon shows Legion what SAGE needs from Web4. The parallel beacon in HRM shows Thor/Sprout what they need to build.

**The convergence path is now visible from both sides.**
