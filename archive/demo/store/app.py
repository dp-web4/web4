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
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime, timezone
import json
import requests

# Import Web4 components (from parent directory)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "implementation" / "reference"))

MEMORY_REPO_ROOT = Path(__file__).parent.parent.parent.parent / "memory"
sys.path.insert(0, str(MEMORY_REPO_ROOT))

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
from memory_lightchain_integration import MemoryLightchainNode
from lct_context import GLOBAL_CONTEXT_GRAPH


# Initialize FastAPI app
app = FastAPI(title="Web4 Demo Store", version="1.0.0")

# Allow the trust visualizer (and local dev tools) to call the JSON APIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

trust_memory_nodes: Dict[str, MemoryLightchainNode] = {}


def get_trust_memory_node(agent_id: str) -> MemoryLightchainNode:
    node = trust_memory_nodes.get(agent_id)
    if not node:
        node = MemoryLightchainNode(node_id="web4-demo-store", agent_id=agent_id)
        trust_memory_nodes[agent_id] = node
    return node


settlement_events: List[dict] = []


def record_settlement_event(
    *,
    society_lct: str,
    agent_lct: str,
    amount: Decimal,
    currency: str,
    product_id: str,
    category: str,
    description: str,
):
    """Record a minimal settlement event for potential ACT integration.

    This is an in-process stub that appends structured events to
    settlement_events. Future work can replace this with a real ACT
    client that posts these events to a society treasury module.
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    event = {
        "society_lct": society_lct,
        "agent_lct": agent_lct,
        "amount": float(amount),
        "currency": currency,
        "product_id": product_id,
        "category": category,
        "description": description,
        "timestamp": timestamp,
    }
    settlement_events.append(event)

    # Also project this settlement into the global LCT context graph using
    # a few simple, public-safe predicates. This is an in-process view
    # only; it does not change external behavior.
    try:
        mrh_profile = {
            "deltaR": "local",
            "deltaT": "session",
            "deltaC": "agent-scale",
        }
        # Agent participates in the demo society for this transaction.
        GLOBAL_CONTEXT_GRAPH.add_link(
            subject=agent_lct,
            predicate="web4:participantIn",
            object=society_lct,
            mrh=mrh_profile,
        )
        # Agent is contextually related to the product category.
        category_lct = f"lct:web4:category:{category}"
        GLOBAL_CONTEXT_GRAPH.add_link(
            subject=agent_lct,
            predicate="web4:relevantTo",
            object=category_lct,
            mrh=mrh_profile,
        )
    except Exception:
        # Context graph population is best-effort; never break settlement logging.
        pass


def should_apply_t3_high_value_gate(
    *,
    composite_trust: float,
    trust_threshold: float,
    price: Decimal,
    high_value_threshold: Decimal,
    already_allowed: bool,
) -> bool:
    """Decide whether the T3-based high-value gate should be applied.

    This encapsulates the demo policy that low-trust agents must obtain
    explicit approval for high-value purchases, while preserving existing
    behavior. Future work can swap this logic for a SAGE-driven policy
    module without changing the rest of the purchase flow.
    """
    if already_allowed:
        return False
    if composite_trust >= trust_threshold:
        return False
    if price < high_value_threshold:
        return False
    return True

# Setup demo agent "Claude" (default active agent)
DEMO_AGENT_ID = "agent-claude-demo"
DEMO_USER_ID = "user-alice-demo"

# Active agent for the store session (can be switched via API)
ACTIVE_AGENT_ID = DEMO_AGENT_ID

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

# Create financial binding with default limits (can be overridden by Delegation Manager)
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


class SetActiveAgentRequest(BaseModel):
    """Request to change the active agent for the demo store."""
    agent_id: str


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
            <div style="margin-top: 20px; display: flex; align-items: center; gap: 10px;">
                <label for="agent-select" style="font-weight: 500;">Active Agent:</label>
                <select id="agent-select" style="padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.6); background: rgba(255,255,255,0.9); min-width: 220px;"></select>
                <span id="agent-select-status" style="font-size: 12px; opacity: 0.9;"></span>
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
            let activeAgentId = null;

            async function loadAgents() {
                try {
                    const [agentsResp, activeResp] = await Promise.all([
                        fetch('/api/agents'),
                        fetch('/api/active-agent'),
                    ]);

                    const agents = await agentsResp.json();
                    const activeData = await activeResp.json();
                    activeAgentId = activeData.agent_id;

                    const select = document.getElementById('agent-select');
                    const status = document.getElementById('agent-select-status');

                    select.innerHTML = agents.map(a => `
                        <option value="${a.agent_id}" ${a.agent_id === activeAgentId ? 'selected' : ''}>
                            ${a.agent_name} (${a.agent_id})
                        </option>
                    `).join('');

                    select.onchange = async () => {
                        const newId = select.value;
                        try {
                            const resp = await fetch('/api/active-agent', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ agent_id: newId })
                            });
                            if (resp.ok) {
                                const data = await resp.json();
                                activeAgentId = data.agent_id;
                                status.textContent = '✓ Agent updated';
                            } else {
                                status.textContent = '⚠️ Failed to update agent';
                            }
                        } catch (e) {
                            status.textContent = '⚠️ Error updating agent';
                        }
                    };

                    status.textContent = 'Using agent ' + activeAgentId;
                } catch (e) {
                    const select = document.getElementById('agent-select');
                    const status = document.getElementById('agent-select-status');
                    select.innerHTML = '<option>agent-claude-demo</option>';
                    activeAgentId = 'agent-claude-demo';
                    status.textContent = '⚠️ Could not load agents; using default';
                }
            }

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
                    // Fallback in case agent metadata failed to load
                    if (!activeAgentId) {
                        try {
                            const activeResp = await fetch('/api/active-agent');
                            const activeData = await activeResp.json();
                            activeAgentId = activeData.agent_id || 'agent-claude-demo';
                        } catch (e) {
                            activeAgentId = 'agent-claude-demo';
                        }
                    }

                    const response = await fetch('/api/purchase', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            product_id: productId,
                            lct_chain: {
                                delegator: 'user-alice-demo',
                                delegatee: activeAgentId,
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

            loadAgents().then(loadProducts);
        </script>
    </body>
    </html>
    """


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Activity dashboard."""
    # Try to pull delegation limits from Delegation Manager for the active agent
    delegation_daily_limit = Decimal("500.00")
    delegation_per_tx_limit = Decimal("100.00")
    try:
        resp = requests.get(
            "http://localhost:8001/api/delegations/by-agent/" + ACTIVE_AGENT_ID,
            timeout=2.0,
        )
        if resp.ok:
            d = resp.json()
            delegation_daily_limit = Decimal(str(d.get("daily_budget", 500.0)))
            delegation_per_tx_limit = Decimal(str(d.get("per_transaction_limit", 100.0)))
            demo_binding.daily_limit = delegation_daily_limit
            demo_binding.per_transaction_limit = delegation_per_tx_limit
    except Exception:
        pass

    # Get spending info
    spent = demo_binding.get_daily_spending()
    remaining = demo_binding.get_remaining_daily()
    by_merchant = demo_binding.get_spending_by_merchant()
    recent = demo_binding.get_charge_history(limit=10)

    # Get ATP info for active agent
    atp_account = atp_tracker.accounts.get(ACTIVE_AGENT_ID)
    atp_remaining = atp_account.remaining_today() if atp_account else 0

    # Get T3 trust statistics for active agent (if any)
    t3_stats = t3_tracker.get_stats(ACTIVE_AGENT_ID)
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
        <div style=\"padding: 15px; border-bottom: 1px solid #eee;\">
            <div style=\"display: flex; justify-content: space-between; align-items: center;\">
                <div>
                    <strong>{charge.description}</strong><br>
                    <small style=\"color: #666;\">{charge.timestamp[:19]} at {charge.merchant}</small>
                </div>
                <div style=\"text-align: right;\">
                    <div style=\"font-size: 20px; font-weight: bold;\">${charge.amount}</div>
                    <div>{status_icon} {charge.status.value}</div>
                </div>
            </div>
        </div>
        """

    # Build a simple MRH/LCT context view for the active agent using the
    # in-process GLOBAL_CONTEXT_GRAPH. This is a read-only, best-effort
    # visualization of RDF-like triples associated with the agent.
    context_triples = GLOBAL_CONTEXT_GRAPH.neighbors(
        ACTIVE_AGENT_ID,
        direction="both",
        within_mrh={
            "deltaC": "agent-scale",
        },
    )
    context_html = ""
    for t in context_triples:
        mrh = t.get("mrh") or {}
        mrh_str = ", ".join(
            f"{k}={v}" for k, v in mrh.items()
        ) if mrh else "(no MRH)"
        context_html += f"""
        <div style=\"padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px;\">
            <div><strong>{t['subject']}</strong> <span style=\"color: #666;\">{t['predicate']}</span> <strong>{t['object']}</strong></div>
            <div style=\"color: #999; font-size: 12px;\">MRH: {mrh_str}</div>
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
            <div class="stat">${spent} / ${delegation_daily_limit}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {float(spent)/float(delegation_daily_limit)*100 if delegation_daily_limit else 0}%">
                    {float(spent)/float(delegation_daily_limit)*100 if delegation_daily_limit else 0:.0f}%
                </div>
            </div>
            <p style="color: #666;">Remaining today: ${remaining}</p>
        </div>

        <div class="card">
            <h2>⚡ ATP Budget</h2>
            <div class="stat">{atp_remaining} ATP</div>
            <p style="color: #666;">Allocation Transfer Packets remaining</p>
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
            <h2>🌐 MRH / LCT Context</h2>
            <p style="color: #666; margin-bottom: 10px; font-size: 14px;">
                RDF-like context triples for the active agent within the current MRH band
                (agent-scale complexity). This reflects recent settlements and category
                relationships only.
            </p>
            {context_html if context_html else '<p style="color: #666;">No context triples recorded yet</p>'}
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
                    <small style="color: #666;">${delegation_per_tx_limit}/transaction max</small>
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


@app.get("/api/context/agent/{agent_lct}")
async def get_agent_context(agent_lct: str):
    """Return a simple MRH-scoped context neighborhood for an agent LCT.

    This is a read-only introspection endpoint for the demo, exposing the
    RDF-like triples currently stored in the in-process GLOBAL_CONTEXT_GRAPH
    for a given agent.
    """

    triples = GLOBAL_CONTEXT_GRAPH.neighbors(
        agent_lct,
        direction="both",
        within_mrh={
            "deltaC": "agent-scale",
        },
    )
    return {"agent_lct": agent_lct, "triples": triples}


@app.get("/api/active-agent")
async def get_active_agent():
    """Return the current active agent ID for the demo store."""
    return {"agent_id": ACTIVE_AGENT_ID}


@app.post("/api/active-agent")
async def set_active_agent(request: SetActiveAgentRequest):
    """Set the active agent for the demo store session.

    This controls which delegation limits, T3 profile, and approvals are used
    when processing purchases and rendering the dashboard.
    """
    global ACTIVE_AGENT_ID
    ACTIVE_AGENT_ID = request.agent_id
    return {"success": True, "agent_id": ACTIVE_AGENT_ID}


@app.get("/api/agents")
async def list_agents():
    """List agents based on delegations in the Delegation Manager.

    This is a thin proxy to avoid CORS issues from the browser. Returns a
    de-duplicated list of {agent_id, agent_name} objects.
    """
    agents = {}
    try:
        resp = requests.get("http://localhost:8001/api/delegations", timeout=2.0)
        if resp.ok:
            for d in resp.json():
                aid = d.get("agent_id")
                if not aid:
                    continue
                if aid not in agents:
                    agents[aid] = {
                        "agent_id": aid,
                        "agent_name": d.get("agent_name", aid),
                    }
    except Exception:
        pass

    # Ensure the default demo agent is always present
    if DEMO_AGENT_ID not in agents:
        agents[DEMO_AGENT_ID] = {
            "agent_id": DEMO_AGENT_ID,
            "agent_name": "Claude (demo agent)",
        }

    return list(agents.values())


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
        nonce = nonce_tracker.generate_nonce(ACTIVE_AGENT_ID)

        # Verify authorization (this does ALL security checks except T3 policy)
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

        # Demo-local T3 policy: low-trust agents cannot make high-value purchases
        composite_trust = t3_tracker.get_composite_trust(ACTIVE_AGENT_ID) or 0.5
        trust_threshold = 0.3
        high_value_threshold = Decimal("75.00")

        # First, check if this specific purchase was already approved in Delegation Manager
        already_allowed = False
        try:
            resp = requests.get(
                "http://localhost:8001/api/approvals/allowed",
                params={
                    "agent_id": ACTIVE_AGENT_ID,
                    "item_id": product["id"],
                    "amount": float(product["price"]),
                },
                timeout=2.0,
            )
            if resp.ok:
                body = resp.json()
                already_allowed = bool(body.get("allowed"))
        except Exception:
            already_allowed = False

        if should_apply_t3_high_value_gate(
            composite_trust=composite_trust,
            trust_threshold=trust_threshold,
            price=product["price"],
            high_value_threshold=high_value_threshold,
            already_allowed=already_allowed,
        ):
            approval_id = None
            try:
                resp = requests.post(
                    "http://localhost:8001/api/approvals",
                    json={
                        "agent_name": "Claude (demo agent)",
                        "agent_id": DEMO_AGENT_ID,
                        "amount": float(product["price"]),
                        "item_id": product["id"],
                        "item_description": product["name"],
                        "reason": "Low trust score for high-value purchase",
                    },
                    timeout=2.0,
                )
                if resp.ok:
                    body = resp.json()
                    approval_id = body.get("approval_id")
            except Exception:
                approval_id = None

            base_msg = (
                f"Agent trust too low for high-value purchase. "
                f"Trust {composite_trust:.2f} < {trust_threshold:.2f} for items over ${high_value_threshold}. "
            )
            if approval_id:
                extra = f"Approval request created. Open the Delegation Manager to review (ID: {approval_id})."
            else:
                extra = "Open the Delegation Manager to review and approve this type of request."

            return PurchaseResponse(
                success=False,
                message=base_msg + extra,
                verification_result=result.to_dict(),
            )

        # Authorization successful and T3 policy satisfied - record purchase and update T3 reputation
        verifier.record_purchase(
            delegatee_id=ACTIVE_AGENT_ID,
            amount=product["price"],
            merchant="demostore.com",
            item_id=product["id"],
            category=product["category"],
            success=True,
            within_constraints=True,
            quality_score=0.9,
        )

        node = get_trust_memory_node(ACTIVE_AGENT_ID)
        node.create_memory(
            content=json.dumps(
                {
                    "agent_id": ACTIVE_AGENT_ID,
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "transaction_type": "purchase",
                    "product_id": product["id"],
                    "category": product["category"],
                    "amount": float(product["price"]),
                },
                sort_keys=True,
            ),
            type="trust_event",
            tags=["web4", "t3", "purchase", product["category"]],
        )
        node.create_memory_block(lct_id=ACTIVE_AGENT_ID)

        record_settlement_event(
            society_lct="lct:web4:society:demo",
            agent_lct=ACTIVE_AGENT_ID,
            amount=product["price"],
            currency="USD",
            product_id=product["id"],
            category=product["category"],
            description=f"Purchase settlement for {product['name']}",
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


@app.get("/api/t3/history")
async def t3_history(agent_id: str):
    """Return a simplified trust history for visualization.

    Maps the T3Tracker transaction history into a sequence of points with
    time index, value in [-1,1], certainty in [0,1], and an outcome label.
    """
    profile = t3_tracker.get_profile(agent_id)
    if not profile:
        return {"agent_id": agent_id, "history": []}

    history = profile.transaction_history or []
    points = []
    trust_value = 0.0
    certainty = 0.0

    for idx, rec in enumerate(history):
        success = rec.get("success", False)
        within_constraints = rec.get("within_constraints", True)

        if success and within_constraints:
            outcome = "positive"
        elif not success or not within_constraints:
            outcome = "negative"
        else:
            outcome = "neutral"

        # Very simple mapping: move toward +1 on positive, -1 on negative
        if outcome == "positive":
            trust_value += (1 - trust_value) * 0.3
        elif outcome == "negative":
            trust_value += (-1 - trust_value) * 0.5
        else:
            trust_value += (0 - trust_value) * 0.05

        trust_value = max(-1.0, min(1.0, trust_value))

        certainty += (1 - certainty) * 0.15
        certainty *= 0.99
        certainty = max(0.0, min(1.0, certainty))

        points.append(
            {
                "time": idx,
                "value": trust_value,
                "certainty": certainty,
                "outcome": outcome,
            }
        )

    return {"agent_id": agent_id, "history": points}


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
