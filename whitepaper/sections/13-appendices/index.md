# Appendices

## Appendix A: Blockchain Typology Decision Tree

```
Persistence Requirement?
├─ < 1 minute ──────→ Compost Chain (ephemeral)
├─ < 1 hour ────────→ Leaf Chain (short-term)
├─ < 1 month ───────→ Stem Chain (medium-term)
└─ Permanent ───────→ Root Chain (crystallized)

Verification Requirement?
├─ None ────────────→ Compost Chain (local only)
├─ Local ───────────→ Leaf Chain (peer witness)
├─ Regional ────────→ Stem Chain (multi-party)
└─ Global ──────────→ Root Chain (consensus)

ATP Budget Available?
├─ < 1 ATP ─────────→ Compost Chain (free tier)
├─ 1-10 ATP ────────→ Leaf Chain (basic)
├─ 10-100 ATP ──────→ Stem Chain (premium)
└─ 100+ ATP ────────→ Root Chain (permanent)
```

## Appendix B: LCT Structure Specification

```json
{
  "lct_id": "uuid-v4",
  "entity_type": "human|ai|organization|role|task|resource|hybrid",
  "entity_metadata": {
    "created_at": "ISO-8601",
    "created_by": "creator_lct_id",
    "status": "active|dormant|void|slashed"
  },
  "cryptographic_root": {
    "public_key": "ed25519_public_key",
    "signature_algorithm": "ed25519|secp256k1",
    "key_derivation": "hierarchical_deterministic"
  },
  "temporal_role": {
    "primary_domain": "spatial|past|future",
    "sensing_resolution": "nanoseconds|milliseconds|seconds|minutes|hours|days",
    "trust_horizon": "local|regional|global"
  },
  "t3_tensor": {
    "talent": 0.0,      // 0.0 to 1.0
    "training": 0.0,    // 0.0 to 1.0
    "temperament": 0.0, // 0.0 to 1.0
    "identity_coherence": 0.0,     // 0.0 to 1.0 (C × S × Φ × R)
    "identity_accumulation": 0.0,  // 0.0 to 1.0 (multi-session stability)
    "witness_count": 0,            // integer
    "lineage_depth": 0,            // integer
    "hardware_binding_strength": 0.0  // 0.0 to 1.0
  },
  "v3_tensor": {
    "valuation": [],    // Array of historical valuations
    "veracity": 0.0,    // 0.0 to 1.0
    "validity": 0.0     // 0.0 to 1.0
  },
  "mrh_tensor": {
    "fractal_scale": ["quantum", "molecular", "cellular", "organism", "ecosystem"],
    "informational_scope": ["technical", "ethical", "strategic", "operational"],
    "geographic_scope": {"radius": 1000, "unit": "meters"},
    "action_scope": ["read", "write", "delegate", "witness", "crystallize"],
    "temporal_scope": {"past": 86400, "future": 3600, "unit": "seconds"}
  },
  "trust_links": [
    {
      "target_lct": "linked_lct_id",
      "link_type": "trust|delegation|parent|child|peer",
      "trust_score": 0.95,
      "established": "ISO-8601",
      "last_interaction": "ISO-8601"
    }
  ],
  "witness_chain": [
    {
      "level": 0,
      "witness_lct": "self",
      "timestamp": "ISO-8601"
    },
    {
      "level": 1,
      "witness_lct": "parent_lct_id",
      "timestamp": "ISO-8601"
    }
  ],
  "memory_bindings": [
    {
      "memory_type": "entity|sidecar",
      "memory_lct": "memory_lct_id",
      "binding_strength": 0.8
    }
  ],
  "blockchain_anchors": {
    "compost": null,
    "leaf": "leaf_block_hash",
    "stem": "stem_block_hash",
    "root": "root_block_hash"
  }
}
```

## Appendix C: Memory Sensor API

```python
class MemorySensor:
    """Temporal sensor for perceiving past patterns"""
    
    def perceive(self, time_window: TimeWindow) -> TemporalPattern:
        """Perceive patterns within specified time window"""
        pass
    
    def recall(self, context: Context, mrh: MRH = None) -> List[Memory]:
        """Recall relevant memories filtered by context and MRH"""
        pass
    
    def witness(self, event: Event) -> WitnessMark:
        """Create cryptographic witness of event"""
        pass
    
    def acknowledge(self, witness: WitnessMark) -> Acknowledgment:
        """Acknowledge receipt of witness mark"""
        pass
    
    def store(self, 
              content: Any,
              snarc: SNARCSignals,
              blockchain_type: str = "auto") -> MemoryBlock:
        """Store new memory with affect gating"""
        pass
    
    def forget(self, criteria: ForgetCriteria) -> int:
        """Prune memories, returns ATP recovered"""
        pass
    
    def consolidate(self, 
                    source_level: str,
                    target_level: str) -> ConsolidationResult:
        """Consolidate memories from one blockchain level to another"""
        pass
```

