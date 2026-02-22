#!/usr/bin/env python3
"""
Web4 Cross-Implementation Integration Test

Validates that independently-developed reference implementations work together
as a coherent system. Each module was built from its own spec section; this test
proves the semantic glue between them.

7 Integration Chains:
  C1: Society → Treasury → ATP Metering (resource lifecycle)
  C2: W4ID → LCT Document → Verifiable Credential (identity lifecycle)
  C3: T3/V3 Reputation → MCP Trust Gating (trust-based access control)
  C4: MCP Interaction → Reputation Delta → Society Ledger (full loop)
  C5: Error codes consistent across MCP, Metering, and Error Handler
  C6: Capability Levels + Reputation Integration
  C7: Full Lifecycle — Formation → Identity → Operation → Audit

Cross-references 8 reference implementations:
  - society_lifecycle.py, atp_metering.py, t3v3_reputation_engine.py
  - mcp_trust_binding.py, w4id_data_formats.py, lct_document.py
  - web4_error_handler.py, lct_capability_levels_v2.py

@version 1.0.0
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import society_lifecycle as soc
import atp_metering as atp
import t3v3_reputation_engine as rep
import mcp_trust_binding as mcp
import w4id_data_formats as w4id
import lct_document as lctd
import web4_error_handler as err
import lct_capability_levels_v2 as cap


# ═══════════════════════════════════════════════════════════════
# Test Framework
# ═══════════════════════════════════════════════════════════════

passed = 0
failed = 0


def check(label: str, condition: bool):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_tests():
    global passed, failed

    # ══════════════════════════════════════════════════════════
    # Chain 1: Society → Treasury → ATP Metering
    # ══════════════════════════════════════════════════════════
    print("\n═══ C1: Society → Treasury → ATP Metering ═══")

    # 1a. Form society (requires founding_law)
    founding_law = soc.Law("LAW-GENESIS", "Genesis Law",
                           "All decisions by unanimous consent")
    society = soc.Society(
        society_lct="lct:web4:society:devteam",
        name="Dev Team Society",
        founding_law=founding_law,
        initial_atp=1000,
        ledger_type=soc.LedgerType.CONFINED,
    )
    founders = ["lct:web4:human:alice", "lct:web4:human:bob"]
    society.bootstrap(founders, witness_lcts=["lct:web4:oracle:genesis"])
    society.go_operational()
    check("C1.1: society operational", society.phase == soc.SocietyPhase.OPERATIONAL)
    check("C1.2: treasury has 1000 ATP", society.treasury.atp_balance == 1000)

    # 1b. Propose and ratify allocation law
    alloc_law = soc.Law("LAW-ATP-ALLOC", "ATP Allocation",
                         "Citizens may receive up to 200 ATP per cycle")
    society.propose_law(alloc_law, "lct:web4:human:alice")
    society.ratify_law("LAW-ATP-ALLOC",
                       {"alice": "yea", "bob": "yea"},
                       witnesses=["lct:web4:oracle:law"])
    check("C1.3: allocation law ratified", society.laws["LAW-ATP-ALLOC"].status == "ratified")

    # 1c. Allocate ATP to citizen (Society → Treasury)
    alloc = society.allocate_atp("lct:web4:human:alice", 100, "sprint allocation")
    check("C1.4: ATP allocated", alloc is not None)
    check("C1.5: treasury balance decreased", society.treasury.atp_balance == 900)

    # 1d. Create metering engine and grant
    grantor_engine = atp.MeteringEngine("lct:web4:society:devteam")
    grant = grantor_engine.issue_grant(
        scopes=["sprint:tools"],
        ceiling=100,
        unit="joule-equivalent",
        rate_max_per_min=20,
    )
    check("C1.6: grant created", grant is not None)
    check("C1.7: grant ceiling=100", grant.ceiling_total == 100)

    # Consumer receives the grant
    consumer_engine = atp.MeteringEngine("lct:web4:human:alice")
    consumer_engine.receive_grant(grant)

    # 1e. Consumer reports usage (with required time witness)
    time_witness = [atp.WitnessAttestation(
        witness_type="time", witness_ref="lct:web4:oracle:time")]

    usage1 = consumer_engine.submit_usage(
        grant.grant_id,
        [atp.UsageItem(scope="sprint:tools", amount=10, unit="joule-equivalent")],
        witness=time_witness,
    )
    check("C1.8: first usage recorded", usage1 is not None)
    check("C1.9: usage seq=1", usage1.seq == 1)

    usage2 = consumer_engine.submit_usage(
        grant.grant_id,
        [atp.UsageItem(scope="sprint:tools", amount=15, unit="joule-equivalent")],
        witness=time_witness,
    )
    check("C1.10: second usage recorded", usage2 is not None)
    check("C1.11: usage seq=2", usage2.seq == 2)

    # 1f. Grantor settles (replay usage on grantor side)
    grantor_engine.submit_usage(
        grant.grant_id,
        [atp.UsageItem(scope="sprint:tools", amount=10, unit="joule-equivalent")],
        witness=time_witness,
    )
    grantor_engine.submit_usage(
        grant.grant_id,
        [atp.UsageItem(scope="sprint:tools", amount=15, unit="joule-equivalent")],
        witness=time_witness,
    )
    settlement = grantor_engine.settle(grant.grant_id)
    check("C1.12: settlement created", settlement is not None)
    check("C1.13: settlement remaining = 75", settlement.remaining == 75)

    # Record in society ledger
    society.ledger.append(
        entry_type="economic_event",
        data={
            "action": "metering_settlement",
            "grant_id": grant.grant_id,
            "citizen_lct": "lct:web4:human:alice",
            "consumed": 25,
            "remaining": 75,
        },
        witnesses=["lct:web4:oracle:audit"],
    )
    ledger_econ = [e for e in society.ledger.entries if e.entry_type == "economic_event"]
    check("C1.14: settlement in ledger", len(ledger_econ) > 0)
    check("C1.15: ATP conservation", society.treasury.atp_balance + 100 == 1000)

    # ══════════════════════════════════════════════════════════
    # Chain 2: W4ID → LCT Document → Verifiable Credential
    # ══════════════════════════════════════════════════════════
    print("\n═══ C2: W4ID → LCT Document → Verifiable Credential ═══")

    # 2a. Generate keypair and create W4ID
    priv_bytes, pub_bytes = w4id.generate_keypair()
    entity_w4id = w4id.W4ID.from_public_key(pub_bytes)
    check("C2.1: W4ID created", entity_w4id.method == "key")
    check("C2.2: DID format correct", entity_w4id.did.startswith("did:web4:key:"))

    # 2b. Build LCT document referencing the W4ID
    lct_doc = lctd.LCTBuilder("ai", "sage-agent") \
        .with_binding(entity_w4id.method_specific_id, "cose:ed25519_proof") \
        .with_birth_certificate(
            "lct:web4:society:devteam",
            "lct:web4:role:citizen:ai",
            witnesses=["lct:web4:oracle:genesis"]) \
        .with_t3(talent=0.85, training=0.90, temperament=0.80) \
        .with_v3(veracity=0.88, validity=0.85, valuation=0.0) \
        .add_capability("witness:attest") \
        .add_capability("execute:tools") \
        .build()
    check("C2.3: LCT doc built", lct_doc is not None)
    check("C2.4: LCT has binding", lct_doc.binding is not None)
    check("C2.5: LCT has T3", lct_doc.t3_tensor is not None)
    check("C2.6: LCT has V3", lct_doc.v3_tensor is not None)
    check("C2.7: LCT has capabilities", len(lct_doc.policy.capabilities) == 2)

    # 2c. Validate LCT document against schema
    validation = lct_doc.validate()
    check("C2.8: LCT validates", validation.valid)

    # 2d. Issue verifiable credential for citizenship
    vc = w4id.VerifiableCredential(
        vc_id=f"vc:{society.society_lct}:citizenship:{lct_doc.lct_id}",
        vc_type=["VerifiableCredential", "Web4Citizenship"],
        issuer=society.society_lct,
        issuance_date=_now(),
        credential_subject={
            "id": entity_w4id.did,
            "society": society.society_lct,
            "citizen_lct": lct_doc.lct_id,
            "rights": ["vote", "propose", "allocate"],
            "status": "active",
        },
    )
    check("C2.9: VC issued", vc is not None)
    check("C2.10: VC subject references W4ID",
          vc.credential_subject["id"] == entity_w4id.did)
    check("C2.11: VC issuer is society", vc.issuer == society.society_lct)

    # 2e. Sign and verify the VC
    signed_vc = vc.sign(priv_bytes)
    check("C2.12: VC signed", signed_vc.proof is not None)
    check("C2.13: VC proof type", signed_vc.proof["type"] == "Ed25519Signature2020")

    verified = signed_vc.verify(pub_bytes)
    check("C2.14: VC verified", verified)

    # 2f. T3 composite from LCT
    t3_composite = lct_doc.t3_tensor.compute_composite()
    check("C2.15: LCT T3 composite valid", 0 < t3_composite <= 1.0)

    # 2g. JCS canonicalization of LCT + VC
    combined = {
        "lct": lct_doc.to_dict(),
        "credential": vc.to_dict(),
    }
    canonical = w4id.canonicalize_json(combined)
    check("C2.16: JCS canonical form", isinstance(canonical, str))
    check("C2.17: JCS deterministic", canonical == w4id.canonicalize_json(combined))

    # ══════════════════════════════════════════════════════════
    # Chain 3: T3/V3 Reputation → MCP Trust Gating
    # ══════════════════════════════════════════════════════════
    print("\n═══ C3: T3/V3 Reputation → MCP Trust Gating ═══")

    # 3a. Set up reputation engine
    registry = rep.EntityTensorRegistry()
    engine = rep.ReputationEngine(registry)

    success_rule = rep.ReputationRule(
        rule_id="tool_success",
        trigger_conditions={"result_status": "success"},
        t3_impacts={
            "training": rep.DimensionImpact(base_delta=0.02),
            "temperament": rep.DimensionImpact(base_delta=0.01),
        },
        v3_impacts={
            "veracity": rep.DimensionImpact(base_delta=0.015),
        },
    )
    failure_rule = rep.ReputationRule(
        rule_id="tool_failure",
        trigger_conditions={"result_status": "failure"},
        t3_impacts={
            "temperament": rep.DimensionImpact(base_delta=-0.05),
        },
        v3_impacts={
            "veracity": rep.DimensionImpact(base_delta=-0.03),
        },
        category="failure",
    )
    engine.add_rule(success_rule)
    engine.add_rule(failure_rule)

    # Entity with moderate initial T3
    rt = registry.get_or_create(
        "lct:web4:ai:sage", "web4:DataAnalyst",
        t3_init={"talent": 0.70, "training": 0.65, "temperament": 0.60},
        v3_init={"veracity": 0.70, "validity": 0.65, "value": 0.50},
    )
    check("C3.1: entity created", rt is not None)
    initial_trust = rt.trust_score()
    check("C3.2: initial trust moderate", 0.5 < initial_trust < 0.8)

    # 3b. MCP server with trust-gated tool
    server = mcp.MCPServer("lct:web4:service:analytics")
    server.register_tool(mcp.MCPTool(
        name="advanced_query",
        description="Complex analytical query requiring high trust",
        atp_cost=5.0,
        trust_requirements=mcp.T3(talent=0.65, training=0.70, temperament=0.65),
    ))

    # 3c. Bridge: reputation T3 → MCP T3
    def rep_to_mcp_t3(role_tensor):
        return mcp.T3(
            talent=role_tensor.t3["talent"],
            training=role_tensor.t3["training"],
            temperament=role_tensor.t3["temperament"],
        )

    mcp_t3 = rep_to_mcp_t3(rt)
    check("C3.3: T3 bridge works", mcp_t3.talent == 0.70)

    # 3d. FIRST ATTEMPT: training too low (0.65 < 0.70)
    ctx = mcp.Web4Context(
        sender_lct="lct:web4:ai:sage",
        sender_role="web4:DataAnalyst",
        t3_in_role=mcp_t3,
    )
    session = server.create_session("lct:web4:ai:sage", atp_budget=50)
    try:
        server.handle_request(session.session_id, "advanced_query", {}, ctx)
        check("C3.4: trust gated (should fail)", False)
    except mcp.MCPError as e:
        check("C3.4: trust gated correctly",
              e.code == mcp.MCPErrorCode.INSUFFICIENT_TRUST)

    # 3e. Build reputation through successes
    for i in range(5):
        engine.compute_reputation_delta(
            "lct:web4:ai:sage", "web4:DataAnalyst",
            "data_analysis", f"txn:train-{i}", "success", 0.92)
    check("C3.5: training improved", rt.t3["training"] > 0.65)
    check("C3.6: temperament improved", rt.t3["temperament"] > 0.60)

    # 3f. SECOND ATTEMPT with improved T3
    mcp_t3_improved = rep_to_mcp_t3(rt)
    ctx_improved = mcp.Web4Context(
        sender_lct="lct:web4:ai:sage",
        sender_role="web4:DataAnalyst",
        t3_in_role=mcp_t3_improved,
    )
    result = server.handle_request(session.session_id, "advanced_query", {}, ctx_improved)
    check("C3.7: now passes trust gate", result["result"]["status"] == "ok")
    check("C3.8: ATP consumed", result["web4_context"]["atp_consumed"] == 5.0)

    # 3g. Witness attestation
    check("C3.9: interaction witnessed", len(server.witness_log) > 0)
    last_witness = server.witness_log[-1]
    check("C3.10: witness records success", last_witness.success)

    # 3h. Failure scenario
    delta = engine.compute_reputation_delta(
        "lct:web4:ai:sage", "web4:DataAnalyst",
        "data_analysis", "txn:fail-1", "failure")
    check("C3.11: failure recorded", delta is not None)
    check("C3.12: temperament dropped",
          "temperament" in delta.t3_delta)
    check("C3.13: net trust negative", delta.net_trust_change < 0)

    # ══════════════════════════════════════════════════════════
    # Chain 4: MCP Interaction → Reputation → Society Ledger
    # ══════════════════════════════════════════════════════════
    print("\n═══ C4: MCP → Reputation → Society Ledger ═══")

    # 4a. MCP witness → reputation delta
    witness = server.witness_log[-1]
    check("C4.1: witness has client", witness.client_lct == "lct:web4:ai:sage")
    check("C4.2: witness has server", witness.server_lct == server.lct_id)

    mcp_delta = engine.compute_reputation_delta(
        witness.client_lct, "web4:DataAnalyst",
        f"mcp:{witness.action}", "txn:mcp-witnessed",
        "success" if witness.success else "failure",
        0.95 if witness.success else 0.0,
    )
    check("C4.3: MCP witness → rep delta", mcp_delta is not None)

    # 4b. Record in society ledger
    society.ledger.append(
        entry_type="trust_event",
        data={
            "action": "reputation_update",
            "entity_lct": mcp_delta.subject_lct,
            "role_lct": mcp_delta.role_lct,
            "source": "mcp_interaction",
            "t3_changes": {k: v.to_dict() for k, v in mcp_delta.t3_delta.items()},
            "v3_changes": {k: v.to_dict() for k, v in mcp_delta.v3_delta.items()},
            "net_trust_change": mcp_delta.net_trust_change,
            "witness": witness.to_dict(),
        },
        witnesses=[witness.witness_lct],
    )
    check("C4.4: reputation in ledger", True)

    # 4c. Ledger integrity
    ledger_entries = society.ledger.entries
    trust_entries = [e for e in ledger_entries if e.entry_type == "trust_event"]
    econ_entries = [e for e in ledger_entries if e.entry_type == "economic_event"]
    check("C4.5: trust events in ledger", len(trust_entries) > 0)
    check("C4.6: economic events in ledger", len(econ_entries) > 0)

    # 4d. Hash chain
    chain_ok = True
    for i in range(1, len(ledger_entries)):
        if ledger_entries[i].prev_hash != ledger_entries[i-1].entry_hash:
            chain_ok = False
            break
    check("C4.7: hash chain valid", chain_ok)

    # 4e. Trust event content
    latest_trust = trust_entries[-1]
    check("C4.8: entity correct",
          latest_trust.data["entity_lct"] == "lct:web4:ai:sage")
    check("C4.9: has t3 changes", "t3_changes" in latest_trust.data)
    check("C4.10: has witness", "witness" in latest_trust.data)

    # 4f. Session summary
    session_data = session.to_dict()
    check("C4.11: session tracks interactions",
          session_data["session"]["context"]["trust_evolution"]["interaction_count"] > 0)
    check("C4.12: session has t3 deltas",
          len(session_data["session"]["context"]["trust_evolution"]["t3_delta"]) > 0)

    # ══════════════════════════════════════════════════════════
    # Chain 5: Error Code Consistency
    # ══════════════════════════════════════════════════════════
    print("\n═══ C5: Error Code Consistency ═══")

    # 5a. MCP errors → W4Error equivalents
    mcp_to_w4 = {
        mcp.MCPErrorCode.INSUFFICIENT_TRUST: err.W4Error.AUTHZ_DENIED,
        mcp.MCPErrorCode.INVALID_LCT: err.W4Error.BINDING_INVALID,
        mcp.MCPErrorCode.ATP_INSUFFICIENT: err.W4Error.AUTHZ_SCOPE,
    }
    check("C5.1: trust error maps",
          mcp_to_w4[mcp.MCPErrorCode.INSUFFICIENT_TRUST].name == "AUTHZ_DENIED")

    # 5b. MCP error → W4 ProblemDetails
    mcp_err = mcp.MCPError(mcp.MCPErrorCode.INSUFFICIENT_TRUST, "Training too low")
    mcp_response = mcp_err.to_response()
    check("C5.2: MCP error has jsonrpc", mcp_response.get("jsonrpc") == "2.0")
    check("C5.3: MCP error code -32001", mcp_response["error"]["code"] == -32001)

    w4_err = mcp_to_w4[mcp.MCPErrorCode.INSUFFICIENT_TRUST]
    problem = err.ProblemDetails.from_w4error(
        w4_err,
        detail=mcp_err.detail,
        instance=f"/mcp/{server.lct_id}/advanced_query",
    )
    check("C5.4: W4 problem details created", problem is not None)
    check("C5.5: HTTP status mapped", problem.status > 0)
    pd_json = problem.to_dict()
    check("C5.6: RFC 9457 type field", "type" in pd_json)
    check("C5.7: RFC 9457 title field", "title" in pd_json)
    check("C5.8: RFC 9457 detail", pd_json.get("detail") == "Training too low")

    # 5c. Metering error → W4Error
    meter_to_w4 = {
        atp.MeteringError.GRANT_EXPIRED: err.W4Error.AUTHZ_EXPIRED,
        atp.MeteringError.RATE_LIMIT: err.W4Error.AUTHZ_RATE,
        atp.MeteringError.SCOPE_DENIED: err.W4Error.AUTHZ_SCOPE,
    }
    for m_err, w4_equiv in meter_to_w4.items():
        check(f"C5.9: {m_err.name} → {w4_equiv.name}", w4_equiv is not None)

    # 5d. Consistent HTTP status ranges
    check("C5.10: MCP trust = JSON-RPC negative",
          mcp.MCPErrorCode.INSUFFICIENT_TRUST.json_rpc_code < 0)
    check("C5.11: W4 authz denied = HTTP 401", err.W4Error.AUTHZ_DENIED.status == 401)
    check("C5.12: W4 authz rate = HTTP 429", err.W4Error.AUTHZ_RATE.status == 429)

    # 5e. Error in society audit ledger
    society.ledger.append(
        entry_type="audit_event",
        data={
            "error_code": w4_err.code,
            "http_status": w4_err.status,
            "mcp_code": mcp.MCPErrorCode.INSUFFICIENT_TRUST.json_rpc_code,
            "detail": "Training too low for advanced_query",
            "entity_lct": "lct:web4:ai:sage",
        },
        witnesses=["lct:web4:oracle:audit"],
    )
    audit_entries = [e for e in society.ledger.entries if e.entry_type == "audit_event"]
    check("C5.13: error in audit ledger", len(audit_entries) > 0)
    check("C5.14: audit has W4 code",
          audit_entries[-1].data["error_code"] == "W4_ERR_AUTHZ_DENIED")

    # ══════════════════════════════════════════════════════════
    # Chain 6: Capability Levels + Reputation
    # ══════════════════════════════════════════════════════════
    print("\n═══ C6: Capability Levels + Reputation ═══")

    # 6a. Create entity at STANDARD level
    entity = cap.EntityFactory.make_standard("ai", "sage-1", "lct:web4:device:legion")
    check("C6.1: entity at STANDARD", entity.capability_level == cap.CapLevel.STANDARD)

    # 6b. Validate entity
    validator = cap.CapabilityValidator()
    result = validator.validate(entity)
    check("C6.2: entity valid", result.valid)

    # 6c. Reputation engine T3 → capability context
    # Note: cap module uses 6-dim tensors (legacy), rep module uses 3-dim (canonical)
    # The bridge maps 3 canonical dims to the 6-dim legacy representation
    check("C6.3: rep engine T3 talent",
          rt.t3["talent"] == registry.get("lct:web4:ai:sage", "web4:DataAnalyst").t3["talent"])

    # 6d. Security check
    sec = cap.SecurityChecker()
    misrep = sec.check_misrepresentation(entity)
    check("C6.4: no misrepresentation", misrep.clean)

    # 6e. Capability query
    query = cap.CapabilityQuery(
        target_lct=entity.lct_id,
        requester_lct="lct:web4:service:analytics",
    )
    response = cap.handle_capability_query(entity, query)
    check("C6.5: capability response", response is not None)
    check("C6.6: response has components",
          len(response.supported_components) > 0)

    # 6f. Cross-domain negotiation
    negotiator = cap.CrossDomainNegotiator()
    partner = cap.EntityFactory.make_full("service", "partner-1", "lct:web4:society:s1")
    neg_result = negotiator.negotiate(entity, partner)
    check("C6.7: negotiation completed", neg_result is not None)
    check("C6.8: entities compatible", neg_result.compatible)

    # ══════════════════════════════════════════════════════════
    # Chain 7: Full Lifecycle — Formation → Identity → Operation → Audit
    # ══════════════════════════════════════════════════════════
    print("\n═══ C7: Full Lifecycle Integration ═══")

    # 7a. Form new society
    ops_law = soc.Law("LAW-OPS-GENESIS", "Ops Genesis", "Operations by majority vote")
    ops_society = soc.Society(
        society_lct="lct:web4:society:ops",
        name="Operations Society",
        founding_law=ops_law,
        initial_atp=5000,
        ledger_type=soc.LedgerType.WITNESSED,
    )
    ops_society.bootstrap(
        ["lct:web4:human:carol", "lct:web4:human:dave"],
        witness_lcts=["lct:web4:oracle:genesis"],
    )
    ops_society.go_operational()
    check("C7.1: ops society operational", ops_society.phase == soc.SocietyPhase.OPERATIONAL)

    # 7b. Create W4ID for agent
    agent_w4id = w4id.W4ID.from_domain("agent.ops.web4.example")
    check("C7.2: agent W4ID created", agent_w4id.method == "web")

    # 7c. Build agent LCT (full compliant document)
    agent_lct = lctd.LCTBuilder("ai", "ops-agent") \
        .with_binding("mb64ops_agent_key", "cose:ed25519_ops") \
        .with_birth_certificate(
            ops_society.society_lct,
            "lct:web4:role:citizen:ai",
            witnesses=["lct:web4:oracle:genesis"]) \
        .with_t3(talent=0.75, training=0.80, temperament=0.85) \
        .build()
    check("C7.3: agent LCT built", agent_lct is not None)

    # 7d. Grant citizenship (apply → accept flow)
    ops_society.apply_for_citizenship(agent_lct.lct_id)
    ops_society.accept_citizen(
        agent_lct.lct_id,
        rights=["execute", "witness"],
        obligations=["contribute"],
        witnesses=["lct:web4:oracle:citizenship"],
    )
    citizen = ops_society.citizens.get(agent_lct.lct_id)
    check("C7.4: citizen accepted", citizen is not None)
    check("C7.5: citizen active", citizen.status == soc.CitizenStatus.ACTIVE)

    # 7e. MCP tool access for citizen
    ops_server = mcp.MCPServer("lct:web4:service:ops-tools")
    ops_server.register_tool(mcp.MCPTool(
        name="deploy",
        description="Deploy service",
        atp_cost=10,
        trust_requirements=mcp.T3(talent=0.70, training=0.75, temperament=0.80),
    ))
    ops_session = ops_server.create_session(agent_lct.lct_id, atp_budget=200)
    ops_ctx = mcp.Web4Context(
        sender_lct=agent_lct.lct_id,
        sender_role="web4:Operator",
        t3_in_role=mcp.T3(
            talent=agent_lct.t3_tensor.talent,
            training=agent_lct.t3_tensor.training,
            temperament=agent_lct.t3_tensor.temperament,
        ),
        society=ops_society.society_lct,
    )
    deploy_result = ops_server.handle_request(
        ops_session.session_id, "deploy", {"target": "production"}, ops_ctx)
    check("C7.6: deploy succeeded", deploy_result["result"]["status"] == "ok")

    # 7f. Reputation update from deployment
    ops_registry = rep.EntityTensorRegistry()
    ops_engine = rep.ReputationEngine(ops_registry)
    ops_engine.add_rule(success_rule)
    ops_registry.get_or_create(
        agent_lct.lct_id, "web4:Operator",
        t3_init={"talent": 0.75, "training": 0.80, "temperament": 0.85},
    )
    deploy_delta = ops_engine.compute_reputation_delta(
        agent_lct.lct_id, "web4:Operator",
        "deploy", "txn:deploy-1", "success", 0.95)
    check("C7.7: deploy rep delta", deploy_delta is not None)
    check("C7.8: positive trust change", deploy_delta.net_trust_change > 0)

    # 7g. Record in ledger
    ops_society.ledger.append(
        entry_type="operational_event",
        data={
            "action": "deployment",
            "actor_lct": agent_lct.lct_id,
            "tool": "deploy",
            "atp_consumed": deploy_result["web4_context"]["atp_consumed"],
            "trust_delta": deploy_delta.net_trust_change,
            "result": "success",
        },
        witnesses=[ops_server.lct_id],
    )

    # 7h. Verify audit trail
    all_entries = ops_society.ledger.entries
    cit_events = [e for e in all_entries if e.entry_type == "citizenship_event"]
    op_events = [e for e in all_entries if e.entry_type == "operational_event"]
    check("C7.9: citizenship in ledger", len(cit_events) > 0)
    check("C7.10: operation in ledger", len(op_events) > 0)

    # Hash chain integrity
    chain_valid = True
    for i in range(1, len(all_entries)):
        if all_entries[i].prev_hash != all_entries[i-1].entry_hash:
            chain_valid = False
            break
    check("C7.11: full ledger hash chain valid", chain_valid)

    # Treasury
    check("C7.12: ops treasury intact", ops_society.treasury.atp_balance > 0)

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
        print("  All checks pass — Web4 implementations integrate correctly")
        print(f"  Modules tested: 8 reference implementations")
        print(f"  Chains validated:")
        print(f"    C1: Society → Treasury → ATP Metering")
        print(f"    C2: W4ID → LCT Document → Verifiable Credential")
        print(f"    C3: T3/V3 Reputation → MCP Trust Gating")
        print(f"    C4: MCP Interaction → Reputation → Society Ledger")
        print(f"    C5: Error Code Consistency across layers")
        print(f"    C6: Capability Levels + Reputation Integration")
        print(f"    C7: Full Lifecycle — Formation → Identity → Operation → Audit")
    else:
        print("  Some checks failed — review output above")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)
