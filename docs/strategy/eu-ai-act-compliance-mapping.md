# EU AI Act Compliance Mapping — Web4 Infrastructure

**Version**: 1.0
**Date**: February 19, 2026
**Status**: Working draft — article-by-article mapping
**Deadline**: August 2, 2026 (high-risk AI system obligations apply)
**Regulation**: EU Regulation 2024/1689 (the "AI Act")

---

## Executive Summary

Web4 provides **native compliance infrastructure** for organizations deploying high-risk AI systems under the EU AI Act. Rather than retrofitting compliance onto existing architectures, Web4's foundational primitives — LCT presence tokens, T3/V3 trust tensors, ATP/ADP energy accounting, R6 action framework, and immutable ledgers — map directly onto the Act's core requirements.

This document provides the article-by-article mapping, citing specific Web4 specifications and implementations that satisfy each requirement.

**Key positioning**: Web4 is not an AI system subject to the Act. It is the **infrastructure layer** that enables AI systems to satisfy the Act's requirements by design. Organizations using Web4 gain compliance primitives out of the box.

---

## Compliance Timeline

| Date | Milestone | Web4 Readiness |
|------|-----------|----------------|
| Feb 2, 2025 | Prohibited AI practices in effect | N/A (Web4 doesn't enable prohibited uses) |
| Aug 2, 2025 | GPAI model obligations begin | Partial (audit trails available) |
| **Aug 2, 2026** | **Full high-risk AI system compliance** | **Target: infrastructure-ready** |
| Aug 2, 2027 | High-risk AI in regulated products | Full compliance infrastructure |

**Penalty exposure**: Non-compliance can cost up to 7% of global annual revenue.

---

## Article-by-Article Mapping

### Article 6 — Classification of High-Risk AI Systems

**Requirement**: Determine whether an AI system qualifies as high-risk under Annex III categories (biometrics, critical infrastructure, education, employment, essential services, law enforcement, migration, justice).

**Web4 Mechanism**: Entity type taxonomy with classification metadata.

| Requirement Detail | Web4 Component | Spec Reference |
|---|---|---|
| System classification and intended purpose | `entity_type` field in LCT with 15 entity types | `web4-standard/core-spec/entity-types.md` |
| Classification persistence and auditability | LCT birth certificate records entity classification at creation | `web4-standard/core-spec/LCT-linked-context-token.md` §4 |
| Classification change tracking | Ledger entries record any reclassification with witness attestation | `ledgers/spec/witness-protocol/` |

**Evidence**: Entity type taxonomy (`entity-types.md`) defines AI, Human, Device, Service, Policy, and 10 other types. Each entity's classification is recorded in its LCT birth certificate and immutably logged.

**Gap**: No explicit Annex III category mapping in entity metadata. Recommend adding `annex_iii_category` optional field to LCT schema.

---

### Article 9 — Risk Management System

**Requirement**: Establish a continuous, iterative risk management system throughout the AI system's lifecycle. Must identify, analyze, evaluate, and mitigate risks. Post-market data must feed back into risk evaluation.

**Web4 Mechanism**: ATP/ADP energy cycle + T3 trust tensors + PolicyEntity evaluation.

| Requirement Detail | Web4 Component | Spec Reference |
|---|---|---|
| Continuous risk identification | T3 trust tensors track 3 root risk dimensions (Talent/Training/Temperament) per entity | `web4-standard/ontology/t3v3-ontology.ttl` |
| Lifecycle-wide risk process | ATP/ADP cycle enforces energy accounting from allocation through discharge to recharge | `web4-standard/core-spec/atp-adp-cycle.md` |
| Risk mitigation measures | PolicyEntity evaluates policy rules as IRP energy function; can block, modify, or flag actions | `docs/history/design_decisions/POLICY-ENTITY-REPOSITIONING.md` |
| Post-market risk feedback | T3 tensor updates flow through `update_from_outcome()` after each action result | `simulations/coherence_trust_tensor.py` |
| Documented risk register | 424+ attack vectors across 84 tracks with defense coverage | `simulations/docs/ATTACK_CATALOG_SUMMARY.md` |

**Evidence**:
- T3 tensors provide **real-time risk scoring** across three root dimensions, each decomposable into sub-dimensions via `web4:subDimensionOf` RDF predicates
- ATP/ADP cycle ensures **resource traceability** — every action has a measurable energy cost, creating audit trail of resource consumption
- PolicyEntity (15th entity type) enables **governance-as-code** — policy rules are living entities with their own LCTs, evaluated through IRP plugin architecture
- Attack simulation suite provides **empirical risk evidence** — 424 vectors tested, ~85% detection rate (FO-GB classifier)

**Gap**: No formal Art. 9-compliant risk register template. Recommend creating `docs/compliance/risk-register-template.md`.

---

### Article 10 — Data and Data Governance

**Requirement**: Training, validation, and testing data must be relevant, representative, free of errors, and complete. Appropriate data governance practices including examination for biases.

**Web4 Mechanism**: Immutable behavioral history + reputation washing detection + V3 value tensors.

| Requirement Detail | Web4 Component | Spec Reference |
|---|---|---|
| Data quality assurance | V3 Veracity dimension tracks data truthfulness and accuracy | `web4-standard/ontology/t3v3-ontology.ttl` |
| Bias examination | Trust tensor multidimensionality reveals bias — single-dimension scores expose narrow training | `web4-standard/core-spec/mrh-tensors.md` |
| Data provenance tracking | Ledger entries provide hash-chained provenance for all data operations | `ledgers/README.md` |
| Representative datasets | Witness diversity requirements (minimum 3 from different societies) detect monoculture bias | `simulations/signed_gossip.py` |
| Bias detection in reputation | Reputation washing detection identifies manipulated trust histories | `simulations/docs/ATTACK_CATALOG_SUMMARY.md` Track EB |

**Evidence**:
- V3 tensor root dimensions (Valuation/Veracity/Validity) provide structured quality assessment for data-related operations
- MRH (Markov Relevancy Horizon) scopes relevance — irrelevant data naturally falls outside the context window
- Witness diversity system requires attestations from >=3 independent societies, reducing single-source bias
- Reputation washing detection (Track EB attacks) identifies entities attempting to fabricate clean data histories

**Gap**: No explicit dataset bias auditing tool. Web4 provides the primitives (tensor scoring, witness diversity) but not a turnkey bias audit workflow.

---

### Article 11 — Technical Documentation

**Requirement**: Prepare and maintain technical documentation before market placement, demonstrating compliance. Must include system description, design specs, risk management measures, validation procedures.

**Web4 Mechanism**: LCT birth certificates + R6 action records + whitepaper documentation.

| Requirement Detail | Web4 Component | Spec Reference |
|---|---|---|
| System description | LCT birth certificate contains entity type, capabilities, binding level, policy references | `web4-standard/schemas/lct.schema.json` |
| Design specifications | Entity type spec with behavioral modes (Agentic/Responsive/Delegative) and energy patterns | `web4-standard/core-spec/entity-types.md` |
| Risk management documentation | Formal threat model v2.0 with adversary capability matrix | `docs/reference/security/THREAT_MODEL.md` |
| Validation and testing | 424 attack simulations with documented results across 84 tracks | `simulations/` directory |
| Version tracking | LCT lineage and `lineage_depth` track entity evolution | `web4-core/src/lct.rs` |

**Evidence**:
- LCT JSON schema (`lct.schema.json`) enforces structured documentation at entity creation
- R6 framework captures every action with structured metadata (Rules/Role/Request/Reference/Resource/Result)
- Whitepaper provides 100+ pages of technical documentation
- Each LCT carries its complete lineage history, enabling reconstruction of any entity's evolution

**Status**: Strong. Web4's documentation-by-design approach inherently satisfies this article.

---

### Article 12 — Record-Keeping and Logging

**Requirement**: High-risk AI systems must automatically log events throughout operational lifetime. Logs must enable traceability, monitoring for anomalies, and be retained for minimum 6 months.

**Web4 Mechanism**: Fractal chain ledger architecture + R6 audit trails + witness protocol.

| Requirement Detail | Web4 Component | Spec Reference |
|---|---|---|
| Automatic event logging | R6 framework records every action with structured before/after hooks | `web4-standard/core-spec/r6-implementation-guide.md` |
| Traceability of operations | Hash-chained ledger entries with SHA-256 provenance | `ledgers/reference/python/enterprise_ledger.py` |
| Anomaly monitoring | T3 tensor drift detection identifies behavioral changes over time | `simulations/coherence_trust_tensor.py` |
| Log retention (>=6 months) | Fractal chain: Compost (ephemeral) → Leaf → Stem → Root (permanent) | `ledgers/spec/fractal-chains/` |
| Immutable record store | ACT Chain: 81,000+ lines Go, Cosmos SDK, distributed ledger | `ledgers/act-chain/` |

**Evidence**:
- **R6 Tier 1 (Observational)**: Already deployed in moltbot plugin — records all tool calls in hash-linked JSONL chains
- **Fractal chain architecture**: Four temporal layers ensure appropriate retention — ephemeral data composts, significant events promote to permanent Root chain
- **ACT Chain**: Production-ready distributed ledger (81,000+ lines Go) provides the permanent record layer
- **Enterprise Ledger**: Python implementation (730 lines, production-ready) with `verify_chain()` integrity checking
- **Metabolic timing**: Ledger block intervals adapt to activity level (60s active, 300s rest, 1800s sleep, 3600s hibernation)

**Status**: **Strongest mapping.** Web4's ledger architecture was designed for exactly this use case. Multiple implementations exist across languages.

---

### Article 13 — Transparency and Information Provision

**Requirement**: High-risk AI systems must be sufficiently transparent for deployers to interpret outputs. Instructions for use must include provider identity, system capabilities/limitations, performance metrics, and human oversight measures.

**Web4 Mechanism**: LCT hardware-anchored identities + tensor-scored explanations + immutable ledger entries.

| Requirement Detail | Web4 Component | Spec Reference |
|---|---|---|
| Provider identity | LCT contains `subject` (DID), `created_by`, and verifiable public key | `web4-standard/core-spec/LCT-linked-context-token.md` |
| System capabilities | Entity type taxonomy with behavioral modes and energy metabolism patterns | `web4-standard/core-spec/entity-types.md` |
| Performance metrics | T3/V3 tensor scores provide 6 root dimensions of measurable performance | `web4-standard/ontology/t3v3-ontology.ttl` |
| Interpretable outputs | R6 Result includes `status`, `output_hash`, `trust_delta`, `coherence` score | `web4-standard/core-spec/r6-implementation-guide.md` |
| Hardware-anchored identity | Hardware binding levels 1-5 with verifiable attestation | `core/lct_binding/` |

**Evidence**:
- LCT identities are **verifiable** — hardware-bound at Level 5 (TPM2/TrustZone), cryptographically signed at all levels
- T3 tensor (Talent/Training/Temperament) provides structured, quantitative performance assessment
- V3 tensor (Valuation/Veracity/Validity) provides structured value assessment
- R6 framework forces structured output with explicit success/failure status and measurable coherence
- Every action is attributed to a specific LCT, making attribution and explanation traceable

**Gap**: No dedicated "instructions for use" document generator. Recommend tooling that exports LCT metadata + tensor history into Art. 13-compliant format.

---

### Article 14 — Human Oversight

**Requirement**: AI systems must be designed for effective human oversight. Humans must be able to understand capabilities/limitations, monitor operations, detect anomalies, override/interrupt/shut down the system, and refrain from using outputs in certain situations.

**Web4 Mechanism**: SAGE/HRM governance patterns + human-in-the-loop overrides + R6 approval workflow.

| Requirement Detail | Web4 Component | Spec Reference |
|---|---|---|
| Understand capabilities | Entity type modes (Agentic/Responsive/Delegative) with explicit capability declarations | `web4-standard/core-spec/entity-types.md` |
| Monitor operations | Real-time T3/V3 tensor monitoring with drift detection | `simulations/coherence_trust_tensor.py` |
| Detect anomalies | Trust tensor entropy increase and boundary permeability spikes | `docs/strategy/cross-model-strategic-review-2026-02.md` §4d |
| Override/interrupt | R6 Tier 2 requires admin approval; PolicyEntity can block actions | `web4-standard/core-spec/r6-implementation-guide.md` Tier 2 |
| Shutdown capability | LCT status transitions: Active → Dormant → Void → Slashed | `web4-core/src/lct.rs` |
| Human-in-the-loop | Society governance with human Law Oracle approval for critical operations | `web4-standard/core-spec/atp-adp-cycle.md` §3 |

**Evidence**:
- **R6 Tier 2 (Authorization)**: Full approval workflow — admin must approve actions based on policy, trust thresholds, and ATP balance
- **LCT lifecycle management**: Entities can be transitioned to Dormant (paused), Void (terminated), or Slashed (trust penalty) by authorized humans
- **PolicyEntity evaluation**: Policy rules are themselves living entities that can be updated by human governance
- **SAGE integration**: Human-in-the-loop overrides at tensor/reputation level, federated trust with governance patterns
- **Crisis mode**: `accountability_frame` field in PolicyEvaluation distinguishes normal vs crisis contexts, changing the accountability equation

**Status**: Strong. The R6 approval workflow with LCT lifecycle management provides exactly the oversight mechanisms the Act requires.

---

### Article 15 — Accuracy, Robustness, and Cybersecurity

**Requirement**: AI systems must achieve appropriate accuracy levels (with declared metrics), resilience against errors/faults, robustness against adversarial attacks, and technical redundancy.

**Web4 Mechanism**: Hardware binding + sybil-resistant LCTs + 424+ attack simulation corpus + trust tensor monitoring.

| Requirement Detail | Web4 Component | Spec Reference |
|---|---|---|
| Accuracy metrics | T3/V3 tensor scores with declared dimensions and measurement methodology | `web4-standard/ontology/t3v3-ontology.ttl` |
| Resilience against errors | Fractal chain architecture with 4 temporal layers; hash integrity checking | `ledgers/spec/fractal-chains/` |
| Adversarial robustness | 424 attack vectors across 84 tracks with ~85% detection (FO-GB) | `simulations/docs/ATTACK_CATALOG_SUMMARY.md` |
| Protection against unauthorized access | Hardware binding (TPM2/TrustZone) makes key extraction physically impossible at Level 5 | `core/lct_binding/tpm2_provider.py` |
| Sybil resistance | Economic stakes (ATP cost) + witness diversity + challenge protocols | `simulations/signed_gossip.py`, `simulations/challenge_protocol.py` |
| Technical redundancy | Multi-device LCT constellation with device loss recovery | `web4-standard/core-spec/multi-device-lct-binding.md` |

**Evidence**:
- **Attack simulation corpus**: 424 vectors is the largest empirical attack testing corpus for any trust infrastructure project. Categories include: Sybil attacks, collusion, reputation washing, resource drain, eclipse attacks, prompt injection, goal drift, cross-chain MEV, AI agent collusion, ESG gaming, APT patterns, privacy/ZK attacks
- **Hardware binding**: TPM2 implementation on Legion, TrustZone planned for ARM64 (Thor/Sprout). Level 5 keys are non-extractable (`FIXEDTPM|FIXEDPARENT` attributes)
- **Defense-in-depth**: Economic layer (ATP costs make attacks expensive) + Social layer (witness diversity detects collusion) + Cryptographic layer (Ed25519/P-256 signatures prevent forgery) + Behavioral layer (trust tensors detect anomalies over time)
- **Multi-device resilience**: Device constellation with quorum-based recovery ensures no single device failure causes identity loss

**Gap**: Formal security proofs not yet complete (empirical testing only). No formal adversarial testing by external red team.

---

### Article 16 — Obligations of Providers

**Requirement**: Providers must ensure conformity assessment, register systems, affix CE marking, prepare EU declaration of conformity, implement quality management, maintain documentation and logs, and take corrective action for non-conformity.

**Web4 Mechanism**: Comprehensive infrastructure layer that enables providers to meet these obligations.

| Provider Obligation | Web4 Support | How |
|---|---|---|
| Conformity assessment | T3/V3 tensor framework provides structured assessment methodology | Tensor scores serve as quantitative conformity evidence |
| System registration | LCT registry with birth certificates | Each AI system gets a verifiable LCT with full metadata |
| Quality management | Fractal chain audit trails + R6 action framework | Every action recorded, hash-chained, and attributable |
| Documentation maintenance | LCT lineage + ledger history | Complete evolution history maintained automatically |
| Corrective action | LCT status transitions + PolicyEntity updates | Non-conforming systems can be Slashed or Voided; policies updated |
| Incident logging | Ledger entries with witness attestation | Incidents recorded immutably with multiple attestations |

**Status**: Web4 provides the infrastructure for providers to satisfy these obligations. The tooling is available; providers need to adopt it.

---

### Article 17 — Quality Management System

**Requirement**: Providers must implement a QMS covering: regulatory compliance strategy, design procedures, post-market monitoring, incident reporting, data management, cybersecurity, and documented policies.

**Web4 Mechanism**: Society governance + PolicyEntity + ledger audit trails.

| QMS Element | Web4 Component | Implementation |
|---|---|---|
| Compliance strategy | PolicyEntity with `accountability_frame` | Policy rules encoded as living entities, evaluated per IRP |
| Design procedures | R6 framework (Request → Process → Result) | Structured workflow for all system modifications |
| Post-market monitoring | T3/V3 tensor continuous monitoring with drift detection | Real-time quality metrics across 6 root dimensions |
| Incident reporting | Ledger entries with severity classification | Hash-chained incident records with witness attestation |
| Data management | Fractal chain temporal hierarchy | Data classified by significance and retained appropriately |
| Cybersecurity | Hardware binding + 424 attack vectors | TPM2/TrustZone + empirical attack testing |
| Documented policies | PolicyEntity as code | Policies are living, versioned, auditable entities |

**Evidence**: Web4's governance-as-code approach (PolicyEntity evaluated through IRP) means quality management is not a separate process but an inherent property of the system architecture.

---

### Article 26 — Obligations of Deployers

**Requirement**: Deployers must use AI systems per instructions, assign human oversight, monitor operations, inform providers of incidents, conduct fundamental rights impact assessments, and keep logs.

**Web4 Mechanism**: R6 workflow + LCT delegation chains + society membership.

| Deployer Obligation | Web4 Support | How |
|---|---|---|
| Use per instructions | R6 Rules component encodes permitted uses | PolicyEntity rejects out-of-scope requests |
| Human oversight assignment | Role entity type with explicit delegation | Oversight role has its own LCT, bound to human entity |
| Operation monitoring | Ledger + tensor dashboards | Real-time monitoring via T3/V3 scores and ledger events |
| Incident notification | Witness protocol + ledger entries | Automatic incident recording with propagation to provider |
| Fundamental rights assessment | Trust tensor bias detection | Multidimensional tensor analysis reveals discriminatory patterns |
| Log retention | Fractal chain architecture | Automatic retention with configurable temporal layers |

**Status**: Deployer obligations are naturally satisfied by Web4's society membership model — deployers are society members with specific roles, subject to society law (policy).

---

### Articles 61-68 — Post-Market Monitoring and Enforcement

**Requirement**: Active post-market monitoring, serious incident reporting (15 days / immediately for life-threatening), authority access to documentation, corrective action procedures.

**Web4 Mechanism**: Continuous monitoring infrastructure.

| Enforcement Requirement | Web4 Component | Spec Reference |
|---|---|---|
| Post-market monitoring plan | T3/V3 continuous tensor monitoring | `simulations/coherence_trust_tensor.py` |
| Serious incident reporting | Ledger witness protocol with severity classification | `ledgers/spec/witness-protocol/` |
| Authority access to docs | LCT birth certificates + ledger exports | `web4-standard/schemas/lct.schema.json` |
| Corrective action | LCT status transitions (Void/Slash) + policy updates | `web4-core/src/lct.rs` |
| Withdrawal from market | LCT Void status = complete deactivation | `web4-standard/core-spec/entity-types.md` §2.3 |
| Compliance export | Ledger entries exportable to regulatory format | `ledgers/README.md` (compliance export listed as core function) |

**Evidence**:
- Fractal chain architecture ensures relevant records persist at the Root layer (permanent)
- Witness protocol provides cryptographic proof of when events occurred and who attested
- LCT Void/Slash status provides immediate, verifiable deactivation of non-conforming systems
- ATP/ADP discharge records provide complete resource consumption audit trail

---

## Summary: Coverage Assessment

| Article | Requirement | Web4 Coverage | Strength |
|---|---|---|---|
| **Art. 6** | Classification | Entity type taxonomy | Medium |
| **Art. 9** | Risk management | T3 tensors + ATP/ADP + PolicyEntity | **Strong** |
| **Art. 10** | Data governance | V3 tensors + witness diversity | Medium |
| **Art. 11** | Technical documentation | LCT birth certs + R6 records + whitepaper | **Strong** |
| **Art. 12** | Record-keeping | Fractal chain ledgers + R6 audit trails | **Strongest** |
| **Art. 13** | Transparency | LCT identity + tensor scores + R6 results | **Strong** |
| **Art. 14** | Human oversight | R6 approval + LCT lifecycle + PolicyEntity | **Strong** |
| **Art. 15** | Cybersecurity | Hardware binding + 424 attacks + sybil resistance | **Strong** |
| **Art. 16** | Provider obligations | Infrastructure layer for all obligations | **Strong** |
| **Art. 17** | Quality management | Society governance + PolicyEntity | Medium-Strong |
| **Art. 26** | Deployer obligations | R6 workflow + society membership | Medium-Strong |
| **Art. 61-68** | Post-market monitoring | Continuous monitoring + incident logging | Medium-Strong |

### Key Strengths

1. **Record-keeping (Art. 12)** is the strongest mapping — Web4 was designed for immutable audit trails
2. **Risk management (Art. 9)** benefits from real-time T3/V3 tensor monitoring, not just periodic assessments
3. **Cybersecurity (Art. 15)** is backed by the largest empirical attack corpus (424 vectors) of any trust infrastructure
4. **Human oversight (Art. 14)** is native through R6 approval workflows and LCT lifecycle management
5. **Transparency (Art. 13)** is inherent — hardware-anchored identities with verifiable attestation chains

### Key Gaps

1. **No Annex III category field** in LCT schema (Art. 6)
2. **No formal Art. 9 risk register template** (process exists, document template doesn't)
3. **No turnkey bias audit workflow** (Art. 10) — primitives exist but not packaged
4. **No "instructions for use" document generator** (Art. 13) — metadata exists but no export format
5. **Hardware binding not fully validated** (Art. 15) — TPM2 implementation exists, TCTI blocker partially resolved
6. **No formal security proofs** (Art. 15) — empirical testing only, no mathematical proofs of sybil resistance
7. **No external red team testing** (Art. 15) — all 424 attack simulations are internal/synthetic

---

## Implementation Roadmap

### Phase 1: Documentation (March 2026)
- [ ] Create Art. 9 risk register template
- [ ] Add `annex_iii_category` optional field to LCT schema
- [ ] Create Art. 13 "instructions for use" export tool
- [ ] Create Art. 10 bias audit workflow documentation

### Phase 2: Validation (April-May 2026)
- [ ] Complete TPM2 hardware binding validation on Legion
- [ ] Validate TrustZone binding on Thor/Sprout
- [ ] Run cross-machine trust verification (Legion L5 ↔ Thor L5)
- [ ] Begin external security review / red team engagement

### Phase 3: Compliance Packaging (June-July 2026)
- [ ] Package Web4 primitives as EU AI Act compliance toolkit
- [ ] Create conformity assessment methodology using T3/V3 tensors
- [ ] Build regulatory export format for ledger entries
- [ ] Prepare demo for EU AI Office / compliance consultancies

### Phase 4: Launch (August 2026)
- [ ] EU AI Act high-risk system deadline: infrastructure ready
- [ ] Compliance toolkit available for organizations
- [ ] Documentation package for regulators

---

## Demo Script (5 Minutes)

For compliance consultancies and regulatory bodies:

1. **Identity** (1 min): Create an AI agent with hardware-bound LCT. Show TPM2 attestation. "This agent's identity is physically bound to this machine — it cannot be copied or impersonated."

2. **Action Trail** (1 min): Agent performs task via R6 framework. Show structured Request → Result with ATP consumption. "Every action is recorded with who did it, why, what it cost, and what resulted."

3. **Risk Monitoring** (1 min): Show T3/V3 tensor dashboard. Inject anomalous behavior. Show tensor drift detection. "Real-time risk monitoring across 6 dimensions, not periodic checklists."

4. **Human Override** (1 min): Show PolicyEntity blocking an unauthorized action. Show LCT status transition to Dormant. "Humans can override, pause, or terminate any AI agent at any time."

5. **Audit Export** (1 min): Export ledger history as compliance report. Show hash chain verification. "Immutable, verifiable audit trail — tamper-evident by design."

---

## References

### Web4 Specifications
- `web4-standard/core-spec/LCT-linked-context-token.md` — LCT presence token spec
- `web4-standard/core-spec/entity-types.md` — 15 entity types
- `web4-standard/core-spec/atp-adp-cycle.md` — Energy/value cycle
- `web4-standard/core-spec/r6-implementation-guide.md` — Action framework
- `web4-standard/ontology/t3v3-ontology.ttl` — Trust/value tensor ontology
- `web4-standard/core-spec/mrh-tensors.md` — Relevancy horizon
- `web4-standard/core-spec/multi-device-lct-binding.md` — Device constellation
- `web4-standard/schemas/lct.schema.json` — LCT JSON schema

### Security and Threat Model
- `docs/reference/security/THREAT_MODEL.md` — Formal threat model v2.0
- `simulations/docs/ATTACK_CATALOG_SUMMARY.md` — 424 attack vector catalog

### Implementation
- `core/lct_binding/` — Hardware binding providers (TPM2, TrustZone, Software)
- `ledgers/` — Fractal chain ledger implementations
- `web4-core/src/lct.rs` — Rust LCT implementation
- `simulations/coherence_trust_tensor.py` — Trust tensor implementation

### EU AI Act
- [Regulation EU 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng) — Official text
- [EU AI Act Explorer](https://artificialintelligenceact.eu/) — Article-by-article analysis

### Strategy
- `docs/strategy/cross-model-strategic-review-2026-02.md` — Three-model convergence assessment

---

*This document is a living artifact. It will be updated as Web4 implementations mature and as EU guidance on the AI Act is published.*
