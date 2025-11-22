"""
Web4 Demo E-Commerce Store

Simple bookstore demonstrating Web4 agent authorization.
Shows complete purchase flow with all security checks.

Features:
- Product catalog (books, music, digital content)
- Web4 authorization integration
- Agent purchase flow
- Activity dashboard
- Witness approval for high-value items

Run:
    python app.py

Then visit: http://localhost:8000

Author: Claude (Anthropic AI), autonomous development
Date: November 10, 2025
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timezone
import json

# Import Web4 components (from parent directory)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "implementation" / "reference"))

from vendor_sdk import Web4Verifier, VerificationStatus
from atp_tracker import ATPTracker
from revocation_registry import RevocationRegistry
from nonce_tracker import NonceTracker
from timestamp_validator import TimestampValidator
from key_rotation import KeyRotationManager
from witness_enforcer import WitnessEnforcer
from resource_constraints import ResourceConstraints, PermissionLevel
from financial_binding import FinancialBinding, PaymentMethod, PaymentMethodType
from t3_tracker import T3Tracker


# Initialize FastAPI app
app = FastAPI(title="Web4 Demo Store", version="1.0.0")


# ============================================================================
# PRODUCT CATALOG
# ============================================================================

PRODUCTS = {
    "book-001": {
        "id": "book-001",
        "name": "Introduction to Machine Learning",
        "category": "books",
        "price": Decimal("79.99"),
        "description": "Comprehensive guide to ML fundamentals",
        "image_url": "/static/ml-book.jpg"
    },
    "book-002": {
        "id": "book-002",
        "name": "Python Programming Bible",
        "category": "books",
        "price": Decimal("45.00"),
        "description": "Complete Python reference",
        "image_url": "/static/python-book.jpg"
    },
    "book-003": {
        "id": "book-003",
        "name": "Web4 Specification",
        "category": "books",
        "price": Decimal("29.99"),
        "description": "Official Web4 protocol documentation",
        "image_url": "/static/web4-book.jpg"
    },
    "music-001": {
        "id": "music-001",
        "name": "Classical Favorites Album",
        "category": "music",
        "price": Decimal("12.99"),
        "description": "50 timeless classical pieces",
        "image_url": "/static/classical-album.jpg"
    },
    "music-002": {
        "id": "music-002",
        "name": "Jazz Standards Collection",
        "category": "music",
        "price": Decimal("15.99"),
        "description": "Best of jazz music",
        "image_url": "/static/jazz-album.jpg"
    },
    "digital-001": {
        "id": "digital-001",
        "name": "Premium API Access (1 month)",
        "category": "digital",
        "price": Decimal("99.00"),
        "description": "Monthly API subscription",
        "image_url": "/static/api-key.jpg"
    }
}


# ============================================================================
# WEB4 COMPONENTS INITIALIZATION
# ============================================================================

# Initialize all security components
atp_tracker = ATPTracker()
revocation_registry = RevocationRegistry()
nonce_tracker = NonceTracker()
timestamp_validator = TimestampValidator()
key_rotation_manager = KeyRotationManager()
witness_enforcer = WitnessEnforcer()

# T3 tracker for demo agent reputation
t3_tracker = T3Tracker(storage_path="demo_t3_profiles.json")

# Setup demo agent "Claude"
DEMO_AGENT_ID = "agent-claude-demo"
DEMO_USER_ID = "user-alice-demo"

# Create ATP account for demo agent
atp_tracker.create_account(
    DEMO_AGENT_ID,
    daily_limit=1000,
    per_action_limit=100
)

# Create resource constraints (what agent can access)
demo_constraints = ResourceConstraints()
demo_constraints.add_allowed("demostore.com:products/books/*")
demo_constraints.add_allowed("demostore.com:products/music/*")
demo_constraints.add_denied("demostore.com:products/digital/*")  # No digital goods

# Create financial binding
demo_card = PaymentMethod(
    method_type=PaymentMethodType.CREDIT_CARD,
    identifier="4242",
    provider="Demo Visa",
    holder_name="Alice Smith (Demo)"
)

demo_binding = FinancialBinding(
    lct_id=DEMO_AGENT_ID,
    payment_method=demo_card,
    daily_limit=Decimal("500.00"),
    per_transaction_limit=Decimal("100.00"),
    allowed_merchants=["demostore.com"],
    allowed_categories=["books", "music"]
)

# Create Web4 verifier with T3 trust integration
verifier = Web4Verifier(
    atp_tracker=atp_tracker,
    revocation_registry=revocation_registry,
    nonce_tracker=nonce_tracker,
    timestamp_validator=timestamp_validator,
    key_rotation_manager=key_rotation_manager,
    witness_enforcer=witness_enforcer,
    resource_constraints_registry={DEMO_USER_ID: demo_constraints},
    financial_binding_registry={DEMO_AGENT_ID: demo_binding},
    t3_tracker=t3_tracker,
    min_trust_threshold=0.0,  # Do not hard-fail on trust in the demo, just track it
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PurchaseRequest(BaseModel):
    """Purchase request from agent."""
    product_id: str
    lct_chain: dict
    nonce: Optional[str] = None


class PurchaseResponse(BaseModel):
    """Purchase response."""
    success: bool
    message: str
    verification_result: Optional[dict] = None
    charge_id: Optional[str] = None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Web4 Demo Store</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }
            .product-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }
            .product-card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .product-card h3 {
                margin-top: 0;
            }
            .price {
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
            }
            .category {
                background: #f0f0f0;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                display: inline-block;
                margin-bottom: 10px;
            }
            .buy-button {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                width: 100%;
                margin-top: 10px;
            }
            .buy-button:hover {
                background: #5568d3;
            }
            .info-box {
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }
            .nav {
                display: flex;
                gap: 20px;
                margin-top: 20px;
            }
            .nav a {
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                background: rgba(255,255,255,0.2);
                border-radius: 6px;
            }
            .nav a:hover {
                background: rgba(255,255,255,0.3);
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛍️ Web4 Demo Store</h1>
            <p>AI Agent Authorization Demonstration</p>
            <div class="nav">
                <a href="/">Products</a>
                <a href="/dashboard">Dashboard</a>
                <a href="/docs">API Docs</a>
            </div>
        </div>

        <div class="info-box">
            <strong>👋 Welcome!</strong> This demo showcases Web4 agent authorization.
            The agent "Claude" can purchase items with enforced limits and full audit trail.
            <br><br>
            <strong>Agent Limits:</strong> $500/day, $100/transaction, books and music only (no digital goods)
        </div>

        <div id="products" class="product-grid"></div>

        <script>
            async function loadProducts() {
                const response = await fetch('/api/products');
                const products = await response.json();

                const grid = document.getElementById('products');
                grid.innerHTML = products.map(p => `
                    <div class="product-card">
                        <span class="category">${p.category}</span>
                        <h3>${p.name}</h3>
                        <p>${p.description}</p>
                        <div class="price">$${p.price}</div>
                        <button class="buy-button" onclick="buyProduct('${p.id}')">
                            🤖 Agent Purchase
                        </button>
                    </div>
                `).join('');
            }

            async function buyProduct(productId) {
                try {
                    const response = await fetch('/api/purchase', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            product_id: productId,
                            lct_chain: {
                                delegator: 'user-alice-demo',
                                delegatee: 'agent-claude-demo',
                                delegation_timestamp: new Date().toISOString()
                            }
                        })
                    });

                    const result = await response.json();

                    if (result.success) {
                        alert('✅ Purchase successful! ' + result.message);
                        window.location.href = '/dashboard';
                    } else {
                        alert('❌ Purchase denied: ' + result.message);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            loadProducts();
        </script>
    </body>
    </html>
    """


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Activity dashboard."""
    # Get spending info
    spent = demo_binding.get_daily_spending()
    remaining = demo_binding.get_remaining_daily()
    by_merchant = demo_binding.get_spending_by_merchant()
    recent = demo_binding.get_charge_history(limit=10)

    # Get ATP info
    atp_account = atp_tracker.accounts.get(DEMO_AGENT_ID)
    atp_remaining = atp_account.remaining_today() if atp_account else 0

    # Get T3 trust statistics for demo agent (if any)
    t3_stats = t3_tracker.get_stats(DEMO_AGENT_ID)
    if t3_stats:
        t3_scores = t3_stats["t3_scores"]
        t3_statistics = t3_stats["statistics"]
    else:
        t3_scores = {
            "talent": 0.5,
            "training": 0.0,
            "temperament": 0.5,
            "composite": 0.0,
        }
        t3_statistics = {
            "total_transactions": 0,
            "successful_transactions": 0,
            "success_rate": 0.0,
            "constraint_violations": 0,
            "constraint_adherence_rate": 0.0,
            "total_value_handled": 0.0,
            "experience_level": 0.0,
        }

    charges_html = ""
    for charge in recent:
        status_icon = "✅" if charge.status.value == "completed" else "❌"
        charges_html += f"""
        <div style="padding: 15px; border-bottom: 1px solid #eee;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{charge.description}</strong><br>
                    <small style="color: #666;">{charge.timestamp[:19]} at {charge.merchant}</small>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 20px; font-weight: bold;">${charge.amount}</div>
                    <div>{status_icon} {charge.status.value}</div>
                </div>
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Web4 Demo Store</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .stat {{
                font-size: 36px;
                font-weight: bold;
                color: #667eea;
            }}
            .progress-bar {{
                background: #f0f0f0;
                height: 30px;
                border-radius: 15px;
                overflow: hidden;
                margin: 10px 0;
            }}
            .progress-fill {{
                background: linear-gradient(90deg, #667eea, #764ba2);
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
            }}
            .nav {{
                display: flex;
                gap: 20px;
                margin-top: 20px;
            }}
            .nav a {{
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                background: rgba(255,255,255,0.2);
                border-radius: 6px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Agent Activity Dashboard</h1>
            <p>Real-time monitoring of Claude's purchases</p>
            <div class="nav">
                <a href="/">Products</a>
                <a href="/dashboard">Dashboard</a>
                <a href="/docs">API Docs</a>
            </div>
        </div>

        <div class="card">
            <h2>💰 Daily Budget</h2>
            <div class="stat">${spent} / $500.00</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {float(spent)/500.0*100}%">
                    {float(spent)/500.0*100:.0f}%
                </div>
            </div>
            <p style="color: #666;">Remaining today: ${remaining}</p>
        </div>

        <div class="card">
            <h2>⚡ ATP Budget</h2>
            <div class="stat">{atp_remaining} ATP</div>
            <p style="color: #666;">Adaptive Trust Points remaining</p>
        </div>

        <div class="card">
            <h2>🎯 Agent Trust (T3)</h2>
            <p style="color: #666; margin-bottom: 10px;">Trust tensor for demo agent based on transaction history.</p>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
                <div class="stat-box">
                    <div class="stat-label">Talent</div>
                    <div class="stat-value">{t3_scores["talent"]:.2f}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Training</div>
                    <div class="stat-value">{t3_scores["training"]:.2f}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Temperament</div>
                    <div class="stat-value">{t3_scores["temperament"]:.2f}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Composite</div>
                    <div class="stat-value">{t3_scores["composite"]:.2f}</div>
                </div>
            </div>
            <p style="color: #666; margin-top: 10px; font-size: 14px;">
                {t3_statistics["total_transactions"]} transactions,
                {t3_statistics["successful_transactions"]} successful,
                success rate {(t3_statistics["success_rate"] * 100):.0f}%
            </p>
        </div>

        <div class="card">
            <h2>📝 Recent Activity</h2>
            {charges_html if charges_html else '<p style="color: #666;">No purchases yet</p>'}
        </div>

        <div class="card">
            <h2>🔒 Security Status</h2>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                <div style="padding: 10px; background: #e8f5e9; border-radius: 6px;">
                    ✅ Resource Constraints Active<br>
                    <small style="color: #666;">Books & music only</small>
                </div>
                <div style="padding: 10px; background: #e8f5e9; border-radius: 6px;">
                    ✅ Financial Limits Enforced<br>
                    <small style="color: #666;">$100/transaction max</small>
                </div>
                <div style="padding: 10px; background: #e8f5e9; border-radius: 6px;">
                    ✅ ATP Budget Tracked<br>
                    <small style="color: #666;">{atp_remaining} ATP remaining</small>
                </div>
                <div style="padding: 10px; background: #e8f5e9; border-radius: 6px;">
                    ✅ Replay Prevention Active<br>
                    <small style="color: #666;">Nonce-based protection</small>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/api/products")
async def get_products():
    """Get product catalog."""
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "price": str(p["price"]),
            "description": p["description"]
        }
        for p in PRODUCTS.values()
    ]


@app.post("/api/purchase")
async def purchase(request: PurchaseRequest):
    """
    Process agent purchase with Web4 authorization.

    This is the main integration point showing all security checks.
    """
    try:
        # Get product
        product = PRODUCTS.get(request.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Build resource ID
        resource_id = f"demostore.com:products/{product['category']}/{product['id']}"

        # Generate nonce for this request
        nonce = nonce_tracker.generate_nonce(DEMO_AGENT_ID)

        # Verify authorization (this does ALL security checks)
        result = verifier.verify_authorization(
            lct_chain=request.lct_chain,
            resource_id=resource_id,
            permission_level=PermissionLevel.WRITE,
            amount=product["price"],
            merchant="demostore.com",
            nonce=nonce,
            description=f"Purchase: {product['name']}"
        )

        if not result.authorized:
            return PurchaseResponse(
                success=False,
                message=result.denial_reason or "Authorization denied",
                verification_result=result.to_dict()
            )

        # Authorization successful - record purchase and update T3 reputation
        verifier.record_purchase(
            delegatee_id=DEMO_AGENT_ID,
            amount=product["price"],
            merchant="demostore.com",
            item_id=product["id"],
            category=product["category"],
            success=True,
            within_constraints=True,
            quality_score=0.9,
        )

        # Get the latest charge from financial binding for response
        latest_charge = demo_binding.get_charge_history(limit=1)[0]

        return PurchaseResponse(
            success=True,
            message=f"Purchase successful! Bought {product['name']} for ${product['price']}",
            verification_result=result.to_dict(),
            charge_id=latest_charge.charge_id
        )

    except Exception as e:
        return PurchaseResponse(
            success=False,
            message=f"Error: {str(e)}"
        )


@app.get("/api/dashboard-data")
async def dashboard_data():
    """Get dashboard data as JSON, including T3 trust stats."""
    spent = demo_binding.get_daily_spending()
    remaining = demo_binding.get_remaining_daily()
    recent = demo_binding.get_charge_history(limit=10)

    atp_account = atp_tracker.accounts.get(DEMO_AGENT_ID)
    atp_remaining = atp_account.remaining_today() if atp_account else 0

    t3_stats = t3_tracker.get_stats(DEMO_AGENT_ID)

    return {
        "financial": {
            "spent": str(spent),
            "remaining": str(remaining),
            "daily_limit": "500.00",
            "per_transaction_limit": "100.00"
        },
        "atp": {
            "remaining": atp_remaining,
            "daily_limit": 1000
        },
        "t3": t3_stats,
        "recent_charges": [
            {
                "timestamp": c.timestamp,
                "amount": str(c.amount),
                "merchant": c.merchant,
                "description": c.description,
                "status": c.status.value
            }
            for c in recent
        ]
    }


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*70)
    print("🛍️  Web4 Demo Store Starting")
    print("="*70)
    print("\nAccess the demo at: http://localhost:8000")
    print("\nEndpoints:")
    print("  - Home: http://localhost:8000")
    print("  - Dashboard: http://localhost:8000/dashboard")
    print("  - API Docs: http://localhost:8000/docs")
    print("\nDemo Agent: Claude")
    print("  - Daily limit: $500")
    print("  - Per-transaction: $100")
    print("  - Allowed: books, music")
    print("  - Denied: digital goods")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
