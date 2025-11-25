"""
MRH (Markov Relevancy Horizons) Profile Utilities for Web4 Game Engine
Session #68: Integration of HRM MRH concepts into game simulation
Session #73: Extended with deltaQ (Quality) dimension

Based on HRM/sage/core/mrh_utils.py and HRM/sage/docs/WEB4_SAGE_INTEGRATION_ANALYSIS.md,
this module provides MRH profile inference and management for game events.

MRH Dimensions (4D):
- deltaR (Spatial): local | regional | global
- deltaT (Temporal): ephemeral | session | day | epoch
- deltaC (Complexity): simple | agent-scale | society-scale
- deltaQ (Quality): low | medium | high | critical [NEW in Session #73]

Quality Levels:
- low (0.5-0.7): Approximate, cached, best-effort
- medium (0.7-0.85): Validated, recent, reliable
- high (0.85-0.95): Multi-witness, cryptographically verified
- critical (0.95-1.0): Safety-critical, legal, financial
"""

from typing import Dict

# Canonical MRH profiles for different event types
MRH_PROFILES = {
    # Treasury Operations
    "treasury_spend": {
        "deltaR": "local",       # Within single society
        "deltaT": "session",     # Affects current session state
        "deltaC": "simple"       # Direct balance update
    },
    "treasury_deposit": {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "simple"
    },
    "treasury_transfer": {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "agent-scale"  # Requires tracking sender/receiver
    },

    # Role Operations
    "role_binding": {
        "deltaR": "local",
        "deltaT": "day",         # Roles persist beyond session
        "deltaC": "agent-scale"  # Affects agent capabilities
    },
    "role_revocation": {
        "deltaR": "local",
        "deltaT": "day",
        "deltaC": "agent-scale"
    },
    "role_pairing": {
        "deltaR": "local",
        "deltaT": "day",
        "deltaC": "agent-scale"
    },

    # Membership Operations
    "membership_grant": {
        "deltaR": "local",
        "deltaT": "epoch",       # Long-term membership
        "deltaC": "society-scale"  # Society composition changes
    },
    "membership_revocation": {
        "deltaR": "local",
        "deltaT": "epoch",
        "deltaC": "society-scale"
    },

    # Audit & Investigation
    "audit_request": {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "agent-scale"  # Requires reasoning about behavior
    },
    "audit_result": {
        "deltaR": "local",
        "deltaT": "day",         # Results persist
        "deltaC": "agent-scale"
    },

    # Policy Enforcement
    "policy_violation": {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "simple"       # Pattern detection
    },
    "trust_update": {
        "deltaR": "local",
        "deltaT": "day",
        "deltaC": "agent-scale"  # Reputation calculation
    },

    # Federation (Cross-Society)
    "federation_throttle": {
        "deltaR": "regional",    # Cross-society
        "deltaT": "session",
        "deltaC": "society-scale"
    },
    "quarantine_request": {
        "deltaR": "regional",
        "deltaT": "day",         # Isolation persists
        "deltaC": "society-scale"
    },
    "cross_society_audit": {
        "deltaR": "regional",
        "deltaT": "session",
        "deltaC": "society-scale"  # Multi-society coordination
    },

    # Blockchain Sealing
    "block_seal": {
        "deltaR": "local",
        "deltaT": "epoch",       # Immutable history
        "deltaC": "simple"       # Cryptographic hash
    },
}

def get_mrh_for_event_type(event_type: str) -> Dict[str, str]:
    """
    Get canonical MRH profile for an event type

    Args:
        event_type: Event type string (e.g., "treasury_spend")

    Returns:
        MRH profile dict with deltaR, deltaT, deltaC
        Falls back to default if event_type unknown
    """
    return MRH_PROFILES.get(event_type, {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "agent-scale"
    })

def infer_mrh_from_event(event: Dict) -> Dict[str, str]:
    """
    Infer MRH profile from an event dictionary

    Args:
        event: Event dict with 'type' and possibly 'mrh' fields

    Returns:
        MRH profile dict, using event's mrh if present,
        otherwise inferring from event type
    """
    # If event already has MRH, use it
    if "mrh" in event:
        return event["mrh"]

    # Infer from event type
    event_type = event.get("type", "unknown")
    return get_mrh_for_event_type(event_type)

def compute_mrh_similarity(mrh1: Dict[str, str], mrh2: Dict[str, str]) -> float:
    """
    Compute similarity score between two MRH profiles
    Based on HRM/sage/core/mrh_utils.py:compute_mrh_similarity()

    Args:
        mrh1: First MRH profile
        mrh2: Second MRH profile

    Returns:
        Similarity score from 0.0 (completely different) to 1.0 (identical)
    """
    matches = 0
    total = 0

    for dim in ['deltaR', 'deltaT', 'deltaC']:
        if dim in mrh1 and dim in mrh2:
            if mrh1[dim] == mrh2[dim]:
                matches += 1
            total += 1

    return matches / total if total > 0 else 0.0

