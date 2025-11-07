"""
Tests for Web4 Authorization Engine
===================================

Comprehensive test suite validating authorization logic, security boundaries,
and integration with Web4 protocols.
"""

import pytest
import time
from authorization_engine import (
    AuthorizationEngine,
    AuthorizationRequest,
    AgentDelegation,
    LCTCredential,
    AuthorizationDecision,
    DenialReason
)


class TestAuthorizationEngine:
    """Test suite for authorization engine"""

    def setup_method(self):
        """Setup test environment"""
        self.engine = AuthorizationEngine("society:test")

        # Create test delegation
        self.delegation = AgentDelegation(
            delegation_id="deleg:test001",
            client_lct="lct:human:alice",
            agent_lct="lct:ai:assistant",
            role_lct="role:researcher",
            granted_permissions={"read", "write", "compute"},
            atp_budget=1000,
            max_actions_per_hour=10
        )
        self.engine.register_delegation(self.delegation)

        # Create test credential
        self.credential = LCTCredential(
            lct_id="lct:ai:assistant",
            entity_type="AI",
            society_id="society:test",
            birth_certificate_hash="test_hash",
            public_key="test_pubkey"
        )

    def test_successful_authorization(self):
        """Test that valid request is authorized"""
        request = AuthorizationRequest(
            requester_lct="lct:ai:assistant",
            action="read",
            target_resource="data:test",
            atp_cost=10,
            context={},
            delegation_id="deleg:test001"
        )

        result = self.engine.authorize_action(request, self.credential)

        assert result.decision == AuthorizationDecision.GRANTED
        assert result.actual_trust_score > 0
        assert result.atp_remaining == 990  # 1000 - 10

    def test_invalid_lct_denial(self):
        """Test that invalid LCT is denied"""
        request = AuthorizationRequest(
            requester_lct="lct:invalid",
            action="read",
            target_resource="data:test",
            atp_cost=10,
            context={}
        )

        result = self.engine.authorize_action(request)

        assert result.decision == AuthorizationDecision.DENIED
        assert result.denial_reason == DenialReason.INVALID_LCT

    def test_role_mismatch_denial(self):
        """Test that unauthorized action is denied"""
        request = AuthorizationRequest(
            requester_lct="lct:ai:assistant",
            action="delete",  # Not in granted_permissions
            target_resource="data:test",
            atp_cost=10,
            context={},
            delegation_id="deleg:test001"
        )

        result = self.engine.authorize_action(request, self.credential)

        assert result.decision == AuthorizationDecision.DENIED
        assert result.denial_reason == DenialReason.ROLE_MISMATCH

    def test_atp_budget_exceeded(self):
        """Test that ATP budget is enforced"""
        request = AuthorizationRequest(
            requester_lct="lct:ai:assistant",
            action="read",
            target_resource="data:test",
            atp_cost=2000,  # Exceeds budget of 1000
            context={},
            delegation_id="deleg:test001"
        )

        result = self.engine.authorize_action(request, self.credential)

        assert result.decision == AuthorizationDecision.DENIED
        assert result.denial_reason == DenialReason.ATP_BUDGET_EXCEEDED

    def test_atp_consumption(self):
        """Test that ATP is correctly consumed"""
        # First request
        request1 = AuthorizationRequest(
            requester_lct="lct:ai:assistant",
            action="read",
            target_resource="data:test1",
            atp_cost=100,
            context={},
            delegation_id="deleg:test001"
        )

        result1 = self.engine.authorize_action(request1, self.credential)
        assert result1.decision == AuthorizationDecision.GRANTED
        assert result1.atp_remaining == 900

        # Second request
        request2 = AuthorizationRequest(
            requester_lct="lct:ai:assistant",
            action="write",
            target_resource="data:test2",
            atp_cost=300,
            context={},
            delegation_id="deleg:test001"
        )

        result2 = self.engine.authorize_action(request2, self.credential)
        assert result2.decision == AuthorizationDecision.GRANTED
        assert result2.atp_remaining == 600

        # Verify delegation state
        delegation = self.engine.get_delegation("deleg:test001")
        assert delegation.atp_spent == 400

    def test_rate_limiting(self):
        """Test that rate limits are enforced"""
        # Max is 10 actions per hour
        for i in range(10):
            request = AuthorizationRequest(
                requester_lct="lct:ai:assistant",
                action="read",
                target_resource=f"data:test{i}",
                atp_cost=1,
                context={},
                delegation_id="deleg:test001"
            )

            result = self.engine.authorize_action(request, self.credential)
            assert result.decision == AuthorizationDecision.GRANTED

        # 11th request should be denied
        request = AuthorizationRequest(
            requester_lct="lct:ai:assistant",
            action="read",
            target_resource="data:test11",
            atp_cost=1,
            context={},
            delegation_id="deleg:test001"
        )

        result = self.engine.authorize_action(request, self.credential)
        assert result.decision == AuthorizationDecision.DENIED
        assert result.denial_reason == DenialReason.RATE_LIMIT_EXCEEDED

    def test_expired_delegation(self):
        """Test that expired delegations are denied"""
        # Create delegation that expires immediately
        expired_delegation = AgentDelegation(
            delegation_id="deleg:expired",
            client_lct="lct:human:bob",
            agent_lct="lct:ai:assistant",
            role_lct="role:researcher",
            granted_permissions={"read"},
            atp_budget=1000,
            valid_from=time.time() - 100,
            valid_until=time.time() - 50  # Expired
        )
        self.engine.register_delegation(expired_delegation)

        request = AuthorizationRequest(
            requester_lct="lct:ai:assistant",
            action="read",
            target_resource="data:test",
            atp_cost=10,
            context={},
            delegation_id="deleg:expired"
        )

        result = self.engine.authorize_action(request, self.credential)
        assert result.decision == AuthorizationDecision.DENIED
        assert result.denial_reason == DenialReason.DELEGATION_EXPIRED

    def test_delegation_revocation(self):
        """Test that revoked delegations cannot be used"""
        # Revoke delegation
        assert self.engine.revoke_delegation("deleg:test001")

        request = AuthorizationRequest(
            requester_lct="lct:ai:assistant",
            action="read",
            target_resource="data:test",
            atp_cost=10,
            context={},
            delegation_id="deleg:test001"
        )

        result = self.engine.authorize_action(request, self.credential)
        assert result.decision == AuthorizationDecision.DENIED
        assert result.denial_reason == DenialReason.DELEGATION_EXPIRED

    def test_authorization_statistics(self):
        """Test that authorization statistics are tracked"""
        # Make several requests
        for i in range(5):
            request = AuthorizationRequest(
                requester_lct="lct:ai:assistant",
                action="read",
                target_resource=f"data:test{i}",
                atp_cost=10,
                context={},
                delegation_id="deleg:test001"
            )
            self.engine.authorize_action(request, self.credential)

        # Get stats
        stats = self.engine.get_authorization_stats("lct:ai:assistant")

        assert stats["total"] == 5
        assert stats["granted"] == 5
        assert stats["denied"] == 0
        assert stats["success_rate"] == 1.0
        assert stats["total_atp_cost"] == 50

    def test_audit_log_integrity(self):
        """Test that authorization decisions are logged with hashes"""
        request = AuthorizationRequest(
            requester_lct="lct:ai:assistant",
            action="read",
            target_resource="data:test",
            atp_cost=10,
            context={},
            delegation_id="deleg:test001"
        )

        result = self.engine.authorize_action(request, self.credential)

        assert result.decision_log_hash != ""
        assert len(result.decision_log_hash) == 64  # SHA-256 hex string

        # Verify log entry exists
        assert len(self.engine.authorization_log) > 0
        assert self.engine.authorization_log[-1].decision_log_hash == result.decision_log_hash


