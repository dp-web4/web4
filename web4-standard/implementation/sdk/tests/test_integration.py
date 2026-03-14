"""
Cross-module integration tests for the Web4 Python SDK.

These tests verify that trust, lct, atp, and federation modules compose
correctly in end-to-end workflows. Each test exercises a realistic scenario
that spans multiple modules — not unit-level behavior of any single module.

Sprint task: S2
"""

import pytest

from web4.trust import T3, V3, TrustProfile, coherence, is_coherent, mrh_trust_decay, mrh_zone
from web4.lct import LCT, EntityType, RevocationStatus
from web4.atp import ATPAccount, transfer, sliding_scale, check_conservation, energy_ratio
from web4.federation import Society, LawDataset, Norm, Procedure, Delegation


class TestEntityLifecycle:
    """Workflow: society issues citizen → assign trust → check coherence."""

    def test_birth_to_trust_assessment(self):
        """Create entity via society, assign role trust, compute coherence."""
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

        # Coherence check using T3/V3 composites + energy ratio
        account = ATPAccount(available=80.0)
        account.adp = 20.0  # spent some energy
        coh = coherence(alice.t3.composite, alice.v3.composite, account.energy_ratio)
        assert 0.0 <= coh <= 1.0
        assert is_coherent(alice.t3.composite, alice.v3.composite, account.energy_ratio)

    def test_revoked_entity_loses_coherence(self):
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
        authority delegation → ATP transfer governed by law → coherence check.
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

        # 9. Coherence check
        coh = coherence(
            alice_t3_updated.composite,
            alice.v3.composite,
            alice_atp.energy_ratio,
        )
        assert coh > 0.5  # entity is coherent
        assert is_coherent(
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