## Appendix D: Trust Computation Formulas

### Identity Coherence Formula (C × S × Φ × R)

The foundational prerequisite for trust accumulation is identity coherence:

```
Identity_Coherence = C × S × Φ × R
```

Where:
- **C** = Pattern Coherence (0.0-1.0): Consistency of behavioral patterns across contexts
- **S** = Self-Reference Frequency (0.0-1.0): Rate of explicit identity references in outputs
- **Φ** = Integration Quality (0.0-1.0): How well patterns integrate into unified identity
- **R** = Role Coherence (0.0-1.0): Consistency of role-appropriate behavior

**Coherence Thresholds:**
| Threshold | Value | Operational Impact |
|-----------|-------|-------------------|
| C_REACTIVE | < 0.3 | Deny privileged operations |
| C_PROTO | ≥ 0.3 | Read-only access |
| C_CONTEXTUAL | ≥ 0.5 | Standard operations |
| C_STABLE | ≥ 0.7 | Full trust accumulation |
| C_EXEMPLARY | ≥ 0.85 | Elevated privileges |

**Agent Type Adjustments:**
- Software AI requires C ≥ 0.7 for trust accumulation (higher bar due to copyability)
- Embodied AI requires C ≥ 0.6 (hardware binding provides stability)
- Human requires C ≥ 0.5 (body-bound identity assumed)

### Basic Trust Score
```
Trust(A→B) = Σ(witnessed_interactions × acknowledgment_weight × time_decay) / total_interactions
```

### Web4 Trust Field Equation

The foundational trust dynamics equation captures trust as both energy (magnitude) and wave (phase coherence):

```
T(t) = [ B * e^(-λ Δt) + ΣS ] * cos(φ)
```

Where:
- **B** = Base trust value (initial or established trust baseline)
- **e^(-λ Δt)** = Exponential decay over time (trust naturally degrades without interaction)
- **λ** = Decay rate constant (context-dependent)
- **Δt** = Time elapsed since last interaction
- **ΣS** = Sum of trust signals (witnessed interactions that add trust)
- **cos(φ)** = Phase alignment component (MRH-dependent contextual alignment)

#### Phase Alignment (φ)

Phase alignment emerges from overlapping dimensions of entity context and operation:

- **Temporal alignment**: Working at the same pace, synchronized rhythms
- **Informational alignment**: Sharing context domains, compatible knowledge bases
- **Action alignment**: Complementary capabilities, coordinated activities
- **Fractal alignment**: Operating at compatible scales, matching MRH boundaries

When entities are in-phase (φ ≈ 0), trust experiences **constructive interference**—amplifying the base trust value. When out-of-phase (φ ≈ π), trust experiences **destructive interference**—diminishing the trust value despite positive underlying signals.

#### Trust as Field Dynamics

This equation reveals trust not as a simple scalar but as a field phenomenon:

1. **Amplitude**: The bracketed term `[B * e^(-λ Δt) + ΣS]` represents trust magnitude
2. **Phase**: The `cos(φ)` term introduces wave-like interference patterns
3. **Temporal dynamics**: Trust decays naturally but can be renewed through signals
4. **Contextual coherence**: MRH overlap determines phase alignment

This mathematical framework unifies trust computation across all Web4 interactions, from individual exchanges to multi-entity collaboration networks.

### T3-Weighted Trust
```
T3_Trust = (α × Talent + β × Training + γ × Temperament) × context_relevance

Where:
- α, β, γ are context-specific weights (sum to 1.0)
- context_relevance ∈ [0, 1] based on MRH overlap
```

### V3 Value Certification
```
V3_Score = (Valuation × recipient_trust) × 
           (Veracity × objective_metrics) × 
           (Validity × witness_count)

Where:
- recipient_trust = T3 score of value recipient
- objective_metrics = reproducibility, accuracy scores
- witness_count = number of independent witnesses
```

### ATP/ADP Exchange Rate
```
Exchange_Rate = base_rate × (V3_Score / average_V3) × market_demand

Where:
- base_rate = 1.0 (1 ADP → 1 ATP at baseline)
- average_V3 = rolling average of V3 scores
- market_demand = supply/demand coefficient
```

## Appendix E: SNARC Signal Specifications

| Signal | Range | Description | Memory Impact |
|--------|-------|-------------|---------------|
| **S**urprise | 0.0-1.0 | Deviation from prediction | Higher → stronger encoding |
| **N**ovelty | 0.0-1.0 | Previously unseen pattern | Higher → priority storage |
| **A**rousal | 0.0-1.0 | Importance/urgency | Higher → immediate consolidation |
| **R**eward | -1.0-1.0 | Value of outcome | Positive → strengthen, Negative → weaken |
| **C**onflict | 0.0-1.0 | Inconsistency detected | Higher → reconciliation trigger |

