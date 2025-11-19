# Web4 Strategic Direction: AI Agent Authorization

**Date**: November 10, 2025
**Status**: Active Development Direction
**Context**: Post-security fixes completion, ready for real-world application

---

## The Core Problem: AI Agent Commerce & Authorization

AI agents need to act on behalf of humans across multiple services, including making purchases. Current systems don't adequately answer the critical questions from both vendors and users.

---

## Critical Questions That Must Be Answered

### From Service Provider/Vendor Perspective

**Q1: How do I know it's an agent?**
- Need explicit entity type declaration
- Need provenance (who created it, who operates it)
- Need ability to apply agent-specific policies

**Q2: Who is it an agent for?**
- Need verified delegation chain
- Need cryptographic proof of authorization
- Need to identify root principal (the human responsible)

**Q3: What is its authorized scope?**
- Need fine-grained resource constraints
- Need budget limits (financial and operational)
- Need blacklist capabilities (explicitly denied actions)

**Q4: Who is liable for its actions?**
- Need clear liability chain
- Need financial limits (max exposure)
- Need payment method verification
- Need recourse mechanism for unauthorized actions

### From Human User Perspective

**Q1: How do I tell the agent what it's allowed to do?**
- Need simple, user-friendly interface
- Need clear scope definition (not technical jargon)
- Need budget controls in dollars, not abstract tokens

**Q2: How does the world confirm authorizations?**
- Need standard verification protocol
- Need cryptographic proof
- Need real-time checking (not batch/delayed)

**Q3: How do I detect and correct transgressions?**
- Need real-time activity monitoring
- Need instant revocation capability
- Need audit trail of all actions
- Need alerts for out-of-scope attempts

**Q4: To what extent am I liable? (Do I have to pay?)**
- Need clear maximum exposure
- Need protection from unauthorized purchases
- Need dispute resolution protocol
- Need legal clarity on responsibility

---

## How Web4 Features Map to These Questions

### What We Have (Security Fixes Complete)

**1. LCT Identity System**
- Entity identification with metadata
- Entity type declaration (human, agent, service, hardware)
- Provenance tracking (created by, operated by)
- **Answers**: "How do I know it's an agent?"

**2. Delegation Chains**
- Cryptographically signed delegations
- Transitive trust (Alice → Bob → Agent)
- Full audit trail of delegation path
- **Answers**: "Who is it an agent for?"

**3. Resource Constraints**
- Fine-grained resource patterns with glob support
- Permission level hierarchy (READ < WRITE < ADMIN)
- Whitelist/blacklist with precedence
- **Answers**: "What is its authorized scope?" (partially)

**4. ATP Budget Tracking**
- Daily and per-action limits
- Automatic budget reset
- Real-time budget checking
- **Answers**: "What is its authorized scope?" (budget aspect)

**5. Witness Enforcement**
- Multi-party approval requirements
- Trust-weighted validation
- Role-based witness requirements
- **Answers**: "How do I detect and correct?" (approval layer)

**6. Revocation Registry**
- Instant credential invalidation
- Cryptographically signed revocations
- Immediate effect across all services
- **Answers**: "How do I detect and correct?" (revocation)

**7. Timestamp Validation**
- Temporal security
- Prevents backdating/future-dating
- Clock skew tolerance
- **Answers**: Audit trail integrity

**8. Key Rotation**
- Secure key lifecycle
- Emergency revocation
- Smooth transitions
- **Answers**: Long-term identity security

### What We Need to Build

**1. Financial Binding**
- Link payment methods to LCTs
- Real-time balance/limit checking
- Charge authorization protocol
- **Fills gap**: "Who pays?" and "Maximum liability"

**2. Payment Integration Protocol**
- Standard format for charge requests
- Verification before charging
- Chargeback/dispute mechanism
- **Fills gap**: "How does the world confirm?" (payment aspect)

**3. User Interface**
- Simple delegation creation
- Activity dashboard
- Approval workflows
- Budget monitoring
- **Fills gap**: "How do I tell the agent?" and "How do I monitor?"

**4. Vendor Integration Libraries**
- Verification SDK (Python, JavaScript, Go, etc.)
- Reference implementations
- Testing tools
- **Fills gap**: Ecosystem adoption

**5. Legal Framework**
- Liability allocation protocol
- Dispute resolution process
- Terms of service templates
- **Fills gap**: "Who is liable?" (legal clarity)

---

## Concrete Example: End-to-End Purchase Flow

### Setup Phase

