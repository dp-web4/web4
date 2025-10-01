# RFC: Law Oracle Procedure Extensions

**RFC ID**: RFC-LAW-PROC-001
**Title**: Law Oracle Procedure Definition Extensions
**Author**: Society 4
**Status**: Draft
**Target**: web4 v1.1.0 (SAL Specification)
**Category**: Core Protocol Enhancement
**Created**: 2025-09-30
**Updated**: 2025-09-30

## Abstract

The minimal web4 SAL (Society-Authority-Law) specification defines procedures as enforcement mechanisms for law norms, but provides limited structure for expressing complex procedural logic. Society 4's Law Oracle implementation identified critical gaps when modeling real-world governance procedures requiring time-based triggers, multi-threshold decision logic, and failure handling.

This RFC proposes standardized extensions to the Procedure schema enabling:
1. **Time-based triggers** - Scheduled and periodic procedure execution
2. **Multi-threshold logic** - Complex decision trees based on computed values
3. **Failure actions** - Explicit handling for procedure violations
4. **Immediate execution flags** - Emergency bypass of normal consensus
5. **Action mappings** - Threshold-to-action bindings for dynamic responses

## Motivation

### Current Limitation

The web4 SAL specification defines procedures minimally:

```json
{
  "id": "PROC-WIT-3",
  "name": "Minimum Witness Requirement",
  "requiresWitnesses": 3
}
```

This is insufficient for modeling:
- **Scheduled operations**: Daily ATP recharge at 00:00 UTC
- **Emergency protocols**: Immediate halt without quorum on security breach
- **Graduated responses**: Temporal surprise threshold triggering escalating actions
- **Failure handling**: Rejected transaction vs. flagged for review vs. emergency halt

### Real-World Requirements

Society 4's governance revealed concrete needs:

1. **PROC-ATP-RECHARGE**: Daily energy regeneration
   - Trigger: Daily at 00:00 UTC
   - Amount: +20 ATP
   - Cap: Initial allocation
   - Targets: All queens

2. **PROC-EMERGENCY**: Security breach response
   - Trigger: Security breach detected
   - Authority: Security Queen
   - Immediate: True (no quorum)
   - Witnesses: False

3. **PROC-TEMPORAL-AUTH**: Surprise-based authentication
   - Trigger: Network state change
   - Method: Compute surprise factor
   - Thresholds: {low: 0.3, medium: 0.6, high: 0.8}
   - Actions: {low: continue, medium: validate, high: witness}

4. **PROC-HARDWARE-VERIFY**: Hardware binding validation
   - Trigger: Every critical operation
   - Method: Extract and compare hash
   - Failure action: Reject transaction

These cannot be expressed in the minimal SAL schema without custom fields.

## Specification

### 1. Time-Based Triggers

**Problem**: No standard format for scheduled or periodic execution.

**Proposal**: Define `trigger` field with standard formats:

```json
{
  "trigger": {
    "type": "schedule",
    "schedule": "daily",
    "time": "00:00:00Z",
    "timezone": "UTC"
  }
}
```

Or simplified string format:

```json
{
  "trigger": "daily_00:00_utc"
}
```

**Supported trigger types**:
- `event:<event_name>` - Event-driven
- `schedule:<cron_expression>` - Cron-style scheduling
- `daily_HH:MM_TZ` - Daily at specific time
- `interval_<duration>` - Periodic (e.g., `interval_90_days`)
- `condition:<r6_selector>` - Conditional execution

**Example**:
```json
{
  "id": "PROC-ATP-RECHARGE",
  "name": "Daily ATP Regeneration",
  "trigger": "daily_00:00_utc",
  "amount": 20,
  "targets": ["all_queens"],
  "cap": "initial_allocation"
}
```

### 2. Multi-Threshold Logic

**Problem**: No way to express graduated responses based on computed values.

**Proposal**: Define `thresholds` and `actions` mappings:

```json
{
  "thresholds": {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8
  },
  "actions": {
    "low": "continue_normal",
    "medium": "additional_validation",
    "high": "witness_request"
  }
}
```

**Threshold evaluation**:
- Compute value via `method` field
- Compare to threshold levels
- Execute corresponding action

**Example**:
```json
{
  "id": "PROC-TEMPORAL-AUTH",
  "name": "Temporal Authentication Check",
  "trigger": "network_state_change",
  "method": "compute_surprise_factor",
  "thresholds": {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8
  },
  "actions": {
    "low": "continue_normal",
    "medium": "additional_validation",
    "high": "witness_request"
  },
  "rfc": "RFC-TEMP-AUTH-001"
}
```

