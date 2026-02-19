# EU AI Act Article 9 — Risk Management System Template

**Version**: 1.0
**Date**: February 19, 2026
**Regulation**: EU Regulation 2024/1689, Article 9
**Status**: Template for organizations deploying high-risk AI systems on Web4 infrastructure

---

## Overview

Article 9 of the EU AI Act requires providers of high-risk AI systems to establish, implement, document, and maintain a **risk management system** that is:

1. **Continuous** — not a one-time assessment but an ongoing, iterative process
2. **Lifecycle-wide** — covers design, development, deployment, and post-market phases
3. **Risk-identifying** — identifies and analyzes known and foreseeable risks
4. **Risk-mitigating** — adopts appropriate risk mitigation measures
5. **Post-market-aware** — evaluates data from post-market monitoring

This template provides a structured risk register that maps to Web4's infrastructure primitives, enabling native compliance through built-in risk monitoring and mitigation.

---

## 1. System Identification

| Field | Value |
|-------|-------|
| **AI System Name** | _[Your system name]_ |
| **System LCT ID** | `lct:web4:[type]:[hash]` |
| **Entity Type** | _[One of: AI, Human, Society, Organization, Role, Task, Resource, Device, Service, Oracle, Accumulator, Dictionary, Hybrid, Policy, Infrastructure]_ |
| **Annex III Category** | _[If applicable: biometrics, critical infrastructure, education, employment, essential services, law enforcement, migration, justice]_ |
| **Intended Purpose** | _[Clear description of what the system does]_ |
| **Provider** | _[Organization name and contact]_ |
| **Deployment Date** | _[Date or expected date]_ |
| **Last Risk Review** | _[Date]_ |
| **Next Scheduled Review** | _[Date — must be at least annually, recommended quarterly]_ |

### Web4 Infrastructure Layer

| Component | Status | Reference |
|-----------|--------|-----------|
| LCT Identity | _[Active / Dormant / Void]_ | _[LCT ID]_ |
| Hardware Binding Level | _[1-5]_ | _[TPM2 / TrustZone / Software]_ |
| T3 Trust Tensor | _[Current values]_ | _[Tensor snapshot]_ |
| V3 Value Tensor | _[Current values]_ | _[Tensor snapshot]_ |
| ATP/ADP Budget | _[Current allocation]_ | _[Budget reference]_ |
| R6 Audit Trail | _[Enabled / Disabled]_ | _[Ledger reference]_ |

---

## 2. Risk Register

### 2.1 Risk Identification Categories

The following categories structure the risk analysis per Art. 9(2):

| Category | Art. 9 Reference | Web4 Monitoring Mechanism |
|----------|-----------------|---------------------------|
| **A. Health and Safety** | Art. 9(2)(a) | T3 Temperament dimension (behavioral stability) |
| **B. Fundamental Rights** | Art. 9(2)(a) | V3 Validity dimension (output appropriateness) |
| **C. Foreseeable Misuse** | Art. 9(2)(b) | Attack simulation corpus (424 vectors) |
| **D. Data Quality** | Art. 9(2)(c) | V3 Veracity dimension (data truthfulness) |
| **E. Interaction Effects** | Art. 9(2)(d) | MRH context scoping (cross-system interactions) |
| **F. Cybersecurity** | Art. 9(8) | Hardware binding + sybil resistance + ledger integrity |

### 2.2 Risk Entry Template

For each identified risk, complete the following entry:

---

#### Risk [ID]: _[Risk Title]_

| Field | Value |
|-------|-------|
| **Risk ID** | R-[NNN] |
| **Category** | _[A-F from above]_ |
| **Description** | _[Clear description of the risk]_ |
| **Source** | _[How was this risk identified? Threat model, post-market data, incident report, etc.]_ |
| **Affected Population** | _[Who could be harmed?]_ |
| **Likelihood** | _[Very Low / Low / Medium / High / Very High]_ |
| **Severity** | _[Negligible / Low / Medium / High / Critical]_ |
| **Overall Risk Level** | _[Acceptable / Tolerable / Unacceptable]_ |

**Web4 Monitoring**:
| Metric | Threshold | Current Value | Alert Trigger |
|--------|-----------|---------------|---------------|
| _[T3/V3 dimension]_ | _[Min acceptable]_ | _[Current]_ | _[Condition]_ |

**Mitigation Measures**:
| Measure | Type | Status | Effectiveness |
|---------|------|--------|---------------|
| _[Description]_ | _[Prevention / Reduction / Control]_ | _[Implemented / Planned / N/A]_ | _[Verified / Untested]_ |

