# Web4 Security Case Study Package

This folder contains a small, self-contained package that uses a real-world Business Email Compromise (BEC) incident as a design driver for Web4 security primitives.

All actors and specifics have been anonymized.

---

## Contents

1. `01_case_study_bec_web4.md`  
   Narrative case study of a payment diversion attack via BEC.

2. `02_attack_reconstruction_and_failure_points.md`  
   Technical reconstruction of the attack and identification of structural weaknesses in the legacy web/email model.

3. `03_web4_mapping_and_mitigation.md`  
   Mapping from observed failure modes to Web4 primitives (LCT, MRH, provenance, trust vectors, intent validation).

4. `04_web4_specs_fipt_mpe_wal.md`  
   Draft specifications for three Web4 constructs:
   - FIPT (Financial Instruction Provenance Token),
   - MPE (Message Provenance Envelope),
   - WAL (Web4 Accountability Layer).

5. `threat_model_bec_web4.md`  
   Threat-model style view of the case, including attacker goals, capabilities, and how Web4 alters the threat landscape.

---

## Intended Use

This package is designed to be ingested by autonomous or semi-autonomous agents evolving Web4 architectures. It provides:

- A concrete, emotionally and economically grounded failure scenario.
- A clear mapping from failure to requirements.
- Initial concrete specs that can be refactored, extended, and formalized.

It is also suitable for human readers as a teaching and design artifact.

---

## How to Extend

Suggested directions for further development:

- Add JSON or JSON-LD schemas derived from the FIPT, MPE, and WAL definitions.
- Integrate with broader Web4 governance and consensus documents.
- Add simulation scenarios (e.g., red-team/blue-team runs) to validate that the proposed primitives actually prevent or mitigate similar attacks.
- Connect to higher-level constructs like T3/V3, LCT hierarchies, and Web4-native economic incentives.

---

## High-Level Insight

The core insight illustrated here is that:

> The problem is not just that email can be spoofed;  
> it is that we lack a substrate where identity, context, and intent are natively bound and auditable.

Web4’s role is to provide that substrate.
