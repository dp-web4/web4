# SPDX-License-Identifier: MIT
# Pytest-compatible wrappers for Hardbound test suites
#
# Runs the existing sequential test suites (test_team.py, test_integration.py,
# attack_simulations.py) through pytest discovery.

import pytest
from datetime import datetime, timezone, timedelta
from hardbound.team import Team, TeamConfig


class TestTeamSuite:
    """Run the full team test suite as a single pytest test."""

    def test_full_team_suite(self):
        """Execute all team tests sequentially (they share state)."""
        from hardbound.test_team import main
        main()


class TestIntegrationSuite:
    """Run cross-layer integration tests."""

    def test_integration_suite(self):
        """Execute all integration tests."""
        from hardbound.test_integration import main
        main()


class TestAttackSimulations:
    """Run attack simulation suite."""

    def test_attack_simulations(self):
        """Execute all 6 attack vectors."""
        from hardbound.attack_simulations import run_all_attacks
        results = run_all_attacks()
        assert len(results) == 11


class TestEndToEndIntegration:
    """Full integration test: R6 → Multi-Sig → Federation → Execution."""

    def test_full_admin_transfer_workflow(self):
        """
        End-to-end test of a critical action (admin transfer) requiring:
        1. R6 request creation
        2. Multi-sig delegation and voting
        3. Federation witness selection and attestation
        4. Execution and outcome propagation
        """
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType
        from hardbound.multisig import MultiSigManager, CriticalAction, ProposalStatus
        from hardbound.federation import FederationRegistry

        # === PHASE 1: Setup teams and federation ===
        config = TeamConfig(
            name="integration-team",
            description="Integration test team",
            default_member_budget=200,
        )
        team = Team(config=config)
        team.set_admin("admin:int")
        members = ["voter:a", "voter:b", "voter:c", "voter:d"]
        for m in members:
            team.add_member(m, role="developer", atp_budget=100)
            member = team.get_member(m)
            member["trust"] = {k: 0.85 for k in member["trust"]}
        team._update_team()

        # Federation with witness team
        fed = FederationRegistry()
        fed.register_team(team.team_id, "Integration Team", creator_lct="alice")
        fed.register_team("team:witness_a", "Witness A", creator_lct="bob")
        fed.register_team("team:witness_b", "Witness B", creator_lct="carol")

        # === PHASE 2: Setup R6 workflow with multi-sig ===
        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="admin_transfer",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.5,
            atp_cost=25,
            approval=ApprovalType.MULTI_SIG,
            approval_count=3,
        ))

        msig = MultiSigManager(team, federation=fed)
        wf = R6Workflow(team, policy, multisig=msig)

        # Add admin as member so they can use R6 (R6 requires get_member)
        team.add_member("admin:int", role="admin", atp_budget=200)
        admin_member = team.get_member("admin:int")
        admin_member["trust"] = {k: 0.90 for k in admin_member["trust"]}
        team._update_team()

        # === PHASE 3: Create R6 request (creates linked multi-sig proposal) ===
        r6_request = wf.create_request(
            requester_lct="admin:int",
            action_type="admin_transfer",
            description="Transfer admin to new leader",
            parameters={"new_admin_lct": "new_leader:int"},
        )

        # Verify R6 created with linked proposal
        assert r6_request.status == R6Status.PENDING
        assert r6_request.linked_proposal_id != ""
        assert r6_request.expires_at != ""

        proposal = msig.get_proposal(r6_request.linked_proposal_id)
        assert proposal is not None
        assert proposal.external_witness_required >= 1

        # === PHASE 4: Vote via R6 (delegates to multi-sig) ===
        wf.approve_request(r6_request.r6_id, "voter:b")
        wf.approve_request(r6_request.r6_id, "voter:c")
        wf.approve_request(r6_request.r6_id, "voter:d")

        # Check proposal has votes
        proposal = msig.get_proposal(r6_request.linked_proposal_id)
        assert proposal.approval_count >= 3

        # === PHASE 5: Request external witnesses from federation ===
        witness_teams = msig.request_external_witnesses(
            r6_request.linked_proposal_id, seed=42)
        assert len(witness_teams) >= 1

        # Add external witness manually (simulating witness responding)
        witness_team = witness_teams[0]
        msig.add_external_witness(
            r6_request.linked_proposal_id,
            witness_lct=f"witness:{witness_team['team_id']}",
            witness_team_id=witness_team["team_id"],
            witness_trust_score=0.9,
            attestation="Verified proposal legitimacy",
        )

        # === PHASE 6: Verify proposal is approved ===
        proposal = msig.get_proposal(r6_request.linked_proposal_id)
        assert proposal.status == ProposalStatus.APPROVED

        # R6 should also be approved now
        r6_reloaded = wf.get_request(r6_request.r6_id)
        assert r6_reloaded.status == R6Status.APPROVED

        # === PHASE 7: Execute R6 ===
        result = wf.execute_request(r6_request.r6_id, success=True)
        assert result.status == R6Status.EXECUTED

        # === PHASE 8: Verify federation health ===
        health = fed.get_federation_health()
        assert health["overall_health"] in ("healthy", "warning")

        # === PHASE 9: Verify audit trail ===
        audit = team.ledger.get_session_audit_trail(team.team_id)
        action_types = [a.get("action_type") for a in audit]
        assert "r6_created" in action_types
        assert "r6_approved" in action_types
        assert "r6_completed" in action_types  # execute_request records as r6_completed
        assert "witnesses_requested" in action_types
        assert "multisig_external_witness" in action_types


class TestStandaloneComponents:
    """Individual component tests that don't require shared state."""

    def test_team_creation(self):
        config = TeamConfig(name="pytest-team", description="Created by pytest")
        team = Team(config=config)
        assert team.team_id.startswith("web4:team:")
        assert team.config.name == "pytest-team"

    def test_member_management(self):
        config = TeamConfig(name="member-test", description="Member management")
        team = Team(config=config)
        team.set_admin("web4:soft:admin:pytest")
        team.add_member("web4:soft:dev:pytest", role="developer", atp_budget=100)
        member = team.get_member("web4:soft:dev:pytest")
        assert member is not None
        assert member["role"] == "developer"
        assert member["atp_budget"] == 100

    def test_trust_velocity_caps(self):
        """Verify velocity caps limit per-day trust growth."""
        config = TeamConfig(name="velocity-test", description="Velocity cap test")
        team = Team(config=config)
        team.set_admin("web4:soft:admin:vel")
        team.add_member("web4:soft:dev:vel", role="developer")

        # Rapid-fire 50 success updates (same epoch/day)
        for _ in range(50):
            team.update_member_trust("web4:soft:dev:vel", "success", 1.0)

        trust = team.get_member_trust("web4:soft:dev:vel")
        # With velocity caps, no dimension should exceed base + cap
        for dim, val in trust.items():
            cap = Team.TRUST_VELOCITY_CAPS.get(dim, 0.10)
            assert val <= 0.5 + cap + 0.01, (
                f"{dim} exceeded velocity cap: {val:.3f} > {0.5 + cap:.3f}"
            )

    def test_atp_consumption(self):
        config = TeamConfig(name="atp-test", description="ATP test")
        team = Team(config=config)
        team.set_admin("web4:soft:admin:atp")
        team.add_member("web4:soft:dev:atp", role="developer", atp_budget=100)
        remaining = team.consume_member_atp("web4:soft:dev:atp", 30)
        assert remaining == 70
        assert team.get_member_atp("web4:soft:dev:atp") == 70

    def test_audit_chain_integrity(self):
        config = TeamConfig(name="audit-test", description="Audit chain test")
        team = Team(config=config)
        team.set_admin("web4:soft:admin:audit")
        team.add_member("web4:soft:dev:audit", role="developer")
        valid, error = team.verify_audit_chain()
        assert valid is True, f"Audit chain invalid: {error}"


class TestActivityQuality:
    """Activity quality scoring tests."""

    def test_activity_quality_self_test(self):
        """Run the full activity quality self-test."""
        from hardbound.activity_quality import _self_test
        _self_test()

    def test_micro_ping_detection(self):
        """Micro-pings should get minimal trust decay credit."""
        from hardbound.activity_quality import (
            ActivityWindow, ActivityTier, compute_quality_adjusted_decay
        )
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        window = ActivityWindow(entity_id="test:micro", window_seconds=86400*7)
        for day in range(7):
            ts = (now - timedelta(days=6-day)).isoformat()
            window.record("presence_ping", ts)

        assert window.tier == ActivityTier.TRIVIAL
        adjusted = compute_quality_adjusted_decay(7, window)
        assert adjusted < 1.0, "Micro-pings should get <1.0 credit for 7 days"

    def test_diverse_work_scores_high(self):
        """Diverse meaningful actions should score well."""
        from hardbound.activity_quality import ActivityWindow, ActivityTier
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        window = ActivityWindow(entity_id="test:diverse")
        types = ["r6_created", "r6_approved", "r6_completed", "trust_update",
                 "multisig_vote", "heartbeat", "audit_record"]
        for i, tx_type in enumerate(types):
            ts = (now - timedelta(hours=6-i)).isoformat()
            window.record(tx_type, ts, atp_cost=2.0 if i % 2 == 0 else 0.0)

        assert window.quality_score > 0.4
        assert window.tier in (ActivityTier.HIGH, ActivityTier.CRITICAL)


class TestSybilDetection:
    """Sybil detection tests."""

    def test_sybil_self_test(self):
        """Run the full Sybil detection self-test."""
        from hardbound.sybil_detection import _self_test
        _self_test()

    def test_clean_team_no_false_positives(self):
        """Clean team with diverse trust should not trigger detection."""
        from hardbound.sybil_detection import SybilDetector, SybilRisk

        detector = SybilDetector()
        trusts = {
            "dev_a": {"reliability": 0.75, "competence": 0.60, "alignment": 0.80,
                      "consistency": 0.70, "witnesses": 0.55, "lineage": 0.65},
            "dev_b": {"reliability": 0.50, "competence": 0.85, "alignment": 0.45,
                      "consistency": 0.60, "witnesses": 0.70, "lineage": 0.40},
        }
        report = detector.analyze_team("test:clean", trusts)
        assert report.overall_risk == SybilRisk.NONE

    def test_identical_trust_detected(self):
        """Members with identical trust should be flagged."""
        from hardbound.sybil_detection import SybilDetector, SybilRisk

        detector = SybilDetector()
        same = {"reliability": 0.55, "competence": 0.55, "alignment": 0.55,
                "consistency": 0.55, "witnesses": 0.55, "lineage": 0.55}
        trusts = {
            "sybil_1": same.copy(),
            "sybil_2": same.copy(),
            "honest": {"reliability": 0.80, "competence": 0.60, "alignment": 0.70,
                       "consistency": 0.65, "witnesses": 0.75, "lineage": 0.50},
        }
        report = detector.analyze_team("test:sybil", trusts)
        assert len(report.clusters) > 0
        assert any("sybil_1" in c.members and "sybil_2" in c.members
                   for c in report.clusters)


class TestWitnessDiminishing:
    """Tests for diminishing same-pair witnessing."""

    def test_diminishing_returns(self):
        """Repeated same-pair witnessing should have diminishing impact."""
        config = TeamConfig(name="witness-test", description="Witness test")
        team = Team(config=config)
        team.set_admin("admin:wit")
        team.add_member("witness:a", role="developer")
        team.add_member("target:a", role="developer")

        # First attestation: full effectiveness
        eff1 = team.get_witness_effectiveness("witness:a", "target:a")
        assert eff1 == 1.0

        trust1 = team.witness_member("witness:a", "target:a")
        wit_dim_1 = trust1["witnesses"]

        # 5 more attestations
        for _ in range(5):
            team.witness_member("witness:a", "target:a")

        eff6 = team.get_witness_effectiveness("witness:a", "target:a")
        assert eff6 < 0.35, f"After 6 attestations, effectiveness should be <35%, got {eff6}"

        # Fresh witness still has full effectiveness
        team.add_member("fresh:a", role="reviewer")
        eff_fresh = team.get_witness_effectiveness("fresh:a", "target:a")
        assert eff_fresh == 1.0

    def test_self_witness_blocked(self):
        """Cannot witness yourself."""
        config = TeamConfig(name="self-test", description="Self witness test")
        team = Team(config=config)
        team.set_admin("admin:self")
        team.add_member("member:self", role="developer")

        import pytest
        with pytest.raises(ValueError, match="Cannot witness yourself"):
            team.witness_member("member:self", "member:self")


