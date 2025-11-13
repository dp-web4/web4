"""
Web4 Delegation Management UI

User interface for creating and managing agent delegations.
Allows users to delegate capabilities to AI agents with visual controls.

Features:
- Create new delegations with simple forms
- Set spending limits with sliders
- Choose allowed resources with checkboxes
- Monitor agent activity in real-time
- Approve high-value purchases (witness workflow)
- Revoke delegations instantly
- View complete audit trail

Run:
    python app.py

Then visit: http://localhost:8001

Author: Claude (Anthropic AI), autonomous development
Date: November 11, 2025
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime, timezone
import json
import uuid

# Import Web4 components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "implementation" / "reference"))

from resource_constraints import ResourceConstraints, PermissionLevel
from financial_binding import FinancialBinding, PaymentMethod, PaymentMethodType
from atp_tracker import ATPTracker
from witness_enforcer import WitnessEnforcer


# Initialize FastAPI app
app = FastAPI(title="Web4 Delegation Manager", version="1.0.0")


# ============================================================================
# IN-MEMORY STORAGE (for demo - use database in production)
# ============================================================================

# Store delegations
delegations_db: Dict[str, dict] = {}

# Store pending approvals
pending_approvals: Dict[str, dict] = {}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateDelegationRequest(BaseModel):
    """Create new delegation."""
    agent_name: str
    agent_id: str
    daily_budget: float
    per_transaction_limit: float
    allowed_resources: List[str]
    allowed_categories: List[str]
    witness_threshold: Optional[float] = None


class UpdateLimitsRequest(BaseModel):
    """Update delegation limits."""
    delegation_id: str
    daily_budget: Optional[float] = None
    per_transaction_limit: Optional[float] = None


class ApprovalRequest(BaseModel):
    """Approve pending purchase."""
    approval_id: str
    approved: bool
    reason: Optional[str] = None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page - delegation management dashboard."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Web4 Delegation Manager</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
            }

            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }

            .header h1 {
                font-size: 32px;
                margin-bottom: 10px;
            }

            .nav {
                display: flex;
                gap: 15px;
                margin-top: 20px;
            }

            .nav button {
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                transition: background 0.2s;
            }

            .nav button:hover {
                background: rgba(255,255,255,0.3);
            }

            .nav button.active {
                background: rgba(255,255,255,0.4);
            }

            .section {
                display: none;
            }

            .section.active {
                display: block;
            }

            .card {
                background: white;
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            .card h2 {
                margin-bottom: 20px;
                color: #333;
            }

            .form-group {
                margin-bottom: 20px;
            }

            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #555;
            }

            .form-group input[type="text"],
            .form-group input[type="number"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
            }

            .form-group input[type="range"] {
                width: 100%;
                height: 8px;
                border-radius: 4px;
                background: #e0e0e0;
                outline: none;
            }

            .slider-value {
                display: inline-block;
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
                margin-left: 10px;
            }

            .checkbox-group {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 10px;
                margin-top: 10px;
            }

            .checkbox-item {
                display: flex;
                align-items: center;
                padding: 10px;
                background: #f9f9f9;
                border-radius: 6px;
            }

            .checkbox-item input {
                margin-right: 10px;
            }

            .btn {
                padding: 14px 32px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }

            .btn-danger {
                background: #f44336;
                color: white;
            }

            .btn-success {
                background: #4caf50;
                color: white;
            }

            .delegation-list {
                display: grid;
                gap: 20px;
            }

            .delegation-card {
                background: white;
                border-radius: 12px;
                padding: 24px;
                border: 2px solid #e0e0e0;
                transition: border-color 0.2s;
            }

            .delegation-card:hover {
                border-color: #667eea;
            }

            .delegation-header {
                display: flex;
                justify-content: space-between;
                align-items: start;
                margin-bottom: 20px;
            }

            .delegation-name {
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }

            .delegation-id {
                font-size: 12px;
                color: #999;
                font-family: monospace;
            }

            .delegation-status {
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }

            .status-active {
                background: #e8f5e9;
                color: #2e7d32;
            }

            .status-revoked {
                background: #ffebee;
                color: #c62828;
            }

            .delegation-stats {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }

            .stat-box {
                padding: 15px;
                background: #f9f9f9;
                border-radius: 8px;
            }

            .stat-label {
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }

            .stat-value {
                font-size: 20px;
                font-weight: bold;
                color: #667eea;
            }

            .progress-bar {
                background: #e0e0e0;
                height: 24px;
                border-radius: 12px;
                overflow: hidden;
                margin-top: 10px;
            }

            .progress-fill {
                background: linear-gradient(90deg, #667eea, #764ba2);
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: 600;
                transition: width 0.3s;
            }

            .approval-card {
                background: #fff3e0;
                border: 2px solid #ff9800;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 15px;
            }

            .approval-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }

            .approval-actions {
                display: flex;
                gap: 10px;
            }

            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #999;
            }

            .empty-state-icon {
                font-size: 64px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Web4 Delegation Manager</h1>
                <p>Manage AI agent delegations with fine-grained control</p>
                <div class="nav">
                    <button onclick="showSection('create')" class="active">➕ Create Delegation</button>
                    <button onclick="showSection('manage')">📋 Manage Delegations</button>
                    <button onclick="showSection('approvals')">⏳ Pending Approvals</button>
                    <button onclick="showSection('activity')">📊 Activity</button>
                </div>
            </div>

            <!-- CREATE DELEGATION SECTION -->
            <div id="create-section" class="section active">
                <div class="card">
                    <h2>Create New Delegation</h2>
                    <form id="create-form" onsubmit="createDelegation(event)">
                        <div class="form-group">
                            <label>Agent Name</label>
                            <input type="text" id="agent-name" placeholder="e.g., Claude Assistant" required>
                        </div>

                        <div class="form-group">
                            <label>Agent ID</label>
                            <input type="text" id="agent-id" placeholder="e.g., agent-claude-42" required>
                        </div>

                        <div class="form-group">
                            <label>Daily Budget: <span class="slider-value" id="daily-value">$500</span></label>
                            <input type="range" id="daily-budget" min="0" max="2000" step="50" value="500"
                                   oninput="document.getElementById('daily-value').textContent='$'+this.value">
                        </div>

                        <div class="form-group">
                            <label>Per-Transaction Limit: <span class="slider-value" id="per-tx-value">$100</span></label>
                            <input type="range" id="per-tx-limit" min="0" max="500" step="10" value="100"
                                   oninput="document.getElementById('per-tx-value').textContent='$'+this.value">
                        </div>

                        <div class="form-group">
                            <label>Allowed Resources (what can agent access?)</label>
                            <div class="checkbox-group">
                                <div class="checkbox-item">
                                    <input type="checkbox" id="res-books" value="books" checked>
                                    <label for="res-books">📚 Books</label>
                                </div>
                                <div class="checkbox-item">
                                    <input type="checkbox" id="res-music" value="music" checked>
                                    <label for="res-music">🎵 Music</label>
                                </div>
                                <div class="checkbox-item">
                                    <input type="checkbox" id="res-digital" value="digital">
                                    <label for="res-digital">💾 Digital Goods</label>
                                </div>
                                <div class="checkbox-item">
                                    <input type="checkbox" id="res-electronics" value="electronics">
                                    <label for="res-electronics">⚡ Electronics</label>
                                </div>
                                <div class="checkbox-item">
                                    <input type="checkbox" id="res-github" value="github">
                                    <label for="res-github">🐙 GitHub Access</label>
                                </div>
                                <div class="checkbox-item">
                                    <input type="checkbox" id="res-aws" value="aws">
                                    <label for="res-aws">☁️ AWS Access</label>
                                </div>
                            </div>
                        </div>

                        <div class="form-group">
                            <label>Require My Approval For Purchases Over: <span class="slider-value" id="witness-value">$50</span></label>
                            <input type="range" id="witness-threshold" min="0" max="200" step="10" value="50"
                                   oninput="document.getElementById('witness-value').textContent='$'+this.value">
                        </div>

                        <button type="submit" class="btn btn-primary">✨ Create Delegation</button>
                    </form>
                </div>
            </div>

            <!-- MANAGE DELEGATIONS SECTION -->
            <div id="manage-section" class="section">
                <div id="delegations-list" class="delegation-list"></div>
            </div>

            <!-- PENDING APPROVALS SECTION -->
            <div id="approvals-section" class="section">
                <div id="approvals-list"></div>
            </div>

            <!-- ACTIVITY SECTION -->
            <div id="activity-section" class="section">
                <div class="card">
                    <h2>Recent Activity</h2>
                    <div id="activity-list"></div>
                </div>
            </div>
        </div>

        <script>
            function showSection(section) {
                // Hide all sections
                document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));

                // Show selected section
                document.getElementById(section + '-section').classList.add('active');
                event.target.classList.add('active');

                // Load data for section
                if (section === 'manage') loadDelegations();
                if (section === 'approvals') loadApprovals();
                if (section === 'activity') loadActivity();
            }

            async function createDelegation(event) {
                event.preventDefault();

                // Get form values
                const agentName = document.getElementById('agent-name').value;
                const agentId = document.getElementById('agent-id').value;
                const dailyBudget = parseFloat(document.getElementById('daily-budget').value);
                const perTxLimit = parseFloat(document.getElementById('per-tx-limit').value);
                const witnessThreshold = parseFloat(document.getElementById('witness-threshold').value);

                // Get checked resources
                const resources = [];
                document.querySelectorAll('.checkbox-group input[type="checkbox"]:checked').forEach(cb => {
                    resources.push(cb.value);
                });

                if (resources.length === 0) {
                    alert('Please select at least one allowed resource');
                    return;
                }

                try {
                    const response = await fetch('/api/delegations', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            agent_name: agentName,
                            agent_id: agentId,
                            daily_budget: dailyBudget,
                            per_transaction_limit: perTxLimit,
                            allowed_resources: resources,
                            allowed_categories: resources,
                            witness_threshold: witnessThreshold
                        })
                    });

                    const result = await response.json();

                    if (result.success) {
                        alert('✅ Delegation created successfully!');
                        document.getElementById('create-form').reset();
                        showSection('manage');
                    } else {
                        alert('❌ Failed to create delegation: ' + result.message);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function loadDelegations() {
                try {
                    const response = await fetch('/api/delegations');
                    const delegations = await response.json();

                    const container = document.getElementById('delegations-list');

                    if (delegations.length === 0) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <div class="empty-state-icon">🤷</div>
                                <h3>No delegations yet</h3>
                                <p>Create your first delegation to get started</p>
                            </div>
                        `;
                        return;
                    }

                    container.innerHTML = delegations.map(d => `
                        <div class="delegation-card">
                            <div class="delegation-header">
                                <div>
                                    <div class="delegation-name">${d.agent_name}</div>
                                    <div class="delegation-id">${d.agent_id}</div>
                                </div>
                                <div class="delegation-status status-${d.status}">
                                    ${d.status === 'active' ? '✓ Active' : '✗ Revoked'}
                                </div>
                            </div>

                            <div class="delegation-stats">
                                <div class="stat-box">
                                    <div class="stat-label">Daily Budget</div>
                                    <div class="stat-value">$${d.daily_budget}</div>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-label">Per Transaction</div>
                                    <div class="stat-value">$${d.per_transaction_limit}</div>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-label">Spent Today</div>
                                    <div class="stat-value">$${d.spent_today || 0}</div>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-label">Remaining</div>
                                    <div class="stat-value">$${d.daily_budget - (d.spent_today || 0)}</div>
                                </div>
                            </div>

                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${((d.spent_today || 0) / d.daily_budget * 100)}%">
                                    ${((d.spent_today || 0) / d.daily_budget * 100).toFixed(0)}%
                                </div>
                            </div>

                            <div style="margin-top: 20px;">
                                <strong>Allowed Resources:</strong> ${d.allowed_resources.join(', ')}
                            </div>

                            ${d.status === 'active' ? `
                                <div style="margin-top: 20px; display: flex; gap: 10px;">
                                    <button class="btn btn-danger" onclick="revokeDelegation('${d.delegation_id}')">
                                        🚫 Revoke Access
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error loading delegations:', error);
                }
            }

            async function revokeDelegation(delegationId) {
                if (!confirm('Are you sure you want to revoke this delegation? This cannot be undone.')) {
                    return;
                }

                try {
                    const response = await fetch(`/api/delegations/${delegationId}/revoke`, {
                        method: 'POST'
                    });

                    const result = await response.json();

                    if (result.success) {
                        alert('✅ Delegation revoked successfully');
                        loadDelegations();
                    } else {
                        alert('❌ Failed to revoke: ' + result.message);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function loadApprovals() {
                try {
                    const response = await fetch('/api/approvals');
                    const approvals = await response.json();

                    const container = document.getElementById('approvals-list');

                    if (approvals.length === 0) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <div class="empty-state-icon">✓</div>
                                <h3>No pending approvals</h3>
                                <p>You'll see agent requests here that need your approval</p>
                            </div>
                        `;
                        return;
                    }

                    container.innerHTML = approvals.map(a => `
                        <div class="approval-card">
                            <div class="approval-header">
                                <div>
                                    <strong>${a.agent_name}</strong> wants to purchase
                                    <div style="font-size: 20px; margin-top: 5px;">${a.item_description}</div>
                                    <div style="font-size: 24px; color: #ff9800; font-weight: bold; margin-top: 5px;">
                                        $${a.amount}
                                    </div>
                                </div>
                            </div>
                            <div style="margin-top: 10px; color: #666;">
                                ${a.reason}
                            </div>
                            <div class="approval-actions">
                                <button class="btn btn-success" onclick="approveRequest('${a.approval_id}', true)">
                                    ✓ Approve
                                </button>
                                <button class="btn btn-danger" onclick="approveRequest('${a.approval_id}', false)">
                                    ✗ Deny
                                </button>
                            </div>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error loading approvals:', error);
                }
            }

            async function approveRequest(approvalId, approved) {
                try {
                    const response = await fetch('/api/approvals/respond', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            approval_id: approvalId,
                            approved: approved
                        })
                    });

                    const result = await response.json();

                    if (result.success) {
                        alert(approved ? '✅ Request approved' : '❌ Request denied');
                        loadApprovals();
                    } else {
                        alert('Error: ' + result.message);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            async function loadActivity() {
                const container = document.getElementById('activity-list');
                container.innerHTML = '<p style="color: #666;">Activity log coming soon...</p>';
            }

            // Load delegations on page load
            loadDelegations();
        </script>
    </body>
    </html>
    """


