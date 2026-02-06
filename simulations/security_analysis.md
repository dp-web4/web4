# Hardbound Security Analysis

**Date**: 2026-01-24
**Analyst**: Claude Opus 4.5 (autonomous research session)

## Overview

This document analyzes potential attack vectors against the Hardbound team/society implementation and proposes mitigations.

---

## 1. Identity System Attacks

### 1.1 Soft LCT Spoofing

**Vector**: Software-bound LCTs derive identity from machine_hash + user_hash. An attacker could:
- Clone machine identity on another device
- Spoof UID/hostname to generate matching hashes

**Current Protection**:
- 16-character truncated SHA256 hashes
- Stored in SQLite (local only)

**Risk Level**: MEDIUM

**Mitigation**:
- [ ] Hardware binding (TPM attestation) for admin roles
- [ ] Witness attestation from known-good entities
- [ ] Rate limiting on LCT creation
- [ ] Machine fingerprinting beyond hostname

### 1.2 Admin Impersonation

**Vector**: Admin role grants full control. If admin LCT is compromised:
- Attacker can approve any R6 request
- Can modify policy
- Can add/remove members
- Access to team secrets

**Current Protection**:
- Admin LCT stored in team record
- Audit trail of admin actions

**Risk Level**: HIGH

**Mitigation**:
- [ ] MANDATORY hardware binding for admin (TPM, FIDO2)
- [ ] Multi-sig for critical admin actions
- [ ] Admin rotation policy
- [ ] Alert on suspicious admin patterns
- [ ] Time-limited admin sessions

---

## 2. R6 Workflow Attacks

### 2.1 Self-Approval Bypass

**Vector**: Requester attempts to approve their own request.

**Current Protection**:
- PEER approval type rejects self-approval
- ADMIN approval requires admin LCT

**Risk Level**: LOW (currently protected)

**Verification**:
```python
# In r6.py approve_request():
if approver_lct == request.requester_lct:
    raise PermissionError("Cannot self-approve")
```

### 2.2 Replay Attack on R6

**Vector**: Attacker captures an approved R6 request and replays it.

**Current Protection**:
- R6 ID is hash-based (timestamp included)
- Request is removed from pending after execution

**Risk Level**: LOW

**Additional Mitigation**:
- [ ] Add nonce to R6 request
- [ ] Track executed R6 IDs in ledger
- [ ] Time-based validity window

### 2.3 Policy Manipulation

**Vector**: Attacker modifies policy to grant themselves permissions.

**Current Protection**:
- Policy stored in memory (not yet persisted)
- Policy version tracked

**Risk Level**: MEDIUM

**Mitigation**:
- [ ] Persist policy to ledger
- [ ] Require admin approval for policy changes
- [ ] Hash-chain policy versions
- [ ] Alert on policy modifications

---

## 3. ATP Economic Attacks

### 3.1 ATP Exhaustion

**Vector**: Attacker submits many requests to drain target's ATP.

**Current Protection**:
- ATP only consumed on execution (not request creation)
- Rejected requests don't consume ATP

**Risk Level**: LOW for target, MEDIUM for self-exhaustion

**Mitigation**:
- [ ] Rate limiting on request creation
- [ ] ATP reservation on request (return on rejection)
- [ ] Minimum ATP threshold for requests

### 3.2 ATP Inflation

**Vector**: Attacker finds way to increase ATP without legitimate work.

**Current Protection**:
- ATP budget is fixed at member creation
- No ATP earning mechanism yet

**Risk Level**: LOW (no earning mechanism)

**Mitigation**:
- [ ] When ATP earning is added, require verified outcomes
- [ ] ATP earning requires witness attestation
- [ ] Bounded ATP growth rates

---

## 4. Trust Manipulation Attacks

### 4.1 Trust Grinding

**Vector**: Attacker performs many low-risk successful actions to inflate trust, then performs single high-risk action.

**Current Protection**:
- Trust updates are small (0.05 for success)
- Different actions have different trust thresholds

**Risk Level**: MEDIUM