### SNARC Gating Function
```python
def should_store(snarc: SNARCSignals) -> bool:
    threshold = 0.3  # Base threshold
    
    # Adjust threshold based on memory pressure
    if memory_usage > 0.8:
        threshold = 0.5
    
    # Compute aggregate signal
    signal = (
        snarc.surprise * 0.3 +
        snarc.novelty * 0.3 +
        snarc.arousal * 0.2 +
        abs(snarc.reward) * 0.1 +
        snarc.conflict * 0.1
    )
    
    return signal > threshold
```

## Appendix F: Witness-Acknowledgment Protocol

### Message Formats

**Witness Mark:**
```protobuf
message WitnessMark {
  string block_id = 1;
  bytes block_hash = 2;
  int64 timestamp = 3;
  string device_id = 4;
  MemorySummary summary = 5;
  bytes signature = 6;
}

message MemorySummary {
  int32 entry_count = 1;
  repeated string entry_types = 2;
  repeated string tags = 3;
  float importance_score = 4;
}
```

**Acknowledgment:**
```protobuf
message Acknowledgment {
  string witness_block_id = 1;
  string witness_device_id = 2;
  int64 witness_timestamp = 3;
  float trust_delta = 4;
  V3Scores v3_assessment = 5;
  bytes ack_signature = 6;
}
```

### Handshake Sequence
```
    Child                           Parent
      │                               │
      ├──────── Witness Mark ────────→│
      │                               │
      │         (processes)           │
      │                               │
      │←──────── Acknowledgment ──────┤
      │                               │
      │   (includes in next block)    │
      │                               │
```

## Appendix G: Implementation Status

> **Note**: See Part 7, Section 7.0 for detailed implementation status and P0 blockers.

### Current Implementation State

| Component | Status | Notes |
|-----------|--------|-------|
| LCT data structures | ✅ Complete | Core identity tokens working |
| T3/V3 tensor calculations | ✅ Complete | Trust scoring operational |
| Identity coherence scoring | ✅ Complete | D9 metrics, C × S × Φ × R validated |
| Witness system framework | ⚠️ Partial | 8 witness types, not persisted to chain |
| Coherence regulation | ⚠️ Partial | Decay, soft bounds implemented |
| Blockchain consensus | ❌ Not started | Zero consensus backend |
| VCM recipient attestation | ❌ Not started | Vision only |
| ATP/ADP settlement | ❌ Not started | No energy accounting |
| **Hardware binding** | 🚨 **P0 BLOCKER** | Keys stored in filesystem |

### Completed Features
- [x] LCT data structure implementation
- [x] Basic cryptographic functions (Ed25519)
- [x] File-based storage backend
- [x] T3/V3 tensor calculations
- [x] Identity coherence scoring (C × S × Φ × R)
- [x] Self-reference detection (D9 metric)
- [x] Coherence threshold enforcement
- [x] Death spiral detection and prevention
- [x] Temporal decay (6-hour half-life)
- [x] Soft bounds preventing lock-out
- [x] 8 witness types (TIME, AUDIT, ORACLE, EXISTENCE, ACTION, STATE, QUALITY, AUDIT_MINIMAL)
- [x] Nonce-based replay protection
- [x] Witness reputation tracking

### Roadmap (Pending Hardware Binding)
- [ ] TPM 2.0 integration (hardware-sealed keys)
- [ ] TrustZone/OP-TEE for ARM platforms
- [ ] Hardware attestation protocols
- [ ] PCR sealing for boot-time verification
- [ ] Four-tier blockchain implementation
- [ ] ATP/ADP token system
- [ ] VCM multi-party attestation
- [ ] Cross-chain value transfer
- [ ] Production deployment

## Appendix H: Glossary of Acronyms

| Acronym | Full Form | Description |
|---------|-----------|-------------|
| **LCT** | Linked Context Token | Non-transferable identity token |
| **ATP** | Allocation Transfer Packet | Energy/value tracking system |
| **ADP** | Allocation Discharge Packet | Spent ATP awaiting certification |
| **T3** | Trust Tensor | Capability assessment (Talent, Training, Temperament + extended dims) |
| **V3** | Value Tensor | Value creation (Valuation, Veracity, Validity) |
| **MRH** | Markov Relevancy Horizon | Contextual relevance boundary |
| **SNARC** | Surprise, Novelty, Arousal, Reward, Conflict | Affect gating signals |
| **HRM** | Hierarchical Reasoning Model | Two-level reasoning architecture |
| **SAGE** | Self-Aware Goal-directed Entity | AI identity research testbed |
| **VCM** | Value Confirmation Mechanism | Multi-party value certification |
| **MCP** | Model Context Protocol | AI model communication standard |
| **D9** | Dimension 9 | Self-reference frequency metric |
| **C_STABLE** | Coherence Stable Threshold | 0.7 minimum for trust accumulation |
| **TPM** | Trusted Platform Module | Hardware security for key binding |
| **SE** | Secure Enclave | Hardware-isolated key storage |

---

*These appendices provide technical details for implementers. For the latest specifications and updates, see https://github.com/dp-web4/web4*