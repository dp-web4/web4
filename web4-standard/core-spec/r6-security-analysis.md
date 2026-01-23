# R6 Security Analysis

## Attack Surface Overview

The R6 framework provides audit trails and (in Tier 2) authorization. This document analyzes attack vectors and mitigations.

## Tier 1: Observational (web4-governance plugin)

### Attack Vectors

#### A1: Session File Tampering
**Vector**: Attacker modifies `~/.web4/sessions/*.json` directly
**Impact**: Falsified session state, broken chain
**Current mitigation**: None (local files)
**Recommendation**: Add integrity verification on load, signature from session token

#### A2: Audit Log Tampering
**Vector**: Attacker modifies/deletes `~/.web4/audit/*.jsonl`
**Impact**: Lost audit trail, modified history
**Current mitigation**: Hash chain (tampering detectable but not preventable)
**Recommendation**:
- Remote backup to trusted service
- Periodic snapshots with signatures
- Chain anchoring to external ledger

#### A3: Session Token Forgery
**Vector**: Attacker creates fake session with arbitrary token_id
**Impact**: Actions attributed to fake identity
**Current mitigation**: None (software tokens are just hashes)
**Recommendation**:
- Tier 2 adds hardware binding via TPM
- For Tier 1: accept limited trust, document binding type clearly

#### A4: Hash Collision Attack
**Vector**: Attacker crafts content with same hash as existing record
**Impact**: Indistinguishable forgery
**Current mitigation**: SHA-256 (collision-resistant)
**Risk level**: Negligible with SHA-256, 16-byte truncation is still 128 bits

#### A5: Pre-image Bypass
**Vector**: Create R6 request after action (bypass pre_tool_use)
**Impact**: Post-hoc fabricated intent
**Current mitigation**: None
**Recommendation**:
- Add timestamp verification
- Check pending_r6 consistency
- In Tier 2: require signed request before execution

#### A6: Chain Gap Injection
**Vector**: Skip recording some actions while recording others
**Impact**: Selective audit trail (hide malicious actions)
**Current mitigation**: action_index should be monotonic
**Recommendation**: Add gap detection in verification

### Threat Model for Tier 1

| Attacker | Capability | Mitigated? |
|----------|------------|------------|
| Remote attacker | Cannot access local files | Yes |
| Local user (same account) | Full file access | **No** |
| Malicious plugin | Can intercept hooks | **No** |
| Compromised Claude | Can bypass hooks | **No** |

**Conclusion**: Tier 1 provides audit for **honest actors**, not adversarial environments. Trust the actor, verify the trail.

## Tier 2: Authorization (hardbound-core)

### Attack Vectors

#### B1: Admin Key Theft
**Vector**: Attacker steals admin_lct private key
**Impact**: Full authorization bypass
**Current mitigation**: Hardware binding (TPM)
**Recommendation**: Key never leaves TPM, attestation on demand

#### B2: Role Escalation
**Vector**: Developer requests action beyond role permission
**Impact**: Unauthorized actions
**Current mitigation**: check_permission() in R6Processor
**Recommendation**: Policy engine integration, multi-approver for sensitive actions

#### B3: ATP Drain
**Vector**: Flood system with expensive requests
**Impact**: Resource exhaustion
**Current mitigation**: ATP budget tracking
**Recommendation**: Rate limiting, minimum trust threshold for large requests

#### B4: Approval Racing
**Vector**: Submit many requests, approve in bulk
**Impact**: Bypass individual review
**Current mitigation**: None explicit
**Recommendation**: Add approval cooldown, batch size limits

#### B5: Trust Inflation
**Vector**: Execute many cheap successful actions to inflate trust
**Impact**: Gain auto-approval for expensive actions
**Current mitigation**: Trust delta is small
**Recommendation**:
- Diminishing returns on repeated action types
- Suspicious pattern detection
- Time decay on trust

#### B6: Replay Attack
**Vector**: Replay a previously approved R6 request
**Impact**: Execute same action multiple times
**Current mitigation**: Unique request IDs (uuid)
**Recommendation**: Add nonce, check ID uniqueness in processor

### Hardware Binding Security

TPM integration provides:
1. **Key Protection**: Private keys generated in TPM, never exported
2. **Attestation**: Can prove key is TPM-bound on demand
3. **Death Awareness**: Key destruction means identity death

Limitations:
- TPM access requires root/admin on most systems
- TPM firmware vulnerabilities exist (rare)
- Side-channel attacks possible (expensive)

## Cross-Tier Concerns

### C1: Tier Confusion
**Vector**: Present Tier 1 (software-bound) audit as Tier 2 (hardware-bound)
**Impact**: Overstate trustworthiness
**Mitigation**: Always expose `binding` field, relying party checks

### C2: Import Poisoning
**Vector**: Import malicious Tier 1 records into Tier 2 system
**Impact**: Polluted audit trail
**Mitigation**: Validate chain integrity, verify source trust

### C3: Clock Manipulation
**Vector**: Adjust system clock to fabricate timestamps
**Impact**: Timeline falsification
**Mitigation**:
- External timestamp service
- Chain analysis (detect time anomalies)
- TPM-based secure clock (where available)

## Verification Procedures

### Chain Integrity Check
```python
def verify_chain(records):
    prev_hash = "genesis"
    for record in records:
        # Check chain link
        if record["provenance"]["prev_record_hash"] != prev_hash:
            return False, f"Chain break at {record['record_id']}"
        # Verify record hash
        expected = hash_content({k:v for k,v in record.items() if k != 'record_hash'})
        if record["record_hash"] != expected:
            return False, f"Hash mismatch at {record['record_id']}"
        prev_hash = record["record_hash"]
    return True, "Chain valid"
```

### Gap Detection
```python
def detect_gaps(records, session):
    indices = [r["provenance"]["action_index"] for r in records]
    for i, idx in enumerate(indices):
        if i > 0 and idx != indices[i-1] + 1:
            return False, f"Gap detected: {indices[i-1]} → {idx}"
    return True, "No gaps"
```

## Recommendations Summary

### For Tier 1 (Adoption)
1. Document trust limitations clearly
2. Add chain verification command
3. Consider optional remote backup
4. Warn users about local file trust

### For Tier 2 (Enterprise)
1. Integrate with policy engine (done)
2. Add multi-approver workflows
3. Implement trust pattern analysis
4. Add audit anchoring to external ledger
5. Rate limiting on request submission

### For Both
1. Add timestamp verification service
2. Implement gap detection
3. Create forensic tools for chain analysis
4. Document threat model for operators

## References

- OWASP Logging Cheat Sheet
- NIST SP 800-92 (Log Management)
- TPM 2.0 Security Best Practices
