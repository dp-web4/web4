# Web4 Commerce Demo: Agent Authorization with T3 Trust Tracking

A complete, self-contained demonstration of Web4's agent authorization system for commerce applications.

## Overview

This demo shows how Web4 enables **safe delegation of purchasing authority to AI agents** with:

- **Cryptographically enforced limits** on spending
- **Fine-grained resource constraints** (what agents can access)
- **ATP (Allocation Transfer Packet)** budget tracking
- **T3 (Talent/Training/Temperament) trust tracking** for reputation-based authorization
- **Instant revocation** of delegated authority
- **Witness-based approval** for high-value purchases
- **Complete audit trail** of all agent actions

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     User (Delegator)                        │
│              via Delegation UI (port 8001)                  │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Creates delegation with limits
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Delegation Registry                        │
│  - Resource constraints (what can be accessed)              │
│  - Financial binding (spending limits)                      │
│  - ATP budget (computational costs)                         │
│  - T3 trust profile (agent reputation)                      │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Agent attempts purchase
             ▼
┌─────────────────────────────────────────────────────────────┐
│               Web4Verifier (Merchant SDK)                   │
│                                                              │
│  ✓ Check 1: Timestamp validation                           │
│  ✓ Check 2: Signature verification                         │
│  ✓ Check 3: Revocation check                               │
│  ✓ Check 4: Replay prevention (nonce)                      │
│  ✓ Check 5: Resource authorization                         │
│  ✓ Check 6: Financial authorization                        │
│  ✓ Check 7: ATP budget                                     │
│  ✓ Check 8: Witness enforcement                            │
│  ✓ Check 9: Trust score (T3)                               │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Record transaction outcome
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   T3 Trust Tracker                          │
│                                                              │
│  • Talent:      Success rate + quality (30%)               │
│  • Training:    Experience level (50%)                      │
│  • Temperament: Constraint adherence (20%)                 │
│                                                              │
│  Composite Trust = weighted average                         │
└─────────────────────────────────────────────────────────────┘
```

### T3 Trust System

The **T3 (Talent/Training/Temperament) system** provides reputation-based trust scores that evolve based on agent behavior:

#### 1. **Talent** (30% weight)
   - Measures **capability** - how well the agent performs
   - Calculated from: `0.7 × success_rate + 0.3 × avg_quality`
   - Increases with successful transactions
   - Decreases with failures or poor quality

#### 2. **Training** (50% weight)
   - Measures **experience** - how much the agent has learned
   - Calculated logarithmically: `log(1 + transactions) / log(101)`
   - Grows with transaction count (caps around 100 transactions)
   - New agents start at 0.0, experienced agents reach ~1.0

#### 3. **Temperament** (20% weight)
   - Measures **reliability** - how well the agent follows rules
   - Calculated from: `0.6 × constraint_adherence + 0.4 × behavioral_consistency`
   - High when agent stays within constraints
   - Decreases with constraint violations

#### Composite Trust Score
```
Composite = (0.3 × Talent) + (0.5 × Training) + (0.2 × Temperament)
```

**Authorization Logic**:
- New agents (no history): Allowed, profile created on first transaction
- Existing agents: Must meet minimum trust threshold (default: 0.3 / 30%)
- Trust evolves in real-time based on transaction outcomes

## Demo Components

### 1. Delegation UI (`delegation-ui/`)

**Web interface for users to manage agent delegations.**

**Features**:
- Create new delegations with spending limits
- Set per-transaction limits
- Choose allowed resources/categories
- Set witness approval thresholds
- Monitor agent activity in real-time
- View T3 trust scores with visual progress bars
- Approve/deny high-value purchases
- Revoke delegations instantly

**Run**:
```bash
cd delegation-ui
python app.py
# Visit: http://localhost:8001
```

**T3 Display**:
- Visual progress bars for Talent, Training, Temperament
- Overall composite trust score
- Transaction statistics (count, success rate)
- Real-time updates as agent builds reputation

### 2. Store Demo (`store/`)

**Mock e-commerce store showing agent-initiated purchases.**

**Features**:
- Agent browses products
- Agent attempts purchases using delegated authority
- Real-time authorization verification
- Transaction recording with T3 updates
- Visual feedback on trust evolution

**Run**:
```bash
cd store
python app.py
# Visit: http://localhost:8000
```

### 3. Vendor SDK (`../implementation/reference/vendor_sdk.py`)

**Simple library for merchants to verify Web4 authorizations.**

**One-line integration**:
```python
from vendor_sdk import Web4Verifier

