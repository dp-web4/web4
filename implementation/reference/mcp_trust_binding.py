#!/usr/bin/env python3
"""
Web4 MCP Trust Binding — Reference Implementation

Makes MCP servers and clients first-class Web4 entities with LCTs, trust
tensors, ATP metering, and witness attestation.

Per: web4-standard/core-spec/mcp-protocol.md

Implements:
  - MCPServer: Web4 entity with LCT, capabilities, trust requirements
  - MCPClient: Web4 entity with LCT, model info, trust profile
  - Web4ContextHeaders: trust context injected into every MCP call
  - Trust-Based Resource Access: T3/V3 minimum checks before tool access
  - ATP-Based Metering: tool invocations consume ATP per cost table
  - Witness Integration: MCP servers witness interactions
  - Session Management: stateful sessions with context preservation
  - R6 Mapping: MCP invocations as R6 transactions
  - Capability Broadcasting: servers advertise capabilities with trust levels

@version 1.0.0
@see web4-standard/core-spec/mcp-protocol.md
"""

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# MCP Error Types (per spec §10)
# ═══════════════════════════════════════════════════════════════

class MCPErrorCode(Enum):
    INSUFFICIENT_TRUST = (-32001, "Insufficient trust")
    INVALID_LCT        = (-32002, "Client LCT cannot be verified")
    RESOURCE_UNAVAIL    = (-32003, "Resource temporarily unavailable")
    ATP_INSUFFICIENT    = (-32004, "Insufficient ATP for request")
    AGENCY_VIOLATION    = (-32005, "Agency delegation scope violated")

    def __init__(self, code: int, message: str):
        self.json_rpc_code = code
        self.message = message


class MCPError(Exception):
    def __init__(self, code: MCPErrorCode, detail: str = "",
                 trust_impact: Optional[Dict] = None):
        self.code = code
        self.detail = detail
        self.trust_impact = trust_impact or {}
        super().__init__(f"[{code.json_rpc_code}] {code.message}: {detail}")

    def to_response(self) -> dict:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": self.code.json_rpc_code,
                "message": self.code.message,
                "data": {
                    "error_type": self.code.name,
                    "detail": self.detail,
                },
            },
            "web4_context": {
                "error_witnessed": True,
                "trust_impact": self.trust_impact,
            },
        }


# ═══════════════════════════════════════════════════════════════
# Trust Tensors (minimal for MCP context)
# ═══════════════════════════════════════════════════════════════

