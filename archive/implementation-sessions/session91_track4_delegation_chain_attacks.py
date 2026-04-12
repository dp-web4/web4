#!/usr/bin/env python3
"""
Session 91 Track 4: Multi-Level Delegation Chain Attack Testing

**Date**: 2025-12-26
**Platform**: Legion (RTX 4090)
**Track**: 4 of 4 - Comprehensive Attack Validation

## Problem Statement

Session 91 Track 1 implemented multi-level delegation chains with:
- Recursive parent legitimacy checking
- Graceful degradation through chains
- Capability validation against delegated capabilities
- Chain depth limits and circular detection

**This Track**: Comprehensive attack testing to validate defenses.

## Attack Scenarios

### Attack 1: Circular Delegation
```python
# Create A → B → C → A circular chain
root → parent → child → grandchild → parent  # LOOP!
```

**Expected**: CircularDelegationError, chain validation fails

### Attack 2: Chain Depth DoS
```python
# Create 11-level chain (exceeds max_chain_depth=10)
root → L1 → L2 → L3 → ... → L11
```

**Expected**: ExcessiveChainDepthError, chain validation fails

### Attack 3: Capability Escalation Through Chain
```python
# Parent has [QUALITY_ATTESTATION]
# Child tries to delegate [QUALITY_ATTESTATION, REVOCATION] to grandchild
parent.capabilities = [QUALITY_ATTESTATION]
child → grandchild with [QUALITY_ATTESTATION, REVOCATION]  # ESCALATION!
```

**Expected**: CapabilityEscalationError during validation

### Attack 4: Concurrent Middle-Node Revocation
```python
# 5-level chain, revoke nodes at positions 2 and 4 simultaneously
root → L1 → L2 → L3 → L4
revoke(L1)  # Position 2
revoke(L3)  # Position 4
```

**Expected**: All descendants DEGRADED (not REVOKED), graceful degradation

### Attack 5: Chain Cache Poisoning
```python
# Build chain, cache it, revoke middle node, try to use stale cache
chain = build_chain(grandchild)  # Cached
revoke(parent)
status = compute_chain_trust_status(grandchild)  # Should invalidate cache
```

**Expected**: Cache invalidated, fresh computation shows DEGRADED status

## Expected Results

All 5 attacks should be DEFENDED:
- Attack Success Rate: 0% (down from potential vulnerabilities)
- Defense mechanisms validated
- Chain security properties maintained
"""

import hashlib
import hmac
import secrets
import time
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from pathlib import Path

# Import from Session 91 Track 1
from session91_track1_multilevel_delegation import (
    MultiLevelDelegationAuthenticator,
    CircularDelegationError,
    ExcessiveChainDepthError,
    CapabilityEscalationError,
)

from session90_track2_graceful_degradation import (
    TrustLevel,
    TrustStatus,
)

from session90_track1_explicit_delegation import (
    Capability,
    DelegationAttestation,
)

from session88_track1_lct_society_authentication import (
    LCTIdentity,
    LCTAttestation,
    create_test_lct_identity,
    create_attestation,
)

# ============================================================================
# Attack 1: Circular Delegation
# ============================================================================

