# Web4 Delegation Management UI

User interface for creating and managing AI agent delegations.

## What This Does

Provides a beautiful web interface for users to:
- **Create delegations** with visual controls (sliders, checkboxes)
- **Monitor agent activity** in real-time
- **Set spending limits** (daily budget and per-transaction)
- **Choose allowed resources** (what agent can access)
- **Approve high-value purchases** (witness workflow)
- **Revoke delegations** instantly
- **View complete audit trail**

## Features

### Visual Delegation Creation
- Simple form-based interface
- Budget sliders ($0-$2000 daily, $0-$500 per-transaction)
- Resource checkboxes (books, music, digital goods, GitHub, AWS, etc.)
- Witness threshold slider (require approval for purchases over $X)
- One-click delegation creation

### Real-Time Monitoring
- View all active and revoked delegations
- See spending progress with visual bars
- Track daily budget consumption
- Monitor agent activity

### Approval Workflow
- Pending approvals section
- High-value purchase requests
- One-click approve/deny
- Reason tracking

### Security
- Instant revocation capability
- Complete audit trail
- Spending limit enforcement
- Resource scope restrictions

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Then visit: http://localhost:8001

## Screenshots

### Home - Create Delegation
Beautiful gradient header with navigation tabs. Create form with:
- Agent name and ID inputs
- Visual budget sliders with live value display
- Resource selection grid with icons
- Witness threshold slider
- Create button

### Manage Delegations
Grid of delegation cards showing:
- Agent name and ID
- Active/Revoked status badge
- Four stat boxes (daily budget, per-tx limit, spent today, remaining)
- Visual progress bar showing spending percentage
- Allowed resources list
- Revoke button (for active delegations)

### Pending Approvals
Cards for each pending approval with:
- Agent name
- Item description
- Amount (highlighted in orange)
- Reason for approval requirement
- Approve/Deny buttons

### Activity
Activity log showing recent agent actions (coming soon)

## Architecture

```
User Interface (Port 8001)
    ↓
FastAPI Backend
    ↓
In-Memory Storage (demo)
    ├─ delegations_db
    └─ pending_approvals

Integration with Web4 Components:
    ├─ ResourceConstraints (what agent can access)
    ├─ FinancialBinding (spending limits)
    ├─ ATPTracker (trust points budget)
    └─ WitnessEnforcer (approval requirements)
```

## API Endpoints

### `GET /`
Home page with delegation management interface

### `POST /api/delegations`
Create new delegation

Request:
```json
{
  "agent_name": "Claude Assistant",
  "agent_id": "agent-claude-42",
  "daily_budget": 500.0,
  "per_transaction_limit": 100.0,
  "allowed_resources": ["books", "music"],
  "allowed_categories": ["books", "music"],
  "witness_threshold": 50.0
}
```

Response:
```json
{
  "success": true,
  "delegation_id": "del-abc123...",
  "message": "Delegation created successfully"
}
```

### `GET /api/delegations`
Get all delegations (active and revoked)

Response:
```json
[
  {
    "delegation_id": "del-abc123...",
    "agent_name": "Claude Assistant",
    "agent_id": "agent-claude-42",
    "daily_budget": 500.0,
    "per_transaction_limit": 100.0,
    "allowed_resources": ["books", "music"],
    "allowed_categories": ["books", "music"],
    "witness_threshold": 50.0,
    "status": "active",
    "created_at": "2025-11-11T08:00:00Z",
    "spent_today": 75.0
  }
]
```

### `POST /api/delegations/{delegation_id}/revoke`
Revoke a delegation

Response:
```json
{
  "success": true,
  "message": "Delegation revoked"
}
```

### `GET /api/approvals`
Get pending approvals

Response:
```json
[
  {
    "approval_id": "app-xyz789...",
    "agent_name": "Claude Assistant",
    "item_description": "The Pragmatic Programmer (Book)",
    "amount": 75.0,
    "reason": "Purchase exceeds witness threshold ($50)"
  }
]
```

### `POST /api/approvals/respond`
Approve or deny a pending approval

Request:
```json
{
  "approval_id": "app-xyz789...",
  "approved": true,
  "reason": "Educational material approved"
}
```

