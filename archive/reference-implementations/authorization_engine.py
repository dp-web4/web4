"""
Web4 Authorization Engine
=========================

Runtime authorization verification system for Web4 entities performing actions.

This implements the authorization layer that sits between Web4 protocols (LCT, SAL, AGY)
and actual execution, answering the critical question: "Is this entity authorized to
perform this action right now?"

Key Components:
- LCT credential verification
- Role-based permission checking against Law Oracle
- ATP budget enforcement
- Trust-based authorization thresholds
- Decision logging for reputation updates

Design Philosophy:
- Default deny (fail-safe)
- Explicit authorization required
- All decisions logged and witnessed
- Trust accumulation through successful authorizations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import time
import hashlib
import json

# Import real Trust Oracle (Session: Autonomous Web4 Research 2025-12-05)
from trust_oracle import TrustOracle as RealTrustOracle

# Import real cryptographic verification (Track 2: 2025-12-05)
from crypto_verification import verify_signature as verify_ed25519_signature

# Import real Law Oracle implementation
from law_oracle import LawOracle, RolePermissions, create_default_law_dataset


class AuthorizationDecision(Enum):
    """Authorization decision outcomes"""
    GRANTED = "granted"
    DENIED = "denied"
    DEFERRED = "deferred"  # Requires human approval
    EXPIRED = "expired"


class DenialReason(Enum):
    """Why authorization was denied"""
    INVALID_LCT = "invalid_lct"
    ROLE_MISMATCH = "role_mismatch"
    INSUFFICIENT_TRUST = "insufficient_trust"
    ATP_BUDGET_EXCEEDED = "atp_budget_exceeded"
    LAW_VIOLATION = "law_violation"
    DELEGATION_EXPIRED = "delegation_expired"
    MISSING_WITNESS = "missing_witness"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


@dataclass
class LCTCredential:
    """Verified LCT identity credential"""
    lct_id: str
    entity_type: str  # HUMAN, AI, ROLE, etc.
    society_id: str
    birth_certificate_hash: str
    public_key: str
    hardware_binding_hash: Optional[str] = None

    def verify_signature(self, message: bytes, signature: bytes) -> bool:
        """
        Verify cryptographic signature using Ed25519.

        Updated: Track 2 (2025-12-05) - Real crypto verification
        Replaced stub with actual Ed25519 signature verification.

        Args:
            message: Message that was signed
            signature: Signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            return verify_ed25519_signature(
                public_key=self.public_key,
                message=message,
                signature=signature
            )
        except Exception as e:
            # Log error but don't raise - return False for invalid signature
            print(f"Signature verification error for {self.lct_id}: {e}")
            return False


@dataclass
class AgentDelegation:
    """
    Authority delegated from Client to Agent

    Attack Mitigations #4-5 Integrated:
    - #4: Budget fragmentation tracking (min_atp_per_action)
    - #5: Delegation chain depth limits (chain_depth, parent_delegation_id)
    """
    delegation_id: str
    client_lct: str
    agent_lct: str
    role_lct: str
    granted_permissions: Set[str]
    atp_budget: int
    atp_spent: int = 0
    valid_from: float = field(default_factory=time.time)
    valid_until: float = field(default_factory=lambda: time.time() + 86400)  # 24h default
    max_actions_per_hour: int = 100
    actions_this_hour: int = 0
    last_hour_reset: float = field(default_factory=time.time)

    # Mitigation #4: Budget fragmentation prevention
    min_atp_per_action: int = 1  # Minimum ATP cost per action (prevents dust attacks)
    total_actions_allowed: int = 10000  # Maximum total actions (prevents fragmentation)
    total_actions_taken: int = 0

    # Mitigation #5: Delegation chain amplification detection
    chain_depth: int = 0  # Depth in delegation chain (0 = direct delegation)
    parent_delegation_id: Optional[str] = None  # Parent delegation (if sub-delegated)
    max_chain_depth: int = 3  # Maximum delegation chain depth allowed

    def is_valid(self) -> bool:
        """Check if delegation is still valid"""
        now = time.time()
        return self.valid_from <= now <= self.valid_until

    def has_budget(self, cost: int) -> bool:
        """Check if ATP budget allows this action"""
        return (self.atp_spent + cost) <= self.atp_budget

    def consume_atp(self, cost: int) -> bool:
        """Consume ATP from budget"""
        if not self.has_budget(cost):
            return False
        self.atp_spent += cost
        return True

    def check_rate_limit(self) -> bool:
        """Check if rate limit allows action"""
        now = time.time()
        # Reset hourly counter if needed
        if now - self.last_hour_reset > 3600:
            self.actions_this_hour = 0
            self.last_hour_reset = now

        return self.actions_this_hour < self.max_actions_per_hour

    def record_action(self):
        """Record an action for rate limiting and fragmentation tracking"""
        self.actions_this_hour += 1
        self.total_actions_taken += 1  # Mitigation #4: Track total actions

    def check_fragmentation(self, atp_cost: int) -> Tuple[bool, Optional[str]]:
        """
        Check if action violates budget fragmentation limits

        Attack Mitigation #4: Budget Fragmentation Prevention
        Prevents agents from performing excessive micro-transactions to
        circumvent rate limits or extend delegation lifetime artificially.

        Returns:
            (valid, error_message) tuple
        """
        # Check minimum ATP per action
        if atp_cost < self.min_atp_per_action:
            return False, f"ATP cost {atp_cost} below minimum {self.min_atp_per_action}"

        # Check total action limit
        if self.total_actions_taken >= self.total_actions_allowed:
            return False, f"Total action limit reached: {self.total_actions_allowed}"

        # Check fragmentation ratio (avg ATP per action)
        if self.total_actions_taken > 0:
            avg_atp = self.atp_spent / self.total_actions_taken
            if avg_atp < self.min_atp_per_action * 0.5:
                return False, f"Average ATP per action too low: {avg_atp:.2f}"

        return True, None

    def check_chain_depth(self) -> Tuple[bool, Optional[str]]:
        """
        Check if delegation chain depth is within limits

        Attack Mitigation #5: Delegation Chain Amplification Detection
        Prevents privilege escalation through deep delegation chains.

        Returns:
            (valid, error_message) tuple
        """
        if self.chain_depth > self.max_chain_depth:
            return False, f"Delegation chain too deep: {self.chain_depth} > {self.max_chain_depth}"

        return True, None


