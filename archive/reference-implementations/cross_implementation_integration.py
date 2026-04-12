#!/usr/bin/env python3
"""
Web4 Cross-Implementation Integration Test

Verifies that independently-implemented Web4 reference modules work together
as a coherent system. Each chain exercises data flow across 2-4 implementations.

Integration Chains:
  C1: Society → Treasury → ATP Metering (economic lifecycle)
  C2: T3/V3 Reputation → MCP Trust Gating (trust-based access control)
  C3: W4ID → LCT Document → Verifiable Credential (identity stack)
  C4: MCP Interaction → Reputation Delta → Society Ledger (feedback loop)
  C5: Error Taxonomy consistency across MCP + W4Error + Metering
  C6: Capability Level → MCP Access → Reputation (promotion/demotion cycle)
  C7: Full lifecycle: Society forms → member joins → gets ATP → uses MCP tool
      → reputation updates → society records
  C8: Pairwise privacy across societies
  C9: Team composition via multi-role reputation tensors
  C10: Serialization round-trip consistency across all modules

This is NOT a unit test — it validates semantic coherence across modules.

@version 1.0.0
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

# ── Import all modules under test ────────────────────────────

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Society lifecycle
from society_lifecycle import (
    Society, SocietyPhase, CitizenStatus, LedgerType,
    Law, SocietyLedger, Treasury, TreasuryAllocation, CitizenRecord,
)

# ATP metering
from atp_metering import (
    CreditGrant, UsageReport, UsageItem, WitnessAttestation as MeteringWitness,
    MeteringError, MeteringException, TokenBucket,
)

# MCP trust binding
from mcp_trust_binding import (
    MCPServer, MCPClient, MCPTool, MCPSession, MCPError, MCPErrorCode,
    Web4Context, InteractionWitness,
    T3 as MCPT3, V3 as MCPV3,
)

# T3/V3 reputation engine
from t3v3_reputation_engine import (
    Tensor, RoleTensor, EntityTensorRegistry, ReputationEngine,
    ReputationRule, DimensionImpact, RuleModifier,
    ContributingFactor, WitnessSelector,
    compute_team_trust,
    T3_DIMS, V3_DIMS,
)

# W4ID data formats
from w4id_data_formats import (
    W4ID, PairwiseIdentityManager, VerifiableCredential,
    W4IDDocument, canonicalize_json, generate_keypair,
)

# LCT document
from lct_document import (
    LCTBuilder, ENTITY_TYPES,
    T3Tensor as LCTT3,
)

# Error handler
from web4_error_handler import (
    W4Error, ProblemDetails, Web4Exception, error as make_error,
)

# Capability levels
from lct_capability_levels_v2 import (
    LCTEntity, CapabilityValidator, CapLevel,
    EntityFactory, CapabilityQuery, CapabilityResponse,
)


# ══════════════════════════════════════════════════════════════
# Test Harness
# ══════════════════════════════════════════════════════════════

passed = 0
failed = 0

def check(name: str, condition: bool):
    global passed, failed
    if condition:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}")
        failed += 1


def run_tests() -> tuple[int, int]:
    global passed, failed

    # ══════════════════════════════════════════════════════════
    # C1: Society → Treasury → ATP Metering
    # ══════════════════════════════════════════════════════════
    print("\n═══ C1: Society → Treasury → ATP Metering ═══")

    # 1. Society forms with ATP treasury
    founding_law = Law("LAW-001", "Charter", "All members get ATP allocation")
    society = Society(
        society_lct="lct:web4:society:integration-test",
        name="Integration Test Society",
        founding_law=founding_law,
        initial_atp=1000.0,
        ledger_type=LedgerType.WITNESSED,
    )
    check("C1: society created", society.phase == SocietyPhase.GENESIS)
    check("C1: treasury has 1000 ATP", society.treasury.atp_balance == 1000.0)

    # 2. Bootstrap with founders
    founders = ["lct:web4:human:alice", "lct:web4:ai:sage"]
    society.bootstrap(founders, witness_lcts=["lct:web4:oracle:time"])
    check("C1: bootstrapped", society.phase == SocietyPhase.BOOTSTRAP)
    society.go_operational()
    check("C1: operational", society.phase == SocietyPhase.OPERATIONAL)

    # 3. Allocate ATP to member → becomes CreditGrant ceiling
    alloc = society.allocate_atp("lct:web4:ai:sage", 100.0, "MCP tool access")
    check("C1: ATP allocated", alloc is not None)
    check("C1: treasury decreased", society.treasury.atp_balance == 900.0)

    # 4. CreditGrant matches allocated amount
    grant = CreditGrant(
        grant_id="grant:sage-mcp",
        scopes=["tools/analyze", "tools/search"],
        ceiling_total=alloc.amount,
        ceiling_unit="ATP",
        rate_max_per_min=10,
    )
    check("C1: grant ceiling = allocation", grant.ceiling_total == 100.0)
    check("C1: grant active", grant.is_active())

    # 5. Usage report against grant
    usage = UsageReport(
        grant_id=grant.grant_id,
        seq=1,
        window_start="2026-02-21T12:00:00Z",
        window_end="2026-02-21T12:05:00Z",
        usage=[UsageItem(scope="tools/analyze", amount=5.0, unit="ATP")],
        witness=[MeteringWitness(witness_type="time", witness_ref="lct:web4:oracle:time")],
    )
    check("C1: usage < ceiling", usage.total_amount <= grant.ceiling_total)
    check("C1: evidence digest computed", len(usage.evidence_digest) == 64)

    # 6. ADP returns to treasury after settlement
    society.treasury.receive_adp(usage.total_amount * 0.9)  # 90% ADP return
    check("C1: ADP received", society.treasury.adp_pool == 4.5)
    recharged = society.treasury.recharge(4.5)
    check("C1: recharge", recharged == 4.5)
    check("C1: ATP restored", society.treasury.atp_balance == 904.5)

    # 7. Ledger records full economic lifecycle
    econ_entries = society.ledger.query(entry_type="economic_event")
    check("C1: economic events in ledger", len(econ_entries) >= 1)
    check("C1: ledger chain valid", society.ledger.verify_chain())

    # ══════════════════════════════════════════════════════════
    # C2: T3/V3 Reputation → MCP Trust Gating
    # ══════════════════════════════════════════════════════════
    print("\n═══ C2: Reputation Engine → MCP Trust Gating ═══")

    # 1. Entity has reputation-managed T3 tensors
    registry = EntityTensorRegistry()
    rt = registry.get_or_create(
        "lct:web4:ai:sage", "web4:DataAnalyst",
        t3_init={"talent": 0.85, "training": 0.90, "temperament": 0.80},
        v3_init={"veracity": 0.85, "validity": 0.80, "value": 0.70},
    )
    check("C2: role tensor created", rt.trust_score() > 0.8)

    # 2. Bridge reputation T3 to MCP T3
    mcp_t3 = MCPT3(
        talent=rt.t3["talent"],
        training=rt.t3["training"],
        temperament=rt.t3["temperament"],
    )
    check("C2: T3 bridged to MCP", mcp_t3.talent == 0.85)

    # 3. MCP server with trust-gated tools
    server = MCPServer("lct:web4:service:analyzer", entity_type="service")
    high_tool = MCPTool(
        name="deep_analysis",
        description="Advanced analysis requiring high trust",
        atp_cost=10.0,
        trust_requirements=MCPT3(talent=0.7, training=0.8, temperament=0.7),
    )
    low_tool = MCPTool(
        name="basic_search",
        description="Basic search, low trust needed",
        atp_cost=1.0,
        trust_requirements=MCPT3(talent=0.3, training=0.3, temperament=0.3),
    )
    server.register_tool(high_tool)
    server.register_tool(low_tool)

    # 4. High-trust entity can access high-trust tools
    ctx = Web4Context(
        sender_lct="lct:web4:ai:sage",
        sender_role="web4:DataAnalyst",
        t3_in_role=mcp_t3,
    )
    session = server.create_session("lct:web4:ai:sage", atp_budget=100)
    result = server.handle_request(session.session_id, "deep_analysis", {}, ctx)
    check("C2: high-trust access granted", result["result"]["status"] == "ok")

    # 5. Low-trust entity gets denied
    low_t3 = MCPT3(talent=0.4, training=0.35, temperament=0.4)
    low_ctx = Web4Context(
        sender_lct="lct:web4:ai:newbie",
        sender_role="web4:Intern",
        t3_in_role=low_t3,
    )
    low_session = server.create_session("lct:web4:ai:newbie", atp_budget=50)
    denied = False
    try:
        server.handle_request(low_session.session_id, "deep_analysis", {}, low_ctx)
    except MCPError as e:
        denied = True
        check("C2: denial is INSUFFICIENT_TRUST", e.code == MCPErrorCode.INSUFFICIENT_TRUST)
    check("C2: low-trust denied", denied)

    # 6. Same low-trust entity can access low-trust tool
    result2 = server.handle_request(low_session.session_id, "basic_search", {}, low_ctx)
    check("C2: low-trust accesses basic tool", result2["result"]["status"] == "ok")

    # ══════════════════════════════════════════════════════════
    # C3: W4ID → LCT Document → Verifiable Credential
    # ══════════════════════════════════════════════════════════
    print("\n═══ C3: W4ID → LCT Document → Verifiable Credential ═══")

    # 1. Generate Ed25519 keypair → W4ID
    priv_key, pub_key = generate_keypair()
    w4id = W4ID.from_public_key(pub_key)
    check("C3: W4ID created", w4id.did.startswith("did:web4:key:"))
    check("C3: W4ID has method", w4id.method == "key")

    # 2. Build LCT document referencing W4ID
    lct_doc = LCTBuilder("ai", "sage-integration") \
        .with_binding(pub_key.hex()[:20], "cose:ed25519_proof") \
        .with_birth_certificate(
            "lct:web4:society:integration-test",
            "lct:web4:role:citizen:ai",
            witnesses=["lct:web4:oracle:time"],
        ) \
        .with_t3(talent=0.85, training=0.90, temperament=0.80) \
        .add_capability("witness:attest") \
        .add_capability("execute:tools/analyze") \
        .build()
    check("C3: LCT document built", lct_doc is not None)
    check("C3: LCT has id", lct_doc.lct_id.startswith("lct:web4:"))
    validation = lct_doc.validate()
    check("C3: LCT validates", validation.valid)

    # 3. LCT T3 matches W4ID-holder's reputation
    lct_t3 = lct_doc.t3_tensor
    check("C3: LCT T3 talent matches", lct_t3.talent == 0.85)
    check("C3: LCT T3 training matches", lct_t3.training == 0.90)

    # 4. Issue VC for citizenship
    citizenship_vc = VerifiableCredential(
        vc_id=f"vc:{hashlib.sha256(lct_doc.lct_id.encode()).hexdigest()[:16]}",
        vc_type=["VerifiableCredential", "Web4Citizenship"],
        issuer=w4id.did,
        issuance_date="2026-02-21T12:00:00Z",
        credential_subject={
            "id": lct_doc.lct_id,
            "society": "lct:web4:society:integration-test",
            "rights": ["vote", "propose"],
        },
    )
    signed_vc = citizenship_vc.sign(priv_key)
    check("C3: VC signed", signed_vc.proof is not None)
    check("C3: VC issuer is W4ID", signed_vc.issuer == w4id.did)
    check("C3: VC subject is LCT", signed_vc.credential_subject["id"] == lct_doc.lct_id)

    # 5. VC can be verified
    verified = signed_vc.verify(pub_key)
    check("C3: VC verification passes", verified)

    # 6. JCS canonicalization is deterministic
    vc_dict = signed_vc.to_dict()
    canonical1 = canonicalize_json(vc_dict)
    canonical2 = canonicalize_json(vc_dict)
    check("C3: JCS deterministic", canonical1 == canonical2)

    # ══════════════════════════════════════════════════════════
    # C4: MCP Interaction → Reputation Delta → Ledger
    # ══════════════════════════════════════════════════════════
    print("\n═══ C4: MCP → Reputation → Society Ledger ═══")

    # 1. Set up reputation engine with rules
    rep_registry = EntityTensorRegistry()
    rep_engine = ReputationEngine(rep_registry)

    success_rule = ReputationRule(
        rule_id="mcp_tool_success",
        trigger_conditions={"result_status": "success", "quality_threshold": 0.5},
        t3_impacts={
            "training": DimensionImpact(base_delta=0.02),
            "temperament": DimensionImpact(base_delta=0.01),
        },
        v3_impacts={
            "veracity": DimensionImpact(base_delta=0.01),
        },
    )
    failure_rule = ReputationRule(
        rule_id="mcp_tool_failure",
        trigger_conditions={"result_status": "failure"},
        t3_impacts={
            "temperament": DimensionImpact(base_delta=-0.03),
        },
        v3_impacts={
            "veracity": DimensionImpact(base_delta=-0.02),
        },
        category="failure",
    )
    rep_engine.add_rule(success_rule)
    rep_engine.add_rule(failure_rule)

    # Pre-create role tensor
    rep_registry.get_or_create(
        "lct:web4:ai:sage", "web4:DataAnalyst",
        t3_init={"talent": 0.85, "training": 0.70, "temperament": 0.80},
        v3_init={"veracity": 0.75, "validity": 0.80, "value": 0.60},
    )

    # 2. Simulate MCP interaction (success)
    mcp_result = server.handle_request(session.session_id, "deep_analysis",
                                        {"query": "trust analysis"}, ctx)
    mcp_success = mcp_result["result"]["status"] == "ok"
    check("C4: MCP interaction successful", mcp_success)

    # 3. Feed MCP result into reputation engine
    rep_status = "success" if mcp_success else "failure"
    delta = rep_engine.compute_reputation_delta(
        "lct:web4:ai:sage",
        "web4:DataAnalyst",
        "deep_analysis",
        "txn:mcp-1",
        rep_status,
        quality=0.92,
        factors_data={"deadline_met": True},
    )
    check("C4: reputation delta computed", delta is not None)
    check("C4: training increased", delta.t3_delta.get("training") is not None and
                                     delta.t3_delta["training"].change > 0)
    check("C4: net trust positive", delta.net_trust_change > 0)

    # 4. Record reputation change in society ledger
    society.ledger.append("reputation_event", {
        "entity_lct": "lct:web4:ai:sage",
        "role": "web4:DataAnalyst",
        "action": "deep_analysis",
        "result": rep_status,
        "trust_delta": round(delta.net_trust_change, 4),
        "value_delta": round(delta.net_value_change, 4),
    }, witnesses=["lct:web4:service:analyzer"])
    rep_events = society.ledger.query(entry_type="reputation_event")
    check("C4: reputation event in ledger", len(rep_events) == 1)

    # 5. Failure path
    delta_fail = rep_engine.compute_reputation_delta(
        "lct:web4:ai:sage", "web4:DataAnalyst",
        "deep_analysis", "txn:mcp-fail", "failure",
    )
    check("C4: failure delta computed", delta_fail is not None)
    check("C4: failure decreases temperament", delta_fail.net_trust_change < 0)

    society.ledger.append("reputation_event", {
        "entity_lct": "lct:web4:ai:sage",
        "action": "deep_analysis",
        "result": "failure",
        "trust_delta": round(delta_fail.net_trust_change, 4),
    })

    # 6. Ledger maintains integrity across all events
    check("C4: ledger chain still valid", society.ledger.verify_chain())
    total_entries = society.ledger.length
    check("C4: ledger has full history", total_entries >= 8)

    # ══════════════════════════════════════════════════════════
    # C5: Error Taxonomy Consistency
    # ══════════════════════════════════════════════════════════
    print("\n═══ C5: Error Taxonomy Consistency ═══")

    # 1. MCP error codes map to W4Error taxonomy
    mcp_err = MCPError(MCPErrorCode.INSUFFICIENT_TRUST, "Not enough trust")
    mcp_resp = mcp_err.to_response()
    check("C5: MCP error has JSON-RPC code", mcp_resp["error"]["code"] == -32001)
    check("C5: MCP error has web4_context", "web4_context" in mcp_resp)

    # 2. W4Error covers the same error space (AUTHZ_DENIED maps to trust denial)
    w4_trust_err = make_error(W4Error.AUTHZ_DENIED, detail="T3 too low for tool")
    check("C5: W4Error has status", w4_trust_err.status == 401)
    check("C5: W4Error has code", w4_trust_err.code == "W4_ERR_AUTHZ_DENIED")

    # 3. Metering errors map to HTTP status codes
    meter_rate = MeteringError.RATE_LIMIT
    check("C5: metering rate limit = 429", meter_rate.value[2] == 429)
    meter_scope = MeteringError.SCOPE_DENIED
    check("C5: metering scope denied = 403", meter_scope.value[2] == 403)

    # 4. Error codes don't collide
    mcp_codes = {e.json_rpc_code for e in MCPErrorCode}
    check("C5: MCP codes are negative", all(c < 0 for c in mcp_codes))
    w4_statuses = {e.value[2] for e in W4Error}
    meter_statuses = {e.value[2] for e in MeteringError}
    check("C5: HTTP statuses overlap expected", 403 in w4_statuses and 403 in meter_statuses)

    # 5. ProblemDetails wraps correctly
    pd = make_error(W4Error.AUTHZ_RATE, detail="Session budget exhausted after 10 tool calls")
    pd_json = pd.to_dict()
    check("C5: ProblemDetails has code", "AUTHZ_RATE" in pd_json["code"])
    check("C5: ProblemDetails has status", pd_json["status"] == 429)

    # ══════════════════════════════════════════════════════════
    # C6: Capability Level → MCP → Reputation Cycle
    # ══════════════════════════════════════════════════════════
    print("\n═══ C6: Capability Level → MCP → Reputation Cycle ═══")

    # 1. Entity at capability level 3 (STANDARD)
    entity = EntityFactory.make_standard("ai", "cap-sage", "lct:web4:device:legion")
    validator = CapabilityValidator()
    val_result = validator.validate(entity)
    check("C6: STANDARD entity valid", val_result.valid)
    check("C6: entity level = 3", entity.capability_level == CapLevel.STANDARD)

    # 2. Entity's T3 from capability level → MCP context
    # Cap levels use 6-dim legacy tensors; bridge to 3-dim MCP T3
    # Map: technical_competence→talent, social_reliability→temperament, temporal_consistency→training
    entity_mcp_t3 = MCPT3(
        talent=entity.t3.dimensions.get("technical_competence", 0.5),
        training=entity.t3.dimensions.get("temporal_consistency", 0.5),
        temperament=entity.t3.dimensions.get("social_reliability", 0.5),
    )
    check("C6: cap→MCP T3 bridge", entity_mcp_t3.average() > 0.3)

    # 3. MCP tool call success → reputation improves
    cap_registry = EntityTensorRegistry()
    cap_engine = ReputationEngine(cap_registry)
    cap_engine.add_rule(success_rule)
    cap_registry.get_or_create(
        entity.lct_id, "web4:Researcher",
        t3_init={"talent": entity_mcp_t3.talent,
                 "training": entity_mcp_t3.training,
                 "temperament": entity_mcp_t3.temperament},
    )

    # Multiple successes → reputation grows
    for i in range(5):
        d = cap_engine.compute_reputation_delta(
            entity.lct_id, "web4:Researcher",
            "research_query", f"txn:cap-{i}", "success", quality=0.95,
            factors_data={"deadline_met": True},
        )
    rt_after = cap_registry.get(entity.lct_id, "web4:Researcher")
    check("C6: training improved after successes", rt_after.t3["training"] > entity_mcp_t3.training)
    check("C6: temperament improved", rt_after.t3["temperament"] > entity_mcp_t3.temperament)

    # 4. Updated reputation feeds back into MCP access
    updated_mcp_t3 = MCPT3(
        talent=rt_after.t3["talent"],
        training=rt_after.t3["training"],
        temperament=rt_after.t3["temperament"],
    )
    check("C6: MCP T3 reflects reputation growth",
          updated_mcp_t3.training > entity_mcp_t3.training)

    # ══════════════════════════════════════════════════════════
    # C7: Full Lifecycle Integration
    # ══════════════════════════════════════════════════════════
    print("\n═══ C7: Full Lifecycle Integration ═══")

    # 1. Create a society
    charter = Law("LAW-FULL", "Full Charter", "Members use MCP tools under ATP budget")
    full_society = Society(
        society_lct="lct:web4:society:full-test",
        name="Full Integration Society",
        founding_law=charter,
        initial_atp=5000.0,
        ledger_type=LedgerType.WITNESSED,
    )

    # 2. Bootstrap with human founder
    full_society.bootstrap(
        ["lct:web4:human:admin"],
        witness_lcts=["lct:web4:oracle:time"],
    )

    # 3. AI entity joins
    app = full_society.apply_for_citizenship("lct:web4:ai:worker")
    check("C7: AI applied", app is not None)
    full_society.accept_citizen(
        "lct:web4:ai:worker",
        rights=["execute", "report"],
        obligations=["abide_law", "witness"],
        witnesses=["lct:web4:human:admin"],
    )
    check("C7: AI accepted", full_society.citizens["lct:web4:ai:worker"].status == CitizenStatus.ACTIVE)
    full_society.go_operational()
    check("C7: society operational", full_society.phase == SocietyPhase.OPERATIONAL)

    # 4. Society allocates ATP to AI worker
    atp_alloc = full_society.allocate_atp("lct:web4:ai:worker", 200.0, "tool_access",
                                           approved_by=["lct:web4:human:admin"])
    check("C7: ATP allocated to worker", atp_alloc is not None)
    check("C7: correct amount", atp_alloc.amount == 200.0)

    # 5. ATP allocation becomes CreditGrant for MCP
    worker_grant = CreditGrant(
        grant_id="grant:worker-mcp",
        scopes=["tools/*"],
        ceiling_total=atp_alloc.amount,
        ceiling_unit="ATP",
        rate_max_per_min=20,
    )

    # 6. Worker creates identity
    w_priv, w_pub = generate_keypair()
    worker_w4id = W4ID.from_public_key(w_pub)
    check("C7: worker W4ID created", worker_w4id.did.startswith("did:web4:key:"))

    # 7. Worker builds LCT with reputation-based T3
    worker_registry = EntityTensorRegistry()
    worker_rt = worker_registry.get_or_create(
        "lct:web4:ai:worker", "web4:TaskExecutor",
        t3_init={"talent": 0.60, "training": 0.55, "temperament": 0.70},
        v3_init={"veracity": 0.65, "validity": 0.60, "value": 0.50},
    )

    worker_lct = LCTBuilder("ai", "worker-full") \
        .with_binding(w_pub.hex()[:20], "cose:ed25519_proof") \
        .with_birth_certificate(
            "lct:web4:society:full-test",
            "lct:web4:role:citizen:ai",
            witnesses=["lct:web4:human:admin"],
        ) \
        .with_t3(
            talent=worker_rt.t3["talent"],
            training=worker_rt.t3["training"],
            temperament=worker_rt.t3["temperament"],
        ) \
        .add_capability("execute:tools/*") \
        .build()
    check("C7: worker LCT built", worker_lct is not None)
    check("C7: LCT T3 matches reputation", worker_lct.t3_tensor.talent == 0.60)

    # 8. Worker uses MCP tool
    mcp_server = MCPServer("lct:web4:service:task-runner", entity_type="service")
    mcp_server.register_tool(MCPTool(
        name="execute_task",
        description="Execute a task",
        atp_cost=5.0,
        trust_requirements=MCPT3(talent=0.5, training=0.5, temperament=0.5),
    ))
    worker_session = mcp_server.create_session("lct:web4:ai:worker",
                                                atp_budget=worker_grant.ceiling_total)
    worker_ctx = Web4Context(
        sender_lct="lct:web4:ai:worker",
        sender_role="web4:TaskExecutor",
        t3_in_role=MCPT3(
            talent=worker_rt.t3["talent"],
            training=worker_rt.t3["training"],
            temperament=worker_rt.t3["temperament"],
        ),
        society="lct:web4:society:full-test",
    )
    tool_result = mcp_server.handle_request(
        worker_session.session_id, "execute_task",
        {"task": "analyze trust data"}, worker_ctx,
    )
    check("C7: tool execution success", tool_result["result"]["status"] == "ok")
    check("C7: ATP consumed", tool_result["web4_context"]["atp_consumed"] == 5.0)

    # 9. Usage report for metering
    worker_usage = UsageReport(
        grant_id=worker_grant.grant_id,
        seq=1,
        window_start="2026-02-21T12:00:00Z",
        window_end="2026-02-21T12:05:00Z",
        usage=[UsageItem(scope="tools/execute_task", amount=5.0, unit="ATP")],
    )
    check("C7: usage within ceiling", worker_usage.total_amount <= worker_grant.ceiling_total)

    # 10. MCP result → reputation delta
    worker_engine = ReputationEngine(worker_registry)
    worker_engine.add_rule(success_rule)
    worker_delta = worker_engine.compute_reputation_delta(
        "lct:web4:ai:worker", "web4:TaskExecutor",
        "execute_task", "txn:full-1", "success",
        quality=0.88,
        factors_data={"deadline_met": True},
    )
    check("C7: reputation delta computed", worker_delta is not None)
    check("C7: worker trust improved", worker_delta.net_trust_change > 0)

    # 11. Record in society ledger
    full_society.ledger.append("interaction_event", {
        "entity_lct": "lct:web4:ai:worker",
        "tool": "execute_task",
        "atp_consumed": 5.0,
        "trust_delta": round(worker_delta.net_trust_change, 4),
        "grant_id": worker_grant.grant_id,
    }, witnesses=["lct:web4:service:task-runner"])

    # 12. Issue VC for completed work
    work_vc = VerifiableCredential(
        vc_id="vc:task-completion-001",
        vc_type=["VerifiableCredential", "Web4TaskCompletion"],
        issuer="lct:web4:service:task-runner",
        issuance_date="2026-02-21T12:05:00Z",
        credential_subject={
            "id": "lct:web4:ai:worker",
            "task": "analyze trust data",
            "quality": 0.88,
            "trust_delta": round(worker_delta.net_trust_change, 4),
            "society": "lct:web4:society:full-test",
        },
    )
    check("C7: work VC created", "Web4TaskCompletion" in work_vc.vc_type)

    # 13. Verify full ledger integrity
    check("C7: ledger chain valid", full_society.ledger.verify_chain())
    check("C7: ledger has all events", full_society.ledger.length >= 6)

    # 14. Treasury conservation: ATP allocated + remaining = initial
    consumed = atp_alloc.amount
    remaining = full_society.treasury.atp_balance
    check("C7: ATP conserved", consumed + remaining == 5000.0)

    # 15. Cross-check MCP witness log
    check("C7: MCP interactions witnessed", len(mcp_server.witness_log) >= 1)
    witness_entry = mcp_server.witness_log[0]
    check("C7: witness records client", witness_entry.client_lct == "lct:web4:ai:worker")

    # ══════════════════════════════════════════════════════════
    # C8: Pairwise Privacy Across Societies
    # ══════════════════════════════════════════════════════════
    print("\n═══ C8: Pairwise Privacy Across Societies ═══")

    # 1. Entity has different W4IDs for different peer societies
    pw_manager = PairwiseIdentityManager(
        master_secret=b"worker-master-secret-key-32bytes!",
    )

    pw_for_society1 = pw_manager.get_pairwise_id("lct:web4:society:alpha")
    pw_for_society2 = pw_manager.get_pairwise_id("lct:web4:society:beta")
    check("C8: pairwise IDs are different", pw_for_society1 != pw_for_society2)
    check("C8: pairwise is w4id", pw_for_society1.startswith("w4id:pair:"))

    # 2. Same entity, same peer → same pairwise (deterministic)
    pw_repeat = pw_manager.get_pairwise_id("lct:web4:society:alpha")
    check("C8: pairwise is deterministic", pw_for_society1 == pw_repeat)
    check("C8: deterministic verified", pw_manager.verify_deterministic("lct:web4:society:alpha"))

    # 3. Pairwise W4IDs can be used in VCs
    pw_vc = VerifiableCredential(
        vc_id="vc:pairwise-membership-001",
        vc_type=["VerifiableCredential", "PairwiseMembership"],
        issuer=pw_for_society1,
        issuance_date="2026-02-21T12:00:00Z",
        credential_subject={"id": "lct:web4:society:alpha", "role": "researcher", "pseudonymous": True},
    )
    check("C8: pairwise VC created", pw_vc.issuer == pw_for_society1)

    # ══════════════════════════════════════════════════════════
    # C9: Team Composition via Multi-Role Tensors
    # ══════════════════════════════════════════════════════════
    print("\n═══ C9: Team Composition via Reputation ═══")

    # 1. Build a team of entities with role-specific T3
    team_reg = EntityTensorRegistry()
    team_reg.get_or_create("lct:alice", "web4:Engineer",
                            t3_init={"talent": 0.90, "training": 0.85, "temperament": 0.80})
    team_reg.get_or_create("lct:bob", "web4:Engineer",
                            t3_init={"talent": 0.70, "training": 0.75, "temperament": 0.90})
    team_reg.get_or_create("lct:carol", "web4:Engineer",
                            t3_init={"talent": 0.85, "training": 0.80, "temperament": 0.85})

    # 2. Compute team trust
    team_members = ["lct:alice", "lct:bob", "lct:carol"]
    team_trust = compute_team_trust(team_reg, team_members, "web4:Engineer")
    check("C9: team trust computed", team_trust is not None)
    check("C9: team trust > 0.7", team_trust > 0.7)

    # 3. Team trust determines MCP session budget
    team_budget = 100.0 + (team_trust * 200.0)
    check("C9: team budget > 200", team_budget > 200)

    team_grant = CreditGrant(
        grant_id="grant:team-project",
        scopes=["tools/*"],
        ceiling_total=team_budget,
        ceiling_unit="ATP",
        rate_max_per_min=30,
    )
    check("C9: team grant reflects trust", team_grant.ceiling_total > 200)

    # 4. Any member uses tools under team grant
    alice_mcp_t3 = MCPT3(talent=0.90, training=0.85, temperament=0.80)
    alice_ctx = Web4Context(
        sender_lct="lct:alice",
        sender_role="web4:Engineer",
        t3_in_role=alice_mcp_t3,
    )
    team_session = mcp_server.create_session("lct:alice", atp_budget=team_grant.ceiling_total)
    alice_result = mcp_server.handle_request(
        team_session.session_id, "execute_task",
        {"task": "team engineering work"}, alice_ctx,
    )
    check("C9: team member uses tool", alice_result["result"]["status"] == "ok")

    # ══════════════════════════════════════════════════════════
    # C10: Serialization Round-Trip Consistency
    # ══════════════════════════════════════════════════════════
    print("\n═══ C10: Serialization Round-Trip ═══")

    # 1. Society serializes → JSON → fields preserved
    soc_dict = full_society.to_dict()
    soc_json = json.dumps(soc_dict)
    soc_rt2 = json.loads(soc_json)
    check("C10: society roundtrip", soc_rt2["name"] == "Full Integration Society")
    check("C10: society phase preserved", soc_rt2["phase"] == "operational")
    check("C10: treasury in dict", "atp_balance" in soc_rt2["treasury"])

    # 2. MCP session serializes
    sess_dict = worker_session.to_dict()
    check("C10: session has id", "id" in sess_dict["session"])
    check("C10: session has atp_consumed", "atp_consumed" in sess_dict["session"]["context"])

    # 3. Reputation delta serializes
    delta_dict = worker_delta.to_dict()
    delta_json = json.dumps(delta_dict)
    delta_rt2 = json.loads(delta_json)
    check("C10: delta roundtrip subject", delta_rt2["subject_lct"] == "lct:web4:ai:worker")
    check("C10: delta has t3", "t3_delta" in delta_rt2)

    # 4. LCT document serializes
    lct_dict = worker_lct.to_dict()
    lct_json = json.dumps(lct_dict)
    lct_rt2 = json.loads(lct_json)
    check("C10: LCT roundtrip id", lct_rt2["lct_id"] == worker_lct.lct_id)
    check("C10: LCT has t3_tensor", "t3_tensor" in lct_rt2)

    # 5. W4ID roundtrip
    w4id_str = worker_w4id.did
    w4id_parsed = W4ID.parse(w4id_str)
    check("C10: W4ID roundtrip", w4id_parsed == worker_w4id)

    # 6. CreditGrant serializes
    grant_dict = worker_grant.to_dict()
    grant_json = json.dumps(grant_dict)
    grant_rt2 = json.loads(grant_json)
    check("C10: grant roundtrip", grant_rt2["grant_id"] == "grant:worker-mcp")
    check("C10: grant ceiling preserved", grant_rt2["ceil"]["total"] == 200.0)

    # ══════════════════════════════════════════════════════════
    # Summary
    # ══════════════════════════════════════════════════════════
    print(f"""
{'='*60}
  Cross-Implementation Integration — Results
  {passed} passed, {failed} failed out of {passed + failed} checks
{'='*60}
""")

    if failed == 0:
        print("  All integration chains verified:")
        print("  C1:  Society → Treasury → ATP Metering (economic lifecycle)")
        print("  C2:  T3/V3 Reputation → MCP Trust Gating (access control)")
        print("  C3:  W4ID → LCT Document → Verifiable Credential (identity)")
        print("  C4:  MCP → Reputation Delta → Society Ledger (feedback loop)")
        print("  C5:  Error taxonomy consistency (MCP + W4Error + Metering)")
        print("  C6:  Capability Level → MCP → Reputation (promotion cycle)")
        print("  C7:  Full lifecycle: form → join → ATP → MCP → reputation → ledger")
        print("  C8:  Pairwise privacy across societies")
        print("  C9:  Team composition via multi-role reputation tensors")
        print("  C10: Serialization round-trip consistency across all modules")
        print()
        print("  8 modules integrated: Society, ATP Metering, MCP Trust,")
        print("  T3/V3 Reputation, W4ID, LCT Document, Error Handler, Capability Levels")
    else:
        print("  Some checks failed — review output above")

    return passed, failed


if __name__ == "__main__":
    p, f = run_tests()
    sys.exit(0 if f == 0 else 1)
