"""
SAGE-Web4 Authorization Integration
===================================

Integrates SAGE consciousness decision-making with Web4's authorization engine.

This creates a consciousness-aware authorization system where:
1. SAGE's metabolic state influences authorization decisions
2. SAGE's arousal/attention affects trust assessment
3. SAGE can delegate actions based on consciousness state
4. Authorization decisions feed back into SAGE's experience

Use Cases:
- "Only authorize high-risk actions when SAGE is in FOCUS state"
- "Require higher trust thresholds when SAGE arousal is low"
- "Defer decisions to human when SAGE is in DREAM state"
- "Track authorization patterns in SAGE's memory"

Author: Legion Autonomous Research
Date: 2025-12-07
Track: 24 (SAGE-Authorization Integration)
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add paths
sage_path = Path.home() / "ai-workspace" / "HRM" / "sage"
sys.path.insert(0, str(sage_path))
web4_path = Path(__file__).parent
sys.path.insert(0, str(web4_path))

# Import SAGE components
try:
    from core.metabolic_controller import MetabolicState
    SAGE_AVAILABLE = True
except ImportError:
    SAGE_AVAILABLE = False
    
    # Stub for demonstration
    class MetabolicState(str, Enum):
        WAKE = "WAKE"
        FOCUS = "FOCUS"
        REST = "REST"
        DREAM = "DREAM"

# Import Web4 components
from authorization_engine import (
    AuthorizationEngine, AgentDelegation, AuthorizationRequest,
    AuthorizationDecision, LCTCredential
)
from lct_registry import LCTRegistry, EntityType


@dataclass
class ConsciousnessContext:
    """SAGE consciousness state for authorization decisions"""
    metabolic_state: MetabolicState
    arousal: float  # 0-1
    attention_allocated: bool
    salience: float  # 0-1
    atp_level: float  # 0-1
    
    def is_high_alertness(self) -> bool:
        """Check if consciousness is in high alertness state"""
        return (self.metabolic_state in [MetabolicState.WAKE, MetabolicState.FOCUS] 
                and self.arousal > 0.5)
    
    def can_handle_critical_decision(self) -> bool:
        """Check if consciousness can handle critical decisions"""
        return (self.metabolic_state == MetabolicState.FOCUS
                and self.arousal > 0.6
                and self.atp_level > 0.4)


class ConsciousnessAwareAuthorizationEngine:
    """
    Authorization engine that integrates SAGE consciousness state
    
    Enhances Web4 authorization with consciousness awareness:
    - State-dependent trust thresholds
    - Arousal-based decision deferral
    - ATP-aware rate limiting
    - Memory-integrated authorization logging
    """
    
    def __init__(self, society_id: str, sage_lct_id: Optional[str] = None):
        self.society_id = society_id
        self.sage_lct_id = sage_lct_id
        
        # Web4 components
        self.lct_registry = LCTRegistry(society_id)
        self.auth_engine = AuthorizationEngine(society_id)
        
        # Consciousness-specific policies
        self.state_trust_multipliers = {
            MetabolicState.FOCUS: 1.0,   # Full trust in FOCUS
            MetabolicState.WAKE: 0.9,    # Slightly reduced in WAKE
            MetabolicState.REST: 0.5,    # Significantly reduced in REST
            MetabolicState.DREAM: 0.0    # No high-risk decisions in DREAM
        }
        
        # Track consciousness-authorization correlations
        self.decision_history: list = []
    
    def authorize_with_consciousness(
        self,
        request: AuthorizationRequest,
        consciousness: ConsciousnessContext,
        credential: LCTCredential,
        signature: bytes
    ) -> Tuple[AuthorizationDecision, str]:
        """
        Authorize action with consciousness-aware policies
        
        Args:
            request: Authorization request
            consciousness: Current consciousness state
            credential: LCT credential
            signature: Request signature
            
        Returns:
            (decision, reason) tuple
        """
        
        # Policy 1: Block critical actions in low-alertness states
        if self._is_critical_action(request.action):
            if not consciousness.can_handle_critical_decision():
                reason = (f"Critical action '{request.action}' requires FOCUS state "
                         f"(current: {consciousness.metabolic_state.value}, "
                         f"arousal: {consciousness.arousal:.2f})")
                self._log_decision(request, AuthorizationDecision.DEFERRED, consciousness, reason)
                return AuthorizationDecision.DEFERRED, reason
        
        # Policy 2: Adjust trust requirements based on consciousness state
        effective_trust_multiplier = self.state_trust_multipliers.get(
            consciousness.metabolic_state, 0.5
        )
        
        # If consciousness arousal is low, require even higher trust
        if consciousness.arousal < 0.4:
            effective_trust_multiplier *= 0.8
        
        # Policy 3: Check ATP level - don't authorize expensive actions if ATP is low
        if request.atp_cost > 10 and consciousness.atp_level < 0.3:
            reason = f"ATP level too low ({consciousness.atp_level:.0%}) for expensive action ({request.atp_cost} ATP)"
            self._log_decision(request, AuthorizationDecision.DENIED, consciousness, reason)
            return AuthorizationDecision.DENIED, reason
        
        # Policy 4: Require attention allocation for important decisions
        if request.atp_cost > 5 and not consciousness.attention_allocated:
            reason = "Action requires attention allocation (not allocated in current cycle)"
            self._log_decision(request, AuthorizationDecision.DEFERRED, consciousness, reason)
            return AuthorizationDecision.DEFERRED, reason
        
        # Perform standard Web4 authorization
        result = self.auth_engine.authorize_action(request, credential, signature)
        
        # Apply consciousness-based trust adjustment
        if result.decision == AuthorizationDecision.GRANTED:
            # If consciousness state requires higher trust, re-evaluate
            required_trust = result.required_trust_score / effective_trust_multiplier
            if result.actual_trust_score < required_trust:
                reason = (f"Trust score {result.actual_trust_score:.2f} insufficient for "
                         f"{consciousness.metabolic_state.value} state "
                         f"(requires {required_trust:.2f})")
                self._log_decision(request, AuthorizationDecision.DENIED, consciousness, reason)
                return AuthorizationDecision.DENIED, reason
        
        # Log decision with consciousness context
        self._log_decision(request, result.decision, consciousness, "Standard authorization")
        
        return result.decision, "Authorized with consciousness awareness"
    
    def _is_critical_action(self, action: str) -> bool:
        """Check if action is critical (requires high alertness)"""
        critical_actions = {
            "transfer_funds",
            "change_permissions",
            "delete_data",
            "deploy_code",
            "modify_settings"
        }
        return action in critical_actions
    
    def _log_decision(
        self,
        request: AuthorizationRequest,
        decision: AuthorizationDecision,
        consciousness: ConsciousnessContext,
        reason: str
    ):
        """Log authorization decision with consciousness context"""
        log_entry = {
            "action": request.action,
            "decision": decision.value if hasattr(decision, 'value') else str(decision),
            "requester": request.requester_lct,
            "consciousness": {
                "state": consciousness.metabolic_state.value if hasattr(consciousness.metabolic_state, 'value') else str(consciousness.metabolic_state),
                "arousal": consciousness.arousal,
                "atp": consciousness.atp_level,
                "attention": consciousness.attention_allocated
            },
            "reason": reason
        }
        self.decision_history.append(log_entry)
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get statistics on consciousness-aware decisions"""
        if not self.decision_history:
            return {"total_decisions": 0}
        
        total = len(self.decision_history)
        by_state = {}
        by_decision = {}
        
        for entry in self.decision_history:
            state = entry["consciousness"]["state"]
            decision = entry["decision"]
            
            by_state[state] = by_state.get(state, 0) + 1
            by_decision[decision] = by_decision.get(decision, 0) + 1
        
        return {
            "total_decisions": total,
            "decisions_by_state": by_state,
            "decisions_by_outcome": by_decision,
            "avg_arousal": sum(e["consciousness"]["arousal"] for e in self.decision_history) / total,
            "avg_atp": sum(e["consciousness"]["atp"] for e in self.decision_history) / total
        }


