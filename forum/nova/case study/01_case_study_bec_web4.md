# Case Study: Payment Diversion via Business Email Compromise

## Abstract

This case study describes a real-world payment diversion attack using Business Email Compromise (BEC). It focuses on how an attacker successfully diverted a five-figure ACH payment by hijacking an existing email thread, suppressing legitimate messages, and inserting fraudulent payment instructions.

The incident is then used as a reference scenario for designing Web4-native security mechanisms.

> All names and identifiable details have been anonymized.

---

## Actors

- **Vendor**  
  A small engineering company providing specialized hardware and consulting services.

- **Customer**  
  A business client purchasing hardware and engineering services from the Vendor.

- **Attacker**  
  An unknown third party who compromises the Customer’s email account and manipulates the payment instructions.

- **Banking System**  
  Traditional ACH rails, not Web4-native.

---

## High-Level Summary

1. Customer requests bank details for a ~\$70,000 ACH payment.
2. Vendor confirms correct routing and account info via email.
3. Vendor’s confirmation never effectively reaches Customer.
4. Attacker inserts a forged reply into the same thread, claiming the original account is “under audit” and providing a new destination account.
5. Customer sends the payment to the attacker’s account.
6. Around the same time, Vendor’s email address is mail-bombed (newsletter signups), making it difficult for Vendor to see or respond to anything meaningful.
7. The loss is only discovered after the funds have already been sent.

---

## Detailed Timeline

### T0 — Payment Coordination

- Customer emails Vendor asking to confirm bank routing and account number for an upcoming ACH payment of approximately \$70,000.
- Vendor replies from their normal business email address, confirming that the provided bank details are correct.

At this point, communication appears normal from both sides.

---

### T1 — “Payment Sent” but Not Received

- Customer indicates that the payment has been sent via ACH.
- Vendor checks their account the following day:
  - **No incoming payment** is visible.
- Vendor expects a typical ACH delay but is alert that something may be off.

---

### T2 — Mail Bombing of Vendor

- Vendor’s email inbox is suddenly flooded with hundreds of subscription/confirmation emails per minute.
- These appear to come from automated sign-up forms, suggesting someone has used the Vendor’s email address to register for numerous online services.
- Vendor must enable defensive measures (e.g., a “catch-all” filter / box-catcher) just to keep the inbox usable.

Practical effect:
- Important messages (including anything related to the payment) are much harder to spot.
- Vendor’s attention is consumed by damage control and inbox cleanup.

---

### T3 — Discovery of the Fraudulent Email

- Customer sends Vendor a text message asking for clarification.
- The Customer includes a screenshot of an email that:
  - Appears visually consistent with the Vendor (same name, similar display address).
  - Is a **reply in the existing email thread**.
  - States that the original bank account is “under audit.”
  - Provides a **different** bank account and routing number and instructs the Customer to send the payment there instead.

- Customer has already followed these instructions and sent the funds to the new (fraudulent) account.

Vendor confirms:
- The Vendor **never sent** this “under audit” email.
- The false message does **not** appear in the Vendor’s Sent folder or account history.

---

## Observed Technical Characteristics

1. **Thread Hijacking**
   - The fraudulent email is a “reply” within the same conversation thread between Vendor and Customer.
   - It aligns with the subject, quoting style, and apparent context of the original conversation.
   - This gives it a high level of credibility from the Customer’s point of view.

2. **Suppression of Legitimate Content**
   - Vendor’s legitimate confirmation email either:
     - never reached the Customer’s inbox, or
     - was automatically filtered/moved/deleted before the Customer saw it.
   - The Customer therefore saw **only** the attacker’s modified instructions regarding the bank account.

3. **Mail Bombing as Distraction**
   - The mail-bombing of the Vendor’s address happens near the time of the fraudulent payment.
   - This is consistent with an attempt to:
     - Distract the Vendor.
     - Suppress any further communication.
     - Make it harder for Vendor to react quickly or spot anomalies.

4. **No Evidence of Vendor Account Compromise**
   - The fraudulent email:
     - Did not originate from the Vendor’s mail server.
     - Does not appear in Vendor’s mailbox.
   - Strong indication: **Vendor email was not compromised**.

---

## Likely Root Cause

The most probable scenario is:

- The **Customer’s email account** (or device) was compromised prior to or during the payment coordination.
- The Attacker had the ability to:
  - Monitor the Customer’s inbox and sent mail.
  - Create mail rules to hide or delete messages from the Vendor.
  - Send messages as the Customer or inject messages that appear to be from the Vendor, using the Customer’s compromised environment as the insertion point.
- The fraudulent “under audit” message was:
  - Crafted by the Attacker.
  - Injected into the thread from the Customer side.
  - Presented to the Customer as if it were a legitimate response from the Vendor.

---

## Human-Level Failure Modes

- **Over-reliance on email as an authoritative channel**  
  The Customer trusted an email that appeared to come from the Vendor, with no secondary verification.

- **No out-of-band confirmation**  
  No phone or secure-channel confirmation was used before changing payment details.

- **Lack of provenance / intent binding**  
  There was no cryptographic or contextual binding between:
  - The Vendor’s identity,
  - The specific payment instructions,
  - And the Customer’s confirmation of those instructions.

---

## Lessons Learned (Pre-Web4)

1. Email alone is **not** a sufficient channel for confirming high-value financial instructions.
2. Even if both parties are acting in good faith, a third party can:
   - Silence one side,
   - Impersonate them,
   - And successfully insert malicious instructions.
3. Traditional email security (SPF/DKIM/DMARC, TLS, etc.) does not solve the fundamental problem of **contextual, intent-level authenticity**.

---

## Use as Web4 Reference Scenario

This case is an excellent reference for Web4 because it demonstrates:

- Identity ambiguity
- Intent ambiguity
- Context manipulation
- Lack of persistent, auditable provenance

Subsequent documents in this series propose Web4-native constructs to:
- Prevent such attacks,
- Detect anomalies,
- And enforce systemic consequences for malicious actors.
