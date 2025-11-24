from __future__ import annotations

"""Minimal read-only society view UI for the Web4 game (v0).

This FastAPI app bootstraps the two-society world and exposes:
- JSON APIs to inspect societies and their chains.
- A simple HTML page that renders basic information about societies,
  blocks, and MRH/LCT context.
"""

from typing import Dict, Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from engine.two_societies import bootstrap_two_societies_world
from engine.sim_loop import run_world
from engine.verify import verify_chain_structure, verify_stub_signatures


app = FastAPI(title="Web4 Society View", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Bootstrapped world (long-lived for demo purposes)
WORLD = bootstrap_two_societies_world()
# Run some ticks so membership/role events are sealed into blocks
run_world(WORLD, steps=20)


@app.get("/api/societies")
async def list_societies():
    items: list[Dict[str, Any]] = []
    for soc in WORLD.societies.values():
        struct = verify_chain_structure(soc)
        sigs = verify_stub_signatures(soc)
        items.append(
            {
                "society_lct": soc.society_lct,
                "name": soc.name,
                "treasury": soc.treasury,
                "block_count": struct["block_count"],
                "chain_valid": struct["valid"],
                "signature_ok": sigs["valid"],
            }
        )
    return JSONResponse(items)


@app.get("/api/planet")
async def planet_view():
    """Return a cross-society summary suitable for a planet-view panel."""

    # Build federation links.
    federation: Dict[str, set[str]] = {}
    for edge in WORLD.context_edges:
        if edge.predicate == "web4:federatesWith":
            federation.setdefault(edge.subject, set()).add(edge.object)

    items: list[Dict[str, Any]] = []
    for soc in WORLD.societies.values():
        struct = verify_chain_structure(soc)
        t_axes = (soc.trust_axes or {}).get("T3") or {}
        composite = float(t_axes.get("composite", 0.0))

        # Count suppression-like events.
        audits = 0
        role_rev = 0
        memb_rev = 0
        suppression = 0
        for b in soc.blocks:
            for ev in b.get("events", []):
                et = ev.get("type")
                if et == "audit_request":
                    audits += 1
                elif et == "role_revocation":
                    role_rev += 1
                elif et == "membership_revocation":
                    memb_rev += 1
                elif et in {"federation_throttle", "quarantine_request"}:
                    suppression += 1

        items.append(
            {
                "society_lct": soc.society_lct,
                "name": soc.name,
                "trust_composite": composite,
                "block_count": struct["block_count"],
                "chain_valid": struct["valid"],
                "audits": audits,
                "role_revocations": role_rev,
                "membership_revocations": memb_rev,
                "suppression_events": suppression,
                "federates_with": sorted(list(federation.get(soc.society_lct, set()))),
            }
        )

    return JSONResponse(items)


@app.get("/api/societies/{society_lct}")
async def get_society(society_lct: str):
    soc = WORLD.societies.get(society_lct)
    if not soc:
        return JSONResponse({"error": "not found"}, status_code=404)

    struct = verify_chain_structure(soc)
    sigs = verify_stub_signatures(soc)

    blocks: list[Dict[str, Any]] = []
    role_bindings: Dict[str, set[str]] = {}
    role_revocations: Dict[str, set[str]] = {}
    membership_revoked: set[str] = set()

    for b in soc.blocks[-20:]:  # last 20 blocks
        events = b.get("events", [])
        blocks.append(
            {
                "index": b.get("index"),
                "timestamp": b.get("timestamp"),
                "previous_hash": b.get("previous_hash"),
                "header_hash": b.get("header_hash"),
                "signature": b.get("signature"),
                "event_count": len(events),
                "events": events,
            }
        )

        # Derive simple role and membership status from recent events.
        for ev in events:
            etype = ev.get("type")
            if etype == "role_binding":
                subject = ev.get("subject_lct")
                role_lct = ev.get("role_lct")
                if subject and role_lct:
                    role_bindings.setdefault(subject, set()).add(role_lct)
            elif etype == "role_revocation":
                subject = ev.get("subject_lct")
                role_lct = ev.get("role_lct")
                if subject and role_lct:
                    role_revocations.setdefault(subject, set()).add(role_lct)
            elif etype == "membership_revocation":
                agent_lct = ev.get("agent_lct")
                if agent_lct:
                    membership_revoked.add(agent_lct)

    # Simple agent/role/membership summary
    agents: list[Dict[str, Any]] = []
    for agent in WORLD.agents.values():
        if society_lct not in agent.memberships:
            continue

        t3 = (agent.trust_axes or {}).get("T3") or {}
        composite = t3.get("composite", 0.0)

        bound_roles = role_bindings.get(agent.agent_lct, set())
        revoked_roles = role_revocations.get(agent.agent_lct, set())
        current_roles = sorted(list(bound_roles - revoked_roles))
        revoked_roles_list = sorted(list(revoked_roles))

        membership_status = "revoked" if agent.agent_lct in membership_revoked else "active"

        agents.append(
            {
                "agent_lct": agent.agent_lct,
                "name": agent.name,
                "trust_axes": agent.trust_axes,
                "composite_trust": composite,
                "resources": agent.resources,
                "memberships": agent.memberships,
                "current_roles": current_roles,
                "revoked_roles": revoked_roles_list,
                "membership_status": membership_status,
            }
        )

    return JSONResponse(
        {
            "society_lct": soc.society_lct,
            "name": soc.name,
            "treasury": soc.treasury,
            "policies": soc.policies,
            "verification": {
                "structure": struct,
                "signatures": sigs,
            },
            "blocks": blocks,
            "agents": agents,
        }
    )


@app.get("/")
async def home() -> HTMLResponse:
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Web4 Society View</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            h1 {
                margin-bottom: 10px;
            }
            .societies {
                display: flex;
                gap: 20px;
            }
            .society-list {
                width: 30%;
                background: white;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .society-details {
                flex: 1;
                background: white;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .society-item {
                padding: 8px;
                border-bottom: 1px solid #eee;
                cursor: pointer;
            }
            .society-item.selected {
                background: #e3f2fd;
            }
            pre {
                background: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
                overflow-x: auto;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 4px 6px;
                font-size: 12px;
            }
            th {
                background: #fafafa;
            }
        </style>
    </head>
    <body>
        <h1>Web4 Society View</h1>
        <p>Read-only view of Web4 societies, their chains, and agents.</p>
        <div class="societies">
            <div class="society-list">
                <h2>Societies</h2>
                <div id="society-list"></div>
            </div>
            <div class="society-details">
                <h2 id="society-name">Select a society</h2>
                <div id="society-meta"></div>
                <h3>Blocks</h3>
                <div id="blocks"></div>
                <h3>Agents</h3>
                <div id="agents"></div>
                <h3>Planet View</h3>
                <div id="planet"></div>
            </div>
        </div>

        <script>
            async function loadSocieties() {
                const resp = await fetch('/api/societies');
                const societies = await resp.json();
                const listEl = document.getElementById('society-list');
                listEl.innerHTML = '';
                societies.forEach(s => {
                    const div = document.createElement('div');
                    div.className = 'society-item';
                    div.textContent = s.name + ' (' + s.society_lct + ')';
                    div.onclick = () => selectSociety(s.society_lct, div);
                    listEl.appendChild(div);
                });
            }

            async function selectSociety(societyLct, el) {
                document.querySelectorAll('.society-item').forEach(x => x.classList.remove('selected'));
                el.classList.add('selected');

                const resp = await fetch('/api/societies/' + encodeURIComponent(societyLct));
                const data = await resp.json();

                document.getElementById('society-name').textContent = data.name + ' (' + data.society_lct + ')';

                const meta = document.getElementById('society-meta');
                meta.innerHTML = '';
                meta.innerHTML += '<p><strong>Treasury ATP:</strong> ' + (data.treasury.ATP || 0) + '</p>';
                meta.innerHTML += '<p><strong>Block count:</strong> ' + data.blocks.length + '</p>';
                meta.innerHTML += '<p><strong>Chain valid:</strong> ' + data.verification.structure.valid + '</p>';

                const blocksEl = document.getElementById('blocks');
                blocksEl.innerHTML = '';
                const table = document.createElement('table');
                table.innerHTML = '<tr><th>Index</th><th>Timestamp</th><th>Events</th></tr>';
                data.blocks.forEach(b => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = '<td>' + b.index + '</td>' +
                                   '<td>' + b.timestamp + '</td>' +
                                   '<td>' + b.event_count + '</td>';
                    table.appendChild(tr);
                });
                blocksEl.appendChild(table);

                const agentsEl = document.getElementById('agents');
                agentsEl.innerHTML = '';
                const at = document.createElement('table');
                at.innerHTML = '<tr><th>Name</th><th>LCT</th><th>ATP</th><th>Roles</th><th>Status</th><th>Trust</th></tr>';
                data.agents.forEach(a => {
                    const roles = (a.current_roles || []).join(', ');
                    const status = a.membership_status || 'unknown';
                    const trust = a.composite_trust != null ? a.composite_trust.toFixed(2) : '0.00';
                    const tr = document.createElement('tr');
                    tr.innerHTML = '<td>' + a.name + '</td>' +
                                   '<td>' + a.agent_lct + '</td>' +
                                   '<td>' + (a.resources.ATP || 0) + '</td>' +
                                   '<td>' + roles + '</td>' +
                                   '<td>' + status + '</td>' +
                                   '<td>' + trust + '</td>';
                    at.appendChild(tr);
                });
                agentsEl.appendChild(at);

                // Update planet view once on first society selection.
                loadPlanetView();
            }

            async function loadPlanetView() {
                const resp = await fetch('/api/planet');
                const data = await resp.json();
                const planetEl = document.getElementById('planet');
                planetEl.innerHTML = '';
                const pt = document.createElement('table');
                pt.innerHTML = '<tr><th>Name</th><th>LCT</th><th>Trust</th><th>Blocks</th><th>Chain OK</th><th>Audits</th><th>Role Rev</th><th>Mem Rev</th><th>Suppression</th><th>Federates With</th></tr>';
                data.forEach(s => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = '<td>' + s.name + '</td>' +
                                   '<td>' + s.society_lct + '</td>' +
                                   '<td>' + s.trust_composite.toFixed(2) + '</td>' +
                                   '<td>' + s.block_count + '</td>' +
                                   '<td>' + s.chain_valid + '</td>' +
                                   '<td>' + s.audits + '</td>' +
                                   '<td>' + s.role_revocations + '</td>' +
                                   '<td>' + s.membership_revocations + '</td>' +
                                   '<td>' + s.suppression_events + '</td>' +
                                   '<td>' + (s.federates_with || []).join(', ') + '</td>';
                    pt.appendChild(tr);
                });
                planetEl.appendChild(pt);
            }

            loadSocieties();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
