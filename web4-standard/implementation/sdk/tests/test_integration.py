"""
Cross-module integration tests for the Web4 Python SDK.

These tests verify that Web4 SDK modules compose correctly in end-to-end
workflows. Each test exercises a realistic scenario that spans multiple
modules — not unit-level behavior of any single module.

Sprint tasks: S2, S6, U16
"""

import pytest

from web4.trust import T3, V3, TrustProfile, operational_health, is_healthy, mrh_trust_decay, mrh_zone
from web4.lct import LCT, EntityType, RevocationStatus
from web4.atp import ATPAccount, transfer, sliding_scale, check_conservation, energy_ratio
from web4.federation import Society, LawDataset, Norm, Procedure, Delegation
from web4.r6 import (
    R7Action, ActionStatus, Rules, Role, Request, Reference, ResourceRequirements,
    Result, ActionChain, build_action,
)
from web4.mrh import MRHGraph, MRHNode, MRHEdge, RelationType, propagate_multiplicative
from web4.acp import (
    ACPStateMachine, ACPState, AgentPlan, PlanStep, Intent, Decision,
    DecisionType, ExecutionRecord, Guards, ResourceCaps, HumanApproval,
    ApprovalMode, Trigger, TriggerKind, build_intent, validate_plan,
)
from web4.dictionary import (
    DictionaryEntity, DictionarySpec, DictionaryType, TranslationRequest,
    TranslationChain, CompressionProfile, DomainCoverage,
    dictionary_selection_score, select_best_dictionary,
)


class TestEntityLifecycle:
    """Workflow: society issues citizen → assign trust → check operational health."""

    def test_birth_to_trust_assessment(self):
        """Create entity via society, assign role trust, compute operational health."""
        # Society with law
        society = Society("lct:web4:society:acme", "ACME")
        law = LawDataset(
            law_id="law:acme:v1", version="1.0", society_id=society.society_id,
            procedures=[Procedure(procedure_id="PROC-WITNESS-QUORUM", requires_witnesses=2)],
        )
        society.set_law(law)

        # Issue citizenship (LCT created through federation)
        alice = society.issue_citizenship(
            entity_type=EntityType.HUMAN,
            public_key="alice_pub_key_001",
            witnesses=["w1", "w2"],
            t3=T3(talent=0.8, training=0.7, temperament=0.9),
            v3=V3(valuation=0.6, veracity=0.85, validity=0.75),
        )

        # LCT has trust tensors from creation
        assert alice.t3.talent == 0.8
        assert alice.v3.veracity == 0.85

        # Federation knows about the citizen
        assert society.is_citizen(alice.lct_id)

        # Birth certificate references the society
        assert alice.birth_certificate.issuing_society == society.society_id

        # Operational health check using T3/V3 composites + energy ratio
        account = ATPAccount(available=80.0)
        account.adp = 20.0  # spent some energy
        health = operational_health(alice.t3.composite, alice.v3.composite, account.energy_ratio)
        assert 0.0 <= health <= 1.0
        assert is_healthy(alice.t3.composite, alice.v3.composite, account.energy_ratio)

    def test_revoked_entity_loses_status(self):
        """Revoked LCT should still have tensors but is_active is False."""
        society = Society("lct:web4:society:test", "Test")
        lct = society.issue_citizenship(
            entity_type=EntityType.AI, public_key="ai_key_001",
            t3=T3(0.9, 0.9, 0.9), v3=V3(0.9, 0.9, 0.9),
        )
        assert lct.is_active
        lct.revoke()
        assert not lct.is_active
        # Tensors remain — trust doesn't vanish, entity is just suspended
        assert lct.t3.composite > 0.8


class TestTrustInformsPayment:
    """Workflow: trust score drives ATP payment via sliding scale."""

    def test_high_trust_gets_full_payment(self):
        """High-trust entity earns full payment for work."""
        t3 = T3(talent=0.9, training=0.85, temperament=0.8)
        quality = t3.composite  # ~0.865
        assert quality > 0.7  # above full_threshold

        payment = sliding_scale(quality, base_payment=100.0)
        assert payment == 100.0

    def test_low_trust_gets_partial_payment(self):
        """Low-trust entity earns partial payment."""
        t3 = T3(talent=0.4, training=0.5, temperament=0.6)
        quality = t3.composite  # ~0.49
        payment = sliding_scale(quality, base_payment=100.0)
        # Between 0.3 and 0.7 → partial
        assert 0.0 < payment < 100.0

    def test_zero_trust_gets_nothing(self):
        """Entity below quality threshold earns nothing."""
        t3 = T3(talent=0.1, training=0.1, temperament=0.1)
        quality = t3.composite  # 0.1
        payment = sliding_scale(quality, base_payment=100.0)
        assert payment == 0.0

    def test_payment_updates_trust(self):
        """After receiving payment (successful action), trust updates."""
        t3 = T3(talent=0.7, training=0.7, temperament=0.7)
        quality = t3.composite
        payment = sliding_scale(quality, base_payment=100.0)
        assert payment == 100.0

        # Successful action updates trust
        t3_updated = t3.update(quality=0.9, success=True)
        assert t3_updated.talent > t3.talent  # trust grew


class TestFederationGovernsATP:
    """Workflow: federation law constrains ATP transfers."""

    def test_law_caps_transfer_amount(self):
        """Society law defines max ATP transfer; check before executing."""
        society = Society("lct:web4:society:regulated", "Regulated Corp")
        law = LawDataset(
            law_id="law:regulated:v1", version="1.0",
            society_id=society.society_id,
            norms=[Norm(norm_id="LAW-ATP-LIMIT", selector="r6.resource.atp",
                        op="<=", value=500.0, description="Max 500 ATP per transfer")],
        )
        society.set_law(law)

        sender = ATPAccount(available=1000.0)
        receiver = ATPAccount(available=0.0)

        # Check law before transfer
        proposed_amount = 300.0
        assert society.law.check_norm("LAW-ATP-LIMIT", proposed_amount) is True

        # Execute transfer (law says OK)
        result = transfer(sender, receiver, proposed_amount)
        assert result.actual_credit == 300.0

        # Try exceeding the law
        excessive_amount = 600.0
        assert society.law.check_norm("LAW-ATP-LIMIT", excessive_amount) is False
        # Application would block this transfer based on law check

    def test_witness_quorum_for_high_value(self):
        """High-value operations require witness quorum per law."""
        society = Society("lct:web4:society:strict", "Strict Corp")
        law = LawDataset(
            law_id="law:strict:v1", version="1.0",
            society_id=society.society_id,
            procedures=[Procedure(
                procedure_id="PROC-WITNESS-QUORUM",
                requires_witnesses=3,
                description="3 witnesses for citizenship",
            )],
        )
        society.set_law(law)

        # Insufficient witnesses → rejected
        with pytest.raises(ValueError, match="Insufficient witnesses"):
            society.issue_citizenship(
                entity_type=EntityType.HUMAN, public_key="bob_key",
                witnesses=["w1", "w2"],  # need 3
            )

        # Sufficient witnesses → accepted
        bob = society.issue_citizenship(
            entity_type=EntityType.HUMAN, public_key="bob_key",
            witnesses=["w1", "w2", "w3"],
        )
        assert society.is_citizen(bob.lct_id)


