#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Web4 MCP Server - web4.io/ namespace prototype
# https://github.com/dp-web4/web4

"""
Web4 MCP Server

Implements Model Context Protocol server exposing Web4 capabilities:
- web4.io/trust - Trust tensor operations
- web4.io/lct - Linked Context Token management
- web4.io/heartbeat - Timing coherence tracking
- web4.io/session - Session management

This is a reference implementation for Claude Code and other MCP clients.
"""

import json
import sys
import os
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Web4 state directory
WEB4_DIR = Path.home() / ".web4"

# Add claude-code-plugin to path for governance imports
PLUGIN_DIR = Path(__file__).parent.parent / "claude-code-plugin"
sys.path.insert(0, str(PLUGIN_DIR))

# Try to import governance module
try:
    from governance import Ledger, SoftLCT, SessionManager, EntityTrustStore, EntityTrust
    GOVERNANCE_AVAILABLE = True
except ImportError:
    GOVERNANCE_AVAILABLE = False
    EntityTrustStore = None
    EntityTrust = None

# MCP Protocol version
MCP_VERSION = "2024-11-05"


class MCPServer:
    """
    Web4 MCP Server implementation.

    Handles JSON-RPC 2.0 over stdio.
    """

    def __init__(self):
        self.tools = self._register_tools()
        self.resources = self._register_resources()
        self.prompts = self._register_prompts()

        # Session state
        self.sessions: Dict[str, dict] = {}

    def _register_tools(self) -> Dict[str, dict]:
        """Register available tools in web4.io/ namespace."""
        return {
            "web4.io/trust/query": {
                "description": "Query trust tensor for an entity in a role",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "Entity LCT or identifier"
                        },
                        "role": {
                            "type": "string",
                            "description": "Role context for trust query"
                        }
                    },
                    "required": ["entity_id"]
                }
            },
            "web4.io/trust/update": {
                "description": "Update trust tensor based on action outcome",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "role": {"type": "string"},
                        "outcome": {
                            "type": "string",
                            "enum": ["success", "failure", "partial"]
                        },
                        "magnitude": {
                            "type": "number",
                            "description": "Update magnitude 0.0-1.0"
                        }
                    },
                    "required": ["entity_id", "role", "outcome"]
                }
            },
            "web4.io/lct/create": {
                "description": "Create a new Linked Context Token",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "binding": {
                            "type": "string",
                            "enum": ["software", "hardware", "tpm"],
                            "description": "Token binding type"
                        },
                        "label": {
                            "type": "string",
                            "description": "Human-readable label"
                        }
                    }
                }
            },
            "web4.io/lct/verify": {
                "description": "Verify LCT signature",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lct_id": {"type": "string"},
                        "data": {"type": "string"},
                        "signature": {"type": "string"}
                    },
                    "required": ["lct_id", "data", "signature"]
                }
            },
            "web4.io/heartbeat/record": {
                "description": "Record a heartbeat event",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "action": {"type": "string"},
                        "action_index": {"type": "integer"}
                    },
                    "required": ["session_id", "action"]
                }
            },
            "web4.io/heartbeat/coherence": {
                "description": "Query timing coherence for session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "window": {
                            "type": "integer",
                            "description": "Number of recent entries to consider"
                        }
                    },
                    "required": ["session_id"]
                }
            },
            "web4.io/session/status": {
                "description": "Get current session status and health",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"}
                    },
                    "required": ["session_id"]
                }
            },
            "web4.io/heartbeat/verify": {
                "description": "Verify a heartbeat chain (for cross-machine trust)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entries": {
                            "type": "array",
                            "description": "List of heartbeat entries to verify",
                            "items": {"type": "object"}
                        }
                    },
                    "required": ["entries"]
                }
            },
            "web4.io/heartbeat/export": {
                "description": "Export session heartbeats for remote verification",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"}
                    },
                    "required": ["session_id"]
                }
            },
            "web4.io/ledger/session/start": {
                "description": "Start a new governed session with identity and ATP budget",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project": {"type": "string", "description": "Project name"},
                        "atp_budget": {"type": "integer", "description": "Action budget", "default": 100}
                    },
                    "required": ["project"]
                }
            },
            "web4.io/ledger/session/end": {
                "description": "End current session and get summary",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "status": {"type": "string", "enum": ["completed", "aborted", "error"]}
                    },
                    "required": ["session_id"]
                }
            },
            "web4.io/ledger/audit/query": {
                "description": "Query audit trail for a session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"}
                    },
                    "required": ["session_id"]
                }
            },
            "web4.io/ledger/audit/verify": {
                "description": "Verify audit trail witnessing chain integrity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"}
                    },
                    "required": ["session_id"]
                }
            },
            "web4.io/ledger/identity": {
                "description": "Get current soft LCT identity",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "web4.io/agent/context": {
                "description": "Get full context for an agent role (trust, references, capabilities)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "role_id": {"type": "string", "description": "Agent role identifier"}
                    },
                    "required": ["role_id"]
                }
            },
            "web4.io/agent/spawn": {
                "description": "Record agent spawn and get role context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "agent_name": {"type": "string", "description": "Agent role identifier"}
                    },
                    "required": ["session_id", "agent_name"]
                }
            },
            "web4.io/agent/complete": {
                "description": "Record agent completion and update trust",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "agent_name": {"type": "string"},
                        "success": {"type": "boolean"}
                    },
                    "required": ["session_id", "agent_name", "success"]
                }
            },
            "web4.io/agent/reference/add": {
                "description": "Add a learned reference for an agent role",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "role_id": {"type": "string"},
                        "content": {"type": "string", "description": "Reference content"},
                        "source": {"type": "string", "description": "Where it came from"},
                        "ref_type": {"type": "string", "enum": ["pattern", "fact", "preference", "context", "summary"]}
                    },
                    "required": ["role_id", "content", "source"]
                }
            },
            "web4.io/agent/roles": {
                "description": "List all known agent roles with trust levels",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            # Entity Trust Tools (MCP servers, references, etc.)
            "web4.io/entity/trust": {
                "description": "Query trust for any Web4 entity (MCP server, role, reference)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {
                            "type": "string",
                            "description": "Entity ID (e.g., mcp:filesystem, role:code-reviewer, ref:abc123)"
                        }
                    },
                    "required": ["entity_id"]
                }
            },
            "web4.io/entity/witness": {
                "description": "Record a witnessing event between two entities",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "witness_id": {
                            "type": "string",
                            "description": "Entity doing the witnessing (e.g., session:abc)"
                        },
                        "target_id": {
                            "type": "string",
                            "description": "Entity being witnessed (e.g., mcp:filesystem)"
                        },
                        "success": {
                            "type": "boolean",
                            "description": "Whether the witnessed action succeeded"
                        },
                        "magnitude": {
                            "type": "number",
                            "description": "Update magnitude (0.0-1.0)"
                        }
                    },
                    "required": ["witness_id", "target_id", "success"]
                }
            },
            "web4.io/entity/list": {
                "description": "List all entities of a given type",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "Entity type (mcp, role, ref, session)",
                            "enum": ["mcp", "role", "ref", "session"]
                        }
                    }
                }
            },
            "web4.io/entity/chain": {
                "description": "Get witnessing chain for an entity (who witnessed whom)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string"},
                        "depth": {"type": "integer", "description": "Chain depth to return"}
                    },
                    "required": ["entity_id"]
                }
            },
            "web4.io/mcp/trust": {
                "description": "Update MCP server trust after a tool call",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_name": {
                            "type": "string",
                            "description": "MCP server name (e.g., filesystem, web4)"
                        },
                        "success": {"type": "boolean"},
                        "session_id": {
                            "type": "string",
                            "description": "Session witnessing the MCP call"
                        }
                    },
                    "required": ["server_name", "success"]
                }
            }
        }

    def _register_resources(self) -> Dict[str, dict]:
        """Register available resources."""
        return {
            "web4://trust/{entity_id}": {
                "description": "Trust tensor for an entity",
                "mimeType": "application/json"
            },
            "web4://heartbeat/{session_id}": {
                "description": "Heartbeat ledger for a session",
                "mimeType": "application/json"
            },
            "web4://session/{session_id}": {
                "description": "Session state and audit trail",
                "mimeType": "application/json"
            }
        }

    def _register_prompts(self) -> Dict[str, dict]:
        """Register available prompts."""
        return {
            "web4.io/analyze-trust": {
                "description": "Analyze trust patterns for an entity",
                "arguments": [
                    {"name": "entity_id", "description": "Entity to analyze", "required": True},
                    {"name": "role", "description": "Role context", "required": False}
                ]
            },
            "web4.io/audit-session": {
                "description": "Generate audit report for a session",
                "arguments": [
                    {"name": "session_id", "description": "Session to audit", "required": True}
                ]
            }
        }

    def handle_request(self, request: dict) -> dict:
        """Handle incoming JSON-RPC request."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "tools/list":
                result = self._handle_tools_list()
            elif method == "tools/call":
                result = self._handle_tools_call(params)
            elif method == "resources/list":
                result = self._handle_resources_list()
            elif method == "resources/read":
                result = self._handle_resources_read(params)
            elif method == "prompts/list":
                result = self._handle_prompts_list()
            elif method == "prompts/get":
                result = self._handle_prompts_get(params)
            elif method == "notifications/initialized":
                return None  # No response for notifications
            else:
                return self._error_response(request_id, -32601, f"Method not found: {method}")

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except Exception as e:
            return self._error_response(request_id, -32603, str(e))

    def _error_response(self, request_id: Any, code: int, message: str) -> dict:
        """Create error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    def _handle_initialize(self, params: dict) -> dict:
        """Handle initialize request."""
        return {
            "protocolVersion": MCP_VERSION,
            "capabilities": {
                "tools": {},
                "resources": {"subscribe": False},
                "prompts": {}
            },
            "serverInfo": {
                "name": "web4-mcp-server",
                "version": "0.1.0"
            }
        }

    def _handle_tools_list(self) -> dict:
        """List available tools."""
        tools = []
        for name, info in self.tools.items():
            tools.append({
                "name": name,
                "description": info["description"],
                "inputSchema": info["inputSchema"]
            })
        return {"tools": tools}

    def _handle_tools_call(self, params: dict) -> dict:
        """Execute a tool call."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Route to specific tool handler
        if tool_name == "web4.io/trust/query":
            result = self._tool_trust_query(arguments)
        elif tool_name == "web4.io/trust/update":
            result = self._tool_trust_update(arguments)
        elif tool_name == "web4.io/lct/create":
            result = self._tool_lct_create(arguments)
        elif tool_name == "web4.io/lct/verify":
            result = self._tool_lct_verify(arguments)
        elif tool_name == "web4.io/heartbeat/record":
            result = self._tool_heartbeat_record(arguments)
        elif tool_name == "web4.io/heartbeat/coherence":
            result = self._tool_heartbeat_coherence(arguments)
        elif tool_name == "web4.io/session/status":
            result = self._tool_session_status(arguments)
        elif tool_name == "web4.io/heartbeat/verify":
            result = self._tool_heartbeat_verify(arguments)
        elif tool_name == "web4.io/heartbeat/export":
            result = self._tool_heartbeat_export(arguments)
        elif tool_name == "web4.io/ledger/session/start":
            result = self._tool_ledger_session_start(arguments)
        elif tool_name == "web4.io/ledger/session/end":
            result = self._tool_ledger_session_end(arguments)
        elif tool_name == "web4.io/ledger/audit/query":
            result = self._tool_ledger_audit_query(arguments)
        elif tool_name == "web4.io/ledger/audit/verify":
            result = self._tool_ledger_audit_verify(arguments)
        elif tool_name == "web4.io/ledger/identity":
            result = self._tool_ledger_identity(arguments)
        elif tool_name == "web4.io/agent/context":
            result = self._tool_agent_context(arguments)
        elif tool_name == "web4.io/agent/spawn":
            result = self._tool_agent_spawn(arguments)
        elif tool_name == "web4.io/agent/complete":
            result = self._tool_agent_complete(arguments)
        elif tool_name == "web4.io/agent/reference/add":
            result = self._tool_agent_reference_add(arguments)
        elif tool_name == "web4.io/agent/roles":
            result = self._tool_agent_roles(arguments)
        # Entity trust tools
        elif tool_name == "web4.io/entity/trust":
            result = self._tool_entity_trust(arguments)
        elif tool_name == "web4.io/entity/witness":
            result = self._tool_entity_witness(arguments)
        elif tool_name == "web4.io/entity/list":
            result = self._tool_entity_list(arguments)
        elif tool_name == "web4.io/entity/chain":
            result = self._tool_entity_chain(arguments)
        elif tool_name == "web4.io/mcp/trust":
            result = self._tool_mcp_trust(arguments)
        else:
            raise ValueError(f"Tool not implemented: {tool_name}")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }

    # Tool implementations

    def _tool_trust_query(self, args: dict) -> dict:
        """Query trust tensor for entity."""
        entity_id = args.get("entity_id")
        role = args.get("role", "default")

        # Load trust store
        trust_file = WEB4_DIR / "trust" / f"{_safe_filename(entity_id)}.json"

        if trust_file.exists():
            with open(trust_file) as f:
                trust_data = json.load(f)

            role_trust = trust_data.get("roles", {}).get(role, {})
            return {
                "entity_id": entity_id,
                "role": role,
                "t3": role_trust.get("t3", self._default_t3()),
                "v3": role_trust.get("v3", self._default_v3()),
                "last_updated": role_trust.get("last_updated")
            }

        # Return default tensors for unknown entity
        return {
            "entity_id": entity_id,
            "role": role,
            "t3": self._default_t3(),
            "v3": self._default_v3(),
            "note": "New entity - default trust"
        }

    def _tool_trust_update(self, args: dict) -> dict:
        """Update trust tensor based on outcome."""
        entity_id = args.get("entity_id")
        role = args.get("role", "default")
        outcome = args.get("outcome")
        magnitude = args.get("magnitude", 0.1)

        # Load or create trust data
        trust_dir = WEB4_DIR / "trust"
        trust_dir.mkdir(parents=True, exist_ok=True)
        trust_file = trust_dir / f"{_safe_filename(entity_id)}.json"

        if trust_file.exists():
            with open(trust_file) as f:
                trust_data = json.load(f)
        else:
            trust_data = {"entity_id": entity_id, "roles": {}}

        if role not in trust_data["roles"]:
            trust_data["roles"][role] = {
                "t3": self._default_t3(),
                "v3": self._default_v3()
            }

        # Calculate update
        role_data = trust_data["roles"][role]
        t3 = role_data["t3"]

        if outcome == "success":
            delta = magnitude * 0.05  # Small positive
        elif outcome == "failure":
            delta = -magnitude * 0.10  # Larger negative
        else:
            delta = magnitude * 0.02  # Minimal partial

        # Update reliability and consistency
        t3["reliability"] = max(0, min(1, t3["reliability"] + delta))
        t3["consistency"] = max(0, min(1, t3["consistency"] + delta * 0.5))

        role_data["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Save
        with open(trust_file, "w") as f:
            json.dump(trust_data, f, indent=2)

        return {
            "entity_id": entity_id,
            "role": role,
            "outcome": outcome,
            "t3": t3,
            "delta": delta
        }

    def _tool_lct_create(self, args: dict) -> dict:
        """Create a new LCT."""
        binding = args.get("binding", "software")
        label = args.get("label", "")

        # Generate LCT
        seed = f"{datetime.now(timezone.utc).isoformat()}:{uuid.uuid4()}"
        lct_hash = hashlib.sha256(seed.encode()).hexdigest()[:16]
        lct_id = f"lct:web4:{binding}:{lct_hash}"

        lct = {
            "lct_id": lct_id,
            "binding": binding,
            "label": label,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "public_key": None  # Would be filled for hardware binding
        }

        # Store LCT
        lct_dir = WEB4_DIR / "lct"
        lct_dir.mkdir(parents=True, exist_ok=True)
        lct_file = lct_dir / f"{lct_hash}.json"

        with open(lct_file, "w") as f:
            json.dump(lct, f, indent=2)

        return lct

    def _tool_lct_verify(self, args: dict) -> dict:
        """Verify LCT signature."""
        lct_id = args.get("lct_id")
        data = args.get("data")
        signature = args.get("signature")

        # Extract hash from LCT ID
        parts = lct_id.split(":")
        if len(parts) < 4:
            return {"valid": False, "error": "Invalid LCT ID format"}

        lct_hash = parts[-1]
        lct_file = WEB4_DIR / "lct" / f"{lct_hash}.json"

        if not lct_file.exists():
            return {"valid": False, "error": "LCT not found"}

        # For software binding, we just check the LCT exists
        # Real implementation would verify cryptographic signature
        return {
            "valid": True,
            "lct_id": lct_id,
            "binding": "software",
            "note": "Signature verification - software binding (placeholder)"
        }

    def _tool_heartbeat_record(self, args: dict) -> dict:
        """Record a heartbeat."""
        session_id = args.get("session_id")
        action = args.get("action")
        action_index = args.get("action_index", 0)

        heartbeat_dir = WEB4_DIR / "heartbeat"
        heartbeat_dir.mkdir(parents=True, exist_ok=True)
        ledger_file = heartbeat_dir / f"{session_id}.jsonl"

        # Load previous entries for chain
        entries = []
        if ledger_file.exists():
            with open(ledger_file) as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))

        now = datetime.now(timezone.utc)

        if entries:
            last = entries[-1]
            ts = last["timestamp"]
            # Handle both formats: with Z suffix and without
            if ts.endswith("Z"):
                ts = ts[:-1] + "+00:00"
            elif "+" not in ts and "-" not in ts[-6:]:
                ts = ts + "+00:00"
            last_time = datetime.fromisoformat(ts)
            delta = (now - last_time).total_seconds()

            if delta < 30:
                status = "early"
            elif delta <= 90:
                status = "on_time"
            elif delta <= 180:
                status = "late"
            else:
                status = "gap"

            prev_hash = last["entry_hash"]
            sequence = last["sequence"] + 1
        else:
            status = "initial"
            delta = 0.0
            prev_hash = ""
            sequence = 1

        # Compute hash
        hash_input = f"{session_id}:{now.isoformat()}:{prev_hash}:{sequence}"
        entry_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:32]

        # Format timestamp - use Z for UTC
        ts = now.isoformat()
        if ts.endswith("+00:00"):
            ts = ts[:-6] + "Z"

        entry = {
            "sequence": sequence,
            "timestamp": ts,
            "status": status,
            "delta_seconds": round(delta, 2),
            "action": action,
            "action_index": action_index,
            "previous_hash": prev_hash,
            "entry_hash": entry_hash
        }

        # Append
        with open(ledger_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry

    def _tool_heartbeat_coherence(self, args: dict) -> dict:
        """Calculate timing coherence for session."""
        session_id = args.get("session_id")
        window = args.get("window", 10)

        ledger_file = WEB4_DIR / "heartbeat" / f"{session_id}.jsonl"

        if not ledger_file.exists():
            return {"session_id": session_id, "coherence": 1.0, "entries": 0}

        entries = []
        with open(ledger_file) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        if len(entries) < 2:
            return {"session_id": session_id, "coherence": 1.0, "entries": len(entries)}

        # Score recent entries
        recent = entries[-window:] if len(entries) >= window else entries

        scores = []
        for entry in recent:
            status = entry.get("status", "")
            if status in ("initial", "on_time"):
                scores.append(1.0)
            elif status == "early":
                scores.append(0.8)
            elif status == "late":
                scores.append(0.7)
            elif status == "gap":
                scores.append(0.3)
            else:
                scores.append(0.5)

        # Weighted average
        total_weight = 0.0
        weighted_sum = 0.0
        for i, score in enumerate(scores):
            weight = (i + 1) / len(scores)
            weighted_sum += score * weight
            total_weight += weight

        coherence = round(weighted_sum / total_weight, 3) if total_weight > 0 else 1.0

        return {
            "session_id": session_id,
            "coherence": coherence,
            "entries": len(entries),
            "window": len(recent),
            "status_distribution": {s: sum(1 for e in recent if e.get("status") == s)
                                   for s in set(e.get("status") for e in recent)}
        }

    def _tool_session_status(self, args: dict) -> dict:
        """Get session status."""
        session_id = args.get("session_id")

        session_file = WEB4_DIR / "sessions" / f"{session_id}.json"

        if not session_file.exists():
            return {"session_id": session_id, "status": "not_found"}

        with open(session_file) as f:
            session = json.load(f)

        # Get heartbeat coherence
        coherence_result = self._tool_heartbeat_coherence({"session_id": session_id})

        return {
            "session_id": session_id,
            "status": "active",
            "started_at": session.get("started_at"),
            "action_count": session.get("action_count", 0),
            "timing_coherence": coherence_result.get("coherence", 1.0),
            "token_binding": session.get("token", {}).get("binding", "unknown"),
            "audit_level": session.get("preferences", {}).get("audit_level", "standard")
        }

    def _tool_heartbeat_verify(self, args: dict) -> dict:
        """Verify a heartbeat chain for cross-machine trust."""
        entries = args.get("entries", [])

        if not entries:
            return {
                "valid": False,
                "error": "No entries provided",
                "trust_score": 0.0
            }

        errors = []
        warnings = []
        chain_intact = True
        timing_consistent = True
        signatures_present = 0

        for i, entry in enumerate(entries):
            # Check hash chain
            if i > 0:
                prev = entries[i - 1]
                if entry.get("previous_hash") != prev.get("entry_hash"):
                    chain_intact = False
                    errors.append(f"Chain broken at entry {i}")

                # Check sequence
                if entry.get("sequence", 0) != prev.get("sequence", 0) + 1:
                    warnings.append(f"Sequence gap at entry {i}")

                # Check timing
                try:
                    prev_ts = prev["timestamp"]
                    curr_ts = entry["timestamp"]

                    # Normalize timestamps
                    if prev_ts.endswith("Z"):
                        prev_ts = prev_ts[:-1] + "+00:00"
                    if curr_ts.endswith("Z"):
                        curr_ts = curr_ts[:-1] + "+00:00"

                    from datetime import datetime
                    prev_time = datetime.fromisoformat(prev_ts)
                    curr_time = datetime.fromisoformat(curr_ts)

                    if curr_time < prev_time:
                        timing_consistent = False
                        errors.append(f"Negative time delta at entry {i}")
                except (KeyError, ValueError) as e:
                    warnings.append(f"Cannot parse timestamp at entry {i}")

            # Check for signatures
            if entry.get("signature"):
                signatures_present += 1

        # Compute trust score
        score = 0.0
        if len(entries) >= 5:
            if chain_intact:
                score += 0.3
            if timing_consistent:
                score += 0.2
            sig_ratio = signatures_present / len(entries) if entries else 0
            score += 0.4 * sig_ratio
            if any(e.get("binding_type") == "tpm" for e in entries):
                score += 0.1

        valid = chain_intact and timing_consistent and not errors

        return {
            "valid": valid,
            "entries_verified": len(entries),
            "chain_intact": chain_intact,
            "timing_consistent": timing_consistent,
            "signatures_present": signatures_present,
            "trust_score": round(score, 3),
            "errors": errors,
            "warnings": warnings
        }

    def _tool_heartbeat_export(self, args: dict) -> dict:
        """Export session heartbeats for remote verification."""
        session_id = args.get("session_id")

        ledger_file = WEB4_DIR / "heartbeat" / f"{session_id}.jsonl"

        if not ledger_file.exists():
            return {
                "session_id": session_id,
                "error": "Session not found",
                "entries": []
            }

        entries = []
        with open(ledger_file) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        return {
            "session_id": session_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "entry_count": len(entries),
            "entries": entries,
            "source_machine": hashlib.sha256(
                os.uname().nodename.encode()
            ).hexdigest()[:8]
        }

    # --- Governance Ledger Tools ---

    def _tool_ledger_session_start(self, args: dict) -> dict:
        """Start a new governed session."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available", "governance_available": False}

        project = args.get("project", "default")
        atp_budget = args.get("atp_budget", 100)

        try:
            manager = SessionManager()
            session = manager.start_session(project=project, atp_budget=atp_budget)
            return {
                "session_id": session["session_id"],
                "session_number": session.get("session_number"),
                "lct_id": session["lct_id"],
                "project": project,
                "atp_budget": atp_budget,
                "started_at": session["started_at"],
                "governance_available": True
            }
        except Exception as e:
            return {"error": str(e), "governance_available": True}

    def _tool_ledger_session_end(self, args: dict) -> dict:
        """End a session and get summary."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available"}

        session_id = args.get("session_id")
        status = args.get("status", "completed")

        try:
            ledger = Ledger()
            ledger.end_session(session_id, status)
            summary = ledger.get_session_summary(session_id)
            return summary or {"error": "Session not found", "session_id": session_id}
        except Exception as e:
            return {"error": str(e), "session_id": session_id}

    def _tool_ledger_audit_query(self, args: dict) -> dict:
        """Query audit trail for a session."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available"}

        session_id = args.get("session_id")

        try:
            ledger = Ledger()
            records = ledger.get_session_audit_trail(session_id)
            return {
                "session_id": session_id,
                "record_count": len(records),
                "records": records
            }
        except Exception as e:
            return {"error": str(e), "session_id": session_id}

    def _tool_ledger_audit_verify(self, args: dict) -> dict:
        """Verify audit trail witnessing chain."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available"}

        session_id = args.get("session_id")

        try:
            ledger = Ledger()
            is_valid, error = ledger.verify_audit_chain(session_id)
            records = ledger.get_session_audit_trail(session_id)
            return {
                "session_id": session_id,
                "chain_valid": is_valid,
                "error": error,
                "record_count": len(records),
                "verification": "witnessing_chain"
            }
        except Exception as e:
            return {"error": str(e), "session_id": session_id}

    def _tool_ledger_identity(self, args: dict) -> dict:
        """Get current soft LCT identity."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available"}

        try:
            lct = SoftLCT()
            identity = lct.get_or_create()
            verification = lct.verify_local()
            return {
                "lct_id": identity["lct_id"],
                "binding": identity["binding"],
                "created_at": identity["created_at"],
                "verified": verification.get("verified", False),
                "confidence": verification.get("confidence", 0.0),
                "note": identity.get("trust_note", "")
            }
        except Exception as e:
            return {"error": str(e)}

    # --- Agent Governance Tools ---

    def _tool_agent_context(self, args: dict) -> dict:
        """Get full context for an agent role."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available"}

        role_id = args.get("role_id")

        try:
            from governance import AgentGovernance
            gov = AgentGovernance()
            return gov.get_role_context(role_id)
        except Exception as e:
            return {"error": str(e), "role_id": role_id}

    def _tool_agent_spawn(self, args: dict) -> dict:
        """Record agent spawn and get role context."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available"}

        session_id = args.get("session_id")
        agent_name = args.get("agent_name")

        try:
            from governance import AgentGovernance
            gov = AgentGovernance()
            return gov.on_agent_spawn(session_id, agent_name)
        except Exception as e:
            return {"error": str(e), "session_id": session_id, "agent_name": agent_name}

    def _tool_agent_complete(self, args: dict) -> dict:
        """Record agent completion and update trust."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available"}

        session_id = args.get("session_id")
        agent_name = args.get("agent_name")
        success = args.get("success", True)

        try:
            from governance import AgentGovernance
            gov = AgentGovernance()
            return gov.on_agent_complete(session_id, agent_name, success)
        except Exception as e:
            return {"error": str(e), "session_id": session_id, "agent_name": agent_name}

    def _tool_agent_reference_add(self, args: dict) -> dict:
        """Add a learned reference for an agent role."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available"}

        role_id = args.get("role_id")
        content = args.get("content")
        source = args.get("source")
        ref_type = args.get("ref_type", "context")

        try:
            from governance import ReferenceStore
            refs = ReferenceStore()
            ref = refs.add(role_id, content, source, ref_type)
            return {
                "ref_id": ref.ref_id,
                "role_id": role_id,
                "ref_type": ref_type,
                "content_preview": content[:100]
            }
        except Exception as e:
            return {"error": str(e), "role_id": role_id}

    def _tool_agent_roles(self, args: dict) -> dict:
        """List all known agent roles with trust levels."""
        if not GOVERNANCE_AVAILABLE:
            return {"error": "Governance module not available"}

        try:
            from governance import AgentGovernance
            gov = AgentGovernance()
            roles = gov.get_all_roles()
            return {
                "role_count": len(roles),
                "roles": roles
            }
        except Exception as e:
            return {"error": str(e)}

    # --- Entity Trust Tools ---

    def _tool_entity_trust(self, args: dict) -> dict:
        """Query trust for any Web4 entity."""
        if not GOVERNANCE_AVAILABLE or EntityTrustStore is None:
            return {"error": "Entity trust module not available"}

        entity_id = args.get("entity_id")

        try:
            store = EntityTrustStore()
            trust = store.get(entity_id)
            return {
                "entity_id": entity_id,
                "entity_type": trust.entity_type,
                "entity_name": trust.entity_name,
                "t3_average": round(trust.t3_average(), 3),
                "v3_average": round(trust.v3_average(), 3),
                "trust_level": trust.trust_level(),
                "t3": {
                    "competence": round(trust.competence, 3),
                    "reliability": round(trust.reliability, 3),
                    "consistency": round(trust.consistency, 3),
                    "witnesses": round(trust.witnesses, 3),
                    "lineage": round(trust.lineage, 3),
                    "alignment": round(trust.alignment, 3)
                },
                "witnessing": {
                    "witness_count": trust.witness_count,
                    "witnessed_by": trust.witnessed_by[:10],
                    "has_witnessed": trust.has_witnessed[:10]
                },
                "action_count": trust.action_count,
                "success_count": trust.success_count
            }
        except Exception as e:
            return {"error": str(e), "entity_id": entity_id}

    def _tool_entity_witness(self, args: dict) -> dict:
        """Record a witnessing event between two entities."""
        if not GOVERNANCE_AVAILABLE or EntityTrustStore is None:
            return {"error": "Entity trust module not available"}

        witness_id = args.get("witness_id")
        target_id = args.get("target_id")
        success = args.get("success", True)
        magnitude = args.get("magnitude", 0.1)

        try:
            store = EntityTrustStore()
            witness_trust, target_trust = store.witness(
                witness_id, target_id, success, magnitude
            )
            return {
                "witness": {
                    "entity_id": witness_id,
                    "t3_average": round(witness_trust.t3_average(), 3),
                    "alignment": round(witness_trust.alignment, 3)
                },
                "target": {
                    "entity_id": target_id,
                    "t3_average": round(target_trust.t3_average(), 3),
                    "witnesses_score": round(target_trust.witnesses, 3),
                    "reputation": round(target_trust.reputation, 3)
                },
                "success": success,
                "magnitude": magnitude
            }
        except Exception as e:
            return {"error": str(e)}

    def _tool_entity_list(self, args: dict) -> dict:
        """List all entities of a given type."""
        if not GOVERNANCE_AVAILABLE or EntityTrustStore is None:
            return {"error": "Entity trust module not available"}

        entity_type = args.get("entity_type")

        try:
            store = EntityTrustStore()
            entities = store.list_entities(entity_type)

            # Get summary for each
            summaries = []
            for eid in entities[:50]:  # Limit for performance
                trust = store.get(eid)
                summaries.append({
                    "entity_id": eid,
                    "t3_average": round(trust.t3_average(), 3),
                    "trust_level": trust.trust_level(),
                    "action_count": trust.action_count,
                    "witness_count": trust.witness_count
                })

            return {
                "entity_type": entity_type or "all",
                "count": len(entities),
                "entities": summaries
            }
        except Exception as e:
            return {"error": str(e)}

    def _tool_entity_chain(self, args: dict) -> dict:
        """Get witnessing chain for an entity."""
        if not GOVERNANCE_AVAILABLE or EntityTrustStore is None:
            return {"error": "Entity trust module not available"}

        entity_id = args.get("entity_id")
        depth = args.get("depth", 2)

        try:
            store = EntityTrustStore()
            chain = store.get_witnessing_chain(entity_id, depth)
            return chain
        except Exception as e:
            return {"error": str(e), "entity_id": entity_id}

    def _tool_mcp_trust(self, args: dict) -> dict:
        """Update MCP server trust after a tool call."""
        if not GOVERNANCE_AVAILABLE or EntityTrustStore is None:
            return {"error": "Entity trust module not available"}

        server_name = args.get("server_name")
        success = args.get("success", True)
        session_id = args.get("session_id", "session:current")

        try:
            from governance import update_mcp_trust
            mcp_trust = update_mcp_trust(server_name, success, session_id)
            return {
                "mcp_server": server_name,
                "entity_id": f"mcp:{server_name}",
                "success": success,
                "t3_average": round(mcp_trust.t3_average(), 3),
                "trust_level": mcp_trust.trust_level(),
                "reliability": round(mcp_trust.reliability, 3),
                "action_count": mcp_trust.action_count,
                "success_count": mcp_trust.success_count,
                "witnessed_by": session_id
            }
        except Exception as e:
            return {"error": str(e), "server_name": server_name}

    def _handle_resources_list(self) -> dict:
        """List available resources."""
        resources = []
        for uri, info in self.resources.items():
            resources.append({
                "uri": uri,
                "description": info["description"],
                "mimeType": info["mimeType"]
            })
        return {"resources": resources}

    def _handle_resources_read(self, params: dict) -> dict:
        """Read a resource."""
        uri = params.get("uri", "")

        if uri.startswith("web4://trust/"):
            entity_id = uri.split("/")[-1]
            result = self._tool_trust_query({"entity_id": entity_id})
        elif uri.startswith("web4://heartbeat/"):
            session_id = uri.split("/")[-1]
            result = self._tool_heartbeat_coherence({"session_id": session_id})
        elif uri.startswith("web4://session/"):
            session_id = uri.split("/")[-1]
            result = self._tool_session_status({"session_id": session_id})
        else:
            raise ValueError(f"Unknown resource URI: {uri}")

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }

    def _handle_prompts_list(self) -> dict:
        """List available prompts."""
        prompts = []
        for name, info in self.prompts.items():
            prompts.append({
                "name": name,
                "description": info["description"],
                "arguments": info["arguments"]
            })
        return {"prompts": prompts}

    def _handle_prompts_get(self, params: dict) -> dict:
        """Get a prompt."""
        name = params.get("name", "")
        arguments = params.get("arguments", {})

        if name == "web4.io/analyze-trust":
            entity_id = arguments.get("entity_id", "unknown")
            role = arguments.get("role", "")

            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Analyze the trust patterns for entity '{entity_id}'" +
                               (f" in role '{role}'" if role else "") +
                               ". Consider the T3 tensor dimensions (competence, reliability, consistency, witnesses, lineage, alignment) and V3 tensor dimensions (energy, contribution, stewardship, network, reputation, temporal). Provide insights on trust evolution and recommendations."
                    }
                }
            ]
        elif name == "web4.io/audit-session":
            session_id = arguments.get("session_id", "unknown")

            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Generate an audit report for session '{session_id}'. Review the R6 action chain, heartbeat timing coherence, and overall session health. Identify any anomalies or concerns."
                    }
                }
            ]
        else:
            raise ValueError(f"Unknown prompt: {name}")

        return {"messages": messages}

    def _default_t3(self) -> dict:
        """Default T3 tensor values."""
        return {
            "competence": 0.5,
            "reliability": 0.5,
            "consistency": 0.5,
            "witnesses": 0.5,
            "lineage": 0.5,
            "alignment": 0.5
        }

    def _default_v3(self) -> dict:
        """Default V3 tensor values."""
        return {
            "energy": 0.5,
            "contribution": 0.5,
            "stewardship": 0.5,
            "network": 0.5,
            "reputation": 0.5,
            "temporal": 0.5
        }

    def run(self):
        """Run the MCP server on stdio."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                response = self.handle_request(request)

                if response is not None:
                    print(json.dumps(response), flush=True)

            except json.JSONDecodeError as e:
                error = self._error_response(None, -32700, f"Parse error: {e}")
                print(json.dumps(error), flush=True)
            except Exception as e:
                error = self._error_response(None, -32603, f"Internal error: {e}")
                print(json.dumps(error), flush=True)


def _safe_filename(s: str) -> str:
    """Create safe filename from string."""
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    """Entry point."""
    server = MCPServer()
    server.run()


if __name__ == "__main__":
    main()
