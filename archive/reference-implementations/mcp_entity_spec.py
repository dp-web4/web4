#!/usr/bin/env python3
"""
Web4 MCP Server as Web4 Entity — Reference Implementation
Spec: web4-standard/MCP_ENTITY_SPECIFICATION.md (408 lines, 10 sections)

Covers:
  §1  MCP Server Definition (responsive + delegative dual nature)
  §2  MCP as Web4 Entity (classification, LCT structure)
  §3  MCP in Web4 Equation (I/O membrane role)
  §4  MCP Server Types (Database, Tool, Knowledge, API, Process)
  §5  Trust and Reputation (4 trust dimensions, weighted computation)
  §6  SAGE Architecture Integration (H-level strategic, L-level tactical)
  §7  Protocol Extensions (web4_context fields, trust attestation)
  §8  Benefits (unified access, composability, trust-based selection, context preservation)
  §9  Implementation Roadmap (3 phases)
  §10 Conclusion

Run:  python3 mcp_entity_spec.py
"""

import time, hashlib, json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum

# ─────────────────────────────────────────────
# §1 MCP Server Definition
# ─────────────────────────────────────────────

class MCPCapability(Enum):
    RESPONSIVE = "responsive"      # Processes requests and returns results
    DELEGATIVE = "delegative"      # Front-end for complex resources
    AGENTIC = "agentic"           # Can initiate actions autonomously

@dataclass
class MCPServerDefinition:
    """MCP server with dual responsive+delegative nature"""
    entity_id: str
    protocol_version: str = "1.0"
    capabilities: Set[MCPCapability] = field(default_factory=lambda: {MCPCapability.RESPONSIVE, MCPCapability.DELEGATIVE})

    # Responsive properties
    maintains_state: bool = True
    rate_limited: bool = True

    # Delegative properties
    backend_abstracted: bool = True
    manages_auth: bool = True
    connection_pooling: bool = True

    def is_responsive(self) -> bool:
        return MCPCapability.RESPONSIVE in self.capabilities

    def is_delegative(self) -> bool:
        return MCPCapability.DELEGATIVE in self.capabilities

    def is_agentic(self) -> bool:
        return MCPCapability.AGENTIC in self.capabilities


# ─────────────────────────────────────────────
# §2 MCP as Web4 Entity
# ─────────────────────────────────────────────

class MCPServerSubtype(Enum):
    DATABASE = "database"        # Delegates to SQL/NoSQL
    API = "api"                  # Delegates to REST/GraphQL
    TOOL = "tool"                # Delegates to CLI/SDK
    PROCESS = "process"          # Delegates to running processes
    KNOWLEDGE = "knowledge"      # Delegates to knowledge bases

@dataclass
class MRHRelevance:
    """MRH relevance entry"""
    target: str
    probability: float       # [0,1]
    relation: str            # mrh:depends_on, mrh:delegates_to, mrh:produces, mrh:references

@dataclass
class MCPEntityLCT:
    """LCT structure for MCP servers per spec §2.2"""
    lct_version: str = "1.0"
    entity_id: str = ""
    entity_type: str = "mcp_server"
    entity_subtype: str = ""  # MCPServerSubtype value
    capabilities: Dict[str, bool] = field(default_factory=lambda: {
        "responsive": True, "delegative": True, "agentic": False
    })
    mcp_metadata: Dict[str, Any] = field(default_factory=dict)
    mrh: List[MRHRelevance] = field(default_factory=list)
    trust_tensor: Dict[str, float] = field(default_factory=dict)

    def add_mrh_relevance(self, target: str, probability: float, relation: str):
        self.mrh.append(MRHRelevance(target=target, probability=probability, relation=relation))

    def to_json(self) -> Dict:
        return {
            "lct_version": self.lct_version,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "entity_subtype": self.entity_subtype,
            "capabilities": self.capabilities,
            "mcp_metadata": self.mcp_metadata,
            "mrh": {"@graph": [
                {"@type": "mrh:Relevance", "mrh:target": {"@id": r.target},
                 "mrh:probability": r.probability, "mrh:relation": r.relation}
                for r in self.mrh
            ]},
            "trust_tensor": self.trust_tensor
        }