def is_cross_society_event(event: Dict) -> bool:
    """Check if event involves cross-society coordination"""
    mrh = infer_mrh_from_event(event)
    return mrh.get("deltaR") in ["regional", "global"]

def is_long_term_event(event: Dict) -> bool:
    """Check if event has long-term (day or epoch) temporal extent"""
    mrh = infer_mrh_from_event(event)
    return mrh.get("deltaT") in ["day", "epoch"]

def is_complex_event(event: Dict) -> bool:
    """Check if event requires agent-scale or society-scale complexity"""
    mrh = infer_mrh_from_event(event)
    return mrh.get("deltaC") in ["agent-scale", "society-scale"]

def filter_events_by_mrh(events: list, target_mrh: Dict[str, str],
                         min_similarity: float = 0.67) -> list:
    """
    Filter events by MRH similarity to target profile

    Args:
        events: List of event dicts
        target_mrh: Target MRH profile to match
        min_similarity: Minimum similarity score (0.0-1.0)

    Returns:
        List of events with similarity >= min_similarity
    """
    filtered = []
    for event in events:
        event_mrh = infer_mrh_from_event(event)
        similarity = compute_mrh_similarity(event_mrh, target_mrh)
        if similarity >= min_similarity:
            filtered.append(event)
    return filtered

def get_mrh_for_situation(*,
                          spatial_scope: str = "local",
                          temporal_scope: str = "session",
                          complexity: str = "agent-scale",
                          quality_level: str = "medium") -> Dict[str, str]:
    """
    Construct MRH profile for a specific situation (4D with quality)

    Args:
        spatial_scope: "local" | "regional" | "global"
        temporal_scope: "ephemeral" | "session" | "day" | "epoch"
        complexity: "simple" | "agent-scale" | "society-scale"
        quality_level: "low" | "medium" | "high" | "critical" [NEW in Session #73]

    Returns:
        MRH profile dict (now includes deltaQ)

    Example:
        >>> get_mrh_for_situation(
        ...     spatial_scope="local",
        ...     temporal_scope="session",
        ...     complexity="agent-scale",
        ...     quality_level="high"
        ... )
        {'deltaR': 'local', 'deltaT': 'session', 'deltaC': 'agent-scale', 'deltaQ': 'high'}
    """
    return {
        "deltaR": spatial_scope,
        "deltaT": temporal_scope,
        "deltaC": complexity,
        "deltaQ": quality_level
    }

# ATP Cost Models by MRH Profile (based on HRM experiments)
# Base costs without quality multiplier
ATP_COSTS_BASE = {
    ("local", "ephemeral", "simple"): 0,      # Pattern matching (pre-cached)
    ("local", "session", "simple"): 5,         # Simple state update
    ("local", "session", "agent-scale"): 15,   # Agent reasoning
    ("local", "day", "agent-scale"): 20,       # Persistent agent state
    ("local", "day", "society-scale"): 30,     # Society-level decision
    ("regional", "session", "society-scale"): 50,  # Cross-society coordination
    ("regional", "day", "society-scale"): 75,  # Cross-society persistent state
    ("global", "session", "agent-scale"): 100, # Global network call
}

# Quality multipliers (Session #73: HRM quality-aware integration)
# Based on HRM experiment showing 7x ATP cost for 100% quality compliance
QUALITY_MULTIPLIERS = {
    "low": 1.0,      # Best-effort, cached, approximate
    "medium": 1.5,   # Validated, recent, reliable
    "high": 2.0,     # Multi-witness, verified
    "critical": 3.0  # Safety-critical, cryptographic proof
}

def quality_level_to_veracity(quality_level: str) -> float:
    """
    Convert quality level to V3 veracity threshold

    Args:
        quality_level: "low" | "medium" | "high" | "critical"

    Returns:
        Minimum V3 veracity required (0.0-1.0)
    """
    return {
        "low": 0.60,
        "medium": 0.75,
        "high": 0.90,
        "critical": 0.95
    }.get(quality_level, 0.75)  # Default: medium

def veracity_to_quality_level(veracity: float) -> str:
    """
    Convert V3 veracity to quality level

    Args:
        veracity: V3 veracity score (0.0-1.0)

    Returns:
        Quality level string
    """
    if veracity >= 0.95:
        return "critical"
    elif veracity >= 0.90:
        return "high"
    elif veracity >= 0.75:
        return "medium"
    else:
        return "low"