@dataclass
class T3:
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def average(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def meets(self, required: "T3") -> bool:
        return (self.talent >= required.talent and
                self.training >= required.training and
                self.temperament >= required.temperament)

    def to_dict(self) -> dict:
        return {"talent": self.talent, "training": self.training,
                "temperament": self.temperament}


@dataclass
class V3:
    valuation: float = 0.0
    veracity: float = 0.5
    validity: float = 0.5

    def to_dict(self) -> dict:
        return {"valuation": self.valuation, "veracity": self.veracity,
                "validity": self.validity}


# ═══════════════════════════════════════════════════════════════
# Web4 Context Headers (per spec §4.1)
# ═══════════════════════════════════════════════════════════════

@dataclass
class Web4Context:
    """Trust context injected into every MCP message."""
    sender_lct: str
    sender_role: str
    t3_in_role: T3
    atp_stake: float = 0.0
    mrh_depth: int = 2
    society: str = ""
    law_hash: str = ""
    proof_of_agency: Optional[Dict[str, str]] = None

    def to_dict(self) -> dict:
        d = {
            "sender_lct": self.sender_lct,
            "sender_role": self.sender_role,
            "trust_context": {
                "t3_in_role": self.t3_in_role.to_dict(),
                "atp_stake": self.atp_stake,
            },
            "mrh_depth": self.mrh_depth,
            "society": self.society,
            "law_hash": self.law_hash,
        }
        if self.proof_of_agency:
            d["proof_of_agency"] = self.proof_of_agency
        return d


# ═══════════════════════════════════════════════════════════════
# Tool Definition (per spec §6.1)
# ═══════════════════════════════════════════════════════════════

@dataclass
class MCPTool:
    """MCP tool resource with trust requirements and ATP cost."""
    name: str
    description: str
    atp_cost: float = 1.0
    trust_requirements: Optional[T3] = None
    role_required: Optional[str] = None
    handler: Optional[Callable] = None

    def to_dict(self) -> dict:
        d = {
            "resource_type": "mcp_tool",
            "tool_definition": {
                "name": self.name,
                "description": self.description,
                "resource_requirements": {"atp_cost": self.atp_cost},
            },
        }
        if self.trust_requirements:
            d["tool_definition"]["trust_requirements"] = {
                "minimum_t3": self.trust_requirements.to_dict(),
            }
        if self.role_required:
            d["tool_definition"]["trust_requirements"] = d["tool_definition"].get("trust_requirements", {})
            d["tool_definition"]["trust_requirements"]["role_required"] = self.role_required
        return d


# ═══════════════════════════════════════════════════════════════
# MCP Session (per spec §11)
# ═══════════════════════════════════════════════════════════════

@dataclass
class MCPSession:
    """Stateful MCP session with context preservation."""
    session_id: str
    client_lct: str
    server_lct: str
    established: str
    atp_consumed: float = 0.0
    atp_remaining: float = 0.0
    interaction_count: int = 0
    success_count: int = 0
    t3_deltas: Dict[str, float] = field(default_factory=dict)
    timeout: int = 3600

    @property
    def success_rate(self) -> float:
        return self.success_count / self.interaction_count if self.interaction_count > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "session": {
                "id": self.session_id,
                "client": self.client_lct,
                "server": self.server_lct,
                "established": self.established,
                "context": {
                    "atp_consumed": self.atp_consumed,
                    "atp_remaining": self.atp_remaining,
                    "trust_evolution": {
                        "interaction_count": self.interaction_count,
                        "success_rate": self.success_rate,
                        "t3_delta": self.t3_deltas,
                    },
                },
                "timeout": self.timeout,
            },
        }


# ═══════════════════════════════════════════════════════════════
# Witness Attestation (per spec §4.3)
# ═══════════════════════════════════════════════════════════════

@dataclass
class InteractionWitness:
    """Witness attestation for an MCP interaction."""
    client_lct: str
    server_lct: str
    action: str
    timestamp: str
    success: bool
    witness_lct: str
    signature: str = ""
    mrh_update: Optional[Dict] = None

    def to_dict(self) -> dict:
        d = {
            "witness_attestation": {
                "witnessed_interaction": {
                    "client": self.client_lct,
                    "server": self.server_lct,
                    "action": self.action,
                    "timestamp": self.timestamp,
                    "success": self.success,
                },
                "witness": self.witness_lct,
                "signature": self.signature or f"cose:{os.urandom(16).hex()}",
            },
        }
        if self.mrh_update:
            d["witness_attestation"]["mrh_update"] = self.mrh_update
        return d


# ═══════════════════════════════════════════════════════════════
# MCP Server — Web4 Entity (per spec §3.1)
# ═══════════════════════════════════════════════════════════════