Response:
```json
{
  "success": true,
  "approved": true
}
```

## User Experience Flow

### 1. Create Delegation
```
User visits http://localhost:8001
  → Clicks "Create Delegation" tab (default)
  → Fills in agent name: "Claude Assistant"
  → Fills in agent ID: "agent-claude-42"
  → Drags daily budget slider to $500
  → Drags per-transaction limit slider to $100
  → Checks "Books" and "Music" resource boxes
  → Sets witness threshold to $50 (require approval for purchases over $50)
  → Clicks "Create Delegation" button
  → Success message appears
  → Automatically switches to "Manage Delegations" tab
```

### 2. Monitor Activity
```
User clicks "Manage Delegations" tab
  → Sees delegation card for Claude Assistant
  → Status badge shows "Active"
  → Stats show: $500 daily, $100 per-tx, $75 spent, $425 remaining
  → Progress bar shows 15% (75/500)
  → Allowed resources: books, music
  → Revoke button available
```

### 3. Handle Approval Request
```
Agent attempts to purchase $75 book
  → Exceeds witness threshold ($50)
  → User gets notification (future: push notification)
  → User clicks "Pending Approvals" tab
  → Sees approval card:
      - Agent: Claude Assistant
      - Item: The Pragmatic Programmer (Book)
      - Amount: $75
      - Reason: Purchase exceeds witness threshold ($50)
  → User clicks "Approve" button
  → Purchase proceeds
  → Dashboard updates: $150 spent, $350 remaining
```

### 4. Revoke Access
```
User decides to revoke agent access
  → Clicks "Manage Delegations" tab
  → Finds delegation card
  → Clicks "Revoke Access" button
  → Confirmation dialog appears
  → Confirms revocation
  → Status badge changes to "Revoked"
  → Revoke button disappears
  → Agent can no longer make purchases
```

## Design Highlights