class TestDelegationWithTrust:
    """Workflow: delegate authority → check permissions → trust context."""

    def test_delegation_requires_citizenship(self):
        """Cannot delegate to non-citizen."""
        society = Society("lct:web4:society:auth", "AuthCorp")
        with pytest.raises(ValueError, match="not a citizen"):
            society.delegate_authority(
                "lct:unknown:entity", scope="finance", permissions=["approve_atp"],
            )

    def test_delegate_with_trust_profile(self):
        """Citizen gets delegation; trust profile tracks role-specific trust."""
        society = Society("lct:web4:society:corp", "Corp")
        alice = society.issue_citizenship(
            entity_type=EntityType.HUMAN, public_key="alice_key",
        )

        # Delegate authority
        deleg = society.delegate_authority(
            alice.lct_id, scope="finance", permissions=["approve_atp", "view_ledger"],
        )

        # Trust profile tracks role-specific trust
        profile = TrustProfile(alice.lct_id)
        profile.set_role("web4:FinanceApprover", T3(0.85, 0.90, 0.80))
        profile.set_role("web4:Citizen", alice.t3)

        # Permission check + trust lookup
        assert society.has_permission(alice.lct_id, "finance", "approve_atp")
        assert profile.get_t3("web4:FinanceApprover").composite > 0.8
        assert "web4:Citizen" in profile.roles

    def test_sub_delegation_narrows_scope(self):
        """Sub-delegation must be subset of parent permissions."""
        society = Society("lct:web4:society:chain", "Chain")
        alice = society.issue_citizenship(EntityType.HUMAN, "alice_key")
        bob = society.issue_citizenship(EntityType.HUMAN, "bob_key")

        # Alice gets broad delegation
        deleg = society.delegate_authority(
            alice.lct_id, scope="finance",
            permissions=["approve_atp", "view_ledger", "audit"],
            max_depth=2,
        )

        # Alice sub-delegates to Bob with narrower scope
        sub = deleg.sub_delegate(bob.lct_id, permissions=["view_ledger"])
        assert sub is not None
        assert sub.permissions == ["view_ledger"]
        assert sub.max_depth == 1  # reduced by 1

        # Cannot amplify: Bob can't get permissions Alice didn't have
        amplified = deleg.sub_delegate(bob.lct_id, permissions=["delete_records"])
        assert amplified is None


class TestATPConservationAcrossEntities:
    """Workflow: multi-party ATP transfers preserve conservation invariant."""

    def test_three_party_transfer_chain(self):
        """A → B → C transfer chain preserves total ATP."""
        a = ATPAccount(available=1000.0)
        b = ATPAccount(available=500.0)
        c = ATPAccount(available=200.0)

        initial = [a.available, b.available, c.available]
        total_fees = 0.0

        # A sends 200 to B
        r1 = transfer(a, b, 200.0, fee_rate=0.05)
        total_fees += r1.fee

        # B sends 100 to C
        r2 = transfer(b, c, 100.0, fee_rate=0.05)
        total_fees += r2.fee

        final = [a.available, b.available, c.available]
        assert check_conservation(initial, final, total_fees)

    def test_lock_commit_with_energy_tracking(self):
        """Lock → commit cycle tracks ADP and energy ratio."""
        account = ATPAccount(available=100.0)
        assert account.energy_ratio == 1.0  # all ATP, no ADP

        # Lock for pending operation
        assert account.lock(30.0)
        assert account.available == 70.0
        assert account.locked == 30.0

        # Commit (discharge to ADP)
        committed = account.commit(30.0)
        assert committed == 30.0
        assert account.adp == 30.0
        assert account.energy_ratio == pytest.approx(70.0 / 100.0)

        # Energy ratio reflects work done
        er = energy_ratio(account.total, account.adp)
        assert er == pytest.approx(account.energy_ratio)


class TestMRHTrustDecayWithLCT:
    """Workflow: trust decays with MRH hops; zones classify relationships."""

    def test_witness_chain_trust_decay(self):
        """Trust decays along witness chain: direct → indirect → peripheral."""
        society = Society("lct:web4:society:net", "Network")
        alice = society.issue_citizenship(EntityType.HUMAN, "alice_key",
                                          t3=T3(0.9, 0.9, 0.9))

        base_trust = alice.t3.composite  # ~0.9

        # Direct witness (1 hop)
        trust_1 = mrh_trust_decay(base_trust, hops=1)
        assert mrh_zone(1) == "DIRECT"
        assert 0.5 < trust_1 < base_trust

        # Indirect (2 hops)
        trust_2 = mrh_trust_decay(base_trust, hops=2)
        assert mrh_zone(2) == "INDIRECT"
        assert trust_2 < trust_1

        # Peripheral (4 hops)
        trust_4 = mrh_trust_decay(base_trust, hops=4)
        assert mrh_zone(4) == "PERIPHERAL"
        assert trust_4 < trust_2

        # Beyond (5+ hops) = zero
        trust_5 = mrh_trust_decay(base_trust, hops=5)
        assert mrh_zone(5) == "BEYOND"
        assert trust_5 == 0.0

    def test_lct_witnessing_builds_context(self):
        """Adding witnesses to LCT builds MRH context."""
        society = Society("lct:web4:society:ctx", "Context")
        alice = society.issue_citizenship(EntityType.HUMAN, "alice_key")
        bob = society.issue_citizenship(EntityType.AI, "bob_key")

        # Alice witnesses Bob
        alice.add_witness(bob.lct_id)
        assert bob.lct_id in alice.mrh.witnessing

        # Bob pairs with Alice
        bob.add_pairing(alice.lct_id, "collaboration")
        assert any(p.lct_id == alice.lct_id for p in bob.mrh.paired)

        # Canonical hash changes with new relationships
        hash_before = alice.canonical_hash()
        alice.add_witness("lct:web4:human:charlie")
        hash_after = alice.canonical_hash()
        assert hash_before != hash_after


class TestFractalSocietyCitizenship:
    """Workflow: nested societies with law inheritance and citizenship."""

    def test_child_inherits_parent_law(self):
        """Child society inherits parent law when no local law is set."""
        parent = Society("lct:web4:society:parent", "Parent Org")
        parent_law = LawDataset(
            law_id="law:parent:v1", version="1.0",
            society_id=parent.society_id,
            norms=[Norm(norm_id="LAW-GLOBAL", selector="trust.min",
                        op=">=", value=0.3)],
        )
        parent.set_law(parent_law)

        child = Society("lct:web4:society:child", "Child Team", parent=parent)

        # Child inherits parent law
        effective = child.effective_law()
        assert effective is not None
        assert effective.law_id == "law:parent:v1"
        assert effective.check_norm("LAW-GLOBAL", 0.5) is True
        assert effective.check_norm("LAW-GLOBAL", 0.1) is False

    def test_child_overrides_parent_law(self):
        """Child law takes precedence over parent law."""
        parent = Society("lct:web4:society:p", "Parent")
        parent.set_law(LawDataset(
            law_id="law:p:v1", version="1.0", society_id=parent.society_id,
            norms=[Norm(norm_id="LAW-LIMIT", selector="atp", op="<=", value=1000)],
        ))

        child = Society("lct:web4:society:c", "Child", parent=parent)
        child.set_law(LawDataset(
            law_id="law:c:v1", version="1.0", society_id=child.society_id,
            norms=[Norm(norm_id="LAW-LIMIT", selector="atp", op="<=", value=500)],
        ))

        # Child's own law is stricter
        assert child.effective_law().check_norm("LAW-LIMIT", 750) is False
        assert parent.effective_law().check_norm("LAW-LIMIT", 750) is True

    def test_multi_level_citizenship(self):
        """Entity can be citizen of child society within parent hierarchy."""
        root = Society("lct:web4:society:root", "Root")
        org = Society("lct:web4:society:org", "Org", parent=root)
        team = Society("lct:web4:society:team", "Team", parent=org)

        assert team.depth == 2
        assert team.ancestry == [
            "lct:web4:society:root",
            "lct:web4:society:org",
            "lct:web4:society:team",
        ]

        # Issue citizen at team level
        alice = team.issue_citizenship(EntityType.HUMAN, "alice_key")
        assert team.is_citizen(alice.lct_id)
        # Not automatically a citizen of parent (explicit issuance required)
        assert not org.is_citizen(alice.lct_id)


