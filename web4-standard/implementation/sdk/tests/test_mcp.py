"""Tests for web4.mcp — MCP protocol types module."""

import json
import pathlib

import pytest

from web4.mcp import (
    CommunicationPattern,
    TrustDimension,
    MCPResourceType,
    ResourceRequirements,
    TrustRequirements,
    MCPToolResource,
    MCPPromptResource,
    ProofOfAgency,
    TrustContext,
    Web4Context,
    WitnessedInteraction,
    WitnessAttestation,
    MCPCapabilities,
    CapabilityBroadcast,
    MCPAuthority,
    MCPSession,
    SessionHandoff,
    PricingModifiers,
    calculate_mcp_cost,
    MCPErrorContext,
    web4_context_to_json,
    web4_context_from_json,
)

VECTORS_DIR = pathlib.Path(__file__).resolve().parents[3] / "test-vectors" / "mcp"


def load_vectors():
    with open(VECTORS_DIR / "mcp-protocol.json") as f:
        return json.load(f)["vectors"]


def vector_by_id(vid: str):
    for v in load_vectors():
        if v["id"] == vid:
            return v
    raise KeyError(vid)


# ── Communication Patterns ──────────────────────────────────────

class TestCommunicationPattern:
    def test_enum_values(self):
        assert CommunicationPattern.REQUEST_RESPONSE.value == "request_response"
        assert CommunicationPattern.DELEGATION.value == "delegation"
        assert CommunicationPattern.OBSERVATION.value == "observation"
        assert CommunicationPattern.BROADCAST.value == "broadcast"

    def test_count(self):
        assert len(CommunicationPattern) == 4

    def test_vector_patterns(self):
        v = vector_by_id("mcp-pattern-001")
        for p in v["input"]["patterns"]:
            assert CommunicationPattern(p["pattern"]) is not None
        assert v["expected"]["count"] == len(CommunicationPattern)


class TestTrustDimension:
    def test_all_dimensions(self):
        assert len(TrustDimension) == 4
        assert TrustDimension.SENDER.value == "sender"
        assert TrustDimension.CHANNEL.value == "channel"
        assert TrustDimension.CONTENT.value == "content"
        assert TrustDimension.RESULT.value == "result"


# ── Resource Types ───────────────────────────────────────────────

class TestMCPResourceType:
    def test_enum_values(self):
        assert MCPResourceType.TOOL.value == "mcp_tool"
        assert MCPResourceType.PROMPT.value == "mcp_prompt"
        assert MCPResourceType.CONTEXT.value == "mcp_context"


class TestResourceRequirements:
    def test_defaults(self):
        r = ResourceRequirements()
        assert r.compute == "low"
        assert r.memory == "256MB"
        assert r.atp_cost == 1

    def test_round_trip(self):
        r = ResourceRequirements(compute="high", memory="4GB", atp_cost=10)
        r2 = ResourceRequirements.from_dict(r.to_dict())
        assert r2 == r


class TestTrustRequirements:
    def test_is_met_passing(self):
        v = vector_by_id("mcp-trust-001")
        reqs = TrustRequirements.from_dict(v["input"]["requirements"])
        p = v["input"]["provided"]
        assert reqs.is_met(p["t3"], p["atp_available"], p["role"]) == v["expected"]["is_met"]

    def test_is_met_failing(self):
        v = vector_by_id("mcp-trust-002")
        reqs = TrustRequirements.from_dict(v["input"]["requirements"])
        p = v["input"]["provided"]
        assert reqs.is_met(p["t3"], p["atp_available"], p.get("role")) == v["expected"]["is_met"]

    def test_atp_insufficient(self):
        reqs = TrustRequirements(atp_stake=50)
        assert not reqs.is_met({}, 10)

    def test_role_mismatch(self):
        reqs = TrustRequirements(role_required="web4:Admin")
        assert not reqs.is_met({}, 100, "web4:User")

    def test_empty_requirements_always_met(self):
        reqs = TrustRequirements()
        assert reqs.is_met({}, 0)

    def test_round_trip(self):
        reqs = TrustRequirements(
            minimum_t3={"talent": 0.5, "training": 0.7},
            atp_stake=10,
            role_required="web4:Analyst",
        )
        reqs2 = TrustRequirements.from_dict(reqs.to_dict())
        assert reqs2 == reqs


# ── MCP Resources ───────────────────────────────────────────────

class TestMCPToolResource:
    def test_round_trip(self):
        tool = MCPToolResource(
            name="analyze_dataset",
            description="Statistical analysis",
            resource_requirements=ResourceRequirements(compute="medium", memory="4GB", atp_cost=10),
            trust_requirements=TrustRequirements(minimum_t3={"training": 0.7}),
        )
        d = tool.to_dict()
        assert d["resource_type"] == "mcp_tool"
        tool2 = MCPToolResource.from_dict(d)
        assert tool2.name == tool.name
        assert tool2.resource_requirements.atp_cost == 10

    def test_minimal(self):
        tool = MCPToolResource(name="simple_tool")
        d = tool.to_dict()
        assert d["name"] == "simple_tool"