def estimate_atp_cost(mrh: Dict[str, str], include_quality: bool = True) -> float:
    """
    Estimate ATP cost for an operation with given MRH profile

    Session #73: Extended to include quality multiplier
    Based on HRM ATP cost models and quality-aware selection experiment

    Args:
        mrh: MRH profile dict (may include deltaQ)
        include_quality: Whether to apply quality multiplier (default True)

    Returns:
        Estimated ATP cost

    Example:
        >>> mrh = {"deltaR": "local", "deltaT": "session", "deltaC": "agent-scale", "deltaQ": "high"}
        >>> estimate_atp_cost(mrh)
        30.0  # Base cost 15 * quality multiplier 2.0
    """
    # Get base cost from 3D MRH (spatial, temporal, complexity)
    key = (mrh.get("deltaR"), mrh.get("deltaT"), mrh.get("deltaC"))
    base_cost = ATP_COSTS_BASE.get(key, 10.0)  # Default: 10 ATP

    # Apply quality multiplier if deltaQ present
    if include_quality and "deltaQ" in mrh:
        quality_level = mrh["deltaQ"]
        multiplier = QUALITY_MULTIPLIERS.get(quality_level, 1.0)
        return base_cost * multiplier

    return base_cost

# Example Usage and Tests
if __name__ == "__main__":
    print("=" * 80)
    print("MRH Profile Examples (4D with Quality)")
    print("=" * 80)
    print()

    # Example 1: Treasury spend (backward compatible - no quality)
    treasury_mrh = get_mrh_for_event_type("treasury_spend")
    print(f"Treasury Spend (3D): {treasury_mrh}")
    print(f"  Cost: {estimate_atp_cost(treasury_mrh, include_quality=False)} ATP (no quality)")
    print()

    # Example 2: 4D MRH with quality levels
    print("4D MRH with Quality Levels:")
    for quality in ["low", "medium", "high", "critical"]:
        mrh = get_mrh_for_situation(
            spatial_scope="local",
            temporal_scope="session",
            complexity="agent-scale",
            quality_level=quality
        )
        cost = estimate_atp_cost(mrh)
        veracity = quality_level_to_veracity(quality)
        print(f"  {quality:8s} (V3≥{veracity:.2f}): {mrh} → {cost:5.1f} ATP")
    print()

    # Example 3: Quality multiplier impact
    print("Quality Multiplier Impact on Insurance Claim:")
    base_mrh = {"deltaR": "local", "deltaT": "session", "deltaC": "agent-scale"}
    base_cost = estimate_atp_cost(base_mrh, include_quality=False)
    print(f"  Base cost (no quality): {base_cost} ATP")

    for quality in ["low", "medium", "high", "critical"]:
        mrh_with_q = {**base_mrh, "deltaQ": quality}
        cost = estimate_atp_cost(mrh_with_q)
        multiplier = QUALITY_MULTIPLIERS[quality]
        print(f"  {quality:8s} quality: {cost:5.1f} ATP ({multiplier}x multiplier)")
    print()

    # Example 4: Veracity ↔ Quality Level conversion
    print("Veracity ↔ Quality Level Conversion:")
    for veracity in [0.55, 0.70, 0.80, 0.92, 0.97]:
        quality = veracity_to_quality_level(veracity)
        print(f"  V3 veracity {veracity:.2f} → {quality:8s} quality")
    print()

    # Example 5: MRH similarity (still 3D-based)
    print("MRH Similarity (3D dimensions only):")
    mrh1 = {"deltaR": "local", "deltaT": "session", "deltaC": "simple"}
    mrh2 = {"deltaR": "local", "deltaT": "session", "deltaC": "agent-scale"}
    similarity = compute_mrh_similarity(mrh1, mrh2)
    print(f"  {mrh1}")
    print(f"  {mrh2}")
    print(f"  Similarity: {similarity:.2f}")
    print()

    # Example 6: Critical operation cost comparison
    print("Cost Comparison: Routine vs Critical Operation:")
    routine = get_mrh_for_situation(
        spatial_scope="local",
        temporal_scope="session",
        complexity="simple",
        quality_level="low"
    )
    critical = get_mrh_for_situation(
        spatial_scope="local",
        temporal_scope="session",
        complexity="agent-scale",
        quality_level="critical"
    )
    print(f"  Routine (event_logging): {estimate_atp_cost(routine):.1f} ATP")
    print(f"  Critical (insurance_claim): {estimate_atp_cost(critical):.1f} ATP")
    print(f"  Ratio: {estimate_atp_cost(critical) / estimate_atp_cost(routine):.1f}x")
    print()

    print("=" * 80)
    print("✓ All examples complete")
    print("=" * 80)