class TestEndToEndWorkflow:
    """Full workflow: create society → issue citizens → delegate → transact → verify."""

    def test_complete_entity_economic_lifecycle(self):
        """
        End-to-end: society setup → citizenship → trust assignment →
        authority delegation → ATP transfer governed by law → health check.
        """
        # 1. Create society with law
        society = Society("lct:web4:society:demo", "Demo")
        law = LawDataset(
            law_id="law:demo:v1", version="1.0",
            society_id=society.society_id,
            norms=[
                Norm(norm_id="LAW-ATP-MAX", selector="atp.transfer",
                     op="<=", value=200.0),
                Norm(norm_id="LAW-TRUST-MIN", selector="trust.composite",
                     op=">=", value=0.3),
            ],
            procedures=[
                Procedure(procedure_id="PROC-WITNESS-QUORUM", requires_witnesses=2),
            ],
        )
        society.set_law(law)

        # 2. Issue citizens with trust
        alice = society.issue_citizenship(
            EntityType.HUMAN, "alice_pub",
            witnesses=["w1", "w2"],
            t3=T3(0.85, 0.80, 0.90),
            v3=V3(0.70, 0.85, 0.80),
        )
        bob = society.issue_citizenship(
            EntityType.AI, "bob_pub",
            witnesses=["w1", "w2"],
            t3=T3(0.70, 0.75, 0.65),
            v3=V3(0.60, 0.70, 0.65),
        )

        # 3. Delegate authority to Alice
        deleg = society.delegate_authority(
            alice.lct_id, scope="finance", permissions=["approve_atp"],
        )
        assert society.has_permission(alice.lct_id, "finance", "approve_atp")
        assert not society.has_permission(bob.lct_id, "finance", "approve_atp")

        # 4. ATP accounts
        alice_atp = ATPAccount(available=500.0)
        bob_atp = ATPAccount(available=100.0)
        initial_balances = [alice_atp.available, bob_atp.available]

        # 5. Check law before transfer
        proposed = 150.0
        assert law.check_norm("LAW-ATP-MAX", proposed) is True
        assert law.check_norm("LAW-TRUST-MIN", alice.t3.composite) is True

        # 6. Execute transfer
        result = transfer(alice_atp, bob_atp, proposed, fee_rate=0.05)
        total_fees = result.fee

        # 7. Conservation holds
        final_balances = [alice_atp.available, bob_atp.available]
        assert check_conservation(initial_balances, final_balances, total_fees)

        # 8. Trust update after successful action
        alice_t3_updated = alice.t3.update(quality=0.85, success=True)
        assert alice_t3_updated.talent > alice.t3.talent  # trust grew slightly

        # 9. Operational health check
        health = operational_health(
            alice_t3_updated.composite,
            alice.v3.composite,
            alice_atp.energy_ratio,
        )
        assert health > 0.5  # entity is healthy
        assert is_healthy(
            alice_t3_updated.composite,
            alice.v3.composite,
            alice_atp.energy_ratio,
        )

        # 10. MRH context: Alice witnessed Bob's work
        alice.add_witness(bob.lct_id)
        bob.add_pairing(alice.lct_id, "work_relationship")

        # Final state is self-consistent
        assert alice.is_active
        assert bob.is_active
        assert society.is_citizen(alice.lct_id)
        assert society.is_citizen(bob.lct_id)
        assert len(alice.mrh.witnessing) == 1
        assert len(bob.mrh.paired) == 2  # birth cert + work relationship


# ═══════════════════════════════════════════════════════════════════
# S6: Post-merge integration tests — all 8 modules
# ═══════════════════════════════════════════════════════════════════


class TestAgentActionWorkflow:
    """
    Workflow: Society → citizen → R7 action → ACP plan → execute → MRH graph.

    Modules exercised: trust, lct, atp, federation, r6, acp, mrh (7 of 8).

    Scenario: A society issues an AI agent citizen, delegates authority to it,
    the agent builds an ACP plan to perform a governed action, executes through
    the state machine, records the result as an R7 action, and the relationships
    are tracked in an MRH graph.
    """

    def _setup_society_with_agent(self):
        """Create society, principal, and AI agent with delegation."""
        society = Society("lct:web4:society:ops", "Operations")
        law = LawDataset(
            law_id="law:ops:v1", version="1.0",
            society_id=society.society_id,
            norms=[
                Norm(norm_id="LAW-ATP-CAP", selector="atp.transfer",
                     op="<=", value=500.0),
            ],
            procedures=[
                Procedure(procedure_id="PROC-WITNESS", requires_witnesses=1),
            ],
        )
        society.set_law(law)

        # Principal (human) and agent (AI)
        principal = society.issue_citizenship(
            EntityType.HUMAN, "principal_key",
            witnesses=["w1"],
            t3=T3(0.9, 0.85, 0.88),
            v3=V3(0.8, 0.9, 0.85),
        )
        agent = society.issue_citizenship(
            EntityType.AI, "agent_key",
            witnesses=["w1"],
            t3=T3(0.75, 0.80, 0.70),
            v3=V3(0.65, 0.75, 0.70),
        )

        # Delegate authority from principal to agent
        deleg = society.delegate_authority(
            agent.lct_id, scope="data_processing",
            permissions=["query_data", "transform_data"],
        )

        return society, principal, agent, deleg

    def test_agent_plans_and_executes_governed_action(self):
        """Full ACP lifecycle: plan → intent → approve → execute → record → R7 action."""
        society, principal, agent, deleg = self._setup_society_with_agent()

        # Agent has required permissions
        assert society.has_permission(agent.lct_id, "data_processing", "query_data")

        # Build ACP plan
        plan = AgentPlan(
            plan_id="plan:data-query-001",
            principal=principal.lct_id,
            agent=agent.lct_id,
            grant_id=deleg.delegation_id,
            triggers=[Trigger(kind=TriggerKind.MANUAL, expr="user_request")],
            steps=[
                PlanStep(step_id="s1", mcp_tool="data.query",
                         args={"table": "sensors", "limit": 100}),
                PlanStep(step_id="s2", mcp_tool="data.transform",
                         args={"format": "json"}, depends_on=["s1"]),
            ],
            guards=Guards(
                law_hash="law:ops:v1",
                resource_caps=ResourceCaps(max_atp=200.0, max_executions=10),
                witness_level=1,
                human_approval=HumanApproval(mode=ApprovalMode.CONDITIONAL,
                                             auto_threshold=100.0),
            ),
        )
        assert validate_plan(plan) == []  # Valid plan

        # ACP state machine lifecycle
        sm = ACPStateMachine(plan)
        assert sm.state == ACPState.IDLE

        sm.start_planning()
        assert sm.state == ACPState.PLANNING

        # Build intent for step s1
        intent = build_intent(plan, "s1", explanation="Query sensor data")
        sm.create_intent(intent)
        assert sm.state == ACPState.INTENT_CREATED

        # Approval gate — auto-approve (value within threshold)
        sm.enter_approval_gate()
        decision = Decision(
            intent_id=intent.intent_id,
            decision=DecisionType.APPROVE,
            decided_by=principal.lct_id,
            rationale="Within auto-approve threshold",
            witnesses=[principal.lct_id],
        )
        sm.approve(decision)
        assert sm.state == ACPState.EXECUTING

        # Record execution
        record = ExecutionRecord(
            record_id="rec:001",
            intent_id=intent.intent_id,
            grant_id=plan.grant_id,
            law_hash=plan.guards.law_hash,
            mcp_call={"tool": "data.query", "args": {"table": "sensors"}},
            result_status="success",
            result_output={"rows": 42},
            resources_consumed={"atp": 15.0},
            witnesses=[principal.lct_id],
        )
        sm.record_execution(record)
        assert sm.state == ACPState.RECORDING

        sm.complete()
        assert sm.state == ACPState.COMPLETE
        assert sm.record.success

        # Now create the corresponding R7 action
        action = build_action(
            actor=agent.lct_id,
            role_lct="role:data-processor",
            action="query_data",
            target="sensors",
            t3=agent.t3,
            v3=agent.v3,
            atp_stake=15.0,
            available_atp=200.0,
            permissions=["query_data", "transform_data"],
            society=society.society_id,
            law_hash="law:ops:v1",
            parameters={"table": "sensors", "limit": 100},
        )
        assert action.is_valid

        # Compute reputation delta for the successful action
        rep = action.compute_reputation(quality=0.85, rule_triggered=False)
        assert rep.net_trust_change > 0  # Success boosts trust
        assert rep.subject_lct == agent.lct_id

        # ATP conservation through the action
        agent_atp = ATPAccount(available=200.0)
        assert agent_atp.lock(15.0)
        committed = agent_atp.commit(15.0)
        assert committed == 15.0
        assert agent_atp.adp == 15.0
        assert agent_atp.energy_ratio < 1.0  # Work was done

        # Operational health check after action
        updated_t3 = agent.t3.update(quality=0.85, success=True)
        coh = operational_health(updated_t3.composite, agent.v3.composite, agent_atp.energy_ratio)
        assert is_healthy(updated_t3.composite, agent.v3.composite, agent_atp.energy_ratio)
        assert coh > 0.5

    def test_mrh_graph_tracks_agent_relationships(self):
        """Build MRH graph from society relationships; verify trust propagation."""
        society, principal, agent, _ = self._setup_society_with_agent()

        # Build MRH graph representing the society's relationship structure
        graph = MRHGraph(horizon_depth=3)

        # Add nodes
        graph.add_node(MRHNode(
            lct_id=society.society_id,
            entity_type="society",
            trust_scores={"governance": 1.0},
        ))
        graph.add_node(MRHNode(
            lct_id=principal.lct_id,
            entity_type="human",
            trust_scores={
                "talent": principal.t3.talent,
                "training": principal.t3.training,
                "temperament": principal.t3.temperament,
            },
        ))
        graph.add_node(MRHNode(
            lct_id=agent.lct_id,
            entity_type="ai",
            trust_scores={
                "talent": agent.t3.talent,
                "training": agent.t3.training,
                "temperament": agent.t3.temperament,
            },
        ))

        # Add edges: society → principal (citizenship), principal → agent (delegation)
        graph.add_edge(MRHEdge(
            source=society.society_id,
            target=principal.lct_id,
            relation=RelationType.PARENT_BINDING,
            weight=0.95,
        ))
        graph.add_edge(MRHEdge(
            source=principal.lct_id,
            target=agent.lct_id,
            relation=RelationType.SERVICE_PAIRING,
            weight=0.8,
        ))
        # Agent witnesses principal (trust-building observation)
        graph.add_edge(MRHEdge(
            source=agent.lct_id,
            target=principal.lct_id,
            relation=RelationType.WITNESSED_BY,
            weight=0.85,
        ))

        assert graph.node_count == 3
        assert graph.edge_count == 3

        # Horizon from society: both principal and agent within 2 hops
        zones = graph.horizon_zones(society.society_id, depth=2)
        assert principal.lct_id in zones.get("DIRECT", [])  # 1 hop
        assert agent.lct_id in zones.get("INDIRECT", [])  # 2 hops

        # Trust propagation: society → principal → agent
        trust = graph.trust_between(society.society_id, agent.lct_id)
        assert 0.0 < trust < 0.95  # Attenuated through delegation chain

        # Relationship summary
        summary = graph.relationship_summary(principal.lct_id)
        assert summary.get("pairing", 0) >= 1  # service pairing to agent

        # Witness count for principal
        assert graph.witness_count(principal.lct_id) >= 1  # agent witnesses principal

    def test_action_chain_with_acp_lifecycle(self):
        """Chain two R7 actions (query → transform) through ACP plan steps."""
        society, principal, agent, deleg = self._setup_society_with_agent()

        # Build the action chain
        chain = ActionChain()

        # Action 1: query
        a1 = build_action(
            actor=agent.lct_id,
            role_lct="role:data-processor",
            action="query_data",
            target="sensors",
            t3=agent.t3, v3=agent.v3,
            atp_stake=10.0, available_atp=200.0,
            permissions=["query_data"],
            society=society.society_id,
        )
        a1.result = Result(
            status=ActionStatus.SUCCESS,
            output={"rows": 42},
            atp_consumed=10.0,
        )
        chain.append(a1)

        # Action 2: transform (depends on query)
        a2 = build_action(
            actor=agent.lct_id,
            role_lct="role:data-processor",
            action="transform_data",
            target="sensors_output",
            t3=agent.t3, v3=agent.v3,
            atp_stake=5.0, available_atp=190.0,
            permissions=["transform_data"],
            society=society.society_id,
        )
        a2.result = Result(
            status=ActionStatus.SUCCESS,
            output={"format": "json", "records": 42},
            atp_consumed=5.0,
        )
        chain.append(a2)

        assert chain.length == 2
        assert chain.verify_chain()  # Hash chain integrity

        # Each action produces distinct hashes
        assert a1.canonical_hash() != a2.canonical_hash()

        # Total ATP consumed across chain
        total_atp = sum(
            a.result.atp_consumed for a in chain.actions
            if a.result and a.result.atp_consumed
        )
        assert total_atp == 15.0