def test_circular_delegation_attack():
    """
    Attack 1: Create circular delegation chain.

    Attempt: root → parent → child → grandchild → parent (circular!)

    Expected: CircularDelegationError when building chain
    """
    print("=" * 80)
    print("ATTACK 1: CIRCULAR DELEGATION")
    print("=" * 80)
    print()

    authenticator = MultiLevelDelegationAuthenticator(network="web4.network")

    # Register root
    root_identity, root_key = create_test_lct_identity("root")
    root_attestation = create_attestation(root_identity, root_key)
    authenticator.register_society(root_identity, root_attestation)

    # Create URIs
    parent_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/parent"
    child_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/child"
    grandchild_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/grandchild"

    print("Setup:")
    print("-" * 80)
    print(f"  Root: {root_identity.to_lct_uri()[:50]}...")
    print(f"  Parent: {parent_lct[:60]}...")
    print(f"  Child: {child_lct[:60]}...")
    print(f"  Grandchild: {grandchild_lct[:60]}...")
    print()

    # Create normal delegations
    authenticator.create_delegation(
        parent_identity=root_identity,
        child_lct_uri=parent_lct,
        capabilities=[Capability.SUB_DELEGATION, Capability.QUALITY_ATTESTATION],
        expires_at=None
    )

    # Manually create delegations to form circular chain
    # parent → child
    parent_to_child = DelegationAttestation(
        parent_lct_uri=parent_lct,
        child_lct_uri=child_lct,
        capabilities=[Capability.SUB_DELEGATION, Capability.QUALITY_ATTESTATION],
        created_at=int(time.time()),
        expires_at=None,
        signature=secrets.token_hex(32)
    )
    authenticator.delegations[child_lct] = parent_to_child

    # child → grandchild
    child_to_grandchild = DelegationAttestation(
        parent_lct_uri=child_lct,
        child_lct_uri=grandchild_lct,
        capabilities=[Capability.QUALITY_ATTESTATION],
        created_at=int(time.time()),
        expires_at=None,
        signature=secrets.token_hex(32)
    )
    authenticator.delegations[grandchild_lct] = child_to_grandchild

    # ATTACK: grandchild → parent (creates circular chain!)
    print("Attack: Create circular delegation (grandchild → parent)")
    print("-" * 80)

    grandchild_to_parent = DelegationAttestation(
        parent_lct_uri=grandchild_lct,
        child_lct_uri=parent_lct,  # CIRCULAR!
        capabilities=[Capability.QUALITY_ATTESTATION],
        created_at=int(time.time()),
        expires_at=None,
        signature=secrets.token_hex(32)
    )
    # Override parent's delegation to create circular reference
    authenticator.delegations[parent_lct] = grandchild_to_parent

    print(f"  Created: grandchild → parent (circular link)")
    print()

    # Try to compute trust status (should detect circular delegation)
    print("Result:")
    print("-" * 80)

    status = authenticator.compute_chain_trust_status(parent_lct)

    # Defense: Circular delegation results in REVOKED status
    if status.trust_level == TrustLevel.REVOKED:
        print(f"  ✅ DEFENDED: Circular delegation detected")
        print(f"  Status: REVOKED (circular chain invalidated)")
        attack_successful = False
    else:
        print(f"  ❌ VULNERABLE: Circular delegation not detected!")
        print(f"  Status: {status.trust_level.value}")
        attack_successful = True

    print()

    return {
        'attack_type': 'CIRCULAR_DELEGATION',
        'attack_successful': attack_successful,
        'defense_mechanism': 'visited_set_tracking'
    }


# ============================================================================
# Attack 2: Chain Depth DoS
# ============================================================================

def test_chain_depth_dos_attack():
    """
    Attack 2: Create excessively deep delegation chain.

    Attempt: Create 11-level chain (exceeds max_chain_depth=10)

    Expected: ExcessiveChainDepthError when building chain
    """
    print("=" * 80)
    print("ATTACK 2: CHAIN DEPTH DoS")
    print("=" * 80)
    print()

    authenticator = MultiLevelDelegationAuthenticator(network="web4.network", max_chain_depth=10)

    # Register root
    root_identity, root_key = create_test_lct_identity("root")
    root_attestation = create_attestation(root_identity, root_key)
    authenticator.register_society(root_identity, root_attestation)

    print("Setup:")
    print("-" * 80)
    print(f"  Root: {root_identity.to_lct_uri()[:50]}...")
    print(f"  Max chain depth: {authenticator.max_chain_depth}")
    print()

    # ATTACK: Create 11-level chain
    print("Attack: Create 11-level delegation chain")
    print("-" * 80)

    prev_lct = root_identity.to_lct_uri()

    for level in range(1, 12):  # Create 11 levels (exceeds max of 10)
        level_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/L{level}"

        delegation = DelegationAttestation(
            parent_lct_uri=prev_lct,
            child_lct_uri=level_lct,
            capabilities=[Capability.QUALITY_ATTESTATION],
            created_at=int(time.time()),
            expires_at=None,
            signature=secrets.token_hex(32)
        )
        authenticator.delegations[level_lct] = delegation

        prev_lct = level_lct

    print(f"  Created 11-level chain (root → L1 → L2 → ... → L11)")
    print()

    # Try to compute trust status for deepest node
    leaf_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/L11"

    print("Result:")
    print("-" * 80)

    status = authenticator.compute_chain_trust_status(leaf_lct)

    # Defense: Excessive depth results in REVOKED status
    if status.trust_level == TrustLevel.REVOKED:
        print(f"  ✅ DEFENDED: Excessive chain depth detected")
        print(f"  Status: REVOKED (chain exceeds max depth)")
        attack_successful = False
    else:
        print(f"  ❌ VULNERABLE: Excessive depth not detected!")
        print(f"  Status: {status.trust_level.value}")
        attack_successful = True

    print()

    return {
        'attack_type': 'CHAIN_DEPTH_DOS',
        'attack_successful': attack_successful,
        'defense_mechanism': 'max_depth_limit',
        'attempted_depth': 11,
        'max_allowed_depth': 10
    }