class TestAuditHealth:
    """Team health audit tests."""

    def test_audit_health_report(self):
        """audit_health() returns complete health report."""
        config = TeamConfig(name="health-test", description="Health test")
        team = Team(config=config)
        team.set_admin("admin:h")
        team.add_member("dev:h1", role="developer")
        team.add_member("dev:h2", role="developer")

        report = team.audit_health()
        assert "team_id" in report
        assert "sybil" in report
        assert "trust" in report
        assert "witness_health" in report
        assert "health_score" in report
        assert report["member_count"] == 2
        assert report["health_score"] >= 0
        assert report["health_score"] <= 100

    def test_sybil_lowers_health(self):
        """Sybil-like patterns should lower health score."""
        config = TeamConfig(name="sybil-health", description="Sybil health test")
        team = Team(config=config)
        team.set_admin("admin:sh")

        # Create members with identical trust (Sybil signal)
        same_trust = {
            "reliability": 0.55, "competence": 0.55, "alignment": 0.55,
            "consistency": 0.55, "witnesses": 0.55, "lineage": 0.55,
        }
        for i in range(4):
            lct = f"sybil:{i}"
            team.add_member(lct, role="developer")
            member = team.get_member(lct)
            member["trust"] = same_trust.copy()
        team._update_team()

        report = team.audit_health()
        # Should detect Sybil patterns and lower health
        assert report["sybil"]["cluster_count"] > 0


class TestCrossTeamWitnessing:
    """Tests for cross-team witnessing on multi-sig proposals."""

    def _make_team_with_members(self, name, admin, members):
        """Helper: create a team with admin and high-trust members."""
        config = TeamConfig(name=name, description=f"{name} test team")
        team = Team(config=config)
        team.set_admin(admin)
        for m in members:
            team.add_member(m, role="developer")
            # Directly set trust above thresholds (velocity caps limit incremental growth)
            member = team.get_member(m)
            member["trust"] = {
                "reliability": 0.85, "competence": 0.85, "alignment": 0.85,
                "consistency": 0.85, "witnesses": 0.85, "lineage": 0.85,
            }
        team._update_team()
        return team

    def test_admin_transfer_requires_external_witness(self):
        """ADMIN_TRANSFER cannot execute without external witness."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        import pytest

        team = self._make_team_with_members(
            "xt-admin", "admin:xt",
            ["voter:1", "voter:2", "voter:3", "voter:4"]
        )
        msig = MultiSigManager(team)

        # Create admin transfer proposal
        proposal = msig.create_proposal(
            proposer_lct="admin:xt",
            action=CriticalAction.ADMIN_TRANSFER,
            action_data={"new_admin_lct": "voter:1"},
            description="Transfer admin to voter:1",
        )

        # Verify external_witness_required is set from quorum config
        assert proposal.external_witness_required == 1

        # Get enough votes to approve
        for voter in ["voter:2", "voter:3", "voter:4"]:
            msig.vote(proposal.proposal_id, voter, approve=True)

        # Proposal should be approved (quorum met)
        proposal = msig.get_proposal(proposal.proposal_id)
        assert proposal.status.value == "approved"

        # But execution should FAIL without external witness
        # (We bypass voting period check by monkey-patching for test)
        proposal.min_voting_period_hours = 0
        msig._save_proposal(proposal)

        with pytest.raises(ValueError, match="Insufficient external witnesses"):
            msig.execute_proposal(proposal.proposal_id, "admin:xt")

    def test_external_witness_must_be_outside_team(self):
        """External witnesses must not be members of the proposing team."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        import pytest

        team = self._make_team_with_members(
            "xt-outside", "admin:xo",
            ["voter:a", "voter:b", "voter:c", "voter:d"]
        )
        msig = MultiSigManager(team)

        proposal = msig.create_proposal(
            proposer_lct="admin:xo",
            action=CriticalAction.ADMIN_TRANSFER,
            action_data={"new_admin_lct": "voter:a"},
            description="Test external witness validation",
        )

        # Internal member cannot be external witness
        with pytest.raises(ValueError, match="member of this team"):
            msig.add_external_witness(
                proposal.proposal_id,
                witness_lct="voter:b",
                witness_team_id="web4:team:other",
                witness_trust_score=0.9,
            )

        # Same team ID also blocked
        with pytest.raises(ValueError, match="different team"):
            msig.add_external_witness(
                proposal.proposal_id,
                witness_lct="external:witness:1",
                witness_team_id=team.team_id,
                witness_trust_score=0.9,
            )

    def test_external_witness_enables_execution(self):
        """With external witness, admin transfer can execute."""
        from hardbound.multisig import MultiSigManager, CriticalAction

        team = self._make_team_with_members(
            "xt-execute", "admin:xe",
            ["voter:x1", "voter:x2", "voter:x3", "voter:x4"]
        )
        msig = MultiSigManager(team)

        proposal = msig.create_proposal(
            proposer_lct="admin:xe",
            action=CriticalAction.ADMIN_TRANSFER,
            action_data={"new_admin_lct": "voter:x1"},
            description="Transfer with external witness",
        )

        # Vote to approve
        for voter in ["voter:x2", "voter:x3", "voter:x4"]:
            msig.vote(proposal.proposal_id, voter, approve=True)

        # Add external witness from another team
        msig.add_external_witness(
            proposal.proposal_id,
            witness_lct="external:auditor:1",
            witness_team_id="web4:team:auditors",
            witness_trust_score=0.85,
            attestation="Verified admin transfer is legitimate",
        )

        # Bypass voting period for test
        proposal = msig.get_proposal(proposal.proposal_id)
        proposal.min_voting_period_hours = 0
        msig._save_proposal(proposal)

        # Now execution should succeed
        result = msig.execute_proposal(proposal.proposal_id, "admin:xe")
        assert result.status.value == "executed"
        assert len(result.external_witnesses) == 1

    def test_team_dissolution_requires_two_witnesses(self):
        """TEAM_DISSOLUTION requires 2 external witnesses."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        import pytest

        team = self._make_team_with_members(
            "xt-dissolve", "admin:xd",
            ["voter:d1", "voter:d2", "voter:d3", "voter:d4", "voter:d5"]
        )
        msig = MultiSigManager(team)

        proposal = msig.create_proposal(
            proposer_lct="admin:xd",
            action=CriticalAction.TEAM_DISSOLUTION,
            action_data={"reason": "Test dissolution"},
            description="Dissolve team for testing",
        )

        assert proposal.external_witness_required == 2

        # Only 1 external witness - should still fail
        msig.add_external_witness(
            proposal.proposal_id,
            witness_lct="external:gov:1",
            witness_team_id="web4:team:governance",
            witness_trust_score=0.9,
        )

        # Vote to approve (need 4 for dissolution)
        for voter in ["voter:d1", "voter:d2", "voter:d3", "voter:d4"]:
            msig.vote(proposal.proposal_id, voter, approve=True)

        # Bypass voting period
        proposal = msig.get_proposal(proposal.proposal_id)
        proposal.min_voting_period_hours = 0
        msig._save_proposal(proposal)

        # Should fail - only 1 of 2 required witnesses
        with pytest.raises(ValueError, match="Insufficient external witnesses"):
            msig.execute_proposal(proposal.proposal_id, "admin:xd")

        # Add second external witness
        msig.add_external_witness(
            proposal.proposal_id,
            witness_lct="external:gov:2",
            witness_team_id="web4:team:oversight",
            witness_trust_score=0.88,
        )

        # Now should succeed
        result = msig.execute_proposal(proposal.proposal_id, "admin:xd")
        assert result.status.value == "executed"
        assert len(result.external_witnesses) == 2


    def test_witness_diversity_blocks_same_team(self):
        """Two witnesses from the same team are blocked by diversity requirement."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        import pytest

        team = self._make_team_with_members(
            "xt-diverse", "admin:div",
            ["voter:v1", "voter:v2", "voter:v3", "voter:v4", "voter:v5"]
        )
        msig = MultiSigManager(team)

        # Dissolution requires 2 external witnesses
        proposal = msig.create_proposal(
            proposer_lct="admin:div",
            action=CriticalAction.TEAM_DISSOLUTION,
            action_data={"reason": "Diversity test"},
            description="Test witness diversity",
        )

        # First witness from team-alpha: OK
        msig.add_external_witness(
            proposal.proposal_id,
            witness_lct="ext:alpha:1",
            witness_team_id="web4:team:alpha",
            witness_trust_score=0.9,
        )

        # Second witness from SAME team-alpha: BLOCKED
        with pytest.raises(ValueError, match="already provided a witness"):
            msig.add_external_witness(
                proposal.proposal_id,
                witness_lct="ext:alpha:2",
                witness_team_id="web4:team:alpha",
                witness_trust_score=0.9,
            )

        # Second witness from team-beta: OK
        msig.add_external_witness(
            proposal.proposal_id,
            witness_lct="ext:beta:1",
            witness_team_id="web4:team:beta",
            witness_trust_score=0.9,
        )

        proposal = msig.get_proposal(proposal.proposal_id)
        assert len(proposal.external_witnesses) == 2
        assert len(proposal.external_witness_teams) == 2
        assert set(proposal.external_witness_teams) == {"web4:team:alpha", "web4:team:beta"}


class TestMemberRemoval:
    """Tests for Team.remove_member() with audit trail."""

    def test_admin_can_remove_member(self):
        """Admin can directly remove a member."""
        config = TeamConfig(name="rm-admin", description="Removal test")
        team = Team(config=config)
        team.set_admin("admin:rm")
        team.add_member("target:rm", role="developer")

        assert team.get_member("target:rm") is not None

        result = team.remove_member(
            "target:rm", requester_lct="admin:rm", reason="Performance issues"
        )

        assert result["removed_lct"] == "target:rm"
        assert "admin:rm" in result["auth_method"]
        assert result["archived_trust"] is not None
        assert team.get_member("target:rm") is None

    def test_cannot_remove_admin(self):
        """Admin cannot be removed (must use admin transfer)."""
        import pytest
        config = TeamConfig(name="rm-noadmin", description="No admin removal")
        team = Team(config=config)
        team.set_admin("admin:no")
        team.add_member("normal:1", role="developer")

        with pytest.raises(ValueError, match="Cannot remove admin"):
            team.remove_member("admin:no", requester_lct="admin:no")

    def test_non_admin_cannot_remove(self):
        """Non-admin cannot remove members without multi-sig."""
        import pytest
        config = TeamConfig(name="rm-noauth", description="No auth test")
        team = Team(config=config)
        team.set_admin("admin:na")
        team.add_member("member:a", role="developer")
        team.add_member("member:b", role="developer")

        with pytest.raises(PermissionError, match="admin authority or multi-sig"):
            team.remove_member("member:b", requester_lct="member:a")

    def test_removal_via_multisig(self):
        """Member can be removed via multi-sig proposal."""
        config = TeamConfig(name="rm-msig", description="Multi-sig removal")
        team = Team(config=config)
        team.set_admin("admin:ms")
        team.add_member("target:ms", role="developer")

        result = team.remove_member(
            "target:ms",
            reason="Voted out",
            via_multisig="msig:abc123",
        )

        assert result["removed_lct"] == "target:ms"
        assert "multisig:msig:abc123" in result["auth_method"]
        assert team.get_member("target:ms") is None

    def test_witness_history_preserved_on_other_members(self):
        """When a witness is removed, their attestations on targets persist."""
        config = TeamConfig(name="rm-witness", description="Witness history test")
        team = Team(config=config)
        team.set_admin("admin:wh")
        team.add_member("witness:wh", role="developer")
        team.add_member("target:wh", role="developer")

        # Witness attests target several times
        for _ in range(5):
            team.witness_member("witness:wh", "target:wh")

        # Target's witness log should reference the witness
        target = team.get_member("target:wh")
        assert "witness:wh" in target.get("_witness_log", {})
        log_count = len(target["_witness_log"]["witness:wh"])
        assert log_count == 5

        # Remove the witness
        team.remove_member("witness:wh", requester_lct="admin:wh")

        # Target's witness log should STILL reference the removed witness
        target = team.get_member("target:wh")
        assert "witness:wh" in target.get("_witness_log", {})
        assert len(target["_witness_log"]["witness:wh"]) == 5


