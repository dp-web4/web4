"""
Test Trust Source Diversity Mitigation

Session #42

Focused test to verify diversity enforcement prevents trust inflation.
"""

import math
from cross_society_trust_propagation import CrossSocietyTrustNetwork
from cross_society_security_mitigations import DiversifiedTrustEngine


def test_diversity_enforcement():
    """Test diversity enforcement against collusion"""

    print("=" * 80)
    print("TRUST SOURCE DIVERSITY MITIGATION TEST")
    print("=" * 80)

    # Test without diversity enforcement
    print("\n### Scenario 1: WITHOUT Diversity Enforcement")
    print("-" * 80)

    network1 = CrossSocietyTrustNetwork()
    network1.add_society("lct-victim")

    colluders = [f"lct-collude-{i}" for i in range(5)]

    for colluder_id in colluders:
        network1.add_society(colluder_id)
        network1.connect_societies("lct-victim", colluder_id)
        network1.set_society_trust("lct-victim", colluder_id, 0.8)
        network1.set_identity_trust(colluder_id, "lct-attacker", 1.0)

    network1.propagate_all()

    trust_without_diversity = network1.engines["lct-victim"].get_aggregated_trust("lct-attacker")
    print(f"Trust score: {trust_without_diversity:.3f}")

    breakdown1 = network1.engines["lct-victim"].get_trust_breakdown("lct-attacker")
    print(f"Sources: {len(breakdown1['propagated_trust'])}")

    # Test WITH diversity enforcement
    print("\n### Scenario 2: WITH Diversity Enforcement")
    print("-" * 80)

    network2 = CrossSocietyTrustNetwork()

    # Create victim with diversified engine
    diversified_engine = DiversifiedTrustEngine(
        society_lct="lct-victim",
        diversity_enabled=True,
    )
    network2.engines["lct-victim"] = diversified_engine

    # Add colluding societies
    for colluder_id in colluders:
        network2.add_society(colluder_id)
        network2.connect_societies("lct-victim", colluder_id)

        # Set society trust on diversified engine
        diversified_engine.set_society_trust(colluder_id, 0.8)

        # Set identity trust on colluders
        network2.set_identity_trust(colluder_id, "lct-attacker", 1.0)

    network2.propagate_all()

    trust_with_diversity = diversified_engine.get_aggregated_trust("lct-attacker")
    print(f"Trust score: {trust_with_diversity:.3f}")

    breakdown2 = diversified_engine.get_trust_breakdown("lct-attacker")
    print(f"Sources: {len(breakdown2['propagated_trust'])}")

    # Verify diversity discount was applied
    print("\n### Analysis")
    print("-" * 80)

    print(f"Without diversity: {trust_without_diversity:.3f}")
    print(f"With diversity: {trust_with_diversity:.3f}")

    if trust_with_diversity < trust_without_diversity:
        reduction = (1 - trust_with_diversity / trust_without_diversity) * 100
        print(f"Reduction: {reduction:.1f}%")
        print("✅ MITIGATION EFFECTIVE")
    else:
        print("⚠️  MITIGATION FAILED - No reduction observed")

    # Calculate expected diversity discount
    num_sources = len(breakdown2['propagated_trust'])
    if num_sources > 0:
        expected_discount = 1.0 / math.log2(num_sources + 1)
        print(f"\nExpected diversity discount: {expected_discount:.3f}")
        print(f"(for {num_sources} sources)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_diversity_enforcement()