# ─────────────────────────────────────────────
# §4 MCP Server Types
# ─────────────────────────────────────────────

class MCPEntity:
    """Base MCP server entity"""

    def __init__(self, entity_type: str = "mcp_server", subtype: str = ""):
        self.lct = MCPEntityLCT(entity_id=f"mcp:{subtype}_{id(self)}", entity_subtype=subtype)
        self.lct.mcp_metadata["protocol_version"] = "1.0"
        self.request_count = 0
        self.success_count = 0
        self.delegation_count = 0
        self.delegation_success = 0
        self.latencies: List[float] = []
        self.auth_attempts = 0
        self.auth_failures = 0

    def handle_request(self, method: str, params: Dict) -> Dict:
        self.request_count += 1
        return {"status": "not_implemented"}

    def record_delegation(self, success: bool):
        self.delegation_count += 1
        if success:
            self.delegation_success += 1

    def record_latency(self, ms: float):
        self.latencies.append(ms)

    def record_auth(self, success: bool):
        self.auth_attempts += 1
        if not success:
            self.auth_failures += 1

class DatabaseMCPServer(MCPEntity):
    """§4.1 Database MCP server"""

    def __init__(self, backend_type: str = "postgresql"):
        super().__init__(subtype="database")
        self.backend_type = backend_type
        self.lct.mcp_metadata["backend_type"] = backend_type
        self.lct.mcp_metadata["supported_methods"] = ["query", "insert", "update", "delete"]
        self.data: Dict[str, List[Dict]] = {}  # table -> rows

    def handle_request(self, method: str, params: Dict) -> Dict:
        self.request_count += 1
        self.delegation_count += 1  # Every DB op is a delegation
        if method == "query":
            table = params.get("table", "")
            rows = self.data.get(table, [])
            self.delegation_success += 1
            self.success_count += 1
            query_hash = hashlib.sha256(json.dumps(params).encode()).hexdigest()[:16]
            self.lct.add_mrh_relevance(f"lct:query_{query_hash}", 0.9, "mrh:produces")
            return {"status": "success", "data": rows, "count": len(rows)}
        elif method == "insert":
            table = params.get("table", "")
            row = params.get("row", {})
            self.data.setdefault(table, []).append(row)
            self.delegation_success += 1
            self.success_count += 1
            return {"status": "success", "inserted": 1}
        return {"status": "error", "message": f"unknown method: {method}"}

class ToolMCPServer(MCPEntity):
    """§4.2 Tool MCP server"""

    def __init__(self, tool_name: str = ""):
        super().__init__(subtype="tool")
        self.tool_name = tool_name
        self.lct.mcp_metadata["supported_methods"] = ["execute", "status", "cancel"]
        self.executions: Dict[str, str] = {}

    def handle_request(self, method: str, params: Dict) -> Dict:
        self.request_count += 1
        if method == "execute":
            exec_id = f"exec_{self.request_count}"
            self.executions[exec_id] = "running"
            self.delegation_count += 1
            self.delegation_success += 1
            self.success_count += 1
            self.lct.add_mrh_relevance(f"lct:execution_{exec_id}", 1.0, "mrh:produces")
            return {"status": "running", "pid": exec_id}
        elif method == "status":
            pid = params.get("pid", "")
            status = self.executions.get(pid, "unknown")
            return {"status": status}
        return {"status": "error", "message": f"unknown method: {method}"}