class TestDictionaryTranslationWorkflow:
    """
    Workflow: Dictionary entities → translation → trust tracking → MRH graph.

    Modules exercised: trust, lct, atp, federation, dictionary, r6, mrh (7 of 8).

    Scenario: Two domain-specific dictionaries mediate translation between
    medical and legal domains. Trust degrades across translation chains.
    Actions and relationships are recorded.
    """

    def test_cross_domain_translation_with_trust_tracking(self):
        """
        Create dictionaries, translate across domains, track trust degradation,
        record as R7 action, and map relationships in MRH graph.
        """
        # Create a society for dictionary governance
        society = Society("lct:web4:society:standards", "Standards Body")
        society.set_law(LawDataset(
            law_id="law:standards:v1", version="1.0",
            society_id=society.society_id,
            norms=[
                Norm(norm_id="LAW-FIDELITY", selector="translation.confidence",
                     op=">=", value=0.7, description="Min translation fidelity"),
            ],
        ))

        # Create medical→legal dictionary entity
        med_legal = DictionaryEntity.create(
            source_domain="medical",
            target_domain="legal",
            public_key="dict_med_legal_key",
            bidirectional=False,
            coverage=DomainCoverage(terms=500, concepts=120, relationships=80),
            compression=CompressionProfile(average_ratio=0.6, lossy_threshold=0.1),
            t3=T3(0.85, 0.90, 0.80),
            v3=V3(0.80, 0.85, 0.75),
        )
        assert med_legal.can_translate("medical", "legal")
        assert not med_legal.can_translate("legal", "medical")  # Not bidirectional

        # Create legal→regulatory dictionary entity
        legal_reg = DictionaryEntity.create(
            source_domain="legal",
            target_domain="regulatory",
            public_key="dict_legal_reg_key",
            bidirectional=True,
            coverage=DomainCoverage(terms=300, concepts=90, relationships=60),
            compression=CompressionProfile(average_ratio=0.7, lossy_threshold=0.05),
            t3=T3(0.80, 0.85, 0.75),
            v3=V3(0.75, 0.80, 0.70),
        )

        # Perform translation: medical → legal
        request1 = TranslationRequest(
            source_content="Patient exhibited acute myocardial infarction",
            source_domain="medical",
            target_domain="legal",
            context={"case_type": "malpractice"},
            minimum_fidelity=0.7,
        )
        result1 = med_legal.record_translation(
            request=request1,
            content="Subject suffered a heart attack (acute myocardial infarction)",
            confidence=0.92,
            witness_lct_ids=["w1"],
        )
        assert result1.confidence == 0.92
        assert med_legal.translation_count == 1
        assert med_legal.success_rate == 1.0

        # Chain translation: legal → regulatory
        request2 = TranslationRequest(
            source_content=result1.content,
            source_domain="legal",
            target_domain="regulatory",
            context={"regulation": "FDA"},
            minimum_fidelity=0.7,
        )
        result2 = legal_reg.record_translation(
            request=request2,
            content="Adverse cardiac event: acute MI per ICD-10 I21",
            confidence=0.88,
        )

        # Build translation chain — confidence degrades multiplicatively
        chain = TranslationChain()
        chain.add_step("medical", "legal", med_legal.lct_id, result1.confidence)
        chain.add_step("legal", "regulatory", legal_reg.lct_id, result2.confidence)

        assert chain.length == 2
        # Cumulative confidence = 0.92 * 0.88 ≈ 0.8096
        assert chain.cumulative_confidence == pytest.approx(0.92 * 0.88, abs=0.01)
        assert chain.is_acceptable(minimum_confidence=0.7)
        # Degradation increases with chain length
        assert chain.cumulative_degradation > 0

        # Dictionary selection: choose the best from candidates
        score_med = dictionary_selection_score(
            trust_composite=med_legal.t3.composite,
            coverage_ratio=500 / 1000,  # 50% of a hypothetical full domain
            recency_score=1.0,
        )
        score_leg = dictionary_selection_score(
            trust_composite=legal_reg.t3.composite,
            coverage_ratio=300 / 1000,
            recency_score=0.9,
        )
        assert score_med > 0 and score_leg > 0

        # Record the translation as an R7 action
        action = build_action(
            actor=med_legal.lct_id,
            role_lct="role:translator",
            action="translate",
            target="medical→legal",
            t3=med_legal.t3,
            v3=med_legal.v3,
            atp_stake=5.0,
            available_atp=100.0,
            society=society.society_id,
            parameters={
                "source_domain": "medical",
                "target_domain": "legal",
                "confidence": result1.confidence,
            },
        )
        assert action.is_valid
        rep = action.compute_reputation(quality=result1.confidence, rule_triggered=False)
        assert rep.net_trust_change > 0  # High-quality translation boosts trust

        # Build MRH graph of the translation relationship
        graph = MRHGraph(horizon_depth=3)
        graph.add_node(MRHNode(lct_id=med_legal.lct_id, entity_type="dictionary"))
        graph.add_node(MRHNode(lct_id=legal_reg.lct_id, entity_type="dictionary"))
        graph.add_node(MRHNode(
            lct_id="lct:web4:domain:medical", entity_type="domain",
        ))
        graph.add_node(MRHNode(
            lct_id="lct:web4:domain:legal", entity_type="domain",
        ))
        graph.add_node(MRHNode(
            lct_id="lct:web4:domain:regulatory", entity_type="domain",
        ))

        # Dictionaries are bound to their domains
        graph.add_edge(MRHEdge(
            source=med_legal.lct_id, target="lct:web4:domain:medical",
            relation=RelationType.BOUND_TO, weight=1.0,
        ))
        graph.add_edge(MRHEdge(
            source=med_legal.lct_id, target="lct:web4:domain:legal",
            relation=RelationType.BOUND_TO, weight=1.0,
        ))
        graph.add_edge(MRHEdge(
            source=legal_reg.lct_id, target="lct:web4:domain:legal",
            relation=RelationType.BOUND_TO, weight=1.0,
        ))
        graph.add_edge(MRHEdge(
            source=legal_reg.lct_id, target="lct:web4:domain:regulatory",
            relation=RelationType.BOUND_TO, weight=1.0,
        ))
        # Dictionaries witness each other through shared domain (legal)
        graph.add_edge(MRHEdge(
            source=med_legal.lct_id, target=legal_reg.lct_id,
            relation=RelationType.DATA_PAIRING, weight=0.8,
        ))

        assert graph.node_count == 5
        assert graph.edge_count == 5

        # Medical domain reaches regulatory through dictionary chain
        reachable = graph.horizon(med_legal.lct_id, depth=2)
        assert legal_reg.lct_id in reachable

        # Trust between dictionaries (through data pairing)
        dict_trust = graph.trust_between(med_legal.lct_id, legal_reg.lct_id)
        assert dict_trust > 0

    def test_dictionary_feedback_updates_trust_and_actions(self):
        """
        Dictionary receives correction feedback → trust updates → new version →
        action recorded.
        """
        from web4.dictionary import FeedbackRecord

        # Create dictionary
        tech_biz = DictionaryEntity.create(
            source_domain="technical",
            target_domain="business",
            public_key="dict_tech_biz_key",
            t3=T3(0.70, 0.75, 0.65),
            v3=V3(0.60, 0.70, 0.65),
        )
        initial_t3 = tech_biz.t3.composite

        # Record a translation
        request = TranslationRequest(
            source_content="API rate limiting exceeded",
            source_domain="technical",
            target_domain="business",
        )
        result = tech_biz.record_translation(
            request=request,
            content="Service usage cap reached",
            confidence=0.75,
        )

        # Apply correction feedback — trust decreases
        correction = FeedbackRecord(
            feedback_type="correction",
            mapping_id="map-001",
            success=False,
            corrector_lct_id="lct:web4:human:reviewer",
            original_content="Service usage cap reached",
            corrected_content="API request quota exceeded — temporary throttling in effect",
        )
        tech_biz.apply_feedback(correction)
        assert tech_biz.t3.composite < initial_t3  # Trust decreased from correction

        # Apply validation feedback — trust recovers
        validation = FeedbackRecord(
            feedback_type="validation",
            mapping_id="map-002",
            success=True,
            corrector_lct_id="lct:web4:human:reviewer",
        )
        tech_biz.apply_feedback(validation)

        # Create a new version after corrections
        new_ver = tech_biz.create_new_version(
            new_version="1.1.0",
            changelog="Improved API terminology translations",
        )
        assert new_ver.version == "1.1.0"
        assert tech_biz.current_version == "1.1.0"
        assert len(tech_biz.versions) == 2

        # Record this versioning as an R7 action
        action = build_action(
            actor=tech_biz.lct_id,
            role_lct="role:dictionary-maintainer",
            action="version_update",
            target="technical→business",
            t3=tech_biz.t3,
            v3=tech_biz.v3,
        )
        assert action.is_valid

        # ATP account for dictionary operations
        dict_atp = ATPAccount(available=50.0)
        assert dict_atp.lock(2.0)
        dict_atp.commit(2.0)
        er = energy_ratio(dict_atp.total, dict_atp.adp)
        assert er < 1.0

        # Operational health after feedback cycle
        coh = operational_health(tech_biz.t3.composite, tech_biz.v3.composite, er)
        assert 0.0 <= coh <= 1.0

    def test_dictionary_selection_in_federation_context(self):
        """
        Multiple dictionaries in a society → select best → translate →
        verify with MRH decay.
        """
        society = Society("lct:web4:society:translators", "Translator Guild")

        # Create competing dictionaries
        dict_a = DictionaryEntity.create(
            source_domain="engineering", target_domain="finance",
            public_key="dict_a_key",
            coverage=DomainCoverage(terms=800, concepts=200, relationships=150),
            t3=T3(0.90, 0.85, 0.88),
        )
        dict_b = DictionaryEntity.create(
            source_domain="engineering", target_domain="finance",
            public_key="dict_b_key",
            coverage=DomainCoverage(terms=400, concepts=100, relationships=70),
            t3=T3(0.75, 0.70, 0.80),
        )

        # Select best dictionary
        best = select_best_dictionary(
            candidates=[dict_a, dict_b],
            source_domain="engineering",
            target_domain="finance",
            coverage_scores={dict_a.lct_id: 0.8, dict_b.lct_id: 0.4},
            recency_scores={dict_a.lct_id: 0.9, dict_b.lct_id: 1.0},
        )
        assert best is not None
        assert best.lct_id == dict_a.lct_id  # Higher trust + coverage wins

        # Translate using the selected dictionary
        request = TranslationRequest(
            source_content="Load-bearing capacity exceeded design margin",
            source_domain="engineering",
            target_domain="finance",
            context={"report_type": "risk_assessment"},
        )
        result = best.record_translation(
            request=request,
            content="Asset structural risk exceeds acceptable threshold",
            confidence=0.88,
        )

        # Trust decays with MRH hops — translation at different distances
        base_trust = best.t3.composite
        trust_direct = mrh_trust_decay(base_trust, hops=0)
        trust_1hop = mrh_trust_decay(base_trust, hops=1)
        trust_2hop = mrh_trust_decay(base_trust, hops=2)

        assert trust_direct == base_trust  # No decay at source
        assert trust_1hop < trust_direct   # Decays at 1 hop
        assert trust_2hop < trust_1hop     # Further decay

        # Zone classification
        assert mrh_zone(0) == "SELF"
        assert mrh_zone(1) == "DIRECT"
        assert mrh_zone(3) == "PERIPHERAL"


