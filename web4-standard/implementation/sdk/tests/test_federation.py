"""
Test web4.federation module — Society, Authority, Law (SAL).

Tests verify:
- Society creates LCTs with proper birth certificates (integrates web4.lct)
- Authority delegation with scope limits
- Sub-delegation attenuation (cannot amplify)
- Law dataset versioning and norm checking
- Fractal citizenship (nested societies)
- Law inheritance from parent society
- Witness quorum enforcement
- Citizenship lifecycle (apply → active → suspended → reinstated → terminated)
- Quorum policy modes (threshold, majority, unanimous)
- Ledger type classification
- Law merge (parent + child norm inheritance)
- Audit requests and adjustments with appeal path validation
"""

import pytest

from web4.federation import (
    Society, Delegation, LawDataset, Norm, Procedure, Interpretation, RoleType,
    CitizenshipStatus, CitizenshipRecord, valid_citizenship_transition,
    QuorumMode, QuorumPolicy, LedgerType,
    AuditRequest, AuditAdjustment,
    merge_law,
)
from web4.lct import EntityType, RevocationStatus
from web4.trust import T3, V3


class TestSociety:
    """Core society operations."""

    def test_create_society(self):
        s = Society("lct:web4:society:acme", "ACME Corp")
        assert s.society_id == "lct:web4:society:acme"
        assert s.name == "ACME Corp"
        assert len(s.citizens) == 0
        assert s.depth == 0

    def test_issue_citizenship(self):
        s = Society("lct:web4:society:acme", "ACME Corp")
        lct = s.issue_citizenship(
            entity_type=EntityType.HUMAN,
            public_key="alice_key",
            witnesses=["w1", "w2"],
        )
        # LCT is properly formed
        assert lct.is_active
        assert lct.binding.entity_type == EntityType.HUMAN
        assert lct.birth_certificate is not None
        assert lct.birth_certificate.issuing_society == "lct:web4:society:acme"

        # Society tracks citizenship
        assert s.is_citizen(lct.lct_id)
        assert len(s.citizens) == 1

    def test_citizenship_first_pairing_is_citizen_role(self):
        """Birth certificate creates citizen role as first pairing (§2.1)."""
        s = Society("lct:web4:society:test", "Test")
        lct = s.issue_citizenship(EntityType.AI, "bot_key")

        assert len(lct.mrh.paired) == 1
        pairing = lct.mrh.paired[0]
        assert pairing.pairing_type == "birth_certificate"
        assert pairing.permanent is True
        assert "citizen" in pairing.lct_id

    def test_multiple_citizens(self):
        s = Society("lct:web4:society:test", "Test")
        lct1 = s.issue_citizenship(EntityType.HUMAN, "key1")
        lct2 = s.issue_citizenship(EntityType.AI, "key2")
        assert len(s.citizens) == 2
        assert s.is_citizen(lct1.lct_id)
        assert s.is_citizen(lct2.lct_id)

    def test_citizenship_with_custom_t3v3(self):
        s = Society("lct:web4:society:test", "Test")
        lct = s.issue_citizenship(
            EntityType.HUMAN, "key",
            t3=T3(0.8, 0.7, 0.9),
            v3=V3(0.6, 0.5, 0.4),
        )
        assert lct.t3.talent == 0.8
        assert lct.v3.valuation == 0.6

    def test_society_with_quorum_policy(self):
        qp = QuorumPolicy(mode=QuorumMode.THRESHOLD, required=3)
        s = Society("soc", "Soc", quorum_policy=qp)
        assert s.quorum_policy.required == 3
        assert s.quorum_policy.mode == QuorumMode.THRESHOLD
        assert s.witness_quorum == 3  # backward compat

    def test_society_with_ledger_type(self):
        s = Society("soc", "Soc", ledger_type=LedgerType.WITNESSED)
        assert s.ledger_type == LedgerType.WITNESSED

    def test_default_ledger_type_is_confined(self):
        s = Society("soc", "Soc")
        assert s.ledger_type == LedgerType.CONFINED