class TestDelegationManagement:
    """Test delegation lifecycle"""

    def setup_method(self):
        self.engine = AuthorizationEngine("society:test")

    def test_delegation_registration(self):
        """Test delegation registration"""
        delegation = AgentDelegation(
            delegation_id="deleg:new",
            client_lct="lct:human:charlie",
            agent_lct="lct:ai:helper",
            role_lct="role:assistant",
            granted_permissions={"read"},
            atp_budget=500
        )

        self.engine.register_delegation(delegation)

        retrieved = self.engine.get_delegation("deleg:new")
        assert retrieved is not None
        assert retrieved.delegation_id == "deleg:new"
        assert retrieved.atp_budget == 500

    def test_delegation_validity_check(self):
        """Test delegation validity checking"""
        delegation = AgentDelegation(
            delegation_id="deleg:temp",
            client_lct="lct:human:dave",
            agent_lct="lct:ai:temp",
            role_lct="role:temp",
            granted_permissions={"read"},
            atp_budget=100,
            valid_from=time.time() + 100,  # Future start
            valid_until=time.time() + 200
        )

        assert not delegation.is_valid()  # Not yet valid

    def test_delegation_budget_tracking(self):
        """Test ATP budget tracking"""
        delegation = AgentDelegation(
            delegation_id="deleg:budget",
            client_lct="lct:human:eve",
            agent_lct="lct:ai:spender",
            role_lct="role:spender",
            granted_permissions={"compute"},
            atp_budget=1000
        )

        assert delegation.has_budget(500)
        assert delegation.consume_atp(500)
        assert delegation.atp_spent == 500

        assert delegation.has_budget(500)
        assert not delegation.has_budget(501)