```python
# Alice creates delegation to Claude
delegation = Delegation(
    delegator=LCT(
        entity_id="human-alice-123",
        entity_type="human",
        email="alice@company.com"
    ),
    delegatee=LCT(
        entity_id="agent-claude-42",
        entity_type="ai_agent",
        model="claude-sonnet-4.5",
        operator="anthropic"
    ),
    resources=ResourceConstraints([
        "amazon:products/books/*",      # Can buy books
        "amazon:products/music/*",      # Can buy music
        "!amazon:products/electronics/*" # Cannot buy electronics
    ]),
    atp_budget=ATPBudget(
        daily_limit=1000,      # $1000/day max
        per_action_limit=100   # $100/transaction max
    ),
    witness_requirements=WitnessRequirement(
        threshold_amount=50,    # Purchases >$50 need approval
        witnesses=["alice-approval-key"]
    ),
    payment_binding=PaymentBinding(
        method=alice_credit_card,
        max_daily=1000,
        max_transaction=100
    )
)
```

### Purchase Flow

**Step 1: Claude wants to buy book ($75)**

```python
# Claude creates purchase request
request = PurchaseRequest(
    item="book-isbn-123456",
    price=75.00,
    merchant="amazon",
    agent_lct="agent-claude-42",
    reason="Research materials for ML project"
)
```

**Step 2: Web4 Authorization Checks**

```python
# Check 1: Resource authorization
authorized, msg = resource_constraints.is_authorized(
    "amazon:products/books/isbn-123456",
    PermissionLevel.WRITE
)
# → ✅ True (books are in allowed list)

# Check 2: ATP budget
sufficient, msg = atp_tracker.check_and_deduct(
    "agent-claude-42",
    amount=75
)
# → ✅ True (75 < 100 per-action, daily total < 1000)

# Check 3: Witness requirement
needs_witness = (75 > 50)  # threshold_amount
# → ⚠️ True (requires Alice's approval)
```

**Step 3: Alice Approval Request**

```
📱 Push Notification to Alice:

Claude wants to purchase:
━━━━━━━━━━━━━━━━━━━━━━━
📚 "Machine Learning Textbook"
💰 $75.00
🏪 Amazon

Reason: "Research materials for ML project"

Your budget: $225/$1000 used today
This purchase: $75 (within your $100 limit)

[Approve] [Deny] [View Details]
```

**Step 4: Alice Approves**

```python
# Alice signs approval
witness_signature = alice_key.sign(
    purchase_hash(request)
)

# Witness added to request
request.witnesses.append(
    WitnessSignature(
        witness_id="alice-approval-key",
        signature=witness_signature,
        timestamp=now()
    )
)
```

**Step 5: Amazon Verification**

```python
# Amazon receives request with Web4 authorization
POST /api/purchase
Headers:
  Authorization: Web4-LCT <base64-encoded-chain>

Body:
{
  "item": "book-isbn-123456",
  "price": 75.00,
  "lct_chain": {
    "delegator": "human-alice-123",
    "delegatee": "agent-claude-42",
    "delegation_signature": "sig-alice-...",
    "request_signature": "sig-claude-...",
    "witnesses": [
      {
        "witness_id": "alice-approval-key",
        "signature": "sig-alice-approval-...",
        "timestamp": "2025-11-10T14:30:00Z"
      }
    ]
  }
}

# Amazon verifies
verifier = Web4Verifier()

# 1. Verify signature chain
assert verifier.verify_delegation_chain(lct_chain)

# 2. Check resource authorization
assert verifier.check_resource_authorization(
    "amazon:products/books/isbn-123456",
    delegation.resources
)

# 3. Check ATP budget
assert verifier.check_atp_budget(
    "agent-claude-42",
    amount=75,
    delegation.atp_budget
)

# 4. Verify witness
assert verifier.verify_witnesses(
    purchase_hash,
    witnesses=[lct_chain.witnesses[0]],
    requirements=delegation.witness_requirements
)

# 5. Check payment binding
assert verifier.check_payment_authorization(
    alice_credit_card,
    amount=75,
    delegation.payment_binding
)

# All checks pass → Charge card and fulfill order
charge_card(alice_credit_card, 75.00)
ship_order(item="book-isbn-123456", to=alice_address)
```

**Step 6: Audit Trail Updated**