class TestAuthority:
    """Authority delegation (§5.2)."""

    def setup_method(self):
        self.society = Society("lct:web4:society:acme", "ACME")
        self.alice = self.society.issue_citizenship(EntityType.HUMAN, "alice_key")
        self.bob = self.society.issue_citizenship(EntityType.HUMAN, "bob_key")

    def test_delegate_authority(self):
        d = self.society.delegate_authority(
            self.alice.lct_id, scope="finance", permissions=["approve_atp", "audit"],
        )
        assert d.active
        assert d.scope == "finance"
        assert "approve_atp" in d.permissions
        assert d.delegator == self.society.society_id

    def test_delegate_must_be_citizen(self):
        """Cannot delegate to non-citizen."""
        with pytest.raises(ValueError, match="not a citizen"):
            self.society.delegate_authority(
                "lct:web4:stranger", scope="finance", permissions=["read"],
            )

    def test_has_permission(self):
        self.society.delegate_authority(
            self.alice.lct_id, scope="finance", permissions=["approve_atp"],
        )
        assert self.society.has_permission(self.alice.lct_id, "finance", "approve_atp")
        assert not self.society.has_permission(self.alice.lct_id, "finance", "delete")
        assert not self.society.has_permission(self.bob.lct_id, "finance", "approve_atp")

    def test_revoke_delegation(self):
        d = self.society.delegate_authority(
            self.alice.lct_id, scope="safety", permissions=["inspect"],
        )
        assert self.society.has_permission(self.alice.lct_id, "safety", "inspect")

        self.society.revoke_delegation(d.delegation_id)
        assert not self.society.has_permission(self.alice.lct_id, "safety", "inspect")

    def test_sub_delegation(self):
        """Delegate can sub-delegate with reduced scope."""
        d = self.society.delegate_authority(
            self.alice.lct_id, scope="finance",
            permissions=["approve_atp", "audit", "report"],
            max_depth=2,
        )
        # Alice sub-delegates to Bob with fewer permissions
        sub = d.sub_delegate(self.bob.lct_id, permissions=["report"])
        assert sub is not None
        assert sub.permissions == ["report"]
        assert sub.max_depth == 1  # reduced by 1
        assert sub.delegator == self.alice.lct_id

    def test_sub_delegation_cannot_amplify(self):
        """Sub-delegation cannot add permissions not in parent."""
        d = self.society.delegate_authority(
            self.alice.lct_id, scope="finance", permissions=["read"],
        )
        sub = d.sub_delegate(self.bob.lct_id, permissions=["read", "write"])
        assert sub is None  # Cannot amplify

    def test_sub_delegation_depth_limit(self):
        """Cannot sub-delegate past max_depth."""
        d = self.society.delegate_authority(
            self.alice.lct_id, scope="ops", permissions=["read"],
            max_depth=0,  # no sub-delegation allowed
        )
        assert not d.can_sub_delegate()
        sub = d.sub_delegate(self.bob.lct_id)
        assert sub is None

    def test_active_delegations_filter(self):
        self.society.delegate_authority(self.alice.lct_id, "finance", ["read"])
        self.society.delegate_authority(self.bob.lct_id, "safety", ["inspect"])
        d3 = self.society.delegate_authority(self.alice.lct_id, "ops", ["deploy"])
        d3.revoke()

        assert len(self.society.active_delegations()) == 2
        assert len(self.society.active_delegations(self.alice.lct_id)) == 1


