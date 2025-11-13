# GitHub Issues Ready to Create

**Status**: Ready to create - Post these as issues on the web4 repository
**Labels**: Use labels like `question`, `enhancement`, `security`, `help wanted`, `research`

---

## Issue 1: LCT Agent-to-Organization Relationship Design

**Title**: How should LCTs represent agent-to-organization relationships?

**Labels**: `question`, `design`, `identity`, `help wanted`

**Body**:

### Context

Web4 LCT (Lightweight Context Token) currently handles individual entity identity, but we need to design how AI agents represent their relationship to organizations.

### Current Implementation

```python
lct_credential = {
    "entity_id": "claude-anthropic-instance-001",
    "entity_type": "ai_agent",
    "bound_to": "dennis-palatov",  # Individual human
    "public_key": "ed25519:...",
}
```

### Questions

1. **Multi-level hierarchy**: How do we represent Agent → Team → Organization → Consortium?
2. **Authority delegation**: Can organizations delegate to teams, teams to agents?
3. **Reputation aggregation**: Does org reputation aggregate from member reputation?
4. **Credential revocation**: Who can revoke at each level?
5. **Cross-organization**: Can agents work for multiple organizations?

### Example Scenarios

**Scenario 1**: Research Lab with AI Agents
```
MIT AI Lab (org)
  → Robotics Team (team)
    → Agent-R1, Agent-R2 (agents)
  → NLP Team (team)
    → Agent-N1, Agent-N2 (agents)
```

**Scenario 2**: AI Agent Freelancer
```
Agent-Freelance-001 works for:
  → CompanyA (contract, expires 2025-12-31)
  → CompanyB (contract, expires 2026-03-15)
  → Individual clients (multiple LCT bindings)
```

### Proposed Approaches

**Option A**: Hierarchical LCT chains
```json
{
  "entity_id": "agent-r1",
  "bound_to_chain": [
    "robotics-team",
    "mit-ai-lab",
    "mit-university"
  ]
}
```

**Option B**: Multi-binding with delegation proofs
```json
{
  "entity_id": "agent-freelance-001",
  "bindings": [
    {"org": "company-a", "delegation": "...", "expires": "2025-12-31"},
    {"org": "company-b", "delegation": "...", "expires": "2026-03-15"}
  ]
}
```

**Option C**: Role-based with context
```json
{
  "entity_id": "agent-001",
  "roles": [
    {"org": "company-a", "role": "data-analyst", "context": "..."},
    {"org": "company-b", "role": "code-reviewer", "context": "..."}
  ]
}
```

### What We Need

- Feedback on proposed approaches
- Alternative designs
- Real-world use cases we're missing
- Security implications (privilege escalation, confused deputy, etc.)
- Implementation considerations (performance, scalability)

### References

- LCT Registry implementation: `implementation/reference/lct_registry.py`
- Authorization engine: `implementation/reference/authorization_engine.py`
- Current delegation format in code

**Your input welcome!**

---

## Issue 2: Sybil Attack Resistance in Reputation System

**Title**: How can we prevent Sybil attacks on the T3/V3 reputation system?

**Labels**: `security`, `reputation`, `attack-vector`, `help wanted`

**Body**:

### Context

Web4's reputation system uses T3/V3 tensors (Talent/Training/Temperament and Veracity/Validity/Value) with gaming resistance mechanisms. We need to ensure it resists Sybil attacks at scale.

### Current Mitigations

From `implementation/reference/reputation_engine.py`:

```python
# Gaming resistance mechanisms:
1. Witness boost (1.2x) - reputation gains higher when witnessed
2. Consistency bonus (1.1x) - reward reliable performance
3. Novelty multiplier (1.5x) - encourage innovation
4. Diminishing returns - high reputation = slower gains
5. Time decay - training atrophies without practice
6. Pattern detection - identifies suspicious activity
```

### Attack Scenario

**Attack**: Create 100 fake AI entities, have them witness each other's actions to boost reputation artificially.

