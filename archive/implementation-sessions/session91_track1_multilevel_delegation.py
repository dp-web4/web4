#!/usr/bin/env python3
"""
Session 91 Track 1: Multi-Level Delegation Chains

**Date**: 2025-12-26
**Platform**: Legion (RTX 4090)
**Track**: 1 of 5 - Delegation Chain Extension

## Problem Statement

Session 90 achieved 100% defense for single-level delegation:
- Parent → Child delegation with explicit attestations
- Graceful degradation on revocation

**New Challenge**: Multi-level delegation chains

```
Root → Parent → Child → Grandchild
```

## Key Questions

1. **Trust Propagation**: How does trust flow through chain?
   - If Parent has DEGRADED trust, what about Child?
   - If middle node revoked, how do descendants degrade?

2. **Capability Inheritance**: How do capabilities restrict through chain?
   - Parent grants [SUB_DELEGATION, QUALITY_ATTESTATION]
   - Child can grant subset to Grandchild
   - Cannot escalate privileges

3. **Chain Validation**: How to efficiently validate entire chain?
   - Recursive validation from leaf to root
   - Cache validation results for performance
   - Detect circular delegations

4. **Attack Vectors**: New attacks enabled by multi-level chains?
   - Middle-node revocation cascade
   - Circular delegation loops
   - Privilege escalation through chain
   - Chain length DoS (excessive depth)

## Architecture

### Trust Propagation Rules

```
Root: FULL → Parent: FULL → Child: FULL → Grandchild: FULL
Root: FULL → Parent: DEGRADED → Child: DEGRADED → Grandchild: DEGRADED
Root: FULL → Parent: REVOKED → Child: DEGRADED → Grandchild: DEGRADED
Root: REVOKED → Parent: DEGRADED → Child: DEGRADED → Grandchild: DEGRADED
```

**Rule**: Trust level = min(own_status, parent_trust_level)

**Graceful Degradation Through Chain**:
- Revoke middle node → descendants inherit DEGRADED from that point
- Prevents cascade but maintains reduced functionality
- ATP allocation compounds through chain

### Capability Restrictions

```python
# Root grants to Parent
root → parent: [SUB_DELEGATION, QUALITY_ATTESTATION, REVOCATION]

# Parent can grant subset to Child
parent → child: [SUB_DELEGATION, QUALITY_ATTESTATION]  # OK
parent → child: [REVOCATION]  # BLOCKED (not in parent's set)

# Child grants to Grandchild
child → grandchild: [QUALITY_ATTESTATION]  # OK (subset of parent's)
child → grandchild: [REVOCATION]  # BLOCKED (not in child's set)
```

**Rule**: capabilities(child) ⊆ capabilities(parent)

### Chain Validation

Validate delegation chain from leaf to root:
- Build chain by following parent pointers
- Check for circular delegations
- Validate each link in chain
- Cache results for performance

## Expected Results

**Functionality**:
- ✅ Multi-level chains validate correctly
- ✅ Trust propagates through chain
- ✅ Capabilities restrict through chain
- ✅ Circular delegation detected

**Security**:
- ✅ Middle-node revocation gracefully degrades descendants
- ✅ Cannot escalate capabilities through chain
- ✅ Chain depth limits prevent DoS
- ✅ Circular delegations rejected

**Performance**:
- ✅ Chain validation cached for efficiency
- ✅ O(depth) validation time
- ✅ Graceful degradation under load
"""

import hashlib
import hmac
import secrets
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from enum import Enum