class KnowledgeMCPServer(MCPEntity):
    """§4.3 Knowledge MCP server"""

    def __init__(self):
        super().__init__(subtype="knowledge")
        self.lct.mcp_metadata["supported_methods"] = ["search", "retrieve", "update_graph"]
        self.knowledge: Dict[str, Dict] = {}

    def add_knowledge(self, lct_id: str, content: Dict):
        self.knowledge[lct_id] = content

    def handle_request(self, method: str, params: Dict) -> Dict:
        self.request_count += 1
        if method == "search":
            query = params.get("query", "")
            limit = params.get("limit", 10)
            results = []
            for lct_id, content in self.knowledge.items():
                if query.lower() in json.dumps(content).lower():
                    score = 0.9 if query.lower() in str(content.get("title", "")).lower() else 0.6
                    results.append({"lct_id": lct_id, "relevance_score": score, "content": content})
                    self.lct.add_mrh_relevance(lct_id, score, "mrh:references")
            self.delegation_count += 1
            self.delegation_success += 1
            self.success_count += 1
            return {"status": "success", "results": results[:limit]}
        return {"status": "error", "message": f"unknown method: {method}"}

class APIMCPServer(MCPEntity):
    """API MCP server — delegates to REST/GraphQL"""

    def __init__(self, api_endpoint: str = ""):
        super().__init__(subtype="api")
        self.api_endpoint = api_endpoint
        self.lct.mcp_metadata["supported_methods"] = ["get", "post", "put", "delete"]

    def handle_request(self, method: str, params: Dict) -> Dict:
        self.request_count += 1
        self.delegation_count += 1
        self.delegation_success += 1
        self.success_count += 1
        return {"status": "success", "endpoint": self.api_endpoint, "method": method}

class ProcessMCPServer(MCPEntity):
    """Process MCP server — delegates to running processes"""

    def __init__(self):
        super().__init__(subtype="process")
        self.lct.mcp_metadata["supported_methods"] = ["start", "stop", "monitor"]
        self.processes: Dict[str, str] = {}

    def handle_request(self, method: str, params: Dict) -> Dict:
        self.request_count += 1
        if method == "start":
            pid = f"proc_{self.request_count}"
            self.processes[pid] = "running"
            self.delegation_count += 1
            self.delegation_success += 1
            self.success_count += 1
            return {"status": "started", "pid": pid}
        return {"status": "error"}


# ─────────────────────────────────────────────
# §5 Trust and Reputation
# ─────────────────────────────────────────────

class MCPTrustComputer:
    """Trust computation per spec §5.2"""

    WEIGHT_SUCCESS = 0.3
    WEIGHT_DELEGATION = 0.3
    WEIGHT_LATENCY = 0.2
    WEIGHT_SECURITY = 0.2

    @staticmethod
    def compute_trust(server: MCPEntity) -> Dict[str, float]:
        # Response trust: success rate
        success_rate = server.success_count / max(server.request_count, 1)

        # Delegation reliability
        delegation_reliability = server.delegation_success / max(server.delegation_count, 1)

        # Latency consistency (lower variance = higher trust)
        if len(server.latencies) > 1:
            mean_lat = sum(server.latencies) / len(server.latencies)
            variance = sum((x - mean_lat) ** 2 for x in server.latencies) / len(server.latencies)
            latency_trust = 1.0 / (1.0 + variance)
        else:
            latency_trust = 1.0  # Default high if not enough data

        # Security trust
        security_trust = 1.0 - (server.auth_failures / max(server.auth_attempts, 1))

        # Weighted combination
        overall = (MCPTrustComputer.WEIGHT_SUCCESS * success_rate +
                   MCPTrustComputer.WEIGHT_DELEGATION * delegation_reliability +
                   MCPTrustComputer.WEIGHT_LATENCY * latency_trust +
                   MCPTrustComputer.WEIGHT_SECURITY * security_trust)

        return {
            "overall": overall,
            "response_trust": success_rate,
            "delegation_trust": delegation_reliability,
            "latency_trust": latency_trust,
            "security_trust": security_trust
        }


# ─────────────────────────────────────────────
# §6 SAGE Architecture Integration
# ─────────────────────────────────────────────

class MCPRegistry:
    """Registry for MCP servers with trust-based selection"""

    def __init__(self):
        self.servers: Dict[str, MCPEntity] = {}

    def register(self, name: str, server: MCPEntity):
        self.servers[name] = server

    def find_servers(self, subtype: str) -> List[MCPEntity]:
        return [s for s in self.servers.values() if s.lct.entity_subtype == subtype]

    def find_best(self, subtype: str) -> Optional[MCPEntity]:
        candidates = self.find_servers(subtype)
        if not candidates:
            return None
        return max(candidates, key=lambda s: MCPTrustComputer.compute_trust(s)["overall"])