### 3. Failure Actions

**Problem**: No standard way to specify what happens when procedure fails.

**Proposal**: Define `failureAction` field with standard actions:

```json
{
  "failureAction": "reject_transaction"
}
```

**Standard failure actions**:
- `reject_transaction` - Hard fail, abort operation
- `flag_for_review` - Soft fail, queue for manual review
- `emergency_halt` - Stop all operations
- `notify_authority:<role>` - Alert specific role
- `escalate_to_quorum` - Require higher approval

**Example**:
```json
{
  "id": "PROC-HARDWARE-VERIFY",
  "name": "Hardware Binding Verification",
  "trigger": "every_critical_operation",
  "method": "extract_and_compare_hash",
  "failureAction": "reject_transaction"
}
```

### 4. Immediate Execution Flag

**Problem**: No way to bypass normal consensus for emergencies.

**Proposal**: Define `immediate` boolean flag:

```json
{
  "immediate": true,
  "requiresWitnesses": false
}
```

**Semantics**:
- `immediate: true` - Execute without waiting for consensus
- Only allowed for security/emergency procedures
- Must specify `authority` field for who can invoke
- Should log for post-hoc audit

**Example**:
```json
{
  "id": "PROC-EMERGENCY",
  "name": "Emergency Halt Procedure",
  "trigger": "security_breach_detected",
  "authority": "security_queen",
  "requiresWitnesses": false,
  "immediate": true
}
```

### 5. Action Mappings

**Problem**: Static procedures can't adapt to dynamic conditions.

**Proposal**: Define `actions` as threshold-to-action mappings:

```json
{
  "actions": {
    "low": "continue_normal",
    "medium": "additional_validation",
    "high": "witness_request"
  }
}
```

Combined with `thresholds`, enables dynamic procedure behavior.

## Complete Schema Extension

### Extended Procedure Type

```json
{
  "id": "string",
  "name": "string",
  "description": "string",

  // Execution control
  "trigger": "string | TriggerObject",
  "immediate": "boolean",
  "authority": "string | string[]",

  // Witness requirements
  "requiresWitnesses": "boolean | number",
  "witnessTypes": "string[]",
  "witnessCount": "number",

  // Logic and computation
  "method": "string",
  "thresholds": {
    "<level>": "number"
  },
  "actions": {
    "<level>": "string"
  },

  // Failure handling
  "failureAction": "string",

  // Additional parameters (procedure-specific)
  "amount": "number",
  "targets": "string[]",
  "cap": "string",
  "votingPeriod": "string",

  // References
  "rfc": "string",
  "relatedNorms": "string[]"
}
```

### Trigger Object Type

```json
{
  "type": "event | schedule | condition | interval",
  "schedule": "string",  // Cron expression
  "time": "string",      // ISO 8601 time
  "timezone": "string",  // IANA timezone
  "event": "string",     // Event name
  "condition": "string", // R6 selector
  "interval": "string"   // Duration (e.g., "90_days")
}
```

## Implementation Guidance

### Minimal Implementation

Implementations MUST support:
- `trigger` as string in simplified format
- `immediate` boolean flag
- `failureAction` as predefined action string

### Full Implementation

Implementations SHOULD support:
- `trigger` as full TriggerObject
- `thresholds` and `actions` mappings
- Custom `method` execution
- All standard failure actions

### Validation

Procedures with extensions MUST:
1. Validate `trigger` format if present
2. Ensure `immediate: true` has `authority` specified
3. Verify `thresholds` and `actions` have matching keys
4. Check `failureAction` is recognized action

## Examples

### Example 1: Daily Scheduled Operation

```json
{
  "id": "PROC-ATP-RECHARGE",
  "name": "Daily ATP Regeneration",
  "trigger": "daily_00:00_utc",
  "amount": 20,
  "targets": ["all_queens"],
  "cap": "initial_allocation",
  "description": "Daily energy recharge for all queens"
}
```

### Example 2: Emergency Protocol

```json
{
  "id": "PROC-EMERGENCY",
  "name": "Emergency Halt Procedure",
  "trigger": "security_breach_detected",
  "authority": "security_queen",
  "requiresWitnesses": false,
  "immediate": true,
  "description": "Security Queen can immediately halt without quorum"
}
```

### Example 3: Graduated Response

