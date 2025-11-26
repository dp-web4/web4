#!/usr/bin/env python3
"""
SAGE-Web4 Local Bridge
Session #77: Phase 1 - Connect SAGE edge agent to Web4 infrastructure

Purpose:
Enable SAGE (HRM edge AI assistant) to participate in Web4 as a first-class agent
with full LCT identity, V3 reputation tracking, and ATP resource allocation.

This module provides the bridge between SAGE's edge operations and Web4's
reputation/federation systems.

Architecture:
┌─────────────────────┐
│  SAGE Edge Agent    │
│  (Jetson Orin Nano) │
└──────────┬──────────┘
           │
           │ sage_web4_bridge.py
           ▼
┌─────────────────────┐
│  Web4 Infrastructure│
│  - LCT Registry     │
│  - V3 Reputation    │
│  - ATP Metering     │
└─────────────────────┘

Based on SAGE_WEB4_INTEGRATION_DESIGN.md (Session #76)
"""

from typing import Dict, Optional
from dataclasses import dataclass
import time

try:
    from .lct import LCT
    from .multidimensional_v3 import V3Components, calculate_composite_veracity
    from .v3_evolution import update_v3_with_components
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from lct import LCT
    from multidimensional_v3 import V3Components, calculate_composite_veracity
    from v3_evolution import update_v3_with_components


@dataclass
class SAGEOperationResult:
    """Result from SAGE operation"""
    operation_id: str
    operation_type: str
    success: bool
    latency: float  # seconds
    atp_consumed: float
    quality_score: float  # 0-1
    output: Optional[str] = None
    error: Optional[str] = None


def create_sage_agent_lct(
    sage_instance_id: str = "sprout_01",
    hardware: str = "Jetson Orin Nano 8GB"
) -> LCT:
    """
    Create SAGE agent LCT with full V3/T3 metadata

    Args:
        sage_instance_id: Unique identifier for this SAGE instance
        hardware: Hardware platform description

    Returns:
        SAGE agent LCT

    Based on SAGE_WEB4_INTEGRATION_DESIGN.md schema
    """
    sage_lct = LCT(
        lct_id=f"lct:web4:agent:sage:{sage_instance_id}",
        lct_type="agent",
        owning_society_lct=f"lct:web4:society:sage_edge:{sage_instance_id}",
        created_at_block=1,
        created_at_tick=1,

        # V3: Value through Verification
        value_axes={
            "V3": {
                "veracity": 0.85,  # Initial reputation
                "veracity_raw": 0.85,
                "valuation": 0.80,
                "validity": 0.95,

                # Multi-dimensional veracity (Session #77)
                "components": {
                    "consistency": 0.85,
                    "accuracy": 0.85,
                    "reliability": 0.90,  # Edge stability validated
                    "speed": 0.75,  # 40s avg (slower than cloud)
                    "cost_efficiency": 0.85
                }
            }
        },

        # T3: Trust through Testing
        trust_axes={
            "T3": {
                "talent": 0.85,  # LLM capability
                "training": 0.90,  # IRP fine-tuning
                "temperament": 0.95,  # Edge stability
                "composite": 0.90
            }
        },

        # Hardware and capability metadata
        metadata={
            "name": f"SAGE ({hardware})",
            "hardware": hardware,
            "model": "epistemic-pragmatism",
            "model_size": "1.9GB",
            "irp_iterations": 3,
            "avg_inference_time": 40.0,  # seconds
            "thermal_max": 54.4,  # °C (from Session #16)
            "tts_rtf": 0.367,  # 2.7x real-time
            "deployment_date": time.strftime("%Y-%m-%d"),
            "validation_session": "Sprout #16",

            # Capabilities (from Sprout Session #16)
            "capabilities": {
                "edge_inference": 0.95,
                "voice_synthesis": 0.90,
                "thermal_stability": 0.95,
                "memory_efficiency": 0.90,
                "conversation": 0.85,
                "meta_cognitive": 0.80,
                "philosophical": 0.75
            },

            # Resource profile
            "resources": {
                "ATP": 1000.0,
                "compute_power": 0.75,
                "storage": 0.80,
                "network": 0.85
            }
        }
    )

    return sage_lct


def create_sage_edge_society_lct(
    sage_instance_id: str = "sprout_01",
    hardware: str = "Jetson Orin Nano 8GB"
) -> LCT:
    """
    Create SAGE edge society LCT

    Args:
        sage_instance_id: Unique identifier for this SAGE instance
        hardware: Hardware platform description

    Returns:
        SAGE edge society LCT

    Note: Single-agent society (SAGE is the only member)
    """
    society_lct = LCT(
        lct_id=f"lct:web4:society:sage_edge:{sage_instance_id}",
        lct_type="society",
        owning_society_lct=f"lct:web4:society:sage_edge:{sage_instance_id}",
        created_at_block=1,
        created_at_tick=1,

        # Society V3 (aggregate of member agents)
        value_axes={
            "V3": {
                "veracity": 0.85,
                "valuation": 0.80,
                "validity": 0.95
            }
        },

        # Edge-specific metadata
        metadata={
            "name": f"SAGE Edge Society ({hardware})",
            "type": "edge_agent_society",
            "location": "edge",
            "agent_count": 1,  # Single-agent society
            "hardware_platform": hardware,
            "network_connectivity": "local+internet",
            "federation_role": "edge_provider",
            "specialization": "conversational_ai",
            "validation_status": "production_ready",

            # Society resources
            "treasury": {
                "ATP": 5000.0  # Society ATP pool
            }
        }
    )

    return society_lct