class TestMCPPromptResource:
    def test_round_trip(self):
        prompt = MCPPromptResource(
            name="code_review",
            template="Review the following code...",
            variables=["code", "language"],
            expected_output="structured_review",
            atp_cost=5,
        )
        d = prompt.to_dict()
        assert d["resource_type"] == "mcp_prompt"
        prompt2 = MCPPromptResource.from_dict(d)
        assert prompt2 == prompt


# ── Web4 Context ─────────────────────────────────────────────────

class TestWeb4Context:
    def test_full_context(self):
        v = vector_by_id("mcp-ctx-001")
        ctx = Web4Context.from_dict(v["input"])
        assert ctx.sender_lct == v["expected"]["sender_lct"]
        assert ctx.sender_role == v["expected"]["sender_role"]
        assert ctx.mrh_depth == v["expected"]["mrh_depth"]
        assert ctx.society == v["expected"]["society"]
        assert ctx.proof_of_agency is not None
        assert ctx.proof_of_agency.grant_id == "agy:grant:001"

    def test_minimal_context(self):
        v = vector_by_id("mcp-ctx-002")
        ctx = Web4Context.from_dict(v["input"])
        assert ctx.sender_lct == v["expected"]["sender_lct"]
        assert ctx.sender_role == v["expected"]["sender_role"]
        assert ctx.mrh_depth == v["expected"]["mrh_depth"]
        assert ctx.proof_of_agency is None

    def test_round_trip(self):
        ctx = Web4Context(
            sender_lct="lct:web4:client:test",
            sender_role="web4:Developer",
            trust_context=TrustContext(t3_in_role={"talent": 0.8}, atp_stake=25),
            mrh_depth=3,
            society="lct:web4:society:eng",
            proof_of_agency=ProofOfAgency(grant_id="agy:1", scope="code:review"),
        )
        ctx2 = Web4Context.from_dict(ctx.to_dict())
        assert ctx2 == ctx

    def test_json_round_trip(self):
        ctx = Web4Context(sender_lct="lct:test", mrh_depth=2)
        s = web4_context_to_json(ctx)
        ctx2 = web4_context_from_json(s)
        assert ctx2 == ctx


# ── Trust Context ────────────────────────────────────────────────

class TestTrustContext:
    def test_round_trip(self):
        tc = TrustContext(t3_in_role={"training": 0.9}, atp_stake=50)
        tc2 = TrustContext.from_dict(tc.to_dict())
        assert tc2 == tc

    def test_empty(self):
        tc = TrustContext()
        d = tc.to_dict()
        assert "atp_stake" not in d  # zero omitted
        assert "t3_in_role" not in d  # empty omitted


# ── Proof of Agency ──────────────────────────────────────────────

class TestProofOfAgency:
    def test_round_trip(self):
        poa = ProofOfAgency(grant_id="agy:1", scope="data:read")
        poa2 = ProofOfAgency.from_dict(poa.to_dict())
        assert poa2 == poa


# ── Witness Attestation ─────────────────────────────────────────

class TestWitnessAttestation:
    def test_vector(self):
        v = vector_by_id("mcp-witness-001")
        wi = WitnessedInteraction.from_dict(v["input"]["witnessed_interaction"])
        wa = WitnessAttestation(
            witnessed_interaction=wi,
            witness=v["input"]["witness"],
            signature=v["input"]["signature"],
            mrh_updates=v["input"]["mrh_updates"],
        )
        assert wa.witness == v["expected"]["witness"]
        assert wa.witnessed_interaction.success == v["expected"]["success"]
        assert len(wa.mrh_updates) == v["expected"]["mrh_update_count"]

    def test_round_trip(self):
        wi = WitnessedInteraction(
            client="lct:c", server="lct:s", action="query",
            timestamp="2025-01-01T00:00:00Z", success=True,
        )
        wa = WitnessAttestation(witnessed_interaction=wi, witness="lct:w")
        wa2 = WitnessAttestation.from_dict(wa.to_dict())
        assert wa2 == wa


# ── Capabilities & Broadcast ────────────────────────────────────

class TestMCPCapabilities:
    def test_defaults(self):
        cap = MCPCapabilities()
        assert "mcp/1.0" in cap.protocols
        assert "web4/1.0" in cap.protocols
        assert cap.availability == 0.99

    def test_round_trip(self):
        cap = MCPCapabilities(tools=["query", "compute"], availability=0.999)
        cap2 = MCPCapabilities.from_dict(cap.to_dict())
        assert cap2 == cap


class TestCapabilityBroadcast:
    def test_round_trip(self):
        bc = CapabilityBroadcast(
            server_lct="lct:web4:server:db",
            capabilities=MCPCapabilities(tools=["query"]),
            ttl=7200,
            signature="sig:1",
        )
        d = bc.to_dict()
        assert d["broadcast_type"] == "mcp_capabilities"
        bc2 = CapabilityBroadcast.from_dict(d)
        assert bc2 == bc


# ── MCP Authority ───────────────────────────────────────────────