class TestLawDataset:
    """Law dataset operations (§4)."""

    def test_create_law(self):
        law = LawDataset(
            law_id="web4://law/acme/1.0.0",
            version="1.0.0",
            society_id="lct:web4:society:acme",
            norms=[
                Norm("LAW-ATP-LIMIT", "r6.resource.atp", "<=", 100, "Max ATP per transaction"),
                Norm("LAW-MIN-TRUST", "t3.composite", ">=", 0.3, "Minimum trust to participate"),
            ],
            procedures=[
                Procedure("PROC-WITNESS-QUORUM", requires_witnesses=3, description="3 witnesses required"),
            ],
        )
        assert law.version == "1.0.0"
        assert len(law.norms) == 2
        assert len(law.procedures) == 1

    def test_law_hash_deterministic(self):
        """Same content → same hash."""
        kwargs = dict(
            law_id="test", version="1.0", society_id="s1",
            norms=[Norm("N1", "x", "<=", 10)],
        )
        law1 = LawDataset(**kwargs)
        law2 = LawDataset(**kwargs)
        assert law1.hash == law2.hash

    def test_law_hash_changes_with_content(self):
        law1 = LawDataset("test", "1.0", "s1", norms=[Norm("N1", "x", "<=", 10)])
        law2 = LawDataset("test", "1.0", "s1", norms=[Norm("N1", "x", "<=", 20)])
        assert law1.hash != law2.hash

    def test_norm_check(self):
        norm = Norm("N1", "atp", "<=", 100)
        assert norm.check(50)
        assert norm.check(100)
        assert not norm.check(101)

    def test_norm_operators(self):
        assert Norm("n", "x", ">=", 5).check(5)
        assert Norm("n", "x", ">=", 5).check(10)
        assert not Norm("n", "x", ">=", 5).check(4)
        assert Norm("n", "x", "==", 7).check(7)
        assert not Norm("n", "x", "==", 7).check(8)
        assert Norm("n", "x", "!=", 0).check(1)
        assert not Norm("n", "x", "!=", 0).check(0)

    def test_law_check_norm(self):
        law = LawDataset("test", "1.0", "s1", norms=[Norm("ATP-LIMIT", "atp", "<=", 100)])
        assert law.check_norm("ATP-LIMIT", 50) is True
        assert law.check_norm("ATP-LIMIT", 150) is False
        assert law.check_norm("NONEXISTENT", 50) is None

    def test_law_with_interpretations(self):
        law = LawDataset(
            "test", "1.1", "s1",
            interpretations=[
                Interpretation("INT-1"),
                Interpretation("INT-2", replaces="INT-1", reason="edge case fix"),
            ],
        )
        assert len(law.interpretations) == 2
        assert law.interpretations[1].replaces == "INT-1"


class TestFractalCitizenship:
    """Nested society composition (§3.2, §3.5)."""

    def test_nested_societies(self):
        ecosystem = Society("lct:web4:society:ecosystem", "Ecosystem")
        network = Society("lct:web4:society:network", "Network", parent=ecosystem)
        org = Society("lct:web4:society:org", "Org", parent=network)

        assert ecosystem.depth == 0
        assert network.depth == 1
        assert org.depth == 2

    def test_ancestry(self):
        root = Society("root", "Root")
        mid = Society("mid", "Mid", parent=root)
        leaf = Society("leaf", "Leaf", parent=mid)

        assert leaf.ancestry == ["root", "mid", "leaf"]
        assert root.ancestry == ["root"]

    def test_parent_child_links(self):
        parent = Society("parent", "Parent")
        child = Society("child", "Child", parent=parent)
        assert parent.find_child("child") is child
        assert parent.find_child("nonexistent") is None
        assert len(parent.children) == 1

    def test_law_inheritance(self):
        """Child inherits parent law if no local law set (§3.5)."""
        parent = Society("parent", "Parent")
        child = Society("child", "Child", parent=parent)

        parent_law = LawDataset("law1", "1.0", "parent",
                                norms=[Norm("PARENT-RULE", "x", "<=", 100)])
        parent.set_law(parent_law)

        # Child has no law → inherits parent's
        assert child.effective_law() is parent_law
        assert child.effective_law().check_norm("PARENT-RULE", 50) is True

    def test_law_override(self):
        """Child law overrides parent law (§3.5)."""
        parent = Society("parent", "Parent")
        child = Society("child", "Child", parent=parent)

        parent.set_law(LawDataset("p_law", "1.0", "parent",
                                  norms=[Norm("RULE", "x", "<=", 100)]))
        child_law = LawDataset("c_law", "1.0", "child",
                               norms=[Norm("RULE", "x", "<=", 50)])
        child.set_law(child_law)

        # Child's own law takes precedence
        assert child.effective_law() is child_law
        assert child.effective_law().check_norm("RULE", 75) is False  # child says <=50

    def test_no_law_anywhere(self):
        """No law in hierarchy → None."""
        s = Society("solo", "Solo")
        assert s.effective_law() is None


