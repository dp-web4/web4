# Attack Reconstruction and Failure Points (Legacy Web Context)

This document reconstructs the likely technical steps of the attack and highlights the structural weaknesses of the legacy web/email model that made it possible.

It is intended to serve as a bridge from real-world failure to Web4 design requirements.

---

## 1. Likely Attacker Workflow

### Step 1 — Initial Compromise of Customer Email

The attacker first needs persistent access to the Customer’s email account or device. Common paths:

- Password reuse across breached services.
- Phishing email capturing credentials.
- Malware on Customer’s device (keylogger, token theft).
- OAuth token theft via malicious app.
- MFA fatigue or SIM-based attack.

Once obtained, the attacker can:

- Read all Customer–Vendor email threads.
- See all invoices, bank details, and payment conversations.
- Configure forwarding and filtering rules.

---

### Step 2 — Monitoring for Payment Opportunities

The attacker scans email content for high-value targets, using keywords such as:

- “invoice”
- “ACH”
- “wire”
- “bank”
- “routing”
- “payment”
- “account number”

When they identify a live financial negotiation, they begin active preparation.

---

### Step 3 — Suppression of Vendor’s Legitimate Email

When the Vendor sends a legitimate email confirming bank details, the attacker ensures the Customer does not see it by:

- Creating mailbox rules that:
  - Delete the message,
  - Move it to an obscure folder,
  - Mark it as read and archive it.
- Or selectively deleting the message after reading it.

From the Customer’s perspective:
- The Vendor’s correct confirmation never appears,
- Or appears later, after the damage is done.

---

### Step 4 — Insertion of Fraudulent Reply

The attacker then crafts a fraudulent email that:

- Appears as a reply in the same thread.
- Uses the Vendor’s name in the “From” display or in the body.
- States that the original account is “under audit” or otherwise unavailable.
- Provides a new bank account and routing number under attacker control.

Technically, this can be done by:

- Sending from a similar-looking domain (e.g., vendor-co.com vs vendor.com).
- Using direct SMTP spoofing (if SPF/DMARC are weakly enforced downstream).
- Or sending from the Customer’s compromised account but editing headers or content to make it appear relayed.

Crucially:
- The message appears in the Customer’s email client as if it came from the Vendor (or within the Vendor’s thread), with enough visual similarity to bypass human scrutiny.

---

### Step 5 — Distraction and Signal Suppression Against Vendor

Around the time of the fraudulent communication, the attacker triggers a large-scale mail-bomb attack against the Vendor’s email address:

- Automated signup for hundreds or thousands of online newsletters and services.
- Vendor inbox fills with subscription confirmations and promotions.

Consequences:

- Critical messages are buried.
- Vendor’s attention is consumed by firefighting.
- Even if the Customer or bank tries to contact the Vendor, their messages may be missed or delayed.

---

### Step 6 — Execution of Fraudulent Payment

The Customer, believing they are following updated instructions from the Vendor, sends the ACH payment to the fraudulent account.

Once funds arrive:

- The attacker may:
  - Rapidly transfer funds to another bank (often offshore),
  - Distribute funds across mule accounts,
  - Convert to other assets.

Recovery window for the funds is limited and time-sensitive.

---

## 2. Failure Points in the Legacy Model

### Failure 1 — Email as a Trust Anchor

Email is treated as if:

- Sender identity = email address display.
- Thread continuity = authenticity.
- Appearance in the same conversation = provenance.

None of this is actually guaranteed at a system level.

---

### Failure 2 — Lack of Intent Binding

The system has no mechanism to express:

- “This message is an authoritative statement of bank details from the Vendor.”
- “Any changes to payment endpoints must be cryptographically bound to the same identity and intent.”

Financial instructions are free-floating text, not structured, auditable commitments.

---

### Failure 3 — No Cross-Context Consistency Check

There is no automatic mechanism to say:

- “This instruction conflicts with previous instructions.”
- “This new account is unrelated to historical payment endpoints.”
- “The language, timing, or trust characteristics of this message deviate from prior patterns.”

The system is essentially memoryless at an intent level.

---

### Failure 4 — Asymmetric Visibility

- The Attacker sees both sides of communication (via compromised Customer account).
- Vendor and Customer only see what is presented to them.
- There is no shared, tamper-resistant view of “what was actually said by whom.”

---

### Failure 5 — Weak or Absent Consequence Layer

Even if the attacker is identified:

- The identity used is often disposable.
- There is no global, persistent trust penalty that follows the attacker across systems.
- Enforcement requires slow, jurisdiction-limited, human legal processes.

---

## 3. Design Requirements Implied for Web4

From this case, Web4 needs to provide:

1. **Authentic, non-forgeable message provenance**  
   A way to say, and verify:  
   - “This message did in fact originate from this entity, in this context.”

2. **Intent binding for high-impact actions**  
   Payment instructions must be:
   - Explicit,
   - Structured,
   - Bound to sender identity and context,
   - Verifiable as consistent (or inconsistent) with previous intent.

3. **Context-aware anomaly detection (MRH)**  
   The system must automatically:
   - Notice deviations in payment endpoints,
   - Flag changes in tone/behavior,
   - Require higher assurance for out-of-pattern actions.

4. **Shared, tamper-resistant history**  
   A canonical view of:
   - Who said what,
   - Under what identity,
   - With what trust and context state.

5. **Systemic, portable consequences**  
   Malicious activity must:
   - Propagate to a durable trust penalty,
   - Limit the attacker’s future ability to operate,
   - Be referenceable across chains and systems.

Subsequent documents propose concrete Web4 primitives to satisfy these requirements.