class TestFederationRegistry:
    """Tests for cross-team federation and witness coordination."""

    def test_register_and_find_teams(self):
        """Teams can register and be discovered by domain."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:a", "Alpha", domains=["finance"], member_count=5)
        reg.register_team("team:b", "Beta", domains=["engineering"], member_count=3)
        reg.register_team("team:c", "Gamma", domains=["finance", "audit"], member_count=8)

        # Find finance teams
        finance = reg.find_teams(domain="finance")
        assert len(finance) == 2
        names = {t.name for t in finance}
        assert "Alpha" in names
        assert "Gamma" in names

    def test_witness_pool_excludes_self(self):
        """Witness pool never includes the requesting team."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:self", "Self Team", member_count=5)
        reg.register_team("team:other", "Other Team", member_count=3)

        pool = reg.find_witness_pool("team:self", count=10)
        assert all(t.team_id != "team:self" for t in pool)
        assert len(pool) == 1

    def test_witness_reputation_after_outcomes(self):
        """Witness score degrades after witnessed proposals fail."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:witness", "Witness Team")
        reg.register_team("team:propose", "Proposing Team")

        # 3 successful witnesses, 2 failed
        for i in range(5):
            reg.record_witness_event("team:witness", "team:propose",
                                     f"w:lct:{i}", f"msig:{i}")
        for i in range(3):
            reg.update_witness_outcome(f"msig:{i}", "succeeded")
        for i in range(3, 5):
            reg.update_witness_outcome(f"msig:{i}", "failed")

        team = reg.get_team("team:witness")
        assert team.witness_successes == 3
        assert team.witness_failures == 2
        # With Bayesian smoothing (5 pseudo-successes over 5 pseudo-total):
        # score = (3 + 5) / (5 + 5) = 0.8
        assert 0.75 <= team.witness_score <= 0.85

    def test_reciprocity_detection(self):
        """High reciprocity between teams triggers collusion flag."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:x", "Team X")
        reg.register_team("team:y", "Team Y")
        reg.register_team("team:z", "Team Z")

        # X and Y witness for each other 5 times each (tight reciprocity)
        for i in range(5):
            reg.record_witness_event("team:x", "team:y", f"x:{i}", f"msig:xy:{i}")
            reg.record_witness_event("team:y", "team:x", f"y:{i}", f"msig:yx:{i}")

        recip = reg.check_reciprocity("team:x", "team:y")
        assert recip["a_witnesses_b"] == 5
        assert recip["b_witnesses_a"] == 5
        assert recip["reciprocity_ratio"] == 1.0
        assert recip["is_suspicious"] is True

    def test_collusion_report(self):
        """Collusion report identifies flagged pairs."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        for t in ["team:1", "team:2", "team:3"]:
            reg.register_team(t, f"Team {t}")

        # Team 1 and 2 collude
        for i in range(5):
            reg.record_witness_event("team:1", "team:2", f"m:{i}", f"p12:{i}")
            reg.record_witness_event("team:2", "team:1", f"m:{i}", f"p21:{i}")

        report = reg.get_collusion_report()
        assert report["total_teams"] == 3
        assert len(report["flagged_pairs"]) >= 1
        assert report["health"] in ("concerning", "critical")

    def test_witness_pool_filters_colluding_teams(self):
        """find_witness_pool() excludes teams with high reciprocity."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:req", "Requester")
        reg.register_team("team:colluder", "Colluding Team")
        reg.register_team("team:clean", "Clean Team")

        # Create collusion pattern between req and colluder
        for i in range(5):
            reg.record_witness_event("team:req", "team:colluder", f"r:{i}", f"pc:{i}")
            reg.record_witness_event("team:colluder", "team:req", f"c:{i}", f"pr:{i}")

        # Clean team has no reciprocity
        pool = reg.find_witness_pool("team:req", count=5)
        pool_ids = {t.team_id for t in pool}

        # Colluder should be excluded, clean should be included
        assert "team:clean" in pool_ids
        assert "team:colluder" not in pool_ids


class TestRandomWitnessSelection:
    """Tests for reputation-weighted random witness selection."""

    def test_select_from_pool(self):
        """select_witnesses returns teams from the pool."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:req", "Requester", creator_lct="alice")
        reg.register_team("team:w1", "Witness 1", creator_lct="bob")
        reg.register_team("team:w2", "Witness 2", creator_lct="carol")
        reg.register_team("team:w3", "Witness 3", creator_lct="diana")

        selected = reg.select_witnesses("team:req", count=2, seed=42)
        assert len(selected) == 2
        assert all(t.team_id != "team:req" for t in selected)
        # All from different teams
        assert len(set(t.team_id for t in selected)) == 2

    def test_reproducible_with_seed(self):
        """Same seed produces same selection."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:r", "Requester", creator_lct="a")
        for i in range(5):
            reg.register_team(f"team:w{i}", f"W{i}", creator_lct=f"c{i}")

        sel1 = reg.select_witnesses("team:r", count=2, seed=123)
        sel2 = reg.select_witnesses("team:r", count=2, seed=123)
        assert [t.team_id for t in sel1] == [t.team_id for t in sel2]

    def test_high_rep_selected_more_often(self):
        """Higher-reputation teams are selected more frequently over many runs."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:r", "Requester", creator_lct="req")
        reg.register_team("team:high", "High Rep", creator_lct="h")
        reg.register_team("team:low", "Low Rep", creator_lct="l")
        reg.register_team("team:other", "Other Team", creator_lct="o")

        # Give high team many successes (witnessing for OTHER team, not requester)
        for i in range(20):
            reg.record_witness_event("team:high", "team:other", f"h:{i}", f"p:{i}")
            reg.update_witness_outcome(f"p:{i}", "succeeded")

        # Give low team some failures (witnessing for other team)
        for i in range(5):
            reg.record_witness_event("team:low", "team:other", f"l:{i}", f"q:{i}")
            reg.update_witness_outcome(f"q:{i}", "failed")

        # Select many times
        high_count = 0
        for seed in range(100):
            selected = reg.select_witnesses("team:r", count=1, seed=seed)
            if selected and selected[0].team_id == "team:high":
                high_count += 1

        # High-rep team (score=1.0) should be selected more than low-rep (score=0.5)
        # Pool has: high(1.0), low(0.5), other(1.0) - high should get ~40%
        low_count = sum(
            1 for seed in range(100)
            if (s := reg.select_witnesses("team:r", count=1, seed=seed))
            and s[0].team_id == "team:low"
        )
        assert high_count > low_count, (
            f"High-rep ({high_count}) should be selected more than low-rep ({low_count})"
        )

    def test_empty_pool_returns_empty(self):
        """No qualified witnesses returns empty list."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:lonely", "Lonely Team")

        selected = reg.select_witnesses("team:lonely", count=3)
        assert selected == []


class TestWitnessSelectionIntegration:
    """Tests for witness selection integration with multi-sig."""

    def _make_team(self, name, admin, members):
        """Create a team with admin and high-trust members."""
        config = TeamConfig(name=name, description=f"{name} team")
        team = Team(config=config)
        team.set_admin(admin)
        for m in members:
            team.add_member(m, role="developer")
            member = team.get_member(m)
            member["trust"] = {k: 0.85 for k in member["trust"]}
        team._update_team()
        return team

    def test_request_witnesses_selects_from_federation(self):
        """request_external_witnesses() selects from qualified teams."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        from hardbound.federation import FederationRegistry

        # Setup requesting team
        team = self._make_team("req-team", "admin:req", ["v1", "v2", "v3", "v4"])
        fed = FederationRegistry()
        fed.register_team(team.team_id, "Requester", creator_lct="alice")
        fed.register_team("team:witness1", "Witness 1", creator_lct="bob")
        fed.register_team("team:witness2", "Witness 2", creator_lct="carol")

        msig = MultiSigManager(team, federation=fed)

        proposal = msig.create_proposal(
            proposer_lct="admin:req",
            action=CriticalAction.ADMIN_TRANSFER,
            action_data={"new_admin": "new_admin:lct"},
            description="Transfer admin",
        )

        # Get votes
        for v in ["v1", "v2", "v3"]:
            msig.vote(proposal.proposal_id, v, approve=True)

        # Request witnesses
        selected = msig.request_external_witnesses(proposal.proposal_id, seed=42)

        assert len(selected) >= 1
        assert all("team_id" in s for s in selected)
        assert all(s["team_id"] != team.team_id for s in selected)

    def test_request_witnesses_fails_without_federation(self):
        """request_external_witnesses() fails without federation."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        import pytest

        team = self._make_team("no-fed", "admin:nf", ["v1", "v2", "v3", "v4"])
        msig = MultiSigManager(team, federation=None)

        proposal = msig.create_proposal(
            proposer_lct="admin:nf",
            action=CriticalAction.ADMIN_TRANSFER,
            action_data={},
            description="No federation",
        )

        with pytest.raises(ValueError, match="No federation"):
            msig.request_external_witnesses(proposal.proposal_id)

    def test_request_witnesses_returns_empty_when_satisfied(self):
        """Returns empty list when witness requirement already met."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        from hardbound.federation import FederationRegistry

        team = self._make_team("sat-team", "admin:sat", ["v1", "v2", "v3", "v4"])
        fed = FederationRegistry()
        fed.register_team(team.team_id, "Sat Team", creator_lct="sat")
        fed.register_team("team:ext", "External", creator_lct="ext")

        msig = MultiSigManager(team, federation=fed)

        proposal = msig.create_proposal(
            proposer_lct="admin:sat",
            action=CriticalAction.ADMIN_TRANSFER,
            action_data={},
            description="Already witnessed",
        )

        # Vote
        for v in ["v1", "v2", "v3"]:
            msig.vote(proposal.proposal_id, v, approve=True)

        # Manually add an external witness
        msig.add_external_witness(
            proposal.proposal_id,
            witness_lct="ext:person",
            witness_team_id="team:ext",
            witness_trust_score=0.9,
        )

        # Request should return empty (already have 1 witness, need 1)
        selected = msig.request_external_witnesses(proposal.proposal_id)
        assert selected == []


class TestFederationHealthDashboard:
    """Tests for the aggregate federation health dashboard."""

    def test_healthy_federation(self):
        """Clean federation reports healthy status."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:alpha", "Alpha Corp", creator_lct="alice")
        reg.register_team("team:beta", "Beta Corp", creator_lct="bob")
        reg.register_team("team:gamma", "Gamma Corp", creator_lct="carol")

        report = reg.get_federation_health()
        assert report["overall_health"] == "healthy"
        assert report["health_score"] >= 80
        assert len(report["issues"]) == 0
        assert "signature" in report

    def test_collusion_degrades_health(self):
        """Colluding teams degrade federation health."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:x", "Team X", creator_lct="creator:x")
        reg.register_team("team:y", "Team Y", creator_lct="creator:y")

        # Create reciprocal witnessing (collusion signal)
        for i in range(5):
            reg.record_witness_event("team:x", "team:y", f"x:{i}", f"mxy:{i}")
            reg.record_witness_event("team:y", "team:x", f"y:{i}", f"myx:{i}")

        report = reg.get_federation_health()
        assert report["health_score"] < 100
        assert len(report["issues"]) > 0
        assert report["subsystems"]["collusion"]["flagged_pairs"] > 0

    def test_lineage_issues_flagged(self):
        """Same-creator multi-teams are flagged in health report."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:m1", "Shell 1", creator_lct="mallory")
        reg.register_team("team:m2", "Shell 2", creator_lct="mallory")
        reg.register_team("team:legit", "Legit", creator_lct="alice")

        report = reg.get_federation_health()
        assert report["subsystems"]["lineage"]["multi_team_creators"] == 1
        assert report["health_score"] < 100

    def test_overlap_analysis_included(self):
        """Member overlap is included when data is provided."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:a", "Team A")
        reg.register_team("team:b", "Team B")

        report = reg.get_federation_health(
            team_member_maps={
                "team:a": ["alice", "bob", "shared"],
                "team:b": ["carol", "diana", "shared"],
            }
        )
        assert report["subsystems"]["member_overlap"]["health"] != "not_analyzed"
        assert report["subsystems"]["member_overlap"]["multi_team_count"] == 1

    def test_critical_score_on_multiple_issues(self):
        """Multiple critical issues drive score below 40."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        # Same creator teams that witness for each other (lineage + collusion)
        reg.register_team("team:s1", "Shell 1", creator_lct="mallory")
        reg.register_team("team:s2", "Shell 2", creator_lct="mallory")

        for i in range(5):
            reg.record_witness_event("team:s1", "team:s2", f"s1:{i}", f"ms:{i}")
            reg.record_witness_event("team:s2", "team:s1", f"s2:{i}", f"mr:{i}")

        report = reg.get_federation_health(
            team_member_maps={
                "team:s1": ["alice", "bob", "carol"],
                "team:s2": ["alice", "bob", "carol"],  # Full overlap!
            }
        )
        # Multiple issues compound: collusion + lineage + overlap
        assert report["health_score"] < 60
        assert len(report["issues"]) >= 2