# ============================================================================
# Attack 3: Capability Escalation Through Chain
# ============================================================================

def test_capability_escalation_attack():
    """
    Attack 3: Escalate capabilities through delegation chain.

    Attempt: Parent has [QUALITY_ATTESTATION], child tries to grant
    [QUALITY_ATTESTATION, REVOCATION] to grandchild.

    Expected: CapabilityEscalationError during validation
    """
    print("=" * 80)
    print("ATTACK 3: CAPABILITY ESCALATION THROUGH CHAIN")
    print("=" * 80)
    print()

    authenticator = MultiLevelDelegationAuthenticator(network="web4.network")

    # Register root
    root_identity, root_key = create_test_lct_identity("root")
    root_attestation = create_attestation(root_identity, root_key)
    authenticator.register_society(root_identity, root_attestation)

    parent_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/parent"
    child_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/child"
    grandchild_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/grandchild"

    print("Setup:")
    print("-" * 80)
    print(f"  Root: {root_identity.to_lct_uri()[:50]}...")
    print()

    # Root → Parent with LIMITED capabilities
    authenticator.create_delegation(
        parent_identity=root_identity,
        child_lct_uri=parent_lct,
        capabilities=[Capability.QUALITY_ATTESTATION],  # Only this capability!
        expires_at=None
    )

    # Parent → Child (valid subset)
    parent_to_child = DelegationAttestation(
        parent_lct_uri=parent_lct,
        child_lct_uri=child_lct,
        capabilities=[Capability.QUALITY_ATTESTATION],  # OK
        created_at=int(time.time()),
        expires_at=None,
        signature=secrets.token_hex(32)
    )
    authenticator.delegations[child_lct] = parent_to_child

    print("  Parent capabilities: [QUALITY_ATTESTATION]")
    print("  Child capabilities: [QUALITY_ATTESTATION]")
    print()

    # ATTACK: Child → Grandchild with ESCALATED capabilities
    print("Attack: Child attempts capability escalation")
    print("-" * 80)

    child_to_grandchild = DelegationAttestation(
        parent_lct_uri=child_lct,
        child_lct_uri=grandchild_lct,
        capabilities=[
            Capability.QUALITY_ATTESTATION,
            Capability.REVOCATION  # ESCALATION! Child doesn't have this
        ],
        created_at=int(time.time()),
        expires_at=None,
        signature=secrets.token_hex(32)
    )
    authenticator.delegations[grandchild_lct] = child_to_grandchild

    print(f"  Child tries to grant: [QUALITY_ATTESTATION, REVOCATION]")
    print(f"  (Child only has: [QUALITY_ATTESTATION])")
    print()

    # Try to compute trust status (should detect escalation)
    print("Result:")
    print("-" * 80)

    status = authenticator.compute_chain_trust_status(grandchild_lct)

    # Defense: Capability escalation results in REVOKED status
    if status.trust_level == TrustLevel.REVOKED:
        print(f"  ✅ DEFENDED: Capability escalation detected")
        print(f"  Status: REVOKED (invalid capability grant)")
        attack_successful = False
    else:
        print(f"  ❌ VULNERABLE: Capability escalation not detected!")
        print(f"  Grandchild capabilities: {[c.value for c in status.allowed_capabilities]}")
        attack_successful = True

    print()

    return {
        'attack_type': 'CAPABILITY_ESCALATION',
        'attack_successful': attack_successful,
        'defense_mechanism': 'delegated_capability_validation',
        'attempted_escalation': ['REVOCATION']
    }