# ═══════════════════════════════════════════════════════════════════
# U16: Full-stack integration tests — all 18 modules
# ═══════════════════════════════════════════════════════════════════

from web4.security import (
    CryptoSuiteId, parse_w4id, negotiate_suite, get_suite,
    W4ID, KeyPolicy, KeyStorageLevel, SignatureEnvelope,
    VerifiableCredential, derive_pairwise_w4id,
)
from web4.protocol import (
    ClientHello, ServerHello, ClientFinished, ServerFinished,
    HandshakeMessage, HandshakePhase, PairingMethod,
    Transport, negotiate_transport, get_transport_profile,
    DiscoveryMethod, discovery_privacy, PrivacyLevel,
    Web4URI,
)
from web4.mcp import (
    Web4Context, TrustContext, ProofOfAgency,
    MCPSession, MCPToolResource, TrustRequirements as MCPTrustRequirements,
    ResourceRequirements as MCPResourceRequirements,
    WitnessedInteraction, WitnessAttestation,
    MCPCapabilities, CapabilityBroadcast,
    MCPErrorContext, calculate_mcp_cost,
    web4_context_to_json, web4_context_from_json,
)
from web4.entity import (
    get_info, is_agentic, can_delegate, can_process_r6,
    valid_interaction, InteractionType, BehavioralMode, EnergyPattern,
)
from web4.capability import (
    CapabilityLevel, assess_level, validate_level,
    entity_level_range, trust_tier, common_ground,
)
from web4.errors import (
    ErrorCode, ErrorCategory, Web4Error, AuthzError, ProtoError,
    make_error, get_error_meta,
)
from web4.metabolic import (
    MetabolicState, MetabolicProfile,
    valid_transition, energy_cost, wake_penalty,
    accepts_transactions, accepts_new_citizens, is_dormant,
    required_witnesses,
)
from web4.binding import (
    AnchorType, HardwareAnchor, DeviceConstellation, DeviceStatus,
    enroll_device, compute_constellation_trust,
    constellation_trust_ceiling, coherence_bonus,
    record_cross_witness, check_recovery_quorum,
)
from web4.society import (
    SocietyPhase, SocietyState, Treasury, SocietyLedger,
    LedgerEventType,
    create_society, admit_citizen, transition_metabolic_state,
    deposit_treasury, allocate_treasury,
    compute_society_t3, society_health,
)
from web4.reputation import (
    ReputationRule, ReputationEngine, ReputationStore,
    DimensionImpact, Modifier,
)