class TestWitnessQuorum:
    """Witness quorum enforcement via law."""

    def test_quorum_enforced(self):
        """Society enforces witness quorum from law procedures."""
        s = Society("soc", "Soc")
        s.set_law(LawDataset("law", "1.0", "soc",
                              procedures=[Procedure("PROC-WITNESS-QUORUM", requires_witnesses=3)]))

        # Too few witnesses → error
        with pytest.raises(ValueError, match="Insufficient witnesses"):
            s.issue_citizenship(EntityType.HUMAN, "key", witnesses=["w1", "w2"])

        # Enough witnesses → success
        lct = s.issue_citizenship(EntityType.HUMAN, "key", witnesses=["w1", "w2", "w3"])
        assert lct.is_active

    def test_no_quorum_law_allows_any(self):
        """Without quorum law, any number of witnesses is OK."""
        s = Society("soc", "Soc")
        lct = s.issue_citizenship(EntityType.AI, "key", witnesses=[])
        assert lct.is_active


class TestRoleTypes:
    """Role type enum coverage."""

    def test_all_sal_roles(self):
        assert RoleType.CITIZEN.value == "citizen"
        assert RoleType.AUTHORITY.value == "authority"
        assert RoleType.LAW_ORACLE.value == "law_oracle"
        assert RoleType.WITNESS.value == "witness"
        assert RoleType.AUDITOR.value == "auditor"
        assert len(RoleType) == 5


# ── New: Citizenship Lifecycle ──────────────────────────────────

class TestCitizenshipStatus:
    """Citizenship lifecycle states and transitions."""

    def test_all_statuses(self):
        assert len(CitizenshipStatus) == 5
        assert CitizenshipStatus.APPLIED.value == "applied"
        assert CitizenshipStatus.TERMINATED.value == "terminated"

    def test_valid_transitions(self):
        assert valid_citizenship_transition(CitizenshipStatus.APPLIED, CitizenshipStatus.ACTIVE)
        assert valid_citizenship_transition(CitizenshipStatus.APPLIED, CitizenshipStatus.PROVISIONAL)
        assert valid_citizenship_transition(CitizenshipStatus.ACTIVE, CitizenshipStatus.SUSPENDED)
        assert valid_citizenship_transition(CitizenshipStatus.ACTIVE, CitizenshipStatus.TERMINATED)
        assert valid_citizenship_transition(CitizenshipStatus.SUSPENDED, CitizenshipStatus.ACTIVE)
        assert valid_citizenship_transition(CitizenshipStatus.SUSPENDED, CitizenshipStatus.TERMINATED)

    def test_invalid_transitions(self):
        # Terminated is final
        assert not valid_citizenship_transition(CitizenshipStatus.TERMINATED, CitizenshipStatus.ACTIVE)
        # Can't go backwards
        assert not valid_citizenship_transition(CitizenshipStatus.ACTIVE, CitizenshipStatus.APPLIED)
        # Can't skip
        assert not valid_citizenship_transition(CitizenshipStatus.APPLIED, CitizenshipStatus.SUSPENDED)

    def test_citizenship_record_lifecycle(self):
        """Full lifecycle: active → suspended → reinstated → terminated."""
        record = CitizenshipRecord(entity_lct="lct:alice", society_id="soc:acme")
        assert record.is_active

        # Suspend
        assert record.transition(CitizenshipStatus.SUSPENDED)
        assert record.status == CitizenshipStatus.SUSPENDED
        assert record.suspended_at is not None
        assert not record.is_active

        # Reinstate
        assert record.transition(CitizenshipStatus.ACTIVE)
        assert record.status == CitizenshipStatus.ACTIVE
        assert record.suspended_at is None  # Cleared on reinstatement
        assert record.is_active

        # Terminate
        assert record.transition(CitizenshipStatus.TERMINATED)
        assert record.status == CitizenshipStatus.TERMINATED
        assert record.terminated_at is not None
        assert not record.is_active

        # Terminal — no further transitions
        assert not record.transition(CitizenshipStatus.ACTIVE)

    def test_citizenship_record_defaults(self):
        record = CitizenshipRecord(entity_lct="lct:x", society_id="soc:y")
        assert record.rights == ["exist", "interact", "accumulate_reputation"]
        assert record.obligations == ["abide_law", "respect_quorum"]
        assert record.granted_at != ""


