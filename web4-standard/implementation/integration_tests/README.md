# Web4 Integration Testing Framework

**Purpose**: Enable UNIT_TESTED → INTEGRATION_TESTED progression for Web4 components

**Created**: Session #23 (2025-11-13)

## Overview

Integration tests validate that multiple Web4 components work together correctly. Unlike unit tests (which test components in isolation), integration tests verify:

1. **Component Interactions**: Do components communicate correctly?
2. **Data Flow**: Does data flow correctly through the system?
3. **State Consistency**: Do components maintain consistent state?
4. **Error Propagation**: Do errors propagate correctly?

## Test Levels

```
UNIT_TESTED        → Tests single component in isolation
INTEGRATION_TESTED → Tests multiple components working together
VALIDATED          → Tests in real-world/production scenarios
```

## Current Web4 Components

### UNIT_TESTED (ready for integration testing):
1. **LCT Identity System** (reputation_tracker.py:1-470)
   - Reputation (T3) calculation
   - Behavior event recording
   - Coherence tracking

2. **Authorization System** (authorization_engine.py:1-560)
   - Policy evaluation
   - Tiered permissions
   - Context-aware authorization

3. **Identity Service** (identity_service_phase2.py:1-561)
   - LCT minting
   - Witness validation
   - ATP cost enforcement
   - Attack resistance (0% bypass rate)

### Integration Test Scenarios

#### Scenario 1: Identity + Reputation Integration
**Components**: LCT minting + Reputation tracking

**Test Flow**:
1. Mint new LCT (identity service)
2. Record witness attestation (reputation)
3. Check witness T3 score before/after
4. Verify attestation increases witness reputation

**Expected Behavior**:
- Successful LCT mint creates attestation event
- Witness gets WITNESS_VERIFICATION coherence boost (+0.2)
- Witness T3 increases appropriately

**Validation**:
- Witness T3 before attestation < Witness T3 after
- Event appears in reputation tracker
- Event metadata contains LCT reference

---

#### Scenario 2: Reputation + Authorization Integration
**Components**: Reputation tracking + Authorization engine

**Test Flow**:
1. Create agents with different T3 scores
2. Test authorization decisions based on T3
3. Verify permission grants align with reputation tiers

**Expected Behavior**:
- Novice (T3 < 0.3): Read-only permissions
- Developing (0.3-0.5): Limited write permissions
- Trusted (0.5-0.7): Normal write permissions
- Expert (0.7-0.9): Elevated permissions
- Master (0.9-1.0): Admin permissions

**Validation**:
- Authorization decisions match T3 thresholds
- Context-specific reputation affects permissions
- Organization isolation preserved

---

#### Scenario 3: Full Stack Integration
**Components**: Identity + Reputation + Authorization

**Test Flow**:
1. New agent requests LCT
2. Witnesses attest (reputation updated)
3. Agent requests resource access (authorization check)
4. Permission granted based on witness reputation

**Expected Behavior**:
- High-reputation witnesses → faster trust building
- Low-reputation witnesses → slower trust building
- Authorization respects reputation tiers

**Validation**:
- End-to-end flow completes successfully
- State consistent across all components
- No data loss or corruption

---

## Integration Test Structure

```python
# Example integration test structure

import pytest
from pathlib import Path
import sys

# Add component paths
sys.path.insert(0, str(Path(__file__).parent.parent / "reputation"))
sys.path.insert(0, str(Path(__file__).parent.parent / "authorization"))
sys.path.insert(0, str(Path(__file__).parent.parent / "services"))

from reputation_tracker import ReputationTracker, BehaviorType
from authorization_engine import AuthorizationEngine, Permission
from identity_service_phase2 import IdentityService


class TestIdentityReputationIntegration:
    """Integration tests for Identity + Reputation"""

    def setup_method(self):
        """Setup test environment"""
        self.reputation = ReputationTracker()
        self.identity = IdentityService(reputation_tracker=self.reputation)

    def test_witness_attestation_updates_reputation(self):
        """Witness attestation should increase witness reputation"""
        # Test implementation...
        pass


class TestReputationAuthorizationIntegration:
    """Integration tests for Reputation + Authorization"""

    def setup_method(self):
        """Setup test environment"""
        self.reputation = ReputationTracker()
        self.authz = AuthorizationEngine(reputation_tracker=self.reputation)

    def test_authorization_respects_reputation_tiers(self):
        """Authorization decisions should align with reputation tiers"""
        # Test implementation...
        pass


class TestFullStackIntegration:
    """Integration tests for complete Web4 stack"""

    def setup_method(self):
        """Setup test environment"""
        self.reputation = ReputationTracker()
        self.identity = IdentityService(reputation_tracker=self.reputation)
        self.authz = AuthorizationEngine(reputation_tracker=self.reputation)

    def test_end_to_end_agent_lifecycle(self):
        """Test complete agent lifecycle: mint → attest → authorize"""
        # Test implementation...
        pass
```

## Running Integration Tests

```bash
# Run all integration tests
cd ~/ai-workspace/web4/web4-standard/implementation/integration_tests
pytest -v

# Run specific integration test
pytest -v test_identity_reputation_integration.py

# Run with coverage
pytest --cov=../reputation --cov=../authorization --cov=../services
```

## Success Criteria

Integration tests PASS if:
1. All component interactions work correctly
2. Data flows correctly between components
3. State remains consistent across components
4. Errors propagate correctly
5. No unexpected side effects

## Epistemic Status Progression

```
Component A: UNIT_TESTED
Component B: UNIT_TESTED
Integration Test: PASS
→ System (A+B): INTEGRATION_TESTED
```

## Next Steps

1. **Immediate**: Implement Scenario 1 (Identity + Reputation)
2. **Short-term**: Implement Scenario 2 (Reputation + Authorization)
3. **Medium-term**: Implement Scenario 3 (Full Stack)
4. **Long-term**: ACT society integration testing

## Design Philosophy

**Integration testing validates assumptions**:
- Unit tests prove components work alone
- Integration tests prove components work together
- Neither guarantees real-world success (that's VALIDATED)

**Epistemic proprioception**:
- UNIT_TESTED = "I know this component works"
- INTEGRATION_TESTED = "I know these components work together"
- VALIDATED = "I know this works in the real world"

**Value of integration testing**:
- Discovers interface mismatches
- Reveals state management issues
- Exposes timing/ordering dependencies
- Validates assumptions about component interactions

## References

- Session #15: LCT Identity implementation (UNIT_TESTED)
- Session #19-21: Identity service hardening (VALIDATED)
- Session #22: Authorization engine (UNIT_TESTED)
- Session #23: Reputation system (UNIT_TESTED)

---

**Status**: Framework created, tests pending implementation

**Epistemic Status**: Integration test framework = POSTULATED (needs test implementation)

---