class TestPatternSigning:
    """Tests for cryptographic pattern signing on federation analysis."""

    def test_sign_and_verify_collusion_report(self):
        """Signed collusion report passes verification."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:sig_a", "Team A")
        reg.register_team("team:sig_b", "Team B")

        report = reg.get_collusion_report()
        signed = reg.sign_pattern("collusion_report", report, signer_lct="auditor:1")

        assert signed["pattern_type"] == "collusion_report"
        assert signed["signature"] != ""
        assert signed["algorithm"] == "hmac-sha256"

        # Verification should pass
        assert reg.verify_pattern_signature(signed) is True

    def test_tampered_data_fails_verification(self):
        """Modifying signed data causes verification to fail."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:tam_a", "Tamper Test A")

        report = reg.get_collusion_report()
        signed = reg.sign_pattern("collusion_report", report, signer_lct="auditor:2")

        # Tamper with the data
        signed["data"]["health"] = "healthy_TAMPERED"

        # Verification should fail
        assert reg.verify_pattern_signature(signed) is False

    def test_sign_lineage_report(self):
        """Lineage reports can be signed and verified."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:lin_a", "Lineage A", creator_lct="creator:x")
        reg.register_team("team:lin_b", "Lineage B", creator_lct="creator:x")

        lineage = reg.get_lineage_report()
        signed = reg.sign_pattern("lineage_report", lineage, signer_lct="compliance:1")

        assert reg.verify_pattern_signature(signed) is True
        assert signed["data"]["health"] == "warning"  # Multi-creator but no witnessing

    def test_different_signers_produce_different_signatures(self):
        """Same data signed by different LCTs produces different signatures."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        data = {"test": "value", "count": 42}

        sig_a = reg.sign_pattern("test", data, signer_lct="signer:alpha")
        sig_b = reg.sign_pattern("test", data, signer_lct="signer:beta")

        assert sig_a["signature"] != sig_b["signature"]


class TestRejoinCooldown:
    """Tests for post-rejoin witnessing cooldown."""

    def test_fresh_member_has_no_cooldown(self):
        """New members added for the first time have no cooldown."""
        config = TeamConfig(name="cooldown-fresh", description="Fresh member")
        team = Team(config=config)
        team.set_admin("admin:cd")
        team.add_member("fresh:1", role="developer")

        assert not team.is_in_cooldown("fresh:1")
        member = team.get_member("fresh:1")
        assert member["_cooldown_until"] == ""

    def test_readded_member_has_cooldown(self):
        """Members who were removed and re-added get a cooldown period."""
        config = TeamConfig(name="cooldown-readd", description="Re-add test")
        team = Team(config=config)
        team.set_admin("admin:ra")
        team.add_member("target:ra", role="developer")
        team.add_member("witness:ra", role="developer")

        # Remove target
        team.remove_member("target:ra", requester_lct="admin:ra", reason="test")

        # Re-add - should have cooldown
        team.add_member("target:ra", role="developer")
        assert team.is_in_cooldown("target:ra")

        member = team.get_member("target:ra")
        assert member["_cooldown_until"] != ""

    def test_cooldown_blocks_witnessing(self):
        """Members in cooldown cannot witness."""
        config = TeamConfig(name="cooldown-block", description="Block witness test")
        team = Team(config=config)
        team.set_admin("admin:cb")
        team.add_member("cycled:cb", role="developer")
        team.add_member("target:cb", role="developer")

        # Remove and re-add the cycled member
        team.remove_member("cycled:cb", requester_lct="admin:cb", reason="cycling test")
        team.add_member("cycled:cb", role="developer")

        # Attempt to witness should fail
        with pytest.raises(PermissionError, match="post-rejoin cooldown"):
            team.witness_member("cycled:cb", "target:cb")

    def test_non_cooldown_member_can_still_witness(self):
        """Normal members are unaffected by another member's cooldown."""
        config = TeamConfig(name="cooldown-other", description="Other witness test")
        team = Team(config=config)
        team.set_admin("admin:co")
        team.add_member("normal:co", role="developer")
        team.add_member("cycled:co", role="developer")
        team.add_member("target:co", role="developer")

        # Remove and re-add cycled member
        team.remove_member("cycled:co", requester_lct="admin:co")
        team.add_member("cycled:co", role="developer")

        # Normal member can still witness
        trust = team.witness_member("normal:co", "target:co")
        assert trust["witnesses"] > 0.5