class TestSocietyCitizenshipLifecycle:
    """Society-level citizenship lifecycle methods."""

    def setup_method(self):
        self.society = Society("soc:test", "Test")
        self.lct = self.society.issue_citizenship(EntityType.HUMAN, "key")

    def test_issue_creates_record(self):
        record = self.society.get_citizenship(self.lct.lct_id)
        assert record is not None
        assert record.is_active
        assert record.society_id == "soc:test"

    def test_suspend_citizen(self):
        assert self.society.suspend_citizen(self.lct.lct_id)
        assert not self.society.is_citizen(self.lct.lct_id)  # Suspended ≠ active
        record = self.society.get_citizenship(self.lct.lct_id)
        assert record.status == CitizenshipStatus.SUSPENDED

    def test_reinstate_citizen(self):
        self.society.suspend_citizen(self.lct.lct_id)
        assert self.society.reinstate_citizen(self.lct.lct_id)
        assert self.society.is_citizen(self.lct.lct_id)

    def test_terminate_citizen(self):
        assert self.society.terminate_citizen(self.lct.lct_id)
        assert not self.society.is_citizen(self.lct.lct_id)
        assert self.lct.lct_id not in self.society.citizens

    def test_terminate_is_permanent(self):
        self.society.terminate_citizen(self.lct.lct_id)
        assert not self.society.reinstate_citizen(self.lct.lct_id)

    def test_suspended_cannot_delegate(self):
        """Suspended citizen cannot receive authority delegation."""
        self.society.suspend_citizen(self.lct.lct_id)
        with pytest.raises(ValueError, match="not a citizen"):
            self.society.delegate_authority(self.lct.lct_id, "finance", ["read"])

    def test_unknown_citizen_operations_return_false(self):
        assert not self.society.suspend_citizen("lct:nonexistent")
        assert not self.society.reinstate_citizen("lct:nonexistent")
        assert not self.society.terminate_citizen("lct:nonexistent")
        assert self.society.get_citizenship("lct:nonexistent") is None


# ── New: Quorum Policy ──────────────────────────────────────────

class TestQuorumPolicy:
    """QuorumPolicy modes and checks."""

    def test_threshold_mode(self):
        qp = QuorumPolicy(mode=QuorumMode.THRESHOLD, required=3)
        assert qp.check(3)
        assert qp.check(5)
        assert not qp.check(2)

    def test_majority_mode(self):
        qp = QuorumPolicy(mode=QuorumMode.MAJORITY)
        assert qp.check(3, total_registered=5)   # 3 > 2.5
        assert not qp.check(2, total_registered=5)  # 2 ≤ 2.5
        assert not qp.check(1, total_registered=0)  # No registered = fail

    def test_unanimous_mode(self):
        qp = QuorumPolicy(mode=QuorumMode.UNANIMOUS)
        assert qp.check(5, total_registered=5)
        assert not qp.check(4, total_registered=5)
        assert not qp.check(0, total_registered=0)

    def test_default_quorum(self):
        qp = QuorumPolicy()
        assert qp.mode == QuorumMode.THRESHOLD
        assert qp.required == 2


# ── New: Ledger Types ───────────────────────────────────────────

class TestLedgerType:
    def test_all_types(self):
        assert LedgerType.CONFINED.value == "confined"
        assert LedgerType.WITNESSED.value == "witnessed"
        assert LedgerType.PARTICIPATORY.value == "participatory"
        assert len(LedgerType) == 3


# ── New: Law Merge ──────────────────────────────────────────────

