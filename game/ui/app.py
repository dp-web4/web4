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


@app.get("/api/societies/{society_lct}")
async def get_society(society_lct: str):
    soc = WORLD.societies.get(society_lct)
    if not soc:
        return JSONResponse({"error": "not found"}, status_code=404)

    struct = verify_chain_structure(soc)
    sigs = verify_stub_signatures(soc)

    blocks: list[Dict[str, Any]] = []
    for b in soc.blocks[-20:]:  # last 20 blocks
        blocks.append(
            {
                "index": b.get("index"),
                "timestamp": b.get("timestamp"),
                "previous_hash": b.get("previous_hash"),
                "header_hash": b.get("header_hash"),
                "signature": b.get("signature"),
                "event_count": len(b.get("events", [])),
                "events": b.get("events", []),
            }
        )

    # Simple agent/role/membership summary
    agents: list[Dict[str, Any]] = []
    for agent in WORLD.agents.values():
        if society_lct not in agent.memberships:
            continue
        agents.append(
            {
                "agent_lct": agent.agent_lct,
                "name": agent.name,
                "trust_axes": agent.trust_axes,
                "resources": agent.resources,
                "memberships": agent.memberships,
                # Roles are inferred from context edges client-side for now.
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
                at.innerHTML = '<tr><th>Name</th><th>LCT</th><th>ATP</th></tr>';
                data.agents.forEach(a => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = '<td>' + a.name + '</td>' +
                                   '<td>' + a.agent_lct + '</td>' +
                                   '<td>' + (a.resources.ATP || 0) + '</td>';
                    at.appendChild(tr);
                });
                agentsEl.appendChild(at);
            }

            loadSocieties();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