```
Attacker creates: Agent-001 through Agent-100
  Agent-001 performs action → witnessed by Agent-002, Agent-003
  Agent-002 performs action → witnessed by Agent-001, Agent-003
  ...
  All agents gain 1.2x witness boost
  → Reputation laundering through mutual witnessing
```

### Current Detection

Pattern detection catches:
- High success rate without external witnesses (suspicious)
- Rapid reputation growth (likely gaming)
- Circular witness patterns (collusion)

But:
- What if Sybils build reputation slowly over time?
- What if they occasionally witness legitimate actions to blend in?
- What if collusion groups are large and distributed?

### Questions

1. **Witness Web of Trust**: Should witnesses themselves need reputation?
2. **Stake Requirements**: Should entities stake ATP to become witnesses?
3. **Witness Diversity**: Require witnesses from different organizations/contexts?
4. **Graph Analysis**: Use social graph metrics to detect collusion clusters?
5. **Proof of Work/Stake**: Require computational/economic cost to create identities?
6. **Invitation System**: New entities must be vouched for by established ones?

### Proposed Enhancements

**Option A**: Witness Reputation Weighting
```python
witness_boost = 1.2 * witness_reputation_score
# Low-reputation witnesses provide minimal boost
# High-reputation witnesses provide full boost
```

**Option B**: ATP Staking for Witnesses
```python
to_witness_action:
    require_stake(100 ATP)  # Lost if caught gaming
    if witness_fraud_detected:
        slash_stake()
```

**Option C**: Cross-Context Witness Requirement
```python
witness_requirements = {
    "min_witnesses": 2,
    "require_diversity": True,  # Different orgs/contexts
    "max_from_same_org": 1
}
```

### Test Cases Needed

We need attack simulations:
1. Slow Sybil reputation building (years, not days)
2. Large collusion networks (1000+ entities)
3. Blending attack (Sybils + legitimate witnesses)
4. Reputation washing (transfer through intermediaries)

### What We Need

- Attack scenarios we haven't considered
- Proven techniques from other systems (blockchain, social networks)
- Trade-offs analysis (security vs usability)
- Game theory analysis
- Implementation guidance

### References

- Reputation engine: `implementation/reference/reputation_engine.py`
- Security audit: `docs/SECURITY_AUDIT.md`
- Pattern detection code in reputation engine

**Security researchers welcome!**

---

## Issue 3: ATP Energy Market Design - Static vs Dynamic Pricing

**Title**: Should ATP resource pricing be static or market-based?

**Labels**: `question`, `design`, `economics`, `resources`

**Body**:

### Context

Web4 uses ATP (Adaptive Trust Points) as energy for resource allocation. Currently, pricing is static (1 ATP = X compute hours). Should we move to dynamic market-based pricing?

### Current Implementation

From `implementation/reference/resource_allocator.py`:

```python
RESOURCE_COSTS = {
    ResourceType.COMPUTE: 10 ATP/hour,
    ResourceType.STORAGE: 1 ATP/GB/month,
    ResourceType.NETWORK: 0.1 ATP/GB transferred
}
```

### Problems with Static Pricing

1. **Supply/Demand Mismatch**: High demand periods waste resources
2. **No Price Discovery**: Can't find fair market value
3. **Gaming**: Entities hoard resources when cheap
4. **Inefficiency**: Resources allocated suboptimally

### Market-Based Pricing Proposal

**Option A**: Simple Supply/Demand
```python
price = base_price * (demand / supply)
# More demand = higher price
# More supply = lower price
```

**Option B**: Auction-Based
```python
# Entities bid ATP for resources
# Highest bidders get allocation
# Market clears at equilibrium price
```

**Option C**: Reputation-Weighted Pricing
```python
price = base_price * (1 - reputation_discount)
# High-reputation entities get lower prices
# Incentivizes good behavior
```

### Questions

1. **Volatility**: How do we prevent extreme price swings?
2. **Poor Entities**: How do low-reputation/low-ATP entities participate?
3. **Market Manipulation**: Can wealthy entities manipulate prices?
4. **Complexity**: Is market-based too complex for most users?
5. **Hybrid Approach**: Mix static base + market dynamics?

