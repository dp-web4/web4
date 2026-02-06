# Adversarial Taxonomy

## Attack Vectors and Defense Analysis for Web4

Version: 1.2
Last Updated: 2026-02-05

---

## 1. Adversary Classification

### 1.1 By Entity Type

| Type | Description | Examples | Primary Motivation |
|------|-------------|----------|-------------------|
| **AI Agent** | Autonomous system optimizing for misaligned objectives | Rogue LLM, gaming bot, adversarial optimizer | Metric optimization, resource acquisition |
| **Human Individual** | Single actor with malicious intent | Fraudster, saboteur, disgruntled user | Financial gain, revenge, ideology |
| **Human Collective** | Coordinated group action | Cartel, nation-state, activist group | Market control, political power, disruption |
| **Societal/Systemic** | Emergent adversarial dynamics | Regulatory capture, market failures, tragedy of commons | Structural incentives, collective action problems |
| **Hybrid** | AI-human coordination | Bot farms with human oversight, AI-assisted fraud | Amplified capability, plausible deniability |

### 1.2 By Motivation

| Category | Goal | Damage Model | Detection Difficulty |
|----------|------|--------------|---------------------|
| **Extractive** | Gain value without providing equivalent value | Value leakage, ATP drain | Medium - leaves economic traces |
| **Manipulative** | Distort trust/reputation for advantage | Trust inflation, reputation laundering | High - mimics legitimate behavior |
| **Destructive** | Destroy system integrity or availability | DoS, data corruption, trust collapse | Low-Medium - obvious effects |
| **Subversive** | Undermine system from within | Governance capture, standard corruption | Very High - looks legitimate |
| **Chaotic** | Maximize entropy/disorder for its own sake | Random attacks, nihilistic destruction | Low - no strategic pattern |

---

## 2. Attack Vector Taxonomy

### 2.1 Identity & Sybil Attacks

| Attack | Mechanism | Cost | Detection | Status |
|--------|-----------|------|-----------|--------|
| **Basic Sybil** | Create fake identities | 1,200-75,000 ATP | LCT verification | MITIGATED |
| **Sybil Farm** | Mass identity creation | High ($$$) | Hardware binding | PARTIALLY MITIGATED |
| **Identity Theft** | Acquire legitimate identity | Variable | Behavioral fingerprinting | RESEARCH |
| **Reputation Inheritance** | Transfer trust to new identity | Medium | Non-transferability rules | MITIGATED |

**Gap**: Well-funded adversaries can still create Sybils. Hardware binding raises floor but doesn't eliminate.

**Related Documentation**: `THREAT_MODEL.md` Section 3.1

### 2.2 Trust & Reputation Attacks

| Attack | Mechanism | Impact | Detection Time | Status |
|--------|-----------|--------|----------------|--------|
| **Trust Inflation** | Build trust then exploit | High | Days-Weeks | PARTIAL (velocity limits) |
| **Reputation Laundering** | Wash bad reputation through intermediaries | Critical | Weeks-Months | PARTIAL (audit trails) |
| **Collusion Ring** | Mutual trust inflation | Critical | Variable | RESEARCH (diversity requirements) |
| **Strategic Withholding** | Hoard quality, deploy strategically | Medium | Months | PARTIAL (variance tracking) |
| **Pump-and-Dump** | Build rep, then "cash out" via bad acts | Medium | Days | MITIGATED (real-time adjustment) |

**Gap**: Long-con attacks (patient adversary building trust over months) remain difficult to detect.

**Related Documentation**: `attack_vectors_reputation_gaming.md`

### 2.3 Economic & Resource Attacks

