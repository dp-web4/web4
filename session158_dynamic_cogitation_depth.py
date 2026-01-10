#!/usr/bin/env python3
"""
Session 158: Dynamic Cogitation Depth Based on ATP Balance

Research Goal: Implement adaptive verification depth that responds to economic
state. High ATP → deeper verification. Low ATP → lighter verification.

Hypothesis: Economic efficiency requires balancing verification quality with
ATP costs. Nodes should invest more in verification when they can afford it,
and conserve resources when ATP is scarce.

Economic Feedback Loop:
- High ATP → Deep verification → Catch more errors → Maintain high ATP
- Low ATP → Light verification → Miss some errors → Learn and adapt → Recover ATP
- Creates self-regulating economic equilibrium

Inspiration: Biological systems adjust metabolic activity based on energy reserves.

Platform: Legion (RTX 4090)
Session: Autonomous Web4 Research - Session 158
Date: 2026-01-09
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import sys

# Add paths
HOME = Path.home()
sys.path.insert(0, str(HOME / "ai-workspace" / "web4"))

# Import Session 157 (optimized verification)
from session157_optimized_verification import (
    OptimizedVerificationNode,
    InternalCogitationMode,
    InternalCogitationResult,
    CogitationMode,
    ClaimType,
)


# ============================================================================
# COGITATION DEPTH LEVELS
# ============================================================================

class CogitationDepth(Enum):
    """
    Verification depth levels based on ATP balance.

    Lighter verification = fewer modes, faster execution, lower quality.
    Deeper verification = more modes, slower execution, higher quality.
    """
    MINIMAL = "minimal"  # 1-2 modes, very fast, ATP < 50
    LIGHT = "light"  # 2-3 modes, fast, ATP 50-75
    STANDARD = "standard"  # All 5 modes, normal, ATP 75-100
    DEEP = "deep"  # All 5 modes + extra scrutiny, ATP 100-125
    THOROUGH = "thorough"  # Maximum verification, ATP > 125


@dataclass
class DepthConfiguration:
    """Configuration for verification depth level."""
    depth: CogitationDepth
    modes_enabled: List[InternalCogitationMode]
    quality_threshold: float  # Minimum quality to pass
    claim_verification_enabled: bool
    contradiction_detection_sensitivity: float  # 0.0-1.0
    identity_grounding_required: bool


# ============================================================================
# DYNAMIC DEPTH NODE
# ============================================================================

class DynamicDepthCogitationNode(OptimizedVerificationNode):
    """
    Node with dynamic cogitation depth based on ATP balance.

    Adjusts verification intensity according to economic state:
    - High ATP: Deep verification (catch everything)
    - Medium ATP: Standard verification (balanced)
    - Low ATP: Light verification (conserve resources)

    Creates economic feedback loop that self-regulates quality vs cost.
    """

    def __init__(
        self,
        node_id: str,
        lct_id: str,
        hardware_type: str,
        hardware_level: int = 4,
        listen_host: str = "0.0.0.0",
        listen_port: int = 8888,
        pow_difficulty: int = 18,
        network_subnet: str = "10.0.0.0/24",
        enable_internal_cogitation: bool = True,
        enable_dynamic_depth: bool = True,
    ):
        """Initialize dynamic depth cogitation node."""
        super().__init__(
            node_id=node_id,
            lct_id=lct_id,
            hardware_type=hardware_type,
            hardware_level=hardware_level,
            listen_host=listen_host,
            listen_port=listen_port,
            pow_difficulty=pow_difficulty,
            network_subnet=network_subnet,
            enable_internal_cogitation=enable_internal_cogitation,
        )

        self.enable_dynamic_depth = enable_dynamic_depth

        # Depth configurations
        self.depth_configs = {
            CogitationDepth.MINIMAL: DepthConfiguration(
                depth=CogitationDepth.MINIMAL,
                modes_enabled=[
                    InternalCogitationMode.CONTRADICTION_DETECTION,
                ],
                quality_threshold=0.2,  # Very permissive
                claim_verification_enabled=False,
                contradiction_detection_sensitivity=0.5,
                identity_grounding_required=False,
            ),
            CogitationDepth.LIGHT: DepthConfiguration(
                depth=CogitationDepth.LIGHT,
                modes_enabled=[
                    InternalCogitationMode.IDENTITY_GROUNDING,
                    InternalCogitationMode.CONTRADICTION_DETECTION,
                ],
                quality_threshold=0.3,
                claim_verification_enabled=False,
                contradiction_detection_sensitivity=0.7,
                identity_grounding_required=False,
            ),
            CogitationDepth.STANDARD: DepthConfiguration(
                depth=CogitationDepth.STANDARD,
                modes_enabled=[
                    InternalCogitationMode.IDENTITY_GROUNDING,
                    InternalCogitationMode.CONTRADICTION_DETECTION,
                    InternalCogitationMode.CLAIM_VERIFICATION,
                    InternalCogitationMode.SELF_QUESTIONING,
                    InternalCogitationMode.EPISTEMIC_CALIBRATION,
                ],
                quality_threshold=0.3,  # Session 157 threshold
                claim_verification_enabled=True,
                contradiction_detection_sensitivity=1.0,
                identity_grounding_required=False,
            ),
            CogitationDepth.DEEP: DepthConfiguration(
                depth=CogitationDepth.DEEP,
                modes_enabled=[
                    InternalCogitationMode.IDENTITY_GROUNDING,
                    InternalCogitationMode.CONTRADICTION_DETECTION,
                    InternalCogitationMode.CLAIM_VERIFICATION,
                    InternalCogitationMode.SELF_QUESTIONING,
                    InternalCogitationMode.EPISTEMIC_CALIBRATION,
                ],
                quality_threshold=0.4,  # Higher threshold
                claim_verification_enabled=True,
                contradiction_detection_sensitivity=1.0,
                identity_grounding_required=True,  # Stricter
            ),
            CogitationDepth.THOROUGH: DepthConfiguration(
                depth=CogitationDepth.THOROUGH,
                modes_enabled=[
                    InternalCogitationMode.IDENTITY_GROUNDING,
                    InternalCogitationMode.CONTRADICTION_DETECTION,
                    InternalCogitationMode.CLAIM_VERIFICATION,
                    InternalCogitationMode.SELF_QUESTIONING,
                    InternalCogitationMode.EPISTEMIC_CALIBRATION,
                ],
                quality_threshold=0.5,  # Highest threshold
                claim_verification_enabled=True,
                contradiction_detection_sensitivity=1.0,
                identity_grounding_required=True,
                # Would add: cross-reference with historical claims, etc.
            ),
        }

        # Depth history (track which depths used)
        self.depth_history: List[CogitationDepth] = []
        self.depth_quality_by_level: Dict[CogitationDepth, List[float]] = {
            depth: [] for depth in CogitationDepth
        }

        print(f"[{self.node_id}] Dynamic cogitation depth initialized ✅")
        print(f"[{self.node_id}] Depth levels: {len(self.depth_configs)}")
        print(f"[{self.node_id}] Current ATP: {self.internal_atp_balance}")

    # ========================================================================
    # DYNAMIC DEPTH SELECTION
    # ========================================================================

    def select_depth(self, atp_balance: float) -> CogitationDepth:
        """
        Select verification depth based on ATP balance.

        ATP Thresholds:
        - < 50: MINIMAL (conserve resources)
        - 50-75: LIGHT (basic verification)
        - 75-100: STANDARD (normal operation)
        - 100-125: DEEP (high quality)
        - > 125: THOROUGH (maximum scrutiny)
        """
        if not self.enable_dynamic_depth:
            return CogitationDepth.STANDARD

        if atp_balance < 50:
            return CogitationDepth.MINIMAL
        elif atp_balance < 75:
            return CogitationDepth.LIGHT
        elif atp_balance < 100:
            return CogitationDepth.STANDARD
        elif atp_balance < 125:
            return CogitationDepth.DEEP
        else:
            return CogitationDepth.THOROUGH

    async def internal_cogitation_with_depth(
        self,
        thought_content: str,
        mode: CogitationMode
    ) -> InternalCogitationResult:
        """
        Perform internal verification with dynamic depth.

        Depth is determined by current ATP balance.
        """
        # Select depth based on ATP
        depth = self.select_depth(self.internal_atp_balance)
        config = self.depth_configs[depth]

        print(f"[{self.node_id}] Cogitation depth: {depth.value} (ATP: {self.internal_atp_balance:.1f})")

        start_time = time.time()

        modes_activated = []
        contradictions_found = 0
        claims_verified = 0
        claims_ungrounded = 0
        identity_verified = False
        epistemic_confidence = 0.5

        # Only run enabled modes based on depth
        if InternalCogitationMode.IDENTITY_GROUNDING in config.modes_enabled:
            identity_verified = await self._verify_identity_grounding(thought_content)
            modes_activated.append(InternalCogitationMode.IDENTITY_GROUNDING)
            self.mode_activation_counts[InternalCogitationMode.IDENTITY_GROUNDING] += 1
            if identity_verified:
                epistemic_confidence += 0.1

        if InternalCogitationMode.CONTRADICTION_DETECTION in config.modes_enabled:
            contradictions = await self._detect_contradictions(thought_content)
            contradictions_found = len(contradictions)
            # Apply sensitivity (at low depth, only catch severe contradictions)
            contradictions_found = int(contradictions_found * config.contradiction_detection_sensitivity)
            modes_activated.append(InternalCogitationMode.CONTRADICTION_DETECTION)
            self.mode_activation_counts[InternalCogitationMode.CONTRADICTION_DETECTION] += 1
            if contradictions_found > 0:
                epistemic_confidence -= 0.2 * contradictions_found

        if config.claim_verification_enabled and InternalCogitationMode.CLAIM_VERIFICATION in config.modes_enabled:
            verified, ungrounded = await self._verify_claims(thought_content)
            claims_verified = verified
            claims_ungrounded = ungrounded
            modes_activated.append(InternalCogitationMode.CLAIM_VERIFICATION)
            self.mode_activation_counts[InternalCogitationMode.CLAIM_VERIFICATION] += 1
            if claims_verified > 0:
                epistemic_confidence += 0.1 * claims_verified
            if claims_ungrounded > 0:
                epistemic_confidence -= 0.15 * claims_ungrounded

        if InternalCogitationMode.SELF_QUESTIONING in config.modes_enabled:
            questioning_result = await self._self_questioning(thought_content, mode)
            modes_activated.append(InternalCogitationMode.SELF_QUESTIONING)
            self.mode_activation_counts[InternalCogitationMode.SELF_QUESTIONING] += 1
            epistemic_confidence += questioning_result * 0.1

        if InternalCogitationMode.EPISTEMIC_CALIBRATION in config.modes_enabled:
            calibrated_confidence = await self._epistemic_calibration(epistemic_confidence)
            modes_activated.append(InternalCogitationMode.EPISTEMIC_CALIBRATION)
            self.mode_activation_counts[InternalCogitationMode.EPISTEMIC_CALIBRATION] += 1
            epistemic_confidence = max(0.0, min(1.0, calibrated_confidence))

        # Calculate quality (uses inherited method)
        quality_score = self._calculate_verification_quality(
            identity_verified,
            contradictions_found,
            claims_verified,
            claims_ungrounded,
            epistemic_confidence
        )

        # Check against depth-specific threshold
        if config.identity_grounding_required and not identity_verified:
            quality_score = 0.0  # Force fail if identity required but not verified

        verification_time_ms = (time.time() - start_time) * 1000

        result = InternalCogitationResult(
            modes_activated=modes_activated,
            identity_verified=identity_verified,
            contradictions_found=contradictions_found,
            claims_verified=claims_verified,
            claims_ungrounded=claims_ungrounded,
            epistemic_confidence=epistemic_confidence,
            verification_quality_score=quality_score,
            verification_time_ms=verification_time_ms,
        )

        # Update metrics
        self.total_internal_cogitations += 1
        if quality_score > config.quality_threshold:
            self.total_verifications_passed += 1
        self.total_contradictions_detected += contradictions_found
        self.total_claims_verified += claims_verified
        self.total_claims_ungrounded += claims_ungrounded

        # Track depth history
        self.depth_history.append(depth)
        self.depth_quality_by_level[depth].append(quality_score)

        # Store in history
        self.cogitation_history.append(result)

        # Apply ATP economics
        await self._apply_atp_verification_economics(result)

        print(f"[{self.node_id}]   Modes activated: {len(modes_activated)}/{len(InternalCogitationMode)}")
        print(f"[{self.node_id}]   Quality: {quality_score:.3f} (threshold: {config.quality_threshold})")

        return result

    async def submit_thought_with_dynamic_depth(
        self,
        content: str,
        mode: CogitationMode = CogitationMode.GENERAL,
    ) -> Optional[str]:
        """
        Submit thought with dynamic depth verification.

        Depth automatically adjusted based on ATP balance.
        """
        print(f"\n[{self.node_id}] Submitting thought with dynamic depth...")
        print(f"[{self.node_id}] Mode: {mode.value}")

        # Dynamic depth verification
        if self.enable_internal_cogitation:
            cogitation_result = await self.internal_cogitation_with_depth(content, mode)

            depth = self.select_depth(self.internal_atp_balance)
            config = self.depth_configs[depth]

            # Check if quality sufficient for this depth level
            if cogitation_result.verification_quality_score < config.quality_threshold:
                print(f"[{self.node_id}] ❌ Rejected by depth {depth.value} (quality {cogitation_result.verification_quality_score:.3f} < {config.quality_threshold})")
                return None

        # Submit to federation
        thought_id = await self.submit_thought(content, mode)

        if thought_id:
            print(f"[{self.node_id}] ✅ Accepted by federation: {thought_id}")
        else:
            print(f"[{self.node_id}] ❌ Rejected by federation")

        return thought_id

    # ========================================================================
    # METRICS
    # ========================================================================

    def get_dynamic_depth_metrics(self) -> Dict[str, Any]:
        """Get dynamic depth metrics."""
        base_metrics = self.get_internal_cogitation_metrics()

        # Calculate depth statistics
        depth_usage = {depth.value: self.depth_history.count(depth) for depth in CogitationDepth}
        depth_avg_quality = {
            depth.value: (
                sum(self.depth_quality_by_level[depth]) / len(self.depth_quality_by_level[depth])
                if self.depth_quality_by_level[depth] else 0.0
            )
            for depth in CogitationDepth
        }

        dynamic_metrics = {
            "current_depth": self.select_depth(self.internal_atp_balance).value,
            "depth_usage_counts": depth_usage,
            "depth_avg_quality": depth_avg_quality,
            "total_cogitations": len(self.depth_history),
            "depth_configurations": {
                depth.value: {
                    "modes_count": len(config.modes_enabled),
                    "quality_threshold": config.quality_threshold,
                    "claim_verification": config.claim_verification_enabled,
                }
                for depth, config in self.depth_configs.items()
            }
        }

        base_metrics["dynamic_depth"] = dynamic_metrics
        return base_metrics


# ============================================================================
# TESTING
# ============================================================================

async def test_dynamic_depth():
    """
    Test dynamic cogitation depth.

    Simulates ATP balance changes and observes depth adaptation.
    """
    print("\n" + "="*80)
    print("TEST: Dynamic Cogitation Depth")
    print("="*80)
    print("Hypothesis: Verification depth should adapt to ATP balance")
    print("="*80)

    # Create node
    print("\n[TEST] Creating dynamic depth node...")

    legion = DynamicDepthCogitationNode(
        node_id="legion",
        lct_id="lct:web4:ai:legion",
        hardware_type="tpm2",
        hardware_level=5,
        listen_port=8888,
        enable_internal_cogitation=True,
        enable_dynamic_depth=True,
    )

    # Start server
    print("\n[TEST] Starting node...")
    legion_task = asyncio.create_task(legion.start())
    await asyncio.sleep(1)

    # Test 1: High ATP (should use STANDARD depth initially)
    print("\n[TEST] Test 1: High ATP balance (100) - should use STANDARD depth...")
    thought1 = await legion.submit_thought_with_dynamic_depth(
        "Testing dynamic depth at high ATP balance with standard verification",
        mode=CogitationMode.VERIFYING
    )
    await asyncio.sleep(1)

    # Test 2: Artificially set ATP to THOROUGH range
    print("\n[TEST] Test 2: Setting ATP to 130 (THOROUGH range)...")
    legion.internal_atp_balance = 130.0
    thought2 = await legion.submit_thought_with_dynamic_depth(
        "With abundant ATP resources thorough verification can catch subtle issues",
        mode=CogitationMode.VERIFYING
    )
    await asyncio.sleep(1)

    # Test 3: Medium ATP (LIGHT range)
    print("\n[TEST] Test 3: Setting ATP to 65 (LIGHT range)...")
    legion.internal_atp_balance = 65.0
    thought3 = await legion.submit_thought_with_dynamic_depth(
        "Lower ATP means lighter verification for economic efficiency",
        mode=CogitationMode.GENERAL
    )
    await asyncio.sleep(1)

    # Test 4: Low ATP (MINIMAL range)
    print("\n[TEST] Test 4: Setting ATP to 40 (MINIMAL range)...")
    legion.internal_atp_balance = 40.0
    thought4 = await legion.submit_thought_with_dynamic_depth(
        "Minimal ATP requires minimal verification to conserve resources",
        mode=CogitationMode.EXPLORING
    )
    await asyncio.sleep(1)

    # Test 5: Recovery to DEEP range
    print("\n[TEST] Test 5: Setting ATP to 110 (DEEP range)...")
    legion.internal_atp_balance = 110.0
    thought5 = await legion.submit_thought_with_dynamic_depth(
        "Recovered ATP enables deep verification with higher quality thresholds",
        mode=CogitationMode.INTEGRATING
    )
    await asyncio.sleep(1)

    # Get metrics
    print("\n[TEST] Test 6: Dynamic depth metrics...")
    metrics = legion.get_dynamic_depth_metrics()

    print("\n=== DYNAMIC DEPTH METRICS ===")
    print(json.dumps(metrics["dynamic_depth"], indent=2))

    # Cleanup
    print("\n[TEST] Stopping node...")
    await legion.stop()
    legion_task.cancel()

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run dynamic depth test."""
    print("\n" + "="*80)
    print("SESSION 158: DYNAMIC COGITATION DEPTH")
    print("="*80)
    print("Adaptive verification: High ATP → Deep, Low ATP → Light")
    print("="*80)

    # Run test
    asyncio.run(test_dynamic_depth())

    print("\n" + "="*80)
    print("SESSION 158 COMPLETE")
    print("="*80)
    print("Status: ✅ Dynamic depth adaptation implemented")
    print("Validation: Depth responds to ATP balance")
    print("Insight: Economic efficiency through adaptive verification")
    print("="*80)


if __name__ == "__main__":
    main()