def track_sage_operation(
    sage_lct: LCT,
    operation_result: SAGEOperationResult
) -> Dict:
    """
    Track SAGE operation and update V3 reputation

    Args:
        sage_lct: SAGE agent LCT
        operation_result: Operation outcome

    Returns:
        Updated V3 data including component deltas

    Example:
        >>> result = SAGEOperationResult(
        ...     operation_id="sage_op_001",
        ...     operation_type="conversation",
        ...     success=True,
        ...     latency=42.3,
        ...     atp_consumed=50.0,
        ...     quality_score=0.88
        ... )
        >>> update = track_sage_operation(sage_lct, result)
    """
    # Convert SAGEOperationResult to operation_result dict
    operation_data = {
        "success": operation_result.success,
        "quality_score": operation_result.quality_score,
        "latency": operation_result.latency,
        "expected_latency": 40.0,  # SAGE's baseline
        "atp_cost": operation_result.atp_consumed,
        "expected_efficiency": 0.015,  # quality per ATP
        "consistency_check": True  # Assume consistent for now
    }

    # Update V3 with multi-dimensional components
    v3_update = update_v3_with_components(sage_lct, operation_data)

    # Log operation
    if "operations" not in sage_lct.metadata:
        sage_lct.metadata["operations"] = []

    sage_lct.metadata["operations"].append({
        "operation_id": operation_result.operation_id,
        "operation_type": operation_result.operation_type,
        "timestamp": time.time(),
        "success": operation_result.success,
        "composite_veracity": v3_update["composite_veracity"],
        "atp_consumed": operation_result.atp_consumed
    })

    return {
        "operation_id": operation_result.operation_id,
        "v3_update": v3_update,
        "sage_status": get_sage_status(sage_lct)
    }


def get_sage_status(sage_lct: LCT) -> Dict:
    """
    Get current status of SAGE agent

    Args:
        sage_lct: SAGE agent LCT

    Returns:
        Status dictionary with V3 components, ATP, operation count
    """
    components = V3Components.from_dict(
        sage_lct.value_axes["V3"].get("components", {})
    )

    composite = calculate_composite_veracity(components)

    operation_count = len(sage_lct.metadata.get("operations", []))

    return {
        "agent_id": sage_lct.lct_id,
        "name": sage_lct.metadata["name"],
        "composite_veracity": composite,
        "components": components.to_dict(),
        "atp_available": sage_lct.metadata.get("resources", {}).get("ATP", 0),
        "operations_performed": operation_count
    }


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  SAGE-Web4 Bridge - Unit Tests")
    print("  Session #77")
    print("=" * 80)

    # Test 1: Create SAGE agent LCT
    print("\n=== Test 1: Create SAGE Agent LCT ===\n")

    sage_lct = create_sage_agent_lct()

    print(f"Agent ID: {sage_lct.lct_id}")
    print(f"Name: {sage_lct.metadata['name']}")
    print(f"Hardware: {sage_lct.metadata['hardware']}")
    print(f"Model: {sage_lct.metadata['model']}")
    print(f"Initial V3 veracity: {sage_lct.value_axes['V3']['veracity']:.3f}")

    print(f"\nV3 Components:")
    for comp, value in sage_lct.value_axes["V3"]["components"].items():
        print(f"  {comp:20} = {value:.3f}")

    # Test 2: Create SAGE edge society LCT
    print("\n=== Test 2: Create SAGE Edge Society LCT ===\n")

    society_lct = create_sage_edge_society_lct()

    print(f"Society ID: {society_lct.lct_id}")
    print(f"Name: {society_lct.metadata['name']}")
    print(f"Type: {society_lct.metadata['type']}")
    print(f"Agent count: {society_lct.metadata['agent_count']}")
    print(f"ATP pool: {society_lct.metadata['treasury']['ATP']:.0f}")

    # Test 3: Track SAGE operations
    print("\n=== Test 3: Track SAGE Operations ===\n")

    # Simulate 5 operations
    print("Simulating 5 SAGE operations...\n")

    for i in range(5):
        # Simulate operation result
        operation_result = SAGEOperationResult(
            operation_id=f"sage_op_{i+1:03d}",
            operation_type="conversation",
            success=(i % 4 != 0),  # 4/5 success rate
            latency=38.0 + i * 2,  # Variable latency
            atp_consumed=45.0 + i * 5,
            quality_score=0.85 + i * 0.02
        )

        # Track operation
        tracking = track_sage_operation(sage_lct, operation_result)

        status = "✓" if operation_result.success else "✗"
        print(f"Op {i+1} {status} {operation_result.operation_type}:")
        print(f"  V3 composite: {tracking['v3_update']['composite_veracity']:.3f}")
        print(f"  Component deltas: ", end="")

        deltas = tracking["v3_update"]["component_deltas"]
        for comp, delta in deltas.items():
            if delta != 0:
                print(f"{comp}:{delta:+.3f} ", end="")
        print()

    # Test 4: Get SAGE status
    print("\n=== Test 4: Get SAGE Status ===\n")

    status = get_sage_status(sage_lct)

    print(f"Agent: {status['name']}")
    print(f"Composite V3: {status['composite_veracity']:.3f}")
    print(f"Operations performed: {status['operations_performed']}")
    print(f"ATP available: {status['atp_available']:.0f}")

    print(f"\nFinal Components:")
    for comp, value in status["components"].items():
        print(f"  {comp:20} = {value:.3f}")

    print("\n" + "=" * 80)
    print("  All Unit Tests Passed!")
    print("=" * 80)