# ============================================================================
# Attack 4: Concurrent Middle-Node Revocation
# ============================================================================

def test_concurrent_revocation_attack():
    """
    Attack 4: Revoke multiple middle nodes simultaneously.

    Attempt: 5-level chain, revoke nodes at positions 2 and 4

    Expected: All descendants DEGRADED (not REVOKED), graceful degradation
    """
    print("=" * 80)
    print("ATTACK 4: CONCURRENT MIDDLE-NODE REVOCATION")
    print("=" * 80)
    print()

    authenticator = MultiLevelDelegationAuthenticator(network="web4.network")

    # Register root
    root_identity, root_key = create_test_lct_identity("root")
    root_attestation = create_attestation(root_identity, root_key)
    authenticator.register_society(root_identity, root_attestation)

    # Create 5-level chain
    level_lcts = []
    prev_lct = root_identity.to_lct_uri()

    for level in range(1, 6):
        level_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/L{level}"
        level_lcts.append(level_lct)

        delegation = DelegationAttestation(
            parent_lct_uri=prev_lct,
            child_lct_uri=level_lct,
            capabilities=[Capability.QUALITY_ATTESTATION, Capability.SUB_DELEGATION],
            created_at=int(time.time()),
            expires_at=None,
            signature=secrets.token_hex(32)
        )
        authenticator.delegations[level_lct] = delegation

        prev_lct = level_lct

    print("Setup:")
    print("-" * 80)
    print(f"  5-level chain: root → L1 → L2 → L3 → L4 → L5")
    print()

    # Check status before revocation
    l5_status_before = authenticator.compute_chain_trust_status(level_lcts[4])
    print("Before Revocation:")
    print("-" * 80)
    print(f"  L5 trust: {l5_status_before.trust_level.value}")
    print(f"  L5 ATP: {l5_status_before.atp_multiplier}x")
    print()

    # ATTACK: Revoke L2 and L4 simultaneously
    print("Attack: Revoke L2 and L4 (positions 2 and 4)")
    print("-" * 80)

    authenticator.revoke_society(level_lcts[1])  # L2
    authenticator.revoke_society(level_lcts[3])  # L4

    print(f"  Revoked: {level_lcts[1].split('/')[-1]}")
    print(f"  Revoked: {level_lcts[3].split('/')[-1]}")
    print()

    # Check status after revocation
    print("After Revocation:")
    print("-" * 80)

    statuses = []
    for i, lct in enumerate(level_lcts):
        status = authenticator.compute_trust_status(lct)
        statuses.append(status)
        print(f"  L{i+1}: {status.trust_level.value} (ATP: {status.atp_multiplier}x)")

    print()

    l5_status_after = authenticator.compute_chain_trust_status(level_lcts[4])

    print(f"  L5 aggregated trust: {l5_status_after.trust_level.value}")
    print(f"  L5 aggregated ATP: {l5_status_after.atp_multiplier}x")
    print()

    print("Result:")
    print("-" * 80)

    # Verify graceful degradation
    degraded_count = sum(1 for s in statuses if s.trust_level == TrustLevel.DEGRADED)
    revoked_count = sum(1 for s in statuses if s.trust_level == TrustLevel.REVOKED)

    if l5_status_after.trust_level == TrustLevel.DEGRADED:
        print(f"  ✅ DEFENDED: Graceful degradation")
        print(f"    - L5 DEGRADED (not REVOKED despite 2 revoked ancestors)")
        print(f"    - Descendants with DEGRADED trust: {degraded_count}/5")
        print(f"    - Explicitly REVOKED: {revoked_count}/5 (L2, L4)")
        attack_successful = False
    else:
        print(f"  ❌ VULNERABLE: Cascade revocation occurred")
        print(f"    - L5 trust: {l5_status_after.trust_level.value}")
        attack_successful = True

    print()

    return {
        'attack_type': 'CONCURRENT_REVOCATION',
        'attack_successful': attack_successful,
        'revoked_nodes': 2,
        'degraded_nodes': degraded_count,
        'chain_length': 5,
        'defense_mechanism': 'graceful_degradation'
    }