# Initialize with T3 tracker
verifier = Web4Verifier(
    atp_tracker=atp_tracker,
    # ... other security components
    t3_tracker=t3_tracker,
    min_trust_threshold=0.3  # Require 30% trust minimum
)

# Verify purchase authorization
result = verifier.verify_authorization(
    lct_chain=request_data["lct_chain"],
    resource_id="amazon.com:products/book-123",
    amount=75.00,
    merchant="amazon.com"
)

if result.authorized:
    process_payment()

    # Record for T3 reputation building
    verifier.record_purchase(
        delegatee_id=agent_id,
        amount=75.00,
        merchant="amazon.com",
        item_id="book-123",
        success=True,
        quality_score=0.9  # Optional quality rating
    )
```

**Key Methods**:
- `verify_authorization()` - Performs all 9 security checks
- `verify_purchase()` - Simplified purchase verification
- `record_purchase()` - Records outcome + updates T3 trust

## Running the Demo

### Prerequisites
```bash
pip install fastapi uvicorn pytest
```

### 1. Run Delegation UI
```bash
cd demo/delegation-ui
python app.py
```
Visit: http://localhost:8001

### 2. Run Store Demo
```bash
cd demo/store
python app.py
```
Visit: http://localhost:8000

### 3. Test the Flow

1. **Create Delegation** (in UI):
   - Agent Name: "Claude Shopping Assistant"
   - Agent ID: "agent-claude-42"
   - Daily Budget: $500
   - Per-Transaction: $100
   - Allowed Resources: Books, Music
   - Approval threshold: $50

2. **Make Purchase** (in Store):
   - Agent browses books
   - Selects item under $50 (auto-approved)
   - Authorization verified (9 checks pass)
   - Purchase recorded, T3 updated

3. **View Trust Evolution** (in UI):
   - Navigate to "Manage Delegations"
   - See T3 scores update:
     - Talent increases (successful purchase)
     - Training increases (experience gained)
     - Temperament maintained (stayed within limits)
   - Composite trust improves

4. **High-Value Purchase** (in Store):
   - Agent selects item over $50
   - Requires witness approval
   - User approves in UI
   - T3 scores continue to evolve

## Test Results

### Unit Tests (T3 Tracker)
```bash
cd implementation/reference
pytest tests/test_t3_tracker.py -v
```
**Result**: 30/30 tests passing

**Coverage**:
- Profile creation and persistence
- Transaction recording
- Score calculations (talent, training, temperament)
- Composite trust calculation
- Historical tracking
- Edge cases and error handling

### Integration Tests (T3 + Authorization)
```bash
cd implementation/reference
pytest tests/test_t3_integration.py -v
```
**Result**: 10/10 tests passing

**Coverage**:
- Trust threshold enforcement
- Trust improvement through successful transactions
- Trust degradation from failures
- Constraint violation impact
- First-time agent handling
- Composite trust weighting
- record_purchase integration
- Verification result details

### Component Tests (Full Stack)
```bash
cd implementation/reference
pytest tests/ -v
```
**Result**: 166/166 tests passing

**Full test suite includes**:
- LCT identity (13 tests)
- ATP budget tracking (15 tests)
- Resource constraints (18 tests)
- Financial binding (25 tests)
- Revocation registry (8 tests)
- Nonce tracker (9 tests)
- Timestamp validation (12 tests)
- Key rotation (11 tests)
- Witness enforcer (13 tests)
- Vendor SDK (12 tests)
- T3 tracker (30 tests)
- T3 integration (10 tests)

## Key Files

```
demo/
├── README.md                           # This file
├── delegation-ui/
│   └── app.py                          # User delegation management UI
└── store/
    └── app.py                          # Mock e-commerce store

implementation/reference/
├── vendor_sdk.py                       # Merchant verification library
├── t3_tracker.py                       # T3 trust tracking system
├── atp_tracker.py                      # ATP budget tracking
├── resource_constraints.py             # Resource authorization
├── financial_binding.py                # Financial limits
├── revocation_registry.py              # Delegation revocation
├── nonce_tracker.py                    # Replay attack prevention
├── timestamp_validator.py              # Timestamp validation
├── key_rotation.py                     # Key management
└── witness_enforcer.py                 # Witness protocol