class MCPServer:
    """
    MCP server as a first-class Web4 entity with LCT.

    Implements:
      - Trust-based resource access (spec §4.2)
      - ATP metering (spec §9)
      - Witness attestation (spec §4.3)
      - Capability broadcasting (spec §8)
    """

    def __init__(self, lct_id: str, entity_type: str = "service",
                 protocols: Optional[List[str]] = None):
        self.lct_id = lct_id
        self.entity_type = entity_type
        self.protocols = protocols or ["mcp/1.0", "web4/1.0"]
        self.tools: Dict[str, MCPTool] = {}
        self.sessions: Dict[str, MCPSession] = {}
        self.witness_log: List[InteractionWitness] = []
        self.event_log: List[Dict] = []
        # Server's own trust
        self.t3 = T3(talent=0.8, training=0.85, temperament=0.9)
        self.v3 = V3(valuation=0.0, veracity=0.9, validity=0.85)

    def register_tool(self, tool: MCPTool):
        """Register a tool with the server."""
        self.tools[tool.name] = tool

    def broadcast_capabilities(self) -> dict:
        """Broadcast server capabilities (spec §8.1)."""
        return {
            "broadcast_type": "mcp_capabilities",
            "server": self.lct_id,
            "capabilities": {
                "tools": [t.to_dict() for t in self.tools.values()],
                "protocols": self.protocols,
                "trust_level": "high" if self.t3.average() > 0.8 else "medium",
                "availability": 0.999,
            },
            "ttl": 3600,
        }

    def create_session(self, client_lct: str, atp_budget: float = 100) -> MCPSession:
        """Establish a new MCP session with a client."""
        session_id = f"mcp:session:{os.urandom(8).hex()}"
        session = MCPSession(
            session_id=session_id,
            client_lct=client_lct,
            server_lct=self.lct_id,
            established=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            atp_remaining=atp_budget,
        )
        self.sessions[session_id] = session
        return session

    def handle_request(self, session_id: str, tool_name: str,
                       arguments: Dict[str, Any],
                       web4_ctx: Web4Context) -> dict:
        """
        Handle an MCP tools/call request with trust evaluation.
        Implements the 6-step process from spec §4.2.
        """
        # 0. Get session
        if session_id not in self.sessions:
            raise MCPError(MCPErrorCode.RESOURCE_UNAVAIL, "Unknown session")
        session = self.sessions[session_id]

        # 1. Verify entity identity (LCT check)
        if not web4_ctx.sender_lct:
            raise MCPError(MCPErrorCode.INVALID_LCT, "Missing sender LCT")

        # 2. Check trust requirements
        if tool_name not in self.tools:
            raise MCPError(MCPErrorCode.RESOURCE_UNAVAIL, f"Tool '{tool_name}' not found")
        tool = self.tools[tool_name]

        if tool.trust_requirements and not web4_ctx.t3_in_role.meets(tool.trust_requirements):
            raise MCPError(
                MCPErrorCode.INSUFFICIENT_TRUST,
                f"Tool '{tool_name}' requires T3 {tool.trust_requirements.to_dict()}, "
                f"got {web4_ctx.t3_in_role.to_dict()}",
                trust_impact={"t3": {"temperament": -0.01}},
            )

        # 3. Verify ATP stake
        if session.atp_remaining < tool.atp_cost:
            raise MCPError(MCPErrorCode.ATP_INSUFFICIENT,
                           f"Need {tool.atp_cost} ATP, have {session.atp_remaining}")

        # 4. Check agency delegation
        if tool.role_required and web4_ctx.sender_role != tool.role_required:
            if not web4_ctx.proof_of_agency:
                raise MCPError(MCPErrorCode.AGENCY_VIOLATION,
                               f"Tool requires role '{tool.role_required}'")

        # 5. Execute with metering
        session.interaction_count += 1
        try:
            if tool.handler:
                result = tool.handler(arguments)
            else:
                result = {"status": "ok", "tool": tool_name, "args": arguments}
            session.success_count += 1
            success = True
        except Exception as e:
            result = {"status": "error", "message": str(e)}
            success = False

        # Deduct ATP
        session.atp_consumed += tool.atp_cost
        session.atp_remaining -= tool.atp_cost

        # Apply trust modifier (higher trust = lower effective cost)
        trust_discount = 1.0 - (web4_ctx.t3_in_role.average() * 0.2)

        # 6. Update trust tensors
        if success:
            session.t3_deltas["temperament"] = session.t3_deltas.get("temperament", 0) + 0.01

        # Witness the interaction
        witness = InteractionWitness(
            client_lct=web4_ctx.sender_lct,
            server_lct=self.lct_id,
            action=tool_name,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            success=success,
            witness_lct=self.lct_id,
            mrh_update={"add_witnessing": [web4_ctx.sender_lct]} if success else None,
        )
        self.witness_log.append(witness)

        # R6 transaction record
        r6_record = {
            "type": "mcp_invocation",
            "rules": {"mcp_protocol": "1.0", "web4_compliance": True},
            "role": {"entity": web4_ctx.sender_lct, "roleType": web4_ctx.sender_role},
            "request": {"action": "tools/call", "target": f"mcp://{self.lct_id}/{tool_name}"},
            "resource": {"atp": tool.atp_cost * trust_discount},
            "result": {"success": success, "trust_updates": session.t3_deltas},
        }
        self.event_log.append(r6_record)

        return {
            "jsonrpc": "2.0",
            "result": result,
            "web4_context": {
                "atp_consumed": tool.atp_cost,
                "trust_modifier": trust_discount,
                "session_atp_remaining": session.atp_remaining,
                "interaction_witnessed": True,
            },
        }