| Attack | Mechanism | Cost to Attacker | Cost to System | Status |
|--------|-----------|-----------------|----------------|--------|
| **ATP Hoarding** | Accumulate ATP to dominate markets | Capital | Liquidity squeeze | RESEARCH |
| **Front-Running** | Exploit timing for unfair advantage | Low | Trust erosion | N/A (synchronous execution) |
| **Resource Exhaustion** | CPU/memory/bandwidth DoS | Medium | Service degradation | MITIGATED (rate limiting) |
| **Quality Inflation** | Claim high quality for mediocre work | Low | 30% value leakage | PARTIAL (challenge system) |
| **Refund Exploitation** | Game refund mechanisms | Low | ATP drain | MITIGATED (50% retention) |

**Gap**: ATP market dynamics not empirically validated. Hoarding attacks need economic modeling.

**Related Documentation**: `session146_advanced_attack_vectors.md`

### 2.4 Network & Consensus Attacks

| Attack | Mechanism | Requirements | Impact | Status |
|--------|-----------|--------------|--------|--------|
| **Eclipse Attack** | Isolate honest nodes from network | 5+ Sybil nodes | Critical | MITIGATED (diversity sampling) |
| **Byzantine Proposer** | Malicious consensus participant | Node compromise | High | MITIGATED (2/3 threshold) |
| **Gossip Poisoning** | Inject false information | Network access | Medium | MITIGATED (signed gossip) |
| **Partition Attack** | Split network into inconsistent views | Network control | Critical | PARTIAL (CRDT resolution) |

**Gap**: Formal Byzantine fault tolerance proof needed. Partition recovery not fully tested.

**Related Documentation**: `THREAT_MODEL.md` Section 4

### 2.5 MRH (Markov Relevancy Horizon) Attacks

| Attack | Mechanism | Exploits | Status |
|--------|-----------|----------|--------|
| **Overlap Manipulation** | Craft context to appear similar to trusted experts | MRH discovery | RESEARCH |
| **Visibility Eclipse** | Control all visible MRH alternatives | Privacy trade-off | RESEARCH |
| **Context Flooding** | Create fake contexts to dilute trust signals | Context classifier | PARTIAL (count limits) |
| **Context Poisoning** | Manipulate context classification | Classifier vulnerabilities | PARTIAL (ensemble classifiers) |

**Gap**: MRH visibility limits are by design but create coordination blind spots.

### 2.6 Coherence & Decoherence Attacks

| Attack | Mechanism | Theoretical Basis | Status |
|--------|-----------|-------------------|--------|
| **Coherence Spoofing** | Fake coherence metrics | Goodhart's Law | PARTIAL (multi-dimensional) |
| **Decoherence Injection** | Introduce noise to break phase alignment | Phase decorrelation | RESEARCH |
| **Cascade Triggering** | Trigger trust collapse through single violation | Asymmetric trust dynamics | RESEARCH |
| **Complexity Bomb** | Overwhelm system with excessive complexity | Complexity-dependent instability | RESEARCH |

**Gap**: Correlated noise protection not implemented in systems.

### 2.7 Governance Interface Attacks (Cross-Substrate)

These attacks target the interface between human governance (external authority, bioregional councils, standing credentials) and computational trust (T3/ATP). They exploit process rather than protocol.

| Attack | Mechanism | Detection | Status |
|--------|-----------|-----------|--------|
| **Unbundling** | Stay under each individual cap while exceeding aggregate burden | Cumulative cost tracking | RESEARCH |
| **Adjudication Delay** | Stall dispute resolution with evidence requests, jurisdiction claims | Timer enforcement | RESEARCH |
| **Soft Veto via Reasonable Requests** | Impose cumulative requirements that freeze work without violating caps | Transaction cost metering | RESEARCH |
| **Pay-to-Violate** | Leak protected content when penalty < extractive value | Penalty economics | RESEARCH |
| **Forum Shopping** | Register through jurisdiction with cheaper compliance to evade stricter rules | Origin-of-impact binding | RESEARCH |

**Detailed Attack Patterns**:

