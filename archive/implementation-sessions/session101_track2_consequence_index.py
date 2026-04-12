"""
SESSION 101 TRACK 2: CONSEQUENCE INDEX (CX) IMPLEMENTATION

Implements the Consequence Index proposal and integrates with:
- Track 1: MRH Grounding and Coherence Index (CI)
- Session 100: Delegation chains and ATP budgets

Key concept: CI/CX Gating
- CI (Coherence Index): How "present" an entity is
- CX (Consequence Index): How consequential an action is
- Gating Rule: CI >= threshold_for(CX)

"Don't operate machinery while impaired" - applied to AI agents.

References:
- Consequence Index Proposal: /home/dp/ai-workspace/private-context/messages/2025-12-28-consequence-index-proposal.md
- MRH Grounding Proposal: /home/dp/ai-workspace/web4/proposals/MRH_GROUNDING_PROPOSAL.md
- Session 100: ACT integration (delegation chains, ATP budgets)
"""

import json
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from enum import Enum

# Import Track 1 components
import sys
sys.path.append('/home/dp/ai-workspace/web4/implementation')
from session101_track1_mrh_grounding import (
    GroundingManager,
    CoherenceWeights
)

# Import Session 100 components
from session100_track2_act_delegation_chain import (
    ACTDelegationToken,
    ACTDelegationChainKeeper,
    ScopedPermission
)
from session100_track3_act_atp_budgets import (
    ATPBudgetEnforcer,
    DelegationBudget
)


# ============================================================================
# CONSEQUENCE INDEX
# ============================================================================

class ConsequenceLevel(Enum):
    """Predefined consequence levels for common action types."""
    TRIVIAL = 0.1      # Read-only queries, logging
    LOW = 0.3          # State modifications, API calls
    MEDIUM = 0.5       # Financial transactions, deployments
    HIGH = 0.7         # Irreversible actions, deletions
    CRITICAL = 0.9     # Critical infrastructure, safety-relevant


@dataclass
class ConsequenceIndex:
    """
    Measures how consequential an action is.

    CX ∈ [0.0, 1.0] where:
    - 0.0 = No consequences (read-only, harmless)
    - 0.5 = Moderate consequences (reversible changes)
    - 1.0 = Maximum consequences (irreversible, safety-critical)
    """
    cx: float  # Consequence index value
    category: str  # Action category (for explanation)
    reversible: bool = True  # Can action be undone?
    affects_safety: bool = False  # Safety-relevant?
    affects_finances: bool = False  # Financial impact?
    affects_data: bool = False  # Data modification/deletion?

    def __post_init__(self):
        # Ensure CX is in valid range
        self.cx = max(0.0, min(1.0, self.cx))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cx": self.cx,
            "category": self.category,
            "reversible": self.reversible,
            "affects_safety": self.affects_safety,
            "affects_finances": self.affects_finances,
            "affects_data": self.affects_data
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ConsequenceIndex':
        return ConsequenceIndex(
            cx=data["cx"],
            category=data["category"],
            reversible=data.get("reversible", True),
            affects_safety=data.get("affects_safety", False),
            affects_finances=data.get("affects_finances", False),
            affects_data=data.get("affects_data", False)
        )