```json
{
  "id": "PROC-TEMPORAL-AUTH",
  "name": "Temporal Authentication Check",
  "trigger": "network_state_change",
  "method": "compute_surprise_factor",
  "thresholds": {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8
  },
  "actions": {
    "low": "continue_normal",
    "medium": "additional_validation",
    "high": "witness_request"
  },
  "description": "Check temporal patterns and modulate trust",
  "rfc": "RFC-TEMP-AUTH-001"
}
```

### Example 4: Validation with Failure Handling

```json
{
  "id": "PROC-HARDWARE-VERIFY",
  "name": "Hardware Binding Verification",
  "trigger": "every_critical_operation",
  "method": "extract_and_compare_hash",
  "failureAction": "reject_transaction",
  "description": "Verify hardware hash matches genesis binding"
}
```

### Example 5: Quorum with Time Limit

```json
{
  "id": "PROC-QUEEN-CONSENSUS",
  "name": "Queens Quorum Voting",
  "requiresQuorum": 5,
  "totalQueens": 8,
  "votingPeriod": "48_hours",
  "vetoAuthority": ["security_queen"],
  "description": "Major decisions require 5/8 queens (Security Queen has veto)"
}
```

## Backward Compatibility

### Minimal Procedures Still Valid

Existing minimal procedures remain valid:

```json
{
  "id": "PROC-WIT-3",
  "name": "Minimum Witness Requirement",
  "requiresWitnesses": 3
}
```

### Graceful Degradation

Implementations not supporting extensions SHOULD:
- Ignore unknown fields
- Log warnings for unsupported features
- Fall back to minimal procedure semantics

### Version Detection

Law Datasets using extensions SHOULD declare:

```json
{
  "complianceLevel": "web4-core-v1.0",
  "extensions": ["law-oracle-procedures-v1"]
}
```

## Security Considerations

### Immediate Execution

`immediate: true` bypasses consensus, creating security risk:
- MUST restrict to trusted authorities
- SHOULD require post-hoc audit
- MUST log all immediate executions
- SHOULD have revocation mechanism

### Time-Based Triggers

Scheduled procedures create timing attack surface:
- MUST use authenticated time source
- SHOULD validate trigger hasn't been tampered
- MUST handle clock skew gracefully

### Threshold Gaming

Complex thresholds enable gaming:
- SHOULD make computation methods transparent
- MUST prevent threshold manipulation
- SHOULD include threshold change in lineage

## Web4 Integration

### R6 Action Grammar Binding

Procedures map to R6 selectors:

```
r6.procedure.<proc_id>.execute
r6.procedure.<proc_id>.trigger
r6.procedure.<proc_id>.validate
```

### Law Dataset Compliance

Extended procedures remain valid Web4LawDataset:

```json
{
  "@context": ["https://web4.io/contexts/law.jsonld"],
  "type": "Web4LawDataset",
  "procedures": [/* extended procedures */]
}
```

### SPARQL Queries

Query procedures by capability:

```sparql
PREFIX law: <web4://law/>
SELECT ?id ?trigger
WHERE {
  ?proc law:trigger ?trigger .
  ?proc law:id ?id .
  FILTER(CONTAINS(?trigger, "daily"))
}
```

## Open Questions

1. **Standard method registry**: Should we define standard `method` names?
2. **Threshold ordering**: Should thresholds be ordered or explicit ranges?
3. **Action composition**: Can actions be composite (e.g., "validate AND notify")?
4. **Trigger priority**: How to handle multiple triggered procedures?
5. **Procedure dependencies**: Should we support procedure prerequisites?

## References

- Web4 SAL Specification (web4-standard/protocols/sal.md)
- Society 4 Law Oracle v1.0.0 (implementation/society4/laws/)
- RFC-TEMP-AUTH-001: Temporal Authentication
- RFC 9334: Entity Attestation Token (EAT)

## Appendix: Society 4 Implementation

Society 4's Law Oracle v1.0.0 includes 7 procedures using these extensions:

1. **PROC-WIT-3**: Minimal (baseline)
2. **PROC-EMERGENCY**: Uses `immediate`, `authority`
3. **PROC-CONSENSUS**: Uses `trigger`, `requiresWitnesses`
4. **PROC-HARDWARE-VERIFY**: Uses `trigger`, `method`, `failureAction`
5. **PROC-TEMPORAL-AUTH**: Uses all features (thresholds, actions, method)
6. **PROC-ATP-RECHARGE**: Uses `trigger`, custom fields
7. **PROC-QUEEN-CONSENSUS**: Uses `requiresQuorum`, `votingPeriod`, `vetoAuthority`

These demonstrate real-world utility of proposed extensions.

## Changelog

- 2025-09-30: Initial draft based on Society 4 Law Oracle implementation
