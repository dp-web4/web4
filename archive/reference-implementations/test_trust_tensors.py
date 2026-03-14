#!/usr/bin/env python3
"""
Unit tests for CI-modulated trust tensors

Tests Phase 3 trust integration functions:
- effective_trust() - CI as multiplicative ceiling
- adjusted_atp_cost() - ATP cost penalties for low CI
- required_witnesses() - Witness requirement increases for low CI
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from game.engine.mrh_aware_trust import T3Tensor
from trust_tensors import (
    effective_trust, adjusted_atp_cost, required_witnesses,
    ci_modulation_curve, CIModulationConfig
)


class TestCIModulationCurve(unittest.TestCase):
    """Test CI modulation curve calculation"""

    def test_perfect_coherence(self):
        """CI = 1.0 should give full multiplier (1.0)"""
        config = CIModulationConfig()
        multiplier = ci_modulation_curve(1.0, config)
        self.assertAlmostEqual(multiplier, 1.0)

    def test_zero_coherence(self):
        """CI = 0.0 should give minimum multiplier"""
        config = CIModulationConfig()
        multiplier = ci_modulation_curve(0.0, config)
        self.assertAlmostEqual(multiplier, config.trust_minimum_multiplier)

    def test_quadratic_penalty(self):
        """Default steepness=2.0 should give quadratic penalty"""
        config = CIModulationConfig(trust_modulation_steepness=2.0)
        # CI=0.5 with quadratic should give 0.25
        multiplier = ci_modulation_curve(0.5, config)
        self.assertAlmostEqual(multiplier, 0.25)

    def test_custom_steepness(self):
        """Custom steepness should affect curve shape"""
        # Linear curve (steepness=1.0)
        config_linear = CIModulationConfig(trust_modulation_steepness=1.0)
        multiplier_linear = ci_modulation_curve(0.5, config_linear)
        self.assertAlmostEqual(multiplier_linear, 0.5)

        # Cubic curve (steepness=3.0)
        config_cubic = CIModulationConfig(trust_modulation_steepness=3.0)
        multiplier_cubic = ci_modulation_curve(0.5, config_cubic)
        self.assertAlmostEqual(multiplier_cubic, 0.125)


class TestEffectiveTrust(unittest.TestCase):
    """Test effective trust calculation with CI modulation"""

    def test_perfect_coherence_no_penalty(self):
        """CI = 1.0 should give nearly full trust"""
        base_t3 = T3Tensor(talent=0.9, training=0.8, temperament=0.95)
        eff_trust = effective_trust(base_t3, ci=1.0)

        # Should be close to original (within small modulation)
        self.assertGreater(eff_trust.composite(), 0.85)

    def test_zero_coherence_minimum_trust(self):
        """CI = 0.0 should give minimum trust"""
        base_t3 = T3Tensor(talent=0.9, training=0.8, temperament=0.95)
        config = CIModulationConfig(trust_minimum_multiplier=0.1)
        eff_trust = effective_trust(base_t3, ci=0.0, config=config)

        # Should be at minimum multiplier
        self.assertAlmostEqual(eff_trust.talent, 0.9 * 0.1, places=2)
        self.assertAlmostEqual(eff_trust.training, 0.8 * 0.1, places=2)
        self.assertAlmostEqual(eff_trust.temperament, 0.95 * 0.1, places=2)

    def test_medium_coherence_penalty(self):
        """CI = 0.5 should give quadratic penalty (25% of base)"""
        base_t3 = T3Tensor(talent=0.8, training=0.8, temperament=0.8)
        eff_trust = effective_trust(base_t3, ci=0.5)

        # With steepness=2.0, CI=0.5 gives multiplier=0.25
        self.assertAlmostEqual(eff_trust.talent, 0.8 * 0.25, places=2)
        self.assertAlmostEqual(eff_trust.training, 0.8 * 0.25, places=2)
        self.assertAlmostEqual(eff_trust.temperament, 0.8 * 0.25, places=2)

    def test_preserves_t3_proportions(self):
        """CI modulation should preserve relative T3 proportions"""
        base_t3 = T3Tensor(talent=0.9, training=0.6, temperament=0.3)
        eff_trust = effective_trust(base_t3, ci=0.7)

        # Ratios should be preserved
        base_ratio = base_t3.talent / base_t3.temperament
        eff_ratio = eff_trust.talent / eff_trust.temperament
        self.assertAlmostEqual(base_ratio, eff_ratio, places=5)


class TestAdjustedATPCost(unittest.TestCase):
    """Test ATP cost modulation with CI penalties"""

    def test_high_coherence_no_penalty(self):
        """CI ≥ 0.9 should not increase ATP cost"""
        base_cost = 100.0
        config = CIModulationConfig(atp_threshold_high=0.9)

        cost_perfect = adjusted_atp_cost(base_cost, ci=1.0, config=config)
        cost_high = adjusted_atp_cost(base_cost, ci=0.9, config=config)

        self.assertEqual(cost_perfect, base_cost)
        self.assertEqual(cost_high, base_cost)

    def test_low_coherence_penalty(self):
        """Low CI should increase ATP cost"""
        base_cost = 100.0

        cost_medium = adjusted_atp_cost(base_cost, ci=0.7)
        cost_low = adjusted_atp_cost(base_cost, ci=0.3)

        # Both should be higher than base
        self.assertGreater(cost_medium, base_cost)
        self.assertGreater(cost_low, base_cost)

        # Lower CI should cost more
        self.assertGreater(cost_low, cost_medium)

    def test_quadratic_penalty_default(self):
        """Default penalty should be quadratic (1/ci^2)"""
        base_cost = 100.0
        config = CIModulationConfig(
            atp_threshold_high=0.9,
            atp_penalty_exponent=2.0,
            atp_max_multiplier=10.0
        )

        # CI=0.5 with quadratic: multiplier = 1/(0.5^2) = 4.0
        cost = adjusted_atp_cost(base_cost, ci=0.5, config=config)
        self.assertAlmostEqual(cost, 400.0, delta=1.0)

    def test_penalty_capped_at_max(self):
        """ATP cost penalty should be capped at max multiplier"""
        base_cost = 100.0
        config = CIModulationConfig(
            atp_threshold_high=0.9,
            atp_max_multiplier=10.0
        )

        # Very low CI should hit cap
        cost = adjusted_atp_cost(base_cost, ci=0.1, config=config)
        self.assertAlmostEqual(cost, 1000.0, delta=1.0)  # 10x max

    def test_custom_penalty_exponent(self):
        """Custom penalty exponent should change curve shape"""
        base_cost = 100.0

        # Linear penalty (exponent=1.0)
        config_linear = CIModulationConfig(
            atp_threshold_high=0.9,
            atp_penalty_exponent=1.0,
            atp_max_multiplier=10.0
        )
        cost_linear = adjusted_atp_cost(base_cost, ci=0.5, config=config_linear)
        self.assertAlmostEqual(cost_linear, 200.0, delta=1.0)  # 1/0.5 = 2.0

        # Cubic penalty (exponent=3.0)
        config_cubic = CIModulationConfig(
            atp_threshold_high=0.9,
            atp_penalty_exponent=3.0,
            atp_max_multiplier=10.0
        )
        cost_cubic = adjusted_atp_cost(base_cost, ci=0.5, config=config_cubic)
        self.assertAlmostEqual(cost_cubic, 800.0, delta=1.0)  # 1/(0.5^3) = 8.0


class TestRequiredWitnesses(unittest.TestCase):
    """Test witness requirement modulation with CI"""

    def test_high_coherence_no_additional_witnesses(self):
        """CI ≥ 0.8 should not require additional witnesses"""
        base_req = 3
        config = CIModulationConfig(witness_threshold_high=0.8)

        req_perfect = required_witnesses(base_req, ci=1.0, config=config)
        req_high = required_witnesses(base_req, ci=0.8, config=config)

        self.assertEqual(req_perfect, base_req)
        self.assertEqual(req_high, base_req)

    def test_low_coherence_additional_witnesses(self):
        """Low CI should require additional witnesses"""
        base_req = 3

        req_medium = required_witnesses(base_req, ci=0.6)
        req_low = required_witnesses(base_req, ci=0.2)

        # Both should be higher than base
        self.assertGreater(req_medium, base_req)
        self.assertGreater(req_low, base_req)

        # Lower CI should require more witnesses
        self.assertGreater(req_low, req_medium)

    def test_linear_scaling(self):
        """Witness requirements should scale linearly with CI distance"""
        base_req = 3
        config = CIModulationConfig(
            witness_threshold_high=0.8,
            witness_penalty_steepness=10.0
        )

        # CI=0.6: distance ≈ 0.2, additional = ceil(0.2 * 10) = 3 (due to float precision)
        req = required_witnesses(base_req, ci=0.6, config=config)
        self.assertEqual(req, 6)  # 3 + 3

    def test_penalty_capped_at_max(self):
        """Additional witnesses should be capped at maximum"""
        base_req = 3
        config = CIModulationConfig(
            witness_threshold_high=0.8,
            witness_max_additional=8
        )

        # Very low CI should hit cap
        req = required_witnesses(base_req, ci=0.0, config=config)
        self.assertLessEqual(req - base_req, 8)  # Additional witnesses ≤ 8

    def test_ceiling_function(self):
        """Should use ceiling for fractional witness counts"""
        base_req = 3
        config = CIModulationConfig(
            witness_threshold_high=0.8,
            witness_penalty_steepness=5.0  # Gives fractional results
        )

        # CI=0.7: distance = 0.1, additional = ceil(0.1 * 5) = ceil(0.5) = 1
        req = required_witnesses(base_req, ci=0.7, config=config)
        self.assertEqual(req, 4)  # 3 + 1


class TestConfigurability(unittest.TestCase):
    """Test society-configurable parameters"""

    def test_strict_society_config(self):
        """Strict societies should have aggressive modulation"""
        strict_config = CIModulationConfig(
            trust_modulation_steepness=3.0,      # Steep penalty
            trust_minimum_multiplier=0.05,        # Very low minimum
            atp_max_multiplier=20.0,              # High max cost
            witness_max_additional=15             # Many additional witnesses
        )

        base_t3 = T3Tensor(talent=0.8, training=0.8, temperament=0.8)
        base_cost = 100.0
        base_witnesses = 3

        eff_trust = effective_trust(base_t3, ci=0.5, config=strict_config)
        adj_cost = adjusted_atp_cost(base_cost, ci=0.5, config=strict_config)
        req_wit = required_witnesses(base_witnesses, ci=0.5, config=strict_config)

        # Strict config should give harsher penalties
        self.assertLess(eff_trust.composite(), 0.15)  # Very low trust
        self.assertGreater(adj_cost, 300.0)           # High cost
        self.assertGreater(req_wit, 5)                # Many witnesses

    def test_lenient_society_config(self):
        """Lenient societies should have gentle modulation"""
        lenient_config = CIModulationConfig(
            trust_modulation_steepness=1.0,       # Linear penalty
            trust_minimum_multiplier=0.5,         # High minimum
            atp_max_multiplier=3.0,               # Low max cost
            witness_max_additional=2              # Few additional witnesses
        )

        base_t3 = T3Tensor(talent=0.8, training=0.8, temperament=0.8)
        base_cost = 100.0
        base_witnesses = 3

        eff_trust = effective_trust(base_t3, ci=0.5, config=lenient_config)
        adj_cost = adjusted_atp_cost(base_cost, ci=0.5, config=lenient_config)
        req_wit = required_witnesses(base_witnesses, ci=0.5, config=lenient_config)

        # Lenient config should give lighter penalties
        self.assertGreater(eff_trust.composite(), 0.35)  # Moderate trust
        self.assertLess(adj_cost, 500.0)                 # Moderate cost
        self.assertLessEqual(req_wit, 6)                 # Moderate witnesses


if __name__ == '__main__':
    unittest.main()