class TestMemberOverlap:
    """Tests for cross-team member overlap analysis."""

    def test_no_overlap_is_healthy(self):
        """Teams with disjoint members show healthy status."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        result = reg.analyze_member_overlap({
            "team:a": ["alice", "bob", "charlie"],
            "team:b": ["diana", "eve", "frank"],
        })
        assert result["health"] == "healthy"
        assert result["multi_team_count"] == 0
        assert len(result["pair_analysis"]) == 0

    def test_low_overlap_detected(self):
        """One shared member across teams is detected but low risk."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        result = reg.analyze_member_overlap({
            "team:a": ["alice", "bob", "shared_member", "charlie", "diana"],
            "team:b": ["eve", "frank", "shared_member", "george", "helen"],
        })
        assert result["multi_team_count"] == 1
        assert "shared_member" in result["multi_team_members"]
        assert len(result["pair_analysis"]) == 1
        assert result["pair_analysis"][0]["risk"] == "low"
        assert result["health"] == "info"

    def test_high_overlap_flagged(self):
        """High member overlap triggers warning."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        # 3 out of 5 shared = 60% overlap
        result = reg.analyze_member_overlap({
            "team:x": ["a", "b", "c", "d", "e"],
            "team:y": ["a", "b", "c", "f", "g"],
        })
        assert len(result["pair_analysis"]) == 1
        pair = result["pair_analysis"][0]
        assert pair["shared_count"] == 3
        assert pair["risk"] == "high"
        assert result["health"] == "warning"

    def test_full_overlap_critical(self):
        """Fully overlapping teams are critical risk."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        # Same members = shell teams
        result = reg.analyze_member_overlap({
            "team:shell_a": ["x", "y", "z"],
            "team:shell_b": ["x", "y", "z"],
        })
        pair = result["pair_analysis"][0]
        assert pair["overlap_ratio"] == 1.0
        assert pair["risk"] == "critical"
        assert result["health"] == "critical"

    def test_multi_team_member_tracking(self):
        """Members appearing in 3+ teams are tracked."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        result = reg.analyze_member_overlap({
            "team:1": ["alice", "bob", "carol"],
            "team:2": ["alice", "diana", "eve"],
            "team:3": ["alice", "frank", "grace"],
        })
        assert "alice" in result["multi_team_members"]
        assert len(result["multi_team_members"]["alice"]) == 3


class TestActivityQualityIntegration:
    """Tests that ActivityWindow is wired into Team trust operations."""

    def test_activity_window_populated_on_trust_update(self):
        """update_member_trust() records to ActivityWindow."""
        config = TeamConfig(name="aq-update", description="Activity window test")
        team = Team(config=config)
        team.set_admin("admin:aq")
        team.add_member("worker:aq", role="developer")

        # Perform trust updates
        team.update_member_trust("worker:aq", "success", 0.5)
        team.update_member_trust("worker:aq", "failure", 0.3)
        team.update_member_trust("worker:aq", "success", 0.2)

        # Check that activity window was populated
        window = team._activity_windows.get("worker:aq")
        assert window is not None
        assert len(window.actions) == 3
        action_types = [a["tx_type"] for a in window.actions]
        assert "trust_update_success" in action_types
        assert "trust_update_failure" in action_types

    def test_activity_window_populated_on_witness(self):
        """witness_member() records to both witness and target windows."""
        config = TeamConfig(name="aq-witness", description="Witness activity test")
        team = Team(config=config)
        team.set_admin("admin:aqw")
        team.add_member("witness:aqw", role="developer")
        team.add_member("target:aqw", role="developer")

        team.witness_member("witness:aqw", "target:aqw")

        # Both should have activity recorded
        w_window = team._activity_windows.get("witness:aqw")
        t_window = team._activity_windows.get("target:aqw")
        assert w_window is not None
        assert t_window is not None
        assert any(a["tx_type"] == "witness_given" for a in w_window.actions)
        assert any(a["tx_type"] == "witness_received" for a in t_window.actions)

    def test_quality_adjusted_actions_returns_int(self):
        """_quality_adjusted_actions returns a non-negative integer."""
        config = TeamConfig(name="aq-int", description="Adjusted action test")
        team = Team(config=config)
        team.set_admin("admin:qi")
        team.add_member("member:qi", role="developer")

        # Without any activity recorded, falls back to raw count
        result = team._quality_adjusted_actions("member:qi", 10)
        assert isinstance(result, int)
        assert result == 10  # No window yet = raw count

        # After some activity, uses quality adjustment
        for _ in range(5):
            team.update_member_trust("member:qi", "success", 0.1)

        result = team._quality_adjusted_actions("member:qi", 10)
        assert isinstance(result, int)
        assert result >= 0


class TestFederatedWitnessing:
    """Tests for federation-integrated multi-sig witnessing."""

    def _make_team(self, name, admin, members):
        config = TeamConfig(name=name, description=f"{name} test")
        team = Team(config=config)
        team.set_admin(admin)
        for m in members:
            team.add_member(m, role="developer")
            member = team.get_member(m)
            member["trust"] = {
                "reliability": 0.85, "competence": 0.85, "alignment": 0.85,
                "consistency": 0.85, "witnesses": 0.85, "lineage": 0.85,
            }
        team._update_team()
        return team

    def test_federation_validates_witness_team(self):
        """Unregistered teams are rejected when federation is active."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        from hardbound.federation import FederationRegistry
        import pytest

        team = self._make_team("fed-val", "admin:fv",
                               ["v:1", "v:2", "v:3", "v:4"])
        fed = FederationRegistry()
        fed.register_team(team.team_id, "Test Team")
        # Do NOT register "unregistered:team"

        msig = MultiSigManager(team, federation=fed)
        proposal = msig.create_proposal(
            proposer_lct="admin:fv",
            action=CriticalAction.ADMIN_TRANSFER,
            action_data={"new_admin_lct": "v:1"},
        )
        for v in ["v:2", "v:3", "v:4"]:
            msig.vote(proposal.proposal_id, v, approve=True)

        with pytest.raises(ValueError, match="not registered in the federation"):
            msig.add_external_witness(
                proposal.proposal_id,
                witness_lct="ext:unreg:1",
                witness_team_id="unregistered:team",
                witness_trust_score=0.9,
            )

    def test_federation_records_witness_event(self):
        """When federation is active, witness events are recorded."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        from hardbound.federation import FederationRegistry

        team = self._make_team("fed-rec", "admin:fr",
                               ["v:a", "v:b", "v:c", "v:d"])
        fed = FederationRegistry()
        fed.register_team(team.team_id, "Proposal Team")
        fed.register_team("external:team", "External Team")

        msig = MultiSigManager(team, federation=fed)
        proposal = msig.create_proposal(
            proposer_lct="admin:fr",
            action=CriticalAction.ADMIN_TRANSFER,
            action_data={"new_admin_lct": "v:a"},
        )
        for v in ["v:b", "v:c", "v:d"]:
            msig.vote(proposal.proposal_id, v, approve=True)

        msig.add_external_witness(
            proposal.proposal_id,
            witness_lct="ext:member:1",
            witness_team_id="external:team",
            witness_trust_score=0.9,
        )

        # Federation should have recorded the witness event
        ext_team = fed.get_team("external:team")
        assert ext_team.witness_count == 1

    def test_federation_updates_reputation_on_execute(self):
        """Successful execution improves witness reputation."""
        from hardbound.multisig import MultiSigManager, CriticalAction
        from hardbound.federation import FederationRegistry

        team = self._make_team("fed-rep", "admin:frep",
                               ["v:x", "v:y", "v:z", "v:w"])
        fed = FederationRegistry()
        fed.register_team(team.team_id, "Proposal Team")
        fed.register_team("witness:team", "Witness Team")

        msig = MultiSigManager(team, federation=fed)
        proposal = msig.create_proposal(
            proposer_lct="admin:frep",
            action=CriticalAction.ADMIN_TRANSFER,
            action_data={"new_admin_lct": "v:x"},
        )
        for v in ["v:y", "v:z", "v:w"]:
            msig.vote(proposal.proposal_id, v, approve=True)

        msig.add_external_witness(
            proposal.proposal_id,
            witness_lct="wit:member:1",
            witness_team_id="witness:team",
            witness_trust_score=0.9,
        )

        # Bypass voting period
        proposal = msig.get_proposal(proposal.proposal_id)
        proposal.min_voting_period_hours = 0
        msig._save_proposal(proposal)

        # Execute - should update federation
        msig.execute_proposal(proposal.proposal_id, "admin:frep")

        # Witness team should have success recorded
        wit_team = fed.get_team("witness:team")
        assert wit_team.witness_successes == 1
        assert wit_team.witness_score > 0.9  # Bayesian: (1+5)/(1+5) = 1.0


class TestIsAdmin:
    """Tests for is_admin() bool correctness (fixes truthy-dict bug)."""

    def test_is_admin_returns_bool(self):
        """is_admin() returns True for admin, False for non-admin."""
        config = TeamConfig(name="admin-bool", description="Admin bool test")
        team = Team(config=config)
        team.set_admin("admin:bool")
        team.add_member("member:bool", role="developer")

        assert team.is_admin("admin:bool") is True
        assert team.is_admin("member:bool") is False
        assert team.is_admin("unknown:lct") is False

    def test_verify_admin_dict_is_truthy_for_non_admin(self):
        """Demonstrates the bug: verify_admin() dict is truthy even for non-admins."""
        config = TeamConfig(name="admin-bug", description="Bug demo")
        team = Team(config=config)
        team.set_admin("admin:bug")

        # verify_admin returns a dict which is always truthy
        result = team.verify_admin("not_the_admin")
        assert isinstance(result, dict)
        # The dict IS truthy even though verified=False
        assert bool(result) is True
        # But is_admin correctly returns False
        assert team.is_admin("not_the_admin") is False


class TestFederatedSybilDetection:
    """Tests for cross-team Sybil detection via FederatedSybilDetector."""

    def test_cross_team_trust_mirroring_detected(self):
        """Members in different teams with identical trust are flagged."""
        from hardbound.sybil_detection import FederatedSybilDetector, SybilRisk

        detector = FederatedSybilDetector()

        # Sybil has same trust profile in both teams
        sybil_trust = {
            "reliability": 0.55, "competence": 0.55, "alignment": 0.55,
            "consistency": 0.55, "witnesses": 0.55, "lineage": 0.55,
        }
        teams_data = {
            "team_alpha": {
                "sybil_in_alpha": dict(sybil_trust),
                "legit_alpha": {
                    "reliability": 0.80, "competence": 0.60, "alignment": 0.70,
                    "consistency": 0.65, "witnesses": 0.75, "lineage": 0.50,
                },
            },
            "team_beta": {
                "sybil_in_beta": dict(sybil_trust),
                "legit_beta": {
                    "reliability": 0.45, "competence": 0.90, "alignment": 0.50,
                    "consistency": 0.70, "witnesses": 0.40, "lineage": 0.85,
                },
            },
        }

        report = detector.analyze_federation(teams_data)
        assert report.teams_analyzed == 2
        assert report.total_members == 4
        assert len(report.cross_team_clusters) > 0

        # Check the flagged pair spans teams
        flagged = report.cross_team_clusters[0]
        assert len(flagged.team_ids) == 2
        assert "sybil_in_alpha" in flagged.members or "sybil_in_beta" in flagged.members

    def test_cross_team_timing_detected(self):
        """Members in different teams acting simultaneously are flagged."""
        from hardbound.sybil_detection import FederatedSybilDetector

        detector = FederatedSybilDetector()
        now = datetime.now(timezone.utc)

        teams_data = {
            "team_x": {
                "bot_x": {"reliability": 0.5, "competence": 0.5, "alignment": 0.5,
                           "consistency": 0.5, "witnesses": 0.5, "lineage": 0.5},
            },
            "team_y": {
                "bot_y": {"reliability": 0.6, "competence": 0.4, "alignment": 0.7,
                           "consistency": 0.3, "witnesses": 0.8, "lineage": 0.5},
            },
        }

        # Both bots act within 2 seconds of each other consistently
        action_timestamps = {
            "team_x": {
                "bot_x": [
                    (now - timedelta(hours=i, seconds=0)).isoformat()
                    for i in range(10)
                ],
            },
            "team_y": {
                "bot_y": [
                    (now - timedelta(hours=i, seconds=2)).isoformat()
                    for i in range(10)
                ],
            },
        }

        report = detector.analyze_federation(teams_data, action_timestamps=action_timestamps)
        timing_clusters = [
            c for c in report.cross_team_clusters
            if c.timing_correlation > 0
        ]
        assert len(timing_clusters) > 0
        assert any("timing" in s.lower() for c in timing_clusters for s in c.signals)

    def test_no_false_positives_across_teams(self):
        """Distinct members in different teams should not trigger."""
        from hardbound.sybil_detection import FederatedSybilDetector

        detector = FederatedSybilDetector()

        # Very different trust profiles
        teams_data = {
            "team_finance": {
                "alice": {"reliability": 0.90, "competence": 0.30, "alignment": 0.80,
                          "consistency": 0.50, "witnesses": 0.70, "lineage": 0.60},
                "bob": {"reliability": 0.40, "competence": 0.85, "alignment": 0.55,
                        "consistency": 0.75, "witnesses": 0.35, "lineage": 0.90},
            },
            "team_engineering": {
                "charlie": {"reliability": 0.60, "competence": 0.70, "alignment": 0.40,
                            "consistency": 0.80, "witnesses": 0.50, "lineage": 0.30},
                "diana": {"reliability": 0.75, "competence": 0.55, "alignment": 0.65,
                          "consistency": 0.45, "witnesses": 0.85, "lineage": 0.70},
            },
        }

        report = detector.analyze_federation(teams_data)
        assert len(report.cross_team_clusters) == 0
        assert report.overall_risk.value == "none"

    def test_registration_timing_detection(self):
        """Accounts created at nearly the same time across teams are flagged."""
        from hardbound.sybil_detection import FederatedSybilDetector

        detector = FederatedSybilDetector()
        now = datetime.now(timezone.utc)

        teams_data = {
            "team_a": {
                "batch_1": {"reliability": 0.5, "competence": 0.6, "alignment": 0.4,
                            "consistency": 0.5, "witnesses": 0.5, "lineage": 0.5},
            },
            "team_b": {
                "batch_2": {"reliability": 0.7, "competence": 0.3, "alignment": 0.8,
                            "consistency": 0.6, "witnesses": 0.4, "lineage": 0.5},
            },
        }

        # Both registered within 10 seconds
        registration_times = {
            "batch_1": now.isoformat(),
            "batch_2": (now + timedelta(seconds=10)).isoformat(),
        }

        report = detector.analyze_federation(
            teams_data, registration_times=registration_times
        )
        reg_clusters = [
            c for c in report.cross_team_clusters
            if any("Registration" in s for s in c.signals)
        ]
        assert len(reg_clusters) > 0

    def test_multi_signal_amplification(self):
        """Multiple cross-team signals amplify confidence."""
        from hardbound.sybil_detection import FederatedSybilDetector

        detector = FederatedSybilDetector()
        now = datetime.now(timezone.utc)

        # Same trust AND same timing = higher confidence
        sybil_trust = {
            "reliability": 0.55, "competence": 0.55, "alignment": 0.55,
            "consistency": 0.55, "witnesses": 0.55, "lineage": 0.55,
        }
        teams_data = {
            "team_1": {"sybil_a": dict(sybil_trust)},
            "team_2": {"sybil_b": dict(sybil_trust)},
        }
        action_timestamps = {
            "team_1": {"sybil_a": [
                (now - timedelta(hours=i)).isoformat() for i in range(8)
            ]},
            "team_2": {"sybil_b": [
                (now - timedelta(hours=i, seconds=1)).isoformat() for i in range(8)
            ]},
        }
        registration_times = {
            "sybil_a": now.isoformat(),
            "sybil_b": (now + timedelta(seconds=5)).isoformat(),
        }

        report = detector.analyze_federation(
            teams_data,
            action_timestamps=action_timestamps,
            registration_times=registration_times,
        )

        # Should have at least one high-confidence cluster
        assert len(report.cross_team_clusters) > 0
        top = max(report.cross_team_clusters, key=lambda c: c.confidence)
        # Multiple signals should push confidence higher than any single signal
        assert top.confidence > 0.4
        assert len(top.signals) >= 2


class TestTeamCreationLineage:
    """Tests for team creation lineage tracking and collusion detection."""

    def test_creator_lct_stored_on_registration(self):
        """Creator LCT is persisted and retrievable."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        team = reg.register_team(
            "team:lineage_test", "Lineage Test",
            creator_lct="creator:alice",
            member_count=3,
        )
        assert team.creator_lct == "creator:alice"

        # Retrieve and verify
        retrieved = reg.get_team("team:lineage_test")
        assert retrieved.creator_lct == "creator:alice"

    def test_find_teams_by_creator(self):
        """Can find all teams created by the same entity."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:a1", "Alpha 1", creator_lct="creator:mallory")
        reg.register_team("team:a2", "Alpha 2", creator_lct="creator:mallory")
        reg.register_team("team:b1", "Beta 1", creator_lct="creator:bob")

        mallory_teams = reg.find_teams_by_creator("creator:mallory")
        assert len(mallory_teams) == 2
        assert {t.team_id for t in mallory_teams} == {"team:a1", "team:a2"}

        bob_teams = reg.find_teams_by_creator("creator:bob")
        assert len(bob_teams) == 1

    def test_witness_pool_excludes_same_creator(self):
        """Teams created by the same entity cannot witness for each other."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:sybil_a", "Sybil A", creator_lct="creator:mallory")
        reg.register_team("team:sybil_b", "Sybil B", creator_lct="creator:mallory")
        reg.register_team("team:legit", "Legit Team", creator_lct="creator:alice")

        # Sybil A looks for witnesses - should NOT get Sybil B
        pool = reg.find_witness_pool("team:sybil_a", count=5)
        pool_ids = {t.team_id for t in pool}
        assert "team:sybil_b" not in pool_ids
        assert "team:legit" in pool_ids

    def test_lineage_report_flags_multi_team_creators(self):
        """Lineage report identifies entities creating multiple teams."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:m1", "Mallory 1", creator_lct="creator:mallory")
        reg.register_team("team:m2", "Mallory 2", creator_lct="creator:mallory")
        reg.register_team("team:m3", "Mallory 3", creator_lct="creator:mallory")
        reg.register_team("team:honest", "Honest", creator_lct="creator:alice")

        report = reg.get_lineage_report()
        assert len(report["multi_team_creators"]) == 1
        assert report["multi_team_creators"][0]["creator_lct"] == "creator:mallory"
        assert report["multi_team_creators"][0]["team_count"] == 3
        assert report["health"] == "warning"  # Multi-creator but no cross-witnessing

    def test_lineage_report_critical_on_cross_witnessing(self):
        """Lineage report goes CRITICAL when same-creator teams witness for each other."""
        from hardbound.federation import FederationRegistry

        reg = FederationRegistry()
        reg.register_team("team:s1", "Sybil 1", creator_lct="creator:mallory")
        reg.register_team("team:s2", "Sybil 2", creator_lct="creator:mallory")

        # Simulate cross-witnessing between same-creator teams
        reg.record_witness_event("team:s1", "team:s2", "s1:member", "prop:1")
        reg.record_witness_event("team:s2", "team:s1", "s2:member", "prop:2")

        report = reg.get_lineage_report()
        assert report["health"] == "critical"
        assert len(report["same_creator_witness_pairs"]) > 0
        pair = report["same_creator_witness_pairs"][0]
        assert pair["creator_lct"] == "creator:mallory"
        assert pair["witness_events"] > 0


class TestATPEconomics:
    """Tests for ATP replenishment, rewards, and economic sustainability."""

    def test_admin_can_replenish_atp(self):
        """Admin can top up a member's ATP budget."""
        config = TeamConfig(name="atp-econ", description="ATP economics test")
        team = Team(config=config)
        team.set_admin("admin:atp")
        team.add_member("worker:1", role="developer", atp_budget=10)

        # Consume some ATP
        team.consume_member_atp("worker:1", 8)
        assert team.get_member_atp("worker:1") == 2

        # Admin replenishes
        remaining = team.replenish_member_atp("worker:1", 20, requester_lct="admin:atp")
        assert remaining == 22  # 2 + 20

    def test_non_admin_cannot_replenish(self):
        """Non-admin members cannot replenish ATP."""
        config = TeamConfig(name="atp-perm", description="ATP permissions")
        team = Team(config=config)
        team.set_admin("admin:boss")
        team.add_member("worker:1", role="developer")
        team.add_member("worker:2", role="developer")

        with pytest.raises(PermissionError, match="admin authority"):
            team.replenish_member_atp("worker:1", 50, requester_lct="worker:2")

    def test_reward_on_success(self):
        """Successful outcomes generate ATP rewards."""
        config = TeamConfig(name="atp-reward", description="Reward test")
        team = Team(config=config)
        team.set_admin("admin:r")
        team.add_member("dev:1", role="developer", atp_budget=100)

        initial = team.get_member_atp("dev:1")

        # Reward for successful outcome (base_reward=10)
        reward = team.reward_member_atp("dev:1", "success", base_reward=10)
        assert reward == 10
        assert team.get_member_atp("dev:1") == initial + 10

        # Partial reward
        reward_partial = team.reward_member_atp("dev:1", "partial", base_reward=10)
        assert reward_partial == 5  # 50% for partial

        # No reward for failure
        reward_fail = team.reward_member_atp("dev:1", "failure", base_reward=10)
        assert reward_fail == 0

    def test_r6_execute_rewards_atp(self):
        """R6 execute_request() rewards ATP on successful completion."""
        from hardbound.r6 import R6Workflow
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-reward", description="R6 reward test")
        team = Team(config=config)
        team.set_admin("admin:r6")
        team.add_member("dev:r6", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="code_review",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=10,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy)
        request = wf.create_request(
            requester_lct="dev:r6",
            action_type="code_review",
            description="Review PR #42",
        )
        r6_id = request.r6_id

        wf.approve_request(r6_id, "admin:r6")

        # Execute successfully
        before_atp = team.get_member_atp("dev:r6")
        response = wf.execute_request(r6_id, success=True)
        after_atp = team.get_member_atp("dev:r6")

        # ATP consumed (10) but rewarded back (10 // 2 = 5)
        # Net cost = 10 - 5 = 5
        assert after_atp == before_atp - 10 + 5

    def test_atp_exhaustion_blocks_actions(self):
        """Members with 0 ATP cannot perform actions."""
        config = TeamConfig(name="atp-exhaust", description="Exhaustion test")
        team = Team(config=config)
        team.set_admin("admin:e")
        team.add_member("worker:e", role="developer", atp_budget=5)

        team.consume_member_atp("worker:e", 5)
        assert team.get_member_atp("worker:e") == 0

        with pytest.raises(ValueError, match="Insufficient ATP"):
            team.consume_member_atp("worker:e", 1)


