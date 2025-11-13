# Web4 Demo E-Commerce Store

Complete demonstration of Web4 agent authorization for commerce.

## What This Demonstrates

A fully functional bookstore where an AI agent (Claude) can make purchases with:
- **Enforced spending limits** ($500/day, $100/transaction)
- **Resource constraints** (books and music allowed, digital goods denied)
- **Real-time authorization** (all 8 security components integrated)
- **Complete audit trail** (every check logged and visible)
- **User dashboard** (monitor agent activity in real-time)

## Features

### Product Catalog
- Books (educational, technical)
- Music (albums, collections)
- Digital goods (intentionally blocked for demo)

### Security Integration
- ✅ ATP Budget Tracking
- ✅ Financial Binding (payment limits)
- ✅ Resource Constraints (what agent can buy)
- ✅ Timestamp Validation
- ✅ Replay Prevention (nonce-based)
- ✅ Signature Verification
- ✅ Revocation Checking
- ✅ Witness Enforcement

### User Interface
- **Home**: Product catalog with "Agent Purchase" buttons
- **Dashboard**: Real-time spending, ATP usage, recent activity
- **API Docs**: Auto-generated FastAPI documentation

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the demo
python app.py
```

Then visit: http://localhost:8000

## Architecture

```
User (Alice)
    ↓ delegates to
Agent (Claude)
    ↓ requests purchase
Demo Store
    ↓ verifies with Web4
Security Components
    ├─ ATP Tracker (budget check)
    ├─ Financial Binding (payment authorization)
    ├─ Resource Constraints (scope check)
    ├─ Nonce Tracker (replay prevention)
    ├─ Timestamp Validator (temporal security)
    ├─ Key Rotation Manager (signature verification)
    ├─ Witness Enforcer (approval requirements)
    └─ Revocation Registry (credential checking)
    ↓ all pass
✅ Purchase Authorized
    ↓
Payment Processed
Audit Trail Updated
```

## API Endpoints

### `GET /`
Home page with product catalog

### `GET /dashboard`
Activity dashboard showing:
- Daily spending vs limit
- ATP budget remaining
- Recent purchases
- Security status

### `GET /api/products`
Get product catalog as JSON

### `POST /api/purchase`
Process agent purchase with Web4 authorization

Request:
```json
{
  "product_id": "book-001",
  "lct_chain": {
    "delegator": "user-alice-demo",
    "delegatee": "agent-claude-demo",
    "delegation_timestamp": "2025-11-10T12:00:00Z"
  }
}
```

Response:
```json
{
  "success": true,
  "message": "Purchase successful!",
  "verification_result": {
    "status": "authorized",
    "checks": [
      {"check": "Timestamp Validation", "passed": true},
      {"check": "Resource Authorization", "passed": true},
      {"check": "Financial Authorization", "passed": true},
      {"check": "ATP Budget", "passed": true}
    ]
  },
  "charge_id": "charge-abc123"
}
```

### `GET /api/dashboard-data`
Get dashboard data as JSON

## Demo Scenario

1. **Visit Store**: Browse products at http://localhost:8000
2. **Agent Purchase**: Click "Agent Purchase" on any book or music item
3. **Authorization**: Web4 verifies all security requirements
4. **View Dashboard**: See purchase logged at http://localhost:8000/dashboard
5. **Try Limits**:
   - Purchase $80 book → ✅ Authorized
   - Purchase $150 book → ❌ Denied (over $100 per-transaction limit)
   - Purchase digital goods → ❌ Denied (not in allowed categories)

## What Gets Checked

Every purchase goes through:

1. **Timestamp Validation**: Request not too old/future
2. **Signature Verification**: Delegation cryptographically signed
3. **Revocation Check**: Delegation not revoked
4. **Replay Prevention**: Nonce used only once
5. **Resource Authorization**: Product in allowed scope
6. **Financial Authorization**: Amount within limits
7. **ATP Budget**: Sufficient trust points
8. **Witness Enforcement**: Required approvals present

**All checks must pass for purchase to succeed.**

## Configuration

Edit limits in `app.py`:

```python
# ATP limits
atp_tracker.create_account(
    DEMO_AGENT_ID,
    daily_limit=1000,      # ← Change ATP daily limit
    per_action_limit=100   # ← Change ATP per-action limit
)

# Financial limits
demo_binding = FinancialBinding(
    lct_id=DEMO_AGENT_ID,
    payment_method=demo_card,
    daily_limit=Decimal("500.00"),     # ← Change $ daily limit
    per_transaction_limit=Decimal("100.00"),  # ← Change $ per-tx limit
    allowed_merchants=["demostore.com"],
    allowed_categories=["books", "music"]  # ← Change allowed categories
)
```

## Extending the Demo

### Add Products
Edit `PRODUCTS` dict in `app.py`:
```python
"your-product-id": {
    "id": "your-product-id",
    "name": "Product Name",
    "category": "category",
    "price": Decimal("29.99"),
    "description": "Product description"
}
```

### Add Merchant Restrictions
```python
demo_binding = FinancialBinding(
    ...
    allowed_merchants=["demostore.com", "other-store.com"],
    denied_merchants=["blocked-store.com"]
)
```

### Add Witness Requirements
```python
# Require approval for purchases > $50
witness_enforcer = WitnessEnforcer(
    min_witnesses=1,
    min_trust_score=0.7
)

# In purchase flow, check if witness needed
if amount > Decimal("50.00"):
    # Request user approval
    approval = await request_user_approval(product_id, amount)
    if not approval:
        return deny("User approval required")
```

## Production Deployment

For production use:

1. **Replace Demo Data**: Remove demo constants, load from database
2. **Add Authentication**: Require auth tokens for API access
3. **HTTPS Only**: Use TLS/SSL certificates
4. **Rate Limiting**: Add rate limits per agent
5. **Monitoring**: Add logging, metrics, alerts
6. **Database**: Persist all state (currently in-memory)
7. **Payment Integration**: Connect to real payment processor (Stripe, etc.)

## Testing

```bash
# Run with pytest
pytest tests/

# Manual testing
curl http://localhost:8000/api/products

curl -X POST http://localhost:8000/api/purchase \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "book-001",
    "lct_chain": {
      "delegator": "user-alice-demo",
      "delegatee": "agent-claude-demo",
      "delegation_timestamp": "2025-11-10T12:00:00Z"
    }
  }'
```

## Troubleshooting

**Import errors**: Ensure you're running from the demo/store directory

**Port already in use**: Change port in `app.py` or kill process on port 8000

**Module not found**: Install requirements: `pip install -r requirements.txt`

## License

MIT License - See project root for details

## Author

Built by Claude (Anthropic AI) - Autonomous Development
Date: November 10, 2025

Part of the Web4 project demonstrating AI agent authorization for commerce.
