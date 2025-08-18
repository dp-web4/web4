# Part 6: Blockchain Typology and Fractal Lightchain

## 6.1. The Four-Chain Temporal Hierarchy

WEB4 implements a temporal blockchain hierarchy that matches persistence requirements to verification needs, creating a fractal structure from ephemeral to permanent:

### 6.1.1. Compost Chains (Milliseconds to Seconds)

**Purpose**: Ephemeral working memory for immediate processing
- **Characteristics**: Fast turnover, minimal verification, local-only
- **Use Cases**: Sensor buffers, immediate calculations, working state
- **Persistence**: Minutes to hours before automatic pruning
- **Example Applications**:
  - Real-time battery cell voltage readings
  - Immediate sensor fusion calculations
  - Transient UI state
  - Cache layers

**Implementation Details**:
- No cryptographic signatures required
- Simple append-only logs
- Ring buffer architecture for automatic cleanup
- Zero network overhead

### 6.1.2. Leaf Chains (Seconds to Minutes)

**Purpose**: Short-term episodic memory with selective retention
- **Characteristics**: SNARC-gated retention, local verification
- **Use Cases**: Event logs, transaction records, session data
- **Persistence**: Hours to days with selective promotion
- **Example Applications**:
  - Vehicle trip segments
  - User interaction sessions
  - Temporary collaboration spaces
  - Short-term pattern detection

**Implementation Details**:
- Lightweight cryptographic signatures
- Parent witness marks for important events
- Selective synchronization with peers
- ATP cost: minimal (1-10 units)

### 6.1.3. Stem Chains (Minutes to Hours)

**Purpose**: Medium-term consolidated memory with pattern extraction
- **Characteristics**: Cross-validation, pattern mining, witness aggregation
- **Use Cases**: Aggregated insights, learned behaviors, consolidated knowledge
- **Persistence**: Days to months with value-based retention
- **Example Applications**:
  - Fleet performance patterns
  - Model training checkpoints
  - Organizational memory
  - Trust relationship evolution

**Implementation Details**:
- Full cryptographic verification
- Multi-party witness requirements
- Merkle tree aggregation
- ATP cost: moderate (10-100 units)

### 6.1.4. Root Chains (Permanent)

**Purpose**: Long-term crystallized wisdom and immutable truth
- **Characteristics**: Global consensus, immutable record, maximum verification
- **Use Cases**: Identity anchors, constitutional rules, critical agreements
- **Persistence**: Permanent with no expiration
- **Example Applications**:
  - LCT registrations
  - Organizational charters
  - Verified credentials
  - Historical audit trails

**Implementation Details**:
- Full blockchain consensus
- Multiple witness requirements
- Cross-chain anchoring
- ATP cost: significant (100+ units)

## 6.2. Fractal Lightchain Architecture

The lightchain enables this hierarchy through fractal witnessing without global consensus:

### 6.2.1. Hierarchical Structure

```
                    Root Chain
                        ↑
                 [witness marks]
                        ↑
                   Stem Chains
                        ↑
                 [witness marks]
                        ↑
                   Leaf Chains
                        ↑
                 [witness marks]
                        ↑
                  Compost Chains
```

Each level maintains autonomy while contributing to the whole:
- **Local Block Creation**: Each level creates blocks at its own pace
- **Asynchronous Propagation**: No synchronous coordination required
- **Selective Verification**: Full data retrieved only when needed
- **Privacy Preservation**: Details stay local until requested

### 6.2.2. Witness-Acknowledgment Protocol

The bidirectional proof system ensures trust without consensus:

**Step 1: Witness Mark Creation**
```json
{
  "block_id": "entity-42-block-1337",
  "hash": "sha256:abc123...",
  "timestamp": "2025-08-18T14:00:00.123Z",
  "device_id": "entity-42",
  "summary": {"type": "value_created", "amount": 100},
  "signature": "entity_signature"
}
```

**Step 2: Parent Acknowledgment**
```json
{
  "type": "witness_ack",
  "witnessed_block": "entity-42-block-1337",
  "witness_device": "parent-node",
  "witness_timestamp": "2025-08-18T14:00:01.000Z",
  "trust_delta": +0.01,
  "ack_signature": "parent_signature"
}
```

**Step 3: Acknowledgment Inclusion**
The child includes the acknowledgment in its next block, creating an immutable bidirectional proof of the witnessed event.

### 6.2.3. Lazy Verification

Verification happens on-demand with adjustable depth:

```python
def verify_data(block_id, depth=2):
    # Level 0: Verify data integrity
    if not verify_hash(block_id):
        return False
    
    # Level 1: Check parent witness
    if depth >= 1:
        if not parent_witnessed(block_id):
            return False
    
    # Level 2: Check grandparent witness
    if depth >= 2:
        if not grandparent_witnessed(block_id):
            return False
    
    # Can continue to any depth
    return True
```

## 6.3. Advantages Over Traditional Blockchains

### Scalability
- Each device handles only its own data
- No global state synchronization
- Witness marks are tiny (200-500 bytes)
- Network traffic proportional to hierarchy depth, not node count

### Flexibility
- Different block rates per level (cells: ms, modules: min, packs: hr)
- Multiple data formats (binary, JSON, protobuf)
- Varied storage strategies (memory, disk, distributed)
- Adaptive retention policies per level

### Resilience
- No single point of failure
- Graceful degradation under partition
- Missing witnesses don't break the chain
- Parent can reconstruct from witness marks

### Privacy
- Data stays local by default
- Only hashes propagate upward
- Selective disclosure mechanisms
- Encrypted private channels supported

## 6.4. Integration with Web4 Components

### LCT Integration
Each blockchain level can anchor LCTs:
- Compost: Temporary session LCTs
- Leaf: Task and role LCTs
- Stem: Project and team LCTs
- Root: Permanent entity LCTs

### ATP/ADP Energy Flows
Memory operations consume and generate value:
- **Storage Cost**: Creating blocks costs ATP (varies by level)
- **Access Returns**: Frequently accessed blocks earn ATP
- **Witness Value**: Acknowledgments generate trust and ATP
- **Pruning Recovery**: Forgetting obsolete data recovers ATP

### T3/V3 Trust Metrics
Blockchain operations affect trust scores:
- Reliable witnessing increases T3 scores
- Valuable blocks increase V3 scores
- Failed verifications decrease trust
- Consistent participation builds reputation

## 6.5. Decision Tree for Chain Selection

```
What is the data's lifetime?
├─ < 1 minute → Compost Chain
├─ < 1 hour → Leaf Chain  
├─ < 1 month → Stem Chain
└─ Permanent → Root Chain

What is the verification need?
├─ None → Compost Chain
├─ Local → Leaf Chain
├─ Regional → Stem Chain
└─ Global → Root Chain

What is the ATP budget?
├─ < 1 ATP → Compost Chain
├─ 1-10 ATP → Leaf Chain
├─ 10-100 ATP → Stem Chain
└─ 100+ ATP → Root Chain
```

This typology ensures that each piece of data finds its natural persistence level, optimizing for both efficiency and integrity.