### Real-World Analogues

- **AWS Spot Instances**: Market-based, up to 90% cheaper but interruptible
- **Electricity Markets**: Time-of-use pricing, peak vs off-peak
- **Bandwidth Markets**: Congestion pricing on networks

### Trade-Offs

| Approach | Pros | Cons |
|----------|------|------|
| **Static** | Simple, predictable | Inefficient allocation |
| **Market** | Efficient, fair | Complex, volatile |
| **Hybrid** | Balance | Requires careful tuning |

### What We Need

- Economic analysis (game theory, mechanism design)
- Real-world case studies
- Simulation results
- Implementation complexity assessment
- User experience considerations

### References

- Resource allocator: `implementation/reference/resource_allocator.py`
- ATP tracking in authorization engine
- Economics background in Synchronism whitepaper

**Economists and mechanism designers welcome!**

---

## Issue 4: Cross-System Reputation Transfer - Should It Be Allowed?

**Title**: Can/should reputation transfer when entities move between Web4 networks?

**Labels**: `question`, `design`, `reputation`, `federation`

**Body**:

### Context

Web4 T3/V3 reputation is currently network-specific. If an entity moves from NetworkA to NetworkB, should reputation transfer? If so, how?

### Scenarios

**Scenario 1**: AI agent builds reputation in CompanyA's Web4 network
- T3 scores: Talent=0.9, Training=0.8, Temperament=0.9
- V3 scores: Veracity=0.85, Validity=0.9, Value=0.92
- Moves to CompanyB's Web4 network
- **Question**: Start from zero or transfer reputation?

**Scenario 2**: Researcher collaborates across universities
- High reputation in University-A network
- Joins University-B collaboration
- **Question**: Should past reputation count?

**Scenario 3**: Malicious entity with bad reputation
- Burned reputation in NetworkA through ethics violations
- Tries to join NetworkB with clean slate
- **Question**: Should negative history follow them?

### Arguments FOR Transfer

1. **Continuity**: Entities shouldn't lose earned reputation
2. **Efficiency**: Don't need to rebuild trust from zero
3. **Portability**: Enables cross-network collaboration
4. **Fairness**: Past good behavior should count

### Arguments AGAINST Transfer

1. **Context Sensitivity**: Reputation in one domain ≠ another
   - Great data scientist ≠ great roboticist
   - Different orgs have different standards

2. **Reputation Washing**: Buy high reputation in cheap network, use in valuable network

3. **Scale Differences**: Small network (easy to gain rep) vs large network

4. **Trust Boundaries**: NetworkA shouldn't have to trust NetworkB's reputation system

### Proposed Approaches

**Option A**: Full Transfer with Attestation
```python
reputation_transfer = {
    "from_network": "company-a",
    "attestation": sign(network_a_key, reputation_data),
    "t3_scores": {...},
    "v3_scores": {...},
    "verification": "cryptographic_proof"
}
# Receiving network verifies attestation
```

**Option B**: Partial Transfer with Decay
```python
transferred_reputation = original_reputation * 0.5
# Start at half of previous reputation
# Must prove yourself again in new context
```

**Option C**: Context-Mapped Transfer
```python
# Map reputation to new context
if role_similar(old_role, new_role):
    transfer_factor = 0.8
else:
    transfer_factor = 0.3
```

**Option D**: No Transfer, But Visibility
```python
# Reputation doesn't transfer
# But visible as "external reference"
# Like letters of recommendation
```

### Questions

1. **Verification**: How do we verify transferred reputation is legitimate?
2. **Decay Rate**: If partial transfer, what decay rate is fair?
3. **Context Mapping**: How do we map reputation across domains?
4. **Negative Reputation**: Should bad reputation transfer?
5. **Revocation**: Can originating network revoke attestations?

### What We Need

- Real-world examples (academic credentials, professional certifications)
- Security analysis (reputation laundering attacks)
- User studies (what do entities expect?)
- Implementation complexity
- Federation protocol design

### References

- Reputation engine: `implementation/reference/reputation_engine.py`
- T3/V3 tensor definitions
- MRH knowledge graph (for cross-network links)

