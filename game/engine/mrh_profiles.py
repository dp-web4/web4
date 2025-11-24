"""
MRH (Markov Relevancy Horizons) Profile Utilities for Web4 Game Engine
Session #68: Integration of HRM MRH concepts into game simulation

Based on HRM/sage/core/mrh_utils.py and HRM/sage/docs/WEB4_SAGE_INTEGRATION_ANALYSIS.md,
this module provides MRH profile inference and management for game events.

MRH Dimensions:
- deltaR (Spatial): local | regional | global
- deltaT (Temporal): ephemeral | session | day | epoch
- deltaC (Complexity): simple | agent-scale | society-scale
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
                          complexity: str = "agent-scale") -> Dict[str, str]:
    """
    Construct MRH profile for a specific situation

    Args:
        spatial_scope: "local" | "regional" | "global"
        temporal_scope: "ephemeral" | "session" | "day" | "epoch"
        complexity: "simple" | "agent-scale" | "society-scale"

    Returns:
        MRH profile dict
    """
    return {
        "deltaR": spatial_scope,
        "deltaT": temporal_scope,
        "deltaC": complexity
    }

# ATP Cost Models by MRH Profile (based on HRM experiments)
ATP_COSTS = {
    ("local", "ephemeral", "simple"): 0,      # Pattern matching (pre-cached)
    ("local", "session", "simple"): 5,         # Simple state update
    ("local", "session", "agent-scale"): 15,   # Agent reasoning
    ("local", "day", "agent-scale"): 20,       # Persistent agent state
    ("local", "day", "society-scale"): 30,     # Society-level decision
    ("regional", "session", "society-scale"): 50,  # Cross-society coordination
    ("regional", "day", "society-scale"): 75,  # Cross-society persistent state
    ("global", "session", "agent-scale"): 100, # Global network call
}

def estimate_atp_cost(mrh: Dict[str, str]) -> float:
    """
    Estimate ATP cost for an operation with given MRH profile
    Based on HRM ATP cost models

    Args:
        mrh: MRH profile dict

    Returns:
        Estimated ATP cost
    """
    key = (mrh.get("deltaR"), mrh.get("deltaT"), mrh.get("deltaC"))
    return ATP_COSTS.get(key, 10.0)  # Default: 10 ATP

# Example Usage and Tests
if __name__ == "__main__":
    print("MRH Profile Examples:")
    print("-" * 80)

    # Example 1: Treasury spend
    treasury_mrh = get_mrh_for_event_type("treasury_spend")
    print(f"Treasury Spend: {treasury_mrh}")
    print(f"  Cost: {estimate_atp_cost(treasury_mrh)} ATP")

    # Example 2: Audit request
    audit_mrh = get_mrh_for_event_type("audit_request")
    print(f"Audit Request: {audit_mrh}")
    print(f"  Cost: {estimate_atp_cost(audit_mrh)} ATP")

    # Example 3: Cross-society throttle
    throttle_mrh = get_mrh_for_event_type("federation_throttle")
    print(f"Federation Throttle: {throttle_mrh}")
    print(f"  Cost: {estimate_atp_cost(throttle_mrh)} ATP")

    # Example 4: MRH similarity
    mrh1 = {"deltaR": "local", "deltaT": "session", "deltaC": "simple"}
    mrh2 = {"deltaR": "local", "deltaT": "session", "deltaC": "agent-scale"}
    similarity = compute_mrh_similarity(mrh1, mrh2)
    print(f"\nSimilarity between {mrh1} and {mrh2}: {similarity:.2f}")

    # Example 5: Event filtering
    events = [
        {"type": "treasury_spend", "amount": 100},
        {"type": "audit_request", "auditor": "sage"},
        {"type": "treasury_deposit", "amount": 50},
    ]
    target = {"deltaR": "local", "deltaT": "session", "deltaC": "simple"}
    filtered = filter_events_by_mrh(events, target, min_similarity=1.0)
    print(f"\nFiltered events (exact match to {target}):")
    for e in filtered:
        print(f"  - {e['type']}")