```python
# Activity logged
activity_log.append({
    "timestamp": "2025-11-10T14:30:00Z",
    "agent": "agent-claude-42",
    "action": "purchase",
    "resource": "amazon:products/books/isbn-123456",
    "amount": 75.00,
    "atp_deducted": 75,
    "witness_required": True,
    "witness_approved_by": "alice-approval-key",
    "status": "completed",
    "signatures": {
        "delegation": "sig-alice-...",
        "request": "sig-claude-...",
        "witness": "sig-alice-approval-..."
    }
})

# Budget updated
atp_tracker.budgets["agent-claude-42"].daily_used = 300  # Was 225, now 300
```

**Step 7: Alice Dashboard Shows**

```
┌─────────────────────────────────────────┐
│ Claude Agent Activity - Today           │
├─────────────────────────────────────────┤
│ ATP Used: $300 / $1,000 daily limit     │
│ ████████░░░░░░░░░░░░░░░░░ 30%          │
│                                         │
│ Recent Actions:                         │
│ ✅ 14:30 - Purchased book ($75.00)     │
│            "Machine Learning Textbook"  │
│            YOU APPROVED ✓               │
│                                         │
│ ✅ 12:15 - Purchased book ($45.00)     │
│            Auto-approved (<$50)         │
│                                         │
│ ✅ 09:30 - Created GitHub issue         │
│            No charge                    │
│                                         │
│ ⚠️  08:45 - ATTEMPTED electronics      │
│            purchase → BLOCKED            │
│            (Outside authorized scope)   │
│                                         │
│ [View Full History] [Adjust Limits]    │
│ [🚨 REVOKE ALL ACCESS]                  │
└─────────────────────────────────────────┘
```

---

## The MVP: What We Need to Build

### Phase 1: Core Financial Integration (2-3 weeks)

**Components**:
1. **Payment Binding Module**
   - Link payment methods to LCTs
   - Daily/per-transaction limit enforcement
   - Real-time balance checking
   - Charge authorization protocol

2. **Purchase Authorization Flow**
   - Extend existing authorization engine
   - Add financial checks
   - Integrate witness approval for high-value transactions
   - Generate audit trail entries

3. **Vendor Verification SDK**
   - Python library (primary)
   - JavaScript library (web merchants)
   - Example integrations
   - Testing framework

**Deliverable**: Working authorization system for purchases

### Phase 2: User Interface (2-3 weeks)

**Components**:
1. **Delegation Creation UI**
   - Simple form: "What can agent do?"
   - Budget sliders
   - Resource selection (checkboxes, not patterns)
   - Witness threshold setting

2. **Activity Dashboard**
   - Real-time activity feed
   - Budget usage visualization
   - Approval inbox (pending witness requests)
   - Instant revocation button

3. **Mobile App (optional)**
   - Push notifications for approval requests
   - Quick approve/deny
   - Activity monitoring

**Deliverable**: User-friendly delegation and monitoring

### Phase 3: Demo Merchant (1-2 weeks)

**Components**:
1. **Demo Store**
   - Simple e-commerce site
   - Web4 authentication
   - Books, music, digital products
   - Real checkout flow (demo mode)

2. **Agent Integration**
   - Claude Code can browse store
   - Make purchases on user's behalf
   - Request approval for high-value items
   - Handle rejections gracefully

3. **End-to-End Demo**
   - Video walkthrough
   - Live demo site
   - Documentation

**Deliverable**: Proof of concept that answers all critical questions

### Phase 4: Real Merchant Integration (Parallel to Phase 3)

**Target**: Find 1-2 friendly merchants willing to pilot

**Candidates**:
- Digital goods (lower risk, instant delivery)
- Developer tools (tech-savvy audience)
- API services (already familiar with programmatic access)

**Deliverable**: Real-world usage data

---

## Success Criteria

The MVP successfully demonstrates:

✅ **Vendor Perspective**:
- [ ] Clear agent identification in requests
- [ ] Verified delegation chain to human principal
- [ ] Fine-grained scope verification
- [ ] Clear liability chain and payment binding
- [ ] Simple integration (SDK does the heavy lifting)

✅ **User Perspective**:
- [ ] Simple delegation creation (< 2 minutes)
- [ ] Clear scope definition (non-technical language)
- [ ] Real-time activity monitoring
- [ ] Instant revocation capability
- [ ] Clear maximum financial exposure
- [ ] Approval flow for high-value actions

✅ **Agent Perspective**:
- [ ] Standard authorization protocol
- [ ] Clear capability discovery ("What am I allowed to do?")
- [ ] Graceful handling of denials
- [ ] Witness request flow for high-privilege actions

✅ **Technical**:
- [ ] All security components integrated
- [ ] Cryptographic verification working
- [ ] Performance acceptable (< 100ms for auth checks)
- [ ] Audit trail complete and queryable

---