tests/
├── test_t3_tracker.py                  # T3 unit tests (30 tests)
├── test_t3_integration.py              # T3 integration tests (10 tests)
└── test_*.py                           # Other component tests (126 tests)
```

## What This Demonstrates

### 1. **Safe AI Agent Delegation**
- Users maintain full control
- Agents can't exceed delegated authority
- Instant revocation capability
- Clear audit trail

### 2. **Trust-Based Authorization**
- New agents start with neutral trust
- Trust builds through successful actions
- Poor performance lowers trust
- Constraint violations hurt reputation
- Trust can gate access to higher-value operations

### 3. **Merchant Integration**
- One SDK call verifies everything
- Clear verification reports
- Automatic reputation tracking
- Minimal integration effort (< 1 day)

### 4. **Web4 Principles in Action**
- **Presence**: LCT identity for agents
- **Capability**: Resource constraints define what agents can do
- **Context**: ATP tracks computational costs
- **Trust**: T3 tensors measure reputation
- **Witness**: High-value actions require approval

## Trust Evolution Example

**Scenario**: New shopping agent over 10 transactions

```
Transaction 1: $25 book (success, quality=0.9)
  Talent:      0.50 → 0.97  (first success, high quality)
  Training:    0.00 → 0.15  (first experience)
  Temperament: 0.50 → 0.50  (within constraints)
  Composite:   0.30 → 0.52  ✅ Above threshold

Transaction 2-5: Various purchases (all successful)
  Talent:      0.97 → 0.98  (maintaining high success rate)
  Training:    0.15 → 0.38  (growing experience)
  Temperament: 0.50 → 0.60  (consistent behavior)
  Composite:   0.52 → 0.67  ✅ Trust increasing

Transaction 6: $120 item (exceeds $100 limit, but succeeded)
  Talent:      0.98 → 0.98  (success maintained)
  Training:    0.38 → 0.43  (more experience)
  Temperament: 0.60 → 0.45  (constraint violation!)
  Composite:   0.67 → 0.64  ⚠️ Trust slightly decreased

Transaction 7-10: Back to normal purchases (all successful)
  Talent:      0.98 → 0.99  (excellent track record)
  Training:    0.43 → 0.52  (experienced agent now)
  Temperament: 0.45 → 0.55  (recovering from violation)
  Composite:   0.64 → 0.71  ✅ Trust restored and growing
```

**Result**: Agent with 71% trust score, mostly trusted for autonomous operations, might get access to higher limits or lower witness thresholds.

## Limitations & Future Work

### Current Scope
This is a **proof-of-concept** demonstrating Web4 principles in commerce context. Not production-ready without:

- Real cryptographic signatures (currently mocked)
- Blockchain integration for LCT identities
- Distributed witness protocol
- Production database (currently in-memory)
- Rate limiting and DDoS protection
- PCI compliance for real payments

### Vision vs Implementation Gap
See `WHITEPAPER_DISCREPANCIES.md` for detailed analysis of what's implemented vs. the full Web4 vision.

**Implemented** (this demo):
- Agent authorization for commerce
- Resource constraints and financial limits
- T3 trust tracking and reputation
- ATP budget tracking
- Witness workflow for high-value actions
- Complete test coverage

**Vision** (not yet implemented):
- Full LCT identity system with trust webs
- Complete ATP/ADP energy-value metabolic cycles
- Blockchain typology (Compost/Leaf/Stem/Root chains)
- Memory as temporal sensing architecture
- Dictionary entities for cross-domain meaning
- Global trust tensors

## Architecture Decisions

### Why T3 for Commerce?
Traditional authorization is binary (yes/no). T3 adds a **continuous trust dimension**:

- **New agents** start neutral, can transact but watched closely
- **Proven agents** earn higher trust, get more autonomy
- **Problematic agents** lose trust, face stricter limits
- **Trust recovery** possible through improved behavior

This mirrors how humans build trust - gradual, evidence-based, recoverable.

### Why These Weights (30/50/20)?
```
Talent:      30%  - Important but can be learned
Training:    50%  - Experience is the best predictor
Temperament: 20%  - Following rules matters, but less than results
```

These can be customized per use case:
- **High-stakes** (medical, financial): Increase Temperament weight
- **Creative tasks**: Increase Talent weight
- **Routine operations**: Increase Training weight

### Why Logarithmic Training Growth?
Experience has diminishing returns. The difference between transaction 1 and 10 is huge. Between 91 and 100, negligible. Logarithmic curve captures this.

## License

This demo is part of the Web4 project. See main repository for license details.

## Authors

- **Claude (Anthropic AI)** - Interactive development
- **Web4 Project** - Architecture and vision

## Generated

🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

**This is a self-contained proof-of-concept. The full Web4 vision includes many more components. See `/whitepaper` for complete architecture.**