# ============================================================================
# Attack 5: Chain Cache Poisoning
# ============================================================================

def test_cache_poisoning_attack():
    """
    Attack 5: Attempt to use stale cached chain after revocation.

    Attempt: Build chain, cache it, revoke middle node, verify cache invalidation

    Expected: Cache invalidated, fresh computation shows updated status
    """
    print("=" * 80)
    print("ATTACK 5: CHAIN CACHE POISONING")
    print("=" * 80)
    print()

    authenticator = MultiLevelDelegationAuthenticator(network="web4.network")

    # Register root
    root_identity, root_key = create_test_lct_identity("root")
    root_attestation = create_attestation(root_identity, root_key)
    authenticator.register_society(root_identity, root_attestation)

    # Create 4-level chain
    parent_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/parent"
    child_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/child"
    grandchild_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/grandchild"

    authenticator.create_delegation(
        parent_identity=root_identity,
        child_lct_uri=parent_lct,
        capabilities=[Capability.SUB_DELEGATION, Capability.QUALITY_ATTESTATION],
        expires_at=None
    )

    parent_to_child = DelegationAttestation(
        parent_lct_uri=parent_lct,
        child_lct_uri=child_lct,
        capabilities=[Capability.QUALITY_ATTESTATION],
        created_at=int(time.time()),
        expires_at=None,
        signature=secrets.token_hex(32)
    )
    authenticator.delegations[child_lct] = parent_to_child

    child_to_grandchild = DelegationAttestation(
        parent_lct_uri=child_lct,
        child_lct_uri=grandchild_lct,
        capabilities=[Capability.QUALITY_ATTESTATION],
        created_at=int(time.time()),
        expires_at=None,
        signature=secrets.token_hex(32)
    )
    authenticator.delegations[grandchild_lct] = child_to_grandchild

    print("Setup:")
    print("-" * 80)
    print(f"  4-level chain: root → parent → child → grandchild")
    print()

    # Build chain and cache it
    print("Phase 1: Build and cache chain")
    print("-" * 80)

    chain_before = authenticator.get_delegation_chain(grandchild_lct)
    status_before = authenticator.compute_chain_trust_status(grandchild_lct)

    print(f"  Chain built: {len(chain_before)} levels")
    print(f"  Grandchild trust: {status_before.trust_level.value}")
    print(f"  Chain cached: {grandchild_lct in authenticator.chain_cache}")
    print()

    # ATTACK: Revoke parent, attempt to use stale cache
    print("Attack: Revoke parent, check cache invalidation")
    print("-" * 80)

    authenticator.revoke_society(parent_lct)

    print(f"  Revoked: {parent_lct.split('/')[-1]}")
    print(f"  Cache invalidated: {grandchild_lct not in authenticator.chain_cache}")
    print()

    # Compute status again (should use fresh data, not stale cache)
    print("Phase 2: Re-compute after revocation")
    print("-" * 80)

    status_after = authenticator.compute_chain_trust_status(grandchild_lct)

    print(f"  Grandchild trust: {status_after.trust_level.value}")
    print(f"  Grandchild ATP: {status_after.atp_multiplier}x")
    print()

    print("Result:")
    print("-" * 80)

    # Verify cache was invalidated and status reflects revocation
    cache_invalidated = grandchild_lct not in authenticator.chain_cache or \
                       status_after.trust_level != status_before.trust_level

    if cache_invalidated and status_after.trust_level == TrustLevel.DEGRADED:
        print(f"  ✅ DEFENDED: Cache properly invalidated")
        print(f"    - Status changed: {status_before.trust_level.value} → {status_after.trust_level.value}")
        print(f"    - Cache reflects revocation")
        attack_successful = False
    else:
        print(f"  ❌ VULNERABLE: Stale cache used")
        print(f"    - Status unchanged: {status_after.trust_level.value}")
        attack_successful = True

    print()

    return {
        'attack_type': 'CACHE_POISONING',
        'attack_successful': attack_successful,
        'cache_invalidated': cache_invalidated,
        'status_before': status_before.trust_level.value,
        'status_after': status_after.trust_level.value,
        'defense_mechanism': 'cache_invalidation_on_revocation'
    }