class TestLawMerge:
    """merge_law: parent + child norm inheritance (§3.5)."""

    def test_child_overrides_parent_norm(self):
        parent = LawDataset("p", "1.0", "p",
                            norms=[Norm("SHARED", "x", "<=", 100),
                                   Norm("PARENT-ONLY", "y", ">=", 0)])
        child = LawDataset("c", "1.0", "c",
                           norms=[Norm("SHARED", "x", "<=", 50)])

        merged = merge_law(parent, child)
        assert len(merged.norms) == 2  # SHARED (child) + PARENT-ONLY
        assert merged.check_norm("SHARED", 75) is False   # Child's <=50
        assert merged.check_norm("PARENT-ONLY", 1) is True  # Inherited

    def test_parent_procs_inherited(self):
        parent = LawDataset("p", "1.0", "p",
                            procedures=[Procedure("PROC-A", 3)])
        child = LawDataset("c", "1.0", "c",
                           procedures=[Procedure("PROC-B", 2)])
        merged = merge_law(parent, child)
        assert len(merged.procedures) == 2
        assert merged.get_procedure("PROC-A") is not None
        assert merged.get_procedure("PROC-B") is not None

    def test_child_overrides_proc(self):
        parent = LawDataset("p", "1.0", "p",
                            procedures=[Procedure("PROC-A", 3)])
        child = LawDataset("c", "1.0", "c",
                           procedures=[Procedure("PROC-A", 1)])
        merged = merge_law(parent, child)
        assert len(merged.procedures) == 1
        assert merged.get_procedure("PROC-A").requires_witnesses == 1  # Child wins

    def test_effective_law_merge_mode(self):
        """Society.effective_law(merge=True) merges hierarchically."""
        parent_soc = Society("parent", "Parent")
        child_soc = Society("child", "Child", parent=parent_soc)

        parent_soc.set_law(LawDataset("p_law", "1.0", "parent",
                                       norms=[Norm("PARENT-ONLY", "x", "<=", 100),
                                              Norm("SHARED", "y", "<=", 200)]))
        child_soc.set_law(LawDataset("c_law", "1.0", "child",
                                      norms=[Norm("SHARED", "y", "<=", 50)]))

        # Default mode: child overrides entirely
        default = child_soc.effective_law(merge=False)
        assert default.check_norm("PARENT-ONLY", 50) is None  # Not inherited

        # Merge mode: child overrides + parent inherited
        merged = child_soc.effective_law(merge=True)
        assert merged.check_norm("PARENT-ONLY", 50) is True   # Inherited
        assert merged.check_norm("SHARED", 75) is False        # Child's <=50

    def test_merge_no_parent_returns_child_law(self):
        """Merge with no parent just returns child law."""
        soc = Society("solo", "Solo")
        soc.set_law(LawDataset("law", "1.0", "solo", norms=[Norm("N1", "x", "<=", 10)]))
        merged = soc.effective_law(merge=True)
        assert merged.check_norm("N1", 5) is True


# ── New: Audit ──────────────────────────────────────────────────

class TestAudit:
    """Audit request and adjustment validation (§5.5)."""

    def test_audit_request_creation(self):
        req = AuditRequest(
            audit_id="audit:001",
            society_id="soc:acme",
            auditor_lct="lct:auditor",
            targets=["lct:alice", "lct:bob"],
            scope=["data_analysis"],
            evidence=["hash:ev1", "hash:ev2"],
            proposed_t3_deltas={"temperament": -0.02},
            proposed_v3_deltas={"veracity": -0.03},
        )
        assert len(req.targets) == 2
        assert req.proposed_t3_deltas["temperament"] == -0.02
        assert req.timestamp != ""

    def test_positive_adjustment_valid_without_appeal(self):
        adj = AuditAdjustment(
            audit_id="audit:001",
            target_lct="lct:alice",
            applied_t3_deltas={"training": 0.05},
            applied_v3_deltas={"validity": 0.03},
            witnesses=["w1", "w2"],
        )
        assert not adj.has_negative_adjustment()
        assert adj.is_valid()

    def test_negative_adjustment_requires_appeal_path(self):
        adj = AuditAdjustment(
            audit_id="audit:002",
            target_lct="lct:alice",
            applied_t3_deltas={"temperament": -0.02},
            applied_v3_deltas={},
            witnesses=["w1", "w2"],
        )
        assert adj.has_negative_adjustment()
        assert not adj.is_valid()  # Missing appeal path

    def test_negative_adjustment_with_appeal_is_valid(self):
        adj = AuditAdjustment(
            audit_id="audit:003",
            target_lct="lct:alice",
            applied_t3_deltas={"temperament": -0.02},
            applied_v3_deltas={"veracity": -0.01},
            witnesses=["w1", "w2", "w3"],
            appeal_path="soc:acme:appeal:003",
        )
        assert adj.has_negative_adjustment()
        assert adj.is_valid()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
