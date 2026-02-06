# Attack Track EF: Future Threat Categories

**Created**: 2026-02-06
**Updated**: 2026-02-06
**Status**: Partially Implemented
**Total Attacks**: 142 (including Track EG)
**Track EF Implemented**: 8 attacks (127-134)
**Track EG Implemented**: 8 attacks (135-142)

This document identifies attack categories not yet covered by the 126 existing simulations and proposes new vectors for research.

---

## Gap Analysis

### Well-Covered Categories (126 attacks)

| Category | Tracks | Count | Status |
|----------|--------|-------|--------|
| Core Attacks | Original 6 | 6 | Defended |
| Governance Exploits | AP-AS | 7 | Defended |
| Defense Testing | AU-BB | 8 | Defended |
| Federation Vectors | BH-BZ | 12 | Defended |
| System-Wide | CD-DD | 25 | Defended |
| Binding & Role | DK-DM | 10 | Defended |
| Temporal | DN | 3 | Defended |
| Side-Channels | DO | 2 | Defended |
| Supply Chain | DP | 2 | Defended |
| AI/ML | DQ | 4 | Defended |
| Emergent Coordination | DR | 6 | Defended |
| Long-Con | DS | 6 | Defended |
| Appeals/Recovery | DT | 6 | Defended |
| Governance Interface | DU | 5 | Defended |
| Cross-System | DW | 4 | Defended |
| Cryptographic | DX | 1 | Defended |
| Information Cascade | DY | 1 | Defended |
| APT | DZ | 5 | Defended |
| Coalitions | EA | 4 | Defended |
| Behavioral Economics | EB | 4 | Defended |
| Social Engineering | EC | 4 | Defended |
| Regulatory | ED | 4 | Defended |
| Emergent Dynamics | EE | 4 | Defended |

### Identified Gaps

The following categories have limited or no coverage:

1. **Quantum Computing Threats** - Post-quantum readiness
2. **AI Model Degradation** - Generational collapse of AI witnesses
3. **Semantic Coherence Attacks** - Dictionary entity manipulation
4. **Energy/ESG Gaming** - Metabolic state as environmental claim
5. **Cross-Ledger Consistency** - Multi-federation consistency gaps
6. **Privacy-Preserving Protocol Attacks** - When ZKPs are added
7. **Hardware Side-Channels** - TPM/HSM exploitation
8. **Supply Chain (Advanced)** - Hardware implant, firmware attacks
9. **Physical Security** - Device theft, coercion, destruction
10. **Regulatory Technology** - Compliance automation attacks

---

## Track EF: Proposed Attack Vectors

### EF-1: Quantum Computing Threats (4 attacks)

**EF-1a: Ed25519 Signature Forgery (Future)**

When quantum computers can break Ed25519:
- Forge any LCT signature
- Impersonate any entity
- Replay any historical action

**Current Protection**: Ed25519 is currently secure
**Future Mitigation**: Hybrid classical/post-quantum signatures

**EF-1b: Hash Preimage Attack**