# ============================================================================
# Main Comprehensive Test
# ============================================================================

def main():
    """Run comprehensive attack suite for multi-level delegation chains."""
    print("=" * 80)
    print("SESSION 91 TRACK 4: MULTI-LEVEL DELEGATION CHAIN ATTACKS")
    print("=" * 80)
    print()

    print("Objective: Validate all defenses for multi-level delegation chains")
    print("Expected: 100% defense rate (0 of 5 attacks successful)")
    print()

    results = []

    # Attack 1: Circular Delegation
    result1 = test_circular_delegation_attack()
    results.append(result1)

    # Attack 2: Chain Depth DoS
    result2 = test_chain_depth_dos_attack()
    results.append(result2)

    # Attack 3: Capability Escalation
    result3 = test_capability_escalation_attack()
    results.append(result3)

    # Attack 4: Concurrent Revocation
    result4 = test_concurrent_revocation_attack()
    results.append(result4)

    # Attack 5: Cache Poisoning
    result5 = test_cache_poisoning_attack()
    results.append(result5)

    # Summary
    print("=" * 80)
    print("COMPREHENSIVE SUMMARY")
    print("=" * 80)
    print()

    attacks_successful = sum(1 for r in results if r['attack_successful'])
    attacks_defended = len(results) - attacks_successful

    success_rate = (attacks_successful / len(results)) * 100
    defense_rate = (attacks_defended / len(results)) * 100

    print(f"Total attacks: {len(results)}")
    print(f"Attacks successful: {attacks_successful}")
    print(f"Attacks defended: {attacks_defended}")
    print()
    print(f"Attack success rate: {success_rate:.0f}%")
    print(f"Defense rate: {defense_rate:.0f}%")
    print()

    print("Attack-by-Attack Breakdown:")
    print("-" * 80)
    for r in results:
        status = "❌ VULNERABLE" if r['attack_successful'] else "✅ DEFENDED"
        print(f"  {status}: {r['attack_type']}")
    print()

    if defense_rate == 100:
        print("✅ SUCCESS: All multi-level delegation attacks defended")
        print()
        print("  Defense Mechanisms Validated:")
        print("    1. Circular delegation detection (visited set)")
        print("    2. Chain depth limits (max 10 levels)")
        print("    3. Capability validation (against delegated capabilities)")
        print("    4. Graceful degradation (concurrent revocations)")
        print("    5. Cache invalidation (on revocation)")
        print()
        print("  Security Properties:")
        print("    - No circular chains")
        print("    - DoS protection via depth limits")
        print("    - No capability escalation through chain")
        print("    - Graceful degradation preserves descendant operation")
        print("    - Cache coherence maintained during revocations")
    else:
        print("⚠️  Some attacks succeeded - review results")

    print()

    # Save results
    results_path = Path("/home/dp/ai-workspace/web4/implementation/session91_track4_attack_results.json")
    with open(results_path, 'w') as f:
        json.dump({
            'total_attacks': len(results),
            'attacks_successful': attacks_successful,
            'attacks_defended': attacks_defended,
            'attack_success_rate': success_rate,
            'defense_rate': defense_rate,
            'results': results
        }, f, indent=2)

    print(f"Results saved to: {results_path}")
    print()

    return results


if __name__ == "__main__":
    main()