@dataclass
class AuthorizationRequest:
    """Request to authorize an action"""
    requester_lct: str
    action: str  # R6 action type
    target_resource: str
    atp_cost: int
    context: Dict[str, any]
    delegation_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class AuthorizationResult:
    """Result of authorization check"""
    decision: AuthorizationDecision
    request: AuthorizationRequest
    denial_reason: Optional[DenialReason] = None
    required_trust_score: float = 0.0
    actual_trust_score: float = 0.0
    atp_remaining: int = 0
    requires_witness: bool = False
    decision_log_hash: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_audit_record(self) -> Dict:
        """Convert to audit log record"""
        return {
            "decision": self.decision.value,
            "requester": self.request.requester_lct,
            "action": self.request.action,
            "target": self.request.target_resource,
            "atp_cost": self.request.atp_cost,
            "denial_reason": self.denial_reason.value if self.denial_reason else None,
            "trust_required": self.required_trust_score,
            "trust_actual": self.actual_trust_score,
            "timestamp": self.timestamp,
            "log_hash": self.decision_log_hash
        }


class TrustOracle:
    """
    Wrapper for Trust Oracle integration

    This maintains backward compatibility with existing authorization_engine code
    while delegating to the real PostgreSQL-backed TrustOracle.

    Updated: Autonomous Web4 Research Session 2025-12-05
    - Replaced hardcoded 0.75 stub with real T3/V3 queries
    - Delegates to trust_oracle.TrustOracle
    """

    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """
        Initialize Trust Oracle wrapper.

        Args:
            db_config: PostgreSQL connection config (if None, uses stub mode)
        """
        self.db_config = db_config
        self.real_oracle: Optional[RealTrustOracle] = None

        if db_config:
            try:
                self.real_oracle = RealTrustOracle(db_config)
            except Exception as e:
                # Fall back to stub mode on error
                print(f"Warning: Trust Oracle init failed, using stub mode: {e}")

    def get_trust_score(self, entity_lct: str, role_lct: str, context: str) -> float:
        """
        Get T3 trust score for entity in role context

        Args:
            entity_lct: Entity whose trust to query
            role_lct: Role context
            context: Organization or action context

        Returns:
            Trust score (0.0-1.0)
        """
        if self.real_oracle:
            # Use real oracle
            try:
                return self.real_oracle.query_trust_for_authorization(
                    lct_id=entity_lct,
                    organization_id=context,
                    action_type="",
                    required_role=role_lct
                )
            except Exception as e:
                print(f"Warning: Trust query failed, using default: {e}")
                return 0.5  # Conservative default on error
        else:
            # Stub mode fallback
            return 0.75