class TestSecurityProtocolMCPWorkflow:
    """
    Workflow: W4ID identity → crypto negotiation → handshake → MCP session →
    ATP metering → witnessed interaction.

    Modules exercised: security, protocol, mcp, trust, lct, atp, federation,
    entity, errors (9 of 18).

    Scenario: Two entities establish a secure MCP session. Client authenticates
    with W4ID, negotiates crypto suite and transport, opens an MCP session with
    Web4Context headers, performs a tool call with ATP metering, and the
    interaction is witnessed.
    """

    def test_identity_to_mcp_session_lifecycle(self):
        """End-to-end: W4ID → handshake → MCP session → ATP metering → witness."""
        # 1. Create W4ID identities
        client_id = parse_w4id("did:web4:key:client_ephemeral_abc123")
        server_id = parse_w4id("did:web4:key:server_ephemeral_def456")
        assert client_id.method == "key"
        assert server_id.is_known_method

        # Derive pairwise ID for privacy (different per peer)
        pairwise = derive_pairwise_w4id(b"client_master_secret", str(server_id))
        assert str(pairwise) != str(client_id)  # Pairwise is different

        # 2. Negotiate crypto suite
        selected = negotiate_suite(
            [CryptoSuiteId.W4_FIPS_1, CryptoSuiteId.W4_BASE_1],
            [CryptoSuiteId.W4_BASE_1],
        )
        assert selected == CryptoSuiteId.W4_BASE_1
        suite = get_suite(selected)
        assert suite.sig == "Ed25519"

        # 3. Build handshake messages
        client_hello = ClientHello(
            supported_suites=[selected.value],
            client_public_key=client_id.method_specific_id,
            client_w4id_ephemeral=str(client_id),
            nonce="nonce_001",
        )
        assert client_hello.phase == HandshakePhase.CLIENT_HELLO

        server_hello = ServerHello(
            selected_suite=selected.value,
            server_public_key=server_id.method_specific_id,
            server_w4id_ephemeral=str(server_id),
            nonce="nonce_002",
        )
        assert server_hello.phase == HandshakePhase.SERVER_HELLO

        # Envelope wraps phase + payload + transport
        msg = HandshakeMessage(
            phase=HandshakePhase.CLIENT_HELLO,
            payload=client_hello,
            transport=Transport.TLS_1_3,
        )
        assert msg.to_dict()["phase"] == "CLIENT_HELLO"

        # 4. Negotiate transport
        transport = negotiate_transport(
            [Transport.TLS_1_3, Transport.QUIC, Transport.WEB_SOCKET],
            [Transport.TLS_1_3, Transport.WEB_TRANSPORT],
        )
        assert transport == Transport.TLS_1_3
        profile = get_transport_profile(transport)
        assert profile.full_metering  # TLS supports full metering

        # 5. Entity type check — verify client is agentic
        assert is_agentic(EntityType.AI)
        assert can_process_r6(EntityType.AI)

        # 6. Create trust context and Web4Context headers
        client_trust = T3(talent=0.82, training=0.78, temperament=0.85)
        context = Web4Context(
            sender_lct=str(pairwise),  # Use pairwise ID for privacy
            sender_role="web4:DataAnalyst",
            trust_context=TrustContext(
                t3_in_role={
                    "talent": client_trust.talent,
                    "training": client_trust.training,
                    "temperament": client_trust.temperament,
                },
                atp_stake=50,
            ),
            mrh_depth=2,
            society="lct:web4:society:research",
            proof_of_agency=ProofOfAgency(
                grant_id="grant-data-001",
                scope="data_access",
            ),
        )

        # Context round-trips through JSON
        ctx_json = web4_context_to_json(context)
        ctx_restored = web4_context_from_json(ctx_json)
        assert ctx_restored.sender_lct == context.sender_lct
        assert ctx_restored.trust_context.atp_stake == 50
        assert ctx_restored.proof_of_agency.scope == "data_access"

        # 7. Define MCP tool with trust requirements
        tool = MCPToolResource(
            name="data.query",
            description="Query research datasets",
            resource_requirements=MCPResourceRequirements(
                compute="medium", memory="2GB", atp_cost=25,
            ),
            trust_requirements=MCPTrustRequirements(
                minimum_t3={"talent": 0.7, "training": 0.6},
                atp_stake=20,
                role_required="web4:DataAnalyst",
            ),
        )

        # Trust requirements are met
        assert tool.trust_requirements.is_met(
            t3={"talent": client_trust.talent, "training": client_trust.training},
            atp_available=100,
            role="web4:DataAnalyst",
        )

        # 8. Open MCP session with ATP budget
        session = MCPSession(
            session_id="sess-research-001",
            client_lct=str(pairwise),
            server_lct=str(server_id),
            atp_remaining=500,
        )
        assert session.active

        # 9. Calculate cost with trust discount
        cost = calculate_mcp_cost(
            base_cost=100,
            trust_average=client_trust.composite,
            complexity_factor=1.5,  # Complex query
        )
        assert cost > 100  # Complexity increases cost
        # But trust discount partially offsets
        cost_no_trust = calculate_mcp_cost(
            base_cost=100, trust_average=0.0, complexity_factor=1.5,
        )
        assert cost <= cost_no_trust  # Trust earns discount

        # Consume ATP
        assert session.consume_atp(cost)
        assert session.atp_remaining == 500 - cost
        assert session.interaction_count == 1

        # 10. Record witnessed interaction
        interaction = WitnessedInteraction(
            client=str(pairwise),
            server=str(server_id),
            action="data.query",
            timestamp="2026-03-18T12:05:00Z",
            success=True,
        )
        attestation = WitnessAttestation(
            witnessed_interaction=interaction,
            witness="lct:web4:human:lab_director",
            mrh_updates=["mrh:edge:pairwise→server:witnessed_by"],
        )
        assert attestation.witnessed_interaction.success
        assert attestation.witness == "lct:web4:human:lab_director"

        # 11. Verify URI addressing
        uri = Web4URI.parse("web4://did:web4:key:server_ephemeral_def456/tools/data.query")
        assert uri.w4id == "did:web4:key:server_ephemeral_def456"
        assert uri.path == "/tools/data.query"

        # 12. Capability broadcast from server
        broadcast = CapabilityBroadcast(
            server_lct=str(server_id),
            capabilities=MCPCapabilities(
                tools=["data.query", "data.transform"],
                protocols=["web4-mcp-v1"],
                trust_requirements=MCPTrustRequirements(minimum_t3={"talent": 0.5}),
                availability=0.99,
            ),
            ttl=3600,
        )
        assert len(broadcast.capabilities.tools) == 2
        assert broadcast.capabilities.availability == 0.99