# ═══════════════════════════════════════════════════════════════
# MCP Client — Web4 Entity (per spec §3.2)
# ═══════════════════════════════════════════════════════════════

class MCPClient:
    """MCP client as a Web4 entity."""

    def __init__(self, lct_id: str, entity_type: str = "ai",
                 role: str = "web4:DataAnalyst"):
        self.lct_id = lct_id
        self.entity_type = entity_type
        self.role = role
        self.t3 = T3(talent=0.9, training=0.95, temperament=0.85)
        self.v3 = V3(valuation=0.0, veracity=0.92, validity=0.88)
        self.sessions: Dict[str, MCPSession] = {}

    def make_context(self, atp_stake: float = 10,
                     agency: Optional[Dict[str, str]] = None) -> Web4Context:
        """Build Web4 context headers for an MCP request."""
        return Web4Context(
            sender_lct=self.lct_id,
            sender_role=self.role,
            t3_in_role=self.t3,
            atp_stake=atp_stake,
            proof_of_agency=agency,
        )

    def call_tool(self, server: MCPServer, session_id: str,
                  tool_name: str, arguments: Dict[str, Any],
                  atp_stake: float = 10,
                  agency: Optional[Dict[str, str]] = None) -> dict:
        """Call a tool on an MCP server with trust context."""
        ctx = self.make_context(atp_stake, agency)
        return server.handle_request(session_id, tool_name, arguments, ctx)


# ═══════════════════════════════════════════════════════════════
# Dynamic Pricing (per spec §9.2)
# ═══════════════════════════════════════════════════════════════

@dataclass
class PricingModel:
    """ATP-based pricing with trust modifiers."""
    base_prices: Dict[str, float] = field(default_factory=dict)
    high_trust_discount: float = 0.8
    peak_demand_surge: float = 1.5
    bulk_discount: float = 0.9

    def calculate_cost(self, tool_name: str, t3: T3,
                       is_peak: bool = False, is_bulk: bool = False) -> float:
        base = self.base_prices.get(tool_name, 1.0)
        cost = base

        # Trust discount: higher trust → lower cost
        if t3.average() > 0.8:
            cost *= self.high_trust_discount

        if is_peak:
            cost *= self.peak_demand_surge
        if is_bulk:
            cost *= self.bulk_discount

        return round(cost, 2)