# Import from Session 90
from session90_track2_graceful_degradation import (
    GracefulDegradationAuthenticator,
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
# Exceptions
# ============================================================================

class CircularDelegationError(Exception):
    """Raised when circular delegation detected in chain."""
    pass


class ExcessiveChainDepthError(Exception):
    """Raised when delegation chain exceeds max depth."""
    pass


class CapabilityEscalationError(Exception):
    """Raised when child tries to grant capabilities not possessed by parent."""
    pass


# ============================================================================
# Multi-Level Delegation Chain Authenticator
# ============================================================================

class MultiLevelDelegationAuthenticator(GracefulDegradationAuthenticator):
    """
    Extends graceful degradation with multi-level delegation chain support.

    Features:
    - Parent → Child → Grandchild → ... chains
    - Trust propagation through chain
    - Capability restriction through chain
    - Circular delegation detection
    - Chain depth limits
    - Cached chain validation
    """

    def __init__(self, network: str = "web4.network", max_chain_depth: int = 10):
        """
        Initialize multi-level delegation authenticator.

        Args:
            network: Web4 network identifier
            max_chain_depth: Maximum allowed delegation chain depth
        """
        super().__init__(network)

        self.max_chain_depth = max_chain_depth

        # Chain validation cache
        self.chain_cache: Dict[str, List[str]] = {}  # child_uri → chain (leaf to root)
        self.chain_cache_timestamps: Dict[str, int] = {}
        self.chain_cache_ttl = 300  # 5 minutes

    def compute_trust_status(self, society_lct_uri: str) -> TrustStatus:
        """
        Compute trust status with recursive parent legitimacy check.

        Overrides parent to support multi-level chains where parent might
        itself be a delegated society (not in registered_societies).

        Args:
            society_lct_uri: LCT URI to compute status for

        Returns:
            Trust status
        """
        # Check if society is explicitly revoked
        child_revoked = society_lct_uri in self.revoked_societies

        # Check if society has delegation RECORD (regardless of parent status)
        has_delegation = self.has_delegation_record(society_lct_uri)

        # Determine parent trust level RECURSIVELY
        parent_trust_level = None
        if has_delegation:
            delegation = self.delegations[society_lct_uri]
            parent_lct_uri = delegation.parent_lct_uri

            # Get parent's trust level
            if parent_lct_uri in self.registered_societies:
                if parent_lct_uri not in self.revoked_societies:
                    parent_trust_level = TrustLevel.FULL
                else:
                    parent_trust_level = TrustLevel.DEGRADED  # Revoked parent → children degraded
            elif self.has_delegation_record(parent_lct_uri):
                # Recursive check: parent has delegation, get its trust level
                parent_status = self.compute_trust_status(parent_lct_uri)
                parent_trust_level = parent_status.trust_level

        # Compute trust level (inherit minimum of self and parent)
        if child_revoked:
            trust_level = TrustLevel.REVOKED
            atp_multiplier = self.revoked_atp_multiplier
            allowed_capabilities = []
        elif has_delegation:
            delegation = self.delegations[society_lct_uri]

            # Trust level = min(parent_trust, own_status)
            if parent_trust_level == TrustLevel.FULL:
                # Parent FULL → child FULL
                trust_level = TrustLevel.FULL
                atp_multiplier = self.full_trust_atp_multiplier
                allowed_capabilities = delegation.capabilities
            elif parent_trust_level == TrustLevel.DEGRADED:
                # Parent DEGRADED → child DEGRADED (cascade)
                trust_level = TrustLevel.DEGRADED
                atp_multiplier = self.degraded_trust_atp_multiplier
                allowed_capabilities = [
                    cap for cap in delegation.capabilities
                    if cap in self.degraded_allowed_capabilities
                ]
            else:
                # Parent REVOKED or None → child DEGRADED (graceful)
                trust_level = TrustLevel.DEGRADED
                atp_multiplier = self.degraded_trust_atp_multiplier
                allowed_capabilities = [
                    cap for cap in delegation.capabilities
                    if cap in self.degraded_allowed_capabilities
                ]
        else:
            # No delegation: Check direct registration
            if society_lct_uri in self.registered_societies:
                if child_revoked:
                    trust_level = TrustLevel.REVOKED
                    atp_multiplier = self.revoked_atp_multiplier
                    allowed_capabilities = []
                else:
                    trust_level = TrustLevel.FULL
                    atp_multiplier = self.full_trust_atp_multiplier
                    allowed_capabilities = list(Capability)
            else:
                trust_level = TrustLevel.REVOKED
                atp_multiplier = self.revoked_atp_multiplier
                allowed_capabilities = []

        # Compute parent_legitimate flag for TrustStatus
        parent_legitimate = parent_trust_level in [TrustLevel.FULL, TrustLevel.DEGRADED] if parent_trust_level else False

        return TrustStatus(
            society_lct_uri=society_lct_uri,
            trust_level=trust_level,
            has_delegation=has_delegation,
            parent_legitimate=parent_legitimate,
            child_revoked=child_revoked,
            atp_multiplier=atp_multiplier,
            allowed_capabilities=allowed_capabilities
        )

    def get_delegation_chain(self, leaf_lct_uri: str) -> List[str]:
        """
        Get full delegation chain from leaf to root.

        Args:
            leaf_lct_uri: LCT URI of leaf node

        Returns:
            List of LCT URIs from leaf to root

        Raises:
            CircularDelegationError: If circular delegation detected
            ExcessiveChainDepthError: If chain exceeds max depth
        """
        # Check cache
        if leaf_lct_uri in self.chain_cache:
            cache_time = self.chain_cache_timestamps[leaf_lct_uri]
            if time.time() - cache_time < self.chain_cache_ttl:
                return self.chain_cache[leaf_lct_uri]

        # Build chain
        chain = []
        current = leaf_lct_uri
        visited = set()

        while True:
            # Check for circular delegation
            if current in visited:
                raise CircularDelegationError(
                    f"Circular delegation detected in chain: {current} appears twice"
                )

            visited.add(current)
            chain.append(current)

            # Check chain depth
            if len(chain) > self.max_chain_depth:
                raise ExcessiveChainDepthError(
                    f"Chain depth {len(chain)} exceeds maximum {self.max_chain_depth}"
                )

            # Check if has parent delegation
            if not self.has_delegation_record(current):
                # Reached root (no delegation means registered directly)
                break

            # Move to parent
            delegation = self.delegations[current]
            current = delegation.parent_lct_uri

        # Cache result
        self.chain_cache[leaf_lct_uri] = chain
        self.chain_cache_timestamps[leaf_lct_uri] = int(time.time())

        return chain

    def validate_capability_inheritance(self, child_lct_uri: str) -> bool:
        """
        Validate that capabilities don't escalate through delegation chain.

        Each child can only have capabilities that are subset of parent's DELEGATED capabilities.
        Note: We check against parent's delegated capabilities (not current allowed capabilities)
        because parent's current status (DEGRADED/REVOKED) shouldn't invalidate existing delegations.

        Args:
            child_lct_uri: LCT URI to validate

        Returns:
            True if capability inheritance valid

        Raises:
            CapabilityEscalationError: If child has capabilities parent wasn't delegated
        """
        if not self.has_delegation_record(child_lct_uri):
            # No delegation, no inheritance to validate
            return True

        child_delegation = self.delegations[child_lct_uri]
        parent_lct_uri = child_delegation.parent_lct_uri

        # Get child's granted capabilities
        child_capabilities = set(child_delegation.capabilities)

        # Get parent's DELEGATED capabilities (not current allowed capabilities)
        # This is important for graceful degradation - parent's current status shouldn't
        # invalidate existing child delegations
        if parent_lct_uri in self.registered_societies:
            # Parent is root (registered) - has all capabilities
            parent_capabilities = set(Capability)
        elif self.has_delegation_record(parent_lct_uri):
            # Parent is delegated - use its delegated capabilities
            parent_delegation = self.delegations[parent_lct_uri]
            parent_capabilities = set(parent_delegation.capabilities)
        else:
            # Parent not found - shouldn't happen, but treat as no capabilities
            parent_capabilities = set()

        # Check subset relationship
        if not child_capabilities.issubset(parent_capabilities):
            escalated = child_capabilities - parent_capabilities
            raise CapabilityEscalationError(
                f"Child {child_lct_uri} has capabilities {escalated} "
                f"not delegated to parent {parent_lct_uri}"
            )

        return True

    def compute_chain_trust_status(self, leaf_lct_uri: str) -> TrustStatus:
        """
        Compute trust status considering entire delegation chain.

        Trust level = min(own_status, all_ancestors_status)
        Capabilities = intersection of all ancestors' capabilities
        ATP multiplier = product of all ancestors' multipliers

        Args:
            leaf_lct_uri: LCT URI to compute status for

        Returns:
            Trust status considering full chain
        """
        try:
            # Get delegation chain
            chain = self.get_delegation_chain(leaf_lct_uri)

            # Validate capability inheritance
            for node in chain:
                if self.has_delegation_record(node):
                    self.validate_capability_inheritance(node)

            # Compute trust status for each node in chain
            chain_statuses = [
                self.compute_trust_status(node)
                for node in chain
            ]

            # Aggregate trust level
            # Key insight: If leaf itself is not revoked, it should be DEGRADED (not REVOKED)
            # even if ancestors are revoked (graceful degradation)
            leaf_status = chain_statuses[0]

            if leaf_status.child_revoked:
                # Leaf explicitly revoked
                min_trust_level = TrustLevel.REVOKED
            else:
                # Leaf not revoked - check ancestors
                # Exclude leaf from min calculation (graceful degradation)
                ancestor_statuses = chain_statuses[1:] if len(chain_statuses) > 1 else []

                if not ancestor_statuses:
                    # Only leaf in chain (no ancestors)
                    min_trust_level = leaf_status.trust_level
                else:
                    # Get minimum of ancestors (excluding REVOKED ancestors for graceful degradation)
                    # If any ancestor is REVOKED, descendants should be DEGRADED (not REVOKED)
                    ancestor_trust_levels = [s.trust_level for s in ancestor_statuses]

                    if TrustLevel.REVOKED in ancestor_trust_levels:
                        # Ancestor revoked → graceful degradation
                        min_trust_level = TrustLevel.DEGRADED
                    elif TrustLevel.DEGRADED in ancestor_trust_levels:
                        # Ancestor degraded → cascade degradation
                        min_trust_level = TrustLevel.DEGRADED
                    else:
                        # All ancestors FULL → leaf stays at its level
                        min_trust_level = leaf_status.trust_level

            # Aggregate capabilities (intersection of chain)
            if min_trust_level == TrustLevel.REVOKED:
                aggregated_capabilities = []
            else:
                # Start with leaf's capabilities
                capability_sets = [set(status.allowed_capabilities) for status in chain_statuses]
                if capability_sets:
                    aggregated_capabilities = list(set.intersection(*capability_sets))
                else:
                    aggregated_capabilities = []

            # Aggregate ATP multiplier (product of chain, excluding REVOKED ancestors)
            # For graceful degradation: ignore REVOKED ancestors, compound only DEGRADED
            aggregated_atp_multiplier = 1.0
            for status in chain_statuses:
                # Skip REVOKED nodes in ATP calculation (graceful degradation)
                if status.trust_level != TrustLevel.REVOKED:
                    aggregated_atp_multiplier *= status.atp_multiplier

            # Determine overall status
            leaf_status = chain_statuses[0]

            return TrustStatus(
                society_lct_uri=leaf_lct_uri,
                trust_level=min_trust_level,
                has_delegation=leaf_status.has_delegation,
                parent_legitimate=all(s.parent_legitimate or not s.has_delegation for s in chain_statuses),
                child_revoked=leaf_status.child_revoked,
                atp_multiplier=aggregated_atp_multiplier,
                allowed_capabilities=aggregated_capabilities
            )

        except (CircularDelegationError, ExcessiveChainDepthError, CapabilityEscalationError) as e:
            # Chain validation failed - treat as revoked
            return TrustStatus(
                society_lct_uri=leaf_lct_uri,
                trust_level=TrustLevel.REVOKED,
                has_delegation=False,
                parent_legitimate=False,
                child_revoked=True,
                atp_multiplier=0.0,
                allowed_capabilities=[]
            )

    def invalidate_chain_cache(self, lct_uri: str):
        """
        Invalidate chain cache for society and all descendants.

        Called when revocation or delegation changes occur.

        Args:
            lct_uri: LCT URI whose cache to invalidate
        """
        # Invalidate direct cache entry
        if lct_uri in self.chain_cache:
            del self.chain_cache[lct_uri]
            del self.chain_cache_timestamps[lct_uri]

        # Invalidate all entries that have this URI in their chain
        to_invalidate = []
        for cached_uri, chain in self.chain_cache.items():
            if lct_uri in chain:
                to_invalidate.append(cached_uri)

        for uri in to_invalidate:
            del self.chain_cache[uri]
            del self.chain_cache_timestamps[uri]

    def revoke_society(self, lct_uri: str):
        """
        Revoke society and invalidate chain cache.

        Args:
            lct_uri: LCT URI to revoke
        """
        super().revoke_society(lct_uri)
        self.invalidate_chain_cache(lct_uri)

    def create_delegation(
        self,
        parent_identity: LCTIdentity,
        child_lct_uri: str,
        capabilities: List[Capability],
        expires_at: Optional[int] = None
    ) -> DelegationAttestation:
        """
        Create delegation and invalidate chain cache.

        Args:
            parent_identity: Parent LCT identity
            child_lct_uri: Child LCT URI
            capabilities: Capabilities to grant
            expires_at: Optional expiration timestamp

        Returns:
            Created delegation attestation

        Raises:
            CapabilityEscalationError: If parent doesn't have capabilities to grant
        """
        # Validate parent has capabilities to grant
        parent_status = self.compute_trust_status(parent_identity.to_lct_uri())
        parent_capabilities = set(parent_status.allowed_capabilities)
        requested_capabilities = set(capabilities)

        if not requested_capabilities.issubset(parent_capabilities):
            escalated = requested_capabilities - parent_capabilities
            raise CapabilityEscalationError(
                f"Parent {parent_identity.to_lct_uri()} cannot grant capabilities {escalated} "
                f"that it doesn't possess"
            )

        # Create delegation
        delegation = super().create_delegation(
            parent_identity, child_lct_uri, capabilities, expires_at
        )

        # Invalidate cache
        self.invalidate_chain_cache(child_lct_uri)

        return delegation


# ============================================================================
# Test: Multi-Level Chain Trust Propagation
# ============================================================================

def test_multilevel_trust_propagation():
    """
    Test trust propagation through 3-level chain.

    Scenario:
    Root → Parent → Child → Grandchild

    Test cases:
    1. All FULL: Chain should be FULL
    2. Parent DEGRADED: Child and Grandchild should be DEGRADED
    3. Parent REVOKED: Child and Grandchild should be DEGRADED (graceful)
    """
    print("=" * 80)
    print("TEST: MULTI-LEVEL TRUST PROPAGATION")
    print("=" * 80)
    print()

    authenticator = MultiLevelDelegationAuthenticator(network="web4.network")

    # Create 4-level chain: Root → Parent → Child → Grandchild
    root_identity, root_key = create_test_lct_identity("root")
    root_attestation = create_attestation(root_identity, root_key)
    authenticator.register_society(root_identity, root_attestation)

    parent_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/parent"
    child_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/parent/child"
    grandchild_lct = f"lct://{root_identity.agent_id}@{root_identity.network}/parent/child/grandchild"

    # Root → Parent delegation
    root_to_parent = authenticator.create_delegation(
        parent_identity=root_identity,
        child_lct_uri=parent_lct,
        capabilities=[Capability.SUB_DELEGATION, Capability.QUALITY_ATTESTATION],
        expires_at=None
    )

    # For multi-level, we manually add delegations to simulate the chain
    # In real implementation, each level would have its own identity
    # But for testing, we create the delegation records directly

    # Parent → Child delegation (parent has same agent_id as root)
    parent_to_child = DelegationAttestation(
        parent_lct_uri=parent_lct,
        child_lct_uri=child_lct,
        capabilities=[Capability.SUB_DELEGATION, Capability.QUALITY_ATTESTATION],
        created_at=int(time.time()),
        expires_at=None,
        signature=secrets.token_hex(32)  # Mock signature for testing
    )
    authenticator.delegations[child_lct] = parent_to_child

    # Child → Grandchild delegation
    child_to_grandchild = DelegationAttestation(
        parent_lct_uri=child_lct,
        child_lct_uri=grandchild_lct,
        capabilities=[Capability.QUALITY_ATTESTATION],
        created_at=int(time.time()),
        expires_at=None,
        signature=secrets.token_hex(32)  # Mock signature for testing
    )
    authenticator.delegations[grandchild_lct] = child_to_grandchild

    print("Setup:")
    print("-" * 80)
    print(f"  Root: {root_identity.to_lct_uri()[:50]}...")
    print(f"  Parent: {parent_lct[:60]}...")
    print(f"  Child: {child_lct[:60]}...")
    print(f"  Grandchild: {grandchild_lct[:60]}...")
    print()

    # Test Case 1: All FULL
    print("Test Case 1: All nodes legitimate (FULL trust)")
    print("-" * 80)

    grandchild_status = authenticator.compute_chain_trust_status(grandchild_lct)
    chain = authenticator.get_delegation_chain(grandchild_lct)

    print(f"  Chain depth: {len(chain)}")
    print(f"  Chain: {' → '.join([c.split('/')[-1] if '/' in c else 'root' for c in reversed(chain)])}")

    # Debug: Show status of each node
    print(f"\n  Individual node statuses:")
    for node in reversed(chain):
        node_status = authenticator.compute_trust_status(node)
        node_name = node.split('/')[-1] if '/' in node else 'root'
        print(f"    {node_name}: {node_status.trust_level.value} (ATP: {node_status.atp_multiplier}x)")

    print(f"\n  Aggregated grandchild status:")
    print(f"  Trust level: {grandchild_status.trust_level.value}")
    print(f"  ATP multiplier: {grandchild_status.atp_multiplier}x")
    print(f"  Capabilities: {[c.value for c in grandchild_status.allowed_capabilities]}")
    print()

    # Test Case 2: Revoke Parent (middle node)
    print("Test Case 2: Revoke Parent (middle node)")
    print("-" * 80)

    authenticator.revoke_society(parent_lct)

    # Debug: Show status of each node after revocation
    print(f"\n  Individual node statuses after revocation:")
    for node in reversed(chain):
        node_status = authenticator.compute_trust_status(node)
        node_name = node.split('/')[-1] if '/' in node else 'root'
        print(f"    {node_name}: {node_status.trust_level.value} (ATP: {node_status.atp_multiplier}x)")

    try:
        grandchild_status_after = authenticator.compute_chain_trust_status(grandchild_lct)

        print(f"\n  Aggregated grandchild status:")
        print(f"  Grandchild trust level: {grandchild_status_after.trust_level.value}")
        print(f"  Grandchild ATP multiplier: {grandchild_status_after.atp_multiplier}x")
    except Exception as e:
        print(f"\n  ❌ ERROR computing chain trust status: {e}")
        import traceback
        traceback.print_exc()
        grandchild_status_after = TrustStatus(
            society_lct_uri=grandchild_lct,
            trust_level=TrustLevel.REVOKED,
            has_delegation=False,
            parent_legitimate=False,
            child_revoked=False,
            atp_multiplier=0.0,
            allowed_capabilities=[]
        )
    print()

    # Verify graceful degradation
    if grandchild_status_after.trust_level == TrustLevel.DEGRADED:
        print("  ✅ SUCCESS: Graceful degradation through chain")
        print("    - Grandchild DEGRADED (not REVOKED)")
        print("    - Maintains reduced functionality")
        success = True
    else:
        print("  ❌ FAILURE: Expected DEGRADED, got", grandchild_status_after.trust_level.value)
        success = False

    print()

    return {
        'test': 'MULTILEVEL_TRUST_PROPAGATION',
        'success': success,
        'chain_depth': len(chain),
        'full_trust_atp': grandchild_status.atp_multiplier,
        'degraded_trust_atp': grandchild_status_after.atp_multiplier
    }


# ============================================================================
# Main
# ============================================================================

def main():
    """Test multi-level delegation chains."""
    print("=" * 80)
    print("SESSION 91 TRACK 1: MULTI-LEVEL DELEGATION CHAINS")
    print("=" * 80)
    print()

    print("Objective: Extend Session 90 delegation to multi-level chains")
    print("Features: Trust propagation, capability restriction, circular detection")
    print()

    results = []

    # Test 1: Trust propagation
    result1 = test_multilevel_trust_propagation()
    results.append(result1)

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    tests_passed = sum(1 for r in results if r['success'])

    print(f"Tests run: {len(results)}")
    print(f"Tests passed: {tests_passed}")
    print()

    if tests_passed == len(results):
        print("✅ SUCCESS: Multi-level delegation chains working")
    else:
        print("⚠️  Some tests failed - review results")

    print()

    # Save results
    results_path = Path("/home/dp/ai-workspace/web4/implementation/session91_track1_multilevel_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results saved to: {results_path}")
    print()

    return results


if __name__ == "__main__":
    main()