**Residual Risk** (after mitigation): _[Acceptable / Tolerable / Requires monitoring]_

**Review Schedule**: _[Quarterly / Monthly / Continuous via T3/V3 monitoring]_

---

### 2.3 Pre-Populated Risk Entries

The following risks are pre-populated from Web4's formal threat model (`docs/reference/security/THREAT_MODEL.md`). Organizations should review, customize, and supplement with system-specific risks.

---

#### Risk R-001: Identity Impersonation (Sybil Attack)

| Field | Value |
|-------|-------|
| **Risk ID** | R-001 |
| **Category** | F. Cybersecurity |
| **Description** | Attacker creates multiple fake identities to gain majority control of witness attestations, dilute honest platform influence, or create appearance of diversity |
| **Source** | Threat Model T1.1, Attack Tracks Track EA |
| **Affected Population** | All entities in the federation |
| **Likelihood** | Medium (deterred by ATP cost) |
| **Severity** | High (could compromise trust network integrity) |
| **Overall Risk Level** | Tolerable with monitoring |

**Web4 Monitoring**:
| Metric | Threshold | Current Value | Alert Trigger |
|--------|-----------|---------------|---------------|
| T3 Talent (competence) | > 0.3 | _[Monitor]_ | New entity with T3 < 0.3 requesting high-trust operations |
| Witness diversity | >= 3 unique societies | _[Monitor]_ | Attestations from < 3 societies |
| ATP stake per identity | >= 1,200 ATP | _[Monitor]_ | Bulk identity creation from single source |

**Mitigation Measures**:
| Measure | Type | Status | Effectiveness |
|---------|------|--------|---------------|
| ATP-aware identity stakes (1,200-75,000 ATP) | Prevention | Implemented | Empirically tested |
| Witness diversity requirement (>= 3 societies) | Detection | Implemented | Blocks simple cartels |
| Signed epidemic gossip for reputation propagation | Control | Implemented | 88k sig/sec throughput |

**Residual Risk**: Tolerable — well-funded attacker could still create identities, but at measurable economic cost.

---

#### Risk R-002: Private Key Compromise

| Field | Value |
|-------|-------|
| **Risk ID** | R-002 |
| **Category** | F. Cybersecurity |
| **Description** | Attacker obtains the entity's private signing key, enabling impersonation, ATP drainage, and reputation manipulation |
| **Source** | Threat Model T1.2 |
| **Affected Population** | Compromised entity and all interacting entities |
| **Likelihood** | Low (with hardware binding) / Medium (software-only) |
| **Severity** | Critical |
| **Overall Risk Level** | Acceptable (Level 5 hardware) / Tolerable (Level 4 software) |

**Web4 Monitoring**:
| Metric | Threshold | Current Value | Alert Trigger |
|--------|-----------|---------------|---------------|
| Hardware binding level | Level 5 | _[Monitor]_ | Binding level < 5 for high-trust operations |
| Aliveness verification | Continuity score = 1.0 | _[Monitor]_ | Continuity score drop |
| PCR values (boot integrity) | Stable across checks | _[Monitor]_ | Unexpected PCR drift |

**Mitigation Measures**:
| Measure | Type | Status | Effectiveness |
|---------|------|--------|---------------|
| TPM2 hardware binding (non-extractable keys) | Prevention | **Validated** on Legion (Feb 19, 2026) | Key physically cannot be extracted |
| Aliveness Verification Protocol (AVP) | Detection | Implemented | Proves current hardware access |
| Multi-device LCT constellation | Reduction | Designed | Quorum-based recovery for device loss |

**Residual Risk**: Acceptable with hardware binding (Level 5). The private key exists only in the TPM chip.

---

#### Risk R-003: Reputation Manipulation

| Field | Value |
|-------|-------|
| **Risk ID** | R-003 |
| **Category** | A. Health and Safety / B. Fundamental Rights |
| **Description** | Entity artificially inflates its own trust scores or deflates competitors' scores to gain unmerited influence over decision-making |
| **Source** | Threat Model T3.1/T3.2, Attack Track EB |
| **Affected Population** | End users who rely on trust-based decisions |
| **Likelihood** | Medium |
| **Severity** | High (affects decision quality for downstream users) |
| **Overall Risk Level** | Tolerable with monitoring |

**Web4 Monitoring**:
| Metric | Threshold | Current Value | Alert Trigger |
|--------|-----------|---------------|---------------|
| T3 tensor trajectory | Smooth growth curve | _[Monitor]_ | Sudden score jumps (> 0.2 in single period) |
| V3 Veracity dimension | > 0.5 | _[Monitor]_ | Veracity below threshold |
| Witness attestation patterns | Diverse sources | _[Monitor]_ | All attestations from same 1-2 witnesses |