**Mitigation**:
- [ ] Decay trust over time (temporal coherence)
- [ ] Weight recent actions more heavily
- [ ] Different trust dimensions for different action types
- [ ] Require sustained trust for high-risk actions

### 4.2 Sybil Trust Attack

**Vector**: Attacker creates many identities to witness/approve each other.

**Current Protection**:
- Members must be added by existing members
- Approval tracked in audit

**Risk Level**: MEDIUM-HIGH

**Mitigation**:
- [ ] Hardware-bound LCTs make Sybil expensive
- [ ] Trust from witnessed approvals, not just count
- [ ] Graph analysis for Sybil detection
- [ ] Require diverse witness set

---

## 5. Audit Trail Attacks

### 5.1 Chain Tampering

**Vector**: Attacker modifies past audit records.

**Current Protection**:
- Hash-linked chain (each record contains prev_hash)
- Chain verification function exists

**Risk Level**: LOW (chain tampering is detectable)

**Note**: Tampering would break verification, so it's detectable but not preventable with current single-node storage.

**Mitigation**:
- [ ] Periodic chain verification
- [ ] Distributed witnesses for audit records
- [ ] Merkle root publication to external timestamping service

### 5.2 Selective Audit Deletion

**Vector**: Attacker with database access deletes specific audit records.

**Current Protection**:
- SQLite file permissions
- Chain would break if records deleted

**Risk Level**: MEDIUM (database access = game over anyway)

**Mitigation**:
- [ ] Append-only audit log file in addition to SQLite
- [ ] External replication of audit hashes
- [ ] Tamper-evident storage

---

## 6. Database Attacks

### 6.1 SQLite Corruption

**Vector**: Attacker corrupts SQLite database file.

**Current Protection**:
- WAL mode for integrity
- Standard SQLite protections

**Risk Level**: LOW-MEDIUM

**Mitigation**:
- [ ] Regular backups
- [ ] Checksum verification
- [ ] Graceful recovery procedures

### 6.2 Concurrent Access Race

**Vector**: Race condition during concurrent updates.

**Current Protection**:
- busy_timeout = 30s
- WAL mode allows concurrent reads

**Risk Level**: LOW

**Verification**: WAL mode handles this correctly.

---

## 7. Implementation Vulnerabilities

### 7.1 Hash Truncation Collision

**Vector**: Using 12-16 character truncated hashes creates birthday attack potential.

**Current Usage**:
- LCT IDs: 12 chars (48 bits) - 2^24 for collision
- Entry hashes: 32 chars (128 bits) - 2^64 for collision

**Risk Level**: LOW for current scale

**Mitigation**:
- [ ] Increase hash length for high-value identifiers
- [ ] Full SHA256 for cryptographic proofs

### 7.2 Timestamp Manipulation

**Vector**: Attacker manipulates system clock.

**Current Protection**:
- Timestamps from datetime.now(timezone.utc)
- No clock drift detection

**Risk Level**: MEDIUM

**Mitigation**:
- [ ] NTP verification
- [ ] Witness timestamps from multiple sources
- [ ] Heartbeat coherence detection

---

## Priority Recommendations

### Critical (implement immediately for production):
1. **Hardware-bound admin LCTs** (TPM/FIDO2)
2. **Multi-sig for critical operations** (admin changes, policy updates)
3. **External audit hash publication** (tamper evidence)

### High (implement before enterprise deployment):
4. **Rate limiting** on requests and LCT creation
5. **Trust decay** (temporal coherence)
6. **Policy persistence** in ledger
7. **Sybil detection** via graph analysis

### Medium (implement for robustness):
8. **Nonce in R6** for replay protection
9. **Incremental backup** of audit trail
10. **Clock drift detection**

### Low (nice to have):
11. Increase hash lengths
12. External NTP verification
13. Distributed witness network

---

## Next Steps

1. Implement hardware binding for admin (TPM integration exists in `tpm_binding.py`)
2. Add policy persistence to ledger
3. Implement trust decay
4. Add rate limiting infrastructure
5. Create Sybil detection module

---

*"Security is not a feature, it's a process. Every attack vector discovered is a vulnerability prevented."*