**Federation and trust experts welcome!**

---

## Issue 5: Audit Trail Completeness Proof

**Title**: How can we cryptographically prove no authorizations were hidden?

**Labels**: `security`, `cryptography`, `audit`, `hard-problem`

**Body**:

### Context

Web4 authorization engine logs all decisions for audit. But how do we prove to auditors that **all** authorizations are in the log (none hidden)?

### Current Implementation

From `implementation/reference/authorization_engine.py`:

```python
audit_entry = {
    "timestamp": now(),
    "entity_id": entity.lct_id,
    "action": action.type,
    "resource": resource_id,
    "decision": "grant" | "deny",
    "reasons": [...],
    "hash": sha256(entry_data)
}
```

Logs are tamper-evident (chained hashes), but **not provably complete**.

### The Problem

**Attack**: Authorization server grants secret permission, doesn't log it
- Auditor sees all logged authorizations
- But can't detect missing entries
- Classic completeness problem

### Proposed Approaches

**Option A**: Merkle Tree with Periodic Commitments
```python
# Every N minutes, commit Merkle root to blockchain
merkle_root = build_tree(all_authorizations_this_period)
blockchain.commit(merkle_root, timestamp)

# Auditor can verify:
# 1. All shown authorizations in tree
# 2. Root matches blockchain commitment
# 3. No authorizations possible between commitments
```

**Problem**: Window between commitments allows hidden authorizations

**Option B**: Counter-Signed by Requesting Entity
```python
# Entity requesting authorization also signs and stores
requester_copy = sign(entity_key, authorization_request)
server_copy = sign(server_key, authorization_decision)

# If discrepancy, entity proves they requested but got no logged response
```

**Problem**: Requires entity to store everything, trust requester

**Option C**: Witness-Based Auditing
```python
# Independent witnesses observe authorization channel
# Multiple witnesses must see same authorizations
# Byzantine fault tolerance - majority agreement
witnesses = [w1, w2, w3, w4, w5]
for auth in authorizations:
    witness_attestations = collect_attestations(witnesses)
    require_majority(witness_attestations)
```

**Problem**: Requires trusted witness network

**Option D**: Zero-Knowledge Proof of Completeness
```python
# Server proves set of authorizations is complete
# Without revealing authorization details
# Uses ZK-SNARKs or similar
proof = zkp.prove(
    statement="all authorizations in [start, end] are in this set",
    public_input=merkle_root,
    private_input=all_authorizations
)
```

**Problem**: Computational complexity, proof system trust

### Questions

1. **Performance**: Can we afford cryptographic overhead?
2. **Trust Model**: Who must we trust (blockchain, witnesses, entities)?
3. **Real-Time**: Must proof be real-time or can it be periodic?
4. **Granularity**: Prove completeness per entity, per resource, or globally?
5. **Recovery**: What if proof system fails temporarily?

### Related Work

- **Certificate Transparency**: Similar problem for TLS certificates
- **Blockchain**: Public ledger completeness
- **Byzantine Consensus**: Agreement on complete set
- **Zero-Knowledge Proofs**: Private completeness proofs

### What We Need

- Cryptography experts
- Formal verification specialists
- Performance analysis (real-world feasibility)
- Trade-offs assessment (security vs overhead)
- Proof of concept implementation

### References

- Authorization engine: `implementation/reference/authorization_engine.py`
- Audit trail in code
- Security audit document

**This is a hard problem. Cryptographers especially welcome!**

---

## How to Create These Issues

1. Go to https://github.com/dp-web4/web4/issues/new
2. Copy the title and body for each issue
3. Add the suggested labels
4. Submit

Or use GitHub CLI if installed:
```bash
gh issue create --title "Issue title" --body "$(cat issue_body.md)" --label "label1,label2"
```

---

**Note**: These issues are designed to invite collaboration from:
- Security researchers (Sybil attacks, audit completeness)
- Economists (ATP market design)
- Cryptographers (proof systems)
- Distributed systems experts (federation)
- AI researchers (multi-agent coordination)