**Unbundling (Execution Controls Cap Evasion)**
- Stay under holdback cap (20%), audit frequency cap, reporting cap
- Add "documentation prerequisites," "pre-approval gates," "special compliance review"
- Each requirement "reasonable" individually, cumulative effect is veto
- **Tell**: Many small requirements, project effectively frozen but "no cap violated"
- **Mitigation**: Transaction Cost Budget (aggregate burden metering)

**Adjudication Delay**
- Accept external authority nominally: "we'll respect your ruling... eventually"
- Endless evidence requests, jurisdiction challenges, internal committee cycles
- Harm occurs before adjudication completes
- **Tell**: Dispute process becomes paperwork treadmill, no ruling in reasonable time
- **Mitigation**: Hard deadlines + default-state enforcement during dispute

**Soft Veto via Reasonable Requests**
- Never exceed any single cap
- Impose weekly reporting, required tools/platforms, photo/video proof, auditor interviews
- Counterparty time shifts from productive work to compliance theater
- **Tell**: High-legitimacy actors spending >50% time on counterparty requirements
- **Mitigation**: Transaction cost metering; prohibited_requirements block platform lock-in

**Pay-to-Violate (Boundary Arbitrage)**
- Leak boundary-protected content knowing penalty < extractive value
- Use shell recipients outside enforcement reach
- Forward to parties who don't recognize external authority
- **Tell**: Boundary violations become profitable business model
- **Mitigation**: Penalty scaling (harm_class multipliers) + contagion to sponsoring org

**Forum Shopping**
- Operate in Jurisdiction A with strict governance
- Register/route through Jurisdiction B with cheaper compliance requirements
- Claim Jurisdiction B standing for Jurisdiction A operations
- **Tell**: Operational footprint doesn't match registration footprint
- **Mitigation**: Impact-of-operation binding + mutual recognition requirements

**Gap**: These attacks require human governance hooks (external authority registration, dispute resolution binding, sanction execution) that Web4 doesn't currently expose.

**Key Insight**: These are "legitimate actor" attacks - they don't violate any single rule, they erode governance through process. Detection requires measuring cumulative burden, not individual violations.

---

## 3. Destructive Attacks (System Annihilation)

These attacks aim not to extract value but to destroy the system entirely.

### 3.1 Infrastructure Destruction

| Attack | Target | Method | Motivation |
|--------|--------|--------|------------|
| **Key Infrastructure DoS** | Core nodes | Overwhelming resource attacks | Competitor, nation-state |
| **Data Corruption** | Merkle trees, trust stores | Byzantine injection | Saboteur, ideology |
| **Protocol Poisoning** | Consensus mechanism | Exploit implementation bugs | Reputation attack on Web4 |

### 3.2 Trust Network Destruction

| Attack | Target | Method | Motivation |
|--------|--------|--------|------------|
| **Trust Nihilism** | All trust relationships | Systematic false accusations | Anarchist, competitor |
| **Reputation Holocaust** | High-trust nodes | Coordinated smear campaign | Cartel elimination |
| **Forgiveness Exploitation** | Recovery mechanisms | Build trust → violate → appeal → repeat | System gaming |

### 3.3 Economic Destruction

| Attack | Target | Method | Motivation |
|--------|--------|--------|------------|
| **ATP Hyperinflation** | Economic stability | Exploit minting bugs | Currency attack |
| **Market Manipulation** | Price discovery | Coordinated buy/sell | Profit + destruction |
| **Liquidity Crisis** | ATP availability | Coordinated hoarding | System collapse |

### 3.4 Governance Destruction

| Attack | Target | Method | Motivation |
|--------|--------|--------|------------|
| **Regulatory Capture** | External governance | Lobby for hostile regulations | Incumbent protection |
| **Standard Corruption** | Protocol standards | Insert malicious requirements | Long-term subversion |
| **Community Fragmentation** | Social consensus | Divide community on ideology | Competitor, ideology |

---

## 4. Current Defense Inventory

### 4.1 Implemented Defenses (Production-Ready)