**Mitigation Measures**:
| Measure | Type | Status | Effectiveness |
|---------|------|--------|---------------|
| T3/V3 multi-dimensional tensors (resist single-axis gaming) | Prevention | Implemented | Tested in 84 attack tracks |
| Challenge-response protocol | Detection | Implemented | 561 lines, accountability enforcement |
| Reputation washing detection | Detection | Implemented | Track EB attack vectors |

**Residual Risk**: Tolerable — multi-dimensional tensor scoring makes manipulation detectable but not impossible.

---

#### Risk R-004: Resource Exhaustion (ATP Drain)

| Field | Value |
|-------|-------|
| **Risk ID** | R-004 |
| **Category** | C. Foreseeable Misuse |
| **Description** | Attacker floods the system with expensive operations to deplete ATP budget, forcing degraded or shutdown state |
| **Source** | Threat Model T2.1 |
| **Affected Population** | System availability for legitimate users |
| **Likelihood** | Medium |
| **Severity** | Medium (degraded but not dangerous) |
| **Overall Risk Level** | Tolerable |

**Web4 Monitoring**:
| Metric | Threshold | Current Value | Alert Trigger |
|--------|-----------|---------------|---------------|
| ATP balance | > 10% of allocation | _[Monitor]_ | Balance below 10% triggers CRISIS metabolic state |
| ATP burn rate | Normal operating range | _[Monitor]_ | Burn rate > 3x normal |
| Request frequency | Within rate limits | _[Monitor]_ | Sustained maximum rate requests |

**Mitigation Measures**:
| Measure | Type | Status | Effectiveness |
|---------|------|--------|---------------|
| Rate limiting on task delegation | Prevention | Implemented | Prevents unlimited flooding |
| Metabolic state transitions (CRISIS mode) | Control | Implemented | Automatic degraded-mode operation |
| ATP bounty requirements for challenges | Prevention | Implemented | Economic cost to attacker |

**Residual Risk**: Tolerable — system degrades gracefully under attack, never fails catastrophically.

---

#### Risk R-005: Discriminatory Output (Bias)

| Field | Value |
|-------|-------|
| **Risk ID** | R-005 |
| **Category** | B. Fundamental Rights |
| **Description** | AI system produces outputs that discriminate based on protected characteristics (race, gender, age, disability, etc.) |
| **Source** | Art. 10 requirements, general AI bias literature |
| **Affected Population** | Individuals in protected groups |
| **Likelihood** | Medium (depends on training data) |
| **Severity** | High (fundamental rights impact) |
| **Overall Risk Level** | Requires active monitoring |

**Web4 Monitoring**:
| Metric | Threshold | Current Value | Alert Trigger |
|--------|-----------|---------------|---------------|
| V3 Validity dimension | > 0.6 across demographics | _[Monitor]_ | Validity variance > 0.2 across groups |
| T3 Training dimension | > 0.5 | _[Monitor]_ | Low training quality score |
| Witness diversity in attestations | Representative coverage | _[Monitor]_ | Homogeneous witness pool |

**Mitigation Measures**:
| Measure | Type | Status | Effectiveness |
|---------|------|--------|---------------|
| Multi-dimensional tensor analysis (reveals narrow training) | Detection | Implemented | Detects bias signatures |
| Witness diversity requirements (>= 3 societies) | Prevention | Implemented | Reduces monoculture bias |
| MRH context scoping (filters irrelevant attributes) | Reduction | Implemented | Prevents protected attributes from dominating |

**Residual Risk**: Requires monitoring — Web4 provides detection primitives but bias elimination requires system-specific measures.

---

#### Risk R-006: Human Oversight Failure

| Field | Value |
|-------|-------|
| **Risk ID** | R-006 |
| **Category** | A. Health and Safety |
| **Description** | AI system operates without effective human oversight, making consequential decisions autonomously without ability to intervene |
| **Source** | Art. 14 requirements |
| **Affected Population** | All affected individuals |
| **Likelihood** | Low (with R6 Tier 2) |
| **Severity** | Critical |
| **Overall Risk Level** | Acceptable with R6 authorization |

**Web4 Monitoring**:
| Metric | Threshold | Current Value | Alert Trigger |
|--------|-----------|---------------|---------------|
| R6 approval rate | Admin approval for critical actions | _[Monitor]_ | Action executed without required approval |
| LCT status | Active | _[Monitor]_ | Autonomous action during Dormant/Void state |
| PolicyEntity evaluation | Policy check on every action | _[Monitor]_ | Policy bypass detected |