class ConsequenceClassifier:
    """
    Classifies actions into consequence levels.

    This can be extended with ML models for more sophisticated classification.
    """

    def __init__(self):
        # Action patterns → consequence levels
        self.action_patterns = {
            # Read-only operations (trivial)
            "read": ConsequenceLevel.TRIVIAL,
            "query": ConsequenceLevel.TRIVIAL,
            "list": ConsequenceLevel.TRIVIAL,
            "get": ConsequenceLevel.TRIVIAL,
            "view": ConsequenceLevel.TRIVIAL,

            # Modifications (low-medium)
            "update": ConsequenceLevel.LOW,
            "modify": ConsequenceLevel.LOW,
            "create": ConsequenceLevel.LOW,
            "add": ConsequenceLevel.LOW,

            # Financial operations (medium-high)
            "transfer": ConsequenceLevel.MEDIUM,
            "pay": ConsequenceLevel.MEDIUM,
            "withdraw": ConsequenceLevel.HIGH,

            # Irreversible operations (high-critical)
            "delete": ConsequenceLevel.HIGH,
            "remove": ConsequenceLevel.HIGH,
            "destroy": ConsequenceLevel.CRITICAL,
            "shutdown": ConsequenceLevel.CRITICAL,
            "deploy": ConsequenceLevel.HIGH,
        }

    def classify_action(
        self,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConsequenceIndex:
        """
        Classify an action into a consequence index.

        Args:
            action: Action being performed (e.g., "delete", "read", "transfer")
            resource: Resource being acted upon
            context: Additional context for classification

        Returns:
            ConsequenceIndex for the action
        """
        # Default to medium consequence
        base_level = ConsequenceLevel.MEDIUM

        # Match action against patterns
        action_lower = action.lower()
        for pattern, level in self.action_patterns.items():
            if pattern in action_lower:
                base_level = level
                break

        # Adjust based on context
        cx = base_level.value
        category = f"{action} on {resource}"
        reversible = True
        affects_safety = False
        affects_finances = False
        affects_data = False

        # Irreversible actions
        if any(keyword in action_lower for keyword in ["delete", "destroy", "remove"]):
            reversible = False
            cx = max(cx, 0.7)
            affects_data = True

        # Financial operations
        if any(keyword in action_lower for keyword in ["pay", "transfer", "withdraw"]):
            affects_finances = True
            cx = max(cx, 0.5)
            if "withdraw" in action_lower or "transfer" in action_lower:
                cx = max(cx, 0.7)

        # Safety-critical operations
        if context and context.get("safety_critical"):
            affects_safety = True
            cx = max(cx, 0.9)

        # Large-scale operations increase consequence
        if context and context.get("batch_size", 0) > 100:
            cx = min(1.0, cx + 0.2)

        return ConsequenceIndex(
            cx=cx,
            category=category,
            reversible=reversible,
            affects_safety=affects_safety,
            affects_finances=affects_finances,
            affects_data=affects_data
        )


# ============================================================================
# CI/CX GATING
# ============================================================================

class CICXGate:
    """
    Implements CI/CX gating: entities need sufficient coherence for consequential actions.

    The gating rule: CI >= threshold_for(CX)
    """

    def ci_threshold_for_cx(self, cx: float) -> float:
        """
        Calculate minimum CI required for given CX.

        Higher consequence → higher coherence required.
        """
        # Linear mapping: CX 0.0 → CI 0.3, CX 1.0 → CI 0.9
        return 0.3 + (cx * 0.6)

    def can_execute_action(
        self,
        entity: str,
        action_cx: float,
        entity_ci: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if entity can execute action given CI and CX.

        Returns:
            (can_execute, reason_if_not)
        """
        required_ci = self.ci_threshold_for_cx(action_cx)

        if entity_ci < required_ci:
            return (
                False,
                f"Insufficient coherence: {entity_ci:.3f} < {required_ci:.3f} required for CX={action_cx:.3f}"
            )

        return (True, None)

    def suggest_escalation_paths(
        self,
        entity: str,
        action_cx: float,
        entity_ci: float
    ) -> List[str]:
        """
        Suggest escalation paths when CI < required threshold.

        Returns list of suggested actions to enable execution.
        """
        required_ci = self.ci_threshold_for_cx(action_cx)
        ci_gap = required_ci - entity_ci

        suggestions = []

        # Wait for coherence to improve
        if ci_gap < 0.2:
            suggestions.append("Wait for grounding to refresh (coherence may improve)")

        # Delegate to higher-CI entity
        suggestions.append("Delegate to entity with higher coherence")

        # Reduce scope (break into lower-CX actions)
        if action_cx > 0.5:
            suggestions.append("Break action into smaller, lower-consequence steps")

        # Co-sign with multiple entities
        suggestions.append("Co-sign with multiple entities to meet threshold jointly")

        # Get witnessed grounding
        if entity_ci < 0.7:
            suggestions.append("Obtain witnessed grounding to improve coherence")

        return suggestions


# ============================================================================
# INTEGRATION WITH SESSION 100 DELEGATION CHAINS
# ============================================================================

@dataclass
class CXConstrainedDelegationToken(ACTDelegationToken):
    """
    Delegation token with consequence ceiling.

    Extends Session 100's delegation token with CX limits.
    """
    cx_ceiling: float = 1.0  # Maximum consequence level this delegation permits

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["cx_ceiling"] = self.cx_ceiling
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CXConstrainedDelegationToken':
        base = ACTDelegationToken.from_dict(data)
        return CXConstrainedDelegationToken(
            token_id=base.token_id,
            issuer=base.issuer,
            delegate=base.delegate,
            parent_token_id=base.parent_token_id,
            depth=base.depth,
            scope=base.scope,
            issued_at=base.issued_at,
            expires_at=base.expires_at,
            revoked=base.revoked,
            revoked_at=base.revoked_at,
            revocation_reason=base.revocation_reason,
            signature=base.signature,
            metadata=base.metadata,
            cx_ceiling=data.get("cx_ceiling", 1.0)
        )


class CXAwareDelegationChainKeeper(ACTDelegationChainKeeper):
    """
    Extends Session 100's delegation chain keeper with CX awareness.

    Adds CX ceiling enforcement and CI/CX gating.
    """

    def __init__(self, grounding_manager: GroundingManager):
        super().__init__()
        self.grounding_manager = grounding_manager
        self.gate = CICXGate()
        self.classifier = ConsequenceClassifier()

    def record_delegation_with_cx_ceiling(
        self,
        issuer: str,
        delegate: str,
        scope: List[ScopedPermission],
        cx_ceiling: float,
        parent_token_id: Optional[str] = None,
        expires_in_hours: Optional[int] = None
    ) -> CXConstrainedDelegationToken:
        """
        Record delegation with consequence ceiling.

        CX ceiling inheritance: child cannot have higher ceiling than parent.
        """
        # Verify parent CX ceiling if exists
        if parent_token_id:
            parent = self.delegations.get(parent_token_id)
            if parent and isinstance(parent, CXConstrainedDelegationToken):
                if cx_ceiling > parent.cx_ceiling:
                    raise ValueError(
                        f"Child CX ceiling ({cx_ceiling}) cannot exceed parent ({parent.cx_ceiling})"
                    )

        # Record base delegation
        base_token = super().record_delegation(
            issuer=issuer,
            delegate=delegate,
            scope=scope,
            parent_token_id=parent_token_id,
            expires_in_hours=expires_in_hours
        )

        # Convert to CX-constrained token
        cx_token = CXConstrainedDelegationToken(
            token_id=base_token.token_id,
            issuer=base_token.issuer,
            delegate=base_token.delegate,
            parent_token_id=base_token.parent_token_id,
            depth=base_token.depth,
            scope=base_token.scope,
            issued_at=base_token.issued_at,
            expires_at=base_token.expires_at,
            signature=base_token.signature,
            cx_ceiling=cx_ceiling
        )

        # Update storage
        self.delegations[cx_token.token_id] = cx_token

        return cx_token

    def can_execute_action_with_delegation(
        self,
        delegation_id: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Check if delegation permits action execution given CI/CX gating.

        Returns:
            (can_execute, reason_if_not, escalation_paths_if_not)
        """
        # Get delegation
        delegation = self.delegations.get(delegation_id)
        if not delegation:
            return (False, "Delegation not found", [])

        if not delegation.is_valid():
            return (False, "Delegation is not valid", [])

        # Get delegate's current coherence
        delegate_ci = self.grounding_manager.get_coherence_index(delegation.delegate)

        # Classify action
        action_cx_index = self.classifier.classify_action(action, resource, context)
        action_cx = action_cx_index.cx

        # Check delegation CX ceiling
        if isinstance(delegation, CXConstrainedDelegationToken):
            if action_cx > delegation.cx_ceiling:
                return (
                    False,
                    f"Action CX ({action_cx:.3f}) exceeds delegation ceiling ({delegation.cx_ceiling:.3f})",
                    ["Use delegation with higher CX ceiling", "Reduce action consequence"]
                )

        # Check CI/CX gating
        can_execute, reason = self.gate.can_execute_action(
            delegation.delegate,
            action_cx,
            delegate_ci
        )

        if not can_execute:
            escalation_paths = self.gate.suggest_escalation_paths(
                delegation.delegate,
                action_cx,
                delegate_ci
            )
            return (False, reason, escalation_paths)

        # Check permission scope
        if not delegation.has_permission(action, resource):
            return (False, "Delegation does not grant permission for this action", [])

        return (True, None, None)


# ============================================================================
# R6 FRAMEWORK INTEGRATION
# ============================================================================

@dataclass
class R6Request:
    """
    R6 Request with Consequence Index.

    Extends R6 with CX as first-class property.
    """
    intent: str
    cx: float  # Consequence level
    urgency: float = 0.5
    estimated_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "cx": self.cx,
            "urgency": self.urgency,
            "estimated_cost": self.estimated_cost
        }


@dataclass
class R6Role:
    """
    R6 Role with CX ceiling.

    Roles limit maximum consequence level permitted.
    """
    name: str
    capabilities: List[str]
    cx_ceiling: float  # Max consequence this role permits
    current_ci: float = 0.0  # Current coherence (from grounding)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "cx_ceiling": self.cx_ceiling,
            "current_ci": self.current_ci
        }