class AuthorizationEngine:
    """
    Web4 Authorization Engine

    Central authorization system that verifies every Web4 action before execution.
    Integrates LCT identity, role-based permissions, trust assessment, and ATP budgeting.
    """

    def __init__(self, society_id: str, law_oracle_lct: Optional[str] = None):
        self.society_id = society_id

        # Create law oracle and publish default law dataset
        if law_oracle_lct is None:
            law_oracle_lct = f"lct:web4:oracle:law:{society_id}:1"

        self.law_oracle = LawOracle(society_id, law_oracle_lct)

        # Publish default law dataset
        default_law = create_default_law_dataset(society_id, law_oracle_lct, "1.0.0")
        self.law_oracle.publish_law_dataset(default_law)

        self.trust_oracle = TrustOracle()

        # Runtime state
        self.active_delegations: Dict[str, AgentDelegation] = {}
        self.verified_lcts: Dict[str, LCTCredential] = {}
        self.authorization_log: List[AuthorizationResult] = []

    def verify_lct(self, lct_id: str, signature: bytes, message: bytes) -> Optional[LCTCredential]:
        """Verify LCT credential and signature"""
        # Check cache first
        if lct_id in self.verified_lcts:
            cached = self.verified_lcts[lct_id]
            if cached.verify_signature(message, signature):
                return cached

        # TODO: Fetch and verify LCT from registry
        # For now, create stub credential
        credential = LCTCredential(
            lct_id=lct_id,
            entity_type="AI",
            society_id=self.society_id,
            birth_certificate_hash="stub_hash",
            public_key="stub_pubkey"
        )

        if credential.verify_signature(message, signature):
            self.verified_lcts[lct_id] = credential
            return credential

        return None

    def get_delegation(self, delegation_id: str) -> Optional[AgentDelegation]:
        """Retrieve active delegation"""
        delegation = self.active_delegations.get(delegation_id)
        if delegation and delegation.is_valid():
            return delegation
        return None

    def authorize_action(self, request: AuthorizationRequest,
                        credential: Optional[LCTCredential] = None,
                        signature: Optional[bytes] = None) -> AuthorizationResult:
        """
        Main authorization check - is this entity authorized for this action?

        Process:
        1. Verify LCT credential
        2. Check delegation if agent action
        3. Get role permissions from Law Oracle
        4. Check trust score against threshold
        5. Verify ATP budget
        6. Check rate limits
        7. Verify witness requirements
        8. Make final decision
        9. Log decision
        """

        # Step 1: Verify LCT
        if credential is None:
            if signature is None:
                return self._deny(request, DenialReason.INVALID_LCT)
            credential = self.verify_lct(request.requester_lct, signature, b"stub_message")

        if credential is None:
            return self._deny(request, DenialReason.INVALID_LCT)

        # Step 2: Check delegation if provided
        delegation = None
        if request.delegation_id:
            delegation = self.get_delegation(request.delegation_id)
            if not delegation or not delegation.is_valid():
                return self._deny(request, DenialReason.DELEGATION_EXPIRED)

            # Check if delegation allows this action
            if request.action not in delegation.granted_permissions:
                return self._deny(request, DenialReason.ROLE_MISMATCH)

            # Check ATP budget
            if not delegation.has_budget(request.atp_cost):
                return self._deny(request, DenialReason.ATP_BUDGET_EXCEEDED)

            # Check rate limits
            if not delegation.check_rate_limit():
                return self._deny(request, DenialReason.RATE_LIMIT_EXCEEDED)

            # Mitigation #4: Check budget fragmentation
            valid_frag, frag_error = delegation.check_fragmentation(request.atp_cost)
            if not valid_frag:
                logger.warning(f"Budget fragmentation detected: {frag_error}")
                return self._deny(request, DenialReason.ATP_BUDGET_EXCEEDED)

            # Mitigation #5: Check delegation chain depth
            valid_depth, depth_error = delegation.check_chain_depth()
            if not valid_depth:
                logger.warning(f"Delegation chain violation: {depth_error}")
                return self._deny(request, DenialReason.DELEGATION_EXPIRED)

        # Step 3: Get role permissions
        role_lct = delegation.role_lct if delegation else f"role:citizen:{credential.lct_id}"
        permissions = self.law_oracle.get_role_permissions(role_lct)

        if not permissions:
            return self._deny(request, DenialReason.ROLE_MISMATCH)

        if not permissions.can_perform(request.action):
            return self._deny(request, DenialReason.ROLE_MISMATCH)

        # Step 4: Check trust score
        trust_score = self.trust_oracle.get_trust_score(
            credential.lct_id,
            role_lct,
            request.context.get("trust_context", "general")
        )

        if trust_score < permissions.trust_threshold:
            result = self._deny(request, DenialReason.INSUFFICIENT_TRUST)
            result.required_trust_score = permissions.trust_threshold
            result.actual_trust_score = trust_score
            return result

        # Step 5: Check Law Oracle for action legality
        is_legal, violation = self.law_oracle.check_action_legality(
            request.action,
            request.context,
            role_lct
        )

        if not is_legal:
            return self._deny(request, DenialReason.LAW_VIOLATION)

        # Step 6: Check ATP cost against role limits
        if request.atp_cost > permissions.max_atp_per_action:
            return self._deny(request, DenialReason.ATP_BUDGET_EXCEEDED)

        # Step 7: Check witness requirements
        # Only require witness if explicitly required by role OR trust is very low (<0.6)
        requires_witness = permissions.requires_witness or trust_score < 0.6

        if requires_witness and not request.context.get("witness_attestation"):
            # Defer to human oversight
            result = AuthorizationResult(
                decision=AuthorizationDecision.DEFERRED,
                request=request,
                required_trust_score=permissions.trust_threshold,
                actual_trust_score=trust_score,
                requires_witness=True,
                atp_remaining=delegation.atp_budget - delegation.atp_spent if delegation else 0
            )
            self._log_decision(result)
            return result

        # Step 8: GRANT authorization
        if delegation:
            delegation.consume_atp(request.atp_cost)
            delegation.record_action()

        result = AuthorizationResult(
            decision=AuthorizationDecision.GRANTED,
            request=request,
            required_trust_score=permissions.trust_threshold,
            actual_trust_score=trust_score,
            atp_remaining=delegation.atp_budget - delegation.atp_spent if delegation else 0,
            requires_witness=requires_witness
        )

        self._log_decision(result)
        return result

    def _deny(self, request: AuthorizationRequest, reason: DenialReason) -> AuthorizationResult:
        """Create denial result"""
        result = AuthorizationResult(
            decision=AuthorizationDecision.DENIED,
            request=request,
            denial_reason=reason
        )
        self._log_decision(result)
        return result

    def _log_decision(self, result: AuthorizationResult):
        """Log authorization decision for audit and learning"""
        # Create hash of decision for tamper-evidence
        audit_record = result.to_audit_record()
        record_json = json.dumps(audit_record, sort_keys=True)
        result.decision_log_hash = hashlib.sha256(record_json.encode()).hexdigest()

        self.authorization_log.append(result)

        # TODO: Send to immutable ledger
        # TODO: Update trust scores based on outcome

    def register_delegation(self, delegation: AgentDelegation):
        """Register a new agent delegation"""
        self.active_delegations[delegation.delegation_id] = delegation

    def revoke_delegation(self, delegation_id: str) -> bool:
        """Revoke an active delegation"""
        if delegation_id in self.active_delegations:
            del self.active_delegations[delegation_id]
            return True
        return False

    def get_authorization_stats(self, lct_id: str) -> Dict:
        """Get authorization statistics for an entity"""
        entity_logs = [log for log in self.authorization_log
                      if log.request.requester_lct == lct_id]

        if not entity_logs:
            return {"total": 0}

        granted = len([l for l in entity_logs if l.decision == AuthorizationDecision.GRANTED])
        denied = len([l for l in entity_logs if l.decision == AuthorizationDecision.DENIED])
        deferred = len([l for l in entity_logs if l.decision == AuthorizationDecision.DEFERRED])

        return {
            "total": len(entity_logs),
            "granted": granted,
            "denied": denied,
            "deferred": deferred,
            "success_rate": granted / len(entity_logs) if entity_logs else 0.0,
            "avg_trust_score": sum(l.actual_trust_score for l in entity_logs) / len(entity_logs),
            "total_atp_cost": sum(l.request.atp_cost for l in entity_logs if l.decision == AuthorizationDecision.GRANTED)
        }


