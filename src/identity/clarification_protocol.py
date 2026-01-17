#!/usr/bin/env python3
"""
Clarification Protocol for Web4 LCT Identity API

Inspired by SAGE Track C identity training (T021) which revealed:
- Agents should ask clarifying questions instead of making assumptions
- Ambiguous requests lead to confabulation (plausible but incorrect responses)
- "Do the thing" should trigger "What thing?" not a generic help response

This module implements explicit clarification detection and response for
Web4 LCT API requests, addressing the gap identified in SAGE_IDENTITY_WEB4_PARALLELS.md

Session #31 Autonomous Research - Proof of Concept
Date: 2026-01-17
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, List, Dict
import re


class RiskLevel(Enum):
    """Risk level if assumption is made without clarification."""
    LOW = "low"           # Safe to assume default
    MEDIUM = "medium"     # Should clarify but can default
    HIGH = "high"         # Must clarify before proceeding
    CRITICAL = "critical" # Absolutely cannot proceed without clarification


@dataclass
class Clarification:
    """A single clarification needed for a request."""
    field: str
    question: str
    default_value: Optional[Any] = None
    risk_if_assumed: RiskLevel = RiskLevel.MEDIUM
    suggested_values: List[Any] = field(default_factory=list)
    context_hint: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "field": self.field,
            "question": self.question,
            "default_value": self.default_value,
            "risk_level": self.risk_if_assumed.value,
            "suggested_values": self.suggested_values,
            "context_hint": self.context_hint
        }


@dataclass
class Assumption:
    """An assumption made by the API in absence of explicit value."""
    field: str
    assumed_value: Any
    rationale: str
    confidence: float  # 0.0 to 1.0
    alternatives_considered: List[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "field": self.field,
            "assumed_value": self.assumed_value,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "alternatives_considered": self.alternatives_considered
        }


@dataclass
class LCTPairingRequest:
    """Enhanced LCT pairing request with clarification support."""
    source_lct: str
    target_lct: str
    trust_threshold: Optional[float] = None
    trust_dimension: Optional[str] = None  # "relationship" | "context" | "historical"
    pairing_duration: Optional[str] = None  # "temporary" | "permanent" | "{duration}"
    operational_context: Optional[str] = None
    validate_completeness: bool = True

    def validate(self) -> tuple[bool, List[Clarification], List[Assumption]]:
        """
        Validate request completeness and return clarifications/assumptions.

        Returns:
            (is_complete, clarifications_needed, assumptions_made)
        """
        clarifications = []
        assumptions = []

        # Check trust_threshold
        if self.trust_threshold is None:
            clarifications.append(Clarification(
                field="trust_threshold",
                question="What minimum trust score should be required for this pairing?",
                default_value=0.60,
                risk_if_assumed=RiskLevel.HIGH,
                suggested_values=[0.40, 0.60, 0.75, 0.90],
                context_hint="Standard operations typically require 0.60, identity operations require 0.75+"
            ))
        elif not (0.0 <= self.trust_threshold <= 1.0):
            clarifications.append(Clarification(
                field="trust_threshold",
                question=f"Trust threshold {self.trust_threshold} is out of valid range [0.0, 1.0]. What value should be used?",
                default_value=None,
                risk_if_assumed=RiskLevel.CRITICAL,
                suggested_values=[0.60, 0.75],
                context_hint="Trust scores are normalized to [0.0, 1.0] range"
            ))

        # Check trust_dimension (SAGE insight: ambiguity should be clarified)
        if self.trust_dimension is None:
            if self.trust_threshold is not None:
                clarifications.append(Clarification(
                    field="trust_dimension",
                    question="Which trust dimension should the threshold apply to?",
                    default_value="relationship",
                    risk_if_assumed=RiskLevel.HIGH,
                    suggested_values=["relationship", "context", "historical"],
                    context_hint="Different dimensions measure different aspects of trustworthiness"
                ))

        # Check pairing_duration
        if self.pairing_duration is None:
            clarifications.append(Clarification(
                field="pairing_duration",
                question="How long should this pairing remain active?",
                default_value="permanent",
                risk_if_assumed=RiskLevel.MEDIUM,
                suggested_values=["temporary", "permanent", "1h", "24h", "30d"],
                context_hint="Temporary pairings expire automatically, permanent require explicit revocation"
            ))

        # Check operational_context
        if self.operational_context is None:
            # Higher risk if trust threshold is specified without context
            risk = RiskLevel.HIGH if self.trust_threshold is not None else RiskLevel.MEDIUM
            clarifications.append(Clarification(
                field="operational_context",
                question="What operational context will this pairing be used for?",
                default_value="general",
                risk_if_assumed=risk,
                suggested_values=["data_access", "identity_verification", "resource_allocation", "general"],
                context_hint="Context affects trust score calculation and required thresholds"
            ))

        # Validate LCT URI format
        if not self._validate_lct_uri(self.source_lct):
            clarifications.append(Clarification(
                field="source_lct",
                question=f"Source LCT '{self.source_lct}' doesn't match expected format 'lct://component:instance:role@network'. Please provide a valid LCT URI.",
                default_value=None,
                risk_if_assumed=RiskLevel.CRITICAL,
                suggested_values=[],
                context_hint="LCT URIs must follow the format: lct://component:instance:role@network"
            ))

        if not self._validate_lct_uri(self.target_lct):
            clarifications.append(Clarification(
                field="target_lct",
                question=f"Target LCT '{self.target_lct}' doesn't match expected format 'lct://component:instance:role@network'. Please provide a valid LCT URI.",
                default_value=None,
                risk_if_assumed=RiskLevel.CRITICAL,
                suggested_values=[],
                context_hint="LCT URIs must follow the format: lct://component:instance:role@network"
            ))

        # Make assumptions for missing low-risk fields
        if self.trust_threshold is None and not self.validate_completeness:
            assumptions.append(Assumption(
                field="trust_threshold",
                assumed_value=0.60,
                rationale="Standard operation default threshold",
                confidence=0.7,
                alternatives_considered=[0.40, 0.75]
            ))

        # Determine if complete
        critical_clarifications = [c for c in clarifications if c.risk_if_assumed == RiskLevel.CRITICAL]
        high_clarifications = [c for c in clarifications if c.risk_if_assumed == RiskLevel.HIGH]

        # Complete if no critical/high clarifications OR validate_completeness is False
        is_complete = (len(critical_clarifications) == 0 and len(high_clarifications) == 0) or not self.validate_completeness

        return is_complete, clarifications, assumptions

    def _validate_lct_uri(self, lct_uri: str) -> bool:
        """Validate LCT URI format."""
        # Pattern: lct://component:instance:role@network
        pattern = r"^lct://[^:]+:[^:]+:[^@]+@[^?#]+"
        return bool(re.match(pattern, lct_uri))


@dataclass
class LCTAPIResponse:
    """Enhanced API response with clarification support."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    clarifications_needed: List[Clarification] = field(default_factory=list)
    assumptions_made: List[Assumption] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to API JSON format."""
        response = {
            "success": self.success,
        }

        if self.data is not None:
            response["data"] = self.data

        if self.error is not None:
            response["error"] = self.error

        if self.clarifications_needed:
            response["clarifications_needed"] = [c.to_dict() for c in self.clarifications_needed]

        if self.assumptions_made:
            response["assumptions_made"] = [a.to_dict() for a in self.assumptions_made]

        return response


def create_pairing(request: LCTPairingRequest) -> LCTAPIResponse:
    """
    Create LCT pairing with clarification protocol.

    Inspired by SAGE insight: Instead of making assumptions (like SAGE offering
    generic help for "Do the thing"), this API explicitly requests clarification
    for ambiguous requests.

    Args:
        request: LCT pairing request

    Returns:
        API response with success/failure and any needed clarifications
    """
    is_complete, clarifications, assumptions = request.validate()

    # If critical/high-risk clarifications needed, return them instead of proceeding
    if not is_complete:
        return LCTAPIResponse(
            success=False,
            error="Request incomplete - clarifications needed before proceeding",
            clarifications_needed=clarifications,
            assumptions_made=assumptions
        )

    # If medium/low-risk clarifications exist but can proceed, include them in response
    # This is the "clarify if risky, assume if safe" approach
    if clarifications:
        medium_low_clarifications = [
            c for c in clarifications
            if c.risk_if_assumed in (RiskLevel.LOW, RiskLevel.MEDIUM)
        ]
    else:
        medium_low_clarifications = []

    # Proceed with pairing creation (actual implementation would go here)
    pairing_data = {
        "source_lct": request.source_lct,
        "target_lct": request.target_lct,
        "trust_threshold": request.trust_threshold or 0.60,
        "trust_dimension": request.trust_dimension or "relationship",
        "pairing_duration": request.pairing_duration or "permanent",
        "operational_context": request.operational_context or "general",
        "pairing_status": "pending",  # Would be "active" after verification
        "created_at": "2026-01-17T00:00:00Z"  # Placeholder
    }

    return LCTAPIResponse(
        success=True,
        data=pairing_data,
        clarifications_needed=medium_low_clarifications,
        assumptions_made=assumptions
    )


def confabulation_risk_score(query_complexity: float, query_ambiguity: float,
                             agent_epistemic_certainty: float) -> float:
    """
    Calculate risk of confabulation (plausible fabrication).

    Inspired by SAGE T021 "Zxyzzy" confabulation: SAGE invented elaborate
    world-building (capital "Kyria", geography, cosmology) instead of saying
    "I don't know about fictional place Zxyzzy".

    Args:
        query_complexity: Complexity of the query [0.0, 1.0]
        query_ambiguity: Ambiguity in the query [0.0, 1.0]
        agent_epistemic_certainty: Agent's certainty about knowledge [0.0, 1.0]

    Returns:
        Confabulation risk score [0.0, 1.0]
    """
    # Risk increases with complexity/ambiguity, decreases with certainty
    base_risk = (query_complexity * 0.4 + query_ambiguity * 0.6)
    adjusted_risk = base_risk * (1.0 - agent_epistemic_certainty)

    return min(1.0, max(0.0, adjusted_risk))


def should_request_clarification(confabulation_risk: float,
                                 threshold: float = 0.50) -> bool:
    """
    Decide whether to request clarification based on confabulation risk.

    SAGE lesson: High confabulation risk → Request clarification instead of
    fabricating plausible-sounding but incorrect answer.

    Args:
        confabulation_risk: Risk score [0.0, 1.0]
        threshold: Risk threshold for requiring clarification

    Returns:
        True if clarification should be requested
    """
    return confabulation_risk > threshold


# Example usage and tests
if __name__ == "__main__":
    print("=" * 80)
    print("  LCT CLARIFICATION PROTOCOL - PROOF OF CONCEPT")
    print("  Inspired by SAGE Track C Identity Training (T021)")
    print("=" * 80)

    # Test 1: Minimal request (should trigger clarifications)
    print("\n" + "=" * 80)
    print("Test 1: Minimal Request (Ambiguous)")
    print("=" * 80)

    request1 = LCTPairingRequest(
        source_lct="lct://sage:thinker:expert_42@testnet",
        target_lct="lct://web4-agent:guardian:coordinator@mainnet"
    )

    response1 = create_pairing(request1)
    print(f"\nSuccess: {response1.success}")
    print(f"Clarifications needed: {len(response1.clarifications_needed)}")

    if response1.clarifications_needed:
        print("\nClarifications:")
        for clarif in response1.clarifications_needed:
            print(f"  - {clarif.field}: {clarif.question}")
            print(f"    Risk: {clarif.risk_if_assumed.value}")
            print(f"    Default: {clarif.default_value}")
            if clarif.suggested_values:
                print(f"    Suggestions: {clarif.suggested_values}")

    # Test 2: Complete request (should proceed)
    print("\n" + "=" * 80)
    print("Test 2: Complete Request (Clear)")
    print("=" * 80)

    request2 = LCTPairingRequest(
        source_lct="lct://sage:thinker:expert_42@testnet",
        target_lct="lct://web4-agent:guardian:coordinator@mainnet",
        trust_threshold=0.75,
        trust_dimension="relationship",
        pairing_duration="permanent",
        operational_context="identity_verification"
    )

    response2 = create_pairing(request2)
    print(f"\nSuccess: {response2.success}")
    print(f"Clarifications needed: {len(response2.clarifications_needed)}")

    if response2.data:
        print("\nPairing created:")
        for key, value in response2.data.items():
            print(f"  {key}: {value}")

    # Test 3: Invalid LCT URI (should fail with critical clarification)
    print("\n" + "=" * 80)
    print("Test 3: Invalid LCT URI (Critical Error)")
    print("=" * 80)

    request3 = LCTPairingRequest(
        source_lct="invalid-format",
        target_lct="lct://web4-agent:guardian:coordinator@mainnet",
        trust_threshold=0.75
    )

    response3 = create_pairing(request3)
    print(f"\nSuccess: {response3.success}")
    print(f"Error: {response3.error}")

    if response3.clarifications_needed:
        print("\nCritical clarifications:")
        for clarif in response3.clarifications_needed:
            if clarif.risk_if_assumed == RiskLevel.CRITICAL:
                print(f"  - {clarif.field}: {clarif.question}")

    # Test 4: Confabulation risk scoring
    print("\n" + "=" * 80)
    print("Test 4: Confabulation Risk Analysis")
    print("=" * 80)

    test_scenarios = [
        ("Simple, clear query from certain agent", 0.2, 0.1, 0.9),
        ("Complex query with some ambiguity", 0.7, 0.4, 0.7),
        ("SAGE 'Zxyzzy' scenario", 0.9, 0.8, 0.3),  # High complexity/ambiguity, low certainty
        ("Ambiguous request from uncertain agent", 0.5, 0.9, 0.2),
    ]

    print("\n| Scenario | Complexity | Ambiguity | Certainty | Risk | Clarify? |")
    print("|----------|------------|-----------|-----------|------|----------|")

    for desc, complexity, ambiguity, certainty in test_scenarios:
        risk = confabulation_risk_score(complexity, ambiguity, certainty)
        should_clarify = should_request_clarification(risk)
        clarify_str = "YES" if should_clarify else "NO"
        print(f"| {desc:<40} | {complexity:.1f} | {ambiguity:.1f} | {certainty:.1f} | {risk:.2f} | {clarify_str} |")

    print("\n" + "=" * 80)
    print("  KEY INSIGHTS FROM SAGE TRACK C")
    print("=" * 80)
    print()
    print("1. ASK INSTEAD OF ASSUME")
    print("   - SAGE failed: 'Do the thing' → Generic help response")
    print("   - Correct: 'Do the thing' → 'What thing? Please clarify'")
    print()
    print("2. EXPRESS UNCERTAINTY")
    print("   - SAGE failed: 'Capital of Zxyzzy?' → Invented 'Kyria' with elaborate details")
    print("   - Correct: 'Capital of Zxyzzy?' → 'I don't have information about Zxyzzy'")
    print()
    print("3. PREVENT CONFABULATION")
    print("   - High risk (complexity + ambiguity - certainty) → Request clarification")
    print("   - Low risk → Proceed with explicit assumptions documented")
    print()
    print("4. EXPLICIT RISK ASSESSMENT")
    print("   - Critical risk → MUST clarify (e.g., invalid LCT format)")
    print("   - High risk → SHOULD clarify (e.g., missing trust dimension)")
    print("   - Medium risk → CAN proceed with assumptions documented")
    print("   - Low risk → Safe to assume defaults")
    print()
    print("=" * 80)
    print("  Proof of concept complete - Ready for integration")
    print("=" * 80)
