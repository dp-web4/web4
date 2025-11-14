# Threat Model: Business Email Compromise (BEC) vs Web4

This document frames the anonymized BEC case study as a threat model and examines how Web4 primitives change the attacker’s options and economics.

It is loosely informed by STRIDE-style thinking, but adapted to Web4’s context.

---

## 1. Assets

- **Funds in transit**  
  ~Five-figure ACH payment from Customer to Vendor.

- **Payment instructions**  
  Bank routing and account information associated with the Vendor.

- **Reputation and trust**  
  Trust between Vendor and Customer; Vendor’s perceived reliability.

- **Communication channels**  
  Email threads used for negotiation and confirmation.

- **Provenance / audit trail** (in Web4)  
  Canonical record of who authorized what, when, and under which context.

---

## 2. Adversary Goals

- Divert funds to an account controlled (directly or indirectly) by the attacker.
- Avoid timely detection.
- Obscure or complicate forensic reconstruction.
- Preserve ability to repeat the attack against other victims (i.e., maintain reusable infrastructure and identities).

---

## 3. Adversary Capabilities (Legacy Web)

- Phishing / credential harvesting.
- Exploiting password reuse.
- Installing malware on endpoint devices.
- Abusing email protocols (SMTP spoofing, weak DMARC).
- Registering lookalike domains.
- Creating and manipulating mailbox rules.
- Mass-automating newsletter signups (mail bombing) to flood inboxes.
- Rapidly moving funds once received.

The legacy environment grants the attacker a powerful advantage:  
**Control of what each party sees, with neither party having access to an authoritative shared ground truth.**

---

## 4. Threats (Legacy Web Perspective)

Roughly mapping to STRIDE-like categories:

- **Spoofing**  
  - Attacker forges emails that appear to come from the Vendor.
  - Attacker may also control a compromised Customer account and send from it.

- **Tampering**  
  - Attacker selectively deletes or modifies emails in the Customer’s mailbox.

- **Repudiation**  
  - Both Vendor and Customer can plausibly claim “I never sent/received that message.”
  - Logs are partial, fragmented, and easy to dispute.

- **Information Disclosure**  
  - Attacker reads all Customer–Vendor communication once the Customer account is compromised.

- **Denial of Service**  
  - Attacker mail-bombs Vendor to degrade their ability to process legitimate mail and react in time.

- **Elevation of Privilege**  
  - By compromising a mailbox, the attacker effectively gains the authority of that identity in email space, far beyond what they should have.

---

## 5. How Web4 Changes the Threat Landscape

### 5.1 Spoofing

- **Legacy:**  
  Email headers and display names are easily forged.

- **Web4:**  
  - Messages of consequence are accompanied by **MPEs (Message Provenance Envelopes)**, signed with the sender’s LCT.
  - Financial instructions require **FIPTs** bound to the Vendor’s LCT.
  - A spoofed email without valid MPE/FIPT is visibly and programmatically untrusted.

**Result:** Spoofing may still work at the pure-UX level (legacy inbox), but it cannot produce a valid Web4-level instruction.

---

### 5.2 Tampering

- **Legacy:**  
  Attacker deletes or alters messages in a compromised mailbox; each party has only a partial view.

- **Web4:**  
  - The canonical view of “who authorized what” is in the Web4 provenance graph, not in the mailbox.
  - Deleting emails does not alter FIPTs, MPEs, or WAL events already confirmed on Web4.

**Result:** Local tampering loses most of its strategic value.

---

### 5.3 Repudiation

- **Legacy:**  
  Parties can deny having sent or received specific messages; logs are inconclusive.

- **Web4:**  
  - All high-impact actions are signed with LCTs and recorded with MRH context.
  - Repudiation must now argue against a shared, cryptographically anchored history.

**Result:** Repudiation risk is materially reduced for Web4-mediated actions.

---

### 5.4 Information Disclosure

- **Legacy:**  
  Attacker reading an inbox gains almost complete visibility into transactions.

- **Web4:**  
  - Reading email gives information, but not control over canonical instructions.
  - Critical state transitions are executed via Web4, where attacker needs valid LCTs and trust to act.

**Result:** Confidentiality threats remain, but their leverage over control is reduced.

---

### 5.5 Denial of Service

- **Legacy:**  
  Mail bombing can severely delay human response.

- **Web4:**  
  - Critical paths are machine-verifiable and do not rely solely on humans catching specific emails.
  - Automated agents can monitor outstanding FIPTs and MRH anomalies independent of email volume.

**Result:** DoS at the UX layer still possible, but less effective at disrupting canonical state transitions.

---

### 5.6 Elevation of Privilege

- **Legacy:**  
  Compromising Customer’s mailbox effectively grants authority to act “as the Customer” in all email-mediated workflows.

- **Web4:**  
  - Authority to perform high-impact actions is gated by trust vectors, MRH, and LCTs.
  - Account compromise alone does not immediately confer the ability to generate valid Web4 actions, especially if:
    - Devices, agents, or intent workflows have additional checks.

**Result:** Privilege escalation from mailbox compromise is substantially constrained.

---

## 6. Residual Risks in a Web4 World

Web4 does not magically remove all risk. Some residual or shifted risks include:

- **Compromise of LCT issuance processes**  
  - If an attacker can fraudulently obtain or control an LCT, they can act with system-level authority.

- **Compromise of adjudication agents**  
  - If WAL adjudicators are captured or corrupted, trust vectors and constraints can be gamed.

- **Social engineering around overrides**  
  - Humans may still override system warnings, especially under time pressure or manipulation.

- **Implementation flaws**  
  - Bugs in client, agent, or chain code may mis-handle FIPTs, MPEs, MRH logic, or WAL events.

These risks need separate mitigation strategies, but they exist in a strictly more structured and auditable environment than the legacy email model.

---

## 7. High-Level Conclusion

The BEC attack described in the case study thrives on:

- Ambiguous identity,
- Mutable local history,
- Intent expressed as free-text,
- Lack of a shared canonical record.

Web4’s role is to provide a substrate where:

- Identity, context, and intent are natively bound,
- Provenance is tamper-resistant,
- Trust and consequences are systemic rather than ad hoc,
- And attackers pay a lasting price in their ability to operate if they try.

This threat model can serve as a baseline scenario to validate Web4 designs and to test autonomous agents’ ability to anticipate, detect, and neutralize similar attacks.