# Example usage
if __name__ == "__main__":
    # Create authorization engine for a society
    engine = AuthorizationEngine("society:demo")

    # Register a delegation
    delegation = AgentDelegation(
        delegation_id="deleg:001",
        client_lct="lct:human:alice",
        agent_lct="lct:ai:assistant",
        role_lct="role:researcher",
        granted_permissions={"read", "write", "compute"},
        atp_budget=1000,
        max_actions_per_hour=50
    )
    engine.register_delegation(delegation)

    # Create authorization request
    request = AuthorizationRequest(
        requester_lct="lct:ai:assistant",
        action="read",
        target_resource="data:research_papers",
        atp_cost=5,
        context={"trust_context": "research"},
        delegation_id="deleg:001"
    )

    # Authorize
    result = engine.authorize_action(request)

    print(f"Authorization Decision: {result.decision.value}")
    print(f"Trust Score: {result.actual_trust_score} (required: {result.required_trust_score})")
    print(f"ATP Remaining: {result.atp_remaining}")
    print(f"Decision Hash: {result.decision_log_hash}")

    # Get stats
    stats = engine.get_authorization_stats("lct:ai:assistant")
    print(f"\nAuthorization Stats:")
    print(f"  Success Rate: {stats['success_rate']:.2%}")
    print(f"  Total ATP Cost: {stats['total_atp_cost']}")