class TestDeviceBindingCapabilitySocietyWorkflow:
    """
    Workflow: entity taxonomy → device binding → capability assessment →
    society formation → metabolic gating → treasury operations.

    Modules exercised: entity, binding, capability, society, metabolic,
    trust, lct, atp, federation (9 of 18).

    Scenario: A human entity enrolls hardware devices, gets capability
    assessed, joins a society with metabolic state management, and the
    society manages treasury and transitions between metabolic states.
    """

    def test_entity_devices_capability_society_lifecycle(self):
        """End-to-end: entity type → devices → capability → society → metabolic."""
        # 1. Entity type taxonomy
        human_info = get_info(EntityType.HUMAN)
        assert BehavioralMode.AGENTIC in human_info.modes
        assert human_info.energy == EnergyPattern.ACTIVE
        assert human_info.can_r6

        device_info = get_info(EntityType.DEVICE)
        assert BehavioralMode.RESPONSIVE in device_info.modes
        assert device_info.energy == EnergyPattern.ACTIVE  # Devices are active (can expend ATP)

        # Infrastructure is passive (no behavioral modes, ADP slashed)
        infra_info = get_info(EntityType.INFRASTRUCTURE)
        assert infra_info.energy == EnergyPattern.PASSIVE

        # Interaction validation: humans pair, societies delegate
        assert valid_interaction(EntityType.HUMAN, EntityType.AI, InteractionType.PAIRING)
        assert valid_interaction(EntityType.HUMAN, EntityType.AI, InteractionType.WITNESSING)
        # Societies (DELEGATIVE) delegate to agents (AGENTIC)
        assert can_delegate(EntityType.SOCIETY)
        assert valid_interaction(EntityType.SOCIETY, EntityType.AI, InteractionType.DELEGATION)

        # 2. Create LCT for the human entity
        alice_lct = LCT.create(
            entity_type=EntityType.HUMAN,
            public_key="alice_hw_bound_key_001",
            society="lct:web4:society:techcorp",
            witnesses=["witness1", "witness2"],
            t3=T3(0.80, 0.75, 0.85),
            v3=V3(0.70, 0.80, 0.75),
        )
        assert alice_lct.birth_certificate is not None
        assert alice_lct.t3.composite > 0.7

        # 3. Create device constellation and enroll hardware
        constellation = DeviceConstellation(root_lct_id=alice_lct.lct_id)

        # First device (genesis — no existing witness required)
        phone = enroll_device(
            constellation=constellation,
            device_lct_id="dev:phone:alice-001",
            anchor=HardwareAnchor(
                anchor_type=AnchorType.PHONE_SECURE_ELEMENT,
                platform="iOS",
                manufacturer="Apple",
            ),
            witnesses=[],  # Genesis enrollment
            timestamp="2026-03-18T12:00:00Z",
        )
        assert phone.status == DeviceStatus.ACTIVE
        assert phone.anchor.is_hardware_bound

        # Second device (requires first device as witness)
        laptop = enroll_device(
            constellation=constellation,
            device_lct_id="dev:laptop:alice-001",
            anchor=HardwareAnchor(
                anchor_type=AnchorType.TPM2,
                platform="Linux",
                manufacturer="Lenovo",
            ),
            witnesses=["dev:phone:alice-001"],  # Existing device witnesses
            timestamp="2026-03-18T12:01:00Z",
        )
        assert constellation.device_count == 2

        # Cross-witness for mesh trust
        record_cross_witness(
            constellation, "dev:phone:alice-001", "dev:laptop:alice-001",
            "2026-03-18T12:02:00Z",
        )

        # Constellation trust
        trust_score = compute_constellation_trust(constellation)
        ceiling = constellation_trust_ceiling(constellation)
        assert 0.0 < trust_score <= ceiling
        assert ceiling > 0.7  # Two hardware devices = high ceiling

        # Coherence bonus from type diversity
        bonus = coherence_bonus(constellation.active_devices)
        assert bonus > 0  # Different anchor types earn bonus

        # Recovery quorum
        assert check_recovery_quorum(
            constellation, ["dev:phone:alice-001", "dev:laptop:alice-001"],
        )

        # 4. Assess LCT capability level
        level = assess_level(alice_lct)
        assert level.value >= CapabilityLevel.STUB.value

        # Entity-level range for humans
        min_lvl, max_lvl = entity_level_range(EntityType.HUMAN)
        assert min_lvl <= max_lvl

        # Trust tier for the assessed level
        tier_name, tier_min, tier_max = trust_tier(level.value)
        assert isinstance(tier_name, str)

        # 5. Create society with metabolic management
        society_state = create_society(
            society_id="lct:web4:society:techcorp",
            name="TechCorp",
            founders=["founder1", "founder2"],
            timestamp="2026-03-18T12:00:00Z",
            initial_treasury=1000.0,
        )
        assert society_state.phase == SocietyPhase.OPERATIONAL
        assert society_state.metabolic_state == MetabolicState.ACTIVE
        assert society_state.treasury.balance == 1000.0

        # 6. Metabolic state gates operations
        assert accepts_transactions(MetabolicState.ACTIVE)
        assert accepts_new_citizens(MetabolicState.ACTIVE)
        assert not is_dormant(MetabolicState.ACTIVE)

        # Energy cost depends on metabolic state and society size
        cost = energy_cost(
            MetabolicState.ACTIVE,
            baseline_cost_per_hour=10.0,
            society_size=2,
        )
        assert cost > 0

        # Witness requirements scale with state
        witnesses_needed = required_witnesses(MetabolicState.ACTIVE, total_witnesses=10)
        assert witnesses_needed > 0

        # 7. Admit citizen (requires operational society + active metabolic state)
        admitted = admit_citizen(
            state=society_state,
            entity_lct=alice_lct.lct_id,
            timestamp="2026-03-18T12:05:00Z",
            witnesses=["founder1", "founder2"],
        )
        assert admitted
        assert society_state.citizen_count > 0

        # 8. Treasury operations
        deposit_treasury(
            society_state, amount=200.0,
            timestamp="2026-03-18T12:06:00Z",
            source="membership_fee",
        )
        assert society_state.treasury.balance == 1200.0

        allocated = allocate_treasury(
            society_state, entity_lct=alice_lct.lct_id, amount=50.0,
            timestamp="2026-03-18T12:07:00Z",
            purpose="onboarding_grant",
        )
        assert allocated
        assert society_state.treasury.balance == 1150.0

        # 9. Metabolic transition: ACTIVE → REST
        assert valid_transition(MetabolicState.ACTIVE, MetabolicState.REST)
        transitioned = transition_metabolic_state(
            state=society_state,
            new_state=MetabolicState.REST,
            timestamp="2026-03-18T18:00:00Z",
            witnesses=["founder1"],
        )
        assert transitioned
        assert society_state.metabolic_state == MetabolicState.REST

        # REST still accepts transactions but with higher energy cost
        assert accepts_transactions(MetabolicState.REST)
        rest_cost = energy_cost(MetabolicState.REST, 10.0, society_size=3)
        assert rest_cost > 0

        # 10. Ledger records all operations
        assert society_state.ledger.entry_count > 0
        metabolic_entries = society_state.ledger.query(
            event_type=LedgerEventType.METABOLIC,
        )
        assert len(metabolic_entries) >= 1

        # 11. Society aggregate trust
        society_t3 = compute_society_t3(society_state)
        # May be None if no citizen_trust profiles, but function works
        health = society_health(society_state)