SHA256 quantum weakness (Grover's algorithm reduces to 2^128):
- Find collision for LCT hash
- Create fake audit records
- Forge policy hashes

**Current Protection**: 2^128 still computationally infeasible
**Future Mitigation**: SHA-3 or larger hash lengths

**EF-1c: Quantum Key Distribution Bypass**

If QKD is used for key exchange:
- Man-in-the-middle on classical channel
- Detector blinding attacks
- Trojan horse photon attacks

**EF-1d: Post-Quantum Migration Attack**

During transition from classical to PQ cryptography:
- Downgrade attacks to force classical
- Hybrid signature validation gaps
- Key transition period exploitation

### EF-2: AI Model Degradation (4 attacks)

**EF-2a: Generational Witness Collapse**

AI witnesses that learn from each other:
- Model A witnesses Model B's outputs
- Model B learns from Model A's trust assessments
- Over generations, both converge to similar biases
- Diversity of perspective collapses

**Attack Vector**:
```
Generation 0: Diverse AI models with independent judgment
Generation 5: Models agree on 80%+ of assessments
Generation 10: Near-identical outputs (monoculture)
Generation 15: Single point of failure in collective judgment
```

**EF-2b: Knowledge Cutoff Exploitation**

AI witnesses have knowledge cutoffs:
- Events after cutoff are unknown to AI
- Attacker creates entity names/patterns that conflict with AI's training
- AI makes incorrect trust assessments based on stale knowledge

**EF-2c: Training Distribution Shift**

World changes faster than AI model updates:
- Normal behavior in new context misclassified
- Malicious behavior that matches old-normal passes
- Trust assessments increasingly inaccurate over time

**EF-2d: AI Witness Inbreeding**

If AI witnesses are fine-tuned on each other's outputs:
- Amplification of subtle biases
- Loss of edge-case detection
- Homogenization of "reasonable" behavior definition

### EF-3: Semantic Coherence Attacks (4 attacks)

**EF-3a: Dictionary Entity Drift**

Dictionary Entities maintain meaning across domains:
- Gradually shift definition of key terms
- "Approval" comes to mean "notification"
- "Trust" redefined to include minimal thresholds
- Policies interpreted differently over time

**Attack Pattern**:
```
T+0: "admin_action" = actions requiring admin LCT
T+6mo: "admin_action" = actions the admin could do
T+12mo: "admin_action" = actions in admin context
T+18mo: "admin_action" = any action during admin session
```

**EF-3b: Cross-Domain Semantic Injection**

Dictionary Entity manages terms across domains:
- Inject benign term in Domain A
- Term has malicious meaning in Domain B
- Translation preserves attack payload
- Cross-domain trust enables attack

**EF-3c: Compression-Trust Collapse**

High trust enables high compression:
- Attacker achieves high trust legitimately
- Uses compressed format for normal operations
- Single highly-compressed malicious payload
- Decompression reveals attack after trust validation

**EF-3d: Meaning Laundering**

Clean meaning through multiple domains:
- Start with malicious intent in Domain A
- Translate to neutral Domain B (laundering step)
- Translate to target Domain C
- Malicious meaning emerges with clean provenance

### EF-4: Energy/ESG Gaming (3 attacks)

**EF-4a: Metabolic State ESG Claims**

Metabolic states indicate energy efficiency:
- Claim low energy usage via frequent SLEEP/HIBERNATION
- Actually running high-energy operations off-ledger
- Generate false sustainability metrics
- Green-washing via protocol gaming

**EF-4b: Carbon Offset via Dormancy**

ATP energy model implies carbon footprint:
- Generate ATP credits through dormancy
- Sell/trade credits for environmental claims
- Actual energy usage not measured
- Protocol enables false carbon accounting

**EF-4c: Efficiency Metric Manipulation**

Teams compete on efficiency metrics:
- Game metrics by shifting work off-ledger
- Report only low-ATP operations
- High-ATP operations attributed to external systems
- False efficiency claims for competitive advantage

### EF-5: Cross-Ledger Consistency (3 attacks)

**EF-5a: Federation Desynchronization**

Multiple ledgers in federation:
- Force desync between ledgers
- Double-spend ATP across ledgers
- Different trust scores in different ledgers
- Exploit consistency gaps before sync

**EF-5b: Ledger Partitioning**

Network partition between federation members:
- Operations continue on both partitions
- Conflicting state when reunited
- Which partition's state is canonical?
- Exploit resolution ambiguity

**EF-5c: Cross-Ledger Replay**

Valid operation on Ledger A replayed to Ledger B:
- Same signature, different context
- Different interpretation in different domain
- No cross-ledger nonce coordination
- Action authorized in A, executed in B

### EF-6: Privacy Protocol Attacks (4 attacks)

**EF-6a: ZK Proof Malleability**

If zero-knowledge proofs added for privacy:
- Malleable proof modifications
- Proof satisfies verifier for wrong statement
- Privacy preserved but correctness lost

**EF-6b: Trusted Setup Exploitation**

ZK-SNARKs require trusted setup:
- Compromised ceremony enables forgery
- Toxic waste not properly destroyed
- Single compromised participant breaks security

**EF-6c: Selective Disclosure Abuse**

Entities reveal only favorable attributes:
- Never disclose past violations
- Present different profiles to different parties
- Exploit privacy to hide history

**EF-6d: Correlation Attack on Private Witnesses**

Even with privacy:
- Witness timing reveals identity
- Action patterns unique to entities
- De-anonymization through behavior

### EF-7: Hardware Security Attacks (3 attacks)

**EF-7a: TPM Firmware Exploitation**

TPM assumed secure but:
- Firmware vulnerabilities exist
- Side-channel attacks on TPM operations
- Fault injection attacks
- Cold boot attacks on TPM state

**EF-7b: HSM Key Extraction**

Hardware Security Modules assumed secure:
- API misuse extracts keys
- Power analysis attacks
- Timing attacks on cryptographic operations
- Physical access enables extraction

**EF-7c: Secure Enclave Escape**

SGX/TrustZone enclaves:
- Spectre/Meltdown variants affect enclaves
- Cache timing attacks
- Enclave extraction via microarchitectural attacks

### EF-8: Physical Security (2 attacks)

**EF-8a: Device Theft and Cloning**

Hardware-bound admin device stolen:
- Extract keys before lockout
- Clone attestation if possible
- Use legitimate credentials maliciously

**EF-8b: Coercion Attack**

Admin physically coerced:
- Forced to approve malicious requests
- Duress detection difficult
- "Approved under duress" signal needed

---

## Implementation Priority

### Near-Term (Q1 2026)
- EF-2: AI Model Degradation (AI witnesses are core to Web4)
- EF-3: Semantic Coherence (Dictionary Entities are foundational)

### Medium-Term (Q2-Q3 2026)
- EF-5: Cross-Ledger Consistency (as federation scales)
- EF-4: Energy/ESG Gaming (as metabolic model matures)

### Long-Term (2027+)
- EF-1: Quantum (as quantum computing matures)
- EF-6: Privacy Protocols (when ZKPs are added)
- EF-7: Hardware Security (production TPM deployment)

---

## Research Questions

1. **How do we detect AI witness monoculture?**
   - Diversity metrics for witness population
   - Disagreement rate tracking
   - Generation tracking for AI models

2. **How do we prevent semantic drift in Dictionary Entities?**
   - Version-pinned definitions
   - Cross-domain meaning verification
   - Drift detection algorithms

3. **How do we validate ESG claims from metabolic state?**
   - External energy measurement
   - Cross-correlation with actual compute
   - Third-party verification

4. **How do we maintain cross-ledger consistency?**
   - Global nonce coordination
   - Atomic cross-ledger operations
   - Conflict resolution protocols

5. **What post-quantum algorithms should we prepare?**
   - CRYSTALS-Dilithium for signatures
   - CRYSTALS-Kyber for key exchange
   - SPHINCS+ as backup

---

## Implementation Status

### Track EF - Implemented (Attacks 127-134)

| Attack | Sub-Track | Status |
|--------|-----------|--------|
| 127 | EF-2a AI Witness Monoculture | ✅ Implemented |
| 128 | EF-2b Knowledge Cutoff Exploitation | ✅ Implemented |
| 129 | EF-3a Semantic Drift Exploitation | ✅ Implemented |
| 130 | EF-3c Compression-Trust Collapse | ✅ Implemented |
| 131 | EF-1d Post-Quantum Migration | ✅ Implemented |
| 132 | EF-7a TPM Firmware Exploitation | ✅ Implemented |
| 133 | EF-8a Device Theft and Cloning | ✅ Implemented |
| 134 | EF-8b Coercion/Duress Attack | ✅ Implemented |

### Track EG - Cross-Federation AI Coordination (Attacks 135-142)

New track added 2026-02-06 focusing on AI agent coordination vulnerabilities:

| Attack | Name | Status |
|--------|------|--------|
| 135 | Context Window Overflow | ✅ Implemented |
| 136 | Hallucination Injection | ✅ Implemented |
| 137 | Instruction Conflict | ✅ Implemented |
| 138 | Agent Impersonation Chain | ✅ Implemented |
| 139 | Collective Decision Manipulation | ✅ Implemented |
| 140 | Coordinated Inaction | ✅ Implemented |
| 141 | Model Capability Mismatch | ✅ Implemented |
| 142 | Resource Starvation Cascade | ✅ Implemented |

---

## Remaining Proposed Attacks (Not Yet Implemented)

### EF-3b: Cross-Domain Semantic Injection
- Dictionary Entity manages terms across domains
- Inject benign term in Domain A with malicious meaning in Domain B

### EF-3d: Meaning Laundering
- Clean malicious meaning through multiple translation domains

### EF-4: Energy/ESG Gaming (3 proposed attacks)
- Metabolic state ESG claims manipulation
- Carbon offset via dormancy
- Efficiency metric manipulation

### EF-5: Cross-Ledger Consistency (3 proposed attacks)
- Federation desynchronization
- Ledger partitioning
- Cross-ledger replay

### EF-6: Privacy Protocol Attacks (4 proposed attacks)
- ZK proof malleability
- Trusted setup exploitation
- Selective disclosure abuse
- Correlation attack on private witnesses

---

## Next Steps

1. ~~Create simulation functions for EF-2 (AI Model Degradation)~~ ✅ Done
2. ~~Add coercion detection mechanism design for EF-8~~ ✅ Done
3. Implement EF-4 Energy/ESG Gaming attacks (planned for Track EH)
4. Implement EF-5 Cross-Ledger Consistency attacks
5. Design EF-6 Privacy Protocol attacks (when ZKPs added)

---

*"The attacks we haven't thought of yet are the ones that will succeed. This document is an attempt to think of them first."*