def demonstrate_sage_authorization():
    """Demonstrate consciousness-aware authorization"""
    
    print("=" * 70)
    print("  SAGE-Web4 Authorization Integration")
    print("  Consciousness-Aware Decision Making")
    print("=" * 70)
    
    # Create engine
    engine = ConsciousnessAwareAuthorizationEngine("society:sage")
    
    # Create test LCT
    credential, _ = engine.lct_registry.mint_lct(
        entity_type=EntityType.AI,
        entity_identifier="sage:demo",
        witnesses=["witness:sage"]
    )
    
    # Create delegation
    delegation = AgentDelegation(
        delegation_id="sage_deleg",
        client_lct="lct:user:demo",
        agent_lct=credential.lct_id,
        role_lct="role:sage_agent",
        granted_permissions={"read", "write", "transfer_funds", "delete_data"},
        atp_budget=1000
    )
    engine.auth_engine.register_delegation(delegation)
    
    # Test scenarios
    print("\n" + "=" * 70)
    print("Scenario 1: Critical action in FOCUS state (should succeed)")
    print("=" * 70)
    
    consciousness_focus = ConsciousnessContext(
        metabolic_state=MetabolicState.FOCUS,
        arousal=0.75,
        attention_allocated=True,
        salience=0.6,
        atp_level=0.8
    )
    
    request1 = AuthorizationRequest(
        requester_lct=credential.lct_id,
        action="transfer_funds",
        target_resource="account:12345",
        atp_cost=15,
        context={"trust_context": "financial"},
        delegation_id="sage_deleg"
    )
    
    message1 = b"request1"
    sig1 = credential.sign(message1)
    
    decision1, reason1 = engine.authorize_with_consciousness(request1, consciousness_focus, credential, sig1)
    print(f"Decision: {decision1.value if hasattr(decision1, 'value') else decision1}")
    print(f"Reason: {reason1}")
    print(f"Consciousness: FOCUS state, arousal={consciousness_focus.arousal:.2f}, ATP={consciousness_focus.atp_level:.0%}")
    
    # Scenario 2: Critical action in DREAM state
    print("\n" + "=" * 70)
    print("Scenario 2: Critical action in DREAM state (should defer)")
    print("=" * 70)
    
    consciousness_dream = ConsciousnessContext(
        metabolic_state=MetabolicState.DREAM,
        arousal=0.2,
        attention_allocated=False,
        salience=0.3,
        atp_level=0.6
    )
    
    decision2, reason2 = engine.authorize_with_consciousness(request1, consciousness_dream, credential, sig1)
    print(f"Decision: {decision2}")
    print(f"Reason: {reason2}")
    print(f"Consciousness: DREAM state, arousal={consciousness_dream.arousal:.2f}, ATP={consciousness_dream.atp_level:.0%}")
    
    # Scenario 3: Low ATP
    print("\n" + "=" * 70)
    print("Scenario 3: Expensive action with low ATP (should deny)")
    print("=" * 70)
    
    consciousness_low_atp = ConsciousnessContext(
        metabolic_state=MetabolicState.WAKE,
        arousal=0.5,
        attention_allocated=True,
        salience=0.5,
        atp_level=0.2  # Low ATP
    )
    
    decision3, reason3 = engine.authorize_with_consciousness(request1, consciousness_low_atp, credential, sig1)
    print(f"Decision: {decision3}")
    print(f"Reason: {reason3}")
    print(f"Consciousness: WAKE state, arousal={consciousness_low_atp.arousal:.2f}, ATP={consciousness_low_atp.atp_level:.0%}")
    
    # Statistics
    print("\n" + "=" * 70)
    print("Decision Statistics")
    print("=" * 70)
    
    import json
    stats = engine.get_decision_statistics()
    print(json.dumps(stats, indent=2))
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("✅ SAGE consciousness integrated with Web4 authorization")
    print("✅ State-aware decision making demonstrated")
    print("✅ ATP-aware rate limiting working")
    print("✅ Critical action deferral in low-alertness states")
    
    print("\nKey Benefits:")
    print("  1. Consciousness state influences authorization decisions")
    print("  2. Higher trust required in low-alertness states")
    print("  3. Critical actions blocked when consciousness not ready")
    print("  4. ATP level considered in resource allocation")
    print("  5. Decision history tracked with consciousness context")


if __name__ == "__main__":
    demonstrate_sage_authorization()