### Visual Language
- **Purple gradient** (#667eea → #764ba2) for primary actions and trust
- **White cards** with subtle shadows for content
- **Green** for active/approved states
- **Red** for revoked/denied states
- **Orange** for pending approvals
- **Clean typography** (system fonts for native feel)

### Interactive Elements
- **Sliders with live values** - Budget amounts update as you drag
- **Hover effects** - Buttons lift slightly on hover
- **Progress bars** - Smooth animations as spending updates
- **Responsive grid** - Adapts to screen size
- **Empty states** - Friendly messages when no data

### User Experience
- **No page reloads** - All actions use AJAX
- **Immediate feedback** - Success/error alerts
- **Visual consistency** - Same design language throughout
- **Clear hierarchy** - Important info stands out
- **Accessible** - High contrast, clear labels

## Configuration

### Change Default Budget Limits
Edit the slider ranges in `app.py` (lines ~425-432):

```python
# Daily budget slider
<input type="range" id="daily-budget"
       min="0" max="2000" step="50" value="500">

# Per-transaction slider
<input type="range" id="per-tx-limit"
       min="0" max="500" step="10" value="100">
```

### Add More Resource Options
Edit the checkbox grid in `app.py` (lines ~437-462):

```python
<div class="checkbox-item">
    <input type="checkbox" id="res-your-resource" value="your-resource">
    <label for="res-your-resource">🎯 Your Resource</label>
</div>
```

### Change Port
Edit the startup code in `app.py` (line ~842):

```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change 8001 to your port
```

## Integration with Demo Store

The delegation UI creates delegations that can be used with the Demo Store:

1. **Create delegation** in Delegation UI (http://localhost:8001)
   - Set agent ID: `agent-claude-demo`
   - Set allowed resources: `books`, `music`
   - Set daily limit: $500
   - Set per-tx limit: $100

2. **Start Demo Store** (http://localhost:8000)
   - Agent makes purchase requests
   - Web4 Verifier checks against delegation
   - Financial Binding enforces limits
   - Purchase succeeds if authorized

3. **Monitor in Delegation UI**
   - Spending updates in real-time
   - Approve high-value purchases
   - Revoke if needed

## Production Deployment

For production use:

### 1. Database Integration
Replace in-memory storage with database:
```python
# Current (demo)
delegations_db: Dict[str, dict] = {}

# Production
from sqlalchemy import create_engine
from models import Delegation

delegations = session.query(Delegation).all()
```

### 2. Authentication
Add user authentication:
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/api/delegations")
async def get_delegations(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    return user.delegations
```

### 3. Real-Time Updates
Add WebSocket for live updates:
```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Send spending updates
        await websocket.send_json(get_delegation_status())
```

### 4. Push Notifications
Integrate approval notifications:
```python
from firebase_admin import messaging

def send_approval_request(user_id: str, approval: dict):
    message = messaging.Message(
        notification=messaging.Notification(
            title=f"{approval['agent_name']} needs approval",
            body=f"${approval['amount']} purchase"
        ),
        token=user_tokens[user_id]
    )
    messaging.send(message)
```

### 5. Security Hardening
- HTTPS only (TLS/SSL certificates)
- CSRF protection
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection

### 6. Monitoring & Logging
```python
import logging
from prometheus_client import Counter

delegation_created = Counter('delegations_created_total', 'Total delegations created')
delegation_revoked = Counter('delegations_revoked_total', 'Total delegations revoked')

@app.post("/api/delegations")
async def create_delegation(request: CreateDelegationRequest):
    delegation_created.inc()
    logger.info(f"Delegation created: {delegation_id}")
    # ... rest of implementation
```

## Testing

### Manual Testing
```bash
# Start the server
python app.py

# In browser, visit http://localhost:8001
# 1. Create delegation
# 2. Check it appears in "Manage Delegations"
# 3. Test revocation
# 4. Check "Pending Approvals" section
```

### API Testing
```bash
# Create delegation
curl -X POST http://localhost:8001/api/delegations \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "Test Agent",
    "agent_id": "agent-test-001",
    "daily_budget": 1000.0,
    "per_transaction_limit": 200.0,
    "allowed_resources": ["books", "music"],
    "allowed_categories": ["books", "music"],
    "witness_threshold": 100.0
  }'

# Get delegations
curl http://localhost:8001/api/delegations

# Revoke delegation
curl -X POST http://localhost:8001/api/delegations/del-abc123.../revoke
```

### Automated Testing
```bash
# Add pytest tests (future)
pytest tests/test_delegation_ui.py
```

## Troubleshooting

**Port already in use**:
```bash
# Find process on port 8001
lsof -i :8001

# Kill it
kill -9 <PID>

# Or change port in app.py
```

**Module not found**:
```bash
# Install dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

**Import errors from Web4 components**:
```bash
# Ensure you're running from demo/delegation-ui directory
cd demo/delegation-ui
python app.py

# The sys.path manipulation in app.py handles the rest
```

**Browser console errors**:
- Check browser developer console (F12)
- Verify API endpoints are responding
- Check CORS settings if accessing from different domain

## Future Enhancements

### Short Term
- [ ] Activity log implementation
- [ ] Export delegation configs as JSON
- [ ] Import existing delegations
- [ ] Batch operations (revoke multiple)
- [ ] Delegation templates

### Medium Term
- [ ] Mobile responsive design
- [ ] Dark mode
- [ ] Multi-language support
- [ ] Delegation sharing (let others use your agent)
- [ ] Spending analytics and charts

### Long Term
- [ ] Mobile app (React Native)
- [ ] Browser extension
- [ ] Voice control ("Revoke Claude's access")
- [ ] AI-powered spending insights
- [ ] Delegation marketplace

## License

MIT License - See project root for details

## Author

Built by Claude (Anthropic AI) - Autonomous Development
Date: November 11, 2025

Part of the Web4 project demonstrating AI agent authorization for commerce.

## Related Components

- **Demo Store** (`../store/`) - E-commerce store using Web4 authorization
- **Financial Binding** (`../../implementation/reference/financial_binding.py`) - Payment limits
- **Resource Constraints** (`../../implementation/reference/resource_constraints.py`) - Scope control
- **Vendor SDK** (`../../implementation/reference/vendor_sdk.py`) - Merchant integration
- **ATP Tracker** (`../../implementation/reference/atp_tracker.py`) - Trust points
- **Witness Enforcer** (`../../implementation/reference/witness_enforcer.py`) - Approvals

---

**The complete user experience for AI agent delegation!** 🚀