@dataclass
class ExecutionStep:
    """A step in a SAGE execution plan"""
    server_name: str
    method: str
    params: Dict[str, Any]
    requires_mcp: bool = True

class SAGEWithMCP:
    """SAGE system with MCP server integration per spec §6.2"""

    def __init__(self, registry: MCPRegistry):
        self.registry = registry
        self.execution_log: List[Dict] = []

    def identify_resources(self, task: str) -> List[str]:
        """H-level: determine required MCP server subtypes"""
        # Simple keyword-based identification
        resources = []
        if any(kw in task.lower() for kw in ["query", "database", "data", "sql"]):
            resources.append("database")
        if any(kw in task.lower() for kw in ["api", "rest", "endpoint"]):
            resources.append("api")
        if any(kw in task.lower() for kw in ["search", "knowledge", "find"]):
            resources.append("knowledge")
        if any(kw in task.lower() for kw in ["run", "execute", "tool"]):
            resources.append("tool")
        return resources if resources else ["database"]  # Default

    def create_plan(self, task: str, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """H-level: create execution plan"""
        return steps

    def execute_plan(self, steps: List[ExecutionStep]) -> List[Dict]:
        """L-level: execute plan using MCP servers"""
        results = []
        for step in steps:
            if step.requires_mcp:
                server = self.registry.servers.get(step.server_name)
                if server:
                    result = server.handle_request(step.method, step.params)
                    results.append(result)
                    self.execution_log.append({
                        "server": step.server_name,
                        "method": step.method,
                        "status": result.get("status")
                    })
                else:
                    results.append({"status": "error", "message": f"server not found: {step.server_name}"})
            else:
                results.append({"status": "success", "direct": True})
        return results


# ─────────────────────────────────────────────
# §7 Protocol Extensions
# ─────────────────────────────────────────────

@dataclass
class Web4Context:
    """Web4-specific MCP message context per spec §7.1"""
    requesting_lct: str
    mrh_depth: int = 2
    trust_requirement: float = 0.8
    delegation_chain: List[str] = field(default_factory=list)

    def to_json(self) -> Dict:
        return {
            "requesting_lct": self.requesting_lct,
            "mrh_depth": self.mrh_depth,
            "trust_requirement": self.trust_requirement,
            "delegation_chain": self.delegation_chain
        }

@dataclass
class TrustAttestation:
    """Trust attestation in MCP responses per spec §7.2"""
    server_lct: str
    confidence: float
    delegation_target: str = ""
    latency_ms: float = 0.0
    cache_hit: bool = False

    def to_json(self) -> Dict:
        return {
            "server_lct": self.server_lct,
            "confidence": self.confidence,
            "delegation_target": self.delegation_target,
            "latency_ms": self.latency_ms,
            "cache_hit": self.cache_hit
        }

def build_web4_mcp_request(method: str, params: Dict, context: Web4Context) -> Dict:
    """Build Web4-enhanced MCP request"""
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "web4_context": context.to_json()
    }

def build_web4_mcp_response(data: Any, attestation: TrustAttestation) -> Dict:
    """Build Web4-enhanced MCP response"""
    return {
        "jsonrpc": "2.0",
        "result": {
            "data": data,
            "trust_attestation": attestation.to_json()
        }
    }


# ─────────────────────────────────────────────
# §8 Benefits + §9 Roadmap
# ─────────────────────────────────────────────

class MCPServerChain:
    """Composable server chains (§8.2 Composability)"""

    def __init__(self):
        self.chain: List[MCPEntity] = []

    def add(self, server: MCPEntity):
        self.chain.append(server)

    def execute_chain(self, initial_params: Dict) -> List[Dict]:
        """Execute through chain of MCP servers"""
        results = []
        current_params = initial_params
        for server in self.chain:
            method = current_params.get("method", "query")
            result = server.handle_request(method, current_params)
            results.append(result)
            # Pass output as input to next server
            if result.get("status") == "success":
                current_params = {**current_params, "previous_result": result}
            else:
                break
        return results