**Mitigation Measures**:
| Measure | Type | Status | Effectiveness |
|---------|------|--------|---------------|
| R6 Tier 2 authorization workflow | Prevention | Implemented | Admin must approve actions |
| LCT lifecycle management (Dormant/Void/Slash) | Control | Implemented | Immediate entity deactivation |
| PolicyEntity as IRP-backed evaluation | Control | Implemented | Policy rules are living, updatable entities |

**Residual Risk**: Acceptable — R6 framework provides explicit approval gates, and LCT lifecycle management provides immediate shutdown capability.

---

## 3. Risk Assessment Matrix

| | Negligible | Low | Medium | High | Critical |
|---|---|---|---|---|---|
| **Very High** | Tolerable | Tolerable | Unacceptable | Unacceptable | Unacceptable |
| **High** | Acceptable | Tolerable | Tolerable | Unacceptable | Unacceptable |
| **Medium** | Acceptable | Acceptable | Tolerable | Tolerable | Unacceptable |
| **Low** | Acceptable | Acceptable | Acceptable | Tolerable | Tolerable |
| **Very Low** | Acceptable | Acceptable | Acceptable | Acceptable | Tolerable |

**Actions by risk level:**
- **Acceptable**: Document and monitor. Review annually.
- **Tolerable**: Implement monitoring and mitigation. Review quarterly.
- **Unacceptable**: Immediate action required. System may not deploy until risk is reduced.

---

## 4. Continuous Monitoring Plan

### 4.1 Automated Monitoring (via Web4 Infrastructure)

| Monitor | Frequency | Mechanism | Alert Method |
|---------|-----------|-----------|-------------|
| T3/V3 tensor drift | Continuous | `update_from_outcome()` after each action | Threshold alerts |
| ATP balance | Continuous | ATP/ADP cycle tracking | Balance below 10% |
| Ledger integrity | Per-block | Hash chain verification | Broken chain detection |
| PCR values (boot integrity) | On aliveness check | TPM attestation quote | PCR value change |
| R6 audit trail | Per-action | Structured before/after hooks | Policy violation |
| Witness diversity | Per-attestation | Society count verification | < 3 unique witnesses |

### 4.2 Manual Review Schedule

| Review | Frequency | Responsible | Scope |
|--------|-----------|-------------|-------|
| Risk register update | Quarterly | Provider risk manager | All risks, add new ones |
| Tensor analysis report | Monthly | System operator | T3/V3 trends, anomalies |
| Incident review | Per-incident + monthly summary | Provider + deployer | Root cause, mitigation |
| Penetration testing | Annually | External security team | Full attack surface |
| Compliance audit | Annually (pre-Aug 2) | Compliance officer | Full Art. 9 requirements |

### 4.3 Post-Market Monitoring Integration (Art. 61)

Web4 infrastructure supports continuous post-market monitoring:

| Requirement | Web4 Implementation |
|-------------|---------------------|
| Active data collection | Ledger entries automatically collect operational data |
| Performance evaluation | T3/V3 tensor scores provide quantitative performance metrics |
| Systematic complaints review | R6 framework captures all interactions with structured metadata |
| Incident detection | Trust tensor entropy increase triggers automated alerts |
| Corrective action tracking | LCT status transitions + policy updates logged immutably |

---

## 5. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-19 | Initial template | Created with 6 pre-populated risks |
| _[Next]_ | _[Date]_ | _[Author]_ | _[Customize for specific system]_ |

---

## How to Use This Template

1. **Copy this file** for each high-risk AI system you deploy
2. **Fill in Section 1** with system-specific information
3. **Review the pre-populated risks** (R-001 through R-006) and customize
4. **Add system-specific risks** using the risk entry template in Section 2.2
5. **Assess each risk** using the matrix in Section 3
6. **Enable monitoring** per Section 4
7. **Review quarterly** at minimum, update as risks evolve
8. **Retain this document** for regulatory inspection (Art. 11 technical documentation)

---

## References

- [EU AI Act, Article 9](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng) — Risk Management System
- `docs/reference/security/THREAT_MODEL.md` — Web4 Formal Threat Model v2.0
- `docs/strategy/eu-ai-act-compliance-mapping.md` — Full article-by-article mapping
- `simulations/docs/ATTACK_CATALOG_SUMMARY.md` — 424 attack vector catalog
- `core/lct_binding/tpm2_provider.py` — TPM2 hardware binding (VALIDATED)