class TestSecurityBoundaries:
    """Test security boundary enforcement"""

    def setup_method(self):
        self.engine = AuthorizationEngine("society:security_test")

    def test_cross_society_access_denied(self):
        """Test that entities from different societies cannot access resources"""
        # TODO: Implement cross-society boundary checks
        pass

    def test_privilege_escalation_prevention(self):
        """Test that agents cannot escalate their privileges"""
        # Create limited delegation
        delegation = AgentDelegation(
            delegation_id="deleg:limited",
            client_lct="lct:human:frank",
            agent_lct="lct:ai:limited",
            role_lct="role:read_only",
            granted_permissions={"read"},  # Only read, not write
            atp_budget=100
        )
        self.engine.register_delegation(delegation)

        credential = LCTCredential(
            lct_id="lct:ai:limited",
            entity_type="AI",
            society_id="society:security_test",
            birth_certificate_hash="test",
            public_key="test"
        )

        # Attempt to perform write action (should be denied)
        request = AuthorizationRequest(
            requester_lct="lct:ai:limited",
            action="write",
            target_resource="data:sensitive",
            atp_cost=10,
            context={},
            delegation_id="deleg:limited"
        )

        result = self.engine.authorize_action(request, credential)
        assert result.decision == AuthorizationDecision.DENIED
        assert result.denial_reason == DenialReason.ROLE_MISMATCH

    def test_delegation_cannot_exceed_budget(self):
        """Test that agents cannot circumvent ATP budget"""
        delegation = AgentDelegation(
            delegation_id="deleg:strict_budget",
            client_lct="lct:human:grace",
            agent_lct="lct:ai:spender",
            role_lct="role:spender",
            granted_permissions={"compute"},
            atp_budget=50
        )
        self.engine.register_delegation(delegation)

        credential = LCTCredential(
            lct_id="lct:ai:spender",
            entity_type="AI",
            society_id="society:security_test",
            birth_certificate_hash="test",
            public_key="test"
        )

        # Spend budget
        request1 = AuthorizationRequest(
            requester_lct="lct:ai:spender",
            action="compute",
            target_resource="task:1",
            atp_cost=30,
            context={},
            delegation_id="deleg:strict_budget"
        )
        result1 = self.engine.authorize_action(request1, credential)
        assert result1.decision == AuthorizationDecision.GRANTED

        # Attempt to exceed budget
        request2 = AuthorizationRequest(
            requester_lct="lct:ai:spender",
            action="compute",
            target_resource="task:2",
            atp_cost=30,  # Would exceed 50 total
            context={},
            delegation_id="deleg:strict_budget"
        )
        result2 = self.engine.authorize_action(request2, credential)
        assert result2.decision == AuthorizationDecision.DENIED
        assert result2.denial_reason == DenialReason.ATP_BUDGET_EXCEEDED


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
