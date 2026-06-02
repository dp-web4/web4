# 🔐 CRYPTO_ANALYSIS.md
## Web4 Security Reference — Edge Crypto Analysis Layer

---

# 1. Overview

The Edge Crypto Layer secures all data flowing through the Web4 runtime system:

- UI execution layer
- Plugins and modules
- State kernel
- HMR updates
- Remote module loading
- Network communication

It enforces **zero-trust cryptographic execution at every layer**.

---

# 2. Threat Model

The system assumes all external inputs are hostile.

## Covered threats:

- Malicious plugin execution
- SSRF attacks via runtime fetch
- Prompt injection via remote modules
- State leakage via logs or UI
- Hot Module Replacement (HMR) injection
- Path traversal in filesystem routing

---

# 3. Cryptographic Core

## 3.1 Algorithms

- AEAD Encryption: AES-256-GCM / ChaCha20-Poly1305  
- Key Exchange: X25519 (ECDH)  
- Signatures: Ed25519  
- KDF: HKDF-SHA256 / Argon2  

---

## 3.2 Secure Randomness

All cryptographic operations MUST use OS-level entropy:

- `crypto.getRandomValues()`
- No deterministic fallback allowed

---

# 4. Data Protection Layers

## Layer 1 — Transport Security

- TLS 1.2+ required
- Certificate validation enforced
- No insecure overrides allowed in production

---

## Layer 2 — Payload Encryption

All sensitive payloads are encrypted before transmission:
Rules:
- Unique nonce per message
- Never reuse key/nonce pairs
- Always verify authentication tag

---

## Layer 3 — State Encryption

Client state is encrypted before storage:
Keys:
- Derived per-session via HKDF
- Never exposed to plugins

---

## Layer 4 — Plugin Isolation

Plugins operate under strict trust boundaries:

### Trusted plugins:
- read/write state
- UI rendering
- internal APIs

### Untrusted plugins:
- read-only state
- no network access
- sandboxed execution only

---

# 5. SSRF Protection

## Blocked IP ranges:

- 127.0.0.0/8
- 169.254.0.0/16
- 10.0.0.0/8
- 172.16.0.0/12
- 192.168.0.0/16

## Rules:

- DNS resolution before request execution
- IP validation before network call
- Only allowlisted domains for plugins

---

# 6. HMR Security Model

Hot Module Reload is treated as a high-risk vector.

## Secure flow:
Rules:
- Unique nonce per message
- Never reuse key/nonce pairs
- Always verify authentication tag

---

## Layer 3 — State Encryption

Client state is encrypted before storage:

Keys:
- Derived per-session via HKDF
- Never exposed to plugins

---

## Layer 4 — Plugin Isolation

Plugins operate under strict trust boundaries:

### Trusted plugins:
- read/write state
- UI rendering
- internal APIs

### Untrusted plugins:
- read-only state
- no network access
- sandboxed execution only

---

# 5. SSRF Protection

## Blocked IP ranges:

- 127.0.0.0/8
- 169.254.0.0/16
- 10.0.0.0/8
- 172.16.0.0/12
- 192.168.0.0/16

## Rules:

- DNS resolution before request execution
- IP validation before network call
- Only allowlisted domains for plugins

---

# 6. HMR Security Model

Hot Module Reload is treated as a high-risk vector.

## Secure flow:

## Requirements:

- Signed update payloads
- Version hash validation
- Rollback support

## Failure response:

- Reject patch
- Restore previous state
- Log security event

---

# 7. Key Management

## Key Types:

- session_key → runtime encryption
- state_key → persistent storage encryption
- plugin_key → module verification

## Rules:

- Never store keys in plaintext
- Rotate per session or TTL window
- Private keys never exposed to plugins

---

# 8. Signature Verification

All external modules MUST be verified:

If verification fails:
- Block execution
- Discard module
- Log security event

---

# 9. Secure Execution Sandbox

All dynamic code runs inside a sandbox:

## Restrictions:

- No direct DOM access
- No unrestricted network access
- No filesystem access
- No crypto key access

## Allowed API surface:

- state
- navigate
- emitEvent
- secureFetch
- readOnlyStorage

---

# 10. Logging & Redaction

Security logging system:

- Secrets automatically redacted
- Keys hashed before logging
- Sensitive stack traces sanitized

---

# 11. Forward Security Model

- Compromised session keys cannot decrypt past sessions
- Keys rotate per runtime lifecycle
- Plugins cannot persist cryptographic access

---

# 12. Production Hardening

Recommended safeguards:

- Enable signed HMR only
- Enforce strict CSP headers
- Disable unsigned remote modules
- Use hardware-backed key storage where available

---

# 13. Core Principle

> Everything is untrusted until cryptographically verified.

---

# 14. Summary

This system ensures:

- 🔐 Everything is encrypted
- 🧾 Everything is signed
- 🧪 Everything is sandboxed
- 🌐 Everything remote is hostile by default

---
