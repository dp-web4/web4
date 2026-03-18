"""
Web4 MCP Protocol Types

Canonical implementation per web4-standard/core-spec/mcp-protocol.md.

Typed dataclasses for Web4's Model Context Protocol integration:
- Communication patterns (§2.2): Request-Response, Delegation, Observation, Broadcast
- Web4 context headers (§4.1): Trust context, agency proofs, MRH scope
- MCP resource types (§6): Tool, Prompt, Context resources with ATP costs
- Session management (§11): Stateful sessions, handoff, context preservation
- ATP metering (§9): Cost calculation with trust discounts and demand modifiers
- Trust requirements (§4.2): T3 minimums, ATP stakes, role requirements

Types only — no networking, no JSON-RPC, no SPARQL.
Composes with: web4.lct, web4.trust, web4.atp, web4.errors, web4.entity.

Validated against: web4-standard/test-vectors/mcp/
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Communication Patterns (spec §2.2) ──────────────────────────

class CommunicationPattern(str, Enum):
    """MCP communication patterns aligned with Web4 relationships (§2.2)."""
    REQUEST_RESPONSE = "request_response"  # Pairing relationship
    DELEGATION = "delegation"              # Binding relationship
    OBSERVATION = "observation"            # Witnessing relationship
    BROADCAST = "broadcast"               # Announcement relationship


# ── Trust Dimensions (spec §2.3) ─────────────────────────────────

class TrustDimension(str, Enum):
    """Trust dimensions carried in MCP interactions (§2.3)."""
    SENDER = "sender"      # T3/V3 of requesting entity
    CHANNEL = "channel"    # Security/reliability of connection
    CONTENT = "content"    # Verifiability of exchanged data
    RESULT = "result"      # Confidence in response accuracy


# ── MCP Resource Types (spec §6) ─────────────────────────────────

class MCPResourceType(str, Enum):
    """Types of resources exposed via MCP (§6)."""
    TOOL = "mcp_tool"
    PROMPT = "mcp_prompt"
    CONTEXT = "mcp_context"


@dataclass(frozen=True)
class ResourceRequirements:
    """Compute/memory/ATP requirements for an MCP resource (§6.1)."""
    compute: str = "low"         # low / medium / high
    memory: str = "256MB"
    atp_cost: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {"compute": self.compute, "memory": self.memory, "atp_cost": self.atp_cost}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ResourceRequirements:
        return cls(
            compute=d.get("compute", "low"),
            memory=d.get("memory", "256MB"),
            atp_cost=d.get("atp_cost", 1),
        )


@dataclass(frozen=True)
class TrustRequirements:
    """Minimum trust thresholds for accessing an MCP resource (§4.2, §6.1)."""
    minimum_t3: Dict[str, float] = field(default_factory=dict)  # dimension → min value
    atp_stake: int = 0
    role_required: Optional[str] = None

    def is_met(self, t3: Dict[str, float], atp_available: int, role: Optional[str] = None) -> bool:
        """Check whether the provided trust context meets these requirements."""
        for dim, minimum in self.minimum_t3.items():
            if t3.get(dim, 0.0) < minimum:
                return False
        if atp_available < self.atp_stake:
            return False
        if self.role_required and role != self.role_required:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.minimum_t3:
            d["minimum_t3"] = dict(self.minimum_t3)
        if self.atp_stake:
            d["atp_stake"] = self.atp_stake
        if self.role_required:
            d["role_required"] = self.role_required
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TrustRequirements:
        return cls(
            minimum_t3=d.get("minimum_t3", {}),
            atp_stake=d.get("atp_stake", 0),
            role_required=d.get("role_required"),
        )


@dataclass(frozen=True)
class MCPToolResource:
    """An MCP tool resource definition (§6.1)."""
    name: str
    description: str = ""
    resource_requirements: ResourceRequirements = field(default_factory=ResourceRequirements)
    trust_requirements: TrustRequirements = field(default_factory=TrustRequirements)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": MCPResourceType.TOOL.value,
            "name": self.name,
            "description": self.description,
            "resource_requirements": self.resource_requirements.to_dict(),
            "trust_requirements": self.trust_requirements.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MCPToolResource:
        return cls(
            name=d["name"],
            description=d.get("description", ""),
            resource_requirements=ResourceRequirements.from_dict(d.get("resource_requirements", {})),
            trust_requirements=TrustRequirements.from_dict(d.get("trust_requirements", {})),
        )


@dataclass(frozen=True)
class MCPPromptResource:
    """An MCP prompt resource definition (§6.2)."""
    name: str
    template: str = ""
    variables: List[str] = field(default_factory=list)
    expected_output: str = "text"
    atp_cost: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": MCPResourceType.PROMPT.value,
            "name": self.name,
            "template": self.template,
            "variables": list(self.variables),
            "expected_output": self.expected_output,
            "atp_cost": self.atp_cost,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MCPPromptResource:
        return cls(
            name=d["name"],
            template=d.get("template", ""),
            variables=d.get("variables", []),
            expected_output=d.get("expected_output", "text"),
            atp_cost=d.get("atp_cost", 1),
        )


# ── Web4 Context Headers (spec §4.1) ────────────────────────────

@dataclass(frozen=True)
class ProofOfAgency:
    """Agency delegation proof attached to MCP requests (§4.1)."""
    grant_id: str
    scope: str

    def to_dict(self) -> Dict[str, Any]:
        return {"grant_id": self.grant_id, "scope": self.scope}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ProofOfAgency:
        return cls(grant_id=d["grant_id"], scope=d["scope"])


@dataclass(frozen=True)
class TrustContext:
    """Trust information carried in Web4 MCP context (§4.1)."""
    t3_in_role: Dict[str, float] = field(default_factory=dict)
    atp_stake: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.t3_in_role:
            d["t3_in_role"] = dict(self.t3_in_role)
        if self.atp_stake:
            d["atp_stake"] = self.atp_stake
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TrustContext:
        return cls(
            t3_in_role=d.get("t3_in_role", {}),
            atp_stake=d.get("atp_stake", 0),
        )


@dataclass(frozen=True)
class Web4Context:
    """Web4 context headers included in every MCP message (§4.1).

    Every MCP interaction carries identity, trust, scope, and governance context.
    """
    sender_lct: str
    sender_role: str = ""
    trust_context: TrustContext = field(default_factory=TrustContext)
    mrh_depth: int = 1
    society: str = ""
    law_hash: str = ""
    proof_of_agency: Optional[ProofOfAgency] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "sender_lct": self.sender_lct,
        }
        if self.sender_role:
            d["sender_role"] = self.sender_role
        d["trust_context"] = self.trust_context.to_dict()
        d["mrh_depth"] = self.mrh_depth
        if self.society:
            d["society"] = self.society
        if self.law_hash:
            d["law_hash"] = self.law_hash
        if self.proof_of_agency:
            d["proof_of_agency"] = self.proof_of_agency.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Web4Context:
        poa = d.get("proof_of_agency")
        return cls(
            sender_lct=d["sender_lct"],
            sender_role=d.get("sender_role", ""),
            trust_context=TrustContext.from_dict(d.get("trust_context", {})),
            mrh_depth=d.get("mrh_depth", 1),
            society=d.get("society", ""),
            law_hash=d.get("law_hash", ""),
            proof_of_agency=ProofOfAgency.from_dict(poa) if poa else None,
        )


# ── Witness Attestation (spec §4.3) ─────────────────────────────

@dataclass(frozen=True)
class WitnessedInteraction:
    """A witnessed MCP interaction record (§4.3)."""
    client: str
    server: str
    action: str
    timestamp: str
    success: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client": self.client,
            "server": self.server,
            "action": self.action,
            "timestamp": self.timestamp,
            "success": self.success,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> WitnessedInteraction:
        return cls(
            client=d["client"],
            server=d["server"],
            action=d["action"],
            timestamp=d["timestamp"],
            success=d["success"],
        )


@dataclass(frozen=True)
class WitnessAttestation:
    """Witness attestation for an MCP interaction (§4.3)."""
    witnessed_interaction: WitnessedInteraction
    witness: str
    signature: str = ""
    mrh_updates: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "witnessed_interaction": self.witnessed_interaction.to_dict(),
            "witness": self.witness,
        }
        if self.signature:
            d["signature"] = self.signature
        if self.mrh_updates:
            d["mrh_updates"] = list(self.mrh_updates)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> WitnessAttestation:
        return cls(
            witnessed_interaction=WitnessedInteraction.from_dict(d["witnessed_interaction"]),
            witness=d["witness"],
            signature=d.get("signature", ""),
            mrh_updates=d.get("mrh_updates", []),
        )


# ── MCP Server/Client Capabilities (spec §3, §8) ────────────────

@dataclass(frozen=True)
class MCPCapabilities:
    """Capability advertisement for an MCP entity (§3, §8.1)."""
    tools: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=lambda: ["mcp/1.0", "web4/1.0"])
    trust_requirements: TrustRequirements = field(default_factory=TrustRequirements)
    availability: float = 0.99

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tools": list(self.tools),
            "protocols": list(self.protocols),
            "trust_requirements": self.trust_requirements.to_dict(),
            "availability": self.availability,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MCPCapabilities:
        return cls(
            tools=d.get("tools", []),
            protocols=d.get("protocols", ["mcp/1.0", "web4/1.0"]),
            trust_requirements=TrustRequirements.from_dict(d.get("trust_requirements", {})),
            availability=d.get("availability", 0.99),
        )


@dataclass(frozen=True)
class CapabilityBroadcast:
    """Capability broadcast message from an MCP server (§8.1)."""
    server_lct: str
    capabilities: MCPCapabilities
    ttl: int = 3600
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "broadcast_type": "mcp_capabilities",
            "server": self.server_lct,
            "capabilities": self.capabilities.to_dict(),
            "ttl": self.ttl,
        }
        if self.signature:
            d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CapabilityBroadcast:
        return cls(
            server_lct=d["server"],
            capabilities=MCPCapabilities.from_dict(d.get("capabilities", {})),
            ttl=d.get("ttl", 3600),
            signature=d.get("signature", ""),
        )


# ── MCP Authority (spec §7.2) ───────────────────────────────────

@dataclass(frozen=True)
class MCPAuthority:
    """Delegated authority held by an MCP server (§7.2)."""
    server_lct: str
    delegated_from: str
    resources: List[str] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)
    max_atp_per_request: int = 100
    rate_limit: str = "1000/hour"
    valid_until: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "server": self.server_lct,
            "delegated_from": self.delegated_from,
            "resources": list(self.resources),
            "operations": list(self.operations),
            "max_atp_per_request": self.max_atp_per_request,
            "rate_limit": self.rate_limit,
            "valid_until": self.valid_until,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MCPAuthority:
        return cls(
            server_lct=d["server"],
            delegated_from=d["delegated_from"],
            resources=d.get("resources", []),
            operations=d.get("operations", []),
            max_atp_per_request=d.get("max_atp_per_request", 100),
            rate_limit=d.get("rate_limit", "1000/hour"),
            valid_until=d.get("valid_until", ""),
        )


# ── Session Management (spec §11) ───────────────────────────────

@dataclass
class MCPSession:
    """Stateful MCP session with context preservation (§11.1)."""
    session_id: str
    client_lct: str
    server_lct: str
    established: str = ""
    timeout: int = 3600
    atp_consumed: int = 0
    atp_remaining: int = 100
    interaction_count: int = 0
    active: bool = True

    def consume_atp(self, amount: int) -> bool:
        """Consume ATP for an interaction. Returns False if insufficient."""
        if amount > self.atp_remaining:
            return False
        self.atp_consumed += amount
        self.atp_remaining -= amount
        self.interaction_count += 1
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "client": self.client_lct,
            "server": self.server_lct,
            "established": self.established,
            "timeout": self.timeout,
            "atp_consumed": self.atp_consumed,
            "atp_remaining": self.atp_remaining,
            "interaction_count": self.interaction_count,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MCPSession:
        return cls(
            session_id=d["session_id"],
            client_lct=d["client"],
            server_lct=d["server"],
            established=d.get("established", ""),
            timeout=d.get("timeout", 3600),
            atp_consumed=d.get("atp_consumed", 0),
            atp_remaining=d.get("atp_remaining", 100),
            interaction_count=d.get("interaction_count", 0),
            active=d.get("active", True),
        )


@dataclass(frozen=True)
class SessionHandoff:
    """Session transfer between MCP servers (§11.2)."""
    session_id: str
    from_server: str
    to_server: str
    client_consent_signature: str = ""
    trust_proofs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "session_id": self.session_id,
            "from_server": self.from_server,
            "to_server": self.to_server,
        }
        if self.client_consent_signature:
            d["client_consent"] = self.client_consent_signature
        if self.trust_proofs:
            d["trust_proofs"] = list(self.trust_proofs)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SessionHandoff:
        return cls(
            session_id=d["session_id"],
            from_server=d["from_server"],
            to_server=d["to_server"],
            client_consent_signature=d.get("client_consent", ""),
            trust_proofs=d.get("trust_proofs", []),
        )


# ── ATP Metering (spec §9) ──────────────────────────────────────

@dataclass(frozen=True)
class PricingModifiers:
    """Dynamic pricing modifiers for MCP interactions (§9.2)."""
    high_trust_discount: float = 0.8
    peak_demand_surge: float = 1.5
    bulk_discount: float = 0.9

    def to_dict(self) -> Dict[str, Any]:
        return {
            "high_trust_discount": self.high_trust_discount,
            "peak_demand_surge": self.peak_demand_surge,
            "bulk_discount": self.bulk_discount,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PricingModifiers:
        return cls(
            high_trust_discount=d.get("high_trust_discount", 0.8),
            peak_demand_surge=d.get("peak_demand_surge", 1.5),
            bulk_discount=d.get("bulk_discount", 0.9),
        )


def calculate_mcp_cost(
    base_cost: int,
    trust_average: float = 0.5,
    complexity_factor: float = 1.0,
    atp_cap: Optional[int] = None,
) -> int:
    """Calculate ATP cost for an MCP interaction (§9.1).

    Higher trust → lower cost (up to 20% discount).
    Returns integer ATP amount, respecting optional cap.
    """
    trust_modifier = 1.0 - (min(max(trust_average, 0.0), 1.0) * 0.2)
    total = base_cost * trust_modifier * max(complexity_factor, 0.0)
    result = max(1, int(total + 0.5))  # Round, minimum 1 ATP
    if atp_cap is not None:
        result = min(result, atp_cap)
    return result


# ── MCP Error Context (spec §10) ────────────────────────────────

@dataclass(frozen=True)
class MCPErrorContext:
    """Web4-specific error context attached to MCP error responses (§10.2)."""
    error_type: str
    required_t3: Dict[str, float] = field(default_factory=dict)
    provided_t3: Dict[str, float] = field(default_factory=dict)
    suggestion: str = ""
    error_witnessed: bool = False
    witness_lct: str = ""
    trust_impact: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"error_type": self.error_type}
        if self.required_t3:
            d["required_t3"] = dict(self.required_t3)
        if self.provided_t3:
            d["provided_t3"] = dict(self.provided_t3)
        if self.suggestion:
            d["suggestion"] = self.suggestion
        d["error_witnessed"] = self.error_witnessed
        if self.witness_lct:
            d["witness"] = self.witness_lct
        if self.trust_impact:
            d["trust_impact"] = dict(self.trust_impact)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MCPErrorContext:
        return cls(
            error_type=d["error_type"],
            required_t3=d.get("required_t3", {}),
            provided_t3=d.get("provided_t3", {}),
            suggestion=d.get("suggestion", ""),
            error_witnessed=d.get("error_witnessed", False),
            witness_lct=d.get("witness", ""),
            trust_impact=d.get("trust_impact", {}),
        )


# ── JSON Helpers ─────────────────────────────────────────────────

def web4_context_to_json(ctx: Web4Context) -> str:
    """Serialize Web4Context to JSON string."""
    return json.dumps(ctx.to_dict(), sort_keys=True)


def web4_context_from_json(s: str) -> Web4Context:
    """Deserialize Web4Context from JSON string."""
    return Web4Context.from_dict(json.loads(s))