# ═══════════════════════════════════════════════════════════════
# Self-Test
# ═══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(label, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}{f' — {detail}' if detail else ''}")
        else:
            failed += 1
            print(f"  [FAIL] {label}{f' — {detail}' if detail else ''}")

    # ── T1: MCP Server as Web4 Entity ──
    print("\n═══ T1: MCP Server as Web4 Entity ═══")
    server = MCPServer("lct:web4:mcp:server:db-001")
    check("T1: Server has LCT", server.lct_id == "lct:web4:mcp:server:db-001")
    check("T1: Server has entity type", server.entity_type == "service")
    check("T1: Server has protocols", "mcp/1.0" in server.protocols)
    check("T1: Server has T3", server.t3.average() > 0.8)

    # Register tools
    server.register_tool(MCPTool(
        name="database_query", description="Query the database",
        atp_cost=10,
        trust_requirements=T3(talent=0.5, training=0.6, temperament=0.0),
    ))
    server.register_tool(MCPTool(
        name="api_invoke", description="Call external API",
        atp_cost=25,
        trust_requirements=T3(talent=0.7, training=0.7, temperament=0.5),
        role_required="web4:Developer",
    ))
    server.register_tool(MCPTool(
        name="simple_read", description="Read public data",
        atp_cost=1,
    ))
    check("T1: 3 tools registered", len(server.tools) == 3)

    # ── T2: MCP Client as Web4 Entity ──
    print("\n═══ T2: MCP Client as Web4 Entity ═══")
    client = MCPClient("lct:web4:mcp:client:sage-001", role="web4:DataAnalyst")
    check("T2: Client has LCT", client.lct_id == "lct:web4:mcp:client:sage-001")
    check("T2: Client has role", client.role == "web4:DataAnalyst")
    check("T2: Client has T3", client.t3.talent == 0.9)

    ctx = client.make_context(atp_stake=50)
    check("T2: Context has sender_lct", ctx.sender_lct == client.lct_id)
    check("T2: Context has role", ctx.sender_role == "web4:DataAnalyst")
    check("T2: Context has T3", ctx.t3_in_role.talent == 0.9)

    d = ctx.to_dict()
    check("T2: Context serializes", "sender_lct" in d)
    check("T2: Trust context in dict", d["trust_context"]["atp_stake"] == 50)

    # ── T3: Session Management ──
    print("\n═══ T3: Session Management ═══")
    session = server.create_session(client.lct_id, atp_budget=200)
    check("T3: Session created", session.session_id.startswith("mcp:session:"))
    check("T3: Session knows client", session.client_lct == client.lct_id)
    check("T3: Session knows server", session.server_lct == server.lct_id)
    check("T3: ATP budget set", session.atp_remaining == 200)
    check("T3: Session serializes", "session" in session.to_dict())

    # ── T4: Trust-Based Resource Access ──
    print("\n═══ T4: Trust-Based Resource Access ═══")
    # Client calls simple_read (no trust requirements)
    result = client.call_tool(server, session.session_id,
                              "simple_read", {"path": "/data"})
    check("T4: Simple read succeeds", result["result"]["status"] == "ok")
    check("T4: ATP consumed", result["web4_context"]["atp_consumed"] == 1)
    check("T4: Remaining updated", result["web4_context"]["session_atp_remaining"] == 199)
    check("T4: Interaction witnessed", result["web4_context"]["interaction_witnessed"])

    # Client calls database_query (trust required)
    result2 = client.call_tool(server, session.session_id,
                               "database_query", {"sql": "SELECT 1"})
    check("T4: Database query succeeds (meets T3)", result2["result"]["status"] == "ok")
    check("T4: ATP deducted (10)", result2["web4_context"]["atp_consumed"] == 10)

    # ── T5: Insufficient Trust ──
    print("\n═══ T5: Insufficient Trust ═══")
    low_trust_client = MCPClient("lct:web4:mcp:client:untrusted")
    low_trust_client.t3 = T3(talent=0.3, training=0.2, temperament=0.1)
    low_session = server.create_session(low_trust_client.lct_id, atp_budget=100)

    try:
        low_trust_client.call_tool(server, low_session.session_id,
                                   "database_query", {"sql": "DROP TABLE"})
        check("T5: Low trust rejected", False)
    except MCPError as e:
        check("T5: Low trust rejected", e.code == MCPErrorCode.INSUFFICIENT_TRUST)
        resp = e.to_response()
        check("T5: Error has JSON-RPC code", resp["error"]["code"] == -32001)
        check("T5: Error has trust impact", "trust_impact" in resp["web4_context"])

    # ── T6: ATP Insufficient ──
    print("\n═══ T6: ATP Insufficient ═══")
    tiny_session = server.create_session(client.lct_id, atp_budget=5)
    try:
        client.call_tool(server, tiny_session.session_id,
                         "database_query", {"sql": "SELECT 1"})
        check("T6: ATP insufficient rejected", False)
    except MCPError as e:
        check("T6: ATP insufficient rejected", e.code == MCPErrorCode.ATP_INSUFFICIENT,
              f"need=10, have=5")

    # ── T7: Role-Based Access ──
    print("\n═══ T7: Role-Based Access ═══")
    # api_invoke requires "web4:Developer" role
    try:
        client.call_tool(server, session.session_id,
                         "api_invoke", {"url": "/api"})
        check("T7: Wrong role rejected", False)
    except MCPError as e:
        check("T7: Wrong role rejected", e.code == MCPErrorCode.AGENCY_VIOLATION)

    # With agency delegation
    result3 = client.call_tool(server, session.session_id,
                               "api_invoke", {"url": "/api"},
                               agency={"grant_id": "agy:dev-delegation",
                                       "scope": "web4:Developer"})
    check("T7: With agency delegation succeeds", result3["result"]["status"] == "ok")

    # ── T8: Capability Broadcasting ──
    print("\n═══ T8: Capability Broadcasting ═══")
    broadcast = server.broadcast_capabilities()
    check("T8: Broadcast has type", broadcast["broadcast_type"] == "mcp_capabilities")
    check("T8: Broadcast has server LCT", broadcast["server"] == server.lct_id)
    check("T8: Broadcast has tools", len(broadcast["capabilities"]["tools"]) == 3)
    check("T8: Broadcast has protocols", "mcp/1.0" in broadcast["capabilities"]["protocols"])
    check("T8: Broadcast has TTL", broadcast["ttl"] == 3600)
    check("T8: Trust level computed",
          broadcast["capabilities"]["trust_level"] in ("high", "medium"))

    # ── T9: Witness Log ──
    print("\n═══ T9: Witness Log ═══")
    check("T9: Witnesses recorded", len(server.witness_log) > 0)
    w = server.witness_log[0]
    check("T9: Witness has client LCT", w.client_lct == client.lct_id)
    check("T9: Witness has server LCT", w.server_lct == server.lct_id)
    check("T9: Witness has action", w.action == "simple_read")
    check("T9: Witness has timestamp", len(w.timestamp) > 0)

    wd = w.to_dict()
    check("T9: Witness serializes", "witness_attestation" in wd)
    check("T9: Witness has signature",
          "signature" in wd["witness_attestation"])

    # ── T10: Session Trust Evolution ──
    print("\n═══ T10: Session Trust Evolution ═══")
    check("T10: Interaction count tracked", session.interaction_count > 0,
          f"count={session.interaction_count}")
    check("T10: Success count tracked", session.success_count > 0)
    check("T10: Success rate computed", session.success_rate > 0)
    check("T10: T3 deltas accumulated", len(session.t3_deltas) > 0)
    check("T10: ATP consumed tracked", session.atp_consumed > 0,
          f"consumed={session.atp_consumed}")

    sd = session.to_dict()
    check("T10: Session serializes", "session" in sd)
    check("T10: Session has trust evolution",
          "trust_evolution" in sd["session"]["context"])

    # ── T11: R6 Event Log ──
    print("\n═══ T11: R6 Event Log ═══")
    check("T11: Events recorded", len(server.event_log) > 0)
    r6 = server.event_log[0]
    check("T11: R6 has type", r6["type"] == "mcp_invocation")
    check("T11: R6 has rules", r6["rules"]["web4_compliance"])
    check("T11: R6 has role entity", "entity" in r6["role"])
    check("T11: R6 has request action", r6["request"]["action"] == "tools/call")
    check("T11: R6 has resource ATP", "atp" in r6["resource"])

    # ── T12: Dynamic Pricing ──
    print("\n═══ T12: Dynamic Pricing ═══")
    pricing = PricingModel(
        base_prices={
            "simple_query": 1, "complex_analysis": 10, "heavy_compute": 100,
        },
    )
    # High trust client
    high_t3 = T3(talent=0.9, training=0.9, temperament=0.9)
    cost1 = pricing.calculate_cost("simple_query", high_t3)
    check("T12: High trust discount", cost1 == 0.8, f"cost={cost1}")

    # Low trust client
    low_t3 = T3(talent=0.3, training=0.3, temperament=0.3)
    cost2 = pricing.calculate_cost("simple_query", low_t3)
    check("T12: Low trust no discount", cost2 == 1.0)

    # Peak demand
    cost3 = pricing.calculate_cost("complex_analysis", high_t3, is_peak=True)
    check("T12: Peak demand surge", cost3 == 12.0, f"cost={cost3}")

    # Bulk discount
    cost4 = pricing.calculate_cost("heavy_compute", high_t3, is_bulk=True)
    check("T12: Bulk discount", cost4 == 72.0, f"cost={cost4}")

    # ── T13: Tool Serialization ──
    print("\n═══ T13: Tool Serialization ═══")
    tool = server.tools["database_query"]
    td = tool.to_dict()
    check("T13: Tool has resource_type", td["resource_type"] == "mcp_tool")
    check("T13: Tool has name", td["tool_definition"]["name"] == "database_query")
    check("T13: Tool has ATP cost",
          td["tool_definition"]["resource_requirements"]["atp_cost"] == 10)
    check("T13: Tool has trust requirements",
          "minimum_t3" in td["tool_definition"]["trust_requirements"])

    # ── T14: Multiple Sessions ──
    print("\n═══ T14: Multiple Sessions ═══")
    client2 = MCPClient("lct:web4:mcp:client:nova-001", role="web4:Researcher")
    client2.t3 = T3(talent=0.85, training=0.9, temperament=0.88)
    s2 = server.create_session(client2.lct_id, atp_budget=50)

    r1 = client2.call_tool(server, s2.session_id, "simple_read", {"path": "/readme"})
    check("T14: Second client works", r1["result"]["status"] == "ok")
    check("T14: Sessions isolated", s2.session_id != session.session_id)
    check("T14: Server has multiple sessions", len(server.sessions) >= 2)

    # ── T15: Error Response Format ──
    print("\n═══ T15: Error Response Format ═══")
    for err_code in MCPErrorCode:
        err = MCPError(err_code, f"test detail for {err_code.name}")
        resp = err.to_response()
        check(f"T15: {err_code.name} has JSON-RPC format",
              "jsonrpc" in resp and resp["jsonrpc"] == "2.0")
    check("T15: 5 error codes defined", len(MCPErrorCode) == 5)

    # ── T16: Full Interaction Flow ──
    print("\n═══ T16: Full Interaction Flow ═══")
    # Setup fresh server + client
    srv = MCPServer("lct:web4:mcp:server:analytics")
    srv.register_tool(MCPTool(
        name="analyze",
        description="Run analysis",
        atp_cost=15,
        trust_requirements=T3(talent=0.6, training=0.6, temperament=0.0),
        handler=lambda args: {"result": sum(args.get("data", [])),
                               "count": len(args.get("data", []))},
    ))
    cli = MCPClient("lct:web4:mcp:client:sage", role="web4:Analyst")
    sess = srv.create_session(cli.lct_id, atp_budget=100)

    # Call with actual handler
    r = cli.call_tool(srv, sess.session_id, "analyze",
                      {"data": [1, 2, 3, 4, 5]})
    check("T16: Handler executed", r["result"]["result"] == 15)
    check("T16: Handler returns count", r["result"]["count"] == 5)
    check("T16: ATP metered", r["web4_context"]["atp_consumed"] == 15)
    check("T16: Remaining correct", r["web4_context"]["session_atp_remaining"] == 85)
    check("T16: Witnessed", len(srv.witness_log) == 1)
    check("T16: R6 logged", len(srv.event_log) == 1)

    # ═══ Summary ═══
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  MCP Trust Binding — Track P Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'='*60}")

    if failed == 0:
        print(f"\n  All {total} checks pass — MCP is now trust-native")
        print(f"  MCPServer/MCPClient as Web4 entities with LCTs")
        print(f"  Trust-based access, ATP metering, witness attestation")
        print(f"  R6 transaction logging, dynamic pricing, 5 error codes")
    else:
        print(f"\n  {failed} failures need investigation")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