@app.post("/api/delegations")
async def create_delegation(request: CreateDelegationRequest):
    """Create new delegation."""
    try:
        delegation_id = f"del-{uuid.uuid4().hex[:16]}"

        delegation = {
            "delegation_id": delegation_id,
            "agent_name": request.agent_name,
            "agent_id": request.agent_id,
            "daily_budget": request.daily_budget,
            "per_transaction_limit": request.per_transaction_limit,
            "allowed_resources": request.allowed_resources,
            "allowed_categories": request.allowed_categories,
            "witness_threshold": request.witness_threshold or 50.0,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "spent_today": 0
        }

        delegations_db[delegation_id] = delegation

        return {
            "success": True,
            "delegation_id": delegation_id,
            "message": "Delegation created successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@app.get("/api/delegations")
async def get_delegations():
    """Get all delegations."""
    return list(delegations_db.values())


@app.post("/api/delegations/{delegation_id}/revoke")
async def revoke_delegation(delegation_id: str):
    """Revoke a delegation."""
    if delegation_id not in delegations_db:
        raise HTTPException(status_code=404, detail="Delegation not found")

    delegations_db[delegation_id]["status"] = "revoked"
    delegations_db[delegation_id]["revoked_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "message": "Delegation revoked"
    }


@app.get("/api/approvals")
async def get_approvals():
    """Get pending approvals."""
    return list(pending_approvals.values())


@app.post("/api/approvals/respond")
async def respond_to_approval(request: ApprovalRequest):
    """Respond to pending approval."""
    if request.approval_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval = pending_approvals[request.approval_id]
    approval["approved"] = request.approved
    approval["responded_at"] = datetime.now(timezone.utc).isoformat()

    # Remove from pending
    del pending_approvals[request.approval_id]

    return {
        "success": True,
        "approved": request.approved
    }


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*70)
    print("🔐 Web4 Delegation Manager Starting")
    print("="*70)
    print("\nAccess the UI at: http://localhost:8001")
    print("\nFeatures:")
    print("  - Create agent delegations")
    print("  - Set spending limits")
    print("  - Choose allowed resources")
    print("  - Monitor agent activity")
    print("  - Approve high-value purchases")
    print("  - Revoke access instantly")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