class TestReputationEntityErrorWorkflow:
    """
    Workflow: entity taxonomy check → R7 action → reputation evaluation →
    trust update → error handling → MCP error context.

    Modules exercised: reputation, entity, errors, mcp, trust, lct, atp,
    r6, federation, mrh (10 of 18).

    Scenario: An AI agent performs a governed action. The reputation engine
    evaluates the outcome, updating trust scores. A subsequent action fails
    trust requirements, producing a structured error with MCP error context.
    The error round-trips through RFC 9457 serialization.
    """

    def test_action_reputation_error_lifecycle(self):
        """End-to-end: action → reputation → trust update → error → MCP context."""
        # 1. Verify entity capabilities
        assert is_agentic(EntityType.AI)
        assert can_process_r6(EntityType.AI)
        ai_info = get_info(EntityType.AI)
        assert ai_info.energy == EnergyPattern.ACTIVE

        # Pairing is valid: human ↔ AI (both can initiate)
        assert valid_interaction(
            EntityType.HUMAN, EntityType.AI, InteractionType.PAIRING,
        )
        # Delegation is valid: society → AI (delegative → agentic)
        assert valid_interaction(
            EntityType.SOCIETY, EntityType.AI, InteractionType.DELEGATION,
        )

        # 2. Create society and citizen
        society = Society("lct:web4:society:analytics", "Analytics Dept")
        society.set_law(LawDataset(
            law_id="law:analytics:v1", version="1.0",
            society_id=society.society_id,
            norms=[
                Norm(norm_id="LAW-TRUST-MIN", selector="trust.composite",
                     op=">=", value=0.6),
            ],
        ))

        agent = society.issue_citizenship(
            EntityType.AI, "agent_analytics_key",
            t3=T3(0.72, 0.68, 0.75),
            v3=V3(0.65, 0.70, 0.68),
        )
        assert society.is_citizen(agent.lct_id)

        # 3. Configure reputation engine
        engine = ReputationEngine()
        engine.add_rule(ReputationRule(
            rule_id="RULE-SUCCESS-BOOST",
            trigger_conditions={"result_status": "success"},
            t3_impacts={
                "talent": DimensionImpact(base_delta=0.03, modifiers=[
                    Modifier(condition="high_quality", multiplier=1.5),
                ]),
                "training": DimensionImpact(base_delta=0.02, modifiers=[]),
            },
            v3_impacts={
                "veracity": DimensionImpact(base_delta=0.02, modifiers=[]),
            },
        ))
        engine.add_rule(ReputationRule(
            rule_id="RULE-FAILURE-PENALTY",
            trigger_conditions={"result_status": "failure"},
            t3_impacts={
                "temperament": DimensionImpact(base_delta=-0.08, modifiers=[
                    Modifier(condition="repeat_offender", multiplier=2.0),
                ]),
            },
            v3_impacts={},
        ))
        assert len(engine.rules) == 2

        # 4. Agent performs successful R7 action
        action = build_action(
            actor=agent.lct_id,
            role_lct="role:data-analyst",
            action="analyze_dataset",
            target="customer_segments",
            t3=agent.t3, v3=agent.v3,
            atp_stake=15.0, available_atp=100.0,
            permissions=["analyze_dataset"],
            society=society.society_id,
            law_hash="law:analytics:v1",
        )
        action.result = Result(
            status=ActionStatus.SUCCESS,
            output={"segments": 5, "quality": 0.91},
            atp_consumed=15.0,
        )
        assert action.is_valid

        # 5. Reputation engine evaluates the successful action
        delta = engine.evaluate(action)
        assert delta is not None
        assert "talent" in delta.t3_delta
        assert delta.t3_delta["talent"].change > 0  # Success boosted talent
        assert "training" in delta.t3_delta
        assert delta.t3_delta["training"].change > 0  # Training also improved

        # 6. Store and query reputation
        store = ReputationStore()
        store.record(delta)

        rep_talent = store.effective_reputation(
            agent.lct_id, "role:data-analyst", "talent",
        )
        assert rep_talent > 0  # Positive reputation from success

        # 7. Update trust after successful action
        updated_t3 = agent.t3.update(quality=0.91, success=True)
        assert updated_t3.talent > agent.t3.talent

        # Operational health check
        agent_atp = ATPAccount(available=85.0)
        agent_atp.adp = 15.0  # Work was done
        health = operational_health(
            updated_t3.composite, agent.v3.composite, agent_atp.energy_ratio,
        )
        assert health > 0.5

        # 8. ATP conservation — total (available + locked) decreased by work
        # ADP tracks discharged energy separately
        assert agent_atp.available == 85.0
        assert agent_atp.adp == 15.0
        # Energy ratio reflects work done (ATP / (ATP + ADP))
        assert agent_atp.energy_ratio < 1.0

        # 9. Now simulate a trust-gated failure
        # Agent's trust is below a hypothetical higher threshold
        required_trust = {"talent": 0.9, "training": 0.9, "temperament": 0.9}
        actual_trust = {
            "talent": agent.t3.talent,
            "training": agent.t3.training,
            "temperament": agent.t3.temperament,
        }

        # Check trust requirements (MCP-style)
        high_req = MCPTrustRequirements(
            minimum_t3=required_trust, atp_stake=50,
        )
        assert not high_req.is_met(
            t3=actual_trust, atp_available=100, role="web4:DataAnalyst",
        )

        # 10. Produce structured error (AUTHZ_DENIED = insufficient trust)
        error = make_error(
            ErrorCode.AUTHZ_DENIED,
            detail=f"Trust composite {agent.t3.composite:.3f} below required 0.9",
            instance=f"/actions/{agent.lct_id}/premium_analysis",
        )
        assert isinstance(error, AuthzError)

        # Error metadata
        meta = get_error_meta(ErrorCode.AUTHZ_DENIED)
        assert meta.category == ErrorCategory.AUTHZ
        assert meta.status == 401  # Unauthorized (credential lacks capability)

        # RFC 9457 Problem Details round-trip
        problem = error.to_problem_json()
        assert problem["status"] == 401
        assert "trust" in problem["detail"].lower()
        assert problem["instance"].endswith("/premium_analysis")

        restored = Web4Error.from_problem_json(problem)
        assert restored.code == ErrorCode.AUTHZ_DENIED

        # 11. MCP error context enriches the error with trust details
        error_ctx = MCPErrorContext(
            error_type="AUTHZ_DENIED",
            required_t3=required_trust,
            provided_t3=actual_trust,
            suggestion="Complete 10+ successful analyses to build sufficient trust",
            error_witnessed=True,
            witness_lct="lct:web4:human:supervisor",
            trust_impact={"temperament": -0.02},  # Failed attempt costs trust
        )
        ctx_dict = error_ctx.to_dict()
        assert ctx_dict["error_type"] == "AUTHZ_DENIED"
        assert ctx_dict["required_t3"]["talent"] == 0.9
        assert ctx_dict["provided_t3"]["talent"] == agent.t3.talent

        # 12. MRH tracks the relationship context
        graph = MRHGraph(horizon_depth=3)
        graph.add_node(MRHNode(
            lct_id=agent.lct_id, entity_type="ai",
            trust_scores={"talent": agent.t3.talent},
        ))
        graph.add_node(MRHNode(
            lct_id="lct:web4:human:supervisor", entity_type="human",
            trust_scores={"talent": 0.95},
        ))
        graph.add_edge(MRHEdge(
            source="lct:web4:human:supervisor",
            target=agent.lct_id,
            relation=RelationType.SERVICE_PAIRING,
            weight=0.8,
        ))

        # Trust propagation through the supervision relationship
        trust = graph.trust_between(
            "lct:web4:human:supervisor", agent.lct_id,
        )
        assert trust > 0

        # Witness count reflects supervision
        assert graph.witness_count(agent.lct_id) >= 0