class TestATPBulkReplenish:
    """Tests for periodic bulk ATP replenishment."""

    def test_replenish_all_gives_each_member_atp(self):
        """replenish_all_budgets() adds ATP to all members."""
        config = TeamConfig(
            name="bulk-replenish", description="Bulk replenish",
            default_member_budget=100
        )
        team = Team(config=config)
        team.set_admin("admin:br")
        team.add_member("dev:br1", role="developer", atp_budget=50)
        team.add_member("dev:br2", role="developer", atp_budget=30)

        # 10% replenishment = 10 ATP each
        result = team.replenish_all_budgets(rate=0.1)

        assert result["dev:br1"] == 10
        assert result["dev:br2"] == 10
        assert team.get_member("dev:br1")["atp_budget"] == 60
        assert team.get_member("dev:br2")["atp_budget"] == 40

    def test_replenish_respects_cap(self):
        """replenish_all_budgets() respects the cap parameter."""
        config = TeamConfig(
            name="capped-replenish", description="Capped",
            default_member_budget=100
        )
        team = Team(config=config)
        team.set_admin("admin:cr")
        team.add_member("dev:cr1", role="developer", atp_budget=95)
        team.add_member("dev:cr2", role="developer", atp_budget=80)

        # Cap at 100, rate 0.1 = 10 ATP each, but cr1 only gets 5
        result = team.replenish_all_budgets(rate=0.1, cap=100)

        assert result["dev:cr1"] == 5  # 95 + 5 = 100 (capped)
        assert result["dev:cr2"] == 10  # 80 + 10 = 90 (under cap)
        assert team.get_member("dev:cr1")["atp_budget"] == 100
        assert team.get_member("dev:cr2")["atp_budget"] == 90

    def test_replenish_uses_min_atp(self):
        """Minimum ATP is guaranteed even if rate is low."""
        config = TeamConfig(
            name="min-replenish", description="Min",
            default_member_budget=10  # Very small budget
        )
        team = Team(config=config)
        team.set_admin("admin:mr")
        team.add_member("dev:mr", role="developer", atp_budget=5)

        # 1% of 10 = 0.1 → rounds to 0, but min_atp=5 guarantees 5
        result = team.replenish_all_budgets(rate=0.01, min_atp=5)

        assert result["dev:mr"] == 5
        assert team.get_member("dev:mr")["atp_budget"] == 10

    def test_replenish_skips_already_at_cap(self):
        """Members at or above cap get 0 replenishment."""
        config = TeamConfig(
            name="skip-replenish", description="Skip",
            default_member_budget=100
        )
        team = Team(config=config)
        team.set_admin("admin:sr")
        team.add_member("dev:sr", role="developer", atp_budget=100)

        result = team.replenish_all_budgets(rate=0.1, cap=100)

        assert result["dev:sr"] == 0
        assert team.get_member("dev:sr")["atp_budget"] == 100