| Defense | Attacks Mitigated | Implementation | Reference |
|---------|-------------------|----------------|-----------|
| LCT Hardware Binding | Sybil (basic) | TPM 2.0 attestation | `web4-standard/` |
| Signed Epidemic Gossip | Gossip poisoning | Ed25519 signatures | `federation/` |
| Rate Limiting | Resource exhaustion | 60/min/LCT | `ATTACK_VECTORS.md` |
| Byzantine Consensus | Byzantine proposer | 2/3 threshold | `THREAT_MODEL.md` |
| Merkle Anchoring | Batch replay | Root chaining | `web4-standard/` |
| Witness Diversity | Sybil collusion | ≥3 platforms | `SECURITY.md` |
| Trust Decay | Inactive node abuse | Time-based decay | `trust/` |

### 4.2 Partial Defenses (Need Hardening)

| Defense | Current State | Gap | Priority |
|---------|---------------|-----|----------|
| Velocity Limits | Implemented | Thresholds not empirically validated | HIGH |
| Challenge System | 10% rate | Detection time unknown in adversarial env | HIGH |
| Diversity Requirements | Basic | No formal diversity metric | MEDIUM |
| Appeals Process | Not implemented | Major open problem | CRITICAL |

### 4.3 Research Defenses (Not Implemented)

| Defense | Concept | Blocker |
|---------|---------|---------|
| Behavioral Fingerprinting | Detect identity changes via behavior | Privacy concerns |
| Correlated Noise Protection | Coherence preservation under noise | Implementation complexity |
| Game-Theoretic Proof | Nash equilibrium for honesty | Mathematical complexity |
| Formal Verification | Prove security properties | Specification incomplete |

---

## 5. Attack Success Rates (Historical)

### 5.1 Web4 Testing Results

| Attack | Initial Success | Post-Defense | Sessions |
|--------|-----------------|--------------|----------|
| Coverage Inflation | 67% | 0% | 84+ |
| Delegation Chain | 50% | 0% | 89-91 |
| Quality Inflation | 16.2% | Defended | 73 |
| Sybil Specialist | 39.7% | Defended | 73 |
| Context Poisoning | 0% | N/A | 73 |

### 5.2 Known Vulnerabilities (Not Yet Exploited)

| Vulnerability | Severity | Exploitability | Status |
|---------------|----------|----------------|--------|
| Long-con trust building | HIGH | Medium (requires patience) | OPEN |
| Well-funded Sybil farms | MEDIUM | Low (expensive) | OPEN |
| Appeals process absence | CRITICAL | Low (needs false positive) | OPEN |
| ATP market manipulation | UNKNOWN | Unknown | RESEARCH |

---

## 6. Research Gaps

### 6.1 Theoretical Gaps

1. **No formal security proofs** - All defenses empirical, not proven
2. **No game-theoretic equilibrium** - Don't know if honesty is Nash equilibrium
3. **No adversarial ML analysis** - How do attacks evolve with AI adversaries?
4. **No cross-domain attack analysis** - Attacks spanning multiple systems

### 6.2 Empirical Gaps

1. **No external red team** - All attacks self-inflicted simulations
2. **No real-world validation** - Parameters (stakes, decay rates) not empirically tested
3. **No long-term adversarial data** - Patient attacker behavior unknown
4. **No societal-scale simulation** - Regulatory capture, market dynamics

### 6.3 Implementation Gaps

1. **Appeals process** - Major open problem
2. **Emergency overrides** - What happens when system is wrong?
3. **Recovery mechanisms** - How do reformed actors regain trust?
4. **Human oversight integration** - When does human judgment override?

---

## 7. Priority Matrix

### 7.1 By Impact × Likelihood