class TestMCPAuthority:
    def test_round_trip(self):
        auth = MCPAuthority(
            server_lct="lct:server:1",
            delegated_from="lct:org:1",
            resources=["database", "api"],
            operations=["read", "write"],
            max_atp_per_request=200,
            rate_limit="500/hour",
            valid_until="2026-12-31T23:59:59Z",
        )
        auth2 = MCPAuthority.from_dict(auth.to_dict())
        assert auth2 == auth


# ── Sessions ─────────────────────────────────────────────────────

class TestMCPSession:
    def test_consume_atp(self):
        v = vector_by_id("mcp-session-001")
        sess = MCPSession.from_dict(v["input"]["session"])
        results = [sess.consume_atp(amt) for amt in v["input"]["consume"]]
        assert sess.atp_consumed == v["expected"]["atp_consumed"]
        assert sess.atp_remaining == v["expected"]["atp_remaining"]
        assert sess.interaction_count == v["expected"]["interaction_count"]
        assert all(results) == v["expected"]["all_succeeded"]

    def test_consume_atp_exhaustion(self):
        v = vector_by_id("mcp-session-002")
        sess = MCPSession.from_dict(v["input"]["session"])
        results = [sess.consume_atp(amt) for amt in v["input"]["consume"]]
        assert sess.atp_consumed == v["expected"]["atp_consumed"]
        assert sess.atp_remaining == v["expected"]["atp_remaining"]
        assert sess.interaction_count == v["expected"]["interaction_count"]
        assert all(results) == v["expected"]["all_succeeded"]

    def test_round_trip(self):
        sess = MCPSession(
            session_id="s1", client_lct="lct:c", server_lct="lct:s",
            established="2025-01-01T00:00:00Z",
        )
        sess2 = MCPSession.from_dict(sess.to_dict())
        assert sess2.session_id == sess.session_id
        assert sess2.client_lct == sess.client_lct


class TestSessionHandoff:
    def test_vector(self):
        v = vector_by_id("mcp-handoff-001")
        ho = SessionHandoff.from_dict(v["input"])
        assert ho.session_id == v["expected"]["session_id"]
        assert ho.from_server == v["expected"]["from_server"]
        assert ho.to_server == v["expected"]["to_server"]

    def test_round_trip(self):
        ho = SessionHandoff(
            session_id="s1",
            from_server="lct:a",
            to_server="lct:b",
            client_consent_signature="sig:1",
            trust_proofs=["p1", "p2"],
        )
        ho2 = SessionHandoff.from_dict(ho.to_dict())
        assert ho2 == ho


# ── ATP Metering ─────────────────────────────────────────────────

class TestCalculateMCPCost:
    def test_high_trust_discount(self):
        v = vector_by_id("mcp-cost-001")
        inp = v["input"]
        cost = calculate_mcp_cost(inp["base_cost"], inp["trust_average"], inp["complexity_factor"])
        assert cost == v["expected"]["cost"]

    def test_zero_trust_no_discount(self):
        v = vector_by_id("mcp-cost-002")
        inp = v["input"]
        cost = calculate_mcp_cost(inp["base_cost"], inp["trust_average"], inp["complexity_factor"])
        assert cost == v["expected"]["cost"]

    def test_cap_applied(self):
        v = vector_by_id("mcp-cost-003")
        inp = v["input"]
        cost = calculate_mcp_cost(inp["base_cost"], inp["trust_average"], inp["complexity_factor"], inp["atp_cap"])
        assert cost == v["expected"]["cost"]

    def test_minimum_one_atp(self):
        cost = calculate_mcp_cost(base_cost=0, trust_average=1.0)
        assert cost >= 1

    def test_trust_clamped(self):
        cost_normal = calculate_mcp_cost(100, trust_average=1.0)
        cost_over = calculate_mcp_cost(100, trust_average=2.0)
        assert cost_normal == cost_over  # clamped to 1.0


class TestPricingModifiers:
    def test_defaults(self):
        pm = PricingModifiers()
        assert pm.high_trust_discount == 0.8
        assert pm.peak_demand_surge == 1.5
        assert pm.bulk_discount == 0.9

    def test_round_trip(self):
        pm = PricingModifiers(high_trust_discount=0.7, peak_demand_surge=2.0, bulk_discount=0.85)
        pm2 = PricingModifiers.from_dict(pm.to_dict())
        assert pm2 == pm


# ── Error Context ────────────────────────────────────────────────

class TestMCPErrorContext:
    def test_round_trip(self):
        ec = MCPErrorContext(
            error_type="InsufficientTrust",
            required_t3={"training": 0.7},
            provided_t3={"training": 0.5},
            suggestion="Build trust through successful interactions",
            error_witnessed=True,
            witness_lct="lct:witness:1",
            trust_impact={"temperament": -0.01},
        )
        ec2 = MCPErrorContext.from_dict(ec.to_dict())
        assert ec2 == ec

    def test_minimal(self):
        ec = MCPErrorContext(error_type="ResourceUnavailable")
        d = ec.to_dict()
        assert d["error_type"] == "ResourceUnavailable"
        assert not d["error_witnessed"]