class TestR6Cancellation:
    """Tests for R6 request cancellation."""

    def test_requester_can_cancel_own_request(self):
        """The original requester can cancel their pending request."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-cancel", description="Cancel test")
        team = Team(config=config)
        team.set_admin("admin:cancel")
        team.add_member("dev:cancel", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="code_review",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=5,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy)
        request = wf.create_request(
            requester_lct="dev:cancel",
            action_type="code_review",
            description="Review PR #99",
        )
        r6_id = request.r6_id

        response = wf.cancel_request(r6_id, "dev:cancel", reason="Changed my mind")
        assert response.status == R6Status.CANCELLED
        assert wf.get_request(r6_id) is None

    def test_admin_can_cancel_any_request(self):
        """Admin can cancel any member's request."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-admin-cancel", description="Admin cancel")
        team = Team(config=config)
        team.set_admin("admin:ac")
        team.add_member("dev:ac", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="deploy",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=10,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy)
        request = wf.create_request(
            requester_lct="dev:ac",
            action_type="deploy",
            description="Deploy to prod",
        )

        response = wf.cancel_request(request.r6_id, "admin:ac", reason="Deployment freeze")
        assert response.status == R6Status.CANCELLED

    def test_other_member_cannot_cancel(self):
        """A different member cannot cancel someone else's request."""
        from hardbound.r6 import R6Workflow
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-no-cancel", description="No cancel")
        team = Team(config=config)
        team.set_admin("admin:nc")
        team.add_member("dev:nc1", role="developer", atp_budget=100)
        team.add_member("dev:nc2", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="test_run",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=3,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy)
        request = wf.create_request(
            requester_lct="dev:nc1",
            action_type="test_run",
            description="Run tests",
        )

        with pytest.raises(PermissionError, match="original requester or admin"):
            wf.cancel_request(request.r6_id, "dev:nc2")

    def test_cannot_cancel_executed_request(self):
        """Cannot cancel a request that has already been executed."""
        from hardbound.r6 import R6Workflow
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-no-cancel-exec", description="No cancel executed")
        team = Team(config=config)
        team.set_admin("admin:nce")
        team.add_member("dev:nce", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="test_run",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=3,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy)
        request = wf.create_request(
            requester_lct="dev:nce",
            action_type="test_run",
            description="Run tests",
        )
        wf.approve_request(request.r6_id, "admin:nce")
        wf.execute_request(request.r6_id, success=True)

        with pytest.raises(ValueError, match="not found"):
            wf.cancel_request(request.r6_id, "dev:nce")

    def test_cancel_removes_from_persistence(self):
        """Cancelled request is removed from SQLite persistence."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-cancel-persist", description="Cancel persistence")
        team = Team(config=config)
        team.set_admin("admin:cp")
        team.add_member("dev:cp", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="review",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=2,
            approval=ApprovalType.ADMIN,
        ))

        wf1 = R6Workflow(team, policy)
        request = wf1.create_request(
            requester_lct="dev:cp",
            action_type="review",
            description="Review code",
        )
        r6_id = request.r6_id

        wf1.cancel_request(r6_id, "dev:cp")

        # New workflow instance should NOT see cancelled request
        wf2 = R6Workflow(team, policy)
        assert wf2.get_request(r6_id) is None


class TestR6MultiSigDelegation:
    """Tests for R6 requests delegating to multi-sig for critical actions."""

    def _make_team(self, name):
        """Create a team with admin and high-trust members."""
        config = TeamConfig(name=name, description=f"{name} test")
        team = Team(config=config)
        team.set_admin(f"admin:{name}")
        for i in range(4):
            lct = f"dev:{name}:{i}"
            team.add_member(lct, role="developer", atp_budget=100)
            member = team.get_member(lct)
            member["trust"] = {
                "reliability": 0.85, "competence": 0.85, "alignment": 0.85,
                "consistency": 0.85, "witnesses": 0.85, "lineage": 0.85,
            }
        team._update_team()
        return team

    def test_multisig_proposal_created_for_critical_action(self):
        """R6 request with MULTI_SIG approval creates a linked proposal."""
        from hardbound.r6 import R6Workflow
        from hardbound.multisig import MultiSigManager, CriticalAction
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        team = self._make_team("msig-r6")
        msig = MultiSigManager(team)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="member_removal",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=5,
            approval=ApprovalType.MULTI_SIG,
            approval_count=2,
        ))

        wf = R6Workflow(team, policy, multisig=msig)
        request = wf.create_request(
            requester_lct=f"dev:msig-r6:0",
            action_type="member_removal",
            description="Remove inactive member",
            parameters={"member_lct": f"dev:msig-r6:3"},
        )

        # R6 request should have a linked proposal
        assert request.linked_proposal_id != ""
        assert request.linked_proposal_id.startswith("msig:")

        # The proposal should exist in the multi-sig manager
        proposal = msig.get_proposal(request.linked_proposal_id)
        assert proposal is not None
        assert "[R6:" in proposal.description

    def test_r6_approval_delegates_to_multisig_vote(self):
        """Approving an R6 request also votes on the linked proposal."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.multisig import MultiSigManager, ProposalStatus
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        team = self._make_team("msig-vote")
        msig = MultiSigManager(team)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="policy_change",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=3,
            approval=ApprovalType.MULTI_SIG,
            approval_count=2,
        ))

        wf = R6Workflow(team, policy, multisig=msig)
        request = wf.create_request(
            requester_lct=f"dev:msig-vote:0",
            action_type="policy_change",
            description="Update trust thresholds",
            parameters={"changes": {"trust_min": 0.4}},
        )
        r6_id = request.r6_id
        proposal_id = request.linked_proposal_id

        # First voter approves via R6
        wf.approve_request(r6_id, f"dev:msig-vote:1")

        # Check proposal has a vote
        proposal = msig.get_proposal(proposal_id)
        assert proposal.approval_count == 1

        # Second voter approves - should trigger proposal approval
        updated = wf.approve_request(r6_id, f"dev:msig-vote:2")

        # R6 request should now be APPROVED (driven by proposal)
        assert updated.status == R6Status.APPROVED

        # Proposal should also be APPROVED
        proposal = msig.get_proposal(proposal_id)
        assert proposal.status == ProposalStatus.APPROVED

    def test_no_multisig_without_manager(self):
        """Without multisig manager, MULTI_SIG approval works with counts only."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        team = self._make_team("no-msig")

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="member_removal",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=5,
            approval=ApprovalType.MULTI_SIG,
            approval_count=2,
        ))

        # No multisig manager
        wf = R6Workflow(team, policy, multisig=None)
        request = wf.create_request(
            requester_lct=f"dev:no-msig:0",
            action_type="member_removal",
            description="Remove member",
            parameters={"member_lct": f"dev:no-msig:3"},
        )

        # No linked proposal
        assert request.linked_proposal_id == ""

        # Approval still works via count
        wf.approve_request(request.r6_id, f"dev:no-msig:1")
        wf.approve_request(request.r6_id, f"dev:no-msig:2")
        reloaded = wf.get_request(request.r6_id)
        assert reloaded.status == R6Status.APPROVED


class TestR6Expiry:
    """Tests for R6 request timeout and expiry."""

    def test_request_has_expiry_timestamp(self):
        """Created R6 requests have an expires_at timestamp."""
        from hardbound.r6 import R6Workflow
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-expiry", description="Expiry test")
        team = Team(config=config)
        team.set_admin("admin:exp")
        team.add_member("dev:exp", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="review",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=5,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy)
        request = wf.create_request(
            requester_lct="dev:exp",
            action_type="review",
            description="Review code",
        )

        assert request.expires_at != ""
        assert "2026" in request.expires_at  # Should be a future date

    def test_short_expiry_triggers_expired_status(self):
        """Request with very short expiry becomes expired."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType
        import time

        config = TeamConfig(name="r6-short-exp", description="Short expiry")
        team = Team(config=config)
        team.set_admin("admin:se")
        team.add_member("dev:se", role="developer", atp_budget=100)

        # Policy that allows very short expiry for testing
        policy = Policy(min_expiry_hours=0, max_expiry_hours=24*365)
        policy.add_rule(PolicyRule(
            action_type="quick_action",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=1,
            approval=ApprovalType.ADMIN,
        ))

        # Very short expiry (1 second = 1/3600 hours)
        wf = R6Workflow(team, policy, default_expiry_hours=1/3600)
        request = wf.create_request(
            requester_lct="dev:se",
            action_type="quick_action",
            description="Quick action",
        )
        r6_id = request.r6_id

        # Wait for expiry
        time.sleep(1.5)

        # Request should now be expired
        assert request.is_expired()

        # expire_request should work
        response = wf.expire_request(r6_id)
        assert response.status == R6Status.EXPIRED

    def test_cleanup_expired_batch(self):
        """cleanup_expired() expires all timed-out requests."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType
        import time

        config = TeamConfig(name="r6-batch-exp", description="Batch expiry")
        team = Team(config=config)
        team.set_admin("admin:be")
        team.add_member("dev:be", role="developer", atp_budget=100)

        # Policy that allows very short expiry for testing
        policy = Policy(min_expiry_hours=0, max_expiry_hours=24*365)
        policy.add_rule(PolicyRule(
            action_type="batch_action",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=1,
            approval=ApprovalType.ADMIN,
        ))

        # Short expiry
        wf = R6Workflow(team, policy, default_expiry_hours=1/3600)

        # Create multiple requests
        for i in range(3):
            wf.create_request(
                requester_lct="dev:be",
                action_type="batch_action",
                description=f"Batch {i}",
            )

        assert len(wf.get_pending_requests()) == 3

        # Wait for expiry
        time.sleep(1.5)

        # Cleanup should expire all
        expired = wf.cleanup_expired()
        assert len(expired) == 3
        assert all(r.status == R6Status.EXPIRED for r in expired)
        assert len(wf.get_pending_requests()) == 0

    def test_no_expiry_when_hours_zero(self):
        """Setting expiry_hours=0 disables expiry."""
        from hardbound.r6 import R6Workflow
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-no-exp", description="No expiry")
        team = Team(config=config)
        team.set_admin("admin:ne")
        team.add_member("dev:ne", role="developer", atp_budget=100)

        # Policy that allows zero expiry for testing "no expiry" mode
        policy = Policy(min_expiry_hours=0, max_expiry_hours=24*365)
        policy.add_rule(PolicyRule(
            action_type="eternal",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=1,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy, default_expiry_hours=0)
        request = wf.create_request(
            requester_lct="dev:ne",
            action_type="eternal",
            description="Never expires",
        )

        assert request.expires_at == ""
        assert not request.is_expired()


class TestPolicyExpiryEnforcement:
    """Tests for policy-enforced expiry constraints on R6 requests."""

    def test_policy_rejects_zero_expiry(self):
        """Policy rejects zero-expiry configuration."""
        from hardbound.policy import Policy

        policy = Policy(min_expiry_hours=24)
        valid, error, enforced = policy.validate_expiry_hours(0)

        assert not valid
        assert "positive" in error.lower()
        assert enforced == 24  # Enforced to minimum

    def test_policy_enforces_minimum_expiry(self):
        """Policy prevents expiry below minimum."""
        from hardbound.policy import Policy

        policy = Policy(min_expiry_hours=48)
        valid, error, enforced = policy.validate_expiry_hours(24)

        assert not valid
        assert "below" in error.lower()
        assert enforced == 48

    def test_policy_enforces_maximum_expiry(self):
        """Policy prevents expiry above maximum."""
        from hardbound.policy import Policy

        policy = Policy(max_expiry_hours=168)  # 7 days max
        valid, error, enforced = policy.validate_expiry_hours(720)  # 30 days

        assert not valid
        assert "exceeds" in error.lower()
        assert enforced == 168

    def test_workflow_clamps_to_policy_minimum(self):
        """R6Workflow respects policy minimum expiry."""
        from hardbound.r6 import R6Workflow
        from hardbound.policy import Policy

        config = TeamConfig(name="policy-min-exp", description="Minimum expiry test")
        team = Team(config=config)
        team.set_admin("admin:pme")

        # Policy requires minimum 72 hours
        policy = Policy(min_expiry_hours=72)

        # Workflow tries to use 24 hours
        wf = R6Workflow(team, policy, default_expiry_hours=24)

        # Should be clamped to 72
        assert wf.expiry_hours == 72
        assert wf._expiry_enforced == True


class TestR6Persistence:
    """Tests for R6 request persistence across workflow instances."""

    def test_pending_request_survives_restart(self):
        """Pending R6 requests persist across R6Workflow instantiations."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-persist", description="R6 persistence test")
        team = Team(config=config)
        team.set_admin("admin:persist")
        team.add_member("dev:persist", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="code_review",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=5,
            approval=ApprovalType.ADMIN,
        ))

        # Create request in first workflow instance
        wf1 = R6Workflow(team, policy)
        request = wf1.create_request(
            requester_lct="dev:persist",
            action_type="code_review",
            description="Review for persistence test",
        )
        r6_id = request.r6_id

        # Verify it's in the first workflow
        assert wf1.get_request(r6_id) is not None
        assert wf1.get_request(r6_id).status == R6Status.PENDING

        # Create SECOND workflow instance (simulates restart)
        wf2 = R6Workflow(team, policy)

        # Request should be loaded from DB
        reloaded = wf2.get_request(r6_id)
        assert reloaded is not None
        assert reloaded.r6_id == r6_id
        assert reloaded.status == R6Status.PENDING
        assert reloaded.description == "Review for persistence test"
        assert reloaded.action_type == "code_review"
        assert reloaded.requester_lct == "dev:persist"

    def test_approved_request_persists(self):
        """Approved requests persist with updated status."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-approve-persist", description="Approved persist")
        team = Team(config=config)
        team.set_admin("admin:ap")
        team.add_member("dev:ap", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="deploy",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=5,
            approval=ApprovalType.ADMIN,
        ))

        wf1 = R6Workflow(team, policy)
        request = wf1.create_request(
            requester_lct="dev:ap",
            action_type="deploy",
            description="Deploy to staging",
        )
        r6_id = request.r6_id
        wf1.approve_request(r6_id, "admin:ap")

        # New workflow instance should see approved status
        wf2 = R6Workflow(team, policy)
        reloaded = wf2.get_request(r6_id)
        assert reloaded is not None
        assert reloaded.status == R6Status.APPROVED
        assert "admin:ap" in reloaded.approvals

    def test_executed_request_removed_from_active(self):
        """Executed requests are removed from the active requests table."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-exec-clean", description="Exec cleanup")
        team = Team(config=config)
        team.set_admin("admin:ec")
        team.add_member("dev:ec", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="test_run",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=3,
            approval=ApprovalType.ADMIN,
        ))

        wf1 = R6Workflow(team, policy)
        request = wf1.create_request(
            requester_lct="dev:ec",
            action_type="test_run",
            description="Run test suite",
        )
        r6_id = request.r6_id
        wf1.approve_request(r6_id, "admin:ec")
        wf1.execute_request(r6_id, success=True)

        # New workflow instance should NOT see the executed request
        wf2 = R6Workflow(team, policy)
        assert wf2.get_request(r6_id) is None
        assert len(wf2.get_pending_requests()) == 0

    def test_rejected_request_removed_from_active(self):
        """Rejected requests are removed from the active requests table."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-reject-clean", description="Reject cleanup")
        team = Team(config=config)
        team.set_admin("admin:rc")
        team.add_member("dev:rc", role="developer", atp_budget=100)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="delete_env",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=5,
            approval=ApprovalType.ADMIN,
        ))

        wf1 = R6Workflow(team, policy)
        request = wf1.create_request(
            requester_lct="dev:rc",
            action_type="delete_env",
            description="Delete staging",
        )
        r6_id = request.r6_id
        wf1.reject_request(r6_id, "admin:rc", reason="Denied")

        # New workflow instance should NOT see the rejected request
        wf2 = R6Workflow(team, policy)
        assert wf2.get_request(r6_id) is None


class TestR6HeartbeatIntegration:
    """Tests for R6 events flowing into the heartbeat ledger."""

    def test_r6_events_become_heartbeat_transactions(self):
        """R6 create/approve/execute should appear as heartbeat ledger transactions."""
        from hardbound.r6 import R6Workflow
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-heartbeat", description="R6 heartbeat test")
        team = Team(config=config)
        team.set_admin("admin:hb")
        team.add_member("dev:hb", role="developer", atp_budget=100)

        # Initialize heartbeat ledger
        hl = team.heartbeat

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="deploy",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=5,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy)

        # Create request -> should submit r6_created transaction
        request = wf.create_request(
            requester_lct="dev:hb",
            action_type="deploy",
            description="Deploy to staging",
        )

        # Approve -> should submit r6_approved transaction
        wf.approve_request(request.r6_id, "admin:hb")

        # Execute -> should submit r6_executed transaction
        wf.execute_request(request.r6_id, success=True)

        # Check heartbeat ledger pending transactions
        pending = hl._pending_transactions
        tx_types = [tx.tx_type for tx in pending]

        assert "r6_created" in tx_types
        assert "r6_approved" in tx_types
        assert "r6_executed" in tx_types

        # The r6_executed transaction should have ATP cost
        exec_tx = [tx for tx in pending if tx.tx_type == "r6_executed"][0]
        assert exec_tx.atp_cost == 5.0

    def test_r6_rejection_recorded_in_heartbeat(self):
        """R6 rejection should also appear as a heartbeat transaction."""
        from hardbound.r6 import R6Workflow
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="r6-reject-hb", description="R6 reject heartbeat")
        team = Team(config=config)
        team.set_admin("admin:rj")
        team.add_member("dev:rj", role="developer", atp_budget=50)

        hl = team.heartbeat

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="delete_env",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=10,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy)
        request = wf.create_request(
            requester_lct="dev:rj",
            action_type="delete_env",
            description="Delete staging env",
        )

        # Reject the request
        wf.reject_request(request.r6_id, "admin:rj", reason="Not authorized")

        tx_types = [tx.tx_type for tx in hl._pending_transactions]
        assert "r6_created" in tx_types
        assert "r6_rejected" in tx_types

    def test_pulse_triggers_r6_cleanup(self):
        """pulse() with registered workflow cleans up expired R6 requests."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType
        import time

        config = TeamConfig(name="r6-pulse-cleanup", description="Pulse cleanup test")
        team = Team(config=config)
        team.set_admin("admin:pc")
        team.add_member("dev:pc", role="developer", atp_budget=100)

        # Policy allowing very short expiry for testing
        policy = Policy(min_expiry_hours=0, max_expiry_hours=24*365)
        policy.add_rule(PolicyRule(
            action_type="quick_job",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=1,
            approval=ApprovalType.ADMIN,
        ))

        # Short expiry workflow
        wf = R6Workflow(team, policy, default_expiry_hours=1/3600)

        # Register workflow with team
        team.register_r6_workflow(wf)

        # Create some requests
        for i in range(3):
            wf.create_request(
                requester_lct="dev:pc",
                action_type="quick_job",
                description=f"Job {i}",
            )

        assert len(wf.get_pending_requests()) == 3

        # Wait for expiry
        time.sleep(1.5)

        # pulse() should trigger cleanup
        block = team.pulse()

        # Requests should be gone
        assert len(wf.get_pending_requests()) == 0

        # Audit trail should have cleanup record
        audits = team.get_audit_trail()
        action_types = [a["action_type"] for a in audits]
        assert "r6_heartbeat_cleanup" in action_types

    def test_pulse_without_workflow_ok(self):
        """pulse() works fine without registered workflow."""
        config = TeamConfig(name="no-workflow", description="No workflow")
        team = Team(config=config)
        team.set_admin("admin:nw")

        # Just pulse without any R6 workflow
        block = team.pulse()
        assert block is not None
        assert block.block_number >= 0