| Attack | Impact | Likelihood | Priority |
|--------|--------|------------|----------|
| Long-con trust exploitation | HIGH | MEDIUM | P0 |
| Appeals process exploitation | CRITICAL | LOW (needs bug) | P0 |
| Sybil farm (well-funded) | MEDIUM | LOW | P1 |
| System destruction (nation-state) | CRITICAL | VERY LOW | P1 |
| Collusion ring | HIGH | MEDIUM | P1 |
| ATP market manipulation | UNKNOWN | UNKNOWN | P2 (research) |
| Governance interface (unbundling) | HIGH | MEDIUM | P1 |
| Governance interface (soft veto) | HIGH | HIGH | P0 |
| Forum shopping | MEDIUM | LOW | P2 |

### 7.2 By Defense Maturity

| Category | Maturity | Next Step |
|----------|----------|-----------|
| Sybil resistance | 70% | Hardware binding coverage |
| Reputation gaming | 50% | Velocity validation |
| Economic attacks | 30% | Market simulation |
| Network attacks | 80% | Formal proof |
| Governance attacks | 10% | Framework design |
| Destruction attacks | 20% | Threat modeling |
| Governance interface | 5% | External authority hooks + transaction cost metering |
| Social engineering | 60% | Credential verification standards |
| Regulatory arbitrage | 40% | Jurisdiction binding implementation |
| Emergent dynamics | 55% | Circuit breaker deployment |

---

## 8. Attack Simulation Catalog (126 Attacks)

**Updated**: 2026-02-05
**Total Attacks**: 126 across 35+ tracks

The comprehensive attack simulation catalog (`simulations/attack_simulations.py`) provides executable tests for all attack vectors. Key tracks added in recent sessions:

### Recent Additions (2026-02-05)

**Track EC: Social Engineering in Trust Systems (Attacks 115-118)**
- Authority Impersonation (Milgram obedience)
- Social Proof Manipulation (Asch conformity)
- Urgency/Scarcity Exploitation (FOMO)
- Reciprocity Exploitation (gift traps)

**Track ED: Regulatory and Compliance Arbitrage (Attacks 119-122)**
- Jurisdiction Shopping
- Compliance Theater
- Standard Capture
- Reporting Manipulation (Goodhart's Law)

**Track EE: Emergent System Dynamics (Attacks 123-126)**
- Complexity Bomb (exponential state space)
- Phase Transition Triggering (critical thresholds)
- Positive Feedback Amplification (winner-take-all)
- Network Topology Exploitation (hub/bridge capture)

**Full catalog documentation**: `simulations/docs/ATTACK_CATALOG_SUMMARY.md`

---

## 10. Integration with Existing Documentation

This taxonomy consolidates and extends existing web4 security documentation:

| Document | Focus | How This Extends |
|----------|-------|------------------|
| `THREAT_MODEL.md` | 15+ formal threats | Adds motivation categories, destruction attacks |
| `SECURITY.md` | Defense framework | Adds maturity assessment, gaps |
| `attack_vectors_reputation_gaming.md` | 7 reputation attacks | Adds long-con, societal attacks |
| `session146_advanced_attack_vectors.md` | 6 advanced attacks | Adds coherence attacks, destruction |
| `ATTACK_VECTORS.md` | 16 specific vectors | Adds cross-category synthesis |

---

## References

- web4/THREAT_MODEL.md - Formal 15+ threat enumeration
- web4/SECURITY.md - Defense framework
- web4/attack_vectors_reputation_gaming.md - 7 reputation attacks
- web4/session146_advanced_attack_vectors.md - 6 advanced attacks
- web4/web4-standard/implementation/authorization/ATTACK_VECTORS.md - Specific vectors
- **web4/simulations/attack_simulations.py** - 126 executable attack simulations
- **web4/simulations/docs/ATTACK_CATALOG_SUMMARY.md** - Comprehensive attack catalog
- web4/game/GAME_THEORETIC_EQUILIBRIUM_ANALYSIS.md - Nash equilibrium analysis
- Kahneman & Tversky (1979) - Prospect Theory
- Milgram (1963) - Obedience to Authority
- Asch (1951) - Conformity Studies
- Cialdini (2001) - Influence: The Psychology of Persuasion