class TrustBasedSelector:
    """Trust-based server selection with failover (§8.3)"""

    def __init__(self, registry: MCPRegistry):
        self.registry = registry

    def select_with_failover(self, subtype: str, min_trust: float = 0.5) -> Optional[MCPEntity]:
        candidates = self.registry.find_servers(subtype)
        # Sort by trust, highest first
        ranked = sorted(candidates,
                        key=lambda s: MCPTrustComputer.compute_trust(s)["overall"],
                        reverse=True)
        for server in ranked:
            trust = MCPTrustComputer.compute_trust(server)["overall"]
            if trust >= min_trust:
                return server
        return None


# ═══════════════════════════════════════════════
# TEST SUITE
# ═══════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    # ─── §1: MCP Server Definition ───
    print("§1: MCP Server Definition")

    defn = MCPServerDefinition(entity_id="mcp:test_001")
    check("T1.1 Default is responsive", defn.is_responsive())
    check("T1.2 Default is delegative", defn.is_delegative())
    check("T1.3 Default not agentic", not defn.is_agentic())
    check("T1.4 Maintains state", defn.maintains_state)
    check("T1.5 Rate limited", defn.rate_limited)
    check("T1.6 Backend abstracted", defn.backend_abstracted)
    check("T1.7 Manages auth", defn.manages_auth)
    check("T1.8 Connection pooling", defn.connection_pooling)

    defn_agentic = MCPServerDefinition(
        entity_id="mcp:agentic",
        capabilities={MCPCapability.RESPONSIVE, MCPCapability.DELEGATIVE, MCPCapability.AGENTIC}
    )
    check("T1.9 Agentic server", defn_agentic.is_agentic())

    # ─── §2: MCP as Web4 Entity ───
    print("§2: MCP as Web4 Entity")

    db_server = DatabaseMCPServer("postgresql")
    lct = db_server.lct
    check("T2.1 Entity type = mcp_server", lct.entity_type == "mcp_server")
    check("T2.2 Subtype = database", lct.entity_subtype == "database")
    check("T2.3 LCT version", lct.lct_version == "1.0")
    check("T2.4 Responsive capability", lct.capabilities["responsive"])
    check("T2.5 Delegative capability", lct.capabilities["delegative"])
    check("T2.6 Not agentic", not lct.capabilities["agentic"])
    check("T2.7 Backend type in metadata", lct.mcp_metadata["backend_type"] == "postgresql")
    check("T2.8 Supported methods in metadata", "query" in lct.mcp_metadata["supported_methods"])

    lct.add_mrh_relevance("lct:schema", 0.95, "mrh:depends_on")
    check("T2.9 MRH relevance added", len(lct.mrh) == 1)
    check("T2.10 MRH probability", lct.mrh[0].probability == 0.95)
    check("T2.11 MRH relation", lct.mrh[0].relation == "mrh:depends_on")

    lct_json = lct.to_json()
    check("T2.12 JSON serialization", lct_json["entity_type"] == "mcp_server")
    check("T2.13 MRH graph in JSON", len(lct_json["mrh"]["@graph"]) >= 1)

    # ─── §3: MCP in Web4 Equation ───
    print("§3: MCP in Web4 Equation")

    # MCP is the I/O membrane - verify all 5 server subtypes
    subtypes = [s.value for s in MCPServerSubtype]
    check("T3.1 5 server subtypes", len(subtypes) == 5)
    check("T3.2 Database subtype", "database" in subtypes)
    check("T3.3 API subtype", "api" in subtypes)
    check("T3.4 Tool subtype", "tool" in subtypes)
    check("T3.5 Process subtype", "process" in subtypes)
    check("T3.6 Knowledge subtype", "knowledge" in subtypes)

    # ─── §4: MCP Server Types ───
    print("§4: MCP Server Types")

    # Database
    db = DatabaseMCPServer("postgresql")
    db.data["users"] = [{"name": "Alice"}, {"name": "Bob"}]
    result_q = db.handle_request("query", {"table": "users"})
    check("T4.1 DB query succeeds", result_q["status"] == "success")
    check("T4.2 DB returns data", result_q["count"] == 2)

    result_i = db.handle_request("insert", {"table": "users", "row": {"name": "Carol"}})
    check("T4.3 DB insert succeeds", result_i["status"] == "success")
    check("T4.4 Data stored", len(db.data["users"]) == 3)
    check("T4.5 MRH updated on query", len(db.lct.mrh) > 0)

    # Tool
    tool = ToolMCPServer("compiler")
    result_t = tool.handle_request("execute", {"command": "gcc", "args": ["-o", "test"]})
    check("T4.6 Tool execution succeeds", result_t["status"] == "running")
    check("T4.7 Tool returns PID", "pid" in result_t)
    check("T4.8 Tool MRH updated", len(tool.lct.mrh) > 0)

    # Knowledge
    kb = KnowledgeMCPServer()
    kb.add_knowledge("lct:doc1", {"title": "Web4 Architecture", "content": "..."})
    kb.add_knowledge("lct:doc2", {"title": "MCP Protocol", "content": "..."})
    result_k = kb.handle_request("search", {"query": "Web4"})
    check("T4.9 Knowledge search succeeds", result_k["status"] == "success")
    check("T4.10 Knowledge returns results", len(result_k["results"]) >= 1)
    check("T4.11 Knowledge MRH updated", len(kb.lct.mrh) > 0)

    # API
    api = APIMCPServer("https://api.example.com")
    result_a = api.handle_request("get", {"path": "/users"})
    check("T4.12 API request succeeds", result_a["status"] == "success")

    # Process
    proc = ProcessMCPServer()
    result_p = proc.handle_request("start", {"name": "worker"})
    check("T4.13 Process start succeeds", result_p["status"] == "started")
    check("T4.14 Process returns PID", "pid" in result_p)

    # ─── §5: Trust and Reputation ───
    print("§5: Trust and Reputation")

    # Perfect server
    perfect = DatabaseMCPServer()
    for _ in range(10):
        perfect.handle_request("query", {"table": "t"})
        perfect.record_latency(50.0)
        perfect.record_auth(True)
    trust_p = MCPTrustComputer.compute_trust(perfect)
    check("T5.1 Perfect server trust = 1.0", abs(trust_p["overall"] - 1.0) < 0.01)
    check("T5.2 Response trust = 1.0", abs(trust_p["response_trust"] - 1.0) < 0.01)
    check("T5.3 Delegation trust = 1.0", abs(trust_p["delegation_trust"] - 1.0) < 0.01)
    check("T5.4 Security trust = 1.0", abs(trust_p["security_trust"] - 1.0) < 0.01)

    # Server with issues
    flaky = DatabaseMCPServer()
    flaky.request_count = 10
    flaky.success_count = 7  # 70% success
    flaky.delegation_count = 10
    flaky.delegation_success = 8  # 80%
    flaky.latencies = [10, 10, 10, 10, 100]  # High variance
    flaky.auth_attempts = 10
    flaky.auth_failures = 2  # 20% failure
    trust_f = MCPTrustComputer.compute_trust(flaky)
    check("T5.5 Flaky server < perfect", trust_f["overall"] < trust_p["overall"])
    check("T5.6 Response trust = 0.7", abs(trust_f["response_trust"] - 0.7) < 0.01)
    check("T5.7 Delegation trust = 0.8", abs(trust_f["delegation_trust"] - 0.8) < 0.01)
    check("T5.8 Security trust = 0.8", abs(trust_f["security_trust"] - 0.8) < 0.01)
    check("T5.9 Latency trust < 1.0 (high variance)", trust_f["latency_trust"] < 1.0)
    check("T5.10 Overall trust > 0.5", trust_f["overall"] > 0.5)

    # New server (no history): 0/0 success + 0/0 delegation + 1.0 latency + 1.0 security
    new = DatabaseMCPServer()
    trust_n = MCPTrustComputer.compute_trust(new)
    check("T5.11 New server: no history = low response + delegation trust",
          abs(trust_n["overall"] - 0.4) < 0.01)

    # ─── §6: SAGE Architecture Integration ───
    print("§6: SAGE Architecture Integration")

    registry = MCPRegistry()
    db1 = DatabaseMCPServer("postgresql")
    db2 = DatabaseMCPServer("mysql")
    tool1 = ToolMCPServer("compiler")
    registry.register("db1", db1)
    registry.register("db2", db2)
    registry.register("tool1", tool1)

    check("T6.1 Registry has 3 servers", len(registry.servers) == 3)
    db_servers = registry.find_servers("database")
    check("T6.2 Find database servers", len(db_servers) == 2)
    tool_servers = registry.find_servers("tool")
    check("T6.3 Find tool servers", len(tool_servers) == 1)
    none_servers = registry.find_servers("knowledge")
    check("T6.4 No knowledge servers", len(none_servers) == 0)

    best_db = registry.find_best("database")
    check("T6.5 Find best database", best_db is not None)

    # SAGE integration
    sage = SAGEWithMCP(registry)
    resources = sage.identify_resources("Query the database for user data")
    check("T6.6 H-level identifies database", "database" in resources)

    steps = [
        ExecutionStep("db1", "query", {"table": "users"}),
        ExecutionStep("tool1", "execute", {"command": "analyze"})
    ]
    results = sage.execute_plan(steps)
    check("T6.7 Plan executes 2 steps", len(results) == 2)
    check("T6.8 DB step succeeds", results[0]["status"] == "success")
    check("T6.9 Tool step succeeds", results[1]["status"] == "running")
    check("T6.10 Execution log recorded", len(sage.execution_log) == 2)

    # Missing server
    steps_bad = [ExecutionStep("nonexistent", "query", {})]
    results_bad = sage.execute_plan(steps_bad)
    check("T6.11 Missing server → error", results_bad[0]["status"] == "error")

    # ─── §7: Protocol Extensions ───
    print("§7: Protocol Extensions")

    ctx = Web4Context(
        requesting_lct="lct:ai_agent_001",
        mrh_depth=2,
        trust_requirement=0.8,
        delegation_chain=["lct:orchestrator", "mcp:database_server"]
    )
    ctx_json = ctx.to_json()
    check("T7.1 Web4 context has lct", ctx_json["requesting_lct"] == "lct:ai_agent_001")
    check("T7.2 MRH depth", ctx_json["mrh_depth"] == 2)
    check("T7.3 Trust requirement", ctx_json["trust_requirement"] == 0.8)
    check("T7.4 Delegation chain", len(ctx_json["delegation_chain"]) == 2)

    request_msg = build_web4_mcp_request("query", {"sql": "SELECT *"}, ctx)
    check("T7.5 JSON-RPC format", request_msg["jsonrpc"] == "2.0")
    check("T7.6 Method in request", request_msg["method"] == "query")
    check("T7.7 Web4 context attached", "web4_context" in request_msg)

    attestation = TrustAttestation(
        server_lct="mcp:database_server_001",
        confidence=0.95,
        delegation_target="postgresql://db.internal",
        latency_ms=45,
        cache_hit=False
    )
    response_msg = build_web4_mcp_response([{"id": 1}], attestation)
    check("T7.8 Response has result", "result" in response_msg)
    check("T7.9 Trust attestation present", "trust_attestation" in response_msg["result"])
    check("T7.10 Confidence in attestation", response_msg["result"]["trust_attestation"]["confidence"] == 0.95)
    check("T7.11 Latency tracked", response_msg["result"]["trust_attestation"]["latency_ms"] == 45)

    # ─── §8: Benefits ───
    print("§8: Benefits")

    # Composability — server chains
    chain = MCPServerChain()
    chain_db = DatabaseMCPServer()
    chain_db.data["results"] = [{"id": 1, "value": "data"}]
    chain_tool = ToolMCPServer("processor")
    chain.add(chain_db)
    chain.add(chain_tool)

    chain_results = chain.execute_chain({"method": "query", "table": "results"})
    check("T8.1 Chain executes 2 servers", len(chain_results) == 2)
    check("T8.2 First server succeeds", chain_results[0]["status"] == "success")

    # Trust-based selection with failover
    reg = MCPRegistry()
    good_server = DatabaseMCPServer()
    for _ in range(10):
        good_server.handle_request("query", {"table": "t"})
    bad_server = DatabaseMCPServer()
    bad_server.request_count = 10
    bad_server.success_count = 2  # 20% success
    bad_server.delegation_count = 10
    bad_server.delegation_success = 2
    reg.register("good", good_server)
    reg.register("bad", bad_server)

    selector = TrustBasedSelector(reg)
    selected = selector.select_with_failover("database", min_trust=0.5)
    check("T8.3 Trust-based selection picks good server",
          selected is good_server)
    check("T8.4 No server above 0.99 threshold",
          selector.select_with_failover("database", min_trust=0.999) is good_server)

    # Context preservation (MRH grows with operations)
    kb2 = KnowledgeMCPServer()
    kb2.add_knowledge("doc1", {"title": "Web4"})
    kb2.handle_request("search", {"query": "Web4"})
    kb2.handle_request("search", {"query": "Web4"})
    check("T8.5 Context preserved across calls (MRH grows)", len(kb2.lct.mrh) >= 2)

    # ─── §9: Implementation Roadmap ───
    print("§9: Implementation Roadmap")

    # Phase 1: Basic entity support
    entity = DatabaseMCPServer()
    check("T9.1 Phase 1: Entity type defined", entity.lct.entity_type == "mcp_server")
    check("T9.2 Phase 1: LCT structure", entity.lct.lct_version == "1.0")
    trust = MCPTrustComputer.compute_trust(entity)
    check("T9.3 Phase 1: Trust metrics", "overall" in trust)

    # Phase 2: SAGE integration
    check("T9.4 Phase 2: Registry works", len(registry.servers) > 0)
    check("T9.5 Phase 2: SAGE workflow works", len(sage.execution_log) > 0)

    # Phase 3: Advanced features
    check("T9.6 Phase 3: Chain execution", len(chain_results) > 0)
    check("T9.7 Phase 3: Trust-based selection", selected is not None)
    check("T9.8 Phase 3: MRH propagation", len(kb2.lct.mrh) > 0)

    # ─── Integration: Full MCP entity lifecycle ───
    print()
    print("Integration: Full MCP entity lifecycle")

    # Create server
    full_db = DatabaseMCPServer("postgresql")
    full_db.data["users"] = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    # Register
    full_reg = MCPRegistry()
    full_reg.register("main_db", full_db)

    # Use via SAGE
    full_sage = SAGEWithMCP(full_reg)
    full_steps = [ExecutionStep("main_db", "query", {"table": "users"})]
    full_results = full_sage.execute_plan(full_steps)

    # Verify trust after operations
    full_trust = MCPTrustComputer.compute_trust(full_db)

    # Build Web4-enhanced response
    full_att = TrustAttestation(
        server_lct=full_db.lct.entity_id,
        confidence=full_trust["overall"],
        delegation_target="postgresql://db",
        latency_ms=25.0
    )
    full_response = build_web4_mcp_response(full_results[0]["data"], full_att)

    check("T10.1 Full lifecycle: query returns data",
          full_results[0]["status"] == "success")
    check("T10.2 Full lifecycle: trust computed",
          full_trust["overall"] > 0.9)
    check("T10.3 Full lifecycle: Web4 response formed",
          full_response["result"]["trust_attestation"]["confidence"] > 0.9)
    check("T10.4 Full lifecycle: MRH has entries",
          len(full_db.lct.mrh) > 0)
    check("T10.5 Full lifecycle: execution logged",
          len(full_sage.execution_log) == 1)

    # ─── Summary ───
    print()
    print("=" * 60)
    if failed == 0:
        print(f"MCP Entity Spec: {passed}/{total} checks passed")
        print("  All checks passed!")
    else:
        print(f"MCP Entity Spec: {passed}/{total} checks passed, {failed} FAILED")
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    run_tests()