class TestR6DelegationChains:
    """Tests for R6 request parent-child delegation chains."""

    def test_create_child_request(self):
        """Can create a request that depends on another."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="chain-test", description="Chain test")
        team = Team(config=config)
        team.set_admin("admin:ct")
        team.add_member("dev:ct", role="developer", atp_budget=100)

        policy = Policy()
        for action in ["review", "deploy"]:
            policy.add_rule(PolicyRule(
                action_type=action,
                allowed_roles=["developer", "admin"],
                trust_threshold=0.3,
                atp_cost=5,
                approval=ApprovalType.ADMIN,
            ))

        wf = R6Workflow(team, policy)

        # Create parent request
        parent = wf.create_request(
            requester_lct="dev:ct",
            action_type="review",
            description="Review code",
        )

        # Create child that depends on parent
        child = wf.create_request(
            requester_lct="dev:ct",
            action_type="deploy",
            description="Deploy after review",
            parent_r6_id=parent.r6_id,
        )

        assert child.parent_r6_id == parent.r6_id
        # Parent should track child
        parent_updated = wf.get_request(parent.r6_id)
        assert child.r6_id in parent_updated.child_r6_ids

    def test_parent_success_triggers_child(self):
        """Successful parent execution auto-approves children."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="chain-trigger", description="Chain trigger")
        team = Team(config=config)
        team.set_admin("admin:tr")
        team.add_member("dev:tr", role="developer", atp_budget=100)

        policy = Policy()
        for action in ["step1", "step2"]:
            policy.add_rule(PolicyRule(
                action_type=action,
                allowed_roles=["developer", "admin"],
                trust_threshold=0.3,
                atp_cost=2,
                approval=ApprovalType.ADMIN,
            ))

        wf = R6Workflow(team, policy)

        # Create parent and child
        parent = wf.create_request(
            requester_lct="dev:tr",
            action_type="step1",
            description="Step 1",
        )
        child = wf.create_request(
            requester_lct="dev:tr",
            action_type="step2",
            description="Step 2 (after step 1)",
            parent_r6_id=parent.r6_id,
        )

        # Child starts pending
        assert child.status == R6Status.PENDING

        # Approve and execute parent
        wf.approve_request(parent.r6_id, "admin:tr")
        wf.execute_request(parent.r6_id, success=True)

        # Child should now be auto-approved
        child_updated = wf.get_request(child.r6_id)
        assert child_updated.status == R6Status.APPROVED
        assert any("auto:parent" in a for a in child_updated.approvals)

    def test_parent_failure_does_not_trigger_child(self):
        """Failed parent does not auto-approve children."""
        from hardbound.r6 import R6Workflow, R6Status
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="chain-fail", description="Chain fail test")
        team = Team(config=config)
        team.set_admin("admin:cf")
        team.add_member("dev:cf", role="developer", atp_budget=100)

        policy = Policy()
        for action in ["stage", "prod"]:
            policy.add_rule(PolicyRule(
                action_type=action,
                allowed_roles=["developer", "admin"],
                trust_threshold=0.3,
                atp_cost=2,
                approval=ApprovalType.ADMIN,
            ))

        wf = R6Workflow(team, policy)

        parent = wf.create_request(
            requester_lct="dev:cf",
            action_type="stage",
            description="Deploy to staging",
        )
        child = wf.create_request(
            requester_lct="dev:cf",
            action_type="prod",
            description="Deploy to prod after staging",
            parent_r6_id=parent.r6_id,
        )

        # Approve and execute parent with FAILURE
        wf.approve_request(parent.r6_id, "admin:cf")
        wf.execute_request(parent.r6_id, success=False, error_message="Staging failed")

        # Child should remain pending
        child_updated = wf.get_request(child.r6_id)
        assert child_updated.status == R6Status.PENDING

    def test_chain_depth_limit(self):
        """Cannot create chains deeper than 10."""
        from hardbound.r6 import R6Workflow
        from hardbound.policy import Policy, PolicyRule, ApprovalType

        config = TeamConfig(name="chain-depth", description="Chain depth limit")
        team = Team(config=config)
        team.set_admin("admin:cd")
        team.add_member("dev:cd", role="developer", atp_budget=200)

        policy = Policy()
        policy.add_rule(PolicyRule(
            action_type="action",
            allowed_roles=["developer", "admin"],
            trust_threshold=0.3,
            atp_cost=1,
            approval=ApprovalType.ADMIN,
        ))

        wf = R6Workflow(team, policy)

        # Create a chain of 11 requests (depths 0-10)
        prev_id = ""
        for i in range(11):
            req = wf.create_request(
                requester_lct="dev:cd",
                action_type="action",
                description=f"Chain step {i}",
                parent_r6_id=prev_id if prev_id else None,
            )
            prev_id = req.r6_id

        # 12th should fail (depth would be 11)
        try:
            wf.create_request(
                requester_lct="dev:cd",
                action_type="action",
                description="Chain step 11 (too deep)",
                parent_r6_id=prev_id,
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "too deep" in str(e).lower()


class TestCrossTeamProposals:
    """Tests for federation-level cross-team R6 proposals."""

    def test_create_cross_team_proposal(self):
        """Can create a proposal requiring multiple team approvals."""
        from hardbound.federation import FederationRegistry
        import tempfile
        from pathlib import Path

        db_path = Path(tempfile.mkdtemp()) / "xteam.db"
        fed = FederationRegistry(db_path=db_path)

        # Register 3 teams
        fed.register_team("team:alpha", "Alpha", domains=["core"])
        fed.register_team("team:beta", "Beta", domains=["audit"])
        fed.register_team("team:gamma", "Gamma", domains=["ops"])

        # Alpha proposes something that requires Beta and Gamma approval
        proposal = fed.create_cross_team_proposal(
            proposing_team_id="team:alpha",
            proposer_lct="admin:alpha",
            action_type="shared_resource_grant",
            description="Grant shared access to resource X",
            target_team_ids=["team:beta", "team:gamma"],
            parameters={"resource_id": "res:X"},
        )

        assert proposal["status"] == "pending"
        assert proposal["proposing_team_id"] == "team:alpha"
        assert len(proposal["target_team_ids"]) == 2
        assert proposal["required_approvals"] == 2

    def test_approval_threshold(self):
        """Proposal approved when threshold met."""
        from hardbound.federation import FederationRegistry
        import tempfile
        from pathlib import Path

        db_path = Path(tempfile.mkdtemp()) / "xteam_approve.db"
        fed = FederationRegistry(db_path=db_path)

        fed.register_team("team:a", "Team A")
        fed.register_team("team:b", "Team B")
        fed.register_team("team:c", "Team C")

        proposal = fed.create_cross_team_proposal(
            proposing_team_id="team:a",
            proposer_lct="admin:a",
            action_type="policy_change",
            description="Change federation policy",
            target_team_ids=["team:b", "team:c"],
        )

        # First approval
        updated = fed.approve_cross_team_proposal(
            proposal["proposal_id"], "team:b", "admin:b"
        )
        assert updated["status"] == "pending"
        assert "team:b" in updated["approvals"]

        # Second approval triggers approval
        updated = fed.approve_cross_team_proposal(
            proposal["proposal_id"], "team:c", "admin:c"
        )
        assert updated["status"] == "approved"
        assert updated["outcome"] == "approved"

    def test_single_rejection_vetoes(self):
        """Single rejection blocks the entire proposal."""
        from hardbound.federation import FederationRegistry
        import tempfile
        from pathlib import Path

        db_path = Path(tempfile.mkdtemp()) / "xteam_reject.db"
        fed = FederationRegistry(db_path=db_path)

        fed.register_team("team:x", "Team X")
        fed.register_team("team:y", "Team Y")
        fed.register_team("team:z", "Team Z")

        proposal = fed.create_cross_team_proposal(
            proposing_team_id="team:x",
            proposer_lct="admin:x",
            action_type="access_grant",
            description="Grant cross-team access",
            target_team_ids=["team:y", "team:z"],
        )

        # Y approves
        fed.approve_cross_team_proposal(proposal["proposal_id"], "team:y", "admin:y")

        # Z rejects - entire proposal fails
        updated = fed.reject_cross_team_proposal(
            proposal["proposal_id"], "team:z", "admin:z", reason="Security concern"
        )
        assert updated["status"] == "rejected"
        assert updated["outcome"] == "rejected"
        assert "team:z" in updated["rejections"]

    def test_get_pending_for_team(self):
        """Can query pending proposals for a specific team."""
        from hardbound.federation import FederationRegistry
        import tempfile
        from pathlib import Path

        db_path = Path(tempfile.mkdtemp()) / "xteam_pending.db"
        fed = FederationRegistry(db_path=db_path)

        fed.register_team("team:p1", "P1")
        fed.register_team("team:p2", "P2")
        fed.register_team("team:p3", "P3")

        # Create 2 proposals targeting p2
        fed.create_cross_team_proposal(
            "team:p1", "admin:p1", "action1", "Desc 1", ["team:p2"]
        )
        fed.create_cross_team_proposal(
            "team:p3", "admin:p3", "action2", "Desc 2", ["team:p2"]
        )

        # Create 1 proposal not targeting p2
        fed.create_cross_team_proposal(
            "team:p1", "admin:p1", "action3", "Desc 3", ["team:p3"]
        )

        # P2 should see 2 pending proposals
        pending = fed.get_pending_cross_team_proposals("team:p2")
        assert len(pending) == 2

        # P3 should see 1 pending proposal
        pending = fed.get_pending_cross_team_proposals("team:p3")
        assert len(pending) == 1