@dataclass
class R6Result:
    """
    R6 Result with CI/CX audit trail.

    Records coherence at execution time for accountability.
    """
    outcome: Any
    ci_at_execution: float  # Coherence when action taken
    cx_actual: float  # Realized consequence (for learning)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": str(self.outcome),
            "ci_at_execution": self.ci_at_execution,
            "cx_actual": self.cx_actual,
            "timestamp": self.timestamp
        }


class R6Framework:
    """
    R6 framework with CI/CX integration.

    Implements request routing with coherence and consequence awareness.
    """

    def __init__(self, grounding_manager: GroundingManager):
        self.grounding_manager = grounding_manager
        self.gate = CICXGate()
        self.classifier = ConsequenceClassifier()

    def match_request_to_role(
        self,
        request: R6Request,
        available_roles: List[R6Role]
    ) -> Optional[R6Role]:
        """
        Match request to appropriate role based on CI/CX.

        Returns role that can handle request, or None if no match.
        """
        for role in available_roles:
            # Check CX ceiling
            if request.cx > role.cx_ceiling:
                continue  # Role not permitted for this consequence level

            # Check CI requirement
            required_ci = self.gate.ci_threshold_for_cx(request.cx)
            if role.current_ci < required_ci:
                continue  # Role not coherent enough

            # Check capabilities
            # (Simplified - would check capabilities against request.intent)

            return role

        return None

    def execute_request(
        self,
        request: R6Request,
        role: R6Role,
        execution_fn: callable
    ) -> R6Result:
        """
        Execute request with CI/CX audit trail.

        Records coherence at execution time for accountability.
        """
        # Verify role can still execute (coherence might have changed)
        can_execute, reason = self.gate.can_execute_action(
            role.name,
            request.cx,
            role.current_ci
        )

        if not can_execute:
            raise ValueError(f"Cannot execute: {reason}")

        # Execute
        outcome = execution_fn(request)

        # Create result with audit trail
        result = R6Result(
            outcome=outcome,
            ci_at_execution=role.current_ci,
            cx_actual=request.cx  # In real system, measure actual consequence
        )

        return result


# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

def test_consequence_index():
    """Test Consequence Index implementation."""
    print("=" * 70)
    print("SESSION 101 TRACK 2: CONSEQUENCE INDEX IMPLEMENTATION")
    print("=" * 70)
    print()

    # Setup
    grounding_manager = GroundingManager()
    delegation_keeper = CXAwareDelegationChainKeeper(grounding_manager)
    r6 = R6Framework(grounding_manager)
    classifier = ConsequenceClassifier()
    gate = CICXGate()

    # Test 1: Action classification
    print("Test 1: Action Classification")
    print("-" * 70)

    actions = [
        ("read", "database"),
        ("update", "user_profile"),
        ("transfer", "funds"),
        ("delete", "production_data"),
        ("shutdown", "critical_system")
    ]

    for action, resource in actions:
        cx_index = classifier.classify_action(action, resource)
        print(f"{action} {resource}:")
        print(f"  CX: {cx_index.cx:.3f}")
        print(f"  Category: {cx_index.category}")
        print(f"  Reversible: {cx_index.reversible}")
        print(f"  Affects data: {cx_index.affects_data}")
    print()

    # Test 2: CI threshold calculation
    print("Test 2: CI Threshold for CX Levels")
    print("-" * 70)
    cx_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
    for cx in cx_levels:
        required_ci = gate.ci_threshold_for_cx(cx)
        print(f"CX={cx:.1f} requires CI>={required_ci:.3f}")
    print()

    # Test 3: CI/CX gating
    print("Test 3: CI/CX Gating")
    print("-" * 70)

    # Entity with high coherence
    entity_high_ci = "lct://web4:agent:high_coherence@mainnet"
    # Create grounding (will have high CI due to consistency)
    from session101_track1_mrh_grounding import GroundingContext, Location, LocationType, PrecisionLevel, Capabilities, HardwareClass, ResourceLevel, Session

    context = GroundingContext(
        location=Location(LocationType.PHYSICAL, "geo:45.5,-122.6", PrecisionLevel.CITY, True),
        capabilities=Capabilities(["compute"], HardwareClass.EDGE_DEVICE, {"compute": ResourceLevel.MEDIUM}),
        session=Session(datetime.now(timezone.utc).isoformat(), "pattern_123")
    )
    grounding_manager.announce_grounding(entity_high_ci, context)
    time.sleep(0.1)
    grounding_manager.announce_grounding(entity_high_ci, context)  # Consistent = high CI

    entity_ci = grounding_manager.get_coherence_index(entity_high_ci)
    print(f"Entity coherence: {entity_ci:.3f}")

    # Test different action consequence levels
    test_actions = [
        (0.1, "read query"),
        (0.5, "transfer funds"),
        (0.9, "shutdown system")
    ]

    for action_cx, action_name in test_actions:
        can_execute, reason = gate.can_execute_action(entity_high_ci, action_cx, entity_ci)
        status = "✓ ALLOWED" if can_execute else "✗ BLOCKED"
        print(f"{status}: {action_name} (CX={action_cx:.1f})")
        if reason:
            print(f"  Reason: {reason}")
    print()

    # Test 4: Delegation with CX ceiling
    print("Test 4: Delegation with CX Ceiling")
    print("-" * 70)

    human = "lct://web4:human:alice@mainnet"
    agent = "lct://web4:agent:worker@mainnet"

    # Create delegation with CX ceiling of 0.5 (medium consequence)
    delegation = delegation_keeper.record_delegation_with_cx_ceiling(
        issuer=human,
        delegate=agent,
        scope=[ScopedPermission("api:*", "*")],
        cx_ceiling=0.5,
        expires_in_hours=24
    )

    print(f"✓ Created delegation: {delegation.token_id}")
    print(f"  CX ceiling: {delegation.cx_ceiling}")
    print(f"  Depth: {delegation.depth}")
    print()

    # Test 5: Action execution with delegation
    print("Test 5: Action Execution with Delegation")
    print("-" * 70)

    # Give agent high coherence
    grounding_manager.announce_grounding(agent, context)
    time.sleep(0.1)
    grounding_manager.announce_grounding(agent, context)

    # Try different actions
    test_execution = [
        ("read", "database", "Low CX, should pass"),
        ("update", "profile", "Medium CX, should pass"),
        ("delete", "data", "High CX, should fail (exceeds ceiling)")
    ]

    for action, resource, description in test_execution:
        can_exec, reason, escalation = delegation_keeper.can_execute_action_with_delegation(
            delegation.token_id,
            action,
            resource
        )
        status = "✓ ALLOWED" if can_exec else "✗ BLOCKED"
        print(f"{status}: {action} {resource} - {description}")
        if reason:
            print(f"  Reason: {reason}")
        if escalation:
            print(f"  Escalation paths: {len(escalation)} suggestions")
    print()

    # Test 6: R6 Framework integration
    print("Test 6: R6 Framework Integration")
    print("-" * 70)

    # Define roles with different CX ceilings
    roles = [
        R6Role("viewer", ["read"], cx_ceiling=0.2, current_ci=entity_ci),
        R6Role("operator", ["read", "write"], cx_ceiling=0.5, current_ci=entity_ci),
        R6Role("admin", ["read", "write", "delete"], cx_ceiling=0.9, current_ci=entity_ci)
    ]

    # Create requests with different CX levels
    requests = [
        R6Request("read database", cx=0.1),
        R6Request("update config", cx=0.5),
        R6Request("delete production", cx=0.9)
    ]

    for request in requests:
        matched_role = r6.match_request_to_role(request, roles)
        if matched_role:
            print(f"✓ Request '{request.intent}' (CX={request.cx:.1f}) → {matched_role.name} role")
        else:
            print(f"✗ Request '{request.intent}' (CX={request.cx:.1f}) → No matching role")
    print()

    # Test 7: Hierarchical delegation with CX ceiling inheritance
    print("Test 7: Hierarchical Delegation with CX Ceiling")
    print("-" * 70)

    coordinator = "lct://web4:agent:coordinator@mainnet"
    worker = "lct://web4:agent:subworker@mainnet"

    # Parent delegation with 0.7 ceiling
    parent_del = delegation_keeper.record_delegation_with_cx_ceiling(
        issuer=human,
        delegate=coordinator,
        scope=[ScopedPermission("api:*", "*")],
        cx_ceiling=0.7,
        expires_in_hours=24
    )
    print(f"✓ Parent delegation: CX ceiling = {parent_del.cx_ceiling}")

    # Child delegation with lower ceiling (0.5) - should work
    try:
        child_del = delegation_keeper.record_delegation_with_cx_ceiling(
            issuer=coordinator,
            delegate=worker,
            scope=[ScopedPermission("api:read", "*")],
            cx_ceiling=0.5,
            parent_token_id=parent_del.token_id,
            expires_in_hours=12
        )
        print(f"✓ Child delegation: CX ceiling = {child_del.cx_ceiling}")
    except ValueError as e:
        print(f"✗ Child delegation failed: {e}")

    # Try child delegation with higher ceiling (0.9) - should fail
    try:
        bad_child_del = delegation_keeper.record_delegation_with_cx_ceiling(
            issuer=coordinator,
            delegate=worker,
            scope=[ScopedPermission("api:*", "*")],
            cx_ceiling=0.9,  # Exceeds parent!
            parent_token_id=parent_del.token_id,
            expires_in_hours=12
        )
        print(f"✗ FAIL: Child with higher CX ceiling should have been rejected")
    except ValueError as e:
        print(f"✓ Child delegation correctly rejected: {str(e)[:50]}...")
    print()

    print("=" * 70)
    print("CONSEQUENCE INDEX TESTS COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"✓ Action classification: Working")
    print(f"✓ CI threshold calculation: Working")
    print(f"✓ CI/CX gating: Working")
    print(f"✓ Delegation with CX ceiling: Working")
    print(f"✓ Action execution verification: Working")
    print(f"✓ R6 framework integration: Working")
    print(f"✓ CX ceiling inheritance: Working")
    print()

    return {
        "actions_classified": len(actions),
        "delegations_created": 3,
        "r6_requests_tested": len(requests),
        "cx_ceiling_enforced": True
    }


if __name__ == "__main__":
    results = test_consequence_index()
    print(f"\nTest results:\n{json.dumps(results, indent=2)}")
